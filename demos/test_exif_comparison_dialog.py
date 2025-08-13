#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF对比分析对话框演示
==liuq debug== FastMapV2 EXIF对比分析对话框演示

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 15:50:00 +08:00; Reason: 阶段2-演示EXIF对比分析对话框; Principle_Applied: 用户体验优先;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 演示EXIF对比分析对话框和报告生成功能
"""

import sys
import os
import tempfile
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from gui.dialogs.exif_comparison_dialog import ExifComparisonDialog
from core.services.exif_comparison_report_generator import ExifComparisonReportGenerator


class DemoMainWindow(QMainWindow):
    """演示主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastMapV2 EXIF对比分析演示")
        self.setGeometry(100, 100, 600, 400)
        
        # 创建临时目录和演示文件
        self.temp_dir = tempfile.mkdtemp()
        self.create_demo_csv_files()
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 添加说明
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtGui import QFont
        
        title_label = QLabel("EXIF对比分析功能演示")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        info_label = QLabel(f"""
演示说明：
1. 已自动创建演示用的EXIF CSV文件
2. 测试机文件：{Path(self.test_csv_path).name}
3. 对比机文件：{Path(self.reference_csv_path).name}
4. 点击下方按钮打开EXIF对比分析对话框
5. 在对话框中可以预览字段、配置参数、生成报告

演示文件位置：{self.temp_dir}
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 添加按钮
        self.open_dialog_btn = QPushButton("打开EXIF对比分析对话框")
        self.open_dialog_btn.clicked.connect(self.open_exif_dialog)
        layout.addWidget(self.open_dialog_btn)
        
        self.test_generator_btn = QPushButton("测试报告生成器")
        self.test_generator_btn.clicked.connect(self.test_generator)
        layout.addWidget(self.test_generator_btn)
        
        self.open_temp_dir_btn = QPushButton("打开演示文件目录")
        self.open_temp_dir_btn.clicked.connect(self.open_temp_directory)
        layout.addWidget(self.open_temp_dir_btn)
        
        layout.addStretch()
        
        print("==liuq debug== EXIF对比分析演示窗口初始化完成")
    
    def create_demo_csv_files(self):
        """创建演示用的CSV文件"""
        # 创建测试机数据
        test_data = []
        for i in range(20):
            row = {
                'timestamp': (datetime.now().replace(hour=10, minute=i, second=0)).strftime('%Y-%m-%d %H:%M:%S'),
                'image_name': f'TEST_IMG_{i:04d}.jpg',
                'image_path': f'/test/path/TEST_IMG_{i:04d}.jpg',
                'meta_data_lastFrame_bv': 5.0 + i * 0.1 + (i % 3) * 0.05,
                'meta_data_currentFrame_bv': 5.1 + i * 0.1 + (i % 3) * 0.05,
                'color_sensor_irRatio': 0.8 + i * 0.01 + (i % 2) * 0.02,
                'color_sensor_rGain': 1.0 + i * 0.02 + (i % 4) * 0.01,
                'color_sensor_gGain': 1.0 + i * 0.01 + (i % 3) * 0.015,
                'color_sensor_bGain': 1.0 + i * 0.015 + (i % 5) * 0.008,
                'color_sensor_cct': 3000 + i * 100 + (i % 6) * 50,
                'color_sensor_lux': 100 + i * 10 + (i % 7) * 5,
                'awb_gain_r': 1.2 + i * 0.01,
                'awb_gain_g': 1.0,
                'awb_gain_b': 1.3 + i * 0.012,
                'exposure_time': 0.033 + i * 0.001,
                'iso_speed': 100 + i * 10
            }
            test_data.append(row)
        
        # 创建对比机数据（稍有不同）
        reference_data = []
        for i in range(20):
            row = {
                'timestamp': (datetime.now().replace(hour=10, minute=i, second=0)).strftime('%Y-%m-%d %H:%M:%S'),
                'image_name': f'TEST_IMG_{i:04d}.jpg',  # 相同的文件名用于匹配
                'image_path': f'/reference/path/TEST_IMG_{i:04d}.jpg',
                'meta_data_lastFrame_bv': 5.2 + i * 0.12 + (i % 3) * 0.03,  # 略有差异
                'meta_data_currentFrame_bv': 5.3 + i * 0.12 + (i % 3) * 0.03,
                'color_sensor_irRatio': 0.82 + i * 0.012 + (i % 2) * 0.018,
                'color_sensor_rGain': 1.02 + i * 0.022 + (i % 4) * 0.008,
                'color_sensor_gGain': 1.01 + i * 0.012 + (i % 3) * 0.012,
                'color_sensor_bGain': 1.02 + i * 0.018 + (i % 5) * 0.006,
                'color_sensor_cct': 3050 + i * 105 + (i % 6) * 45,
                'color_sensor_lux': 105 + i * 12 + (i % 7) * 3,
                'awb_gain_r': 1.22 + i * 0.012,
                'awb_gain_g': 1.0,
                'awb_gain_b': 1.32 + i * 0.014,
                'exposure_time': 0.034 + i * 0.0012,
                'iso_speed': 105 + i * 12
            }
            reference_data.append(row)
        
        # 保存CSV文件
        self.test_csv_path = os.path.join(self.temp_dir, 'test_device_exif.csv')
        self.reference_csv_path = os.path.join(self.temp_dir, 'reference_device_exif.csv')
        
        test_df = pd.DataFrame(test_data)
        reference_df = pd.DataFrame(reference_data)
        
        test_df.to_csv(self.test_csv_path, index=False, encoding='utf-8-sig')
        reference_df.to_csv(self.reference_csv_path, index=False, encoding='utf-8-sig')
        
        print(f"==liuq debug== 演示CSV文件创建完成:")
        print(f"  测试机: {self.test_csv_path}")
        print(f"  对比机: {self.reference_csv_path}")
    
    def open_exif_dialog(self):
        """打开EXIF对比分析对话框"""
        try:
            dialog = ExifComparisonDialog(self)
            
            # 预填充文件路径
            dialog.test_file_edit.setText(self.test_csv_path)
            dialog.reference_file_edit.setText(self.reference_csv_path)
            
            # 自动加载文件信息
            dialog.load_test_file_info(self.test_csv_path)
            dialog.load_reference_file_info(self.reference_csv_path)
            
            # 显示对话框
            if dialog.exec_() == dialog.Accepted:
                config = dialog.get_configuration()
                print("==liuq debug== 用户配置:")
                for key, value in config.items():
                    print(f"  {key}: {value}")
                
                # 生成报告
                self.generate_report_with_config(config)
            else:
                print("==liuq debug== 用户取消了对话框")
                
        except Exception as e:
            print(f"==liuq debug== 打开对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开对话框失败:\n{e}")
    
    def test_generator(self):
        """测试报告生成器"""
        try:
            generator = ExifComparisonReportGenerator()
            
            # 测试配置
            config = {
                'test_csv_path': self.test_csv_path,
                'reference_csv_path': self.reference_csv_path,
                'selected_fields': ['BV_Last_Frame', 'BV_Current_Frame', 'IR_Ratio', 'R_Gain'],
                'output_path': os.path.join(self.temp_dir, 'demo_report.html'),
                'similarity_threshold': 0.8,
                'match_column': 'image_name'
            }
            
            print("==liuq debug== 开始生成演示报告...")
            report_path = generator.generate(config)
            
            QMessageBox.information(
                self,
                "报告生成完成",
                f"演示报告已生成:\n{report_path}\n\n点击确定后将自动打开报告。"
            )
            
            # 打开报告（公共方法）
            from utils.browser_utils import open_html_report
            open_html_report(report_path)
            
        except Exception as e:
            print(f"==liuq debug== 测试报告生成失败: {e}")
            QMessageBox.critical(self, "错误", f"测试报告生成失败:\n{e}")
    
    def generate_report_with_config(self, config):
        """使用配置生成报告"""
        try:
            generator = ExifComparisonReportGenerator()
            
            print("==liuq debug== 开始生成用户配置的报告...")
            report_path = generator.generate(config)
            
            reply = QMessageBox.question(
                self,
                "报告生成完成",
                f"报告已生成:\n{report_path}\n\n是否立即打开？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                from utils.browser_utils import open_html_report
                open_html_report(report_path)
            
        except Exception as e:
            print(f"==liuq debug== 生成报告失败: {e}")
            QMessageBox.critical(self, "错误", f"生成报告失败:\n{e}")
    
    def open_temp_directory(self):
        """打开临时目录"""
        try:
            import subprocess
            subprocess.Popen(f'explorer "{self.temp_dir}"')
        except Exception as e:
            print(f"==liuq debug== 打开目录失败: {e}")
            QMessageBox.information(self, "目录路径", f"演示文件目录:\n{self.temp_dir}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 清理临时文件
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"==liuq debug== 清理临时目录: {self.temp_dir}")
        except Exception as e:
            print(f"==liuq debug== 清理临时目录失败: {e}")
        
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("FastMapV2 EXIF对比分析演示")
    app.setApplicationVersion("1.0.0")
    
    # 创建主窗口
    window = DemoMainWindow()
    window.show()
    
    print("==liuq debug== EXIF对比分析演示启动")
    print("==liuq debug== 功能说明:")
    print("  1. 自动创建演示用的EXIF CSV文件")
    print("  2. 演示EXIF对比分析对话框的完整功能")
    print("  3. 支持字段预览、参数配置、数据匹配预览")
    print("  4. 可以生成完整的HTML对比分析报告")
    print("  5. 演示了模拟模块的工作方式（当0_csv_compare不可用时）")
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
