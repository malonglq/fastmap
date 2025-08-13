#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
表格列管理器
==liuq debug== FastMapV2 动态表格列生成管理器

{{CHENGQI:
Action: Added; Timestamp: 2025-08-04 16:35:00 +08:00; Reason: 实现动态表格列生成功能; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-08-04
版本: 2.0.0
描述: 基于字段注册系统的动态表格列管理器，解决GUI硬编码问题
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.interfaces.xml_field_definition import (
    XMLFieldDefinition, TableColumnDefinition, TableConfiguration
)
from core.interfaces.field_definition_provider import FieldGroup
from core.services.field_registry_service import field_registry

logger = logging.getLogger(__name__)


# ==================== 移除硬编码常量 ====================
# {{CHENGQI:
# Action: Removed; Timestamp: 2025-08-04 18:35:00 +08:00; Reason: 移除硬编码常量，改用动态核心字段标记; Principle_Applied: 动态配置原则;
# }}

# 原硬编码常量已移除，现在使用字段注册系统的is_core_field标记来动态生成40列配置


class TableColumnManager:
    """
    表格列管理器
    
    负责基于字段注册系统动态生成表格列定义，支持：
    - 动态列生成
    - 用户配置管理
    - 列可见性控制
    - 配置持久化
    
    设计特点：
    - 基于字段注册系统，支持动态字段
    - 支持多套配置方案
    - 提供默认配置和用户自定义配置
    - 完整的配置导入/导出功能
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化表格列管理器
        
        Args:
            config_dir: 配置文件目录，None则使用默认目录
        """
        self.config_dir = config_dir or Path("data/configs/table_columns")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前配置
        self.current_config: Optional[TableConfiguration] = None
        self.default_config: Optional[TableConfiguration] = None
        
        # 配置缓存
        self._config_cache: Dict[str, TableConfiguration] = {}
        
        logger.info("==liuq debug== 表格列管理器初始化完成")
    
    def generate_default_configuration(self) -> TableConfiguration:
        """
        生成默认表格配置（基于核心字段的动态版本）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-04 18:35:00 +08:00; Reason: 改为基于核心字段标记的真正动态配置; Principle_Applied: 动态配置原则;
        }}

        Returns:
            TableConfiguration: 默认表格配置
        """
        logger.info("==liuq debug== 开始生成默认表格配置（基于核心字段的动态模式）")

        columns = []

        # 获取所有核心字段，按sort_order排序
        all_fields = field_registry.get_all_fields()
        core_fields = [field for field in all_fields if getattr(field, 'is_core_field', False)]
        core_fields.sort(key=lambda f: f.sort_order)

        logger.info(f"==liuq debug== 找到 {len(core_fields)} 个核心字段用于默认表格配置")

        # 为每个核心字段创建列定义
        for field_def in core_fields:
            # 创建列定义
            column = TableColumnDefinition(
                column_id=f"col_{field_def.field_id}",
                field_id=field_def.field_id,
                display_name=field_def.display_name,  # 使用字段注册系统的显示名称
                width=field_def.width_hint,
                is_visible=True,
                sort_order=field_def.sort_order,
                group=field_def.group,
                tooltip=field_def.tooltip or field_def.description,
                is_resizable=True,
                is_sortable=True,
                alignment="left" if field_def.field_id == "alias_name" else "center"
            )
            columns.append(column)
        
        # 创建默认配置
        config = TableConfiguration(
            config_name="default",
            columns=columns,
            auto_resize=True,
            show_grid=True,
            alternate_row_colors=True,
            created_time=datetime.now().isoformat(),
            modified_time=datetime.now().isoformat()
        )
        
        # 计算总宽度
        config.total_width = sum(col.width for col in config.get_visible_columns())
        
        # 验证生成的配置
        self._validate_40_columns_configuration(config)

        logger.info(f"==liuq debug== 默认表格配置生成完成，共 {len(columns)} 列（40列兼容模式）")
        return config

    def _validate_40_columns_configuration(self, config: TableConfiguration) -> bool:
        """
        验证40列配置的正确性

        Args:
            config: 表格配置

        Returns:
            bool: 验证是否通过
        """
        try:
            # 获取核心字段作为验证基准
            all_fields = field_registry.get_all_fields()
            core_fields = [field for field in all_fields if getattr(field, 'is_core_field', False)]
            core_fields.sort(key=lambda f: f.sort_order)

            # 验证列数量
            expected_count = len(core_fields)
            if len(config.columns) != expected_count:
                logger.error(f"==liuq debug== 列数量不正确: 期望{expected_count}列，实际{len(config.columns)}列")
                return False

            # 验证列顺序和字段ID
            for i, expected_field in enumerate(core_fields):
                if i >= len(config.columns):
                    logger.error(f"==liuq debug== 缺少第{i+1}列: {expected_field.field_id}")
                    return False

                actual_col = config.columns[i]
                if actual_col.field_id != expected_field.field_id:
                    logger.error(f"==liuq debug== 第{i+1}列字段ID不匹配: 期望{expected_field.field_id}，实际{actual_col.field_id}")
                    return False

            logger.info(f"==liuq debug== {expected_count}列配置验证通过")
            return True

        except Exception as e:
            logger.error(f"==liuq debug== 40列配置验证失败: {e}")
            return False
    
    def _sort_fields_for_display(self, field_definitions: List[XMLFieldDefinition]) -> List[XMLFieldDefinition]:
        """
        按显示顺序排序字段

        Args:
            field_definitions: 字段定义列表

        Returns:
            List[XMLFieldDefinition]: 排序后的字段定义列表
        """
        fields = field_definitions
        
        # 定义分组优先级
        group_priority = {
            FieldGroup.BASIC: 1,
            FieldGroup.RANGES: 2,
            FieldGroup.BOUNDARIES: 3,
            FieldGroup.ADVANCED: 4,
            FieldGroup.CUSTOM: 5
        }
        
        # 按分组优先级和排序权重排序
        def sort_key(field_def: XMLFieldDefinition):
            try:
                group = FieldGroup(field_def.group)
                group_prio = group_priority.get(group, 999)
            except ValueError:
                group_prio = 999
            
            return (group_prio, field_def.sort_order, field_def.field_id)
        
        sorted_fields = sorted(fields, key=sort_key)
        
        logger.info(f"==liuq debug== 字段排序完成，共 {len(sorted_fields)} 个字段")
        return sorted_fields
    
    def _create_column_from_field(self, field_def: XMLFieldDefinition) -> TableColumnDefinition:
        """
        从字段定义创建列定义
        
        Args:
            field_def: 字段定义
            
        Returns:
            TableColumnDefinition: 列定义
        """
        # 根据字段类型确定默认宽度
        width_map = {
            "alias_name": 120,
            "offset_x": 80,
            "offset_y": 80,
            "weight": 80,
            "trans_step": 60,
        }
        
        # 范围字段使用较小宽度
        if any(keyword in field_def.field_id for keyword in ["_min", "_max", "tran_"]):
            default_width = 80
        else:
            default_width = width_map.get(field_def.field_id, field_def.width_hint)
        
        # 创建列定义
        column = TableColumnDefinition(
            column_id=f"col_{field_def.field_id}",
            field_id=field_def.field_id,
            display_name=field_def.display_name,
            width=default_width,
            is_visible=field_def.is_visible,
            sort_order=field_def.sort_order,
            group=field_def.group,
            tooltip=field_def.description,
            is_resizable=True,
            is_sortable=True,
            alignment="left" if field_def.field_id == "alias_name" else "center"
        )
        
        return column
    
    def get_current_configuration(self) -> TableConfiguration:
        """
        获取当前表格配置
        
        Returns:
            TableConfiguration: 当前配置
        """
        if self.current_config is None:
            # 尝试加载用户配置，失败则使用默认配置
            try:
                self.current_config = self.load_configuration("user_default")
            except:
                self.current_config = self.generate_default_configuration()
                
        return self.current_config
    
    def update_column_visibility(self, field_id: str, is_visible: bool) -> bool:
        """
        更新列可见性
        
        Args:
            field_id: 字段ID
            is_visible: 是否可见
            
        Returns:
            bool: 更新是否成功
        """
        config = self.get_current_configuration()
        success = config.update_column_visibility(field_id, is_visible)
        
        if success:
            config.modified_time = datetime.now().isoformat()
            logger.info(f"==liuq debug== 更新列可见性: {field_id} -> {is_visible}")
        
        return success
    
    def save_configuration(self, config_name: str, config: Optional[TableConfiguration] = None) -> bool:
        """
        保存表格配置
        
        Args:
            config_name: 配置名称
            config: 配置对象，None则保存当前配置
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if config is None:
                config = self.get_current_configuration()
            
            config.config_name = config_name
            config.modified_time = datetime.now().isoformat()
            
            # 转换为字典格式
            config_dict = self._config_to_dict(config)
            
            # 保存到文件
            config_file = self.config_dir / f"{config_name}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            # 更新缓存
            self._config_cache[config_name] = config
            
            logger.info(f"==liuq debug== 表格配置保存成功: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 保存表格配置失败: {e}")
            return False
    
    def load_configuration(self, config_name: str) -> TableConfiguration:
        """
        加载表格配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            TableConfiguration: 配置对象
            
        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误
        """
        # 检查缓存
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        # 从文件加载
        config_file = self.config_dir / f"{config_name}.json"
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            config = self._dict_to_config(config_dict)
            
            # 更新缓存
            self._config_cache[config_name] = config
            
            logger.info(f"==liuq debug== 表格配置加载成功: {config_file}")
            return config
            
        except Exception as e:
            logger.error(f"==liuq debug== 加载表格配置失败: {e}")
            raise ValueError(f"配置格式错误: {e}")

    def _config_to_dict(self, config: TableConfiguration) -> dict:
        """
        将配置对象转换为字典

        Args:
            config: 配置对象

        Returns:
            dict: 配置字典
        """
        return {
            "config_name": config.config_name,
            "columns": [
                {
                    "column_id": col.column_id,
                    "field_id": col.field_id,
                    "display_name": col.display_name,
                    "width": col.width,
                    "is_visible": col.is_visible,
                    "sort_order": col.sort_order,
                    "group": col.group,
                    "is_resizable": col.is_resizable,
                    "is_sortable": col.is_sortable,
                    "alignment": col.alignment,
                    "tooltip": col.tooltip,
                    "min_width": col.min_width,
                    "max_width": col.max_width
                }
                for col in config.columns
            ],
            "total_width": config.total_width,
            "auto_resize": config.auto_resize,
            "show_grid": config.show_grid,
            "alternate_row_colors": config.alternate_row_colors,
            "created_time": config.created_time,
            "modified_time": config.modified_time
        }

    def _dict_to_config(self, config_dict: dict) -> TableConfiguration:
        """
        将字典转换为配置对象

        Args:
            config_dict: 配置字典

        Returns:
            TableConfiguration: 配置对象
        """
        columns = []
        for col_dict in config_dict.get("columns", []):
            column = TableColumnDefinition(
                column_id=col_dict["column_id"],
                field_id=col_dict["field_id"],
                display_name=col_dict["display_name"],
                width=col_dict.get("width", 100),
                is_visible=col_dict.get("is_visible", True),
                sort_order=col_dict.get("sort_order", 0),
                group=col_dict.get("group", "default"),
                is_resizable=col_dict.get("is_resizable", True),
                is_sortable=col_dict.get("is_sortable", True),
                alignment=col_dict.get("alignment", "left"),
                tooltip=col_dict.get("tooltip", ""),
                min_width=col_dict.get("min_width", 50),
                max_width=col_dict.get("max_width", 300)
            )
            columns.append(column)

        return TableConfiguration(
            config_name=config_dict["config_name"],
            columns=columns,
            total_width=config_dict.get("total_width", 0),
            auto_resize=config_dict.get("auto_resize", True),
            show_grid=config_dict.get("show_grid", True),
            alternate_row_colors=config_dict.get("alternate_row_colors", True),
            created_time=config_dict.get("created_time", ""),
            modified_time=config_dict.get("modified_time", "")
        )

    def get_available_configurations(self) -> List[str]:
        """
        获取可用的配置列表

        Returns:
            List[str]: 配置名称列表
        """
        configs = []

        # 扫描配置目录
        for config_file in self.config_dir.glob("*.json"):
            configs.append(config_file.stem)

        return sorted(configs)

    def delete_configuration(self, config_name: str) -> bool:
        """
        删除配置

        Args:
            config_name: 配置名称

        Returns:
            bool: 删除是否成功
        """
        try:
            config_file = self.config_dir / f"{config_name}.json"
            if config_file.exists():
                config_file.unlink()

                # 从缓存中移除
                if config_name in self._config_cache:
                    del self._config_cache[config_name]

                logger.info(f"==liuq debug== 配置删除成功: {config_name}")
                return True
            else:
                logger.warning(f"==liuq debug== 配置文件不存在: {config_name}")
                return False

        except Exception as e:
            logger.error(f"==liuq debug== 删除配置失败: {e}")
            return False

    def export_configuration(self, config_name: str, export_path: Path) -> bool:
        """
        导出配置到指定路径

        Args:
            config_name: 配置名称
            export_path: 导出路径

        Returns:
            bool: 导出是否成功
        """
        try:
            config = self.load_configuration(config_name)
            config_dict = self._config_to_dict(config)

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"==liuq debug== 配置导出成功: {export_path}")
            return True

        except Exception as e:
            logger.error(f"==liuq debug== 导出配置失败: {e}")
            return False

    def import_configuration(self, import_path: Path, config_name: Optional[str] = None) -> bool:
        """
        从指定路径导入配置

        Args:
            import_path: 导入路径
            config_name: 新配置名称，None则使用文件中的名称

        Returns:
            bool: 导入是否成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)

            config = self._dict_to_config(config_dict)

            if config_name:
                config.config_name = config_name

            return self.save_configuration(config.config_name, config)

        except Exception as e:
            logger.error(f"==liuq debug== 导入配置失败: {e}")
            return False


# 全局表格列管理器实例
table_column_manager = TableColumnManager()

logger.info("==liuq debug== 表格列管理器模块加载完成")
