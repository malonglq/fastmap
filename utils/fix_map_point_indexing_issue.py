#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastMapV2 Map点索引映射问题修复方案

修复Map点排序导致的XML索引映射错误问题
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.services.map_analysis.xml_writer_service import XMLWriterService

logger = logging.getLogger(__name__)


def create_alias_to_xml_mapping():
    """
    创建Map点别名到XML节点的映射表
    
    这个函数分析现有的XML结构，建立别名与offset_map节点的固定映射关系
    """
    
    # 这里需要根据实际的XML结构来建立映射
    # 示例映射（需要根据实际数据调整）
    alias_mapping = {
        # 格式：别名 -> XML节点名称
        "1_BlueSky_Bright": "offset_map01",
        "2_Cloudy_Day": "offset_map02", 
        "3_Indoor_Light": "offset_map03",
        # ... 需要补充完整的映射表
    }
    
    return alias_mapping


def fix_xml_writer_service():
    """
    修复XMLWriterService中的索引映射问题
    """
    
    print("=" * 60)
    print("FastMapV2 Map点索引映射问题修复")
    print("=" * 60)
    
    print("\n1. 问题分析:")
    print("   - Map点排序功能破坏了XML索引映射的一致性")
    print("   - XML写入时使用排序后的列表顺序进行映射")
    print("   - 导致Map点数据写入到错误的XML节点位置")
    
    print("\n2. 修复方案:")
    print("   - 建立别名到XML节点的固定映射关系")
    print("   - 修改XML写入逻辑，不依赖列表顺序")
    print("   - 确保XML写入与排序状态无关")
    
    print("\n3. 需要修改的文件:")
    print("   - core/services/xml_writer_service.py")
    print("   - 添加别名映射逻辑")
    print("   - 修改_update_map_points_in_xml方法")
    print("   - 修改_update_offset_map_in_xml方法")
    
    print("\n4. 修复步骤:")
    
    # 步骤1：创建别名映射
    print("   步骤1: 创建别名到XML节点的映射表...")
    alias_mapping = create_alias_to_xml_mapping()
    print(f"   - 创建了 {len(alias_mapping)} 个映射关系")
    
    # 步骤2：显示需要修改的代码
    print("\n   步骤2: 需要在XMLWriterService中添加以下方法:")
    
    print("""
    def _get_xml_node_name_by_alias(self, alias_name: str) -> str:
        \"\"\"
        根据别名获取对应的XML节点名称
        
        Args:
            alias_name: Map点别名
            
        Returns:
            str: 对应的XML节点名称（如'offset_map01'）
        \"\"\"
        # 建立别名到XML节点的映射关系
        alias_mapping = {
            # 这里需要根据实际XML结构建立完整映射
            "1_BlueSky_Bright": "offset_map01",
            "2_Cloudy_Day": "offset_map02",
            # ... 更多映射
        }
        
        return alias_mapping.get(alias_name, None)
    """)
    
    print("\n   步骤3: 修改_update_map_points_in_xml方法:")
    
    print("""
    # 原始代码（有问题）:
    offset_map_counter = 1
    for i, map_point in enumerate(map_points):
        if map_point.alias_name == "base_boundary0":
            success = self._update_base_boundary_in_xml(root, map_point)
        else:
            success = self._update_offset_map_in_xml(root, map_point, offset_map_counter)
            offset_map_counter += 1
    
    # 修复后的代码:
    for map_point in map_points:
        if map_point.alias_name == "base_boundary0":
            success = self._update_base_boundary_in_xml(root, map_point)
        else:
            success = self._update_offset_map_in_xml(root, map_point)
    """)
    
    print("\n   步骤4: 修改_update_offset_map_in_xml方法签名:")
    
    print("""
    # 原始方法签名:
    def _update_offset_map_in_xml(self, root: ET.Element, map_point: MapPoint, map_index: int) -> bool:
    
    # 修复后的方法签名:
    def _update_offset_map_in_xml(self, root: ET.Element, map_point: MapPoint) -> bool:
        \"\"\"
        更新offset_map的双组数据结构
        
        Args:
            root: XML根元素
            map_point: Map点对象
            
        Returns:
            bool: 更新是否成功
        \"\"\"
        try:
            # 根据别名获取XML节点名称
            element_name = self._get_xml_node_name_by_alias(map_point.alias_name)
            if not element_name:
                logger.warning(f"未找到别名 {map_point.alias_name} 对应的XML节点")
                return False
            
            logger.info(f"查找XML节点: {element_name}")
            
            # 查找offset_map的两个节点
            offset_map_nodes = root.findall(f'.//{element_name}')
            # ... 后续逻辑保持不变
    """)
    
    print("\n5. 验证计划:")
    print("   - 创建测试用例验证修复效果")
    print("   - 测试排序后的XML写入是否正确")
    print("   - 确认修改单个Map点不会影响其他Map点")
    
    print("\n6. 注意事项:")
    print("   - 需要根据实际XML结构建立完整的别名映射表")
    print("   - 确保所有Map点都有对应的映射关系")
    print("   - 测试各种排序场景下的XML写入正确性")
    
    print("\n" + "=" * 60)
    print("修复方案说明完成！")
    print("请按照上述步骤修改代码，然后进行充分测试。")
    print("=" * 60)


def create_test_case():
    """
    创建测试用例来验证修复效果
    """
    
    test_code = '''
def test_map_point_indexing_after_sorting():
    """
    测试排序后Map点索引映射的正确性
    """
    # 1. 加载XML文件
    config = parser.parse_xml(xml_file_path, "test")
    
    # 2. 记录原始Map点位置
    original_positions = {}
    for i, mp in enumerate(config.map_points):
        if mp.alias_name != "base_boundary0":
            original_positions[mp.alias_name] = i
    
    # 3. 对Map点进行排序
    config.map_points.sort(key=lambda mp: mp.weight, reverse=True)
    
    # 4. 修改一个Map点的数据
    target_map_point = None
    for mp in config.map_points:
        if mp.alias_name == "1_BlueSky_Bright":
            target_map_point = mp
            break
    
    if target_map_point:
        original_offset_x = target_map_point.offset_x
        target_map_point.offset_x = 0.999  # 修改值
        
        # 5. 保存XML
        writer = XMLWriterService()
        success = writer.write_xml(config, xml_file_path, backup=False)
        assert success, "XML写入失败"
        
        # 6. 重新解析XML验证
        config_after = parser.parse_xml(xml_file_path, "test")
        
        # 7. 验证只有目标Map点被修改，其他Map点保持不变
        for mp in config_after.map_points:
            if mp.alias_name == "1_BlueSky_Bright":
                assert mp.offset_x == 0.999, f"目标Map点修改失败: {mp.offset_x}"
            else:
                # 其他Map点应该保持原始值
                original_mp = None
                for orig_mp in original_config.map_points:
                    if orig_mp.alias_name == mp.alias_name:
                        original_mp = orig_mp
                        break
                
                if original_mp:
                    assert mp.offset_x == original_mp.offset_x, f"Map点 {mp.alias_name} 意外被修改"
        
        print("✓ 测试通过：排序后的XML写入正确")
    '''
    
    return test_code


if __name__ == '__main__':
    # 执行修复方案说明
    fix_xml_writer_service()
    
    print("\n" + "=" * 60)
    print("测试用例代码:")
    print("=" * 60)
    test_code = create_test_case()
    print(test_code)
