#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastMapV2 Map点索引映射问题修复验证测试

测试修复后的XML写入逻辑是否正确处理排序后的Map点
"""

import sys
import os
import logging
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.services.xml_parser_service import XMLParserService
from core.services.xml_writer_service import XMLWriterService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_map_point_indexing_after_sorting():
    """
    测试排序后Map点索引映射的正确性
    """
    
    print("=" * 80)
    print("FastMapV2 Map点索引映射修复验证测试")
    print("=" * 80)
    
    # 使用简单的测试XML文件
    test_xml = Path("tests/test_data/simple_map_test.xml")
    backup_xml = Path("tests/test_data/simple_map_test_backup.xml")
    
    if not test_xml.exists():
        print(f"❌ 测试文件不存在: {test_xml}")
        return False
    
    try:
        # 备份原始文件
        shutil.copy2(test_xml, backup_xml)
        print(f"✓ 已备份原始文件到: {backup_xml}")
        
        # 1. 解析XML文件
        print("\n1. 解析XML文件...")
        parser = XMLParserService()
        config = parser.parse_xml(str(test_xml), "test")
        
        if not config or not config.map_points:
            print("❌ XML解析失败或没有Map点")
            return False
        
        print(f"✓ 成功解析XML，共 {len(config.map_points)} 个Map点")
        
        # 2. 记录原始Map点位置和数据
        print("\n2. 记录原始Map点数据...")
        original_data = {}
        for mp in config.map_points:
            if mp.alias_name != "base_boundary0":
                original_data[mp.alias_name] = {
                    'offset_x': mp.offset_x,
                    'offset_y': mp.offset_y,
                    'weight': mp.weight
                }
                print(f"   {mp.alias_name}: offset_x={mp.offset_x}, offset_y={mp.offset_y}, weight={mp.weight}")
        
        # 3. 对Map点进行排序（模拟用户操作）
        print("\n3. 对Map点进行排序（按weight降序）...")
        original_order = [mp.alias_name for mp in config.map_points if mp.alias_name != "base_boundary0"]
        print(f"   原始顺序: {original_order}")
        
        # 按weight降序排序
        config.map_points.sort(key=lambda mp: mp.weight if mp.alias_name != "base_boundary0" else float('inf'), reverse=True)
        
        sorted_order = [mp.alias_name for mp in config.map_points if mp.alias_name != "base_boundary0"]
        print(f"   排序后顺序: {sorted_order}")
        
        # 4. 修改一个特定Map点的数据
        print("\n4. 修改Map_Point_1的数据...")
        target_map_point = None
        for mp in config.map_points:
            if mp.alias_name == "Map_Point_1":
                target_map_point = mp
                break
        
        if not target_map_point:
            print("❌ 未找到Map_Point_1")
            return False
        
        original_offset_x = target_map_point.offset_x
        new_offset_x = 0.888  # 使用一个特殊值
        target_map_point.offset_x = new_offset_x
        
        print(f"   修改Map_Point_1的offset_x: {original_offset_x} -> {new_offset_x}")
        
        # 5. 保存XML（测试修复后的逻辑）
        print("\n5. 保存XML（测试修复后的逻辑）...")
        writer = XMLWriterService()
        success = writer.write_xml(config, str(test_xml), backup=False)
        
        if not success:
            print("❌ XML写入失败")
            return False
        
        print("✓ XML写入成功")
        
        # 6. 重新解析XML验证结果
        print("\n6. 重新解析XML验证结果...")
        config_after = parser.parse_xml(str(test_xml), "test")
        
        if not config_after or not config_after.map_points:
            print("❌ 重新解析XML失败")
            return False
        
        # 7. 验证修改结果
        print("\n7. 验证修改结果...")
        verification_passed = True
        
        for mp in config_after.map_points:
            if mp.alias_name == "base_boundary0":
                continue
                
            if mp.alias_name == "Map_Point_1":
                # 验证目标Map点被正确修改
                if abs(mp.offset_x - new_offset_x) < 0.001:
                    print(f"   ✓ Map_Point_1正确更新: offset_x = {mp.offset_x}")
                else:
                    print(f"   ❌ Map_Point_1更新失败: 期望 {new_offset_x}, 实际 {mp.offset_x}")
                    verification_passed = False
            else:
                # 验证其他Map点没有被意外修改
                original_mp_data = original_data.get(mp.alias_name)
                if original_mp_data:
                    if (abs(mp.offset_x - original_mp_data['offset_x']) < 0.001 and
                        abs(mp.offset_y - original_mp_data['offset_y']) < 0.001 and
                        abs(mp.weight - original_mp_data['weight']) < 0.001):
                        print(f"   ✓ {mp.alias_name}保持不变: offset_x={mp.offset_x}")
                    else:
                        print(f"   ❌ {mp.alias_name}意外被修改:")
                        print(f"      原始: offset_x={original_mp_data['offset_x']}, offset_y={original_mp_data['offset_y']}")
                        print(f"      现在: offset_x={mp.offset_x}, offset_y={mp.offset_y}")
                        verification_passed = False
        
        # 8. 测试结果
        print("\n" + "=" * 80)
        if verification_passed:
            print("🎉 测试通过！Map点索引映射修复成功！")
            print("✓ 排序后的XML写入正确")
            print("✓ 只有目标Map点被修改")
            print("✓ 其他Map点保持不变")
        else:
            print("❌ 测试失败！仍存在索引映射问题")
        print("=" * 80)
        
        return verification_passed
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False
    
    finally:
        # 恢复原始文件
        if backup_xml.exists():
            shutil.copy2(backup_xml, test_xml)
            backup_xml.unlink()
            print(f"✓ 已恢复原始文件")


def test_alias_mapping_completeness():
    """
    测试别名映射的完整性
    """
    
    print("\n" + "=" * 80)
    print("测试别名映射的完整性")
    print("=" * 80)
    
    try:
        # 解析实际的XML文件
        test_xml = Path("tests/test_data/awb_scenario.xml")
        if not test_xml.exists():
            print(f"❌ 测试文件不存在: {test_xml}")
            return False
        
        parser = XMLParserService()
        config = parser.parse_xml(str(test_xml), "test")
        
        if not config or not config.map_points:
            print("❌ XML解析失败或没有Map点")
            return False
        
        # 创建XMLWriterService实例来测试别名映射
        writer = XMLWriterService()
        
        # 统计映射情况
        mapped_count = 0
        unmapped_aliases = []
        
        for mp in config.map_points:
            if mp.alias_name == "base_boundary0":
                continue
                
            xml_node_name = writer._get_xml_node_name_by_alias(mp.alias_name)
            if xml_node_name:
                mapped_count += 1
                print(f"   ✓ {mp.alias_name} -> {xml_node_name}")
            else:
                unmapped_aliases.append(mp.alias_name)
                print(f"   ❌ {mp.alias_name} -> 未映射")
        
        total_map_points = len([mp for mp in config.map_points if mp.alias_name != "base_boundary0"])
        
        print(f"\n映射统计:")
        print(f"   总Map点数: {total_map_points}")
        print(f"   已映射: {mapped_count}")
        print(f"   未映射: {len(unmapped_aliases)}")
        print(f"   映射率: {mapped_count/total_map_points*100:.1f}%")
        
        if unmapped_aliases:
            print(f"\n未映射的别名:")
            for alias in unmapped_aliases[:10]:  # 只显示前10个
                print(f"   - {alias}")
            if len(unmapped_aliases) > 10:
                print(f"   ... 还有 {len(unmapped_aliases)-10} 个")
        
        return len(unmapped_aliases) == 0
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        return False


if __name__ == '__main__':
    print("开始Map点索引映射修复验证测试...")
    
    # 测试1：基本功能测试
    test1_result = test_map_point_indexing_after_sorting()
    
    # 测试2：别名映射完整性测试
    test2_result = test_alias_mapping_completeness()
    
    print("\n" + "=" * 80)
    print("总体测试结果:")
    print(f"   基本功能测试: {'通过' if test1_result else '失败'}")
    print(f"   别名映射测试: {'通过' if test2_result else '失败'}")
    
    if test1_result and test2_result:
        print("🎉 所有测试通过！修复成功！")
    else:
        print("❌ 部分测试失败，需要进一步修复")
    print("=" * 80)
