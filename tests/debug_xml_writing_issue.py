#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深入调试XML写入问题
使用指定的测试文件进行完整的问题重现和诊断
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

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_xml_writing_issue():
    """深入调试XML写入问题"""
    
    # 使用指定的测试文件
    test_xml = Path("e:/code/3__My/22_tool_fastmapv2/tests/test_data/awb_scenario.xml")
    
    if not test_xml.exists():
        logger.error(f"==liuq debug== ❌ 指定的测试文件不存在: {test_xml}")
        return False
    
    # 创建工作副本
    work_xml = test_xml.parent / "debug_work_copy.xml"
    shutil.copy2(test_xml, work_xml)
    
    logger.info(f"==liuq debug== 🔍 开始深入调试XML写入问题")
    logger.info(f"==liuq debug== 使用测试文件: {test_xml}")
    logger.info(f"==liuq debug== 工作副本: {work_xml}")
    
    # 1. 解析XML并检查原始数据
    logger.info(f"==liuq debug== === 步骤1: 解析XML并检查原始数据 ===")
    
    parser = XMLParserService()
    config = parser.parse_xml(work_xml)
    
    # 查找"1_BlueSky_Bright"
    target_map_point = None
    for mp in config.map_points:
        if mp.alias_name == "1_BlueSky_Bright":
            target_map_point = mp
            break
    
    if target_map_point is None:
        logger.error(f"==liuq debug== ❌ 未找到'1_BlueSky_Bright'")
        return False
    
    logger.info(f"==liuq debug== 找到目标Map点: {target_map_point.alias_name}")
    logger.info(f"==liuq debug== 原始数据:")
    logger.info(f"  - offset_x (Offset R/G): {target_map_point.offset_x}")
    logger.info(f"  - offset_y (Offset B/G): {target_map_point.offset_y}")
    logger.info(f"  - weight: {target_map_point.weight}")
    logger.info(f"  - detect_flag: {target_map_point.detect_flag} (类型: {type(target_map_point.detect_flag)})")
    
    # 2. 检查XML中的原始值
    logger.info(f"==liuq debug== === 步骤2: 检查XML中的原始值 ===")
    
    tree = ET.parse(work_xml)
    root = tree.getroot()
    
    # 查找offset_map01的双组数据
    offset_map01_nodes = root.findall('.//offset_map01')
    if len(offset_map01_nodes) >= 2:
        # 第一组数据
        first_node = offset_map01_nodes[0]
        offset_elem = first_node.find('offset')
        if offset_elem is not None:
            x_elem = offset_elem.find('x')
            y_elem = offset_elem.find('y')
            if x_elem is not None and y_elem is not None:
                original_xml_x = x_elem.text
                original_xml_y = y_elem.text
                logger.info(f"==liuq debug== XML中offset_map01第一组数据:")
                logger.info(f"  - offset/x: {original_xml_x}")
                logger.info(f"  - offset/y: {original_xml_y}")
        
        # 检查DetectMapFlag
        range_elem = first_node.find('range')
        if range_elem is not None:
            detect_flag_elem = range_elem.find('DetectMapFlag')
            if detect_flag_elem is not None:
                original_detect_flag = detect_flag_elem.text
                logger.info(f"  - DetectMapFlag: {original_detect_flag} (XML原始值)")
        
        # 第二组数据
        second_node = offset_map01_nodes[1]
        alias_elem = second_node.find('AliasName')
        if alias_elem is not None:
            original_alias = alias_elem.text
            logger.info(f"==liuq debug== XML中offset_map01第二组数据:")
            logger.info(f"  - AliasName: {original_alias}")
    
    # 3. 执行修改
    logger.info(f"==liuq debug== === 步骤3: 执行修改 ===")
    
    original_offset_x = target_map_point.offset_x
    new_offset_x = 0.999  # 使用一个明显的测试值
    target_map_point.offset_x = new_offset_x
    
    logger.info(f"==liuq debug== 修改 Offset R/G: {original_offset_x} -> {new_offset_x}")
    
    # 4. 保存XML
    logger.info(f"==liuq debug== === 步骤4: 保存XML ===")
    
    writer = XMLWriterService()
    try:
        success = writer.write_xml(config, work_xml, backup=True)
        if success:
            logger.info(f"==liuq debug== ✅ XML保存成功")
        else:
            logger.error(f"==liuq debug== ❌ XML保存失败")
            return False
    except Exception as e:
        logger.error(f"==liuq debug== ❌ XML保存异常: {e}")
        return False
    
    # 5. 验证XML中的实际更新
    logger.info(f"==liuq debug== === 步骤5: 验证XML中的实际更新 ===")
    
    # 重新解析XML文件
    tree = ET.parse(work_xml)
    root = tree.getroot()
    
    offset_map01_nodes = root.findall('.//offset_map01')
    if len(offset_map01_nodes) >= 2:
        # 检查第一组数据是否更新
        first_node = offset_map01_nodes[0]
        offset_elem = first_node.find('offset')
        if offset_elem is not None:
            x_elem = offset_elem.find('x')
            y_elem = offset_elem.find('y')
            if x_elem is not None and y_elem is not None:
                updated_xml_x = x_elem.text
                updated_xml_y = y_elem.text
                logger.info(f"==liuq debug== 更新后XML中offset_map01第一组数据:")
                logger.info(f"  - offset/x: {updated_xml_x} (期望: {new_offset_x})")
                logger.info(f"  - offset/y: {updated_xml_y}")
                
                # 验证更新是否正确
                try:
                    xml_x_float = float(updated_xml_x)
                    if abs(xml_x_float - new_offset_x) < 0.001:
                        logger.info(f"==liuq debug== ✅ offset/x更新正确")
                    else:
                        logger.error(f"==liuq debug== ❌ offset/x更新错误！")
                        logger.error(f"  期望: {new_offset_x}")
                        logger.error(f"  实际: {xml_x_float}")
                        return False
                except ValueError:
                    logger.error(f"==liuq debug== ❌ offset/x值无法转换为浮点数: {updated_xml_x}")
                    return False
        
        # 检查DetectMapFlag的数据类型
        range_elem = first_node.find('range')
        if range_elem is not None:
            detect_flag_elem = range_elem.find('DetectMapFlag')
            if detect_flag_elem is not None:
                updated_detect_flag = detect_flag_elem.text
                logger.info(f"==liuq debug== 更新后DetectMapFlag: {updated_detect_flag}")
                
                # 验证DetectMapFlag是否为int类型（0或1）
                if updated_detect_flag in ['0', '1']:
                    logger.info(f"==liuq debug== ✅ DetectMapFlag保持int类型")
                elif updated_detect_flag in ['true', 'false']:
                    logger.error(f"==liuq debug== ❌ DetectMapFlag被错误转换为boolean字符串！")
                    logger.error(f"  实际值: {updated_detect_flag}")
                    logger.error(f"  应该是: 0 或 1")
                    return False
                else:
                    logger.warning(f"==liuq debug== ⚠️ DetectMapFlag值异常: {updated_detect_flag}")
        
        # 检查第二组数据是否保持完整
        second_node = offset_map01_nodes[1]
        alias_elem = second_node.find('AliasName')
        if alias_elem is not None:
            updated_alias = alias_elem.text
            logger.info(f"==liuq debug== 更新后AliasName: {updated_alias}")
            
            if updated_alias == "1_BlueSky_Bright":
                logger.info(f"==liuq debug== ✅ AliasName保持正确")
            else:
                logger.error(f"==liuq debug== ❌ AliasName被意外修改！")
                return False
    
    # 6. 重新加载验证数据一致性
    logger.info(f"==liuq debug== === 步骤6: 重新加载验证数据一致性 ===")
    
    try:
        new_config = parser.parse_xml(work_xml)
        new_target_point = None
        
        for mp in new_config.map_points:
            if mp.alias_name == "1_BlueSky_Bright":
                new_target_point = mp
                break
        
        if new_target_point:
            logger.info(f"==liuq debug== 重新加载后的数据:")
            logger.info(f"  - offset_x: {new_target_point.offset_x}")
            logger.info(f"  - detect_flag: {new_target_point.detect_flag} (类型: {type(new_target_point.detect_flag)})")
            
            if abs(new_target_point.offset_x - new_offset_x) < 0.001:
                logger.info(f"==liuq debug== ✅ 数据一致性验证通过")
                return True
            else:
                logger.error(f"==liuq debug== ❌ 数据一致性验证失败")
                return False
        else:
            logger.error(f"==liuq debug== ❌ 重新加载后未找到目标Map点")
            return False
            
    except Exception as e:
        logger.error(f"==liuq debug== ❌ 重新加载失败: {e}")
        return False

if __name__ == "__main__":
    logger.info(f"==liuq debug== 🚀 开始深入调试XML写入问题")
    
    success = debug_xml_writing_issue()
    
    if success:
        logger.info(f"==liuq debug== ✅ 调试完成，XML写入功能正常")
    else:
        logger.error(f"==liuq debug== ❌ 发现XML写入问题，需要修复")
