#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML数据处理核心接口
==liuq debug== FastMapV2 XML数据处理抽象接口

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 10:15:00 +08:00; Reason: P1-AR-001 设计核心接口定义; Principle_Applied: SOLID-D依赖倒置原则;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 定义XML数据处理的核心抽象接口，支持可扩展架构
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging

# 导入数据模型
from core.models.map_data import MapConfiguration


class ValidationLevel(Enum):
    """验证级别枚举"""
    BASIC = "basic"          # 基础验证（文件存在、格式正确）
    STRUCTURE = "structure"  # 结构验证（XML结构完整性）
    CONTENT = "content"      # 内容验证（数据有效性）
    FULL = "full"           # 完整验证（所有级别）


@dataclass
class ValidationResult:
    """验证结果数据类"""
    is_valid: bool                          # 是否通过验证
    level: ValidationLevel                  # 验证级别
    errors: List[str]                      # 错误信息列表
    warnings: List[str]                    # 警告信息列表
    metadata: Dict[str, Any]               # 验证元数据
    
    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """添加警告信息"""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0


class XMLDataProcessor(ABC):
    """
    XML数据处理核心接口
    
    定义XML数据的解析、写入、验证等核心操作的抽象契约。
    所有XML处理实现都必须遵循此接口，确保系统的可扩展性和可测试性。
    
    设计原则：
    - 依赖倒置：高层模块不依赖低层模块，都依赖抽象
    - 接口隔离：接口功能单一，职责明确
    - 开闭原则：对扩展开放，对修改封闭
    """
    
    @abstractmethod
    def parse_xml(self, xml_path: Union[str, Path], device_type: str = "unknown") -> MapConfiguration:
        """
        解析XML文件为MapConfiguration对象
        
        Args:
            xml_path: XML文件路径
            device_type: 设备类型 ('reference' | 'debug' | 'unknown')
            
        Returns:
            MapConfiguration: 解析后的配置对象
            
        Raises:
            XMLParseError: XML解析失败
            FileNotFoundError: 文件不存在
            PermissionError: 文件权限不足
        """
        pass
    
    @abstractmethod
    def write_xml(self, config: MapConfiguration, xml_path: Union[str, Path], 
                  backup: bool = True, preserve_format: bool = True) -> bool:
        """
        将MapConfiguration对象写入XML文件
        
        Args:
            config: 要写入的配置对象
            xml_path: 目标XML文件路径
            backup: 是否创建备份文件
            preserve_format: 是否保持原有格式
            
        Returns:
            bool: 写入是否成功
            
        Raises:
            XMLWriteError: XML写入失败
            PermissionError: 文件权限不足
            ValidationError: 数据验证失败
        """
        pass
    
    @abstractmethod
    def validate_xml(self, xml_path: Union[str, Path], 
                     level: ValidationLevel = ValidationLevel.FULL) -> ValidationResult:
        """
        验证XML文件的结构和内容
        
        Args:
            xml_path: XML文件路径
            level: 验证级别
            
        Returns:
            ValidationResult: 验证结果对象
        """
        pass
    
    @abstractmethod
    def get_supported_versions(self) -> List[str]:
        """
        获取支持的XML版本列表
        
        Returns:
            List[str]: 支持的版本列表，如 ['1.0', '1.1', '2.0']
        """
        pass
    
    @abstractmethod
    def get_xml_metadata(self, xml_path: Union[str, Path]) -> Dict[str, Any]:
        """
        获取XML文件的元数据信息
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            Dict[str, Any]: 元数据字典，包含版本、创建时间、大小等信息
        """
        pass
    
    @abstractmethod
    def backup_xml(self, xml_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> str:
        """
        创建XML文件备份
        
        Args:
            xml_path: 源XML文件路径
            backup_dir: 备份目录，None则使用默认备份目录
            
        Returns:
            str: 备份文件路径
            
        Raises:
            BackupError: 备份创建失败
        """
        pass
    
    @abstractmethod
    def restore_from_backup(self, backup_path: Union[str, Path], 
                           target_path: Union[str, Path]) -> bool:
        """
        从备份恢复XML文件
        
        Args:
            backup_path: 备份文件路径
            target_path: 目标文件路径
            
        Returns:
            bool: 恢复是否成功
        """
        pass


class XMLParseError(Exception):
    """XML解析错误"""
    def __init__(self, message: str, line_number: Optional[int] = None, 
                 column_number: Optional[int] = None):
        super().__init__(message)
        self.line_number = line_number
        self.column_number = column_number


class XMLWriteError(Exception):
    """XML写入错误"""
    pass


class ValidationError(Exception):
    """数据验证错误"""
    def __init__(self, message: str, field_name: Optional[str] = None):
        super().__init__(message)
        self.field_name = field_name


class BackupError(Exception):
    """备份操作错误"""
    pass


# 接口版本信息
__version__ = "2.0.0"
__author__ = "龙sir团队"
__description__ = "XML数据处理核心接口定义"

logger = logging.getLogger(__name__)
logger.info("==liuq debug== XML数据处理接口模块加载完成")
