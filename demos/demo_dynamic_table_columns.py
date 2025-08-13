#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态表格列生成功能演示
==liuq debug== FastMapV2 动态表格列生成演示脚本

{{CHENGQI:
Action: Added; Timestamp: 2025-08-04 17:05:00 +08:00; Reason: 添加动态表格列生成演示; Principle_Applied: 演示驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-04
版本: 2.0.0
描述: 演示动态表格列生成功能的使用方法
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.interfaces.xml_field_definition import (
    XMLFieldDefinition, FieldType, TableColumnDefinition, TableConfiguration
)
from core.managers.table_column_manager import TableColumnManager, table_column_manager
from core.services.field_registry_service import field_registry


def demo_basic_usage():
    """演示基本使用方法"""
    print("==liuq debug== 演示1: 基本使用方法")
    print("=" * 50)
    
    # 获取当前表格配置
    config = table_column_manager.get_current_configuration()
    print(f"当前配置名称: {config.config_name}")
    print(f"总列数: {len(config.columns)}")
    print(f"可见列数: {len(config.get_visible_columns())}")
    
    # 显示前5列的信息
    print("\n前5列信息:")
    for i, column in enumerate(config.get_visible_columns()[:5]):
        print(f"  {i+1}. {column.display_name} ({column.field_id}) - 宽度: {column.width}")
    
    print()


def demo_generate_default_config():
    """演示生成默认配置"""
    print("==liuq debug== 演示2: 生成默认配置")
    print("=" * 50)
    
    # 生成默认配置
    default_config = table_column_manager.generate_default_configuration()
    
    print(f"默认配置生成完成:")
    print(f"  配置名称: {default_config.config_name}")
    print(f"  总列数: {len(default_config.columns)}")
    print(f"  可见列数: {len(default_config.get_visible_columns())}")
    print(f"  总宽度: {default_config.total_width}")
    
    # 按分组显示列信息
    groups = {}
    for column in default_config.columns:
        if column.group not in groups:
            groups[column.group] = []
        groups[column.group].append(column)
    
    print(f"\n按分组显示列信息:")
    for group_name, columns in groups.items():
        print(f"  {group_name} 组 ({len(columns)} 列):")
        for column in columns[:3]:  # 只显示前3列
            print(f"    - {column.display_name} ({column.field_id})")
        if len(columns) > 3:
            print(f"    ... 还有 {len(columns) - 3} 列")
    
    print()


def demo_column_visibility_management():
    """演示列可见性管理"""
    print("==liuq debug== 演示3: 列可见性管理")
    print("=" * 50)
    
    # 获取当前配置
    config = table_column_manager.get_current_configuration()
    
    # 显示当前可见列
    visible_columns = config.get_visible_columns()
    print(f"当前可见列数: {len(visible_columns)}")
    
    # 隐藏一些列
    test_fields = ["e_ratio_min", "e_ratio_max", "trans_step"]
    print(f"\n隐藏字段: {test_fields}")
    
    for field_id in test_fields:
        success = table_column_manager.update_column_visibility(field_id, False)
        print(f"  隐藏 {field_id}: {'成功' if success else '失败'}")
    
    # 显示更新后的可见列数
    updated_config = table_column_manager.get_current_configuration()
    updated_visible = updated_config.get_visible_columns()
    print(f"\n更新后可见列数: {len(updated_visible)}")
    
    # 恢复可见性
    print(f"\n恢复字段可见性: {test_fields}")
    for field_id in test_fields:
        success = table_column_manager.update_column_visibility(field_id, True)
        print(f"  显示 {field_id}: {'成功' if success else '失败'}")
    
    print()


def demo_configuration_persistence():
    """演示配置持久化"""
    print("==liuq debug== 演示4: 配置持久化")
    print("=" * 50)
    
    # 创建自定义配置
    custom_columns = [
        TableColumnDefinition(
            column_id="col_alias",
            field_id="alias_name",
            display_name="Map名称",
            width=150,
            is_visible=True,
            sort_order=1,
            group="basic",
            tooltip="Map点别名"
        ),
        TableColumnDefinition(
            column_id="col_offset_x",
            field_id="offset_x",
            display_name="X偏移",
            width=80,
            is_visible=True,
            sort_order=2,
            group="coordinate"
        ),
        TableColumnDefinition(
            column_id="col_offset_y",
            field_id="offset_y",
            display_name="Y偏移",
            width=80,
            is_visible=True,
            sort_order=3,
            group="coordinate"
        ),
        TableColumnDefinition(
            column_id="col_weight",
            field_id="weight",
            display_name="权重",
            width=80,
            is_visible=True,
            sort_order=4,
            group="basic"
        )
    ]
    
    custom_config = TableConfiguration(
        config_name="demo_custom",
        columns=custom_columns,
        auto_resize=False,
        show_grid=True,
        alternate_row_colors=True
    )
    
    # 保存自定义配置
    success = table_column_manager.save_configuration("demo_custom", custom_config)
    print(f"保存自定义配置: {'成功' if success else '失败'}")
    
    # 获取可用配置列表
    available_configs = table_column_manager.get_available_configurations()
    print(f"可用配置: {available_configs}")
    
    # 加载自定义配置
    try:
        loaded_config = table_column_manager.load_configuration("demo_custom")
        print(f"加载自定义配置成功:")
        print(f"  配置名称: {loaded_config.config_name}")
        print(f"  列数: {len(loaded_config.columns)}")
        print(f"  自动调整大小: {loaded_config.auto_resize}")
        
        # 显示列信息
        print(f"  列信息:")
        for column in loaded_config.columns:
            print(f"    - {column.display_name}: {column.width}px")
            
    except Exception as e:
        print(f"加载配置失败: {e}")
    
    # 清理演示配置
    table_column_manager.delete_configuration("demo_custom")
    print(f"清理演示配置完成")
    
    print()


def demo_field_registry_integration():
    """演示与字段注册系统的集成"""
    print("==liuq debug== 演示5: 字段注册系统集成")
    print("=" * 50)
    
    # 显示字段注册系统信息
    all_fields = field_registry.get_all_fields()
    visible_fields = field_registry.get_visible_fields()
    editable_fields = field_registry.get_editable_fields()
    
    print(f"字段注册系统统计:")
    print(f"  总字段数: {len(all_fields)}")
    print(f"  可见字段数: {len(visible_fields)}")
    print(f"  可编辑字段数: {len(editable_fields)}")
    
    # 按分组显示字段
    from core.interfaces.field_definition_provider import FieldGroup

    print(f"\n按分组显示字段:")
    for group in FieldGroup:
        try:
            group_fields = field_registry.get_fields_by_group(group)
            if group_fields:
                print(f"  {group.value} 组: {len(group_fields)} 个字段")
                # 显示前3个字段
                for field_def in group_fields[:3]:
                    print(f"    - {field_def.display_name} ({field_def.field_id})")
                if len(group_fields) > 3:
                    print(f"    ... 还有 {len(group_fields) - 3} 个字段")
        except Exception as e:
            print(f"  获取 {group.value} 组字段失败: {e}")
    
    print()


def main():
    """主演示函数"""
    print("FastMapV2 动态表格列生成功能演示")
    print("=" * 60)
    print()
    
    try:
        # 运行各个演示
        demo_basic_usage()
        demo_generate_default_config()
        demo_column_visibility_management()
        demo_configuration_persistence()
        demo_field_registry_integration()
        
        print("=" * 60)
        print("所有演示完成！")
        print()
        print("动态表格列生成功能特点:")
        print("1. 基于字段注册系统自动生成列定义")
        print("2. 支持列可见性动态控制")
        print("3. 支持配置的保存、加载、导入、导出")
        print("4. 完全替代硬编码的列定义")
        print("5. 支持用户自定义配置方案")
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
