#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map表格样式管理器

负责Map表格的样式和格式化功能

作者: AI Assistant
日期: 2025-08-25
"""

import logging
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QBrush

from core.models.map_data import MapPoint, BaseBoundary
from utils.white_points import REFERENCE_INTERVALS

logger = logging.getLogger(__name__)


class MapTableStyler:
    """Map表格样式管理器"""
    
    def __init__(self, table_widget):
        self.table_widget = table_widget
        self.style_config = {
            'base_boundary_bg': QColor(240, 240, 240),
            'base_boundary_font': QFont('Arial', 9, QFont.Bold),
            'header_bg': QColor(220, 220, 220),
            'header_font': QFont('Arial', 9, QFont.Bold),
            'alternating_row_colors': True,
            'grid_style': Qt.SolidLine
        }
        
    def apply_table_style(self):
        """应用表格样式"""
        # 设置表头样式
        header = self.table_widget.horizontalHeader()
        header.setStyleSheet(f"""
            QHeaderView::section {{
                background-color: {self.style_config['header_bg'].name()};
                color: black;
                padding: 5px;
                border: 1px solid #ccc;
                font-weight: bold;
            }}
        """)
        
        # 设置交替行颜色
        if self.style_config['alternating_row_colors']:
            self.table_widget.setAlternatingRowColors(True)
            self.table_widget.setStyleSheet("""
                QTableWidget {
                    alternate-background-color: #f8f8f8;
                    background-color: white;
                    gridline-color: #ddd;
                }
            """)
            
        # 设置网格线
        self.table_widget.setShowGrid(True)
        self.table_widget.setGridStyle(self.style_config['grid_style'])
        
        # 设置选择行为
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        
        logger.debug("表格样式应用完成")
        
    def apply_row_styles(self):
        """应用行样式"""
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, 0)
            if item:
                data_object = item.data(Qt.UserRole)
                
                if isinstance(data_object, BaseBoundary):
                    self._apply_base_boundary_style(row)
                elif isinstance(data_object, MapPoint):
                    self._apply_map_point_style(row, data_object)
                    
    def _apply_base_boundary_style(self, row: int):
        """应用Base Boundary行样式"""
        font = self.style_config['base_boundary_font']
        bg_color = self.style_config['base_boundary_bg']
        
        # 设置整行的样式
        for col in range(self.table_widget.columnCount()):
            item = self.table_widget.item(row, col)
            if item:
                item.setFont(font)
                item.setBackground(QBrush(bg_color))
                item.setForeground(QBrush(Qt.black))
                
        logger.debug(f"应用Base Boundary行样式: 第{row}行")
        
    def _apply_map_point_style(self, row: int, map_point: MapPoint):
        """应用Map点行样式"""
        # 根据权重设置样式
        if hasattr(map_point, 'weight') and map_point.weight:
            if map_point.weight >= 0.8:
                # 高权重：深色背景
                bg_color = QColor(255, 245, 235)
            elif map_point.weight >= 0.5:
                # 中权重：浅色背景
                bg_color = QColor(245, 255, 235)
            else:
                # 低权重：默认背景
                bg_color = None
                
            if bg_color:
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item:
                        item.setBackground(QBrush(bg_color))
                        
        # 根据色温跨度设置特殊样式
        if hasattr(map_point, 'temperature_span_names') and map_point.temperature_span_names:
            span_names = map_point.temperature_span_names
            if isinstance(span_names, list) and span_names:
                # 如果有特定的色温跨度，设置特殊样式
                self._apply_temperature_span_style(row, span_names)
                
    def _apply_temperature_span_style(self, row: int, span_names: list):
        """应用色温跨度样式"""
        # 检查是否包含关键色温跨度
        key_spans = ['D65-D50', 'D50-F', 'F-A']
        for span in key_spans:
            if span in span_names:
                # 设置特殊样式
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item:
                        item.setFont(QFont('Arial', 9, QFont.Bold))
                        item.setForeground(QBrush(Qt.blue))
                break
                
    def apply_cell_style(self, row: int, col: int, style_config: Dict[str, Any]):
        """应用单元格样式"""
        item = self.table_widget.item(row, col)
        if not item:
            return
            
        # 应用字体
        if 'font' in style_config:
            item.setFont(style_config['font'])
            
        # 应用背景色
        if 'background_color' in style_config:
            item.setBackground(QBrush(style_config['background_color']))
            
        # 应用前景色
        if 'foreground_color' in style_config:
            item.setForeground(QBrush(style_config['foreground_color']))
            
        # 应用对齐方式
        if 'alignment' in style_config:
            item.setTextAlignment(style_config['alignment'])
            
    def highlight_cell(self, row: int, col: int, highlight_type: str = 'warning'):
        """高亮单元格"""
        item = self.table_widget.item(row, col)
        if not item:
            return
            
        if highlight_type == 'warning':
            item.setBackground(QBrush(QColor(255, 255, 200)))
            item.setForeground(QBrush(Qt.black))
        elif highlight_type == 'error':
            item.setBackground(QBrush(QColor(255, 200, 200)))
            item.setForeground(QBrush(Qt.black))
        elif highlight_type == 'success':
            item.setBackground(QBrush(QColor(200, 255, 200)))
            item.setForeground(QBrush(Qt.black))
            
    def clear_highlight(self, row: int, col: int):
        """清除高亮"""
        item = self.table_widget.item(row, col)
        if item:
            # 恢复默认样式
            item.setBackground(QBrush())
            item.setForeground(QBrush())
            
    def update_style_config(self, config: Dict[str, Any]):
        """更新样式配置"""
        self.style_config.update(config)
        self.apply_table_style()
        self.apply_row_styles()
        
    def get_style_config(self) -> Dict[str, Any]:
        """获取当前样式配置"""
        return self.style_config.copy()
        
    def reset_styles(self):
        """重置所有样式"""
        # 清除所有单元格的样式
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    item.setFont(QFont())
                    item.setBackground(QBrush())
                    item.setForeground(QBrush())
                    
        # 重新应用基本样式
        self.apply_table_style()
        self.apply_row_styles()
        
        logger.debug("样式重置完成")