#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准光源白点参考点常量与工具函数

提供在可视化与筛选中复用的参考点坐标与区间工具。
坐标系与项目一致：X=R/G (RpG)，Y=B/G (BpG)。

==liuq debug== 本文件用于提供白点参考坐标与区间判断工具
"""
from typing import Dict, Tuple
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# 锚点坐标 (RpG, BpG) 用于等色温带绘制；不作为白点标注数据源
TEMPERATURE_ANCHORS: Dict[str, Tuple[float, float]] = {
    # Ultra: 高于 High 的超高色温（更靠左上），取经验坐标以覆盖左上角区域
    "Ultra": (0.01, 1.70),
    "High": (0.29, 0.997878),
    "D75": (0.432664, 0.775651),
    "D65": (0.455606, 0.741601),
    "D50": (0.507914, 0.610665),
    "F":   (0.585179, 0.483977),
    "A":   (0.756114, 0.391159),
    "H":   (0.940325, 0.345813),
    "1500": (1.35, 0.25),
    # 100K: 低于 1500K 的超低色温（更靠右下），取经验坐标以覆盖右下角区域
    "100K": (2.50, 0.01),
}

# 可选：从 XML 中动态加载白点参考点，以替代硬编码。
def load_white_points_from_xml(xml_path: str) -> Dict[str, Tuple[float, float]]:
    """
    加载白点数据：
    - XML 由多个 <region> 组成，包含 ctemp, RGain, GGain, BGain
    - 注意：RGain/BGain 为倒数表示，实际绘制坐标需取倒数：rpg=1/RGain, bpg=1/BGain
    - GGain 通常为 1，不参与坐标
    返回：字典 { str(ctemp): (rpg, bpg) }
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        pts: Dict[str, Tuple[float, float]] = {}
        skipped_out_of_range = 0
        skipped_zero_gain = 0
        parse_errors = 0
        for reg in root.findall('.//region'):
            try:
                ctemp_text = (reg.findtext('ctemp') or '').strip()
                # 统一为纯数字字符串键，例如 '5000'，避免 '500K' 之类格式
                # 若出现带 K 的格式，剥离字母
                ctemp_key = ''.join(ch for ch in ctemp_text if ch.isdigit())
                if not ctemp_key:
                    continue
                try:
                    ctemp_val = int(ctemp_key)
                except Exception:
                    parse_errors += 1
                    continue
                # 任务2：过滤不合理的色温（物理上通常100K-20000K）
                if ctemp_val < 100 or ctemp_val > 20000:
                    skipped_out_of_range += 1
                    continue
                r_gain_text = (reg.findtext('RGain') or '').strip()
                b_gain_text = (reg.findtext('BGain') or '').strip()
                # 转为浮点
                r_gain = float(r_gain_text)
                b_gain = float(b_gain_text)
                # 取倒数，避免除以0
                if r_gain == 0.0 or b_gain == 0.0:
                    skipped_zero_gain += 1
                    continue
                rpg = 1.0 / r_gain
                bpg = 1.0 / b_gain
                pts[ctemp_key] = (rpg, bpg)
            except Exception as e:
                parse_errors += 1
                continue
        if skipped_out_of_range or skipped_zero_gain or parse_errors:
            logger.warning("==liuq debug== 白点XML过滤统计: 越界=%d, 零增益=%d, 解析失败=%d", skipped_out_of_range, skipped_zero_gain, parse_errors)
        return pts
    except Exception as e:
        logger.error("==liuq debug== 加载白点XML失败: %s", e)
        return {}


# 预设区间（用于筛选）
# 为保证覆盖典型色温范围，补全高低端区间：High-D75 与 H-1500
REFERENCE_INTERVALS = [
    ("Ultra", "High"),
    ("High", "D75"),
    ("D75", "D65"),
    ("D65", "D50"),
    ("D50", "F"),
    ("F", "A"),
    ("A", "H"),
    ("H", "1500"),
    ("1500", "100K"),
]
# 画布固定坐标范围（与MapShapeViewer._setup_fixed_coordinate_system一致）
PLOT_X_MIN = 0.0
PLOT_X_MAX = 2.53
PLOT_Y_MIN = 0.0
PLOT_Y_MAX = 1.7
TOP_RIGHT_CORNER = (PLOT_X_MAX, PLOT_Y_MAX)



def get_point(name: str) -> Tuple[float, float]:
    """获取等色温带锚点坐标，名称区分大小写。若不存在，抛出KeyError。"""
    return TEMPERATURE_ANCHORS[name]


def get_interval_bounds(a: str, b: str) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """返回由两个参考点形成的轴对齐矩形边界。

    Returns:
        ((min_rpg, max_rpg), (min_bpg, max_bpg))
    """
    ax, ay = get_point(a)
    bx, by = get_point(b)
    return ((min(ax, bx), max(ax, bx)), (min(ay, by), max(ay, by)))


def is_in_interval_rect(x: float, y: float, a: str, b: str) -> bool:
    """判断点是否落在由两个参考点构成的轴对齐矩形范围内。"""
    (rx, rx2), (by, by2) = get_interval_bounds(a, b)
    return (rx <= x <= rx2) and (by <= y <= by2)


# 已移除硬编码白点数据源。白点仅来源于 XML。


# ---------------- 新增：等色温线与区间判断 ----------------
# 说明：这里实现一个工程近似法，用于根据参考点区间（例如 D65-D50）
# 判断某点 (x,y) 是否位于两条等色温线之间。为避免复杂的CIE计算，
# 使用分段线性近似：将日光轨迹在这些参考点之间视为一段折线，
# 通过点到线段的投影确定落点在线段参数 t∈[0,1] 范围内，并使用到线段的
# 符号距离与带宽（容差）判定是否“位于这两条等色温线之间”。
#
# 思路：
# - 对于区间 (A,B)：
#   定义主轨迹线段 L = A->B。点P到 L 的投影参数 t 给出其色温插值位置。
#   使用到线段法线方向的距离 d 与容差 band 判断是否靠近该轨迹带。
# - 为增强稳定性，为每段给定一个经验带宽（单位为 B/G），也可统一用默认 band。
# - 该方法不依赖真实Planckian locus公式，适合工程快速判断；如需更高精度，可后续替换。

# 每段的经验带宽（B/G 轴单位）。如无特例则使用 DEFAULT_BAND。
DEFAULT_BAND = 0.06
SEGMENT_BANDS: Dict[Tuple[str, str], float] = {
    ("Ultra", "High"): 0.10,
    ("High", "D75"): 0.08,
    ("D75", "D65"): 0.07,
    ("D65", "D50"): 0.07,
    ("D50", "F"): 0.06,
    ("F", "A"): 0.06,
    ("A", "H"): 0.06,
    ("H", "1500"): 0.08,
    ("1500", "100K"): 0.08,
}


def _get_band(a: str, b: str) -> float:
    return SEGMENT_BANDS.get((a, b), DEFAULT_BAND)


def _project_point_to_segment(px: float, py: float,
                              ax: float, ay: float,
                              bx: float, by: float) -> Tuple[float, float, float]:
    """将点P投影到线段AB，返回 (t, x_proj, y_proj)。t∈(-∞,∞)，线段内为[0,1]。
    """
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    denom = vx * vx + vy * vy
    if denom == 0:
        return 0.0, ax, ay
    t = (wx * vx + wy * vy) / denom
    x_proj = ax + t * vx
    y_proj = ay + t * vy
    return t, x_proj, y_proj


def is_in_temperature_interval(x: float, y: float, a: str, b: str,
                               band: float = None) -> bool:
    """
    基于等色温线（工程近似：分段日光轨迹）判断 (x,y) 是否位于区间(a,b)。

    实现：
    - 将区间(a,b) 对应成参考点A(xa,ya)、B(xb,yb) 的主轨迹线段 AB
    - 计算点P到 AB 的投影参数 t，限制在[0,1] 表示位于 A 与 B 之间
    - 计算到该线段的法向距离 d，若 |d| <= band 则视为处于该区间
    - band 若未指定，使用针对该段的经验带宽
    """
    (xa, ya) = get_point(a)
    (xb, yb) = get_point(b)

    t, x_proj, y_proj = _project_point_to_segment(x, y, xa, ya, xb, yb)
    if t < 0.0 or t > 1.0:
        return False

    # 法向距离（欧氏距离到投影点）
    dx, dy = x - x_proj, y - y_proj
    dist = (dx * dx + dy * dy) ** 0.5
    tol = _get_band(a, b) if band is None else band

    return dist <= tol
# ---------------- 新增：基于右上角扇形的区间判断 ----------------
from typing import NamedTuple

class RectBounds(NamedTuple):
    xmin: float
    xmax: float
    ymin: float
    ymax: float

def _ray_to_rect_intersection(x0: float, y0: float, x1: float, y1: float,
                              bounds: RectBounds) -> Tuple[float, float]:
    """从(x0,y0)指向(x1,y1)的射线与矩形边界的交点（t>0最近命中）。"""
    dx, dy = x1 - x0, y1 - y0
    t_candidates = []
    eps = 1e-12
    if abs(dx) > eps:
        t_to_xmin = (bounds.xmin - x0) / dx
        t_to_xmax = (bounds.xmax - x0) / dx
        for t, x_edge in ((t_to_xmin, bounds.xmin), (t_to_xmax, bounds.xmax)):
            if t > 0:
                y_hit = y0 + t * dy
                if bounds.ymin - eps <= y_hit <= bounds.ymax + eps:
                    t_candidates.append((t, x_edge, y_hit))
    if abs(dy) > eps:
        t_to_ymin = (bounds.ymin - y0) / dy
        t_to_ymax = (bounds.ymax - y0) / dy
        for t, y_edge in ((t_to_ymin, bounds.ymin), (t_to_ymax, bounds.ymax)):
            if t > 0:
                x_hit = x0 + t * dx
                if bounds.xmin - eps <= x_hit <= bounds.xmax + eps:
                    t_candidates.append((t, x_hit, y_edge))
    if not t_candidates:
        return x1, y1
    t_candidates.sort(key=lambda v: v[0])
    _, ix, iy = t_candidates[0]
    return ix, iy

def _sign(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    return (px - bx) * (ay - by) - (ax - bx) * (py - by)

def _point_in_triangle(px: float, py: float,
                       ax: float, ay: float,
                       bx: float, by: float,
                       cx: float, cy: float) -> bool:
    """点在三角形内(含边)判定。"""
    d1 = _sign(px, py, ax, ay, bx, by)
    d2 = _sign(px, py, bx, by, cx, cy)
    d3 = _sign(px, py, cx, cy, ax, ay)
    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (has_neg and has_pos)

def get_temperature_sector_vertices(a: str, b: str,
                                    corner: Tuple[float, float] = TOP_RIGHT_CORNER,
                                    bounds: RectBounds = RectBounds(PLOT_X_MIN, PLOT_X_MAX, PLOT_Y_MIN, PLOT_Y_MAX)) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
    """返回(a,b)对应扇形三角形的三个顶点：(Corner, Pa, Pb)。"""
    cx, cy = corner
    ax, ay = get_point(a)
    bx, by = get_point(b)
    pa_x, pa_y = _ray_to_rect_intersection(cx, cy, ax, ay, bounds)
    pb_x, pb_y = _ray_to_rect_intersection(cx, cy, bx, by, bounds)
    return (cx, cy), (pa_x, pa_y), (pb_x, pb_y)


def is_in_temperature_sector(x: float, y: float, a: str, b: str,
                             corner: Tuple[float, float] = TOP_RIGHT_CORNER,
                             bounds: RectBounds = RectBounds(PLOT_X_MIN, PLOT_X_MAX, PLOT_Y_MIN, PLOT_Y_MAX)) -> bool:
    """使用“右上角扇形”方法判断点(x,y)是否位于(a,b)对应的扇区内。
    算法：Corner→a、Corner→b 两条射线与坐标矩形求交，得到Pa、Pb，
    判定 P 是否位于三角形 [Corner, Pa, Pb] 内。
    """
    try:
        (corner_pt, pa, pb) = get_temperature_sector_vertices(a, b, corner, bounds)
        cx, cy = corner_pt
        pa_x, pa_y = pa
        pb_x, pb_y = pb
        inside = _point_in_triangle(x, y, cx, cy, pa_x, pa_y, pb_x, pb_y)
        logger.debug(f"==liuq debug== 扇形判定: P=({x:.6f},{y:.6f}), sector={a}-{b}, corner=({cx:.3f},{cy:.3f}), pa=({pa_x:.3f},{pa_y:.3f}), pb=({pb_x:.3f},{pb_y:.3f}), inside={inside}")
        return inside
    except Exception as e:
        logger.warning(f"==liuq debug== is_in_temperature_sector异常: {e}")
        return False

