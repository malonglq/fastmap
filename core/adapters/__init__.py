#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
适配器模块
==liuq debug== FastMapV2适配器模块

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 15:10:00 +08:00; Reason: 阶段2-创建适配器模块; Principle_Applied: 适配器模式;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 提供各种数据格式和外部模块的适配器
"""

from .exif_data_adapter import ExifDataAdapter
from .csv_comparison_adapter import CSVComparisonAdapter

__all__ = [
    'ExifDataAdapter',
    'CSVComparisonAdapter'
]
