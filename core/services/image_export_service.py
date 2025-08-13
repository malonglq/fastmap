#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片导出服务实现（不复用legacy）
==liuq debug== FastMapV2 ImageExportService

{{CHENGQI:
Action: Added; Timestamp: 2025-08-11 11:05:00 +08:00; Reason: 实现图片导出服务; Principle_Applied: KISS;
}}
"""
from __future__ import annotations
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, Optional

from core.interfaces.image_classification import (
    IImageExportService, ClassificationResult, ExportSelection, NamingOptions, ExportStats
)

logger = logging.getLogger(__name__)


class ImageExportService(IImageExportService):
    CATEGORY_DIRS = {
        'large_changes': '1_large_changes',
        'medium_changes': '2_medium_changes',
        'small_changes': '3_small_changes',
        'no_changes': '4_no_changes',
    }

    def export(self,
               classification: ClassificationResult,
               selection: ExportSelection,
               source_dir: Path,
               output_dir: Path,
               naming: NamingOptions,
               progress_cb: Optional[callable] = None) -> ExportStats:
        start = time.time()
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建类别目录
        category_dirs: Dict[str, Path] = {}
        for key, sub in self.CATEGORY_DIRS.items():
            d = output_dir / sub
            d.mkdir(parents=True, exist_ok=True)
            category_dirs[key] = d

        chosen = []
        if selection.export_large: chosen.append('large_changes')
        if selection.export_medium: chosen.append('medium_changes')
        if selection.export_small: chosen.append('small_changes')
        if selection.export_no_change: chosen.append('no_changes')

        copied_counts = {k:0 for k in self.CATEGORY_DIRS.keys()}
        missing_files = []

        # 遍历导出
        total_items = sum(len(classification.categories.get(k, [])) for k in chosen)
        processed = 0

        for cat in chosen:
            items = classification.categories.get(cat, [])
            for info in items:
                ok = self._copy_single(info, source_dir, category_dirs[cat], naming)
                if ok:
                    copied_counts[cat] += 1
                else:
                    missing_files.append(info.image_name)
                processed += 1
                if progress_cb:
                    progress_cb(int(processed/ max(total_items,1) * 100), f"复制 {processed}/{total_items}")

        end = time.time()
        total_copied = sum(copied_counts.values())
        return ExportStats(
            started_at=start,
            finished_at=end,
            duration_seconds=round(end-start,2),
            copied_counts=copied_counts,
            total_copied=total_copied,
            missing_files=missing_files,
            chosen_categories=chosen,
        )

    # 简单文件查找策略（大小写/扩展名/常见尾缀）
    def _find_file(self, dir_path: Path, image_name: str) -> Optional[Path]:
        name = image_name
        p = dir_path / name
        if p.exists():
            return p
        # 大小写
        for candidate in dir_path.glob(name):
            if candidate.exists():
                return candidate
        # 扩展名尝试
        stem = Path(name).stem
        for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            q = dir_path / f"{stem}{ext}"
            if q.exists():
                return q
        # _ori/-ori 变体
        variants = []
        if stem.lower().endswith('_ori'):
            variants.append(stem[:-4])
        else:
            variants.append(stem + '_ori')
        if stem.lower().endswith('-ori'):
            variants.append(stem[:-4])
        else:
            variants.append(stem + '-ori')
        for v in variants:
            for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
                q = dir_path / f"{v}{ext}"
                if q.exists():
                    return q
        return None

    def _resolve_conflict(self, target: Path) -> Path:
        if not target.exists():
            return target
        stem = target.stem
        suffix = target.suffix
        idx = 1
        while True:
            cand = target.with_name(f"{stem}({idx}){suffix}")
            if not cand.exists():
                return cand
            idx += 1

    def _add_suffix(self, filename: str, field_name: str, is_cct: bool, abs_percent_or_abs: float, signed_diff: Optional[float], naming: NamingOptions) -> str:
        # 无变化：保持原名
        if abs_percent_or_abs == 0 or (signed_diff is not None and signed_diff == 0):
            return filename
        p = Path(filename)
        # 方向符号（默认正号，若有符号差值则据此判断）
        sign = "+" if (signed_diff is None or signed_diff > 0) else "-"
        field = (field_name or "").strip()
        if is_cct:
            value = int(round(abs(signed_diff if signed_diff is not None else abs_percent_or_abs)))
            suffix = naming.cct_format.format(field=field, sign=sign, value=value)
        else:
            value = abs_percent_or_abs if abs_percent_or_abs is not None else 0.0
            suffix = naming.percent_format.format(field=field, sign=sign, value=value)
        return f"{p.stem}{suffix}{p.suffix}"

    def _copy_single(self, info, source_dir: Path, target_dir: Path, naming: NamingOptions) -> bool:
        try:
            src = self._find_file(source_dir, info.image_name)
            if not src:
                logger.warning(f"==liuq debug== 未找到图片文件: {info.image_name}")
                return False
            fc = info.field_changes.get(info.primary_field_name) if hasattr(info, 'field_changes') else None
            signed_diff = fc.absolute_change if fc else None
            target_name = self._add_suffix(
                src.name,
                info.primary_field_name,
                info.is_cct_field,
                info.primary_field_change,
                signed_diff,
                naming
            )
            dst = target_dir / target_name
            dst = self._resolve_conflict(dst)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            logger.error(f"==liuq debug== 复制失败 {info.image_name}: {e}")
            return False

