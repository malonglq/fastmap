#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证40列修复效果
==liuq debug== FastMapV2 40列结构修复验证脚本

{{CHENGQI:
Action: Added; Timestamp: 2025-08-04 18:10:00 +08:00; Reason: 验证40列修复效果; Principle_Applied: 测试驱动验证;
}}

作者: 龙sir团队
创建时间: 2025-08-04
版本: 2.0.0
描述: 验证动态表格列生成功能是否正确生成40列结构
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.managers.table_column_manager import table_column_manager, LEGACY_40_COLUMNS_DEFINITION


def verify_40_columns_structure():
    """验证40列结构"""
    print("==liuq debug== 验证40列结构修复效果")
    print("=" * 60)
    
    # 生成默认配置
    config = table_column_manager.generate_default_configuration()
    
    print(f"生成的配置信息:")
    print(f"  配置名称: {config.config_name}")
    print(f"  总列数: {len(config.columns)}")
    print(f"  可见列数: {len(config.get_visible_columns())}")
    print(f"  总宽度: {config.total_width}")
    
    # 验证列数量
    if len(config.columns) == 40:
        print("✅ 列数量正确: 40列")
    else:
        print(f"❌ 列数量错误: 期望40列，实际{len(config.columns)}列")
        return False
    
    # 验证列结构
    print(f"\n验证列结构:")
    errors = []
    
    for i, expected_col in enumerate(LEGACY_40_COLUMNS_DEFINITION):
        if i >= len(config.columns):
            errors.append(f"缺少第{i+1}列: {expected_col['field_id']}")
            continue
        
        actual_col = config.columns[i]
        
        # 验证字段ID
        if actual_col.field_id != expected_col["field_id"]:
            errors.append(f"第{i+1}列字段ID不匹配: 期望{expected_col['field_id']}，实际{actual_col.field_id}")
        
        # 验证显示名称
        if actual_col.display_name != expected_col["display_name"]:
            errors.append(f"第{i+1}列显示名称不匹配: 期望{expected_col['display_name']}，实际{actual_col.display_name}")
        
        # 验证宽度
        if actual_col.width != expected_col["width"]:
            errors.append(f"第{i+1}列宽度不匹配: 期望{expected_col['width']}，实际{actual_col.width}")
    
    if errors:
        print("❌ 发现以下错误:")
        for error in errors[:10]:  # 只显示前10个错误
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... 还有 {len(errors) - 10} 个错误")
        return False
    else:
        print("✅ 列结构验证通过")
    
    return True


def display_column_mapping():
    """显示列映射对比"""
    print(f"\n==liuq debug== 列映射对比")
    print("=" * 60)
    
    config = table_column_manager.generate_default_configuration()
    
    print(f"{'索引':<4} {'字段ID':<20} {'显示名称':<15} {'宽度':<6}")
    print("-" * 60)
    
    for i, column in enumerate(config.columns):
        print(f"{i:<4} {column.field_id:<20} {column.display_name:<15} {column.width:<6}")


def verify_original_hardcoded_mapping():
    """验证与原始硬编码映射的一致性"""
    print(f"\n==liuq debug== 验证与原始硬编码映射的一致性")
    print("=" * 60)
    
    # 原始硬编码的列索引到字段ID映射
    original_mapping = {
        0: 'alias_name',           # MapList
        1: 'offset_x',             # Offset R/G
        2: 'offset_y',             # Offset B/G
        3: 'weight',               # Weight
        4: 'trans_step',           # Step
        5: 'e_ratio_min',          # ERatio Min
        6: 'e_ratio_max',          # ERatio Max
        7: 'tran_bv_min',          # BV Lower
        8: 'bv_min',               # BV Min
        9: 'bv_max',               # BV Max
        10: 'tran_bv_max',         # BV Upper
        11: 'tran_ctemp_min',      # Ctemp Lower
        12: 'ctemp_min',           # Ctemp Min
        13: 'ctemp_max',           # Ctemp Max
        14: 'tran_ctemp_max',      # Ctemp Upper
        15: 'tran_ir_min',         # IR Lower
        16: 'ir_min',              # IR Min
        17: 'ir_max',              # IR Max
        18: 'tran_ir_max',         # IR Upper
        19: 'tran_ac_min',         # AC Lower
        20: 'ac_min',              # AC Min
        21: 'ac_max',              # AC Max
        22: 'tran_ac_max',         # AC Upper
        23: 'tran_count_min',      # COUNT Lower
        24: 'count_min',           # COUNT Min
        25: 'count_max',           # COUNT Max
        26: 'tran_count_max',      # COUNT Upper
        27: 'tran_color_cct_min',  # ColorCCT Lower
        28: 'color_cct_min',       # ColorCCT Min
        29: 'color_cct_max',       # ColorCCT Max
        30: 'tran_color_cct_max',  # ColorCCT Upper
        31: 'tran_diff_ctemp_min', # diffCtemp Lower
        32: 'diff_ctemp_min',      # diffCtemp Min
        33: 'diff_ctemp_max',      # diffCtemp Max
        34: 'tran_diff_ctemp_max', # diffCtemp Upper
        35: 'tran_face_ctemp_min', # FaceCtemp Lower
        36: 'face_ctemp_min',      # FaceCtemp Min
        37: 'face_ctemp_max',      # FaceCtemp Max
        38: 'tran_face_ctemp_max', # FaceCtemp Upper
        39: 'ml',                  # ml
    }
    
    config = table_column_manager.generate_default_configuration()
    
    errors = []
    for i, expected_field_id in original_mapping.items():
        if i >= len(config.columns):
            errors.append(f"缺少列索引 {i}: {expected_field_id}")
            continue
        
        actual_field_id = config.columns[i].field_id
        if actual_field_id != expected_field_id:
            errors.append(f"列索引 {i} 字段ID不匹配: 期望{expected_field_id}，实际{actual_field_id}")
    
    if errors:
        print("❌ 与原始硬编码映射不一致:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ 与原始硬编码映射完全一致")
        return True


def main():
    """主验证函数"""
    print("FastMapV2 40列结构修复验证")
    print("=" * 60)
    
    try:
        # 验证40列结构
        structure_ok = verify_40_columns_structure()
        
        # 显示列映射
        display_column_mapping()
        
        # 验证与原始映射的一致性
        mapping_ok = verify_original_hardcoded_mapping()
        
        print(f"\n" + "=" * 60)
        print("验证结果总结:")
        print(f"  40列结构: {'✅ 通过' if structure_ok else '❌ 失败'}")
        print(f"  原始映射一致性: {'✅ 通过' if mapping_ok else '❌ 失败'}")
        
        if structure_ok and mapping_ok:
            print(f"\n🎉 40列结构修复成功！")
            print("动态表格列生成功能现在与原始硬编码版本完全一致。")
        else:
            print(f"\n⚠️  修复未完成，请检查上述错误。")
        
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
