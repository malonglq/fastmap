#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强字段处理器注册表
==liuq debug== FastMapV2 增强字段处理器注册表

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: 优化的字段处理器注册表，提供更强大的字段管理功能
"""

import logging
from typing import Dict, List, Any, Optional, Type, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from core.interfaces.xml_field_definition import XMLFieldDefinition, FieldType

logger = logging.getLogger(__name__)


class ProcessorType(Enum):
    """处理器类型枚举"""
    VALIDATOR = "validator"
    FORMATTER = "formatter"
    CONVERTER = "converter"
    PARSER = "parser"
    SERIALIZER = "serializer"


@dataclass
class ProcessorRegistration:
    """处理器注册信息"""
    processor_id: str
    processor_type: ProcessorType
    field_types: List[FieldType]
    priority: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IFieldProcessor(ABC):
    """字段处理器接口"""
    
    @abstractmethod
    def can_handle(self, field_definition: XMLFieldDefinition, context: Dict[str, Any] = None) -> bool:
        """检查是否能处理指定字段"""
        pass
    
    @abstractmethod
    def process(self, value: Any, field_definition: XMLFieldDefinition, context: Dict[str, Any] = None) -> Any:
        """处理字段值"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """获取处理器元数据"""
        pass


class BaseFieldProcessor(IFieldProcessor):
    """字段处理器基类"""
    
    def __init__(self, name: str, supported_types: List[FieldType]):
        self.name = name
        self.supported_types = supported_types
    
    def can_handle(self, field_definition: XMLFieldDefinition, context: Dict[str, Any] = None) -> bool:
        """默认实现：检查字段类型是否支持"""
        return field_definition.field_type in self.supported_types
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取处理器元数据"""
        return {
            "name": self.name,
            "supported_types": [t.value for t in self.supported_types],
            "description": getattr(self, '__doc__', '')
        }


class FieldValidator(BaseFieldProcessor):
    """字段验证器"""
    
    def __init__(self, name: str, supported_types: List[FieldType], 
                 validation_func: Callable[[Any, XMLFieldDefinition], bool]):
        super().__init__(name, supported_types)
        self.validation_func = validation_func
    
    def process(self, value: Any, field_definition: XMLFieldDefinition, context: Dict[str, Any] = None) -> bool:
        """验证字段值"""
        try:
            return self.validation_func(value, field_definition)
        except Exception as e:
            logger.error(f"==liuq debug== 字段验证失败: {field_definition.field_id} - {e}")
            return False


class FieldFormatter(BaseFieldProcessor):
    """字段格式化器"""
    
    def __init__(self, name: str, supported_types: List[FieldType],
                 format_func: Callable[[Any, XMLFieldDefinition], str]):
        super().__init__(name, supported_types)
        self.format_func = format_func
    
    def process(self, value: Any, field_definition: XMLFieldDefinition, context: Dict[str, Any] = None) -> str:
        """格式化字段值"""
        try:
            return self.format_func(value, field_definition)
        except Exception as e:
            logger.error(f"==liuq debug== 字段格式化失败: {field_definition.field_id} - {e}")
            return str(value) if value is not None else ""


class FieldConverter(BaseFieldProcessor):
    """字段转换器"""
    
    def __init__(self, name: str, supported_types: List[FieldType],
                 convert_func: Callable[[Any, XMLFieldDefinition], Any]):
        super().__init__(name, supported_types)
        self.convert_func = convert_func
    
    def process(self, value: Any, field_definition: XMLFieldDefinition, context: Dict[str, Any] = None) -> Any:
        """转换字段值"""
        try:
            return self.convert_func(value, field_definition)
        except Exception as e:
            logger.error(f"==liuq debug== 字段转换失败: {field_definition.field_id} - {e}")
            return value


class EnhancedFieldProcessorRegistry:
    """
    增强字段处理器注册表
    
    提供强大的字段处理器管理功能：
    - 多类型处理器注册
    - 优先级管理
    - 链式处理
    - 插件化扩展
    """
    
    def __init__(self):
        """初始化注册表"""
        self._processors: Dict[ProcessorType, Dict[str, IFieldProcessor]] = {
            ProcessorType.VALIDATOR: {},
            ProcessorType.FORMATTER: {},
            ProcessorType.CONVERTER: {},
            ProcessorType.PARSER: {},
            ProcessorType.SERIALIZER: {}
        }
        
        self._registrations: Dict[str, ProcessorRegistration] = {}
        self._field_type_cache: Dict[FieldType, Dict[ProcessorType, List[str]]] = {}
        
        # 注册默认处理器
        self._register_default_processors()
        
        logger.info("==liuq debug== 增强字段处理器注册表初始化完成")
    
    def register_processor(self, processor: IFieldProcessor, registration: ProcessorRegistration) -> bool:
        """
        注册字段处理器
        
        Args:
            processor: 处理器实例
            registration: 注册信息
            
        Returns:
            bool: 注册是否成功
        """
        try:
            processor_type = registration.processor_type
            processor_id = registration.processor_id
            
            # 检查是否已存在
            if processor_id in self._processors[processor_type]:
                logger.warning(f"==liuq debug== 处理器已存在，将被覆盖: {processor_id}")
            
            # 注册处理器
            self._processors[processor_type][processor_id] = processor
            self._registrations[processor_id] = registration
            
            # 清除缓存
            self._field_type_cache.clear()
            
            logger.info(f"==liuq debug== 处理器注册成功: {processor_id} ({processor_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理器注册失败: {e}")
            return False
    
    def unregister_processor(self, processor_id: str) -> bool:
        """
        注销处理器
        
        Args:
            processor_id: 处理器ID
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if processor_id not in self._registrations:
                logger.warning(f"==liuq debug== 处理器不存在: {processor_id}")
                return False
            
            registration = self._registrations[processor_id]
            processor_type = registration.processor_type
            
            # 移除处理器
            if processor_id in self._processors[processor_type]:
                del self._processors[processor_type][processor_id]
            
            del self._registrations[processor_id]
            
            # 清除缓存
            self._field_type_cache.clear()
            
            logger.info(f"==liuq debug== 处理器注销成功: {processor_id}")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理器注销失败: {e}")
            return False
    
    def get_processors(self, processor_type: ProcessorType, 
                      field_definition: XMLFieldDefinition = None) -> List[IFieldProcessor]:
        """
        获取指定类型的处理器
        
        Args:
            processor_type: 处理器类型
            field_definition: 字段定义（可选，用于过滤）
            
        Returns:
            List[IFieldProcessor]: 处理器列表
        """
        try:
            processors = list(self._processors[processor_type].values())
            
            # 如果提供了字段定义，过滤支持的处理器
            if field_definition:
                processors = [p for p in processors if p.can_handle(field_definition)]
            
            # 按优先级排序
            def get_priority(processor):
                for reg in self._registrations.values():
                    if reg.processor_type == processor_type:
                        # 找到对应的注册信息
                        for pid, p in self._processors[processor_type].items():
                            if p is processor:
                                return self._registrations[pid].priority
                return 0
            
            processors.sort(key=get_priority, reverse=True)
            return processors
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取处理器失败: {e}")
            return []
    
    def process_field(self, value: Any, field_definition: XMLFieldDefinition,
                     processor_type: ProcessorType, context: Dict[str, Any] = None) -> Any:
        """
        处理字段值
        
        Args:
            value: 字段值
            field_definition: 字段定义
            processor_type: 处理器类型
            context: 上下文信息
            
        Returns:
            Any: 处理后的值
        """
        try:
            processors = self.get_processors(processor_type, field_definition)
            
            if not processors:
                logger.debug(f"==liuq debug== 未找到合适的{processor_type.value}处理器: {field_definition.field_id}")
                return value
            
            # 使用第一个匹配的处理器
            processor = processors[0]
            result = processor.process(value, field_definition, context)
            
            logger.debug(f"==liuq debug== 字段处理完成: {field_definition.field_id} ({processor_type.value})")
            return result
            
        except Exception as e:
            logger.error(f"==liuq debug== 字段处理失败: {field_definition.field_id} - {e}")
            return value
    
    def validate_field(self, value: Any, field_definition: XMLFieldDefinition) -> bool:
        """验证字段值"""
        return self.process_field(value, field_definition, ProcessorType.VALIDATOR)
    
    def format_field(self, value: Any, field_definition: XMLFieldDefinition) -> str:
        """格式化字段值"""
        return self.process_field(value, field_definition, ProcessorType.FORMATTER)
    
    def convert_field(self, value: Any, field_definition: XMLFieldDefinition) -> Any:
        """转换字段值"""
        return self.process_field(value, field_definition, ProcessorType.CONVERTER)
    
    def get_processor_info(self) -> Dict[str, Any]:
        """获取处理器注册信息"""
        info = {
            "total_processors": len(self._registrations),
            "by_type": {},
            "processors": []
        }
        
        for processor_type in ProcessorType:
            count = len(self._processors[processor_type])
            info["by_type"][processor_type.value] = count
        
        for processor_id, registration in self._registrations.items():
            processor = self._processors[registration.processor_type][processor_id]
            info["processors"].append({
                "id": processor_id,
                "type": registration.processor_type.value,
                "priority": registration.priority,
                "supported_types": [t.value for t in registration.field_types],
                "metadata": processor.get_metadata()
            })
        
        return info
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取处理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            # 复用get_processor_info的结果
            info = self.get_processor_info()
            
            # 添加额外的统计信息
            stats = {
                "total_processors": info["total_processors"],
                "by_type": info["by_type"],
                "total_registrations": len(self._registrations),
                "supported_field_types": len(set(
                    ft for reg in self._registrations.values() 
                    for ft in reg.field_types
                ))
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取处理器统计信息失败: {e}")
            return {"error": str(e)}
    
    def export_configuration(self, file_path: Path) -> bool:
        """
        导出处理器配置
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            config = {
                "version": "1.0",
                "exported_at": str(Path().absolute()),
                "processors": self.get_processor_info()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"==liuq debug== 处理器配置导出成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理器配置导出失败: {e}")
            return False
    
    def _register_default_processors(self):
        """注册默认处理器"""
        # 字符串验证器
        string_validator = FieldValidator(
            "string_validator",
            [FieldType.STRING],
            lambda value, field_def: isinstance(value, str) or value is None
        )
        self.register_processor(string_validator, ProcessorRegistration(
            "string_validator", ProcessorType.VALIDATOR, [FieldType.STRING], priority=10
        ))
        
        # 数值验证器
        number_validator = FieldValidator(
            "number_validator",
            [FieldType.INTEGER, FieldType.FLOAT],
            lambda value, field_def: isinstance(value, (int, float)) or value is None
        )
        self.register_processor(number_validator, ProcessorRegistration(
            "number_validator", ProcessorType.VALIDATOR, [FieldType.INTEGER, FieldType.FLOAT], priority=10
        ))
        
        # 布尔验证器
        bool_validator = FieldValidator(
            "bool_validator",
            [FieldType.BOOLEAN],
            lambda value, field_def: isinstance(value, bool) or value is None
        )
        self.register_processor(bool_validator, ProcessorRegistration(
            "bool_validator", ProcessorType.VALIDATOR, [FieldType.BOOLEAN], priority=10
        ))
        
        # 字符串格式化器
        string_formatter = FieldFormatter(
            "string_formatter",
            [FieldType.STRING],
            lambda value, field_def: str(value) if value is not None else ""
        )
        self.register_processor(string_formatter, ProcessorRegistration(
            "string_formatter", ProcessorType.FORMATTER, [FieldType.STRING], priority=10
        ))
        
        # 数值格式化器
        number_formatter = FieldFormatter(
            "number_formatter",
            [FieldType.INTEGER, FieldType.FLOAT],
            self._format_number_value
        )
        self.register_processor(number_formatter, ProcessorRegistration(
            "number_formatter", ProcessorType.FORMATTER, [FieldType.INTEGER, FieldType.FLOAT], priority=10
        ))
        
        # 布尔格式化器
        bool_formatter = FieldFormatter(
            "bool_formatter",
            [FieldType.BOOLEAN],
            lambda value, field_def: "是" if value else "否"
        )
        self.register_processor(bool_formatter, ProcessorRegistration(
            "bool_formatter", ProcessorType.FORMATTER, [FieldType.BOOLEAN], priority=10
        ))
        
        # 类型转换器
        string_converter = FieldConverter(
            "string_converter",
            [FieldType.STRING],
            lambda value, field_def: str(value) if value is not None else ""
        )
        self.register_processor(string_converter, ProcessorRegistration(
            "string_converter", ProcessorType.CONVERTER, [FieldType.STRING], priority=10
        ))
        
        integer_converter = FieldConverter(
            "integer_converter",
            [FieldType.INTEGER],
            self._convert_to_integer
        )
        self.register_processor(integer_converter, ProcessorRegistration(
            "integer_converter", ProcessorType.CONVERTER, [FieldType.INTEGER], priority=10
        ))
        
        float_converter = FieldConverter(
            "float_converter",
            [FieldType.FLOAT],
            self._convert_to_float
        )
        self.register_processor(float_converter, ProcessorRegistration(
            "float_converter", ProcessorType.CONVERTER, [FieldType.FLOAT], priority=10
        ))
        
        bool_converter = FieldConverter(
            "bool_converter",
            [FieldType.BOOLEAN],
            self._convert_to_boolean
        )
        self.register_processor(bool_converter, ProcessorRegistration(
            "bool_converter", ProcessorType.CONVERTER, [FieldType.BOOLEAN], priority=10
        ))
        
        logger.info("==liuq debug== 默认字段处理器注册完成")
    
    def _format_number_value(self, value: Any, field_definition: XMLFieldDefinition) -> str:
        """格式化数值"""
        if value is None:
            return ""
        
        try:
            if field_definition.field_type == FieldType.INTEGER:
                return str(int(value))
            elif field_definition.field_type == FieldType.FLOAT:
                # 特殊处理：如果是整数值，显示为整数
                if isinstance(value, float) and value.is_integer():
                    return str(int(value))
                else:
                    return f"{float(value):.3f}"
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)
    
    def _convert_to_integer(self, value: Any, field_definition: XMLFieldDefinition) -> int:
        """转换为整数"""
        if value is None:
            return 0
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return 0
    
    def _convert_to_float(self, value: Any, field_definition: XMLFieldDefinition) -> float:
        """转换为浮点数"""
        if value is None:
            return 0.0
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return 0.0
    
    def _convert_to_boolean(self, value: Any, field_definition: XMLFieldDefinition) -> bool:
        """转换为布尔值"""
        if value is None:
            return False
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, (int, float)):
            return value != 0
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on', '是')
        
        return bool(value)


# 全局字段处理器注册表实例
_field_processor_registry: Optional[EnhancedFieldProcessorRegistry] = None


def get_field_processor_registry() -> EnhancedFieldProcessorRegistry:
    """获取字段处理器注册表实例"""
    global _field_processor_registry
    
    if _field_processor_registry is None:
        _field_processor_registry = EnhancedFieldProcessorRegistry()
        logger.info("==liuq debug== 创建字段处理器注册表实例")
    
    return _field_processor_registry