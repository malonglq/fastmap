#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastMapV2 主窗口
==liuq debug== PyQt5主窗口实现

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 17:43:00 +08:00; Reason: P1-LD-005 建立PyQt主窗口框架; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: FastMapV2的主窗口界面，包含5个功能标签页
"""

from pathlib import Path
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout,
    QWidget, QMenuBar, QStatusBar, QAction, QMessageBox,
    QLabel, QPushButton, QTextEdit, QSplitter,
    QFileDialog, QApplication, QAbstractScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QFont
import time

# 导入ViewModel
from gui.view_models.main_window_view_model import get_main_window_viewmodel
from gui.managers.tab_communication_manager import get_tab_communication_manager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    FastMapV2主窗口类

    采用标签页设计，包含5个主要功能模块：
    1. Map分析界面
    2. EXIF处理界面
    3. 仿写功能界面
    4. 特征点功能界面
    5. 报告界面
    """

    # 自定义信号
    status_message = pyqtSignal(str)

    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        logger.info("==liuq debug== 开始初始化主窗口")

        # 初始化ViewModel
        self.view_model = get_main_window_viewmodel()
        
        # 初始化Tab通信管理器
        self.tab_communication_manager = get_tab_communication_manager()
        
        # 连接ViewModel信号
        self._connect_viewmodel_signals()
        
        # 连接Tab通信管理器信号
        self._connect_tab_communication_signals()

        # 先在顶层窗口启用拖拽（尽早）
        try:
            self.setAcceptDrops(True)
            logger.info("==liuq debug== 顶层窗口预启用拖拽")
        except Exception:
            pass

        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.setup_signals()
        self.setup_drag_and_drop()
        # 启动签名，便于确认运行最新拖拽实现
        logger.info("==liuq debug== BOOT_SIGNATURE: DnD_v4_unified_manager_enabled")

        logger.info("==liuq debug== 主窗口初始化完成")
        # 启动“拖拽区域”兜底监控（桌面目录）
        try:
            self._start_drag_zone_monitor()
        except Exception as e:
            logger.debug("==liuq debug== 启动拖拽区域监控失败: %s", e)
        # 注意：统一拖拽注册改为在窗口显示后执行（showEvent 中），避免 HWND 未就绪
        logger.info("==liuq debug== 统一拖拽注册将于窗口显示后执行(SHOW)")
    
    def _connect_viewmodel_signals(self):
        """连接ViewModel信号"""
        # 连接状态消息信号
        self.view_model.status_message_changed.connect(self.status_message.emit)
        
        # 连接XML文件加载信号
        self.view_model.xml_file_loaded.connect(self._on_xml_file_loaded)
        
        # 连接分析完成信号
        self.view_model.map_analysis_completed.connect(self._on_map_analysis_completed)
        
        # 连接报告生成按钮状态信号
        self.view_model.generate_report_enabled.connect(self._on_generate_report_enabled)
    
    def _connect_tab_communication_signals(self):
        """连接Tab通信管理器信号"""
        # 连接状态更新信号
        self.tab_communication_manager.status_updated.connect(self.status_message.emit)
        
        # 连接XML文件加载信号
        self.tab_communication_manager.xml_file_loaded.connect(self._on_tab_xml_file_loaded)
        
        # 连接Map分析完成信号
        self.tab_communication_manager.map_analysis_completed.connect(self._on_tab_map_analysis_completed)
        
        # 连接EXIF处理完成信号
        self.tab_communication_manager.exif_processing_completed.connect(self._on_tab_exif_processing_completed)
        
        # 连接报告生成完成信号
        self.tab_communication_manager.report_generated.connect(self._on_tab_report_generated)



    def _ensure_native_drop_installed(self, phase: str = ""):
        try:
            from utils.win_drop import install_win_drop
            hwnd = int(self.winId())
            self._native_drop_filter = install_win_drop(hwnd, self._on_native_files)
            if self._native_drop_filter:
                logger.info("==liuq debug== 已安装 Windows 原生拖拽过滤器 (WM_DROPFILES) phase=%s hwnd=%s", phase, hwnd)
        except Exception as e:
            logger.debug("==liuq debug== _ensure_native_drop_installed 失败: %s", e)


    def setup_ui(self):
        """设置用户界面"""
        # 设置窗口属性
        self.setWindowTitle("FastMapV2 - 对比机Map分析&仿写工具 v2.0.0")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)

        # 设置窗口图标（如果有的话）
        # self.setWindowIcon(QIcon('resources/icon.png'))

        # 创建中央控件
        central_widget = QWidget()
        self._central_widget = central_widget
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(False)
        # 使标签容器也支持拖拽，并将事件转发给主窗口
        try:
            self.tab_widget.setAcceptDrops(True)
            self.tab_widget.installEventFilter(self)
        except Exception:
            pass

        # 创建各个标签页
        self.create_tabs()

        # 添加到主布局
        main_layout.addWidget(self.tab_widget)

        # 设置样式
        self.setup_styles()

        logger.info("==liuq debug== UI界面设置完成")

    def create_tabs(self):
        """创建所有标签页"""
        # 1. Map分析标签页
        self.map_analysis_tab = self.create_map_analysis_tab()
        self.tab_widget.addTab(self.map_analysis_tab, "Map分析")

        # 2. EXIF处理标签页
        self.exif_processing_tab = self.create_exif_processing_tab()
        self.tab_widget.addTab(self.exif_processing_tab, "EXIF处理")

        # 3. 仿写功能标签页
        self.copywriting_tab = self.create_copywriting_tab()
        self.tab_widget.addTab(self.copywriting_tab, "仿写功能")

        # 4. 特征点功能标签页
        self.feature_point_tab = self.create_feature_point_tab()
        self.tab_widget.addTab(self.feature_point_tab, "特征点功能")

        # 5. 报告标签页
        self.report_tab = self.create_report_tab()
        self.tab_widget.addTab(self.report_tab, "分析报告")
        # Windows 原生拖拽兜底（WM_DROPFILES）
        try:
            self._ensure_native_drop_installed(phase="create_tabs")
        except Exception as e:
            logger.debug("==liuq debug== 安装原生拖拽过滤器失败: %s", e)


        # 设置默认选中第一个标签页
        self.tab_widget.setCurrentIndex(0)

        logger.info("==liuq debug== 所有标签页创建完成")

    def create_map_analysis_tab(self) -> QWidget:
        """创建Map分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)


        # 顶部控制区域
        control_layout = QHBoxLayout()

        # XML文件选择
        self.xml_file_label = QLabel("未选择文件")
        self.xml_file_label.setWordWrap(True)
        control_layout.addWidget(QLabel("XML文件:"))
        control_layout.addWidget(self.xml_file_label, 1)

        # 已移除“选择XML文件/开始分析”按钮：通过菜单加载XML后自动分析

        self.generate_report_btn = QPushButton("生成HTML报告")
        self.generate_report_btn.clicked.connect(self._on_generate_report_clicked)
        self.generate_report_btn.setEnabled(False)
        control_layout.addWidget(self.generate_report_btn)

        # 已移除首页的“多维度分析”按钮，避免与分析报告页重复



        layout.addLayout(control_layout)

        # 主要内容区域（左右分栏）
        main_splitter = QSplitter(Qt.Horizontal)

        # 左侧：Map点列表表格 (70%宽度)
        from gui.widgets.map_table_widget import MapTableWidget
        self.map_table = MapTableWidget()
        # 直接连接到展示方法，确保右侧即时显示图形
        self.map_table.map_point_selected.connect(self.on_map_point_selected)
        self.map_table.base_boundary_selected.connect(self.on_base_boundary_selected)

        # 右侧：Map形状可视化 (30%宽度)
        from gui.widgets.map_shape_viewer import MapShapeViewer
        self.map_shape_viewer = MapShapeViewer()

        # 设置分割器
        main_splitter.addWidget(self.map_table)
        main_splitter.addWidget(self.map_shape_viewer)
        main_splitter.setSizes([700, 300])  # 70:30 比例

        layout.addWidget(main_splitter)

        return tab



    def create_exif_processing_tab(self) -> QWidget:
        """创建EXIF处理标签页 (接入 ExifProcessingTab)"""
        from gui.tabs.exif_processing_tab import ExifProcessingTab
        return ExifProcessingTab(self)

    def create_copywriting_tab(self) -> QWidget:
        """创建仿写功能标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 标题
        title_label = QLabel("Map配置仿写功能")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 占位内容
        content_label = QLabel("仿写功能将在Phase 3实现")
        content_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(content_label)

        return tab

    def create_feature_point_tab(self) -> QWidget:
        """创建特征点功能标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 标题
        title_label = QLabel("特征点功能")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 占位内容
        content_label = QLabel("特征点功能将在Phase 4实现")
        content_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(content_label)

        return tab

    def create_report_tab(self) -> QWidget:
        """创建报告标签页"""
        # 使用新的分析报告标签页
        from gui.tabs.analysis_report_tab import AnalysisReportTab

        analysis_report_tab = AnalysisReportTab(self)

        # 连接状态消息信号
        analysis_report_tab.status_message.connect(self.status_message.emit)

        return analysis_report_tab

    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')

        # 打开XML文件
        open_xml_action = QAction('打开XML文件(&O)', self)
        open_xml_action.setShortcut('Ctrl+O')
        open_xml_action.triggered.connect(self.open_xml_file)
        file_menu.addAction(open_xml_action)

        # 保存XML文件
        self.save_xml_action = QAction('保存XML文件(&S)', self)
        self.save_xml_action.setShortcut('Ctrl+S')
        self.save_xml_action.triggered.connect(self.save_xml_file)
        self.save_xml_action.setEnabled(False)  # 初始状态禁用
        file_menu.addAction(self.save_xml_action)

        # 另存为XML文件
        self.save_as_xml_action = QAction('另存为XML文件(&A)', self)
        self.save_as_xml_action.setShortcut('Ctrl+Shift+S')
        self.save_as_xml_action.triggered.connect(self.save_xml_file_as)
        self.save_as_xml_action.setEnabled(False)  # 初始状态禁用
        file_menu.addAction(self.save_as_xml_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具菜单
        tools_menu = menubar.addMenu('工具(&T)')

        # 设置
        settings_action = QAction('设置(&S)', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')

        # 关于
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        logger.info("==liuq debug== 菜单栏设置完成")

    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")

        # 添加永久状态信息
        self.status_label = QLabel("FastMapV2 v2.0.0")
        self.status_bar.addPermanentWidget(self.status_label)

        logger.info("==liuq debug== 状态栏设置完成")

    def setup_signals(self):
        """设置信号连接"""
        # 连接自定义信号
        self.status_message.connect(self.status_bar.showMessage)

        # 连接标签页切换信号
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        logger.info("==liuq debug== 信号连接设置完成")

    def setup_styles(self):
        """设置界面样式"""
        # 设置整体样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #0078d4;
            }
            /* 按钮统一改为白底描边+主色文字，降低视觉噪音 */
            QPushButton {
                background-color: #ffffff;
                color: #0078d4;
                border: 1px solid #0078d4;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f3f6fb;
                border-color: #106ebe;
                color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #e7effb;
                border-color: #005a9e;
                color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                border-color: #d1d5db;
                color: #9ca3af;
            }
        """)

        logger.info("==liuq debug== 界面样式设置完成")

    def on_tab_changed(self, index):
        """标签页切换事件处理"""
        tab_names = ["Map分析", "EXIF处理", "仿写功能", "特征点功能", "分析报告"]
        if 0 <= index < len(tab_names):
            tab_name = tab_names[index]
            self.status_message.emit(f"切换到 {tab_name} 标签页")
            logger.info(f"==liuq debug== 切换到标签页: {tab_name}")
            
            # 通过ViewModel触发事件
            from core.infrastructure.event_bus import EventType
            self.view_model.event_bus.emit(EventType.TAB_CHANGED, {
                'tab_index': index,
                'tab_name': tab_name
            })
    
    def _on_map_point_selected(self, point_index: int):
        """处理Map点选择事件"""
        try:
            # 通过ViewModel处理Map点选择
            self.view_model.select_map_point(point_index)
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Map点选择事件失败: {e}")
    
    def _on_base_boundary_selected(self):
        """处理基础边界选择事件"""
        try:
            # 通过ViewModel处理基础边界选择
            self.view_model.select_base_boundary()
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理基础边界选择事件失败: {e}")

    def open_xml_file(self):
        """打开XML文件"""
        self._select_xml_file()

    def save_xml_file(self):
        """保存XML文件"""
        try:
            if not self.view_model.current_xml_file:
                QMessageBox.warning(self, "警告", "没有打开的XML文件")
                return
            
            success = self.view_model.save_xml_file()
            if success:
                QMessageBox.information(self, "成功", "XML文件保存成功")
            else:
                QMessageBox.warning(self, "警告", "XML文件保存失败")
                
        except Exception as e:
            logger.error(f"==liuq debug== 保存XML文件失败: {e}")
            QMessageBox.critical(self, "错误", f"保存文件失败: {e}")

    def save_xml_file_as(self):
        """另存为XML文件"""
        try:
            if not self.view_model.map_configuration:
                QMessageBox.warning(self, "警告", "没有可保存的配置数据")
                return

            # 选择保存路径
            filename, _ = QFileDialog.getSaveFileName(
                self, "另存为XML文件", "",
                "XML files (*.xml);;All files (*.*)"
            )

            if filename:
                success = self.view_model.save_xml_file(filename)
                if success:
                    QMessageBox.information(self, "成功", "XML文件保存成功")
                else:
                    QMessageBox.warning(self, "警告", "XML文件保存失败")

        except Exception as e:
            logger.error(f"==liuq debug== 另存为XML文件失败: {e}")
            QMessageBox.critical(self, "错误", f"另存为文件失败: {e}")
    
    def _select_xml_file(self):
        """选择XML文件"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "选择Map配置XML文件", "",
                "XML files (*.xml);;All files (*.*)"
            )

            if filename:
                # 使用ViewModel加载XML文件
                success = self.view_model.load_xml_file(filename)
                if not success:
                    QMessageBox.critical(self, "错误", "XML文件加载失败")

        except Exception as e:
            logger.error(f"==liuq debug== 选择XML文件失败: {e}")
            QMessageBox.critical(self, "错误", f"选择文件失败: {e}")
    
    def _on_xml_file_loaded(self, file_path: str):
        """处理XML文件加载完成事件"""
        try:
            # 更新UI显示
            self.xml_file_label.setText(f"文件: {self.view_model.get_xml_file_display_name()}")
            
            # 启用相关菜单项
            self.save_xml_action.setEnabled(True)
            self.save_as_xml_action.setEnabled(True)
            
            # 更新组件
            if hasattr(self, 'map_shape_viewer') and self.map_shape_viewer:
                self.map_shape_viewer.set_xml_white_points(file_path)
                
        except Exception as e:
            logger.error(f"==liuq debug== 处理XML文件加载事件失败: {e}")
    
    def _on_map_analysis_completed(self, analysis_result):
        """处理Map分析完成事件"""
        try:
            # 更新表格数据
            if hasattr(self, 'map_table') and self.map_table:
                try:
                    # 使用ViewModel中已解析好的 MapConfiguration 刷新左侧表格
                    if self.view_model.map_configuration:
                        self.map_table.set_configuration(self.view_model.map_configuration)
                        # 传递XML路径，支持自动保存等功能
                        if self.view_model.current_xml_file:
                            self.map_table.set_xml_file_path(str(self.view_model.current_xml_file))
                        logger.info("==liuq debug== 通过ViewModel分析完成回调刷新Map表格")
                    else:
                        logger.warning("==liuq debug== 分析完成但无map_configuration，跳过表格刷新")
                except Exception as _e:
                    logger.error(f"==liuq debug== 刷新Map表格失败: {_e}")

            # 更新形状查看器
            if hasattr(self, 'map_shape_viewer') and self.map_shape_viewer:
                # 传入 MapPoint 形态的 base_boundary_point（若存在）
                try:
                    bbp = getattr(self.view_model.map_configuration, 'base_boundary_point', None)
                except Exception:
                    bbp = None
                if bbp:
                    self.map_shape_viewer.show_base_boundary(bbp)

        except Exception as e:
            logger.error(f"==liuq debug== 处理Map分析完成事件失败: {e}")
    
    def _on_generate_report_enabled(self, enabled: bool):
        """处理报告生成按钮状态事件"""
        try:
            if hasattr(self, 'generate_report_btn'):
                self.generate_report_btn.setEnabled(enabled)
                
        except Exception as e:
            logger.error(f"==liuq debug== 处理报告生成按钮状态事件失败: {e}")
    
    def _on_generate_report_clicked(self):
        """处理生成报告按钮点击事件"""
        try:
            # 使用新的MVVM架构：调用ViewModel的方法
            success = self.view_model.generate_html_report()
            if not success:
                QMessageBox.warning(self, "警告", "生成报告失败")

        except Exception as e:
            logger.error(f"==liuq debug== 生成HTML报告失败: {e}")
            QMessageBox.critical(self, "错误", f"生成报告失败: {e}")
    
    # Tab通信事件处理方法
    def _on_tab_xml_file_loaded(self, file_path: str, metadata: dict):
        """处理Tab通信的XML文件加载事件"""
        try:
            logger.info(f"==liuq debug== Tab通信: XML文件已加载 - {file_path}")
            # 可以在这里添加额外的UI更新逻辑
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab通信XML文件加载事件失败: {e}")
    
    def _on_tab_map_analysis_completed(self, analysis_result: dict):
        """处理Tab通信的Map分析完成事件"""
        try:
            logger.info("==liuq debug== Tab通信: Map分析已完成")
            # 可以在这里添加额外的UI更新逻辑
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab通信Map分析完成事件失败: {e}")
    
    def _on_tab_exif_processing_completed(self, processing_path: str, result: dict):
        """处理Tab通信的EXIF处理完成事件"""
        try:
            logger.info(f"==liuq debug== Tab通信: EXIF处理已完成 - {processing_path}")
            # 可以在这里添加额外的UI更新逻辑
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab通信EXIF处理完成事件失败: {e}")
    
    def _on_tab_report_generated(self, report_type: str, file_path: str):
        """处理Tab通信的报告生成完成事件（新MVVM架构）"""
        try:
            logger.info(f"==liuq debug== Tab通信: {report_type}报告已生成 - {file_path}")

            # 显示报告生成完成弹窗（从旧逻辑迁移）
            reply = QMessageBox.question(
                self, '报告生成完成',
                f'HTML报告已生成: {file_path}\n\n是否立即打开？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                from utils.browser_utils import open_html_report
                open_html_report(file_path)

        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab通信报告生成事件失败: {e}")

    def select_xml_file(self):
        """选择XML文件"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "选择Map配置XML文件", "",
                "XML files (*.xml);;All files (*.*)"
            )

            if filename:
                self.xml_file_label.setText(f"文件: {filename}")
                self.current_xml_file = filename
                # 将白点XML路径设置到形状查看器（用于从XML加载白点参考点）
                try:
                    if hasattr(self, 'map_shape_viewer') and self.map_shape_viewer:
                        self.map_shape_viewer.set_xml_white_points(filename)
                except Exception as _e:
                    logger.warning(f"==liuq debug== 传递XML白点路径失败: {_e}")
                # 直接开始分析
                self.status_message.emit(f"已选择XML文件: {filename}，开始分析…")
                logger.info(f"==liuq debug== 选择XML并自动分析: {filename}")
                self.start_map_analysis()

        except Exception as e:
            logger.error(f"==liuq debug== 选择XML文件失败: {e}")
            QMessageBox.critical(self, "错误", f"选择文件失败: {e}")

    def start_map_analysis(self):
        """开始Map分析"""
        try:
            if not hasattr(self, 'current_xml_file'):
                QMessageBox.warning(self, "警告", "请先选择XML文件")
                return

            self.status_message.emit("正在分析Map配置...")

            # 导入必要的类
            from core.services.map_analysis.xml_parser_service import XMLParserService
            from core.services.map_analysis.map_analyzer import MapAnalyzer
            from core.services.map_analysis.multi_dimensional_analyzer import MultiDimensionalAnalyzer
            from core.models.scene_classification_config import SceneClassificationConfig, get_default_config_path

            # 解析XML文件
            parser = XMLParserService()
            t0 = time.time()
            self.map_configuration = parser.parse_xml(self.current_xml_file, "analysis")
            logger.info("==liuq debug== XML解析完成，用时 %.3fs", time.time() - t0)

            # 立即更新右侧 MapShapeViewer（在任何重负载操作之前），避免延迟
            try:
                if hasattr(self, 'map_shape_viewer') and self.map_shape_viewer:
                    self.map_shape_viewer.clear_current_selections()
                    if getattr(self.map_configuration, 'base_boundary_point', None):
                        self.map_shape_viewer.show_base_boundary(self.map_configuration.base_boundary_point)
                        # 立刻刷新Qt事件，确保即刻渲染
                        from PyQt5.QtWidgets import QApplication
                        QApplication.processEvents()
                        logger.info("==liuq debug== ⏱ 已即时刷新右侧Base Boundary显示（在表格/分析前）")
                    else:
                        logger.info("==liuq debug== 新配置不包含 base_boundary_point，右侧视图显示为空状态")
            except Exception as _e:
                logger.warning(f"==liuq debug== 预刷新MapShapeViewer失败: {_e}")

            # 将后续重负载任务安排到事件循环中，避免阻塞刚刚完成的即时重绘
            try:
                QTimer.singleShot(0, self._continue_map_analysis)
                logger.info("==liuq debug== 已安排延后执行_continue_map_analysis，立刻返回事件循环以展示即时重绘")
                return
            except Exception as _e:
                logger.warning(f"==liuq debug== 安排延后执行失败，回退为同步流程: {_e}")
                # fallback: 若singleShot异常，则继续执行同步流程

                # 创建传统分析器并分析
                t1 = time.time()
                self.map_analyzer = MapAnalyzer(self.map_configuration)
                self.analysis_result = self.map_analyzer.analyze()

                # 同时设置ViewModel的数据（新MVVM架构）
                self.view_model.set_map_analyzer(self.map_analyzer)
                self.view_model.set_map_configuration(self.map_configuration)

                logger.info("==liuq debug== MapAnalyzer分析完成，用时 %.3fs", time.time() - t1)

                # 创建多维度分析器并分析（使用相同的MapConfiguration数据源）
                t2 = time.time()
                classification_config = SceneClassificationConfig.load_from_file(get_default_config_path())
                self.multi_dimensional_analyzer = MultiDimensionalAnalyzer(self.map_configuration, classification_config)
                self.multi_dimensional_result = self.multi_dimensional_analyzer.analyze()
                logger.info("==liuq debug== MultiDimensional分析完成，用时 %.3fs", time.time() - t2)

                # 更新Map点表格，同时传递XML文件路径以支持自动保存
                t3 = time.time()
                self.map_table.set_configuration(self.map_configuration)
                self.map_table.set_xml_file_path(self.current_xml_file)
                logger.info("==liuq debug== 表格填充完成，用时 %.3fs", time.time() - t3)

                # 再次确保右侧显示保持最新（避免表格重绘覆盖）
                try:
                    if hasattr(self, 'map_shape_viewer') and self.map_shape_viewer and getattr(self.map_configuration, 'base_boundary_point', None):
                        self.map_shape_viewer.show_base_boundary(self.map_configuration.base_boundary_point)
                except Exception as _e2:
                    logger.warning(f"==liuq debug== 最终确认刷新MapShapeViewer失败: {_e2}")

                # 启用报告生成按钮和保存按钮（首页已移除多维度分析按钮）
                self.generate_report_btn.setEnabled(True)
                self.save_xml_action.setEnabled(True)
                self.save_as_xml_action.setEnabled(True)

                self.status_message.emit(f"分析完成，共 {len(self.map_configuration.map_points)} 个Map点")
                logger.info(f"==liuq debug== Map分析完成")
        except Exception as e:
            logger.error(f"==liuq debug== Map分析失败: {e}")
            QMessageBox.critical(self, "分析错误", f"Map分析失败: {e}")
            self.status_message.emit("分析失败")


    def _continue_map_analysis(self):
        """延后执行的重负载步骤，避免阻塞即时重绘。"""
        try:
            from core.services.map_analysis.map_analyzer import MapAnalyzer
            from core.services.map_analysis.multi_dimensional_analyzer import MultiDimensionalAnalyzer
            from core.models.scene_classification_config import SceneClassificationConfig, get_default_config_path

            t1 = time.time()
            self.map_analyzer = MapAnalyzer(self.map_configuration)
            self.analysis_result = self.map_analyzer.analyze()

            # 同时设置ViewModel的数据（新MVVM架构）
            self.view_model.set_map_analyzer(self.map_analyzer)
            self.view_model.set_map_configuration(self.map_configuration)

            logger.info("==liuq debug== (延后)MapAnalyzer分析完成，用时 %.3fs", time.time() - t1)

            t2 = time.time()
            classification_config = SceneClassificationConfig.load_from_file(get_default_config_path())
            self.multi_dimensional_analyzer = MultiDimensionalAnalyzer(self.map_configuration, classification_config)
            self.multi_dimensional_result = self.multi_dimensional_analyzer.analyze()
            logger.info("==liuq debug== (延后)MultiDimensional分析完成，用时 %.3fs", time.time() - t2)

            t3 = time.time()
            self.map_table.set_configuration(self.map_configuration)
            self.map_table.set_xml_file_path(self.current_xml_file)
            logger.info("==liuq debug== (延后)表格填充完成，用时 %.3fs", time.time() - t3)

            try:
                if hasattr(self, 'map_shape_viewer') and self.map_shape_viewer and getattr(self.map_configuration, 'base_boundary_point', None):
                    self.map_shape_viewer.show_base_boundary(self.map_configuration.base_boundary_point)
            except Exception as _e2:
                logger.warning(f"==liuq debug== (延后)最终确认刷新MapShapeViewer失败: {_e2}")

            self.generate_report_btn.setEnabled(True)
            self.save_xml_action.setEnabled(True)
            self.save_as_xml_action.setEnabled(True)

            self.status_message.emit(f"分析完成，共 {len(self.map_configuration.map_points)} 个Map点")
            logger.info(f"==liuq debug== (延后)Map分析完成")
        except Exception as e:
            logger.error(f"==liuq debug== _continue_map_analysis失败: {e}")

    # 旧的generate_html_report方法已迁移到MainWindowViewModel中（新MVVM架构）

    # 首页已移除多维度分析入口；保留报告页内的多维度分析

    def on_map_point_selected(self, map_point):
        """处理Map点选择事件"""
        try:
            self.map_shape_viewer.show_map_point(map_point)
            self.status_message.emit(f"选中Map点: {map_point.alias_name}")

        except Exception as e:
            logger.error(f"==liuq debug== 显示Map点详情失败: {e}")

    def on_base_boundary_selected(self, base_boundary_point):
        """处理base_boundary选择事件"""
        try:
            # 传递base_boundary_point（MapPoint对象）而不是BaseBoundary对象
            self.map_shape_viewer.show_base_boundary(base_boundary_point)
            self.status_message.emit(f"选中Base Boundary: {base_boundary_point.alias_name}")

        except Exception as e:
            logger.error(f"==liuq debug== 显示base_boundary详情失败: {e}")


    def show_settings(self):
        """显示设置对话框"""
        QMessageBox.information(self, "设置", "设置功能待实现")
        logger.info("==liuq debug== 设置功能被调用")

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        FastMapV2 - 对比机Map分析&仿写工具

        版本: 2.0.0
        作者: 龙sir团队
        创建时间: 2025-07-25

        功能特性:
        • Map画图展示与分析报告
        • EXIF数据读取与处理
        • Map配置自动校准和仿写
        • 特征点功能支持
        • 专业HTML报告生成
        """
        QMessageBox.about(self, "关于 FastMapV2", about_text)
        logger.info("==liuq debug== 关于对话框被显示")



    def closeEvent(self, event):
        """窗口关闭事件处理"""
        try:
            # 在测试环境中直接关闭，避免QMessageBox阻塞
            if hasattr(self, '_is_testing') and self._is_testing:
                logger.info("==liuq debug== 测试环境直接关闭窗口")
                self._safe_cleanup_for_testing()
                event.accept()
                return

            reply = QMessageBox.question(
                self, '确认退出',
                '确定要退出FastMapV2吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # 清理拖拽管理器资源
                try:
                    # 简化清理逻辑，移除不存在的函数调用
                    logger.info("==liuq debug== 开始清理应用程序资源")
                    self._safe_cleanup_resources()
                except Exception as e:
                    logger.debug("==liuq debug== 清理资源失败: %s", e)

                logger.info("==liuq debug== 用户确认退出应用程序")
                event.accept()
            else:
                logger.info("==liuq debug== 用户取消退出操作")
                event.ignore()
        except Exception as e:
            logger.error(f"==liuq debug== closeEvent发生异常: {e}")
            # 在异常情况下也要接受关闭事件，避免程序卡死
            event.accept()

    def _safe_cleanup_for_testing(self):
        """测试环境下的安全清理"""
        try:
            # 断开所有信号连接，避免在清理过程中触发事件
            if hasattr(self, 'view_model') and self.view_model:
                try:
                    self.view_model.disconnect()
                except:
                    pass

            if hasattr(self, 'tab_communication_manager') and self.tab_communication_manager:
                try:
                    self.tab_communication_manager.disconnect()
                except:
                    pass

            # 清理标签页控件
            if hasattr(self, 'tab_widget') and self.tab_widget:
                try:
                    self.tab_widget.clear()
                except:
                    pass

            logger.info("==liuq debug== 测试环境清理完成")
        except Exception as e:
            logger.debug(f"==liuq debug== 测试环境清理异常: {e}")

    def _safe_cleanup_resources(self):
        """安全的资源清理"""
        try:
            # 清理各种资源，添加异常保护
            logger.info("==liuq debug== 开始安全清理资源")

            # 清理ViewModel
            if hasattr(self, 'view_model') and self.view_model:
                try:
                    self.view_model.cleanup()
                except:
                    pass

            # 清理Tab通信管理器
            if hasattr(self, 'tab_communication_manager') and self.tab_communication_manager:
                try:
                    self.tab_communication_manager.cleanup()
                except:
                    pass

            logger.info("==liuq debug== 资源清理完成")
        except Exception as e:
            logger.debug(f"==liuq debug== 资源清理异常: {e}")
    # === 拖拽单张图片，弹出EXIF快速查看对话框 ===
    def _install_drop_handlers(self, w):
        try:
            if w is None:
                return
            w.setAcceptDrops(True)
            w.installEventFilter(self)
            logger.info("==liuq debug== 已启用拖拽: %s", w.__class__.__name__)
        except Exception as e:
            logger.debug("==liuq debug== 启用拖拽失败: %s", e)

    def _install_all_drop_handlers(self, root: QWidget):
        try:
            if root is None:
                return
            self._install_drop_handlers(root)
            for w in root.findChildren(QWidget):
                self._install_drop_handlers(w)
                try:
                    # 针对 QAbstractScrollArea 的 viewport 也启用
                    if isinstance(w, QAbstractScrollArea) and w.viewport() is not None:
                        self._install_drop_handlers(w.viewport())
                except Exception as _:
                    pass
        except Exception as e:
            logger.debug("==liuq debug== _install_all_drop_handlers 异常: %s", e)

    def setup_drag_and_drop(self):
        try:
            # 递归安装
            self._install_all_drop_handlers(self)
            # 在 QApplication 层安装全局事件过滤器
            app = QApplication.instance()
            if app:
                app.installEventFilter(self)
                logger.info("==liuq debug== 已在 QApplication 安装全局事件过滤器")
        except Exception as e:
            logger.debug("==liuq debug== setup_drag_and_drop 异常: %s", e)

    def _start_drag_zone_monitor(self):
        """创建并监控桌面的“FastMap_拖拽区域”文件夹，作为拖拽兜底。
        将图片文件复制/拖拽到该文件夹即可自动弹出EXIF查看。
        """
        try:
            from pathlib import Path as _P
            desktop = _P.home() / 'Desktop'
            if not desktop.exists():
                # 中文环境可能是“桌面”
                alt = _P.home() / '桌面'
                desktop = alt if alt.exists() else _P.cwd()
            zone = desktop / 'FastMap_拖拽区域'
            zone.mkdir(parents=True, exist_ok=True)
            self._drag_zone_path = zone
            self._drag_zone_seen = set()
            # 预热已存在文件，避免首次立即触发
            for p in zone.glob('*.jp*g'):
                try:
                    self._drag_zone_seen.add(p.resolve())
                except Exception:
                    pass
            # 定时扫描
            self._drag_zone_timer = QTimer(self)
            self._drag_zone_timer.setInterval(1000)
            def _scan():
                try:
                    for p in zone.glob('*.jp*g'):
                        rp = p.resolve()
                        if rp not in self._drag_zone_seen:
                            self._drag_zone_seen.add(rp)
                            logger.info("==liuq debug== 拖拽区域检测到新文件: %s", str(rp))
                            # 调用同一处理逻辑
                            self._on_native_files([str(rp)])
                            break
                except Exception as e:
                    logger.debug("==liuq debug== 拖拽区域扫描异常: %s", e)
            self._drag_zone_timer.timeout.connect(_scan)
            self._drag_zone_timer.start()
            logger.info("==liuq debug== 拖拽区域已创建并开始监控: %s", str(zone))
        except Exception as e:
            logger.debug("==liuq debug== 启动拖拽区域监控失败: %s", e)

    # _install_ole_drop方法已删除 - ole_drop.py COM接口实现无效

    # _show_ole_fallback_window方法已删除 - ole_drop.py COM接口实现无效

    def _show_pywin_fallback_window(self):
        """创建一个置顶小窗，使用 pywin32 注册 IDropTarget 作为兜底。"""
        try:
            from utils.pywin_drop import install_pywin_drop
            win = QWidget(None)
            win.setWindowTitle("拖到这里 (pywin)")
            win.resize(260, 100)
            try:
                win.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.Tool)
            except Exception:
                pass
            try:
                win.setAttribute(Qt.WA_NativeWindow, True)
            except Exception:
                pass
            lay = QVBoxLayout(win)
            lab = QLabel("将 .jpg/.jpeg 文件\n拖到这里")
            lab.setAlignment(Qt.AlignCenter)
            lay.addWidget(lab)
            try:
                g = self.geometry()
                win.move(g.x() + g.width() - 300, g.y() + g.height() - 220)
            except Exception:
                pass
            hwnd = int(win.winId())
            dt = install_pywin_drop(hwnd, self._on_native_files)
            if dt is not None:
                self._pywin_fallback_win = win
                self._pywin_fallback_dt = dt
                win.show()
                logger.info("==liuq debug== pywin 兜底小窗 注册成功 hwnd=%s", hwnd)
            else:
                logger.info("==liuq debug== pywin 兜底小窗 注册失败")
        except Exception as e:
            logger.error("==liuq debug== _show_pywin_fallback_window 异常: %s", e)

    def dragEnterEvent(self, event):
        try:
            has_urls = event.mimeData().hasUrls()
            urls = event.mimeData().urls() if has_urls else []
            cnt = len(urls)
            first = urls[0].toLocalFile() if cnt >= 1 else ""
            logger.info("==liuq debug== DragEnter: hasUrls=%s count=%d first=%s", has_urls, cnt, first)
            if has_urls and cnt >= 1:
                # 放宽条件：先接受，drop 时再校验扩展名
                event.acceptProposedAction()
                return
            event.ignore()
        except Exception as e:
            logger.debug("==liuq debug== dragEnterEvent 异常: %s", e)
            event.ignore()

    def dragMoveEvent(self, event):
        try:
            if event.mimeData().hasUrls():
                urls = event.mimeData().urls()
                if len(urls) == 1:
                    p = urls[0].toLocalFile()
                    if p.lower().endswith(('.jpg', '.jpeg')):
                        event.acceptProposedAction(); return
            event.ignore()
        except Exception:
            event.ignore()

    # Windows 原生拖拽回调
    def _on_native_files(self, files):
        try:
            if not files:
                logger.info("==liuq debug== NativeDrop: no files")
                return
            p = files[0]
            logger.info("==liuq debug== NativeDrop: %s", p)
            if not p.lower().endswith(('.jpg', '.jpeg')):
                QMessageBox.warning(self, "提示", "仅支持 .jpg/.jpeg 文件")
                return
            from gui.dialogs.exif_quick_view_dialog import ExifQuickViewDialog
            dlg = ExifQuickViewDialog(Path(p), self)
            dlg.exec_()
        except Exception as e:
            logger.error("==liuq debug== _on_native_files 异常: %s", e)

    def showEvent(self, event):
        super().showEvent(event)
        try:
            logger.info("==liuq debug== SHOW 事件触发，开始 pywin 注册流程")
            from utils.pywin_drop import install_pywin_drop
            self._pywin_any_ok = False
            for tag, w in [("main", self), ("central", getattr(self, "_central_widget", None)), ("tabs", getattr(self, "tab_widget", None))]:
                if w is None:
                    continue
                try:
                    hwnd = int(w.winId())
                    dt = install_pywin_drop(hwnd, self._on_native_files)
                    if dt is not None:
                        self._pywin_any_ok = True
                        logger.info("==liuq debug== pywin %s 注册成功 hwnd=%s", tag, hwnd)
                except Exception as e:
                    logger.info("==liuq debug== pywin %s 注册异常: %s", tag, e)
            if not self._pywin_any_ok:
                logger.info("==liuq debug== pywin 主窗与子控件均未成功，显示兜底小窗")
                self._show_pywin_fallback_window()
        except Exception as e:
            logger.info("==liuq debug== SHOW 阶段 pywin 注册流程异常: %s", e)

    def eventFilter(self, obj, event):
        try:
            if event.type() == QEvent.DragEnter:
                logger.info("==liuq debug== eventFilter捕获DragEnter事件，obj=%s", obj.__class__.__name__)
                self.dragEnterEvent(event); return True
            if event.type() == QEvent.DragMove:
                logger.info("==liuq debug== eventFilter捕获DragMove事件，obj=%s", obj.__class__.__name__)
                self.dragMoveEvent(event); return True
            if event.type() == QEvent.Drop:
                logger.info("==liuq debug== eventFilter捕获Drop事件，obj=%s", obj.__class__.__name__)
                self.dropEvent(event); return True
        except Exception as e:
            logger.debug("==liuq debug== eventFilter 异常: %s", e)
        return super().eventFilter(obj, event)

    def dropEvent(self, event):
        try:
            urls = event.mimeData().urls()
            if not urls:
                logger.info("==liuq debug== Drop: no urls")
                return
            p = urls[0].toLocalFile()
            logger.info("==liuq debug== Drop: %s", p)
            if not p or not p.lower().endswith(('.jpg', '.jpeg')):
                QMessageBox.warning(self, "提示", "仅支持 .jpg/.jpeg 文件")
                return
            from gui.dialogs.exif_quick_view_dialog import ExifQuickViewDialog
            dlg = ExifQuickViewDialog(Path(p), self)
            dlg.exec_()
        except Exception as e:
            logger.error("==liuq debug== dropEvent 异常: %s", e)
            QMessageBox.critical(self, "错误", f"打开图片失败: {e}")
        finally:
            try:
                event.acceptProposedAction()
            except Exception:
                pass
