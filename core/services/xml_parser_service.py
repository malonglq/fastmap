#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML解析服务实现
==liuq debug== FastMapV2 XML解析服务核心实现

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 11:00:00 +08:00; Reason: P1-LD-005 实现XML解析服务; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 基于字段定义的动态XML解析服务实现
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime

from core.interfaces.xml_data_processor import (
    XMLDataProcessor,
    ValidationLevel,
    ValidationResult,
    XMLParseError,
    XMLWriteError,
    ValidationError,
    BackupError
)
from core.models.map_data import (
    MapConfiguration, MapPoint, BaseBoundary,
    XML_FIELD_CONFIG, XMLFieldNodeType, XMLFieldDataType,
    get_field_xml_path, get_field_node_type, get_field_data_type,
    parse_field_value, get_fields_by_node_type
)
from core.services.field_registry_service import field_registry

logger = logging.getLogger(__name__)


class XMLParserService(XMLDataProcessor):
    """
    XML解析服务实现
    
    基于字段注册系统的动态XML解析器，支持：
    - 基于字段定义的动态解析
    - 多种设备类型支持
    - 完整的错误处理和验证
    - 元数据提取和管理
    
    设计特点：
    - 依赖字段注册系统，支持动态字段
    - 保持向后兼容性
    - 提供详细的解析日志和错误信息
    """
    
    def __init__(self):
        """初始化XML解析服务"""
        self.supported_versions = ["1.0", "1.1", "2.0"]
        self.default_encoding = "utf-8"
        logger.info("==liuq debug== XML解析服务初始化完成")
    
    def parse_xml(self, xml_path: Union[str, Path], device_type: str = "unknown") -> MapConfiguration:
        """
        解析XML文件为MapConfiguration对象
        
        Args:
            xml_path: XML文件路径
            device_type: 设备类型 ('reference' | 'debug' | 'unknown')
            
        Returns:
            MapConfiguration: 解析后的配置对象
            
        Raises:
            XMLParseError: XML解析失败
            FileNotFoundError: 文件不存在
            PermissionError: 文件权限不足
        """
        try:
            xml_path = Path(xml_path)
            
            # 检查文件是否存在
            if not xml_path.exists():
                raise FileNotFoundError(f"XML文件不存在: {xml_path}")
            
            # 检查文件权限
            if not xml_path.is_file():
                raise PermissionError(f"路径不是文件: {xml_path}")
            
            logger.info(f"==liuq debug== 开始解析XML文件: {xml_path}")
            
            # 解析XML文件
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
            except ET.ParseError as e:
                raise XMLParseError(f"XML格式错误: {e}", getattr(e, 'lineno', None))
            
            # 提取基础边界数据
            base_boundary = self._extract_base_boundary(root)

            # 解析Map点（不包含base_boundary0）
            map_points = self._parse_map_points(root)

            # 单独解析base_boundary0作为MapPoint
            base_boundary_point = self._parse_base_boundary_as_map_point(root)

            # 提取元数据
            metadata = self._extract_metadata(root)
            metadata.update({
                'source_file': str(xml_path),
                'parse_time': datetime.now().isoformat(),
                'total_points': len(map_points),
                'has_base_boundary_point': base_boundary_point is not None
            })

            # 创建MapConfiguration对象
            config = MapConfiguration(
                device_type=device_type,
                base_boundary=base_boundary,
                map_points=map_points,
                base_boundary_point=base_boundary_point,
                metadata=metadata
            )
            
            logger.info(f"==liuq debug== XML解析完成: 共解析 {len(map_points)} 个Map点")
            return config
            
        except (FileNotFoundError, PermissionError):
            raise
        except XMLParseError:
            raise
        except Exception as e:
            logger.error(f"==liuq debug== XML解析失败: {e}")
            raise XMLParseError(f"解析过程中发生错误: {e}")
    
    def validate_xml(self, xml_path: Union[str, Path], 
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
            root = None  # 初始化root变量

            # 基础验证
            if level.value in [ValidationLevel.BASIC.value, ValidationLevel.FULL.value]:
                if not xml_path.exists():
                    result.add_error(f"文件不存在: {xml_path}")
                    return result

                if not xml_path.is_file():
                    result.add_error(f"路径不是文件: {xml_path}")
                    return result

            # 结构验证
            if level.value in [ValidationLevel.STRUCTURE.value, ValidationLevel.FULL.value]:
                try:
                    tree = ET.parse(xml_path)
                    root = tree.getroot()
                    result.metadata['root_tag'] = root.tag
                    result.metadata['element_count'] = len(list(root.iter()))
                except ET.ParseError as e:
                    result.add_error(f"XML格式错误: {e}")
                    return result

            # 内容验证
            if level.value in [ValidationLevel.CONTENT.value, ValidationLevel.FULL.value]:
                try:
                    # 如果还没有解析XML，先解析
                    if root is None:
                        tree = ET.parse(xml_path)
                        root = tree.getroot()

                    # 尝试解析Map点
                    map_points = self._parse_map_points(root)
                    result.metadata['map_point_count'] = len(map_points)

                    # 验证Map点数据
                    for i, point in enumerate(map_points):
                        point_errors = self._validate_map_point(point)
                        for error in point_errors:
                            result.add_warning(f"Map点 {i+1}: {error}")

                except Exception as e:
                    result.add_error(f"内容验证失败: {e}")
            
            logger.info(f"==liuq debug== XML验证完成: {xml_path}, 级别: {level.value}")
            return result
            
        except Exception as e:
            result.add_error(f"验证过程中发生错误: {e}")
            logger.error(f"==liuq debug== XML验证失败: {e}")
            return result
    
    def get_supported_versions(self) -> List[str]:
        """
        获取支持的XML版本列表
        
        Returns:
            List[str]: 支持的版本列表
        """
        return self.supported_versions.copy()
    
    def get_xml_metadata(self, xml_path: Union[str, Path]) -> Dict[str, Any]:
        """
        获取XML文件的元数据信息
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = {}
        
        try:
            xml_path = Path(xml_path)
            
            # 文件基本信息
            if xml_path.exists():
                stat = xml_path.stat()
                metadata.update({
                    'file_size': stat.st_size,
                    'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'file_name': xml_path.name,
                    'file_path': str(xml_path.absolute())
                })
            
            # XML结构信息
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                
                metadata.update({
                    'root_tag': root.tag,
                    'element_count': len(list(root.iter())),
                    'encoding': tree.docinfo.encoding if hasattr(tree, 'docinfo') else 'unknown'
                })
                
                # 提取版本信息
                version_elem = root.find('.//version')
                if version_elem is not None:
                    metadata['xml_version'] = version_elem.text
                
                # 统计Map点数量
                map_elements = root.findall('.//Map')
                metadata['map_count'] = len(map_elements)
                
            except ET.ParseError as e:
                metadata['parse_error'] = str(e)
            

            return metadata
            
        except Exception as e:
            logger.error(f"==liuq debug== 提取XML元数据失败: {e}")
            return {'error': str(e)}
    



    def write_xml(self, config: MapConfiguration, xml_path: Union[str, Path],
                  backup: bool = True, preserve_format: bool = True) -> bool:
        """
        将MapConfiguration对象写入XML文件（委托给XMLWriterService）

        Args:
            config: 要写入的配置对象
            xml_path: 目标XML文件路径
            backup: 是否创建备份文件
            preserve_format: 是否保持原有格式

        Returns:
            bool: 写入是否成功
        """
        from core.services.xml_writer_service import XMLWriterService
        return XMLWriterService().write_xml(config, xml_path, backup, preserve_format)

    def backup_xml(self, xml_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> str:
        """
        创建XML文件备份（委托给XMLWriterService）

        Args:
            xml_path: 源XML文件路径
            backup_dir: 备份目录，None则使用默认备份目录

        Returns:
            str: 备份文件路径
        """
        from core.services.xml_writer_service import XMLWriterService
        return XMLWriterService().backup_xml(xml_path, backup_dir)

    def restore_from_backup(self, backup_path: Union[str, Path],
                           target_path: Union[str, Path]) -> bool:
        """
        从备份恢复XML文件（委托给XMLWriterService）

        Args:
            backup_path: 备份文件路径
            target_path: 目标文件路径

        Returns:
            bool: 恢复是否成功
        """
        from core.services.xml_writer_service import XMLWriterService
        return XMLWriterService().restore_from_backup(backup_path, target_path)

    def _parse_map_points(self, root: ET.Element) -> List[MapPoint]:
        """
        解析Map点数据 - 使用正确的offset_map双组数据结构

        Args:
            root: XML根元素

        Returns:
            List[MapPoint]: Map点列表
        """
        map_points = []

        try:
            # 注意：base_boundary0不添加到map_points中，而是单独处理
            # 这样可以确保base_boundary0固定在第0行，不参与排序
            logger.info("==liuq debug== 开始解析offset_map节点（base_boundary0将单独处理）")

            # 然后处理offset_map01到offset_map116（按照真实XML结构）
            for i in range(1, 117):
                formatted_i = f"0{i}" if i < 10 else str(i)
                offset_map_nodes = root.findall(f'.//offset_map{formatted_i}')

                if len(offset_map_nodes) >= 2:
                    try:
                        map_point = self._parse_single_offset_map(offset_map_nodes, formatted_i)
                        if map_point:
                            map_points.append(map_point)
                    except Exception as e:
                        logger.warning(f"==liuq debug== 解析offset_map{formatted_i}失败: {e}")
                        continue
                else:
                    # 如果找不到节点，可能已经到达末尾
                    break

            logger.info(f"==liuq debug== 成功解析 {len(map_points)} 个Map点（包含base_boundary）")
            return map_points

        except Exception as e:
            logger.error(f"==liuq debug== 解析Map点数据失败: {e}")
            return map_points

    def _parse_single_offset_map(self, offset_map_nodes: List[ET.Element], map_id: str) -> Optional[MapPoint]:
        """
        解析单个offset_map的双组数据结构

        Args:
            offset_map_nodes: offset_map节点列表（应该有2个节点）
            map_id: Map ID

        Returns:
            MapPoint对象或None
        """
        try:
            # 第一个节点包含offset、range、weight等信息（第一组数据）
            first_node = offset_map_nodes[0]
            # 第二个节点包含AliasName、RpG、BpG等信息（第二组数据）
            second_node = offset_map_nodes[1]

            # 检查是否为空Map
            if self._is_empty_offset_map(first_node, second_node):

                return None

            # 从第二组数据提取别名
            alias_node = second_node.find('AliasName')
            alias_name = alias_node.text if alias_node is not None and alias_node.text else f"Map_{map_id}"

            # 从第一组数据提取offset坐标
            offset_x, offset_y = self._extract_offset_coordinates(first_node)

            # 从第二组数据提取多边形坐标（如果有）
            polygon_vertices, is_polygon = self._extract_polygon_coordinates(second_node)

            # 确定最终坐标
            if is_polygon and polygon_vertices:
                # 计算多边形重心作为代表坐标
                x = sum(vertex[0] for vertex in polygon_vertices) / len(polygon_vertices)
                y = sum(vertex[1] for vertex in polygon_vertices) / len(polygon_vertices)
            else:
                # 使用offset坐标
                x, y = offset_x, offset_y

            # 从第二组数据提取TransStep值
            trans_step_node = second_node.find('TransStep')
            trans_step = int(trans_step_node.text) if trans_step_node is not None and trans_step_node.text else 0

            # 从第一组数据提取权重
            weight_node = first_node.find('weight')
            weight = float(weight_node.text) if weight_node is not None and weight_node.text else 1.0

            # 从第一组数据提取范围数据
            bv_range, ir_range, cct_range, detect_flag = self._extract_range_data_from_node(first_node)

            # 从第一组数据提取详细参数
            detailed_params = self._extract_detailed_parameters(first_node)

            # 创建MapPoint对象
            map_point = MapPoint(
                alias_name=alias_name,
                x=x,
                y=y,
                offset_x=offset_x,
                offset_y=offset_y,
                weight=weight,
                trans_step=trans_step,
                bv_range=bv_range,
                ir_range=ir_range,
                cct_range=cct_range,
                ctemp_range=(detailed_params.get('ctemp_min', 0.0), detailed_params.get('ctemp_max', 0.0)),
                e_ratio_range=(detailed_params.get('e_ratio_min', 0.0), detailed_params.get('e_ratio_max', 0.0)),
                ac_range=(detailed_params.get('ac_min', 0.0), detailed_params.get('ac_max', 0.0)),
                count_range=(detailed_params.get('count_min', 0.0), detailed_params.get('count_max', 0.0)),
                color_cct_range=(detailed_params.get('color_cct_min', 0.0), detailed_params.get('color_cct_max', 0.0)),
                diff_ctemp_range=(detailed_params.get('diff_ctemp_min', 0.0), detailed_params.get('diff_ctemp_max', 0.0)),
                face_ctemp_range=(detailed_params.get('face_ctemp_min', 0.0), detailed_params.get('face_ctemp_max', 0.0)),
                detect_flag=detect_flag,
                polygon_vertices=polygon_vertices,
                is_polygon=is_polygon,
                # 详细范围参数
                tran_bv_min=detailed_params.get('tran_bv_min', 0.0),
                tran_bv_max=detailed_params.get('tran_bv_max', 0.0),
                tran_ctemp_min=detailed_params.get('tran_ctemp_min', 0.0),
                tran_ctemp_max=detailed_params.get('tran_ctemp_max', 0.0),
                tran_ir_min=detailed_params.get('tran_ir_min', 0.0),
                tran_ir_max=detailed_params.get('tran_ir_max', 0.0),
                tran_ac_min=detailed_params.get('tran_ac_min', 0.0),
                tran_ac_max=detailed_params.get('tran_ac_max', 0.0),
                tran_count_min=detailed_params.get('tran_count_min', 0.0),
                tran_count_max=detailed_params.get('tran_count_max', 0.0),
                tran_color_cct_min=detailed_params.get('tran_color_cct_min', 0.0),
                tran_color_cct_max=detailed_params.get('tran_color_cct_max', 0.0),
                tran_diff_ctemp_min=detailed_params.get('tran_diff_ctemp_min', 0.0),
                tran_diff_ctemp_max=detailed_params.get('tran_diff_ctemp_max', 0.0),
                tran_face_ctemp_min=detailed_params.get('tran_face_ctemp_min', 0.0),
                tran_face_ctemp_max=detailed_params.get('tran_face_ctemp_max', 0.0),
                detect_map_flag=detailed_params.get('detect_map_flag', True)
            )

            # 设置额外属性
            map_point.extra_attributes = {
                'source_node_count': len(offset_map_nodes),
                'has_polygon': is_polygon,
                'polygon_vertex_count': len(polygon_vertices) if polygon_vertices else 0,
                'ml': detailed_params.get('ml', 0)
            }


            return map_point

        except Exception as e:
            logger.error(f"==liuq debug== 解析单个offset_map失败: {e}")
            return None

    def _parse_single_base_boundary(self, base_boundary_nodes: List[ET.Element]) -> Optional[MapPoint]:
        """
        解析base_boundary0的双组数据结构

        Args:
            base_boundary_nodes: base_boundary节点列表（应该有2个节点）

        Returns:
            MapPoint对象或None
        """
        try:
            # 第一个节点包含offset、range、weight等信息（第一组数据）
            first_node = base_boundary_nodes[0]
            # 第二个节点包含AliasName、RpG、BpG等信息（第二组数据）
            second_node = base_boundary_nodes[1]

            # 从第二组数据提取别名
            alias_node = second_node.find('AliasName')
            alias_name = alias_node.text if alias_node is not None and alias_node.text else "base_boundary0"

            # 从第一组数据提取offset坐标
            offset_x, offset_y = self._extract_offset_coordinates(first_node)

            # 从第二组数据提取多边形坐标（如果有）
            polygon_vertices, is_polygon = self._extract_polygon_coordinates(second_node)

            # 确定最终坐标
            if is_polygon and polygon_vertices:
                # 计算多边形重心作为代表坐标
                x = sum(vertex[0] for vertex in polygon_vertices) / len(polygon_vertices)
                y = sum(vertex[1] for vertex in polygon_vertices) / len(polygon_vertices)
            else:
                # 使用offset坐标
                x, y = offset_x, offset_y

            # 从第二组数据提取TransStep值
            trans_step_node = second_node.find('TransStep')
            trans_step = int(trans_step_node.text) if trans_step_node is not None and trans_step_node.text else 0

            # 从第一组数据提取权重
            weight_node = first_node.find('weight')
            weight = float(weight_node.text) if weight_node is not None and weight_node.text else 1.0

            # 从第一组数据提取范围数据
            bv_range, ir_range, cct_range, detect_flag = self._extract_range_data_from_node(first_node)

            # 从第一组数据提取详细参数
            detailed_params = self._extract_detailed_parameters(first_node)

            # 创建MapPoint对象（base_boundary作为特殊的Map点）
            map_point = MapPoint(
                alias_name=alias_name,
                x=x,
                y=y,
                offset_x=offset_x,
                offset_y=offset_y,
                weight=weight,
                trans_step=trans_step,
                bv_range=bv_range,
                ir_range=ir_range,
                cct_range=cct_range,
                ctemp_range=(detailed_params.get('ctemp_min', 0.0), detailed_params.get('ctemp_max', 0.0)),
                e_ratio_range=(detailed_params.get('e_ratio_min', 0.0), detailed_params.get('e_ratio_max', 0.0)),
                ac_range=(detailed_params.get('ac_min', 0.0), detailed_params.get('ac_max', 0.0)),
                count_range=(detailed_params.get('count_min', 0.0), detailed_params.get('count_max', 0.0)),
                color_cct_range=(detailed_params.get('color_cct_min', 0.0), detailed_params.get('color_cct_max', 0.0)),
                diff_ctemp_range=(detailed_params.get('diff_ctemp_min', 0.0), detailed_params.get('diff_ctemp_max', 0.0)),
                face_ctemp_range=(detailed_params.get('face_ctemp_min', 0.0), detailed_params.get('face_ctemp_max', 0.0)),
                detect_flag=detect_flag,
                polygon_vertices=polygon_vertices,
                is_polygon=is_polygon,
                # 详细范围参数
                tran_bv_min=detailed_params.get('tran_bv_min', 0.0),
                tran_bv_max=detailed_params.get('tran_bv_max', 0.0),
                tran_ctemp_min=detailed_params.get('tran_ctemp_min', 0.0),
                tran_ctemp_max=detailed_params.get('tran_ctemp_max', 0.0),
                tran_ir_min=detailed_params.get('tran_ir_min', 0.0),
                tran_ir_max=detailed_params.get('tran_ir_max', 0.0),
                tran_ac_min=detailed_params.get('tran_ac_min', 0.0),
                tran_ac_max=detailed_params.get('tran_ac_max', 0.0),
                tran_count_min=detailed_params.get('tran_count_min', 0.0),
                tran_count_max=detailed_params.get('tran_count_max', 0.0),
                tran_color_cct_min=detailed_params.get('tran_color_cct_min', 0.0),
                tran_color_cct_max=detailed_params.get('tran_color_cct_max', 0.0),
                tran_diff_ctemp_min=detailed_params.get('tran_diff_ctemp_min', 0.0),
                tran_diff_ctemp_max=detailed_params.get('tran_diff_ctemp_max', 0.0),
                tran_face_ctemp_min=detailed_params.get('tran_face_ctemp_min', 0.0),
                tran_face_ctemp_max=detailed_params.get('tran_face_ctemp_max', 0.0),
                detect_map_flag=detailed_params.get('detect_map_flag', True)
            )

            # 设置额外属性
            map_point.extra_attributes = {
                'source_node_count': len(base_boundary_nodes),
                'has_polygon': is_polygon,
                'polygon_vertex_count': len(polygon_vertices) if polygon_vertices else 0,
                'ml': detailed_params.get('ml', 0)
            }


            return map_point

        except Exception as e:
            logger.error(f"==liuq debug== 解析base_boundary失败: {e}")
            return None

    def _parse_base_boundary_as_map_point(self, root: ET.Element) -> Optional[MapPoint]:
        """
        单独解析base_boundary0作为MapPoint

        Args:
            root: XML根元素

        Returns:
            base_boundary0的MapPoint对象或None
        """
        try:
            base_boundary_nodes = root.findall('.//base_boundary0')
            if len(base_boundary_nodes) >= 2:
                base_boundary_point = self._parse_single_base_boundary(base_boundary_nodes)
                if base_boundary_point:
                    logger.info("==liuq debug== 成功解析base_boundary0作为单独的MapPoint")
                    return base_boundary_point

            logger.warning("==liuq debug== 未找到base_boundary0节点或节点数量不足")
            return None

        except Exception as e:
            logger.error(f"==liuq debug== 解析base_boundary0作为MapPoint失败: {e}")
            return None

    def _is_empty_offset_map(self, first_node: ET.Element, second_node: ET.Element) -> bool:
        """
        检查offset_map是否为空（从legacy_xml_parser.py移植）

        注意：不对权重进行判断，权重小的Map点仍然是有效的

        Args:
            first_node: 第一个offset_map节点
            second_node: 第二个offset_map节点

        Returns:
            是否为空Map
        """
        try:
            # 检查MapEnabled字段 - 如果明确禁用则认为是空Map
            map_enabled_node = second_node.find('MapEnabled')
            if map_enabled_node is not None and map_enabled_node.text:
                if int(map_enabled_node.text) == 0:

                    return True

            # 检查是否有别名 - 如果有别名说明是有效Map
            alias_node = second_node.find('AliasName')
            if alias_node is not None and alias_node.text and alias_node.text.strip():

                return False

            # 检查是否有坐标信息
            offset_node = first_node.find('offset')
            if offset_node is not None:
                x_node = offset_node.find('x')
                y_node = offset_node.find('y')
                if (x_node is not None and x_node.text and
                    y_node is not None and y_node.text):
                    try:
                        x_val = float(x_node.text)
                        y_val = float(y_node.text)
                        # 如果坐标不为(0,0)，认为是有效Map
                        if x_val != 0.0 or y_val != 0.0:

                            return False
                    except ValueError:
                        pass

            # 检查是否有多边形坐标
            rpg_node = second_node.find('RpG')
            bpg_node = second_node.find('BpG')
            if (rpg_node is not None and rpg_node.text and rpg_node.text.strip() and
                bpg_node is not None and bpg_node.text and bpg_node.text.strip()):

                return False

            # 如果以上条件都不满足，才认为是空Map

            return True

        except Exception as e:
            logger.warning(f"==liuq debug== 检查空offset_map失败: {e}")
            return False

    def _extract_offset_coordinates(self, first_node: ET.Element) -> Tuple[float, float]:
        """从第一组数据提取offset坐标"""
        try:
            offset_node = first_node.find('offset')
            if offset_node is not None:
                x_node = offset_node.find('x')
                y_node = offset_node.find('y')

                x = float(x_node.text) if x_node is not None and x_node.text else 0.0
                y = float(y_node.text) if y_node is not None and y_node.text else 0.0

                return x, y
            return 0.0, 0.0
        except:
            return 0.0, 0.0

    def _extract_polygon_coordinates(self, second_node: ET.Element) -> Tuple[List[Tuple[float, float]], bool]:
        """从第二组数据提取多边形坐标"""
        try:
            rpg_node = second_node.find('RpG')
            bpg_node = second_node.find('BpG')

            if rpg_node is not None and bpg_node is not None and rpg_node.text and bpg_node.text:
                rpg_values = [float(x) for x in rpg_node.text.split()]
                bpg_values = [float(x) for x in bpg_node.text.split()]

                if len(rpg_values) == len(bpg_values) and len(rpg_values) > 0:
                    vertices = list(zip(rpg_values, bpg_values))
                    return vertices, True

            return [], False
        except:
            return [], False

    def _extract_range_data_from_node(self, first_node: ET.Element) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], bool]:
        """
        从第一组数据提取范围数据（重构版本 - 使用配置驱动）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-01 11:15:00 +08:00; Reason: 重构使用配置驱动的字段解析逻辑; Principle_Applied: DRY原则和配置驱动设计;
        }}
        """
        try:
            range_node = first_node.find('range')
            if range_node is None:
                return (0.0, 100.0), (0.0, 100.0), (2000.0, 10000.0), False

            # 使用配置驱动的方式提取范围数据
            bv_range = self._extract_field_range(range_node, 'bv_min', 'bv_max')
            ir_range = self._extract_field_range(range_node, 'ir_min', 'ir_max')
            cct_range = self._extract_field_range(range_node, 'color_cct_min', 'color_cct_max')

            # 提取检测标志 - 修复：正确解析0/1为bool值
            detect_flag_node = range_node.find('DetectMapFlag')
            detect_flag = False
            if detect_flag_node is not None and detect_flag_node.text:
                text_value = detect_flag_node.text.strip().lower()
                # 支持多种格式：'1', 'true', 'yes' 为True；'0', 'false', 'no' 为False
                detect_flag = text_value in ('1', 'true', 'yes')

            return bv_range, ir_range, cct_range, detect_flag

        except Exception as e:
            logger.warning(f"==liuq debug== 提取范围数据失败: {e}")
            return (0.0, 100.0), (0.0, 100.0), (2000.0, 10000.0), False

    def _extract_field_range(self, range_node: ET.Element, min_field: str, max_field: str) -> Tuple[float, float]:
        """
        使用配置驱动的方式提取字段范围

        Args:
            range_node: range XML节点
            min_field: 最小值字段名
            max_field: 最大值字段名

        Returns:
            (min_value, max_value) 元组
        """
        try:
            # 获取字段配置
            min_config = XML_FIELD_CONFIG.get(min_field)
            max_config = XML_FIELD_CONFIG.get(max_field)

            if not min_config or not max_config:
                logger.warning(f"==liuq debug== 字段配置未找到: {min_field}, {max_field}")
                return (0.0, 100.0)

            # 提取最小值
            min_value = self._extract_single_field_value(range_node, min_config)

            # 提取最大值
            max_value = self._extract_single_field_value(range_node, max_config)

            return (min_value, max_value)

        except Exception as e:
            logger.warning(f"==liuq debug== 提取字段范围失败 {min_field}-{max_field}: {e}")
            return (0.0, 100.0)

    def _extract_single_field_value(self, range_node: ET.Element, field_config) -> float:
        """
        提取单个字段值

        Args:
            range_node: range XML节点
            field_config: 字段配置

        Returns:
            字段值
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
                return parse_field_value(target_node.text, field_config.field_name)
            else:
                return field_config.default_value

        except Exception as e:
            logger.warning(f"==liuq debug== 提取单个字段值失败 {field_config.field_name}: {e}")
            return field_config.default_value

    def _extract_map_point_data(self, map_elem: ET.Element) -> Dict[str, Any]:
        """
        从Map元素中提取数据

        Args:
            map_elem: Map XML元素

        Returns:
            Dict[str, Any]: 提取的数据字典
        """
        data = {}

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

        return data
    
    def _extract_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """
        提取XML元数据
        
        Args:
            root: XML根元素
            
        Returns:
            Dict[str, Any]: 元数据字典
        """
        metadata = {}
        
        try:
            # 提取版本信息
            version_elem = root.find('.//version')
            if version_elem is not None:
                metadata['version'] = version_elem.text
            
            # 提取设备信息
            device_elem = root.find('.//device')
            if device_elem is not None:
                metadata['device'] = device_elem.text
            
            # 提取创建时间
            created_elem = root.find('.//created')
            if created_elem is not None:
                metadata['created'] = created_elem.text
            
            # 统计信息
            metadata['total_maps'] = len(root.findall('.//Map'))
            metadata['root_tag'] = root.tag
            
        except Exception as e:
            logger.warning(f"==liuq debug== 提取元数据失败: {e}")
        
        return metadata
    
    def _validate_map_point(self, point: MapPoint) -> List[str]:
        """
        验证Map点数据
        
        Args:
            point: Map点对象
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 获取所有字段定义
        field_definitions = field_registry.get_all_fields()
        
        for field_def in field_definitions:
            try:
                # 获取字段值
                value = getattr(point, field_def.field_id, None)
                
                # 验证字段值
                is_valid, field_errors = field_def.validate_value(value)
                if not is_valid:
                    errors.extend([f"{field_def.display_name}: {error}" for error in field_errors])
                    
            except Exception as e:
                errors.append(f"{field_def.display_name}: 验证失败 - {e}")
        
        return errors

    def _extract_base_boundary(self, root: ET.Element) -> BaseBoundary:
        """
        提取基础边界数据

        Args:
            root: XML根元素

        Returns:
            BaseBoundary: 基础边界对象
        """
        try:
            # 首先尝试从base_boundary0的第二个节点提取RpG和BpG
            base_boundary_nodes = root.findall('.//base_boundary0')
            if len(base_boundary_nodes) >= 2:
                # 第二个节点包含RpG和BpG数据
                second_node = base_boundary_nodes[1]

                rpg_elem = second_node.find('RpG')
                bpg_elem = second_node.find('BpG')

                rpg = self._parse_boundary_value(rpg_elem)
                bpg = self._parse_boundary_value(bpg_elem)

                logger.info(f"==liuq debug== 从base_boundary0提取边界数据: RpG={rpg:.3f}, BpG={bpg:.3f}")
                return BaseBoundary(rpg=rpg, bpg=bpg)

            # 如果没有找到base_boundary0，尝试查找base_boundary元素
            boundary_elem = root.find('.//base_boundary')
            if boundary_elem is not None:
                # 提取rpg和bpg值
                rpg_elem = boundary_elem.find('.//rpg')
                bpg_elem = boundary_elem.find('.//bpg')

                rpg = float(rpg_elem.text) if rpg_elem is not None and rpg_elem.text else 0.0
                bpg = float(bpg_elem.text) if bpg_elem is not None and bpg_elem.text else 0.0

                logger.info(f"==liuq debug== 从base_boundary提取边界数据: RpG={rpg:.3f}, BpG={bpg:.3f}")
                return BaseBoundary(rpg=rpg, bpg=bpg)
            else:
                # 如果都没有找到，使用默认值
                logger.warning("==liuq debug== 未找到base_boundary或base_boundary0元素，使用默认值")
                return BaseBoundary(rpg=0.0, bpg=0.0)

        except Exception as e:
            logger.warning(f"==liuq debug== 提取基础边界数据失败: {e}")
            return BaseBoundary(rpg=0.0, bpg=0.0)

    def _extract_detailed_parameters(self, node: ET.Element) -> Dict[str, float]:
        """
        提取详细参数（重构版本 - 使用配置驱动）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-01 11:20:00 +08:00; Reason: 重构使用配置驱动的详细参数提取逻辑; Principle_Applied: DRY原则和配置驱动设计;
        }}

        Args:
            node: XML节点

        Returns:
            详细参数字典
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
                            field_value = self._extract_single_field_value(range_node, config)
                            params[field_name] = field_value



                        except Exception as e:
                            logger.warning(f"==liuq debug== 提取字段 {field_name} 失败: {e}")
                            params[field_name] = config.default_value

                # ml字段保持原始值（修复数据转换bug）
                #
                # {{CHENGQI:
                # Action: Modified; Timestamp: 2025-08-01 13:35:00 +08:00; Reason: 修复ml字段数据转换bug，保持原始内部值用于XML保存; Principle_Applied: 数据完整性原则和显示存储分离;
                # }}
                #
                # 注意：ml字段的GUI显示转换（65471→2, 65535→3）应该只在GUI层处理，
                # 而不是在数据解析层。这样确保XML保存时使用原始内部值。
                if 'ml' in params:
                    # 保持原始值，不进行转换
                    params['ml'] = int(params['ml'])

                # 提取DetectMapFlag（不在配置中的特殊字段）
                detect_flag_node = range_node.find('DetectMapFlag')
                if detect_flag_node is not None and detect_flag_node.text:
                    text_value = detect_flag_node.text.strip().lower()
                    params['detect_map_flag'] = text_value in ('1', 'true', 'yes')
                else:
                    params['detect_map_flag'] = True

                # 添加ERatio字段（如果存在）
                e_ratio_node = range_node.find('e_ratio')
                if e_ratio_node is not None:
                    min_node = e_ratio_node.find('min')
                    max_node = e_ratio_node.find('max')

                    if min_node is not None and min_node.text:
                        try:
                            params['e_ratio_min'] = float(min_node.text)
                        except ValueError:
                            params['e_ratio_min'] = 0.0

                    if max_node is not None and max_node.text:
                        try:
                            params['e_ratio_max'] = float(max_node.text)
                        except ValueError:
                            params['e_ratio_max'] = 0.0


            return params

        except Exception as e:
            logger.warning(f"==liuq debug== 提取详细参数失败: {e}")
            return params

    def _parse_boundary_value(self, node: ET.Element) -> float:
        """
        解析边界值，支持单个数值或数组

        Args:
            node: XML节点

        Returns:
            解析的浮点数值
        """
        if node is None or not node.text:
            return 0.0

        try:
            # 尝试直接解析为浮点数
            return float(node.text)
        except ValueError:
            try:
                # 如果是空格分隔的数组，取第一个值
                values = node.text.strip().split()
                if values:
                    return float(values[0])
                else:
                    return 0.0
            except (ValueError, IndexError):
                logger.warning(f"==liuq debug== 无法解析边界值: {node.text[:50]}...")
                return 0.0


logger.info("==liuq debug== XML解析服务模块加载完成")
