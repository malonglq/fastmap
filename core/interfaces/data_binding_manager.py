#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据绑定管理接口
==liuq debug== FastMapV2 数据绑定管理抽象接口

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 10:25:00 +08:00; Reason: P1-AR-001 设计核心接口定义; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 定义数据绑定管理的抽象接口，支持GUI与数据模型的双向绑定
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import logging

# 导入相关类型
try:
    from PyQt5.QtWidgets import QWidget
    from PyQt5.QtCore import QObject, pyqtSignal
except ImportError:
    # 如果PyQt5不可用，定义占位符类型
    QWidget = Any
    QObject = Any
    pyqtSignal = Any

from core.interfaces.xml_field_definition import XMLFieldDefinition


class BindingDirection(Enum):
    """绑定方向枚举"""
    ONE_WAY_TO_GUI = "one_way_to_gui"        # 单向：数据 → GUI
    ONE_WAY_TO_DATA = "one_way_to_data"      # 单向：GUI → 数据
    TWO_WAY = "two_way"                      # 双向绑定


class BindingStatus(Enum):
    """绑定状态枚举"""
    ACTIVE = "active"                        # 活跃状态
    INACTIVE = "inactive"                    # 非活跃状态
    ERROR = "error"                          # 错误状态
    SUSPENDED = "suspended"                  # 暂停状态


@dataclass
class BindingInfo:
    """绑定信息数据类"""
    binding_id: str                          # 绑定ID
    data_object: Any                         # 数据对象
    field_definition: XMLFieldDefinition    # 字段定义
    widget: QWidget                          # GUI组件
    direction: BindingDirection              # 绑定方向
    status: BindingStatus                    # 绑定状态
    last_sync_time: Optional[str] = None     # 最后同步时间
    error_message: Optional[str] = None      # 错误信息
    metadata: Dict[str, Any] = None          # 元数据
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SyncResult:
    """同步结果数据类"""
    success: bool                            # 同步是否成功
    binding_id: str                          # 绑定ID
    direction: BindingDirection              # 同步方向
    old_value: Any                           # 旧值
    new_value: Any                           # 新值
    error_message: Optional[str] = None      # 错误信息
    validation_errors: List[str] = None      # 验证错误
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


class DataBindingManager(ABC):
    """
    数据绑定管理接口
    
    负责GUI组件与数据模型之间的双向绑定管理。
    提供自动化的数据同步、验证和错误处理机制。
    
    设计原则：
    - 单一职责：专注于数据绑定管理
    - 开闭原则：支持新的绑定类型扩展
    - 依赖倒置：依赖抽象而非具体实现
    """
    
    @abstractmethod
    def create_binding(self, data_object: Any, field_definition: XMLFieldDefinition,
                      widget: QWidget, direction: BindingDirection = BindingDirection.TWO_WAY,
                      binding_id: Optional[str] = None) -> str:
        """
        创建数据绑定
        
        Args:
            data_object: 数据对象
            field_definition: 字段定义
            widget: GUI组件
            direction: 绑定方向
            binding_id: 自定义绑定ID，None则自动生成
            
        Returns:
            str: 绑定ID
            
        Raises:
            BindingError: 绑定创建失败
        """
        pass
    
    @abstractmethod
    def remove_binding(self, binding_id: str) -> bool:
        """
        移除数据绑定
        
        Args:
            binding_id: 绑定ID
            
        Returns:
            bool: 移除是否成功
        """
        pass
    
    @abstractmethod
    def get_binding(self, binding_id: str) -> Optional[BindingInfo]:
        """
        获取绑定信息
        
        Args:
            binding_id: 绑定ID
            
        Returns:
            Optional[BindingInfo]: 绑定信息，不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_all_bindings(self) -> List[BindingInfo]:
        """
        获取所有绑定信息
        
        Returns:
            List[BindingInfo]: 所有绑定信息列表
        """
        pass
    
    @abstractmethod
    def sync_to_gui(self, binding_id: Optional[str] = None) -> List[SyncResult]:
        """
        同步数据到GUI
        
        Args:
            binding_id: 指定绑定ID，None则同步所有绑定
            
        Returns:
            List[SyncResult]: 同步结果列表
        """
        pass
    
    @abstractmethod
    def sync_to_data(self, binding_id: Optional[str] = None) -> List[SyncResult]:
        """
        同步GUI到数据
        
        Args:
            binding_id: 指定绑定ID，None则同步所有绑定
            
        Returns:
            List[SyncResult]: 同步结果列表
        """
        pass
    
    @abstractmethod
    def validate_binding_data(self, binding_id: str, value: Any) -> List[str]:
        """
        验证绑定数据
        
        Args:
            binding_id: 绑定ID
            value: 要验证的值
            
        Returns:
            List[str]: 验证错误信息列表，空列表表示验证通过
        """
        pass
    
    @abstractmethod
    def set_binding_status(self, binding_id: str, status: BindingStatus) -> bool:
        """
        设置绑定状态
        
        Args:
            binding_id: 绑定ID
            status: 新状态
            
        Returns:
            bool: 设置是否成功
        """
        pass
    
    @abstractmethod
    def suspend_binding(self, binding_id: str) -> bool:
        """
        暂停绑定
        
        Args:
            binding_id: 绑定ID
            
        Returns:
            bool: 暂停是否成功
        """
        pass
    
    @abstractmethod
    def resume_binding(self, binding_id: str) -> bool:
        """
        恢复绑定
        
        Args:
            binding_id: 绑定ID
            
        Returns:
            bool: 恢复是否成功
        """
        pass
    
    @abstractmethod
    def clear_all_bindings(self) -> bool:
        """
        清空所有绑定
        
        Returns:
            bool: 清空是否成功
        """
        pass
    
    @abstractmethod
    def register_sync_callback(self, callback: Callable[[SyncResult], None]) -> str:
        """
        注册同步回调函数
        
        Args:
            callback: 回调函数，参数为SyncResult
            
        Returns:
            str: 回调ID
        """
        pass
    
    @abstractmethod
    def unregister_sync_callback(self, callback_id: str) -> bool:
        """
        注销同步回调函数
        
        Args:
            callback_id: 回调ID
            
        Returns:
            bool: 注销是否成功
        """
        pass
    
    @abstractmethod
    def get_binding_statistics(self) -> Dict[str, Any]:
        """
        获取绑定统计信息
        
        Returns:
            Dict[str, Any]: 统计信息，包含总数、状态分布、错误统计等
        """
        pass
    
    @abstractmethod
    def batch_sync(self, binding_ids: List[str], direction: BindingDirection) -> List[SyncResult]:
        """
        批量同步数据
        
        Args:
            binding_ids: 绑定ID列表
            direction: 同步方向
            
        Returns:
            List[SyncResult]: 同步结果列表
        """
        pass
    
    @abstractmethod
    def auto_sync_enabled(self) -> bool:
        """
        是否启用自动同步
        
        Returns:
            bool: 自动同步状态
        """
        pass
    
    @abstractmethod
    def set_auto_sync(self, enabled: bool) -> bool:
        """
        设置自动同步状态
        
        Args:
            enabled: 是否启用自动同步
            
        Returns:
            bool: 设置是否成功
        """
        pass


class BindingError(Exception):
    """数据绑定错误"""
    def __init__(self, message: str, binding_id: Optional[str] = None):
        super().__init__(message)
        self.binding_id = binding_id


class SyncError(Exception):
    """数据同步错误"""
    def __init__(self, message: str, binding_id: Optional[str] = None):
        super().__init__(message)
        self.binding_id = binding_id


# 接口版本信息
__version__ = "2.0.0"
__author__ = "龙sir团队"
__description__ = "数据绑定管理接口定义"

logger = logging.getLogger(__name__)
logger.info("==liuq debug== 数据绑定管理接口模块加载完成")
