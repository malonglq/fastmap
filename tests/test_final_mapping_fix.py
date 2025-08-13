#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试：验证"1_BlueSky_Bright"到offset_map01的正确映射
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

def test_final_mapping_fix():
    """最终测试：验证修复后的映射逻辑"""
    
    # 测试文件
    original_xml = project_root / "tests" / "test_data" / "awb_scenario.xml"
    test_xml = project_root / "tests" / "test_data" / "test_final_fix.xml"
    
    # 创建测试文件副本
    shutil.copy2(original_xml, test_xml)
    
    logger.info(f"==liuq debug== 开始最终映射测试")
    logger.info(f"==liuq debug== 测试文件: {test_xml}")
    
    # 1. 解析XML
    parser = XMLParserService()
    config = parser.parse_xml(test_xml)
    
    # 2. 查找"1_BlueSky_Bright"
    target_alias = "1_BlueSky_Bright"
    target_map_point = None
    
    for mp in config.map_points:
        if mp.alias_name == target_alias:
            target_map_point = mp
            break
    
    if target_map_point is None:
        logger.error(f"==liuq debug== 未找到目标Map点: {target_alias}")
        return False
    
    logger.info(f"==liuq debug== 找到目标Map点:")
    logger.info(f"  - 别名: {target_map_point.alias_name}")
    logger.info(f"  - 修改前offset_x: {target_map_point.offset_x}")
    logger.info(f"  - 修改前offset_y: {target_map_point.offset_y}")
    
    # 3. 修改offset_x值（用户场景：0.578 -> 0.598）
    original_offset_x = target_map_point.offset_x
    new_offset_x = 0.598
    target_map_point.offset_x = new_offset_x
    
    logger.info(f"==liuq debug== 执行修改:")
    logger.info(f"  - Offset R/G: {original_offset_x} -> {new_offset_x}")
    
    # 4. 写入XML（使用修复后的逻辑）
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
    
    # 5. 验证XML中的实际更新
    logger.info(f"==liuq debug== 验证XML中的实际更新:")
    
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(test_xml)
        root = tree.getroot()
        
        # 检查offset_map01的第一个节点（应该包含更新后的offset/x）
        offset_map01_nodes = root.findall('.//offset_map01')
        
        if len(offset_map01_nodes) >= 2:
            # 第一个节点：包含offset数据
            first_node = offset_map01_nodes[0]
            offset_elem = first_node.find('offset')
            if offset_elem is not None:
                x_elem = offset_elem.find('x')
                if x_elem is not None:
                    xml_offset_x = float(x_elem.text)
                    logger.info(f"  - offset_map01第一个节点的offset/x: {xml_offset_x}")
                    
                    if abs(xml_offset_x - new_offset_x) < 0.001:
                        logger.info(f"  - ✓ offset/x更新正确")
                    else:
                        logger.error(f"  - ✗ offset/x更新错误，期望{new_offset_x}，实际{xml_offset_x}")
                        return False
            
            # 第二个节点：验证AliasName
            second_node = offset_map01_nodes[1]
            alias_elem = second_node.find('AliasName')
            if alias_elem is not None:
                xml_alias = alias_elem.text
                logger.info(f"  - offset_map01第二个节点的AliasName: {xml_alias}")
                
                if xml_alias == target_alias:
                    logger.info(f"  - ✓ AliasName正确")
                else:
                    logger.error(f"  - ✗ AliasName错误，期望{target_alias}，实际{xml_alias}")
                    return False
        else:
            logger.error(f"  - ✗ 未找到足够的offset_map01节点")
            return False
            
    except Exception as e:
        logger.error(f"==liuq debug== 验证XML失败: {e}")
        return False
    
    # 6. 重新解析验证数据一致性
    logger.info(f"==liuq debug== 重新解析验证数据一致性:")
    
    try:
        new_config = parser.parse_xml(test_xml)
        new_target_point = None
        
        for mp in new_config.map_points:
            if mp.alias_name == target_alias:
                new_target_point = mp
                break
        
        if new_target_point:
            logger.info(f"  - 重新解析后的offset_x: {new_target_point.offset_x}")
            
            if abs(new_target_point.offset_x - new_offset_x) < 0.001:
                logger.info(f"  - ✓ 数据一致性验证通过")
                return True
            else:
                logger.error(f"  - ✗ 数据一致性验证失败，期望{new_offset_x}，实际{new_target_point.offset_x}")
                return False
        else:
            logger.error(f"  - ✗ 重新解析后未找到目标Map点")
            return False
            
    except Exception as e:
        logger.error(f"==liuq debug== 重新解析失败: {e}")
        return False

if __name__ == "__main__":
    logger.info(f"==liuq debug== 开始最终映射修复测试")
    
    success = test_final_mapping_fix()
    
    if success:
        logger.info(f"==liuq debug== ✅ 最终测试通过！")
        logger.info(f"==liuq debug== 修复总结：")
        logger.info(f"  1. ✅ 识别了权重排序导致的映射错误问题")
        logger.info(f"  2. ✅ 实现了基于别名的XML节点映射机制")
        logger.info(f"  3. ✅ 确保'1_BlueSky_Bright'正确映射到offset_map01")
        logger.info(f"  4. ✅ 验证了Offset R/G修改的正确写入")
        logger.info(f"  5. ✅ 保证了数据一致性和别名字段的完整性")
        logger.info(f"")
        logger.info(f"==liuq debug== 🎉 用户现在可以安全地在GUI表格中修改'1_BlueSky_Bright'的'Offset R/G'字段！")
    else:
        logger.error(f"==liuq debug== ❌ 最终测试失败，需要进一步调试")
