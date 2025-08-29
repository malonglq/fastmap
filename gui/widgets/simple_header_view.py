#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单表头视图

提供自定义的表头绘制和交互功能

作者: AI Assistant
日期: 2025-08-25
"""

import logging
from typing import Optional
from PyQt5.QtWidgets import QHeaderView, QStyle, QStyleOptionHeader
from PyQt5.QtCore import Qt, QRect, QSize, QPoint
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont

logger = logging.getLogger(__name__)


class SimpleHeaderView(QHeaderView):
    """简单表头视图"""

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setSectionsMovable(False)
        self.setHighlightSections(True)

        # 样式设置
        self._font = QFont('Arial', 9, QFont.Bold)
        self._text_color = QColor(0, 0, 0)
        self._background_color = QColor(240, 240, 240)
        self._border_color = QColor(200, 200, 200)
        self._sort_indicator_color = QColor(100, 100, 100)

        # 排序状态
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder

    def isSectionHovered(self, logical_index: int) -> bool:
        """安全的悬停检测占位方法，避免属性缺失报错。"""
        try:
            # 若未来扩展为真实悬停检测，可在此接入状态记录
            return False
        except Exception:
            return False

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int):
        """绘制表头"""
        if not rect.isValid():
            return

        # 保存画家状态
        painter.save()

        # 设置抗锯齿
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制背景
        self._draw_background(painter, rect, logical_index)

        # 绘制边框
        self._draw_border(painter, rect)

        # 绘制文本
        self._draw_text(painter, rect, logical_index)

        # 绘制排序指示器
        if logical_index == self._sort_column:
            self._draw_sort_indicator(painter, rect)

        # 恢复画家状态
        painter.restore()

    def _draw_background(self, painter: QPainter, rect: QRect, logical_index: int):
        """绘制背景"""
        # 如果是悬停状态，使用不同的背景色
        if self.isSectionHovered(logical_index):
            bg_color = self._background_color.lighter(110)
        else:
            bg_color = self._background_color

        painter.fillRect(rect, QBrush(bg_color))

    def _draw_border(self, painter: QPainter, rect: QRect):
        """绘制边框"""
        pen = QPen(self._border_color)
        pen.setWidth(1)
        painter.setPen(pen)

        # 绘制边框
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

    def _draw_text(self, painter: QPainter, rect: QRect, logical_index: int):
        """绘制文本"""
        text = self.model().headerData(logical_index, Qt.Horizontal, Qt.DisplayRole)
        if not text:
            return

        # 设置字体和颜色
        painter.setFont(self._font)
        painter.setPen(QPen(self._text_color))

        # 计算文本位置
        text_rect = rect.adjusted(8, 0, -8, 0)  # 左右边距

        # 获取文本对齐方式
        alignment = self.model().headerData(logical_index, Qt.Horizontal, Qt.TextAlignmentRole)
        if alignment is None:
            alignment = Qt.AlignLeft | Qt.AlignVCenter

        # 绘制文本
        painter.drawText(text_rect, int(alignment), str(text))

    def _draw_sort_indicator(self, painter: QPainter, rect: QRect):
        """绘制排序指示器"""
        # 计算排序指示器位置
        indicator_size = 8
        indicator_x = rect.right() - indicator_size - 8
        indicator_y = rect.center().y() - indicator_size // 2

        # 设置排序指示器颜色
        painter.setPen(QPen(self._sort_indicator_color))
        painter.setBrush(QBrush(self._sort_indicator_color))

        # 绘制三角形
        if self._sort_order == Qt.AscendingOrder:
            # 向上的三角形
            points = [
                QPoint(indicator_x, indicator_y + indicator_size),
                QPoint(indicator_x + indicator_size, indicator_y + indicator_size),
                QPoint(indicator_x + indicator_size // 2, indicator_y)
            ]
        else:
            # 向下的三角形
            points = [
                QPoint(indicator_x, indicator_y),
                QPoint(indicator_x + indicator_size, indicator_y),
                QPoint(indicator_x + indicator_size // 2, indicator_y + indicator_size)
            ]

        painter.drawPolygon(points)

    def set_sort_indicator(self, logical_index: int, order: Qt.SortOrder):
        """设置排序指示器"""
        self._sort_column = logical_index
        self._sort_order = order
        self.update()

    def clear_sort_indicator(self):
        """清除排序指示器"""
        self._sort_column = -1
        self.update()

    def sizeHint(self) -> QSize:
        """获取推荐大小"""
        # 基础大小
        size = super().sizeHint()

        # 增加一些高度以适应更好的视觉效果
        return QSize(size.width(), size.height() + 4)

    def set_style(self, font: QFont = None, text_color: QColor = None,
                  background_color: QColor = None, border_color: QColor = None):
        """设置样式"""
        if font:
            self._font = font
        if text_color:
            self._text_color = text_color
        if background_color:
            self._background_color = background_color
        if border_color:
            self._border_color = border_color

        self.update()

    def get_style(self) -> dict:
        """获取当前样式"""
        return {
            'font': self._font,
            'text_color': self._text_color,
            'background_color': self._background_color,
            'border_color': self._border_color
        }