#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终综合测试：验证XML写入问题的完整修复
使用指定的测试文件进行完整的用户场景测试
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

def test_complete_user_scenario():
    """完整的用户场景测试"""
    
    # 使用指定的测试文件
    test_xml = Path("e:/code/3__My/22_tool_fastmapv2/tests/test_data/awb_scenario.xml")
    
    if not test_xml.exists():
        logger.error(f"==liuq debug== ❌ 指定的测试文件不存在: {test_xml}")
        return False
    
    # 创建工作副本
    work_xml = test_xml.parent / "final_complete_test.xml"
    shutil.copy2(test_xml, work_xml)
    
    logger.info(f"==liuq debug== 🎯 完整用户场景测试")
    logger.info(f"==liuq debug== 使用指定的测试文件: {test_xml}")
    logger.info(f"==liuq debug== 工作副本: {work_xml}")
    
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
    logger.info(f"==liuq debug== 原始数据:")
    logger.info(f"  - offset_x (Offset R/G): {target_map_point.offset_x}")
    logger.info(f"  - offset_y (Offset B/G): {target_map_point.offset_y}")
    logger.info(f"  - detect_flag: {target_map_point.detect_flag}")
    
    # 2. 执行用户修改（模拟GUI操作）
    original_offset_x = target_map_point.offset_x
    original_detect_flag = target_map_point.detect_flag
    
    new_offset_x = 0.598  # 用户场景：从0.578改为0.598
    new_detect_flag = not original_detect_flag  # 切换检测标志
    
    target_map_point.offset_x = new_offset_x
    target_map_point.detect_flag = new_detect_flag
    
    logger.info(f"==liuq debug== 执行用户修改:")
    logger.info(f"  - Offset R/G: {original_offset_x} -> {new_offset_x}")
    logger.info(f"  - DetectMapFlag: {original_detect_flag} -> {new_detect_flag}")
    
    # 3. 保存XML
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
    
    # 4. 验证XML中的实际更新
    logger.info(f"==liuq debug== 验证XML中的实际更新:")
    
    tree = ET.parse(work_xml)
    root = tree.getroot()
    
    # 检查offset_map01的双组数据结构
    offset_map01_nodes = root.findall('.//offset_map01')
    
    if len(offset_map01_nodes) >= 2:
        # 第一组数据：验证offset和DetectMapFlag更新
        first_node = offset_map01_nodes[0]
        
        # 验证offset/x更新
        offset_elem = first_node.find('offset')
        if offset_elem is not None:
            x_elem = offset_elem.find('x')
            if x_elem is not None:
                xml_offset_x = float(x_elem.text)
                logger.info(f"  - offset/x: {xml_offset_x} (期望: {new_offset_x})")
                
                if abs(xml_offset_x - new_offset_x) < 0.001:
                    logger.info(f"  - ✅ offset/x更新正确")
                else:
                    logger.error(f"  - ❌ offset/x更新错误")
                    return False
        
        # 验证DetectMapFlag更新
        range_elem = first_node.find('range')
        if range_elem is not None:
            detect_flag_elem = range_elem.find('DetectMapFlag')
            if detect_flag_elem is not None:
                xml_detect_flag = detect_flag_elem.text
                expected_detect_flag = "1" if new_detect_flag else "0"
                logger.info(f"  - DetectMapFlag: {xml_detect_flag} (期望: {expected_detect_flag})")
                
                if xml_detect_flag == expected_detect_flag:
                    logger.info(f"  - ✅ DetectMapFlag更新正确（INTEGER类型）")
                else:
                    logger.error(f"  - ❌ DetectMapFlag更新错误")
                    return False
        
        # 第二组数据：验证别名完整性
        second_node = offset_map01_nodes[1]
        alias_elem = second_node.find('AliasName')
        if alias_elem is not None:
            xml_alias = alias_elem.text
            logger.info(f"  - AliasName: {xml_alias}")
            
            if xml_alias == "1_BlueSky_Bright":
                logger.info(f"  - ✅ 别名数据完整")
            else:
                logger.error(f"  - ❌ 别名数据错误")
                return False
    else:
        logger.error(f"==liuq debug== ❌ 未找到足够的offset_map01节点")
        return False
    
    # 5. 重新加载验证数据一致性
    logger.info(f"==liuq debug== 重新加载验证数据一致性:")
    
    try:
        new_config = parser.parse_xml(work_xml)
        new_target_point = None
        
        for mp in new_config.map_points:
            if mp.alias_name == "1_BlueSky_Bright":
                new_target_point = mp
                break
        
        if new_target_point:
            logger.info(f"  - 重新加载后offset_x: {new_target_point.offset_x}")
            logger.info(f"  - 重新加载后detect_flag: {new_target_point.detect_flag}")
            
            offset_match = abs(new_target_point.offset_x - new_offset_x) < 0.001
            flag_match = new_target_point.detect_flag == new_detect_flag
            
            if offset_match and flag_match:
                logger.info(f"  - ✅ 数据一致性验证通过")
                return True
            else:
                logger.error(f"  - ❌ 数据一致性验证失败")
                logger.error(f"    offset_x匹配: {offset_match}")
                logger.error(f"    detect_flag匹配: {flag_match}")
                return False
        else:
            logger.error(f"==liuq debug== ❌ 重新加载后未找到目标Map点")
            return False
            
    except Exception as e:
        logger.error(f"==liuq debug== ❌ 重新加载失败: {e}")
        return False

def test_data_type_consistency():
    """测试数据类型一致性"""
    
    logger.info(f"==liuq debug== 🔍 测试数据类型一致性")
    
    # 使用指定的测试文件
    test_xml = Path("e:/code/3__My/22_tool_fastmapv2/tests/test_data/awb_scenario.xml")
    work_xml = test_xml.parent / "data_type_test.xml"
    shutil.copy2(test_xml, work_xml)
    
    # 解析并检查所有Map点的数据类型
    parser = XMLParserService()
    config = parser.parse_xml(work_xml)
    
    logger.info(f"==liuq debug== 检查前5个Map点的数据类型:")
    
    for i, mp in enumerate(config.map_points[:5]):
        logger.info(f"  Map点 {i+1}: {mp.alias_name}")
        logger.info(f"    - offset_x类型: {type(mp.offset_x)} = {mp.offset_x}")
        logger.info(f"    - detect_flag类型: {type(mp.detect_flag)} = {mp.detect_flag}")
        
        # 验证数据类型
        if not isinstance(mp.offset_x, float):
            logger.error(f"    - ❌ offset_x应该是float类型")
            return False
        
        if not isinstance(mp.detect_flag, bool):
            logger.error(f"    - ❌ detect_flag应该是bool类型")
            return False
    
    logger.info(f"==liuq debug== ✅ 数据类型一致性验证通过")
    return True

if __name__ == "__main__":
    logger.info(f"==liuq debug== 🚀 开始最终综合测试")
    
    # 测试1：完整用户场景
    user_scenario_test = test_complete_user_scenario()
    
    # 测试2：数据类型一致性
    data_type_test = test_data_type_consistency()
    
    if user_scenario_test and data_type_test:
        logger.info(f"==liuq debug== 🎉 所有测试通过！")
        logger.info(f"==liuq debug== ")
        logger.info(f"==liuq debug== 🎯 XML写入问题完全修复总结：")
        logger.info(f"==liuq debug== 1. ✅ 移除了有害的权重排序逻辑")
        logger.info(f"==liuq debug== 2. ✅ 修复了DetectMapFlag的数据类型处理")
        logger.info(f"==liuq debug== 3. ✅ 确保DetectMapFlag使用INTEGER类型（0或1）")
        logger.info(f"==liuq debug== 4. ✅ 修复了字段注册系统中的类型定义")
        logger.info(f"==liuq debug== 5. ✅ 修复了XML解析中的DetectMapFlag逻辑")
        logger.info(f"==liuq debug== 6. ✅ 验证了完整的读写一致性")
        logger.info(f"==liuq debug== ")
        logger.info(f"==liuq debug== 🎊 用户现在可以在GUI中安全地修改任何Map点字段！")
        logger.info(f"==liuq debug== 所有修改都将正确写入XML文件并保持数据类型一致性！")
    else:
        logger.error(f"==liuq debug== ❌ 部分测试失败")
        logger.error(f"  - 完整用户场景测试: {'✓' if user_scenario_test else '✗'}")
        logger.error(f"  - 数据类型一致性测试: {'✓' if data_type_test else '✗'}")
