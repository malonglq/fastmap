#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：导出重命名后缀格式
- 百分比：字段名 + 正负号 + 保留两位小数 + %
- CCT：字段名 + 正负号 + 整数 + K
- 无变化：保持原名
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
import unittest

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core.services.image_export_service import ImageExportService
from core.interfaces.image_classification import (
    NamingOptions,
    ImageInfo,
    FieldChange,
    ClassificationResult,
    ClassificationSummaryItem,
    ExportSelection,
)


class TestImageExportNaming(unittest.TestCase):
    def setUp(self):
        self.exporter = ImageExportService()
        self.naming = NamingOptions()
        self.tmp_src = Path(tempfile.mkdtemp(prefix="fastmapv2_src_"))
        self.tmp_out = Path(tempfile.mkdtemp(prefix="fastmapv2_out_"))
        # 创建空白源图片
        for name in ["p1.jpg", "p2.jpg", "c1.jpg", "n1.jpg"]:
            (self.tmp_src / name).write_bytes(b"test")

    def tearDown(self):
        shutil.rmtree(self.tmp_src, ignore_errors=True)
        shutil.rmtree(self.tmp_out, ignore_errors=True)

    def test__add_suffix_percent_sign_and_field(self):
        fn = self.exporter._add_suffix(
            "img.jpg", "SGW_Gray", False, 10.5, 1.23, self.naming
        )
        self.assertEqual(fn, "img_SGW_Gray+10.50%.jpg")

    def test__add_suffix_percent_negative(self):
        fn = self.exporter._add_suffix(
            "img.jpg", "SGW_Gray", False, 0.5, -0.5, self.naming
        )
        self.assertEqual(fn, "img_SGW_Gray-0.50%.jpg")

    def test__add_suffix_cct_positive_and_negative(self):
        fn_pos = self.exporter._add_suffix(
            "img.jpg", "sensorCCT", True, 250, 250.0, self.naming
        )
        fn_neg = self.exporter._add_suffix(
            "img.jpg", "sensorCCT", True, 250, -250.0, self.naming
        )
        self.assertEqual(fn_pos, "img_sensorCCT+250K.jpg")
        self.assertEqual(fn_neg, "img_sensorCCT-250K.jpg")

    def test__add_suffix_no_change_keep_original(self):
        fn = self.exporter._add_suffix(
            "img.jpg", "SGW_Gray", False, 0.0, 0.0, self.naming
        )
        self.assertEqual(fn, "img.jpg")

    def test_export_flow_generates_expected_names(self):
        # 构造分类结果
        def item(image, field, is_cct, pct_or_abs, diff):
            return ImageInfo(
                image_name=image,
                primary_field_change=pct_or_abs,
                primary_field_name=field,
                is_cct_field=is_cct,
                field_changes={
                    field: FieldChange(before=0, after=0, change_percentage=(pct_or_abs if not is_cct else None), absolute_change=diff)
                },
                pair_data={},
            )

        categories = {
            "large_changes": [item("p1.jpg", "SGW_Gray", False, 10.5, 2.1)],
            "medium_changes": [item("p2.jpg", "SGW_Gray", False, 0.5, -0.5)],
            "small_changes": [item("c1.jpg", "sensorCCT", True, 250.0, -250.0)],
            "no_changes": [item("n1.jpg", "SGW_Gray", False, 0.0, 0.0)],
        }
        summary = {
            k: ClassificationSummaryItem(count=len(v), percentage=100.0 if len(v) else 0.0)
            for k, v in categories.items()
        }
        cls = ClassificationResult(categories=categories, summary=summary, total=sum(len(v) for v in categories.values()))

        selection = ExportSelection(True, True, True, True)

        stats = self.exporter.export(cls, selection, self.tmp_src, self.tmp_out, self.naming)
        self.assertEqual(stats.total_copied, 4)

        # 验证文件存在且名称正确
        self.assertTrue((self.tmp_out / "1_large_changes" / "p1_SGW_Gray+10.50%.jpg").exists())
        self.assertTrue((self.tmp_out / "2_medium_changes" / "p2_SGW_Gray-0.50%.jpg").exists())
        self.assertTrue((self.tmp_out / "3_small_changes" / "c1_sensorCCT-250K.jpg").exists())
        self.assertTrue((self.tmp_out / "4_no_changes" / "n1.jpg").exists())


if __name__ == "__main__":
    unittest.main()

