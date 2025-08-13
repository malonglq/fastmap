#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段定义提供者接口
==liuq debug== FastMapV2 字段定义管理抽象接口

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 10:20:00 +08:00; Reason: P1-AR-001 设计核心接口定义; Principle_Applied: SOLID-I接口隔离原则;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 定义字段定义管理的抽象接口，支持动态字段注册和配置
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass
from enum import Enum
import logging

# 导入字段定义相关类
from core.interfaces.xml_field_definition import XMLFieldDefinition, FieldType, ValidationRule


class FieldGroup(Enum):
    """字段分组枚举"""
    BASIC = "basic"              # 基础字段（alias_name, x, y, weight等）
    RANGES = "ranges"            # 范围字段（bv_range, ir_range, cct_range等）
    BOUNDARIES = "boundaries"    # 边界字段（base_boundary等）
    ADVANCED = "advanced"        # 高级字段（detect_flag等）
    CUSTOM = "custom"           # 自定义字段
    FUTURE = "future"           # 预留字段


@dataclass
class FieldRegistrationResult:
    """字段注册结果"""
    success: bool                           # 注册是否成功
    field_id: str                          # 字段ID
    message: str                           # 结果消息
    conflicts: List[str]                   # 冲突的字段ID列表
    warnings: List[str]                    # 警告信息


class FieldDefinitionProvider(ABC):
    """
    字段定义提供者接口
    
    负责管理XML字段定义的注册、查询、分组等功能。
    支持动态字段注册和配置，是可扩展架构的核心组件。
    
    设计原则：
    - 单一职责：只负责字段定义的管理
    - 开闭原则：支持新字段类型的扩展
    - 接口隔离：提供细粒度的字段操作接口
    """
    
    @abstractmethod
    def register_field(self, field_definition: XMLFieldDefinition, 
                      override: bool = False) -> FieldRegistrationResult:
        """
        注册字段定义
        
        Args:
            field_definition: 字段定义对象
            override: 是否覆盖已存在的字段
            
        Returns:
            FieldRegistrationResult: 注册结果
        """
        pass
    
    @abstractmethod
    def unregister_field(self, field_id: str) -> bool:
        """
        注销字段定义
        
        Args:
            field_id: 字段ID
            
        Returns:
            bool: 注销是否成功
        """
        pass
    
    @abstractmethod
    def get_field(self, field_id: str) -> Optional[XMLFieldDefinition]:
        """
        获取字段定义
        
        Args:
            field_id: 字段ID
            
        Returns:
            Optional[XMLFieldDefinition]: 字段定义对象，不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_all_fields(self) -> List[XMLFieldDefinition]:
        """
        获取所有字段定义
        
        Returns:
            List[XMLFieldDefinition]: 所有字段定义列表
        """
        pass
    
    @abstractmethod
    def get_fields_by_group(self, group: FieldGroup) -> List[XMLFieldDefinition]:
        """
        根据分组获取字段定义
        
        Args:
            group: 字段分组
            
        Returns:
            List[XMLFieldDefinition]: 指定分组的字段定义列表
        """
        pass
    
    @abstractmethod
    def get_visible_fields(self) -> List[XMLFieldDefinition]:
        """
        获取可见字段定义
        
        Returns:
            List[XMLFieldDefinition]: 可见字段定义列表
        """
        pass
    
    @abstractmethod
    def get_editable_fields(self) -> List[XMLFieldDefinition]:
        """
        获取可编辑字段定义
        
        Returns:
            List[XMLFieldDefinition]: 可编辑字段定义列表
        """
        pass
    
    @abstractmethod
    def set_field_visibility(self, field_id: str, visible: bool) -> bool:
        """
        设置字段可见性
        
        Args:
            field_id: 字段ID
            visible: 是否可见
            
        Returns:
            bool: 设置是否成功
        """
        pass
    
    @abstractmethod
    def set_field_editability(self, field_id: str, editable: bool) -> bool:
        """
        设置字段可编辑性
        
        Args:
            field_id: 字段ID
            editable: 是否可编辑
            
        Returns:
            bool: 设置是否成功
        """
        pass
    
    @abstractmethod
    def get_field_groups(self) -> List[FieldGroup]:
        """
        获取所有字段分组
        
        Returns:
            List[FieldGroup]: 字段分组列表
        """
        pass
    
    @abstractmethod
    def get_fields_by_type(self, field_type: FieldType) -> List[XMLFieldDefinition]:
        """
        根据字段类型获取字段定义
        
        Args:
            field_type: 字段类型
            
        Returns:
            List[XMLFieldDefinition]: 指定类型的字段定义列表
        """
        pass
    
    @abstractmethod
    def validate_field_definition(self, field_definition: XMLFieldDefinition) -> List[str]:
        """
        验证字段定义的有效性
        
        Args:
            field_definition: 字段定义对象
            
        Returns:
            List[str]: 验证错误信息列表，空列表表示验证通过
        """
        pass
    
    @abstractmethod
    def export_field_definitions(self, file_path: str, groups: Optional[List[FieldGroup]] = None) -> bool:
        """
        导出字段定义到文件
        
        Args:
            file_path: 导出文件路径
            groups: 要导出的字段分组，None表示导出所有
            
        Returns:
            bool: 导出是否成功
        """
        pass
    
    @abstractmethod
    def import_field_definitions(self, file_path: str, override: bool = False) -> Dict[str, Any]:
        """
        从文件导入字段定义
        
        Args:
            file_path: 导入文件路径
            override: 是否覆盖已存在的字段
            
        Returns:
            Dict[str, Any]: 导入结果，包含成功数量、失败数量、错误信息等
        """
        pass
    
    @abstractmethod
    def register_field_change_callback(self, callback: Callable[[str, str], None]) -> str:
        """
        注册字段变化回调函数
        
        Args:
            callback: 回调函数，参数为(field_id, change_type)
            
        Returns:
            str: 回调ID，用于后续注销
        """
        pass
    
    @abstractmethod
    def unregister_field_change_callback(self, callback_id: str) -> bool:
        """
        注销字段变化回调函数
        
        Args:
            callback_id: 回调ID
            
        Returns:
            bool: 注销是否成功
        """
        pass
    
    @abstractmethod
    def clear_all_fields(self, confirm: bool = False) -> bool:
        """
        清空所有字段定义（危险操作）
        
        Args:
            confirm: 确认执行危险操作
            
        Returns:
            bool: 清空是否成功
        """
        pass
    
    @abstractmethod
    def get_field_statistics(self) -> Dict[str, Any]:
        """
        获取字段统计信息
        
        Returns:
            Dict[str, Any]: 统计信息，包含总数、分组统计、类型统计等
        """
        pass


# 接口版本信息
__version__ = "2.0.0"
__author__ = "龙sir团队"
__description__ = "字段定义提供者接口定义"

logger = logging.getLogger(__name__)
logger.info("==liuq debug== 字段定义提供者接口模块加载完成")
