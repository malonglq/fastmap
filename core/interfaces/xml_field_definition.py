#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML字段定义数据类
==liuq debug== FastMapV2 XML字段定义核心数据结构

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 10:30:00 +08:00; Reason: P1-AR-002 设计字段定义系统; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 定义XML字段的核心数据结构，支持可扩展架构的字段管理
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from enum import Enum
import re
import logging


class FieldType(Enum):
    """
    XML字段类型枚举
    
    定义支持的所有字段类型，用于类型安全和编辑器选择
    """
    STRING = "string"          # 字符串类型
    INTEGER = "integer"        # 整数类型
    FLOAT = "float"           # 浮点数类型
    BOOLEAN = "boolean"       # 布尔值类型
    RANGE = "range"           # 范围类型 (min, max)
    COORDINATE = "coordinate" # 坐标类型 (x, y)
    ARRAY = "array"           # 数组类型
    POLYGON = "polygon"       # 多边形顶点
    ENUM = "enum"             # 枚举类型
    DATE = "date"             # 日期类型
    TIME = "time"             # 时间类型
    DATETIME = "datetime"     # 日期时间类型


class ValidationRuleType(Enum):
    """验证规则类型枚举"""
    REQUIRED = "required"      # 必填验证
    MIN_VALUE = "min_value"    # 最小值验证
    MAX_VALUE = "max_value"    # 最大值验证
    MIN_LENGTH = "min_length"  # 最小长度验证
    MAX_LENGTH = "max_length"  # 最大长度验证
    PATTERN = "pattern"        # 正则表达式验证
    RANGE = "range"           # 范围验证
    ENUM_VALUES = "enum_values" # 枚举值验证
    CUSTOM = "custom"          # 自定义验证函数


@dataclass
class ValidationRule:
    """
    字段验证规则
    
    定义字段的验证逻辑，支持多种验证类型
    """
    rule_type: ValidationRuleType
    value: Any = None                    # 验证参数值
    error_message: str = ""              # 错误提示信息
    custom_validator: Optional[Callable[[Any], bool]] = None  # 自定义验证函数
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.error_message:
            self.error_message = self._generate_default_error_message()
    
    def _generate_default_error_message(self) -> str:
        """生成默认错误信息"""
        messages = {
            ValidationRuleType.REQUIRED: "此字段为必填项",
            ValidationRuleType.MIN_VALUE: f"值不能小于 {self.value}",
            ValidationRuleType.MAX_VALUE: f"值不能大于 {self.value}",
            ValidationRuleType.MIN_LENGTH: f"长度不能少于 {self.value} 个字符",
            ValidationRuleType.MAX_LENGTH: f"长度不能超过 {self.value} 个字符",
            ValidationRuleType.PATTERN: "格式不正确",
            ValidationRuleType.RANGE: f"值必须在 {self.value} 范围内",
            ValidationRuleType.ENUM_VALUES: f"值必须是以下之一: {self.value}",
            ValidationRuleType.CUSTOM: "自定义验证失败"
        }
        return messages.get(self.rule_type, "验证失败")
    
    def validate(self, value: Any) -> Tuple[bool, str]:
        """
        验证值
        
        Args:
            value: 待验证的值
            
        Returns:
            Tuple[bool, str]: (是否通过验证, 错误信息)
        """
        try:
            if self.rule_type == ValidationRuleType.REQUIRED:
                is_valid = value is not None and str(value).strip() != ""
                
            elif self.rule_type == ValidationRuleType.MIN_VALUE:
                is_valid = float(value) >= float(self.value)
                
            elif self.rule_type == ValidationRuleType.MAX_VALUE:
                is_valid = float(value) <= float(self.value)
                
            elif self.rule_type == ValidationRuleType.MIN_LENGTH:
                is_valid = len(str(value)) >= int(self.value)
                
            elif self.rule_type == ValidationRuleType.MAX_LENGTH:
                is_valid = len(str(value)) <= int(self.value)
                
            elif self.rule_type == ValidationRuleType.PATTERN:
                is_valid = bool(re.match(str(self.value), str(value)))
                
            elif self.rule_type == ValidationRuleType.RANGE:
                min_val, max_val = self.value
                is_valid = min_val <= float(value) <= max_val
                
            elif self.rule_type == ValidationRuleType.ENUM_VALUES:
                is_valid = value in self.value
                
            elif self.rule_type == ValidationRuleType.CUSTOM:
                is_valid = self.custom_validator(value) if self.custom_validator else True
                
            else:
                is_valid = True
                
            return is_valid, "" if is_valid else self.error_message
            
        except Exception as e:
            logger.warning(f"==liuq debug== 验证规则执行失败: {e}")
            return False, f"验证执行失败: {e}"


@dataclass
class XMLFieldDefinition:
    """
    XML字段定义
    
    定义XML字段的所有属性，包括类型、验证规则、显示属性等
    这是整个可扩展架构的核心数据结构
    """
    field_id: str                                    # 唯一标识符
    display_name: str                               # 显示名称
    field_type: FieldType                           # 字段类型
    xml_path: str                                   # XML路径表达式
    default_value: Any = None                       # 默认值
    validation_rules: List[ValidationRule] = field(default_factory=list)
    is_editable: bool = True                        # 是否可编辑
    is_visible: bool = True                         # 是否默认显示
    is_core_field: bool = True                      # 是否为核心字段（用于默认表格显示）
    group: str = "default"                          # 字段分组
    description: str = ""                           # 字段描述
    custom_editor: Optional[str] = None             # 自定义编辑器类名
    sort_order: int = 0                             # 排序顺序
    width_hint: int = 100                           # 列宽提示（表格列宽度）
    tooltip: str = ""                               # 工具提示文本
    tooltip: str = ""                               # 工具提示
    placeholder: str = ""                           # 占位符文本
    format_string: str = ""                         # 格式化字符串
    enum_values: List[Any] = field(default_factory=list)  # 枚举值列表
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def validate_value(self, value: Any) -> Tuple[bool, List[str]]:
        """
        验证字段值
        
        Args:
            value: 待验证的值
            
        Returns:
            Tuple[bool, List[str]]: (是否通过所有验证, 错误信息列表)
        """
        errors = []
        
        # 特殊处理：如果是空字符串且字段ID是alias_name，跳过验证
        if (self.field_id == "alias_name" and 
            (value == "" or value is None or str(value).strip() == "")):

            return True, []
        
        for rule in self.validation_rules:
            is_valid, error_msg = rule.validate(value)
            if not is_valid:
                errors.append(error_msg)
        
        is_all_valid = len(errors) == 0
        
        if not is_all_valid:
            logger.warning(f"==liuq debug== 字段 {self.field_id} 验证失败: {errors}")
        
        return is_all_valid, errors
    
    def convert_value(self, raw_value: Any) -> Any:
        """
        根据字段类型转换值
        
        Args:
            raw_value: 原始值
            
        Returns:
            Any: 转换后的值
        """
        if raw_value is None:
            return self.default_value
        
        try:
            if self.field_type == FieldType.STRING:
                return str(raw_value)
                
            elif self.field_type == FieldType.INTEGER:
                return int(float(raw_value))  # 先转float再转int，处理"1.0"这种情况
                
            elif self.field_type == FieldType.FLOAT:
                return float(raw_value)
                
            elif self.field_type == FieldType.BOOLEAN:
                if isinstance(raw_value, bool):
                    return raw_value
                return str(raw_value).lower() in ('true', '1', 'yes', 'on')
                
            elif self.field_type == FieldType.RANGE:
                if isinstance(raw_value, (list, tuple)) and len(raw_value) == 2:
                    return (float(raw_value[0]), float(raw_value[1]))
                return self.default_value
                
            elif self.field_type == FieldType.COORDINATE:
                if isinstance(raw_value, (list, tuple)) and len(raw_value) == 2:
                    return (float(raw_value[0]), float(raw_value[1]))
                return self.default_value
                
            elif self.field_type == FieldType.ARRAY:
                if isinstance(raw_value, (list, tuple)):
                    return list(raw_value)
                return [raw_value] if raw_value is not None else []
                
            elif self.field_type == FieldType.ENUM:
                if raw_value in self.enum_values:
                    return raw_value
                return self.default_value
                
            else:
                return raw_value
                
        except (ValueError, TypeError) as e:
            logger.warning(f"==liuq debug== 字段 {self.field_id} 值转换失败: {e}")
            return self.default_value
    
    def format_value(self, value: Any) -> str:
        """
        格式化值用于显示
        
        Args:
            value: 要格式化的值
            
        Returns:
            str: 格式化后的字符串
        """
        if value is None:
            return ""
        
        if self.format_string:
            try:
                return self.format_string.format(value)
            except:
                pass
        
        if self.field_type == FieldType.FLOAT:
            # 使用智能格式化：整数显示为整数格式，小数保持小数格式
            float_val = float(value)
            if float_val.is_integer():
                return str(int(float_val))
            else:
                return f"{float_val:.2f}"
        elif self.field_type == FieldType.RANGE:
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return f"[{value[0]:.2f}, {value[1]:.2f}]"
        elif self.field_type == FieldType.COORDINATE:
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return f"({value[0]:.2f}, {value[1]:.2f})"
        
        return str(value)
    
    def get_editor_hint(self) -> str:
        """
        获取编辑器提示
        
        Returns:
            str: 编辑器类型提示
        """
        if self.custom_editor:
            return self.custom_editor
        
        editor_mapping = {
            FieldType.STRING: "TextFieldEditor",
            FieldType.INTEGER: "NumericFieldEditor",
            FieldType.FLOAT: "NumericFieldEditor",
            FieldType.BOOLEAN: "BooleanFieldEditor",
            FieldType.RANGE: "RangeFieldEditor",
            FieldType.COORDINATE: "CoordinateFieldEditor",
            FieldType.ENUM: "ComboBoxFieldEditor",
            FieldType.ARRAY: "ArrayFieldEditor"
        }
        
        return editor_mapping.get(self.field_type, "TextFieldEditor")


# 预定义的常用验证规则
class CommonValidationRules:
    """常用验证规则的工厂类"""
    
    @staticmethod
    def required() -> ValidationRule:
        """必填验证"""
        return ValidationRule(ValidationRuleType.REQUIRED)
    
    @staticmethod
    def min_value(min_val: float) -> ValidationRule:
        """最小值验证"""
        return ValidationRule(ValidationRuleType.MIN_VALUE, min_val)
    
    @staticmethod
    def max_value(max_val: float) -> ValidationRule:
        """最大值验证"""
        return ValidationRule(ValidationRuleType.MAX_VALUE, max_val)
    
    @staticmethod
    def range_value(min_val: float, max_val: float) -> List[ValidationRule]:
        """范围验证"""
        return [
            ValidationRule(ValidationRuleType.MIN_VALUE, min_val),
            ValidationRule(ValidationRuleType.MAX_VALUE, max_val)
        ]
    
    @staticmethod
    def positive_number() -> ValidationRule:
        """正数验证"""
        return ValidationRule(ValidationRuleType.MIN_VALUE, 0.0, "值必须为正数")
    
    @staticmethod
    def alias_name_pattern() -> ValidationRule:
        """别名格式验证（放宽规则，允许更多格式）"""
        pattern = r'^[A-Za-z0-9][A-Za-z0-9_]*$'
        return ValidationRule(
            ValidationRuleType.PATTERN,
            pattern,
            "别名必须以字母或数字开头，只能包含字母、数字和下划线"
        )
    
    @staticmethod
    def enum_values(values: List[Any]) -> ValidationRule:
        """枚举值验证"""
        return ValidationRule(
            ValidationRuleType.ENUM_VALUES,
            values,
            f"值必须是以下之一: {', '.join(map(str, values))}"
        )


# 接口版本信息
__version__ = "2.0.0"
__author__ = "龙sir团队"
__description__ = "XML字段定义核心数据结构"

logger = logging.getLogger(__name__)


# ==================== 表格列定义相关数据类 ====================
# {{CHENGQI:
# Action: Added; Timestamp: 2025-08-04 16:30:00 +08:00; Reason: 添加动态表格列生成支持; Principle_Applied: SOLID-S单一职责原则;
# }}

@dataclass
class TableColumnDefinition:
    """
    表格列定义数据类

    定义表格列的所有属性，支持动态列生成和用户配置
    """
    column_id: str                      # 列唯一标识符
    field_id: str                       # 关联的字段ID
    display_name: str                   # 列显示名称
    width: int = 100                    # 列宽度（像素）
    is_visible: bool = True             # 是否可见
    sort_order: int = 0                 # 排序权重（越小越靠前）
    group: str = "default"              # 列分组
    is_resizable: bool = True           # 是否可调整大小
    is_sortable: bool = True            # 是否可排序
    alignment: str = "left"             # 对齐方式 ("left", "center", "right")
    tooltip: str = ""                   # 工具提示
    min_width: int = 50                 # 最小宽度
    max_width: int = 300                # 最大宽度

    def __post_init__(self):
        """初始化后验证"""
        if self.width < self.min_width:
            self.width = self.min_width
        elif self.width > self.max_width:
            self.width = self.max_width


@dataclass
class TableConfiguration:
    """
    表格配置数据类

    管理整个表格的配置信息
    """
    config_name: str                    # 配置名称
    columns: List[TableColumnDefinition] = field(default_factory=list)  # 列定义列表
    total_width: int = 0                # 总宽度
    auto_resize: bool = True            # 自动调整大小
    show_grid: bool = True              # 显示网格线
    alternate_row_colors: bool = True   # 交替行颜色
    created_time: str = ""              # 创建时间
    modified_time: str = ""             # 修改时间

    def get_visible_columns(self) -> List[TableColumnDefinition]:
        """获取可见列列表"""
        return [col for col in self.columns if col.is_visible]

    def get_column_by_field_id(self, field_id: str) -> Optional[TableColumnDefinition]:
        """根据字段ID获取列定义"""
        for col in self.columns:
            if col.field_id == field_id:
                return col
        return None

    def update_column_visibility(self, field_id: str, is_visible: bool) -> bool:
        """更新列可见性"""
        col = self.get_column_by_field_id(field_id)
        if col:
            col.is_visible = is_visible
            return True
        return False


logger.info("==liuq debug== XML字段定义系统模块加载完成")
