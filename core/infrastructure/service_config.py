#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入容器配置
==liuq debug== FastMapV2 依赖注入容器配置

作者: 龙sir团队
创建时间: 2025-08-25
版本: 2.0.0
描述: 配置所有服务的依赖注入关系
"""

import logging
from typing import Type

from core.infrastructure.di_container import DIContainer, ServiceLifetime, get_container
from core.interfaces import (
    # XML处理接口
    IXMLParserService,
    IXMLWriterService,
    IXMLValidatorService,
    IXMLMetadataService,
    
    # Map分析接口
    IMapAnalyzerService,
    ITemperatureSpanAnalyzer,
    IMultiDimensionalAnalyzer,
    IVisualizationService,
    
    # EXIF处理接口
    IExifParserService,
    IExifDataProcessor,
    IExifExporter,
    
    # 报告生成接口
    IReportGeneratorService,
    IChartGeneratorService,
    ITemplateManager,
    
    # 数据绑定接口
    DataBindingManager,
    
    # 字段注册接口
    FieldDefinitionProvider
)

logger = logging.getLogger(__name__)

def configure_services() -> DIContainer:
    """
    配置服务注册
    
    采用依赖倒置原则，所有服务都通过接口进行注册和解析
    """
    container = get_container()
    
    try:
        # 清空现有注册（避免重复注册）
        container.clear()
        
        # ===== XML处理服务 =====
        from core.services.map_analysis.xml_parser_service import XMLParserService
        from core.services.map_analysis.xml_writer_service import XMLWriterService
        from core.services.map_analysis.xml_validation_service import XMLValidationService
        from core.services.map_analysis.xml_metadata_service import XMLMetadataService
        
        container.register_singleton(IXMLParserService, XMLParserService)
        container.register_singleton(IXMLWriterService, XMLWriterService)
        container.register_singleton(IXMLValidatorService, XMLValidationService)
        container.register_singleton(IXMLMetadataService, XMLMetadataService)
        
        # ===== Map分析服务 =====
        from core.services.map_analysis.map_analyzer import MapAnalyzer
        from core.services.map_analysis.temperature_span_analyzer import TemperatureSpanAnalyzer
        from core.services.map_analysis.multi_dimensional_analyzer import MultiDimensionalAnalyzer
        from core.services.map_analysis.visualization_service import VisualizationService
        
        container.register_singleton(IMapAnalyzerService, MapAnalyzer)
        container.register_singleton(ITemperatureSpanAnalyzer, TemperatureSpanAnalyzer)
        container.register_singleton(IMultiDimensionalAnalyzer, MultiDimensionalAnalyzer)
        container.register_singleton(IVisualizationService, VisualizationService)
        
        # ===== EXIF处理服务 =====
        from core.services.exif_processing.exif_parser_service import ExifParserService
        from core.services.exif_processing.exif_data_processor import ExifDataProcessor
        from core.services.exif_processing.exif_exporter import ExifExporter
        
        container.register_singleton(IExifParserService, ExifParserService)
        container.register_singleton(IExifDataProcessor, ExifDataProcessor)
        container.register_singleton(IExifExporter, ExifExporter)
        
        # ===== 报告生成服务 =====
        from core.services.reporting.report_generator_service import ReportGeneratorService
        from core.services.reporting.chart_generator_service import ChartGeneratorService
        from core.services.reporting.template_manager import TemplateManager
        
        container.register_singleton(IReportGeneratorService, ReportGeneratorService)
        container.register_singleton(IChartGeneratorService, ChartGeneratorService)
        container.register_singleton(ITemplateManager, TemplateManager)
        
        # ===== 数据绑定服务 =====
        from core.services.shared.data_binding_manager_impl import DataBindingManagerImpl
        
        container.register_singleton(DataBindingManager, DataBindingManagerImpl)
        
        # ===== 字段注册服务 =====
        from core.services.shared.field_registry_service import FieldRegistryService
        
        container.register_singleton(FieldDefinitionProvider, FieldRegistryService)
        
        # ===== 特征点服务 =====
        from core.services.feature_points.image_classifier_service import ImageClassifierService
        
        container.register_singleton(ImageClassifierService)
        
        logger.info("==liuq debug== 依赖注入服务配置完成")
        logger.info(f"==liuq debug== 已注册服务: {container.get_registered_services()}")
        
        return container
        
    except Exception as e:
        logger.error(f"==liuq debug== 服务配置失败: {e}")
        raise


def get_service(service_interface: Type[T]) -> T:
    """
    获取服务实例
    
    Args:
        service_interface: 服务接口类型
        
    Returns:
        T: 服务实例
    """
    container = get_container()
    return container.resolve(service_interface)


# 自动配置服务（当模块被导入时）
try:
    configure_services()
except Exception as e:
    logger.error(f"==liuq debug== 自动配置服务失败: {e}")

__version__ = "2.0.0"
__author__ = "龙sir团队"
__description__ = "FastMapV2 依赖注入容器配置"
