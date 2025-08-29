#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF对比配置对话框
==liuq debug== FastMapV2 EXIF对比配置对话框

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 15:30:00 +08:00; Reason: 阶段2-创建EXIF对比配置对话框; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: EXIF对比分析的配置界面
"""

import logging
import json
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem,
    QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QTabWidget, QWidget, QMessageBox,
    QProgressBar, QComboBox, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from pathlib import Path

from core.services.reporting.exif_comparison_report_generator import ExifComparisonReportGenerator

logger = logging.getLogger(__name__)


from gui.dialogs.base_analysis_dialog import BaseAnalysisDialog, BaseWorker


class FieldPreviewWorker(BaseWorker):
    """字段预览工作线程"""

    def __init__(self, csv_path: str, generator: ExifComparisonReportGenerator):
        super().__init__()
        self.csv_path = csv_path
        self.generator = generator

    def run(self):
        try:
            self.progress_updated.emit(50, "正在加载字段信息...")
            field_info = self.generator.get_supported_fields(self.csv_path)
            self.progress_updated.emit(100, "字段信息加载完成")
            self.analysis_completed.emit(field_info)
        except Exception as e:
            self.analysis_failed.emit(str(e))


class ExifComparisonDialog(BaseAnalysisDialog):
    """
    EXIF对比配置对话框

    提供文件选择、字段配置、参数设置等功能
    """

    def __init__(self, parent=None):
        # 初始化组件
        self.generator = ExifComparisonReportGenerator()
        self.test_field_info = None
        self.reference_field_info = None
        self.selected_fields = []
        # 状态持久化
        self._state_file = Path("data/configs/exif_comparison_last_state.json")
        self._pending_select_fields: Optional[List[str]] = None

        super().__init__(parent, "EXIF对比分析配置", (800, 600), self._state_file)

        # 尝试恢复上次的选择
        self.load_saved_state()

        logger.info("==liuq debug== EXIF对比配置对话框初始化完成")

    def setup_ui(self):
        """设置用户界面"""
        # 基础UI设置已由基类完成

        # 文件选择标签页
        self.file_tab = self.create_file_selection_tab()
        self.tab_widget.addTab(self.file_tab, "文件选择")

        # 字段配置标签页
        self.field_tab = self.create_field_configuration_tab()
        self.tab_widget.addTab(self.field_tab, "字段配置")

        # 参数设置标签页
        self.param_tab = self.create_parameter_settings_tab()
        self.tab_widget.addTab(self.param_tab, "参数设置")

        # 预览标签页
        self.preview_tab = self.create_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "预览")

        # 显示预览和导出按钮
        self.preview_btn.setVisible(True)
        self.preview_btn.setText("预览匹配")
        self.preview_btn.setEnabled(False)
        self.preview_btn.clicked.connect(self.preview_matching)

        self.export_btn.setVisible(True)
        self.export_btn.setText("图片分类导出…")
        self.export_btn.setEnabled(True)  # 允许打开后内部再校验
        self.export_btn.clicked.connect(self.open_image_export_dialog)

    def create_file_selection_tab(self) -> QWidget:
        """创建文件选择标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 测试机文件选择
        test_group = QGroupBox("测试机EXIF数据")
        test_layout = QVBoxLayout(test_group)

        test_file_layout = QHBoxLayout()
        self.test_file_edit = QLineEdit()
        self.test_file_edit.setPlaceholderText("选择测试机的EXIF CSV文件...")
        test_file_layout.addWidget(self.test_file_edit)

        self.test_browse_btn = QPushButton("浏览")
        self.test_browse_btn.clicked.connect(self.browse_test_file)
        test_file_layout.addWidget(self.test_browse_btn)

        test_layout.addLayout(test_file_layout)

        # 测试机文件信息
        self.test_info_label = QLabel("请选择测试机EXIF CSV文件")
        self.test_info_label.setStyleSheet("color: gray;")
        test_layout.addWidget(self.test_info_label)

        layout.addWidget(test_group)

        # 对比机文件选择
        reference_group = QGroupBox("对比机EXIF数据")
        reference_layout = QVBoxLayout(reference_group)

        reference_file_layout = QHBoxLayout()
        self.reference_file_edit = QLineEdit()
        self.reference_file_edit.setPlaceholderText("选择对比机的EXIF CSV文件...")
        reference_file_layout.addWidget(self.reference_file_edit)

        self.reference_browse_btn = QPushButton("浏览")
        self.reference_browse_btn.clicked.connect(self.browse_reference_file)
        reference_file_layout.addWidget(self.reference_browse_btn)

        reference_layout.addLayout(reference_file_layout)

        # 对比机文件信息
        self.reference_info_label = QLabel("请选择对比机EXIF CSV文件")
        self.reference_info_label.setStyleSheet("color: gray;")
        reference_layout.addWidget(self.reference_info_label)

        layout.addWidget(reference_group)

        # 输出路径选择
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)

        output_file_layout = QHBoxLayout()
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setPlaceholderText("选择报告输出路径（可选，留空使用默认路径）...")
        output_file_layout.addWidget(self.output_file_edit)

        self.output_browse_btn = QPushButton("浏览")
        self.output_browse_btn.clicked.connect(self.browse_output_file)
        output_file_layout.addWidget(self.output_browse_btn)

        output_layout.addLayout(output_file_layout)
        layout.addWidget(output_group)

        layout.addStretch()
        return tab

    def create_field_configuration_tab(self) -> QWidget:
        """创建字段配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 说明
        info_label = QLabel("选择要分析的EXIF字段（建议选择数值类型的字段）：")
        info_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(info_label)

        # 字段选择表格
        self.field_table = QTableWidget()
        self.field_table.setColumnCount(6)
        self.field_table.setHorizontalHeaderLabels([
            "选择", "字段名", "显示名", "数据类型", "非空数量", "数值范围"
        ])

        # 设置表格属性
        header = self.field_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.field_table.setAlternatingRowColors(True)
        self.field_table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.field_table)

        # 快速选择按钮
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_fields)
        button_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("全不选")
        self.select_none_btn.clicked.connect(self.select_no_fields)
        button_layout.addWidget(self.select_none_btn)

        self.select_core_btn = QPushButton("选择优先字段")
        self.select_core_btn.clicked.connect(self.select_core_fields)
        button_layout.addWidget(self.select_core_btn)

        self.select_numeric_btn = QPushButton("选择数值字段")
        self.select_numeric_btn.clicked.connect(self.select_numeric_fields)
        button_layout.addWidget(self.select_numeric_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        return tab

    def create_parameter_settings_tab(self) -> QWidget:
        """创建参数设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 匹配参数
        match_group = QGroupBox("数据匹配参数")
        match_layout = QVBoxLayout(match_group)

        # 匹配列
        match_column_layout = QHBoxLayout()
        match_column_layout.addWidget(QLabel("匹配列:"))
        self.match_column_combo = QComboBox()
        self.match_column_combo.addItems(["image_name", "timestamp", "image_path"])
        self.match_column_combo.setCurrentText("image_name")
        match_column_layout.addWidget(self.match_column_combo)
        match_column_layout.addStretch()
        match_layout.addLayout(match_column_layout)

        # 相似度阈值
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("相似度阈值:"))
        self.similarity_threshold_spin = QDoubleSpinBox()
        self.similarity_threshold_spin.setRange(0.0, 1.0)
        self.similarity_threshold_spin.setSingleStep(0.1)
        self.similarity_threshold_spin.setValue(0.8)
        self.similarity_threshold_spin.setDecimals(2)
        threshold_layout.addWidget(self.similarity_threshold_spin)
        threshold_layout.addWidget(QLabel("(0.0-1.0，值越高匹配越严格)"))
        threshold_layout.addStretch()
        match_layout.addLayout(threshold_layout)

        layout.addWidget(match_group)

        # 分析参数
        analysis_group = QGroupBox("分析参数")
        analysis_layout = QVBoxLayout(analysis_group)

        # 最大字段数限制
        max_fields_layout = QHBoxLayout()
        max_fields_layout.addWidget(QLabel("最大分析字段数:"))
        self.max_fields_spin = QSpinBox()
        self.max_fields_spin.setRange(1, 100)
        self.max_fields_spin.setValue(20)
        max_fields_layout.addWidget(self.max_fields_spin)
        max_fields_layout.addWidget(QLabel("(建议不超过20个字段以确保性能)"))
        max_fields_layout.addStretch()
        analysis_layout.addLayout(max_fields_layout)

        layout.addWidget(analysis_group)

        layout.addStretch()
        return tab

    def create_preview_tab(self) -> QWidget:
        """创建预览标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        # 预览信息
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlainText("请先选择文件并配置参数，然后点击'预览匹配'按钮查看匹配结果。")
        layout.addWidget(self.preview_text)
        return tab

    def apply_state(self, state: Dict[str, Any]):
        """应用状态到UI"""
        # 路径
        self.test_file_edit.setText(state.get('test_csv_path', ''))
        self.reference_file_edit.setText(state.get('reference_csv_path', ''))
        self.output_file_edit.setText(state.get('output_path', '') or '')
        # 参数
        match_column = state.get('match_column')
        if match_column:
            index = self.match_column_combo.findText(match_column)
            if index >= 0:
                self.match_column_combo.setCurrentIndex(index)
        threshold = state.get('similarity_threshold')
        if isinstance(threshold, (int, float)):
            try:
                self.similarity_threshold_spin.setValue(float(threshold))
            except Exception:
                pass
        # 字段延迟应用（需等表格构建完成）
        self._pending_select_fields = state.get('selected_fields') or []
        # 若路径存在，尝试自动加载字段信息
        if state.get('test_csv_path'):
            self.load_test_file_info(state.get('test_csv_path'))
        if state.get('reference_csv_path'):
            self.load_reference_file_info(state.get('reference_csv_path'))
        logger.info("==liuq debug== 已恢复EXIF对话框上次状态")

    def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.get_configuration()

    def setup_signals(self):
        """设置信号连接"""
        # 文件路径变化时更新状态
        self.test_file_edit.textChanged.connect(self.update_ui_state)
        self.reference_file_edit.textChanged.connect(self.update_ui_state)

        # 字段选择变化时更新状态
        # 这个信号会在populate_field_table中连接

    def browse_test_file(self):
        """浏览测试机文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择测试机EXIF CSV文件",
            "",
            "CSV文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            self.test_file_edit.setText(file_path)
            self.load_test_file_info(file_path)

    def browse_reference_file(self):
        """浏览对比机文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择对比机EXIF CSV文件",
            "",
            "CSV文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            self.reference_file_edit.setText(file_path)
            self.load_reference_file_info(file_path)

    def browse_output_file(self):
        """浏览输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择报告输出路径",
            "exif_comparison_report.html",
            "HTML文件 (*.html);;所有文件 (*)"
        )

        if file_path:
            self.output_file_edit.setText(file_path)

    def load_test_file_info(self, file_path: str):
        """加载测试机文件信息"""
        try:
            self.test_info_label.setText("正在加载文件信息...")

            # 创建工作线程
            worker = FieldPreviewWorker(file_path, self.generator)
            self.start_worker(worker)

        except Exception as e:
            self.test_info_label.setText(f"加载失败: {e}")
            logger.error(f"==liuq debug== 加载测试机文件信息失败: {e}")

    def load_reference_file_info(self, file_path: str):
        """加载对比机文件信息"""
        try:
            self.reference_info_label.setText("正在加载文件信息...")

            # 创建工作线程
            worker = FieldPreviewWorker(file_path, self.generator)
            self.start_worker(worker)

        except Exception as e:
            self.reference_info_label.setText(f"加载失败: {e}")
            logger.error(f"==liuq debug== 加载对比机文件信息失败: {e}")

    def on_worker_completed(self, field_info: Dict[str, Any]):
        """字段信息加载完成"""
        # 根据当前状态判断是哪个文件的信息
        if not self.test_field_info:
            self.test_field_info = field_info
            # 更新信息标签
            total_fields = field_info['total_fields']
            numeric_fields = len(field_info['numeric_fields'])
            self.test_info_label.setText(f"共 {total_fields} 个字段，其中 {numeric_fields} 个数值字段")
        elif not self.reference_field_info:
            self.reference_field_info = field_info
            # 更新信息标签
            total_fields = field_info['total_fields']
            numeric_fields = len(field_info['numeric_fields'])
            self.reference_info_label.setText(f"共 {total_fields} 个字段，其中 {numeric_fields} 个数值字段")

        # 如果两个文件都加载完成，更新字段表格
        if self.test_field_info and self.reference_field_info:
            self.populate_field_table()

        self.update_ui_state()

    def on_worker_failed(self, error_msg: str):
        """字段信息加载错误"""
        self.show_warning("加载错误", f"文件信息加载失败:\n{error_msg}")

    def populate_field_table(self):
        """填充字段表格"""
        try:
            # 获取两个文件的公共数值字段 - 使用大小写不敏感匹配
            test_numeric_fields = {f['name'] for f in self.test_field_info['numeric_fields']}
            reference_numeric_fields = {f['name'] for f in self.reference_field_info['numeric_fields']}

            # 创建大小写不敏感的字段映射
            test_fields_lower = {f.lower(): f for f in test_numeric_fields}
            ref_fields_lower = {f.lower(): f for f in reference_numeric_fields}

            # 找到公共字段（大小写不敏感）
            common_fields_lower = set(test_fields_lower.keys()).intersection(set(ref_fields_lower.keys()))

            # 构建实际的公共字段集合（使用测试机的字段名作为标准）
            common_fields = {test_fields_lower[field_lower] for field_lower in common_fields_lower}

            logger.info(f"==liuq debug== 大小写不敏感匹配找到 {len(common_fields)} 个公共字段")

            # 获取字段详细信息
            field_details = {}
            for field_info in self.test_field_info['numeric_fields']:
                if field_info['name'] in common_fields:
                    field_details[field_info['name']] = field_info

            # 按照CSV文件中的原始顺序排列字段（保持原始列顺序）
            ordered_common_fields = []
            for field_info in self.test_field_info['numeric_fields']:
                if field_info['name'] in common_fields:
                    ordered_common_fields.append(field_info['name'])

            logger.info(f"==liuq debug== 按原始顺序排列的公共字段: {ordered_common_fields[:5]}...")

            # 设置表格行数
            self.field_table.setRowCount(len(common_fields))

            # 填充表格（按原始顺序）
            for row, field_name in enumerate(ordered_common_fields):
                field_info = field_details[field_name]

                # 选择复选框
                checkbox = QCheckBox()
                checkbox.stateChanged.connect(self.on_field_selection_changed)
                self.field_table.setCellWidget(row, 0, checkbox)

                # 字段名
                self.field_table.setItem(row, 1, QTableWidgetItem(field_name))

                # 显示名
                display_name = self.generator.display_names.get(field_name, field_name)
                self.field_table.setItem(row, 2, QTableWidgetItem(display_name))

                # 数据类型
                self.field_table.setItem(row, 3, QTableWidgetItem(field_info['dtype']))

                # 非空数量
                self.field_table.setItem(row, 4, QTableWidgetItem(str(field_info['non_null_count'])))

                # 数值范围
                if 'min_value' in field_info and 'max_value' in field_info:
                    range_text = f"{field_info['min_value']:.3f} ~ {field_info['max_value']:.3f}"
                else:
                    range_text = "N/A"
                self.field_table.setItem(row, 5, QTableWidgetItem(range_text))

            # 默认选择：若有历史选择则应用，否则选择优先字段
            if self._pending_select_fields:
                self.apply_pending_field_selection()
            else:
                self.select_core_fields()

            logger.info(f"==liuq debug== 字段表格填充完成，共 {len(common_fields)} 个公共字段")

        except Exception as e:
            logger.error(f"==liuq debug== 填充字段表格失败: {e}")
            QMessageBox.warning(self, "错误", f"填充字段表格失败: {e}")

    def apply_pending_field_selection(self):
        """根据_pending_select_fields勾选字段"""
        try:
            if not self._pending_select_fields:
                return
            # 建立不区分大小写的集合
            target_set = {str(x).lower() for x in self._pending_select_fields}
            applied = 0
            for row in range(self.field_table.rowCount()):
                name_item = self.field_table.item(row, 1)
                cb = self.field_table.cellWidget(row, 0)
                if name_item and cb:
                    cb.setChecked(name_item.text().lower() in target_set)
                    if cb.isChecked():
                        applied += 1
            logger.info(f"==liuq debug== 已按历史状态勾选 {applied} 个字段")
        except Exception as e:
            logger.warning(f"==liuq debug== 应用历史字段选择失败: {e}")
        finally:
            self._pending_select_fields = None

    def on_field_selection_changed(self):
        """字段选择变化"""
        self.update_selected_fields()
        self.update_ui_state()

    def update_selected_fields(self):
        """更新选中的字段列表"""
        self.selected_fields = []

        for row in range(self.field_table.rowCount()):
            checkbox = self.field_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                field_name_item = self.field_table.item(row, 1)
                if field_name_item:
                    self.selected_fields.append(field_name_item.text())

        logger.debug(f"==liuq debug== 选中字段: {self.selected_fields}")

    def select_all_fields(self):
        """全选字段"""
        for row in range(self.field_table.rowCount()):
            checkbox = self.field_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)

    def select_no_fields(self):
        """全不选字段"""
        for row in range(self.field_table.rowCount()):
            checkbox = self.field_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)

    def select_core_fields(self):
        """选择优先字段（自动勾选指定的重要字段）"""
        # 使用新的优先字段列表
        priority_fields = self.generator.priority_fields

        # 创建大小写不敏感的优先字段映射
        priority_fields_lower = {field.lower() for field in priority_fields}

        selected_count = 0

        for row in range(self.field_table.rowCount()):
            field_name_item = self.field_table.item(row, 1)
            checkbox = self.field_table.cellWidget(row, 0)

            if field_name_item and checkbox:
                field_name = field_name_item.text()
                # 大小写不敏感匹配
                should_select = field_name.lower() in priority_fields_lower
                checkbox.setChecked(should_select)

                if should_select:
                    selected_count += 1

        logger.info(f"==liuq debug== 自动选择了 {selected_count} 个优先字段")

    def select_numeric_fields(self):
        """选择所有数值字段"""
        max_fields = self.max_fields_spin.value()
        selected_count = 0

        for row in range(self.field_table.rowCount()):
            checkbox = self.field_table.cellWidget(row, 0)
            if checkbox and selected_count < max_fields:
                checkbox.setChecked(True)
                selected_count += 1
            elif checkbox:
                checkbox.setChecked(False)

    def update_ui_state(self):
        """更新UI状态"""
        # 检查文件是否都已选择
        test_file_valid = bool(self.test_file_edit.text().strip())
        reference_file_valid = bool(self.reference_file_edit.text().strip())
        files_ready = test_file_valid and reference_file_valid

        # 检查字段是否已选择
        self.update_selected_fields()
        fields_selected = len(self.selected_fields) > 0

        # 更新按钮状态
        self.preview_btn.setEnabled(files_ready)
        self.ok_btn.setEnabled(files_ready and fields_selected)

        # 更新字段选择按钮状态
        has_field_table = self.field_table.rowCount() > 0
        self.select_all_btn.setEnabled(has_field_table)
        self.select_none_btn.setEnabled(has_field_table)
        self.select_core_btn.setEnabled(has_field_table)
        self.select_numeric_btn.setEnabled(has_field_table)

    
    def preview_matching(self):
        """预览数据匹配"""
        try:
            test_path = self.test_file_edit.text().strip()
            reference_path = self.reference_file_edit.text().strip()
            match_column = self.match_column_combo.currentText()
            similarity_threshold = self.similarity_threshold_spin.value()

            if not test_path or not reference_path:
                QMessageBox.warning(self, "警告", "请先选择测试机和对比机的CSV文件")
                return

            self.preview_text.setPlainText("正在预览数据匹配，请稍候...")

            # 执行预览
            preview_result = self.generator.preview_data_matching(
                test_path, reference_path, match_column, similarity_threshold
            )

            # 显示预览结果
            preview_text = f"""数据匹配预览结果:

文件信息:
- 测试机记录数: {preview_result['total_test_records']}
- 对比机记录数: {preview_result['total_reference_records']}

匹配结果:
- 成功匹配: {preview_result['matched_pairs']} 对
- 未匹配测试机记录: {preview_result['unmatched_test']}
- 未匹配对比机记录: {preview_result['unmatched_reference']}
- 匹配率: {preview_result['match_rate']:.2%}

样例匹配 (前5个):
"""

            for i, sample in enumerate(preview_result['sample_matches'], 1):
                preview_text += f"{i}. {sample['test_name']} ↔ {sample['reference_name']} (相似度: {sample['similarity']:.3f})\n"

            if preview_result['matched_pairs'] == 0:
                preview_text += "\n⚠️ 警告: 没有找到匹配的数据对，请检查:\n"
                preview_text += "1. 匹配列是否正确\n"
                preview_text += "2. 相似度阈值是否过高\n"
                preview_text += "3. 文件名格式是否一致\n"

            self.preview_text.setPlainText(preview_text)

            # 切换到预览标签页
            self.tab_widget.setCurrentWidget(self.preview_tab)

        except Exception as e:
            error_msg = f"预览匹配失败: {e}"
            self.preview_text.setPlainText(error_msg)
            self.show_warning("预览错误", error_msg)
            logger.error(f"==liuq debug== 预览匹配失败: {e}")

    def get_configuration(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'test_csv_path': self.test_file_edit.text().strip(),
            'reference_csv_path': self.reference_file_edit.text().strip(),
            'selected_fields': self.selected_fields.copy(),
            'output_path': self.output_file_edit.text().strip() or None,
            'match_column': self.match_column_combo.currentText(),
            'similarity_threshold': self.similarity_threshold_spin.value()
        }

    def _build_match_result_for_export(self) -> Dict[str, Any]:
        """构造或获取匹配对供导出使用。优先使用实时预览流程以确保一致性。"""
        try:
            test_path = self.test_file_edit.text().strip()
            reference_path = self.reference_file_edit.text().strip()
            if not test_path or not reference_path:
                raise ValueError("请先选择测试机和对比机CSV")
            # 直接使用生成器内部的匹配流程（数字序列号）
            test_df = self.generator._read_csv_file(test_path)
            ref_df = self.generator._read_csv_file(reference_path)
            match_result = self.generator._match_by_sequence_number(test_df, ref_df)
            return match_result
        except Exception as e:
            logger.error(f"==liuq debug== 构造匹配对失败: {e}")
            raise

    def open_image_export_dialog(self):
        """打开图片分类导出对话框"""
        try:
            from gui.dialogs.image_export_dialog import ImageExportDialog
            # 字段列表：取交集数值字段（已在字段表加载时可得），此处简化用测试机字段即可
            available_fields = []
            if self.test_field_info:
                numeric_infos = self.test_field_info.get('numeric_fields', [])
                # numeric_infos 是包含 name 等信息的字典列表，这里提取字段名
                for item in numeric_infos:
                    try:
                        name = item.get('name') if isinstance(item, dict) else str(item)
                        if name and name not in available_fields:
                            available_fields.append(name)
                    except Exception:
                        pass
            if not available_fields:
                available_fields = ['SGW_Gray', 'sensorCCT']

            match_result = self._build_match_result_for_export()
            dlg = ImageExportDialog(self, match_result=match_result, available_fields=available_fields)
            dlg.exec_()
        except Exception as e:
            self.show_warning("错误", f"无法打开导出对话框:\n{e}")
            logger.error(f"==liuq debug== 打开图片分类导出对话框失败: {e}")
