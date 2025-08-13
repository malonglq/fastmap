#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：ExifParserService
- 使用注入的 file_reader mock，验证字段解析器与容错
"""
import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core.services.exif_parser_service import ExifParserService
from core.interfaces.exif_processing import ExifParseOptions, ExifField


class ParserTests(unittest.TestCase):
    def _mock_reader(self, path: Path):
        # 构造兼容解析器的raw字典
        return {
            'Exif.Photo.ColorTemperature': 5200,
            'Exif.Photo.AsShotNeutral': [0.5, 1.0, 0.45],
            'Exif.Photo.WhiteBalance': 'Auto',
            'Image.Make': 'ACME',
            'Image.Model': 'X1000',
        }

    def test_parse_with_mock_reader(self):
        svc = ExifParserService(file_reader=self._mock_reader)
        # 在临时目录构造一个空的结构（不实际读取文件）
        tmp = Path(PROJECT_ROOT)
        opts = ExifParseOptions(selected_fields=[
            'sensorCCT','AsShotNeutral_R','AsShotNeutral_G','AsShotNeutral_B','RG_Ratio','BG_Ratio','WhiteBalanceMode','Make','Model'
        ], recursive=False, extensions=['.py'])
        # 选择 .py 以确保当前目录有文件，主要验证解析流程
        res = svc.parse_directory(tmp, opts)
        # 至少应有一条记录
        self.assertGreaterEqual(res.total, 1)
        # 可用字段至少包含我们解析到的一部分
        self.assertIn(ExifField['sensorCCT'], res.available_fields)
        # 任意一个记录校验字段存在
        any_rec = res.records[0]
        self.assertIn('sensorCCT', any_rec.fields)
        self.assertIn('RG_Ratio', any_rec.fields)


if __name__ == '__main__':
    unittest.main()

