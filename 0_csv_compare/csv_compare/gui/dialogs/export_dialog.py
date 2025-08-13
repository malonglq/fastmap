#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片导出对话框模块
提供用户友好的图片分类导出配置界面
==liuq debug== 图片导出对话框实现
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# ==liuq debug== 全局变量记住上次打开的目录
_last_source_directory = str(Path.home())
_last_output_directory = str(Path.home() / 'Desktop')


class ExportDialog:
    """图片导出配置对话框"""
    
    def __init__(self, parent: tk.Tk, classification_result: Dict[str, List[Dict[str, Any]]]):
        """
        初始化导出对话框
        
        Args:
            parent: 父窗口
            classification_result: 图片分类结果
        """
        self.parent = parent
        self.classification_result = classification_result
        self.result = None
        
        # 对话框窗口
        self.dialog = None
        
        # 用户选择变量
        self.export_large = tk.BooleanVar(value=True)
        self.export_medium = tk.BooleanVar(value=True)
        self.export_small = tk.BooleanVar(value=True)
        self.export_no_change = tk.BooleanVar(value=True)
        
        # 目录路径变量
        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        # 统计信息
        self.large_count = len(classification_result['large_changes'])
        self.medium_count = len(classification_result['medium_changes'])
        self.small_count = len(classification_result['small_changes'])
        self.no_change_count = len(classification_result.get('no_changes', []))
        self.total_count = self.large_count + self.medium_count + self.small_count + self.no_change_count

        # 获取主字段名称和类型（从分类结果中的第一个图片信息获取）
        self.primary_field_name = self.get_primary_field_name()
        self.is_cct_field = self.get_primary_field_type()

        logger.info(f"==liuq debug== 导出对话框初始化完成，总图片数: {self.total_count}")
        logger.info(f"==liuq debug== 使用主字段: {self.primary_field_name}")
        logger.info(f"==liuq debug== 字段类型: {'CCT字段' if self.is_cct_field else '非CCT字段'}")

    def get_primary_field_name(self) -> str:
        """
        从分类结果中获取主字段名称

        Returns:
            主字段名称，默认为'sensorCCT'
        """
        try:
            # 从任意一个分类中获取第一个图片的主字段名称
            for category_images in self.classification_result.values():
                if category_images:
                    first_image = category_images[0]
                    primary_field_name = first_image.get('primary_field_name', 'sensorCCT')
                    return primary_field_name

            # 如果没有找到，返回默认值
            return 'sensorCCT'

        except Exception as e:
            logger.warning(f"==liuq debug== 获取主字段名称失败: {e}")
            return 'sensorCCT'

    def get_primary_field_type(self) -> bool:
        """
        从分类结果中获取主字段类型

        Returns:
            是否为CCT字段，默认为True
        """
        try:
            # 从任意一个分类中获取第一个图片的字段类型信息
            for category_images in self.classification_result.values():
                if category_images:
                    first_image = category_images[0]
                    is_cct_field = first_image.get('is_cct_field', True)
                    return is_cct_field

            # 如果没有找到，根据字段名判断
            return self.is_cct_field_by_name(self.primary_field_name)

        except Exception as e:
            logger.warning(f"==liuq debug== 获取主字段类型失败: {e}")
            return self.is_cct_field_by_name(self.primary_field_name)

    def is_cct_field_by_name(self, field_name: str) -> bool:
        """
        根据字段名判断是否为CCT字段

        Args:
            field_name: 字段名

        Returns:
            是否为CCT字段
        """
        try:
            if not field_name:
                return False

            # 转换为小写进行比较
            field_lower = field_name.lower()

            # 检查字段名是否包含CCT相关关键词
            cct_keywords = ['cct', 'color_temperature', 'colortemperature', 'sensor_cct', 'sensorcct']

            for keyword in cct_keywords:
                if keyword in field_lower:
                    return True

            return False

        except Exception as e:
            logger.warning(f"==liuq debug== 判断CCT字段失败: {e}")
            return False

    def show(self) -> Optional[Dict[str, Any]]:
        """
        显示对话框并返回用户配置
        
        Returns:
            用户配置字典，如果取消则返回None
        """
        try:
            self.create_dialog()
            self.setup_ui()
            
            # 显示对话框（模态）
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            self.dialog.focus_set()
            
            # 居中显示
            self.center_dialog()
            
            # 等待用户操作
            self.parent.wait_window(self.dialog)
            
            return self.result
            
        except Exception as e:
            logger.error(f"==liuq debug== 显示导出对话框失败: {e}")
            messagebox.showerror("错误", f"显示导出对话框失败: {e}")
            return None
    
    def create_dialog(self):
        """创建对话框窗口"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("图片分类导出配置")
        self.dialog.geometry("650x500")  # 进一步减少窗口高度，消除空白区域
        self.dialog.resizable(True, True)  # 允许调整大小以便调试

        # 设置图标（如果有的话）
        try:
            self.dialog.iconbitmap(self.parent.iconbitmap())
        except:
            pass
    
    def setup_ui(self):
        """设置用户界面"""
        try:
            # 主框架 - 紧凑化设计，减少padding
            main_frame = ttk.Frame(self.dialog, padding="5")
            main_frame.pack(fill='both', expand=True)
            
            # 标题
            self.setup_title(main_frame)
            
            # 分类统计区域
            self.setup_statistics(main_frame)
            
            # 分类选择区域
            self.setup_category_selection(main_frame)
            
            # 目录选择区域
            self.setup_directory_selection(main_frame)
            
            # 按钮区域
            self.setup_buttons(main_frame)
            
            logger.info("==liuq debug== 导出对话框UI设置完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== 导出对话框UI设置失败: {e}")
            raise
    
    def setup_title(self, parent):
        """设置标题区域"""
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill='x', pady=(0, 4))  # 进一步减少底部间距

        title_label = ttk.Label(title_frame,
                               text="图片分类导出配置",
                               font=('Arial', 14, 'bold'))
        title_label.pack(anchor='w')

        # 移除空的subtitle_label以节省空间
    
    def setup_statistics(self, parent):
        """设置分类统计区域"""
        stats_frame = ttk.LabelFrame(parent, text="分类统计", padding="5")  # 紧凑化：减少padding
        stats_frame.pack(fill='x', pady=(0, 4))  # 进一步减少底部间距
        
        # 创建统计网格
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill='x')
        
        # 配置列权重
        for i in range(5):
            stats_grid.columnconfigure(i, weight=1)

        # 统计卡片 - 根据字段类型显示不同的阈值描述
        self.create_stat_card(stats_grid, "总计", self.total_count, "blue", 0)

        if self.is_cct_field:
            # CCT字段使用绝对值阈值
            self.create_stat_card(stats_grid, "大变化 (>500K)", self.large_count, "red", 1)
            self.create_stat_card(stats_grid, "中变化 (100K-500K)", self.medium_count, "orange", 2)
            self.create_stat_card(stats_grid, "小变化 (0K-100K)", self.small_count, "green", 3)
            self.create_stat_card(stats_grid, "无变化 (=0K)", self.no_change_count, "gray", 4)
        else:
            # 非CCT字段使用百分比阈值
            self.create_stat_card(stats_grid, "大变化 (>10%)", self.large_count, "red", 1)
            self.create_stat_card(stats_grid, "中变化 (1%-10%)", self.medium_count, "orange", 2)
            self.create_stat_card(stats_grid, "小变化 (0%-1%)", self.small_count, "green", 3)
            self.create_stat_card(stats_grid, "无变化 (=0%)", self.no_change_count, "gray", 4)
    
    def create_stat_card(self, parent, title, count, color, column):
        """创建统计卡片"""
        card_frame = ttk.Frame(parent, relief='solid', borderwidth=1)
        card_frame.grid(row=0, column=column, padx=3, pady=3, sticky='ew')  # 紧凑化：减少间距

        # 数值
        count_label = ttk.Label(card_frame, text=str(count),
                               font=('Arial', 16, 'bold'),
                               foreground=color)
        count_label.pack(pady=(5, 2))  # 紧凑化：减少垂直间距

        # 标题
        title_label = ttk.Label(card_frame, text=title,
                               font=('Arial', 9),
                               foreground='gray')
        title_label.pack(pady=(0, 5))  # 紧凑化：减少底部间距
    
    def setup_category_selection(self, parent):
        """设置分类选择区域"""
        selection_frame = ttk.LabelFrame(parent, text="选择要导出的分类", padding="5")  # 紧凑化：减少padding
        selection_frame.pack(fill='x', pady=(0, 4))  # 进一步减少底部间距

        # 根据字段类型显示不同的阈值描述
        if self.is_cct_field:
            # CCT字段使用绝对值阈值
            large_check = ttk.Checkbutton(selection_frame,
                                         text=f"大变化 ({self.primary_field_name}变化>500K) - {self.large_count} 个图片",
                                         variable=self.export_large)
            large_check.pack(anchor='w', pady=1)  # 紧凑化：减少垂直间距

            medium_check = ttk.Checkbutton(selection_frame,
                                          text=f"中变化 ({self.primary_field_name}变化100K-500K) - {self.medium_count} 个图片",
                                          variable=self.export_medium)
            medium_check.pack(anchor='w', pady=1)  # 紧凑化：减少垂直间距

            small_check = ttk.Checkbutton(selection_frame,
                                         text=f"小变化 ({self.primary_field_name}变化0K-100K) - {self.small_count} 个图片",
                                         variable=self.export_small)
            small_check.pack(anchor='w', pady=1)  # 紧凑化：减少垂直间距

            no_change_check = ttk.Checkbutton(selection_frame,
                                            text=f"无变化 ({self.primary_field_name}变化=0K) - {self.no_change_count} 个图片",
                                            variable=self.export_no_change)
            no_change_check.pack(anchor='w', pady=1)  # 紧凑化：减少垂直间距
        else:
            # 非CCT字段使用百分比阈值
            large_check = ttk.Checkbutton(selection_frame,
                                         text=f"大变化 ({self.primary_field_name}变化>10%) - {self.large_count} 个图片",
                                         variable=self.export_large)
            large_check.pack(anchor='w', pady=1)  # 紧凑化：减少垂直间距

            medium_check = ttk.Checkbutton(selection_frame,
                                          text=f"中变化 ({self.primary_field_name}变化1%-10%) - {self.medium_count} 个图片",
                                          variable=self.export_medium)
            medium_check.pack(anchor='w', pady=1)  # 紧凑化：减少垂直间距

            small_check = ttk.Checkbutton(selection_frame,
                                         text=f"小变化 ({self.primary_field_name}变化0%-1%) - {self.small_count} 个图片",
                                         variable=self.export_small)
            small_check.pack(anchor='w', pady=1)  # 紧凑化：减少垂直间距

            no_change_check = ttk.Checkbutton(selection_frame,
                                            text=f"无变化 ({self.primary_field_name}变化=0%) - {self.no_change_count} 个图片",
                                            variable=self.export_no_change)
            no_change_check.pack(anchor='w', pady=1)  # 紧凑化：减少垂直间距
        
        # 全选/全不选按钮
        button_frame = ttk.Frame(selection_frame)
        button_frame.pack(fill='x', pady=(5, 0))  # 紧凑化：减少顶部间距

        select_all_btn = ttk.Button(button_frame, text="全选",
                                   command=self.select_all_categories)
        select_all_btn.pack(side='left', padx=(0, 5))

        select_none_btn = ttk.Button(button_frame, text="全不选",
                                    command=self.select_no_categories)
        select_none_btn.pack(side='left')
    
    def setup_directory_selection(self, parent):
        """设置目录选择区域"""
        dir_frame = ttk.LabelFrame(parent, text="目录设置", padding="5")  # 紧凑化：减少padding
        dir_frame.pack(fill='x', pady=(0, 4))  # 进一步减少底部间距

        # 源图片目录
        source_frame = ttk.Frame(dir_frame)
        source_frame.pack(fill='x', pady=(0, 4))  # 进一步减少底部间距

        source_label = ttk.Label(source_frame, text="源图片目录:", font=('Arial', 10, 'bold'))
        source_label.pack(anchor='w', pady=(0, 3))  # 紧凑化：减少底部间距

        source_path_frame = ttk.Frame(source_frame)
        source_path_frame.pack(fill='x')  # 紧凑化：移除底部间距
        source_path_frame.columnconfigure(0, weight=1)

        source_entry = ttk.Entry(source_path_frame, textvariable=self.source_dir,
                                state='readonly', font=('Arial', 9))
        source_entry.grid(row=0, column=0, sticky='ew', padx=(0, 8))  # 紧凑化：减少右侧间距

        source_btn = ttk.Button(source_path_frame, text="浏览...",
                               command=self.select_source_directory, width=12)
        source_btn.grid(row=0, column=1)

        # 输出目录
        output_frame = ttk.Frame(dir_frame)
        output_frame.pack(fill='x', pady=(3, 0))  # 进一步减少顶部间距

        output_label = ttk.Label(output_frame, text="输出目录:", font=('Arial', 10, 'bold'))
        output_label.pack(anchor='w', pady=(0, 3))  # 紧凑化：减少底部间距

        output_path_frame = ttk.Frame(output_frame)
        output_path_frame.pack(fill='x')
        output_path_frame.columnconfigure(0, weight=1)

        output_entry = ttk.Entry(output_path_frame, textvariable=self.output_dir,
                                state='readonly', font=('Arial', 9))
        output_entry.grid(row=0, column=0, sticky='ew', padx=(0, 8))  # 紧凑化：减少右侧间距

        output_btn = ttk.Button(output_path_frame, text="浏览...",
                               command=self.select_output_directory, width=12)
        output_btn.grid(row=0, column=1)
    
    def setup_buttons(self, parent):
        """设置按钮区域"""
        # 修改为正常流式布局，消除大片空白区域
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(4, 5))  # 进一步减少顶部间距，消除空白

        # 取消按钮
        cancel_btn = ttk.Button(button_frame, text="取消",
                               command=self.cancel_export,
                               width=12)
        cancel_btn.pack(side='right', padx=(8, 0))  # 紧凑化：减少左侧间距

        # 确认导出按钮
        export_btn = ttk.Button(button_frame, text="开始导出",
                               command=self.confirm_export,
                               style='Accent.TButton',
                               width=12)
        export_btn.pack(side='right')

        logger.info("==liuq debug== 导出对话框按钮区域设置完成")
    
    def select_all_categories(self):
        """全选所有分类"""
        self.export_large.set(True)
        self.export_medium.set(True)
        self.export_small.set(True)
        self.export_no_change.set(True)

    def select_no_categories(self):
        """取消选择所有分类"""
        self.export_large.set(False)
        self.export_medium.set(False)
        self.export_small.set(False)
        self.export_no_change.set(False)
    
    def select_source_directory(self):
        """选择源图片目录"""
        global _last_source_directory

        # ==liuq debug== 优先使用当前设置，其次使用记忆的目录
        initial_dir = self.source_dir.get() or _last_source_directory

        directory = filedialog.askdirectory(
            title="选择源图片目录",
            initialdir=initial_dir
        )
        if directory:
            # ==liuq debug== 更新记忆的目录
            _last_source_directory = directory
            self.source_dir.set(directory)
            logger.info(f"==liuq debug== 选择源图片目录: {directory}")
            logger.info(f"==liuq debug== 记忆源目录更新为: {_last_source_directory}")

    def select_output_directory(self):
        """选择输出目录"""
        global _last_output_directory

        # ==liuq debug== 优先使用当前设置，其次使用记忆的目录
        initial_dir = self.output_dir.get() or _last_output_directory

        directory = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=initial_dir
        )
        if directory:
            # ==liuq debug== 更新记忆的目录
            _last_output_directory = directory
            self.output_dir.set(directory)
            logger.info(f"==liuq debug== 选择输出目录: {directory}")
            logger.info(f"==liuq debug== 记忆输出目录更新为: {_last_output_directory}")
    
    def validate_configuration(self) -> bool:
        """验证用户配置"""
        # 检查是否选择了至少一个分类
        if not (self.export_large.get() or self.export_medium.get() or self.export_small.get()):
            messagebox.showwarning("配置错误", "请至少选择一个要导出的分类")
            return False
        
        # 检查源目录
        if not self.source_dir.get():
            messagebox.showwarning("配置错误", "请选择源图片目录")
            return False
        
        if not Path(self.source_dir.get()).exists():
            messagebox.showerror("配置错误", "源图片目录不存在")
            return False
        
        # 检查输出目录
        if not self.output_dir.get():
            messagebox.showwarning("配置错误", "请选择输出目录")
            return False
        
        return True
    
    def confirm_export(self):
        """确认导出"""
        if not self.validate_configuration():
            return
        
        # 构建结果配置
        self.result = {
            'export_categories': {
                'large_changes': self.export_large.get(),
                'medium_changes': self.export_medium.get(),
                'small_changes': self.export_small.get(),
                'no_changes': self.export_no_change.get()
            },
            'source_directory': self.source_dir.get(),
            'output_directory': self.output_dir.get(),
            'classification_result': self.classification_result
        }
        
        logger.info(f"==liuq debug== 用户确认导出配置: {self.result['export_categories']}")
        self.dialog.destroy()
    
    def cancel_export(self):
        """取消导出"""
        self.result = None
        logger.info("==liuq debug== 用户取消导出")
        self.dialog.destroy()
    
    def center_dialog(self):
        """居中显示对话框"""
        self.dialog.update_idletasks()
        
        # 获取对话框尺寸
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        # 获取父窗口位置和尺寸
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # 计算居中位置
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
