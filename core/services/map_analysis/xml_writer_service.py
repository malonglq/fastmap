#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML写入服务 - 简化版本

负责XML文件的核心写入功能，其他功能委托给专门的服务

作者: AI Assistant
日期: 2025-08-25
"""

import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
from xml.etree import ElementTree as ET

from core.interfaces.xml_data_processor import (
    XMLDataProcessor, XMLWriteError, ValidationError, BackupError,
    ValidationLevel, ValidationResult
)
from core.models.map_data import (
    MapPoint, MapConfiguration, BaseBoundary,
    XML_FIELD_CONFIG, XMLFieldNodeType, XMLFieldDataType,
    get_field_xml_path, get_field_node_type, get_field_data_type,
    format_field_value, get_map_point_field_value, get_fields_by_node_type
)
from core.services.shared.field_registry_service import field_registry
from core.interfaces.xml_field_definition import XMLFieldDefinition, FieldType
from core.services.map_analysis.xml_validation_service import get_xml_validation_service
from core.services.map_analysis.xml_backup_service import get_xml_backup_service
from core.services.map_analysis.xml_formatting_service import get_xml_formatting_service
from core.services.map_analysis.xml_performance_service import get_xml_performance_service

logger = logging.getLogger(__name__)


def format_number_for_xml(value) -> str:
    """
    智能数值格式化函数，用于XML写入 - 委托给格式化服务
    """
    formatting_service = get_xml_formatting_service()
    return formatting_service.format_number_for_xml(value)


class XMLWriterService(XMLDataProcessor):
    """
    XML写入服务实现（简化版本）
    
    基于XMLDataProcessor接口的XML写入服务，核心功能委托给专门的服务：
    - 验证功能：委托给XMLValidationService
    - 备份功能：委托给XMLBackupService
    - 格式化功能：委托给XMLFormattingService
    - 性能优化：委托给XMLPerformanceService
    """
    
    def __init__(self):
        """初始化XML写入服务"""
        self.supported_versions = ["1.0", "1.1", "2.0"]
        self.default_encoding = "utf-8"
        self.field_definitions: List[XMLFieldDefinition] = []
        self._load_field_definitions()

        # 初始化服务组件
        self.validation_service = get_xml_validation_service()
        self.backup_service = get_xml_backup_service()
        self.formatting_service = get_xml_formatting_service()
        self.performance_service = get_xml_performance_service()

        # 保存控制相关
        self.current_config = None          # 当前配置对象
        self.current_xml_path = None        # 当前XML文件路径
        self.current_tree = None            # 当前XML树对象
        self.is_data_modified = False       # 数据是否已修改
        self.modification_count = 0         # 修改计数器

        logger.info("==liuq debug== XML写入服务初始化完成（模块化架构）")

    def _load_field_definitions(self):
        """加载字段定义"""
        try:
            all_groups = field_registry.get_field_groups()
            self.field_definitions = []

            for group in all_groups:
                fields = field_registry.get_fields_by_group(group)
                self.field_definitions.extend(fields)

            logger.info(f"==liuq debug== XML写入服务加载字段定义完成，共 {len(self.field_definitions)} 个字段")

        except Exception as e:
            logger.error(f"==liuq debug== 加载字段定义失败: {e}")
            self.field_definitions = []

    # ==================== 保存控制方法 ====================

    def load_xml_for_editing(self, xml_path: Union[str, Path], device_type: str = "reference") -> Optional[MapConfiguration]:
        """
        加载XML文件用于编辑（不触发自动保存）
        """
        try:
            from .xml_parser_service import XMLParserService

            xml_path = Path(xml_path)
            logger.info(f"==liuq debug== 加载XML文件用于编辑: {xml_path}")

            # 解析XML文件
            parser = XMLParserService()
            config = parser.parse_xml(xml_path, device_type)

            if config:
                # 解析XML树
                tree = ET.parse(xml_path)

                # 保存到当前状态（不触发保存）
                self.current_xml_path = xml_path
                self.current_config = config
                self.current_tree = tree
                self.is_data_modified = False
                self.modification_count = 0

                logger.info(f"==liuq debug== XML文件加载成功，已加载 {len(config.map_points)} 个Map点")
                return config
            else:
                logger.error(f"==liuq debug== XML文件解析失败")
                return None

        except Exception as e:
            logger.error(f"==liuq debug== 加载XML文件失败: {e}")
            return None

    def mark_data_modified(self, description: str = "数据已修改"):
        """
        标记数据已修改
        """
        if not self.is_data_modified:
            self.is_data_modified = True

        self.modification_count += 1

    def save_now(self, backup: bool = True) -> bool:
        """
        立即保存当前数据（用户主动触发）
        """
        try:
            if not self.current_config or not self.current_xml_path:
                logger.error("==liuq debug== 没有可保存的数据")
                return False

            if not self.is_data_modified:
                logger.info("==liuq debug== 数据未修改，跳过保存")
                return True

            logger.info(f"==liuq debug== 开始保存XML数据到: {self.current_xml_path}")

            # 使用性能优化服务
            success = self.performance_service.write_xml_optimized(
                self.current_config,
                self.current_xml_path,
                backup=backup,
                tree=self.current_tree
            )

            if success:
                self.is_data_modified = False
                self.modification_count = 0
                logger.info("==liuq debug== XML数据保存成功")
            else:
                logger.error("==liuq debug== XML数据保存失败")

            return success

        except Exception as e:
            logger.error(f"==liuq debug== 保存XML数据时发生异常: {e}")
            return False

    def is_modified(self) -> bool:
        """检查数据是否已修改"""
        return self.is_data_modified

    def get_modification_count(self) -> int:
        """获取修改次数"""
        return self.modification_count

    def can_close_without_save(self) -> bool:
        """检查是否可以在不保存的情况下关闭"""
        return not self.is_data_modified

    # ==================== 接口方法实现 ====================

    def parse_xml(self, xml_path: Union[str, Path], device_type: str = "unknown") -> MapConfiguration:
        """
        解析XML文件为MapConfiguration对象
        
        注意：XMLWriterService主要负责写入功能，解析功能委托给XMLParserService
        """
        logger.warning("==liuq debug== XMLWriterService.parse_xml 委托给XMLParserService实现")
        from core.services.map_analysis.xml_parser_service import XMLParserService
        parser = XMLParserService()
        return parser.parse_xml(xml_path, device_type)
    
    def write_xml(self, config: MapConfiguration, xml_path: Union[str, Path],
                  backup: bool = True, preserve_format: bool = True) -> bool:
        """
        将MapConfiguration对象写入XML文件
        """
        logger.info("==liuq debug== write_xml方法重定向到性能优化服务")

        # 临时设置当前配置和路径以支持优化方法
        original_config = self.current_config
        original_path = self.current_xml_path

        try:
            # 解析XML树
            tree = ET.parse(xml_path)

            # 设置临时状态
            self.current_config = config
            self.current_xml_path = Path(xml_path)
            self.current_tree = tree

            # 使用性能优化服务
            success = self.performance_service.write_xml_optimized(config, Path(xml_path), backup, tree)

            return success

        except Exception as e:
            logger.error(f"==liuq debug== 高性能写入失败: {e}")
            return False

        finally:
            # 恢复原始状态
            self.current_config = original_config
            self.current_xml_path = original_path

    def validate_xml(self, xml_path: Union[str, Path], 
                     level: ValidationLevel = ValidationLevel.FULL) -> ValidationResult:
        """
        验证XML文件的结构和内容 - 委托给验证服务
        """
        return self.validation_service.validate_xml_file(xml_path, level)
    
    def get_supported_versions(self) -> List[str]:
        """
        获取支持的XML版本列表
        """
        return self.supported_versions.copy()
    
    def get_xml_metadata(self, xml_path: Union[str, Path]) -> Dict[str, Any]:
        """
        获取XML文件的元数据信息 - 委托给验证服务
        """
        return self.validation_service.get_xml_metadata(xml_path)

    def backup_xml(self, xml_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> str:
        """
        创建XML文件备份 - 委托给备份服务
        """
        return self.backup_service.backup_xml(xml_path, backup_dir)

    def restore_from_backup(self, backup_path: Union[str, Path],
                           target_path: Union[str, Path]) -> bool:
        """
        从备份恢复XML文件 - 委托给备份服务
        """
        return self.backup_service.restore_from_backup(backup_path, target_path)

    # ==================== 辅助方法 ====================

    def _build_dynamic_alias_mapping(self, root: ET.Element) -> dict:
        """
        动态构建别名到XML节点的映射关系
        """
        alias_mapping = {}

        try:
            # 遍历所有可能的offset_map节点
            for i in range(1, 120):  # 扩大范围以适应更多Map点
                formatted_i = f"0{i}" if i < 10 else str(i)
                element_name = f"offset_map{formatted_i}"

                # 查找该offset_map的所有节点
                offset_map_nodes = root.findall(f'.//{element_name}')

                if len(offset_map_nodes) >= 2:
                    # 从第二个节点提取别名（第二个节点包含AliasName）
                    second_node = offset_map_nodes[1]
                    alias_node = second_node.find('AliasName')

                    if alias_node is not None and alias_node.text:
                        alias_name = alias_node.text.strip()
                        alias_mapping[alias_name] = element_name

                else:
                    # 如果找不到节点，可能已经到达末尾
                    break

            logger.info(f"==liuq debug== 动态构建别名映射完成，共 {len(alias_mapping)} 个映射关系")
            return alias_mapping

        except Exception as e:
            logger.error(f"==liuq debug== 构建动态别名映射失败: {e}")
            return {}

    def _get_xml_node_name_by_alias(self, root: ET.Element, alias_name: str) -> str:
        """
        根据别名获取对应的XML节点名称（动态方式）
        """
        # 如果还没有构建映射或缓存被清理，则动态构建
        if not hasattr(self, '_alias_mapping_cache') or self._alias_mapping_cache is None:
            self._alias_mapping_cache = self._build_dynamic_alias_mapping(root)

        return self._alias_mapping_cache.get(alias_name, None)

    def _get_map_point_field_value(self, map_point: MapPoint, field_id: str) -> Any:
        """
        从Map点对象获取字段值
        """
        # 字段映射关系
        field_mapping = {
            'alias_name': map_point.alias_name,
            'x': map_point.x,
            'y': map_point.y,
            'offset_x': map_point.offset_x,
            'offset_y': map_point.offset_y,
            'weight': map_point.weight,
            'bv_min': map_point.bv_range[0] if map_point.bv_range else None,
            'bv_max': map_point.bv_range[1] if map_point.bv_range else None,
            'ir_min': map_point.ir_range[0] if map_point.ir_range else None,
            'ir_max': map_point.ir_range[1] if map_point.ir_range else None,
            'cct_min': map_point.cct_range[0] if map_point.cct_range else None,
            'cct_max': map_point.cct_range[1] if map_point.cct_range else None,
            'detect_flag': map_point.detect_flag,
            'trans_step': getattr(map_point, 'trans_step', 0)
        }

        return field_mapping.get(field_id)

    def _update_field_in_element(self, element: ET.Element, field_def: XMLFieldDefinition, value: Any):
        """
        在XML元素中更新字段值
        """
        try:
            # 处理XML路径
            field_path = field_def.xml_path.replace(".//", "").replace("./", "")

            # 查找字段元素
            field_element = element.find(f".//{field_path}")
            if field_element is None:
                # 尝试直接查找子元素
                field_element = element.find(field_path)

            if field_element is None:
                # 如果元素不存在，需要正确创建嵌套元素
                field_element = self._create_nested_element(element, field_path)

            # 根据字段类型设置值
            if field_def.field_type == FieldType.STRING:
                field_element.text = str(value) if value is not None else ""
            elif field_def.field_type == FieldType.FLOAT:
                # 使用智能格式化函数，整数显示为整数格式
                formatted_value = format_number_for_xml(value) if value is not None else "0"
                field_element.text = formatted_value
            elif field_def.field_type == FieldType.INTEGER:
                field_element.text = str(int(value)) if value is not None else "0"
            elif field_def.field_type == FieldType.BOOLEAN:
                # 对于真正的BOOLEAN字段，使用true/false字符串
                field_element.text = "true" if value else "false"
            else:
                field_element.text = str(value) if value is not None else ""

        except Exception as e:
            logger.warning(f"==liuq debug== 更新字段 {field_def.field_id} 失败: {e}")

    def _create_nested_element(self, parent: ET.Element, path: str) -> ET.Element:
        """
        创建嵌套的XML元素
        """
        try:
            # 分割路径
            path_parts = path.split('/')
            current_element = parent

            # 逐级创建或查找元素
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    # 最后一级，创建目标元素
                    target_element = ET.SubElement(current_element, part)
                    return target_element
                else:
                    # 中间级，查找或创建容器元素
                    container = current_element.find(part)
                    if container is None:
                        container = ET.SubElement(current_element, part)
                    current_element = container

            return current_element

        except Exception as e:
            logger.error(f"==liuq debug== 创建嵌套元素失败: {path} - {e}")
            # 回退到简单创建
            return ET.SubElement(parent, path.replace('/', '_'))

    def refresh_field_definitions(self):
        """刷新字段定义"""
        self._load_field_definitions()
        logger.info("==liuq debug== XML写入服务字段定义已刷新")


logger.info("==liuq debug== XML写入服务模块加载完成")