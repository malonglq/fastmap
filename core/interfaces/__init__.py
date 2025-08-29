#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心接口模块
==liuq debug== FastMapV2 核心接口定义模块

作者: 龙sir团队
创建时间: 2025-08-25
版本: 2.0.0
描述: 核心接口模块初始化文件，导出所有接口定义
"""

import logging

# 导入XML处理接口
from .xml_data_processor import (
    XMLDataProcessor,
    ValidationLevel,
    ValidationResult,
    XMLParseError,
    XMLWriteError,
    ValidationError,
    BackupError
)

from .xml_parser_service import (
    IXMLParserService,
    IXMLWriterService,
    IXMLValidatorService,
    IXMLMetadataService,
    XMLVersion,
    ParseMode,
    ParseOptions,
    ParseResult,
    WriteOptions,
    XMLParseError as XMLParserError,
    XMLWriteError as XMLWriterError,
    XMLValidationError,
    XMLBackupError
)

# 导入Map分析接口
from .map_analyzer_service import (
    IMapAnalyzerService,
    ITemperatureSpanAnalyzer,
    IMultiDimensionalAnalyzer,
    IVisualizationService,
    AnalysisOptions,
    AnalysisResult,
    MapAnalysisError,
    OptimizationError
)

# 导入EXIF处理接口
from .exif_parser_service import (
    IExifParserService,
    IExifDataProcessor,
    IExifExporter,
    ExifDataType,
    ExifParseOptionsExtended,
    ExifParseResultExtended,
    ExifExportOptions,
    ExifParseError,
    ExifExportError,
    DllInitializationError
)

# 导入报告生成接口
from .report_generator_service import (
    IReportGeneratorService,
    IChartGeneratorService,
    ITemplateManager,
    OutputFormat,
    ReportOptions,
    ReportResult,
    ReportGenerationError,
    TemplateError
)

# 导入原有接口
from .field_definition_provider import (
    FieldDefinitionProvider,
    FieldGroup,
    FieldRegistrationResult
)

from .data_binding_manager import (
    DataBindingManager,
    BindingDirection,
    BindingStatus,
    BindingInfo,
    SyncResult,
    BindingError,
    SyncError
)

from .xml_field_definition import (
    XMLFieldDefinition,
    FieldType,
    ValidationRule,
    ValidationRuleType,
    CommonValidationRules
)

from .report_generator import (
    IReportGenerator as ILegacyReportGenerator,
    ReportType,
    IReportDataProvider,
    IVisualizationProvider as ILegacyVisualizationProvider,
    IChartGenerator as ILegacyChartGenerator,
    ITemplateProvider as ILegacyTemplateProvider,
    IHTMLReportGenerator,
    IFileManager,
    ReportGeneratorConfig
)

# 导出所有接口和相关类
__all__ = [
    # XML数据处理接口
    "XMLDataProcessor",
    "ValidationLevel",
    "ValidationResult",
    "XMLParseError",
    "XMLWriteError",
    "ValidationError",
    "BackupError",
    
    # XML解析服务接口
    "IXMLParserService",
    "IXMLWriterService",
    "IXMLValidatorService",
    "IXMLMetadataService",
    "XMLVersion",
    "ParseMode",
    "ParseOptions",
    "ParseResult",
    "WriteOptions",
    "XMLParserError",
    "XMLWriterError",
    "XMLValidationError",
    "XMLBackupError",
    
    # Map分析服务接口
    "IMapAnalyzerService",
    "ITemperatureSpanAnalyzer",
    "IMultiDimensionalAnalyzer",
    "IVisualizationService",
    "AnalysisOptions",
    "AnalysisResult",
    "MapAnalysisError",
    "OptimizationError",
    
    # EXIF解析服务接口
    "IExifParserService",
    "IExifDataProcessor",
    "IExifExporter",
    "ExifDataType",
    "ExifParseOptionsExtended",
    "ExifParseResultExtended",
    "ExifExportOptions",
    "ExifParseError",
    "ExifExportError",
    "DllInitializationError",
    
    # 报告生成服务接口
    "IReportGeneratorService",
    "IChartGeneratorService",
    "ITemplateManager",
    "OutputFormat",
    "ReportOptions",
    "ReportResult",
    "ReportGenerationError",
    "TemplateError",
    
    # 字段定义提供者接口
    "FieldDefinitionProvider",
    "FieldGroup",
    "FieldRegistrationResult",
    
    # 数据绑定管理接口
    "DataBindingManager",
    "BindingDirection",
    "BindingStatus",
    "BindingInfo",
    "SyncResult",
    "BindingError",
    "SyncError",
    
    # XML字段定义
    "XMLFieldDefinition",
    "FieldType",
    "ValidationRule",
    "ValidationRuleType",
    "CommonValidationRules",
    
    # 兼容性报告生成接口
    "ILegacyReportGenerator",
    "ReportType",
    "IReportDataProvider",
    "ILegacyVisualizationProvider",
    "ILegacyChartGenerator",
    "ILegacyTemplateProvider",
    "IHTMLReportGenerator",
    "IFileManager",
    "ReportGeneratorConfig"
]

# 版本信息
__version__ = "2.0.0"
__author__ = "龙sir团队"
__description__ = "FastMapV2 核心接口定义模块"

logger = logging.getLogger(__name__)
logger.info("==liuq debug== 核心接口模块加载完成")
