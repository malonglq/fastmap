#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV数据对比分析工具 - 主程序入口
==liuq debug== 主程序启动文件

作者: AI Assistant
创建时间: 2025-06-27
版本: 1.0.0
描述: 专业的CSV文件数据对比分析工具，支持GUI界面操作和HTML报告生成
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('csv_compare.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """检查必要的依赖包是否已安装"""
    required_packages = [
        'pandas',
        'numpy', 
        'chardet',
        'jinja2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"==liuq debug== 依赖包 {package} 检查通过")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"==liuq debug== 缺少依赖包: {package}")
    
    if missing_packages:
        error_msg = f"缺少以下依赖包: {', '.join(missing_packages)}\n"
        error_msg += "请运行: pip install -r requirements.txt"
        messagebox.showerror("依赖检查失败", error_msg)
        return False
    
    return True


def main():
    """主程序入口函数"""
    try:
        logger.info("==liuq debug== CSV数据对比分析工具启动")
        
        # 检查依赖
        if not check_dependencies():
            logger.error("==liuq debug== 依赖检查失败，程序退出")
            sys.exit(1)
        
        # 导入GUI控制器（延迟导入，确保依赖检查通过）
        try:
            from gui.controllers.main_controller import MainController
            logger.info("==liuq debug== GUI控制器导入成功")
        except ImportError as e:
            logger.error(f"==liuq debug== GUI控制器导入失败: {e}")
            messagebox.showerror("程序错误", f"GUI模块导入失败: {e}")
            sys.exit(1)
        
        # 创建主窗口
        root = tk.Tk()
        root.title("CSV数据对比分析工具 v1.0.0")
        root.geometry("800x350")
        root.minsize(800, 350)
        
        # 设置窗口图标（如果有的话）
        try:
            # root.iconbitmap('icon.ico')  # 可选：添加程序图标
            pass
        except:
            pass
        
        # 创建主控制器
        app = MainController(root)
        logger.info("==liuq debug== 主控制器创建成功")
        
        # 启动GUI主循环
        logger.info("==liuq debug== 启动GUI主循环")
        root.mainloop()
        
    except Exception as e:
        logger.error(f"==liuq debug== 程序运行出错: {e}")
        messagebox.showerror("程序错误", f"程序运行出错: {e}")
        sys.exit(1)
    
    finally:
        logger.info("==liuq debug== CSV数据对比分析工具退出")


if __name__ == "__main__":
    main()
