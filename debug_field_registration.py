#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试字段注册系统
==liuq debug== 分析为什么注册了46个字段而不是40个

{{CHENGQI:
Action: Added; Timestamp: 2025-08-04 18:25:00 +08:00; Reason: 分析字段注册问题根源; Principle_Applied: 问题根因分析;
}}
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.services.shared.field_registry_service import field_registry


def analyze_field_registration():
    """分析字段注册情况"""
    print("==liuq debug== 字段注册系统分析")
    print("=" * 60)
    
    # 获取所有注册的字段
    all_fields = field_registry.get_all_fields()
    
    print(f"总注册字段数量: {len(all_fields)}")
    print()
    
    # 原始40列的字段ID列表（按顺序）
    original_40_fields = [
        'alias_name',           # MapList
        'offset_x',             # Offset R/G
        'offset_y',             # Offset B/G
        'weight',               # Weight
        'trans_step',           # Step
        'e_ratio_min',          # ERatio Min
        'e_ratio_max',          # ERatio Max
        'tran_bv_min',          # BV Lower
        'bv_min',               # BV Min
        'bv_max',               # BV Max
        'tran_bv_max',          # BV Upper
        'tran_ctemp_min',       # Ctemp Lower
        'ctemp_min',            # Ctemp Min
        'ctemp_max',            # Ctemp Max
        'tran_ctemp_max',       # Ctemp Upper
        'tran_ir_min',          # IR Lower
        'ir_min',               # IR Min
        'ir_max',               # IR Max
        'tran_ir_max',          # IR Upper
        'tran_ac_min',          # AC Lower
        'ac_min',               # AC Min
        'ac_max',               # AC Max
        'tran_ac_max',          # AC Upper
        'tran_count_min',       # COUNT Lower
        'count_min',            # COUNT Min
        'count_max',            # COUNT Max
        'tran_count_max',       # COUNT Upper
        'tran_color_cct_min',   # ColorCCT Lower
        'color_cct_min',        # ColorCCT Min
        'color_cct_max',        # ColorCCT Max
        'tran_color_cct_max',   # ColorCCT Upper
        'tran_diff_ctemp_min',  # diffCtemp Lower
        'diff_ctemp_min',       # diffCtemp Min
        'diff_ctemp_max',       # diffCtemp Max
        'tran_diff_ctemp_max',  # diffCtemp Upper
        'tran_face_ctemp_min',  # FaceCtemp Lower
        'face_ctemp_min',       # FaceCtemp Min
        'face_ctemp_max',       # FaceCtemp Max
        'tran_face_ctemp_max',  # FaceCtemp Upper
        'ml',                   # ml
    ]
    
    print("注册的字段列表:")
    print("-" * 60)
    
    registered_field_ids = []
    for i, field in enumerate(all_fields):
        is_in_original = field.field_id in original_40_fields
        status = "✅ 核心" if is_in_original else "❓ 额外"
        print(f"{i+1:2d}. {field.field_id:<25} {field.display_name:<20} {status}")
        registered_field_ids.append(field.field_id)
    
    print()
    print("分析结果:")
    print("-" * 60)
    
    # 找出额外的字段
    extra_fields = [fid for fid in registered_field_ids if fid not in original_40_fields]
    missing_fields = [fid for fid in original_40_fields if fid not in registered_field_ids]
    
    print(f"原始40列字段数量: {len(original_40_fields)}")
    print(f"当前注册字段数量: {len(registered_field_ids)}")
    print(f"额外字段数量: {len(extra_fields)}")
    print(f"缺失字段数量: {len(missing_fields)}")
    
    if extra_fields:
        print(f"\n额外的字段 ({len(extra_fields)}个):")
        for field_id in extra_fields:
            field = field_registry.get_field(field_id)
            print(f"  - {field_id}: {field.display_name if field else 'Unknown'}")
    
    if missing_fields:
        print(f"\n缺失的字段 ({len(missing_fields)}个):")
        for field_id in missing_fields:
            print(f"  - {field_id}")
    
    return extra_fields, missing_fields


def main():
    """主函数"""
    print("FastMapV2 字段注册系统分析")
    print("=" * 60)
    print("分析为什么注册了46个字段而不是40个")
    print()
    
    try:
        extra_fields, missing_fields = analyze_field_registration()
        
        print(f"\n" + "=" * 60)
        print("结论:")
        
        if len(extra_fields) == 6 and len(missing_fields) == 0:
            print("✅ 找到问题根源：注册了6个额外字段")
            print("💡 解决方案：在字段注册时添加'核心字段'标记")
        elif missing_fields:
            print("❌ 发现缺失字段，需要补充注册")
        else:
            print("🤔 字段注册情况与预期不符，需要进一步分析")
        
    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
