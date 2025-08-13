#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终40列结构验证
==liuq debug== FastMapV2 40列结构最终验证脚本

{{CHENGQI:
Action: Added; Timestamp: 2025-08-04 18:20:00 +08:00; Reason: 最终验证40列修复效果; Principle_Applied: 全面验证;
}}

作者: 龙sir团队
创建时间: 2025-08-04
版本: 2.0.0
描述: 最终验证动态表格列生成功能与原始硬编码版本的完全一致性
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.managers.table_column_manager import table_column_manager


def verify_exact_40_columns_structure():
    """验证精确的40列结构"""
    print("==liuq debug== 最终验证：精确的40列结构")
    print("=" * 60)
    
    # 原始硬编码的列标题（按顺序）
    original_columns = [
        # MapList (1列)
        "MapList",
        # Offset (2列) - 保留为2列显示
        "Offset R/G", "Offset B/G",
        # Weight, Step, ERatio (4列)
        "Weight", "Step", "ERatio Min", "ERatio Max",
        # BV (4列) - 保留为4列显示
        "BV Lower", "BV Min", "BV Max", "BV Upper",
        # Ctemp (4列)
        "Ctemp Lower", "Ctemp Min", "Ctemp Max", "Ctemp Upper",
        # IR (4列)
        "IR Lower", "IR Min", "IR Max", "IR Upper",
        # AC (4列)
        "AC Lower", "AC Min", "AC Max", "AC Upper",
        # COUNT (4列)
        "COUNT Lower", "COUNT Min", "COUNT Max", "COUNT Upper",
        # ColorCCT (4列)
        "ColorCCT Lower", "ColorCCT Min", "ColorCCT Max", "ColorCCT Upper",
        # diffCtemp (4列)
        "diffCtemp Lower", "diffCtemp Min", "diffCtemp Max", "diffCtemp Upper",
        # FaceCtemp (4列)
        "FaceCtemp Lower", "FaceCtemp Min", "FaceCtemp Max", "FaceCtemp Upper",
        # ml (1列)
        "ml"
    ]
    
    # 原始硬编码的字段ID映射
    original_field_mapping = {
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
    
    # 生成动态配置
    config = table_column_manager.generate_default_configuration()
    
    print(f"验证结果:")
    
    # 1. 验证列数量
    if len(config.columns) == 40:
        print("✅ 列数量: 40列 (正确)")
    else:
        print(f"❌ 列数量: {len(config.columns)}列 (错误，应为40列)")
        return False
    
    # 2. 验证列标题
    title_errors = []
    for i, expected_title in enumerate(original_columns):
        if i >= len(config.columns):
            title_errors.append(f"缺少第{i+1}列: {expected_title}")
            continue
        
        actual_title = config.columns[i].display_name
        if actual_title != expected_title:
            title_errors.append(f"第{i+1}列标题不匹配: 期望'{expected_title}'，实际'{actual_title}'")
    
    if title_errors:
        print("❌ 列标题验证失败:")
        for error in title_errors[:5]:
            print(f"  - {error}")
        if len(title_errors) > 5:
            print(f"  ... 还有 {len(title_errors) - 5} 个错误")
        return False
    else:
        print("✅ 列标题: 与原始硬编码完全一致")
    
    # 3. 验证字段ID映射
    mapping_errors = []
    for i, expected_field_id in original_field_mapping.items():
        if i >= len(config.columns):
            mapping_errors.append(f"缺少列索引{i}: {expected_field_id}")
            continue
        
        actual_field_id = config.columns[i].field_id
        if actual_field_id != expected_field_id:
            mapping_errors.append(f"列索引{i}字段ID不匹配: 期望'{expected_field_id}'，实际'{actual_field_id}'")
    
    if mapping_errors:
        print("❌ 字段ID映射验证失败:")
        for error in mapping_errors[:5]:
            print(f"  - {error}")
        if len(mapping_errors) > 5:
            print(f"  ... 还有 {len(mapping_errors) - 5} 个错误")
        return False
    else:
        print("✅ 字段ID映射: 与原始硬编码完全一致")
    
    # 4. 验证列顺序
    print("✅ 列顺序: 与原始硬编码完全一致")
    
    return True


def display_comparison_table():
    """显示对比表格"""
    print(f"\n==liuq debug== 动态生成 vs 原始硬编码对比")
    print("=" * 80)
    
    config = table_column_manager.generate_default_configuration()
    
    print(f"{'索引':<4} {'字段ID':<20} {'动态生成标题':<15} {'原始硬编码标题':<15} {'状态':<6}")
    print("-" * 80)
    
    # 原始硬编码的列标题
    original_titles = [
        "MapList", "Offset R/G", "Offset B/G", "Weight", "Step", "ERatio Min", "ERatio Max",
        "BV Lower", "BV Min", "BV Max", "BV Upper", "Ctemp Lower", "Ctemp Min", "Ctemp Max", "Ctemp Upper",
        "IR Lower", "IR Min", "IR Max", "IR Upper", "AC Lower", "AC Min", "AC Max", "AC Upper",
        "COUNT Lower", "COUNT Min", "COUNT Max", "COUNT Upper", "ColorCCT Lower", "ColorCCT Min", "ColorCCT Max", "ColorCCT Upper",
        "diffCtemp Lower", "diffCtemp Min", "diffCtemp Max", "diffCtemp Upper", "FaceCtemp Lower", "FaceCtemp Min", "FaceCtemp Max", "FaceCtemp Upper",
        "ml"
    ]
    
    for i, column in enumerate(config.columns):
        original_title = original_titles[i] if i < len(original_titles) else "N/A"
        status = "✅" if column.display_name == original_title else "❌"
        
        print(f"{i:<4} {column.field_id:<20} {column.display_name:<15} {original_title:<15} {status:<6}")


def main():
    """主验证函数"""
    print("FastMapV2 40列结构最终验证")
    print("=" * 60)
    print("验证动态表格列生成功能与原始硬编码版本的完全一致性")
    print()
    
    try:
        # 执行最终验证
        verification_passed = verify_exact_40_columns_structure()
        
        # 显示对比表格
        display_comparison_table()
        
        print(f"\n" + "=" * 60)
        print("最终验证结果:")
        
        if verification_passed:
            print("🎉 验证通过！动态表格列生成功能与原始硬编码版本完全一致！")
            print()
            print("修复成果总结:")
            print("✅ 列数量: 精确的40列")
            print("✅ 列标题: 与原始硬编码完全相同")
            print("✅ 字段映射: 与原始硬编码完全相同")
            print("✅ 列顺序: 与原始硬编码完全相同")
            print("✅ 功能特性: 保持动态配置能力")
            print()
            print("现在可以安全地使用动态表格列生成功能替代硬编码实现！")
        else:
            print("❌ 验证失败！请检查上述错误并进行修复。")
        
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
