#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析报告标签页
==liuq debug== FastMapV2分析报告标签页

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 14:35:00 +08:00; Reason: 阶段1基础架构重构-创建分析报告标签页; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 重构后的分析报告标签页，统一管理三种报告类型
"""

import logging
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QSplitter,
    QGroupBox, QTextEdit, QHeaderView, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from datetime import datetime

from core.services.reporting.unified_report_manager import UnifiedReportManager, ReportHistoryItem
from core.interfaces.report_generator import ReportType
from gui.styles.style_utils import (
    create_styled_button, create_title_label, create_card_group,
    apply_modern_table_style, create_progress_overlay, show_progress_overlay, hide_progress_overlay
)
from gui.styles.theme import get_theme

logger = logging.getLogger(__name__)


class AnalysisReportTab(QWidget):
    """
    重构后的分析报告标签页
    
    统一管理三种报告类型：
    1. EXIF对比分析报告
    2. Map多维度分析报告  
    3. 预留报告类型
    """
    
    # 信号定义
    status_message = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        初始化分析报告标签页

        Args:
            parent: 父窗口
        """
        super().__init__(parent)

        # 初始化报告管理器
        self.report_manager = UnifiedReportManager()

        # 初始化进度遮罩
        self.progress_overlay = None

        # 设置UI
        self.setup_ui()

        # 连接信号
        self.setup_signals()

        # 刷新历史记录
        self.refresh_history()

        logger.info("==liuq debug== 分析报告标签页初始化完成")
    
    def setup_ui(self):
        """设置用户界面"""
        # 应用主题样式
        theme = get_theme()
        self.setStyleSheet(theme.get_complete_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # 标题区域
        self.create_title_section(layout)

        # 主要内容区域（使用分割器）
        splitter = QSplitter(Qt.Vertical)

        # 报告类型选择区域
        report_buttons_widget = self.create_report_buttons_section()
        splitter.addWidget(report_buttons_widget)

        # 报告历史区域
        history_widget = self.create_history_section()
        splitter.addWidget(history_widget)

        # 设置分割器比例
        splitter.setStretchFactor(0, 1)  # 按钮区域
        splitter.setStretchFactor(1, 2)  # 历史区域

        layout.addWidget(splitter)

        # 创建进度遮罩
        self.progress_overlay = create_progress_overlay(self, "正在生成报告，请稍候...")
    
    def create_title_section(self, layout: QVBoxLayout):
        """创建标题区域"""
        title_label = create_title_label("分析报告中心", level=1)
        layout.addWidget(title_label)
    
    def create_report_buttons_section(self) -> QWidget:
        """创建报告类型选择区域"""
        group_box = create_card_group("报告类型选择")

        layout = QHBoxLayout(group_box)
        layout.setSpacing(16)

        # 1. EXIF对比分析按钮
        self.exif_comparison_btn = create_styled_button(
            "EXIF对比分析",
            button_type="primary",
            min_height=80,
            icon="📊"
        )
        self.exif_comparison_btn.clicked.connect(self.open_exif_comparison_dialog)
        layout.addWidget(self.exif_comparison_btn)

        # 2. Map多维度分析按钮
        self.map_analysis_btn = create_styled_button(
            "Map多维度分析",
            button_type="success",
            min_height=80,
            icon="🗺️"
        )
        self.map_analysis_btn.clicked.connect(self.open_map_analysis_dialog)
        layout.addWidget(self.map_analysis_btn)

        # 3. 预留功能按钮
        self.reserved_btn = create_styled_button(
            "预留功能",
            button_type="ghost",
            min_height=80,
            icon="🔮"
        )
        self.reserved_btn.clicked.connect(self.open_reserved_dialog)
        self.reserved_btn.setEnabled(False)  # 暂时禁用
        layout.addWidget(self.reserved_btn)

        return group_box
    
    def create_history_section(self) -> QWidget:
        """创建报告历史区域"""
        group_box = create_card_group("报告历史记录")

        layout = QVBoxLayout(group_box)

        # 历史记录操作按钮
        button_layout = QHBoxLayout()

        self.refresh_btn = create_styled_button("刷新", button_type="secondary", icon="🔄")
        self.refresh_btn.clicked.connect(self.refresh_history)
        button_layout.addWidget(self.refresh_btn)

        self.clear_history_btn = create_styled_button("清空历史", button_type="warning", icon="🗑️")
        self.clear_history_btn.clicked.connect(self.clear_history)
        button_layout.addWidget(self.clear_history_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["报告类型", "生成时间", "文件路径", "操作"])

        # 应用现代化表格样式
        apply_modern_table_style(self.history_table)

        # 设置表格属性
        header = self.history_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        layout.addWidget(self.history_table)
        
        return group_box
    
    def setup_signals(self):
        """设置信号连接"""
        # 双击历史记录打开文件
        self.history_table.cellDoubleClicked.connect(self.open_report_file)
    
    def open_exif_comparison_dialog(self):
        """打开EXIF对比分析对话框"""
        try:
            from gui.dialogs.exif_comparison_dialog import ExifComparisonDialog
            from core.services.reporting.exif_comparison_report_generator import ExifComparisonReportGenerator

            # 创建对话框
            dialog = ExifComparisonDialog(self)

            # 显示对话框
            if dialog.exec_() == QDialog.Accepted:
                # 获取配置
                config = dialog.get_configuration()

                # 生成报告
                self.generate_exif_comparison_report(config)

        except ImportError as e:
            logger.error(f"==liuq debug== 导入EXIF对比分析模块失败: {e}")
            QMessageBox.critical(
                self,
                "模块错误",
                f"EXIF对比分析模块加载失败:\n{e}\n\n"
                "请检查0_csv_compare模块是否正确安装。"
            )
        except Exception as e:
            logger.error(f"==liuq debug== 打开EXIF对比分析对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开EXIF对比分析对话框失败:\n{e}")

    def generate_exif_comparison_report(self, config: Dict[str, Any]):
        """生成EXIF对比分析报告"""
        try:
            from core.services.reporting.exif_comparison_report_generator import ExifComparisonReportGenerator
            from core.interfaces.report_generator import ReportType

            # 显示进度遮罩
            show_progress_overlay(self.progress_overlay, "正在生成EXIF对比分析报告...")
            self.status_message.emit("正在生成EXIF对比分析报告，请稍候...")

            # 创建报告生成器
            generator = ExifComparisonReportGenerator()

            # 注册到报告管理器（如果还没有注册）
            if ReportType.EXIF_COMPARISON not in self.report_manager.get_available_report_types():
                self.report_manager.register_generator(generator)

            # 生成报告
            report_path = self.report_manager.generate_report(
                ReportType.EXIF_COMPARISON,
                config
            )

            # 隐藏进度遮罩
            hide_progress_overlay(self.progress_overlay)

            # 刷新历史记录
            self.refresh_history()

            # 询问是否打开报告
            reply = QMessageBox.question(
                self,
                "报告生成完成",
                f"EXIF对比分析报告已生成:\n{report_path}\n\n是否立即打开？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.open_report_file_by_path(report_path)

            self.status_message.emit("EXIF对比分析报告生成完成")
            logger.info(f"==liuq debug== EXIF对比分析报告生成完成: {report_path}")

        except Exception as e:
            # 隐藏进度遮罩
            hide_progress_overlay(self.progress_overlay)

            error_msg = f"EXIF对比分析报告生成失败: {e}"
            logger.error(f"==liuq debug== {error_msg}")
            QMessageBox.critical(self, "生成错误", error_msg)
            self.status_message.emit("EXIF对比分析报告生成失败")
    
    def open_map_analysis_dialog(self):
        """打开Map多维度分析对话框"""
        try:
            # 检查是否已有Map分析数据
            main_window = self.get_main_window()
            if not main_window or not hasattr(main_window, 'map_configuration'):
                QMessageBox.warning(
                    self,
                    "警告",
                    "请先在Map分析标签页进行Map数据分析\n\n"
                    "步骤：\n"
                    "1. 切换到Map分析标签页\n"
                    "2. 选择XML配置文件\n"
                    "3. 点击'开始分析'按钮\n"
                    "4. 分析完成后返回此处生成报告"
                )
                return

            map_configuration = main_window.map_configuration
            if not map_configuration:
                QMessageBox.warning(
                    self,
                    "警告",
                    "Map配置数据为空，请重新进行Map分析"
                )
                return

            from gui.dialogs.map_multi_dimensional_dialog import MapMultiDimensionalDialog
            from core.services.reporting.map_multi_dimensional_report_generator import MapMultiDimensionalReportGenerator

            # 创建对话框
            dialog = MapMultiDimensionalDialog(map_configuration, self)

            # 显示对话框
            if dialog.exec_() == QDialog.Accepted:
                # 获取配置
                config = dialog.get_configuration()

                # 生成报告
                self.generate_map_multi_dimensional_report(config)

        except ImportError as e:
            logger.error(f"==liuq debug== 导入Map多维度分析模块失败: {e}")
            QMessageBox.critical(
                self,
                "模块错误",
                f"Map多维度分析模块加载失败:\n{e}\n\n"
                "请检查相关模块是否正确安装。"
            )
        except Exception as e:
            logger.error(f"==liuq debug== 打开Map多维度分析对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开Map多维度分析对话框失败:\n{e}")

    def generate_map_multi_dimensional_report(self, config: Dict[str, Any]):
        """生成Map多维度分析报告"""
        try:
            from core.services.reporting.map_multi_dimensional_report_generator import MapMultiDimensionalReportGenerator
            from core.interfaces.report_generator import ReportType

            # 显示进度提示
            self.status_message.emit("正在生成Map多维度分析报告，请稍候...")

            # 创建报告生成器
            generator = MapMultiDimensionalReportGenerator()

            # 注册到报告管理器（如果还没有注册）
            if ReportType.MAP_MULTI_DIMENSIONAL not in self.report_manager.get_available_report_types():
                self.report_manager.register_generator(generator)

            # 生成报告
            report_path = self.report_manager.generate_report(
                ReportType.MAP_MULTI_DIMENSIONAL,
                config
            )

            # 刷新历史记录
            self.refresh_history()

            # 询问是否打开报告
            reply = QMessageBox.question(
                self,
                "报告生成完成",
                f"Map多维度分析报告已生成:\n{report_path}\n\n是否立即打开？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.open_report_file_by_path(report_path)

            self.status_message.emit("Map多维度分析报告生成完成")
            logger.info(f"==liuq debug== Map多维度分析报告生成完成: {report_path}")

        except Exception as e:
            error_msg = f"Map多维度分析报告生成失败: {e}"
            logger.error(f"==liuq debug== {error_msg}")
            QMessageBox.critical(self, "生成错误", error_msg)
            self.status_message.emit("Map多维度分析报告生成失败")
    
    def open_reserved_dialog(self):
        """打开预留功能对话框"""
        QMessageBox.information(
            self, 
            "预留功能", 
            "此功能为未来扩展预留\n\n"
            "将在阶段5实现可插拔的报告类型架构"
        )
        logger.info("==liuq debug== 预留功能对话框")
    
    def refresh_history(self):
        """刷新历史记录"""
        try:
            history = self.report_manager.get_history(limit=50)
            
            self.history_table.setRowCount(len(history))
            
            for row, item in enumerate(history):
                # 报告类型
                type_item = QTableWidgetItem(item.report_name)
                self.history_table.setItem(row, 0, type_item)
                
                # 生成时间
                time_str = item.generation_time.strftime("%Y-%m-%d %H:%M:%S")
                time_item = QTableWidgetItem(time_str)
                self.history_table.setItem(row, 1, time_item)
                
                # 文件路径
                path_item = QTableWidgetItem(item.file_path)
                self.history_table.setItem(row, 2, path_item)
                
                # 操作按钮
                open_btn = QPushButton("📂 打开")
                open_btn.clicked.connect(lambda checked, path=item.file_path: self.open_report_file_by_path(path))
                self.history_table.setCellWidget(row, 3, open_btn)
            
            logger.info(f"==liuq debug== 刷新历史记录: {len(history)}条")
            
        except Exception as e:
            logger.error(f"==liuq debug== 刷新历史记录失败: {e}")
            QMessageBox.warning(self, "错误", f"刷新历史记录失败: {e}")
    
    def clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(
            self, 
            "确认清空", 
            "确定要清空所有历史记录吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.report_manager.clear_history()
            self.refresh_history()
            self.status_message.emit("历史记录已清空")
    
    def open_report_file(self, row: int, column: int):
        """双击打开报告文件"""
        if column == 2:  # 文件路径列
            path_item = self.history_table.item(row, 2)
            if path_item:
                self.open_report_file_by_path(path_item.text())
    
    def open_report_file_by_path(self, file_path: str):
        """根据路径打开报告文件"""
        try:
            import webbrowser
            import os
            
            if os.path.exists(file_path):
                from utils.browser_utils import open_html_report
                open_html_report(file_path)
                self.status_message.emit(f"已打开报告: {file_path}")
                logger.info(f"==liuq debug== 打开报告文件: {file_path}")
            else:
                QMessageBox.warning(self, "文件不存在", f"报告文件不存在:\n{file_path}")
                
        except Exception as e:
            logger.error(f"==liuq debug== 打开报告文件失败: {e}")
            QMessageBox.warning(self, "错误", f"打开报告文件失败: {e}")
    
    def get_main_window(self):
        """获取主窗口引用"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'map_configuration'):
                return parent
            parent = parent.parent()
        return None
