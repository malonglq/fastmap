#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单张图片 EXIF 快速查看对话框
==liuq debug== ExifQuickViewDialog

{{CHENGQI:
Action: Added; Timestamp: 2025-08-12 16:30:00 +08:00; Reason: 新增拖拽图片后单张EXIF快速查看功能; Principle_Applied: KISS, UX-Feedback;
}}
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List

import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt

from core.services.exif_parser_service import ExifParserService
from core.interfaces.exif_processing import ExifParseOptions
from gui.tabs.exif_processing_tab import ExifProcessingTab


class ExifQuickViewDialog(QDialog):
    def __init__(self, image_path: Path, parent=None):
        super().__init__(parent)
        self._image_path = Path(image_path)
        self._parser = ExifParserService()
        self._fields = ExifProcessingTab._priority_list()
        self._values: Dict[str, Any] = {}
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        self.setWindowTitle(self._image_path.name)
        self.resize(760, 560)
        self.setModal(True)

        layout = QVBoxLayout(self)
        # Scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 7)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        # 留给填充用
        self._grid = grid
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # footer buttons
        footer = QHBoxLayout()
        footer.addStretch(1)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        footer.addWidget(btn_close)
        layout.addLayout(footer)

    def _fmt(self, v: Any) -> str:
        if v is None:
            return "N/A"
        try:
            if isinstance(v, float):
                s = f"{v:.4f}"
                return s.rstrip('0').rstrip('.')
            if isinstance(v, (list, tuple)):
                parts = []
                for it in v:
                    if isinstance(it, float):
                        s = f"{it:.4f}".rstrip('0').rstrip('.')
                        parts.append(s)
                    else:
                        parts.append(str(it))
                return ", ".join(parts)
            if isinstance(v, dict):
                try:
                    return json.dumps(v, ensure_ascii=False)
                except Exception:
                    return str(v)
            return str(v)
        except Exception:
            return str(v)

    def _load_values(self):
        try:
            opts = ExifParseOptions(
                selected_fields=self._fields,
                recursive=False,
                build_raw_flat=False,
                compute_available=False,
                debug_log_keys=False,
            )
            # 复用服务的单文件解析
            # 为兼容：如果服务未暴露 parse_file，则退回内部调用
            if hasattr(self._parser, 'parse_file'):
                values = self._parser.parse_file(self._image_path, opts)  # type: ignore
            else:
                # 兼容路径：直接读取raw并用定位索引
                from core.services.exif_parser_service import _get_by_flat_key, _flatten_items
                raw = self._parser._read_raw_exif(self._image_path)  # type: ignore
                values = {}
                for k in self._fields:
                    v = _get_by_flat_key(raw, k)
                    if v is None:
                        for fk, fv in _flatten_items(raw):
                            if fk == k:
                                v = fv
                                break
                    if v is not None:
                        values[k] = v
            self._values = values or {}
            # 渲染到网格
            row = 0
            for key in self._fields:
                name_lbl = QLabel(key)
                name_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                val = self._fmt(self._values.get(key))
                val_lbl = QLabel(val)
                val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                val_lbl.setWordWrap(True)
                self._grid.addWidget(name_lbl, row, 0)
                self._grid.addWidget(val_lbl, row, 1)
                row += 1
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解析图片失败: {e}")
            self.reject()

