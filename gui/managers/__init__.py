#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI管理器模块

该模块包含各种GUI管理器：
- Tab间通信管理器
- 状态管理器
- 事件协调器
"""

from .tab_communication_manager import TabCommunicationManager, get_tab_communication_manager

__all__ = [
    'TabCommunicationManager',
    'get_tab_communication_manager'
]