#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map多维度分析对话框演示
==liuq debug== FastMapV2 Map多维度分析对话框演示

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 16:35:00 +08:00; Reason: 阶段3-演示Map多维度分析对话框; Principle_Applied: 用户体验优先;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 演示Map多维度分析对话框和报告生成功能
"""

import sys
import os
from datetime import datetime

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

from core.models.map_data import MapConfiguration, MapPoint, BaseBoundary, SceneType, MapType
from core.services.map_multi_dimensional_report_generator import MapMultiDimensionalReportGenerator


class DemoMainWindow(QMainWindow):
    """演示主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastMapV2 Map多维度分析演示")
        self.setGeometry(100, 100, 600, 400)
        
        # 创建演示Map配置
        self.map_configuration = self.create_demo_map_configuration()
        
        # 创建中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 添加说明
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtGui import QFont
        
        title_label = QLabel("Map多维度分析功能演示")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        info_label = QLabel(f"""
演示说明：
1. 已自动创建演示用的Map配置数据
2. 包含10个Map点：5个室内、3个室外、2个夜景
3. 点击下方按钮打开Map多维度分析对话框
4. 在对话框中可以预览Map数据、配置多维度分析参数
5. 支持生成包含场景分类和参数分布的HTML报告

Map配置概览：
- 设备类型：demo_device
- Map点数量：10个
- 场景分布：室内(5) + 室外(3) + 夜景(2)
- 基础边界：RpG=0.5, BpG=0.3
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 添加按钮
        self.open_dialog_btn = QPushButton("打开Map多维度分析对话框")
        self.open_dialog_btn.clicked.connect(self.open_map_dialog)
        layout.addWidget(self.open_dialog_btn)
        
        self.test_generator_btn = QPushButton("测试报告生成器")
        self.test_generator_btn.clicked.connect(self.test_generator)
        layout.addWidget(self.test_generator_btn)
        
        self.preview_analysis_btn = QPushButton("预览分析范围")
        self.preview_analysis_btn.clicked.connect(self.preview_analysis)
        layout.addWidget(self.preview_analysis_btn)
        
        layout.addStretch()
        
        print("==liuq debug== Map多维度分析演示窗口初始化完成")
    
    def create_demo_map_configuration(self) -> MapConfiguration:
        """创建演示Map配置"""
        # 创建基础边界
        base_boundary = BaseBoundary(rpg=0.5, bpg=0.3)
        
        # 创建演示Map点
        map_points = []
        
        # 室内场景点
        for i in range(5):
            map_point = MapPoint(
                alias_name=f"Indoor_BV_5000_IR_800_{i}",
                x=10.0 + i * 5,
                y=10.0 + i * 3,
                offset_x=10.0 + i * 5,
                offset_y=10.0 + i * 3,
                weight=0.8 + i * 0.05,
                bv_range=(5000 + i * 200, 6000 + i * 200),
                ir_range=(800, 900),
                cct_range=(3000, 4000),
                detect_flag=True,
                map_type=MapType.ENHANCE,
                scene_type=SceneType.INDOOR
            )
            map_points.append(map_point)
        
        # 室外场景点
        for i in range(3):
            map_point = MapPoint(
                alias_name=f"Outdoor_BV_8000_IR_500_{i}",
                x=-10.0 - i * 8,
                y=20.0 + i * 5,
                offset_x=-10.0 - i * 8,
                offset_y=20.0 + i * 5,
                weight=0.9 + i * 0.03,
                bv_range=(8000 + i * 300, 9000 + i * 300),
                ir_range=(500, 600),
                cct_range=(5000, 6000),
                detect_flag=True,
                map_type=MapType.ENHANCE,
                scene_type=SceneType.OUTDOOR
            )
            map_points.append(map_point)
        
        # 夜景场景点
        for i in range(2):
            map_point = MapPoint(
                alias_name=f"Night_BV_1000_IR_1200_{i}",
                x=30.0 + i * 10,
                y=-20.0 - i * 8,
                offset_x=30.0 + i * 10,
                offset_y=-20.0 - i * 8,
                weight=0.7 + i * 0.1,
                bv_range=(1000 + i * 500, 2000 + i * 500),
                ir_range=(1200, 1500),
                cct_range=(2000, 3000),
                detect_flag=True,
                map_type=MapType.REDUCE,
                scene_type=SceneType.NIGHT
            )
            map_points.append(map_point)
        
        # 创建Map配置
        return MapConfiguration(
            device_type="demo_device",
            base_boundary=base_boundary,
            map_points=map_points,
            reference_points=[(0, 0), (50, 50)],
            metadata={"demo": True, "created": datetime.now().isoformat()}
        )
    
    def open_map_dialog(self):
        """打开Map多维度分析对话框"""
        try:
            from gui.dialogs.map_multi_dimensional_dialog import MapMultiDimensionalDialog
            
            # 创建对话框
            dialog = MapMultiDimensionalDialog(self.map_configuration, self)
            
            # 显示对话框
            if dialog.exec_() == dialog.Accepted:
                config = dialog.get_configuration()
                print("==liuq debug== 用户配置:")
                for key, value in config.items():
                    if key == 'map_configuration':
                        print(f"  {key}: MapConfiguration with {len(value.map_points)} points")
                    else:
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
            generator = MapMultiDimensionalReportGenerator()
            
            # 测试配置
            config = {
                'map_configuration': self.map_configuration,
                'include_multi_dimensional': True,
                'template_name': 'map_analysis'
            }
            
            print("==liuq debug== 开始生成演示报告...")
            
            # 由于可能缺少相关模块，这里只测试基本功能
            summary = generator.get_map_configuration_summary(self.map_configuration)
            
            QMessageBox.information(
                self,
                "Map配置摘要",
                f"设备类型: {summary.get('device_type', '未知')}\n"
                f"Map点数量: {summary.get('total_map_points', 0)}\n"
                f"场景分布: {summary.get('scene_distribution', {})}\n"
                f"坐标范围: {summary.get('coordinate_range', {})}\n"
                f"权重范围: {summary.get('weight_range', {})}"
            )
            
        except Exception as e:
            print(f"==liuq debug== 测试报告生成失败: {e}")
            QMessageBox.critical(self, "错误", f"测试报告生成失败:\n{e}")
    
    def preview_analysis(self):
        """预览分析范围"""
        try:
            generator = MapMultiDimensionalReportGenerator()
            
            preview = generator.preview_analysis_scope(
                self.map_configuration,
                include_multi_dimensional=True
            )
            
            # 格式化预览信息
            preview_text = "分析范围预览:\n\n"
            
            # Map摘要
            map_summary = preview.get('map_summary', {})
            preview_text += f"设备类型: {map_summary.get('device_type', '未知')}\n"
            preview_text += f"Map点数量: {map_summary.get('total_map_points', 0)}\n"
            preview_text += f"场景分布: {map_summary.get('scene_distribution', {})}\n\n"
            
            # 分析范围
            analysis_scope = preview.get('analysis_scope', {})
            preview_text += "分析内容:\n"
            preview_text += f"• 传统Map分析: {'是' if analysis_scope.get('traditional_analysis', False) else '否'}\n"
            preview_text += f"• 多维度场景分析: {'是' if analysis_scope.get('multi_dimensional_analysis', False) else '否'}\n"
            preview_text += f"• 场景分类分析: {'是' if analysis_scope.get('scene_classification', False) else '否'}\n\n"
            
            # 预计处理时间
            preview_text += f"预计处理时间: {preview.get('estimated_processing_time', '未知')}\n\n"
            
            # 输出章节
            output_sections = preview.get('output_sections', [])
            preview_text += "报告章节:\n"
            for section in output_sections:
                preview_text += f"• {section}\n"
            
            QMessageBox.information(self, "分析范围预览", preview_text)
            
        except Exception as e:
            print(f"==liuq debug== 预览分析范围失败: {e}")
            QMessageBox.critical(self, "错误", f"预览分析范围失败:\n{e}")
    
    def generate_report_with_config(self, config):
        """使用配置生成报告"""
        try:
            generator = MapMultiDimensionalReportGenerator()
            
            print("==liuq debug== 开始生成用户配置的报告...")
            
            # 由于可能缺少相关模块，这里只显示配置信息
            QMessageBox.information(
                self,
                "报告配置确认",
                f"报告配置:\n"
                f"• 包含多维度分析: {config.get('include_multi_dimensional', False)}\n"
                f"• 模板类型: {config.get('template_name', 'default')}\n"
                f"• 输出路径: {config.get('output_path', '默认路径')}\n\n"
                f"注意: 由于演示环境限制，实际报告生成功能需要完整的Map分析模块支持。"
            )
            
        except Exception as e:
            print(f"==liuq debug== 生成报告失败: {e}")
            QMessageBox.critical(self, "错误", f"生成报告失败:\n{e}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("FastMapV2 Map多维度分析演示")
    app.setApplicationVersion("1.0.0")
    
    # 创建主窗口
    window = DemoMainWindow()
    window.show()
    
    print("==liuq debug== Map多维度分析演示启动")
    print("==liuq debug== 功能说明:")
    print("  1. 自动创建演示用的Map配置数据")
    print("  2. 演示Map多维度分析对话框的完整功能")
    print("  3. 支持Map数据概览、多维度分析配置、输出设置")
    print("  4. 可以预览分析范围和配置参数")
    print("  5. 演示了报告生成器的基本功能（需要完整模块支持实际生成）")
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
