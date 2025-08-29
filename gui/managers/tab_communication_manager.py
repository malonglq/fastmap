#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tab间通信管理器
==liuq debug== FastMapV2 Tab间通信管理器

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: 使用事件总线实现Tab间的通信和数据共享
"""

import logging
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal

from core.infrastructure.event_bus import EventBus, EventType, get_event_bus

logger = logging.getLogger(__name__)


class TabCommunicationManager(QObject):
    """
    Tab间通信管理器
    
    使用事件总线实现Tab间的数据共享和状态同步：
    - XML文件加载状态同步
    - Map分析结果共享
    - EXIF处理结果共享
    - 报告生成状态同步
    """
    
    # 定义PyQt信号用于GUI更新
    xml_file_loaded = pyqtSignal(str, dict)  # 文件路径, 元数据
    map_analysis_completed = pyqtSignal(dict)  # 分析结果
    exif_processing_completed = pyqtSignal(str, dict)  # 处理路径, 结果
    report_generated = pyqtSignal(str, str)  # 报告类型, 文件路径
    status_updated = pyqtSignal(str)  # 状态消息
    
    def __init__(self):
        """初始化Tab间通信管理器"""
        super().__init__()
        
        # 获取事件总线
        self.event_bus = get_event_bus()
        
        # 注册Tab信息
        self.tabs = {
            'map_analysis': {'name': 'Map分析', 'active': False},
            'exif_processing': {'name': 'EXIF处理', 'active': False},
            'copywriting': {'name': '仿写功能', 'active': False},
            'feature_point': {'name': '特征点功能', 'active': False},
            'analysis_report': {'name': '分析报告', 'active': False}
        }
        
        # 共享数据存储
        self.shared_data = {
            'current_xml_file': None,
            'map_analysis_result': None,
            'exif_processing_result': None,
            'last_report_path': None
        }
        
        # 设置事件监听
        self._setup_event_listeners()
        
        logger.info("==liuq debug== Tab间通信管理器初始化完成")
    
    def _setup_event_listeners(self):
        """设置事件总线监听器"""
        # XML文件相关事件
        self.event_bus.subscribe(EventType.XML_FILE_LOADED, self._on_xml_file_loaded)
        self.event_bus.subscribe(EventType.XML_FILE_SAVED, self._on_xml_file_saved)
        
        # Map分析相关事件
        self.event_bus.subscribe(EventType.MAP_ANALYSIS_STARTED, self._on_map_analysis_started)
        self.event_bus.subscribe(EventType.MAP_ANALYSIS_COMPLETED, self._on_map_analysis_completed)
        self.event_bus.subscribe(EventType.MAP_POINT_SELECTED, self._on_map_point_selected)
        self.event_bus.subscribe(EventType.BASE_BOUNDARY_SELECTED, self._on_base_boundary_selected)
        
        # EXIF处理相关事件
        self.event_bus.subscribe(EventType.EXIF_PROCESSING_STARTED, self._on_exif_processing_started)
        self.event_bus.subscribe(EventType.EXIF_PROCESSING_COMPLETED, self._on_exif_processing_completed)
        
        # 报告生成相关事件
        self.event_bus.subscribe(EventType.REPORT_GENERATION_REQUESTED, self._on_report_generation_requested)
        self.event_bus.subscribe(EventType.REPORT_GENERATION_COMPLETED, self._on_report_generation_completed)
        
        # Tab切换事件
        self.event_bus.subscribe(EventType.TAB_CHANGED, self._on_tab_changed)
        
        # 状态消息事件
        self.event_bus.subscribe(EventType.STATUS_MESSAGE_CHANGED, self._on_status_message_changed)
    
    def _on_xml_file_loaded(self, event):
        """处理XML文件加载事件"""
        try:
            data = event.data
            file_path = data.get('file_path', '')
            
            # 更新共享数据
            self.shared_data['current_xml_file'] = file_path
            
            # 准备元数据
            metadata = {
                'map_points_count': data.get('map_points_count', 0),
                'has_base_boundary': data.get('has_base_boundary', False),
                'loaded_at': event.timestamp
            }
            
            # 发出PyQt信号供GUI更新
            self.xml_file_loaded.emit(file_path, metadata)
            
            # 通知所有Tab文件已加载
            self._broadcast_to_tabs('xml_file_loaded', {
                'file_path': file_path,
                'metadata': metadata
            })
            
            logger.info(f"==liuq debug== XML文件加载事件处理完成: {file_path}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理XML文件加载事件失败: {e}")
    
    def _on_xml_file_saved(self, event):
        """处理XML文件保存事件"""
        try:
            data = event.data
            file_path = data.get('file_path', '')
            
            # 通知所有Tab文件已保存
            self._broadcast_to_tabs('xml_file_saved', {
                'file_path': file_path,
                'saved_at': event.timestamp
            })
            
            logger.info(f"==liuq debug== XML文件保存事件处理完成: {file_path}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理XML文件保存事件失败: {e}")
    
    def _on_map_analysis_started(self, event):
        """处理Map分析开始事件"""
        try:
            # 通知所有Tab分析已开始
            self._broadcast_to_tabs('map_analysis_started', event.data)
            self.status_updated.emit("Map分析已开始...")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Map分析开始事件失败: {e}")
    
    def _on_map_analysis_completed(self, event):
        """处理Map分析完成事件"""
        try:
            data = event.data
            raw_result = data.get('analysis_result', {})

            # 将 AnalysisResult 对象转换为轻量字典，避免Qt信号类型不匹配
            try:
                from core.models.map_data import AnalysisResult
                if isinstance(raw_result, AnalysisResult):
                    analysis_result = raw_result.get_summary()
                else:
                    # 已是字典或其他可序列化对象
                    analysis_result = raw_result
            except Exception as _e:
                logger.warning(f"==liuq debug== 转换AnalysisResult为字典失败，使用空对象: {_e}")
                analysis_result = {}

            # 更新共享数据
            self.shared_data['map_analysis_result'] = analysis_result

            # 发出PyQt信号（签名是 dict）
            self.map_analysis_completed.emit(analysis_result)

            # 通知所有Tab分析完成（广播字典而非对象）
            self._broadcast_to_tabs('map_analysis_completed', {
                'analysis_result': analysis_result,
                'map_points_count': data.get('map_points_count', 0),
                'completed_at': event.timestamp
            })

            self.status_updated.emit("Map分析已完成")
            logger.info("==liuq debug== Map分析完成事件处理完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Map分析完成事件失败: {e}")
    
    def _on_map_point_selected(self, event):
        """处理Map点选择事件"""
        try:
            data = event.data
            point_index = data.get('point_index', -1)
            
            # 通知其他组件有Map点被选择
            self._broadcast_to_tabs('map_point_selected', {
                'point_index': point_index,
                'point_data': data.get('point_data', {}),
                'selected_at': event.timestamp
            })
            
            self.status_updated.emit(f"已选择Map点 #{point_index + 1}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Map点选择事件失败: {e}")
    
    def _on_base_boundary_selected(self, event):
        """处理基础边界选择事件"""
        try:
            # 通知其他组件基础边界被选择
            self._broadcast_to_tabs('base_boundary_selected', {
                'boundary_data': event.data.get('boundary_data', {}),
                'selected_at': event.timestamp
            })
            
            self.status_updated.emit("已选择基础边界")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理基础边界选择事件失败: {e}")
    
    def _on_exif_processing_started(self, event):
        """处理EXIF处理开始事件"""
        try:
            # 通知所有Tab EXIF处理已开始
            self._broadcast_to_tabs('exif_processing_started', event.data)
            self.status_updated.emit("EXIF处理已开始...")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理EXIF处理开始事件失败: {e}")
    
    def _on_exif_processing_completed(self, event):
        """处理EXIF处理完成事件"""
        try:
            data = event.data
            processing_path = data.get('processing_path', '')
            result = data.get('result', {})
            
            # 更新共享数据
            self.shared_data['exif_processing_result'] = result
            
            # 发出PyQt信号
            self.exif_processing_completed.emit(processing_path, result)
            
            # 通知所有Tab处理完成
            self._broadcast_to_tabs('exif_processing_completed', {
                'processing_path': processing_path,
                'result': result,
                'completed_at': event.timestamp
            })
            
            self.status_updated.emit("EXIF处理已完成")
            logger.info(f"==liuq debug== EXIF处理完成事件处理完成: {processing_path}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理EXIF处理完成事件失败: {e}")
    
    def _on_report_generation_requested(self, event):
        """处理报告生成请求事件"""
        try:
            # 通知报告Tab有生成请求
            self._broadcast_to_tabs('report_generation_requested', event.data)
            self.status_updated.emit("正在生成报告...")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理报告生成请求事件失败: {e}")
    
    def _on_report_generation_completed(self, event):
        """处理报告生成完成事件"""
        try:
            data = event.data
            report_type = data.get('report_type', 'unknown')
            file_path = data.get('file_path', '')
            
            # 更新共享数据
            self.shared_data['last_report_path'] = file_path
            
            # 发出PyQt信号
            self.report_generated.emit(report_type, file_path)
            
            # 通知所有Tab报告生成完成
            self._broadcast_to_tabs('report_generation_completed', {
                'report_type': report_type,
                'file_path': file_path,
                'completed_at': event.timestamp
            })
            
            self.status_updated.emit(f"{report_type}报告生成完成")
            logger.info(f"==liuq debug== 报告生成完成事件处理完成: {file_path}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理报告生成完成事件失败: {e}")
    
    def _on_tab_changed(self, event):
        """处理Tab切换事件"""
        try:
            data = event.data
            tab_index = data.get('tab_index', -1)
            tab_name = data.get('tab_name', 'unknown')
            
            # 更新Tab激活状态
            for tab_id, tab_info in self.tabs.items():
                tab_info['active'] = (tab_info['name'] == tab_name)
            
            # 为新激活的Tab提供当前状态信息
            current_state = self._get_current_state()
            self._send_to_active_tab('tab_activated', {
                'tab_index': tab_index,
                'tab_name': tab_name,
                'current_state': current_state
            })
            
            logger.info(f"==liuq debug== Tab切换事件处理完成: {tab_name}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab切换事件失败: {e}")
    
    def _on_status_message_changed(self, event):
        """处理状态消息变更事件"""
        try:
            data = event.data
            message = data.get('message', '')
            
            # 发出PyQt信号更新状态栏
            self.status_updated.emit(message)
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理状态消息变更事件失败: {e}")
    
    def _broadcast_to_tabs(self, event_name: str, data: Dict[str, Any]):
        """向所有Tab广播事件"""
        try:
            # 这里可以实现具体的Tab通信逻辑
            # 例如调用各个Tab的特定方法或发送自定义事件
            logger.debug(f"==liuq debug== 向所有Tab广播事件: {event_name}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 广播事件失败: {e}")
    
    def _send_to_active_tab(self, event_name: str, data: Dict[str, Any]):
        """向当前激活的Tab发送事件"""
        try:
            active_tab = self._get_active_tab()
            if active_tab:
                logger.debug(f"==liuq debug== 向激活Tab发送事件: {event_name} -> {active_tab}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 向激活Tab发送事件失败: {e}")
    
    def _get_active_tab(self) -> Optional[str]:
        """获取当前激活的Tab"""
        for tab_id, tab_info in self.tabs.items():
            if tab_info.get('active', False):
                return tab_id
        return None
    
    def _get_current_state(self) -> Dict[str, Any]:
        """获取当前应用状态"""
        return {
            'shared_data': self.shared_data.copy(),
            'active_tab': self._get_active_tab(),
            'tabs_info': self.tabs.copy()
        }
    
    def get_shared_data(self, key: str) -> Any:
        """获取共享数据"""
        return self.shared_data.get(key)
    
    def set_shared_data(self, key: str, value: Any):
        """设置共享数据"""
        self.shared_data[key] = value
        
        # 通知数据变更
        self.event_bus.emit(EventType.SHARED_DATA_UPDATED, {
            'key': key,
            'value': value,
            'updated_at': self.event_bus.get_current_timestamp()
        })
    
    def request_tab_sync(self, tab_name: str):
        """请求Tab数据同步"""
        try:
            current_state = self._get_current_state()
            
            # 发送同步事件
            self.event_bus.emit(EventType.TAB_SYNC_REQUESTED, {
                'tab_name': tab_name,
                'current_state': current_state,
                'requested_at': self.event_bus.get_current_timestamp()
            })
            
            logger.info(f"==liuq debug== 请求Tab同步: {tab_name}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 请求Tab同步失败: {e}")


# 全局Tab通信管理器实例
_tab_communication_manager: Optional[TabCommunicationManager] = None


def get_tab_communication_manager() -> TabCommunicationManager:
    """获取Tab间通信管理器实例"""
    global _tab_communication_manager
    
    if _tab_communication_manager is None:
        _tab_communication_manager = TabCommunicationManager()
        logger.info("==liuq debug== 创建Tab间通信管理器实例")
    
    return _tab_communication_manager