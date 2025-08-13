#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主控制器
==liuq debug== GUI主界面控制器

协调各个组件，管理整个应用程序的工作流程
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import threading
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# 导入组件
from gui.components.file_selector import FileSelector
from gui.components.field_selector import FieldSelector
from gui.components.progress_bar import ProgressBar
from gui.components.threshold_panel import ThresholdPanel

# 导入核心模块
from core.data_processor.csv_reader import CSVReader
from core.data_processor.data_matcher import DataMatcher
from core.analyzer.trend_analyzer import TrendAnalyzer
from core.analyzer.statistics import StatisticsCalculator
from core.report_generator.html_generator import HTMLGenerator
from core.image_classifier import ImageClassifier
from core.file_export_manager import FileExportManager
from utils.validators import Validators
from utils.file_utils import FileUtils

logger = logging.getLogger(__name__)


class MainController:
    """主控制器类"""
    
    def __init__(self, root: tk.Tk):
        """
        初始化主控制器
        
        Args:
            root: 主窗口
        """
        self.root = root
        self.csv_reader = CSVReader()
        self.data_matcher = DataMatcher()
        self.trend_analyzer = TrendAnalyzer()
        self.statistics_calculator = StatisticsCalculator()
        self.html_generator = HTMLGenerator()
        self.image_classifier = None  # 将在分析完成后初始化
        self.file_export_manager = FileExportManager()
        self.validators = Validators()
        self.file_utils = FileUtils()
        
        # 数据存储
        self.df1 = None
        self.df2 = None
        self.match_result = None
        self.selected_fields = []

        # 列名映射信息
        self.df1_mapping_info = None
        self.df2_mapping_info = None
        
        # 组件引用
        self.file_selector1 = None
        self.file_selector2 = None
        self.field_selector = None
        self.progress_bar = None
        self.threshold_panel = None
        
        self.setup_ui()
        logger.info("==liuq debug== 主控制器初始化完成")

    def setup_styles(self):
        """配置界面样式"""
        try:
            style = ttk.Style()

            # 配置卡片样式的LabelFrame
            style.configure('Card.TLabelFrame',
                          relief='solid',
                          borderwidth=1,
                          background='#ffffff')
            style.configure('Card.TLabelFrame.Label',
                          font=('Microsoft YaHei', 10, 'bold'),
                          foreground='#2c3e50')

            # 配置状态栏样式
            style.configure('StatusBar.TFrame',
                          background='#ecf0f1',
                          relief='sunken',
                          borderwidth=1)

            logger.info("==liuq debug== 界面样式配置完成")

        except Exception as e:
            logger.error(f"==liuq debug== 界面样式配置失败: {e}")

    def setup_ui(self):
        """设置用户界面"""
        try:
            # 配置主窗口
            self.root.title("CSV数据对比分析工具 v1.0.0")
            self.root.geometry("1200x780")
            self.root.minsize(1200, 780)

            # 设置窗口背景色
            self.root.configure(bg="#a0bf9f")

            # 配置样式
            self.setup_styles()

            # 创建主框架 - 紧凑化设计
            main_frame = ttk.Frame(self.root, padding="8")
            main_frame.grid(row=0, column=0, sticky='nsew')
            
            # 配置网格权重 - 三列布局
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            main_frame.columnconfigure(0, weight=2)  # 左侧区域（文件选择+字段选择）
            main_frame.columnconfigure(1, weight=1)  # 右侧区域（阈值配置面板）
            # 配置所有行的权重 - 确保底部组件始终可见
            main_frame.rowconfigure(0, weight=0)  # 标题区域 - 固定高度
            main_frame.rowconfigure(1, weight=0)  # 文件选择区域 - 固定高度
            main_frame.rowconfigure(2, weight=1)  # 字段选择区域 - 可扩展但有限制
            main_frame.rowconfigure(3, weight=0)  # 操作按钮区域 - 固定高度
            main_frame.rowconfigure(4, weight=0)  # 进度条区域 - 固定高度
            main_frame.rowconfigure(5, weight=0)  # 分隔线 - 固定高度
            main_frame.rowconfigure(6, weight=0)  # 状态栏 - 固定高度


            
            # 标题区域
            self.setup_header(main_frame)
            
            # 文件选择区域
            self.setup_file_selection(main_frame)
            
            # 字段选择区域
            self.setup_field_selection(main_frame)

            # 阈值配置面板
            self.setup_threshold_panel(main_frame)

            # 操作按钮区域
            self.setup_action_buttons(main_frame)

            # 进度条区域
            self.setup_progress_area(main_frame)
            
            logger.info("==liuq debug== 主界面设置完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== 主界面设置失败: {e}")
            messagebox.showerror("错误", f"界面初始化失败: {e}")
    
    def setup_header(self, parent):
        """设置标题区域"""

    def setup_file_selection(self, parent):
        """设置文件选择区域"""
        try:
            file_frame = ttk.LabelFrame(parent, text="文件选择", padding="4")
            file_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(0, 6), padx=(0, 8))
            file_frame.columnconfigure(0, weight=1)
            file_frame.columnconfigure(1, weight=1)
            file_frame.rowconfigure(0, weight=1)
            
            # 文件1选择器 - 紧凑化间距
            self.file_selector1 = FileSelector(
                file_frame,
                title="文件1",
                on_file_selected=self.on_file1_selected
            )
            self.file_selector1.grid(row=0, column=0, sticky='nsew', padx=(0, 3))

            # 文件2选择器 - 紧凑化间距
            self.file_selector2 = FileSelector(
                file_frame,
                title="文件2",
                on_file_selected=self.on_file2_selected
            )
            self.file_selector2.grid(row=0, column=1, sticky='nsew', padx=(3, 0))
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件选择区域设置失败: {e}")
    
    def setup_field_selection(self, parent):
        """设置字段选择区域"""
        try:
            field_frame = ttk.LabelFrame(parent, text="字段选择", padding="8")
            field_frame.grid(row=2, column=0, sticky='nsew', pady=(0, 8), padx=(0, 8))
            field_frame.columnconfigure(0, weight=1)
            field_frame.rowconfigure(0, weight=1)
            
            # 字段选择器
            self.field_selector = FieldSelector(
                field_frame,
                title="选择要分析的字段",
                on_selection_changed=self.on_field_selection_changed
            )
            self.field_selector.grid(row=0, column=0, sticky='nsew')
            
        except Exception as e:
            logger.error(f"==liuq debug== 字段选择区域设置失败: {e}")

    def setup_threshold_panel(self, parent):
        """设置阈值配置面板"""
        try:
            # 创建阈值配置面板
            self.threshold_panel = ThresholdPanel(
                parent,
                on_config_changed=self.on_threshold_config_changed
            )
            self.threshold_panel.grid(row=2, column=1, rowspan=2, sticky='nsew', padx=(8, 0))

            logger.info("==liuq debug== 阈值配置面板设置完成")

        except Exception as e:
            logger.error(f"==liuq debug== 阈值配置面板设置失败: {e}")

    def setup_action_buttons(self, parent):
        """设置操作按钮区域"""
        try:
            button_frame = ttk.Frame(parent)
            button_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(0, 8))

            # 开始分析按钮 - 紧凑化设计
            self.analyze_button = ttk.Button(
                button_frame,
                text="🔍 开始分析",
                command=self.start_analysis,
                style='Accent.TButton',
                width=12
            )
            self.analyze_button.grid(row=0, column=0, padx=(0, 8))

            # 生成报告按钮 - 紧凑化设计
            self.report_button = ttk.Button(
                button_frame,
                text="📊 生成HTML报告",
                command=self.generate_report,
                state='disabled',
                width=15
            )
            self.report_button.grid(row=0, column=1, padx=(0, 8))

            # 导出图片按钮 - 紧凑化设计
            self.export_button = ttk.Button(
                button_frame,
                text="📁 导出图片分类",
                command=self.export_images,
                state='disabled',
                width=15
            )
            self.export_button.grid(row=0, column=2, padx=(0, 10))

            # 清除按钮
            self.clear_button = ttk.Button(
                button_frame,
                text="清除数据",
                command=self.clear_data
            )
            self.clear_button.grid(row=0, column=3, padx=(0, 10))
            
            # 帮助按钮
            help_button = ttk.Button(
                button_frame,
                text="帮助",
                command=self.show_help
            )
            help_button.grid(row=0, column=4)
            
            # 初始状态
            self.update_button_states()
            
        except Exception as e:
            logger.error(f"==liuq debug== 操作按钮区域设置失败: {e}")
    
    def setup_progress_area(self, parent):
        """设置进度条区域"""
        try:
            progress_frame = ttk.LabelFrame(parent, text="处理进度", padding="2")
            progress_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 1))
            progress_frame.columnconfigure(0, weight=1)
            
            # 进度条
            self.progress_bar = ProgressBar(
                progress_frame,
                title="",
                show_percentage=True,
                show_status=True
            )
            self.progress_bar.grid(row=0, column=0, sticky='ew')
            
        except Exception as e:
            logger.error(f"==liuq debug== 进度条区域设置失败: {e}")

    def on_file1_selected(self, file_path: str, file_info: Dict[str, Any]):
        """文件1选择回调"""
        try:
            logger.info(f"==liuq debug== 文件1已选择: {file_path}")
            logger.info(f"==liuq debug== 文件1已选择: {Path(file_path).name}")
            
            # 异步加载文件
            threading.Thread(target=self.load_file1, args=(file_path,), daemon=True).start()
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件1选择处理失败: {e}")
    
    def on_file2_selected(self, file_path: str, file_info: Dict[str, Any]):
        """文件2选择回调"""
        try:
            logger.info(f"==liuq debug== 文件2已选择: {file_path}")
            logger.info(f"==liuq debug== 文件2已选择: {Path(file_path).name}")
            
            # 异步加载文件
            threading.Thread(target=self.load_file2, args=(file_path,), daemon=True).start()
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件2选择处理失败: {e}")
    
    def load_file1(self, file_path: str):
        """加载文件1"""
        try:
            self.progress_bar.set_indeterminate("正在读取文件1...")

            # 读取CSV文件
            self.df1 = self.csv_reader.read_csv(file_path)

            # 应用列名映射
            self.df1, self.df1_mapping_info = self.csv_reader.apply_column_mapping(self.df1)

            # 验证文件
            validation_result = self.validators.validate_dataframe(self.df1, "文件1")
            if not validation_result['valid']:
                raise ValueError(f"文件1验证失败: {validation_result['errors']}")

            # 更新界面
            self.root.after(0, self.on_file1_loaded)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"==liuq debug== 文件1加载失败: {error_msg}")
            self.root.after(0, lambda msg=error_msg: self.progress_bar.set_error(f"文件1加载失败: {msg}"))
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"文件1加载失败: {msg}"))
    
    def load_file2(self, file_path: str):
        """加载文件2"""
        try:
            self.progress_bar.set_indeterminate("正在读取文件2...")

            # 读取CSV文件
            self.df2 = self.csv_reader.read_csv(file_path)

            # 应用列名映射
            self.df2, self.df2_mapping_info = self.csv_reader.apply_column_mapping(self.df2)

            # 验证文件
            validation_result = self.validators.validate_dataframe(self.df2, "文件2")
            if not validation_result['valid']:
                raise ValueError(f"文件2验证失败: {validation_result['errors']}")

            # 更新界面
            self.root.after(0, self.on_file2_loaded)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"==liuq debug== 文件2加载失败: {error_msg}")
            self.root.after(0, lambda msg=error_msg: self.progress_bar.set_error(f"文件2加载失败: {msg}"))
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"文件2加载失败: {msg}"))
    
    def on_file1_loaded(self):
        """文件1加载完成回调"""
        try:
            self.progress_bar.stop_indeterminate("文件1加载完成")
            logger.info(f"==liuq debug== 文件1加载完成 - {len(self.df1)} 行, {len(self.df1.columns)} 列")
            self.update_field_selector()
            self.update_button_states()
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件1加载完成处理失败: {e}")
    
    def on_file2_loaded(self):
        """文件2加载完成回调"""
        try:
            self.progress_bar.stop_indeterminate("文件2加载完成")
            logger.info(f"==liuq debug== 文件2加载完成 - {len(self.df2)} 行, {len(self.df2.columns)} 列")
            self.update_field_selector()
            self.update_button_states()
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件2加载完成处理失败: {e}")
    
    def update_field_selector(self):
        """更新字段选择器"""
        try:
            fields_to_show = []
            field_info = {}
            selector_title = "选择要分析的字段"

            if self.df1 is not None and self.df2 is not None:
                # 两个文件都已加载，显示共同字段（使用映射后的显示名称）
                df1_display_cols = self.df1_mapping_info.get('display_columns', list(self.df1.columns))
                df2_display_cols = self.df2_mapping_info.get('display_columns', list(self.df2.columns))

                # 找到共同的显示字段
                common_display_fields = [col for col in df1_display_cols if col in df2_display_cols]
                fields_to_show = common_display_fields
                selector_title = f"选择要分析的字段 (共同字段: {len(common_display_fields)}个)"

                # 获取字段信息（使用映射后的列信息）
                if common_display_fields:
                    df_info = self.csv_reader.get_display_column_info(self.df1, self.df1_mapping_info)
                    for field in common_display_fields:
                        # 从完整的列信息中找到对应字段的信息
                        for col_info in df_info['columns']:
                            if col_info['name'] == field:
                                field_info[field] = col_info
                                break

                logger.info(f"==liuq debug== 显示共同字段: {len(common_display_fields)} 个")

            elif self.df1 is not None:
                # 只有文件1加载，显示文件1的所有字段（使用映射后的显示名称）
                fields_to_show = self.df1_mapping_info.get('display_columns', list(self.df1.columns))
                selector_title = f"选择要分析的字段 (文件1字段: {len(fields_to_show)}个)"

                # 获取字段信息（使用映射后的列信息）
                if fields_to_show:
                    df_info = self.csv_reader.get_display_column_info(self.df1, self.df1_mapping_info)
                    for field in fields_to_show:
                        # 从完整的列信息中找到对应字段的信息
                        for col_info in df_info['columns']:
                            if col_info['name'] == field:
                                field_info[field] = col_info
                                break

                logger.info(f"==liuq debug== 显示文件1字段: {len(fields_to_show)} 个")

            elif self.df2 is not None:
                # 只有文件2加载，显示文件2的所有字段（使用映射后的显示名称）
                fields_to_show = self.df2_mapping_info.get('display_columns', list(self.df2.columns))
                selector_title = f"选择要分析的字段 (文件2字段: {len(fields_to_show)}个)"

                # 获取字段信息（使用映射后的列信息）
                if fields_to_show:
                    df_info = self.csv_reader.get_display_column_info(self.df2, self.df2_mapping_info)
                    for field in fields_to_show:
                        # 从完整的列信息中找到对应字段的信息
                        for col_info in df_info['columns']:
                            if col_info['name'] == field:
                                field_info[field] = col_info
                                break

                logger.info(f"==liuq debug== 显示文件2字段: {len(fields_to_show)} 个")

            # 更新字段选择器
            if fields_to_show:
                self.field_selector.set_fields(fields_to_show, field_info)
                self.field_selector.update_title(selector_title)

                logger.info(f"==liuq debug== 字段选择器更新完成: {selector_title}")
            else:
                # 清空字段选择器
                self.field_selector.clear_fields()
                self.field_selector.update_title("选择要分析的字段")
                logger.info("==liuq debug== 清空字段选择器")

        except Exception as e:
            logger.error(f"==liuq debug== 字段选择器更新失败: {e}")
    
    def on_field_selection_changed(self, selected_fields: List[str]):
        """字段选择变化回调"""
        try:
            # 将显示名称转换为原始列名用于数据分析
            original_fields = []

            # 根据当前加载的文件情况选择映射信息
            mapping_info = None
            if self.df1 is not None and self.df2 is not None:
                # 两个文件都加载时，使用文件1的映射信息
                mapping_info = self.df1_mapping_info
            elif self.df1 is not None:
                mapping_info = self.df1_mapping_info
            elif self.df2 is not None:
                mapping_info = self.df2_mapping_info

            if mapping_info:
                display_to_original = mapping_info.get('display_to_original', {})
                for display_field in selected_fields:
                    original_field = display_to_original.get(display_field, display_field)
                    original_fields.append(original_field)
            else:
                # 没有映射信息时，直接使用显示名称
                original_fields = selected_fields

            # 存储原始列名用于数据分析
            self.selected_fields = original_fields
            self.update_button_states()

            logger.info(f"==liuq debug== 字段选择变化: {len(selected_fields)} 个显示字段 -> {len(original_fields)} 个原始字段")

        except Exception as e:
            logger.error(f"==liuq debug== 字段选择变化处理失败: {e}")

    def on_threshold_config_changed(self, config):
        """阈值配置变化回调"""
        try:
            logger.info("==liuq debug== 阈值配置已变更")

            # 如果有分析结果，提示用户重新分析
            if self.match_result is not None:
                logger.info("==liuq debug== 阈值已更新 - 建议重新分析以应用新阈值")

        except Exception as e:
            logger.error(f"==liuq debug== 阈值配置变化处理失败: {e}")

    def update_button_states(self):
        """更新按钮状态"""
        try:
            # 检查是否可以开始分析
            can_analyze = (
                self.df1 is not None and
                self.df2 is not None and
                len(self.selected_fields) > 0
            )

            # 检查是否可以生成报告
            can_report = self.match_result is not None

            # 检查是否可以导出图片
            can_export = self.match_result is not None and self.image_classifier is not None

            # 更新按钮状态
            self.analyze_button.configure(state='normal' if can_analyze else 'disabled')
            self.report_button.configure(state='normal' if can_report else 'disabled')
            self.export_button.configure(state='normal' if can_export else 'disabled')

        except Exception as e:
            logger.error(f"==liuq debug== 按钮状态更新失败: {e}")
    
    def start_analysis(self):
        """开始分析"""
        try:
            if not self.validate_analysis_requirements():
                return
            
            # 异步执行分析
            threading.Thread(target=self.perform_analysis, daemon=True).start()
            
        except Exception as e:
            logger.error(f"==liuq debug== 开始分析失败: {e}")
            messagebox.showerror("错误", f"开始分析失败: {e}")
    
    def validate_analysis_requirements(self) -> bool:
        """验证分析要求"""
        try:
            # 检查文件
            if self.df1 is None:
                messagebox.showerror("错误", "请先选择文件1")
                return False
            
            if self.df2 is None:
                messagebox.showerror("错误", "请先选择文件2")
                return False
            
            # 检查字段选择
            if not self.selected_fields:
                messagebox.showerror("错误", "请至少选择一个分析字段")
                return False
            
            # 验证选择的字段
            validation_result = self.validators.validate_selected_fields(
                self.df1, self.df2, self.selected_fields
            )
            
            if not validation_result['valid']:
                messagebox.showerror("字段验证失败", "\n".join(validation_result['errors']))
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 分析要求验证失败: {e}")
            return False
    
    def perform_analysis(self):
        """执行分析"""
        try:
            self.root.after(0, lambda: self.progress_bar.start(100, "开始数据分析..."))

            # 步骤1: 数据匹配
            self.root.after(0, lambda: self.progress_bar.update_progress(20, "正在匹配数据..."))
            self.match_result = self.data_matcher.match_data(self.df1, self.df2)

            # 步骤2: 趋势分析
            self.root.after(0, lambda: self.progress_bar.update_progress(50, "正在分析字段趋势..."))
            matched_pairs = self.match_result.get('pairs', [])
            self.trend_analysis = self.trend_analyzer.analyze_field_trends(matched_pairs, self.selected_fields)

            # 步骤3: 统计计算
            self.root.after(0, lambda: self.progress_bar.update_progress(80, "正在计算统计指标..."))
            self.statistics_results = self.calculate_detailed_statistics()

            # 步骤4: 生成分析结果
            self.root.after(0, lambda: self.progress_bar.update_progress(90, "正在生成分析结果..."))
            self.analysis_summary = self.generate_analysis_summary()

            # 步骤5: 初始化图片分类器
            self.root.after(0, lambda: self.progress_bar.update_progress(95, "初始化图片分类器..."))
            self.image_classifier = ImageClassifier(self.match_result, self.selected_fields)

            # 完成
            self.root.after(0, lambda: self.progress_bar.complete("分析完成"))
            self.root.after(0, self.on_analysis_completed)

        except Exception as e:
            logger.error(f"==liuq debug== 数据分析失败: {e}")
            self.root.after(0, lambda: self.progress_bar.set_error(f"分析失败: {e}"))
            self.root.after(0, lambda: messagebox.showerror("分析失败", str(e)))
    
    def calculate_detailed_statistics(self) -> Dict[str, Any]:
        """计算详细统计"""
        try:
            statistics_results = {}
            matched_pairs = self.match_result.get('pairs', [])

            for field in self.selected_fields:
                # 提取字段数据
                values_before = []
                values_after = []

                for pair in matched_pairs:
                    try:
                        row1 = pair['row1']
                        row2 = pair['row2']

                        if field in row1.index and field in row2.index:
                            val1 = pd.to_numeric(row1[field], errors='coerce')
                            val2 = pd.to_numeric(row2[field], errors='coerce')

                            if pd.notna(val1) and pd.notna(val2):
                                values_before.append(float(val1))
                                values_after.append(float(val2))
                    except:
                        continue

                if values_before and values_after:
                    # 计算各种统计指标
                    field_stats = {
                        'before_stats': self.statistics_calculator.calculate_descriptive_statistics(values_before),
                        'after_stats': self.statistics_calculator.calculate_descriptive_statistics(values_after),
                        'change_analysis': self.statistics_calculator.calculate_percentage_changes(values_before, values_after),
                        'effect_size': self.statistics_calculator.calculate_effect_size(values_before, values_after),
                        'confidence_interval_before': self.statistics_calculator.calculate_confidence_interval(values_before),
                        'confidence_interval_after': self.statistics_calculator.calculate_confidence_interval(values_after),
                        'normality_test_before': self.statistics_calculator.perform_normality_test(values_before),
                        'normality_test_after': self.statistics_calculator.perform_normality_test(values_after)
                    }

                    statistics_results[field] = field_stats

            return statistics_results

        except Exception as e:
            logger.error(f"==liuq debug== 详细统计计算失败: {e}")
            return {}

    def generate_analysis_summary(self) -> str:
        """生成分析摘要"""
        try:
            summary_lines = []
            summary_lines.append("=== CSV数据对比分析报告 ===")
            summary_lines.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            summary_lines.append("")

            # 数据匹配摘要
            summary_lines.append("数据匹配结果:")
            summary_lines.append(f"  文件1数据量: {self.match_result['total_file1']} 行")
            summary_lines.append(f"  文件2数据量: {self.match_result['total_file2']} 行")
            summary_lines.append(f"  成功匹配: {self.match_result['matched_pairs']} 对")
            summary_lines.append(f"  匹配率: {self.match_result['match_rate']:.1f}%")
            summary_lines.append("")

            # 字段分析摘要
            if hasattr(self, 'trend_analysis') and self.trend_analysis:
                summary_lines.append("字段趋势分析:")
                for field, analysis in self.trend_analysis.get('field_analyses', {}).items():
                    if 'error' not in analysis:
                        trend = analysis.get('trend_classification', {})
                        summary_lines.append(f"  {field}:")
                        summary_lines.append(f"    趋势: {trend.get('trend', '未知')}")
                        summary_lines.append(f"    置信度: {trend.get('confidence', 0):.2f}")
                        summary_lines.append(f"    有效数据对: {analysis.get('valid_pairs', 0)}")
                summary_lines.append("")

            # 整体统计摘要
            if hasattr(self, 'statistics_results') and self.statistics_results:
                summary_lines.append("统计分析摘要:")
                for field, stats in self.statistics_results.items():
                    change_analysis = stats.get('change_analysis', {})
                    summary = change_analysis.get('summary', {})

                    summary_lines.append(f"  {field}:")
                    summary_lines.append(f"    正向变化: {summary.get('positive_changes', 0)}")
                    summary_lines.append(f"    负向变化: {summary.get('negative_changes', 0)}")
                    summary_lines.append(f"    无变化: {summary.get('no_changes', 0)}")

                    effect_size = stats.get('effect_size', {})
                    if effect_size:
                        summary_lines.append(f"    效应量: {effect_size.get('interpretation', '未知')}")

            return "\n".join(summary_lines)

        except Exception as e:
            logger.error(f"==liuq debug== 生成分析摘要失败: {e}")
            return f"生成分析摘要失败: {e}"

    def on_analysis_completed(self):
        """分析完成回调"""
        try:
            # 显示分析结果
            if hasattr(self, 'analysis_summary'):
                # 创建结果显示窗口
                self.show_analysis_results()
            else:
                # 简单显示匹配结果
                match_info = (
                    f"数据分析完成!\n"
                    f"文件1: {self.match_result['total_file1']} 行\n"
                    f"文件2: {self.match_result['total_file2']} 行\n"
                    f"成功匹配: {self.match_result['matched_pairs']} 对\n"
                    f"匹配率: {self.match_result['match_rate']:.1f}%"
                )
                messagebox.showinfo("分析完成", match_info)

            # 记录状态
            logger.info(f"==liuq debug== 分析完成 - 匹配 {self.match_result['matched_pairs']} 对数据，可生成报告和导出图片")
            self.update_button_states()

        except Exception as e:
            logger.error(f"==liuq debug== 分析完成处理失败: {e}")

    def show_analysis_results(self):
        """显示分析结果窗口"""
        try:
            # 创建结果窗口
            result_window = tk.Toplevel(self.root)
            result_window.title("分析结果")
            result_window.geometry("800x600")

            # 创建文本框显示结果
            text_frame = ttk.Frame(result_window, padding="10")
            text_frame.pack(fill='both', expand=True)

            # 文本框和滚动条
            text_widget = tk.Text(text_frame, wrap='word', font=('Consolas', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)

            text_widget.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

            # 插入分析结果
            text_widget.insert('1.0', self.analysis_summary)
            text_widget.configure(state='disabled')

            # 按钮框架
            button_frame = ttk.Frame(result_window, padding="10")
            button_frame.pack(fill='x')

            # 关闭按钮
            close_button = ttk.Button(button_frame, text="关闭",
                                    command=result_window.destroy)
            close_button.pack(side='right')

            # 复制按钮
            def copy_results():
                result_window.clipboard_clear()
                result_window.clipboard_append(self.analysis_summary)
                messagebox.showinfo("提示", "分析结果已复制到剪贴板")

            copy_button = ttk.Button(button_frame, text="复制结果",
                                   command=copy_results)
            copy_button.pack(side='right', padx=(0, 10))

        except Exception as e:
            logger.error(f"==liuq debug== 显示分析结果失败: {e}")
            messagebox.showerror("错误", f"显示分析结果失败: {e}")
    
    def generate_report(self):
        """生成HTML报告"""
        try:
            if not hasattr(self, 'match_result') or not self.match_result:
                messagebox.showerror("错误", "请先完成数据分析")
                return

            # 显示进度
            self.progress_bar.set_indeterminate("正在生成HTML报告...")

            # 异步生成报告
            threading.Thread(target=self.perform_report_generation, daemon=True).start()

        except Exception as e:
            logger.error(f"==liuq debug== 生成报告失败: {e}")
            messagebox.showerror("错误", f"生成报告失败: {e}")

    def perform_report_generation(self):
        """执行报告生成"""
        try:
            # 获取映射信息（优先使用文件1的映射信息）
            mapping_info = self.df1_mapping_info or self.df2_mapping_info

            # 生成HTML报告
            report_path = self.html_generator.generate_report(
                analysis_results=getattr(self, 'trend_analysis', {}),
                match_result=self.match_result,
                statistics_results=getattr(self, 'statistics_results', {}),
                mapping_info=mapping_info
            )

            # 更新界面
            self.root.after(0, lambda: self.on_report_generated(report_path))

        except Exception as e:
            logger.error(f"==liuq debug== 报告生成失败: {e}")
            self.root.after(0, lambda: self.progress_bar.set_error(f"报告生成失败: {e}"))
            self.root.after(0, lambda: messagebox.showerror("报告生成失败", str(e)))

    def on_report_generated(self, report_path: str):
        """报告生成完成回调"""
        try:
            self.progress_bar.stop_indeterminate("报告生成完成")

            # 询问是否打开报告
            response = messagebox.askyesno(
                "报告生成完成",
                f"HTML报告已生成:\n{report_path}\n\n是否立即打开报告？"
            )

            if response:
                # 在默认浏览器中打开报告（保持遗留模块自包含实现）
                import webbrowser
                webbrowser.open(f"file://{Path(report_path).absolute()}")

            # 记录状态
            logger.info(f"==liuq debug== 报告已生成: {Path(report_path).name}")

        except Exception as e:
            logger.error(f"==liuq debug== 报告生成完成处理失败: {e}")
    
    def clear_data(self):
        """清除数据"""
        try:
            # 确认对话框
            if messagebox.askyesno("确认", "确定要清除所有数据吗？"):
                # 清除数据
                self.df1 = None
                self.df2 = None
                self.match_result = None
                self.selected_fields = []
                
                # 清除界面
                self.file_selector1.clear_selection()
                self.file_selector2.clear_selection()
                self.field_selector.clear_fields()
                self.progress_bar.reset()
                
                # 记录状态
                logger.info("==liuq debug== 数据已清除 - 请重新选择文件")
                self.update_button_states()
                
                logger.info("==liuq debug== 数据已清除")
                
        except Exception as e:
            logger.error(f"==liuq debug== 清除数据失败: {e}")
            messagebox.showerror("错误", f"清除数据失败: {e}")
    
    def show_help(self):
        """显示帮助信息"""
        try:
            help_text = """
CSV数据对比分析工具使用说明：

1. 文件选择：
   - 选择两个CSV文件进行对比
   - 支持拖拽和浏览器选择
   - 文件必须包含Image_name列用于数据匹配

2. 字段选择：
   - 选择要分析的数值字段
   - 支持全选、全不选、反选操作
   - 只有数值字段才能进行趋势分析

3. 数据分析：
   - 基于Image_name前缀进行数据匹配
   - 计算字段变化趋势和统计指标
   - 生成匹配结果和分析报告

4. 报告生成：
   - 生成交互式HTML报告
   - 包含图表、表格和统计信息
   - 支持导出和分享

如有问题，请查看日志文件或联系技术支持。
            """
            
            messagebox.showinfo("帮助", help_text)
            
        except Exception as e:
            logger.error(f"==liuq debug== 显示帮助失败: {e}")

    def export_images(self):
        """导出图片分类"""
        try:
            if not self.image_classifier:
                messagebox.showwarning("提示", "请先完成数据分析")
                return

            logger.info("==liuq debug== 开始图片分类导出")

            # 执行图片分类
            logger.info("==liuq debug== 正在分析图片分类...")
            classification_result = self.image_classifier.classify_images()

            # 显示导出配置对话框
            from gui.dialogs.export_dialog import ExportDialog
            export_dialog = ExportDialog(self.root, classification_result)
            export_config = export_dialog.show()

            if not export_config:
                logger.info("==liuq debug== 用户取消导出")
                return

            # 异步执行导出
            threading.Thread(target=self.perform_image_export,
                           args=(export_config,), daemon=True).start()

        except Exception as e:
            logger.error(f"==liuq debug== 图片导出失败: {e}")
            messagebox.showerror("导出失败", f"图片导出失败: {e}")

    def perform_image_export(self, export_config: Dict[str, Any]):
        """执行图片导出（后台线程）"""
        try:
            # 创建进度对话框
            progress_dialog = self.create_export_progress_dialog()

            def progress_callback(progress: int, message: str):
                """进度回调函数"""
                self.root.after(0, lambda: self.update_export_progress(progress_dialog, progress, message))

            # 执行导出
            export_result = self.file_export_manager.export_images(export_config, progress_callback)

            # 显示结果
            self.root.after(0, lambda: self.show_export_result(progress_dialog, export_result))

        except Exception as e:
            logger.error(f"==liuq debug== 图片导出执行失败: {e}")
            self.root.after(0, lambda: self.show_export_error(progress_dialog, str(e)))

    def create_export_progress_dialog(self) -> tk.Toplevel:
        """创建导出进度对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("导出进度")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # 内容框架
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill='both', expand=True)

        # 标题
        title_label = ttk.Label(frame, text="正在导出图片分类...", font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))

        # 进度条
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill='x', pady=(0, 10))

        # 状态标签
        status_var = tk.StringVar(value="准备中...")
        status_label = ttk.Label(frame, textvariable=status_var)
        status_label.pack()

        # 存储变量引用
        dialog.progress_var = progress_var
        dialog.status_var = status_var

        return dialog

    def update_export_progress(self, dialog: tk.Toplevel, progress: int, message: str):
        """更新导出进度"""
        try:
            if dialog.winfo_exists():
                dialog.progress_var.set(progress)
                dialog.status_var.set(message)
                dialog.update()
        except:
            pass

    def show_export_result(self, progress_dialog: tk.Toplevel, export_result: Dict[str, Any]):
        """显示导出结果"""
        try:
            # 关闭进度对话框
            if progress_dialog.winfo_exists():
                progress_dialog.destroy()

            # 显示结果
            stats = export_result['statistics']
            result_message = (
                f"图片导出完成！\n\n"
                f"总文件数: {stats['total_files']}\n"
                f"成功复制: {stats['copied_files']}\n"
                f"跳过文件: {stats['skipped_files']}\n"
                f"错误文件: {stats['error_files']}\n"
                f"成功率: {stats['success_rate']}%\n\n"
                f"输出目录: {export_result['output_directory']}\n"
                f"用时: {export_result['duration']}"
            )

            # 询问是否打开输出目录
            result = messagebox.askyesno("导出完成",
                                       result_message + "\n\n是否打开输出目录？")

            if result:
                import subprocess
                import os
                if os.name == 'nt':  # Windows
                    subprocess.run(['explorer', export_result['output_directory']])
                elif os.name == 'posix':  # macOS/Linux
                    subprocess.run(['open', export_result['output_directory']])

            logger.info(f"==liuq debug== 导出完成 - 成功复制 {stats['copied_files']} 个文件")

        except Exception as e:
            logger.error(f"==liuq debug== 显示导出结果失败: {e}")

    def show_export_error(self, progress_dialog: tk.Toplevel, error_message: str):
        """显示导出错误"""
        try:
            # 关闭进度对话框
            if progress_dialog.winfo_exists():
                progress_dialog.destroy()

            messagebox.showerror("导出失败", f"图片导出失败:\n{error_message}")
            logger.error("==liuq debug== 导出失败")

        except Exception as e:
            logger.error(f"==liuq debug== 显示导出错误失败: {e}")
