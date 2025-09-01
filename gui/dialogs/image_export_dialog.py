#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片分类导出对话框（PyQt）
==liuq debug== FastMapV2 ImageExportDialog

{{CHENGQI:
Action: Added; Timestamp: 2025-08-11 11:12:00 +08:00; Reason: 新增图片分类导出GUI; Principle_Applied: KISS;
}}
"""
from __future__ import annotations
import logging
from typing import Any, Dict
from pathlib import Path
import shutil

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox,
    QLineEdit, QFileDialog, QMessageBox, QProgressDialog, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.interfaces.image_classification import (
    ClassificationOptions, ExportSelection, NamingOptions, ChangeThresholds
)
from core.services.exif_processing.image_export_workflow_service import ImageExportWorkflowService

logger = logging.getLogger(__name__)


class ImageExportDialog(QDialog):
    def __init__(self, parent=None, match_result: Dict[str, Any] = None, available_fields=None):
        super().__init__(parent)
        self.setWindowTitle("图片分类导出")
        self.resize(640, 360)
        self.match_result = match_result or {}
        self.available_fields = available_fields or []

        self.workflow = ImageExportWorkflowService()

        self._build_ui()
        # 连接主字段变更以自动刷新统计
        try:
            self.field_combo.currentTextChanged.connect(self._on_field_changed)
        except Exception:
            pass
        # 初次进入即计算并显示统计
        self._recompute_and_update_stats()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 主字段选择
        row = QHBoxLayout()
        row.addWidget(QLabel("主字段:"))
        self.field_combo = QComboBox()
        for f in self.available_fields:
            self.field_combo.addItem(f)
        row.addWidget(self.field_combo, 1)
        layout.addLayout(row)

        # 字段对比(SPC)模式
        pair_row = QHBoxLayout()
        self.cb_pair = QCheckBox("使用字段对比(SPC)")
        self.cb_pair.stateChanged.connect(self._on_mode_changed)
        pair_row.addWidget(self.cb_pair)
        pair_row.addWidget(QLabel("字段对:"))
        self.pair_combo = QComboBox()
        # 预置6组字段对
        self._preset_pairs = [
            ("ealgo_data_agw_nomap_rpg", "ealgo_data_agw_gray_rpg"),
            ("ealgo_data_agw_nomap_bpg", "ealgo_data_agw_gray_bpg"),
            ("ealgo_data_agw_nomap_rpg", "ealgo_data_after_face_rpg"),
            ("ealgo_data_agw_nomap_bpg", "ealgo_data_after_face_bpg"),
            ("ealgo_data_agw_nomap_rpg", "ealgo_data_cnvgest_rpg"),
            ("ealgo_data_agw_nomap_bpg", "ealgo_data_cnvgest_bpg"),
        ]
        for a,b in self._preset_pairs:
            self.pair_combo.addItem(f"{a} vs {b}")
        # 下拉选择变化时刷新统计
        try:
            self.pair_combo.currentIndexChanged.connect(self._on_pair_changed)
            self.pair_combo.currentTextChanged.connect(self._on_pair_changed)
        except Exception:
            pass
        pair_row.addWidget(self.pair_combo, 1)
        layout.addLayout(pair_row)

        # 阈值设置（仅字段对比时生效）
        thr_row = QHBoxLayout()
        thr_row.addWidget(QLabel("无变化<"))
        self.thr_none = QLineEdit("0.5")
        self.thr_none.setFixedWidth(60)
        thr_row.addWidget(self.thr_none)
        thr_row.addWidget(QLabel("%， 小[none,med)<"))
        self.thr_med = QLineEdit("5")
        self.thr_med.setFixedWidth(60)
        thr_row.addWidget(self.thr_med)
        thr_row.addWidget(QLabel("%， 中[med,large)<"))
        self.thr_large = QLineEdit("10")
        self.thr_large.setFixedWidth(60)
        thr_row.addWidget(self.thr_large)
        # 阈值变更时刷新（在SPC模式时生效）
        try:
            self.thr_none.editingFinished.connect(self._on_threshold_changed)
            self.thr_med.editingFinished.connect(self._on_threshold_changed)
            self.thr_large.editingFinished.connect(self._on_threshold_changed)
        except Exception:
            pass
        thr_row.addWidget(QLabel("% (SPC)"))
        layout.addLayout(thr_row)

        # 统计卡片区域（在复选框之上）
        self._build_stats_area(layout)

        # 类别复选
        cat_row = QHBoxLayout()
        self.c_large = QCheckBox("大变化")
        self.c_medium = QCheckBox("中变化")
        self.c_small = QCheckBox("小变化")
        self.c_none = QCheckBox("无变化")
        for cb in (self.c_large, self.c_medium, self.c_small, self.c_none):
            cb.setChecked(True)
            cat_row.addWidget(cb)
        layout.addLayout(cat_row)

        # 目录
        src_row = QHBoxLayout()
        self.src_edit = QLineEdit(); self.src_btn = QPushButton("选择源目录")
        self.src_btn.clicked.connect(self._choose_src)
        src_row.addWidget(QLabel("源图片目录:")); src_row.addWidget(self.src_edit, 1); src_row.addWidget(self.src_btn)
        layout.addLayout(src_row)

        out_row = QHBoxLayout()
        self.out_edit = QLineEdit(); self.out_btn = QPushButton("选择输出目录")
        self.out_btn.clicked.connect(self._choose_out)
        out_row.addWidget(QLabel("输出目录:")); out_row.addWidget(self.out_edit, 1); out_row.addWidget(self.out_btn)
        layout.addLayout(out_row)

        # 操作区
        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("开始导出")
        self.start_btn.clicked.connect(self._start)
        btn_row.addWidget(self.start_btn)
        btn_row.addStretch(1)
        self.cancel_btn = QPushButton("关闭")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    # ===== 统计卡片实现 =====
    def _build_stats_area(self, parent_layout: QVBoxLayout):
        # 容器
        self.stats_frame = QFrame()
        self.stats_frame.setFrameShape(QFrame.StyledPanel)
        grid = QGridLayout(self.stats_frame)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        self._stat_cards = {}
        labels = [
            ("total", "总计", "#2c3e50"),
            ("large_changes", "大变化", "#e74c3c"),
            ("medium_changes", "中变化", "#f39c12"),
            ("small_changes", "小变化", "#27ae60"),
            ("no_changes", "无变化", "#7f8c8d"),
        ]
        for idx, (key, title, color) in enumerate(labels):
            num = QLabel("0"); num.setAlignment(Qt.AlignCenter); num.setFont(QFont("Arial", 18, QFont.Bold)); num.setStyleSheet(f"color:{color}")
            desc = QLabel(title); desc.setAlignment(Qt.AlignCenter)
            widget = QFrame(); vl = QVBoxLayout(widget); vl.setContentsMargins(8,6,8,6); vl.addWidget(num); vl.addWidget(desc)
            grid.addWidget(widget, 0, idx)
            self._stat_cards[key] = (num, desc)

        parent_layout.addWidget(self.stats_frame)

    def _format_pct(self, v: float) -> str:
        try:
            return f"{v:.1f}%"
        except Exception:
            return "0%"

    def _recompute_and_update_stats(self):
        try:
            # 构建选项（根据模式）
            if self.cb_pair.isChecked():
                pair_text = self.pair_combo.currentText()
                # 解析 "a vs b"
                parts = [p.strip() for p in pair_text.split('vs')]
                compare_pair = [parts[0], parts[1]] if len(parts) >= 2 else None
                # 阈值
                def _to_float(s, dv):
                    try:
                        return float(str(s).strip())
                    except Exception:
                        return dv
                none_max = _to_float(self.thr_none.text(), 3.0)
                med_min = _to_float(self.thr_med.text(), 10.0)
                large_min = _to_float(self.thr_large.text(), 20.0)

                th = ChangeThresholds(
                    pct_large_min=large_min,
                    pct_medium_min=med_min,
                    pct_medium_max=large_min,
                    pct_no_change_max=none_max
                )
                options = ClassificationOptions(primary_field='', selected_fields=[], compare_pair=compare_pair, metric='percent_spc', thresholds=th)
            else:
                pf = self.field_combo.currentText().strip() if self.field_combo.count() else ''
                if not pf:
                    return
                options = ClassificationOptions(primary_field=pf, selected_fields=[pf])

            result = self.workflow.compute_classification(self.match_result, options)
            panel = self.workflow.build_stats_panel(result)

            # 更新数字
            total = panel.total
            self._stat_cards['total'][0].setText(str(total))
            # 从 panel.cards 更新四类
            for key in ['large_changes','medium_changes','small_changes','no_changes']:
                # 查找对应卡片
                card = next((c for c in panel.cards if c.key == key), None)
                cnt = card.count if card else 0
                pct = card.percentage if card else 0.0
                num_label, desc_label = self._stat_cards[key]
                num_label.setText(str(cnt))
                # 描述包含百分比（使用 card.title 以保持与映射一致）
                title = card.title if card else { 'large_changes':'大变化', 'medium_changes':'中变化', 'small_changes':'小变化', 'no_changes':'无变化' }[key]
                desc_label.setText(f"{title} ({self._format_pct(pct)})")
        except Exception as e:
            logger.error(f"==liuq debug== 更新统计失败: {e}")

    def _on_field_changed(self, _):
        self._recompute_and_update_stats()

    def _on_mode_changed(self, _):
        self._recompute_and_update_stats()

    def _on_pair_changed(self, _):
        self._recompute_and_update_stats()

    def _on_threshold_changed(self):
        self._recompute_and_update_stats()

    # ===== 目录与导出 =====
    def _choose_src(self):
        d = QFileDialog.getExistingDirectory(self, "选择源图片目录")
        if d:
            self.src_edit.setText(d)

    def _choose_out(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if d:
            self.out_edit.setText(d)

    def _start(self):
        pf = self.field_combo.currentText().strip()
        if not pf:
            QMessageBox.warning(self, "提示", "请选择主字段")
            return
        src = self.src_edit.text().strip()
        out = self.out_edit.text().strip()
        if not src or not out:
            QMessageBox.warning(self, "提示", "请设置源目录与输出目录")
            return

        # 构建分类选项
        if self.cb_pair.isChecked():
            pair_text = self.pair_combo.currentText()
            parts = [p.strip() for p in pair_text.split('vs')]
            compare_pair = [parts[0], parts[1]] if len(parts) >= 2 else None
            # 阈值
            def _to_float(s, dv):
                try:
                    return float(str(s).strip())
                except Exception:
                    return dv
            none_max = _to_float(self.thr_none.text(), 3.0)
            med_min = _to_float(self.thr_med.text(), 10.0)
            large_min = _to_float(self.thr_large.text(), 20.0)
            th = ChangeThresholds(
                pct_large_min=large_min,
                pct_medium_min=med_min,
                pct_medium_max=large_min,
                pct_no_change_max=none_max
            )
            options = ClassificationOptions(primary_field='', selected_fields=[], compare_pair=compare_pair, metric='percent_spc', thresholds=th)
        else:
            options = ClassificationOptions(primary_field=pf, selected_fields=[pf])

        selection = ExportSelection(
            export_large=self.c_large.isChecked(),
            export_medium=self.c_medium.isChecked(),
            export_small=self.c_small.isChecked(),
            export_no_change=self.c_none.isChecked()
        )

        # 分类
        result = self.workflow.compute_classification(self.match_result, options)

        # 导出前清理输出目录下的分类子目录
        try:
            out_path = Path(out)
            targets = [
                "1_large_changes",
                "2_medium_changes",
                "3_small_changes",
                "4_no_changes",
            ]
            for name in targets:
                p = out_path / name
                if p.exists():
                    if p.is_dir():
                        shutil.rmtree(p)
                        logger.info(f"==liuq debug== 已清理输出子目录: {p}")
                    else:
                        p.unlink()
                        logger.info(f"==liuq debug== 已删除同名文件: {p}")
        except Exception as e:
            logger.warning(f"==liuq debug== 清理输出目录失败(跳过不阻塞): {e}")

        # 进度对话框
        prog = QProgressDialog("正在导出…", "取消", 0, 100, self)
        prog.setWindowModality(Qt.WindowModal)
        prog.setAutoClose(True)

        def cb(pct, msg):
            prog.setValue(pct)
            prog.setLabelText(f"{msg}")
            if prog.wasCanceled():
                # 简易取消：关闭回调，不中断当前复制（后续可扩展中断）
                pass

        stats = self.workflow.export_images(
            result, selection, Path(src), Path(out), NamingOptions(), progress_cb=cb
        )
        prog.setValue(100)

        QMessageBox.information(self, "完成", f"导出完成\n总计: {stats.total_copied}\n缺失: {len(stats.missing_files)}\n输出: {out}")
        self.accept()

