"""
AWB Stats 解析与点集接口

职责：
- 将 scripts/parse_awb_stats.py 的解析逻辑抽象为可复用的工具函数
- 对外暴露统一接口，供 GUI 在拖入图片时提取并绘制统计点（RpG,BpG）

注意：
- 遵循项目结构：工具类放置于 utils/；不引入 UI 依赖。
- 仅负责解析与数据组织，不负责绘制。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Literal, Dict, Any
import json
import struct

# 允许 GUI 侧调用 EXIF 解析服务以从图片拿 JSON
# 注意：ExifParserService 依赖较多（包含 PyQt5 侧模块），避免顶层导入导致脚本环境缺失依赖。
# 在需要从图片提取时再延迟导入。

APS_NODE = b"QTI Debug Metadata"


@dataclass(frozen=True)
class StatsPoint:
    """单个统计点（块）"""
    rpg: float
    bpg: float
    rpg_otp: float
    bpg_otp: float
    weight: Optional[int] = None
    is_skin: Optional[bool] = None


@dataclass(frozen=True)
class StatsPointSet:
    """统计点集合，作为 GUI 的绘制输入。"""
    rows: int
    cols: int
    bit_depth: int
    platform: Literal['QC', 'MTK']
    correct_coef_rpg: float
    correct_coef_bpg: float
    points: List[StatsPoint]

    def to_xy(self, corrected: bool = True) -> List[Tuple[float, float]]:
        """以 (x=RpG, y=BpG) 返回散点坐标。

        Args:
            corrected: True 返回 OTP 修正后的 (rpg_otp, bpg_otp)，False 返回原始 (rpg, bpg)
        """
        if corrected:
            return [(p.rpg_otp, p.bpg_otp) for p in self.points]
        return [(p.rpg, p.bpg) for p in self.points]


def _remove_aps_nodes(data: bytes) -> bytes:
    """移除内嵌 APS 节点，行为与 C++ removeAPSNode 对齐。"""
    while True:
        pos = data.find(APS_NODE)
        if pos == -1:
            break
        if pos >= 4:
            start = pos - 4
            end = start + 23
            data = data[:start] + data[end:]
        else:
            data = data.replace(APS_NODE, b"")
    return data


def _parse_from_json_obj(d: Dict[str, Any]) -> StatsPointSet:
    rows = int(d["face_info"]["stats_info_row"])
    cols = int(d["face_info"]["stats_info_col"])
    bit_depth = int(d.get("stats_weight", {}).get("bitDepth", d["face_info"]["stats_info_bitDepth"]))
    platform_type = int(d.get("stats_weight", {}).get("platform_type", 0))
    cr = float(d.get("unit_data", {}).get("correctCoefRpG", 1.0))
    cb = float(d.get("unit_data", {}).get("correctCoefBpG", 1.0))
    weights = d.get("stats_weight", {}).get("fStatsWeight")
    is_skin = d.get("face_info", {}).get("isSkinBlock")

    raw_arr = d.get("StatsData")
    if not isinstance(raw_arr, list):
        raise ValueError("JSON 缺少 StatsData 数组")
    # 兼容有符号字节
    stats_bytes = bytes(((x + 256) % 256) for x in raw_arr)
    stats_bytes = _remove_aps_nodes(stats_bytes)

    n_blocks = rows * cols
    qc_len = n_blocks * 16
    mtk_len = n_blocks * 8
    if len(stats_bytes) == qc_len:
        platform: Literal['QC', 'MTK'] = 'QC'
        fmt = "<IIII"
        step = 16
    elif len(stats_bytes) == mtk_len:
        platform = 'MTK'
        fmt = "<HHHH"
        step = 8
    else:
        if platform_type == 0:
            platform = 'QC'
            fmt = "<IIII"
            step = 16
            if len(stats_bytes) < qc_len:
                raise ValueError(f"StatsData 长度不足 QC: {len(stats_bytes)} < {qc_len}")
        else:
            platform = 'MTK'
            fmt = "<HHHH"
            step = 8
            if len(stats_bytes) < mtk_len:
                raise ValueError(f"StatsData 长度不足 MTK: {len(stats_bytes)} < {mtk_len}")

    unpack = struct.Struct(fmt).unpack_from
    points: List[StatsPoint] = []
    idx = 0
    for _ in range(rows):
        for _ in range(cols):
            off = idx * step
            R, G, B, Y = unpack(stats_bytes, off)
            if G > 0:
                rpg = R / G
                bpg = B / G
            else:
                rpg = 0.0
                bpg = 0.0
            p = StatsPoint(
                rpg=rpg,
                bpg=bpg,
                rpg_otp=rpg * cr,
                bpg_otp=bpg * cb,
                weight=(int(weights[idx]) if isinstance(weights, list) and idx < len(weights) else None),
                is_skin=(bool(is_skin[idx]) if isinstance(is_skin, list) and idx < len(is_skin) else None),
            )
            points.append(p)
            idx += 1

    return StatsPointSet(
        rows=rows,
        cols=cols,
        bit_depth=bit_depth,
        platform=platform,
        correct_coef_rpg=cr,
        correct_coef_bpg=cb,
        points=points,
    )


def parse_awb_stats_from_json_file(json_path: str | Path) -> StatsPointSet:
    """从 AWB JSON 文件解析统计点集。"""
    p = Path(json_path)
    with p.open('rb') as f:
        data = json.load(f)
    return _parse_from_json_obj(data)


def extract_awb_stats_from_image(image_path: str | Path) -> Optional[StatsPointSet]:
    """从图片中提取 AWB EXIF 并解析统计点集。

    返回 None 表示解析失败或不包含 AWB 数据。
    """
    try:
        from core.services.exif_processing.exif_parser_service import ExifParserService
        svc = ExifParserService()
        raw = svc._read_raw_exif(Path(image_path))
        if not isinstance(raw, dict) or not raw:
            return None
        return _parse_from_json_obj(raw)
    except Exception:
        return None


def get_stats_points(image_or_json_path: str | Path) -> Optional[StatsPointSet]:
    """统一入口：传入 JPG/JSON 路径，返回 StatsPointSet。"""
    p = Path(image_or_json_path)
    if p.suffix.lower() in ('.json',):
        return parse_awb_stats_from_json_file(p)
    # 视为图片
    return extract_awb_stats_from_image(p)
