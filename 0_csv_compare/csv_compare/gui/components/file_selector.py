#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件选择组件
==liuq debug== GUI文件选择组件

提供文件选择和拖拽功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any

# 尝试导入拖拽库，如果失败则禁用拖拽功能
try:
    import tkinterdnd2 as tkdnd
    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False
    tkdnd = None

logger = logging.getLogger(__name__)

# ==liuq debug== 全局变量记住上次打开的目录
_last_csv_directory = str(Path.home())


class FileSelector(ttk.Frame):
    """文件选择组件类"""
    
    def __init__(self, parent, title: str = "选择文件", 
                 file_types: tuple = (("CSV文件", "*.csv"), ("所有文件", "*.*")),
                 on_file_selected: Optional[Callable] = None):
        """
        初始化文件选择组件
        
        Args:
            parent: 父窗口
            title: 组件标题
            file_types: 支持的文件类型
            on_file_selected: 文件选择回调函数
        """
        super().__init__(parent)
        
        self.title = title
        self.file_types = file_types
        self.on_file_selected = on_file_selected
        self.selected_file_path = None
        self.file_info = {}
        
        self.setup_ui()
        logger.info(f"==liuq debug== 文件选择组件初始化完成: {title}")
    
    def setup_ui(self):
        """设置用户界面"""
        try:
            # 主框架 - 进一步紧凑化padding
            self.configure(padding="3")

            # 配置网格权重 - 简化布局，移除冗余组件
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=0)  # 路径输入框行
            self.rowconfigure(2, weight=1)  # 拖拽区域行

            # 标题标签 - 进一步紧凑化字体和间距
            title_label = ttk.Label(self, text=self.title, font=('Microsoft YaHei', 10, 'bold'))
            title_label.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 4))

            # 文件路径显示框
            self.path_var = tk.StringVar()
            self.path_var.set("请选择CSV文件...")

            path_frame = ttk.Frame(self)
            path_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 3))
            path_frame.columnconfigure(0, weight=1)

            self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var,
                                       state='readonly', font=('Microsoft YaHei', 8))
            self.path_entry.grid(row=0, column=0, sticky='ew', padx=(0, 2))

            # 浏览按钮 - 进一步紧凑化设计
            browse_button = ttk.Button(path_frame, text="浏览...",
                                     command=self.browse_file, width=6)
            browse_button.grid(row=0, column=1)

            
        except Exception as e:
            logger.error(f"==liuq debug== 文件选择组件UI设置失败: {e}")
            messagebox.showerror("错误", f"界面初始化失败: {e}")
    
    def setup_drag_drop(self):
        """设置拖拽功能"""
        try:
            if DRAG_DROP_AVAILABLE and tkdnd:
                # 设置拖拽功能
                self.drop_frame.drop_target_register(tkdnd.DND_FILES)
                self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
                logger.info("==liuq debug== 拖拽功能设置成功")
            else:
                logger.info("==liuq debug== 拖拽功能不可用，跳过设置")
                # 更新提示文本，移除拖拽相关内容
                for child in self.drop_frame.winfo_children():
                    if isinstance(child, ttk.Label):
                        child.configure(text="点击上方浏览按钮选择CSV文件")
        except Exception as e:
            logger.warning(f"==liuq debug== 拖拽功能设置失败: {e}")
            # 更新提示文本，移除拖拽相关内容
            for child in self.drop_frame.winfo_children():
                if isinstance(child, ttk.Label):
                    child.configure(text="点击上方浏览按钮选择CSV文件")
    
    def browse_file(self):
        """浏览文件对话框"""
        try:
            global _last_csv_directory

            file_path = filedialog.askopenfilename(
                title=f"选择{self.title}",
                filetypes=self.file_types,
                initialdir=_last_csv_directory
            )

            if file_path:
                # ==liuq debug== 更新记忆的目录
                _last_csv_directory = str(Path(file_path).parent)
                self.set_file_path(file_path)
                logger.info(f"==liuq debug== 通过浏览选择文件: {file_path}")
                logger.info(f"==liuq debug== 记忆目录更新为: {_last_csv_directory}")

        except Exception as e:
            logger.error(f"==liuq debug== 文件浏览失败: {e}")
            messagebox.showerror("错误", f"文件选择失败: {e}")
    
    def on_drop(self, event):
        """拖拽文件处理"""
        try:
            files = event.data.split()
            if files:
                file_path = files[0].strip('{}')  # 移除可能的大括号
                self.set_file_path(file_path)
                logger.info(f"==liuq debug== 通过拖拽选择文件: {file_path}")
        except Exception as e:
            logger.error(f"==liuq debug== 拖拽文件处理失败: {e}")
            messagebox.showerror("错误", f"拖拽文件处理失败: {e}")
    
    def set_file_path(self, file_path: str):
        """
        设置文件路径

        Args:
            file_path: 文件路径
        """
        try:
            path_obj = Path(file_path)

            # 验证文件
            if not path_obj.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            if not path_obj.is_file():
                raise ValueError(f"路径不是文件: {file_path}")

            # 检查文件扩展名
            if path_obj.suffix.lower() not in ['.csv', '.txt', '.tsv']:
                response = messagebox.askyesno(
                    "文件类型警告",
                    f"选择的文件不是标准CSV文件（{path_obj.suffix}）\n是否继续？"
                )
                if not response:
                    return

            # 更新界面
            self.selected_file_path = str(path_obj.absolute())
            self.path_var.set(self.selected_file_path)

            # 获取文件信息（保留用于回调，但不显示UI）
            self.update_file_info()

            # 调用回调函数
            if self.on_file_selected:
                self.on_file_selected(self.selected_file_path, self.file_info)

            logger.info(f"==liuq debug== 文件路径设置成功: {self.selected_file_path}")

        except Exception as e:
            logger.error(f"==liuq debug== 文件路径设置失败: {e}")
            messagebox.showerror("文件选择错误", str(e))
    
    def update_file_info(self):
        """更新文件信息（仅收集信息，不显示UI）"""
        try:
            if not self.selected_file_path:
                return

            path_obj = Path(self.selected_file_path)
            stat = path_obj.stat()

            # 收集文件信息
            self.file_info = {
                'name': path_obj.name,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': stat.st_mtime,
                'extension': path_obj.suffix,
                'absolute_path': str(path_obj.absolute())
            }

            logger.info(f"==liuq debug== 文件信息已更新: {self.file_info['name']}")

        except Exception as e:
            logger.error(f"==liuq debug== 文件信息更新失败: {e}")
    
    def get_selected_file(self) -> Optional[str]:
        """
        获取选择的文件路径
        
        Returns:
            文件路径，未选择返回None
        """
        return self.selected_file_path
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        获取文件信息
        
        Returns:
            文件信息字典
        """
        return self.file_info.copy()
    
    def clear_selection(self):
        """清除选择"""
        try:
            self.selected_file_path = None
            self.file_info = {}
            self.path_var.set("请选择CSV文件...")

            logger.info("==liuq debug== 文件选择已清除")

        except Exception as e:
            logger.error(f"==liuq debug== 清除文件选择失败: {e}")
    
    def is_file_selected(self) -> bool:
        """
        检查是否已选择文件
        
        Returns:
            是否已选择文件
        """
        return self.selected_file_path is not None
