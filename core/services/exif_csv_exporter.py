#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF CSV 导出器
==liuq debug== FastMapV2 ExifCsvExporter

{{CHENGQI:
Action: Added; Timestamp: 2025-08-11 12:28:00 +08:00; Reason: 新增EXIF CSV导出器; Principle_Applied: KISS;
}}
"""
from __future__ import annotations
from pathlib import Path
from typing import List
import csv
from datetime import datetime

from core.interfaces.exif_processing import IExifCsvExporter, ExifParseResult


class ExifCsvExporter(IExifCsvExporter):
    def export_csv(
        self,
        result: ExifParseResult,
        csv_path: Path,
        selected_fields: List[str],
        include_source_columns: bool = False,
        include_raw_json: bool = False,
        include_timestamp: bool = False,
        include_image_path: bool = False,
    ) -> Path:
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # 默认表头：仅 image_name + 选中字段；附加列通过开关控制
        headers = ['image_name']
        if include_timestamp:
            headers.insert(0, 'timestamp')
        if include_image_path:
            headers.append('image_path')
        for f in selected_fields:
            headers.append(f)
            if include_source_columns:
                headers.append(f"{f}__source")
        if include_raw_json:
            headers.append('raw_json')

        try:
            with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                for rec in result.records:
                    row = {
                        'image_name': rec.image_name,
                    }
                    if include_timestamp:
                        ts = datetime.fromtimestamp(rec.image_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        row['timestamp'] = ts
                    if include_image_path:
                        row['image_path'] = str(rec.image_path)
                    for k in selected_fields:
                        # 仅使用解析阶段命中的字段；未命中写空
                        row[k] = rec.fields.get(k, '')
                        if include_source_columns:
                            row[f"{k}__source"] = rec.field_sources.get(k, '')
                    if include_raw_json:
                        import json as _json
                        row['raw_json'] = _json.dumps(getattr(rec, 'raw_json', {}) or {}, ensure_ascii=False)
                    writer.writerow(row)
        except Exception as e:
            # ==liuq debug== 捕获文件被占用或权限问题，抛出更友好信息
            raise RuntimeError(f"写入CSV失败: {e}. 请确认文件未被占用且具有写入权限")
        return csv_path

