#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阈值配置面板组件
==liuq debug== GUI阈值配置面板

提供CCT和百分比阈值的配置界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Callable, Dict, Any
import threading

from utils.config_manager import ConfigManager, ThresholdConfig

logger = logging.getLogger(__name__)


class ThresholdPanel(ttk.Frame):
    """阈值配置面板组件类"""
    
    def __init__(self, parent, on_config_changed: Optional[Callable] = None):
        """
        初始化阈值配置面板
        
        Args:
            parent: 父窗口
            on_config_changed: 配置变化回调函数
        """
        super().__init__(parent)
        
        self.on_config_changed = on_config_changed
        self.config_manager = ConfigManager()
        
        # 输入框变量
        self.cct_vars = {}
        self.percentage_vars = {}
        
        # 验证状态
        self.validation_errors = {}
        
        # 防抖定时器
        self.update_timer = None
        
        self.setup_ui()
        self.load_current_config()
        
        # 注册为配置观察者
        self.config_manager.register_observer(self.on_config_updated)
        
        logger.info("==liuq debug== 阈值配置面板初始化完成")
    
    def setup_ui(self):
        """设置用户界面"""
        try:
            # 主框架配置
            self.configure(padding="8")
            
            # 配置网格权重
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            
            # 标题
            title_label = ttk.Label(self, text="变化阈值配置", 
                                   font=('Microsoft YaHei', 12, 'bold'))
            title_label.grid(row=0, column=0, sticky='ew', pady=(0, 8))
            
            # 创建Notebook（标签页）
            self.notebook = ttk.Notebook(self)
            self.notebook.grid(row=1, column=0, sticky='nsew', pady=(0, 8))
            
            # CCT阈值标签页
            self.cct_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.cct_frame, text="CCT阈值 (K)")
            self.setup_cct_tab()
            
            # 百分比阈值标签页
            self.percentage_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.percentage_frame, text="百分比阈值 (%)")
            self.setup_percentage_tab()
            
            # 按钮区域
            self.setup_buttons()
            
            # 状态标签
            self.status_label = ttk.Label(self, text="", foreground="green")
            self.status_label.grid(row=3, column=0, sticky='ew', pady=(4, 0))
            
        except Exception as e:
            logger.error(f"==liuq debug== 阈值配置面板UI设置失败: {e}")
            messagebox.showerror("错误", f"界面初始化失败: {e}")
    
    def setup_cct_tab(self):
        """设置CCT阈值标签页"""
        try:
            self.cct_frame.configure(padding="8")
            self.cct_frame.columnconfigure(1, weight=1)
            
            # 创建输入框
            fields = [
                ("small_max", "小变化阈值 (<)", "K"),
                ("medium_min", "中变化最小值 (≥)", "K"),
                ("medium_max", "中变化最大值 (≤)", "K"),
                ("large_min", "大变化阈值 (>)", "K")
            ]
            
            for i, (key, label, unit) in enumerate(fields):
                # 标签
                ttk.Label(self.cct_frame, text=label).grid(
                    row=i, column=0, sticky='w', pady=2, padx=(0, 8)
                )
                
                # 输入框
                var = tk.StringVar()
                var.trace('w', lambda *args, k=key: self.on_cct_value_changed(k))
                self.cct_vars[key] = var
                
                entry = ttk.Entry(self.cct_frame, textvariable=var, width=10)
                entry.grid(row=i, column=1, sticky='w', pady=2, padx=(0, 4))
                
                # 单位标签
                ttk.Label(self.cct_frame, text=unit).grid(
                    row=i, column=2, sticky='w', pady=2
                )
            
            # 说明文本
            info_text = ("CCT阈值说明：\n"
                        "• 小变化：变化值 < 小变化阈值\n"
                        "• 中变化：中变化最小值 ≤ 变化值 ≤ 中变化最大值\n"
                        "• 大变化：变化值 > 大变化阈值")
            
            info_label = ttk.Label(self.cct_frame, text=info_text, 
                                  font=('Arial', 9), foreground='gray')
            info_label.grid(row=len(fields), column=0, columnspan=3, 
                           sticky='ew', pady=(8, 0))
            
        except Exception as e:
            logger.error(f"==liuq debug== CCT标签页设置失败: {e}")
    
    def setup_percentage_tab(self):
        """设置百分比阈值标签页"""
        try:
            self.percentage_frame.configure(padding="8")
            self.percentage_frame.columnconfigure(1, weight=1)
            
            # 创建输入框
            fields = [
                ("small_max", "小变化阈值 (<)", "%"),
                ("medium_min", "中变化最小值 (≥)", "%"),
                ("medium_max", "中变化最大值 (≤)", "%"),
                ("large_min", "大变化阈值 (>)", "%")
            ]
            
            for i, (key, label, unit) in enumerate(fields):
                # 标签
                ttk.Label(self.percentage_frame, text=label).grid(
                    row=i, column=0, sticky='w', pady=2, padx=(0, 8)
                )
                
                # 输入框
                var = tk.StringVar()
                var.trace('w', lambda *args, k=key: self.on_percentage_value_changed(k))
                self.percentage_vars[key] = var
                
                entry = ttk.Entry(self.percentage_frame, textvariable=var, width=10)
                entry.grid(row=i, column=1, sticky='w', pady=2, padx=(0, 4))
                
                # 单位标签
                ttk.Label(self.percentage_frame, text=unit).grid(
                    row=i, column=2, sticky='w', pady=2
                )
            
            # 说明文本
            info_text = ("百分比阈值说明：\n"
                        "• 小变化：变化百分比 < 小变化阈值\n"
                        "• 中变化：中变化最小值 ≤ 变化百分比 ≤ 中变化最大值\n"
                        "• 大变化：变化百分比 > 大变化阈值")
            
            info_label = ttk.Label(self.percentage_frame, text=info_text, 
                                  font=('Arial', 9), foreground='gray')
            info_label.grid(row=len(fields), column=0, columnspan=3, 
                           sticky='ew', pady=(8, 0))
            
        except Exception as e:
            logger.error(f"==liuq debug== 百分比标签页设置失败: {e}")
    
    def setup_buttons(self):
        """设置按钮区域"""
        try:
            button_frame = ttk.Frame(self)
            button_frame.grid(row=2, column=0, sticky='ew', pady=(8, 4))
            button_frame.columnconfigure(0, weight=1)
            button_frame.columnconfigure(1, weight=1)
            
            # 应用按钮
            self.apply_button = ttk.Button(
                button_frame,
                text="应用",
                command=self.apply_config,
                width=10
            )
            self.apply_button.grid(row=0, column=0, padx=(0, 4), sticky='ew')
            
            # 重置按钮
            self.reset_button = ttk.Button(
                button_frame,
                text="重置",
                command=self.reset_config,
                width=10
            )
            self.reset_button.grid(row=0, column=1, padx=(4, 0), sticky='ew')
            
        except Exception as e:
            logger.error(f"==liuq debug== 按钮区域设置失败: {e}")
    
    def load_current_config(self):
        """加载当前配置到界面"""
        try:
            config = self.config_manager.get_config()
            
            # 加载CCT阈值
            self.cct_vars["small_max"].set(str(config.cct_small_max))
            self.cct_vars["medium_min"].set(str(config.cct_medium_min))
            self.cct_vars["medium_max"].set(str(config.cct_medium_max))
            self.cct_vars["large_min"].set(str(config.cct_large_min))
            
            # 加载百分比阈值
            self.percentage_vars["small_max"].set(str(config.percentage_small_max))
            self.percentage_vars["medium_min"].set(str(config.percentage_medium_min))
            self.percentage_vars["medium_max"].set(str(config.percentage_medium_max))
            self.percentage_vars["large_min"].set(str(config.percentage_large_min))
            

            
        except Exception as e:
            logger.error(f"==liuq debug== 加载配置失败: {e}")
    
    def on_cct_value_changed(self, key: str):
        """CCT值变化处理"""
        self.schedule_validation()
    
    def on_percentage_value_changed(self, key: str):
        """百分比值变化处理"""
        self.schedule_validation()
    
    def schedule_validation(self):
        """安排验证（防抖）"""
        if self.update_timer:
            self.after_cancel(self.update_timer)
        
        self.update_timer = self.after(500, self.validate_inputs)
    
    def validate_inputs(self) -> bool:
        """验证输入值"""
        try:
            self.validation_errors.clear()
            
            # 验证CCT值
            cct_values = {}
            for key, var in self.cct_vars.items():
                try:
                    value = float(var.get())
                    if value <= 0:
                        self.validation_errors[f"cct_{key}"] = "必须大于0"
                    else:
                        cct_values[key] = value
                except ValueError:
                    self.validation_errors[f"cct_{key}"] = "必须是有效数字"
            
            # 验证百分比值
            percentage_values = {}
            for key, var in self.percentage_vars.items():
                try:
                    value = float(var.get())
                    if value <= 0:
                        self.validation_errors[f"percentage_{key}"] = "必须大于0"
                    else:
                        percentage_values[key] = value
                except ValueError:
                    self.validation_errors[f"percentage_{key}"] = "必须是有效数字"
            
            # 逻辑验证
            if len(cct_values) == 4:
                if cct_values["medium_max"] < cct_values["medium_min"]:
                    self.validation_errors["cct_logic"] = "CCT中变化最大值必须≥最小值"
                if cct_values["large_min"] < cct_values["medium_max"]:
                    self.validation_errors["cct_logic2"] = "CCT大变化阈值必须≥中变化最大值"
            
            if len(percentage_values) == 4:
                if percentage_values["medium_max"] < percentage_values["medium_min"]:
                    self.validation_errors["percentage_logic"] = "百分比中变化最大值必须≥最小值"
                if percentage_values["large_min"] < percentage_values["medium_max"]:
                    self.validation_errors["percentage_logic2"] = "百分比大变化阈值必须≥中变化最大值"
            
            # 更新状态显示
            if self.validation_errors:
                error_msg = "输入错误: " + "; ".join(self.validation_errors.values())
                self.status_label.configure(text=error_msg[:50] + "...", foreground="red")
                self.apply_button.configure(state='disabled')
                return False
            else:
                self.status_label.configure(text="输入有效", foreground="green")
                self.apply_button.configure(state='normal')
                return True
                
        except Exception as e:
            logger.error(f"==liuq debug== 输入验证失败: {e}")
            self.status_label.configure(text="验证失败", foreground="red")
            return False
    
    def apply_config(self):
        """应用配置"""
        try:
            if not self.validate_inputs():
                return
            
            # 创建新配置
            new_config = ThresholdConfig(
                cct_small_max=float(self.cct_vars["small_max"].get()),
                cct_medium_min=float(self.cct_vars["medium_min"].get()),
                cct_medium_max=float(self.cct_vars["medium_max"].get()),
                cct_large_min=float(self.cct_vars["large_min"].get()),
                percentage_small_max=float(self.percentage_vars["small_max"].get()),
                percentage_medium_min=float(self.percentage_vars["medium_min"].get()),
                percentage_medium_max=float(self.percentage_vars["medium_max"].get()),
                percentage_large_min=float(self.percentage_vars["large_min"].get())
            )
            
            # 更新配置
            success = self.config_manager.update_config(new_config)
            
            if success:
                self.status_label.configure(text="配置已应用", foreground="green")
                logger.info("==liuq debug== 阈值配置已应用")
                
                # 调用回调函数
                if self.on_config_changed:
                    self.on_config_changed(new_config)
            else:
                self.status_label.configure(text="配置应用失败", foreground="red")
                
        except Exception as e:
            logger.error(f"==liuq debug== 应用配置失败: {e}")
            self.status_label.configure(text="应用失败", foreground="red")
            messagebox.showerror("错误", f"应用配置失败: {e}")
    
    def reset_config(self):
        """重置配置"""
        try:
            if messagebox.askyesno("确认", "确定要重置为默认配置吗？"):
                success = self.config_manager.reset_to_default()
                
                if success:
                    self.load_current_config()
                    self.status_label.configure(text="已重置为默认配置", foreground="green")
                    logger.info("==liuq debug== 阈值配置已重置")
                else:
                    self.status_label.configure(text="重置失败", foreground="red")
                    
        except Exception as e:
            logger.error(f"==liuq debug== 重置配置失败: {e}")
            messagebox.showerror("错误", f"重置配置失败: {e}")
    
    def on_config_updated(self, config: ThresholdConfig):
        """配置更新通知处理"""
        try:
            # 在主线程中更新界面
            self.after(0, lambda: self.load_current_config())

        except Exception as e:
            logger.error(f"==liuq debug== 处理配置更新通知失败: {e}")
    
    def destroy(self):
        """销毁组件时清理资源"""
        try:
            # 取消注册观察者
            self.config_manager.unregister_observer(self.on_config_updated)
            
            # 取消定时器
            if self.update_timer:
                self.after_cancel(self.update_timer)
            
            super().destroy()

            
        except Exception as e:
            logger.error(f"==liuq debug== 销毁阈值配置面板失败: {e}")
