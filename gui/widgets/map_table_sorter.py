#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map表格排序器

负责Map表格的排序功能

作者: AI Assistant
日期: 2025-08-25
"""

import logging
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt, QSortFilterProxyModel

from core.models.map_data import MapPoint, BaseBoundary
from utils.natural_sort import natural_sort_key

logger = logging.getLogger(__name__)


class MapTableSorter:
    """Map表格排序器"""
    
    def __init__(self, table_widget: QTableWidget):
        self.table_widget = table_widget
        self.current_sort_column = -1
        self.current_sort_order = Qt.AscendingOrder
        self.sort_cache = {}
        
    def setup_header_sorting(self, header: QHeaderView):
        """设置表头排序"""
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.on_header_clicked)
        
    def on_header_clicked(self, column: int):
        """表头点击事件"""
        if self.current_sort_column == column:
            # 切换排序方向
            self.current_sort_order = Qt.DescendingOrder if self.current_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            # 新的排序列
            self.current_sort_column = column
            self.current_sort_order = Qt.AscendingOrder
            
        self.apply_sort()
        
    def apply_sort(self):
        """应用排序"""
        if self.current_sort_column < 0:
            return
            
        # 收集所有行数据
        row_data = []
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, self.current_sort_column)
            if item:
                text = item.text()
                data_object = item.data(Qt.UserRole)
                row_data.append((text, row, data_object))
                
        # 根据数据类型选择排序方式
        if self._is_numeric_column(self.current_sort_column):
            row_data.sort(key=self._numeric_sort_key, reverse=self.current_sort_order == Qt.DescendingOrder)
        else:
            row_data.sort(key=self._text_sort_key, reverse=self.current_sort_order == Qt.DescendingOrder)
            
        # 重新排列行
        self._reorder_rows(row_data)
        
        # 更新表头指示器
        self._update_sort_indicator()
        
        logger.debug(f"排序完成：列{self.current_sort_column}，{'降序' if self.current_sort_order == Qt.DescendingOrder else '升序'}")
        
    def _is_numeric_column(self, column: int) -> bool:
        """检查是否为数字列"""
        # 检查该列的所有值是否可以转换为数字
        for row in range(self.table_widget.rowCount()):
            item = self.table_widget.item(row, column)
            if item and item.text().strip():
                try:
                    float(item.text().strip())
                except ValueError:
                    return False
        return True
        
    def _numeric_sort_key(self, item):
        """数字排序键"""
        text, row, data_object = item
        if text.strip():
            try:
                return float(text.strip())
            except ValueError:
                return float('-inf')
        return float('-inf')
        
    def _text_sort_key(self, item):
        """文本排序键（自然排序键）"""
        text, row, data_object = item
        try:
            return natural_sort_key(text)
        except Exception:
            # 回退为普通字符串
            return [str(text)]

    def _reorder_rows(self, sorted_data):
        """重新排列行"""
        # 获取当前所有行的数据
        all_row_data = []
        for row in range(self.table_widget.rowCount()):
            row_items = []
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    row_items.append({
                        'text': item.text(),
                        'data': item.data(Qt.UserRole),
                        'flags': item.flags()
                    })
                else:
                    row_items.append(None)
            all_row_data.append(row_items)
            
        # 清空表格
        self.table_widget.setRowCount(0)
        
        # 按排序后的顺序重新添加行
        for _, original_row, _ in sorted_data:
            if 0 <= original_row < len(all_row_data):
                self.table_widget.insertRow(self.table_widget.rowCount())
                new_row = self.table_widget.rowCount() - 1
                
                # 复制行数据
                for col, item_data in enumerate(all_row_data[original_row]):
                    if item_data:
                        new_item = QTableWidgetItem(item_data['text'])
                        new_item.setData(Qt.UserRole, item_data['data'])
                        new_item.setFlags(item_data['flags'])
                        self.table_widget.setItem(new_row, col, new_item)
                        
    def _update_sort_indicator(self):
        """更新排序指示器"""
        header = self.table_widget.horizontalHeader()
        if hasattr(header, 'setSortIndicator'):
            header.setSortIndicator(self.current_sort_column, self.current_sort_order)
            
    def reset_sort(self):
        """重置排序"""
        self.current_sort_column = -1
        self.current_sort_order = Qt.AscendingOrder
        
        # 清除排序指示器
        header = self.table_widget.horizontalHeader()
        if hasattr(header, 'setSortIndicator'):
            header.setSortIndicator(-1, Qt.AscendingOrder)
            
        logger.debug("重置排序")
        
    def get_sort_state(self) -> Dict[str, Any]:
        """获取排序状态"""
        return {
            'column': self.current_sort_column,
            'order': 'ascending' if self.current_sort_order == Qt.AscendingOrder else 'descending'
        }
        
    def set_sort_state(self, state: Dict[str, Any]):
        """设置排序状态"""
        try:
            self.current_sort_column = state.get('column', -1)
            self.current_sort_order = Qt.AscendingOrder if state.get('order') == 'ascending' else Qt.DescendingOrder
            
            if self.current_sort_column >= 0:
                self.apply_sort()
                
        except Exception as e:
            logger.error(f"设置排序状态失败: {e}")
            self.reset_sort()