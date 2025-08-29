#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML样式服务
==liuq debug== FastMapV2 HTML样式处理服务

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: HTML样式处理服务，从HTMLGenerator中拆分
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class StyleTheme(Enum):
    """样式主题枚举"""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    MINIMAL = "minimal"
    CORPORATE = "corporate"


class HTMLStyleService:
    """
    HTML样式服务
    
    专门负责HTML样式的生成和管理功能：
    - CSS样式生成
    - 主题切换
    - 响应式设计
    - 组件样式
    """
    
    def __init__(self, theme: StyleTheme = StyleTheme.DEFAULT):
        """初始化HTML样式服务"""
        self.current_theme = theme
        self.custom_styles = {}
        self.color_schemes = self._load_color_schemes()
        logger.debug("==liuq debug== HTML样式服务初始化完成")
    
    def generate_base_styles(self) -> str:
        """
        生成基础样式
        
        Returns:
            str: CSS样式字符串
        """
        try:
            base_styles = []
            
            # 添加重置样式
            base_styles.append(self._get_reset_styles())
            
            # 添加布局样式
            base_styles.append(self._get_layout_styles())
            
            # 添加组件样式
            base_styles.append(self._get_component_styles())
            
            # 添加主题样式
            base_styles.append(self._get_theme_styles())
            
            # 添加响应式样式
            base_styles.append(self._get_responsive_styles())
            
            return '\n'.join(base_styles)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成基础样式失败: {e}")
            return self._get_fallback_styles()
    
    def generate_chart_styles(self) -> str:
        """
        生成图表样式
        
        Returns:
            str: 图表CSS样式字符串
        """
        return '''
        /* 图表样式 */
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
            padding: 10px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .chart-title {
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }
        
        .chart-legend {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        
        .chart-legend-item {
            display: flex;
            align-items: center;
            margin: 5px 10px;
        }
        
        .chart-legend-color {
            width: 16px;
            height: 16px;
            margin-right: 8px;
            border-radius: 3px;
        }
        
        .chart-tooltip {
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.9em;
            max-width: 200px;
        }
        '''
    
    def generate_table_styles(self) -> str:
        """
        生成表格样式
        
        Returns:
            str: 表格CSS样式字符串
        """
        return '''
        /* 表格样式 */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: #fff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .data-table th,
        .data-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .data-table th {
            background: #f5f5f5;
            font-weight: 600;
            color: #333;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        
        .data-table tbody tr:hover {
            background: #f9f9f9;
        }
        
        .data-table .number-cell {
            text-align: right;
            font-family: monospace;
        }
        
        .data-table .status-cell {
            text-align: center;
        }
        
        .data-table .status-success {
            color: #28a745;
            font-weight: bold;
        }
        
        .data-table .status-warning {
            color: #ffc107;
            font-weight: bold;
        }
        
        .data-table .status-error {
            color: #dc3545;
            font-weight: bold;
        }
        '''
    
    def generate_print_styles(self) -> str:
        """
        生成打印样式
        
        Returns:
            str: 打印CSS样式字符串
        """
        return '''
        /* 打印样式 */
        @media print {
            body {
                font-size: 12pt;
                line-height: 1.4;
                color: #000;
                background: #fff;
            }
            
            .no-print {
                display: none !important;
            }
            
            .print-break {
                page-break-before: always;
            }
            
            .chart-container {
                break-inside: avoid;
                max-height: 300px;
            }
            
            .data-table {
                break-inside: avoid;
            }
            
            .data-table th {
                background: #f0f0f0 !important;
            }
            
            a {
                text-decoration: none;
                color: #000;
            }
            
            .container-fluid {
                max-width: none;
                padding: 0;
            }
        }
        '''
    
    def set_theme(self, theme: StyleTheme):
        """
        设置样式主题
        
        Args:
            theme: 主题枚举值
        """
        self.current_theme = theme
        logger.debug(f"==liuq debug== 切换样式主题: {theme.value}")
    
    def add_custom_style(self, name: str, css: str):
        """
        添加自定义样式
        
        Args:
            name: 样式名称
            css: CSS内容
        """
        self.custom_styles[name] = css
        logger.debug(f"==liuq debug== 添加自定义样式: {name}")
    
    def get_custom_styles(self) -> str:
        """
        获取所有自定义样式
        
        Returns:
            str: 自定义CSS样式字符串
        """
        if not self.custom_styles:
            return ""
        
        styles = ["/* 自定义样式 */"]
        for name, css in self.custom_styles.items():
            styles.append(f"/* {name} */")
            styles.append(css)
        
        return '\n'.join(styles)
    
    def generate_complete_stylesheet(self, include_charts: bool = True, 
                                   include_tables: bool = True,
                                   include_print: bool = True) -> str:
        """
        生成完整样式表
        
        Args:
            include_charts: 是否包含图表样式
            include_tables: 是否包含表格样式
            include_print: 是否包含打印样式
            
        Returns:
            str: 完整CSS样式字符串
        """
        try:
            styles = []
            
            # 基础样式
            styles.append(self.generate_base_styles())
            
            # 图表样式
            if include_charts:
                styles.append(self.generate_chart_styles())
            
            # 表格样式
            if include_tables:
                styles.append(self.generate_table_styles())
            
            # 打印样式
            if include_print:
                styles.append(self.generate_print_styles())
            
            # 自定义样式
            custom = self.get_custom_styles()
            if custom:
                styles.append(custom)
            
            return '\n'.join(styles)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成完整样式表失败: {e}")
            return self._get_fallback_styles()
    
    def _get_reset_styles(self) -> str:
        """获取重置样式"""
        return '''
        /* 重置样式 */
        * {
            box-sizing: border-box;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        
        h1, h2, h3, h4, h5, h6 {
            margin-top: 0;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        p {
            margin-top: 0;
            margin-bottom: 1rem;
        }
        '''
    
    def _get_layout_styles(self) -> str:
        """获取布局样式"""
        return '''
        /* 布局样式 */
        .container-fluid {
            width: 100%;
            padding-right: 15px;
            padding-left: 15px;
            margin-right: auto;
            margin-left: auto;
        }
        
        .row {
            display: flex;
            flex-wrap: wrap;
            margin-right: -15px;
            margin-left: -15px;
        }
        
        .col-12 { flex: 0 0 100%; max-width: 100%; }
        .col-md-3 { flex: 0 0 25%; max-width: 25%; }
        .col-md-6 { flex: 0 0 50%; max-width: 50%; }
        .col-md-9 { flex: 0 0 75%; max-width: 75%; }
        
        [class*="col-"] {
            position: relative;
            width: 100%;
            padding-right: 15px;
            padding-left: 15px;
        }
        '''
    
    def _get_component_styles(self) -> str:
        """获取组件样式"""
        return '''
        /* 组件样式 */
        .card {
            position: relative;
            display: flex;
            flex-direction: column;
            min-width: 0;
            word-wrap: break-word;
            background: #fff;
            border: 1px solid rgba(0,0,0,.125);
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .card-header {
            padding: 15px 20px;
            margin-bottom: 0;
            background: #f8f9fa;
            border-bottom: 1px solid rgba(0,0,0,.125);
            border-top-left-radius: 7px;
            border-top-right-radius: 7px;
        }
        
        .card-body {
            flex: 1 1 auto;
            padding: 20px;
        }
        
        .alert {
            position: relative;
            padding: 15px 20px;
            margin-bottom: 20px;
            border: 1px solid transparent;
            border-radius: 6px;
        }
        
        .alert-info {
            color: #0c5460;
            background: #d1ecf1;
            border-color: #bee5eb;
        }
        
        .alert-warning {
            color: #856404;
            background: #fff3cd;
            border-color: #ffeaa7;
        }
        
        .alert-danger {
            color: #721c24;
            background: #f8d7da;
            border-color: #f5c6cb;
        }
        
        .alert-success {
            color: #155724;
            background: #d4edda;
            border-color: #c3e6cb;
        }
        '''
    
    def _get_theme_styles(self) -> str:
        """获取主题样式"""
        color_scheme = self.color_schemes.get(self.current_theme.value, self.color_schemes['default'])
        
        return f'''
        /* 主题样式 - {self.current_theme.value} */
        .report-header {{
            background: {color_scheme['primary_gradient']};
            color: {color_scheme['text_on_primary']};
            padding: 30px 0;
        }}
        
        .text-primary {{ color: {color_scheme['primary']} !important; }}
        .bg-primary {{ background-color: {color_scheme['primary']} !important; }}
        
        .summary-card {{ border-left: 4px solid {color_scheme['accent']}; }}
        .analysis-card {{ border-left: 4px solid {color_scheme['secondary']}; }}
        
        a {{
            color: {color_scheme['link']};
            text-decoration: none;
        }}
        
        a:hover {{
            color: {color_scheme['link_hover']};
            text-decoration: underline;
        }}
        '''
    
    def _get_responsive_styles(self) -> str:
        """获取响应式样式"""
        return '''
        /* 响应式样式 */
        @media (max-width: 768px) {
            .col-md-3, .col-md-6, .col-md-9 {
                flex: 0 0 100%;
                max-width: 100%;
                margin-bottom: 20px;
            }
            
            .card-body {
                padding: 15px;
            }
            
            .chart-container {
                height: 300px;
            }
            
            .data-table {
                font-size: 0.9em;
            }
            
            .data-table th,
            .data-table td {
                padding: 8px 10px;
            }
        }
        
        @media (max-width: 480px) {
            .container-fluid {
                padding-right: 10px;
                padding-left: 10px;
            }
            
            .card-body {
                padding: 10px;
            }
            
            .chart-container {
                height: 250px;
            }
        }
        '''
    
    def _get_fallback_styles(self) -> str:
        """获取回退样式"""
        return '''
        /* 回退样式 */
        body { font-family: Arial, sans-serif; margin: 20px; }
        .card { border: 1px solid #ddd; margin: 10px 0; padding: 15px; }
        .alert { padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }
        '''
    
    def _load_color_schemes(self) -> Dict[str, Dict[str, str]]:
        """加载颜色方案"""
        return {
            'default': {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'accent': '#28a745',
                'primary_gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                'text_on_primary': '#ffffff',
                'link': '#007bff',
                'link_hover': '#0056b3'
            },
            'dark': {
                'primary': '#375a7f',
                'secondary': '#444',
                'accent': '#00bc8c',
                'primary_gradient': 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)',
                'text_on_primary': '#ffffff',
                'link': '#375a7f',
                'link_hover': '#2a4d73'
            },
            'light': {
                'primary': '#4285f4',
                'secondary': '#9e9e9e',
                'accent': '#ff9800',
                'primary_gradient': 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
                'text_on_primary': '#1976d2',
                'link': '#4285f4',
                'link_hover': '#3367d6'
            },
            'minimal': {
                'primary': '#333333',
                'secondary': '#666666',
                'accent': '#0066cc',
                'primary_gradient': 'linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)',
                'text_on_primary': '#333333',
                'link': '#0066cc',
                'link_hover': '#004499'
            },
            'corporate': {
                'primary': '#1f4e79',
                'secondary': '#5b9bd5',
                'accent': '#70ad47',
                'primary_gradient': 'linear-gradient(135deg, #1f4e79 0%, #2e75b6 100%)',
                'text_on_primary': '#ffffff',
                'link': '#1f4e79',
                'link_hover': '#164061'
            }
        }


# 全局样式服务实例
_style_service: Optional[HTMLStyleService] = None


def get_html_style_service() -> HTMLStyleService:
    """获取HTML样式服务实例"""
    global _style_service
    
    if _style_service is None:
        _style_service = HTMLStyleService()
        logger.info("==liuq debug== 创建HTML样式服务实例")
    
    return _style_service