#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
几何工具函数

提供多边形重心等基础几何运算，供报告与GUI复用。
"""
from __future__ import annotations

from typing import List, Tuple


def polygon_centroid(vertices: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    计算简单多边形的重心（顶点按顺序给定，可不闭合）。

    使用标准的多边形重心公式；若面积为0或顶点不足，回退到算术平均。

    Args:
        vertices: 顶点序列 [(x1,y1), (x2,y2), ...]

    Returns:
        (cx, cy): 重心坐标
    """
    if not vertices:
        return 0.0, 0.0
    n = len(vertices)
    if n == 1:
        return float(vertices[0][0]), float(vertices[0][1])

    # Shoelace 公式
    area2 = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n):
        x1, y1 = float(vertices[i][0]), float(vertices[i][1])
        x2, y2 = float(vertices[(i + 1) % n][0]), float(vertices[(i + 1) % n][1])
        cross = x1 * y2 - x2 * y1
        area2 += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(area2) < 1e-12:
        # 面积近0，使用算术平均作为退化处理
        sx = sum(float(v[0]) for v in vertices)
        sy = sum(float(v[1]) for v in vertices)
        return sx / n, sy / n
    area = area2 / 2.0
    cx /= (6.0 * area)
    cy /= (6.0 * area)
    return cx, cy


__all__ = ["polygon_centroid"]

