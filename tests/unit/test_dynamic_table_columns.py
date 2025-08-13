#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态表格列生成功能测试
==liuq debug== FastMapV2 动态表格列生成单元测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-04 17:00:00 +08:00; Reason: 添加动态表格列生成功能测试; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-04
版本: 2.0.0
描述: 测试动态表格列生成功能的正确性
"""

import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.interfaces.xml_field_definition import (
    XMLFieldDefinition, FieldType, TableColumnDefinition, TableConfiguration
)
from core.interfaces.field_definition_provider import FieldGroup
from core.managers.table_column_manager import TableColumnManager
from core.services.field_registry_service import FieldRegistryService


class TestDynamicTableColumns:
    """动态表格列生成功能测试类"""
    
    def setup_method(self):
        """测试前设置"""
        # 创建临时配置目录
        self.temp_config_dir = Path("temp_test_configs")
        self.temp_config_dir.mkdir(exist_ok=True)
        
        # 创建表格列管理器
        self.column_manager = TableColumnManager(self.temp_config_dir)
        
        # 创建测试字段注册器
        self.field_registry = FieldRegistryService()
        
        # 注册测试字段
        self._register_test_fields()
    
    def teardown_method(self):
        """测试后清理"""
        # 清理临时配置目录
        import shutil
        if self.temp_config_dir.exists():
            shutil.rmtree(self.temp_config_dir)
    
    def _register_test_fields(self):
        """注册测试字段"""
        test_fields = [
            XMLFieldDefinition(
                field_id="alias_name",
                display_name="Map名称",
                field_type=FieldType.STRING,
                xml_path=".//alias_name",
                group="basic",
                sort_order=1,
                width_hint=120,
                tooltip="Map点的别名"
            ),
            XMLFieldDefinition(
                field_id="offset_x",
                display_name="Offset X",
                field_type=FieldType.FLOAT,
                xml_path=".//offset/x",
                group="coordinate",
                sort_order=2,
                width_hint=80,
                tooltip="X轴偏移量"
            ),
            XMLFieldDefinition(
                field_id="offset_y",
                display_name="Offset Y",
                field_type=FieldType.FLOAT,
                xml_path=".//offset/y",
                group="coordinate",
                sort_order=3,
                width_hint=80,
                tooltip="Y轴偏移量"
            ),
            XMLFieldDefinition(
                field_id="weight",
                display_name="权重",
                field_type=FieldType.FLOAT,
                xml_path=".//weight",
                group="basic",
                sort_order=4,
                width_hint=80,
                tooltip="Map点权重"
            ),
            XMLFieldDefinition(
                field_id="bv_min",
                display_name="BV最小值",
                field_type=FieldType.FLOAT,
                xml_path=".//bv/min",
                group="range",
                sort_order=10,
                width_hint=70,
                tooltip="BV范围最小值"
            )
        ]
        
        for field_def in test_fields:
            self.field_registry.register_field(field_def)
    
    def test_table_column_definition_creation(self):
        """测试表格列定义创建"""
        column_def = TableColumnDefinition(
            column_id="col_test",
            field_id="test_field",
            display_name="测试列",
            width=100,
            is_visible=True,
            sort_order=1,
            group="test",
            tooltip="测试列提示"
        )
        
        assert column_def.column_id == "col_test"
        assert column_def.field_id == "test_field"
        assert column_def.display_name == "测试列"
        assert column_def.width == 100
        assert column_def.is_visible == True
        assert column_def.tooltip == "测试列提示"
    
    def test_table_configuration_creation(self):
        """测试表格配置创建"""
        columns = [
            TableColumnDefinition(
                column_id="col_1",
                field_id="field_1",
                display_name="列1",
                width=100
            ),
            TableColumnDefinition(
                column_id="col_2",
                field_id="field_2",
                display_name="列2",
                width=120,
                is_visible=False
            )
        ]
        
        config = TableConfiguration(
            config_name="test_config",
            columns=columns
        )
        
        assert config.config_name == "test_config"
        assert len(config.columns) == 2
        
        # 测试可见列获取
        visible_columns = config.get_visible_columns()
        assert len(visible_columns) == 1
        assert visible_columns[0].field_id == "field_1"
        
        # 测试根据字段ID获取列
        column = config.get_column_by_field_id("field_2")
        assert column is not None
        assert column.display_name == "列2"
        
        # 测试更新列可见性
        success = config.update_column_visibility("field_2", True)
        assert success == True
        assert config.get_column_by_field_id("field_2").is_visible == True
    
    def test_generate_default_configuration(self):
        """测试生成默认配置"""
        # 模拟字段注册器返回可见字段
        import unittest.mock
        
        with unittest.mock.patch.object(
            self.column_manager, 
            '_sort_fields_for_display',
            return_value=[
                self.field_registry.get_field("alias_name"),
                self.field_registry.get_field("offset_x"),
                self.field_registry.get_field("offset_y"),
                self.field_registry.get_field("weight")
            ]
        ):
            config = self.column_manager.generate_default_configuration()
            
            assert config.config_name == "default"
            assert len(config.columns) >= 4
            
            # 验证列定义
            alias_column = config.get_column_by_field_id("alias_name")
            assert alias_column is not None
            assert alias_column.display_name == "Map名称"
            assert alias_column.width == 120
    
    def test_configuration_save_and_load(self):
        """测试配置保存和加载"""
        # 创建测试配置
        columns = [
            TableColumnDefinition(
                column_id="col_alias",
                field_id="alias_name",
                display_name="Map名称",
                width=120
            ),
            TableColumnDefinition(
                column_id="col_offset_x",
                field_id="offset_x",
                display_name="Offset X",
                width=80
            )
        ]
        
        config = TableConfiguration(
            config_name="test_save_load",
            columns=columns,
            auto_resize=False,
            show_grid=True
        )
        
        # 保存配置
        success = self.column_manager.save_configuration("test_save_load", config)
        assert success == True
        
        # 加载配置
        loaded_config = self.column_manager.load_configuration("test_save_load")
        assert loaded_config.config_name == "test_save_load"
        assert len(loaded_config.columns) == 2
        assert loaded_config.auto_resize == False
        assert loaded_config.show_grid == True
        
        # 验证列定义
        alias_column = loaded_config.get_column_by_field_id("alias_name")
        assert alias_column is not None
        assert alias_column.display_name == "Map名称"
        assert alias_column.width == 120
    
    def test_configuration_export_import(self):
        """测试配置导出和导入"""
        # 创建测试配置
        config = TableConfiguration(
            config_name="test_export_import",
            columns=[
                TableColumnDefinition(
                    column_id="col_weight",
                    field_id="weight",
                    display_name="权重",
                    width=80
                )
            ]
        )
        
        # 保存配置
        self.column_manager.save_configuration("test_export_import", config)
        
        # 导出配置
        export_path = self.temp_config_dir / "exported_config.json"
        success = self.column_manager.export_configuration("test_export_import", export_path)
        assert success == True
        assert export_path.exists()
        
        # 导入配置
        success = self.column_manager.import_configuration(export_path, "imported_config")
        assert success == True
        
        # 验证导入的配置
        imported_config = self.column_manager.load_configuration("imported_config")
        assert imported_config.config_name == "imported_config"
        assert len(imported_config.columns) == 1
        assert imported_config.columns[0].field_id == "weight"
    
    def test_get_available_configurations(self):
        """测试获取可用配置列表"""
        # 创建几个测试配置
        configs = ["config1", "config2", "config3"]
        
        for config_name in configs:
            test_config = TableConfiguration(
                config_name=config_name,
                columns=[]
            )
            self.column_manager.save_configuration(config_name, test_config)
        
        # 获取可用配置列表
        available_configs = self.column_manager.get_available_configurations()
        
        for config_name in configs:
            assert config_name in available_configs
    
    def test_delete_configuration(self):
        """测试删除配置"""
        # 创建测试配置
        test_config = TableConfiguration(
            config_name="to_be_deleted",
            columns=[]
        )
        self.column_manager.save_configuration("to_be_deleted", test_config)
        
        # 验证配置存在
        available_configs = self.column_manager.get_available_configurations()
        assert "to_be_deleted" in available_configs
        
        # 删除配置
        success = self.column_manager.delete_configuration("to_be_deleted")
        assert success == True
        
        # 验证配置已删除
        available_configs = self.column_manager.get_available_configurations()
        assert "to_be_deleted" not in available_configs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
