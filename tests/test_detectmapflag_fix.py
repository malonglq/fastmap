#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试DetectMapFlag修复
验证DetectMapFlag字段保持INTEGER类型（0或1）
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

def test_detectmapflag_fix():
    """测试DetectMapFlag修复"""
    
    # 使用指定的测试文件
    test_xml = Path("e:/code/3__My/22_tool_fastmapv2/tests/test_data/awb_scenario.xml")
    
    if not test_xml.exists():
        logger.error(f"==liuq debug== ❌ 指定的测试文件不存在: {test_xml}")
        return False
    
    # 创建工作副本
    work_xml = test_xml.parent / "detectmapflag_fix_test.xml"
    shutil.copy2(test_xml, work_xml)
    
    logger.info(f"==liuq debug== 🔍 测试DetectMapFlag修复")
    logger.info(f"==liuq debug== 使用测试文件: {work_xml}")
    
    # 1. 解析XML
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
    logger.info(f"==liuq debug== 原始detect_flag: {target_map_point.detect_flag} (类型: {type(target_map_point.detect_flag)})")

    # 2. 检查XML中的原始DetectMapFlag值
    tree = ET.parse(work_xml)
    root = tree.getroot()

    offset_map01_nodes = root.findall('.//offset_map01')
    if len(offset_map01_nodes) >= 1:
        first_node = offset_map01_nodes[0]
        range_elem = first_node.find('range')
        if range_elem is not None:
            detect_flag_elem = range_elem.find('DetectMapFlag')
            if detect_flag_elem is not None:
                original_detect_flag = detect_flag_elem.text
                logger.info(f"==liuq debug== XML中原始DetectMapFlag: {original_detect_flag}")

    # 3. 修改detect_flag（模拟用户在GUI中的操作）
    original_flag = target_map_point.detect_flag
    new_flag = not original_flag  # 切换状态
    target_map_point.detect_flag = new_flag

    logger.info(f"==liuq debug== 修改detect_flag: {original_flag} -> {new_flag}")
    
    # 4. 保存XML
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
    
    # 5. 验证XML中的DetectMapFlag值
    tree = ET.parse(work_xml)
    root = tree.getroot()
    
    offset_map01_nodes = root.findall('.//offset_map01')
    if len(offset_map01_nodes) >= 1:
        first_node = offset_map01_nodes[0]
        range_elem = first_node.find('range')
        if range_elem is not None:
            detect_flag_elem = range_elem.find('DetectMapFlag')
            if detect_flag_elem is not None:
                updated_detect_flag = detect_flag_elem.text
                logger.info(f"==liuq debug== 更新后XML中DetectMapFlag: {updated_detect_flag}")
                
                # 验证值是否为0或1
                expected_value = "1" if new_flag else "0"
                if updated_detect_flag == expected_value:
                    logger.info(f"==liuq debug== ✅ DetectMapFlag正确更新为INTEGER类型: {updated_detect_flag}")
                elif updated_detect_flag in ['true', 'false']:
                    logger.error(f"==liuq debug== ❌ DetectMapFlag仍然是BOOLEAN字符串: {updated_detect_flag}")
                    return False
                else:
                    logger.error(f"==liuq debug== ❌ DetectMapFlag值异常: {updated_detect_flag}")
                    return False
            else:
                logger.error(f"==liuq debug== ❌ 未找到DetectMapFlag元素")
                return False
        else:
            logger.error(f"==liuq debug== ❌ 未找到range元素")
            return False
    else:
        logger.error(f"==liuq debug== ❌ 未找到offset_map01节点")
        return False
    
    # 6. 重新加载验证数据一致性
    try:
        new_config = parser.parse_xml(work_xml)
        new_target_point = None
        
        for mp in new_config.map_points:
            if mp.alias_name == "1_BlueSky_Bright":
                new_target_point = mp
                break
        
        if new_target_point:
            logger.info(f"==liuq debug== 重新加载后detect_flag: {new_target_point.detect_flag}")

            if new_target_point.detect_flag == new_flag:
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

def test_multiple_detectmapflag_changes():
    """测试多个Map点的DetectMapFlag修改"""
    
    # 使用指定的测试文件
    test_xml = Path("e:/code/3__My/22_tool_fastmapv2/tests/test_data/awb_scenario.xml")
    work_xml = test_xml.parent / "multiple_detectmapflag_test.xml"
    shutil.copy2(test_xml, work_xml)
    
    logger.info(f"==liuq debug== 🔍 测试多个Map点的DetectMapFlag修改")
    
    # 解析XML
    parser = XMLParserService()
    config = parser.parse_xml(work_xml)
    
    # 修改前3个非base_boundary的Map点的DetectMapFlag
    test_aliases = ["1_BlueSky_Bright", "2_BlueSky_Dim", "3_BlueSky_Landiao"]
    modified_points = []
    
    for alias_name in test_aliases:
        for mp in config.map_points:
            if mp.alias_name == alias_name:
                original_flag = mp.detect_flag
                new_flag = not original_flag  # 切换状态
                mp.detect_flag = new_flag
                modified_points.append((alias_name, original_flag, new_flag))
                logger.info(f"==liuq debug== 修改 {alias_name} DetectMapFlag: {original_flag} -> {new_flag}")
                break
    
    # 保存XML
    writer = XMLWriterService()
    success = writer.write_xml(config, work_xml, backup=True)
    
    if not success:
        logger.error(f"==liuq debug== ❌ 多点修改保存失败")
        return False
    
    # 验证每个修改
    tree = ET.parse(work_xml)
    root = tree.getroot()
    
    for i, (alias_name, original_flag, new_flag) in enumerate(modified_points):
        map_index = i + 1  # offset_map01, offset_map02, offset_map03
        element_name = f"offset_map{map_index:02d}"
        
        offset_map_nodes = root.findall(f'.//{element_name}')
        if len(offset_map_nodes) >= 1:
            # 检查第一组数据的DetectMapFlag
            first_node = offset_map_nodes[0]
            range_elem = first_node.find('range')
            if range_elem is not None:
                detect_flag_elem = range_elem.find('DetectMapFlag')
                if detect_flag_elem is not None:
                    xml_value = detect_flag_elem.text
                    expected_value = "1" if new_flag else "0"
                    
                    if xml_value == expected_value:
                        logger.info(f"==liuq debug== ✅ {element_name} ({alias_name}) DetectMapFlag更新正确: {xml_value}")
                    else:
                        logger.error(f"==liuq debug== ❌ {element_name} ({alias_name}) DetectMapFlag更新错误: 期望{expected_value}, 实际{xml_value}")
                        return False
    
    logger.info(f"==liuq debug== ✅ 多个Map点DetectMapFlag修改测试通过")
    return True

if __name__ == "__main__":
    logger.info(f"==liuq debug== 🚀 开始DetectMapFlag修复测试")
    
    # 测试1：单个DetectMapFlag修改
    single_test = test_detectmapflag_fix()
    
    # 测试2：多个DetectMapFlag修改
    multi_test = test_multiple_detectmapflag_changes()
    
    if single_test and multi_test:
        logger.info(f"==liuq debug== 🎉 所有DetectMapFlag测试通过！")
        logger.info(f"==liuq debug== ")
        logger.info(f"==liuq debug== 🎯 修复总结：")
        logger.info(f"==liuq debug== 1. ✅ 修复了字段注册系统中DetectMapFlag的类型定义")
        logger.info(f"==liuq debug== 2. ✅ DetectMapFlag现在正确使用INTEGER类型（0或1）")
        logger.info(f"==liuq debug== 3. ✅ 修复了XML路径映射（.//DetectMapFlag）")
        logger.info(f"==liuq debug== 4. ✅ 确保了数据类型与XML schema的一致性")
        logger.info(f"==liuq debug== 5. ✅ 验证了GUI修改能正确写入XML文件")
    else:
        logger.error(f"==liuq debug== ❌ 部分测试失败")
        logger.error(f"  - 单个DetectMapFlag测试: {'✓' if single_test else '✗'}")
        logger.error(f"  - 多个DetectMapFlag测试: {'✓' if multi_test else '✗'}")
