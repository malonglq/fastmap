#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
色温段跨度分析器

根据Map点（单点或多边形）与参考色温扇形区域（utils.white_points.REFERENCE_INTERVALS）
的空间关系，统计每个Map点跨越的色温段数量及列表。

输出数据结构可被JSON序列化，便于GUI和报告使用。

==liuq debug== 本模块复用GUI等色温带绘制与筛选所用的扇形判断逻辑，确保一致性
"""
from typing import Dict, Any, List, Tuple
import logging

from core.models.map_data import MapConfiguration
from utils.white_points import (
    REFERENCE_INTERVALS,
    is_in_temperature_sector,
)

logger = logging.getLogger(__name__)


# --- 多边形面积与裁剪工具（Sutherland–Hodgman），用于精确相交判定 ---
from typing import Optional

_MIN_INTERSECT_RATIO = 0.01  # 大于1%视为相交
_EPS = 1e-12

def _signed_area(poly: List[Tuple[float, float]]) -> float:
    n = len(poly)
    if n < 3:
        return 0.0
    s = 0.0
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return 0.5 * s

def _polygon_area(poly: List[Tuple[float, float]]) -> float:
    a = _signed_area(poly)
    return a if a >= 0 else -a

def _ensure_ccw(poly: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    # 若为顺时针则反转
    return poly if _signed_area(poly) > 0 else list(reversed(poly))

def _is_inside(p: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    # 判断点p是否在有向边ab的左侧（含边），CCW情形下左侧为内侧
    px, py = p; ax, ay = a; bx, by = b
    return ((bx - ax) * (py - ay) - (by - ay) * (px - ax)) >= -_EPS

def _compute_intersection(s: Tuple[float, float], e: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    # 线段se与有向边ab的直线求交（无限直线），返回交点；若平行返回None
    sx, sy = s; ex, ey = e; ax, ay = a; bx, by = b
    dx1, dy1 = ex - sx, ey - sy
    dx2, dy2 = bx - ax, by - ay
    denom = dx1 * dy2 - dy1 * dx2
    if abs(denom) < _EPS:
        return None
    t = ((ax - sx) * dy2 - (ay - sy) * dx2) / denom
    # 我们希望交点位于se线段上（t在[0,1]范围内），但Sutherland–Hodgman允许外延求交再裁切
    ix = sx + t * dx1
    iy = sy + t * dy1
    return (ix, iy)

def _clip_polygon(subject: List[Tuple[float, float]], clipper: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if len(subject) < 3 or len(clipper) < 3:
        return []
    # 确保裁剪多边形为CCW
    clip = _ensure_ccw(clipper)
    output = subject[:]
    for i in range(len(clip)):
        a = clip[i]
        b = clip[(i + 1) % len(clip)]
        input_list = output
        output = []
        if not input_list:
            break
        s = input_list[-1]
        for e in input_list:
            if _is_inside(e, a, b):
                if not _is_inside(s, a, b):
                    inter = _compute_intersection(s, e, a, b)
                    if inter is not None:
                        output.append(inter)
                output.append(e)
            elif _is_inside(s, a, b):
                inter = _compute_intersection(s, e, a, b)
                if inter is not None:
                    output.append(inter)
            s = e
    return output

class TemperatureSpanAnalyzer:
    """
    色温段跨度分析器

    使用与GUI绘制一致的“右上角扇形”判定方式统计跨越段。
    """

    def __init__(self, configuration: MapConfiguration):
        self.configuration = configuration

    def analyze(self) -> Dict[str, Any]:
        """
        执行跨度统计分析。

        Returns:
            Dict[str, Any]:
                {
                  'spans_by_map': {
                      alias_name: {
                         'count': int,
                         'interval_keys': List[Tuple[str,str]],
                         'interval_names': List[str],
                         'coords': Tuple[float,float],  # 重心绝对坐标
                      }, ...
                  },
                  'top20': [ { 'alias_name': str, 'interval_names': List[str], 'count': int, 'coords': (x,y) }, ... ]
                }
        """
        try:
            spans_by_map: Dict[str, Any] = {}

            bb = self.configuration.base_boundary if self.configuration else None

            for mp in self.configuration.map_points:
                # 统一绝对坐标：多边形使用重心绝对坐标，单点=base_boundary + offset
                if mp.is_polygon and mp.polygon_vertices:
                    cx = float(mp.x)
                    cy = float(mp.y)
                else:
                    if bb is None:
                        cx = float(getattr(mp, 'x', 0.0))
                        cy = float(getattr(mp, 'y', 0.0))
                    else:
                        cx = float(bb.rpg) + float(getattr(mp, 'offset_x', 0.0))
                        cy = float(bb.bpg) + float(getattr(mp, 'offset_y', 0.0))

                interval_keys: List[Tuple[str, str]] = []
                interval_names: List[str] = []

                # 判定与每个扇形是否相交/重叠：
                # - 单点：重心落入扇形即视为关联
                # - 多边形：若重心或任一顶点在扇形内即可视为关联（工程近似，避免引入额外几何库）
                for (a, b) in REFERENCE_INTERVALS:
                    try:
                        hit = False

                        # 重心命中（扇形）
                        if is_in_temperature_sector(cx, cy, a, b):
                            hit = True
                        else:
                            # 多边形：严格采用面积相交法（>1%阈值），可选保留重心命中
                            if mp.is_polygon and mp.polygon_vertices:
                                from utils.white_points import get_temperature_sector_vertices
                                (corner_pt, pa, pb) = get_temperature_sector_vertices(a, b)
                                tri = [corner_pt, pa, pb]
                                subject = [(float(vx), float(vy)) for (vx, vy) in mp.polygon_vertices]
                                clipped = _clip_polygon(subject, tri)
                                ratio = 0.0
                                if clipped:
                                    inter_area = _polygon_area(clipped)
                                    poly_area = _polygon_area(subject)
                                    ratio = (inter_area / poly_area) if poly_area > 0 else 0.0
                                logger.debug(f"==liuq debug== 面积相交: {mp.alias_name} {a}-{b}, ratio={ratio:.4%}")
                                if ratio > _MIN_INTERSECT_RATIO or is_in_temperature_sector(cx, cy, a, b):
                                    hit = True

                        if hit:
                            interval_keys.append((a, b))
                            interval_names.append(f"{a}-{b}")
                    except Exception as e:
                        logger.debug(f"==liuq debug== 扇形跨度判定异常: {mp.alias_name} {a}-{b} {e}")
                        continue

                spans_by_map[mp.alias_name] = {
                    'count': len(interval_keys),
                    'interval_keys': interval_keys,
                    'interval_names': interval_names,
                    'coords': (cx, cy),
                }
                logger.info("==liuq debug== 预计算: %s coords=(%.6f,%.6f) intervals=%s", mp.alias_name, cx, cy, ','.join(interval_names))

            # 生成Top20
            sortable = [
                {
                    'alias_name': alias,
                    'interval_names': data['interval_names'],
                    'count': data['count'],
                    'coords': data['coords'],
                }
                for alias, data in spans_by_map.items()
            ]
            sortable.sort(key=lambda x: (-x['count'], x['alias_name']))
            top20 = sortable[:20]

            result = {
                'spans_by_map': spans_by_map,
                'top20': top20,
            }

            logger.info("==liuq debug== 色温段跨度分析完成: 共 %d 个Map点", len(spans_by_map))
            return result
        except Exception as e:
            logger.error(f"==liuq debug== 色温段跨度分析失败: {e}")
            return {'spans_by_map': {}, 'top20': []}

