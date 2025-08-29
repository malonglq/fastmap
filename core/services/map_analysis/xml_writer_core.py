#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML Writer Core - 核心写入辅助逻辑

从 XMLPerformanceService 抽离的通用、与性能无关的核心算法：
- base_boundary0 定位
- 别名映射（findall + AliasName 过滤）
- 双节点配对搜索（数据节点 + 含 AliasName 元数据节点）
- 当前 offset 值获取
- 字段值提取（支持 OFFSET 与 RANGE）
- 字段替换（offset 与 range）

说明：保留 ==liuq debug== 日志，供上层服务诊断。
"""

import logging
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

from core.models.map_data import XMLFieldNodeType

logger = logging.getLogger(__name__)


class XMLWriterCore:
    """XML写入核心算法封装"""

    def __init__(self):
        self._alias_mapping_cache: Optional[dict] = None

    # ---------- base_boundary ----------
    def find_base_boundary_node(self, content: str) -> tuple:
        """查找<base_boundary0>节点位置（返回起止索引）。注意：AliasName 文本非固定（如“Base Boundary”）。"""
        try:
            start = content.find('<base_boundary0>')
            if start == -1:
                logger.warning("==liuq debug== 未找到<base_boundary0>开始标签")
                return -1, -1
            end = content.find('</base_boundary0>', start)
            if end == -1:
                logger.warning("==liuq debug== 未找到</base_boundary0>结束标签")
                return -1, -1
            return start, end + len('</base_boundary0>')
        except Exception as e:
            logger.error(f"==liuq debug== 查找base_boundary0节点失败: {e}")
            return -1, -1

    # ---------- 别名映射 ----------
    def _build_dynamic_alias_mapping(self, root: ET.Element) -> dict:
        """动态构建别名到XML节点名称的映射（按AliasName筛选候选节点）"""
        alias_mapping = {}
        try:
            for i in range(1, 300):
                formatted_i = f"0{i}" if i < 10 else str(i)
                element_name = f"offset_map{formatted_i}"
                candidates = root.findall(f'.//{element_name}')
                if not candidates:
                    continue
                picked = None
                for node in candidates:
                    alias_node = node.find('AliasName')
                    if alias_node is not None and alias_node.text and alias_node.text.strip():
                        picked = alias_node.text.strip()
                        break
                if picked:
                    alias_mapping[picked] = element_name
            logger.info(f"==liuq debug== 构建别名映射完成: {len(alias_mapping)} 条（按AliasName筛选候选节点）")
            return alias_mapping
        except Exception as e:
            logger.error(f"==liuq debug== 构建别名映射失败: {e}")
            return {}

    def get_xml_node_name_by_alias(self, root: ET.Element, alias_name: str) -> Optional[str]:
        """根据别名获取对应的XML节点名称（带缓存）"""
        if self._alias_mapping_cache is None:
            self._alias_mapping_cache = self._build_dynamic_alias_mapping(root)
        return self._alias_mapping_cache.get(alias_name)

    # ---------- 节点精确定位（双节点配对） ----------
    def _find_exact_node_by_alias(self, content: str, node_name: str, alias_name: str) -> tuple:
        """根据alias_name精确定位XML节点位置（双节点配对：第一个为数据、第二个为含AliasName的元数据）"""
        try:
            search_start = 0
            while True:
                # 第一个（数据）
                first_start = content.find(f'<{node_name}>', search_start)
                if first_start == -1:
                    break
                first_end = content.find(f'</{node_name}>', first_start)
                if first_end == -1:
                    break
                # 紧随其后的第二个（带AliasName）
                second_start = content.find(f'<{node_name}>', first_end + len(f'</{node_name}>'))
                if second_start == -1:
                    # 兼容：有时AliasName就在第一个里
                    node_content = content[first_start:first_end + len(f'</{node_name}>')]
                    alias_start = node_content.find('<AliasName')
                    if alias_start != -1:
                        tag_end = node_content.find('>', alias_start)
                        content_end = node_content.find('</AliasName>', tag_end)
                        if tag_end != -1 and content_end != -1:
                            found_alias = node_content[tag_end + 1:content_end].strip()
                            if found_alias == alias_name:
                                return first_start, first_end + len(f'</{node_name}>')
                    break
                second_end = content.find(f'</{node_name}>', second_start)
                if second_end == -1:
                    break
                # 在第二个里找 AliasName
                second_content = content[second_start:second_end + len(f'</{node_name}>')]
                alias_start = second_content.find('<AliasName')
                if alias_start != -1:
                    tag_end = second_content.find('>', alias_start)
                    content_end = second_content.find('</AliasName>', tag_end)
                    if tag_end != -1 and content_end != -1:
                        found_alias = second_content[tag_end + 1:content_end].strip()
                        if found_alias == alias_name:
                            return first_start, first_end + len(f'</{node_name}>')
                search_start = second_end + len(f'</{node_name}>')
            logger.warning(f"==liuq debug== 未找到匹配的节点对: {node_name}, 别名: {alias_name}")
            return -1, -1
        except Exception as e:
            logger.error(f"==liuq debug== 精确节点定位失败: {e}")
            return -1, -1

    # ---------- 当前offset值 ----------
    def get_current_offset_values(self, content: str, xml_node_name: str, alias_name: str) -> tuple:
        """获取XML中当前的offset_x和offset_y值"""
        try:
            node_start, node_end = self._find_exact_node_by_alias(content, xml_node_name, alias_name)
            if node_start == -1 or node_end == -1:
                return "0", "0"
            node_content = content[node_start:node_end]
            current_offset_x = "0"
            x_start = node_content.find('<x ')
            if x_start != -1:
                value_start = node_content.find('>', x_start) + 1
                value_end = node_content.find('</x>', value_start)
                if value_start > 0 and value_end > value_start:
                    current_offset_x = node_content[value_start:value_end].strip()
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

    # ---------- 解析字段值 ----------
    def extract_field_value_from_content(self, node_content: str, field_config) -> Optional[str]:
        """从节点内容中提取字段值（支持offset与range）"""
        try:
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

    # ---------- 字段替换 ----------
    def replace_offset_field(self, node_content: str, xml_path: tuple, target_value: str) -> Optional[str]:
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

    def replace_range_field(self, node_content: str, xml_path: tuple, target_value: str) -> Optional[str]:
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

