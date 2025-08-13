#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastMapV2 统一主题样式系统
==liuq debug== FastMapV2 统一主题样式系统

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 17:00:00 +08:00; Reason: 阶段4-创建统一主题样式系统; Principle_Applied: 设计系统一致性原则;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 提供统一的颜色、字体、间距、样式规范
"""

import logging
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ThemeType(Enum):
    """主题类型枚举"""
    LIGHT = "light"
    DARK = "dark"


@dataclass
class ColorPalette:
    """颜色调色板"""
    # 主色调
    primary: str = "#2563eb"
    primary_hover: str = "#1d4ed8"
    primary_pressed: str = "#1e40af"
    
    # 辅助色
    secondary: str = "#10b981"
    secondary_hover: str = "#059669"
    secondary_pressed: str = "#047857"
    
    # 状态色
    success: str = "#10b981"
    warning: str = "#f59e0b"
    error: str = "#ef4444"
    info: str = "#3b82f6"
    
    # 中性色
    gray_50: str = "#f9fafb"
    gray_100: str = "#f3f4f6"
    gray_200: str = "#e5e7eb"
    gray_300: str = "#d1d5db"
    gray_400: str = "#9ca3af"
    gray_500: str = "#6b7280"
    gray_600: str = "#4b5563"
    gray_700: str = "#374151"
    gray_800: str = "#1f2937"
    gray_900: str = "#111827"
    
    # 背景色
    background: str = "#f8fafc"
    surface: str = "#ffffff"
    card: str = "#ffffff"
    
    # 文本色
    text_primary: str = "#1f2937"
    text_secondary: str = "#6b7280"
    text_disabled: str = "#9ca3af"
    text_on_primary: str = "#ffffff"


@dataclass
class DarkColorPalette(ColorPalette):
    """深色主题调色板"""
    # 背景色（深色主题）
    background: str = "#0f172a"
    surface: str = "#1e293b"
    card: str = "#334155"
    
    # 文本色（深色主题）
    text_primary: str = "#f1f5f9"
    text_secondary: str = "#cbd5e1"
    text_disabled: str = "#64748b"


@dataclass
class Typography:
    """字体系统"""
    # 字体族
    font_family: str = '"Microsoft YaHei", "Segoe UI", Arial, sans-serif'
    font_family_mono: str = '"Consolas", "Monaco", "Courier New", monospace'
    
    # 字体大小
    text_xs: str = "12px"
    text_sm: str = "14px"
    text_base: str = "16px"
    text_lg: str = "18px"
    text_xl: str = "20px"
    text_2xl: str = "24px"
    text_3xl: str = "30px"
    
    # 字体权重
    font_normal: str = "400"
    font_medium: str = "500"
    font_semibold: str = "600"
    font_bold: str = "700"
    
    # 行高
    leading_tight: str = "1.25"
    leading_normal: str = "1.5"
    leading_relaxed: str = "1.75"


@dataclass
class Spacing:
    """间距系统"""
    xs: str = "4px"
    sm: str = "8px"
    md: str = "16px"
    lg: str = "24px"
    xl: str = "32px"
    xxl: str = "48px"


@dataclass
class BorderRadius:
    """圆角系统"""
    none: str = "0"
    sm: str = "4px"
    md: str = "8px"
    lg: str = "12px"
    xl: str = "16px"
    full: str = "50%"


@dataclass
class Shadow:
    """阴影系统"""
    none: str = "none"
    sm: str = "0 1px 2px rgba(0, 0, 0, 0.05)"
    md: str = "0 4px 6px rgba(0, 0, 0, 0.1)"
    lg: str = "0 10px 15px rgba(0, 0, 0, 0.1)"
    xl: str = "0 20px 25px rgba(0, 0, 0, 0.1)"


class FastMapTheme:
    """FastMapV2 主题类"""
    
    def __init__(self, theme_type: ThemeType = ThemeType.LIGHT):
        """
        初始化主题
        
        Args:
            theme_type: 主题类型
        """
        self.theme_type = theme_type
        self.colors = DarkColorPalette() if theme_type == ThemeType.DARK else ColorPalette()
        self.typography = Typography()
        self.spacing = Spacing()
        self.border_radius = BorderRadius()
        self.shadow = Shadow()
        
        logger.info(f"==liuq debug== FastMapV2主题初始化完成: {theme_type.value}")
    
    def get_button_style(self, button_type: str = "primary") -> str:
        """
        获取按钮样式
        
        Args:
            button_type: 按钮类型 (primary, secondary, success, warning, error, ghost)
            
        Returns:
            QSS样式字符串
        """
        base_style = f"""
            QPushButton {{
                font-family: {self.typography.font_family};
                font-size: {self.typography.text_base};
                font-weight: {self.typography.font_medium};
                border: none;
                border-radius: {self.border_radius.md};
                padding: {self.spacing.sm} {self.spacing.md};
                min-height: 36px;
                text-align: center;
            }}
        """
        
        if button_type == "primary":
            # 调整为更克制的“描边+浅底”风格，避免大面积纯色填充过于扎眼
            return base_style + f"""
                QPushButton {{
                    background-color: {self.colors.surface};
                    color: {self.colors.primary};
                    border: 1px solid {self.colors.primary};
                }}
                QPushButton:hover {{
                    background-color: {self.colors.gray_50};
                    border-color: {self.colors.primary_hover};
                    color: {self.colors.primary_hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.gray_100};
                    border-color: {self.colors.primary_pressed};
                    color: {self.colors.primary_pressed};
                }}
                QPushButton:disabled {{
                    background-color: {self.colors.gray_100};
                    border-color: {self.colors.gray_300};
                    color: {self.colors.text_disabled};
                }}
            """
        elif button_type == "secondary":
            return base_style + f"""
                QPushButton {{
                    background-color: {self.colors.surface};
                    color: {self.colors.primary};
                    border: 1px solid {self.colors.primary};
                }}
                QPushButton:hover {{
                    background-color: {self.colors.gray_50};
                    border-color: {self.colors.primary_hover};
                    color: {self.colors.primary_hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.gray_100};
                    border-color: {self.colors.primary_pressed};
                    color: {self.colors.primary_pressed};
                }}
                QPushButton:disabled {{
                    background-color: {self.colors.gray_100};
                    border-color: {self.colors.gray_300};
                    color: {self.colors.text_disabled};
                }}
            """
        elif button_type == "success":
            return base_style + f"""
                QPushButton {{
                    background-color: {self.colors.success};
                    color: {self.colors.text_on_primary};
                }}
                QPushButton:hover {{
                    background-color: {self.colors.secondary_hover};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.secondary_pressed};
                }}
                QPushButton:disabled {{
                    background-color: {self.colors.gray_300};
                    color: {self.colors.text_disabled};
                }}
            """
        elif button_type == "warning":
            return base_style + f"""
                QPushButton {{
                    background-color: {self.colors.warning};
                    color: {self.colors.text_on_primary};
                }}
                QPushButton:hover {{
                    background-color: #d97706;
                }}
                QPushButton:pressed {{
                    background-color: #b45309;
                }}
                QPushButton:disabled {{
                    background-color: {self.colors.gray_300};
                    color: {self.colors.text_disabled};
                }}
            """
        elif button_type == "error":
            return base_style + f"""
                QPushButton {{
                    background-color: {self.colors.error};
                    color: {self.colors.text_on_primary};
                }}
                QPushButton:hover {{
                    background-color: #dc2626;
                }}
                QPushButton:pressed {{
                    background-color: #b91c1c;
                }}
                QPushButton:disabled {{
                    background-color: {self.colors.gray_300};
                    color: {self.colors.text_disabled};
                }}
            """
        elif button_type == "ghost":
            return base_style + f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.colors.text_primary};
                    border: 1px solid {self.colors.gray_300};
                }}
                QPushButton:hover {{
                    background-color: {self.colors.gray_50};
                    border-color: {self.colors.gray_400};
                }}
                QPushButton:pressed {{
                    background-color: {self.colors.gray_100};
                    border-color: {self.colors.gray_500};
                }}
                QPushButton:disabled {{
                    background-color: transparent;
                    border-color: {self.colors.gray_200};
                    color: {self.colors.text_disabled};
                }}
            """
        
        return base_style
    
    def get_input_style(self) -> str:
        """获取输入控件样式"""
        return f"""
            QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                font-family: {self.typography.font_family};
                font-size: {self.typography.text_base};
                background-color: {self.colors.surface};
                border: 1px solid {self.colors.gray_300};
                border-radius: {self.border_radius.sm};
                padding: {self.spacing.sm};
                color: {self.colors.text_primary};
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {self.colors.primary};
                outline: none;
            }}
            QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
                background-color: {self.colors.gray_100};
                border-color: {self.colors.gray_200};
                color: {self.colors.text_disabled};
            }}
        """
    
    def get_card_style(self) -> str:
        """获取卡片样式"""
        return f"""
            QGroupBox {{
                font-family: {self.typography.font_family};
                font-size: {self.typography.text_base};
                font-weight: {self.typography.font_semibold};
                background-color: {self.colors.card};
                border: 1px solid {self.colors.gray_200};
                border-radius: {self.border_radius.lg};
                margin-top: {self.spacing.md};
                padding-top: {self.spacing.md};
                color: {self.colors.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {self.spacing.md};
                padding: 0 {self.spacing.sm} 0 {self.spacing.sm};
                background-color: {self.colors.card};
                color: {self.colors.text_primary};
            }}
        """
    
    def get_table_style(self) -> str:
        """获取表格样式"""
        return f"""
            QTableWidget {{
                font-family: {self.typography.font_family};
                font-size: {self.typography.text_sm};
                background-color: {self.colors.surface};
                border: 1px solid {self.colors.gray_200};
                border-radius: {self.border_radius.md};
                gridline-color: {self.colors.gray_200};
                color: {self.colors.text_primary};
            }}
            QTableWidget::item {{
                padding: {self.spacing.sm};
                border-bottom: 1px solid {self.colors.gray_100};
            }}
            QTableWidget::item:selected {{
                background-color: {self.colors.primary};
                color: {self.colors.text_on_primary};
            }}
            QHeaderView::section {{
                background-color: {self.colors.gray_50};
                border: none;
                border-bottom: 1px solid {self.colors.gray_200};
                padding: {self.spacing.sm};
                font-weight: {self.typography.font_semibold};
                color: {self.colors.text_primary};
            }}
        """
    
    def get_tab_style(self) -> str:
        """获取标签页样式"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {self.colors.gray_200};
                border-radius: {self.border_radius.md};
                background-color: {self.colors.surface};
            }}
            QTabBar::tab {{
                background-color: {self.colors.gray_100};
                border: 1px solid {self.colors.gray_200};
                border-bottom: none;
                border-top-left-radius: {self.border_radius.sm};
                border-top-right-radius: {self.border_radius.sm};
                padding: {self.spacing.sm} {self.spacing.md};
                margin-right: 2px;
                font-family: {self.typography.font_family};
                font-size: {self.typography.text_sm};
                font-weight: {self.typography.font_medium};
                color: {self.colors.text_secondary};
            }}
            QTabBar::tab:selected {{
                background-color: {self.colors.surface};
                border-bottom: 2px solid {self.colors.primary};
                color: {self.colors.primary};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self.colors.gray_50};
                color: {self.colors.text_primary};
            }}
        """
    
    def get_main_window_style(self) -> str:
        """获取主窗口样式"""
        return f"""
            QMainWindow {{
                background-color: {self.colors.background};
                color: {self.colors.text_primary};
                font-family: {self.typography.font_family};
            }}
            QStatusBar {{
                background-color: {self.colors.surface};
                border-top: 1px solid {self.colors.gray_200};
                color: {self.colors.text_secondary};
                font-size: {self.typography.text_sm};
            }}
        """
    
    def get_complete_stylesheet(self) -> str:
        """获取完整的样式表"""
        return f"""
            {self.get_main_window_style()}
            {self.get_button_style("primary")}
            {self.get_input_style()}
            {self.get_card_style()}
            {self.get_table_style()}
            {self.get_tab_style()}
        """


# 全局主题实例
current_theme = FastMapTheme(ThemeType.LIGHT)


def get_theme() -> FastMapTheme:
    """获取当前主题"""
    return current_theme


def set_theme(theme_type: ThemeType):
    """设置主题类型"""
    global current_theme
    current_theme = FastMapTheme(theme_type)
    logger.info(f"==liuq debug== 主题已切换到: {theme_type.value}")


def apply_theme_to_widget(widget, custom_style: str = ""):
    """
    将主题应用到控件
    
    Args:
        widget: Qt控件
        custom_style: 自定义样式（可选）
    """
    try:
        base_style = current_theme.get_complete_stylesheet()
        final_style = base_style + "\n" + custom_style if custom_style else base_style
        widget.setStyleSheet(final_style)
        logger.debug(f"==liuq debug== 主题已应用到控件: {widget.__class__.__name__}")
    except Exception as e:
        logger.error(f"==liuq debug== 应用主题失败: {e}")


# 预定义的组件样式
BUTTON_STYLES = {
    "primary": lambda: current_theme.get_button_style("primary"),
    "secondary": lambda: current_theme.get_button_style("secondary"),
    "success": lambda: current_theme.get_button_style("success"),
    "warning": lambda: current_theme.get_button_style("warning"),
    "error": lambda: current_theme.get_button_style("error"),
    "ghost": lambda: current_theme.get_button_style("ghost"),
}
