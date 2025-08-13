#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试字段选择器
==liuq debug== 专门调试复选框显示问题
"""

import sys
import os
import pandas as pd
import logging
import tkinter as tk
from tkinter import ttk

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.column_mapper import ColumnMapper
from core.data_processor.csv_reader import CSVReader
from gui.components.field_selector import FieldSelector

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_field_selector():
    """调试字段选择器"""
    try:
        logger.info("==liuq debug== 开始调试字段选择器")
        
        # 创建主窗口
        root = tk.Tk()
        root.title("调试字段选择器")
        root.geometry("800x600")
        
        # 读取CSV文件
        csv_file = "../src/csv/LOG_BEFORE_JPEG.csv"
        if not os.path.exists(csv_file):
            logger.error(f"==liuq debug== CSV文件不存在: {csv_file}")
            return False
        
        # 使用CSV读取器
        reader = CSVReader()
        df = reader.read_csv(csv_file)
        logger.info(f"==liuq debug== 读取CSV成功，列数: {len(df.columns)}")
        logger.info(f"==liuq debug== 前10列: {list(df.columns[:10])}")
        
        # 应用列名映射
        df_mapped, mapping_info = reader.apply_column_mapping(df)
        display_columns = mapping_info.get('display_columns', list(df.columns))
        logger.info(f"==liuq debug== 映射后显示列数: {len(display_columns)}")
        logger.info(f"==liuq debug== 前10个显示列: {display_columns[:10]}")
        
        # 获取显示列信息
        display_column_info = reader.get_display_column_info(df, mapping_info)
        
        # 构建字段信息字典
        field_info = {}
        for col_info in display_column_info['columns']:
            field_info[col_info['name']] = col_info
        
        logger.info(f"==liuq debug== 字段信息字典键: {list(field_info.keys())[:10]}")
        
        # 创建字段选择器
        field_selector = FieldSelector(
            root,
            title="调试字段选择器",
            on_selection_changed=lambda fields: logger.info(f"==liuq debug== 选择了字段: {fields[:5]}...")
        )
        field_selector.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 设置字段
        logger.info("==liuq debug== 开始设置字段...")
        field_selector.set_fields(display_columns, field_info)
        logger.info("==liuq debug== 字段设置完成")
        
        # 检查复选框
        logger.info(f"==liuq debug== 复选框数量: {len(field_selector.checkboxes)}")
        for i, (field_name, checkbox) in enumerate(field_selector.checkboxes.items()):
            if i < 5:  # 只检查前5个
                checkbox_text = checkbox.cget('text')
                logger.info(f"==liuq debug== 复选框 {i}: 字段名='{field_name}', 显示文本='{checkbox_text}'")
        
        # 启动GUI
        root.mainloop()
        
        return True
        
    except Exception as e:
        logger.error(f"==liuq debug== 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("==liuq debug== 开始字段选择器调试")
    
    success = debug_field_selector()
    
    if success:
        logger.info("==liuq debug== 🎉 调试完成！")
    else:
        logger.error("==liuq debug== ❌ 调试失败")
