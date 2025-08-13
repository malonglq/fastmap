#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心接口模块
==liuq debug== FastMapV2 核心接口定义模块

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 10:35:00 +08:00; Reason: P1-AR-001 设计核心接口定义; Principle_Applied: 模块化设计原则;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 核心接口模块初始化文件，导出所有接口定义
"""

import logging

# 导入核心接口
from .xml_data_processor import (
    XMLDataProcessor,
    ValidationLevel,
    ValidationResult,
    XMLParseError,
    XMLWriteError,
    ValidationError,
    BackupError
)

from .field_definition_provider import (
    FieldDefinitionProvider,
    FieldGroup,
    FieldRegistrationResult
)

from .data_binding_manager import (
    DataBindingManager,
    BindingDirection,
    BindingStatus,
    BindingInfo,
    SyncResult,
    BindingError,
    SyncError
)

from .xml_field_definition import (
    XMLFieldDefinition,
    FieldType,
    ValidationRule,
    ValidationRuleType,
    CommonValidationRules
)

# 导出所有接口和相关类
__all__ = [
    # XML数据处理接口
    "XMLDataProcessor",
    "ValidationLevel",
    "ValidationResult",
    "XMLParseError",
    "XMLWriteError",
    "ValidationError",
    "BackupError",
    
    # 字段定义提供者接口
    "FieldDefinitionProvider",
    "FieldGroup",
    "FieldRegistrationResult",
    
    # 数据绑定管理接口
    "DataBindingManager",
    "BindingDirection",
    "BindingStatus",
    "BindingInfo",
    "SyncResult",
    "BindingError",
    "SyncError",
    
    # XML字段定义
    "XMLFieldDefinition",
    "FieldType",
    "ValidationRule",
    "ValidationRuleType",
    "CommonValidationRules"
]

# 版本信息
__version__ = "2.0.0"
__author__ = "龙sir团队"
__description__ = "FastMapV2 核心接口定义模块"

logger = logging.getLogger(__name__)
logger.info("==liuq debug== 核心接口模块加载完成")
