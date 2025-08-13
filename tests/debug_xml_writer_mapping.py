#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML写入逻辑调试测试
专门用于调试"1_BlueSky_Bright"的映射问题
"""

import sys
import os
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.xml_parser_service import XMLParserService
from core.services.xml_writer_service import XMLWriterService
from core.models.map_data import MapConfiguration

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_map_point_mapping():
    """调试Map点到XML节点的映射关系"""
    
    # 测试文件路径
    xml_file = project_root / "tests" / "test_data" / "awb_scenario.xml"
    
    if not xml_file.exists():
        logger.error(f"==liuq debug== 测试文件不存在: {xml_file}")
        return
    
    logger.info(f"==liuq debug== 开始调试XML映射，文件: {xml_file}")
    
    # 1. 解析XML文件
    parser = XMLParserService()
    try:
        config = parser.parse_xml(xml_file)
        logger.info(f"==liuq debug== 成功解析XML，共 {len(config.map_points)} 个Map点")
    except Exception as e:
        logger.error(f"==liuq debug== XML解析失败: {e}")
        return
    
    # 2. 查找"1_BlueSky_Bright"的位置和信息
    target_alias = "1_BlueSky_Bright"
    target_map_point = None
    target_index = -1
    
    for i, map_point in enumerate(config.map_points):

        if map_point.alias_name == target_alias:
            target_map_point = map_point
            target_index = i
            break
    
    if target_map_point is None:
        logger.error(f"==liuq debug== 未找到目标Map点: {target_alias}")
        return
    
    logger.info(f"==liuq debug== 找到目标Map点:")
    logger.info(f"  - 索引: {target_index}")
    logger.info(f"  - 别名: {target_map_point.alias_name}")
    logger.info(f"  - offset_x: {target_map_point.offset_x}")
    logger.info(f"  - offset_y: {target_map_point.offset_y}")
    
    # 3. 分析当前的索引计算逻辑
    logger.info(f"==liuq debug== 分析当前索引计算逻辑:")
    
    # 模拟当前的错误逻辑
    if target_index == 0 and target_map_point.alias_name == "base_boundary0":
        logger.info(f"  - 会被识别为base_boundary处理")
    else:
        offset_index = target_index if target_map_point.alias_name != "base_boundary0" else target_index - 1
        map_index = offset_index + 1
        logger.info(f"  - offset_index = {offset_index}")
        logger.info(f"  - map_index = {map_index}")
        logger.info(f"  - 会查找节点: offset_map{map_index:02d}")
    
    # 4. 计算正确的映射关系
    logger.info(f"==liuq debug== 计算正确的映射关系:")
    
    # 统计非base_boundary的Map点
    non_base_points = [mp for mp in config.map_points if mp.alias_name != "base_boundary0"]
    logger.info(f"  - 非base_boundary点总数: {len(non_base_points)}")
    
    # 找到目标点在非base_boundary点中的位置
    correct_offset_index = -1
    for i, mp in enumerate(non_base_points):
        if mp.alias_name == target_alias:
            correct_offset_index = i
            break
    
    if correct_offset_index >= 0:
        correct_map_index = correct_offset_index + 1  # offset_map从01开始
        logger.info(f"  - 正确的offset_index: {correct_offset_index}")
        logger.info(f"  - 正确的map_index: {correct_map_index}")
        logger.info(f"  - 应该查找节点: offset_map{correct_map_index:02d}")
    
    # 5. 测试修改和保存
    logger.info(f"==liuq debug== 测试修改offset_x值:")
    
    # 备份原始值
    original_offset_x = target_map_point.offset_x
    new_offset_x = 0.598
    
    logger.info(f"  - 原始值: {original_offset_x}")
    logger.info(f"  - 新值: {new_offset_x}")
    
    # 修改值
    target_map_point.offset_x = new_offset_x
    
    # 创建备份文件
    backup_file = xml_file.parent / f"{xml_file.stem}_debug_backup{xml_file.suffix}"
    
    # 写入XML
    writer = XMLWriterService()
    try:
        success = writer.write_xml(config, xml_file, backup=True)
        if success:
            logger.info(f"==liuq debug== XML写入成功")
        else:
            logger.error(f"==liuq debug== XML写入失败")
    except Exception as e:
        logger.error(f"==liuq debug== XML写入异常: {e}")
    
    # 6. 验证写入结果
    logger.info(f"==liuq debug== 验证写入结果:")

    # 重新解析文件
    try:
        new_config = parser.parse_xml(xml_file)
        new_target_point = None

        for mp in new_config.map_points:
            if mp.alias_name == target_alias:
                new_target_point = mp
                break

        if new_target_point:
            logger.info(f"  - 写入后的offset_x: {new_target_point.offset_x}")
            if abs(new_target_point.offset_x - new_offset_x) < 0.001:
                logger.info(f"  - ✓ 值更新正确")
            else:
                logger.error(f"  - ✗ 值更新错误，期望{new_offset_x}，实际{new_target_point.offset_x}")
        else:
            logger.error(f"  - ✗ 重新解析后未找到目标Map点")

    except Exception as e:
        logger.error(f"==liuq debug== 验证失败: {e}")

    # 7. 检查XML中实际的offset_map01节点
    logger.info(f"==liuq debug== 检查XML中的实际节点:")

    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # 检查offset_map01的第一个节点
        offset_map01_nodes = root.findall('.//offset_map01')
        if len(offset_map01_nodes) >= 1:
            first_node = offset_map01_nodes[0]
            offset_elem = first_node.find('offset')
            if offset_elem is not None:
                x_elem = offset_elem.find('x')
                if x_elem is not None:
                    logger.info(f"  - offset_map01第一个节点的offset/x: {x_elem.text}")

        # 检查offset_map17的节点
        offset_map17_nodes = root.findall('.//offset_map17')
        logger.info(f"  - 找到 {len(offset_map17_nodes)} 个offset_map17节点")
        for i, node in enumerate(offset_map17_nodes):
            offset_elem = node.find('offset')
            if offset_elem is not None:
                x_elem = offset_elem.find('x')
                if x_elem is not None:
                    logger.info(f"    - offset_map17节点{i+1}的offset/x: {x_elem.text}")

    except Exception as e:
        logger.error(f"==liuq debug== 检查XML节点失败: {e}")

if __name__ == "__main__":
    debug_map_point_mapping()
