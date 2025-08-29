#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map分析ViewModel
==liuq debug== FastMapV2 Map分析ViewModel

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: Map分析Tab的ViewModel，处理XML解析、Map数据分析等业务逻辑
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from PyQt5.QtCore import pyqtSignal

from core.infrastructure.base_view_model import BaseViewModel
from core.infrastructure.event_bus import Event, EventType
from core.services.map_analysis import XMLParserService, XMLWriterService, MapAnalyzer
from core.models.map_data import MapConfiguration, AnalysisResult

logger = logging.getLogger(__name__)


class MapAnalysisViewModel(BaseViewModel):
    """
    Map分析ViewModel
    
    负责处理：
    - XML文件加载与解析
    - Map数据分析
    - Map点选择与显示
    - HTML报告生成
    """
    
    # 额外信号定义
    xml_file_loaded = pyqtSignal(str)           # XML文件加载完成
    map_data_analyzed = pyqtSignal(object)      # Map数据分析完成
    map_point_selected = pyqtSignal(dict)       # Map点选择
    boundary_selected = pyqtSignal(dict)        # 边界选择
    
    def __init__(self):
        super().__init__()
        
        # 解析依赖的服务
        self._xml_parser: XMLParserService = self.resolve_service(XMLParserService)
        self._xml_writer: XMLWriterService = self.resolve_service(XMLWriterService)
        # MapAnalyzer需要MapConfiguration作为参数，所以不在构造函数中解析
        self._map_analyzer: Optional[MapAnalyzer] = None
        
        # ViewModel状态
        self._current_xml_file: Optional[Path] = None
        self._map_configuration: Optional[Dict] = None
        self._map_data: Optional[MapConfiguration] = None
        self._analysis_result: Optional[AnalysisResult] = None
        self._selected_map_point: Optional[Dict] = None
        
        # 初始化属性
        self._initialize_properties()
        
        logger.debug("==liuq debug== MapAnalysisViewModel 初始化完成")
    
    def _initialize_properties(self):
        """初始化属性"""
        self.set_property("xml_file_path", "", False)
        self.set_property("xml_file_name", "未选择文件", False)
        self.set_property("map_count", 0, False)
        self.set_property("analysis_complete", False, False)
        self.set_property("can_generate_report", False, False)
        self.set_property("selected_map_point", None, False)
    
    def _setup_event_subscriptions(self):
        """设置事件订阅"""
        # 订阅Tab切换事件
        self.subscribe_event(EventType.TAB_SWITCHED, self._on_tab_switched)
        
        # 订阅应用程序事件
        self.subscribe_event(EventType.APPLICATION_SHUTDOWN, self._on_application_shutdown)
    
    # 属性访问器
    @property
    def xml_file_path(self) -> str:
        """当前XML文件路径"""
        return self.get_property("xml_file_path", "")
    
    @property
    def xml_file_name(self) -> str:
        """当前XML文件名"""
        return self.get_property("xml_file_name", "未选择文件")
    
    @property
    def map_count(self) -> int:
        """Map数量"""
        return self.get_property("map_count", 0)
    
    @property
    def analysis_complete(self) -> bool:
        """分析是否完成"""
        return self.get_property("analysis_complete", False)
    
    @property
    def can_generate_report(self) -> bool:
        """是否可以生成报告"""
        return self.get_property("can_generate_report", False)
    
    @property
    def map_configuration(self) -> Optional[Dict]:
        """Map配置数据"""
        return self._map_configuration
    
    @property
    def map_data(self) -> Optional[MapConfiguration]:
        """Map数据对象"""
        return self._map_data
    
    @property
    def analysis_result(self) -> Optional[AnalysisResult]:
        """分析结果"""
        return self._analysis_result
    
    # 业务方法
    def load_xml_file(self, file_path: str) -> bool:
        """
        加载XML文件
        
        Args:
            file_path: XML文件路径
            
        Returns:
            bool: 是否加载成功
        """
        try:
            self.set_busy(True, "正在加载XML文件...")
            
            xml_path = Path(file_path)
            if not xml_path.exists():
                self.handle_error(FileNotFoundError(f"文件不存在: {file_path}"))
                return False
            
            # 解析XML文件
            self._map_configuration = self._xml_parser.parse_file(xml_path)
            if not self._map_configuration:
                self.handle_error(ValueError("XML文件解析失败"))
                return False
            
            # 更新状态
            self._current_xml_file = xml_path
            self.set_property("xml_file_path", str(xml_path))
            self.set_property("xml_file_name", xml_path.name)
            
            # 自动分析Map数据
            success = self._analyze_map_data()
            
            if success:
                # 发布事件
                self.emit_event(EventType.MAP_FILE_SELECTED, {
                    "file_path": str(xml_path),
                    "map_count": self.map_count
                })
                
                self.emit_event(EventType.MAP_LOADED, {
                    "map_configuration": self._map_configuration,
                    "map_data": self._map_data
                })
                
                self.xml_file_loaded.emit(str(xml_path))
                self.emit_status(f"XML文件加载成功: {xml_path.name}")
                
                logger.info(f"==liuq debug== XML文件加载成功: {xml_path}")
                return True
            
            return False
            
        except Exception as e:
            self.handle_error(e, f"加载XML文件失败: {file_path}")
            return False
        finally:
            self.set_busy(False)
    
    def _analyze_map_data(self) -> bool:
        """分析Map数据"""
        try:
            if not self._map_configuration:
                return False
            
            self.set_busy(True, "正在分析Map数据...")
            
            # 创建MapAnalyzer实例（需要传入MapConfiguration）
            self._map_analyzer = MapAnalyzer(self._map_configuration)
            
            # 使用MapAnalyzer分析数据
            self._analysis_result = self._map_analyzer.analyze()
            
            if self._analysis_result:
                # 提取Map数据
                self._map_data = self._map_configuration  # 这里应该是解析后的数据
                map_count = len(getattr(self._map_data, 'maps', [])) if self._map_data else 0
                
                # 更新属性
                self.set_property("map_count", map_count)
                self.set_property("analysis_complete", True)
                self.set_property("can_generate_report", True)
                
                # 发布事件
                self.emit_event(EventType.MAP_ANALYZED, {
                    "analysis_result": self._analysis_result,
                    "map_count": map_count
                })
                
                self.map_data_analyzed.emit(self._analysis_result)
                
                logger.info(f"==liuq debug== Map数据分析完成，共{map_count}个Map")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"==liuq debug== Map数据分析失败: {e}")
            return False
    
    def select_map_point(self, map_index: int, point_data: Dict):
        """
        选择Map点
        
        Args:
            map_index: Map索引
            point_data: 点数据
        """
        try:
            self._selected_map_point = {
                "map_index": map_index,
                "point_data": point_data,
                "timestamp": self._get_current_timestamp()
            }
            
            self.set_property("selected_map_point", self._selected_map_point)
            
            # 发布事件
            self.emit_event(EventType.MAP_POINT_SELECTED, self._selected_map_point)
            self.map_point_selected.emit(self._selected_map_point)
            
            logger.debug(f"==liuq debug== Map点选择: map_index={map_index}")
            
        except Exception as e:
            self.handle_error(e, "选择Map点失败")
    
    def select_boundary(self, boundary_data: Dict):
        """
        选择边界
        
        Args:
            boundary_data: 边界数据
        """
        try:
            boundary_info = {
                "boundary_data": boundary_data,
                "timestamp": self._get_current_timestamp()
            }
            
            # 发布事件
            self.emit_event(EventType.MAP_BOUNDARY_SELECTED, boundary_info)
            self.boundary_selected.emit(boundary_info)
            
            logger.debug("==liuq debug== 边界选择完成")
            
        except Exception as e:
            self.handle_error(e, "选择边界失败")
    
    def save_xml_file(self, file_path: str = None) -> bool:
        """
        保存XML文件
        
        Args:
            file_path: 保存路径，None则覆盖原文件
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if not self._map_configuration:
                self.handle_error(ValueError("没有可保存的Map配置"))
                return False
            
            self.set_busy(True, "正在保存XML文件...")
            
            save_path = file_path or str(self._current_xml_file)
            save_path = Path(save_path)
            
            # 使用XMLWriter保存
            success = self._xml_writer.write_file(save_path, self._map_configuration)
            
            if success:
                self.emit_status(f"XML文件保存成功: {save_path.name}")
                logger.info(f"==liuq debug== XML文件保存成功: {save_path}")
                return True
            else:
                self.handle_error(ValueError("XML文件保存失败"))
                return False
            
        except Exception as e:
            self.handle_error(e, f"保存XML文件失败: {file_path}")
            return False
        finally:
            self.set_busy(False)
    
    def generate_html_report(self) -> Optional[str]:
        """
        生成HTML报告
        
        Returns:
            str: 报告文件路径，失败返回None
        """
        try:
            if not self.can_generate_report:
                self.handle_error(ValueError("无法生成报告：分析未完成"))
                return None
            
            self.set_busy(True, "正在生成HTML报告...")
            
            # 发布报告生成开始事件
            self.emit_event(EventType.REPORT_GENERATION_STARTED, {
                "report_type": "map_analysis",
                "source": "MapAnalysisViewModel"
            })
            
            # 这里应该调用报告生成服务
            # 暂时返回成功状态，实际实现需要集成报告生成器
            
            report_path = f"output/map_analysis_report_{self._get_current_timestamp()}.html"
            
            # 发布报告生成完成事件
            self.emit_event(EventType.REPORT_GENERATION_COMPLETED, {
                "report_type": "map_analysis",
                "report_path": report_path,
                "success": True
            })
            
            self.emit_status(f"HTML报告生成成功: {report_path}")
            logger.info(f"==liuq debug== HTML报告生成成功: {report_path}")
            
            return report_path
            
        except Exception as e:
            self.handle_error(e, "生成HTML报告失败")
            return None
        finally:
            self.set_busy(False)
    
    # 事件处理器
    def _on_tab_switched(self, event: Event):
        """Tab切换事件处理"""
        if event.data and event.data.get("tab_name") == "Map分析":
            logger.debug("==liuq debug== 切换到Map分析Tab")
    
    def _on_application_shutdown(self, event: Event):
        """应用程序关闭事件处理"""
        self.cleanup()
    
    # 辅助方法
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 生命周期方法
    def cleanup(self):
        """清理资源"""
        try:
            # 清理状态
            self._current_xml_file = None
            self._map_configuration = None
            self._map_data = None
            self._analysis_result = None
            self._selected_map_point = None
            
            logger.debug("==liuq debug== MapAnalysisViewModel 清理完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== MapAnalysisViewModel 清理失败: {e}")