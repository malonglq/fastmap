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
        if not pf:
            raise ValueError('primary_field 不能为空')

        # 判定是否为 CCT 字段
        if options.is_cct_field is None:
            is_cct = ('sensorcct' in pf.lower())
        else:
            is_cct = bool(options.is_cct_field)

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

        def calc_change(row1: Dict[str, Any], row2: Dict[str, Any]) -> float:
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

        def calc_field_changes(row1: Dict[str, Any], row2: Dict[str, Any]) -> Dict[str, FieldChange]:
            result: Dict[str, FieldChange] = {}
            for f in options.selected_fields or []:
                v1 = to_float(row1.get(f))
                v2 = to_float(row2.get(f))
                if math.isnan(v1) or math.isnan(v2):
                    result[f] = FieldChange(before=row1.get(f), after=row2.get(f), change_percentage=None, absolute_change=None)
                else:
                    pct = 100.0 if (v1 == 0 and v2 != 0) else (abs(v2 - v1) / abs(v1) * 100.0 if v1 != 0 else 0.0)
                    diff = v2 - v1
                    result[f] = FieldChange(before=row1.get(f), after=row2.get(f), change_percentage=round(pct, 2), absolute_change=round(diff, 4))
            return result

        # 遍历 pairs
        for pair in pairs:
            row1 = pair.get('test_data') or pair.get('row1') or {}
            row2 = pair.get('reference_data') or pair.get('row2') or {}
            change_val = calc_change(row1, row2)

            info = ImageInfo(
                image_name=pair.get('filename1', ''),
                primary_field_change=change_val,
                primary_field_name=pf,
                is_cct_field=is_cct,
                field_changes=calc_field_changes(row1, row2),
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

