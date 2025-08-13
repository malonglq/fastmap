#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML字段定义单元测试
==liuq debug== FastMapV2 XML字段定义系统测试

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 10:42:00 +08:00; Reason: P1-AR-002 创建字段定义单元测试; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 测试XML字段定义系统的功能
"""

import unittest
import logging
from typing import List

from core.interfaces.xml_field_definition import (
    XMLFieldDefinition,
    FieldType,
    ValidationRule,
    ValidationRuleType,
    CommonValidationRules
)

logger = logging.getLogger(__name__)


class TestValidationRule(unittest.TestCase):
    """验证规则测试类"""
    
    def test_required_validation(self):
        """测试必填验证"""
        rule = ValidationRule(ValidationRuleType.REQUIRED)
        
        # 测试有效值
        is_valid, error = rule.validate("test")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
        
        # 测试无效值
        is_valid, error = rule.validate("")
        self.assertFalse(is_valid)
        self.assertIn("必填", error)
        
        is_valid, error = rule.validate(None)
        self.assertFalse(is_valid)
        self.assertIn("必填", error)
    
    def test_min_value_validation(self):
        """测试最小值验证"""
        rule = ValidationRule(ValidationRuleType.MIN_VALUE, 10)
        
        # 测试有效值
        is_valid, error = rule.validate(15)
        self.assertTrue(is_valid)
        
        is_valid, error = rule.validate(10)
        self.assertTrue(is_valid)
        
        # 测试无效值
        is_valid, error = rule.validate(5)
        self.assertFalse(is_valid)
        self.assertIn("不能小于", error)
    
    def test_max_value_validation(self):
        """测试最大值验证"""
        rule = ValidationRule(ValidationRuleType.MAX_VALUE, 100)
        
        # 测试有效值
        is_valid, error = rule.validate(50)
        self.assertTrue(is_valid)
        
        is_valid, error = rule.validate(100)
        self.assertTrue(is_valid)
        
        # 测试无效值
        is_valid, error = rule.validate(150)
        self.assertFalse(is_valid)
        self.assertIn("不能大于", error)
    
    def test_pattern_validation(self):
        """测试正则表达式验证"""
        rule = ValidationRule(ValidationRuleType.PATTERN, r'^[A-Za-z0-9_]+$')
        
        # 测试有效值
        is_valid, error = rule.validate("test_123")
        self.assertTrue(is_valid)
        
        # 测试无效值
        is_valid, error = rule.validate("test-123")
        self.assertFalse(is_valid)
        self.assertIn("格式不正确", error)
    
    def test_range_validation(self):
        """测试范围验证"""
        rule = ValidationRule(ValidationRuleType.RANGE, (10, 100))
        
        # 测试有效值
        is_valid, error = rule.validate(50)
        self.assertTrue(is_valid)
        
        is_valid, error = rule.validate(10)
        self.assertTrue(is_valid)
        
        is_valid, error = rule.validate(100)
        self.assertTrue(is_valid)
        
        # 测试无效值
        is_valid, error = rule.validate(5)
        self.assertFalse(is_valid)
        
        is_valid, error = rule.validate(150)
        self.assertFalse(is_valid)
    
    def test_enum_values_validation(self):
        """测试枚举值验证"""
        rule = ValidationRule(ValidationRuleType.ENUM_VALUES, ["red", "green", "blue"])
        
        # 测试有效值
        is_valid, error = rule.validate("red")
        self.assertTrue(is_valid)
        
        # 测试无效值
        is_valid, error = rule.validate("yellow")
        self.assertFalse(is_valid)
        self.assertIn("必须是以下之一", error)


class TestXMLFieldDefinition(unittest.TestCase):
    """XML字段定义测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.field_def = XMLFieldDefinition(
            field_id="test_field",
            display_name="测试字段",
            field_type=FieldType.STRING,
            xml_path=".//test",
            default_value="default"
        )
    
    def test_field_creation(self):
        """测试字段创建"""
        self.assertEqual(self.field_def.field_id, "test_field")
        self.assertEqual(self.field_def.display_name, "测试字段")
        self.assertEqual(self.field_def.field_type, FieldType.STRING)
        self.assertEqual(self.field_def.xml_path, ".//test")
        self.assertEqual(self.field_def.default_value, "default")
        self.assertTrue(self.field_def.is_editable)
        self.assertTrue(self.field_def.is_visible)
    
    def test_value_conversion_string(self):
        """测试字符串类型值转换"""
        field_def = XMLFieldDefinition(
            field_id="string_field",
            display_name="字符串字段",
            field_type=FieldType.STRING,
            xml_path=".//string"
        )
        
        self.assertEqual(field_def.convert_value(123), "123")
        self.assertEqual(field_def.convert_value("test"), "test")
        self.assertEqual(field_def.convert_value(None), None)
    
    def test_value_conversion_integer(self):
        """测试整数类型值转换"""
        field_def = XMLFieldDefinition(
            field_id="int_field",
            display_name="整数字段",
            field_type=FieldType.INTEGER,
            xml_path=".//int",
            default_value=0
        )
        
        self.assertEqual(field_def.convert_value("123"), 123)
        self.assertEqual(field_def.convert_value("123.5"), 123)
        self.assertEqual(field_def.convert_value(123.7), 123)
        self.assertEqual(field_def.convert_value(None), 0)
    
    def test_value_conversion_float(self):
        """测试浮点数类型值转换"""
        field_def = XMLFieldDefinition(
            field_id="float_field",
            display_name="浮点数字段",
            field_type=FieldType.FLOAT,
            xml_path=".//float",
            default_value=0.0
        )
        
        self.assertEqual(field_def.convert_value("123.5"), 123.5)
        self.assertEqual(field_def.convert_value(123), 123.0)
        self.assertEqual(field_def.convert_value(None), 0.0)
    
    def test_value_conversion_boolean(self):
        """测试布尔类型值转换"""
        field_def = XMLFieldDefinition(
            field_id="bool_field",
            display_name="布尔字段",
            field_type=FieldType.BOOLEAN,
            xml_path=".//bool",
            default_value=False
        )
        
        self.assertTrue(field_def.convert_value("true"))
        self.assertTrue(field_def.convert_value("1"))
        self.assertTrue(field_def.convert_value("yes"))
        self.assertTrue(field_def.convert_value(True))
        
        self.assertFalse(field_def.convert_value("false"))
        self.assertFalse(field_def.convert_value("0"))
        self.assertFalse(field_def.convert_value("no"))
        self.assertFalse(field_def.convert_value(False))
    
    def test_value_conversion_range(self):
        """测试范围类型值转换"""
        field_def = XMLFieldDefinition(
            field_id="range_field",
            display_name="范围字段",
            field_type=FieldType.RANGE,
            xml_path=".//range",
            default_value=(0.0, 100.0)
        )
        
        result = field_def.convert_value([10, 20])
        self.assertEqual(result, (10.0, 20.0))
        
        result = field_def.convert_value((30.5, 40.5))
        self.assertEqual(result, (30.5, 40.5))
        
        result = field_def.convert_value(None)
        self.assertEqual(result, (0.0, 100.0))
    
    def test_value_validation_with_rules(self):
        """测试带验证规则的值验证"""
        field_def = XMLFieldDefinition(
            field_id="validated_field",
            display_name="验证字段",
            field_type=FieldType.INTEGER,
            xml_path=".//validated",
            validation_rules=[
                ValidationRule(ValidationRuleType.REQUIRED),
                ValidationRule(ValidationRuleType.MIN_VALUE, 10),
                ValidationRule(ValidationRuleType.MAX_VALUE, 100)
            ]
        )
        
        # 测试有效值
        is_valid, errors = field_def.validate_value(50)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # 测试无效值 - 空值
        is_valid, errors = field_def.validate_value(None)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # 测试无效值 - 超出范围
        is_valid, errors = field_def.validate_value(150)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_value_formatting(self):
        """测试值格式化"""
        # 测试浮点数格式化
        float_field = XMLFieldDefinition(
            field_id="float_field",
            display_name="浮点数字段",
            field_type=FieldType.FLOAT,
            xml_path=".//float"
        )
        self.assertEqual(float_field.format_value(123.456), "123.46")
        
        # 测试范围格式化
        range_field = XMLFieldDefinition(
            field_id="range_field",
            display_name="范围字段",
            field_type=FieldType.RANGE,
            xml_path=".//range"
        )
        self.assertEqual(range_field.format_value((10.123, 20.456)), "[10.12, 20.46]")
        
        # 测试坐标格式化
        coord_field = XMLFieldDefinition(
            field_id="coord_field",
            display_name="坐标字段",
            field_type=FieldType.COORDINATE,
            xml_path=".//coord"
        )
        self.assertEqual(coord_field.format_value((10.123, 20.456)), "(10.12, 20.46)")
    
    def test_editor_hint(self):
        """测试编辑器提示"""
        # 测试默认编辑器提示
        string_field = XMLFieldDefinition(
            field_id="string_field",
            display_name="字符串字段",
            field_type=FieldType.STRING,
            xml_path=".//string"
        )
        self.assertEqual(string_field.get_editor_hint(), "TextFieldEditor")
        
        # 测试自定义编辑器
        custom_field = XMLFieldDefinition(
            field_id="custom_field",
            display_name="自定义字段",
            field_type=FieldType.STRING,
            xml_path=".//custom",
            custom_editor="CustomEditor"
        )
        self.assertEqual(custom_field.get_editor_hint(), "CustomEditor")


class TestCommonValidationRules(unittest.TestCase):
    """常用验证规则测试类"""
    
    def test_required_rule(self):
        """测试必填规则"""
        rule = CommonValidationRules.required()
        self.assertEqual(rule.rule_type, ValidationRuleType.REQUIRED)
    
    def test_min_value_rule(self):
        """测试最小值规则"""
        rule = CommonValidationRules.min_value(10)
        self.assertEqual(rule.rule_type, ValidationRuleType.MIN_VALUE)
        self.assertEqual(rule.value, 10)
    
    def test_max_value_rule(self):
        """测试最大值规则"""
        rule = CommonValidationRules.max_value(100)
        self.assertEqual(rule.rule_type, ValidationRuleType.MAX_VALUE)
        self.assertEqual(rule.value, 100)
    
    def test_range_value_rules(self):
        """测试范围值规则"""
        rules = CommonValidationRules.range_value(10, 100)
        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0].rule_type, ValidationRuleType.MIN_VALUE)
        self.assertEqual(rules[1].rule_type, ValidationRuleType.MAX_VALUE)
    
    def test_positive_number_rule(self):
        """测试正数规则"""
        rule = CommonValidationRules.positive_number()
        self.assertEqual(rule.rule_type, ValidationRuleType.MIN_VALUE)
        self.assertEqual(rule.value, 0.0)
    
    def test_alias_name_pattern_rule(self):
        """测试别名格式规则"""
        rule = CommonValidationRules.alias_name_pattern()
        self.assertEqual(rule.rule_type, ValidationRuleType.PATTERN)
        
        # 测试有效别名
        is_valid, _ = rule.validate("Indoor_BV_4000")
        self.assertTrue(is_valid)
        
        # 测试无效别名
        is_valid, _ = rule.validate("-invalid")
        self.assertFalse(is_valid)
    
    def test_enum_values_rule(self):
        """测试枚举值规则"""
        values = ["red", "green", "blue"]
        rule = CommonValidationRules.enum_values(values)
        self.assertEqual(rule.rule_type, ValidationRuleType.ENUM_VALUES)
        self.assertEqual(rule.value, values)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.DEBUG)
    
    # 运行测试
    unittest.main()
