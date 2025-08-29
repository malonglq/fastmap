#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map分析Tab ViewModel
==liuq debug== FastMapV2 Map分析Tab ViewModel

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: Map分析Tab的MVVM架构ViewModel，管理Map分析相关的业务逻辑和数据状态
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from PyQt5.QtCore import pyqtSignal

from core.infrastructure.base_view_model import BaseViewModel
from core.infrastructure.event_bus import EventType
from core.models.map_data import MapPoint, BaseBoundary
from core.services.map_analysis.xml_parser_service import XMLParserService
from core.services.map_analysis.map_analyzer import MapAnalyzer
from core.services.map_analysis.xml_validation_service import XMLValidationService
from core.services.map_analysis.xml_metadata_service import XMLMetadataService

logger = logging.getLogger(__name__)


class MapAnalysisTabViewModel(BaseViewModel):
    """
    Map分析Tab ViewModel
    
    管理Map分析Tab的状态和业务逻辑：
    - XML文件解析和验证
    - Map点数据管理
    - 分析结果生成
    - 表格和可视化数据
    """
    
    # 自定义信号
    map_points_loaded = pyqtSignal(list)  # Map点数据加载完成
    base_boundary_loaded = pyqtSignal(object)  # 基础边界加载完成
    analysis_progress_updated = pyqtSignal(int, str)  # 分析进度更新
    visualization_data_ready = pyqtSignal(dict)  # 可视化数据准备完成
    table_data_ready = pyqtSignal(list, dict)  # 表格数据准备完成
    validation_completed = pyqtSignal(dict)  # 验证完成
    
    def __init__(self):
        """初始化Map分析Tab ViewModel"""
        super().__init__()
        
        # 数据状态
        self._current_xml_file: Optional[Path] = None
        self._map_points: List[MapPoint] = []
        self._base_boundary: Optional[BaseBoundary] = None
        self._analysis_result: Optional[Dict[str, Any]] = None
        self._validation_result: Optional[Dict[str, Any]] = None
        self._metadata: Optional[Dict[str, Any]] = None
        
        # 获取服务
        self._xml_parser = self._di_container.resolve(XMLParserService)
        self._xml_validator = self._di_container.resolve(XMLValidationService)
        self._xml_metadata = self._di_container.resolve(XMLMetadataService)
        
        # 设置事件监听
        self._setup_event_listeners()
        
        logger.info("==liuq debug== Map分析Tab ViewModel初始化完成")
    
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
    def validation_result(self) -> Optional[Dict[str, Any]]:
        """验证结果"""
        return self._validation_result
    
    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """XML元数据"""
        return self._metadata
    
    def load_xml_data(self, xml_file_path: str) -> bool:
        """
        加载XML数据
        
        Args:
            xml_file_path: XML文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            self.set_status_message("正在加载XML数据...")
            self.analysis_progress_updated.emit(10, "开始解析XML文件")
            
            xml_path = Path(xml_file_path)
            if not xml_path.exists():
                self.set_status_message(f"XML文件不存在: {xml_file_path}")
                return False
            
            self._current_xml_file = xml_path
            
            # 1. 验证XML文件
            self.analysis_progress_updated.emit(20, "验证XML文件格式")
            validation_result = self._xml_validator.validate_xml_file(xml_path)
            self._validation_result = validation_result
            self.validation_completed.emit(validation_result)
            
            if not validation_result.get('is_valid', False):
                self.set_status_message("XML文件验证失败")
                return False
            
            # 2. 提取元数据
            self.analysis_progress_updated.emit(40, "提取XML元数据")
            metadata = self._xml_metadata.extract_complete_metadata(xml_path)
            self._metadata = metadata
            
            # 3. 解析XML数据（新架构：直接返回 MapConfiguration）
            self.analysis_progress_updated.emit(60, "解析Map数据")
            config = self._xml_parser.parse_xml(xml_path)

            if not config:
                self.set_status_message("XML解析失败: 无法解析配置")
                return False

            # 4. 更新数据状态
            self._map_points = getattr(config, 'map_points', [])
            self._base_boundary = getattr(config, 'base_boundary', None)

            # 5. 发送信号通知UI更新
            self.analysis_progress_updated.emit(80, "准备数据展示")
            self.map_points_loaded.emit(self._map_points)

            if self._base_boundary:
                self.base_boundary_loaded.emit(self._base_boundary)
            
            # 6. 准备表格数据
            table_data = self._prepare_table_data()
            self.table_data_ready.emit(self._map_points, table_data)
            
            # 7. 准备可视化数据
            visualization_data = self._prepare_visualization_data()
            self.visualization_data_ready.emit(visualization_data)
            
            self.analysis_progress_updated.emit(100, "数据加载完成")
            self.set_status_message(f"XML数据加载完成: {len(self._map_points)} 个Map点")
            
            # 触发事件
            self._event_bus.emit(EventType.MAP_DATA_LOADED, {
                'file_path': str(xml_path),
                'map_points_count': len(self._map_points),
                'has_base_boundary': self._base_boundary is not None,
                'validation_result': validation_result,
                'metadata': metadata
            })
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 加载XML数据失败: {e}")
            self.set_status_message(f"加载XML数据失败: {e}")
            return False
    
    def analyze_map_data(self) -> bool:
        """
        分析Map数据
        
        Returns:
            bool: 分析是否成功
        """
        try:
            if not self._map_points:
                self.set_status_message("没有可分析的Map数据")
                return False
            
            self.set_status_message("正在分析Map数据...")
            self.analysis_progress_updated.emit(0, "开始Map分析")
            
            # 创建分析器
            from core.models.map_data import MapConfiguration, BaseBoundary
            # 新架构：MapAnalyzer 需要完整的 MapConfiguration；不再提供 analyze_maps(map_points)
            # 使用当前解析得到的 map_points 与 base_boundary 构造配置
            safe_boundary = self._base_boundary if self._base_boundary else BaseBoundary(rpg=0.0, bpg=0.0)
            map_config = MapConfiguration(device_type="analysis", base_boundary=safe_boundary, map_points=self._map_points)
            analyzer = MapAnalyzer(map_config)

            # 执行分析
            self.analysis_progress_updated.emit(50, "执行Map数据分析")
            analysis_result = analyzer.analyze()

            if analysis_result:
                self._analysis_result = analysis_result
                self.analysis_progress_updated.emit(100, "Map分析完成")
                self.set_status_message("Map数据分析完成")
                
                # 触发事件
                self._event_bus.emit(EventType.MAP_ANALYSIS_COMPLETED, {
                    'analysis_result': analysis_result,
                    'map_points_count': len(self._map_points),
                    'file_path': str(self._current_xml_file) if self._current_xml_file else None
                })
                
                return True
            else:
                self.set_status_message("Map数据分析失败")
                return False
            
        except Exception as e:
            logger.error(f"==liuq debug== 分析Map数据失败: {e}")
            self.set_status_message(f"分析Map数据失败: {e}")
            return False
    
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
                self._event_bus.emit(EventType.MAP_POINT_SELECTED, {
                    'point_index': point_index,
                    'point_data': selected_point.__dict__ if hasattr(selected_point, '__dict__') else str(selected_point),
                    'tab_source': 'map_analysis'
                })
                
                self.set_status_message(f"选择了Map点 #{point_index + 1}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 选择Map点失败: {e}")
    
    def select_base_boundary(self):
        """选择基础边界"""
        try:
            if self._base_boundary:
                # 触发事件
                self._event_bus.emit(EventType.BASE_BOUNDARY_SELECTED, {
                    'boundary_data': self._base_boundary.__dict__ if hasattr(self._base_boundary, '__dict__') else str(self._base_boundary),
                    'tab_source': 'map_analysis'
                })
                
                self.set_status_message("选择了基础边界")
            
        except Exception as e:
            logger.error(f"==liuq debug== 选择基础边界失败: {e}")
    
    def get_map_statistics(self) -> Dict[str, Any]:
        """
        获取Map统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = {
                'total_map_points': len(self._map_points),
                'has_base_boundary': self._base_boundary is not None,
                'current_file': str(self._current_xml_file) if self._current_xml_file else None,
                'analysis_completed': self._analysis_result is not None,
                'validation_passed': self._validation_result.get('is_valid', False) if self._validation_result else False
            }
            
            if self._metadata:
                stats['file_size'] = self._metadata.get('file_info', {}).get('file_size', 0)
                stats['quality_score'] = self._metadata.get('quality_score', 0)
            
            return stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取Map统计信息失败: {e}")
            return {}
    
    def export_analysis_data(self, export_path: str, export_format: str = 'json') -> bool:
        """
        导出分析数据
        
        Args:
            export_path: 导出路径
            export_format: 导出格式 ('json', 'csv', 'xlsx')
            
        Returns:
            bool: 导出是否成功
        """
        try:
            if not self._analysis_result:
                self.set_status_message("没有可导出的分析数据")
                return False
            
            self.set_status_message("正在导出分析数据...")
            
            export_data = {
                'metadata': self._metadata,
                'validation_result': self._validation_result,
                'analysis_result': self._analysis_result,
                'map_points_count': len(self._map_points),
                'export_timestamp': self.get_current_timestamp()
            }
            
            # 这里可以根据format使用不同的导出服务
            # 暂时使用简单的JSON导出
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.set_status_message(f"分析数据导出完成: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 导出分析数据失败: {e}")
            self.set_status_message(f"导出分析数据失败: {e}")
            return False
    
    def _prepare_table_data(self) -> Dict[str, Any]:
        """准备表格数据"""
        try:
            table_data = {
                'columns': ['索引', 'X坐标', 'Y坐标', 'BV值', 'IR值', 'CCT值'],
                'rows': []
            }
            
            for i, point in enumerate(self._map_points):
                row = [
                    i + 1,
                    getattr(point, 'x', 0),
                    getattr(point, 'y', 0),
                    getattr(point, 'bv', 0),
                    getattr(point, 'ir', 0),
                    getattr(point, 'cct', 0)
                ]
                table_data['rows'].append(row)
            
            return table_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 准备表格数据失败: {e}")
            return {'columns': [], 'rows': []}
    
    def _prepare_visualization_data(self) -> Dict[str, Any]:
        """准备可视化数据"""
        try:
            viz_data = {
                'map_points': [],
                'base_boundary': None,
                'statistics': {}
            }
            
            # 准备Map点数据
            for point in self._map_points:
                point_data = {
                    'x': getattr(point, 'x', 0),
                    'y': getattr(point, 'y', 0),
                    'bv': getattr(point, 'bv', 0),
                    'ir': getattr(point, 'ir', 0)
                }
                viz_data['map_points'].append(point_data)
            
            # 准备基础边界数据
            if self._base_boundary:
                viz_data['base_boundary'] = {
                    'rpg': getattr(self._base_boundary, 'rpg', 0),
                    'bpg': getattr(self._base_boundary, 'bpg', 0)
                }
            
            # 准备统计数据
            if self._map_points:
                bv_values = [getattr(p, 'bv', 0) for p in self._map_points]
                ir_values = [getattr(p, 'ir', 0) for p in self._map_points]
                
                viz_data['statistics'] = {
                    'bv_range': [min(bv_values), max(bv_values)] if bv_values else [0, 0],
                    'ir_range': [min(ir_values), max(ir_values)] if ir_values else [0, 0],
                    'point_count': len(self._map_points)
                }
            
            return viz_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 准备可视化数据失败: {e}")
            return {}
    
    def _setup_event_listeners(self):
        """设置事件监听"""
        # 监听XML文件加载事件
        self._event_bus.subscribe(EventType.XML_FILE_LOADED, self._on_xml_file_loaded)
        
        # 监听Tab激活事件
        self._event_bus.subscribe(EventType.TAB_CHANGED, self._on_tab_changed)
    
    def _on_xml_file_loaded(self, event):
        """处理XML文件加载事件"""
        try:
            if event.source != 'map_analysis_tab':
                # 如果不是本Tab加载的，同步数据
                file_path = event.data.get('file_path', '')
                if file_path and file_path != str(self._current_xml_file):
                    self.load_xml_data(file_path)
                    
        except Exception as e:
            logger.error(f"==liuq debug== 处理XML文件加载事件失败: {e}")
    
    def _on_tab_changed(self, event):
        """处理Tab切换事件"""
        try:
            tab_name = event.data.get('tab_name', '')
            if tab_name == 'Map分析':
                # 当切换到Map分析Tab时，可以执行一些刷新操作
                logger.info("==liuq debug== 切换到Map分析Tab")
                
        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab切换事件失败: {e}")


# 全局Map分析Tab ViewModel实例
_map_analysis_tab_viewmodel: Optional[MapAnalysisTabViewModel] = None


def get_map_analysis_tab_viewmodel() -> MapAnalysisTabViewModel:
    """获取Map分析Tab ViewModel实例"""
    global _map_analysis_tab_viewmodel
    
    if _map_analysis_tab_viewmodel is None:
        _map_analysis_tab_viewmodel = MapAnalysisTabViewModel()
        logger.info("==liuq debug== 创建Map分析Tab ViewModel实例")
    
    return _map_analysis_tab_viewmodel