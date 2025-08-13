#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试权重排序导致的映射问题
"""

import sys
import os
from pathlib import Path
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.xml_parser_service import XMLParserService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_weight_sorting_issue():
    """测试权重排序导致的映射问题"""
    
    xml_file = project_root / "tests" / "test_data" / "awb_scenario.xml"
    
    logger.info(f"==liuq debug== 测试权重排序问题")
    
    # 解析XML
    parser = XMLParserService()
    config = parser.parse_xml(xml_file)
    
    logger.info(f"==liuq debug== 解析后的Map点顺序（按权重排序后）:")
    
    for i, mp in enumerate(config.map_points):
        logger.info(f"  索引{i}: {mp.alias_name}, weight={mp.weight}")
        
        if mp.alias_name == "1_BlueSky_Bright":
            logger.info(f"==liuq debug== '1_BlueSky_Bright'在排序后的索引: {i}")
            
            # 计算当前写入逻辑会映射到哪个节点
            if mp.alias_name != "base_boundary0":
                # 计算在非base_boundary点中的位置
                non_base_points = [p for p in config.map_points if p.alias_name != "base_boundary0"]
                offset_index = -1
                for j, p in enumerate(non_base_points):
                    if p.alias_name == "1_BlueSky_Bright":
                        offset_index = j
                        break
                
                if offset_index >= 0:
                    map_index = offset_index + 1
                    logger.info(f"==liuq debug== 当前逻辑会映射到: offset_map{map_index:02d}")
                    logger.info(f"==liuq debug== 但实际应该映射到: offset_map01")
                    
                    if map_index != 1:
                        logger.error(f"==liuq debug== ✗ 映射错误！权重排序导致索引计算错误")
                        return False
                    else:
                        logger.info(f"==liuq debug== ✓ 映射正确")
                        return True
    
    return False

def analyze_weight_distribution():
    """分析权重分布"""
    
    xml_file = project_root / "tests" / "test_data" / "awb_scenario.xml"
    
    logger.info(f"==liuq debug== 分析权重分布:")
    
    # 解析XML
    parser = XMLParserService()
    config = parser.parse_xml(xml_file)
    
    # 按原始XML顺序（不排序）分析
    logger.info(f"==liuq debug== 前10个Map点的权重分布:")
    
    for i, mp in enumerate(config.map_points[:10]):
        logger.info(f"  {mp.alias_name}: weight={mp.weight}")
        
        if mp.alias_name == "1_BlueSky_Bright":
            logger.info(f"==liuq debug== '1_BlueSky_Bright'的权重: {mp.weight}")

if __name__ == "__main__":
    logger.info(f"==liuq debug== 开始测试权重排序问题")
    
    analyze_weight_distribution()
    success = test_weight_sorting_issue()
    
    if success:
        logger.info(f"==liuq debug== ✓ 映射正确")
    else:
        logger.error(f"==liuq debug== ✗ 发现权重排序导致的映射问题")
