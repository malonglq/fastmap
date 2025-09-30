"""
解析 AWB JSON 中的 StatsData，复现 stats数据计算.cpp 的关键行为：
- 从 JSON 读取 StatsData（字节数组）、rows/cols、bitDepth、platform_type、unit2unit 修正系数、权重、肤色块标记。
- 去除内嵌的 "QTI Debug Metadata" 片段（与 C++ 中 removeAPSNode 一致：从命中位置往前 4 字节起，删除 23 字节）。
- 自动判定 QC(4x uint32) 或 MTK(4x uint16) 布局并逐块解析 (R,G,B,Y)。
- 计算 RpG、BpG 以及 OTP 修正后的 rpg_otp、bpg_otp；安全处理 G=0。

用法示例：
python scripts/parse_awb_stats.py tests/test_data/101_Swangoose_IMG20250101230435_awb.json --limit 5

输出：
- 头部元信息：平台、尺寸、bitDepth、样本总数
- 前 N 个块的 (row,col) 及 R,G,B,Y、RpG、BpG、rpg_otp、bpg_otp、权重、是否肤色块

注意：
- 本脚本默认不做亮/暗/饱和阈值筛选，仅做原始解析与比值计算，方便后续算法对接。
- 若需要开启阈值筛选，可按 stats数据计算.cpp 的 OpAwb_GetLevelGateThreshold 公式自行扩展。
"""

from __future__ import annotations

import argparse
import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


APS_NODE = b"QTI Debug Metadata"


@dataclass(frozen=True)
class BlockStat:
    row: int
    col: int
    R: int
    G: int
    B: int
    Y: int
    rpg: float
    bpg: float
    rpg_otp: float
    bpg_otp: float
    weight: int | None
    is_skin: bool | None


@dataclass(frozen=True)
class StatsParseResult:
    rows: int
    cols: int
    bit_depth: int
    platform: str  # "QC" or "MTK"
    correct_coef_rpg: float
    correct_coef_bpg: float
    blocks: List[BlockStat]


def _remove_aps_nodes(data: bytes) -> bytes:
    """去除内嵌的 APS 节点，与 C++ removeAPSNode 行为一致。

    C++ 逻辑：
        int slice_pos = log.indexOf(APS_NODE);
        if (slice_pos >= 4) {
            log = log.remove(slice_pos - 4, 23); // 23 字节
            removeAPSNode(log);
        }
    这里用 while 循环实现相同效果。
    """
    while True:
        pos = data.find(APS_NODE)
        if pos == -1:
            break
        if pos >= 4:
            # 从 pos-4 起删 23 字节
            start = pos - 4
            end = start + 23
            data = data[:start] + data[end:]
        else:
            # 防御：若异常位置，直接删除命中的标记字符串
            data = data.replace(APS_NODE, b"")
    return data


def parse_awb_stats(json_path: str | Path) -> StatsParseResult:
    """从 AWB JSON 文件解析 stats 数据并计算 RpG/BpG 与 OTP 修正。

    返回 StatsParseResult，其中 blocks 为逐块数据，顺序为 i 行 j 列（row-major）。
    """
    p = Path(json_path)
    with p.open("rb") as f:
        d = json.load(f)

    rows = int(d["face_info"]["stats_info_row"])  # 例如 48
    cols = int(d["face_info"]["stats_info_col"])  # 例如 64
    bit_depth = int(d.get("stats_weight", {}).get("bitDepth", d["face_info"]["stats_info_bitDepth"]))
    platform_type = int(d.get("stats_weight", {}).get("platform_type", 0))
    # unit2unit 修正系数（若缺省则为 1.0）
    correct_coef_rpg = float(d.get("unit_data", {}).get("correctCoefRpG", 1.0))
    correct_coef_bpg = float(d.get("unit_data", {}).get("correctCoefBpG", 1.0))

    # 权重与肤色标记（若缺省则用 None 填充）
    weights = d.get("stats_weight", {}).get("fStatsWeight")
    is_skin = d.get("face_info", {}).get("isSkinBlock")

    # StatsData: 字节数组（list[int] 0..255）
    # StatsData 可能是 int8（-128..127）形式，需转换为无符号字节
    stats_bytes = bytes(((x + 256) % 256) for x in d["StatsData"]) 
    stats_bytes = _remove_aps_nodes(stats_bytes)

    # 自动判定布局：优先依据净长度匹配
    n_blocks = rows * cols
    qc_len = n_blocks * 16  # 4 x uint32
    mtk_len = n_blocks * 8  # 4 x uint16
    platform: str
    if len(stats_bytes) == qc_len:
        platform = "QC"
        fmt = "<IIII"  # little-endian 4 x uint32
        step = 16
    elif len(stats_bytes) == mtk_len:
        platform = "MTK"
        fmt = "<HHHH"  # little-endian 4 x uint16
        step = 8
    else:
        # 回退到 platform_type 判断（0 视为 QC，1 视为 MTK），并尽量容错
        if platform_type == 0:
            platform = "QC"
            fmt = "<IIII"
            step = 16
            if len(stats_bytes) < qc_len:
                raise ValueError(f"StatsData 长度不足以解析 QC：{len(stats_bytes)} < {qc_len}")
        else:
            platform = "MTK"
            fmt = "<HHHH"
            step = 8
            if len(stats_bytes) < mtk_len:
                raise ValueError(f"StatsData 长度不足以解析 MTK：{len(stats_bytes)} < {mtk_len}")

    blocks: List[BlockStat] = []
    unpack = struct.Struct(fmt).unpack_from

    # 逐块解析（行优先）
    idx = 0
    for i in range(rows):
        for j in range(cols):
            off = idx * step
            R, G, B, Y = unpack(stats_bytes, off)
            # 安全计算比值
            if G > 0:
                rpg = R / G
                bpg = B / G
            else:
                rpg = 0.0
                bpg = 0.0
            rpg_otp = rpg * correct_coef_rpg
            bpg_otp = bpg * correct_coef_bpg

            w = int(weights[idx]) if isinstance(weights, list) and idx < len(weights) else None
            skin = bool(is_skin[idx]) if isinstance(is_skin, list) and idx < len(is_skin) else None

            blocks.append(
                BlockStat(
                    row=i,
                    col=j,
                    R=int(R),
                    G=int(G),
                    B=int(B),
                    Y=int(Y),
                    rpg=float(rpg),
                    bpg=float(bpg),
                    rpg_otp=float(rpg_otp),
                    bpg_otp=float(bpg_otp),
                    weight=w,
                    is_skin=skin,
                )
            )
            idx += 1

    return StatsParseResult(
        rows=rows,
        cols=cols,
        bit_depth=bit_depth,
        platform=platform,
        correct_coef_rpg=correct_coef_rpg,
        correct_coef_bpg=correct_coef_bpg,
        blocks=blocks,
    )


def _print_summary(res: StatsParseResult, limit: int = 5) -> None:
    print("Meta:")
    print(f"  platform     = {res.platform}")
    print(f"  size         = {res.rows} x {res.cols} (blocks={res.rows*res.cols})")
    print(f"  bitDepth     = {res.bit_depth}")
    print(f"  correctCoef  = (RpG={res.correct_coef_rpg:.6f}, BpG={res.correct_coef_bpg:.6f})")

    print("Examples:")
    for k, b in enumerate(res.blocks[: max(0, limit) ]):
        print(
            f"  #{k:02d} (r{b.row},c{b.col}) R={b.R} G={b.G} B={b.B} Y={b.Y} "
            f"RpG={b.rpg:.6f} BpG={b.bpg:.6f} rpg_otp={b.rpg_otp:.6f} bpg_otp={b.bpg_otp:.6f} "
            f"W={b.weight} skin={b.is_skin}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="解析 AWB JSON 的 StatsData 并打印摘要")
    parser.add_argument("input", help="AWB JSON 路径")
    parser.add_argument("--limit", type=int, default=5, help="预览前 N 个块")
    args = parser.parse_args()

    res = parse_awb_stats(args.input)
    _print_summary(res, args.limit)


if __name__ == "__main__":
    main()
