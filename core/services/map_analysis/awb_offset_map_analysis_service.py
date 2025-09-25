"""自动化生成 AWB offset map 深度分析报告的服务。"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

from utils.white_points import TEMPERATURE_ANCHORS


# --------------------------- 数据结构定义 ---------------------------


@dataclass
class OffsetMapAnalysisEntry:
    """单张 offset map 的分析结果。"""

    index: int
    tag: str
    alias: str
    primary_class: str
    scene_group: str
    map_enabled: bool
    vertex_count: int
    rpg_range: Optional[Tuple[float, float]]
    bpg_range: Optional[Tuple[float, float]]
    offset: Tuple[float, float]
    ml: Optional[int]
    weight: float
    mapping_label: str
    nearest_reference: Optional[str]
    reference_distance: Optional[float]
    centroid_distance: Optional[float]
    centroid: Optional[Tuple[float, float]]
    ranges: Dict[str, Tuple[Optional[float], Optional[float]]]

    @property
    def map_tag(self) -> str:
        return self.tag


class RangeAccumulator:
    """用于累计一组区间的工具。"""

    def __init__(self) -> None:
        self._min: Optional[float] = None
        self._max: Optional[float] = None

    def update(self, span: Tuple[Optional[float], Optional[float]]) -> None:
        if not span:
            return
        lower, upper = span
        if lower is None or upper is None:
            return
        if self._min is None or lower < self._min:
            self._min = lower
        if self._max is None or upper > self._max:
            self._max = upper

    @property
    def span(self) -> Tuple[Optional[float], Optional[float]]:
        return self._min, self._max


@dataclass
class SceneSummary:
    """室内 / 室外 / 夜景等大类的聚合统计。"""

    scene_group: str
    map_tags: List[str] = field(default_factory=list)
    map_indices: List[int] = field(default_factory=list)
    weights: List[float] = field(default_factory=list)
    ml_counter: Counter = field(default_factory=Counter)
    reference_counter: Counter = field(default_factory=Counter)
    primary_counter: Counter = field(default_factory=Counter)
    bv_accumulator: RangeAccumulator = field(default_factory=RangeAccumulator)
    ct_accumulator: RangeAccumulator = field(default_factory=RangeAccumulator)
    ir_accumulator: RangeAccumulator = field(default_factory=RangeAccumulator)

    def add_entry(self, entry: OffsetMapAnalysisEntry) -> None:
        self.map_tags.append(entry.map_tag)
        self.map_indices.append(entry.index)
        self.weights.append(entry.weight)
        if entry.ml is not None:
            self.ml_counter[entry.ml] += 1
        if entry.nearest_reference:
            self.reference_counter[entry.nearest_reference] += 1
        self.primary_counter[entry.primary_class] += 1
        self.bv_accumulator.update(entry.ranges.get("bv", (None, None)))
        self.ct_accumulator.update(entry.ranges.get("ctemp", (None, None)))
        self.ir_accumulator.update(entry.ranges.get("ir", (None, None)))

    @property
    def count(self) -> int:
        return len(self.map_tags)


@dataclass
class PrimaryClassSummary:
    """主类（如 BlueSky、MixLight）的聚合统计。"""

    primary_class: str
    map_tags: List[str] = field(default_factory=list)
    scene_counter: Counter = field(default_factory=Counter)
    weights: List[float] = field(default_factory=list)
    ml_counter: Counter = field(default_factory=Counter)
    reference_counter: Counter = field(default_factory=Counter)
    bv_accumulator: RangeAccumulator = field(default_factory=RangeAccumulator)
    ct_accumulator: RangeAccumulator = field(default_factory=RangeAccumulator)
    ir_accumulator: RangeAccumulator = field(default_factory=RangeAccumulator)

    def add_entry(self, entry: OffsetMapAnalysisEntry) -> None:
        self.map_tags.append(entry.map_tag)
        self.scene_counter[entry.scene_group] += 1
        self.weights.append(entry.weight)
        if entry.ml is not None:
            self.ml_counter[entry.ml] += 1
        if entry.nearest_reference:
            self.reference_counter[entry.nearest_reference] += 1
        self.bv_accumulator.update(entry.ranges.get("bv", (None, None)))
        self.ct_accumulator.update(entry.ranges.get("ctemp", (None, None)))
        self.ir_accumulator.update(entry.ranges.get("ir", (None, None)))

    @property
    def count(self) -> int:
        return len(self.map_tags)


@dataclass
class AwbOffsetMapReport:
    """完整的 offset map 分析报告。"""

    xml_path: Path
    entries: List[OffsetMapAnalysisEntry]
    scene_summaries: List[SceneSummary]
    class_summaries: List[PrimaryClassSummary]

    def to_markdown(self) -> str:
        """将分析结果转换为 Markdown 文本。"""

        lines: List[str] = []
        lines.append("# AWB Offset Map 自动分析报告")
        lines.append("")
        lines.append(f"- 数据来源：{self.xml_path.name}")
        lines.append(f"- Offset map 数量：{len(self.entries)}")
        lines.append("")
        lines.append("## 单张 offset map 逐项分析")
        lines.append("")

        for entry in self.entries:
            lines.extend(_render_entry(entry))

        lines.append("## 场景大类统计")
        lines.append("")
        for summary in self.scene_summaries:
            lines.extend(_render_scene_summary(summary))

        lines.append("## 主类分组统计")
        lines.append("")
        for summary in self.class_summaries:
            lines.extend(_render_primary_summary(summary))

        return "\n".join(lines).rstrip() + "\n"


# --------------------------- 核心服务实现 ---------------------------


class AwbOffsetMapAnalysisService:
    """读取 XML 并生成 AWB offset map 分析报告的数据服务。"""

    RANGE_FIELDS: Sequence[Tuple[str, str]] = (
        ("e_ratio", "e_ratio"),
        ("bv", "bv"),
        ("ctemp", "ctemp"),
        ("ir", "ir"),
        ("count", "count"),
        ("colorCCT", "colorCCT"),
        ("diffCtemp", "diffCtemp"),
        ("YLevel", "YLevel"),
        ("faceCtemp", "faceCtemp"),
    )

    SCENE_ORDER: Sequence[str] = ("室外", "室内", "夜景")

    def __init__(self, reference_points: Optional[Dict[str, Tuple[float, float]]] = None) -> None:
        self.reference_points = reference_points or TEMPERATURE_ANCHORS

    # ---- 对外接口 ----
    def analyze(self, xml_path: Path | str) -> AwbOffsetMapReport:
        path = Path(xml_path)
        root = ET.parse(path).getroot()

        entries: List[OffsetMapAnalysisEntry] = []
        for index in range(1, 117):
            formatted = f"{index:02d}" if index < 10 else str(index)
            tag = f"offset_map{formatted}"
            nodes = root.findall(f".//{tag}")
            if not nodes:
                continue

            primary_node = None
            meta_node = None
            for node in nodes:
                if primary_node is None and node.find("range") is not None:
                    primary_node = node
                if meta_node is None and node.find("AliasName") is not None:
                    meta_node = node

            if meta_node is None:
                # 缺少别名信息，跳过
                continue

            alias = (meta_node.findtext("AliasName") or tag).strip()
            map_enabled = _parse_bool(meta_node.findtext("MapEnabled"))
            num_vertices = _parse_int(meta_node.findtext("Num")) or 0
            rpg_values = _parse_float_list(meta_node.findtext("RpG"))
            bpg_values = _parse_float_list(meta_node.findtext("BpG"))

            offset_x, offset_y, weight, ml, ranges = self._extract_primary_attributes(primary_node)

            primary_class = _extract_primary_class(alias)
            scene_group = _classify_scene(alias, primary_class)

            rpg_range = _compute_range(rpg_values)
            bpg_range = _compute_range(bpg_values)
            centroid = _compute_centroid(rpg_values, bpg_values)
            centroid_distance = None
            if centroid is not None and math.isfinite(offset_x) and math.isfinite(offset_y):
                centroid_distance = math.hypot(offset_x - centroid[0], offset_y - centroid[1])

            nearest_reference, reference_distance = self._nearest_reference(offset_x, offset_y)
            mapping_label = _resolve_mapping_label(ml)

            entry = OffsetMapAnalysisEntry(
                index=index,
                tag=tag,
                alias=alias,
                primary_class=primary_class,
                scene_group=scene_group,
                map_enabled=map_enabled,
                vertex_count=num_vertices,
                rpg_range=rpg_range,
                bpg_range=bpg_range,
                offset=(offset_x, offset_y),
                ml=ml,
                weight=weight,
                mapping_label=mapping_label,
                nearest_reference=nearest_reference,
                reference_distance=reference_distance,
                centroid_distance=centroid_distance,
                centroid=centroid,
                ranges=ranges,
            )
            entries.append(entry)

        entries.sort(key=lambda item: item.index)

        scene_summaries = self._build_scene_summaries(entries)
        class_summaries = self._build_primary_summaries(entries)

        return AwbOffsetMapReport(path, entries, scene_summaries, class_summaries)

    # ---- 内部实现 ----
    def _extract_primary_attributes(
        self, primary_node: Optional[ET.Element]
    ) -> Tuple[float, float, float, Optional[int], Dict[str, Tuple[Optional[float], Optional[float]]]]:
        if primary_node is None:
            return 0.0, 0.0, 0.0, None, {}

        offset_node = primary_node.find("offset")
        offset_x = _parse_float(offset_node.findtext("x")) if offset_node is not None else 0.0
        offset_y = _parse_float(offset_node.findtext("y")) if offset_node is not None else 0.0
        weight = _parse_float(primary_node.findtext("weight")) or 0.0

        range_node = primary_node.find("range")
        ml = None
        ranges: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
        if range_node is not None:
            ml_text = range_node.findtext("ml")
            if ml_text is not None:
                try:
                    ml = int(float(ml_text))
                except ValueError:
                    ml = None

            for xml_name, key in self.RANGE_FIELDS:
                node = range_node.find(xml_name)
                if node is None:
                    continue
                lower = _parse_float(node.findtext("min"))
                upper = _parse_float(node.findtext("max"))
                ranges[key] = (lower, upper)

        return offset_x, offset_y, weight, ml, ranges

    def _nearest_reference(self, x: float, y: float) -> Tuple[Optional[str], Optional[float]]:
        best_name: Optional[str] = None
        best_distance: Optional[float] = None
        for name, (ref_x, ref_y) in self.reference_points.items():
            distance = math.hypot(x - ref_x, y - ref_y)
            if best_distance is None or distance < best_distance:
                best_name = name
                best_distance = distance
        return best_name, best_distance

    def _build_scene_summaries(self, entries: Sequence[OffsetMapAnalysisEntry]) -> List[SceneSummary]:
        summaries: Dict[str, SceneSummary] = {}
        for entry in entries:
            summary = summaries.setdefault(entry.scene_group, SceneSummary(entry.scene_group))
            summary.add_entry(entry)

        ordered: List[SceneSummary] = []
        for name in self.SCENE_ORDER:
            if name in summaries:
                ordered.append(summaries.pop(name))
        # 将未识别的场景放在最后
        ordered.extend(sorted(summaries.values(), key=lambda item: item.scene_group))
        return ordered

    def _build_primary_summaries(self, entries: Sequence[OffsetMapAnalysisEntry]) -> List[PrimaryClassSummary]:
        summaries: Dict[str, PrimaryClassSummary] = {}
        for entry in entries:
            summary = summaries.setdefault(entry.primary_class, PrimaryClassSummary(entry.primary_class))
            summary.add_entry(entry)

        return [summaries[key] for key in sorted(summaries.keys())]


# --------------------------- Markdown 渲染 ---------------------------


def _render_entry(entry: OffsetMapAnalysisEntry) -> List[str]:
    lines: List[str] = []
    lines.append(f"### {entry.tag} — {entry.alias}")

    scene_note = f"- 场景标签：{entry.alias}（主类 {entry.primary_class}，归类为{entry.scene_group}场景"
    if not entry.map_enabled:
        scene_note += "，amapParam 标记为未启用"
    scene_note += "）"
    lines.append(scene_note)

    lines.append(
        "- 几何覆盖：{count} 个顶点；RpG 范围 {rpg}；BpG 范围 {bpg}".format(
            count=entry.vertex_count,
            rpg=_format_range(entry.rpg_range),
            bpg=_format_range(entry.bpg_range),
        )
    )

    target_parts = [
        f"- 目标坐标：({_format_coord(entry.offset[0])}, {_format_coord(entry.offset[1])})",
    ]
    if entry.nearest_reference:
        ref_text = entry.nearest_reference
        if entry.reference_distance is not None:
            ref_text += f"（距离 {_format_distance(entry.reference_distance)}）"
        target_parts.append(f"最近参考白点 {ref_text}")
    if entry.mapping_label:
        target_parts.append(entry.mapping_label)
    target_parts.append(f"权重 {_format_weight(entry.weight)}")
    lines.append("，".join(target_parts))

    if entry.centroid_distance is not None:
        lines.append(f"- **额外观察**：从多边形质心拉动距离≈{_format_distance(entry.centroid_distance)}")

    trigger_segments = []
    for key, label in (
        ("e_ratio", "e_ratio"),
        ("bv", "BV"),
        ("ctemp", "CT"),
        ("ir", "IR"),
        ("count", "Count"),
        ("colorCCT", "ColorCT"),
        ("diffCtemp", "DiffCT"),
        ("YLevel", "Y"),
        ("faceCtemp", "FaceCT"),
    ):
        span = entry.ranges.get(key)
        if span is None:
            continue
        trigger_segments.append(f"{label}[{_format_trigger_span(span)}]")
    if trigger_segments:
        lines.append("- 触发条件：" + "；".join(trigger_segments))
    else:
        lines.append("- 触发条件：-")

    lines.append("")
    return lines


def _render_scene_summary(summary: SceneSummary) -> List[str]:
    lines: List[str] = []
    lines.append(f"### {summary.scene_group}")
    lines.append(
        f"- Map 数量：{summary.count}（{_format_map_list(summary.map_tags)}）"
    )
    if summary.weights:
        weight_range = (_safe_min(summary.weights), _safe_max(summary.weights))
        average_weight = sum(summary.weights) / len(summary.weights)
        lines.append(
            "- 权重范围：{rng}；平均权重≈{avg}".format(
                rng=_format_range(weight_range),
                avg=_format_weight(average_weight),
            )
        )
    ml_text = _format_counter(summary.ml_counter, {65471: "ml=65471", 65535: "ml=65535"})
    if ml_text:
        lines.append(f"- 映射策略：{ml_text}")
    ref_text = _format_counter(summary.reference_counter)
    if ref_text:
        lines.append(f"- 参考白点分布：{ref_text}")
    primary_text = _format_counter(summary.primary_counter)
    if primary_text:
        lines.append(f"- 主类分布：{primary_text}")

    bv_range = summary.bv_accumulator.span
    ct_range = summary.ct_accumulator.span
    ir_range = summary.ir_accumulator.span
    lines.append(
        "- 触发区间：BV{bv}；CT{ct}；IR{ir}".format(
            bv=_format_range(bv_range),
            ct=_format_range(ct_range),
            ir=_format_range(ir_range),
        )
    )
    lines.append("")
    return lines


def _render_primary_summary(summary: PrimaryClassSummary) -> List[str]:
    lines: List[str] = []
    lines.append(f"### {summary.primary_class}")
    lines.append(
        f"- Map 数量：{summary.count}（{_format_map_list(summary.map_tags)}）"
    )
    scene_text = _format_counter(summary.scene_counter)
    if scene_text:
        lines.append(f"- 覆盖场景分类：{scene_text}")
    if summary.weights:
        weight_range = (_safe_min(summary.weights), _safe_max(summary.weights))
        average_weight = sum(summary.weights) / len(summary.weights)
        lines.append(
            "- 权重范围：{rng}；平均权重≈{avg}".format(
                rng=_format_range(weight_range),
                avg=_format_weight(average_weight),
            )
        )
    ml_text = _format_counter(summary.ml_counter, {65471: "ml=65471", 65535: "ml=65535"})
    if ml_text:
        lines.append(f"- 映射策略：{ml_text}")
    ref_text = _format_counter(summary.reference_counter)
    if ref_text:
        lines.append(f"- 参考白点倾向：{ref_text}")
    lines.append(
        "- 典型触发区间：BV{bv}；CT{ct}；IR{ir}".format(
            bv=_format_range(summary.bv_accumulator.span),
            ct=_format_range(summary.ct_accumulator.span),
            ir=_format_range(summary.ir_accumulator.span),
        )
    )
    lines.append("")
    return lines


# --------------------------- 辅助函数 ---------------------------


def _extract_primary_class(alias: str) -> str:
    trimmed = alias.lstrip("0123456789_")
    if not trimmed:
        return alias or "未知"
    return trimmed.split("_")[0] or alias


def _classify_scene(alias: str, primary_class: str) -> str:
    alias_lower = alias.lower()
    primary_lower = primary_class.lower()

    if "night" in alias_lower or primary_lower.startswith("night"):
        return "夜景"

    indoor_keywords = (
        "indoor",
        "mixlight",
        "mixlowmixhi",
        "midmixlow",
        "midmidxlow",
        "special",
    )
    if any(keyword in alias_lower for keyword in indoor_keywords) or any(
        primary_lower.startswith(keyword)
        for keyword in ("indoor", "mixlight", "mixlowmixhi", "midmixlow", "midmidxlow", "special")
    ):
        return "室内"

    return "室外"


def _parse_float(text: Optional[str]) -> Optional[float]:
    if text is None:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _parse_int(text: Optional[str]) -> Optional[int]:
    if text is None:
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _parse_bool(text: Optional[str]) -> bool:
    if text is None:
        return True
    stripped = text.strip().lower()
    return stripped not in {"0", "false", "no"}


def _parse_float_list(text: Optional[str]) -> List[float]:
    if not text:
        return []
    values: List[float] = []
    for part in text.split():
        try:
            values.append(float(part))
        except ValueError:
            continue
    return values


def _compute_range(values: Sequence[float]) -> Optional[Tuple[float, float]]:
    if not values:
        return None
    return min(values), max(values)


def _compute_centroid(
    rpg_values: Sequence[float],
    bpg_values: Sequence[float],
) -> Optional[Tuple[float, float]]:
    if not rpg_values or not bpg_values:
        return None
    if len(rpg_values) != len(bpg_values):
        return None
    count = len(rpg_values)
    return (
        sum(rpg_values) / count,
        sum(bpg_values) / count,
    )


def _resolve_mapping_label(ml: Optional[int]) -> str:
    if ml == 65471:
        return "强拉至单点"
    if ml == 65535:
        return "整体位移"
    if ml is None:
        return ""
    return f"ml={ml}"


def _format_number(value: Optional[float], digits: int = 4) -> str:
    if value is None or not math.isfinite(value):
        return "-"
    if abs(value) >= 1000 or value.is_integer():
        return str(int(round(value)))
    formatted = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return formatted if formatted else "0"


def _format_range(span: Optional[Tuple[Optional[float], Optional[float]]]) -> str:
    if not span:
        return "-"
    lower, upper = span
    return f"{_format_number(lower)}–{_format_number(upper)}"


def _format_coord(value: float) -> str:
    return _format_number(value, digits=4)


def _format_distance(value: Optional[float]) -> str:
    return _format_number(value, digits=4)


def _format_weight(value: float) -> str:
    return _format_number(value, digits=3)


def _format_trigger_span(span: Tuple[Optional[float], Optional[float]]) -> str:
    lower, upper = span
    return f"{_format_number(lower)},{_format_number(upper)}"


def _format_map_list(map_tags: Sequence[str]) -> str:
    if not map_tags:
        return "-"
    return "、".join(map_tags)


def _format_counter(counter: Counter, label_map: Optional[Dict[int, str]] = None) -> str:
    if not counter:
        return ""
    items = counter.most_common()
    segments: List[str] = []
    for key, count in items:
        label = label_map.get(key) if label_map else str(key)
        segments.append(f"{label}×{count}")
    return "、".join(segments)


def _safe_min(values: Iterable[float]) -> Optional[float]:
    try:
        return min(values)
    except ValueError:
        return None


def _safe_max(values: Iterable[float]) -> Optional[float]:
    try:
        return max(values)
    except ValueError:
        return None


