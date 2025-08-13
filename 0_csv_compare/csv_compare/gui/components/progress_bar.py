#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度条组件
==liuq debug== GUI进度条和状态显示组件

提供进度显示和状态更新功能
"""

import tkinter as tk
from tkinter import ttk
import logging
import threading
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class ProgressBar(ttk.Frame):
    """进度条组件类"""
    
    def __init__(self, parent, title: str = "处理进度",
                 show_percentage: bool = True,
                 show_status: bool = True):
        """
        初始化进度条组件
        
        Args:
            parent: 父窗口
            title: 组件标题
            show_percentage: 是否显示百分比
            show_status: 是否显示状态文本
        """
        super().__init__(parent)
        
        self.title = title
        self.show_percentage = show_percentage
        self.show_status = show_status
        self.is_running = False
        self.current_value = 0
        self.max_value = 100
        
        self.setup_ui()
        logger.info(f"==liuq debug== 进度条组件初始化完成: {title}")
    
    def setup_ui(self):
        """设置用户界面"""
        try:
            # 主框架 - 紧凑化padding
            self.configure(padding="3")

            # 标题标签 - 由于外层已有标题，这里不显示
            if self.title:
                title_label = ttk.Label(self, text=self.title,
                                       font=('Microsoft YaHei', 10, 'bold'))
                title_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 4))
            
            # 进度条框架 - 紧凑化间距
            progress_frame = ttk.Frame(self)
            progress_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 2))
            progress_frame.columnconfigure(0, weight=1)
            
            # 进度条
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(
                progress_frame,
                variable=self.progress_var,
                maximum=100,
                length=400,
                mode='determinate'
            )
            self.progress_bar.grid(row=0, column=0, sticky='ew', padx=(0, 10))
            
            # 百分比标签
            if self.show_percentage:
                self.percentage_var = tk.StringVar()
                self.percentage_var.set("0%")
                
                self.percentage_label = ttk.Label(progress_frame, 
                                                 textvariable=self.percentage_var,
                                                 font=('Arial', 10, 'bold'),
                                                 width=6)
                self.percentage_label.grid(row=0, column=1)
            
            # 状态信息框架 - 紧凑化间距
            if self.show_status:
                status_frame = ttk.Frame(self)
                status_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 0))
                status_frame.columnconfigure(1, weight=1)
                
                # 状态标签
                status_title = ttk.Label(status_frame, text="状态: ")
                status_title.grid(row=0, column=0, sticky='w')
                
                self.status_var = tk.StringVar()
                self.status_var.set("就绪")
                
                self.status_label = ttk.Label(status_frame, 
                                            textvariable=self.status_var,
                                            font=('Arial', 10))
                self.status_label.grid(row=0, column=1, sticky='w')
                
                # 详细信息标签
                self.detail_var = tk.StringVar()
                self.detail_var.set("")
                
                self.detail_label = ttk.Label(status_frame,
                                            textvariable=self.detail_var,
                                            font=('Arial', 9),
                                            foreground='gray')
                self.detail_label.grid(row=1, column=0, columnspan=2, sticky='w')
            
            # 配置权重
            self.columnconfigure(0, weight=1)
            
            # 初始状态
            self.reset()
            
        except Exception as e:
            logger.error(f"==liuq debug== 进度条组件UI设置失败: {e}")
    
    def start(self, max_value: int = 100, status: str = "开始处理..."):
        """
        开始进度
        
        Args:
            max_value: 最大值
            status: 状态文本
        """
        try:
            self.max_value = max_value
            self.current_value = 0
            self.is_running = True
            
            self.progress_bar.configure(maximum=max_value)
            self.update_progress(0, status)
            
            logger.info(f"==liuq debug== 进度条开始: max={max_value}, status={status}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 进度条开始失败: {e}")
    
    def update_progress(self, value: int, status: str = "", detail: str = ""):
        """
        更新进度
        
        Args:
            value: 当前值
            status: 状态文本
            detail: 详细信息
        """
        try:
            self.current_value = min(value, self.max_value)
            percentage = (self.current_value / self.max_value * 100) if self.max_value > 0 else 0
            
            # 更新进度条
            self.progress_var.set(percentage)
            
            # 更新百分比
            if self.show_percentage:
                self.percentage_var.set(f"{percentage:.1f}%")
            
            # 更新状态
            if self.show_status:
                if status:
                    self.status_var.set(status)
                if detail:
                    self.detail_var.set(detail)
            
            # 强制更新界面
            self.update_idletasks()
            

            
        except Exception as e:
            logger.error(f"==liuq debug== 进度更新失败: {e}")
    
    def increment(self, step: int = 1, status: str = "", detail: str = ""):
        """
        增加进度
        
        Args:
            step: 增加步数
            status: 状态文本
            detail: 详细信息
        """
        try:
            new_value = self.current_value + step
            self.update_progress(new_value, status, detail)
            
        except Exception as e:
            logger.error(f"==liuq debug== 进度增加失败: {e}")
    
    def set_percentage(self, percentage: float, status: str = "", detail: str = ""):
        """
        设置百分比进度
        
        Args:
            percentage: 百分比 (0-100)
            status: 状态文本
            detail: 详细信息
        """
        try:
            value = int(self.max_value * percentage / 100)
            self.update_progress(value, status, detail)
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置百分比失败: {e}")
    
    def complete(self, status: str = "处理完成", detail: str = ""):
        """
        完成进度
        
        Args:
            status: 完成状态文本
            detail: 详细信息
        """
        try:
            self.update_progress(self.max_value, status, detail)
            self.is_running = False
            
            logger.info(f"==liuq debug== 进度条完成: {status}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 进度条完成失败: {e}")
    
    def reset(self, status: str = "就绪"):
        """
        重置进度条
        
        Args:
            status: 重置状态文本
        """
        try:
            self.current_value = 0
            self.is_running = False
            
            self.progress_var.set(0)
            
            if self.show_percentage:
                self.percentage_var.set("0%")
            
            if self.show_status:
                self.status_var.set(status)
                self.detail_var.set("")
            
            logger.info(f"==liuq debug== 进度条重置: {status}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 进度条重置失败: {e}")
    
    def set_indeterminate(self, status: str = "处理中..."):
        """
        设置为不确定进度模式
        
        Args:
            status: 状态文本
        """
        try:
            self.progress_bar.configure(mode='indeterminate')
            self.progress_bar.start(10)  # 10ms间隔
            self.is_running = True
            
            if self.show_percentage:
                self.percentage_var.set("...")
            
            if self.show_status:
                self.status_var.set(status)
            
            logger.info(f"==liuq debug== 设置不确定进度模式: {status}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置不确定进度模式失败: {e}")
    
    def stop_indeterminate(self, status: str = "完成"):
        """
        停止不确定进度模式
        
        Args:
            status: 状态文本
        """
        try:
            self.progress_bar.stop()
            self.progress_bar.configure(mode='determinate')
            self.is_running = False
            
            if self.show_percentage:
                self.percentage_var.set("100%")
            
            if self.show_status:
                self.status_var.set(status)
            
            logger.info(f"==liuq debug== 停止不确定进度模式: {status}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 停止不确定进度模式失败: {e}")
    
    def set_error(self, error_message: str):
        """
        设置错误状态
        
        Args:
            error_message: 错误信息
        """
        try:
            self.is_running = False
            
            if self.show_status:
                self.status_var.set("错误")
                self.detail_var.set(error_message)
                self.status_label.configure(foreground='red')
            
            logger.error(f"==liuq debug== 进度条错误状态: {error_message}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置错误状态失败: {e}")
    
    def set_warning(self, warning_message: str):
        """
        设置警告状态
        
        Args:
            warning_message: 警告信息
        """
        try:
            if self.show_status:
                self.status_var.set("警告")
                self.detail_var.set(warning_message)
                self.status_label.configure(foreground='orange')
            
            logger.warning(f"==liuq debug== 进度条警告状态: {warning_message}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置警告状态失败: {e}")
    
    def set_success(self, success_message: str = "操作成功完成"):
        """
        设置成功状态
        
        Args:
            success_message: 成功信息
        """
        try:
            self.complete("成功", success_message)
            
            if self.show_status:
                self.status_label.configure(foreground='green')
            
            logger.info(f"==liuq debug== 进度条成功状态: {success_message}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置成功状态失败: {e}")
    
    def get_current_progress(self) -> dict:
        """
        获取当前进度信息
        
        Returns:
            进度信息字典
        """
        try:
            percentage = (self.current_value / self.max_value * 100) if self.max_value > 0 else 0
            
            return {
                'current_value': self.current_value,
                'max_value': self.max_value,
                'percentage': percentage,
                'is_running': self.is_running,
                'status': self.status_var.get() if self.show_status else "",
                'detail': self.detail_var.get() if self.show_status else ""
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取进度信息失败: {e}")
            return {
                'current_value': 0,
                'max_value': 100,
                'percentage': 0,
                'is_running': False,
                'status': "错误",
                'detail': str(e)
            }
