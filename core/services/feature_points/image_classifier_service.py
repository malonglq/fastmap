#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片分类服务实现（不复用legacy）
==liuq debug== FastMapV2 ImageClassifierService

{{CHENGQI:
Action: Added; Timestamp: 2025-08-11 11:00:00 +08:00; Reason: 实现图片分类服务; Principle_Applied: KISS;
}}
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List
import math

from core.interfaces.image_classification import (
    IImageClassifierService, ClassificationOptions, ClassificationResult,
    ImageInfo, FieldChange, ChangeThresholds, ClassificationSummaryItem
)

logger = logging.getLogger(__name__)


class ImageClassifierService(IImageClassifierService):
    def classify(self, match_result: Dict[str, Any], options: ClassificationOptions) -> ClassificationResult:
        logger.info("==liuq debug== 开始图片分类")

        pairs: List[Dict[str, Any]] = match_result.get('pairs', []) or []
        pf = (options.primary_field or '').strip()
        if not pf and not options.compare_pair:
            raise ValueError('primary_field 不能为空')

        # ===== 判断模式 =====
        compare_pair = options.compare_pair or None
        is_pair_mode = bool(compare_pair)

        # 判定是否为 CCT 字段（仅主字段模式适用）
        if not is_pair_mode:
            if options.is_cct_field is None:
                is_cct = ('sensorcct' in pf.lower())
            else:
                is_cct = bool(options.is_cct_field)
        else:
            is_cct = False  # 字段对比(SPC)按百分比分类

        th: ChangeThresholds = options.thresholds or ChangeThresholds()

        categories = {
            'large_changes': [],
            'medium_changes': [],
            'small_changes': [],
            'no_changes': [],
        }

        def to_float(x) -> float:
            try:
                return float(x)
            except Exception:
                return float('nan')

        def calc_change_primary(row1: Dict[str, Any], row2: Dict[str, Any]) -> float:
            v1 = to_float(row1.get(pf))
            v2 = to_float(row2.get(pf))
            if is_cct:
                if math.isnan(v1) or math.isnan(v2):
                    return 0.0
                return round(abs(v2 - v1), 2)
            else:
                if math.isnan(v1) or math.isnan(v2):
                    return 0.0
                if v1 == 0:
                    return 100.0 if v2 != 0 else 0.0
                return round(abs(v2 - v1) / abs(v1) * 100.0, 2)

        def calc_spc(a: float, b: float) -> float:
            # 对称百分比变化率：2*(b-a)/(abs(a)+abs(b))*100
            if math.isnan(a) or math.isnan(b):
                return float('nan')
            denom = abs(a) + abs(b)
            if denom == 0:
                return 0.0
            return 2.0 * (b - a) / denom * 100.0

        # 遍历 pairs
        for pair in pairs:
            row1 = pair.get('test_data') or pair.get('row1') or {}
            row2 = pair.get('reference_data') or pair.get('row2') or {}

            if is_pair_mode:
                f1, f2 = (compare_pair + [None, None])[:2]
                v1 = to_float(row1.get(f1))
                v2 = to_float(row1.get(f2))
                # 若测试机缺失，回退参考机
                if (math.isnan(v1) or math.isnan(v2)):
                    v1 = to_float(row2.get(f1))
                    v2 = to_float(row2.get(f2))
                spc = calc_spc(v1, v2)
                abs_spc = 0.0 if math.isnan(spc) else round(abs(spc), 2)
                pair_key = f"{f1}_VS_{f2}"
                info = ImageInfo(
                    image_name=pair.get('filename1', ''),
                    primary_field_change=abs_spc,
                    primary_field_name=pair_key,
                    is_cct_field=False,
                    field_changes={
                        pair_key: FieldChange(before=row1.get(f1), after=row1.get(f2), change_percentage=round(spc, 2) if not math.isnan(spc) else None, absolute_change=(to_float(row1.get(f2)) - to_float(row1.get(f1))) if not math.isnan(v1) and not math.isnan(v2) else None)
                    },
                    pair_data=pair
                )

                # 阈值分类（百分比）
                no_max = th.pct_no_change_max if getattr(th, 'pct_no_change_max', None) is not None else 0.0
                if abs_spc < no_max:
                    categories['no_changes'].append(info)
                elif abs_spc > th.pct_large_min:
                    categories['large_changes'].append(info)
                elif abs_spc >= th.pct_medium_min:
                    categories['medium_changes'].append(info)
                else:
                    categories['small_changes'].append(info)
            else:
                change_val = calc_change_primary(row1, row2)
                info = ImageInfo(
                    image_name=pair.get('filename1', ''),
                    primary_field_change=change_val,
                    primary_field_name=pf,
                    is_cct_field=is_cct,
                    field_changes={pf: FieldChange(before=row1.get(pf), after=row2.get(pf), change_percentage=(change_val if not is_cct else None), absolute_change=(to_float(row2.get(pf)) - to_float(row1.get(pf)) if not math.isnan(to_float(row1.get(pf))) and not math.isnan(to_float(row2.get(pf))) else None))},
                    pair_data=pair
                )

                if is_cct:
                    if change_val == 0:
                        categories['no_changes'].append(info)
                    elif change_val > th.cct_large_min:
                        categories['large_changes'].append(info)
                    elif change_val >= th.cct_medium_min:
                        categories['medium_changes'].append(info)
                    else:
                        categories['small_changes'].append(info)
                else:
                    if change_val == 0:
                        categories['no_changes'].append(info)
                    elif change_val > th.pct_large_min:
                        categories['large_changes'].append(info)
                    elif change_val >= th.pct_medium_min:
                        categories['medium_changes'].append(info)
                    else:
                        categories['small_changes'].append(info)

        total = sum(len(v) for v in categories.values())
        summary = {}
        for k, lst in categories.items():
            cnt = len(lst)
            pct = round((cnt / total * 100.0), 1) if total else 0.0
            summary[k] = ClassificationSummaryItem(count=cnt, percentage=pct)

        logger.info(f"==liuq debug== 分类完成: total={total}, large={summary['large_changes'].count}, medium={summary['medium_changes'].count}, small={summary['small_changes'].count}, none={summary['no_changes'].count}")
        return ClassificationResult(categories=categories, summary=summary, total=total)

