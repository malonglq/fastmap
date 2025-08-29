#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口ViewModel
==liuq debug== FastMapV2 主窗口ViewModel

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: 主窗口的MVVM架构ViewModel，管理主窗口的业务逻辑和数据状态
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import pyqtSignal

from core.infrastructure.base_view_model import BaseViewModel
from core.infrastructure.event_bus import EventType
from core.models.map_data import MapPoint, BaseBoundary
from core.services.map_analysis.xml_parser_service import XMLParserService
from core.services.map_analysis.map_analyzer import MapAnalyzer
from core.models.map_data import MapConfiguration

logger = logging.getLogger(__name__)


class MainWindowViewModel(BaseViewModel):
    """
    主窗口ViewModel
    
    管理主窗口的状态和业务逻辑：
    - XML文件管理
    - Map分析状态管理
    - Tab间数据共享
    - 状态消息管理
    """
    
    # 自定义信号
    xml_file_loaded = pyqtSignal(str)  # XML文件加载完成
    map_analysis_completed = pyqtSignal(object)  # Map分析完成
    status_message_changed = pyqtSignal(str)  # 状态消息更新
    generate_report_enabled = pyqtSignal(bool)  # 报告生成按钮状态
    
    def __init__(self):
        """初始化主窗口ViewModel"""
        super().__init__()
        
        # 数据状态
        self._current_xml_file: Optional[Path] = None
        self._map_configuration: Optional[MapConfiguration] = None
        self._map_analyzer: Optional[MapAnalyzer] = None
        self._analysis_result: Optional[Dict[str, Any]] = None
        self._map_points: List[MapPoint] = []
        self._base_boundary: Optional[BaseBoundary] = None
        
        # 获取服务
        self._xml_parser = self.di_container.resolve(XMLParserService)
        
        # 设置事件监听
        self._setup_event_listeners()
        
        logger.info("==liuq debug== 主窗口ViewModel初始化完成")
    
    @property
    def current_xml_file(self) -> Optional[Path]:
        """当前XML文件路径"""
        return self._current_xml_file
    
    @property
    def map_points(self) -> List[MapPoint]:
        """Map点列表"""
        return self._map_points
    
    @property
    def base_boundary(self) -> Optional[BaseBoundary]:
        """基础边界"""
        return self._base_boundary
    
    @property
    def analysis_result(self) -> Optional[Dict[str, Any]]:
        """分析结果"""
        return self._analysis_result
    
    @property
    def map_configuration(self) -> Optional[MapConfiguration]:
        """Map配置"""
        return self._map_configuration
    
    def load_xml_file(self, file_path: str) -> bool:
        """
        加载XML文件
        
        Args:
            file_path: XML文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            self.set_status_message("正在加载XML文件...")
            
            xml_path = Path(file_path)
            if not xml_path.exists():
                self.set_status_message(f"文件不存在: {file_path}")
                return False
            
            # 解析XML文件
            config = self._xml_parser.parse_xml(xml_path)
            
            if not config:
                self.set_status_message("XML解析失败: 无法解析配置")
                return False
            
            # 更新状态
            self._current_xml_file = xml_path
            self._map_points = config.map_points
            self._base_boundary = config.base_boundary
            self._map_configuration = config
            
            # 创建分析器
            self._map_analyzer = MapAnalyzer(self._map_configuration)
            
            # 发送信号
            self.xml_file_loaded.emit(str(xml_path))
            self.set_status_message(f"XML文件加载完成: {xml_path.name}")
            
            # 触发事件
            self.event_bus.emit(EventType.XML_FILE_LOADED, {
                'file_path': str(xml_path),
                'map_points_count': len(self._map_points),
                'has_base_boundary': self._base_boundary is not None
            })
            
            # 自动开始分析
            self._perform_analysis()
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 加载XML文件失败: {e}")
            self.set_status_message(f"加载XML文件失败: {e}")
            return False
    
    def save_xml_file(self, file_path: Optional[str] = None) -> bool:
        """
        保存XML文件（调用XMLWriterService，保留原有格式/结构，仅替换字段值）
        """
        try:
            if not self._map_configuration:
                self.set_status_message("没有可保存的Map配置")
                return False

            save_path = Path(file_path) if file_path else self._current_xml_file
            if not save_path:
                self.set_status_message("未指定保存路径")
                return False

            self.set_status_message("正在保存XML文件...")

            # 使用XMLWriterService 进行高保真写入
            from core.services.map_analysis.xml_writer_service import XMLWriterService
            writer = XMLWriterService()
            try:
                # 预载入以保留原XML树结构与格式
                writer.load_xml_for_editing(save_path)
            except Exception as _e:
                logger.warning(f"==liuq debug== 预载入XML失败，继续直接写入: {_e}")
            try:
                writer.mark_data_modified("ViewModel触发保存")
            except Exception:
                pass

            ok = writer.write_xml(self._map_configuration, save_path, backup=True, preserve_format=True)

            if ok:
                self.set_status_message(f"XML文件保存完成: {save_path.name}")
                logger.info(f"==liuq debug== XML文件保存成功: {save_path}")
                # 触发事件
                self.event_bus.emit(EventType.XML_FILE_SAVED, {
                    'file_path': str(save_path)
                })
                return True
            else:
                self.set_status_message("XML文件保存失败")
                logger.error("==liuq debug== XML文件保存失败")
                return False

        except Exception as e:
            logger.error(f"==liuq debug== 保存XML文件失败: {e}")
            self.set_status_message(f"保存XML文件失败: {e}")
            return False

    def generate_html_report(self) -> bool:
        """
        生成HTML报告（新MVVM架构实现）

        Returns:
            bool: 生成是否成功
        """
        try:
            if not self._analysis_result:
                self.set_status_message("没有分析结果，无法生成报告")
                return False

            # 检查是否有map_analyzer（从旧逻辑迁移）
            if not hasattr(self, '_map_analyzer') or not self._map_analyzer:
                self.set_status_message("请先进行Map分析")
                return False

            self.set_status_message("正在生成HTML报告...")

            # 实际的报告生成逻辑（从旧的MainWindow.generate_html_report迁移）
            report_path = self._execute_report_generation()

            if report_path:
                # 触发报告生成完成事件
                self.event_bus.emit(EventType.REPORT_GENERATION_COMPLETED, {
                    'report_type': 'map_analysis',
                    'file_path': report_path,
                    'success': True
                })

                self.set_status_message("HTML报告生成完成")
                logger.info(f"==liuq debug== HTML报告生成完成: {report_path}")
                return True
            else:
                self.set_status_message("HTML报告生成失败")
                return False

        except Exception as e:
            logger.error(f"==liuq debug== 生成HTML报告失败: {e}")
            self.set_status_message(f"生成HTML报告失败: {e}")
            return False

    def _execute_report_generation(self) -> Optional[str]:
        """
        执行实际的报告生成逻辑（从旧的MainWindow.generate_html_report迁移）

        Returns:
            str: 报告文件路径，失败返回None
        """
        try:
            # 导入必要的类
            from core.services.reporting.html_generator import UniversalHTMLGenerator
            from core.services.reporting.combined_report_data_provider import CombinedReportDataProvider
            from core.services.map_analysis.multi_dimensional_analyzer import MultiDimensionalAnalyzer
            from core.models.scene_classification_config import SceneClassificationConfig, get_default_config_path

            # 检查是否有MapConfiguration数据
            if not self._map_configuration:
                logger.error("==liuq debug== 缺少MapConfiguration数据，无法创建多维度分析器")
                return None

            # 创建多维度分析器（需要传递configuration参数）
            classification_config = SceneClassificationConfig.load_from_file(get_default_config_path())
            multi_dimensional_analyzer = MultiDimensionalAnalyzer(
                self._map_configuration,
                classification_config
            )

            # 执行多维度分析
            multi_dimensional_result = multi_dimensional_analyzer.analyze()

            # 创建组合数据提供者
            combined_data_provider = CombinedReportDataProvider(
                self._map_analyzer,
                multi_dimensional_analyzer,
                include_multi_dimensional=True  # 默认包含多维度分析
            )

            # 创建报告生成器
            html_generator = UniversalHTMLGenerator()

            # 生成报告
            report_path = html_generator.generate_report(
                combined_data_provider,
                template_name="map_analysis"
            )

            return report_path

        except Exception as e:
            logger.error(f"==liuq debug== 执行报告生成失败: {e}")
            return None

    def set_map_analyzer(self, map_analyzer):
        """设置map_analyzer实例"""
        self._map_analyzer = map_analyzer
        logger.debug(f"==liuq debug== ViewModel已设置map_analyzer: {type(map_analyzer)}")

    def set_map_configuration(self, map_configuration):
        """设置map_configuration实例"""
        self._map_configuration = map_configuration
        logger.debug(f"==liuq debug== ViewModel已设置map_configuration: {type(map_configuration)}")
    
    def set_status_message(self, message: str):
        """
        设置状态消息
        
        Args:
            message: 状态消息
        """
        logger.info(f"==liuq debug== 状态消息: {message}")
        self.status_message_changed.emit(message)
        
        # 触发事件
        self.event_bus.emit(EventType.STATUS_MESSAGE_CHANGED, {
            'message': message,
            'timestamp': self.get_current_timestamp()
        })
    
    def select_map_point(self, point_index: int):
        """
        选择Map点
        
        Args:
            point_index: Map点索引
        """
        try:
            if 0 <= point_index < len(self._map_points):
                selected_point = self._map_points[point_index]
                
                # 触发事件
                self.event_bus.emit(EventType.MAP_POINT_SELECTED, {
                    'point_index': point_index,
                    'point_data': selected_point.__dict__ if hasattr(selected_point, '__dict__') else str(selected_point)
                })
                
                self.set_status_message(f"选择了Map点 #{point_index + 1}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 选择Map点失败: {e}")
    
    def select_base_boundary(self):
        """选择基础边界"""
        try:
            if self._base_boundary:
                # 触发事件
                self.event_bus.emit(EventType.BASE_BOUNDARY_SELECTED, {
                    'boundary_data': self._base_boundary.__dict__ if hasattr(self._base_boundary, '__dict__') else str(self._base_boundary)
                })
                
                self.set_status_message("选择了基础边界")
            
        except Exception as e:
            logger.error(f"==liuq debug== 选择基础边界失败: {e}")
    
    def get_xml_file_display_name(self) -> str:
        """
        获取XML文件显示名称
        
        Returns:
            str: 文件显示名称
        """
        if self._current_xml_file:
            return self._current_xml_file.name
        return "未选择文件"
    
    def is_analysis_available(self) -> bool:
        """
        检查是否可以进行分析
        
        Returns:
            bool: 是否可以分析
        """
        return (self._current_xml_file is not None and 
                len(self._map_points) > 0)
    
    def is_report_generation_available(self) -> bool:
        """
        检查是否可以生成报告
        
        Returns:
            bool: 是否可以生成报告
        """
        return self._analysis_result is not None
    
    def _perform_analysis(self):
        """执行Map分析"""
        try:
            if not self._map_analyzer or not self._map_points:
                return
            
            self.set_status_message("正在分析Map数据...")
            
            # 执行分析（新架构：MapAnalyzer.analyze() 不再接收 map_points 参数）
            analysis_result = self._map_analyzer.analyze()

            if analysis_result:
                self._analysis_result = analysis_result
                
                # 发送分析完成信号
                self.map_analysis_completed.emit(analysis_result)
                self.generate_report_enabled.emit(True)
                
                # 触发事件
                self.event_bus.emit(EventType.MAP_ANALYSIS_COMPLETED, {
                    'analysis_result': analysis_result,
                    'map_points_count': len(self._map_points)
                })
                
                self.set_status_message("Map数据分析完成")
            else:
                self.set_status_message("Map数据分析失败")
            
        except Exception as e:
            logger.error(f"==liuq debug== Map分析失败: {e}")
            self.set_status_message(f"Map分析失败: {e}")
    
    def _setup_event_listeners(self):
        """设置事件监听"""
        # 监听Tab切换事件
        self.event_bus.subscribe(EventType.TAB_CHANGED, self._on_tab_changed)
        
        # 监听报告生成请求
        self.event_bus.subscribe(EventType.REPORT_GENERATION_REQUESTED, self._on_report_generation_requested)
    
    def _on_tab_changed(self, event):
        """处理Tab切换事件"""
        try:
            tab_index = event.data.get('tab_index', -1)
            tab_name = event.data.get('tab_name', '未知')
            self.set_status_message(f"切换到 {tab_name} 标签页")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab切换事件失败: {e}")
    
    def _on_report_generation_requested(self, event):
        """处理报告生成请求事件"""
        try:
            # 这里可以添加额外的报告生成逻辑
            logger.info("==liuq debug== 收到报告生成请求事件")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理报告生成请求事件失败: {e}")
    
    def get_current_timestamp(self) -> str:
        """
        获取当前时间戳字符串
        
        Returns:
            str: 格式化的时间戳字符串
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 全局主窗口ViewModel实例
_main_window_viewmodel: Optional[MainWindowViewModel] = None


def get_main_window_viewmodel() -> MainWindowViewModel:
    """获取主窗口ViewModel实例"""
    global _main_window_viewmodel
    
    if _main_window_viewmodel is None:
        _main_window_viewmodel = MainWindowViewModel()
        logger.info("==liuq debug== 创建主窗口ViewModel实例")
    
    return _main_window_viewmodel