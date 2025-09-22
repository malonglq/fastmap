"""Reusable offset-map query helpers for AWB analysis integration."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from core.models.map_data import MapPoint


@dataclass(frozen=True)
class RangeWindow:
    """Target span used when filtering records on a specific axis."""

    key: str
    lower: float
    upper: float
    label: Optional[str] = None
    description: Optional[str] = None

    def describe_overlap(self) -> str:
        if self.description:
            return self.description
        label = self.label or self.key.upper()
        return f"{label} 区间与 [{self.lower:.2f}, {self.upper:.2f}] 有交集"


@dataclass(frozen=True)
class RangeSpan:
    """Numeric span declared on an offset-map axis."""

    key: str
    minimum: float
    maximum: float

    def overlaps(self, window: RangeWindow) -> bool:
        return self.maximum >= window.lower and self.minimum <= window.upper

    def covers(self, window: RangeWindow) -> bool:
        return self.minimum <= window.lower and self.maximum >= window.upper

    def format_bounds(self) -> str:
        return f"[{_format_number(self.minimum)}, {_format_number(self.maximum)}]"


@dataclass(frozen=True)
class OffsetMapRecord:
    """Simplified record extracted from a :class:`MapPoint`."""

    tag: str
    alias: str
    weight: float
    ml: int
    ranges: Dict[str, RangeSpan]
    index: int
    source: Optional[MapPoint] = None

    def overlaps_window(self, axis: str, window: RangeWindow) -> bool:
        span = self.ranges.get(axis)
        return span is not None and span.overlaps(window)

    def covers_window(self, axis: str, window: RangeWindow) -> bool:
        span = self.ranges.get(axis)
        return span is not None and span.covers(window)

    def format_range(self, axis: str) -> str:
        span = self.ranges.get(axis)
        return span.format_bounds() if span is not None else "-"

    def format_weight(self) -> str:
        return f"{self.weight:.2f}"


@dataclass(frozen=True)
class OffsetMapQuerySpec:
    """Declarative query definition applied to :class:`OffsetMapRecord` objects."""

    name: str
    title: str
    ml: Optional[int] = None
    range_windows: Dict[str, RangeWindow] = field(default_factory=dict)
    extra_filters: Tuple[Callable[[OffsetMapRecord], bool], ...] = ()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, record: OffsetMapRecord) -> bool:
        if self.ml is not None and record.ml != self.ml:
            return False
        for axis, window in self.range_windows.items():
            if not record.overlaps_window(axis, window):
                return False
        return all(predicate(record) for predicate in self.extra_filters)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "OffsetMapQuerySpec":
        name = payload.get('name') or payload.get('title') or 'offset_query'
        title = payload.get('title') or name
        ml_value = payload.get('ml')
        range_windows: Dict[str, RangeWindow] = {}
        for axis, spec in (payload.get('range_windows') or payload.get('ranges') or {}).items():
            if isinstance(spec, RangeWindow):
                window = spec
            else:
                lower = spec.get('lower', spec.get('min', 0.0))
                upper = spec.get('upper', spec.get('max', 0.0))
                label = spec.get('label')
                description = spec.get('description')
                window = RangeWindow(
                    key=axis,
                    lower=float(lower),
                    upper=float(upper),
                    label=label,
                    description=description,
                )
            range_windows[axis] = window
        metadata = dict(payload.get('metadata') or {})
        return cls(name=name, title=title, ml=ml_value, range_windows=range_windows, metadata=metadata)


@dataclass
class OffsetMapQueryResult:
    """Result bundle returned by :class:`OffsetMapQueryService`."""

    spec: OffsetMapQuerySpec
    matched: List[OffsetMapRecord]
    coverage: Dict[str, List[OffsetMapRecord]]


class OffsetMapQueryService:
    """Helper service that converts :class:`MapPoint` objects into queryable records."""

    def __init__(self, map_points: Iterable[MapPoint]):
        self.records = self._build_records(map_points)

    def run_query(self, spec: OffsetMapQuerySpec) -> OffsetMapQueryResult:
        matched = [record for record in self.records if spec.matches(record)]
        coverage = {
            axis: [rec for rec in matched if rec.covers_window(axis, window)]
            for axis, window in spec.range_windows.items()
        }
        return OffsetMapQueryResult(spec=spec, matched=matched, coverage=coverage)

    def run_queries(self, specs: Sequence[OffsetMapQuerySpec]) -> List[OffsetMapQueryResult]:
        return [self.run_query(spec) for spec in specs]

    @staticmethod
    def _build_records(map_points: Iterable[MapPoint]) -> List[OffsetMapRecord]:
        records: List[OffsetMapRecord] = []
        for fallback_index, point in enumerate(map_points):
            extra = getattr(point, 'extra_attributes', {}) or {}
            ml_value = extra.get('ml')
            try:
                ml = int(ml_value)
            except (TypeError, ValueError):
                continue

            map_tag = extra.get('map_tag') or getattr(point, 'alias_name', '') or ''
            index_value = extra.get('map_index')
            try:
                map_index = int(index_value)
            except (TypeError, ValueError):
                map_index = _extract_index(map_tag, fallback_index)

            ranges: Dict[str, RangeSpan] = {}
            for axis, attr in (('bv', 'bv_range'), ('ctemp', 'ctemp_range'), ('ir', 'ir_range')):
                span = getattr(point, attr, None)
                if not span:
                    continue
                try:
                    minimum = float(span[0])
                    maximum = float(span[1])
                except (TypeError, ValueError, IndexError):
                    continue
                if math.isfinite(minimum) and math.isfinite(maximum):
                    ranges[axis] = RangeSpan(key=axis, minimum=minimum, maximum=maximum)

            record = OffsetMapRecord(
                tag=map_tag,
                alias=getattr(point, 'alias_name', ''),
                weight=float(getattr(point, 'weight', 0.0)),
                ml=ml,
                ranges=ranges,
                index=map_index,
                source=point,
            )
            records.append(record)

        records.sort(key=lambda rec: (rec.index, rec.tag))
        return records


def build_report_section(result: OffsetMapQueryResult) -> Dict[str, Any]:
    """Generate a narrative section dictionary for report/template usage."""

    narrative_id = result.spec.metadata.get('narrative_id') if result.spec.metadata else None
    if narrative_id == 'awb_reduce_default':
        return _build_awb_reduce_section(result)
    if narrative_id == 'awb_enhance_default':
        return _build_awb_enhance_section(result)
    return _build_generic_section(result)


def _build_generic_section(result: OffsetMapQueryResult) -> Dict[str, Any]:
    spec = result.spec
    matched = _sort_records(result.matched)
    coverage_sorted = {axis: _sort_records(records) for axis, records in result.coverage.items()}

    window_descriptions = [window.describe_overlap() for window in spec.range_windows.values()]
    condition_text = '，'.join(window_descriptions)
    ml_clause = f"，ml={spec.ml}" if spec.ml is not None else ''
    overview_lines = [f"- 满足 {condition_text}{ml_clause} 的 offset_map 共 {len(matched)} 条。"]
    for axis, records in coverage_sorted.items():
        if not records:
            continue
        window = spec.range_windows[axis]
        axis_label = window.label or axis.upper()
        overview_lines.append(
            f"- 其中 {len(records)} 条（{_format_map_list(records)}）完全覆盖 {axis_label} 区间 {window.lower:.2f}–{window.upper:.2f}。"
        )

    table = _build_table_payload(matched, spec)
    highlights = []

    return {
        'title': spec.title or spec.name,
        'methodology': spec.metadata.get('methodology_lines', ["- 针对当前 Map 配置执行可复用的 offset_map 查询逻辑，统计满足条件的条目数量。"]),
        'overview': overview_lines,
        'table': table,
        'highlights': highlights,
        'has_matches': bool(matched),
        'coverage': {axis: {'count': len(records), 'tags': _format_tag_list(records)} for axis, records in coverage_sorted.items()},
        'insights': spec.metadata.get('insights', []) if spec.metadata else [],
    }


def _build_awb_reduce_section(result: OffsetMapQueryResult) -> Dict[str, Any]:
    spec = result.spec
    matched = _sort_records(result.matched)
    coverage_sorted = {axis: _sort_records(records) for axis, records in result.coverage.items()}

    bv_window = spec.range_windows.get('bv')
    ct_window = spec.range_windows.get('ctemp')
    ct_full = coverage_sorted.get('ctemp', [])
    bv_full = coverage_sorted.get('bv', [])

    overview_lines = [
        f"- 满足 BV ∈ ({_format_number(bv_window.lower)}, {_format_number(bv_window.upper)}) 且色温段与 {_format_number(ct_window.lower)}–{_format_number(ct_window.upper)} K 有交集、同时 ml={spec.ml} 的 offset_map 一共有 {len(matched)} 条。",
        f"- 其中只有 {len(ct_full)} 条（{_format_map_list(ct_full)}）在色温上完全覆盖 {_format_number(ct_window.lower)}–{_format_number(ct_window.upper)} K；另有 {len(bv_full)} 条（{_format_map_list(bv_full)}）在 BV 上完整覆盖 {_format_number(bv_window.lower)}–{_format_number(bv_window.upper)}，其他条目仅与目标区间部分重叠。",
    ]

    highlights = []
    if ct_full:
        highlights.append(
            f"- 完整覆盖色温 {_format_number(ct_window.lower)}–{_format_number(ct_window.upper)} K 的 {len(ct_full)} 条规则（{_format_map_list(ct_full)}）分别以 {_format_weight_list(ct_full)} 的权重在高 BV（5.5–7.0）或低 BV（0–5.0）范围抑制统计点，属于专门的门店/蓝衣场景。"
        )
    if bv_full:
        highlights.append(
            f"- 能够在 BV 轴完全覆盖 {_format_number(bv_window.lower)}–{_format_number(bv_window.upper)} 的 {len(bv_full)} 条（{_format_map_list(bv_full)}）多为人脸或混合光场景，权重集中在 {_format_weight_list(bv_full)}，提示在整个目标 BV 带上都进行权重削减。"
        )

    table = _build_table_payload(matched, spec, default_axes=['bv', 'ctemp'])

    methodology = spec.metadata.get('methodology_lines') or [
        "- 解析当前 Map 配置的 `offset_map` `<range>` 数据，读取 BV、色温、权重与 `ml`，并结合同名节点下的 `<AliasName>` 获取别名信息，确认 `ml=65535`（减小权重）的场景。",
    ]

    insights = _generate_awb_reduce_insights(matched, spec)

    return {
        'title': spec.title or spec.name,
        'methodology': methodology,
        'overview': overview_lines,
        'table': table,
        'highlights': highlights,
        'has_matches': bool(matched),
        'coverage': {
            'ctemp': {'count': len(ct_full), 'tags': _format_tag_list(ct_full)},
            'bv': {'count': len(bv_full), 'tags': _format_tag_list(bv_full)},
        },
        'insights': insights,
    }


def _build_awb_enhance_section(result: OffsetMapQueryResult) -> Dict[str, Any]:
    spec = result.spec
    matched = _sort_records(result.matched)
    coverage_sorted = {axis: _sort_records(records) for axis, records in result.coverage.items()}

    windows = spec.range_windows
    metadata = spec.metadata or {}
    shared_records = metadata.get('shared_records')
    if isinstance(shared_records, (list, tuple)):
        window_records = [
            record for record in shared_records if _record_overlaps_windows(record, windows)
        ]
    else:
        window_records = list(matched)

    reduce_records = [record for record in window_records if record.ml == 65535]
    enhance_records = [record for record in window_records if record.ml == 65471]
    total_records = len(window_records)

    bv_window = windows.get('bv')
    overview_lines: List[str] = []
    if bv_window:
        overview_lines.append(
            (
                f"- 在 BV≈{_format_number(bv_window.lower)}–{_format_number(bv_window.upper)} 的区间内共有 {total_records} 条 offset map 规则，"
                f"其中 {len(reduce_records)} 条是减权映射（ml=65535，平均权重约 {_format_average_weight(reduce_records)}），"
                f"{len(enhance_records)} 条为强拉映射（ml=65471，平均权重约 {_format_average_weight(enhance_records)}），"
                "表明该亮度带既需要抑制部分统计点的权重，也要把极端色偏的统计点强制拉回基准多边形。"
            )
        )

    category_line = _build_awb_enhance_category_line(matched)
    if category_line:
        overview_lines.append(category_line)

    insights: List[str] = []
    focus_map_75 = _find_record_by_tag(matched, 'offset_map75')
    if focus_map_75:
        insights.append(
            (
                f"- 极暖人造光：{focus_map_75.tag} 在 BV {_format_range_descriptor(_extract_axis_range(focus_map_75, 'bv'))}、"
                f"色温 {_format_range_descriptor(_extract_axis_range(focus_map_75, 'ctemp'), 'K')}、"
                f"{_format_ir_descriptor(_extract_axis_range(focus_map_75, 'ir'))} 条件下直接强拉，"
                "针对咖啡店等极暖光场景把统计点推回基准区域，避免偏红/偏橙光源主导。"
            )
        )

    focus_map_21 = _find_record_by_tag(matched, 'offset_map21')
    if focus_map_21:
        insights.append(
            (
                f"- 高 IR 绿/黄偏：{focus_map_21.tag} 在 BV {_format_range_descriptor(_extract_axis_range(focus_map_21, 'bv'))}、"
                f"色温 {_format_range_descriptor(_extract_axis_range(focus_map_21, 'ctemp'), 'K')}、"
                f"{_format_ir_descriptor(_extract_axis_range(focus_map_21, 'ir'))} 条件下触发强拉，压制高 IR 植物或黄光场景对估计值的拉动，让系统迅速回归基准白点。"
            )
        )

    focus_map_71 = _find_record_by_tag(matched, 'offset_map71')
    if focus_map_71:
        insights.append(
            (
                f"- 冷色极端块：{focus_map_71.tag} 在 BV {_format_range_descriptor(_extract_axis_range(focus_map_71, 'bv'))}、"
                f"色温 {_format_range_descriptor(_extract_axis_range(focus_map_71, 'ctemp'), 'K')}、"
                f"{_format_ir_descriptor(_extract_axis_range(focus_map_71, 'ir'))} 条件下触发强拉，专门处理高亮冷色广告屏、舞台灯等蓝偏统计点。"
            )
        )

    highlights: List[str] = []
    reduce_map_56 = _find_record_by_tag(reduce_records, 'offset_map56')
    if focus_map_21 and reduce_map_56 and focus_map_75:
        highlights.append(
            (
                f"- 高 IR 门限主要用于强拉（如 {focus_map_21.tag} 的 {_format_ir_descriptor(_extract_axis_range(focus_map_21, 'ir'))}），"
                f"确保强偏绿/黄的统计点被直接送回基准；而在强暖光门店等场景（{reduce_map_56.tag}、{focus_map_75.tag}），"
                f"则分别设定 {_format_ir_descriptor(_extract_axis_range(reduce_map_56, 'ir'))}、{_format_ir_descriptor(_extract_axis_range(focus_map_75, 'ir'))} 的上限，"
                "避免暗暖光或低 IR 区域误触发拉回，使减权或强拉更精准。"
            )
        )

    reduce_map_59 = _find_record_by_tag(reduce_records, 'offset_map59')
    reduce_map_32 = _find_record_by_tag(reduce_records, 'offset_map32')
    if reduce_map_59 and reduce_map_32 and focus_map_75 and focus_map_71:
        reduce_span = _combine_ranges(
            [
                _extract_axis_range(reduce_map_59, 'ctemp'),
                _extract_axis_range(reduce_map_32, 'ctemp'),
            ]
        )
        enhance_span = _combine_ranges(
            [
                _extract_axis_range(focus_map_75, 'ctemp'),
                _extract_axis_range(focus_map_71, 'ctemp'),
            ]
        )
        highlights.append(
            (
                f"- 色温控制：减权映射覆盖 {_format_range_descriptor(reduce_span, 'K')} 的混合光区段（如 {reduce_map_59.tag}、{reduce_map_32.tag}），"
                f"而强拉映射则负责 {_format_range_descriptor(enhance_span, 'K')} 的极暖与极冷两端（{focus_map_75.tag}、{focus_map_71.tag}），"
                "形成互补以快速收敛极端色块统计点。"
            )
        )

    if bv_window and total_records:
        highlights.append(
            (
                f"- 结论：在 BV {_format_number(bv_window.lower)}–{_format_number(bv_window.upper)} 的亮度带上，"
                "AWB map 通过“减权 + 强拉”双通道策略覆盖大部分室内外复杂场景：减权映射抑制高权混合光、绿区和门店等常见偏色统计点，"
                "强拉映射则对极端暖/冷色和高 IR 场景快速回收，二者配合控制 IR 与色温窗口，既保留有效统计点，又避免偏色场景干扰最终白平衡估计。"
            )
        )

    table = _build_table_payload(matched, spec, default_axes=['bv', 'ctemp', 'ir'])

    methodology = metadata.get('methodology_lines') or [
        "- 解析当前 Map 配置的 `offset_map` `<range>` 数据，筛选 BV 覆盖 2–6 的规则并定位 `ml=65471`（强拉）条目，统计其范围与权重布局。",
    ]

    return {
        'title': spec.title or spec.name,
        'methodology': methodology,
        'overview': overview_lines,
        'table': table,
        'highlights': highlights,
        'has_matches': bool(matched),
        'coverage': {
            axis: {'count': len(records), 'tags': _format_tag_list(records)}
            for axis, records in coverage_sorted.items()
        },
        'insights': insights,
    }


def _generate_awb_reduce_insights(records: Sequence[OffsetMapRecord], spec: OffsetMapQuerySpec) -> List[str]:
    if not records:
        return []

    bv_window = spec.range_windows.get('bv') if spec.range_windows else None
    ct_window = spec.range_windows.get('ctemp') if spec.range_windows else None

    normalized: List[Dict[str, Any]] = []
    for record in records:
        normalized.append({
            'record': record,
            'alias_lower': (record.alias or '').lower(),
            'tag_lower': record.tag.lower(),
            'weight': record.weight,
            'bv': _extract_axis_range(record, 'bv'),
            'ctemp': _extract_axis_range(record, 'ctemp'),
            'ir': _extract_axis_range(record, 'ir'),
        })

    insights: List[str] = []
    insights.extend(_build_awb_category_summary(normalized))
    insights.extend(_build_awb_layout_highlights(normalized, bv_window, ct_window))
    return insights


def _build_awb_category_summary(normalized: Sequence[Dict[str, Any]]) -> List[str]:
    if not normalized:
        return []

    category_rules: List[Tuple[str, Tuple[str, ...]]] = [
        ('Mix/MixLight', ('mix',)),
        ('Face', ('face',)),
        ('Special', ('special',)),
        ('GreenZone', ('greenzone',)),
    ]

    buckets: List[Tuple[str, int]] = []
    for label, keywords in category_rules:
        count = sum(1 for item in normalized if any(keyword in item['alias_lower'] for keyword in keywords))
        if count:
            buckets.append((label, count))

    buckets.sort(key=lambda pair: pair[1], reverse=True)
    store_count = sum(1 for item in normalized if 'store' in item['alias_lower'])

    if not buckets and not store_count:
        return []

    segments = ['{} {} 条'.format(label, count) for label, count in buckets[:4]]
    line = '- 类别分布：' + ('，'.join(segments) if segments else '无显著类别')
    if store_count:
        line += f'；其中 {store_count} 条别名含 store 的门店场景'
    line += '。'
    return [line]


def _build_awb_enhance_category_line(records: Sequence[OffsetMapRecord]) -> Optional[str]:
    if not records:
        return None

    buckets: List[str] = []
    keyword_groups: List[Tuple[str, Tuple[str, ...]]] = [
        ('GreenZone', ('greenzone',)),
        ('Special', ('special', 'store')),
        ('极端色块', ('blue', 'pure', 'extreme')),
    ]

    for label, keywords in keyword_groups:
        count = sum(
            1
            for record in records
            if any(keyword in f"{record.tag} {record.alias or ''}".lower() for keyword in keywords)
        )
        if count:
            buckets.append(f"{label} {count} 条")

    if not buckets:
        return None

    return (
        '- 强拉映射布局：' + '、'.join(buckets) + '，用于快速收敛强偏色情况到基准区域。'
    )


def _build_awb_layout_highlights(normalized: Sequence[Dict[str, Any]],
                                 bv_window: Optional[RangeWindow],
                                 ct_window: Optional[RangeWindow]) -> List[str]:
    if not normalized:
        return []

    insights: List[str] = []

    def select(filter_fn: Callable[[Dict[str, Any]], bool],
               score_fn: Callable[[Dict[str, Any]], Tuple[Any, ...]]) -> Optional[Dict[str, Any]]:
        candidates = [item for item in normalized if filter_fn(item)]
        if not candidates:
            return None
        return max(candidates, key=score_fn)

    def overlap(item: Dict[str, Any], axis: str, window: Optional[RangeWindow]) -> float:
        return _overlap_length(item.get(axis, (None, None)), window)

    green = select(
        lambda item: 'greenzone' in item['alias_lower'],
        lambda item: (
            overlap(item, 'bv', bv_window),
            overlap(item, 'ctemp', ct_window),
            item['weight'],
        ),
    )
    if green:
        record = green['record']
        line = (
            f"- GreenZone 布局：{_format_record_brief(record)} 覆盖 BV {_format_range_descriptor(green['bv'])}、"
            f"色温 {_format_range_descriptor(green['ctemp'], 'K')}，{_format_ir_descriptor(green['ir'])}，权重 {record.format_weight()}"
        )
        if bv_window:
            bv_overlap = overlap(green, 'bv', bv_window)
            if bv_overlap > 0:
                line += (
                    f"；与目标 BV({_format_number(bv_window.lower)}–{_format_number(bv_window.upper)}) 重叠 {_format_number(bv_overlap)} EV"
                )
        if ct_window:
            ct_overlap = overlap(green, 'ctemp', ct_window)
            if ct_overlap > 0:
                line += f"，色温重叠 {_format_number(ct_overlap)} K"
        line += '。'
        insights.append(line)

    mix = select(
        lambda item: 'mix' in item['alias_lower'],
        lambda item: (
            item['weight'],
            overlap(item, 'bv', bv_window),
            overlap(item, 'ctemp', ct_window),
        ),
    )
    if mix:
        record = mix['record']
        line = (
            f"- Mix 场景抑制：{_format_record_brief(record)} 覆盖 BV {_format_range_descriptor(mix['bv'])}、"
            f"色温 {_format_range_descriptor(mix['ctemp'], 'K')}，{_format_ir_descriptor(mix['ir'])}，权重 {record.format_weight()}"
        )
        if bv_window:
            bv_overlap = overlap(mix, 'bv', bv_window)
            if bv_overlap > 0:
                line += (
                    f"；与目标 BV({_format_number(bv_window.lower)}–{_format_number(bv_window.upper)}) 重叠 {_format_number(bv_overlap)} EV"
                )
        if ct_window:
            ct_overlap = overlap(mix, 'ctemp', ct_window)
            if ct_overlap > 0:
                line += f"，色温重叠 {_format_number(ct_overlap)} K"
        line += '。'
        insights.append(line)

    store_items = [item for item in normalized if 'store' in item['alias_lower']]
    if store_items:
        store_records = [item['record'] for item in store_items]
        bv_span = _combine_ranges(item.get('bv') for item in store_items)
        ct_span = _combine_ranges(item.get('ctemp') for item in store_items)
        line = (
            f"- 门店场景：{_format_map_list(store_records)} 覆盖 BV {_format_range_descriptor(bv_span)}、"
            f"色温 {_format_range_descriptor(ct_span, 'K')}，权重 {_format_weight_range(store_records)}，集中削弱门店别名统计点。"
        )
        insights.append(line)

    return insights


def _extract_axis_range(record: OffsetMapRecord, axis: str) -> Tuple[Optional[float], Optional[float]]:
    span = record.ranges.get(axis)
    if span is None:
        return (None, None)
    return (span.minimum, span.maximum)


def _overlap_length(bounds: Tuple[Optional[float], Optional[float]], window: Optional[RangeWindow]) -> float:
    if window is None:
        return 0.0
    lower, upper = bounds
    if lower is None or upper is None:
        return 0.0
    overlap_lower = max(lower, window.lower)
    overlap_upper = min(upper, window.upper)
    return max(0.0, overlap_upper - overlap_lower)


def _combine_ranges(ranges: Iterable[Tuple[Optional[float], Optional[float]]]) -> Tuple[Optional[float], Optional[float]]:
    lowers: List[float] = []
    uppers: List[float] = []
    for lower, upper in ranges:
        if lower is not None:
            lowers.append(lower)
        if upper is not None:
            uppers.append(upper)
    if not lowers or not uppers:
        return (None, None)
    return (min(lowers), max(uppers))


def _record_overlaps_windows(record: OffsetMapRecord, windows: Dict[str, RangeWindow]) -> bool:
    if not windows:
        return True
    for axis, window in windows.items():
        if not record.overlaps_window(axis, window):
            return False
    return True


def _format_average_weight(records: Sequence[OffsetMapRecord]) -> str:
    if not records:
        return '-'
    total = sum(record.weight for record in records)
    average = total / len(records)
    return f"{average:.2f}"


def _find_record_by_tag(records: Sequence[OffsetMapRecord], tag: str) -> Optional[OffsetMapRecord]:
    tag_lower = tag.lower()
    for record in records:
        if record.tag.lower() == tag_lower:
            return record
    return None


def _format_range_descriptor(bounds: Tuple[Optional[float], Optional[float]], unit: Optional[str] = None) -> str:
    lower, upper = bounds
    if lower is None or upper is None:
        return '-'
    text = f"{_format_number(lower)}–{_format_number(upper)}"
    if unit:
        return f"{text} {unit}"
    return text


def _format_ir_descriptor(bounds: Tuple[Optional[float], Optional[float]]) -> str:
    lower, upper = bounds
    if lower is None and upper is None:
        return 'IR 范围未知'
    if lower is None:
        return f"IR ≤ {_format_number(upper)}"
    if upper is None:
        return f"IR ≥ {_format_number(lower)}"
    if upper >= 900:
        return f"IR ≥ {_format_number(lower)}"
    return f"IR {_format_number(lower)}–{_format_number(upper)}"


def _format_record_brief(record: OffsetMapRecord) -> str:
    alias = record.alias or '-'
    return f"{record.tag}（{alias}）"


def _format_weight_range(records: Sequence[OffsetMapRecord]) -> str:
    weights = sorted({round(record.weight, 4) for record in records})
    if not weights:
        return '-'
    if len(weights) == 1:
        return f"{weights[0]:.2f}"
    return f"{weights[0]:.2f}–{weights[-1]:.2f}"


def _build_table_payload(records: Sequence[OffsetMapRecord], spec: OffsetMapQuerySpec, default_axes: Optional[List[str]] = None) -> Dict[str, Any]:
    if not records:
        axes = default_axes or list(spec.range_windows.keys()) or ['bv', 'ctemp']
    else:
        axes = default_axes or list(spec.metadata.get('table_axes', []))
        if not axes:
            axes = sorted({axis for record in records for axis in record.ranges.keys()})
    axis_labels = {
        'bv': 'BV Range',
        'ctemp': 'CTemp Range',
        'ir': 'IR Range',
    }
    headers = ['offset_map', 'Alias', 'Weight'] + [axis_labels.get(axis, f'{axis} Range') for axis in axes]
    rows = []
    for record in records:
        row = {
            'tag': record.tag,
            'alias': record.alias,
            'weight': record.format_weight(),
            'ranges': {axis: record.format_range(axis) for axis in axes},
        }
        rows.append(row)
    return {'headers': headers, 'rows': rows}


def _sort_records(records: Sequence[OffsetMapRecord]) -> List[OffsetMapRecord]:
    return sorted(records, key=lambda rec: (rec.index, rec.tag))


def _format_number(value: float) -> str:
    if math.isfinite(value) and abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    return f"{value:.2f}".rstrip('0').rstrip('.')


def _format_map_list(records: Sequence[OffsetMapRecord]) -> str:
    return '、'.join(rec.tag for rec in _sort_records(records)) if records else '-'


def _format_tag_list(records: Sequence[OffsetMapRecord]) -> List[str]:
    return [rec.tag for rec in _sort_records(records)]


def _format_weight_list(records: Sequence[OffsetMapRecord]) -> str:
    formatted = [rec.format_weight() for rec in _sort_records(records)]
    return '、'.join(formatted) if formatted else '-'


def _extract_index(tag: str, fallback: int) -> int:
    digits = ''.join(ch for ch in tag if ch.isdigit())
    if digits:
        try:
            return int(digits)
        except ValueError:
            return fallback
    return fallback


__all__ = [
    'OffsetMapQueryService',
    'OffsetMapQuerySpec',
    'OffsetMapQueryResult',
    'OffsetMapRecord',
    'RangeWindow',
    'RangeSpan',
    'build_report_section',
]
