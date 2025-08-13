#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段注册服务单元测试
==liuq debug== FastMapV2 字段注册服务测试

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 10:50:00 +08:00; Reason: P1-LD-004 实现字段注册系统; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 测试字段注册服务的功能
"""

import unittest
import tempfile
import json
import logging
from pathlib import Path

from core.services.field_registry_service import FieldRegistryService, field_registry
from core.interfaces.field_definition_provider import FieldGroup
from core.interfaces.xml_field_definition import (
    XMLFieldDefinition,
    FieldType,
    ValidationRule,
    ValidationRuleType,
    CommonValidationRules
)

logger = logging.getLogger(__name__)


class TestFieldRegistryService(unittest.TestCase):
    """字段注册服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建新的注册服务实例用于测试
        self.registry = FieldRegistryService()
        # 清空预定义字段，从干净状态开始测试
        self.registry.clear_all_fields(confirm=True)
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        registry1 = FieldRegistryService()
        registry2 = FieldRegistryService()
        self.assertIs(registry1, registry2)
    
    def test_register_field_success(self):
        """测试成功注册字段"""
        field_def = XMLFieldDefinition(
            field_id="test_field",
            display_name="测试字段",
            field_type=FieldType.STRING,
            xml_path=".//test",
            group="custom"
        )
        
        result = self.registry.register_field(field_def)
        
        self.assertTrue(result.success)
        self.assertEqual(result.field_id, "test_field")
        self.assertEqual(result.message, "字段注册成功")
        self.assertEqual(len(result.conflicts), 0)
        self.assertEqual(len(result.warnings), 0)
    
    def test_register_field_duplicate_without_override(self):
        """测试注册重复字段（不覆盖）"""
        field_def = XMLFieldDefinition(
            field_id="test_field",
            display_name="测试字段",
            field_type=FieldType.STRING,
            xml_path=".//test"
        )
        
        # 第一次注册
        result1 = self.registry.register_field(field_def)
        self.assertTrue(result1.success)
        
        # 第二次注册（不覆盖）
        result2 = self.registry.register_field(field_def, override=False)
        self.assertFalse(result2.success)
        self.assertIn("已存在", result2.message)
        self.assertEqual(result2.conflicts, ["test_field"])
    
    def test_register_field_duplicate_with_override(self):
        """测试注册重复字段（覆盖）"""
        field_def1 = XMLFieldDefinition(
            field_id="test_field",
            display_name="测试字段1",
            field_type=FieldType.STRING,
            xml_path=".//test1"
        )
        
        field_def2 = XMLFieldDefinition(
            field_id="test_field",
            display_name="测试字段2",
            field_type=FieldType.INTEGER,
            xml_path=".//test2"
        )
        
        # 第一次注册
        result1 = self.registry.register_field(field_def1)
        self.assertTrue(result1.success)
        
        # 第二次注册（覆盖）
        result2 = self.registry.register_field(field_def2, override=True)
        self.assertTrue(result2.success)
        self.assertEqual(result2.conflicts, ["test_field"])
        
        # 验证字段已被覆盖
        retrieved_field = self.registry.get_field("test_field")
        self.assertEqual(retrieved_field.display_name, "测试字段2")
        self.assertEqual(retrieved_field.field_type, FieldType.INTEGER)
    
    def test_register_field_validation_failure(self):
        """测试字段定义验证失败"""
        # 创建无效的字段定义（缺少必填字段）
        field_def = XMLFieldDefinition(
            field_id="",  # 空的字段ID
            display_name="",  # 空的显示名称
            field_type=FieldType.STRING,
            xml_path=""  # 空的XML路径
        )
        
        result = self.registry.register_field(field_def)
        
        self.assertFalse(result.success)
        self.assertIn("验证失败", result.message)
        self.assertGreater(len(result.warnings), 0)
    
    def test_unregister_field(self):
        """测试注销字段"""
        field_def = XMLFieldDefinition(
            field_id="test_field",
            display_name="测试字段",
            field_type=FieldType.STRING,
            xml_path=".//test"
        )
        
        # 注册字段
        self.registry.register_field(field_def)
        self.assertIsNotNone(self.registry.get_field("test_field"))
        
        # 注销字段
        success = self.registry.unregister_field("test_field")
        self.assertTrue(success)
        self.assertIsNone(self.registry.get_field("test_field"))
        
        # 尝试注销不存在的字段
        success = self.registry.unregister_field("non_existent")
        self.assertFalse(success)
    
    def test_get_fields_by_group(self):
        """测试按分组获取字段"""
        # 注册不同分组的字段
        field1 = XMLFieldDefinition(
            field_id="basic_field",
            display_name="基础字段",
            field_type=FieldType.STRING,
            xml_path=".//basic",
            group="basic"
        )
        
        field2 = XMLFieldDefinition(
            field_id="range_field",
            display_name="范围字段",
            field_type=FieldType.RANGE,
            xml_path=".//range",
            group="ranges"
        )
        
        self.registry.register_field(field1)
        self.registry.register_field(field2)
        
        # 测试按分组获取
        basic_fields = self.registry.get_fields_by_group(FieldGroup.BASIC)
        self.assertEqual(len(basic_fields), 1)
        self.assertEqual(basic_fields[0].field_id, "basic_field")
        
        range_fields = self.registry.get_fields_by_group(FieldGroup.RANGES)
        self.assertEqual(len(range_fields), 1)
        self.assertEqual(range_fields[0].field_id, "range_field")
    
    def test_visibility_and_editability(self):
        """测试可见性和可编辑性管理"""
        field_def = XMLFieldDefinition(
            field_id="test_field",
            display_name="测试字段",
            field_type=FieldType.STRING,
            xml_path=".//test",
            is_visible=True,
            is_editable=True
        )
        
        self.registry.register_field(field_def)
        
        # 测试初始状态
        visible_fields = self.registry.get_visible_fields()
        editable_fields = self.registry.get_editable_fields()
        self.assertEqual(len(visible_fields), 1)
        self.assertEqual(len(editable_fields), 1)
        
        # 设置为不可见
        success = self.registry.set_field_visibility("test_field", False)
        self.assertTrue(success)
        visible_fields = self.registry.get_visible_fields()
        self.assertEqual(len(visible_fields), 0)
        
        # 设置为不可编辑
        success = self.registry.set_field_editability("test_field", False)
        self.assertTrue(success)
        editable_fields = self.registry.get_editable_fields()
        self.assertEqual(len(editable_fields), 0)
    
    def test_get_fields_by_type(self):
        """测试按类型获取字段"""
        # 注册不同类型的字段
        string_field = XMLFieldDefinition(
            field_id="string_field",
            display_name="字符串字段",
            field_type=FieldType.STRING,
            xml_path=".//string"
        )
        
        integer_field = XMLFieldDefinition(
            field_id="integer_field",
            display_name="整数字段",
            field_type=FieldType.INTEGER,
            xml_path=".//integer"
        )
        
        float_field = XMLFieldDefinition(
            field_id="float_field",
            display_name="浮点数字段",
            field_type=FieldType.FLOAT,
            xml_path=".//float"
        )
        
        self.registry.register_field(string_field)
        self.registry.register_field(integer_field)
        self.registry.register_field(float_field)
        
        # 测试按类型获取
        string_fields = self.registry.get_fields_by_type(FieldType.STRING)
        self.assertEqual(len(string_fields), 1)
        self.assertEqual(string_fields[0].field_id, "string_field")
        
        numeric_fields = self.registry.get_fields_by_type(FieldType.INTEGER)
        self.assertEqual(len(numeric_fields), 1)
        self.assertEqual(numeric_fields[0].field_id, "integer_field")
    
    def test_field_statistics(self):
        """测试字段统计信息"""
        # 注册一些字段
        fields = [
            XMLFieldDefinition("field1", "字段1", FieldType.STRING, ".//f1", group="basic"),
            XMLFieldDefinition("field2", "字段2", FieldType.INTEGER, ".//f2", group="basic"),
            XMLFieldDefinition("field3", "字段3", FieldType.RANGE, ".//f3", group="ranges"),
        ]
        
        for field_def in fields:
            self.registry.register_field(field_def)
        
        stats = self.registry.get_field_statistics()
        
        self.assertEqual(stats['total_fields'], 3)
        self.assertEqual(stats['visible_fields'], 3)  # 默认都可见
        self.assertEqual(stats['editable_fields'], 3)  # 默认都可编辑
        self.assertEqual(stats['group_counts']['basic'], 2)
        self.assertEqual(stats['group_counts']['ranges'], 1)
        self.assertEqual(stats['type_counts']['string'], 1)
        self.assertEqual(stats['type_counts']['integer'], 1)
        self.assertEqual(stats['type_counts']['range'], 1)
    
    def test_export_import_fields(self):
        """测试字段定义的导出和导入"""
        # 注册一些字段
        field1 = XMLFieldDefinition(
            field_id="export_field1",
            display_name="导出字段1",
            field_type=FieldType.STRING,
            xml_path=".//export1",
            validation_rules=[CommonValidationRules.required()],
            group="custom"
        )
        
        field2 = XMLFieldDefinition(
            field_id="export_field2",
            display_name="导出字段2",
            field_type=FieldType.INTEGER,
            xml_path=".//export2",
            validation_rules=[CommonValidationRules.min_value(10)],
            group="custom"
        )
        
        self.registry.register_field(field1)
        self.registry.register_field(field2)
        
        # 导出到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            success = self.registry.export_field_definitions(export_path)
            self.assertTrue(success)
            
            # 验证导出文件内容
            with open(export_path, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
            
            self.assertEqual(export_data['total_fields'], 2)
            self.assertEqual(len(export_data['fields']), 2)
            
            # 清空注册表
            self.registry.clear_all_fields(confirm=True)
            self.assertEqual(len(self.registry.get_all_fields()), 0)
            
            # 导入字段
            import_result = self.registry.import_field_definitions(export_path)
            
            self.assertEqual(import_result['success_count'], 2)
            self.assertEqual(import_result['failure_count'], 0)
            self.assertEqual(import_result['total_count'], 2)
            
            # 验证导入结果
            imported_fields = self.registry.get_all_fields()
            self.assertEqual(len(imported_fields), 2)
            
            imported_field1 = self.registry.get_field("export_field1")
            self.assertIsNotNone(imported_field1)
            self.assertEqual(imported_field1.display_name, "导出字段1")
            self.assertEqual(imported_field1.field_type, FieldType.STRING)
            
        finally:
            # 清理临时文件
            Path(export_path).unlink(missing_ok=True)
    
    def test_change_callbacks(self):
        """测试字段变化回调"""
        callback_calls = []
        
        def test_callback(field_id: str, change_type: str):
            callback_calls.append((field_id, change_type))
        
        # 注册回调
        callback_id = self.registry.register_field_change_callback(test_callback)
        self.assertIsNotNone(callback_id)
        
        # 注册字段，应该触发回调
        field_def = XMLFieldDefinition(
            field_id="callback_field",
            display_name="回调字段",
            field_type=FieldType.STRING,
            xml_path=".//callback"
        )
        
        self.registry.register_field(field_def)
        
        # 验证回调被调用
        self.assertEqual(len(callback_calls), 1)
        self.assertEqual(callback_calls[0], ("callback_field", "registered"))
        
        # 注销回调
        success = self.registry.unregister_field_change_callback(callback_id)
        self.assertTrue(success)
        
        # 再次操作，不应该触发回调
        self.registry.unregister_field("callback_field")
        self.assertEqual(len(callback_calls), 1)  # 回调数量不变


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.DEBUG)
    
    # 运行测试
    unittest.main()
