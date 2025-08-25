#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML数据转换服务
==liuq debug== FastMapV2 XML数据转换服务

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: XML数据类型转换和解析服务，从XMLParserService中拆分
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Union, Optional, Tuple
from pathlib import Path

from core.models.map_data import (
    MapPoint, BaseBoundary,
    XML_FIELD_CONFIG, XMLFieldNodeType, XMLFieldDataType,
    parse_field_value, get_fields_by_node_type
)
from core.services.shared.field_registry_service import field_registry

logger = logging.getLogger(__name__)


class XMLDataConversionService:
    """
    XML数据转换服务
    
    专门负责XML数据的类型转换和解析功能：
    - 字段值类型转换
    - 坐标数据提取和转换
    - 范围数据解析
    - 多边形数据处理
    - 详细参数提取
    """
    
    def __init__(self):
        """初始化XML数据转换服务"""
        self.supported_coordinate_types = ['offset', 'absolute', 'relative']
        self.supported_range_fields = ['bv', 'ir', 'cct', 'ctemp', 'ac', 'count', 'color_cct', 'diff_ctemp', 'face_ctemp']
        logger.debug("==liuq debug== XML数据转换服务初始化完成")
    
    def extract_offset_coordinates(self, first_node: ET.Element) -> Tuple[float, float]:
        """
        从第一组数据提取offset坐标
        
        Args:
            first_node: 第一个XML节点（包含offset数据）
            
        Returns:
            Tuple[float, float]: (x, y) 坐标对
        """
        try:
            offset_node = first_node.find('offset')
            if offset_node is not None:
                x_node = offset_node.find('x')
                y_node = offset_node.find('y')

                x = float(x_node.text) if x_node is not None and x_node.text else 0.0
                y = float(y_node.text) if y_node is not None and y_node.text else 0.0

                logger.debug(f"==liuq debug== 提取offset坐标: ({x}, {y})")
                return x, y
                
            return 0.0, 0.0
            
        except Exception as e:
            logger.warning(f"==liuq debug== 提取offset坐标失败: {e}")
            return 0.0, 0.0
    
    def extract_polygon_coordinates(self, second_node: ET.Element) -> Tuple[List[Tuple[float, float]], bool]:
        """
        从第二组数据提取多边形坐标
        
        Args:
            second_node: 第二个XML节点（包含多边形数据）
            
        Returns:
            Tuple[List[Tuple[float, float]], bool]: (顶点列表, 是否为多边形)
        """
        try:
            rpg_node = second_node.find('RpG')
            bpg_node = second_node.find('BpG')

            if rpg_node is not None and bpg_node is not None and rpg_node.text and bpg_node.text:
                rpg_values = [float(x) for x in rpg_node.text.split()]
                bpg_values = [float(x) for x in bpg_node.text.split()]

                if len(rpg_values) == len(bpg_values) and len(rpg_values) > 0:
                    vertices = list(zip(rpg_values, bpg_values))
                    logger.debug(f"==liuq debug== 提取多边形坐标: {len(vertices)} 个顶点")
                    return vertices, True

            return [], False
            
        except Exception as e:
            logger.warning(f"==liuq debug== 提取多边形坐标失败: {e}")
            return [], False
    
    def calculate_polygon_centroid(self, vertices: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        计算多边形重心坐标
        
        Args:
            vertices: 多边形顶点列表
            
        Returns:
            Tuple[float, float]: 重心坐标 (x, y)
        """
        try:
            if not vertices:
                return 0.0, 0.0
            
            x_sum = sum(vertex[0] for vertex in vertices)
            y_sum = sum(vertex[1] for vertex in vertices)
            count = len(vertices)
            
            centroid_x = x_sum / count
            centroid_y = y_sum / count
            
            logger.debug(f"==liuq debug== 计算多边形重心: ({centroid_x}, {centroid_y})")
            return centroid_x, centroid_y
            
        except Exception as e:
            logger.warning(f"==liuq debug== 计算多边形重心失败: {e}")
            return 0.0, 0.0
    
    def extract_range_data_from_node(self, first_node: ET.Element) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], bool]:
        """
        从第一组数据提取范围数据（使用配置驱动）
        
        Args:
            first_node: 第一个XML节点（包含range数据）
            
        Returns:
            Tuple: (bv_range, ir_range, cct_range, detect_flag)
        """
        try:
            range_node = first_node.find('range')
            if range_node is None:
                return (0.0, 100.0), (0.0, 100.0), (2000.0, 10000.0), False

            # 使用配置驱动的方式提取范围数据
            bv_range = self.extract_field_range(range_node, 'bv_min', 'bv_max')
            ir_range = self.extract_field_range(range_node, 'ir_min', 'ir_max')
            cct_range = self.extract_field_range(range_node, 'color_cct_min', 'color_cct_max')

            # 提取检测标志
            detect_flag = self.extract_detect_flag(range_node)

            logger.debug(f"==liuq debug== 提取范围数据: BV{bv_range}, IR{ir_range}, CCT{cct_range}, DetectFlag={detect_flag}")
            return bv_range, ir_range, cct_range, detect_flag

        except Exception as e:
            logger.warning(f"==liuq debug== 提取范围数据失败: {e}")
            return (0.0, 100.0), (0.0, 100.0), (2000.0, 10000.0), False
    
    def extract_field_range(self, range_node: ET.Element, min_field: str, max_field: str) -> Tuple[float, float]:
        """
        使用配置驱动的方式提取字段范围
        
        Args:
            range_node: range XML节点
            min_field: 最小值字段名
            max_field: 最大值字段名
            
        Returns:
            Tuple[float, float]: (min_value, max_value) 元组
        """
        try:
            # 获取字段配置
            min_config = XML_FIELD_CONFIG.get(min_field)
            max_config = XML_FIELD_CONFIG.get(max_field)

            if not min_config or not max_config:
                logger.warning(f"==liuq debug== 字段配置未找到: {min_field}, {max_field}")
                return (0.0, 100.0)

            # 提取最小值和最大值
            min_value = self.extract_single_field_value(range_node, min_config)
            max_value = self.extract_single_field_value(range_node, max_config)

            return (min_value, max_value)

        except Exception as e:
            logger.warning(f"==liuq debug== 提取字段范围失败 {min_field}-{max_field}: {e}")
            return (0.0, 100.0)
    
    def extract_single_field_value(self, range_node: ET.Element, field_config) -> float:
        """
        提取单个字段值
        
        Args:
            range_node: range XML节点
            field_config: 字段配置
            
        Returns:
            float: 字段值
        """
        try:
            xml_path = field_config.xml_path

            if len(xml_path) == 1:
                # 单层路径（如ml）
                target_node = range_node.find(xml_path[0])
            elif len(xml_path) == 2:
                # 双层路径（如bv/min）
                parent_node = range_node.find(xml_path[0])
                if parent_node is not None:
                    target_node = parent_node.find(xml_path[1])
                else:
                    target_node = None
            else:
                target_node = None

            if target_node is not None and target_node.text:
                value = parse_field_value(target_node.text, field_config.field_name)
                logger.debug(f"==liuq debug== 提取字段值 {field_config.field_name}: {value}")
                return value
            else:
                return field_config.default_value

        except Exception as e:
            logger.warning(f"==liuq debug== 提取单个字段值失败 {field_config.field_name}: {e}")
            return field_config.default_value
    
    def extract_detect_flag(self, range_node: ET.Element) -> bool:
        """
        提取检测标志
        
        Args:
            range_node: range XML节点
            
        Returns:
            bool: 检测标志值
        """
        try:
            detect_flag_node = range_node.find('DetectMapFlag')
            if detect_flag_node is not None and detect_flag_node.text:
                text_value = detect_flag_node.text.strip().lower()
                # 支持多种格式：'1', 'true', 'yes' 为True；'0', 'false', 'no' 为False
                detect_flag = text_value in ('1', 'true', 'yes')
                logger.debug(f"==liuq debug== 提取检测标志: {detect_flag} (原值: {detect_flag_node.text})")
                return detect_flag
            
            return False
            
        except Exception as e:
            logger.warning(f"==liuq debug== 提取检测标志失败: {e}")
            return False
    
    def extract_detailed_parameters(self, node: ET.Element) -> Dict[str, float]:
        """
        提取详细参数（使用配置驱动）
        
        Args:
            node: XML节点
            
        Returns:
            Dict[str, float]: 详细参数字典
        """
        params = {}

        try:
            range_node = node.find('range')
            if range_node is not None:
                # 使用配置驱动的方式提取所有range节点字段
                range_fields = get_fields_by_node_type(XMLFieldNodeType.RANGE)

                for field_name in range_fields:
                    if field_name in XML_FIELD_CONFIG:
                        config = XML_FIELD_CONFIG[field_name]

                        # 跳过offset字段（它们不在range节点中）
                        if config.node_type != XMLFieldNodeType.RANGE:
                            continue

                        try:
                            # 提取字段值
                            field_value = self.extract_single_field_value(range_node, config)
                            params[field_name] = field_value
                        except Exception as e:
                            logger.warning(f"==liuq debug== 提取字段 {field_name} 失败: {e}")
                            params[field_name] = config.default_value

                # ml字段保持原始值（修复数据转换bug）
                if 'ml' in params:
                    # 保持原始值，不进行转换
                    params['ml'] = int(params['ml'])

                # 提取DetectMapFlag（不在配置中的特殊字段）
                params['detect_map_flag'] = self.extract_detect_flag(range_node)

                # 添加ERatio字段（如果存在）
                e_ratio_params = self.extract_e_ratio_range(range_node)
                params.update(e_ratio_params)

            logger.debug(f"==liuq debug== 提取详细参数完成: {len(params)} 个参数")
            return params

        except Exception as e:
            logger.warning(f"==liuq debug== 提取详细参数失败: {e}")
            return params
    
    def extract_e_ratio_range(self, range_node: ET.Element) -> Dict[str, float]:
        """
        提取ERatio范围参数
        
        Args:
            range_node: range XML节点
            
        Returns:
            Dict[str, float]: ERatio参数字典
        """
        e_ratio_params = {}
        
        try:
            e_ratio_node = range_node.find('e_ratio')
            if e_ratio_node is not None:
                min_node = e_ratio_node.find('min')
                max_node = e_ratio_node.find('max')

                if min_node is not None and min_node.text:
                    try:
                        e_ratio_params['e_ratio_min'] = float(min_node.text)
                    except ValueError:
                        e_ratio_params['e_ratio_min'] = 0.0

                if max_node is not None and max_node.text:
                    try:
                        e_ratio_params['e_ratio_max'] = float(max_node.text)
                    except ValueError:
                        e_ratio_params['e_ratio_max'] = 0.0
                        
                logger.debug(f"==liuq debug== 提取ERatio范围: {e_ratio_params}")
            
            return e_ratio_params
            
        except Exception as e:
            logger.warning(f"==liuq debug== 提取ERatio范围失败: {e}")
            return {}
    
    def extract_map_point_data(self, map_elem: ET.Element) -> Dict[str, Any]:
        """
        从Map元素中提取数据
        
        Args:
            map_elem: Map XML元素
            
        Returns:
            Dict[str, Any]: 提取的数据字典
        """
        data = {}

        try:
            # 获取所有注册的字段定义
            field_definitions = field_registry.get_all_fields()

            for field_def in field_definitions:
                try:
                    # 使用XPath查找元素
                    xpath = field_def.xml_path.replace('./', './')
                    elem = map_elem.find(xpath)

                    if elem is not None and elem.text is not None:
                        # 获取元素值并进行类型转换
                        raw_value = elem.text.strip()
                        converted_value = field_def.convert_value(raw_value)
                        data[field_def.field_id] = converted_value
                    else:
                        # 使用默认值
                        data[field_def.field_id] = field_def.default_value

                except Exception as e:
                    logger.warning(f"==liuq debug== 提取字段 {field_def.field_id} 失败: {e}")
                    data[field_def.field_id] = field_def.default_value

            # 特殊处理：如果没有找到offset坐标，使用x,y坐标
            if data.get('offset_x') == 0.0 and data.get('x', 0.0) != 0.0:
                data['offset_x'] = data.get('x', 0.0)
            if data.get('offset_y') == 0.0 and data.get('y', 0.0) != 0.0:
                data['offset_y'] = data.get('y', 0.0)

            logger.debug(f"==liuq debug== 提取Map点数据完成: {len(data)} 个字段")
            return data
            
        except Exception as e:
            logger.error(f"==liuq debug== 提取Map点数据失败: {e}")
            return {}
    
    def parse_boundary_value(self, boundary_elem: ET.Element) -> float:
        """
        解析边界值
        
        Args:
            boundary_elem: 边界XML元素
            
        Returns:
            float: 边界值
        """
        try:
            if boundary_elem is not None and boundary_elem.text:
                # 如果是多个值，取第一个
                values = boundary_elem.text.strip().split()
                if values:
                    value = float(values[0])
                    logger.debug(f"==liuq debug== 解析边界值: {value}")
                    return value
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"==liuq debug== 解析边界值失败: {e}")
            return 0.0
    
    def extract_trans_step(self, second_node: ET.Element) -> int:
        """
        提取TransStep值
        
        Args:
            second_node: 第二个XML节点
            
        Returns:
            int: TransStep值
        """
        try:
            trans_step_node = second_node.find('TransStep')
            if trans_step_node is not None and trans_step_node.text:
                trans_step = int(trans_step_node.text)
                logger.debug(f"==liuq debug== 提取TransStep: {trans_step}")
                return trans_step
            
            return 0
            
        except Exception as e:
            logger.warning(f"==liuq debug== 提取TransStep失败: {e}")
            return 0
    
    def extract_weight(self, first_node: ET.Element) -> float:
        """
        提取权重值
        
        Args:
            first_node: 第一个XML节点
            
        Returns:
            float: 权重值
        """
        try:
            weight_node = first_node.find('weight')
            if weight_node is not None and weight_node.text:
                weight = float(weight_node.text)
                logger.debug(f"==liuq debug== 提取权重: {weight}")
                return weight
            
            return 1.0
            
        except Exception as e:
            logger.warning(f"==liuq debug== 提取权重失败: {e}")
            return 1.0
    
    def extract_alias_name(self, second_node: ET.Element, default_name: str = "Unknown") -> str:
        """
        提取别名
        
        Args:
            second_node: 第二个XML节点
            default_name: 默认名称
            
        Returns:
            str: 别名
        """
        try:
            alias_node = second_node.find('AliasName')
            if alias_node is not None and alias_node.text:
                alias_name = alias_node.text.strip()
                logger.debug(f"==liuq debug== 提取别名: {alias_name}")
                return alias_name
            
            return default_name
            
        except Exception as e:
            logger.warning(f"==liuq debug== 提取别名失败: {e}")
            return default_name
    
    def is_empty_offset_map(self, first_node: ET.Element, second_node: ET.Element) -> bool:
        """
        检查offset_map是否为空
        
        Args:
            first_node: 第一个XML节点
            second_node: 第二个XML节点
            
        Returns:
            bool: 是否为空Map
        """
        try:
            # 检查第一个节点是否有有效的offset数据
            offset_x, offset_y = self.extract_offset_coordinates(first_node)
            if offset_x != 0.0 or offset_y != 0.0:
                return False

            # 检查第一个节点是否有有效的range数据
            range_node = first_node.find('range')
            if range_node is not None:
                for elem in range_node.iter():
                    if elem.text and elem.text.strip():
                        try:
                            value = float(elem.text.strip())
                            if value != 0.0:
                                return False
                        except ValueError:
                            pass

            # 检查是否有多边形坐标
            polygon_vertices, is_polygon = self.extract_polygon_coordinates(second_node)
            if is_polygon and polygon_vertices:
                return False

            # 如果以上条件都不满足，才认为是空Map
            logger.debug("==liuq debug== 检测到空offset_map")
            return True

        except Exception as e:
            logger.warning(f"==liuq debug== 检查空offset_map失败: {e}")
            return False
    
    def convert_field_value_to_type(self, value: Any, target_type: XMLFieldDataType) -> Any:
        """
        将字段值转换为指定类型
        
        Args:
            value: 原始值
            target_type: 目标数据类型
            
        Returns:
            Any: 转换后的值
        """
        try:
            if value is None:
                return None
            
            if target_type == XMLFieldDataType.INTEGER:
                return int(float(str(value)))
            elif target_type == XMLFieldDataType.FLOAT:
                return float(str(value))
            elif target_type == XMLFieldDataType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                str_value = str(value).lower()
                return str_value in ('1', 'true', 'yes')
            elif target_type == XMLFieldDataType.STRING:
                return str(value)
            else:
                return value
                
        except Exception as e:
            logger.warning(f"==liuq debug== 类型转换失败: {value} -> {target_type}, 错误: {e}")
            return value


# 全局数据转换服务实例
_conversion_service: Optional[XMLDataConversionService] = None


def get_xml_conversion_service() -> XMLDataConversionService:
    """获取XML数据转换服务实例"""
    global _conversion_service
    
    if _conversion_service is None:
        _conversion_service = XMLDataConversionService()
        logger.info("==liuq debug== 创建XML数据转换服务实例")
    
    return _conversion_service