#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML验证服务
==liuq debug== FastMapV2 XML验证服务

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: XML文件结构和内容验证服务，从XMLParserService中拆分
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Union, Optional
from pathlib import Path

from core.interfaces.xml_data_processor import (
    ValidationLevel, ValidationResult, XMLParseError, ValidationError
)
from core.models.map_data import MapPoint, XMLFieldDataType

logger = logging.getLogger(__name__)


class XMLValidationService:
    """
    XML验证服务
    
    专门负责XML文件的验证功能：
    - 文件存在性验证
    - XML格式验证
    - 结构完整性验证
    - 内容有效性验证
    """
    
    def __init__(self):
        """初始化XML验证服务"""
        self.required_elements = ['base_boundary', 'offset_map']
        self.supported_versions = ["1.0", "1.1", "2.0"]
        logger.debug("==liuq debug== XML验证服务初始化完成")
    
    def validate_xml_file(self, xml_path: Union[str, Path], 
                         level: ValidationLevel = ValidationLevel.FULL) -> ValidationResult:
        """
        验证XML文件的结构和内容
        
        Args:
            xml_path: XML文件路径
            level: 验证级别
            
        Returns:
            ValidationResult: 验证结果对象
        """
        result = ValidationResult(
            is_valid=True,
            level=level,
            errors=[],
            warnings=[],
            metadata={}
        )
        
        try:
            xml_path = Path(xml_path)
            root = None

            # 基础验证
            if level.value in [ValidationLevel.BASIC.value, ValidationLevel.FULL.value]:
                if not self._validate_file_existence(xml_path, result):
                    return result

            # 结构验证
            if level.value in [ValidationLevel.STRUCTURE.value, ValidationLevel.FULL.value]:
                root = self._validate_xml_structure(xml_path, result)
                if not result.is_valid:
                    return result

            # 内容验证
            if level.value in [ValidationLevel.CONTENT.value, ValidationLevel.FULL.value]:
                if root is None:  # 如果还没有解析XML，先解析
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
                
                self._validate_xml_content(root, result)

            logger.debug(f"==liuq debug== XML验证完成: {xml_path}, 有效性: {result.is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"==liuq debug== XML验证失败: {e}")
            result.add_error(f"验证过程中发生错误: {e}")
            return result
    
    def validate_map_point(self, point: MapPoint) -> List[str]:
        """
        验证单个Map点的数据有效性
        
        Args:
            point: Map点对象
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        try:
            # 检查基本属性
            if not hasattr(point, 'alias_name') or not point.alias_name:
                errors.append("缺少别名")
            
            if not hasattr(point, 'x') or point.x is None:
                errors.append("缺少X坐标")
            elif not isinstance(point.x, (int, float)):
                errors.append("X坐标类型无效")
            
            if not hasattr(point, 'y') or point.y is None:
                errors.append("缺少Y坐标")
            elif not isinstance(point.y, (int, float)):
                errors.append("Y坐标类型无效")
            
            if not hasattr(point, 'weight') or point.weight is None:
                errors.append("缺少权重")
            elif not isinstance(point.weight, (int, float)):
                errors.append("权重类型无效")
            elif point.weight < 0:
                errors.append("权重不能为负数")
            
            # 检查范围值的有效性
            range_fields = ['bv_min', 'bv_max', 'ctemp_min', 'ctemp_max', 
                           'ir_min', 'ir_max', 'ac_min', 'ac_max']
            
            for field in range_fields:
                if hasattr(point, field):
                    value = getattr(point, field)
                    if value is not None and not isinstance(value, (int, float)):
                        errors.append(f"{field}类型无效")
            
            # 检查最小值不大于最大值
            min_max_pairs = [
                ('bv_min', 'bv_max'),
                ('ctemp_min', 'ctemp_max'),
                ('ir_min', 'ir_max'),
                ('ac_min', 'ac_max')
            ]
            
            for min_field, max_field in min_max_pairs:
                if (hasattr(point, min_field) and hasattr(point, max_field)):
                    min_val = getattr(point, min_field)
                    max_val = getattr(point, max_field)
                    if (min_val is not None and max_val is not None and 
                        min_val > max_val):
                        errors.append(f"{min_field}不应大于{max_field}")
            
            return errors
            
        except Exception as e:
            logger.error(f"==liuq debug== Map点验证失败: {e}")
            return [f"验证过程中发生错误: {e}"]
    
    def validate_field_value(self, value: Any, data_type: XMLFieldDataType) -> bool:
        """
        验证字段值的类型是否正确
        
        Args:
            value: 字段值
            data_type: 期望的数据类型
            
        Returns:
            bool: 值类型是否有效
        """
        try:
            if value is None:
                return True  # None值总是有效的
            
            if data_type == XMLFieldDataType.INTEGER:
                return isinstance(value, int) or (isinstance(value, float) and value.is_integer())
            elif data_type == XMLFieldDataType.FLOAT:
                return isinstance(value, (int, float))
            elif data_type == XMLFieldDataType.BOOLEAN:
                return isinstance(value, bool) or value in [0, 1, '0', '1', 'true', 'false', 'True', 'False']
            elif data_type == XMLFieldDataType.STRING:
                return isinstance(value, str)
            else:
                return True  # 未知类型总是有效
                
        except Exception as e:
            logger.error(f"==liuq debug== 字段值验证失败: {e}")
            return False
    
    def _validate_file_existence(self, xml_path: Path, result: ValidationResult) -> bool:
        """验证文件存在性"""
        if not xml_path.exists():
            result.add_error(f"文件不存在: {xml_path}")
            return False
        
        if not xml_path.is_file():
            result.add_error(f"路径不是文件: {xml_path}")
            return False
        
        # 检查文件大小
        file_size = xml_path.stat().st_size
        result.metadata['file_size'] = file_size
        
        if file_size == 0:
            result.add_error("文件为空")
            return False
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            result.add_warning("文件过大，可能影响解析性能")
        
        return True
    
    def _validate_xml_structure(self, xml_path: Path, result: ValidationResult) -> Optional[ET.Element]:
        """验证XML结构"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            result.metadata['root_tag'] = root.tag
            result.metadata['element_count'] = len(list(root.iter()))
            
            # 检查根元素
            if root.tag not in ['awb_scenario', 'root', 'configuration']:
                result.add_warning(f"根元素名称不常见: {root.tag}")
            
            # 检查必需的子元素
            missing_elements = []
            for required_elem in self.required_elements:
                if root.find(f".//{required_elem}") is None:
                    missing_elements.append(required_elem)
            
            if missing_elements:
                result.add_error(f"缺少必需元素: {', '.join(missing_elements)}")
                return None
            
            # 检查元素数量
            map_elements = root.findall(".//offset_map")
            result.metadata['map_element_count'] = len(map_elements)
            
            if len(map_elements) == 0:
                result.add_warning("未找到任何offset_map元素")
            elif len(map_elements) > 1000:
                result.add_warning("offset_map元素数量过多，可能影响性能")
            
            return root
            
        except ET.ParseError as e:
            result.add_error(f"XML格式错误: {e}")
            return None
        except Exception as e:
            result.add_error(f"结构验证失败: {e}")
            return None
    
    def _validate_xml_content(self, root: ET.Element, result: ValidationResult):
        """验证XML内容"""
        try:
            # 验证base_boundary内容
            base_boundary = root.find(".//base_boundary")
            if base_boundary is not None:
                boundary_errors = self._validate_base_boundary_content(base_boundary)
                for error in boundary_errors:
                    result.add_warning(f"base_boundary: {error}")
            
            # 验证offset_map内容
            offset_maps = root.findall(".//offset_map")
            invalid_maps = 0
            
            for i, offset_map in enumerate(offset_maps):
                map_errors = self._validate_offset_map_content(offset_map)
                if map_errors:
                    invalid_maps += 1
                    # 只报告前10个错误，避免日志过多
                    if i < 10:
                        for error in map_errors:
                            result.add_warning(f"offset_map[{i}]: {error}")
            
            result.metadata['invalid_map_count'] = invalid_maps
            result.metadata['valid_map_count'] = len(offset_maps) - invalid_maps
            
            if invalid_maps > len(offset_maps) * 0.5:  # 如果超过50%的Map无效
                result.add_error(f"过多无效的offset_map: {invalid_maps}/{len(offset_maps)}")
            
        except Exception as e:
            result.add_error(f"内容验证失败: {e}")
    
    def _validate_base_boundary_content(self, base_boundary: ET.Element) -> List[str]:
        """验证base_boundary内容"""
        errors = []
        
        # 检查是否有有效的坐标数据
        coordinate_elements = base_boundary.findall(".//x") + base_boundary.findall(".//y")
        if not coordinate_elements:
            errors.append("缺少坐标数据")
        
        # 检查坐标值的有效性
        for elem in coordinate_elements:
            if elem.text:
                try:
                    float(elem.text)
                except ValueError:
                    errors.append(f"无效的坐标值: {elem.text}")
        
        return errors
    
    def _validate_offset_map_content(self, offset_map: ET.Element) -> List[str]:
        """验证单个offset_map内容"""
        errors = []
        
        # 检查是否有必要的子元素
        if len(offset_map) < 2:
            errors.append("offset_map子元素数量不足")
            return errors
        
        first_node = offset_map[0]
        second_node = offset_map[1]
        
        # 验证第一个节点（坐标和范围数据）
        x_elem = first_node.find(".//x")
        y_elem = first_node.find(".//y")
        
        if x_elem is None or y_elem is None:
            errors.append("缺少坐标信息")
        else:
            # 验证坐标值
            try:
                if x_elem.text:
                    float(x_elem.text)
                if y_elem.text:
                    float(y_elem.text)
            except ValueError:
                errors.append("坐标值格式无效")
        
        # 验证第二个节点（多边形数据）
        polygon_data = second_node.findall(".//x") + second_node.findall(".//y")
        if len(polygon_data) < 6:  # 至少需要3个点(x,y)组成多边形
            errors.append("多边形数据不足")
        
        return errors


# 全局验证服务实例
_validation_service: Optional[XMLValidationService] = None


def get_xml_validation_service() -> XMLValidationService:
    """获取XML验证服务实例"""
    global _validation_service
    
    if _validation_service is None:
        _validation_service = XMLValidationService()
        logger.info("==liuq debug== 创建XML验证服务实例")
    
    return _validation_service