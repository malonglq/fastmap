#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI: EXIF处理Tab（Phase 1：解析并导出CSV）
==liuq debug== FastMapV2 ExifProcessingTab

{{CHENGQI:
Action: Modified; Timestamp: 2025-08-11 13:15:00 +08:00; Reason: 目录加载后按可用字段动态刷新列表，避免字段为空; Principle_Applied: UX-Feedback, KISS;
}}
"""
from __future__ import annotations
from pathlib import Path
from typing import List

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


from core.interfaces.exif_processing import IExifParserService, IExifCsvExporter, ExifParseOptions
from core.services.exif_parser_service import ExifParserService
from core.services.exif_csv_exporter import ExifCsvExporter

class _ExportWorker(QThread):
    progress = pyqtSignal(int, int, str)  # processed, total, current_file
    finished_ok = pyqtSignal(object, str) # result, out_path
    failed = pyqtSignal(str)
    def __init__(self, parser: IExifParserService, exporter: IExifCsvExporter,
                 src_path: Path, opts: ExifParseOptions, out_path: Path, selected: List[str]):
        super().__init__()
        self._parser = parser
        self._exporter = exporter
        self._src = src_path
        self._opts = opts
        self._out = out_path
        self._selected = selected
        self._cancel = False
    def cancel(self):
        self._cancel = True
    def _on_progress(self, processed: int, total: int, current: str):
        self.progress.emit(processed, total, current)
    def _cancel_check(self) -> bool:
        return self._cancel
    def run(self):
        try:
            # 注入回调
            self._opts.on_progress = self._on_progress
            self._opts.cancel_check = self._cancel_check
            result = self._parser.parse_directory(self._src, self._opts)
            # 写CSV
            self._exporter.export_csv(result, self._out, self._selected,
                                      include_source_columns=False,
                                      include_raw_json=self._opts.keep_raw_json,
                                      include_timestamp=False,
                                      include_image_path=False)
            self.finished_ok.emit(result, str(self._out))
        except Exception as e:
            self.failed.emit(str(e))

class _ExportRawWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished_ok = pyqtSignal(object, str)
    failed = pyqtSignal(str)
    def __init__(self, parser: IExifParserService, raw_exporter,
                 src_path: Path, opts: ExifParseOptions, out_path: Path):
        super().__init__()
        self._parser = parser
        self._raw_exporter = raw_exporter
        self._src = src_path
        self._opts = opts
        self._out = out_path
        self._cancel = False
    def cancel(self):
        self._cancel = True
    def _on_progress(self, processed: int, total: int, current: str):
        self.progress.emit(processed, total, current)
    def _cancel_check(self) -> bool:
        return self._cancel
    def run(self):
        try:
            self._opts.on_progress = self._on_progress
            self._opts.cancel_check = self._cancel_check
            result = self._parser.parse_directory(self._src, self._opts)
            self._raw_exporter.export_raw_json(result, self._out)
            self.finished_ok.emit(result, str(self._out))
        except Exception as e:
            self.failed.emit(str(e))



class _DiscoverWorker(QThread):
    finished = pyqtSignal(list)
    def __init__(self, parser: IExifParserService, root: Path, recursive: bool, sample: int = 3):
        super().__init__()
        self._parser = parser
        self._root = root
        self._recursive = recursive
        self._sample = sample
    def run(self):
        try:
            keys = self._parser.discover_keys(self._root, recursive=self._recursive, sample=self._sample)
        except Exception:
            keys = []
        self.finished.emit(keys)


class ExifProcessingTab(QWidget):
    def __init__(self, parent=None, parser: IExifParserService = None, exporter: IExifCsvExporter = None):
        super().__init__(parent)
        self.parser = parser or ExifParserService()
        self.exporter = exporter or ExifCsvExporter()
        self._last_result = None
        self._discover_worker = None  # 保持线程引用，避免QThread销毁
        self._export_worker = None    # 导出线程引用
        self._raw_worker = None       # 原始JSON导出线程引用
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 源目录
        row_src = QHBoxLayout()
        row_src.addWidget(QLabel("源图片目录:"))
        self.edit_src = QLineEdit()
        btn_src = QPushButton("浏览")
        btn_src.clicked.connect(self._choose_src)
        row_src.addWidget(self.edit_src, 1)
        row_src.addWidget(btn_src)
        layout.addLayout(row_src)

        # 字段选择
        layout.addWidget(QLabel("选择字段:"))
        self.list_fields = QListWidget()
        self._populate_fields([])
        layout.addWidget(self.list_fields)
        # 快速勾选按钮组
        quick = QHBoxLayout()
        quick.addWidget(QLabel("快速勾选:"))
        btn_all = QPushButton("全选")
        btn_all.clicked.connect(self._check_all)
        quick.addWidget(btn_all)
        for name in ["meta_data", "ealgo_data", "color_sensor", "stats_weight", "face_info", "face_cc"]:
            b = QPushButton(name)
            b.clicked.connect(lambda _, p=name: self._check_prefix(p))
            quick.addWidget(b)
        btn_clear = QPushButton("清空选择")
        btn_clear.clicked.connect(self._clear_all)
        quick.addWidget(btn_clear)
        layout.addLayout(quick)


        row_sel = QHBoxLayout()
        self.cb_recursive = QCheckBox("递归子目录")
        self.cb_recursive.setChecked(True)
        row_sel.addWidget(self.cb_recursive)
        # 新增：CSV包含原始JSON
        self.cb_include_raw = QCheckBox("CSV包含原始JSON")
        self.cb_include_raw.setChecked(False)
        row_sel.addWidget(self.cb_include_raw)
        layout.addLayout(row_sel)

        # 输出路径（可选，留空则默认写到源目录）
        row_out = QHBoxLayout()
        row_out.addWidget(QLabel("输出CSV:"))
        self.edit_out = QLineEdit()
        btn_out = QPushButton("浏览")
        btn_out.clicked.connect(self._choose_out)
        row_out.addWidget(self.edit_out, 1)
        row_out.addWidget(btn_out)
        layout.addLayout(row_out)

        # 操作区
        row_ops = QHBoxLayout()
        btn_export = QPushButton("解析并导出")
        btn_export.clicked.connect(self._export)
        row_ops.addWidget(btn_export)
        # 导出进度
        self.lbl_progress = QLabel("")
        row_ops.addWidget(self.lbl_progress, 1)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_export)
        row_ops.addWidget(self.btn_cancel)
        btn_export_raw = QPushButton("导出原始EXIF JSON")
        btn_export_raw.clicked.connect(self._export_raw)
        row_ops.addWidget(btn_export_raw)
        layout.addLayout(row_ops)

    @staticmethod
    def _priority_list() -> List[str]:
        # 指定的精确顺序（逐行粘贴，保持一致）
        return [
            'meta_data_version',
            'meta_data_currentFrame_ctemp',
            'meta_data_after_face_Ctemp',
            'meta_data_outputCtemp',
            'meta_data_lastFrame_ctemp',
            'stats_weight_triggerCtemp',
            'color_cie_lux',
            'face_info_lux_index',
            'meta_data_resultCcmatrix',
            'ealgo_data_SGW_gray_RpG',
            'ealgo_data_SGW_gray_BpG',
            'ealgo_data_AGW_gray_RpG',
            'ealgo_data_AGW_gray_BpG',
            'ealgo_data_Mix_csalgo_RpG',
            'ealgo_data_Mix_csalgo_BpG',
            'ealgo_data_After_face_RpG',
            'ealgo_data_After_face_BpG',
            'ealgo_data_cnvgEst_RpG',
            'ealgo_data_cnvgEst_BpG',
            'meta_data_gslGain_rgain',
            'meta_data_gslGain_bgain',
            'ealgo_data_eRatio',
            'color_sensor_irRatio',
            'color_sensor_acRatio',
            'color_sensor_sensorCct',
            'color_sensor_cs_rpg',
            'color_sensor_cs_bpg',
            'color_sensor_pureColorMainHueAvgL',
            'color_sensor_pureColorMainHueAvgC',
            'color_sensor_pureColorFilterInfo',
            'ctemp_weight_Ctemp_weight',
            'ctemp_weight_Ctemp_count',
            'stats_weight_bitDepth',
            'stats_weight_exposureType',
            'face_info_light_skin_target_rg',
            'face_info_light_skin_target_bg',
            'face_info_dark_skin_target_rg',
            'face_info_dark_skin_target_bg',
            'face_info_light_skin_cct',
            'face_info_dark_skin_cct',
            'face_info_light_skin_weight',
            'face_info_skin_target_dist_ratio',
            'face_info_faceawb_weight',
            'face_info_final_skin_cct',
            'face_info_ffd_awb_enable',
            'face_info_dist',
            'face_info_frameLuma',
            'face_info_faceLuma',
            'face_info_compenADRCGain',
            'face_cc_local_enable',
            'face_cc_face_ccm',
            'face_cc_orig_face_ccm',
            'face_cc_face_awb_rGain',
            'face_cc_face_awb_bGain',
            'face_cc_global_awb_rGain',
            'face_cc_global_awb_bGain',
            'face_cc_face_awb_flag',
            'face_cc_local_face_awb_weight',
            'face_cc_local_ctemp_enable',
            'face_cc_local_ctemp_pos',
            'face_cc_local_gsl_enable',
            'face_cc_local_gsl_r_gain',
            'face_cc_local_gsl_b_gain',
            'face_cc_local_gsl_pos',
            'face_cc_outputCtemp',
            'face_cc_face_c_avg',
            'face_cc_face_h_avg',
            'offset_map',
            'detect_map',
            'map_weight_offsetMapWeight',
        ]

    def _check_all(self):
        for i in range(self.list_fields.count()):
            self.list_fields.item(i).setCheckState(Qt.Checked)

    def _clear_all(self):
        for i in range(self.list_fields.count()):
            self.list_fields.item(i).setCheckState(Qt.Unchecked)

    def _check_prefix(self, prefix: str):
        n = self.list_fields.count()
        for i in range(n):
            it = self.list_fields.item(i)
            if it.text().startswith(prefix):
                it.setCheckState(Qt.Checked)

    def _default_checked_list(self) -> List[str]:
        # 默认勾选清单（与优先清单一致）
        return self._priority_list()

    def _populate_fields(self, fields: List[str]):
        self.list_fields.clear()
        default_set = set(self._default_checked_list())
        available = set(fields)
        for key in fields:
            item = QListWidgetItem(key)
            if key in default_set and key in available:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.list_fields.addItem(item)



    def _choose_src(self):
        d = QFileDialog.getExistingDirectory(self, "选择源图片目录")
        if not d:
            return
        self.edit_src.setText(d)
        # 异步采样发现键名（不阻塞UI）
        self._populate_fields([])
        if self._discover_worker and self._discover_worker.isRunning():
            self._discover_worker.finished.disconnect()
            self._discover_worker.quit()
            self._discover_worker.wait(100)
        self._discover_worker = _DiscoverWorker(self.parser, Path(d), self.cb_recursive.isChecked(), sample=3)
        def on_done(keys: List[str]):
            try:
                pr = self._priority_list()
                ordered = [k for k in pr if k in keys]
                ordered += [k for k in keys if k not in ordered]
                self._populate_fields(ordered)
            except Exception:
                self._populate_fields([])
        self._discover_worker.finished.connect(on_done)
        self._discover_worker.start()

    def _choose_out(self):
        f, _ = QFileDialog.getSaveFileName(self, "选择CSV文件", "", "CSV文件 (*.csv)")
        if f:
            self.edit_out.setText(f)

    def _gather_selected_fields(self) -> List[str]:
        fields = []
        for i in range(self.list_fields.count()):
            it = self.list_fields.item(i)
            if it.checkState() == Qt.Checked:
                fields.append(it.text())
        return fields

    def _export(self):
        src = self.edit_src.text().strip()
        if not src:
            QMessageBox.warning(self, "提示", "请选择源图片目录")
            return
        src_path = Path(src)
        # 选中字段
        selected = self._gather_selected_fields()
        if not selected:
            QMessageBox.warning(self, "提示", "请至少选择一个字段")
            return
        # 若有正在进行的导出，先取消
        if self._export_worker and self._export_worker.isRunning():
            self._export_worker.cancel(); self._export_worker.wait(200)
        self.btn_cancel.setEnabled(True)
        self.lbl_progress.setText("准备开始…")
        # 选中字段顺序：按 priority 列表优先，其余保持原顺序
        pr = self._priority_list()
        selected_sorted = [k for k in pr if k in selected]
        selected_sorted += [k for k in selected if k not in selected_sorted]
        opts = ExifParseOptions(
            selected_fields=selected_sorted,
            recursive=self.cb_recursive.isChecked(),
            keep_raw_json=self.cb_include_raw.isChecked(),
            build_raw_flat=False,
            compute_available=False,
            debug_log_keys=False,
        )
        # 输出路径
        out = self.edit_out.text().strip()
        if not out:
            out = str(src_path / 'exif_awb_export.csv')
        out_path = Path(out)
        # 启动后台导出
        self._export_worker = _ExportWorker(self.parser, self.exporter, src_path, opts, out_path, selected)
        self._export_worker.progress.connect(self._on_export_progress)
        self._export_worker.finished_ok.connect(self._on_export_done)
        self._export_worker.failed.connect(self._on_export_failed)
        self._export_worker.start()


    def _on_export_progress(self, processed: int, total: int, current: str):
        try:
            self.lbl_progress.setText(f"进度: {processed}/{total} - {current}")
        except Exception:
            pass

    def _on_export_done(self, result, out_path: str):
        self.btn_cancel.setEnabled(False)
        self.lbl_progress.setText("")
        self._last_result = result
        QMessageBox.information(self, "完成", f"导出完成: {out_path}")

    def _on_export_failed(self, msg: str):
        self.btn_cancel.setEnabled(False)
        self.lbl_progress.setText("")
        QMessageBox.critical(self, "导出失败", msg)

    def _cancel_export(self):
        if hasattr(self, '_export_worker') and self._export_worker:
            try:
                self._export_worker.cancel()
                self.btn_cancel.setEnabled(False)
                self.lbl_progress.setText("已请求取消…")
            except Exception:
                pass

        # 选中字段顺序：按 priority 列表优先，其余保持原顺序
        pr = self._priority_list()
        selected = self._gather_selected_fields()
        selected_sorted = [k for k in pr if k in selected]
        selected_sorted += [k for k in selected if k not in selected_sorted]
        # 构建 opts 与 out_path 供后续恢复/重试（可选）

        # 选中字段顺序：按 priority 列表优先，其余保持原顺序
        pr = self._priority_list()
        selected_sorted = [k for k in pr if k in selected]
        selected_sorted += [k for k in selected if k not in selected_sorted]
        opts = ExifParseOptions(
            selected_fields=selected_sorted,
            recursive=self.cb_recursive.isChecked(),
            keep_raw_json=self.cb_include_raw.isChecked(),
            build_raw_flat=False,
            compute_available=False,
            debug_log_keys=False,
        )

        # 输出路径
        out = self.edit_out.text().strip()
        if not out:
            out = str(Path(self.edit_src.text().strip()) / 'exif_awb_export.csv')
        out_path = Path(out)

        # 启动后台导出
        self._export_worker = _ExportWorker(self.parser, self.exporter, Path(self.edit_src.text().strip()), opts, out_path, selected)
        self._export_worker.progress.connect(self._on_export_progress)
        self._export_worker.finished_ok.connect(self._on_export_done)
        self._export_worker.failed.connect(self._on_export_failed)
        self._export_worker.start()


    def _export_raw(self):
        try:
            # 源目录：优先使用已选择目录
            src = self.edit_src.text().strip()
            if not src:
                d = QFileDialog.getExistingDirectory(self, "选择源图片目录")
                if not d:
                    return
                src = d
            src_path = Path(src)
            # 选择保存路径，默认放在源目录
            default_path = str(src_path / 'exif_raw.jsonl')
            out, _ = QFileDialog.getSaveFileName(self, "保存原始EXIF JSONL", default_path, "JSON Lines (*.jsonl)")
            if not out:
                return
            out_path = Path(out)
            # 若有正在进行的任务，先取消
            if self._export_worker and self._export_worker.isRunning():
                self._export_worker.cancel(); self._export_worker.wait(200)
            if self._raw_worker and self._raw_worker.isRunning():
                self._raw_worker.cancel(); self._raw_worker.wait(200)
            # 进度
            self.btn_cancel.setEnabled(True)
            self.lbl_progress.setText("准备开始…")
            # 仅需要原始JSON
            opts = ExifParseOptions(
                selected_fields=[],
                recursive=self.cb_recursive.isChecked(),
                keep_raw_json=True,
                build_raw_flat=False,
                compute_available=False,
                debug_log_keys=False,
            )
            from core.services.exif_raw_exporter import ExifRawExporter
            self._raw_worker = _ExportRawWorker(self.parser, ExifRawExporter(), src_path, opts, out_path)
            self._raw_worker.progress.connect(self._on_export_progress)
            self._raw_worker.finished_ok.connect(self._on_export_done)
            self._raw_worker.failed.connect(self._on_export_failed)
            self._raw_worker.start()
        except Exception as e:
            QMessageBox.warning(self, "提示", f"导出失败: {e}")
