#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastMapV2 UI主题演示程序
==liuq debug== FastMapV2 UI主题演示程序

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 17:20:00 +08:00; Reason: 阶段4-创建UI主题演示程序; Principle_Applied: 用户体验验证;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 演示FastMapV2的新主题样式系统
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QTabWidget, QTableWidget, QTableWidgetItem, QLineEdit, QTextEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QRadioButton,
    QProgressBar, QSlider, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from gui.styles.theme import FastMapTheme, ThemeType, get_theme, set_theme
from gui.styles.style_utils import (
    create_styled_button, create_title_label, create_card_group,
    create_status_indicator, create_progress_overlay, show_progress_overlay, hide_progress_overlay,
    apply_modern_table_style, get_icon_button_style
)


class ThemeDemoWindow(QMainWindow):
    """主题演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastMapV2 UI主题演示 - 阶段4界面优化")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化进度遮罩
        self.progress_overlay = None
        
        # 设置UI
        self.setup_ui()
        
        print("==liuq debug== FastMapV2 UI主题演示启动")
    
    def setup_ui(self):
        """设置用户界面"""
        # 应用主题
        theme = get_theme()
        self.setStyleSheet(theme.get_complete_stylesheet())
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 标题
        title = create_title_label("FastMapV2 UI主题演示", level=1)
        layout.addWidget(title)
        
        # 主题切换按钮
        theme_layout = QHBoxLayout()
        
        self.light_theme_btn = create_styled_button("浅色主题", "primary", icon="☀️")
        self.light_theme_btn.clicked.connect(self.switch_to_light_theme)
        theme_layout.addWidget(self.light_theme_btn)
        
        self.dark_theme_btn = create_styled_button("深色主题", "secondary", icon="🌙")
        self.dark_theme_btn.clicked.connect(self.switch_to_dark_theme)
        theme_layout.addWidget(self.dark_theme_btn)
        
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 按钮演示标签页
        self.create_button_demo_tab()
        
        # 输入控件演示标签页
        self.create_input_demo_tab()
        
        # 表格演示标签页
        self.create_table_demo_tab()
        
        # 状态指示器演示标签页
        self.create_status_demo_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 创建进度遮罩
        self.progress_overlay = create_progress_overlay(self, "演示进度处理...")
    
    def create_button_demo_tab(self):
        """创建按钮演示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # 按钮类型演示
        button_group = create_card_group("按钮样式演示")
        button_layout = QVBoxLayout(button_group)
        
        # 主要按钮行
        primary_layout = QHBoxLayout()
        primary_layout.addWidget(create_styled_button("主要按钮", "primary", icon="✨"))
        primary_layout.addWidget(create_styled_button("次要按钮", "secondary", icon="📝"))
        primary_layout.addWidget(create_styled_button("成功按钮", "success", icon="✅"))
        primary_layout.addWidget(create_styled_button("警告按钮", "warning", icon="⚠️"))
        primary_layout.addWidget(create_styled_button("错误按钮", "error", icon="❌"))
        primary_layout.addStretch()
        button_layout.addLayout(primary_layout)
        
        # 幽灵按钮行
        ghost_layout = QHBoxLayout()
        ghost_layout.addWidget(create_styled_button("幽灵按钮", "ghost", icon="👻"))
        
        disabled_btn = create_styled_button("禁用按钮", "primary", icon="🚫")
        disabled_btn.setEnabled(False)
        ghost_layout.addWidget(disabled_btn)
        
        # 图标按钮
        icon_config = get_icon_button_style("🔧", "设置")
        icon_btn = create_styled_button("", "ghost")
        icon_btn.setText(icon_config["text"])
        icon_btn.setStyleSheet(icon_config["style"])
        icon_btn.setToolTip(icon_config["tooltip"])
        ghost_layout.addWidget(icon_btn)
        
        ghost_layout.addStretch()
        button_layout.addLayout(ghost_layout)
        
        # 功能按钮
        function_layout = QHBoxLayout()
        
        progress_btn = create_styled_button("显示进度", "primary", icon="⏳")
        progress_btn.clicked.connect(self.show_progress_demo)
        function_layout.addWidget(progress_btn)
        
        hide_progress_btn = create_styled_button("隐藏进度", "secondary", icon="⏹️")
        hide_progress_btn.clicked.connect(self.hide_progress_demo)
        function_layout.addWidget(hide_progress_btn)
        
        function_layout.addStretch()
        button_layout.addLayout(function_layout)
        
        layout.addWidget(button_group)
        
        self.tab_widget.addTab(tab, "按钮演示")
    
    def create_input_demo_tab(self):
        """创建输入控件演示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # 输入控件演示
        input_group = create_card_group("输入控件样式演示")
        input_layout = QVBoxLayout(input_group)
        
        # 文本输入
        text_layout = QHBoxLayout()
        text_layout.addWidget(create_title_label("文本输入:", level=5))
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText("请输入文本...")
        text_layout.addWidget(line_edit)
        
        input_layout.addLayout(text_layout)
        
        # 多行文本
        textarea_layout = QHBoxLayout()
        textarea_layout.addWidget(create_title_label("多行文本:", level=5))
        
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("请输入多行文本...")
        text_edit.setMaximumHeight(100)
        textarea_layout.addWidget(text_edit)
        
        input_layout.addLayout(textarea_layout)
        
        # 数值输入
        number_layout = QHBoxLayout()
        number_layout.addWidget(create_title_label("数值输入:", level=5))
        
        spin_box = QSpinBox()
        spin_box.setRange(0, 100)
        spin_box.setValue(50)
        number_layout.addWidget(spin_box)
        
        double_spin_box = QDoubleSpinBox()
        double_spin_box.setRange(0.0, 100.0)
        double_spin_box.setValue(25.5)
        double_spin_box.setSingleStep(0.1)
        number_layout.addWidget(double_spin_box)
        
        number_layout.addStretch()
        input_layout.addLayout(number_layout)
        
        # 下拉框
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(create_title_label("下拉选择:", level=5))
        
        combo_box = QComboBox()
        combo_box.addItems(["选项1", "选项2", "选项3", "选项4"])
        combo_layout.addWidget(combo_box)
        
        combo_layout.addStretch()
        input_layout.addLayout(combo_layout)
        
        # 复选框和单选框
        check_layout = QHBoxLayout()
        check_layout.addWidget(create_title_label("选择控件:", level=5))
        
        check_box = QCheckBox("复选框选项")
        check_box.setChecked(True)
        check_layout.addWidget(check_box)
        
        radio_box = QRadioButton("单选框选项")
        radio_box.setChecked(True)
        check_layout.addWidget(radio_box)
        
        check_layout.addStretch()
        input_layout.addLayout(check_layout)
        
        layout.addWidget(input_group)
        
        self.tab_widget.addTab(tab, "输入控件")
    
    def create_table_demo_tab(self):
        """创建表格演示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # 表格演示
        table_group = create_card_group("表格样式演示")
        table_layout = QVBoxLayout(table_group)
        
        # 创建演示表格
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["报告类型", "生成时间", "状态", "操作"])
        
        # 添加演示数据
        demo_data = [
            ("EXIF对比分析", "2025-08-05 17:20:00", "已完成", "打开"),
            ("Map多维度分析", "2025-08-05 17:15:00", "进行中", "查看"),
            ("预留功能报告", "2025-08-05 17:10:00", "失败", "重试"),
            ("数据对比报告", "2025-08-05 17:05:00", "已完成", "打开"),
        ]
        
        table.setRowCount(len(demo_data))
        
        for row, (report_type, time, status, action) in enumerate(demo_data):
            table.setItem(row, 0, QTableWidgetItem(report_type))
            table.setItem(row, 1, QTableWidgetItem(time))
            table.setItem(row, 2, QTableWidgetItem(status))
            
            # 操作按钮
            action_btn = create_styled_button(action, "secondary")
            table.setCellWidget(row, 3, action_btn)
        
        # 应用现代化表格样式
        apply_modern_table_style(table)
        
        table_layout.addWidget(table)
        layout.addWidget(table_group)
        
        self.tab_widget.addTab(tab, "表格演示")
    
    def create_status_demo_tab(self):
        """创建状态指示器演示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # 状态指示器演示
        status_group = create_card_group("状态指示器演示")
        status_layout = QVBoxLayout(status_group)
        
        # 状态指示器行
        status_row1 = QHBoxLayout()
        status_row1.addWidget(create_status_indicator("success", "操作成功"))
        status_row1.addWidget(create_status_indicator("warning", "注意事项"))
        status_row1.addWidget(create_status_indicator("error", "操作失败"))
        status_row1.addWidget(create_status_indicator("info", "提示信息"))
        status_row1.addStretch()
        status_layout.addLayout(status_row1)
        
        # 进度条演示
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(create_title_label("进度条:", level=5))
        
        progress_bar = QProgressBar()
        progress_bar.setValue(75)
        progress_layout.addWidget(progress_bar)
        
        status_layout.addLayout(progress_layout)
        
        # 滑块演示
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(create_title_label("滑块:", level=5))
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(60)
        slider_layout.addWidget(slider)
        
        status_layout.addLayout(slider_layout)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        status_layout.addWidget(separator)
        
        layout.addWidget(status_group)
        
        self.tab_widget.addTab(tab, "状态指示器")
    
    def switch_to_light_theme(self):
        """切换到浅色主题"""
        set_theme(ThemeType.LIGHT)
        self.apply_current_theme()
        print("==liuq debug== 切换到浅色主题")
    
    def switch_to_dark_theme(self):
        """切换到深色主题"""
        set_theme(ThemeType.DARK)
        self.apply_current_theme()
        print("==liuq debug== 切换到深色主题")
    
    def apply_current_theme(self):
        """应用当前主题"""
        theme = get_theme()
        self.setStyleSheet(theme.get_complete_stylesheet())
        
        # 重新应用表格样式
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            for table in tab.findChildren(QTableWidget):
                apply_modern_table_style(table)
    
    def show_progress_demo(self):
        """显示进度演示"""
        show_progress_overlay(self.progress_overlay, "演示进度处理中...")
        
        # 3秒后自动隐藏
        QTimer.singleShot(3000, self.hide_progress_demo)
        
        print("==liuq debug== 显示进度演示")
    
    def hide_progress_demo(self):
        """隐藏进度演示"""
        hide_progress_overlay(self.progress_overlay)
        print("==liuq debug== 隐藏进度演示")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("FastMapV2 UI主题演示")
    app.setApplicationVersion("1.0.0")
    
    # 创建主窗口
    window = ThemeDemoWindow()
    window.show()
    
    print("==liuq debug== FastMapV2 UI主题演示启动")
    print("==liuq debug== 功能说明:")
    print("  1. 展示统一的主题样式系统")
    print("  2. 演示各种按钮类型和状态")
    print("  3. 展示输入控件的现代化样式")
    print("  4. 演示表格的优化显示效果")
    print("  5. 展示状态指示器和进度提示")
    print("  6. 支持浅色/深色主题切换")
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
