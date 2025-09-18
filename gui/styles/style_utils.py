#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
样式工具模块
==liuq debug== FastMapV2 样式工具模块

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 17:05:00 +08:00; Reason: 阶段4-创建样式工具模块; Principle_Applied: DRY原则和工具函数封装;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 提供便捷的样式应用和组件创建工具
"""

import logging
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import QPushButton, QLabel, QGroupBox, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .theme import get_theme, BUTTON_STYLES

logger = logging.getLogger(__name__)


def create_styled_button(text: str, 
                        button_type: str = "primary",
                        min_height: int = 36,
                        min_width: Optional[int] = None,
                        icon: Optional[str] = None) -> QPushButton:
    """
    创建带样式的按钮
    
    Args:
        text: 按钮文本
        button_type: 按钮类型 (primary, secondary, success, warning, error, ghost)
        min_height: 最小高度
        min_width: 最小宽度（可选）
        icon: 图标文本（可选，如 "📁"）
        
    Returns:
        配置好样式的QPushButton
    """
    try:
        button = QPushButton()
        
        # 设置文本（包含图标）
        display_text = f"{icon} {text}" if icon else text
        button.setText(display_text)
        
        # 设置尺寸
        button.setMinimumHeight(min_height)
        if min_width:
            button.setMinimumWidth(min_width)
        
        # 应用样式
        if button_type in BUTTON_STYLES:
            button.setStyleSheet(BUTTON_STYLES[button_type]())
        else:
            logger.warning(f"==liuq debug== 未知的按钮类型: {button_type}")
            button.setStyleSheet(BUTTON_STYLES["primary"]())
        
        logger.debug(f"==liuq debug== 创建样式按钮: {text} ({button_type})")
        return button
        
    except Exception as e:
        logger.error(f"==liuq debug== 创建样式按钮失败: {e}")
        # 返回基本按钮作为备选
        button = QPushButton(text)
        button.setMinimumHeight(min_height)
        return button


def create_title_label(text: str, 
                      level: int = 1,
                      alignment: Qt.Alignment = Qt.AlignCenter) -> QLabel:
    """
    创建标题标签
    
    Args:
        text: 标题文本
        level: 标题级别 (1-6)
        alignment: 对齐方式
        
    Returns:
        配置好样式的QLabel
    """
    try:
        label = QLabel(text)
        label.setAlignment(alignment)
        
        theme = get_theme()
        
        # 根据级别设置字体大小和权重
        font_sizes = {
            1: theme.typography.text_3xl,
            2: theme.typography.text_2xl,
            3: theme.typography.text_xl,
            4: theme.typography.text_lg,
            5: theme.typography.text_base,
            6: theme.typography.text_sm
        }
        
        font_size = font_sizes.get(level, theme.typography.text_base)
        
        style = f"""
            QLabel {{
                font-family: {theme.typography.font_family};
                font-size: {font_size};
                font-weight: {theme.typography.font_bold if level <= 3 else theme.typography.font_semibold};
                color: {theme.colors.text_primary};
                padding: {theme.spacing.sm} 0;
            }}
        """
        
        # 为大标题添加底部边框
        if level <= 2:
            style += f"""
                QLabel {{
                    border-bottom: 2px solid {theme.colors.primary};
                    margin-bottom: {theme.spacing.md};
                }}
            """
        
        label.setStyleSheet(style)
        
        logger.debug(f"==liuq debug== 创建标题标签: {text} (级别{level})")
        return label
        
    except Exception as e:
        logger.error(f"==liuq debug== 创建标题标签失败: {e}")
        # 返回基本标签作为备选
        label = QLabel(text)
        label.setAlignment(alignment)
        return label


def create_card_group(title: str,
                     content_widget: Optional[QWidget] = None) -> QGroupBox:
    """
    创建卡片式分组框
    
    Args:
        title: 分组标题
        content_widget: 内容控件（可选）
        
    Returns:
        配置好样式的QGroupBox
    """
    try:
        group_box = QGroupBox(title)
        
        # 应用卡片样式
        theme = get_theme()
        group_box.setStyleSheet(theme.get_card_style())
        
        # 如果提供了内容控件，添加到分组框中
        if content_widget:
            from PyQt5.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(group_box)
            layout.addWidget(content_widget)
        
        logger.debug(f"==liuq debug== 创建卡片分组: {title}")
        return group_box
        
    except Exception as e:
        logger.error(f"==liuq debug== 创建卡片分组失败: {e}")
        # 返回基本分组框作为备选
        return QGroupBox(title)


def apply_loading_style(widget: QWidget, is_loading: bool = True):
    """
    应用加载状态样式
    
    Args:
        widget: 目标控件
        is_loading: 是否为加载状态
    """
    try:
        theme = get_theme()
        
        if is_loading:
            # 加载状态：降低透明度，禁用交互
            style = f"""
                QWidget {{
                    background-color: {theme.colors.gray_100};
                    opacity: 0.6;
                }}
            """
            widget.setEnabled(False)
        else:
            # 正常状态：恢复样式
            style = f"""
                QWidget {{
                    background-color: {theme.colors.surface};
                    opacity: 1.0;
                }}
            """
            widget.setEnabled(True)
        
        widget.setStyleSheet(style)
        
        logger.debug(f"==liuq debug== 应用加载状态: {is_loading}")
        
    except Exception as e:
        logger.error(f"==liuq debug== 应用加载状态失败: {e}")


def create_status_indicator(status: str, text: str = "") -> QLabel:
    """
    创建状态指示器
    
    Args:
        status: 状态类型 (success, warning, error, info)
        text: 状态文本
        
    Returns:
        配置好样式的状态标签
    """
    try:
        label = QLabel(text)
        theme = get_theme()
        
        # 状态颜色映射
        status_colors = {
            "success": theme.colors.success,
            "warning": theme.colors.warning,
            "error": theme.colors.error,
            "info": theme.colors.info
        }
        
        # 状态图标映射
        status_icons = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️"
        }
        
        color = status_colors.get(status, theme.colors.gray_500)
        icon = status_icons.get(status, "")
        
        # 设置文本（包含图标）
        display_text = f"{icon} {text}" if text else icon
        label.setText(display_text)
        
        style = f"""
            QLabel {{
                font-family: {theme.typography.font_family};
                font-size: {theme.typography.text_sm};
                color: {color};
                background-color: {color}20;
                border: 1px solid {color};
                border-radius: {theme.border_radius.sm};
                padding: {theme.spacing.xs} {theme.spacing.sm};
            }}
        """
        
        label.setStyleSheet(style)
        
        logger.debug(f"==liuq debug== 创建状态指示器: {status} - {text}")
        return label
        
    except Exception as e:
        logger.error(f"==liuq debug== 创建状态指示器失败: {e}")
        # 返回基本标签作为备选
        return QLabel(text)


def create_progress_overlay(parent: QWidget, message: str = "处理中...") -> QWidget:
    """
    创建进度遮罩层
    
    Args:
        parent: 父控件
        message: 进度消息
        
    Returns:
        进度遮罩控件
    """
    try:
        from PyQt5.QtWidgets import QVBoxLayout, QProgressBar
        
        overlay = QWidget(parent)
        overlay.setGeometry(parent.rect())
        
        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignCenter)
        
        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # 无限进度条
        progress_bar.setMaximumWidth(300)
        
        # 消息标签
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(progress_bar)
        layout.addWidget(message_label)
        
        # 应用样式
        theme = get_theme()
        overlay.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.colors.surface}E6;
                border-radius: {theme.border_radius.lg};
            }}
            QProgressBar {{
                border: 1px solid {theme.colors.gray_300};
                border-radius: {theme.border_radius.sm};
                text-align: center;
                background-color: {theme.colors.gray_100};
            }}
            QProgressBar::chunk {{
                background-color: {theme.colors.primary};
                border-radius: {theme.border_radius.sm};
            }}
            QLabel {{
                font-family: {theme.typography.font_family};
                font-size: {theme.typography.text_base};
                color: {theme.colors.text_primary};
                margin-top: {theme.spacing.md};
            }}
        """)
        
        overlay.hide()  # 默认隐藏
        
        logger.debug(f"==liuq debug== 创建进度遮罩: {message}")
        return overlay
        
    except Exception as e:
        logger.error(f"==liuq debug== 创建进度遮罩失败: {e}")
        # 返回空控件作为备选
        return QWidget(parent)


def show_progress_overlay(overlay: QWidget, message: str = None):
    """显示进度遮罩"""
    try:
        if message:
            # 更新消息
            for child in overlay.findChildren(QLabel):
                child.setText(message)
                break
        
        overlay.show()
        overlay.raise_()
        
        logger.debug("==liuq debug== 显示进度遮罩")
        
    except Exception as e:
        logger.error(f"==liuq debug== 显示进度遮罩失败: {e}")


def hide_progress_overlay(overlay: QWidget):
    """隐藏进度遮罩"""
    try:
        overlay.hide()
        logger.debug("==liuq debug== 隐藏进度遮罩")
        
    except Exception as e:
        logger.error(f"==liuq debug== 隐藏进度遮罩失败: {e}")


def get_icon_button_style(icon: str, tooltip: str = "") -> Dict[str, Any]:
    """
    获取图标按钮的配置
    
    Args:
        icon: 图标文本
        tooltip: 工具提示
        
    Returns:
        按钮配置字典
    """
    theme = get_theme()
    
    return {
        "text": icon,
        "style": f"""
            QPushButton {{
                font-size: {theme.typography.text_lg};
                background-color: transparent;
                border: none;
                border-radius: {theme.border_radius.sm};
                padding: {theme.spacing.xs};
                min-width: 32px;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.gray_100};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors.gray_200};
            }}
        """,
        "tooltip": tooltip
    }


def apply_modern_table_style(table_widget):
    """
    应用现代化表格样式
    
    Args:
        table_widget: QTableWidget实例
    """
    try:
        theme = get_theme()
        
        # 应用表格样式
        table_widget.setStyleSheet(theme.get_table_style())
        
        # 设置表格属性
        table_widget.setAlternatingRowColors(True)
        table_widget.setSelectionBehavior(table_widget.SelectRows)
        table_widget.setShowGrid(False)
        
        # 设置表头
        header = table_widget.horizontalHeader()
        header.setDefaultSectionSize(150)
        header.setStretchLastSection(True)
        
        logger.debug("==liuq debug== 应用现代化表格样式")
        
    except Exception as e:
        logger.error(f"==liuq debug== 应用表格样式失败: {e}")


# 常用样式常量
COMMON_STYLES = {
    "separator": lambda: f"""
        QFrame {{
            background-color: {get_theme().colors.gray_200};
            max-height: 1px;
            border: none;
        }}
    """,
    
    "tooltip": lambda: f"""
        QToolTip {{
            background-color: {get_theme().colors.gray_800};
            color: {get_theme().colors.text_on_primary};
            border: none;
            border-radius: {get_theme().border_radius.sm};
            padding: {get_theme().spacing.xs} {get_theme().spacing.sm};
            font-family: {get_theme().typography.font_family};
            font-size: {get_theme().typography.text_sm};
        }}
    """,
}
