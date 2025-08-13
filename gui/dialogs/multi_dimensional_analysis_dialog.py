# {{CHENGQI:
# Action: Added; Timestamp: 2025-08-04 16:50:00 +08:00; Reason: 创建多维度分析对话框以提供完整的Map数据多维度分析报告功能; Principle_Applied: 用户界面设计和功能模块化;
# }}

"""
多维度分析对话框

提供Map数据的多维度分析和报告生成功能
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QLabel, QPushButton, QTextEdit, QTableWidget, 
                           QTableWidgetItem, QGroupBox, QProgressBar,
                           QMessageBox, QFileDialog, QSplitter, QWidget,
                           QHeaderView, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
import json
from pathlib import Path

from core.models.map_data import MapConfiguration
from core.models.scene_classification_config import SceneClassificationConfig, get_default_config_path
from core.services.multi_dimensional_analyzer import MultiDimensionalAnalyzer
from gui.dialogs.analysis_config_dialog import AnalysisConfigDialog

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """分析工作线程"""
    
    progress_updated = pyqtSignal(int, str)
    analysis_completed = pyqtSignal(dict)
    analysis_failed = pyqtSignal(str)
    
    def __init__(self, configuration: MapConfiguration, 
                 classification_config: SceneClassificationConfig):
        super().__init__()
        self.configuration = configuration
        self.classification_config = classification_config
    
    def run(self):
        """执行分析"""
        try:
            self.progress_updated.emit(10, "初始化分析器...")
            
            # 创建分析器
            analyzer = MultiDimensionalAnalyzer(self.configuration, self.classification_config)
            
            self.progress_updated.emit(30, "正在分析场景分类...")
            
            # 执行分析
            result = analyzer.analyze()
            
            self.progress_updated.emit(100, "分析完成")
            self.analysis_completed.emit(result)
            
        except Exception as e:
            logger.error(f"==liuq debug== 分析线程失败: {e}")
            self.analysis_failed.emit(str(e))


class MultiDimensionalAnalysisDialog(QDialog):
    """
    多维度分析对话框
    
    提供Map数据的多维度分析和报告展示功能
    """
    
    def __init__(self, parent=None, configuration: MapConfiguration = None):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
            configuration: Map配置数据
        """
        super().__init__(parent)
        self.configuration = configuration
        self.classification_config = SceneClassificationConfig.load_from_file(get_default_config_path())
        self.analysis_result = None
        
        self.setup_ui()
        self.setup_connections()
        
        logger.info("==liuq debug== 多维度分析对话框初始化完成")
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("Map数据多维度分析报告")
        self.setModal(True)
        self.resize(1200, 800)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # 标题区域
        self.create_title_area(main_layout)
        
        # 控制区域
        self.create_control_area(main_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 主要内容区域
        self.create_content_area(main_layout)
        
        # 底部按钮区域
        self.create_button_area(main_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #e0e0e0;
            }
        """)
    
    def create_title_area(self, parent_layout):
        """创建标题区域"""
        title_label = QLabel("Map数据多维度分析报告")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        parent_layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        parent_layout.addWidget(line)
    
    def create_control_area(self, parent_layout):
        """创建控制区域"""
        control_layout = QHBoxLayout()
        
        # 配置信息
        config_label = QLabel(f"当前配置: {self.classification_config.config_name}")
        control_layout.addWidget(config_label)
        
        control_layout.addStretch()
        
        # 配置按钮
        config_btn = QPushButton("配置分类阈值")
        config_btn.clicked.connect(self.open_config_dialog)
        control_layout.addWidget(config_btn)
        
        # 开始分析按钮
        self.analyze_btn = QPushButton("开始分析")
        self.analyze_btn.clicked.connect(self.start_analysis)
        control_layout.addWidget(self.analyze_btn)
        
        parent_layout.addLayout(control_layout)
    
    def create_content_area(self, parent_layout):
        """创建主要内容区域"""
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        
        # 1. 分析概览标签页
        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "分析概览")
        
        # 2. 场景分类标签页
        self.scene_tab = self.create_scene_classification_tab()
        self.tab_widget.addTab(self.scene_tab, "场景分类")
        
        # 3. 参数分布标签页
        self.parameter_tab = self.create_parameter_distribution_tab()
        self.tab_widget.addTab(self.parameter_tab, "参数分布")
        
        # 4. 详细报告标签页
        self.report_tab = self.create_detailed_report_tab()
        self.tab_widget.addTab(self.report_tab, "详细报告")
        
        parent_layout.addWidget(self.tab_widget)
    
    def create_overview_tab(self) -> QWidget:
        """创建分析概览标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 统计摘要区域
        summary_group = QGroupBox("统计摘要")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(200)
        self.summary_text.setPlainText("请点击'开始分析'按钮进行分析...")
        summary_layout.addWidget(self.summary_text)
        
        layout.addWidget(summary_group)
        
        # 分类准确性区域
        accuracy_group = QGroupBox("分类准确性")
        accuracy_layout = QVBoxLayout(accuracy_group)
        
        self.accuracy_text = QTextEdit()
        self.accuracy_text.setMaximumHeight(150)
        accuracy_layout.addWidget(self.accuracy_text)
        
        layout.addWidget(accuracy_group)
        
        return tab
    
    def create_scene_classification_tab(self) -> QWidget:
        """创建场景分类标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 场景统计表格
        self.scene_table = QTableWidget()
        self.scene_table.setColumnCount(4)
        self.scene_table.setHorizontalHeaderLabels(["场景类型", "Map数量", "占比(%)", "平均权重"])
        
        # 设置表格属性
        header = self.scene_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.scene_table)
        
        return tab
    
    def create_parameter_distribution_tab(self) -> QWidget:
        """创建参数分布标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 参数统计表格
        self.parameter_table = QTableWidget()
        self.parameter_table.setColumnCount(6)
        self.parameter_table.setHorizontalHeaderLabels(["参数", "最小值", "最大值", "平均值", "标准差", "中位数"])
        
        # 设置表格属性
        header = self.parameter_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.parameter_table)
        
        return tab
    
    def create_detailed_report_tab(self) -> QWidget:
        """创建详细报告标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 详细报告文本区域
        self.detailed_report_text = QTextEdit()
        self.detailed_report_text.setPlainText("详细报告将在分析完成后显示...")
        layout.addWidget(self.detailed_report_text)
        
        return tab
    
    def create_button_area(self, parent_layout):
        """创建底部按钮区域"""
        button_layout = QHBoxLayout()
        
        # 导出报告按钮
        export_btn = QPushButton("导出报告")
        export_btn.clicked.connect(self.export_report)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        parent_layout.addLayout(button_layout)
    
    def setup_connections(self):
        """设置信号连接"""
        pass
    
    def open_config_dialog(self):
        """打开配置对话框"""
        try:
            dialog = AnalysisConfigDialog(self, self.classification_config)
            if dialog.exec_() == QDialog.Accepted:
                self.classification_config = dialog.get_config()
                logger.info("==liuq debug== 分类配置已更新")
                
        except Exception as e:
            logger.error(f"==liuq debug== 打开配置对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开配置对话框失败: {e}")
    
    def start_analysis(self):
        """开始分析"""
        try:
            if not self.configuration:
                QMessageBox.warning(self, "警告", "没有可分析的Map配置数据")
                return
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.analyze_btn.setEnabled(False)
            
            # 创建并启动分析线程
            self.analysis_worker = AnalysisWorker(self.configuration, self.classification_config)
            self.analysis_worker.progress_updated.connect(self.update_progress)
            self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
            self.analysis_worker.analysis_failed.connect(self.on_analysis_failed)
            self.analysis_worker.start()
            
            logger.info("==liuq debug== 多维度分析已启动")
            
        except Exception as e:
            logger.error(f"==liuq debug== 启动分析失败: {e}")
            QMessageBox.critical(self, "错误", f"启动分析失败: {e}")
            self.analyze_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{message} ({value}%)")
    
    def on_analysis_completed(self, result: dict):
        """分析完成处理"""
        try:
            self.analysis_result = result
            self.update_ui_with_results()
            
            self.progress_bar.setVisible(False)
            self.analyze_btn.setEnabled(True)
            
            QMessageBox.information(self, "完成", "多维度分析已完成")
            logger.info("==liuq debug== 多维度分析完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理分析结果失败: {e}")
            QMessageBox.critical(self, "错误", f"处理分析结果失败: {e}")
    
    def on_analysis_failed(self, error_message: str):
        """分析失败处理"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        QMessageBox.critical(self, "分析失败", f"分析过程中发生错误: {error_message}")
        logger.error(f"==liuq debug== 多维度分析失败: {error_message}")
    
    def update_ui_with_results(self):
        """使用分析结果更新UI"""
        if not self.analysis_result:
            return
        
        try:
            # 更新概览标签页
            self.update_overview_tab()
            
            # 更新场景分类标签页
            self.update_scene_classification_tab()
            
            # 更新参数分布标签页
            self.update_parameter_distribution_tab()
            
            # 更新详细报告标签页
            self.update_detailed_report_tab()
            
            logger.info("==liuq debug== UI更新完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== 更新UI失败: {e}")
    
    def update_overview_tab(self):
        """更新概览标签页"""
        try:
            summary_stats = self.analysis_result.get('summary_statistics', {})
            accuracy_analysis = self.analysis_result.get('accuracy_analysis', {})
            
            # 更新统计摘要
            summary_text = f"""
分析概览：

总Map数量: {summary_stats.get('total_map_count', 0)}

场景分布:
• 室外场景: {summary_stats.get('scene_distribution', {}).get('outdoor', {}).get('count', 0)} 个 ({summary_stats.get('scene_distribution', {}).get('outdoor', {}).get('percentage', 0):.1f}%)
• 室内场景: {summary_stats.get('scene_distribution', {}).get('indoor', {}).get('count', 0)} 个 ({summary_stats.get('scene_distribution', {}).get('indoor', {}).get('percentage', 0):.1f}%)
• 夜景场景: {summary_stats.get('scene_distribution', {}).get('night', {}).get('count', 0)} 个 ({summary_stats.get('scene_distribution', {}).get('night', {}).get('percentage', 0):.1f}%)

主导场景: {summary_stats.get('dominant_scene', '未知')}

分类阈值:
• BV室外阈值: {summary_stats.get('classification_thresholds', {}).get('bv_outdoor_threshold', 0)}
• BV室内下限: {summary_stats.get('classification_thresholds', {}).get('bv_indoor_min', 0)}
• IR室外阈值: {summary_stats.get('classification_thresholds', {}).get('ir_outdoor_threshold', 0)}
            """
            self.summary_text.setPlainText(summary_text.strip())
            
            # 更新准确性分析
            accuracy_text = f"""
分类准确性分析：

总Map数量: {accuracy_analysis.get('total_maps', 0)}
一致分类: {accuracy_analysis.get('consistent_count', 0)} 个
不一致分类: {accuracy_analysis.get('inconsistent_count', 0)} 个
准确率: {accuracy_analysis.get('accuracy_percentage', 0):.1f}%

注：准确率是指新分类规则与原始分类的一致性程度
            """
            self.accuracy_text.setPlainText(accuracy_text.strip())
            
        except Exception as e:
            logger.error(f"==liuq debug== 更新概览标签页失败: {e}")
    
    def update_scene_classification_tab(self):
        """更新场景分类标签页"""
        try:
            scene_analysis = self.analysis_result.get('scene_analysis', {})
            
            # 设置表格行数
            self.scene_table.setRowCount(len(scene_analysis))
            
            row = 0
            for scene_type, scene_data in scene_analysis.items():
                # 计算平均权重
                maps = scene_data.get('maps', [])
                avg_weight = sum(m.get('weight', 0) for m in maps) / len(maps) if maps else 0
                
                # 场景类型
                scene_name_map = {
                    'outdoor': '室外场景',
                    'indoor': '室内场景', 
                    'night': '夜景场景'
                }
                self.scene_table.setItem(row, 0, QTableWidgetItem(scene_name_map.get(scene_type, scene_type)))
                
                # Map数量
                self.scene_table.setItem(row, 1, QTableWidgetItem(str(scene_data.get('count', 0))))
                
                # 占比
                self.scene_table.setItem(row, 2, QTableWidgetItem(f"{scene_data.get('percentage', 0):.1f}"))
                
                # 平均权重
                self.scene_table.setItem(row, 3, QTableWidgetItem(f"{avg_weight:.2f}"))
                
                row += 1
                
        except Exception as e:
            logger.error(f"==liuq debug== 更新场景分类标签页失败: {e}")
    
    def update_parameter_distribution_tab(self):
        """更新参数分布标签页"""
        try:
            parameter_analysis = self.analysis_result.get('parameter_analysis', {})
            
            # 设置表格行数
            self.parameter_table.setRowCount(len(parameter_analysis))
            
            row = 0
            for param_name, param_stats in parameter_analysis.items():
                # 参数名称映射
                param_name_map = {
                    'bv_min': 'BV最小值',
                    'ir_min': 'IR最小值',
                    'weight': '权重'
                }
                
                self.parameter_table.setItem(row, 0, QTableWidgetItem(param_name_map.get(param_name, param_name)))
                self.parameter_table.setItem(row, 1, QTableWidgetItem(f"{param_stats.get('min', 0):.2f}"))
                self.parameter_table.setItem(row, 2, QTableWidgetItem(f"{param_stats.get('max', 0):.2f}"))
                self.parameter_table.setItem(row, 3, QTableWidgetItem(f"{param_stats.get('mean', 0):.2f}"))
                self.parameter_table.setItem(row, 4, QTableWidgetItem(f"{param_stats.get('std', 0):.2f}"))
                self.parameter_table.setItem(row, 5, QTableWidgetItem(f"{param_stats.get('median', 0):.2f}"))
                
                row += 1
                
        except Exception as e:
            logger.error(f"==liuq debug== 更新参数分布标签页失败: {e}")
    
    def update_detailed_report_tab(self):
        """更新详细报告标签页"""
        try:
            # 生成详细报告文本
            report_text = self.generate_detailed_report_text()
            self.detailed_report_text.setPlainText(report_text)
            
        except Exception as e:
            logger.error(f"==liuq debug== 更新详细报告标签页失败: {e}")
    
    def generate_detailed_report_text(self) -> str:
        """生成详细报告文本"""
        if not self.analysis_result:
            return "暂无分析结果"
        
        try:
            report_lines = []
            report_lines.append("=" * 60)
            report_lines.append("Map数据多维度分析详细报告")
            report_lines.append("=" * 60)
            report_lines.append("")
            
            # 分析元数据
            metadata = self.analysis_result.get('analysis_metadata', {})
            report_lines.append(f"分析时间: {metadata.get('timestamp', '未知')}")
            report_lines.append(f"分析耗时: {metadata.get('duration_seconds', 0):.2f} 秒")
            report_lines.append(f"总Map数量: {metadata.get('total_map_points', 0)}")
            report_lines.append("")
            
            # 场景分类详情
            scene_analysis = self.analysis_result.get('scene_analysis', {})
            report_lines.append("场景分类详情:")
            report_lines.append("-" * 40)
            
            for scene_type, scene_data in scene_analysis.items():
                scene_name_map = {
                    'outdoor': '室外场景',
                    'indoor': '室内场景',
                    'night': '夜景场景'
                }
                scene_name = scene_name_map.get(scene_type, scene_type)
                
                report_lines.append(f"\n{scene_name}:")
                report_lines.append(f"  数量: {scene_data.get('count', 0)} 个")
                report_lines.append(f"  占比: {scene_data.get('percentage', 0):.1f}%")
                
                # 显示前5个Map的详情
                maps = scene_data.get('maps', [])[:5]
                if maps:
                    report_lines.append("  代表性Map:")
                    for i, map_info in enumerate(maps, 1):
                        report_lines.append(f"    {i}. {map_info.get('alias_name', '未知')}")
                        report_lines.append(f"       BV_min: {map_info.get('bv_min', 0):.2f}, IR_ratio: {map_info.get('ir_ratio', 0):.2f}")
            
            report_lines.append("")
            
            # 分类准确性
            accuracy_analysis = self.analysis_result.get('accuracy_analysis', {})
            report_lines.append("分类准确性分析:")
            report_lines.append("-" * 40)
            report_lines.append(f"准确率: {accuracy_analysis.get('accuracy_percentage', 0):.1f}%")
            report_lines.append(f"一致分类: {accuracy_analysis.get('consistent_count', 0)} 个")
            report_lines.append(f"不一致分类: {accuracy_analysis.get('inconsistent_count', 0)} 个")
            
            # 显示不一致的案例
            inconsistent_maps = accuracy_analysis.get('inconsistent_maps', [])
            if inconsistent_maps:
                report_lines.append("\n不一致分类案例:")
                for i, case in enumerate(inconsistent_maps[:5], 1):
                    report_lines.append(f"  {i}. {case.get('alias_name', '未知')}")
                    report_lines.append(f"     原始分类: {case.get('original', '未知')} -> 新分类: {case.get('new', '未知')}")
                    report_lines.append(f"     BV_min: {case.get('bv_min', 0):.2f}, IR_ratio: {case.get('ir_ratio', 0):.2f}")
            
            report_lines.append("")
            report_lines.append("=" * 60)
            report_lines.append("报告结束")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成详细报告文本失败: {e}")
            return f"生成报告失败: {e}"
    
    def export_report(self):
        """导出报告"""
        try:
            if not self.analysis_result:
                QMessageBox.warning(self, "警告", "没有可导出的分析结果")
                return
            
            # 选择导出文件
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出分析报告", 
                f"多维度分析报告_{self.analysis_result.get('analysis_metadata', {}).get('timestamp', '').replace(':', '-').replace(' ', '_')}.json",
                "JSON文件 (*.json);;文本文件 (*.txt);;所有文件 (*)"
            )
            
            if file_path:
                if file_path.endswith('.json'):
                    # 导出JSON格式
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.analysis_result, f, ensure_ascii=False, indent=2)
                else:
                    # 导出文本格式
                    report_text = self.generate_detailed_report_text()
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(report_text)
                
                QMessageBox.information(self, "成功", f"报告已导出到: {file_path}")
                logger.info(f"==liuq debug== 分析报告已导出: {file_path}")
                
        except Exception as e:
            logger.error(f"==liuq debug== 导出报告失败: {e}")
            QMessageBox.critical(self, "导出失败", f"导出报告失败: {e}")
