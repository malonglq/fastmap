#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段选择组件
==liuq debug== GUI字段选择组件

提供CSV字段选择和管理功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class FieldSelector(ttk.Frame):
    """字段选择组件类"""
    
    def __init__(self, parent, title: str = "选择分析字段",
                 on_selection_changed: Optional[Callable] = None):
        """
        初始化字段选择组件
        
        Args:
            parent: 父窗口
            title: 组件标题
            on_selection_changed: 选择变化回调函数
        """
        super().__init__(parent)
        
        self.title = title
        self.on_selection_changed = on_selection_changed
        self.available_fields = []
        self.field_info = {}
        self.checkboxes = {}
        self.checkbox_vars = {}
        
        self.setup_ui()
        logger.info(f"==liuq debug== 字段选择组件初始化完成: {title}")
    
    def setup_ui(self):
        """设置用户界面 - 紧凑化设计"""
        try:
            # 主框架 - 减少padding
            self.configure(padding="6")

            # 配置网格权重
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)  # 字段列表区域 - 最大化空间

            # 标题和控制按钮框架 - 减少间距
            header_frame = ttk.Frame(self)
            header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 6))
            header_frame.columnconfigure(1, weight=1)

            # 标题标签 - 紧凑化字体，整合统计信息
            self.title_label = ttk.Label(header_frame, text=self.title,
                                        font=('Microsoft YaHei', 11, 'bold'))
            self.title_label.grid(row=0, column=0, sticky='w')
            
            # 控制按钮框架 - 紧凑化按钮
            control_frame = ttk.Frame(header_frame)
            control_frame.grid(row=0, column=2, sticky='e')

            # 全选按钮 - 减小宽度
            self.select_all_button = ttk.Button(control_frame, text="全选",
                                              command=self.select_all, width=6)
            self.select_all_button.grid(row=0, column=0, padx=(0, 3))

            # 全不选按钮 - 减小宽度
            self.select_none_button = ttk.Button(control_frame, text="全不选",
                                               command=self.select_none, width=6)
            self.select_none_button.grid(row=0, column=1, padx=(0, 3))

            # 反选按钮 - 减小宽度
            self.invert_button = ttk.Button(control_frame, text="反选",
                                          command=self.invert_selection, width=6)
            self.invert_button.grid(row=0, column=2)

            # 字段列表框架 - 移除LabelFrame，减少嵌套，最大化空间
            list_frame = ttk.Frame(self)
            list_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 0))
            list_frame.columnconfigure(0, weight=1)
            list_frame.rowconfigure(0, weight=1)

            # 创建滚动框架 - 设置合理的最大高度，确保底部组件可见
            self.canvas = tk.Canvas(list_frame, highlightthickness=0, height=300)
            scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
            self.scrollable_frame = ttk.Frame(self.canvas)
            
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            )
            
            self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
            self.canvas.configure(yscrollcommand=scrollbar.set)
            
            self.canvas.grid(row=0, column=0, sticky='nsew')
            scrollbar.grid(row=0, column=1, sticky='ns')

            # 移除统计信息框架和提示信息，统计信息将整合到标题中
            # 这样可以为字段列表释放更多空间

            # 配置权重 - 确保字段列表区域最大化
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            
            # 初始状态
            self.update_ui_state()
            
        except Exception as e:
            logger.error(f"==liuq debug== 字段选择组件UI设置失败: {e}")
            messagebox.showerror("错误", f"界面初始化失败: {e}")
    
    def set_fields(self, fields: List[str], field_info: Optional[Dict[str, Any]] = None):
        """
        设置可用字段
        
        Args:
            fields: 字段名列表
            field_info: 字段信息字典
        """
        try:
            self.available_fields = fields.copy()
            self.field_info = field_info or {}
            
            # 清除现有的复选框
            self.clear_checkboxes()
            
            # 创建新的复选框
            self.create_checkboxes()
            
            # 更新界面状态
            self.update_ui_state()
            
            logger.info(f"==liuq debug== 设置字段完成，共 {len(fields)} 个字段")
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置字段失败: {e}")
            messagebox.showerror("错误", f"设置字段失败: {e}")
    
    def clear_checkboxes(self):
        """清除现有的复选框"""
        try:
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            self.checkboxes.clear()
            self.checkbox_vars.clear()
            
        except Exception as e:
            logger.error(f"==liuq debug== 清除复选框失败: {e}")
    
    def create_checkboxes(self):
        """创建字段复选框"""
        try:
            for i, field in enumerate(self.available_fields):
                # 创建复选框变量
                var = tk.BooleanVar()
                self.checkbox_vars[field] = var
                
                # 创建复选框框架
                checkbox_frame = ttk.Frame(self.scrollable_frame)
                checkbox_frame.grid(row=i, column=0, sticky='ew', pady=2)
                checkbox_frame.columnconfigure(1, weight=1)
                
                # 复选框 - 直接在复选框上显示字段名
                checkbox = ttk.Checkbutton(
                    checkbox_frame,
                    text=field,
                    variable=var,
                    command=self.on_selection_change
                )
                checkbox.grid(row=0, column=0, sticky='w', columnspan=2)
                self.checkboxes[field] = checkbox
                
                # 字段信息标签
                info_text = self.get_field_info_text(field)
                if info_text:
                    info_label = ttk.Label(checkbox_frame, text=info_text,
                                          font=('Arial', 9), foreground='gray')
                    info_label.grid(row=0, column=2, sticky='e')
                
                # 配置框架权重
                self.scrollable_frame.columnconfigure(0, weight=1)
            
            # 更新滚动区域
            self.scrollable_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            logger.error(f"==liuq debug== 创建复选框失败: {e}")
    
    def get_field_info_text(self, field: str) -> str:
        """
        获取字段信息文本
        
        Args:
            field: 字段名
            
        Returns:
            信息文本
        """
        try:
            if field not in self.field_info:
                return ""
            
            info = self.field_info[field]
            
            # 构建信息文本
            info_parts = []
            
            if info.get('is_numeric', False):
                info_parts.append("数值")
            else:
                info_parts.append("文本")
            
            if 'dtype' in info:
                info_parts.append(f"({info['dtype']})")
            
            if 'null_count' in info and info['null_count'] > 0:
                info_parts.append(f"缺失:{info['null_count']}")
            
            return " ".join(info_parts)
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取字段信息文本失败: {e}")
            return ""
    
    def on_selection_change(self):
        """选择变化处理"""
        try:
            # 更新统计信息
            self.update_stats()
            
            # 调用回调函数
            if self.on_selection_changed:
                selected_fields = self.get_selected_fields()
                self.on_selection_changed(selected_fields)
            
        except Exception as e:
            logger.error(f"==liuq debug== 选择变化处理失败: {e}")
    
    def select_all(self):
        """全选"""
        try:
            for var in self.checkbox_vars.values():
                var.set(True)
            
            self.on_selection_change()
            logger.info("==liuq debug== 全选字段")
            
        except Exception as e:
            logger.error(f"==liuq debug== 全选失败: {e}")
    
    def select_none(self):
        """全不选"""
        try:
            for var in self.checkbox_vars.values():
                var.set(False)
            
            self.on_selection_change()
            logger.info("==liuq debug== 全不选字段")
            
        except Exception as e:
            logger.error(f"==liuq debug== 全不选失败: {e}")
    
    def invert_selection(self):
        """反选"""
        try:
            for var in self.checkbox_vars.values():
                var.set(not var.get())
            
            self.on_selection_change()
            logger.info("==liuq debug== 反选字段")
            
        except Exception as e:
            logger.error(f"==liuq debug== 反选失败: {e}")
    
    def get_selected_fields(self) -> List[str]:
        """
        获取选择的字段
        
        Returns:
            选择的字段列表
        """
        try:
            selected = []
            for field, var in self.checkbox_vars.items():
                if var.get():
                    selected.append(field)
            
            return selected
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取选择字段失败: {e}")
            return []
    
    def get_selected_numeric_fields(self) -> List[str]:
        """
        获取选择的数值字段
        
        Returns:
            选择的数值字段列表
        """
        try:
            selected = []
            for field, var in self.checkbox_vars.items():
                if var.get() and self.is_numeric_field(field):
                    selected.append(field)
            
            return selected
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取选择数值字段失败: {e}")
            return []
    
    def is_numeric_field(self, field: str) -> bool:
        """
        检查字段是否为数值类型
        
        Args:
            field: 字段名
            
        Returns:
            是否为数值字段
        """
        try:
            if field in self.field_info:
                return self.field_info[field].get('is_numeric', False)
            return False
            
        except Exception as e:
            logger.error(f"==liuq debug== 检查数值字段失败: {e}")
            return False
    
    def update_stats(self):
        """更新统计信息 - 整合到标题中"""
        try:
            total_fields = len(self.available_fields)
            selected_fields = len(self.get_selected_fields())
            numeric_fields = sum(1 for field in self.available_fields
                               if self.is_numeric_field(field))

            # 将统计信息整合到标题中，节省空间
            title_with_stats = f"{self.title} (已选择: {selected_fields}/{total_fields}, 数值字段: {numeric_fields})"
            self.title_label.configure(text=title_with_stats)

        except Exception as e:
            logger.error(f"==liuq debug== 更新统计信息失败: {e}")
    
    def update_ui_state(self):
        """更新界面状态"""
        try:
            has_fields = len(self.available_fields) > 0
            
            # 启用/禁用控制按钮
            state = 'normal' if has_fields else 'disabled'
            self.select_all_button.configure(state=state)
            self.select_none_button.configure(state=state)
            self.invert_button.configure(state=state)
            
            # 更新统计信息
            self.update_stats()
            
        except Exception as e:
            logger.error(f"==liuq debug== 更新界面状态失败: {e}")
    
    def set_selected_fields(self, fields: List[str]):
        """
        设置选择的字段
        
        Args:
            fields: 要选择的字段列表
        """
        try:
            # 先清除所有选择
            self.select_none()
            
            # 选择指定字段
            for field in fields:
                if field in self.checkbox_vars:
                    self.checkbox_vars[field].set(True)
            
            self.on_selection_change()
            logger.info(f"==liuq debug== 设置选择字段: {fields}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置选择字段失败: {e}")
    
    def clear_fields(self):
        """清除所有字段"""
        try:
            self.available_fields.clear()
            self.field_info.clear()
            self.clear_checkboxes()
            self.update_ui_state()

            logger.info("==liuq debug== 清除所有字段")

        except Exception as e:
            logger.error(f"==liuq debug== 清除字段失败: {e}")

    def update_title(self, new_title: str):
        """更新标题"""
        try:
            self.title = new_title
            self.title_label.configure(text=new_title)
            logger.info(f"==liuq debug== 字段选择器标题已更新: {new_title}")
        except Exception as e:
            logger.error(f"==liuq debug== 更新标题失败: {e}")
