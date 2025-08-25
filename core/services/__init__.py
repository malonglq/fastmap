#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastMapV2 服务层主模块

重构后的服务层，按GUI功能模块组织：
- map_analysis: Map分析相关服务
- exif_processing: EXIF处理相关服务  
- copywriting: 仿写功能相关服务 (预留)
- feature_points: 特征点功能相关服务 (预留)
- reporting: 报告生成相关服务
- shared: 共享通用服务
"""

# Map分析服务
from .map_analysis import (
    XMLParserService, XMLWriterService, MapAnalyzer, 
    TemperatureSpanAnalyzer, MultiDimensionalAnalyzer
)

# EXIF处理服务
from .exif_processing import (
    ExifParserService, ExifCsvExporter, ExifRawExporter,
    ImageExportService, ImageExportWorkflowService
)

# 特征点功能服务
from .feature_points import ImageClassifierService

# 报告生成服务  
from .reporting import (
    UnifiedReportManager, UniversalHTMLGenerator, UniversalChartGenerator,
    ExifComparisonReportGenerator, MapMultiDimensionalReportGenerator,
    CombinedReportDataProvider
)

# 共享服务
from .shared import (
    DataBindingManagerImpl, FieldRegistryService, FieldEditorFactory
)

# 向后兼容性：保持原有的导入方式
# 这样现有代码可以继续工作，而新代码可以使用新的模块化导入

__all__ = [
    # Map分析服务
    'XMLParserService', 'XMLWriterService', 'MapAnalyzer',
    'TemperatureSpanAnalyzer', 'MultiDimensionalAnalyzer',
    
    # EXIF处理服务
    'ExifParserService', 'ExifCsvExporter', 'ExifRawExporter', 
    'ImageExportService', 'ImageExportWorkflowService',
    
    # 特征点功能服务
    'ImageClassifierService',
    
    # 报告生成服务
    'UnifiedReportManager', 'UniversalHTMLGenerator', 'UniversalChartGenerator',
    'ExifComparisonReportGenerator', 'MapMultiDimensionalReportGenerator', 
    'CombinedReportDataProvider',
    
    # 共享服务
    'DataBindingManagerImpl', 'FieldRegistryService', 'FieldEditorFactory'
]