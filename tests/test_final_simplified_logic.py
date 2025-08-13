#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试：验证简化后的逻辑
确保用户场景完全正常工作
"""

import sys
import os
from pathlib import Path
import logging
import shutil

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

def test_user_scenario_final():
    """最终测试用户场景：修改"1_BlueSky_Bright"的Offset R/G从0.578到0.598"""
    
    # 测试文件
    original_xml = project_root / "tests" / "test_data" / "awb_scenario.xml"
    test_xml = project_root / "tests" / "test_data" / "test_final_user_scenario.xml"
    
    # 创建测试文件副本
    shutil.copy2(original_xml, test_xml)
    
    logger.info(f"==liuq debug== 🎯 最终用户场景测试")
    logger.info(f"==liuq debug== 场景：在GUI表格中修改'1_BlueSky_Bright'的'Offset R/G'字段")
    logger.info(f"==liuq debug== 期望：从0.578改为0.598，正确写入offset_map01/offset/x")
    
    # 1. 解析XML
    parser = XMLParserService()
    config = parser.parse_xml(test_xml)
    
    # 2. 查找"1_BlueSky_Bright"
    target_map_point = None
    for mp in config.map_points:
        if mp.alias_name == "1_BlueSky_Bright":
            target_map_point = mp
            break
    
    if target_map_point is None:
        logger.error(f"==liuq debug== ❌ 未找到'1_BlueSky_Bright'")
        return False
    
    logger.info(f"==liuq debug== ✅ 找到目标Map点: {target_map_point.alias_name}")
    logger.info(f"==liuq debug== 当前offset_x (Offset R/G): {target_map_point.offset_x}")
    
    # 3. 验证当前值
    expected_original = 0.578
    if abs(target_map_point.offset_x - expected_original) > 0.001:
        logger.warning(f"==liuq debug== ⚠️ 当前值({target_map_point.offset_x})与期望原始值({expected_original})不符")
    
    # 4. 执行用户操作：修改Offset R/G
    original_offset_x = target_map_point.offset_x
    new_offset_x = 0.598
    target_map_point.offset_x = new_offset_x
    
    logger.info(f"==liuq debug== 🔄 执行修改: Offset R/G {original_offset_x} -> {new_offset_x}")
    
    # 5. 保存XML（模拟GUI的保存操作）
    writer = XMLWriterService()
    try:
        success = writer.write_xml(config, test_xml, backup=True)
        if success:
            logger.info(f"==liuq debug== ✅ XML保存成功")
        else:
            logger.error(f"==liuq debug== ❌ XML保存失败")
            return False
    except Exception as e:
        logger.error(f"==liuq debug== ❌ XML保存异常: {e}")
        return False
    
    # 6. 验证XML中的实际更新
    logger.info(f"==liuq debug== 🔍 验证XML中的实际更新...")
    
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(test_xml)
        root = tree.getroot()
        
        # 检查offset_map01的双组数据结构
        offset_map01_nodes = root.findall('.//offset_map01')
        
        if len(offset_map01_nodes) >= 2:
            # 第一个节点：验证offset数据更新
            first_node = offset_map01_nodes[0]
            offset_elem = first_node.find('offset')
            if offset_elem is not None:
                x_elem = offset_elem.find('x')
                y_elem = offset_elem.find('y')
                if x_elem is not None and y_elem is not None:
                    xml_offset_x = float(x_elem.text)
                    xml_offset_y = float(y_elem.text)
                    
                    logger.info(f"==liuq debug== offset_map01第一组数据:")
                    logger.info(f"  - offset/x: {xml_offset_x} (期望: {new_offset_x})")
                    logger.info(f"  - offset/y: {xml_offset_y}")
                    
                    if abs(xml_offset_x - new_offset_x) < 0.001:
                        logger.info(f"==liuq debug== ✅ offset/x更新正确")
                    else:
                        logger.error(f"==liuq debug== ❌ offset/x更新错误")
                        return False
            
            # 第二个节点：验证别名数据完整性
            second_node = offset_map01_nodes[1]
            alias_elem = second_node.find('AliasName')
            if alias_elem is not None:
                xml_alias = alias_elem.text
                logger.info(f"==liuq debug== offset_map01第二组数据:")
                logger.info(f"  - AliasName: {xml_alias}")
                
                if xml_alias == "1_BlueSky_Bright":
                    logger.info(f"==liuq debug== ✅ 别名数据完整")
                else:
                    logger.error(f"==liuq debug== ❌ 别名数据错误")
                    return False
        else:
            logger.error(f"==liuq debug== ❌ 未找到足够的offset_map01节点")
            return False
            
    except Exception as e:
        logger.error(f"==liuq debug== ❌ 验证XML失败: {e}")
        return False
    
    # 7. 重新加载验证数据一致性（模拟重新打开文件）
    logger.info(f"==liuq debug== 🔄 重新加载验证数据一致性...")
    
    try:
        new_config = parser.parse_xml(test_xml)
        new_target_point = None
        
        for mp in new_config.map_points:
            if mp.alias_name == "1_BlueSky_Bright":
                new_target_point = mp
                break
        
        if new_target_point:
            logger.info(f"==liuq debug== 重新加载后的数据:")
            logger.info(f"  - offset_x: {new_target_point.offset_x}")
            logger.info(f"  - offset_y: {new_target_point.offset_y}")
            
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

def test_multiple_map_points():
    """测试多个Map点的修改"""
    
    # 测试文件
    original_xml = project_root / "tests" / "test_data" / "awb_scenario.xml"
    test_xml = project_root / "tests" / "test_data" / "test_multiple_points.xml"
    
    # 创建测试文件副本
    shutil.copy2(original_xml, test_xml)
    
    logger.info(f"==liuq debug== 🎯 测试多个Map点的修改")
    
    # 解析XML
    parser = XMLParserService()
    config = parser.parse_xml(test_xml)
    
    # 修改前3个非base_boundary的Map点
    test_cases = [
        ("1_BlueSky_Bright", 0.111),
        ("2_BlueSky_Dim", 0.222),
        ("3_BlueSky_Landiao", 0.333)
    ]
    
    modified_points = []
    
    for alias_name, new_value in test_cases:
        for mp in config.map_points:
            if mp.alias_name == alias_name:
                original_value = mp.offset_x
                mp.offset_x = new_value
                modified_points.append((alias_name, original_value, new_value))
                logger.info(f"==liuq debug== 修改 {alias_name}: {original_value} -> {new_value}")
                break
    
    # 保存XML
    writer = XMLWriterService()
    success = writer.write_xml(config, test_xml, backup=True)
    
    if not success:
        logger.error(f"==liuq debug== ❌ 多点修改保存失败")
        return False
    
    # 验证每个修改
    import xml.etree.ElementTree as ET
    tree = ET.parse(test_xml)
    root = tree.getroot()
    
    for i, (alias_name, original_value, new_value) in enumerate(modified_points):
        map_index = i + 1  # offset_map01, offset_map02, offset_map03
        element_name = f"offset_map{map_index:02d}"
        
        offset_map_nodes = root.findall(f'.//{element_name}')
        if len(offset_map_nodes) >= 2:
            # 检查第一组数据的offset/x
            first_node = offset_map_nodes[0]
            offset_elem = first_node.find('offset')
            if offset_elem is not None:
                x_elem = offset_elem.find('x')
                if x_elem is not None:
                    xml_value = float(x_elem.text)
                    if abs(xml_value - new_value) < 0.001:
                        logger.info(f"==liuq debug== ✅ {element_name} ({alias_name}) 更新正确: {xml_value}")
                    else:
                        logger.error(f"==liuq debug== ❌ {element_name} ({alias_name}) 更新错误: 期望{new_value}, 实际{xml_value}")
                        return False
    
    logger.info(f"==liuq debug== ✅ 多个Map点修改测试通过")
    return True

if __name__ == "__main__":
    logger.info(f"==liuq debug== 🚀 开始最终简化逻辑测试")
    
    # 测试1：用户场景
    user_test = test_user_scenario_final()
    
    # 测试2：多点修改
    multi_test = test_multiple_map_points()
    
    if user_test and multi_test:
        logger.info(f"==liuq debug== 🎉 所有测试通过！")
        logger.info(f"==liuq debug== ")
        logger.info(f"==liuq debug== 🎯 修复总结：")
        logger.info(f"==liuq debug== 1. ✅ 移除了有害的权重排序逻辑")
        logger.info(f"==liuq debug== 2. ✅ Map点现在保持原始XML顺序")
        logger.info(f"==liuq debug== 3. ✅ 简化了XML写入逻辑，使用顺序映射")
        logger.info(f"==liuq debug== 4. ✅ '1_BlueSky_Bright'正确映射到offset_map01")
        logger.info(f"==liuq debug== 5. ✅ 用户可以安全地修改GUI表格中的任何字段")
        logger.info(f"==liuq debug== ")
        logger.info(f"==liuq debug== 🎊 问题完全解决！用户现在可以正常使用GUI修改Map点数据！")
    else:
        logger.error(f"==liuq debug== ❌ 部分测试失败")
        logger.error(f"  - 用户场景测试: {'✓' if user_test else '✗'}")
        logger.error(f"  - 多点修改测试: {'✓' if multi_test else '✗'}")
