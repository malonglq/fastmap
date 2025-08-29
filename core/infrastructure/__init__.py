#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastMapV2 基础设施模块

提供MVVM架构的基础设施组件：
- 依赖注入容器
- 事件总线系统
- ViewModel基类
"""

# 依赖注入
from .di_container import (
    DIContainer, ServiceLifetime, ServiceDescriptor,
    get_container, configure_services
)

# 事件总线
from .event_bus import (
    EventBus, Event, EventType, EventHandler,
    get_event_bus, subscribe, unsubscribe, emit
)

# ViewModel基础
from .base_view_model import (
    BaseViewModel, Command, ViewModelFactory,
    get_view_model_factory
)

__all__ = [
    # 依赖注入
    'DIContainer', 'ServiceLifetime', 'ServiceDescriptor',
    'get_container', 'configure_services',
    
    # 事件总线
    'EventBus', 'Event', 'EventType', 'EventHandler',
    'get_event_bus', 'subscribe', 'unsubscribe', 'emit',
    
    # ViewModel基础
    'BaseViewModel', 'Command', 'ViewModelFactory',
    'get_view_model_factory'
]