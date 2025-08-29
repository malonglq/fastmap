#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成服务模块

该模块包含所有与报告生成相关的服务：
- 统一报告管理
- HTML生成
- 图表生成  
- 各类报告生成器
"""

# 导入主要服务
from .unified_report_manager import UnifiedReportManager
from .html_generator import UniversalHTMLGenerator
from .html_template_service import HTMLTemplateService
from .html_style_service import HTMLStyleService
from .html_content_service import HTMLContentService
from .chart_generator import UniversalChartGenerator
from .exif_comparison_report_generator import ExifComparisonReportGenerator
from .map_multi_dimensional_report_generator import MapMultiDimensionalReportGenerator
from .combined_report_data_provider import CombinedReportDataProvider
# EXIF报告辅助函数
# from .exif_report_helpers import ExifReportHelpers  # 该文件包含辅助函数，非类

__all__ = [
    'UnifiedReportManager',
    'UniversalHTMLGenerator',
    'HTMLTemplateService',
    'HTMLStyleService',
    'HTMLContentService',
    'UniversalChartGenerator',
    'ExifComparisonReportGenerator', 
    'MapMultiDimensionalReportGenerator',
    'CombinedReportDataProvider'
    # 'ExifReportHelpers'  # 该文件包含辅助函数，非类
]