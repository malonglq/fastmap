#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML写入服务
==liuq debug== 可扩展XML数据管理架构的XML写入系统

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 14:30:00 +08:00; Reason: P1-LD-006-001 创建XMLWriterService类; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 实现XMLDataProcessor接口的完整XML写入服务，支持数据回写到XML文件
"""

import xml.etree.ElementTree as ET
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import shutil
from datetime import datetime
from abc import ABC
from decimal import Decimal

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
from utils.number_formatter import format_decimal_precise
from core.services.field_registry_service import field_registry
from core.interfaces.xml_field_definition import XMLFieldDefinition, FieldType

logger = logging.getLogger(__name__)


def format_number_for_xml(value) -> str:
    """
    智能数值格式化函数，用于XML写入 - 基于成熟的decimal.js算法实现

    采用业界验证的精度处理方案：
    1. 优先保持原始字符串精度（避免浮点转换损失）
    2. 使用Python Decimal库进行精确计算（类似decimal.js）
    3. 智能处理整数和小数的显示格式
    4. 完全避免浮点精度问题

    Args:
        value: 数值（int, float或可转换为数值的字符串）

    Returns:
        str: 格式化后的字符串

    Examples:
        >>> format_number_for_xml(1.0)
        '1'
        >>> format_number_for_xml(1.5)
        '1.5'
        >>> format_number_for_xml(0.0)
        '0'
        >>> format_number_for_xml(2.3)
        '2.3'
        >>> format_number_for_xml(0.75)
        '0.75'
        >>> format_number_for_xml("0.25")
        '0.25'
    """
    try:
        if value is None:
            return "0"

        # {{CHENGQI:
        # Action: Modified; Timestamp: 2025-08-02 11:00:00 +08:00; Reason: 重构使用统一的格式化核心算法，消除代码重复; Principle_Applied: DRY原则;
        # }}
        result = format_decimal_precise(value)
        # 关键精度日志

        return result

    except (ValueError, TypeError):
        # 如果转换失败，返回原始字符串
        result = str(value) if value is not None else "0"

        return result


# {{CHENGQI:
# Action: Removed; Timestamp: 2025-08-02 11:00:00 +08:00; Reason: 删除重复的内部格式化函数，使用统一的工具模块; Principle_Applied: DRY原则;
# }}
# _format_decimal_for_xml 函数已移动到 utils/number_formatter.py 作为 format_decimal_precise


# {{CHENGQI:
# Action: Removed; Timestamp: 2025-08-02 11:00:00 +08:00; Reason: 删除重复的内部辅助函数，使用统一的工具模块; Principle_Applied: DRY原则;
# }}
# _is_valid_xml_number_string 和 _format_xml_decimal_result 函数已移动到 utils/number_formatter.py


class XMLWriterService(XMLDataProcessor):
    """
    XML写入服务实现
    
    基于XMLDataProcessor接口的完整XML写入服务，支持：
    - 完整的XML数据写入功能
    - 基于字段注册系统的动态写入
    - 保持原XML文件格式和结构
    - 自动备份和错误恢复机制
    - 数据验证和完整性检查
    
    设计特点：
    - 实现XMLDataProcessor接口，保持架构一致性
    - 依赖字段注册系统，支持动态字段写入
    - 提供增量写入和全量写入两种模式
    - 完整的错误处理和回滚机制
    """
    
    def __init__(self):
        """
        初始化XML写入服务

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-07-30 16:05:00 +08:00; Reason: 集成性能优化和保存控制功能; Principle_Applied: 简洁设计原则;
        }}
        """
        self.supported_versions = ["1.0", "1.1", "2.0"]
        self.default_encoding = "utf-8"
        self.field_definitions: List[XMLFieldDefinition] = []
        self._load_field_definitions()

        # 性能优化相关
        self.compiled_patterns = {}  # 预编译的正则表达式缓存
        self._precompile_patterns()

        # 保存控制相关
        self.current_config = None          # 当前配置对象
        self.current_xml_path = None        # 当前XML文件路径
        self.current_tree = None            # 当前XML树对象
        self.is_data_modified = False       # 数据是否已修改
        self.modification_count = 0         # 修改计数器

        logger.info("==liuq debug== XML写入服务初始化完成（集成优化功能）")

    def _precompile_patterns(self):
        """
        预编译常用的正则表达式模式（性能优化）

        {{CHENGQI:
        Action: Added; Timestamp: 2025-07-30 16:05:00 +08:00; Reason: 添加正则表达式预编译优化; Principle_Applied: 性能优化原则;
        }}
        """
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

        {{CHENGQI:
        Action: Added; Timestamp: 2025-07-30 16:10:00 +08:00; Reason: 添加加载但不自动保存的方法; Principle_Applied: 用户控制原则;
        }}

        Args:
            xml_path: XML文件路径
            device_type: 设备类型

        Returns:
            MapConfiguration: 解析后的配置对象，失败时返回None
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
                import xml.etree.ElementTree as ET
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

        Args:
            description: 修改描述
        """
        if not self.is_data_modified:
            self.is_data_modified = True


        self.modification_count += 1

    def save_now(self, backup: bool = True) -> bool:
        """
        立即保存当前数据（用户主动触发）

        Args:
            backup: 是否创建备份

        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.current_config or not self.current_xml_path:
                logger.error("==liuq debug== 没有可保存的数据")
                return False

            if not self.is_data_modified:
                logger.info("==liuq debug== 数据未修改，跳过保存")
                return True

            logger.info(f"==liuq debug== 开始保存XML数据到: {self.current_xml_path}")

            # 使用优化的写入方法
            success = self._write_xml_optimized(
                self.current_config,
                self.current_xml_path,
                backup=backup
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

    # ==================== 性能优化方法 ====================

    def _write_xml_optimized(self, config: MapConfiguration, xml_path: Path, backup: bool = True) -> bool:
        """
        优化的XML写入方法（高性能批量替换）

        {{CHENGQI:
        Action: Added; Timestamp: 2025-07-30 16:15:00 +08:00; Reason: 添加高性能批量替换写入方法; Principle_Applied: 性能优化原则;
        }}

        Args:
            config: Map配置对象
            xml_path: XML文件路径
            backup: 是否创建备份

        Returns:
            bool: 写入是否成功
        """
        try:
            start_time = self._get_current_time_ms()

            # 1. 读取原始文件内容
            with open(xml_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            file_size = len(original_content)
            logger.info(f"==liuq debug== 开始高性能XML写入，文件大小: {file_size} 字符")

            # 2. 构建批量替换操作
            replacements = self._build_optimized_replacements(config, original_content)

            if not replacements:
                logger.info("==liuq debug== 没有需要替换的数据，跳过写入")
                return True

            # 3. 执行批量替换
            modified_content = self._execute_optimized_replacements(original_content, replacements)

            # 4. 创建备份（如果需要）
            if backup:
                self._create_backup(xml_path)

            # 5. 原子性写入文件
            self._atomic_write_file(xml_path, modified_content)

            # 6. 性能统计
            end_time = self._get_current_time_ms()
            duration = end_time - start_time

            logger.info(f"==liuq debug== 高性能XML写入完成，耗时: {duration}ms，替换操作: {len(replacements)}个")

            return True

        except Exception as e:
            logger.error(f"==liuq debug== 高性能XML写入失败: {e}")
            return False

    def _build_optimized_replacements(self, config: MapConfiguration, content: str) -> list:
        """
        构建优化的批量替换操作列表

        Args:
            config: Map配置对象
            content: 原始XML内容

        Returns:
            list: 替换操作列表
        """
        replacements = []

        # 1. 处理边界数据
        if config.base_boundary:
            replacements.extend(self._build_boundary_replacements(config.base_boundary, content))

        # 2. 处理Map点数据
        if self.current_tree:
            root = self.current_tree.getroot()
            replacements.extend(self._build_map_point_replacements(config.map_points, root, content))

        # 3. 智能差异检测：只保留真正需要替换的操作
        filtered_replacements = self._filter_changed_replacements(replacements, content)



        return filtered_replacements

    def _build_boundary_replacements(self, boundary: 'BaseBoundary', content: str) -> list:
        """
        构建边界数据替换操作（修复版本）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-07-31 09:45:00 +08:00; Reason: 修复边界数据误替换问题，只替换base_boundary0节点中的RpG/BpG; Principle_Applied: 精确匹配原则;
        }}
        """
        replacements = []



        # 精确定位base_boundary0节点
        base_boundary_start, base_boundary_end = self._find_base_boundary_node(content)
        if base_boundary_start == -1 or base_boundary_end == -1:
            logger.warning(f"==liuq debug== 未找到base_boundary0节点，跳过边界数据替换")
            return replacements

        # 获取base_boundary0节点内容
        boundary_node_content = content[base_boundary_start:base_boundary_end]

        # 检查RpG是否需要替换
        current_rpg = self._extract_boundary_field_value(boundary_node_content, 'RpG')
        target_rpg = format_number_for_xml(boundary.rpg)

        if current_rpg and current_rpg != target_rpg:
            replacements.append({
                'field_type': 'boundary_rpg',
                'replacement': target_rpg,
                'alias_name': 'base_boundary0',
                'field_name': 'RpG',
                '_node_start': base_boundary_start,
                '_node_end': base_boundary_end,
                '_current_value': current_rpg
            })


        # 检查BpG是否需要替换
        current_bpg = self._extract_boundary_field_value(boundary_node_content, 'BpG')
        target_bpg = format_number_for_xml(boundary.bpg)

        if current_bpg and current_bpg != target_bpg:
            replacements.append({
                'field_type': 'boundary_bpg',
                'replacement': target_bpg,
                'alias_name': 'base_boundary0',
                'field_name': 'BpG',
                '_node_start': base_boundary_start,
                '_node_end': base_boundary_end,
                '_current_value': current_bpg
            })


        logger.info(f"==liuq debug== 边界数据替换操作构建完成，共 {len(replacements)} 个操作")
        return replacements

    def _find_base_boundary_node(self, content: str) -> tuple:
        """
        查找base_boundary0节点的位置

        {{CHENGQI:
        Action: Added; Timestamp: 2025-07-31 09:45:00 +08:00; Reason: 新增方法用于精确定位base_boundary0节点; Principle_Applied: 精确匹配原则;
        }}

        Returns:
            tuple: (node_start, node_end) 节点的开始和结束位置，失败返回(-1, -1)
        """
        try:
            # 查找包含AliasName为base_boundary0的节点
            import re

            # 查找所有包含base_boundary0的AliasName节点
            alias_pattern = r'<AliasName[^>]*>base_boundary0</AliasName>'

            for alias_match in re.finditer(alias_pattern, content):
                alias_pos = alias_match.start()

                # 向前查找包含这个AliasName的节点
                # 查找最近的<offset_map开始标签
                search_start = max(0, alias_pos - 50000)  # 向前搜索50KB范围

                # 在这个范围内查找所有的offset_map节点
                node_pattern = r'<offset_map\d+>'

                for node_match in re.finditer(node_pattern, content[search_start:alias_pos + 1000]):
                    actual_pos = search_start + node_match.start()
                    node_name = node_match.group(0)[1:-1]  # 去掉< >
                    node_end_pos = content.find(f'</{node_name}>', actual_pos)

                    if node_end_pos != -1 and actual_pos <= alias_pos <= node_end_pos:

                        return actual_pos, node_end_pos + len(f'</{node_name}>')

            logger.warning(f"==liuq debug== 未找到base_boundary0节点")
            return -1, -1

        except Exception as e:
            logger.error(f"==liuq debug== 查找base_boundary0节点失败: {e}")
            return -1, -1

    def _extract_boundary_field_value(self, node_content: str, field_name: str) -> str:
        """
        从节点内容中提取边界字段值

        {{CHENGQI:
        Action: Added; Timestamp: 2025-07-31 09:45:00 +08:00; Reason: 新增方法用于提取边界字段值; Principle_Applied: 精确匹配原则;
        }}

        Args:
            node_content: 节点内容
            field_name: 字段名称（RpG或BpG）

        Returns:
            str: 字段值，失败返回None
        """
        try:
            field_start = node_content.find(f'<{field_name}')
            if field_start != -1:
                value_start = node_content.find('>', field_start) + 1
                value_end = node_content.find(f'</{field_name}>', value_start)
                if value_start > 0 and value_end > value_start:
                    value = node_content[value_start:value_end].strip()

                    return value

            logger.warning(f"==liuq debug== 未找到{field_name}字段")
            return None

        except Exception as e:
            logger.error(f"==liuq debug== 提取{field_name}字段值失败: {e}")
            return None

    def _build_map_point_replacements(self, map_points: list, root, content: str) -> list:
        """
        构建Map点替换操作（修复版本）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-07-30 20:35:00 +08:00; Reason: 修复大量误替换问题，只为真正需要修改的Map点创建替换操作; Principle_Applied: 精确匹配原则;
        }}
        """
        replacements = []



        for map_point in map_points:
            if map_point.alias_name == "base_boundary0":
                continue

            # 获取XML节点名称
            xml_node_name = self._get_xml_node_name_by_alias(root, map_point.alias_name)
            if not xml_node_name:
                logger.warning(f"==liuq debug== 未找到Map点 {map_point.alias_name} 对应的XML节点")
                continue

            # 先检查这个Map点是否真的需要修改
            # 通过比较当前XML中的值和Map点的值来判断
            current_offset_x, current_offset_y = self._get_current_offset_values(content, xml_node_name, map_point.alias_name)

            target_offset_x = format_number_for_xml(map_point.offset_x)
            target_offset_y = format_number_for_xml(map_point.offset_y)

            # 只为真正需要修改的字段创建替换操作
            if current_offset_x != target_offset_x:
                x_replacement_info = {
                    'node_name': xml_node_name,
                    'field_type': 'offset_x',
                    'replacement': target_offset_x,
                    'alias_name': map_point.alias_name,
                    'field_name': 'offset_x'
                }
                replacements.append(x_replacement_info)


            if current_offset_y != target_offset_y:
                y_replacement_info = {
                    'node_name': xml_node_name,
                    'field_type': 'offset_y',
                    'replacement': target_offset_y,
                    'alias_name': map_point.alias_name,
                    'field_name': 'offset_y'
                }
                replacements.append(y_replacement_info)


            # 添加所有其他字段的替换操作（重构集成）
            single_map_replacements = self._build_single_map_replacements(map_point, xml_node_name)
            replacements.extend(single_map_replacements)


        logger.info(f"==liuq debug== Map点替换操作构建完成，共 {len(replacements)} 个有效操作")
        return replacements

    def _get_current_offset_values(self, content: str, xml_node_name: str, alias_name: str) -> tuple:
        """
        获取XML中当前的offset_x和offset_y值

        {{CHENGQI:
        Action: Added; Timestamp: 2025-07-30 20:35:00 +08:00; Reason: 新增方法用于获取当前offset值，支持精确比较; Principle_Applied: 精确匹配原则;
        }}

        Args:
            content: XML内容
            xml_node_name: 节点名称
            alias_name: 别名

        Returns:
            tuple: (current_offset_x, current_offset_y)
        """
        try:
            # 使用修复后的节点定位方法
            node_start, node_end = self._find_exact_node_by_alias(content, xml_node_name, alias_name)
            if node_start == -1 or node_end == -1:
                logger.warning(f"==liuq debug== 无法定位节点 {xml_node_name} (别名: {alias_name})")
                return "0", "0"

            # 获取节点内容
            node_content = content[node_start:node_end]

            # 提取offset_x
            current_offset_x = "0"
            x_start = node_content.find('<x ')
            if x_start != -1:
                value_start = node_content.find('>', x_start) + 1
                value_end = node_content.find('</x>', value_start)
                if value_start > 0 and value_end > value_start:
                    current_offset_x = node_content[value_start:value_end].strip()

            # 提取offset_y
            current_offset_y = "0"
            y_start = node_content.find('<y ')
            if y_start != -1:
                value_start = node_content.find('>', y_start) + 1
                value_end = node_content.find('</y>', value_start)
                if value_start > 0 and value_end > value_start:
                    current_offset_y = node_content[value_start:value_end].strip()


            return current_offset_x, current_offset_y

        except Exception as e:
            logger.error(f"==liuq debug== 获取当前offset值失败: {e}")
            return "0", "0"

    def _build_single_map_replacements(self, map_point, xml_node_name: str) -> list:
        """
        为单个Map点构建替换操作（重构版本 - 支持所有字段类型）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-01 10:45:00 +08:00; Reason: 重构支持所有XML字段类型，修复非tran字段保存失败问题; Principle_Applied: DRY原则和配置驱动设计;
        }}
        """
        replacements = []

        # 使用配置驱动的字段处理方式
        # 处理所有已配置的字段类型



        for field_name, config in XML_FIELD_CONFIG.items():
            try:
                # 获取字段值
                field_value = get_map_point_field_value(map_point, field_name)

                # 使用统一的格式化函数
                formatted_value = format_field_value(field_value, field_name)

                # 关键精度日志


                # 创建替换操作信息
                replacement_info = {
                    'node_name': xml_node_name,
                    'field_type': field_name,
                    'replacement': formatted_value,
                    'alias_name': map_point.alias_name,
                    'field_name': field_name,
                    'node_type': config.node_type.value,  # 添加节点类型信息
                    'xml_path': config.xml_path  # 添加XML路径信息
                }
                replacements.append(replacement_info)



            except Exception as e:
                logger.warning(f"==liuq debug== 处理字段 {field_name} 失败: {e}")
                continue

        logger.info(f"==liuq debug== 为Map点 {map_point.alias_name} 创建了 {len(replacements)} 个字段替换操作")
        return replacements

    def _find_exact_node_by_alias(self, content: str, node_name: str, alias_name: str) -> tuple:
        """
        根据alias_name精确定位XML节点位置（简化修复版本）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-07-31 09:55:00 +08:00; Reason: 简化节点定位逻辑，回退到可靠的实现; Principle_Applied: 简单可靠原则;
        }}

        Args:
            content: XML内容
            node_name: 节点名称（如offset_map01）
            alias_name: 别名（如1_BlueSky_Bright）

        Returns:
            tuple: (node_start, node_end) 节点的开始和结束位置，失败返回(-1, -1)
        """
        try:


            # 对于offset_map节点，我们需要找到第一个节点（包含offset数据）
            # 第二个同名节点包含AliasName，用于验证这是正确的节点组

            search_start = 0
            node_count = 0

            while True:
                node_start = content.find(f'<{node_name}>', search_start)
                if node_start == -1:
                    break

                # 找到节点结束位置
                node_end = content.find(f'</{node_name}>', node_start)
                if node_end == -1:
                    break

                node_count += 1

                # 对于第一个节点，我们需要检查后面是否有第二个同名节点包含正确的alias_name
                if node_count % 2 == 1:  # 奇数节点（第1、3、5...个）
                    # 查找下一个同名节点
                    next_search_start = node_end + len(f'</{node_name}>')
                    next_node_start = content.find(f'<{node_name}>', next_search_start)

                    if next_node_start != -1:
                        next_node_end = content.find(f'</{node_name}>', next_node_start)
                        if next_node_end != -1:
                            # 检查第二个节点是否包含正确的alias_name
                            next_node_content = content[next_node_start:next_node_end + len(f'</{node_name}>')]

                            # 查找AliasName标签的内容（支持属性）
                            alias_start = next_node_content.find('<AliasName')
                            if alias_start != -1:
                                # 找到标签结束的>
                                tag_end = next_node_content.find('>', alias_start)
                                if tag_end != -1:
                                    # 找到内容结束的</AliasName>
                                    content_end = next_node_content.find('</AliasName>', tag_end)
                                    if content_end != -1:
                                        found_alias = next_node_content[tag_end + 1:content_end].strip()
                                        if found_alias == alias_name:
                                            # 找到了正确的节点对，返回第一个节点的位置

                                            return node_start, node_end + len(f'</{node_name}>')

                # 继续查找下一个节点
                search_start = node_end + 1

            logger.warning(f"==liuq debug== 未找到匹配的节点对: {node_name}, 别名: {alias_name}")
            return -1, -1

        except Exception as e:
            logger.error(f"==liuq debug== 精确节点定位失败: {e}")
            import traceback
            logger.error(f"==liuq debug== 错误详情: {traceback.format_exc()}")
            return -1, -1

    def _filter_changed_replacements(self, replacements: list, content: str) -> list:
        """
        智能差异检测：只保留真正需要替换的操作（修复版本）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-07-30 20:30:00 +08:00; Reason: 修复数据误替换问题，增强节点验证; Principle_Applied: 精确匹配原则;
        }}
        """
        filtered_replacements = []



        for i, replacement in enumerate(replacements):
            if 'node_name' in replacement:
                node_name = replacement['node_name']
                field_type = replacement['field_type']
                target_value = replacement['replacement']
                alias_name = replacement['alias_name']



                # 精确定位节点
                node_start, node_end = self._find_exact_node_by_alias(content, node_name, alias_name)
                if node_start == -1 or node_end == -1:
                    logger.warning(f"==liuq debug== 跳过替换操作 {i+1}: 未找到节点 {node_name} (别名: {alias_name})")
                    continue

                # 获取节点内容
                node_content = content[node_start:node_end]


                # 验证节点内容确实包含offset数据
                if '<offset>' not in node_content:
                    logger.warning(f"==liuq debug== 跳过替换操作 {i+1}: 节点不包含offset数据")
                    continue

                # 查找目标字段（重构版本 - 支持所有字段类型）
                field_found = False
                current_value = None

                # 使用配置驱动的字段查找
                try:
                    from core.models.map_data import XML_FIELD_CONFIG
                    if field_type in XML_FIELD_CONFIG:
                        config = XML_FIELD_CONFIG[field_type]
                        current_value = self._extract_field_value_from_content(node_content, config)
                        field_found = current_value is not None


                except ImportError:
                    logger.debug(f"==liuq debug== 无法导入XML_FIELD_CONFIG，使用传统方法")
                else:
                    # 保持向后兼容的硬编码字段处理
                    if field_type == 'offset_x':
                        field_start = node_content.find('<x ')
                        if field_start != -1:
                            value_start = node_content.find('>', field_start) + 1
                            value_end = node_content.find('</x>', value_start)
                            if value_start > 0 and value_end > value_start:
                                current_value = node_content[value_start:value_end].strip()
                                field_found = True

                    elif field_type == 'offset_y':
                        field_start = node_content.find('<y ')
                        if field_start != -1:
                            value_start = node_content.find('>', field_start) + 1
                            value_end = node_content.find('</y>', value_start)
                            if value_start > 0 and value_end > value_start:
                                current_value = node_content[value_start:value_end].strip()
                                field_found = True

                if not field_found:
                    logger.warning(f"==liuq debug== 跳过替换操作 {i+1}: 未找到字段 {field_type}")
                    continue

                # 检查是否需要替换
                if current_value != target_value:
                    replacement['_node_start'] = node_start
                    replacement['_node_end'] = node_end
                    replacement['_current_value'] = current_value
                    filtered_replacements.append(replacement)
                    logger.info(f"==liuq debug== 添加有效替换操作: {alias_name}.{field_type}: {current_value} -> {target_value}")
                else:
                    logger.debug(f"==liuq debug== 跳过替换操作 {i+1}: 值未变化 ({current_value})")

            else:
                # 处理边界数据替换（新格式）
                if 'field_type' in replacement and replacement['field_type'].startswith('boundary_'):
                    # 新的边界数据格式，已经在构建时进行了检查
                    filtered_replacements.append(replacement)
                    field_name = replacement.get('field_name', 'unknown')
                    current_value = replacement.get('_current_value', 'unknown')
                    target_value = replacement.get('replacement', 'unknown')
                    logger.info(f"==liuq debug== 添加边界数据替换操作: {field_name}: {current_value[:50]}... -> {target_value}")

                # 处理旧格式（边界数据）- 保持兼容性
                elif 'pattern' in replacement:
                    pattern = replacement['pattern']
                    match = pattern.search(content)

                    if match and len(match.groups()) >= 2:
                        current_value = match.group(2).strip()
                        target_value = replacement['replacement'].strip()

                        if current_value != target_value:
                            filtered_replacements.append(replacement)
                            logger.info(f"==liuq debug== 添加边界数据替换操作: {replacement.get('field_name', 'unknown')}: {current_value} -> {target_value}")

        logger.info(f"==liuq debug== 过滤完成，有效替换操作数: {len(filtered_replacements)}")
        return filtered_replacements

    def _extract_field_value_from_content(self, node_content: str, field_config) -> str:
        """
        从节点内容中提取字段值

        Args:
            node_content: 节点内容
            field_config: 字段配置

        Returns:
            str: 字段值，如果未找到则返回None
        """
        try:
            from core.models.map_data import XMLFieldNodeType

            if field_config.node_type == XMLFieldNodeType.OFFSET:
                # offset字段：<offset><x>value</x></offset>
                tag_name = field_config.xml_path[0]  # 'x' 或 'y'
                pattern = f'<{tag_name}[^>]*>([^<]*)</{tag_name}>'

            elif field_config.node_type == XMLFieldNodeType.RANGE:
                # range字段：<range><bv><min>value</min></bv></range>
                if len(field_config.xml_path) == 1:
                    # 单层：<range><tag>value</tag></range>
                    tag_name = field_config.xml_path[0]
                    pattern = f'<{tag_name}[^>]*>([^<]*)</{tag_name}>'
                elif len(field_config.xml_path) == 2:
                    # 双层：<range><parent><child>value</child></parent></range>
                    parent_tag = field_config.xml_path[0]
                    child_tag = field_config.xml_path[1]
                    pattern = f'<{parent_tag}[^>]*>.*?<{child_tag}[^>]*>([^<]*)</{child_tag}>.*?</{parent_tag}>'
                else:
                    logger.warning(f"==liuq debug== 不支持的XML路径长度: {len(field_config.xml_path)}")
                    return None
            else:
                logger.warning(f"==liuq debug== 不支持的节点类型: {field_config.node_type}")
                return None

            import re
            match = re.search(pattern, node_content, re.DOTALL)
            if match:
                value = match.group(1).strip()

                return value
            else:

                return None

        except Exception as e:
            logger.error(f"==liuq debug== 提取字段值失败: {e}")
            return None

    def _execute_optimized_replacements(self, content: str, replacements: list) -> str:
        """
        执行超高性能批量替换操作（重构版本 - 支持所有字段类型）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-01 10:50:00 +08:00; Reason: 重构支持所有XML字段类型，使用配置驱动的替换逻辑; Principle_Applied: DRY原则和配置驱动设计;
        }}
        """
        modified_content = content
        replacement_count = 0

        # 按位置从后往前排序，避免位置偏移问题
        sorted_replacements = sorted(
            [r for r in replacements if '_node_start' in r],
            key=lambda r: r['_node_start'],
            reverse=True
        )

        # 处理新格式的高性能替换
        for replacement in sorted_replacements:
            node_start = replacement['_node_start']
            node_end = replacement['_node_end']
            field_type = replacement['field_type']
            target_value = replacement['replacement']
            current_value = replacement.get('_current_value', '')

            # 获取节点内容
            node_content = modified_content[node_start:node_end]

            # 使用配置驱动的字段替换
            if field_type in XML_FIELD_CONFIG:
                config = XML_FIELD_CONFIG[field_type]

                if config.node_type == XMLFieldNodeType.OFFSET:
                    # 处理offset节点字段
                    new_node_content = self._replace_offset_field(node_content, config.xml_path, target_value)
                elif config.node_type == XMLFieldNodeType.RANGE:
                    # 处理range节点字段
                    new_node_content = self._replace_range_field(node_content, config.xml_path, target_value)
                else:
                    new_node_content = None

                if new_node_content:
                    # 更新修改后的内容
                    modified_content = (modified_content[:node_start] +
                                      new_node_content +
                                      modified_content[node_end:])
                    replacement_count += 1

                else:
                    logger.warning(f"==liuq debug== 字段替换失败: {field_type}")

            elif field_type in ['boundary_rpg', 'boundary_bpg']:
                # 处理边界字段（保持原有逻辑）
                tag_name = 'RpG' if field_type == 'boundary_rpg' else 'BpG'
                new_node_content = self._replace_boundary_field(node_content, tag_name, target_value)

                if new_node_content:
                    modified_content = (modified_content[:node_start] +
                                      new_node_content +
                                      modified_content[node_end:])
                    replacement_count += 1

            else:
                logger.warning(f"==liuq debug== 未知字段类型: {field_type}")

        logger.info(f"==liuq debug== 完成批量替换操作，共执行 {replacement_count} 个替换")
        return modified_content

    def _replace_offset_field(self, node_content: str, xml_path: tuple, target_value: str) -> str:
        """
        替换offset节点中的字段值

        Args:
            node_content: 节点内容
            xml_path: XML路径元组
            target_value: 目标值

        Returns:
            修改后的节点内容，失败时返回None
        """
        try:
            if len(xml_path) != 1:
                return None

            tag_name = xml_path[0]

            # 查找<tag>标签并替换值
            tag_start = node_content.find(f'<{tag_name} ')
            if tag_start != -1:
                value_start = node_content.find('>', tag_start) + 1
                value_end = node_content.find(f'</{tag_name}>', value_start)
                if value_start > 0 and value_end > value_start:
                    new_content = (node_content[:value_start] +
                                 target_value +
                                 node_content[value_end:])
                    return new_content
            return None
        except Exception as e:
            logger.error(f"==liuq debug== 替换offset字段失败: {e}")
            return None

    def _replace_range_field(self, node_content: str, xml_path: tuple, target_value: str) -> str:
        """
        替换range节点中的字段值

        Args:
            node_content: 节点内容
            xml_path: XML路径元组
            target_value: 目标值

        Returns:
            修改后的节点内容，失败时返回None
        """
        try:
            # 首先找到range节点
            range_start = node_content.find('<range>')
            if range_start == -1:
                return None

            range_end = node_content.find('</range>', range_start)
            if range_end == -1:
                return None

            range_content = node_content[range_start:range_end + len('</range>')]

            # 根据XML路径导航到目标字段
            if len(xml_path) == 1:
                # 单层路径（如ml）
                tag_name = xml_path[0]
                tag_start = range_content.find(f'<{tag_name} ')
                if tag_start != -1:
                    value_start = range_content.find('>', tag_start) + 1
                    value_end = range_content.find(f'</{tag_name}>', value_start)
                    if value_start > 0 and value_end > value_start:
                        new_range_content = (range_content[:value_start] +
                                           target_value +
                                           range_content[value_end:])
                        # 更新整个节点内容
                        new_node_content = (node_content[:range_start] +
                                          new_range_content +
                                          node_content[range_end + len('</range>'):])
                        return new_node_content
            elif len(xml_path) == 2:
                # 双层路径（如bv/min）
                parent_tag, child_tag = xml_path

                # 找到父标签
                parent_start = range_content.find(f'<{parent_tag}>')
                if parent_start != -1:
                    parent_end = range_content.find(f'</{parent_tag}>', parent_start)
                    if parent_end != -1:
                        parent_content = range_content[parent_start:parent_end + len(f'</{parent_tag}>')]

                        # 在父标签内找到子标签
                        child_start = parent_content.find(f'<{child_tag} ')
                        if child_start != -1:
                            value_start = parent_content.find('>', child_start) + 1
                            value_end = parent_content.find(f'</{child_tag}>', value_start)
                            if value_start > 0 and value_end > value_start:
                                new_parent_content = (parent_content[:value_start] +
                                                     target_value +
                                                     parent_content[value_end:])
                                new_range_content = (range_content[:parent_start] +
                                                    new_parent_content +
                                                    range_content[parent_end + len(f'</{parent_tag}>'):])
                                new_node_content = (node_content[:range_start] +
                                                  new_range_content +
                                                  node_content[range_end + len('</range>'):])
                                return new_node_content

            return None
        except Exception as e:
            logger.error(f"==liuq debug== 替换range字段失败: {e}")
            return None

    def _replace_boundary_field(self, node_content: str, tag_name: str, target_value: str) -> str:
        """
        替换边界字段值

        Args:
            node_content: 节点内容
            tag_name: 标签名称
            target_value: 目标值

        Returns:
            修改后的节点内容，失败时返回None
        """
        try:
            tag_start = node_content.find(f'<{tag_name} ')
            if tag_start != -1:
                value_start = node_content.find('>', tag_start) + 1
                value_end = node_content.find(f'</{tag_name}>', value_start)
                if value_start > 0 and value_end > value_start:
                    new_content = (node_content[:value_start] +
                                 target_value +
                                 node_content[value_end:])
                    return new_content
            return None
        except Exception as e:
            logger.error(f"==liuq debug== 替换边界字段失败: {e}")
            return None



    def _create_backup(self, xml_path: Path):
        """创建备份文件"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = xml_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        backup_path = backup_dir / f"{xml_path.stem}_backup_{timestamp}.xml"
        shutil.copy2(xml_path, backup_path)



    def _atomic_write_file(self, xml_path: Path, content: str):
        """原子性写入文件"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                        delete=False, suffix='.xml',
                                        dir=xml_path.parent) as temp_file:
            temp_path = temp_file.name
            temp_file.write(content)

        # 原子性替换
        shutil.move(temp_path, xml_path)

    def _get_current_time_ms(self) -> int:
        """获取当前时间（毫秒）"""
        import time
        return int(time.time() * 1000)

    # ==================== 原有方法 ====================

    def parse_xml(self, xml_path: Union[str, Path], device_type: str = "unknown") -> MapConfiguration:
        """
        解析XML文件为MapConfiguration对象
        
        注意：XMLWriterService主要负责写入功能，解析功能委托给XMLParserService
        
        Args:
            xml_path: XML文件路径
            device_type: 设备类型
            
        Returns:
            MapConfiguration: 解析后的配置对象
            
        Raises:
            NotImplementedError: 解析功能请使用XMLParserService
        """
        logger.warning("==liuq debug== XMLWriterService.parse_xml 委托给XMLParserService实现")
        from core.services.xml_parser_service import XMLParserService
        parser = XMLParserService()
        return parser.parse_xml(xml_path, device_type)
    
    def write_xml(self, config: MapConfiguration, xml_path: Union[str, Path],
                  backup: bool = True, preserve_format: bool = True) -> bool:
        """
        将MapConfiguration对象写入XML文件
        
        Args:
            config: 要写入的配置对象
            xml_path: 目标XML文件路径
            backup: 是否创建备份文件
            preserve_format: 是否保持原有格式
            
        Returns:
            bool: 写入是否成功
            
        Raises:
            XMLWriteError: XML写入失败
            PermissionError: 文件权限不足
            ValidationError: 数据验证失败
        """
        logger.info("==liuq debug== write_xml方法重定向到高性能优化方法")

        # 临时设置当前配置和路径以支持优化方法
        original_config = self.current_config
        original_path = self.current_xml_path

        try:
            # 解析XML树
            import xml.etree.ElementTree as ET
            tree = ET.parse(xml_path)

            # 设置临时状态
            self.current_config = config
            self.current_xml_path = Path(xml_path)
            self.current_tree = tree

            # 使用高性能优化方法
            success = self._write_xml_optimized(config, Path(xml_path), backup)

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
        验证XML文件的结构和内容
        
        Args:
            xml_path: XML文件路径
            level: 验证级别
            
        Returns:
            ValidationResult: 验证结果对象
        """
        try:
            xml_path = Path(xml_path)
            
            if not xml_path.exists():
                return ValidationResult(
                    is_valid=False,
                    level=level,
                    errors=[f"文件不存在: {xml_path}"],
                    warnings=[],
                    metadata={}
                )
            
            # 基础XML格式验证
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
            except ET.ParseError as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"XML格式错误: {e}"],
                    warnings=[],
                    validation_level=level
                )
            
            errors = []
            warnings = []
            
            # 根据验证级别进行不同程度的验证
            if level in [ValidationLevel.BASIC, ValidationLevel.FULL]:
                # 基础结构验证
                if root.tag != "root":
                    warnings.append("根元素不是'root'")
            
            if level == ValidationLevel.FULL:
                # 完整验证：检查Map点结构
                map_elements = root.findall('.//Map')
                if not map_elements:
                    # 检查旧格式的offset_map
                    offset_maps = root.findall('.//offset_map*')
                    if not offset_maps:
                        warnings.append("未找到Map点数据")
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                level=level,
                errors=errors,
                warnings=warnings,
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"==liuq debug== XML验证失败: {e}")
            return ValidationResult(
                is_valid=False,
                level=level,
                errors=[f"验证过程中发生错误: {e}"],
                warnings=[],
                metadata={}
            )
    
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
        try:
            xml_path = Path(xml_path)
            
            if not xml_path.exists():
                return {"error": f"文件不存在: {xml_path}"}
            
            stat = xml_path.stat()
            
            metadata = {
                "file_path": str(xml_path),
                "file_size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "encoding": self.default_encoding
            }
            
            # 尝试解析XML获取更多信息
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                
                metadata.update({
                    "root_tag": root.tag,
                    "map_count": len(root.findall('.//Map')) + len(root.findall('.//offset_map*')),
                    "xml_version": tree.getroot().get("version", "unknown")
                })
                
            except ET.ParseError:
                metadata["parse_error"] = "XML格式错误"
            
            return metadata
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取XML元数据失败: {e}")
            return {"error": f"获取元数据失败: {e}"}

    def backup_xml(self, xml_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> str:
        """
        创建XML文件备份

        Args:
            xml_path: 源XML文件路径
            backup_dir: 备份目录，None则使用默认备份目录

        Returns:
            str: 备份文件路径

        Raises:
            BackupError: 备份创建失败
        """
        try:
            xml_path = Path(xml_path)

            if not xml_path.exists():
                raise BackupError(f"源文件不存在: {xml_path}")

            # 确定备份目录
            if backup_dir is None:
                backup_dir = xml_path.parent / "backups"
            else:
                backup_dir = Path(backup_dir)

            # 创建备份目录
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{xml_path.stem}_backup_{timestamp}{xml_path.suffix}"
            backup_path = backup_dir / backup_name

            # 复制文件
            shutil.copy2(xml_path, backup_path)

            logger.info(f"==liuq debug== XML备份创建成功: {backup_path}")
            return str(backup_path)

        except Exception as e:
            error_msg = f"创建备份失败: {e}"
            logger.error(f"==liuq debug== {error_msg}")
            raise BackupError(error_msg)

    def restore_from_backup(self, backup_path: Union[str, Path],
                           target_path: Union[str, Path]) -> bool:
        """
        从备份恢复XML文件

        Args:
            backup_path: 备份文件路径
            target_path: 目标文件路径

        Returns:
            bool: 恢复是否成功
        """
        try:
            backup_path = Path(backup_path)
            target_path = Path(target_path)

            if not backup_path.exists():
                logger.error(f"==liuq debug== 备份文件不存在: {backup_path}")
                return False

            # 复制备份文件到目标位置
            shutil.copy2(backup_path, target_path)

            logger.info(f"==liuq debug== 从备份恢复成功: {target_path}")
            return True

        except Exception as e:
            logger.error(f"==liuq debug== 从备份恢复失败: {e}")
            return False







    def _build_dynamic_alias_mapping(self, root: ET.Element) -> dict:
        """
        动态构建别名到XML节点的映射关系

        {{CHENGQI:
        Action: Added; Timestamp: 2025-07-30 10:55:00 +08:00; Reason: 修复Map点排序导致的XML索引映射错误问题; Principle_Applied: 动态配置原则，消除硬编码;
        }}

        Args:
            root: XML根元素

        Returns:
            dict: 别名到XML节点名称的映射字典
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

        {{CHENGQI:
        Action: Added; Timestamp: 2025-07-30 10:55:00 +08:00; Reason: 修复Map点排序导致的XML索引映射错误问题; Principle_Applied: 动态配置原则，智能缓存机制;
        }}

        Args:
            root: XML根元素
            alias_name: Map点别名

        Returns:
            str: 对应的XML节点名称（如'offset_map01'）
        """
        # 如果还没有构建映射或缓存被清理，则动态构建
        if not hasattr(self, '_alias_mapping_cache') or self._alias_mapping_cache is None:
            self._alias_mapping_cache = self._build_dynamic_alias_mapping(root)

        return self._alias_mapping_cache.get(alias_name, None)







    def _get_map_point_field_value(self, map_point: MapPoint, field_id: str) -> Any:
        """
        从Map点对象获取字段值

        Args:
            map_point: Map点对象
            field_id: 字段ID

        Returns:
            Any: 字段值
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

        Args:
            element: XML元素
            field_def: 字段定义
            value: 字段值
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
                # 关键精度日志

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

        Args:
            parent: 父元素
            path: 元素路径（如 "offset/x"）

        Returns:
            ET.Element: 创建的最终元素
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
