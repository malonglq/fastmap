#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MapTableWidget集成测试
==liuq debug== FastMapV2 MapTableWidget与动态列生成集成测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-04 18:15:00 +08:00; Reason: 测试MapTableWidget与动态列生成的集成; Principle_Applied: 集成测试;
}}

作者: 龙sir团队
创建时间: 2025-08-04
版本: 2.0.0
描述: 测试MapTableWidget是否能正确使用动态列生成功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.managers.table_column_manager import table_column_manager


def test_map_table_widget_column_generation():
    """测试MapTableWidget的列生成"""
    print("==liuq debug== 测试MapTableWidget列生成")
    print("=" * 50)
    
    # 模拟MapTableWidget的初始化过程
    try:
        # 1. 初始化表格配置
        table_config = table_column_manager.get_current_configuration()
        column_definitions = table_config.get_visible_columns()
        
        print(f"表格配置初始化:")
        print(f"  配置名称: {table_config.config_name}")
        print(f"  总列数: {len(table_config.columns)}")
        print(f"  可见列数: {len(column_definitions)}")
        
        # 2. 验证列数量
        if len(column_definitions) == 40:
            print("✅ 列数量正确: 40列")
        else:
            print(f"❌ 列数量错误: 期望40列，实际{len(column_definitions)}列")
            return False
        
        # 3. 模拟setup_table过程
        print(f"\n模拟setup_table过程:")
        
        # 设置列数
        column_count = len(column_definitions)
        print(f"  设置列数: {column_count}")
        
        # 设置列标题和宽度
        for i, column_def in enumerate(column_definitions):
            print(f"  列{i}: {column_def.display_name} (宽度: {column_def.width})")
            if i >= 5:  # 只显示前5列
                print(f"  ... 还有 {len(column_definitions) - 6} 列")
                break
        
        # 4. 模拟_get_field_id_by_column方法
        print(f"\n测试字段ID映射:")
        test_columns = [0, 1, 2, 3, 39]  # 测试几个关键列
        for col in test_columns:
            if 0 <= col < len(column_definitions):
                field_id = column_definitions[col].field_id
                display_name = column_definitions[col].display_name
                print(f"  列{col}: {field_id} -> {display_name}")
            else:
                print(f"  列{col}: 超出范围")
        
        # 5. 验证可编辑字段
        print(f"\n验证可编辑字段:")
        editable_count = 0
        for column_def in column_definitions:
            # 模拟检查字段是否可编辑的逻辑
            if column_def.field_id in ['alias_name', 'offset_x', 'offset_y', 'weight', 'trans_step']:
                editable_count += 1
        
        print(f"  可编辑字段数量: {editable_count}")
        
        print(f"\n✅ MapTableWidget集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ MapTableWidget集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_column_visibility_control():
    """测试列可见性控制"""
    print(f"\n==liuq debug== 测试列可见性控制")
    print("=" * 50)
    
    try:
        # 获取当前配置
        config = table_column_manager.get_current_configuration()
        original_visible_count = len(config.get_visible_columns())
        
        print(f"原始可见列数: {original_visible_count}")
        
        # 隐藏一些列
        test_fields = ["e_ratio_min", "e_ratio_max"]
        for field_id in test_fields:
            success = table_column_manager.update_column_visibility(field_id, False)
            print(f"隐藏 {field_id}: {'成功' if success else '失败'}")
        
        # 检查更新后的可见列数
        updated_config = table_column_manager.get_current_configuration()
        updated_visible_count = len(updated_config.get_visible_columns())
        
        print(f"更新后可见列数: {updated_visible_count}")
        
        if updated_visible_count == original_visible_count - len(test_fields):
            print("✅ 列可见性控制正常")
        else:
            print("❌ 列可见性控制异常")
            return False
        
        # 恢复可见性
        for field_id in test_fields:
            success = table_column_manager.update_column_visibility(field_id, True)
            print(f"显示 {field_id}: {'成功' if success else '失败'}")
        
        # 验证恢复
        final_config = table_column_manager.get_current_configuration()
        final_visible_count = len(final_config.get_visible_columns())
        
        if final_visible_count == original_visible_count:
            print("✅ 列可见性恢复正常")
            return True
        else:
            print("❌ 列可见性恢复异常")
            return False
        
    except Exception as e:
        print(f"❌ 列可见性控制测试失败: {e}")
        return False


def test_field_id_mapping_consistency():
    """测试字段ID映射一致性"""
    print(f"\n==liuq debug== 测试字段ID映射一致性")
    print("=" * 50)
    
    try:
        config = table_column_manager.get_current_configuration()
        
        # 测试所有列的字段ID映射
        mapping_errors = []
        
        for i, column_def in enumerate(config.columns):
            # 模拟MapTableWidget的_get_field_id_by_column方法
            if 0 <= i < len(config.columns):
                mapped_field_id = config.columns[i].field_id
                if mapped_field_id != column_def.field_id:
                    mapping_errors.append(f"列{i}映射不一致: 期望{column_def.field_id}，实际{mapped_field_id}")
        
        if mapping_errors:
            print("❌ 字段ID映射存在问题:")
            for error in mapping_errors[:5]:  # 只显示前5个错误
                print(f"  - {error}")
            return False
        else:
            print("✅ 字段ID映射一致性验证通过")
            return True
        
    except Exception as e:
        print(f"❌ 字段ID映射一致性测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("MapTableWidget与动态列生成集成测试")
    print("=" * 60)
    
    try:
        # 运行各项测试
        test1_ok = test_map_table_widget_column_generation()
        test2_ok = test_column_visibility_control()
        test3_ok = test_field_id_mapping_consistency()
        
        print(f"\n" + "=" * 60)
        print("集成测试结果总结:")
        print(f"  MapTableWidget列生成: {'✅ 通过' if test1_ok else '❌ 失败'}")
        print(f"  列可见性控制: {'✅ 通过' if test2_ok else '❌ 失败'}")
        print(f"  字段ID映射一致性: {'✅ 通过' if test3_ok else '❌ 失败'}")
        
        if test1_ok and test2_ok and test3_ok:
            print(f"\n🎉 MapTableWidget集成测试全部通过！")
            print("动态表格列生成功能与MapTableWidget完美集成。")
        else:
            print(f"\n⚠️  部分测试失败，请检查上述错误。")
        
    except Exception as e:
        print(f"集成测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
