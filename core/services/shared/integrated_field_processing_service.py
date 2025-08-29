#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段处理器整合服务
==liuq debug== FastMapV2 字段处理器整合服务

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: 将增强字段处理器注册表集成到现有字段注册服务中
"""

import logging
from typing import Dict, List, Any, Optional
from core.services.shared.field_registry_service import FieldRegistryService, field_registry
from core.services.shared.enhanced_field_processor_registry import (
    EnhancedFieldProcessorRegistry, ProcessorType, ProcessorRegistration,
    FieldValidator, FieldFormatter, FieldConverter, FieldType
)
from core.interfaces.xml_field_definition import XMLFieldDefinition

logger = logging.getLogger(__name__)


class IntegratedFieldProcessingService:
    """
    字段处理器整合服务
    
    将增强字段处理器注册表与现有字段注册服务整合：
    - 统一字段定义管理
    - 增强字段处理能力
    - 提供完整的字段生命周期管理
    """
    
    def __init__(self):
        """初始化整合服务"""
        self.field_registry = field_registry
        self.processor_registry = EnhancedFieldProcessorRegistry()
        self._setup_default_processors()
        logger.info("==liuq debug== 字段处理器整合服务初始化完成")
    
    def get_field_definition(self, field_id: str) -> Optional[XMLFieldDefinition]:
        """
        获取字段定义
        
        Args:
            field_id: 字段ID
            
        Returns:
            Optional[XMLFieldDefinition]: 字段定义
        """
        return self.field_registry.get_field(field_id)
    
    def get_all_field_definitions(self) -> List[XMLFieldDefinition]:
        """
        获取所有字段定义
        
        Returns:
            List[XMLFieldDefinition]: 所有字段定义列表
        """
        return self.field_registry.get_all_fields()
    
    def validate_field_value(self, field_id: str, value: Any, context: Dict[str, Any] = None) -> bool:
        """
        验证字段值
        
        Args:
            field_id: 字段ID
            value: 字段值
            context: 上下文信息
            
        Returns:
            bool: 验证是否通过
        """
        try:
            field_def = self.get_field_definition(field_id)
            if not field_def:
                logger.warning(f"==liuq debug== 字段定义未找到: {field_id}")
                return False
            
            # 使用增强处理器进行验证
            return self.processor_registry.process_field(
                value, field_def, ProcessorType.VALIDATOR, context
            )
            
        except Exception as e:
            logger.error(f"==liuq debug== 字段验证失败: {field_id} - {e}")
            return False
    
    def format_field_value(self, field_id: str, value: Any, context: Dict[str, Any] = None) -> str:
        """
        格式化字段值
        
        Args:
            field_id: 字段ID
            value: 字段值
            context: 上下文信息
            
        Returns:
            str: 格式化后的字符串
        """
        try:
            field_def = self.get_field_definition(field_id)
            if not field_def:
                logger.warning(f"==liuq debug== 字段定义未找到: {field_id}")
                return str(value) if value is not None else ""
            
            # 使用增强处理器进行格式化
            return self.processor_registry.process_field(
                value, field_def, ProcessorType.FORMATTER, context
            )
            
        except Exception as e:
            logger.error(f"==liuq debug== 字段格式化失败: {field_id} - {e}")
            return str(value) if value is not None else ""
    
    def convert_field_value(self, field_id: str, value: Any, context: Dict[str, Any] = None) -> Any:
        """
        转换字段值
        
        Args:
            field_id: 字段ID
            value: 字段值
            context: 上下文信息
            
        Returns:
            Any: 转换后的值
        """
        try:
            field_def = self.get_field_definition(field_id)
            if not field_def:
                logger.warning(f"==liuq debug== 字段定义未找到: {field_id}")
                return value
            
            # 使用增强处理器进行转换
            return self.processor_registry.process_field(
                value, field_def, ProcessorType.CONVERTER, context
            )
            
        except Exception as e:
            logger.error(f"==liuq debug== 字段转换失败: {field_id} - {e}")
            return value
    
    def process_field_batch(self, field_data: Dict[str, Any], 
                          processor_type: ProcessorType, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        批量处理字段
        
        Args:
            field_data: 字段数据字典
            processor_type: 处理器类型
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 处理后的字段数据
        """
        try:
            processed_data = {}
            
            for field_id, value in field_data.items():
                field_def = self.get_field_definition(field_id)
                if field_def:
                    processed_value = self.processor_registry.process_field(
                        value, field_def, processor_type, context
                    )
                    processed_data[field_id] = processed_value
                else:
                    processed_data[field_id] = value
            
            return processed_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 批量字段处理失败: {e}")
            return field_data
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            field_count = len(self.get_all_field_definitions())
            processor_stats = self.processor_registry.get_statistics()
            
            return {
                'total_fields': field_count,
                'processor_statistics': processor_stats,
                'field_types': self._get_field_type_distribution(),
                'service_status': 'active'
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取处理统计信息失败: {e}")
            return {'service_status': 'error', 'error': str(e)}
    
    def _setup_default_processors(self):
        """设置默认处理器"""
        try:
            # 注册数字验证器
            number_validator = FieldValidator(
                "number_validator",
                [FieldType.FLOAT, FieldType.INTEGER],
                self._validate_number
            )
            self.processor_registry.register_processor(
                number_validator,
                ProcessorRegistration(
                    "number_validator",
                    ProcessorType.VALIDATOR,
                    [FieldType.FLOAT, FieldType.INTEGER],
                    priority=10
                )
            )
            
            # 注册字符串验证器
            string_validator = FieldValidator(
                "string_validator",
                [FieldType.STRING],
                self._validate_string
            )
            self.processor_registry.register_processor(
                string_validator,
                ProcessorRegistration(
                    "string_validator",
                    ProcessorType.VALIDATOR,
                    [FieldType.STRING],
                    priority=10
                )
            )
            
            # 注册数字格式化器
            number_formatter = FieldFormatter(
                "number_formatter",
                [FieldType.FLOAT, FieldType.INTEGER],
                self._format_number
            )
            self.processor_registry.register_processor(
                number_formatter,
                ProcessorRegistration(
                    "number_formatter",
                    ProcessorType.FORMATTER,
                    [FieldType.FLOAT, FieldType.INTEGER],
                    priority=10
                )
            )
            
            # 注册类型转换器
            type_converter = FieldConverter(
                "type_converter",
                [FieldType.FLOAT, FieldType.INTEGER, FieldType.STRING, FieldType.BOOLEAN],
                self._convert_type
            )
            self.processor_registry.register_processor(
                type_converter,
                ProcessorRegistration(
                    "type_converter",
                    ProcessorType.CONVERTER,
                    [FieldType.FLOAT, FieldType.INTEGER, FieldType.STRING, FieldType.BOOLEAN],
                    priority=10
                )
            )
            
            logger.info("==liuq debug== 默认处理器注册完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置默认处理器失败: {e}")
    
    def _validate_number(self, value: Any, field_def: XMLFieldDefinition) -> bool:
        """验证数字值"""
        try:
            if value is None:
                return not getattr(field_def, 'required', True)
            
            if field_def.field_type == FieldType.INTEGER:
                int(value)
            elif field_def.field_type == FieldType.FLOAT:
                float(value)
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _validate_string(self, value: Any, field_def: XMLFieldDefinition) -> bool:
        """验证字符串值"""
        try:
            if value is None:
                return not getattr(field_def, 'required', True)
            
            str_value = str(value)
            min_length = getattr(field_def, 'min_length', 0)
            max_length = getattr(field_def, 'max_length', None)
            
            if len(str_value) < min_length:
                return False
            
            if max_length and len(str_value) > max_length:
                return False
            
            return True
        except Exception:
            return False
    
    def _format_number(self, value: Any, field_def: XMLFieldDefinition) -> str:
        """格式化数字值"""
        try:
            if value is None:
                return ""
            
            if field_def.field_type == FieldType.INTEGER:
                return str(int(value))
            elif field_def.field_type == FieldType.FLOAT:
                precision = getattr(field_def, 'precision', 3)
                return f"{float(value):.{precision}f}"
            
            return str(value)
        except Exception:
            return str(value) if value is not None else ""
    
    def _convert_type(self, value: Any, field_def: XMLFieldDefinition) -> Any:
        """转换数据类型"""
        try:
            if value is None:
                return field_def.default_value
            
            if field_def.field_type == FieldType.INTEGER:
                return int(float(str(value)))
            elif field_def.field_type == FieldType.FLOAT:
                return float(str(value))
            elif field_def.field_type == FieldType.STRING:
                return str(value)
            elif field_def.field_type == FieldType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                str_value = str(value).lower()
                return str_value in ('1', 'true', 'yes', 'on')
            
            return value
        except Exception:
            return field_def.default_value
    
    def _get_field_type_distribution(self) -> Dict[str, int]:
        """获取字段类型分布"""
        try:
            distribution = {}
            for field_def in self.get_all_field_definitions():
                field_type = field_def.field_type.value
                distribution[field_type] = distribution.get(field_type, 0) + 1
            return distribution
        except Exception as e:
            logger.error(f"==liuq debug== 获取字段类型分布失败: {e}")
            return {}


# 全局整合服务实例
_integrated_service: Optional[IntegratedFieldProcessingService] = None


def get_integrated_field_processing_service() -> IntegratedFieldProcessingService:
    """获取字段处理器整合服务实例"""
    global _integrated_service
    
    if _integrated_service is None:
        _integrated_service = IntegratedFieldProcessingService()
        logger.info("==liuq debug== 创建字段处理器整合服务实例")
    
    return _integrated_service