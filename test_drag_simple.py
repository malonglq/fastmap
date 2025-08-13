#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单拖拽测试程序 - 用于诊断系统级拖拽问题
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SimpleDragTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("拖拽测试 - 请拖拽文件到这里")
        self.setGeometry(100, 100, 400, 300)
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建标签
        self.label = QLabel("请拖拽任何文件到这个窗口\n\n如果看到日志输出，说明拖拽功能正常\n如果没有任何输出，说明系统阻止了拖拽")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Arial", 12))
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                padding: 20px;
                background-color: #f0f0f0;
            }
        """)
        layout.addWidget(self.label)
        
        # 启用拖拽
        self.setAcceptDrops(True)
        print("==liuq debug== 简单拖拽测试程序启动")
        print("==liuq debug== 已启用拖拽，等待拖拽事件...")
    
    def dragEnterEvent(self, event):
        print("==liuq debug== ✅ dragEnterEvent 被调用！")
        print(f"==liuq debug== 拖拽数据类型: {event.mimeData().formats()}")
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            print(f"==liuq debug== 拖拽文件数量: {len(urls)}")
            for i, url in enumerate(urls):
                print(f"==liuq debug== 文件{i+1}: {url.toLocalFile()}")
            event.acceptProposedAction()
            self.label.setText("检测到拖拽！\n正在处理...")
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        print("==liuq debug== ✅ dragMoveEvent 被调用！")
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        print("==liuq debug== ✅ dropEvent 被调用！")
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files = [url.toLocalFile() for url in urls]
            print(f"==liuq debug== 成功接收到 {len(files)} 个文件:")
            for file in files:
                print(f"==liuq debug==   - {file}")
            
            self.label.setText(f"✅ 拖拽成功！\n接收到 {len(files)} 个文件\n\n{chr(10).join(files[:3])}")
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        print("==liuq debug== dragLeaveEvent 被调用")
        self.label.setText("请拖拽任何文件到这个窗口\n\n如果看到日志输出，说明拖拽功能正常\n如果没有任何输出，说明系统阻止了拖拽")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    print("==liuq debug== 创建简单拖拽测试窗口...")
    window = SimpleDragTestWindow()
    window.show()
    
    print("==liuq debug== 测试程序运行中，请拖拽文件进行测试...")
    print("==liuq debug== 如果拖拽后没有任何日志输出，说明系统级别阻止了拖拽事件")
    
    sys.exit(app.exec_())
