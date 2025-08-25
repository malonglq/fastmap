#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML格式化服务

负责XML数据的格式化功能，包括数值格式化、字段格式化等

作者: AI Assistant
日期: 2025-08-25
"""

import logging
from typing import Any, Union, Optional
from decimal import Decimal
from core.models.map_data import (
    MapPoint, BaseBoundary, XML_FIELD_CONFIG, XMLFieldNodeType,
    format_field_value, get_map_point_field_value
)
from utils.number_formatter import format_decimal_precise

logger = logging.getLogger(__name__)


class XMLFormattingService:
    """XML格式化服务"""
    
    def __init__(self):
        """初始化XML格式化服务"""
        self.compiled_patterns = {}
        self._precompile_patterns()
        
    def _precompile_patterns(self):
        """预编译常用的正则表达式模式"""
        import re
        patterns = {
            'offset_x': r'(<x\s+[^>]*>)([^<]+)(<\/x>)',
            'offset_y': r'(<y\s+[^>]*>)([^<]+)(<\/y>)',
            'weight': r'(<weight\s+[^>]*>)([^<]+)(<\/weight>)',
            'rpg_boundary': r'(<RpG\s+[^>]*>)([^<]+)(<\/RpG>)',
            'bpg_boundary': r'(<BpG\s+[^>]*>)([^<]+)(<\/BpG>)',
        }

        for name, pattern in patterns.items():
            self.compiled_patterns[name] = re.compile(pattern)

    def format_number_for_xml(self, value) -> str:
        """
        智能数值格式化函数，用于XML写入

        采用业界验证的精度处理方案：
        1. 优先保持原始字符串精度（避免浮点转换损失）
        2. 使用Python Decimal库进行精确计算
        3. 智能处理整数和小数的显示格式
        4. 完全避免浮点精度问题

        Args:
            value: 数值（int, float或可转换为数值的字符串）

        Returns:
            str: 格式化后的字符串
        """
        try:
            if value is None:
                return "0"

            # 使用统一的格式化核心算法
            result = format_decimal_precise(value)
            return result

        except (ValueError, TypeError):
            # 如果转换失败，返回原始字符串
            result = str(value) if value is not None else "0"
            return result

    def format_field_value(self, field_value: Any, field_name: str) -> str:
        """
        格式化字段值为XML字符串

        Args:
            field_value: 字段值
            field_name: 字段名称

        Returns:
            str: 格式化后的字符串
        """
        return format_field_value(field_value, field_name)

    def format_map_point_data(self, map_point: MapPoint) -> dict:
        """
        格式化Map点数据为XML写入格式

        Args:
            map_point: Map点对象

        Returns:
            dict: 格式化后的字段数据字典
        """
        formatted_data = {}

        for field_name, config in XML_FIELD_CONFIG.items():
            try:
                # 获取字段值
                field_value = get_map_point_field_value(map_point, field_name)

                # 使用统一的格式化函数
                formatted_value = self.format_field_value(field_value, field_name)

                formatted_data[field_name] = {
                    'value': formatted_value,
                    'node_type': config.node_type.value,
                    'xml_path': config.xml_path
                }

            except Exception as e:
                logger.warning(f"格式化字段 {field_name} 失败: {e}")
                continue

        return formatted_data

    def format_boundary_data(self, boundary: BaseBoundary) -> dict:
        """
        格式化边界数据为XML写入格式

        Args:
            boundary: BaseBoundary对象

        Returns:
            dict: 格式化后的边界数据字典
        """
        formatted_data = {}

        # 格式化数值字段
        numeric_fields = ['x', 'y', 'offset_x', 'offset_y', 'weight']
        for field in numeric_fields:
            if hasattr(boundary, field):
                value = getattr(boundary, field)
                formatted_data[field] = self.format_number_for_xml(value)

        # 格式化范围字段
        range_fields = ['bv_range', 'ir_range', 'cct_range']
        for field in range_fields:
            if hasattr(boundary, field):
                range_value = getattr(boundary, field)
                if range_value and isinstance(range_value, tuple) and len(range_value) == 2:
                    min_val, max_val = range_value
                    formatted_data[field] = f"{self.format_number_for_xml(min_val)},{self.format_number_for_xml(max_val)}"
                else:
                    formatted_data[field] = ""

        # 格式化布尔字段
        if hasattr(boundary, 'detect_flag'):
            formatted_data['detect_flag'] = str(boundary.detect_flag).lower()

        return formatted_data

    def validate_formatted_value(self, value: str, field_type: str) -> bool:
        """
        验证格式化后的值是否有效

        Args:
            value: 格式化后的字符串值
            field_type: 字段类型

        Returns:
            bool: 值是否有效
        """
        try:
            if field_type in ['number', 'float', 'integer']:
                # 尝试转换为数值
                float(value)
                return True
            elif field_type == 'boolean':
                return value.lower() in ['true', 'false', '1', '0']
            elif field_type == 'range':
                # 范围格式应为 "min,max"
                parts = value.split(',')
                if len(parts) == 2:
                    float(parts[0].strip())
                    float(parts[1].strip())
                    return True
                return False
            else:
                # 字符串类型总是有效
                return True

        except (ValueError, TypeError):
            return False

    def get_field_xml_path(self, field_name: str) -> tuple:
        """
        获取字段的XML路径

        Args:
            field_name: 字段名称

        Returns:
            tuple: XML路径元组
        """
        if field_name in XML_FIELD_CONFIG:
            return XML_FIELD_CONFIG[field_name].xml_path
        return ()

    def get_field_node_type(self, field_name: str) -> XMLFieldNodeType:
        """
        获取字段的节点类型

        Args:
            field_name: 字段名称

        Returns:
            XMLFieldNodeType: 节点类型
        """
        if field_name in XML_FIELD_CONFIG:
            return XML_FIELD_CONFIG[field_name].node_type
        return XMLFieldNodeType.UNKNOWN

    def format_xml_attribute(self, name: str, value: Any) -> str:
        """
        格式化XML属性

        Args:
            name: 属性名
            value: 属性值

        Returns:
            str: 格式化后的属性字符串
        """
        formatted_value = self.format_number_for_xml(value)
        return f'{name}="{formatted_value}"'

    def format_xml_element(self, tag: str, content: Any = None, 
                          attributes: dict = None) -> str:
        """
        格式化XML元素

        Args:
            tag: 标签名
            content: 元素内容
            attributes: 属性字典

        Returns:
            str: 格式化后的XML元素字符串
        """
        attr_str = ""
        if attributes:
            attr_parts = []
            for name, value in attributes.items():
                attr_parts.append(self.format_xml_attribute(name, value))
            attr_str = " " + " ".join(attr_parts)

        if content is None:
            return f"<{tag}{attr_str}/>"
        else:
            formatted_content = self.format_number_for_xml(content)
            return f"<{tag}{attr_str}>{formatted_content}</{tag}>"


# 全局格式化服务实例
_formatting_service: Optional[XMLFormattingService] = None


def get_xml_formatting_service() -> XMLFormattingService:
    """获取XML格式化服务实例"""
    global _formatting_service
    
    if _formatting_service is None:
        _formatting_service = XMLFormattingService()
        logger.info("创建XML格式化服务实例")
    
    return _formatting_service