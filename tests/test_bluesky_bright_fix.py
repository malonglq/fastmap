#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试"1_BlueSky_Bright"的Offset R/G修改
验证用户场景：从0.578改为0.598
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
from core.models.map_data import MapConfiguration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_bluesky_bright_scenario():
    """测试用户场景：修改"1_BlueSky_Bright"的Offset R/G从0.578到0.598"""
    
    # 使用原始的awb_scenario.xml文件
    original_xml = project_root / "tests" / "test_data" / "awb_scenario.xml"
    test_xml = project_root / "tests" / "test_data" / "test_bluesky_bright.xml"
    
    # 创建测试文件副本
    shutil.copy2(original_xml, test_xml)
    
    logger.info(f"==liuq debug== 开始测试用户场景：修改1_BlueSky_Bright的Offset R/G")
    logger.info(f"==liuq debug== 测试文件: {test_xml}")
    
    # 1. 解析XML文件
    parser = XMLParserService()
    try:
        config = parser.parse_xml(test_xml)
        logger.info(f"==liuq debug== 成功解析XML，共 {len(config.map_points)} 个Map点")
    except Exception as e:
        logger.error(f"==liuq debug== XML解析失败: {e}")
        return False
    
    # 2. 查找"1_BlueSky_Bright"
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
        return False
    
    logger.info(f"==liuq debug== 找到目标Map点:")
    logger.info(f"  - 索引: {target_index}")
    logger.info(f"  - 别名: {target_map_point.alias_name}")
    logger.info(f"  - 当前offset_x (Offset R/G): {target_map_point.offset_x}")
    logger.info(f"  - 当前offset_y (Offset B/G): {target_map_point.offset_y}")
    
    # 3. 验证当前值是否符合预期
    expected_original = 0.578
    if abs(target_map_point.offset_x - expected_original) > 0.001:
        logger.warning(f"==liuq debug== 注意：当前offset_x值({target_map_point.offset_x})与预期原始值({expected_original})不符")
    
    # 4. 执行用户场景：修改Offset R/G从当前值到0.598
    original_offset_x = target_map_point.offset_x
    new_offset_x = 0.598
    target_map_point.offset_x = new_offset_x
    
    logger.info(f"==liuq debug== 执行修改:")
    logger.info(f"  - Offset R/G: {original_offset_x} -> {new_offset_x}")
    
    # 5. 计算正确的映射关系
    non_base_points = [mp for mp in config.map_points if mp.alias_name != "base_boundary0"]
    correct_offset_index = -1
    for i, mp in enumerate(non_base_points):
        if mp.alias_name == target_alias:
            correct_offset_index = i
            break
    
    if correct_offset_index >= 0:
        correct_map_index = correct_offset_index + 1  # offset_map从01开始
        logger.info(f"==liuq debug== 映射关系:")
        logger.info(f"  - 在非base_boundary点中的索引: {correct_offset_index}")
        logger.info(f"  - 应该对应的XML节点: offset_map{correct_map_index:02d}")
    
    # 6. 写入XML
    writer = XMLWriterService()
    try:
        success = writer.write_xml(config, test_xml, backup=True)
        if success:
            logger.info(f"==liuq debug== XML写入成功")
        else:
            logger.error(f"==liuq debug== XML写入失败")
            return False
    except Exception as e:
        logger.error(f"==liuq debug== XML写入异常: {e}")
        return False
    
    # 7. 验证写入结果
    logger.info(f"==liuq debug== 验证写入结果:")
    
    # 重新解析文件
    try:
        new_config = parser.parse_xml(test_xml)
        new_target_point = None
        
        for mp in new_config.map_points:
            if mp.alias_name == target_alias:
                new_target_point = mp
                break
        
        if new_target_point:
            logger.info(f"  - 重新解析后的offset_x: {new_target_point.offset_x}")
            logger.info(f"  - 重新解析后的offset_y: {new_target_point.offset_y}")
            
            if abs(new_target_point.offset_x - new_offset_x) < 0.001:
                logger.info(f"  - ✓ Offset R/G值更新正确")
            else:
                logger.error(f"  - ✗ Offset R/G值更新错误，期望{new_offset_x}，实际{new_target_point.offset_x}")
                return False
        else:
            logger.error(f"  - ✗ 重新解析后未找到目标Map点")
            return False
            
    except Exception as e:
        logger.error(f"==liuq debug== 验证失败: {e}")
        return False
    
    # 8. 检查XML中的实际节点
    logger.info(f"==liuq debug== 检查XML中的实际节点:")
    
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(test_xml)
        root = tree.getroot()
        
        # 检查正确的offset_map节点
        if correct_offset_index >= 0:
            correct_map_index = correct_offset_index + 1
            element_name = f"offset_map{correct_map_index:02d}"
            offset_map_nodes = root.findall(f'.//{element_name}')
            
            if len(offset_map_nodes) >= 1:
                first_node = offset_map_nodes[0]
                offset_elem = first_node.find('offset')
                if offset_elem is not None:
                    x_elem = offset_elem.find('x')
                    y_elem = offset_elem.find('y')
                    if x_elem is not None and y_elem is not None:
                        xml_offset_x = float(x_elem.text)
                        xml_offset_y = float(y_elem.text)
                        logger.info(f"  - {element_name}第一个节点的offset/x: {xml_offset_x}")
                        logger.info(f"  - {element_name}第一个节点的offset/y: {xml_offset_y}")
                        
                        if abs(xml_offset_x - new_offset_x) < 0.001:
                            logger.info(f"  - ✓ XML节点的offset/x更新正确")
                            
                            # 检查第二个节点的别名
                            if len(offset_map_nodes) >= 2:
                                second_node = offset_map_nodes[1]
                                alias_elem = second_node.find('AliasName')
                                if alias_elem is not None:
                                    xml_alias = alias_elem.text
                                    logger.info(f"  - {element_name}第二个节点的AliasName: {xml_alias}")
                                    
                                    if xml_alias == target_alias:
                                        logger.info(f"  - ✓ XML节点的别名正确")
                                        return True
                                    else:
                                        logger.error(f"  - ✗ XML节点的别名错误，期望{target_alias}，实际{xml_alias}")
                                        return False
                            
                        else:
                            logger.error(f"  - ✗ XML节点的offset/x更新错误，期望{new_offset_x}，实际{xml_offset_x}")
                            return False
                            
    except Exception as e:
        logger.error(f"==liuq debug== 检查XML节点失败: {e}")
        return False
    
    return False

if __name__ == "__main__":
    success = test_bluesky_bright_scenario()
    if success:
        logger.info("==liuq debug== ✓ 用户场景测试通过！1_BlueSky_Bright的Offset R/G修改成功！")
        logger.info("==liuq debug== 修复总结：")
        logger.info("  1. 修复了XMLWriterService中的索引计算逻辑")
        logger.info("  2. 确保了Map点到XML节点的正确映射")
        logger.info("  3. 验证了双组数据结构的正确更新")
        logger.info("  4. 保证了别名字段不会被意外修改")
    else:
        logger.error("==liuq debug== ✗ 用户场景测试失败，需要进一步调试")
