#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：工作流服务编排
- 验证 compute_classification 调用分类器
- 验证 build_stats_panel 卡片映射
- 验证 export_images 调用导出服务
"""
import sys
from pathlib import Path
import unittest

# 项目根入路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core.services.image_export_workflow_service import ImageExportWorkflowService
from core.interfaces.image_classification import (
    ClassificationResult, ClassificationSummaryItem, ImageInfo,
    ExportSelection, NamingOptions
)


class DummyClassifier:
    def __init__(self, result):
        self._result = result
        self.called = 0
    def classify(self, match_result, options):
        self.called += 1
        return self._result


class DummyExporter:
    def __init__(self):
        self.called = 0
    def export(self, classification, selection, source_dir, output_dir, naming, progress_cb=None):
        self.called += 1
        class S: pass
        s = S()
        s.total_copied = 42
        s.missing_files = []
        return s


class WorkflowTests(unittest.TestCase):
    def _sample_result(self):
        # 构造一个简易的 ClassificationResult
        info = ImageInfo(
            image_name='a.jpg',
            primary_field_change=12.3,
            primary_field_name='sgw_gray',
            is_cct_field=False,
            field_changes={},
            pair_data={},
        )
        summary = {
            'large_changes': ClassificationSummaryItem(count=1, percentage=50.0),
            'medium_changes': ClassificationSummaryItem(count=0, percentage=0.0),
            'small_changes': ClassificationSummaryItem(count=1, percentage=50.0),
            'no_changes': ClassificationSummaryItem(count=0, percentage=0.0),
        }
        cats = {
            'large_changes': [info], 'medium_changes': [], 'small_changes': [], 'no_changes': []
        }
        return ClassificationResult(categories=cats, summary=summary, total=2)

    def test_workflow_calls_and_panel(self):
        result = self._sample_result()
        clf = DummyClassifier(result)
        exp = DummyExporter()
        wf = ImageExportWorkflowService(classifier=clf, exporter=exp)

        # compute_classification
        out = wf.compute_classification({'pairs': []}, None)  # options 未在 Dummy 使用
        self.assertIs(out, result)
        self.assertEqual(clf.called, 1)

        # build_stats_panel
        panel = wf.build_stats_panel(result)
        self.assertEqual(panel.total, 2)
        # total + 4 类
        self.assertEqual(len(panel.cards), 5)
        # 含有 large_changes 卡
        keys = [c.key for c in panel.cards]
        self.assertIn('large_changes', keys)

        # export_images
        s = wf.export_images(result, ExportSelection(True, True, True, True), Path('.'), Path('.'), NamingOptions())
        self.assertEqual(exp.called, 1)
        self.assertEqual(getattr(s, 'total_copied', 0), 42)


if __name__ == '__main__':
    unittest.main()

