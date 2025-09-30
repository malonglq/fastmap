"""
AWB AGW_Gray_way 计算与调参辅助脚本（对齐 AwbCore 的块级积分模型）。

功能概要
- 支持“多簇统计点”输入，按簇复现 AwbCore 中三路（offset、dist、原始路）加权积分，输出最终 `AGW_Gray_way`。
- 变量命名与 AwbCore/文档一致：`offsetMapTarget`、`blockDistTarget`、`fOffsetWeight`、`fOffsetTargetWeight`、`fDistTargetWeight`、`oriConfidenceMin`、`integralWeight` 等。
- 可通过 `--offset-apply-indices` 指定 offset 仅作用于部分簇（未指定则作用于全部）。
- 默认 dist 路为 0，但保留 dist 项，可按需开启。

计算要点（逐簇）
- 对簇 i：
  - 生效权重：`fOffsetTargetWeight_i = fOffsetTargetWeight_base` 或 0（取决于是否在 `--offset-apply-indices` 中）。
  - 原始保底：`oriConfidenceMin_i = max(0, 1 - fOffsetTargetWeight_i / fOffsetWeight)`（化简近似，fOriBaseW=OriBlockWeight=1）。
  - 映射分子：`tempRpG_i = offsetMapTarget.RpG*fOffsetTargetWeight_i + blockDistTarget.RpG*fDistTargetWeight`；`tempBpG_i` 同理。
  - 映射权重：`tempWeight_i = fOffsetTargetWeight_i + fDistTargetWeight`。
  - 块级累加：
    - `integral.RpG += count_i * (tempRpG_i + block_i.RpG * oriConfidenceMin_i)`
    - `integral.BpG += count_i * (tempBpG_i + block_i.BpG * oriConfidenceMin_i)`
    - `integralWeight += count_i * (tempWeight_i + oriConfidenceMin_i)`
- 归一：`AGW_Gray_way = (integral.RpG/integralWeight, integral.BpG/integralWeight)`。
- 额外打印：每簇的 `fOffsetTargetWeight_i`、`oriConfidenceMin_i`、`tempWeight_i`、`IntegralWeight_i_i` 与该簇局部灰点 `clusterGray`（仅该簇存在时的等效结果）。

默认行为
- 未提供 `--stats` 时，自动构造一个簇：`count=3072`、坐标取 `--agw-nomap`，复现单簇化简。

常用示例
- 单簇（默认等价旧逻辑）
python scripts/compute_agw_gray_way.py --agw-nomap 0.47406 0.540894 --offset-target 0.3 0.8 --f-offset-weight 0.2 --f-offset-target-weight 0.1

- 两簇且仅作用于第二簇
python scripts/compute_agw_gray_way.py --stats 1536,0.2,0.8 --stats 1536,0.4,0.6 --offset-target 0.3 0.8 --f-offset-weight 0.2 --f-offset-target-weight 0.1 --offset-apply-indices 1

- 开启 dist 路（可与上面组合）
python scripts/compute_agw_gray_way.py --stats 1536,0.2,0.8 --stats 1536,0.4,0.6 --offset-target 0.3 0.8 --block-dist-target 0.45 0.58 --f-dist-target-weight 0.05 --f-offset-weight 0.2 --f-offset-target-weight 0.1
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
from typing import List, Optional
from pathlib import Path
import sys

# 确保脚本可直接导入仓库内模块（如 utils.awb_stats_tools）
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@dataclass(frozen=True)
class SOpAwb_ColorSpace:
    """与 AwbCore 中 `SOpAwb_ColorSpace` 对齐的简化数据结构。
    - RpG: R/G 比率
    - BpG: B/G 比率
    """
    RpG: float
    BpG: float


@dataclass(frozen=True)
class StatsCluster:
    """统计点簇（等价于一组重复的 block）。
    - count: 该簇统计块数量
    - block: 原始块坐标（与 AwbCore 中 `block` 对应）
    """
    count: int
    block: SOpAwb_ColorSpace


def compute_agw_gray_way_with_stats(
    stats: List[StatsCluster],
    offsetMapTarget: SOpAwb_ColorSpace,
    fOffsetWeight: float,
    fOffsetTargetWeight_base: float,
    blockDistTarget: SOpAwb_ColorSpace,
    fDistTargetWeight: float,
    offset_apply_mask: List[bool] | None = None,
    verbose: bool = True,
) -> tuple[SOpAwb_ColorSpace, SOpAwb_ColorSpace, float]:

    if fOffsetWeight == 0:
        raise ValueError("fOffsetWeight 不能为 0")

    integralRpG = 0.0
    integralBpG = 0.0
    integralWeight = 0.0

    if verbose:
        print("Inputs (documented names, stats mode):")

    # 额外计算 NoMap 的加权均值（统计点整体的均值）
    total_count = 0
    sum_r = 0.0
    sum_b = 0.0

    if offset_apply_mask is None:
        offset_apply_mask = [True] * len(stats)

    # 打印每簇基础输入
    for idx, sc in enumerate(stats):
        if verbose and idx < 50:
            print(f"  stats[{idx}]: count={sc.count}, block=({sc.block.RpG:.6f}, {sc.block.BpG:.6f})")
        elif verbose and idx == 50:
            print("  ... (省略后续统计点日志，使用 --no-cluster-log 可完全关闭)")
        # 打印全局输入
    if verbose:
        print(f"  offsetMapTarget      = ({offsetMapTarget.RpG:.6f}, {offsetMapTarget.BpG:.6f})")
        print(f"  blockDistTarget      = ({blockDistTarget.RpG:.6f}, {blockDistTarget.BpG:.6f})")
        print(f"  fOffsetWeight        = {fOffsetWeight:g}")
        print(f"  fOffsetTargetWeight  = {fOffsetTargetWeight_base:g}")
        print(f"  fDistTargetWeight    = {fDistTargetWeight:g}")
        if all(offset_apply_mask):
            print("  offset apply indices = all")
        else:
            active = ",".join(str(i) for i, v in enumerate(offset_apply_mask) if v)
            print(f"  offset apply indices = {active}")

    for idx, sc in enumerate(stats):
        cnt = sc.count
        block = sc.block
        total_count += cnt
        sum_r += block.RpG * cnt
        sum_b += block.BpG * cnt

        # 针对该簇决定 offset 是否生效
        fOffsetTargetWeight_i = fOffsetTargetWeight_base if offset_apply_mask[idx] else 0.0

        # 该簇对应的映射分子与权重
        tempRpG_i = offsetMapTarget.RpG * fOffsetTargetWeight_i + blockDistTarget.RpG * fDistTargetWeight
        tempBpG_i = offsetMapTarget.BpG * fOffsetTargetWeight_i + blockDistTarget.BpG * fDistTargetWeight
        tempWeight_i = fOffsetTargetWeight_i + fDistTargetWeight

        # 该簇的原始路保底权重（简化）
        oriConfidenceMin_i = max(0.0, 1.0 - (fOffsetTargetWeight_i / fOffsetWeight))
        # 该簇积分权重（对齐 AwbCore 块级分母项）
        IntegralWeight_i = tempWeight_i + oriConfidenceMin_i

        # 该簇的“贡献灰点”（等价于仅该簇存在时的 AGW 局部结果）
        final_weight = tempWeight_i + oriConfidenceMin_i
        if final_weight > 0:
            AGW_Gray_RpG_i = (block.RpG * oriConfidenceMin_i + tempRpG_i) / final_weight
            AGW_Gray_BpG_i = (block.BpG * oriConfidenceMin_i + tempBpG_i) / final_weight
        else:
            AGW_Gray_RpG_i = float('nan')
            AGW_Gray_BpG_i = float('nan')

        # 将该簇计入积分（按 AwbCore 的块级累加）
        integralRpG += cnt * (tempRpG_i + block.RpG * oriConfidenceMin_i)
        integralBpG += cnt * (tempBpG_i + block.BpG * oriConfidenceMin_i)
        integralWeight += cnt * (tempWeight_i + oriConfidenceMin_i)

        # 打印每簇汇总（输入与权重、结果合并）
        if verbose and idx < 50:
            print(
                f"  cluster[{idx}] fOffsetTargetWeight={fOffsetTargetWeight_i:g}, "
                f"oriConfidenceMin={oriConfidenceMin_i:.6f}, tempWeight={tempWeight_i:.6f}, "
                f"IntegralWeight_i={IntegralWeight_i:.6f}, AGW_Gray_=({AGW_Gray_RpG_i:.6f}, {AGW_Gray_BpG_i:.6f})"
            )

    if total_count == 0:
        raise ValueError("stats 为空")

    # 由统计点得到的 AGW_NOMap（无 map 的灰点均值）
    AGW_NOMap_est = SOpAwb_ColorSpace(sum_r / total_count, sum_b / total_count)

    # 归一得到 AGW_Gray_way
    RpG = integralRpG / (integralWeight)
    BpG = integralBpG / (integralWeight)
    AGW_Gray_way = SOpAwb_ColorSpace(RpG, BpG)
    if verbose:
        print(f"  integralWeight       = {integralWeight:.6f}")

    return AGW_Gray_way, AGW_NOMap_est, integralWeight


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute AGW_Gray_way：支持从 DNP_awb.json 读取 3072 统计点")
    parser.add_argument("--agw-nomap", nargs=2, type=float, default=[0.47406, 0.540894], help="AGW_NOMap: RpG BpG（当未提供 --stats 时使用）")
    parser.add_argument("--offset-target", nargs=2, type=float, default=[0.3, 0.8], help="offsetMapTarget: RpG BpG")
    parser.add_argument("--f-offset-weight", type=float, default=0.2, help="fOffsetWeight: offset 原始权重 (totalWeight)")
    parser.add_argument("--f-offset-target-weight", type=float, default=0.1, help="fOffsetTargetWeight: offset 目标实际生效权重")
    parser.add_argument("--block-dist-target", nargs=2, type=float, default=[0.0, 0.0], help="blockDistTarget: RpG BpG (dist 目标点)")
    parser.add_argument("--f-dist-target-weight", type=float, default=0.0, help="fDistTargetWeight: dist 目标实际生效权重，默认 0")
    # 新增：从 DNP_awb.json 读取完整统计点
    parser.add_argument("--awb-json", type=str, default=None, help="AWB JSON 路径（DNP_awb.json/对比机 AWB JSON），优先于 --stats")
    parser.add_argument("--use-otp", action="store_true", help="使用 OTP 修正后的 (RpG,BpG) 进行计算（默认 False）")
    parser.add_argument("--use-stats-weight", action="store_true", help="将 fStatsWeight 作为块权重计入积分（默认 False，等权重）")
    parser.add_argument(
        "--stats",
        action="append",
        default=[],
        help="统计点簇，格式 count,rpg,bpg；可多次提供。如 1536,0.2,0.8",
    )
    parser.add_argument(
        "--offset-apply-indices",
        type=str,
        default=None,
        help="指定 offsetMap 生效的簇索引（0 基），逗号分隔；未指定则对所有簇生效。例：1 或 0,2",
    )
    parser.add_argument("--no-cluster-log", action="store_true", help="关闭逐簇的详细日志输出（默认打印前50条以示例）")

    args = parser.parse_args()

    offsetMapTarget = SOpAwb_ColorSpace(args.offset_target[0], args.offset_target[1])
    blockDistTarget = SOpAwb_ColorSpace(args.block_dist_target[0], args.block_dist_target[1])

    # 输入优先级：--awb-json > --stats > --agw-nomap
    parsed_stats: List[StatsCluster] = []
    if args.awb_json:
        try:
            from utils.awb_stats_tools import parse_awb_stats_from_json_file
        except Exception as e:
            raise RuntimeError(f"无法导入 utils.awb_stats_tools: {e}")
        sps = parse_awb_stats_from_json_file(args.awb_json)
        use_otp = bool(args.use_otp)
        use_w = bool(args.use_stats_weight)
        print("Inputs (from AWB JSON):")
        print(f"  file                = {args.awb_json}")
        print(f"  platform            = {sps.platform}")
        print(f"  size                = {sps.rows} x {sps.cols} (blocks={sps.rows*sps.cols})")
        print(f"  bitDepth            = {sps.bit_depth}")
        print(f"  correctCoef         = (RpG={sps.correct_coef_rpg:.6f}, BpG={sps.correct_coef_bpg:.6f})")
        print(f"  use_otp             = {use_otp}")
        print(f"  use_stats_weight    = {use_w}")
        for idx, p in enumerate(sps.points):
            r = p.rpg_otp if use_otp else p.rpg
            b = p.bpg_otp if use_otp else p.bpg
            cnt = int(p.weight) if (use_w and p.weight is not None) else 1
            parsed_stats.append(StatsCluster(cnt, SOpAwb_ColorSpace(r, b)))
    elif args.stats:
        for s in args.stats:
            try:
                count_str, r_str, b_str = s.split(",")
                parsed_stats.append(StatsCluster(int(count_str), SOpAwb_ColorSpace(float(r_str), float(b_str))))
            except Exception as e:
                raise ValueError(f"无法解析 --stats '{s}'，应为 count,rpg,bpg，例如 1536,0.2,0.8") from e
    else:
        AGW_NOMap = SOpAwb_ColorSpace(args.agw_nomap[0], args.agw_nomap[1])
        parsed_stats = [StatsCluster(3072, AGW_NOMap)]

    # 解析 offset 生效簇索引
    offset_apply_mask: List[bool] | None = None
    if args.offset_apply_indices is not None:
        mask = [False] * len(parsed_stats)
        try:
            indices = [int(x) for x in args.offset_apply_indices.split(",") if x.strip() != ""]
        except Exception as e:
            raise ValueError("--offset-apply-indices 应为逗号分隔的整数索引，如 1 或 0,2") from e
        for i in indices:
            if not (0 <= i < len(parsed_stats)):
                raise ValueError(f"--offset-apply-indices 包含非法索引 {i}，共有 {len(parsed_stats)} 个簇")
            mask[i] = True
        offset_apply_mask = mask

    AGW_Gray_way, AGW_NOMap_est, integralWeight = compute_agw_gray_way_with_stats(
        stats=parsed_stats,
        offsetMapTarget=offsetMapTarget,
        fOffsetWeight=args.f_offset_weight,
        fOffsetTargetWeight_base=args.f_offset_target_weight,
        blockDistTarget=blockDistTarget,
        fDistTargetWeight=args.f_dist_target_weight,
        offset_apply_mask=offset_apply_mask,
        verbose=not args.no_cluster_log,
    )
    print("Output:")
    print(f"  AGW_Gray_way         = ({AGW_Gray_way.RpG:.6f}, {AGW_Gray_way.BpG:.6f})")


if __name__ == "__main__":
    main()
