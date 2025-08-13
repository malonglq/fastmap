#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试移除权重排序后的效果
验证Map点保持原始XML顺序
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

def test_no_weight_sorting():
    """测试移除权重排序后Map点保持原始顺序"""
    
    xml_file = project_root / "tests" / "test_data" / "awb_scenario.xml"
    
    logger.info(f"==liuq debug== 测试移除权重排序后的Map点顺序")
    
    # 解析XML
    parser = XMLParserService()
    config = parser.parse_xml(xml_file)
    
    logger.info(f"==liuq debug== 解析后的Map点顺序（应该保持XML原始顺序）:")
    
    # 检查前10个Map点
    for i, mp in enumerate(config.map_points[:10]):
        logger.info(f"  索引{i}: {mp.alias_name}, weight={mp.weight}")
    
    # 查找"1_BlueSky_Bright"的位置
    bluesky_index = -1
    for i, mp in enumerate(config.map_points):
        if mp.alias_name == "1_BlueSky_Bright":
            bluesky_index = i
            break
    
    if bluesky_index >= 0:
        logger.info(f"==liuq debug== '1_BlueSky_Bright'在解析后的索引: {bluesky_index}")
        
        # 计算在非base_boundary点中的位置
        non_base_points = [p for p in config.map_points if p.alias_name != "base_boundary0"]
        offset_index = -1
        for i, p in enumerate(non_base_points):
            if p.alias_name == "1_BlueSky_Bright":
                offset_index = i
                break
        
        if offset_index >= 0:
            expected_map_index = offset_index + 1  # offset_map从01开始
            logger.info(f"==liuq debug== '1_BlueSky_Bright'在非base_boundary点中的索引: {offset_index}")
            logger.info(f"==liuq debug== 应该映射到: offset_map{expected_map_index:02d}")
            
            # 如果是第一个非base_boundary点，应该映射到offset_map01
            if offset_index == 0:
                logger.info(f"==liuq debug== ✓ '1_BlueSky_Bright'现在是第一个非base_boundary点，正确映射到offset_map01")
                return True
            else:
                logger.warning(f"==liuq debug== '1_BlueSky_Bright'不是第一个非base_boundary点，映射到offset_map{expected_map_index:02d}")
                return False
    
    logger.error(f"==liuq debug== 未找到'1_BlueSky_Bright'")
    return False

def test_simplified_xml_writing():
    """测试简化后的XML写入逻辑"""
    
    # 测试文件
    original_xml = project_root / "tests" / "test_data" / "awb_scenario.xml"
    test_xml = project_root / "tests" / "test_data" / "test_no_weight_sorting.xml"
    
    # 创建测试文件副本
    shutil.copy2(original_xml, test_xml)
    
    logger.info(f"==liuq debug== 测试简化后的XML写入逻辑")
    
    # 解析XML
    parser = XMLParserService()
    config = parser.parse_xml(test_xml)
    
    # 查找"1_BlueSky_Bright"
    target_map_point = None
    for mp in config.map_points:
        if mp.alias_name == "1_BlueSky_Bright":
            target_map_point = mp
            break
    
    if target_map_point is None:
        logger.error(f"==liuq debug== 未找到'1_BlueSky_Bright'")
        return False
    
    # 修改offset_x值
    original_offset_x = target_map_point.offset_x
    new_offset_x = 0.777  # 使用一个特殊值
    target_map_point.offset_x = new_offset_x
    
    logger.info(f"==liuq debug== 修改'1_BlueSky_Bright'的offset_x: {original_offset_x} -> {new_offset_x}")
    
    # 写入XML（现在应该使用基于别名的映射）
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
    
    # 验证XML中的实际更新
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(test_xml)
        root = tree.getroot()
        
        # 检查offset_map01的第一个节点
        offset_map01_nodes = root.findall('.//offset_map01')
        
        if len(offset_map01_nodes) >= 2:
            # 第一个节点：包含offset数据
            first_node = offset_map01_nodes[0]
            offset_elem = first_node.find('offset')
            if offset_elem is not None:
                x_elem = offset_elem.find('x')
                if x_elem is not None:
                    xml_offset_x = float(x_elem.text)
                    logger.info(f"==liuq debug== offset_map01第一个节点的offset/x: {xml_offset_x}")
                    
                    if abs(xml_offset_x - new_offset_x) < 0.001:
                        logger.info(f"==liuq debug== ✓ offset_map01正确更新")
                        
                        # 验证第二个节点的别名
                        second_node = offset_map01_nodes[1]
                        alias_elem = second_node.find('AliasName')
                        if alias_elem is not None and alias_elem.text == "1_BlueSky_Bright":
                            logger.info(f"==liuq debug== ✓ offset_map01的别名正确")
                            return True
                        else:
                            logger.error(f"==liuq debug== ✗ offset_map01的别名错误")
                            return False
                    else:
                        logger.error(f"==liuq debug== ✗ offset_map01更新错误，期望{new_offset_x}，实际{xml_offset_x}")
                        return False
        
        logger.error(f"==liuq debug== ✗ 未找到足够的offset_map01节点")
        return False
        
    except Exception as e:
        logger.error(f"==liuq debug== 验证XML失败: {e}")
        return False

def test_original_xml_order():
    """测试Map点是否保持原始XML顺序"""
    
    xml_file = project_root / "tests" / "test_data" / "awb_scenario.xml"
    
    logger.info(f"==liuq debug== 验证Map点是否保持原始XML顺序")
    
    # 解析XML
    parser = XMLParserService()
    config = parser.parse_xml(xml_file)
    
    # 检查前几个非base_boundary的Map点是否按XML顺序排列
    non_base_points = [mp for mp in config.map_points if mp.alias_name != "base_boundary0"]
    
    logger.info(f"==liuq debug== 前5个非base_boundary Map点:")
    for i, mp in enumerate(non_base_points[:5]):
        expected_map_index = i + 1
        logger.info(f"  索引{i}: {mp.alias_name} -> 应该对应offset_map{expected_map_index:02d}")
    
    # 验证"1_BlueSky_Bright"是否是第一个
    if non_base_points and non_base_points[0].alias_name == "1_BlueSky_Bright":
        logger.info(f"==liuq debug== ✓ '1_BlueSky_Bright'是第一个非base_boundary点，对应offset_map01")
        return True
    else:
        logger.warning(f"==liuq debug== '1_BlueSky_Bright'不是第一个非base_boundary点")
        if non_base_points:
            logger.info(f"==liuq debug== 第一个非base_boundary点是: {non_base_points[0].alias_name}")
        return False

if __name__ == "__main__":
    logger.info(f"==liuq debug== 开始测试移除权重排序的效果")
    
    # 测试1：验证Map点顺序
    order_test = test_original_xml_order()
    
    # 测试2：验证不再有权重排序
    no_sorting_test = test_no_weight_sorting()
    
    # 测试3：验证XML写入逻辑
    writing_test = test_simplified_xml_writing()
    
    if order_test and no_sorting_test and writing_test:
        logger.info(f"==liuq debug== ✅ 所有测试通过！")
        logger.info(f"==liuq debug== 权重排序已成功移除，Map点保持原始XML顺序")
        logger.info(f"==liuq debug== '1_BlueSky_Bright'现在正确映射到offset_map01")
    else:
        logger.error(f"==liuq debug== ❌ 部分测试失败")
        logger.error(f"  - 原始XML顺序测试: {'✓' if order_test else '✗'}")
        logger.error(f"  - 无权重排序测试: {'✓' if no_sorting_test else '✗'}")
        logger.error(f"  - XML写入测试: {'✓' if writing_test else '✗'}")
