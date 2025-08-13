#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单检查XML中"1_BlueSky_Bright"的位置
"""

import sys
import os
from pathlib import Path
import xml.etree.ElementTree as ET

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_bluesky_location():
    """检查1_BlueSky_Bright在XML中的位置"""
    
    xml_file = project_root / "tests" / "test_data" / "awb_scenario.xml"
    
    print(f"==liuq debug== 检查XML文件: {xml_file}")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # 查找所有包含"1_BlueSky_Bright"的节点
        print(f"==liuq debug== 查找'1_BlueSky_Bright':")
        
        # 方法1：直接搜索AliasName元素
        for elem in root.iter('AliasName'):
            if elem.text and "1_BlueSky_Bright" in elem.text:
                parent = elem.getparent() if hasattr(elem, 'getparent') else None
                if parent is not None:
                    parent_tag = parent.tag
                    print(f"  - 找到AliasName: {elem.text} (父节点: {parent_tag})")
                    
                    # 查找对应的第一组数据
                    first_group_nodes = root.findall(f'.//{parent_tag}')
                    for i, node in enumerate(first_group_nodes):
                        offset_elem = node.find('offset')
                        if offset_elem is not None:
                            x_elem = offset_elem.find('x')
                            if x_elem is not None:
                                print(f"  - 对应的第一组数据在{parent_tag}节点{i+1}，offset/x: {x_elem.text}")
                                break
        
        # 方法2：检查offset_map01的内容
        print(f"==liuq debug== 检查offset_map01:")
        offset_map01_nodes = root.findall('.//offset_map01')
        print(f"  - 找到 {len(offset_map01_nodes)} 个offset_map01节点")
        
        for i, node in enumerate(offset_map01_nodes):
            print(f"  - offset_map01节点 {i+1}:")
            
            # 检查offset子节点
            offset_elem = node.find('offset')
            if offset_elem is not None:
                x_elem = offset_elem.find('x')
                y_elem = offset_elem.find('y')
                if x_elem is not None and y_elem is not None:
                    print(f"    * offset/x: {x_elem.text}, offset/y: {y_elem.text}")
            
            # 检查AliasName子节点
            alias_elem = node.find('AliasName')
            if alias_elem is not None:
                print(f"    * AliasName: {alias_elem.text}")
        
        return True
        
    except Exception as e:
        print(f"==liuq debug== 检查失败: {e}")
        return False

if __name__ == "__main__":
    check_bluesky_location()
