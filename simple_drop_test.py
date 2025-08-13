#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的拖拽测试 - 使用最基本的pywin32实现
==liuq debug== 测试最简单的COM拖拽接口

创建时间: 2025-01-13 15:30:00 +08:00
目的: 使用最简单的方式测试COM拖拽是否能工作
"""

import sys
import os
import logging
import tkinter as tk
from tkinter import messagebox

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    import pythoncom
    from win32com.server.util import wrap
    logger.info("==liuq debug== pywin32模块导入成功")
except ImportError as e:
    logger.error("==liuq debug== pywin32导入失败: %s", e)
    sys.exit(1)

class SimpleDropTarget:
    """最简单的拖拽目标实现"""
    _public_methods_ = ['DragEnter', 'DragOver', 'DragLeave', 'Drop']
    _com_interfaces_ = [pythoncom.IID_IDropTarget]
    
    def __init__(self, callback):
        self.callback = callback
        logger.info("==liuq debug== SimpleDropTarget 创建")
    
    def DragEnter(self, data_object, key_state, point, effect):
        logger.info("==liuq debug== DragEnter 被调用！")
        return 1  # DROPEFFECT_COPY
    
    def DragOver(self, key_state, point, effect):
        logger.info("==liuq debug== DragOver 被调用")
        return 1  # DROPEFFECT_COPY
    
    def DragLeave(self):
        logger.info("==liuq debug== DragLeave 被调用")
    
    def Drop(self, data_object, key_state, point, effect):
        logger.info("==liuq debug== Drop 被调用！！！")
        try:
            # 简单的文件提取
            from ctypes import windll, create_unicode_buffer
            
            # 尝试获取CF_HDROP格式的数据
            fmtetc = (15, None, 1, -1, 1)  # CF_HDROP, DVASPECT_CONTENT, TYMED_HGLOBAL
            try:
                stg = data_object.GetData(fmtetc)
                hdrop = stg.data_handle
                cnt = windll.shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                logger.info("==liuq debug== 文件数量: %d", cnt)
                
                files = []
                for i in range(cnt):
                    ln = windll.shell32.DragQueryFileW(hdrop, i, None, 0)
                    buf = create_unicode_buffer(ln + 1)
                    windll.shell32.DragQueryFileW(hdrop, i, buf, ln + 1)
                    files.append(buf.value)
                    logger.info("==liuq debug== 文件 %d: %s", i, buf.value)
                
                if files and self.callback:
                    self.callback(files)
                    
            except Exception as e:
                logger.error("==liuq debug== 文件提取失败: %s", e)
                
        except Exception as e:
            logger.error("==liuq debug== Drop处理异常: %s", e)
        
        return 1  # DROPEFFECT_COPY

def test_callback(files):
    """测试回调函数"""
    logger.info("==liuq debug== 🎉 拖拽成功！收到文件: %s", files)
    messagebox.showinfo("成功", f"拖拽成功！\n文件: {files}")

def main():
    """主函数"""
    logger.info("==liuq debug== 开始简单拖拽测试")
    
    # 创建tkinter窗口
    root = tk.Tk()
    root.title("简单拖拽测试")
    root.geometry("400x300")
    
    # 添加说明
    label = tk.Label(root, text="简单拖拽测试\n请拖拽文件到此窗口", 
                    font=("Arial", 14), justify="center")
    label.pack(expand=True)
    
    try:
        # 获取窗口句柄
        hwnd = root.winfo_id()
        logger.info("==liuq debug== 窗口句柄: %s", hwnd)
        
        # 初始化OLE
        pythoncom.OleInitialize()
        logger.info("==liuq debug== OLE初始化成功")
        
        # 创建拖拽目标
        drop_target = SimpleDropTarget(test_callback)
        
        # 包装为COM对象
        com_obj = wrap(drop_target)
        logger.info("==liuq debug== COM对象创建成功: %s", com_obj)
        
        # 注册拖拽
        pythoncom.RegisterDragDrop(hwnd, com_obj)
        logger.info("==liuq debug== 拖拽注册成功！")
        
        # 更新标签
        label.config(text="✅ 拖拽注册成功！\n请拖拽文件到此窗口\n查看控制台输出", fg="green")
        
        # 添加退出处理
        def on_exit():
            try:
                pythoncom.RevokeDragDrop(hwnd)
                logger.info("==liuq debug== 拖拽已撤销")
            except Exception as e:
                logger.error("==liuq debug== 撤销失败: %s", e)
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_exit)
        
        # 运行主循环
        logger.info("==liuq debug== 开始运行，请拖拽文件测试")
        root.mainloop()
        
    except Exception as e:
        logger.error("==liuq debug== 测试失败: %s", e)
        import traceback
        logger.error("==liuq debug== 详细错误: %s", traceback.format_exc())

if __name__ == "__main__":
    main()
