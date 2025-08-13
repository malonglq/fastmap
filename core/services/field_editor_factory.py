#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段编辑器工厂
==liuq debug== FastMapV2 字段编辑器工厂实现

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 16:15:00 +08:00; Reason: P1-LD-007-002 实现字段编辑器工厂; Principle_Applied: 工厂模式;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 为不同字段类型提供合适的编辑器组件
"""

import logging
from typing import Dict, Type, Optional, Any, Callable
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QComboBox, QSlider, QDateEdit, QTimeEdit
)
from PyQt5.QtCore import Qt

from core.interfaces.xml_field_definition import XMLFieldDefinition, FieldType

logger = logging.getLogger(__name__)


class FieldEditorFactory:
    """
    字段编辑器工厂
    
    根据字段定义创建合适的编辑器组件，支持：
    - 基础数据类型的编辑器
    - 自定义编辑器注册
    - 编辑器配置和样式设置
    - 验证规则集成
    
    设计特点：
    - 工厂模式，支持编辑器类型扩展
    - 基于字段定义自动选择最佳编辑器
    - 支持自定义编辑器注册
    - 提供统一的编辑器配置接口
    """
    
    def __init__(self):
        """初始化字段编辑器工厂"""
        self._editor_registry: Dict[str, Type[QWidget]] = {}
        self._configurators: Dict[Type[QWidget], Callable] = {}
        
        # 注册默认编辑器
        self._register_default_editors()
        
        logger.info("==liuq debug== 字段编辑器工厂初始化完成")
    
    def _register_default_editors(self):
        """注册默认编辑器"""
        # 基础编辑器映射
        default_editors = {
            'string_line_edit': QLineEdit,
            'integer_spin_box': QSpinBox,
            'float_double_spin_box': QDoubleSpinBox,
            'boolean_check_box': QCheckBox,
            'enum_combo_box': QComboBox,
            'range_slider': QSlider,
        }
        
        for editor_name, editor_class in default_editors.items():
            self._editor_registry[editor_name] = editor_class
        
        # 注册配置器
        self._configurators[QLineEdit] = self._configure_line_edit
        self._configurators[QSpinBox] = self._configure_spin_box
        self._configurators[QDoubleSpinBox] = self._configure_double_spin_box
        self._configurators[QCheckBox] = self._configure_check_box
        self._configurators[QComboBox] = self._configure_combo_box
        self._configurators[QSlider] = self._configure_slider
        

    
    def create_editor(self, field_definition: XMLFieldDefinition, parent: Optional[QWidget] = None) -> QWidget:
        """
        创建字段编辑器
        
        Args:
            field_definition: 字段定义
            parent: 父组件
            
        Returns:
            QWidget: 编辑器组件
        """
        try:
            # 确定编辑器类型
            editor_class = self._determine_editor_class(field_definition)
            
            # 创建编辑器实例
            editor = editor_class(parent)
            
            # 配置编辑器
            self._configure_editor(editor, field_definition)
            

            return editor
            
        except Exception as e:
            logger.error(f"==liuq debug== 创建编辑器失败: {field_definition.field_id} - {e}")
            # 返回默认的QLineEdit作为后备
            return QLineEdit(parent)
    
    def _determine_editor_class(self, field_definition: XMLFieldDefinition) -> Type[QWidget]:
        """
        确定编辑器类型
        
        Args:
            field_definition: 字段定义
            
        Returns:
            Type[QWidget]: 编辑器类
        """
        # 优先使用自定义编辑器
        if field_definition.custom_editor and field_definition.custom_editor in self._editor_registry:
            return self._editor_registry[field_definition.custom_editor]
        
        # 根据字段类型选择默认编辑器
        field_type = field_definition.field_type
        
        if field_type == FieldType.STRING:
            return QLineEdit
        elif field_type == FieldType.INTEGER:
            return QSpinBox
        elif field_type == FieldType.FLOAT:
            return QDoubleSpinBox
        elif field_type == FieldType.BOOLEAN:
            return QCheckBox
        else:
            return QLineEdit  # 默认编辑器
    
    def _configure_editor(self, editor: QWidget, field_definition: XMLFieldDefinition):
        """
        配置编辑器
        
        Args:
            editor: 编辑器组件
            field_definition: 字段定义
        """
        try:
            # 设置基础属性
            if hasattr(editor, 'setToolTip') and field_definition.description:
                editor.setToolTip(field_definition.description)
            
            if hasattr(editor, 'setEnabled'):
                editor.setEnabled(field_definition.is_editable)
            
            # 使用专用配置器
            editor_type = type(editor)
            if editor_type in self._configurators:
                self._configurators[editor_type](editor, field_definition)
            

            
        except Exception as e:
            logger.error(f"==liuq debug== 编辑器配置失败: {field_definition.field_id} - {e}")
    
    def _configure_line_edit(self, editor: QLineEdit, field_definition: XMLFieldDefinition):
        """配置QLineEdit编辑器"""
        try:
            # 设置占位符文本
            if field_definition.default_value:
                editor.setPlaceholderText(str(field_definition.default_value))
            
            # 设置最大长度（如果有验证规则）
            for rule in field_definition.validation_rules:
                if hasattr(rule, 'max_length') and rule.max_length:
                    editor.setMaxLength(rule.max_length)
                    break
            
            # 设置输入掩码（如果需要）
            if field_definition.field_id in ['x', 'y', 'offset_x', 'offset_y', 'weight']:
                # 数值字段，允许小数
                pass  # QLineEdit默认允许所有字符
            
        except Exception as e:
            logger.warning(f"==liuq debug== 配置QLineEdit失败: {e}")
    
    def _configure_spin_box(self, editor: QSpinBox, field_definition: XMLFieldDefinition):
        """配置QSpinBox编辑器"""
        try:
            # 设置范围
            editor.setRange(-999999, 999999)  # 默认范围
            
            # 从验证规则中获取范围
            for rule in field_definition.validation_rules:
                if hasattr(rule, 'min_value') and rule.min_value is not None:
                    editor.setMinimum(int(rule.min_value))
                if hasattr(rule, 'max_value') and rule.max_value is not None:
                    editor.setMaximum(int(rule.max_value))
            
            # 设置默认值
            if field_definition.default_value is not None:
                try:
                    editor.setValue(int(field_definition.default_value))
                except (ValueError, TypeError):
                    pass
            
            # 设置步长
            editor.setSingleStep(1)
            
        except Exception as e:
            logger.warning(f"==liuq debug== 配置QSpinBox失败: {e}")
    
    def _configure_double_spin_box(self, editor: QDoubleSpinBox, field_definition: XMLFieldDefinition):
        """配置QDoubleSpinBox编辑器"""
        try:
            # 设置范围
            editor.setRange(-999999.0, 999999.0)  # 默认范围
            
            # 设置精度
            editor.setDecimals(3)  # 默认3位小数
            
            # 从验证规则中获取范围
            for rule in field_definition.validation_rules:
                if hasattr(rule, 'min_value') and rule.min_value is not None:
                    editor.setMinimum(float(rule.min_value))
                if hasattr(rule, 'max_value') and rule.max_value is not None:
                    editor.setMaximum(float(rule.max_value))
            
            # 设置默认值
            if field_definition.default_value is not None:
                try:
                    editor.setValue(float(field_definition.default_value))
                except (ValueError, TypeError):
                    pass
            
            # 设置步长
            editor.setSingleStep(0.1)
            
            # 特殊字段的精度设置
            if field_definition.field_id in ['x', 'y', 'offset_x', 'offset_y']:
                editor.setDecimals(3)
                editor.setSingleStep(0.001)
            elif field_definition.field_id == 'weight':
                editor.setDecimals(3)
                editor.setSingleStep(0.1)
            
        except Exception as e:
            logger.warning(f"==liuq debug== 配置QDoubleSpinBox失败: {e}")
    
    def _configure_check_box(self, editor: QCheckBox, field_definition: XMLFieldDefinition):
        """配置QCheckBox编辑器"""
        try:
            # 设置文本
            editor.setText(field_definition.display_name)
            
            # 设置默认值
            if field_definition.default_value is not None:
                try:
                    editor.setChecked(bool(field_definition.default_value))
                except (ValueError, TypeError):
                    pass
            
        except Exception as e:
            logger.warning(f"==liuq debug== 配置QCheckBox失败: {e}")
    
    def _configure_combo_box(self, editor: QComboBox, field_definition: XMLFieldDefinition):
        """配置QComboBox编辑器"""
        try:
            # 设置为可编辑
            editor.setEditable(True)
            
            # 添加常用选项（如果有的话）
            if field_definition.field_id == 'alias_name':
                common_names = [
                    "Indoor_BV_4000", "Outdoor_IR_2000", "Night_Scene",
                    "Daylight_Auto", "Tungsten_3200K", "Fluorescent_4000K"
                ]
                editor.addItems(common_names)
            
            # 设置默认值
            if field_definition.default_value is not None:
                editor.setCurrentText(str(field_definition.default_value))
            
        except Exception as e:
            logger.warning(f"==liuq debug== 配置QComboBox失败: {e}")
    
    def _configure_slider(self, editor: QSlider, field_definition: XMLFieldDefinition):
        """配置QSlider编辑器"""
        try:
            # 设置方向
            editor.setOrientation(Qt.Horizontal)
            
            # 设置范围
            editor.setRange(0, 100)  # 默认范围
            
            # 从验证规则中获取范围
            for rule in field_definition.validation_rules:
                if hasattr(rule, 'min_value') and rule.min_value is not None:
                    editor.setMinimum(int(rule.min_value))
                if hasattr(rule, 'max_value') and rule.max_value is not None:
                    editor.setMaximum(int(rule.max_value))
            
            # 设置默认值
            if field_definition.default_value is not None:
                try:
                    editor.setValue(int(field_definition.default_value))
                except (ValueError, TypeError):
                    pass
            
        except Exception as e:
            logger.warning(f"==liuq debug== 配置QSlider失败: {e}")
    
    def register_custom_editor(self, editor_name: str, editor_class: Type[QWidget], 
                              configurator: Optional[Callable] = None):
        """
        注册自定义编辑器
        
        Args:
            editor_name: 编辑器名称
            editor_class: 编辑器类
            configurator: 配置器函数
        """
        try:
            self._editor_registry[editor_name] = editor_class
            
            if configurator:
                self._configurators[editor_class] = configurator
            
            logger.info(f"==liuq debug== 注册自定义编辑器: {editor_name} -> {editor_class.__name__}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 注册自定义编辑器失败: {e}")
    
    def get_registered_editors(self) -> Dict[str, Type[QWidget]]:
        """
        获取已注册的编辑器
        
        Returns:
            Dict[str, Type[QWidget]]: 编辑器注册表
        """
        return self._editor_registry.copy()


# 全局字段编辑器工厂实例
field_editor_factory = FieldEditorFactory()

logger.info("==liuq debug== 字段编辑器工厂模块加载完成")
