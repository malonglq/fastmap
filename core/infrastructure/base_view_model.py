#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ViewModel基类
==liuq debug== FastMapV2 ViewModel基类

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: MVVM模式的ViewModel基类，提供属性通知、命令支持、事件总线集成
"""

import logging
from typing import Any, Dict, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from core.infrastructure.event_bus import EventBus, Event, EventType, get_event_bus
from core.infrastructure.di_container import DIContainer, get_container

logger = logging.getLogger(__name__)


class BaseViewModel(QObject):
    """
    ViewModel基类
    
    提供功能：
    - 属性变更通知
    - 事件总线集成
    - 依赖注入支持
    - 错误处理
    - 状态管理
    """
    
    # 信号定义
    property_changed = pyqtSignal(str, object)  # 属性变更通知
    error_occurred = pyqtSignal(str)           # 错误事件
    status_message = pyqtSignal(str)           # 状态消息
    busy_state_changed = pyqtSignal(bool)      # 忙碌状态变更
    
    def __init__(self, event_bus: EventBus = None, di_container: DIContainer = None):
        """
        初始化ViewModel
        
        Args:
            event_bus: 事件总线实例，None则使用全局实例
            di_container: 依赖注入容器，None则使用全局实例
        """
        super().__init__()
        
        self._event_bus = event_bus or get_event_bus()
        self._di_container = di_container or get_container()
        self._properties: Dict[str, Any] = {}
        self._is_busy = False
        self._view_model_name = self.__class__.__name__
        
        # 设置事件订阅
        self._setup_event_subscriptions()
        
        logger.debug(f"==liuq debug== ViewModel初始化: {self._view_model_name}")
    
    def _setup_event_subscriptions(self):
        """设置事件订阅（子类重写此方法）"""
        pass
    
    # 属性管理
    def get_property(self, name: str, default: Any = None) -> Any:
        """获取属性值"""
        return self._properties.get(name, default)
    
    def set_property(self, name: str, value: Any, emit_signal: bool = True):
        """
        设置属性值
        
        Args:
            name: 属性名
            value: 属性值
            emit_signal: 是否发送属性变更信号
        """
        old_value = self._properties.get(name)
        
        if old_value != value:
            self._properties[name] = value
            
            if emit_signal:
                self.property_changed.emit(name, value)
            
            logger.debug(f"==liuq debug== 属性变更: {self._view_model_name}.{name} = {value}")
    
    def has_property(self, name: str) -> bool:
        """检查属性是否存在"""
        return name in self._properties
    
    # 忙碌状态管理
    @property
    def is_busy(self) -> bool:
        """获取忙碌状态"""
        return self._is_busy
    
    def set_busy(self, busy: bool, message: str = None):
        """
        设置忙碌状态
        
        Args:
            busy: 忙碌状态
            message: 状态消息
        """
        if self._is_busy != busy:
            self._is_busy = busy
            self.busy_state_changed.emit(busy)
            
            if message:
                self.status_message.emit(message)
            
            logger.debug(f"==liuq debug== 忙碌状态变更: {self._view_model_name} = {busy}")
    
    # 事件总线集成
    def subscribe_event(self, event_type: EventType, handler: Callable[[Event], None]):
        """订阅事件"""
        self._event_bus.subscribe(event_type, handler, self._view_model_name)
    
    def unsubscribe_event(self, event_type: EventType, handler: Callable[[Event], None]):
        """取消订阅事件"""
        self._event_bus.unsubscribe(event_type, handler)
    
    def emit_event(self, event_type: EventType, data: Any = None):
        """发布事件"""
        self._event_bus.emit(event_type, data, self._view_model_name)
    
    # 依赖注入集成
    @property
    def di_container(self) -> DIContainer:
        """获取依赖注入容器"""
        return self._di_container
    
    @property
    def event_bus(self) -> EventBus:
        """获取事件总线"""
        return self._event_bus
    
    def resolve_service(self, service_type: type):
        """解析服务"""
        try:
            return self._di_container.resolve(service_type)
        except Exception as e:
            error_msg = f"解析服务失败: {service_type.__name__}, 错误: {e}"
            logger.error(f"==liuq debug== {error_msg}")
            self.error_occurred.emit(error_msg)
            raise
    
    # 错误处理
    def handle_error(self, error: Exception, message: str = None):
        """
        处理错误
        
        Args:
            error: 异常对象
            message: 自定义错误消息
        """
        error_msg = message or str(error)
        logger.error(f"==liuq debug== ViewModel错误: {self._view_model_name}, {error_msg}")
        
        self.error_occurred.emit(error_msg)
        self.set_busy(False)  # 发生错误时清除忙碌状态
    
    def emit_status(self, message: str):
        """发布状态消息"""
        self.status_message.emit(message)
        logger.debug(f"==liuq debug== 状态消息: {self._view_model_name} - {message}")
    
    # 命令支持（简化版）
    def create_command(self, execute_func: Callable, can_execute_func: Callable[[], bool] = None):
        """
        创建命令对象
        
        Args:
            execute_func: 执行函数
            can_execute_func: 是否可执行的判断函数
            
        Returns:
            Command对象
        """
        return Command(execute_func, can_execute_func, self)
    
    # 生命周期方法
    def initialize(self):
        """初始化方法（子类重写）"""
        pass
    
    def cleanup(self):
        """清理方法（子类重写）"""
        pass
    
    def __del__(self):
        """析构函数"""
        try:
            self.cleanup()
            logger.debug(f"==liuq debug== ViewModel销毁: {self._view_model_name}")
        except Exception as e:
            logger.error(f"==liuq debug== ViewModel销毁失败: {self._view_model_name}, {e}")


class Command(QObject):
    """
    命令类，实现命令模式
    """
    
    # 信号定义
    can_execute_changed = pyqtSignal()
    
    def __init__(self, execute_func: Callable, can_execute_func: Callable[[], bool] = None, 
                 view_model: BaseViewModel = None):
        super().__init__()
        self._execute_func = execute_func
        self._can_execute_func = can_execute_func or (lambda: True)
        self._view_model = view_model
    
    def execute(self, *args, **kwargs):
        """执行命令"""
        if self.can_execute():
            try:
                return self._execute_func(*args, **kwargs)
            except Exception as e:
                if self._view_model:
                    self._view_model.handle_error(e)
                else:
                    logger.error(f"==liuq debug== 命令执行失败: {e}")
                    raise
    
    def can_execute(self) -> bool:
        """检查是否可以执行"""
        try:
            return self._can_execute_func()
        except Exception as e:
            logger.error(f"==liuq debug== 检查命令可执行性失败: {e}")
            return False
    
    def raise_can_execute_changed(self):
        """触发可执行状态变更信号"""
        self.can_execute_changed.emit()


class ViewModelFactory:
    """ViewModel工厂类"""
    
    def __init__(self, di_container: DIContainer = None):
        self._di_container = di_container or get_container()
    
    def create_view_model(self, view_model_type: type, **kwargs) -> BaseViewModel:
        """
        创建ViewModel实例
        
        Args:
            view_model_type: ViewModel类型
            **kwargs: 额外参数
            
        Returns:
            ViewModel实例
        """
        try:
            # 尝试通过依赖注入创建
            if self._di_container.is_registered(view_model_type):
                return self._di_container.resolve(view_model_type)
            
            # 手动创建
            view_model = view_model_type(**kwargs)
            view_model.initialize()
            
            logger.debug(f"==liuq debug== 创建ViewModel: {view_model_type.__name__}")
            return view_model
            
        except Exception as e:
            logger.error(f"==liuq debug== 创建ViewModel失败: {view_model_type.__name__}, {e}")
            raise


# 全局工厂实例
_global_factory: Optional[ViewModelFactory] = None


def get_view_model_factory() -> ViewModelFactory:
    """获取全局ViewModel工厂实例"""
    global _global_factory
    
    if _global_factory is None:
        _global_factory = ViewModelFactory()
        logger.info("==liuq debug== 创建全局ViewModel工厂")
    
    return _global_factory