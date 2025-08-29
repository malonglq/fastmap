#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原始 EXIF JSON 导出器
==liuq debug== FastMapV2 ExifRawExporter

{{CHENGQI:
Action: Added; Timestamp: 2025-08-11 14:05:00 +08:00; Reason: 支持导出原始EXIF JSON以便验证; Principle_Applied: KISS;
}}
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import json

from core.interfaces.exif_processing import ExifParseResult, IExifRawExporter


class ExifRawExporter(IExifRawExporter):
    def export_raw_json(self, result: ExifParseResult, out_path: Path) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # 采用 JSON Lines 便于大文件查看
        with out_path.open('w', encoding='utf-8') as f:
            for rec in result.records:
                obj: Any = {
                    'image_name': rec.image_name,
                    'image_path': str(rec.image_path),
                    'raw': rec.raw_json or {},
                }
                f.write(json.dumps(obj, ensure_ascii=False))
                f.write("\n")
        return out_path

