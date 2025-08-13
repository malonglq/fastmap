#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pywin_drop.py 独立测试脚本
==liuq debug== 测试pywin32拖拽功能是否正常工作

创建时间: 2025-01-13 15:20:00 +08:00
目的: 独立测试pywin_drop模块，排除Qt干扰
"""

import sys
import os
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
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_callback(files):
    """测试回调函数"""
    logger.info("==liuq debug== 拖拽回调触发！收到文件: %s", files)
    for file_path in files:
        logger.info("==liuq debug== 文件: %s", file_path)
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            logger.info("==liuq debug== 这是一个图片文件！")
        else:
            logger.info("==liuq debug== 这不是图片文件")

def main():
    """主函数"""
    logger.info("==liuq debug== 开始测试pywin_drop模块")
    
    try:
        # 导入pywin_drop模块
        from utils.pywin_drop import install_pywin_drop, revoke_pywin_drop
        logger.info("==liuq debug== pywin_drop模块导入成功")
        
        # 创建一个简单的窗口来测试
        import tkinter as tk
        from tkinter import messagebox
        
        # 创建主窗口
        root = tk.Tk()
        root.title("pywin_drop 测试窗口")
        root.geometry("400x300")
        
        # 添加说明标签
        label = tk.Label(root, text="请拖拽图片文件到此窗口\n查看控制台输出", 
                        font=("Arial", 14), justify="center")
        label.pack(expand=True)
        
        # 获取窗口句柄
        hwnd = root.winfo_id()
        logger.info("==liuq debug== 窗口句柄: %s", hwnd)
        
        # 注册拖拽功能
        try:
            dt = install_pywin_drop(hwnd, test_callback)
            logger.info("==liuq debug== pywin_drop注册成功: %s", dt)
            
            # 显示成功消息
            success_label = tk.Label(root, text="✅ pywin_drop注册成功！\n现在可以拖拽文件测试", 
                                   fg="green", font=("Arial", 12))
            success_label.pack()
            
        except Exception as e:
            logger.error("==liuq debug== pywin_drop注册失败: %s", e)
            error_label = tk.Label(root, text=f"❌ 注册失败: {e}", 
                                 fg="red", font=("Arial", 10))
            error_label.pack()
        
        # 添加退出按钮
        def on_exit():
            try:
                if 'dt' in locals():
                    revoke_pywin_drop(hwnd)
                    logger.info("==liuq debug== pywin_drop已撤销")
            except Exception as e:
                logger.error("==liuq debug== 撤销失败: %s", e)
            root.destroy()
        
        exit_button = tk.Button(root, text="退出", command=on_exit, 
                               font=("Arial", 12))
        exit_button.pack(pady=10)
        
        # 运行主循环
        logger.info("==liuq debug== 开始运行测试窗口，请拖拽文件测试")
        root.mainloop()
        
    except ImportError as e:
        logger.error("==liuq debug== 导入失败: %s", e)
        print("请确保pywin32已安装: pip install pywin32")
    except Exception as e:
        logger.error("==liuq debug== 测试失败: %s", e)

if __name__ == "__main__":
    main()
