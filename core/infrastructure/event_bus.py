#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件总线系统
==liuq debug== FastMapV2事件总线系统

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: ViewModel间解耦通信的事件总线，支持事件发布/订阅模式
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import threading
import weakref

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""
    
    # XML文件相关事件
    XML_FILE_LOADED = "xml_file_loaded"
    XML_FILE_SAVED = "xml_file_saved"
    XML_FILE_VALIDATED = "xml_file_validated"
    
    # Map分析相关事件
    MAP_DATA_LOADED = "map_data_loaded"
    MAP_ANALYSIS_STARTED = "map_analysis_started"
    MAP_ANALYSIS_COMPLETED = "map_analysis_completed"
    MAP_POINT_SELECTED = "map_point_selected"
    BASE_BOUNDARY_SELECTED = "base_boundary_selected"
    
    # EXIF处理相关事件
    EXIF_SOURCE_DIRECTORY_SET = "exif_source_directory_set"
    EXIF_FIELDS_DISCOVERED = "exif_fields_discovered"
    EXIF_PROCESSING_STARTED = "exif_processing_started"
    EXIF_PROCESSING_PROGRESS = "exif_processing_progress"
    EXIF_PROCESSING_COMPLETED = "exif_processing_completed"
    EXIF_EXPORT_COMPLETED = "exif_export_completed"
    
    # 报告生成相关事件
    REPORT_TYPE_SELECTED = "report_type_selected"
    REPORT_GENERATION_REQUESTED = "report_generation_requested"
    REPORT_GENERATION_STARTED = "report_generation_started"
    REPORT_GENERATION_PROGRESS = "report_generation_progress"
    REPORT_GENERATION_COMPLETED = "report_generation_completed"
    REPORT_GENERATION_CANCELLED = "report_generation_cancelled"
    REPORT_OPENED = "report_opened"
    
    # Tab通信相关事件
    TAB_CHANGED = "tab_changed"
    TAB_SYNC_REQUESTED = "tab_sync_requested"
    SHARED_DATA_UPDATED = "shared_data_updated"
    
    # 应用程序级事件
    APPLICATION_STARTUP = "application_startup"
    APPLICATION_SHUTDOWN = "application_shutdown"
    STATUS_MESSAGE_CHANGED = "status_message_changed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    """事件数据类"""
    event_type: EventType
    data: Any = None
    source: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventHandler:
    """事件处理器包装类，支持弱引用"""
    
    def __init__(self, handler: Callable[[Event], None], source_name: str = None):
        # 使用弱引用避免循环引用
        if hasattr(handler, '__self__'):
            # 方法：使用弱引用到对象
            self._obj_ref = weakref.ref(handler.__self__)
            self._method_name = handler.__func__.__name__
            self._is_method = True
        else:
            # 函数：直接保存
            self._handler = handler
            self._is_method = False
        
        self.source_name = source_name or "Unknown"
    
    def __call__(self, event: Event) -> bool:
        """
        调用事件处理器
        
        Returns:
            bool: True表示成功调用，False表示处理器已失效
        """
        try:
            if self._is_method:
                obj = self._obj_ref()
                if obj is None:
                    # 对象已被垃圾回收
                    return False
                
                method = getattr(obj, self._method_name, None)
                if method is None:
                    return False
                
                method(event)
            else:
                self._handler(event)
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 事件处理器执行失败: {self.source_name}, 错误: {e}")
            return True  # 继续保留处理器


class EventBus:
    """
    事件总线
    
    功能：
    - 事件发布/订阅
    - 弱引用管理，自动清理失效处理器
    - 线程安全
    - 事件历史记录
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._max_history = 100  # 最大历史记录数
        self._lock = threading.RLock()
        
        logger.info("==liuq debug== 事件总线初始化完成")
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None], 
                 source_name: str = None) -> 'EventBus':
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            source_name: 订阅者名称（用于调试）
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            event_handler = EventHandler(handler, source_name)
            self._handlers[event_type].append(event_handler)
            
            logger.debug(f"==liuq debug== 订阅事件: {event_type.value} <- {source_name}")
            return self
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> 'EventBus':
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 要取消的事件处理器
        """
        with self._lock:
            if event_type not in self._handlers:
                return self
            
            # 查找并移除匹配的处理器
            handlers = self._handlers[event_type]
            for i, event_handler in enumerate(handlers):
                if event_handler._is_method:
                    obj = event_handler._obj_ref()
                    if obj is not None and hasattr(handler, '__self__'):
                        if (obj is handler.__self__ and 
                            event_handler._method_name == handler.__func__.__name__):
                            handlers.pop(i)
                            logger.debug(f"==liuq debug== 取消订阅: {event_type.value}")
                            break
                else:
                    if event_handler._handler is handler:
                        handlers.pop(i)
                        logger.debug(f"==liuq debug== 取消订阅: {event_type.value}")
                        break
            
            return self
    
    def emit(self, event_type: EventType, data: Any = None, source: str = None):
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
        """
        event = Event(event_type, data, source)
        
        with self._lock:
            # 记录事件历史
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            # 获取事件处理器
            handlers = self._handlers.get(event_type, [])
            if not handlers:
                logger.debug(f"==liuq debug== 无订阅者的事件: {event_type.value}")
                return
            
            # 执行事件处理器
            valid_handlers = []
            for handler in handlers:
                if handler(event):
                    valid_handlers.append(handler)
                else:
                    logger.debug(f"==liuq debug== 移除失效的事件处理器: {handler.source_name}")
            
            # 更新有效的处理器列表
            self._handlers[event_type] = valid_handlers
            
            logger.debug(f"==liuq debug== 发布事件: {event_type.value} -> {len(valid_handlers)} 个处理器")
    
    def get_subscribers_count(self, event_type: EventType) -> int:
        """获取指定事件类型的订阅者数量"""
        with self._lock:
            return len(self._handlers.get(event_type, []))
    
    def get_event_history(self, event_type: EventType = None, limit: int = 10) -> List[Event]:
        """
        获取事件历史记录
        
        Args:
            event_type: 事件类型过滤，None表示所有事件
            limit: 返回记录数限制
        """
        with self._lock:
            history = self._event_history
            
            if event_type is not None:
                history = [e for e in history if e.event_type == event_type]
            
            return history[-limit:] if limit > 0 else history
    
    def clear_history(self):
        """清空事件历史记录"""
        with self._lock:
            self._event_history.clear()
            logger.debug("==liuq debug== 事件历史记录已清空")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取事件总线统计信息"""
        with self._lock:
            stats = {
                "total_event_types": len(self._handlers),
                "total_subscribers": sum(len(handlers) for handlers in self._handlers.values()),
                "event_history_count": len(self._event_history),
                "subscribers_by_event": {
                    event_type.value: len(handlers) 
                    for event_type, handlers in self._handlers.items()
                }
            }
            return stats


# 全局事件总线实例
_global_event_bus: Optional[EventBus] = None
_event_bus_lock = threading.Lock()


def get_event_bus() -> EventBus:
    """获取全局事件总线实例（单例模式）"""
    global _global_event_bus
    
    if _global_event_bus is None:
        with _event_bus_lock:
            if _global_event_bus is None:
                _global_event_bus = EventBus()
                logger.info("==liuq debug== 创建全局事件总线")
    
    return _global_event_bus


# 便捷的全局函数
def subscribe(event_type: EventType, handler: Callable[[Event], None], source_name: str = None):
    """订阅事件（全局便捷函数）"""
    return get_event_bus().subscribe(event_type, handler, source_name)


def unsubscribe(event_type: EventType, handler: Callable[[Event], None]):
    """取消订阅事件（全局便捷函数）"""
    return get_event_bus().unsubscribe(event_type, handler)


def emit(event_type: EventType, data: Any = None, source: str = None):
    """发布事件（全局便捷函数）"""
    return get_event_bus().emit(event_type, data, source)