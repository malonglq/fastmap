#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map表格数据管理器

负责Map表格数据的加载、存储和转换功能

作者: AI Assistant
日期: 2025-08-25
"""

import logging
from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from core.models.map_data import MapConfiguration, MapPoint, BaseBoundary
from core.interfaces.xml_field_definition import TableColumnDefinition, TableConfiguration, FieldType
from core.services.shared.field_registry_service import field_registry
from core.services.map_analysis.xml_writer_service import format_number_for_xml
from utils.white_points import is_in_temperature_interval, is_in_temperature_sector, REFERENCE_INTERVALS

logger = logging.getLogger(__name__)


class MapTableDataManager:
    """Map表格数据管理器"""
    
    def __init__(self, table_widget: QTableWidget):
        self.table_widget = table_widget
        self.configuration: Optional[MapConfiguration] = None
        self.column_definitions: List[TableColumnDefinition] = []
        
    def set_configuration(self, configuration: MapConfiguration):
        """设置Map配置"""
        self.configuration = configuration
        self._setup_columns()
        
    def _setup_columns(self):
        """设置表格列"""
        if not self.configuration:
            return
            
        # 从动态列管理器获取当前表格列配置，避免依赖 MapConfiguration 自身携带列配置
        try:
            from core.managers.table_column_manager import TableColumnManager
            table_column_manager = TableColumnManager()
            table_config = table_column_manager.get_current_configuration()
            self.column_definitions = list(table_config.get_visible_columns())
        except Exception as _e:
            logger.warning(f"==liuq debug== 获取表格列配置失败，退回空列: {_e}")
            self.column_definitions = []

        # 若无可见列，使用最小安全列集作为兜底，确保表格可见
        if not self.column_definitions:
            from core.interfaces.xml_field_definition import TableColumnDefinition
            self.column_definitions = [
                TableColumnDefinition(column_id='col_alias', field_id='alias_name', display_name='Alias', width=160),
                TableColumnDefinition(column_id='col_x', field_id='x', display_name='X', width=80),
                TableColumnDefinition(column_id='col_y', field_id='y', display_name='Y', width=80),
                TableColumnDefinition(column_id='col_weight', field_id='weight', display_name='Weight', width=80),
            ]

        # 设置列数和标题
        self.table_widget.setColumnCount(len(self.column_definitions))
        headers = [col.display_name for col in self.column_definitions]
        self.table_widget.setHorizontalHeaderLabels(headers)

        # 设置列宽
        for i, col in enumerate(self.column_definitions):
            if getattr(col, 'width', None):
                self.table_widget.setColumnWidth(i, col.width)

    def populate_table(self) -> int:
        """填充表格数据"""
        if not self.configuration:
            return 0
            
        self.table_widget.setRowCount(0)
        
        # 添加Map点
        map_points = self.configuration.map_points
        for i, map_point in enumerate(map_points):
            self.table_widget.insertRow(i)
            self._populate_map_point_row(i, map_point)
            
        # 添加Base Boundary（如果存在）
        try:
            row = len(map_points)
            # 优先使用配置中的 base_boundary_point（MapPoint 形态，更兼容列定义）
            base_boundary_point = getattr(self.configuration, 'base_boundary_point', None)
            if base_boundary_point:
                self.table_widget.insertRow(row)
                self._populate_map_point_row(row, base_boundary_point)
            elif self.configuration.base_boundary:
                # 新架构 BaseBoundary 仅包含 rpg/bpg，适配为临时 MapPoint 行
                from core.models.map_data import MapPoint
                bb = self.configuration.base_boundary
                temp_mp = MapPoint(
                    alias_name='base_boundary0',
                    x=getattr(bb, 'rpg', 0.0),
                    y=getattr(bb, 'bpg', 0.0),
                    offset_x=getattr(bb, 'rpg', 0.0),
                    offset_y=getattr(bb, 'bpg', 0.0),
                    weight=0.0,
                    bv_range=(0.0, 0.0),
                    ir_range=(0.0, 0.0),
                    cct_range=(0.0, 0.0),
                )
                self.table_widget.insertRow(row)
                self._populate_map_point_row(row, temp_mp)
        except Exception as _e:
            logger.warning(f"==liuq debug== 追加BaseBoundary行失败: {_e}")

        logger.info(f"成功填充表格数据，共{len(map_points)}个Map点")
        return self.table_widget.rowCount()

    def _populate_map_point_row(self, row: int, map_point: MapPoint):
        """填充Map点行数据"""
        for col, column_def in enumerate(self.column_definitions):
            value = self._get_map_point_field_value(map_point, column_def.field_id)
            formatted_value = self._format_field_value(value, column_def)
            self._set_table_item(row, col, formatted_value, map_point)
            
    def _populate_base_boundary_row(self, row: int, base_boundary: BaseBoundary):
        """填充Base Boundary行数据"""
        for col, column_def in enumerate(self.column_definitions):
            value = self._get_base_boundary_field_value(base_boundary, column_def.field_id)
            formatted_value = self._format_field_value(value, column_def)
            self._set_table_item(row, col, formatted_value, base_boundary)
            
    def _get_map_point_field_value(self, map_point: MapPoint, field_id: str) -> Any:
        """获取Map点字段值"""
        try:
            from core.models.map_data import get_map_point_field_value
            return get_map_point_field_value(map_point, field_id)
        except Exception as e:
            logger.error(f"获取Map点字段值失败: {field_id}, 错误: {e}")
            return None
            
    def _get_base_boundary_field_value(self, base_boundary: BaseBoundary, field_id: str) -> Any:
        """获取Base Boundary字段值"""
        field_mapping = {
            'alias_name': base_boundary.alias_name,
            'x': base_boundary.x,
            'y': base_boundary.y,
            'offset_x': base_boundary.offset_x,
            'offset_y': base_boundary.offset_y,
            'weight': base_boundary.weight,
            'bv_range': base_boundary.bv_range,
            'ir_range': base_boundary.ir_range,
            'cct_range': base_boundary.cct_range,
            'detect_flag': base_boundary.detect_flag,
            'temperature_span_names': base_boundary.temperature_span_names
        }
        return field_mapping.get(field_id)
        
    def _format_field_value(self, value: Any, column_def: TableColumnDefinition) -> str:
        """格式化字段值（仅用于GUI显示，不改变底层数据）"""
        if value is None:
            return ""

        # 特例：ml 字段显示转换（GUI层 65535->3，65471->2，保持与legacy一致）
        try:
            if getattr(column_def, 'field_id', '') == 'ml':
                try:
                    raw_val = float(value)
                except Exception:
                    raw_val = value
                if raw_val == 65535:
                    return "3"
                elif raw_val == 65471:
                    return "2"
                else:
                    return str(value)
        except Exception:
            pass

        # 通过字段注册表来判定字段类型
        try:
            field_def = field_registry.get_field_by_id(column_def.field_id)
            ftype = getattr(field_def, 'field_type', None)
        except Exception:
            field_def = None
            ftype = None

        # 数值类型格式化
        if ftype in (FieldType.FLOAT, FieldType.INTEGER):
            try:
                return format_number_for_xml(value)
            except Exception:
                return str(value)
        # 布尔类型
        if ftype == FieldType.BOOLEAN:
            try:
                return "是" if bool(value) else "否"
            except Exception:
                return ""

        # 其它类型
        return str(value)

    def _set_table_item(self, row: int, col: int, value: str, data_object):
        """设置表格项"""
        item = QTableWidgetItem(value)
        item.setData(Qt.UserRole, data_object)
        
        # 设置对齐方式（通过字段注册表判断类型）
        if col < len(self.column_definitions):
            column_def = self.column_definitions[col]
            try:
                fdef = field_registry.get_field_by_id(column_def.field_id)
                ftype = getattr(fdef, 'field_type', None)
            except Exception:
                ftype = None
            if ftype in (FieldType.FLOAT, FieldType.INTEGER):
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.table_widget.setItem(row, col, item)

    def get_map_point_by_row(self, row: int) -> Optional[MapPoint]:
        """根据行号获取Map点"""
        if row < 0 or row >= self.table_widget.rowCount():
            return None
            
        item = self.table_widget.item(row, 0)
        if item:
            data_object = item.data(Qt.UserRole)
            if isinstance(data_object, MapPoint):
                return data_object
                
        return None
        
    def get_base_boundary_by_row(self, row: int) -> Optional[BaseBoundary]:
        """根据行号获取Base Boundary"""
        if row < 0 or row >= self.table_widget.rowCount():
            return None
            
        item = self.table_widget.item(row, 0)
        if item:
            data_object = item.data(Qt.UserRole)
            if isinstance(data_object, BaseBoundary):
                return data_object
                
        return None
        
    def refresh_table(self):
        """刷新表格"""
        self.populate_table()
        
    def clear_table(self):
        """清空表格"""
        self.table_widget.setRowCount(0)
        self.configuration = None
        self.column_definitions = []