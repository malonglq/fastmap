#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：ExifCsvExporter
- 验证动态列与空值输出
"""
import sys
from pathlib import Path
import tempfile
import shutil
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core.services.exif_csv_exporter import ExifCsvExporter
from core.interfaces.exif_processing import ExifParseResult, ExifRecord


class CsvExporterTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_export_basic(self):
        # 构造一个最小结果
        img = self.tmpdir / 'a.jpg'
        img.write_bytes(b'fake')
        rec = ExifRecord(image_path=img, image_name='a.jpg', fields={'sensorCCT': 5000, 'RG_Ratio': 1.1})
        result = ExifParseResult(records=[rec], total=1)

        csvf = self.tmpdir / 'out.csv'
        exporter = ExifCsvExporter()
        path = exporter.export_csv(result, csvf, selected_fields=['sensorCCT','RG_Ratio','BG_Ratio'])

        # 验证文件存在与内容列头
        self.assertTrue(path.exists())
        txt = path.read_text(encoding='utf-8-sig')
        self.assertIn('timestamp,image_name,image_path,sensorCCT,RG_Ratio,BG_Ratio', txt.splitlines()[0])
        # 验证空值: BG_Ratio 未提供应为空
        self.assertTrue(txt.splitlines()[1].endswith(',1.1,'))


if __name__ == '__main__':
    unittest.main()

