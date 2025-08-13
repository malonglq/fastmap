#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map多维度分析配置对话框
==liuq debug== FastMapV2 Map多维度分析配置对话框

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 16:15:00 +08:00; Reason: 阶段3-创建Map多维度分析配置对话框; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: Map多维度分析的配置界面
"""

import logging
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem,
    QCheckBox, QGroupBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QTabWidget, QWidget, QMessageBox,
    QProgressBar, QComboBox, QHeaderView, QFormLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from pathlib import Path

from core.services.map_multi_dimensional_report_generator import MapMultiDimensionalReportGenerator
from core.models.map_data import MapConfiguration
from core.models.scene_classification_config import SceneClassificationConfig

logger = logging.getLogger(__name__)


class AnalysisPreviewWorker(QThread):
    """分析预览工作线程"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, generator: MapMultiDimensionalReportGenerator, 
                 map_configuration: MapConfiguration,
                 include_multi_dimensional: bool,
                 classification_config: Optional[SceneClassificationConfig]):
        super().__init__()
        self.generator = generator
        self.map_configuration = map_configuration
        self.include_multi_dimensional = include_multi_dimensional
        self.classification_config = classification_config
    
    def run(self):
        try:
            preview = self.generator.preview_analysis_scope(
                self.map_configuration,
                self.include_multi_dimensional,
                self.classification_config
            )
            self.finished.emit(preview)
        except Exception as e:
            self.error.emit(str(e))


class MapMultiDimensionalDialog(QDialog):
    """
    Map多维度分析配置对话框
    
    提供Map数据概览、多维度分析配置、输出设置等功能
    """
    
    def __init__(self, map_configuration: MapConfiguration, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map多维度分析配置")
        self.setModal(True)
        self.resize(800, 600)
        
        # 初始化组件
        self.map_configuration = map_configuration
        self.generator = MapMultiDimensionalReportGenerator()
        self.classification_config = SceneClassificationConfig()
        
        # 设置UI
        self.setup_ui()
        
        # 连接信号
        self.setup_signals()
        
        # 加载Map数据概览
        self.load_map_overview()
        
        logger.info("==liuq debug== Map多维度分析配置对话框初始化完成")
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # Map数据概览标签页
        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "Map数据概览")
        
        # 多维度分析配置标签页
        self.config_tab = self.create_config_tab()
        self.tab_widget.addTab(self.config_tab, "多维度分析配置")
        
        # 输出设置标签页
        self.output_tab = self.create_output_tab()
        self.tab_widget.addTab(self.output_tab, "输出设置")
        
        # 预览标签页
        self.preview_tab = self.create_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "预览")
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("预览分析范围")
        self.preview_btn.clicked.connect(self.preview_analysis)
        button_layout.addWidget(self.preview_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("生成报告")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def create_overview_tab(self) -> QWidget:
        """创建Map数据概览标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        self.device_type_label = QLabel("未知")
        basic_layout.addRow("设备类型:", self.device_type_label)
        
        self.map_points_count_label = QLabel("0")
        basic_layout.addRow("Map点数量:", self.map_points_count_label)
        
        self.has_base_boundary_label = QLabel("否")
        basic_layout.addRow("包含基础边界:", self.has_base_boundary_label)
        
        self.reference_points_count_label = QLabel("0")
        basic_layout.addRow("参考点数量:", self.reference_points_count_label)
        
        layout.addWidget(basic_group)
        
        # 场景分布
        scene_group = QGroupBox("场景分布")
        scene_layout = QVBoxLayout(scene_group)
        
        self.scene_table = QTableWidget()
        self.scene_table.setColumnCount(2)
        self.scene_table.setHorizontalHeaderLabels(["场景类型", "Map点数量"])
        self.scene_table.horizontalHeader().setStretchLastSection(True)
        scene_layout.addWidget(self.scene_table)
        
        layout.addWidget(scene_group)
        
        # 坐标和权重范围
        range_group = QGroupBox("数据范围")
        range_layout = QFormLayout(range_group)
        
        self.coordinate_range_label = QLabel("未知")
        range_layout.addRow("坐标范围:", self.coordinate_range_label)
        
        self.weight_range_label = QLabel("未知")
        range_layout.addRow("权重范围:", self.weight_range_label)
        
        layout.addWidget(range_group)
        
        layout.addStretch()
        return tab
    
    def create_config_tab(self) -> QWidget:
        """创建多维度分析配置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 分析选项
        analysis_group = QGroupBox("分析选项")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.include_multi_dimensional_cb = QCheckBox("包含多维度场景分析")
        self.include_multi_dimensional_cb.setChecked(True)
        self.include_multi_dimensional_cb.stateChanged.connect(self.on_multi_dimensional_changed)
        analysis_layout.addWidget(self.include_multi_dimensional_cb)
        
        info_label = QLabel("多维度分析将提供详细的场景分类统计和参数分布信息")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        analysis_layout.addWidget(info_label)
        
        layout.addWidget(analysis_group)
        
        # 场景分类配置
        self.classification_group = QGroupBox("场景分类配置")
        classification_layout = QFormLayout(self.classification_group)
        
        # BV阈值配置
        self.indoor_bv_threshold_spin = QDoubleSpinBox()
        self.indoor_bv_threshold_spin.setRange(-10.0, 20.0)
        self.indoor_bv_threshold_spin.setValue(4.0)
        self.indoor_bv_threshold_spin.setSingleStep(0.5)
        classification_layout.addRow("室内BV阈值:", self.indoor_bv_threshold_spin)
        
        self.night_bv_threshold_spin = QDoubleSpinBox()
        self.night_bv_threshold_spin.setRange(-10.0, 20.0)
        self.night_bv_threshold_spin.setValue(-2.0)
        self.night_bv_threshold_spin.setSingleStep(0.5)
        classification_layout.addRow("夜景BV阈值:", self.night_bv_threshold_spin)
        
        # IR阈值配置
        self.ir_threshold_spin = QDoubleSpinBox()
        self.ir_threshold_spin.setRange(0.0, 10.0)
        self.ir_threshold_spin.setValue(1.0)
        self.ir_threshold_spin.setSingleStep(0.1)
        classification_layout.addRow("IR比值阈值:", self.ir_threshold_spin)
        
        layout.addWidget(self.classification_group)
        
        # 高级选项
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QFormLayout(advanced_group)
        
        self.enable_accuracy_analysis_cb = QCheckBox("启用分类准确性分析")
        self.enable_accuracy_analysis_cb.setChecked(True)
        advanced_layout.addRow("", self.enable_accuracy_analysis_cb)
        
        self.enable_parameter_distribution_cb = QCheckBox("启用参数分布分析")
        self.enable_parameter_distribution_cb.setChecked(True)
        advanced_layout.addRow("", self.enable_parameter_distribution_cb)
        
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        return tab
    
    def create_output_tab(self) -> QWidget:
        """创建输出设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 输出路径
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)
        
        path_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("选择报告输出路径（可选，留空使用默认路径）...")
        path_layout.addWidget(self.output_path_edit)
        
        self.browse_output_btn = QPushButton("浏览")
        self.browse_output_btn.clicked.connect(self.browse_output_path)
        path_layout.addWidget(self.browse_output_btn)
        
        output_layout.addLayout(path_layout)
        layout.addWidget(output_group)
        
        # 报告模板
        template_group = QGroupBox("报告模板")
        template_layout = QFormLayout(template_group)
        
        self.template_combo = QComboBox()
        self.template_combo.addItems(["map_analysis", "default"])
        self.template_combo.setCurrentText("map_analysis")
        template_layout.addRow("模板类型:", self.template_combo)
        
        layout.addWidget(template_group)
        
        layout.addStretch()
        return tab
    
    def create_preview_tab(self) -> QWidget:
        """创建预览标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 预览信息
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlainText("请点击'预览分析范围'按钮查看分析范围和预计处理时间。")
        layout.addWidget(self.preview_text)
        
        return tab
    
    def setup_signals(self):
        """设置信号连接"""
        pass
    
    def load_map_overview(self):
        """加载Map数据概览"""
        try:
            summary = self.generator.get_map_configuration_summary(self.map_configuration)
            
            # 更新基本信息
            self.device_type_label.setText(summary.get('device_type', '未知'))
            self.map_points_count_label.setText(str(summary.get('total_map_points', 0)))
            self.has_base_boundary_label.setText("是" if summary.get('has_base_boundary', False) else "否")
            self.reference_points_count_label.setText(str(len(self.map_configuration.reference_points)))
            
            # 更新场景分布表格
            scene_distribution = summary.get('scene_distribution', {})
            self.scene_table.setRowCount(len(scene_distribution))
            
            for row, (scene_type, count) in enumerate(scene_distribution.items()):
                self.scene_table.setItem(row, 0, QTableWidgetItem(scene_type))
                self.scene_table.setItem(row, 1, QTableWidgetItem(str(count)))
            
            # 更新范围信息
            coord_range = summary.get('coordinate_range', {})
            if coord_range:
                coord_text = f"X: [{coord_range.get('x_min', 0):.1f}, {coord_range.get('x_max', 0):.1f}], Y: [{coord_range.get('y_min', 0):.1f}, {coord_range.get('y_max', 0):.1f}]"
                self.coordinate_range_label.setText(coord_text)
            
            weight_range = summary.get('weight_range', {})
            if weight_range:
                weight_text = f"[{weight_range.get('min', 0):.3f}, {weight_range.get('max', 0):.3f}], 平均: {weight_range.get('avg', 0):.3f}"
                self.weight_range_label.setText(weight_text)
            
            logger.info("==liuq debug== Map数据概览加载完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== 加载Map数据概览失败: {e}")
            QMessageBox.warning(self, "加载错误", f"加载Map数据概览失败:\n{e}")
    
    def on_multi_dimensional_changed(self):
        """多维度分析选项变化"""
        enabled = self.include_multi_dimensional_cb.isChecked()
        self.classification_group.setEnabled(enabled)
    
    def browse_output_path(self):
        """浏览输出路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择报告输出路径",
            "map_multi_dimensional_report.html",
            "HTML文件 (*.html);;所有文件 (*)"
        )
        
        if file_path:
            self.output_path_edit.setText(file_path)
    
    def preview_analysis(self):
        """预览分析范围"""
        try:
            self.preview_text.setPlainText("正在预览分析范围，请稍候...")
            
            # 获取当前配置
            include_multi_dimensional = self.include_multi_dimensional_cb.isChecked()
            classification_config = self.get_classification_config() if include_multi_dimensional else None
            
            # 创建预览工作线程
            self.preview_worker = AnalysisPreviewWorker(
                self.generator,
                self.map_configuration,
                include_multi_dimensional,
                classification_config
            )
            self.preview_worker.finished.connect(self.on_preview_finished)
            self.preview_worker.error.connect(self.on_preview_error)
            self.preview_worker.start()
            
        except Exception as e:
            error_msg = f"预览分析范围失败: {e}"
            self.preview_text.setPlainText(error_msg)
            logger.error(f"==liuq debug== {error_msg}")
    
    def on_preview_finished(self, preview: Dict[str, Any]):
        """预览完成"""
        try:
            # 格式化预览信息
            preview_text = "分析范围预览:\n\n"
            
            # Map摘要
            map_summary = preview.get('map_summary', {})
            preview_text += f"设备类型: {map_summary.get('device_type', '未知')}\n"
            preview_text += f"Map点数量: {map_summary.get('total_map_points', 0)}\n"
            preview_text += f"场景分布: {map_summary.get('scene_distribution', {})}\n\n"
            
            # 分析范围
            analysis_scope = preview.get('analysis_scope', {})
            preview_text += "分析内容:\n"
            preview_text += f"• 传统Map分析: {'是' if analysis_scope.get('traditional_analysis', False) else '否'}\n"
            preview_text += f"• 多维度场景分析: {'是' if analysis_scope.get('multi_dimensional_analysis', False) else '否'}\n"
            preview_text += f"• 场景分类分析: {'是' if analysis_scope.get('scene_classification', False) else '否'}\n\n"
            
            # 预计处理时间
            preview_text += f"预计处理时间: {preview.get('estimated_processing_time', '未知')}\n\n"
            
            # 输出章节
            output_sections = preview.get('output_sections', [])
            preview_text += "报告章节:\n"
            for section in output_sections:
                preview_text += f"• {section}\n"
            
            self.preview_text.setPlainText(preview_text)
            
            # 切换到预览标签页
            self.tab_widget.setCurrentWidget(self.preview_tab)
            
        except Exception as e:
            error_msg = f"处理预览结果失败: {e}"
            self.preview_text.setPlainText(error_msg)
            logger.error(f"==liuq debug== {error_msg}")
    
    def on_preview_error(self, error_msg: str):
        """预览错误"""
        self.preview_text.setPlainText(f"预览分析范围失败: {error_msg}")
        QMessageBox.warning(self, "预览错误", f"预览分析范围失败:\n{error_msg}")
    
    def get_classification_config(self) -> SceneClassificationConfig:
        """获取场景分类配置"""
        config = SceneClassificationConfig()
        
        # 更新阈值配置
        config.indoor_bv_threshold = self.indoor_bv_threshold_spin.value()
        config.night_bv_threshold = self.night_bv_threshold_spin.value()
        config.ir_threshold = self.ir_threshold_spin.value()
        
        return config
    
    def get_configuration(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'map_configuration': self.map_configuration,
            'include_multi_dimensional': self.include_multi_dimensional_cb.isChecked(),
            'classification_config': self.get_classification_config() if self.include_multi_dimensional_cb.isChecked() else None,
            'output_path': self.output_path_edit.text().strip() or None,
            'template_name': self.template_combo.currentText()
        }
