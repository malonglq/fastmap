#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片分类导出工作流服务（薄门面）
==liuq debug== FastMapV2 ImageExportWorkflowService

{{CHENGQI:
Action: Added; Timestamp: 2025-08-11 12:00:00 +08:00; Reason: 引入公共门面封装分类/统计卡片/导出; Principle_Applied: KISS, SOLID-ISP;
}}
"""
from __future__ import annotations
from typing import Any, Dict, Optional, Callable, List

from core.interfaces.image_classification import (
    IImageExportWorkflowService,
    IImageClassifierService,
    IImageExportService,
    ClassificationOptions,
    ClassificationResult,
    ExportSelection,
    NamingOptions,
    ExportStats,
    StatsPanel,
    StatsCardItem,
)
from core.services.feature_points.image_classifier_service import ImageClassifierService
from core.services.exif_processing.image_export_service import ImageExportService


class ImageExportWorkflowService(IImageExportWorkflowService):
    def __init__(self,
                 classifier: Optional[IImageClassifierService] = None,
                 exporter: Optional[IImageExportService] = None):
        self.classifier = classifier or ImageClassifierService()
        self.exporter = exporter or ImageExportService()

    # 1) 分类
    def compute_classification(self, match_result: Dict[str, Any], options: ClassificationOptions) -> ClassificationResult:
        return self.classifier.classify(match_result, options)

    # 2) 统计面板构建
    def build_stats_panel(self, result: ClassificationResult) -> StatsPanel:
        total = result.total or 0
        # 固定映射：key -> (title, color)
        mapping: Dict[str, tuple] = {
            'large_changes': ('大变化', '#e74c3c'),
            'medium_changes': ('中变化', '#f39c12'),
            'small_changes': ('小变化', '#27ae60'),
            'no_changes': ('无变化', '#7f8c8d'),
        }
        # 推断主字段与是否 CCT（从随便一个类别中的第一项取样）
        pf = ''
        is_cct = False
        for k in ('large_changes', 'medium_changes', 'small_changes', 'no_changes'):
            lst = result.categories.get(k) or []
            if lst:
                pf = getattr(lst[0], 'primary_field_name', '')
                is_cct = bool(getattr(lst[0], 'is_cct_field', False))
                break

        cards: List[StatsCardItem] = []
        # 总计卡片
        cards.append(StatsCardItem(key='total', title='总计', count=total, percentage=100.0 if total else 0.0, color='#2c3e50'))
        # 其余四类
        for key in ['large_changes', 'medium_changes', 'small_changes', 'no_changes']:
            s = result.summary.get(key)
            cnt = s.count if s else 0
            pct = s.percentage if s else 0.0
            title, color = mapping[key]
            cards.append(StatsCardItem(key=key, title=title, count=cnt, percentage=pct, color=color))

        return StatsPanel(cards=cards, total=total, primary_field=pf, is_cct_field=is_cct)

    # 3) 导出
    def export_images(self,
                      result: ClassificationResult,
                      selection: ExportSelection,
                      source_dir,
                      output_dir,
                      naming: NamingOptions,
                      progress_cb: Optional[Callable] = None) -> ExportStats:
        return self.exporter.export(result, selection, source_dir, output_dir, naming, progress_cb=progress_cb)

