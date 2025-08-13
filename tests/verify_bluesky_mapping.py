#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确验证"1_BlueSky_Bright"到offset_map01的映射关系
"""

import sys
import os
from pathlib import Path
import logging
import shutil
import xml.etree.ElementTree as ET

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.xml_parser_service import XMLParserService
from core.services.xml_writer_service import XMLWriterService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_xml_structure():
    """分析XML文件结构，找出"1_BlueSky_Bright"的真实位置"""
    
    xml_file = project_root / "tests" / "test_data" / "awb_scenario.xml"
    
    logger.info(f"==liuq debug== 分析XML文件结构: {xml_file}")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # 1. 查找所有包含"1_BlueSky_Bright"的节点
        logger.info(f"==liuq debug== 1. 查找所有包含'1_BlueSky_Bright'的节点:")
        
        bluesky_nodes = []
        for elem in root.iter():
            if elem.text and "1_BlueSky_Bright" in elem.text:
                # 找到父节点的标签名
                parent = elem.getparent() if hasattr(elem, 'getparent') else None
                if parent is not None:
                    parent_tag = parent.tag
                else:
                    # 使用xpath查找父节点
                    xpath = f".//*[text()='1_BlueSky_Bright']/.."
                    parents = root.findall(xpath)
                    parent_tag = parents[0].tag if parents else "unknown"
                
                bluesky_nodes.append({
                    'element': elem,
                    'parent_tag': parent_tag,
                    'text': elem.text
                })
                logger.info(f"  - 找到节点: {elem.tag} = '{elem.text}' (父节点: {parent_tag})")
        
        # 2. 查找offset_map01的所有实例
        logger.info(f"==liuq debug== 2. 查找offset_map01的所有实例:")
        
        offset_map01_nodes = root.findall('.//offset_map01')
        logger.info(f"  - 找到 {len(offset_map01_nodes)} 个offset_map01节点")
        
        for i, node in enumerate(offset_map01_nodes):
            logger.info(f"  - offset_map01节点 {i+1}:")
            
            # 检查是否有offset子节点（第一组数据）
            offset_elem = node.find('offset')
            if offset_elem is not None:
                x_elem = offset_elem.find('x')
                y_elem = offset_elem.find('y')
                if x_elem is not None and y_elem is not None:
                    logger.info(f"    * 第一组数据 - offset/x: {x_elem.text}, offset/y: {y_elem.text}")
            
            # 检查是否有AliasName子节点（第二组数据）
            alias_elem = node.find('AliasName')
            if alias_elem is not None:
                logger.info(f"    * 第二组数据 - AliasName: {alias_elem.text}")
            
            # 检查其他关键字段
            for child in node:
                if child.tag in ['Num', 'RpG', 'BpG', 'MapEnabled', 'ViewState', 'TransStep']:
                    logger.info(f"    * {child.tag}: {child.text}")
        
        # 3. 分析"1_BlueSky_Bright"应该对应的offset_map节点
        logger.info(f"==liuq debug== 3. 分析'1_BlueSky_Bright'的正确映射:")
        
        # 查找包含"1_BlueSky_Bright"的offset_map节点
        for bluesky_node in bluesky_nodes:
            if bluesky_node['parent_tag'].startswith('offset_map'):
                logger.info(f"  - '1_BlueSky_Bright'位于: {bluesky_node['parent_tag']}")
                
                # 找到对应的第一组数据节点
                parent_tag = bluesky_node['parent_tag']
                first_group_nodes = root.findall(f'.//{parent_tag}')
                
                for i, node in enumerate(first_group_nodes):
                    offset_elem = node.find('offset')
                    if offset_elem is not None:
                        x_elem = offset_elem.find('x')
                        if x_elem is not None:
                            logger.info(f"  - 对应的第一组数据在{parent_tag}节点{i+1}，offset/x: {x_elem.text}")
                            return parent_tag, x_elem.text
        
        return None, None
        
    except Exception as e:
        logger.error(f"==liuq debug== 分析XML结构失败: {e}")
        return None, None

def verify_mapping_logic():
    """验证当前的映射逻辑是否正确"""
    
    xml_file = project_root / "tests" / "test_data" / "awb_scenario.xml"
    
    logger.info(f"==liuq debug== 验证映射逻辑:")
    
    # 1. 解析XML获取map_points
    parser = XMLParserService()
    try:
        config = parser.parse_xml(xml_file)
        logger.info(f"==liuq debug== 成功解析XML，共 {len(config.map_points)} 个Map点")
    except Exception as e:
        logger.error(f"==liuq debug== XML解析失败: {e}")
        return False
    
    # 2. 查找"1_BlueSky_Bright"在map_points中的位置
    target_alias = "1_BlueSky_Bright"
    target_index = -1
    
    logger.info(f"==liuq debug== Map点列表分析:")
    for i, map_point in enumerate(config.map_points):
        logger.info(f"  索引{i}: {map_point.alias_name}")
        if map_point.alias_name == target_alias:
            target_index = i
    
    if target_index == -1:
        logger.error(f"==liuq debug== 未找到{target_alias}")
        return False
    
    logger.info(f"==liuq debug== '{target_alias}'在map_points中的索引: {target_index}")
    
    # 3. 计算当前修复后的映射逻辑
    non_base_points = [mp for mp in config.map_points if mp.alias_name != "base_boundary0"]
    offset_map_counter = 1
    
    logger.info(f"==liuq debug== 当前映射逻辑计算:")
    logger.info(f"  - 非base_boundary点总数: {len(non_base_points)}")
    
    for i, mp in enumerate(non_base_points):
        expected_map_node = f"offset_map{offset_map_counter:02d}"
        logger.info(f"  - 非base_boundary索引{i}: {mp.alias_name} -> {expected_map_node}")
        
        if mp.alias_name == target_alias:
            logger.info(f"==liuq debug== 根据当前逻辑，'{target_alias}'应该映射到: {expected_map_node}")
            return expected_map_node
        
        offset_map_counter += 1
    
    return None

def test_precise_mapping():
    """精确测试"1_BlueSky_Bright"的映射和修改"""
    
    logger.info(f"==liuq debug== 开始精确映射测试")
    
    # 1. 分析XML结构
    actual_xml_node, current_offset_x = analyze_xml_structure()
    if actual_xml_node:
        logger.info(f"==liuq debug== XML分析结果: '{target_alias}'实际位于 {actual_xml_node}")
        logger.info(f"==liuq debug== 当前offset/x值: {current_offset_x}")
    
    # 2. 验证映射逻辑
    expected_xml_node = verify_mapping_logic()
    if expected_xml_node:
        logger.info(f"==liuq debug== 映射逻辑结果: '{target_alias}'应该映射到 {expected_xml_node}")
    
    # 3. 比较结果
    if actual_xml_node and expected_xml_node:
        if actual_xml_node == expected_xml_node:
            logger.info(f"==liuq debug== ✓ 映射关系正确: {actual_xml_node}")
        else:
            logger.error(f"==liuq debug== ✗ 映射关系错误!")
            logger.error(f"  - XML中实际位置: {actual_xml_node}")
            logger.error(f"  - 逻辑计算位置: {expected_xml_node}")
            return False
    
    # 4. 执行修改测试
    test_xml = project_root / "tests" / "test_data" / "test_precise_mapping.xml"
    original_xml = project_root / "tests" / "test_data" / "awb_scenario.xml"
    shutil.copy2(original_xml, test_xml)
    
    logger.info(f"==liuq debug== 执行修改测试:")
    
    # 解析并修改
    parser = XMLParserService()
    config = parser.parse_xml(test_xml)
    
    target_map_point = None
    for mp in config.map_points:
        if mp.alias_name == "1_BlueSky_Bright":
            target_map_point = mp
            break
    
    if target_map_point:
        original_value = target_map_point.offset_x
        new_value = 0.598
        target_map_point.offset_x = new_value
        
        logger.info(f"  - 修改offset_x: {original_value} -> {new_value}")
        
        # 写入XML
        writer = XMLWriterService()
        success = writer.write_xml(config, test_xml, backup=True)
        
        if success:
            logger.info(f"  - XML写入成功")
            
            # 验证XML中的实际值
            tree = ET.parse(test_xml)
            root = tree.getroot()
            
            # 检查实际应该更新的节点
            if actual_xml_node:
                nodes = root.findall(f'.//{actual_xml_node}')
                for i, node in enumerate(nodes):
                    offset_elem = node.find('offset')
                    if offset_elem is not None:
                        x_elem = offset_elem.find('x')
                        if x_elem is not None:
                            xml_value = float(x_elem.text)
                            logger.info(f"  - {actual_xml_node}节点{i+1}的offset/x: {xml_value}")
                            
                            if abs(xml_value - new_value) < 0.001:
                                logger.info(f"  - ✓ 值更新正确")
                                return True
                            else:
                                logger.error(f"  - ✗ 值更新错误，期望{new_value}，实际{xml_value}")
    
    return False

if __name__ == "__main__":
    target_alias = "1_BlueSky_Bright"
    
    logger.info(f"==liuq debug== 开始精确验证'{target_alias}'的映射关系")
    
    success = test_precise_mapping()
    
    if success:
        logger.info(f"==liuq debug== ✓ 映射验证成功！")
    else:
        logger.error(f"==liuq debug== ✗ 映射验证失败，需要进一步修复")
