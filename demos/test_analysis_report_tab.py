#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析报告标签页演示
==liuq debug== FastMapV2分析报告标签页演示

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 14:55:00 +08:00; Reason: 阶段1基础架构重构-演示分析报告标签页; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 演示新的分析报告标签页功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from gui.tabs.analysis_report_tab import AnalysisReportTab
from core.services.unified_report_manager import UnifiedReportManager
from core.interfaces.report_generator import IReportGenerator, ReportType
from typing import Dict, Any
import tempfile


class DemoReportGenerator(IReportGenerator):
    """演示用报告生成器"""
    
    def __init__(self, report_type: ReportType, report_name: str):
        self.report_type = report_type
        self.report_name = report_name
    
    def generate(self, data: Dict[str, Any]) -> str:
        """生成演示报告"""
        # 创建临时HTML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.report_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .data-section {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{self.report_name}</h1>
        <p>演示报告 - 生成时间: {data.get('timestamp', '未知')}</p>
    </div>
    <div class="content">
        <div class="data-section">
            <h2>报告信息</h2>
            <p><strong>报告类型:</strong> {self.report_type.value}</p>
            <p><strong>报告名称:</strong> {self.report_name}</p>
            <p><strong>生成器:</strong> {self.__class__.__name__}</p>
        </div>
        <div class="data-section">
            <h2>输入数据</h2>
            <pre>{str(data)}</pre>
        </div>
        <div class="data-section">
            <h2>分析结果</h2>
            <p>这是一个演示报告，用于测试基础架构功能。</p>
            <p>在实际实现中，这里将显示详细的分析结果、图表和统计信息。</p>
        </div>
    </div>
</body>
</html>
            """
            f.write(html_content)
            return f.name
    
    def get_report_name(self) -> str:
        """获取报告名称"""
        return self.report_name
    
    def get_report_type(self) -> ReportType:
        """获取报告类型"""
        return self.report_type
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据"""
        return True  # 演示用，总是返回True


class DemoMainWindow(QMainWindow):
    """演示主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastMapV2 分析报告标签页演示")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建分析报告标签页
        self.analysis_report_tab = AnalysisReportTab(self)
        
        # 连接状态消息信号
        self.analysis_report_tab.status_message.connect(self.show_status_message)
        
        layout.addWidget(self.analysis_report_tab)
        
        # 设置演示数据
        self.setup_demo_data()
    
    def setup_demo_data(self):
        """设置演示数据"""
        # 获取报告管理器
        manager = self.analysis_report_tab.report_manager
        
        # 注册演示报告生成器
        exif_generator = DemoReportGenerator(
            ReportType.EXIF_COMPARISON,
            "EXIF对比分析报告（演示）"
        )
        map_generator = DemoReportGenerator(
            ReportType.MAP_MULTI_DIMENSIONAL,
            "Map多维度分析报告（演示）"
        )
        
        manager.register_generator(exif_generator)
        manager.register_generator(map_generator)
        
        # 生成一些演示历史记录
        from datetime import datetime
        import time
        
        demo_data_sets = [
            {"type": "exif", "device": "测试机A", "timestamp": datetime.now().isoformat()},
            {"type": "map", "scene": "室内场景", "timestamp": datetime.now().isoformat()},
            {"type": "exif", "device": "测试机B", "timestamp": datetime.now().isoformat()},
        ]
        
        for i, data in enumerate(demo_data_sets):
            if data["type"] == "exif":
                manager.generate_report(ReportType.EXIF_COMPARISON, data)
            else:
                manager.generate_report(ReportType.MAP_MULTI_DIMENSIONAL, data)
            time.sleep(0.1)  # 确保时间戳不同
        
        # 刷新历史记录显示
        self.analysis_report_tab.refresh_history()
        
        print("==liuq debug== 演示数据设置完成")
    
    def show_status_message(self, message: str):
        """显示状态消息"""
        print(f"==liuq debug== 状态消息: {message}")
        # 在实际应用中，这里会显示在状态栏


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("FastMapV2 分析报告演示")
    app.setApplicationVersion("1.0.0")
    
    # 创建主窗口
    window = DemoMainWindow()
    window.show()
    
    print("==liuq debug== 分析报告标签页演示启动")
    print("==liuq debug== 功能说明:")
    print("  1. 三个报告类型按钮（EXIF对比分析、Map多维度分析、预留功能）")
    print("  2. 报告历史记录表格")
    print("  3. 双击历史记录可打开报告文件")
    print("  4. 支持刷新和清空历史记录")
    print("  5. 当前为演示版本，实际报告生成功能将在后续阶段实现")
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
