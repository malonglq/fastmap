#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map表格编辑器

负责Map表格的编辑功能

作者: AI Assistant
日期: 2025-08-25
"""

import logging
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QDoubleValidator

from core.models.map_data import MapPoint, BaseBoundary
from core.interfaces.xml_field_definition import TableColumnDefinition
from core.services.shared.field_registry_service import field_registry

logger = logging.getLogger(__name__)


class MapTableEditor(QObject):
    """Map表格编辑器"""
    
    # 信号定义
    data_changed = pyqtSignal(object, str, object)  # 数据对象、字段名、新值
    
    def __init__(self, table_widget):
        super().__init__()
        self.table_widget = table_widget
        self.editing_enabled = False
        self.column_definitions = []
        
    def set_column_definitions(self, column_definitions):
        """设置列定义"""
        self.column_definitions = column_definitions
        
    def enable_cell_editing(self, enabled: bool):
        """启用/禁用单元格编辑"""
        self.editing_enabled = enabled
        
        if enabled:
            self.table_widget.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        else:
            self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
            
        logger.info(f"单元格编辑状态: {'启用' if enabled else '禁用'}")
        
    def on_item_changed(self, item: QTableWidgetItem):
        """单元格内容改变事件"""
        if not self.editing_enabled:
            return
            
        row = item.row()
        col = item.column()
        
        if col >= len(self.column_definitions):
            return
            
        column_def = self.column_definitions[col]
        new_value = item.text()
        
        # 获取数据对象
        data_object = item.data(Qt.UserRole)
        if not data_object:
            return
            
        # 验证新值
        if not self._validate_field_value(new_value, column_def):
            # 恢复原值
            original_value = self._get_original_value(data_object, column_def.field_id)
            item.setText(str(original_value) if original_value is not None else "")
            return
            
        # 更新数据
        try:
            if self._update_field_value(data_object, column_def.field_id, new_value):
                self.data_changed.emit(data_object, column_def.field_id, new_value)
                logger.info(f"字段更新成功: {column_def.field_id} = {new_value}")
            else:
                # 更新失败，恢复原值
                original_value = self._get_original_value(data_object, column_def.field_id)
                item.setText(str(original_value) if original_value is not None else "")
                
        except Exception as e:
            logger.error(f"字段更新失败: {e}")
            QMessageBox.critical(self.table_widget, "错误", f"更新字段失败: {str(e)}")
            
            # 恢复原值
            original_value = self._get_original_value(data_object, column_def.field_id)
            item.setText(str(original_value) if original_value is not None else "")
            
    def _validate_field_value(self, value: str, column_def: TableColumnDefinition) -> bool:
        """验证字段值"""
        if not value.strip():
            return True  # 空值允许
            
        # 优先从字段注册表获取字段类型进行校验，避免依赖列定义自身的field_type
        try:
            field_def = field_registry.get_field_by_id(column_def.field_id)
            ftype = getattr(field_def, 'field_type', None)
        except Exception:
            field_def = None
            ftype = None

        if ftype in ('float', 'number') or str(ftype).lower() in ('float', 'number'):
            try:
                float(value)
                return True
            except ValueError:
                return False
        elif str(ftype).lower() in ('boolean', 'bool'):
            return value.lower() in ['true', 'false', '是', '否', '1', '0']

        # 默认放行，由具体字段更新器进行二次校验
        return True

    def _update_field_value(self, data_object, field_id: str, new_value: str) -> bool:
        """更新字段值"""
        try:
            if isinstance(data_object, MapPoint):
                return self._update_map_point_field(data_object, field_id, new_value)
            elif isinstance(data_object, BaseBoundary):
                return self._update_base_boundary_field(data_object, field_id, new_value)
            return False
            
        except Exception as e:
            logger.error(f"更新字段值失败: {field_id} = {new_value}, 错误: {e}")
            return False
            
    def _update_map_point_field(self, map_point: MapPoint, field_id: str, new_value: str) -> bool:
        """更新Map点字段"""
        try:
            from core.models.map_data import set_map_point_field_value
            return set_map_point_field_value(map_point, field_id, new_value)
        except Exception as e:
            logger.error(f"更新Map点字段失败: {e}")
            return False
            
    def _update_base_boundary_field(self, base_boundary: BaseBoundary, field_id: str, new_value: str) -> bool:
        """更新Base Boundary字段"""
        try:
            # 根据字段类型进行转换
            if field_id in ['x', 'y', 'offset_x', 'offset_y', 'weight']:
                converted_value = float(new_value)
            elif field_id in ['bv_range', 'ir_range', 'cct_range']:
                # 范围字段格式为 "min,max"
                parts = new_value.split(',')
                if len(parts) == 2:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())
                    converted_value = (min_val, max_val)
                else:
                    return False
            elif field_id == 'detect_flag':
                converted_value = new_value.lower() in ['true', '是', '1']
            else:
                converted_value = new_value
                
            # 设置字段值
            setattr(base_boundary, field_id, converted_value)
            return True
            
        except Exception as e:
            logger.error(f"更新Base Boundary字段失败: {e}")
            return False
            
    def _get_original_value(self, data_object, field_id: str) -> Any:
        """获取原始值"""
        try:
            if isinstance(data_object, MapPoint):
                from core.models.map_data import get_map_point_field_value
                return get_map_point_field_value(data_object, field_id)
            elif isinstance(data_object, BaseBoundary):
                return getattr(data_object, field_id, None)
            return None
        except Exception as e:
            logger.error(f"获取原始值失败: {e}")
            return None