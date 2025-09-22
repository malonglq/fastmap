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

    normalized = _normalize_records(matched)
    category_stats = _collect_awb_category_stats(normalized)

    overview_lines = [
        f"- 满足 BV ∈ ({_format_number(bv_window.lower)}, {_format_number(bv_window.upper)}) 且色温段与 {_format_number(ct_window.lower)}–{_format_number(ct_window.upper)} K 有交集、同时 ml={spec.ml} 的 offset_map 一共有 {len(matched)} 条。",
    ]

    overlap_line = _build_overlap_summary_line(normalized, bv_window, ct_window)
    if overlap_line:
        overview_lines.append(overlap_line)

    category_line = _build_category_overview_line(category_stats)
    if category_line:
        overview_lines.append(category_line)

    table = _build_table_payload(matched, spec, default_axes=['bv', 'ctemp'])

    methodology = spec.metadata.get('methodology_lines') or [
        "- 解析当前 Map 配置的 `offset_map` `<range>` 数据，读取 BV、色温、权重与 `ml`，并结合同名节点下的 `<AliasName>` 获取别名信息，确认 `ml=65535`（减小权重）的场景。",
    ]

    insights = _generate_awb_reduce_insights(
        matched,
        spec,
        normalized=normalized,
        category_stats=category_stats,
    )

    highlights = _build_awb_reduce_highlights(
        normalized,
        category_stats,
        bv_window,
        ct_window,
        ct_full,
        bv_full,
    )

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


def _generate_awb_reduce_insights(
    records: Sequence[OffsetMapRecord],
    spec: OffsetMapQuerySpec,
    normalized: Optional[Sequence[Dict[str, Any]]] = None,
    category_stats: Optional[Sequence[Dict[str, Any]]] = None,
) -> List[str]:
    if not records:
        return []

    bv_window = spec.range_windows.get('bv') if spec.range_windows else None
    ct_window = spec.range_windows.get('ctemp') if spec.range_windows else None

    if normalized is None:
        normalized = _normalize_records(records)
    if category_stats is None:
        category_stats = _collect_awb_category_stats(normalized)

    insights: List[str] = []
    insights.extend(_build_awb_category_summary(normalized, category_stats))
    insights.extend(_build_awb_layout_highlights(normalized, bv_window, ct_window, category_stats))
    return insights


def _build_awb_category_summary(
    normalized: Sequence[Dict[str, Any]],
    category_stats: Optional[Sequence[Dict[str, Any]]] = None,
) -> List[str]:
    if not normalized:
        return []

    if category_stats is None:
        category_stats = _collect_awb_category_stats(normalized)

    counts = {stat['label']: stat['count'] for stat in category_stats}

    lines: List[str] = []
    mix_labels = ['MixLight', 'HiMixLow', 'MidMixLow', 'LowMixHigh']
    mix_segments = [f"{label} {counts.get(label, 0)} 条" for label in mix_labels if counts.get(label, 0)]
    if mix_segments:
        lines.append(
            "- 混合光条目：" + "、".join(mix_segments) + "，通过多段 Mix 组合削弱高比重混合光统计点。"
        )

    store_labels = ['Special/门店', 'Starbucks']
    store_segments = [f"{label} {counts.get(label, 0)} 条" for label in store_labels if counts.get(label, 0)]
    if store_segments:
        lines.append(
            "- 门店/特定场景：" + "、".join(store_segments) + "，对华为/OPPO/咖啡店等暖光门店进行权重削减。"
        )

    color_labels = ['BlueMoment', 'Pure 色块', 'Sunset', 'BlueSky', 'BrightOutdoor', 'OutdoorScene', 'ExtremeLow']
    color_segments = [f"{label} {counts.get(label, 0)} 条" for label in color_labels if counts.get(label, 0)]
    if color_segments:
        lines.append(
            "- 色彩极端场景：" + "、".join(color_segments) + "，保持蓝调、极暖或高亮户外场景不过度拉动白点。"
        )

    greenzone_count = counts.get('GreenZone', 0)
    if greenzone_count:
        lines.append(
            f"- GreenZone 场景：GreenZone {greenzone_count} 条，重点压制低光绿区/人像的偏色统计点。"
        )

    face_count = counts.get('Face', 0)
    if face_count:
        lines.append(
            f"- 人像辅助：Face {face_count} 条，结合混合光条目在目标 BV 内守护肤色。"
        )

    return lines


_CATEGORY_DEFINITIONS: Tuple[Dict[str, Any], ...] = (
    {
        'label': 'GreenZone',
        'keywords': ('greenzone',),
        'description': '绿区/人像低光场景',
        'purpose': '压低绿区/人像的偏色统计点',
        'note_absent': True,
    },
    {
        'label': 'MixLight',
        'keywords': ('mixlight', 'mix_light'),
        'description': '多灯混合光段',
        'purpose': '削弱复杂混合光的高权重点',
        'note_absent': True,
    },
    {
        'label': 'HiMixLow',
        'keywords': ('himixlow', 'hi_mixlow', 'hi_mix_low'),
        'description': '高亮混合光',
        'purpose': '压制高亮混合光导致的色偏',
        'note_absent': True,
    },
    {
        'label': 'MidMixLow',
        'keywords': ('midmixlow', 'mid_mixlow', 'mid_mix_low'),
        'description': '中亮混合光',
        'purpose': '平衡中亮混合光的权重分布',
        'note_absent': True,
    },
    {
        'label': 'LowMixHigh',
        'keywords': ('lowmixhigh', 'low_mixhigh', 'low_mix_high'),
        'description': '低 BV 混合光',
        'purpose': '在低 BV 条件下保持混合光稳定',
        'note_absent': True,
    },
    {
        'label': 'Special/门店',
        'keywords': ('special', 'store', 'huaweistore', 'oppostore'),
        'description': '定制门店/特定环境',
        'purpose': '针对华为/OPPO 等门店暖光进行减权',
        'note_absent': True,
    },
    {
        'label': 'ExtremeLow',
        'keywords': ('extremelow', 'extreme_low'),
        'description': '极低色温场景',
        'purpose': '保护极低色温木质/暖光场景',
        'note_absent': True,
    },
    {
        'label': 'BlueMoment',
        'keywords': ('bluemoment',),
        'description': '蓝调/暮光场景',
        'purpose': '控制蓝调时刻的偏蓝拉动',
        'note_absent': True,
    },
    {
        'label': 'Pure 色块',
        'keywords': ('pureyellow', 'pureblue'),
        'description': '纯色块/广告屏',
        'purpose': '压制纯色广告屏等极端色块',
        'note_absent': True,
    },
    {
        'label': 'Sunset',
        'keywords': ('sunset',),
        'description': '日落暖色段',
        'purpose': '限制日落暖光偏红',
        'note_absent': True,
    },
    {
        'label': 'BlueSky',
        'keywords': ('bluesky', 'blue_sky'),
        'description': '蓝天高色温',
        'purpose': '约束蓝天高色温拉动',
        'note_absent': True,
    },
    {
        'label': 'BrightOutdoor',
        'keywords': ('brightoutdoor', 'bightoutdoor', 'bright_outdoor'),
        'description': '高亮户外',
        'purpose': '在户外高亮场景维持白点稳定',
        'note_absent': True,
    },
    {
        'label': 'OutdoorScene',
        'keywords': ('outdoorscene', 'outdoor_scene', 'outdoor'),
        'description': '泛户外场景',
        'purpose': '泛化户外光源的减权基线',
        'note_absent': True,
    },
    {
        'label': 'Starbucks',
        'keywords': ('starbucks',),
        'description': '咖啡店/Starbucks',
        'purpose': '应对咖啡店暖光',
        'note_absent': True,
    },
    {
        'label': 'Face',
        'keywords': ('face',),
        'description': '人像优先条目',
        'purpose': '与混合光条目配合守护肤色',
        'note_absent': False,
    },
)


def _normalize_records(records: Sequence[OffsetMapRecord]) -> List[Dict[str, Any]]:
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
    return normalized


def _collect_awb_category_stats(normalized: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    stats: List[Dict[str, Any]] = []
    for definition in _CATEGORY_DEFINITIONS:
        matches = [
            item
            for item in normalized
            if any(keyword in item['alias_lower'] or keyword in item['tag_lower'] for keyword in definition['keywords'])
        ]
        records = [item['record'] for item in matches]
        stats.append({
            'definition': definition,
            'label': definition['label'],
            'description': definition.get('description', ''),
            'purpose': definition.get('purpose', ''),
            'keywords': definition['keywords'],
            'count': len(matches),
            'records': records,
            'bv_span': _combine_ranges((item.get('bv') for item in matches)) if matches else (None, None),
            'ct_span': _combine_ranges((item.get('ctemp') for item in matches)) if matches else (None, None),
            'ir_span': _combine_ranges((item.get('ir') for item in matches)) if matches else (None, None),
            'weight_range': _format_weight_range(records),
            'map_list': _format_map_list(records),
        })
    return stats


def _build_overlap_summary_line(
    normalized: Sequence[Dict[str, Any]],
    bv_window: Optional[RangeWindow],
    ct_window: Optional[RangeWindow],
) -> Optional[str]:
    segments: List[str] = []
    if bv_window:
        overlaps = [
            _overlap_length(item.get('bv', (None, None)), bv_window)
            for item in normalized
        ]
        overlaps = [value for value in overlaps if value > 0]
        if overlaps:
            segments.append(
                f"BV 重叠中位 {_format_number(_median(overlaps))} EV（平均 {_format_number(_mean(overlaps))} EV）"
            )
    if ct_window:
        overlaps = [
            _overlap_length(item.get('ctemp', (None, None)), ct_window)
            for item in normalized
        ]
        overlaps = [value for value in overlaps if value > 0]
        if overlaps:
            segments.append(
                f"色温重叠中位 {_format_number(_median(overlaps))} K（平均 {_format_number(_mean(overlaps))} K）"
            )
    if not segments:
        return None
    return "- 区间交集：" + "，".join(segments) + "，说明大部分条目在目标窗口内具备实际重叠。"


def _build_category_overview_line(category_stats: Sequence[Dict[str, Any]]) -> Optional[str]:
    entries = [f"{stat['label']} {stat['count']} 条" for stat in category_stats if stat.get('count')]
    if not entries:
        return None
    return "- 类型覆盖：" + "、".join(entries) + "。"


def _build_awb_reduce_highlights(
    normalized: Sequence[Dict[str, Any]],
    category_stats: Sequence[Dict[str, Any]],
    bv_window: Optional[RangeWindow],
    ct_window: Optional[RangeWindow],
    ct_full: Sequence[OffsetMapRecord],
    bv_full: Sequence[OffsetMapRecord],
) -> List[str]:
    lines: List[str] = []
    counts = {stat['label']: stat['count'] for stat in category_stats}

    mix_labels = ['MixLight', 'HiMixLow', 'MidMixLow', 'LowMixHigh']
    mix_breakdown = [f"{label} {counts.get(label, 0)} 条" for label in mix_labels if counts.get(label, 0)]
    store_labels = ['Special/门店', 'Starbucks']
    store_breakdown = [f"{label} {counts.get(label, 0)} 条" for label in store_labels if counts.get(label, 0)]
    color_labels = ['BlueMoment', 'Pure 色块', 'Sunset', 'BlueSky', 'BrightOutdoor', 'OutdoorScene', 'ExtremeLow']
    color_breakdown = [f"{label} {counts.get(label, 0)} 条" for label in color_labels if counts.get(label, 0)]
    greenzone_count = counts.get('GreenZone', 0)
    face_count = counts.get('Face', 0)

    strategy_segments: List[str] = []
    if mix_breakdown:
        strategy_segments.append("混合光类 " + "、".join(mix_breakdown))
    if greenzone_count:
        strategy_segments.append(f"GreenZone {greenzone_count} 条")
    if face_count:
        strategy_segments.append(f"Face {face_count} 条")
    if store_breakdown:
        strategy_segments.append("门店/特定场景 " + "、".join(store_breakdown))
    if color_breakdown:
        strategy_segments.append("色彩极端 " + "、".join(color_breakdown))

    if strategy_segments:
        lines.append(
            "- 组合策略：" + "，".join(strategy_segments) + "，协同限制暖光、冷光与高 IR 场景的偏色干扰。"
        )

    if ct_window:
        full_count = len(ct_full)
        partial_overlaps = _collect_partial_overlaps(
            normalized,
            'ctemp',
            ct_window,
            {record.tag for record in ct_full},
        )
        coverage_parts: List[str] = []
        if full_count:
            coverage_parts.append(
                f"{full_count} 条（{_format_map_list(ct_full)}）完全覆盖 {_format_number(ct_window.lower)}–{_format_number(ct_window.upper)} K"
            )
        if partial_overlaps:
            coverage_parts.append(
                f"其余 {len(partial_overlaps)} 条色温重叠 {_format_overlap_range(partial_overlaps)} K"
            )
        if coverage_parts:
            lines.append(
                "- 色温覆盖：" + '；'.join(coverage_parts) + "，保证目标窗口内既有全段覆盖也有细粒度补充。"
            )

    if bv_window:
        full_count = len(bv_full)
        partial_overlaps = _collect_partial_overlaps(
            normalized,
            'bv',
            bv_window,
            {record.tag for record in bv_full},
        )
        coverage_parts: List[str] = []
        if full_count:
            coverage_parts.append(
                f"{full_count} 条（{_format_map_list(bv_full)}）完全覆盖 {_format_number(bv_window.lower)}–{_format_number(bv_window.upper)}"
            )
        if partial_overlaps:
            coverage_parts.append(
                f"其余 {len(partial_overlaps)} 条 BV 重叠 {_format_overlap_range(partial_overlaps)} EV"
            )
        if coverage_parts:
            lines.append(
                "- BV 覆盖：" + '；'.join(coverage_parts) + "，覆盖局部与全局亮度带的减权需求。"
            )

    absence_line = _build_category_absence_line(category_stats)
    if absence_line:
        lines.append(absence_line)

    return lines


def _describe_category_stat(
    stat: Dict[str, Any],
    bv_window: Optional[RangeWindow],
    ct_window: Optional[RangeWindow],
) -> Optional[str]:
    records = stat.get('records') or []
    if not records:
        return None

    label = stat.get('label', '')
    description = stat.get('description') or ''
    purpose = stat.get('purpose') or '削弱该类场景的偏色统计点'
    map_desc = _format_limited_map_list(records)

    line = f"- {label}"
    if description:
        line += f"（{description}）"
    if map_desc:
        line += f"：{map_desc}（共 {stat.get('count', len(records))} 条）"
    else:
        line += f"：共 {stat.get('count', len(records))} 条"

    weight_range = stat.get('weight_range') or '-'
    line += f"；权重 {weight_range}"

    span_parts = _format_category_span_parts(stat, bv_window, ct_window)
    if span_parts:
        line += '；' + '；'.join(span_parts)

    if purpose:
        line += f"；用于{purpose}"

    line += '。'
    return line


def _format_category_span_parts(
    stat: Dict[str, Any],
    bv_window: Optional[RangeWindow],
    ct_window: Optional[RangeWindow],
) -> List[str]:
    parts: List[str] = []
    bv_span = stat.get('bv_span')
    if bv_span and bv_span[0] is not None and bv_span[1] is not None:
        text = f"BV {_format_range_descriptor(bv_span)}"
        if bv_window:
            overlap = _overlap_length(bv_span, bv_window)
            if overlap > 0:
                text += f"（与目标重叠 {_format_number(overlap)} EV）"
        parts.append(text)

    ct_span = stat.get('ct_span')
    if ct_span and ct_span[0] is not None and ct_span[1] is not None:
        text = f"色温 {_format_range_descriptor(ct_span, 'K')}"
        if ct_window:
            overlap = _overlap_length(ct_span, ct_window)
            if overlap > 0:
                text += f"（与目标重叠 {_format_number(overlap)} K）"
        parts.append(text)

    ir_span = stat.get('ir_span')
    if ir_span and (ir_span[0] is not None or ir_span[1] is not None):
        parts.append(_format_ir_descriptor(ir_span))

    return parts


def _format_limited_map_list(records: Sequence[OffsetMapRecord], limit: int = 6) -> str:
    sorted_records = _sort_records(records)
    tags = [record.tag for record in sorted_records]
    if not tags:
        return ''
    if len(tags) > limit:
        return '、'.join(tags[:limit]) + f' 等 {len(tags)} 条'
    return '、'.join(tags)


def _build_category_absence_line(category_stats: Sequence[Dict[str, Any]]) -> Optional[str]:
    missing = [
        stat['label']
        for stat in category_stats
        if not stat.get('count') and stat.get('definition', {}).get('note_absent')
    ]
    if not missing:
        return None
    return "- 类型缺口：" + "、".join(missing) + " 类型在该窗口内暂未出现减权映射。"


def _collect_partial_overlaps(
    normalized: Sequence[Dict[str, Any]],
    axis: str,
    window: RangeWindow,
    exclude_tags: Sequence[str],
) -> List[float]:
    exclude = set(exclude_tags)
    overlaps: List[float] = []
    for item in normalized:
        record = item.get('record')
        tag = getattr(record, 'tag', None) if record else None
        if tag in exclude:
            continue
        bounds = item.get(axis, (None, None))
        overlap = _overlap_length(bounds, window)
        if overlap > 0:
            overlaps.append(overlap)
    return overlaps


def _format_overlap_range(values: Sequence[float]) -> str:
    if not values:
        return '-'
    lower = min(values)
    upper = max(values)
    if math.isclose(lower, upper, rel_tol=1e-6, abs_tol=1e-6):
        return _format_number(lower)
    return f"{_format_number(lower)}–{_format_number(upper)}"


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


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


def _build_awb_layout_highlights(
    normalized: Sequence[Dict[str, Any]],
    bv_window: Optional[RangeWindow],
    ct_window: Optional[RangeWindow],
    category_stats: Sequence[Dict[str, Any]],
) -> List[str]:
    if not normalized:
        return []

    insights: List[str] = []
    for stat in category_stats:
        if not stat.get('count'):
            continue
        line = _describe_category_stat(stat, bv_window, ct_window)
        if line:
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
