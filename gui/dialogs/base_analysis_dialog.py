#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析对话框基类

==liuq debug== FastMapV2 分析对话框基类
提供通用的分析对话框功能和工作线程管理

作者: 龙sir团队
创建时间: 2025-09-01
版本: 1.0.0
描述: 为各种分析对话框提供统一的基础功能，包括UI布局、线程管理、状态持久化等
"""

import logging
import json
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTabWidget, QWidget, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class BaseWorker(QThread):
    """
    分析工作线程基类
    
    提供统一的线程信号定义和基础工作流程
    """
    
    # 信号定义
    progress_updated = pyqtSignal(int, str)  # 进度更新 (百分比, 消息)
    analysis_completed = pyqtSignal(object)  # 分析完成 (结果对象)
    analysis_failed = pyqtSignal(str)        # 分析失败 (错误消息)
    
    def __init__(self):
        """初始化工作线程"""
        super().__init__()
        logger.debug("==liuq debug== BaseWorker初始化")
    
    def run(self):
        """
        执行分析任务（子类必须重写此方法）
        
        子类应该：
        1. 发送progress_updated信号更新进度
        2. 完成时发送analysis_completed信号
        3. 出错时发送analysis_failed信号
        """
        raise NotImplementedError("子类必须实现run方法")


class BaseAnalysisDialog(QDialog):
    """
    分析对话框基类
    
    提供统一的对话框布局、线程管理、状态持久化等功能
    """
    
    def __init__(self, parent=None, title: str = "分析对话框", 
                 size: Tuple[int, int] = (800, 600), 
                 state_file: Optional[Path] = None):
        """
        初始化分析对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            size: 对话框大小 (宽度, 高度)
            state_file: 状态持久化文件路径
        """
        super().__init__(parent)
        
        self.title = title
        self.size = size
        self.state_file = state_file
        self.current_worker = None
        
        # 设置对话框属性
        self.setWindowTitle(title)
        self.resize(*size)
        self.setModal(True)
        
        # 创建UI
        self.setup_base_ui()
        self.setup_ui()  # 子类重写此方法
        
        logger.info(f"==liuq debug== {title}初始化完成")
    
    def setup_base_ui(self):
        """设置基础UI布局"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题区域
        self.create_title_area(main_layout)
        
        # 进度条区域
        self.create_progress_area(main_layout)
        
        # 主内容区域（标签页）
        self.create_content_area(main_layout)
        
        # 底部按钮区域
        self.create_button_area(main_layout)
    
    def create_title_area(self, parent_layout):
        """创建标题区域"""
        title_frame = QFrame()
        title_frame.setFrameStyle(QFrame.StyledPanel)
        title_layout = QVBoxLayout(title_frame)
        
        # 主标题
        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        
        parent_layout.addWidget(title_frame)
    
    def create_progress_area(self, parent_layout):
        """创建进度条区域"""
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setVisible(False)
        progress_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(progress_frame)
    
    def create_content_area(self, parent_layout):
        """创建主内容区域"""
        # 标签页容器
        self.tab_widget = QTabWidget()
        parent_layout.addWidget(self.tab_widget)
    
    def create_button_area(self, parent_layout):
        """创建底部按钮区域"""
        button_layout = QHBoxLayout()
        
        # 预览按钮
        self.preview_btn = QPushButton("预览")
        self.preview_btn.setVisible(False)  # 默认隐藏，子类按需显示
        self.preview_btn.setMinimumHeight(35)
        button_layout.addWidget(self.preview_btn)
        
        # 弹簧
        button_layout.addStretch()
        
        # 开始分析按钮
        self.analyze_btn = QPushButton("开始分析")
        self.analyze_btn.setMinimumHeight(35)
        self.analyze_btn.clicked.connect(self.start_analysis)
        button_layout.addWidget(self.analyze_btn)
        
        # 导出按钮
        self.export_btn = QPushButton("导出报告")
        self.export_btn.setMinimumHeight(35)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_report)
        button_layout.addWidget(self.export_btn)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setMinimumHeight(35)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        parent_layout.addLayout(button_layout)
    
    def setup_ui(self):
        """设置用户界面（子类重写此方法）"""
        pass
    
    def start_worker(self, worker: BaseWorker, button: QPushButton = None):
        """
        启动工作线程
        
        Args:
            worker: 工作线程实例
            button: 触发按钮（用于禁用/启用）
        """
        try:
            # 停止当前工作线程
            if self.current_worker and self.current_worker.isRunning():
                self.current_worker.quit()
                self.current_worker.wait()
            
            self.current_worker = worker
            
            # 连接信号
            worker.progress_updated.connect(self.on_progress_updated)
            worker.analysis_completed.connect(self.on_analysis_completed)
            worker.analysis_failed.connect(self.on_analysis_failed)
            
            # 禁用按钮
            if button:
                button.setEnabled(False)
            
            # 显示进度条
            self.show_progress()
            
            # 启动线程
            worker.start()
            
            logger.info("==liuq debug== 工作线程已启动")
            
        except Exception as e:
            logger.error(f"==liuq debug== 启动工作线程失败: {e}")
            self.on_analysis_failed(str(e))
    
    def show_progress(self):
        """显示进度条"""
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("准备开始...")
    
    def hide_progress(self):
        """隐藏进度条"""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
    
    def on_progress_updated(self, progress: int, message: str):
        """进度更新处理"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def on_analysis_completed(self, result):
        """分析完成处理（子类重写此方法）"""
        self.hide_progress()
        self.analyze_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        logger.info("==liuq debug== 分析完成")
    
    def on_analysis_failed(self, error_message: str):
        """分析失败处理"""
        self.hide_progress()
        self.analyze_btn.setEnabled(True)
        QMessageBox.critical(self, "分析失败", f"分析过程中发生错误:\n{error_message}")
        logger.error(f"==liuq debug== 分析失败: {error_message}")
    
    def start_analysis(self):
        """开始分析（子类重写此方法）"""
        QMessageBox.information(self, "提示", "请在子类中实现start_analysis方法")
    
    def export_report(self):
        """导出报告（子类重写此方法）"""
        QMessageBox.information(self, "提示", "请在子类中实现export_report方法")
    
    def save_state(self, state_data: Dict[str, Any]):
        """保存状态到文件"""
        if not self.state_file:
            return
        
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"==liuq debug== 状态已保存到: {self.state_file}")
        except Exception as e:
            logger.error(f"==liuq debug== 保存状态失败: {e}")
    
    def load_state(self) -> Dict[str, Any]:
        """从文件加载状态"""
        if not self.state_file or not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            logger.debug(f"==liuq debug== 状态已从文件加载: {self.state_file}")
            return state_data
        except Exception as e:
            logger.error(f"==liuq debug== 加载状态失败: {e}")
            return {}

    def load_saved_state(self):
        """加载保存的状态并应用到UI（子类可重写此方法）"""
        try:
            state_data = self.load_state()
            if state_data:
                # 如果子类实现了apply_state方法，则调用它
                if hasattr(self, 'apply_state') and callable(getattr(self, 'apply_state')):
                    self.apply_state(state_data)
                    logger.info("==liuq debug== 已应用保存的状态")
                else:
                    logger.debug("==liuq debug== 子类未实现apply_state方法")
            else:
                logger.debug("==liuq debug== 没有找到保存的状态")
        except Exception as e:
            logger.error(f"==liuq debug== 加载保存状态失败: {e}")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止工作线程
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.quit()
            self.current_worker.wait(3000)  # 等待3秒
        
        super().closeEvent(event)
        logger.debug(f"==liuq debug== {self.title}已关闭")
