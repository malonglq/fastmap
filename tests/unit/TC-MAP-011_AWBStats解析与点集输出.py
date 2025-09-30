#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-MAP-011: AWB Stats 解析与点集输出

目标：
- 验证 utils.awb_stats_tools 能正确解析测试 JSON 的 StatsData
- 校验平台、尺寸、点数量，以及前若干点的 (RpG,BpG) 修正坐标
"""
from __future__ import annotations

from pathlib import Path
import math

from utils.awb_stats_tools import parse_awb_stats_from_json_file


def _isclose(a: float, b: float, rel: float = 1e-6, abs_: float = 1e-6) -> bool:
    return math.isclose(a, b, rel_tol=rel, abs_tol=abs_)


def test_awb_stats_parse_points_basic():
    # 测试数据路径
    json_path = Path('tests/test_data/101_Swangoose_IMG20250101230435_awb.json')
    assert json_path.exists(), '测试数据缺失'

    # 执行解析
    res = parse_awb_stats_from_json_file(json_path)

    # 基本属性
    assert res.platform == 'QC'
    assert res.rows == 48 and res.cols == 64
    assert len(res.points) == res.rows * res.cols == 3072

    # 取前3个点的修正坐标（与脚本打印示例核对，浮点近似）
    xy = res.to_xy(corrected=True)
    assert len(xy) >= 3

    # 预期（来自同一JSON的解析示例结果）
    exp = [
        (0.49930275680216246, 0.8284524746689135),
        (0.5080696842803734,  0.8153951323629884),
        (0.5361376983432673,  0.7852139999358580),
    ]
    for (x, y), (ex, ey) in zip(xy[:3], exp):
        assert _isclose(x, ex, rel=1e-6, abs_=1e-6), f'RpG不匹配: {x} != {ex}'
        assert _isclose(y, ey, rel=1e-6, abs_=1e-6), f'BpG不匹配: {y} != {ey}'

    # 权重与肤色标记（首点应存在，类型正确）
    p0 = res.points[0]
    assert isinstance(p0.weight, int)
    assert isinstance(p0.is_skin, bool)

