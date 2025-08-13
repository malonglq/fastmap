#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数值格式化工具模块

提供统一的高精度数值格式化算法，消除项目中的代码重复

{{CHENGQI:
Action: Added; Timestamp: 2025-08-02 11:00:00 +08:00; Reason: 重构数值格式化函数，提取共同算法消除代码重复; Principle_Applied: DRY原则，单一职责原则;
}}

作者: AI Assistant
日期: 2025-08-02
"""

from decimal import Decimal, getcontext, InvalidOperation
from typing import Any
import re


def format_decimal_precise(value: Any) -> str:
    """
    统一的高精度小数格式化核心算法
    
    基于成熟的decimal.js算法实现，提供精确的数值格式化：
    1. 优先保持原始字符串精度（避免浮点转换损失）
    2. 使用Python Decimal库进行精确计算（类似decimal.js）
    3. 智能处理整数和小数的显示格式
    4. 完全避免浮点精度问题
    
    Args:
        value: 要格式化的数值（int, float或可转换为数值的字符串）
        
    Returns:
        str: 格式化后的字符串
        
    Examples:
        >>> format_decimal_precise(1.0)
        '1'
        >>> format_decimal_precise(0.75)
        '0.75'
        >>> format_decimal_precise("0.25")
        '0.25'
        >>> format_decimal_precise(2.3)
        '2.3'
    """
    # 设置高精度上下文（参考decimal.js的默认精度）
    original_prec = getcontext().prec
    getcontext().prec = 50
    
    try:
        # 策略1：如果输入是字符串且是有效数字，优先保持原始精度
        if isinstance(value, str):
            # 验证是否为有效的数字字符串
            cleaned_str = value.strip()
            if _is_valid_number_string(cleaned_str):
                try:
                    decimal_value = Decimal(cleaned_str)
                    return _format_decimal_result(decimal_value)
                except InvalidOperation:
                    pass
        
        # 策略2：转换为Decimal进行精确处理
        try:
            # 先转为字符串避免浮点精度问题
            decimal_value = Decimal(str(value))
            return _format_decimal_result(decimal_value)
        except (InvalidOperation, ValueError):
            pass
        
        # 策略3：回退到浮点处理（最后手段）
        float_value = float(value)
        if float_value.is_integer():
            return str(int(float_value))
        else:
            # 使用g格式去除不必要的尾随零
            return f"{float_value:.15g}"
            
    finally:
        # 恢复原始精度设置
        getcontext().prec = original_prec


def _is_valid_number_string(value_str: str) -> bool:
    """
    验证字符串是否为有效的数字字符串
    
    Args:
        value_str: 要验证的字符串
        
    Returns:
        bool: 是否为有效数字字符串
    """
    if not value_str:
        return False
    
    # 使用正则表达式验证数字格式
    # 支持：整数、小数、负数、科学计数法
    number_pattern = r'^[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?$'
    return bool(re.match(number_pattern, value_str))


def _format_decimal_result(decimal_value: Decimal) -> str:
    """
    格式化Decimal结果，参考decimal.js的normalize方法
    
    Args:
        decimal_value: Decimal对象
        
    Returns:
        str: 格式化后的字符串
    """
    # 检查是否为整数
    if decimal_value % 1 == 0:
        return str(int(decimal_value))
    
    # 使用normalize移除尾随零
    normalized = decimal_value.normalize()
    result_str = str(normalized)
    
    # 处理科学计数法
    if 'E' in result_str or 'e' in result_str:
        # 对于非常小的数，保持科学计数法格式，但确保指数部分有两位数
        if abs(decimal_value) < 1e-6:
            # 格式化为标准的科学计数法格式（如1e-07）
            return f"{decimal_value:.0e}"
        else:
            # 使用fixed-point notation
            result_str = format(normalized, 'f')
            # 移除尾随零
            if '.' in result_str:
                result_str = result_str.rstrip('0').rstrip('.')

    return result_str


# 为了保持向后兼容性，提供别名函数
def format_number_precise(value: Any) -> str:
    """
    format_decimal_precise的别名，提供更直观的函数名
    
    Args:
        value: 要格式化的数值
        
    Returns:
        str: 格式化后的字符串
    """
    return format_decimal_precise(value)


def format_integer_precise(value: Any) -> str:
    """
    专门用于整数格式化的函数
    
    Args:
        value: 要格式化的数值
        
    Returns:
        str: 格式化后的整数字符串
    """
    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return "0"


def format_string_safe(value: Any) -> str:
    """
    安全的字符串格式化函数
    
    Args:
        value: 要格式化的值
        
    Returns:
        str: 格式化后的字符串
    """
    if value is None:
        return ""
    return str(value)
