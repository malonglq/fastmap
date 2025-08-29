#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map表格筛选器

负责Map表格的筛选功能

作者: AI Assistant
日期: 2025-08-25
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from PyQt5.QtWidgets import QLineEdit, QLabel, QComboBox, QTableWidget
from PyQt5.QtCore import Qt

from core.models.map_data import MapPoint, BaseBoundary, MapConfiguration
from core.services.map_analysis.temperature_span_analyzer import TemperatureSpanAnalyzer
from utils.white_points import REFERENCE_INTERVALS, is_in_temperature_sector

logger = logging.getLogger(__name__)


class MapTableFilter:
    """Map表格筛选器"""

    def __init__(self, table_widget: QTableWidget):
        self.table_widget = table_widget
        # 基础控件
        self.filter_input: Optional[QLineEdit] = None
        self.status_label: Optional[QLabel] = None
        self.column_combo: Optional[QComboBox] = None
        # 扩展控件
        self.interval_combo: Optional[QComboBox] = None
        self.bv_min_edit: Optional[QLineEdit] = None
        self.bv_max_edit: Optional[QLineEdit] = None
        # 状态
        self.original_data = []
        self.current_filter = ""
        self.selected_interval: Optional[Tuple[str, str]] = None
        self.bv_min_value: Optional[float] = None
        self.bv_max_value: Optional[float] = None
        self.configuration: Optional[MapConfiguration] = None
        self.temperature_spans: Dict[str, Dict[str, Any]] = {}
        self._bb_coords: Tuple[float, float] = (0.0, 0.0)

    def set_configuration(self, configuration: MapConfiguration):
        try:
            self.configuration = configuration
            try:
                self._bb_coords = (
                    float(getattr(configuration.base_boundary, 'rpg', 0.0)) if configuration and configuration.base_boundary else 0.0,
                    float(getattr(configuration.base_boundary, 'bpg', 0.0)) if configuration and configuration.base_boundary else 0.0,
                )
            except Exception:
                self._bb_coords = (0.0, 0.0)
            try:
                analyzer = TemperatureSpanAnalyzer(configuration)
                result = analyzer.analyze()
                self.temperature_spans = result.get('spans_by_map', {}) or {}
            except Exception as _e:
                logger.warning("==liuq debug== 预计算色温段跨度失败: %s", _e)
                self.temperature_spans = {}
        except Exception as e:
            logger.warning("==liuq debug== set_configuration失败: %s", e)

    def set_filter_widgets(self, filter_input: QLineEdit, status_label: QLabel, column_combo: QComboBox = None,
                           interval_combo: QComboBox = None, bv_min_edit: QLineEdit = None, bv_max_edit: QLineEdit = None):
        self.filter_input = filter_input
        self.status_label = status_label
        self.column_combo = column_combo
        self.interval_combo = interval_combo
        self.bv_min_edit = bv_min_edit
        self.bv_max_edit = bv_max_edit
        if self.filter_input:
            self.filter_input.textChanged.connect(self.on_filter_changed)
        if self.interval_combo:
            self.interval_combo.currentIndexChanged.connect(self.on_interval_changed)

    def on_interval_changed(self, idx: int = 0):
        try:
            if not self.interval_combo:
                self.selected_interval = None
                return
            text = (self.interval_combo.currentText() or "").strip()
            if text and text != "全部" and '-' in text:
                # 与 REFERENCE_INTERVALS 一致的 'A-B' 形式
                parts = text.split('-', 1)
                a = parts[0].strip(); b = parts[1].strip()
                self.selected_interval = (a, b)
            else:
                self.selected_interval = None
            logger.info("==liuq debug== 区间选择变更: text='%s' -> selected_interval=%s", text, self.selected_interval)
            self.apply_filters()
        except Exception as e:
            logger.warning("==liuq debug== 处理区间变更失败: %s", e)

    def on_filter_changed(self, text: str):
        self.current_filter = (text or "").lower()
        self.apply_filters()

    def _read_bv_inputs(self):
        """读取BV输入，容错转换为空/非法则视为None"""
        def _to_float(x: str):
            try:
                s = (x or "").strip()
                return float(s) if s != "" else None
            except Exception:
                return None
        if self.bv_min_edit:
            self.bv_min_value = _to_float(self.bv_min_edit.text())
        if self.bv_max_edit:
            self.bv_max_value = _to_float(self.bv_max_edit.text())
        try:
            if self.bv_min_value is not None and self.bv_max_value is not None and self.bv_min_value > self.bv_max_value:
                self.bv_min_value, self.bv_max_value = self.bv_max_value, self.bv_min_value
        except Exception:
            pass

    def apply_filters(self):
        """应用筛选（名称/列 + 区间 + BV 叠加 AND）"""
        if not self.table_widget:
            return
        self._read_bv_inputs()
        filter_text = (self.filter_input.text().lower() if self.filter_input else "").strip()
        visible_rows = 0

        filter_column = -1
        if self.column_combo and self.column_combo.currentIndex() > 0:
            filter_column = self.column_combo.currentIndex() - 1
        logger.info("==liuq debug== 开始筛选: filter_text='%s' column_index=%d selected_interval=%s bv=[%s,%s]",
                    filter_text, filter_column, self.selected_interval, self.bv_min_value, self.bv_max_value)

        def _item_text(row: int, col: int) -> str:
            try:
                it = self.table_widget.item(row, col)
                if it is None:
                    return ""
                txt = it.text()
                return txt if txt else ""
            except Exception:
                return ""

        for row in range(self.table_widget.rowCount()):
            matched_col = -1
            if not filter_text:
                name_match = True
            else:
                if filter_column == -1:
                    name_match = False
                    for col in range(self.table_widget.columnCount()):
                        txt = _item_text(row, col).lower()
                        if filter_text in txt:
                            name_match = True
                            matched_col = col
                            break
                else:
                    txt = _item_text(row, filter_column).lower()
                    name_match = (filter_text in txt)
                    matched_col = filter_column if name_match else -1

            first_item = self.table_widget.item(row, 0)
            mp = first_item.data(Qt.UserRole) if first_item else None

            # 区间匹配
            interval_match = True
            if self.selected_interval and isinstance(mp, MapPoint):
                try:
                    a, b = self.selected_interval
                    span = self.temperature_spans.get(getattr(mp, 'alias_name', ''), {})
                    names = span.get('interval_names', [])
                    if names:
                        interval_match = (f"{a}-{b}" in names)
                except Exception:
                    interval_match = True

            # BV匹配（子集关系）：筛选区间 [fmin, fmax] 必须被 Map 区间 [bv_min, bv_max] 完全包含
            # 正确子集条件：bv_min <= fmin 且 fmax <= bv_max
            # 仅输入下限时：判定 fmin >= bv_min；仅输入上限时：判定 fmax <= bv_max
            bv_match = True
            if isinstance(mp, MapPoint) and (self.bv_min_value is not None or self.bv_max_value is not None):
                try:
                    bv_min, bv_max = getattr(mp, 'bv_range', (None, None))
                    if bv_min is None or bv_max is None:
                        bv_match = False
                    else:
                        fmin = self.bv_min_value if self.bv_min_value is not None else None
                        fmax = self.bv_max_value if self.bv_max_value is not None else None
                        cond_lower = True if fmin is None else (fmin >= bv_min)
                        cond_upper = True if fmax is None else (fmax <= bv_max)
                        if not (cond_lower and cond_upper):
                            logger.info("==liuq debug== BV子集不匹配: item=[%s,%s], filter=[%s,%s]", bv_min, bv_max, self.bv_min_value, self.bv_max_value)
                            bv_match = False
                except Exception as e:
                    logger.warning("==liuq debug== BV子集判定异常: %s", e)
                    bv_match = False

            show_row = name_match and interval_match and bv_match
            self.table_widget.setRowHidden(row, not show_row)
            if show_row:
                visible_rows += 1

        if self.status_label:
            total_rows = self.table_widget.rowCount()
            self.status_label.setText(f"显示: {visible_rows}/{total_rows} 行")

        logger.info("==liuq debug== 应用筛选: text='%s', interval=%s, bv=[%s,%s], 可见=%d", filter_text, self.selected_interval, self.bv_min_value, self.bv_max_value, visible_rows)

    def reset_filters(self):
        """重置筛选"""
        if self.filter_input:
            self.filter_input.clear()
            
        # 显示所有行
        for row in range(self.table_widget.rowCount()):
            self.table_widget.setRowHidden(row, False)
            
        # 更新状态标签
        if self.status_label:
            total_rows = self.table_widget.rowCount()
            self.status_label.setText(f"显示: {total_rows}/{total_rows} 行")
            
        logger.debug("重置筛选")

    def get_visible_map_points(self) -> List[MapPoint]:
        """获取可见的Map点"""
        visible_points = []
        
        for row in range(self.table_widget.rowCount()):
            if not self.table_widget.isRowHidden(row):
                item = self.table_widget.item(row, 0)
                if item:
                    data_object = item.data(Qt.UserRole)
                    if isinstance(data_object, MapPoint):
                        visible_points.append(data_object)
                        
        return visible_points
        
    def get_visible_base_boundary(self) -> Optional[BaseBoundary]:
        """获取可见的Base Boundary"""
        for row in range(self.table_widget.rowCount()):
            if not self.table_widget.isRowHidden(row):
                item = self.table_widget.item(row, 0)
                if item:
                    data_object = item.data(Qt.UserRole)
                    if isinstance(data_object, BaseBoundary):
                        return data_object
        return None