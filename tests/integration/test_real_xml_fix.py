#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用实际XML文件测试Map点索引映射修复效果
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
    level=logging.WARNING,  # 减少日志输出
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_real_xml_sorting_fix():
    """
    使用实际的awb_scenario.xml文件测试排序后的修复效果
    """
    
    print("=" * 80)
    print("使用实际XML文件测试Map点索引映射修复")
    print("=" * 80)
    
    # 使用实际的XML文件
    test_xml = Path("tests/test_data/awb_scenario.xml")
    backup_xml = Path("tests/test_data/awb_scenario_backup.xml")
    
    if not test_xml.exists():
        print(f"❌ 测试文件不存在: {test_xml}")
        return False
    
    try:
        # 备份原始文件
        shutil.copy2(test_xml, backup_xml)
        print(f"✓ 已备份原始文件")
        
        # 1. 解析XML文件
        print("\n1. 解析XML文件...")
        parser = XMLParserService()
        config = parser.parse_xml(str(test_xml), "test")
        
        if not config or not config.map_points:
            print("❌ XML解析失败或没有Map点")
            return False
        
        print(f"✓ 成功解析XML，共 {len(config.map_points)} 个Map点")
        
        # 2. 记录原始数据（只记录前5个Map点的数据）
        print("\n2. 记录原始Map点数据（前5个）...")
        original_data = {}
        test_map_points = []
        
        for mp in config.map_points:
            if mp.alias_name != "base_boundary0":
                test_map_points.append(mp)
                if len(test_map_points) <= 5:
                    original_data[mp.alias_name] = {
                        'offset_x': mp.offset_x,
                        'offset_y': mp.offset_y,
                        'weight': mp.weight
                    }
                    print(f"   {mp.alias_name}: offset_x={mp.offset_x}")
        
        # 3. 对Map点进行排序
        print("\n3. 对Map点进行排序（按weight降序）...")
        original_order = [mp.alias_name for mp in test_map_points[:5]]
        print(f"   原始顺序（前5个）: {original_order}")
        
        # 按weight降序排序
        config.map_points.sort(key=lambda mp: mp.weight if mp.alias_name != "base_boundary0" else float('inf'), reverse=True)
        
        sorted_test_points = [mp for mp in config.map_points if mp.alias_name != "base_boundary0"][:5]
        sorted_order = [mp.alias_name for mp in sorted_test_points]
        print(f"   排序后顺序（前5个）: {sorted_order}")
        
        # 4. 修改特定Map点的数据
        print("\n4. 修改'1_BlueSky_Bright'的数据...")
        target_map_point = None
        for mp in config.map_points:
            if mp.alias_name == "1_BlueSky_Bright":
                target_map_point = mp
                break
        
        if not target_map_point:
            print("❌ 未找到'1_BlueSky_Bright'")
            return False
        
        original_offset_x = target_map_point.offset_x
        new_offset_x = 0.999  # 使用一个特殊值
        target_map_point.offset_x = new_offset_x
        
        print(f"   修改'1_BlueSky_Bright'的offset_x: {original_offset_x} -> {new_offset_x}")
        
        # 5. 保存XML
        print("\n5. 保存XML...")
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
        
        # 检查目标Map点
        target_found = False
        for mp in config_after.map_points:
            if mp.alias_name == "1_BlueSky_Bright":
                target_found = True
                if abs(mp.offset_x - new_offset_x) < 0.001:
                    print(f"   ✓ '1_BlueSky_Bright'正确更新: offset_x = {mp.offset_x}")
                else:
                    print(f"   ❌ '1_BlueSky_Bright'更新失败: 期望 {new_offset_x}, 实际 {mp.offset_x}")
                    verification_passed = False
                break
        
        if not target_found:
            print("   ❌ 未找到'1_BlueSky_Bright'")
            verification_passed = False
        
        # 检查其他Map点（前5个）
        for mp in config_after.map_points:
            if mp.alias_name in original_data and mp.alias_name != "1_BlueSky_Bright":
                original_mp_data = original_data[mp.alias_name]
                if abs(mp.offset_x - original_mp_data['offset_x']) < 0.001:
                    print(f"   ✓ {mp.alias_name}保持不变: offset_x={mp.offset_x}")
                else:
                    print(f"   ❌ {mp.alias_name}意外被修改:")
                    print(f"      原始: {original_mp_data['offset_x']}, 现在: {mp.offset_x}")
                    verification_passed = False
        
        # 8. 测试结果
        print("\n" + "=" * 80)
        if verification_passed:
            print("🎉 实际XML文件测试通过！")
            print("✓ 排序后的XML写入正确")
            print("✓ 只有目标Map点被修改")
            print("✓ 其他Map点保持不变")
            print("✓ 修复方案在实际场景中工作正常")
        else:
            print("❌ 实际XML文件测试失败！")
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


def test_multiple_modifications():
    """
    测试多次修改不同Map点的情况
    """
    
    print("\n" + "=" * 80)
    print("测试多次修改不同Map点")
    print("=" * 80)
    
    test_xml = Path("tests/test_data/simple_map_test.xml")
    backup_xml = Path("tests/test_data/simple_map_test_backup2.xml")
    
    if not test_xml.exists():
        print(f"❌ 测试文件不存在: {test_xml}")
        return False
    
    try:
        # 备份原始文件
        shutil.copy2(test_xml, backup_xml)
        
        parser = XMLParserService()
        writer = XMLWriterService()
        
        # 测试修改Map_Point_1
        print("\n1. 修改Map_Point_1...")
        config = parser.parse_xml(str(test_xml), "test")
        
        # 排序
        config.map_points.sort(key=lambda mp: mp.weight if mp.alias_name != "base_boundary0" else float('inf'), reverse=True)
        
        # 修改Map_Point_1
        for mp in config.map_points:
            if mp.alias_name == "Map_Point_1":
                mp.offset_x = 111.111
                break
        
        success = writer.write_xml(config, str(test_xml), backup=False)
        if not success:
            print("❌ 第一次写入失败")
            return False
        
        # 测试修改Map_Point_2
        print("2. 修改Map_Point_2...")
        config = parser.parse_xml(str(test_xml), "test")
        
        # 再次排序
        config.map_points.sort(key=lambda mp: mp.weight if mp.alias_name != "base_boundary0" else float('inf'))
        
        # 修改Map_Point_2
        for mp in config.map_points:
            if mp.alias_name == "Map_Point_2":
                mp.offset_y = 222.222
                break
        
        success = writer.write_xml(config, str(test_xml), backup=False)
        if not success:
            print("❌ 第二次写入失败")
            return False
        
        # 验证结果
        print("3. 验证最终结果...")
        config_final = parser.parse_xml(str(test_xml), "test")
        
        verification_passed = True
        for mp in config_final.map_points:
            if mp.alias_name == "Map_Point_1":
                if abs(mp.offset_x - 111.111) < 0.001:
                    print(f"   ✓ Map_Point_1正确: offset_x = {mp.offset_x}")
                else:
                    print(f"   ❌ Map_Point_1错误: offset_x = {mp.offset_x}")
                    verification_passed = False
            elif mp.alias_name == "Map_Point_2":
                if abs(mp.offset_y - 222.222) < 0.001:
                    print(f"   ✓ Map_Point_2正确: offset_y = {mp.offset_y}")
                else:
                    print(f"   ❌ Map_Point_2错误: offset_y = {mp.offset_y}")
                    verification_passed = False
            elif mp.alias_name == "Map_Point_3":
                if abs(mp.offset_x - 200.0) < 0.001 and abs(mp.offset_y - 300.0) < 0.001:
                    print(f"   ✓ Map_Point_3保持不变: offset_x={mp.offset_x}, offset_y={mp.offset_y}")
                else:
                    print(f"   ❌ Map_Point_3意外改变: offset_x={mp.offset_x}, offset_y={mp.offset_y}")
                    verification_passed = False
        
        if verification_passed:
            print("🎉 多次修改测试通过！")
        else:
            print("❌ 多次修改测试失败！")
        
        return verification_passed
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        return False
    
    finally:
        # 恢复原始文件
        if backup_xml.exists():
            shutil.copy2(backup_xml, test_xml)
            backup_xml.unlink()


if __name__ == '__main__':
    print("开始全面测试Map点索引映射修复...")
    
    # 测试1：实际XML文件测试
    test1_result = test_real_xml_sorting_fix()
    
    # 测试2：多次修改测试
    test2_result = test_multiple_modifications()
    
    print("\n" + "=" * 80)
    print("全面测试结果:")
    print(f"   实际XML文件测试: {'通过' if test1_result else '失败'}")
    print(f"   多次修改测试: {'通过' if test2_result else '失败'}")
    
    if test1_result and test2_result:
        print("🎉 所有测试通过！修复方案完全成功！")
        print("✅ Map点索引映射问题已彻底解决")
        print("✅ 排序功能不再影响XML写入正确性")
        print("✅ 修改单个Map点不会影响其他Map点")
    else:
        print("❌ 部分测试失败，需要进一步检查")
    print("=" * 80)
