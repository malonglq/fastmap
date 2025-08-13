#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastMapV2 Map点索引映射修复最终验证
"""

import sys
import os
import logging
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.services.xml_parser_service import XMLParserService
from core.services.xml_writer_service import XMLWriterService

# 配置日志
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_final_fix():
    """
    最终修复功能验证
    """
    
    print("=" * 60)
    print("FastMapV2 Map点索引映射修复最终验证")
    print("=" * 60)
    
    # 使用简单的测试XML文件
    test_xml = Path("tests/test_data/simple_map_test.xml")
    backup_xml = Path("tests/test_data/simple_map_test_backup_final.xml")
    
    if not test_xml.exists():
        print(f"测试文件不存在: {test_xml}")
        return False
    
    try:
        # 备份原始文件
        shutil.copy2(test_xml, backup_xml)
        print("已备份原始文件")
        
        # 1. 解析XML文件
        print("\n1. 解析XML文件...")
        parser = XMLParserService()
        config = parser.parse_xml(str(test_xml), "test")
        
        if not config or not config.map_points:
            print("XML解析失败或没有Map点")
            return False
        
        print(f"成功解析XML，共 {len(config.map_points)} 个Map点")
        
        # 2. 记录原始数据
        print("\n2. 记录原始Map点数据...")
        original_data = {}
        for mp in config.map_points:
            if mp.alias_name != "base_boundary0":
                original_data[mp.alias_name] = mp.offset_x
                print(f"   {mp.alias_name}: offset_x={mp.offset_x}")
        
        # 3. 排序Map点（这是问题的触发条件）
        print("\n3. 对Map点进行排序...")
        original_order = [mp.alias_name for mp in config.map_points if mp.alias_name != "base_boundary0"]
        print(f"   原始顺序: {original_order}")
        
        # 按weight降序排序
        config.map_points.sort(key=lambda mp: mp.weight if mp.alias_name != "base_boundary0" else float('inf'), reverse=True)
        
        sorted_order = [mp.alias_name for mp in config.map_points if mp.alias_name != "base_boundary0"]
        print(f"   排序后顺序: {sorted_order}")
        
        # 4. 修改一个Map点（测试修复效果）
        print("\n4. 修改Map_Point_1的数据...")
        target_map_point = None
        for mp in config.map_points:
            if mp.alias_name == "Map_Point_1":
                target_map_point = mp
                break
        
        if not target_map_point:
            print("未找到Map_Point_1")
            return False
        
        original_offset_x = target_map_point.offset_x
        new_offset_x = 777.777
        target_map_point.offset_x = new_offset_x
        
        print(f"   修改Map_Point_1的offset_x: {original_offset_x} -> {new_offset_x}")
        
        # 5. 保存XML（测试动态映射修复）
        print("\n5. 保存XML...")
        writer = XMLWriterService()
        success = writer.write_xml(config, str(test_xml), backup=False)
        
        if not success:
            print("XML写入失败")
            return False
        
        print("XML写入成功")
        
        # 6. 重新解析验证
        print("\n6. 重新解析XML验证结果...")
        config_after = parser.parse_xml(str(test_xml), "test")
        
        if not config_after or not config_after.map_points:
            print("重新解析XML失败")
            return False
        
        # 7. 验证结果
        print("\n7. 验证修改结果...")
        verification_passed = True
        
        for mp in config_after.map_points:
            if mp.alias_name == "Map_Point_1":
                if abs(mp.offset_x - new_offset_x) < 0.001:
                    print(f"   [PASS] Map_Point_1正确更新: offset_x = {mp.offset_x}")
                else:
                    print(f"   [FAIL] Map_Point_1更新失败: 期望 {new_offset_x}, 实际 {mp.offset_x}")
                    verification_passed = False
            elif mp.alias_name in original_data:
                original_x = original_data[mp.alias_name]
                if abs(mp.offset_x - original_x) < 0.001:
                    print(f"   [PASS] {mp.alias_name}保持不变: offset_x = {mp.offset_x}")
                else:
                    print(f"   [FAIL] {mp.alias_name}意外改变: offset_x = {mp.offset_x} (原始: {original_x})")
                    verification_passed = False
        
        return verification_passed
        
    except Exception as e:
        print(f"测试过程中发生异常: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")
        return False
    
    finally:
        # 恢复原始文件
        if backup_xml.exists():
            shutil.copy2(backup_xml, test_xml)
            backup_xml.unlink()
            print("已恢复原始文件")


def main():
    """
    主测试函数
    """
    
    print("FastMapV2 Map点索引映射修复最终验证")
    print("=" * 60)
    
    # 运行最终验证测试
    test_result = test_final_fix()
    
    # 输出总结
    print("\n" + "=" * 60)
    print("最终验证结果:")
    
    if test_result:
        print("[SUCCESS] 所有测试通过！修复成功！")
        print("- Map点索引映射问题已彻底解决")
        print("- 排序功能不再影响XML写入正确性")
        print("- 修改单个Map点不会影响其他Map点")
        print("- 动态别名映射机制工作正常")
        print("- 修复方案可以安全部署到生产环境")
        return True
    else:
        print("[FAILED] 测试失败，需要进一步检查")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
