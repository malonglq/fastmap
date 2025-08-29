#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML性能优化服务

负责XML写入的性能优化功能

作者: AI Assistant
日期: 2025-08-25
"""

import logging
import time
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from core.services.map_analysis.xml_writer_core import XMLWriterCore
from pathlib import Path
from xml.etree import ElementTree as ET

from core.models.map_data import (
    MapConfiguration, MapPoint, BaseBoundary, XML_FIELD_CONFIG,
    XMLFieldNodeType, get_map_point_field_value
)
from core.services.map_analysis.xml_formatting_service import get_xml_formatting_service

logger = logging.getLogger(__name__)


class XMLPerformanceService:
    """XML性能优化服务"""

    def __init__(self):
        """初始化XML性能优化服务"""
        self.compiled_patterns = {}
        self._precompile_patterns()
        # 注入核心写入算法（与性能无关）
        self.core = XMLWriterCore()


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

    def get_current_time_ms(self) -> int:
        """获取当前时间（毫秒）"""
        return int(time.time() * 1000)

    def write_xml_optimized(self, config: MapConfiguration, xml_path: Path,
                           backup: bool = True, tree: Optional[ET.ElementTree] = None) -> bool:
        """
        优化的XML写入方法（高性能批量替换）

        Args:
            config: Map配置对象
            xml_path: XML文件路径
            backup: 是否创建备份
            tree: XML树对象（可选）

        Returns:
            bool: 写入是否成功
        """
        try:
            start_time = self.get_current_time_ms()

            # 1. 读取原始文件内容
            with open(xml_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            file_size = len(original_content)
            logger.info(f"开始高性能XML写入，文件大小: {file_size} 字符")

            # 2. 构建批量替换操作
            replacements = self.build_optimized_replacements(config, original_content, tree)

            if not replacements:
                logger.info("==liuq debug== 高性能写入：没有需要替换的数据，返回False以触发回退")
                return False

            # 3. 执行批量替换
            modified_content = self.execute_optimized_replacements(original_content, replacements)

            # 4. 创建备份（如果需要）
            if backup:
                self.create_backup(xml_path)

            # 5. 原子性写入文件
            self.atomic_write_file(xml_path, modified_content)

            # 6. 性能统计
            end_time = self.get_current_time_ms()
            duration = end_time - start_time

            logger.info(f"高性能XML写入完成，耗时: {duration}ms，替换操作: {len(replacements)}个")

            return True

        except Exception as e:
            logger.error(f"高性能XML写入失败: {e}")
            return False

    def build_optimized_replacements(self, config: MapConfiguration,
                                   content: str, tree: Optional[ET.ElementTree] = None) -> list:
        """
        构建优化的批量替换操作列表

        Args:
            config: Map配置对象
            content: 原始XML内容
            tree: XML树对象

        Returns:
            list: 替换操作列表
        """
        replacements = []

        # 1. 处理边界数据
        if config.base_boundary:
            replacements.extend(self.build_boundary_replacements(config.base_boundary, content))

        # 2. 处理Map点数据
        if tree:
            root = tree.getroot()
            replacements.extend(self.build_map_point_replacements(config.map_points, root, content))

        # 3. 智能差异检测：只保留真正需要替换的操作
        filtered_replacements = self.filter_changed_replacements(replacements, content)

        return filtered_replacements

    def build_boundary_replacements(self, boundary: BaseBoundary, content: str) -> list:
        """
        构建边界数据替换操作

        Args:
            boundary: 边界对象
            content: 原始XML内容

        Returns:
            list: 替换操作列表
        """
        replacements = []

        # 精确定位base_boundary0节点
        base_boundary_start, base_boundary_end = self.core.find_base_boundary_node(content)
        if base_boundary_start == -1 or base_boundary_end == -1:
            logger.warning("未找到base_boundary0节点，跳过边界数据替换")
            return replacements

        # 获取base_boundary0节点内容
        boundary_node_content = content[base_boundary_start:base_boundary_end]

        formatting_service = get_xml_formatting_service()

        # 检查RpG是否需要替换
        current_rpg = self.extract_boundary_field_value(boundary_node_content, 'RpG')
        target_rpg = formatting_service.format_number_for_xml(boundary.rpg)

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
        current_bpg = self.extract_boundary_field_value(boundary_node_content, 'BpG')
        target_bpg = formatting_service.format_number_for_xml(boundary.bpg)

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

        logger.info(f"边界数据替换操作构建完成，共 {len(replacements)} 个操作")
        return replacements

    def build_map_point_replacements(self, map_points: list, root: ET.Element, content: str) -> list:
        """
        构建Map点替换操作

        Args:
            map_points: Map点列表
            root: XML根元素
            content: 原始XML内容

        Returns:
            list: 替换操作列表
        """
        replacements = []

        for map_point in map_points:
            if map_point.alias_name == "base_boundary0":
                continue

            # 获取XML节点名称
            xml_node_name = self.core.get_xml_node_name_by_alias(root, map_point.alias_name)
            if not xml_node_name:
                logger.warning(f"未找到Map点 {map_point.alias_name} 对应的XML节点")
                continue

            # 先检查这个Map点是否真的需要修改
            current_offset_x, current_offset_y = self.core.get_current_offset_values(content, xml_node_name, map_point.alias_name)

            formatting_service = get_xml_formatting_service()
            target_offset_x = formatting_service.format_number_for_xml(map_point.offset_x)
            target_offset_y = formatting_service.format_number_for_xml(map_point.offset_y)

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

            # 添加所有其他字段的替换操作
            single_map_replacements = self.build_single_map_replacements(map_point, xml_node_name)
            replacements.extend(single_map_replacements)

        logger.info(f"Map点替换操作构建完成，共 {len(replacements)} 个有效操作")
        return replacements

    def build_single_map_replacements(self, map_point: MapPoint, xml_node_name: str) -> list:
        """
        为单个Map点构建替换操作（支持所有字段类型）

        Args:
            map_point: Map点对象
            xml_node_name: XML节点名称

        Returns:
            list: 替换操作列表
        """
        replacements = []

        formatting_service = get_xml_formatting_service()

        # 使用配置驱动的字段处理方式
        for field_name, config in XML_FIELD_CONFIG.items():
            try:
                # 获取字段值
                field_value = get_map_point_field_value(map_point, field_name)

                # 使用统一的格式化函数
                formatted_value = formatting_service.format_field_value(field_value, field_name)

                # 创建替换操作信息
                replacement_info = {
                    'node_name': xml_node_name,
                    'field_type': field_name,
                    'replacement': formatted_value,
                    'alias_name': map_point.alias_name,
                    'field_name': field_name,
                    'node_type': config.node_type.value,
                    'xml_path': config.xml_path
                }
                replacements.append(replacement_info)

            except Exception as e:
                logger.warning(f"处理字段 {field_name} 失败: {e}")
                continue

        logger.info(f"为Map点 {map_point.alias_name} 创建了 {len(replacements)} 个字段替换操作")
        return replacements

    def execute_optimized_replacements(self, content: str, replacements: list) -> str:
        """
        执行超高性能批量替换操作

        Args:
            content: 原始XML内容
            replacements: 替换操作列表

        Returns:
            str: 修改后的XML内容
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

            # 获取节点内容
            node_content = modified_content[node_start:node_end]

            # 使用配置驱动的字段替换
            if field_type in XML_FIELD_CONFIG:
                config = XML_FIELD_CONFIG[field_type]

                if config.node_type == XMLFieldNodeType.OFFSET:
                    # 处理offset节点字段
                    new_node_content = self.core.replace_offset_field(node_content, config.xml_path, target_value)
                elif config.node_type == XMLFieldNodeType.RANGE:
                    # 处理range节点字段
                    new_node_content = self.core.replace_range_field(node_content, config.xml_path, target_value)
                else:
                    new_node_content = None

                if new_node_content:
                    # 更新修改后的内容
                    modified_content = (modified_content[:node_start] +
                                      new_node_content +
                                      modified_content[node_end:])
                    replacement_count += 1
                else:
                    logger.warning(f"字段替换失败: {field_type}")

            elif field_type in ['boundary_rpg', 'boundary_bpg']:
                # 处理边界字段
                tag_name = 'RpG' if field_type == 'boundary_rpg' else 'BpG'
                new_node_content = self.replace_boundary_field(node_content, tag_name, target_value)

                if new_node_content:
                    modified_content = (modified_content[:node_start] +
                                      new_node_content +
                                      modified_content[node_end:])
                    replacement_count += 1

            else:
                logger.warning(f"未知字段类型: {field_type}")

        logger.info(f"完成批量替换操作，共执行 {replacement_count} 个替换")
        return modified_content

    # 以下为辅助方法（参考legacy实现，做精简适配）
    # 以下辅助方法已迁移到 XMLWriterCore，并通过 self.core 调用

    def extract_boundary_field_value(self, node_content: str, field_name: str) -> str:
        """从节点内容中提取边界字段值"""
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





    def _extract_field_value_from_content(self, node_content: str, field_config) -> str:
        """从节点内容中提取字段值（支持offset与range）"""
        try:
            from core.models.map_data import XMLFieldNodeType
            if field_config.node_type == XMLFieldNodeType.OFFSET:
                tag_name = field_config.xml_path[0]
                pattern = f'<{tag_name}[^>]*>([^<]*)</{tag_name}>'
            elif field_config.node_type == XMLFieldNodeType.RANGE:
                if len(field_config.xml_path) == 1:
                    tag_name = field_config.xml_path[0]
                    pattern = f'<{tag_name}[^>]*>([^<]*)</{tag_name}>'
                elif len(field_config.xml_path) == 2:
                    parent_tag, child_tag = field_config.xml_path
                    pattern = f'<{parent_tag}[^>]*>.*?<{child_tag}[^>]*>([^<]*)</{child_tag}>.*?</{parent_tag}>'
                else:
                    return None
            else:
                return None
            import re
            match = re.search(pattern, node_content, re.DOTALL)
            if match:
                return match.group(1).strip()
            return None
        except Exception as e:
            logger.error(f"==liuq debug== 提取字段值失败: {e}")
            return None

    def filter_changed_replacements(self, replacements: list, content: str) -> list:
        """智能差异检测：只保留真正需要替换的操作，并填充节点范围元数据"""
        filtered_replacements = []
        from core.models.map_data import XML_FIELD_CONFIG
        for i, replacement in enumerate(replacements):
            if 'node_name' in replacement:
                node_name = replacement['node_name']
                field_type = replacement['field_type']
                target_value = replacement['replacement']
                alias_name = replacement['alias_name']
                node_start, node_end = self.core._find_exact_node_by_alias(content, node_name, alias_name)
                if node_start == -1 or node_end == -1:
                    logger.warning(f"==liuq debug== 跳过替换操作 {i+1}: 未找到节点 {node_name} (别名: {alias_name})")
                    continue
                node_content = content[node_start:node_end]
                # 直接依据字段配置解析当前值（无需存在<offset>包裹）
                field_found = False
                current_value = None
                if field_type in XML_FIELD_CONFIG:
                    config = XML_FIELD_CONFIG[field_type]
                    current_value = self.core.extract_field_value_from_content(node_content, config)
                    field_found = current_value is not None
                if not field_found:
                    logger.warning(f"==liuq debug== 跳过替换操作 {i+1}: 未找到字段 {field_type}")
                    continue
                if current_value != target_value:
                    replacement['_node_start'] = node_start
                    replacement['_node_end'] = node_end
                    replacement['_current_value'] = current_value
                    filtered_replacements.append(replacement)
                    logger.info(f"==liuq debug== 添加有效替换操作: {alias_name}.{field_type}: {current_value} -> {target_value}")
                else:
                    logger.debug(f"==liuq debug== 跳过替换操作 {i+1}: 值未变化 ({current_value})")
            else:
                # 处理边界数据替换（已在构建时验证）
                if 'field_type' in replacement and replacement['field_type'].startswith('boundary_'):
                    filtered_replacements.append(replacement)
                    field_name = replacement.get('field_name', 'unknown')
                    current_value = replacement.get('_current_value', 'unknown')
                    target_value = replacement.get('replacement', 'unknown')
                    logger.info(f"==liuq debug== 添加边界数据替换操作: {field_name}: {current_value} -> {target_value}")
        logger.info(f"==liuq debug== 过滤完成，有效替换操作数: {len(filtered_replacements)}")
        return filtered_replacements

    def replace_offset_field(self, node_content: str, xml_path: tuple, target_value: str) -> str:
        """替换offset节点中的字段值"""
        try:
            if len(xml_path) != 1:
                return None
            tag_name = xml_path[0]
            tag_start = node_content.find(f'<{tag_name} ')
            if tag_start != -1:
                value_start = node_content.find('>', tag_start) + 1
                value_end = node_content.find(f'</{tag_name}>', value_start)
                if value_start > 0 and value_end > value_start:
                    new_content = node_content[:value_start] + target_value + node_content[value_end:]
                    return new_content
            return None
        except Exception as e:
            logger.error(f"==liuq debug== 替换offset字段失败: {e}")
            return None

    def replace_range_field(self, node_content: str, xml_path: tuple, target_value: str) -> str:
        """替换range节点中的字段值"""
        try:
            range_start = node_content.find('<range>')
            if range_start == -1:
                return None
            range_end = node_content.find('</range>', range_start)
            if range_end == -1:
                return None
            range_content = node_content[range_start:range_end + len('</range>')]
            if len(xml_path) == 1:
                tag_name = xml_path[0]
                tag_start = range_content.find(f'<{tag_name} ')
                if tag_start != -1:
                    value_start = range_content.find('>', tag_start) + 1
                    value_end = range_content.find(f'</{tag_name}>', value_start)
                    if value_start > 0 and value_end > value_start:
                        new_range_content = range_content[:value_start] + target_value + range_content[value_end:]
                        return node_content[:range_start] + new_range_content + node_content[range_end + len('</range>'):]
            elif len(xml_path) == 2:
                parent_tag, child_tag = xml_path
                parent_start = range_content.find(f'<{parent_tag}>')
                if parent_start != -1:
                    parent_end = range_content.find(f'</{parent_tag}>', parent_start)
                    if parent_end != -1:
                        parent_content = range_content[parent_start:parent_end + len(f'</{parent_tag}>')]
                        child_start = parent_content.find(f'<{child_tag} ')
                        if child_start != -1:
                            value_start = parent_content.find('>', child_start) + 1
                            value_end = parent_content.find(f'</{child_tag}>', value_start)
                            if value_start > 0 and value_end > value_start:
                                new_parent_content = parent_content[:value_start] + target_value + parent_content[value_end:]
                                new_range_content = range_content[:parent_start] + new_parent_content + range_content[parent_end + len(f'</{parent_tag}>'):]
                                return node_content[:range_start] + new_range_content + node_content[range_end + len('</range>'):]
            return None
        except Exception as e:
            logger.error(f"==liuq debug== 替换range字段失败: {e}")
            return None

    def replace_boundary_field(self, node_content: str, tag_name: str, target_value: str) -> str:
        """替换边界字段值"""
        try:
            tag_start = node_content.find(f'<{tag_name} ')
            if tag_start != -1:
                value_start = node_content.find('>', tag_start) + 1
                value_end = node_content.find(f'</{tag_name}>', value_start)
                if value_start > 0 and value_end > value_start:
                    return node_content[:value_start] + target_value + node_content[value_end:]
            return None
        except Exception as e:
            logger.error(f"==liuq debug== 替换边界字段失败: {e}")
            return None

    def create_backup(self, xml_path: Path):
        """创建备份文件（委托备份服务）"""
        try:
            from core.services.map_analysis.xml_writer_service import get_xml_backup_service
        except Exception:
            pass
        # 回退到简单复制（保持原行为）
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = xml_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / f"{xml_path.stem}_backup_{timestamp}.xml"
            shutil.copy2(xml_path, backup_path)
            logger.info(f"==liuq debug== XML备份创建成功: {backup_path}")
        except Exception as e:
            logger.warning(f"==liuq debug== 创建备份失败: {e}")

    def atomic_write_file(self, xml_path: Path, content: str):
        """原子性写入文件"""
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.xml', dir=xml_path.parent) as temp_file:
                temp_path = temp_file.name
                temp_file.write(content)
            shutil.move(temp_path, xml_path)
            logger.info("==liuq debug== 原子性写入完成")
        except Exception as e:
            logger.error(f"==liuq debug== 原子性写入失败: {e}")


# 全局性能服务实例
_performance_service: Optional[XMLPerformanceService] = None


def get_xml_performance_service() -> XMLPerformanceService:
    """获取XML性能优化服务实例"""
    global _performance_service

    if _performance_service is None:
        _performance_service = XMLPerformanceService()
        logger.info("创建XML性能优化服务实例")

    return _performance_service