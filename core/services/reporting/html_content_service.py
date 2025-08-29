#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML内容服务
==liuq debug== FastMapV2 HTML内容生成服务

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: HTML内容生成服务，从HTMLGenerator中拆分
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class HTMLContentService:
    """
    HTML内容服务
    
    专门负责HTML内容片段的生成功能：
    - 表格内容生成
    - 统计卡片生成
    - 分析段落生成
    - 数据可视化容器生成
    """
    
    def __init__(self):
        """初始化HTML内容服务"""
        logger.debug("==liuq debug== HTML内容服务初始化完成")
    
    def generate_summary_cards(self, summary_data: Dict[str, Any]) -> str:
        """
        生成概览卡片
        
        Args:
            summary_data: 概览数据字典
            
        Returns:
            str: 概览卡片HTML
        """
        try:
            if not summary_data:
                return '<div class="alert alert-info">暂无概览数据</div>'
            
            cards = []
            cards.append('<div class="row">')
            
            for key, value in summary_data.items():
                # 处理显示名称
                display_name = self._format_field_name(key)
                
                # 处理数值
                display_value = self._format_field_value(value)
                
                # 确定卡片图标
                icon = self._get_field_icon(key)
                
                card_html = f'''
                <div class="col-md-4 col-sm-6 mb-3">
                    <div class="card h-100">
                        <div class="card-body text-center">
                            <i class="{icon} fa-2x text-primary mb-2"></i>
                            <h5 class="card-title">{display_name}</h5>
                            <p class="card-text display-6 text-primary">{display_value}</p>
                        </div>
                    </div>
                </div>
                '''
                cards.append(card_html)
            
            cards.append('</div>')
            return ''.join(cards)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成概览卡片失败: {e}")
            return f'<div class="alert alert-danger">概览卡片生成失败: {e}</div>'
    
    def generate_data_table(self, data: List[Dict[str, Any]], 
                           columns: Optional[List[Dict[str, str]]] = None,
                           table_id: str = "data-table",
                           max_rows: int = 100) -> str:
        """
        生成数据表格
        
        Args:
            data: 数据列表
            columns: 列定义 [{"key": "字段名", "title": "显示标题", "type": "数据类型"}]
            table_id: 表格ID
            max_rows: 最大显示行数
            
        Returns:
            str: 数据表格HTML
        """
        try:
            if not data:
                return '<div class="alert alert-info">暂无数据</div>'
            
            # 限制行数
            display_data = data[:max_rows]
            
            # 自动生成列定义
            if not columns:
                columns = self._auto_generate_columns(data[0])
            
            html_parts = []
            
            # 表格开始
            html_parts.append(f'<div class="table-responsive">')
            html_parts.append(f'<table id="{table_id}" class="table table-striped table-hover data-table">')
            
            # 表头
            html_parts.append('<thead class="table-dark">')
            html_parts.append('<tr>')
            for col in columns:
                html_parts.append(f'<th>{col["title"]}</th>')
            html_parts.append('</tr>')
            html_parts.append('</thead>')
            
            # 表体
            html_parts.append('<tbody>')
            for row_data in display_data:
                html_parts.append('<tr>')
                for col in columns:
                    value = row_data.get(col["key"], "")
                    formatted_value = self._format_table_cell_value(value, col.get("type", "string"))
                    cell_class = self._get_table_cell_class(value, col.get("type", "string"))
                    html_parts.append(f'<td class="{cell_class}">{formatted_value}</td>')
                html_parts.append('</tr>')
            html_parts.append('</tbody>')
            
            html_parts.append('</table>')
            html_parts.append('</div>')
            
            # 添加分页提示
            if len(data) > max_rows:
                html_parts.append(f'<p class="text-muted mt-2">显示前 {max_rows} 行，共 {len(data)} 行数据</p>')
            
            return ''.join(html_parts)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成数据表格失败: {e}")
            return f'<div class="alert alert-danger">数据表格生成失败: {e}</div>'
    
    def generate_statistics_section(self, stats_data: Dict[str, Any], 
                                   title: str = "统计信息") -> str:
        """
        生成统计信息区块
        
        Args:
            stats_data: 统计数据
            title: 区块标题
            
        Returns:
            str: 统计信息HTML
        """
        try:
            if not stats_data:
                return f'<div class="alert alert-info">{title}暂无数据</div>'
            
            html_parts = []
            
            # 区块标题
            html_parts.append(f'''
            <div class="card">
                <div class="card-header">
                    <h4><i class="fas fa-chart-bar me-2"></i>{title}</h4>
                </div>
                <div class="card-body">
            ''')
            
            # 统计项目
            if isinstance(stats_data, dict):
                html_parts.append('<div class="row">')
                for key, value in stats_data.items():
                    display_name = self._format_field_name(key)
                    display_value = self._format_field_value(value)
                    
                    html_parts.append(f'''
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="d-flex justify-content-between">
                            <span class="fw-bold">{display_name}:</span>
                            <span class="text-primary">{display_value}</span>
                        </div>
                    </div>
                    ''')
                html_parts.append('</div>')
            else:
                html_parts.append(f'<p>{stats_data}</p>')
            
            html_parts.append('''
                </div>
            </div>
            ''')
            
            return ''.join(html_parts)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成统计信息区块失败: {e}")
            return f'<div class="alert alert-danger">统计信息生成失败: {e}</div>'
    
    def generate_chart_container(self, chart_id: str, title: str = "", 
                               height: int = 400) -> str:
        """
        生成图表容器
        
        Args:
            chart_id: 图表ID
            title: 图表标题
            height: 图表高度
            
        Returns:
            str: 图表容器HTML
        """
        try:
            container_html = f'''
            <div class="chart-section mb-4">
                {"<h5 class='chart-title'>" + title + "</h5>" if title else ""}
                <div class="chart-container" style="height: {height}px;">
                    <canvas id="{chart_id}"></canvas>
                </div>
            </div>
            '''
            
            return container_html
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成图表容器失败: {e}")
            return f'<div class="alert alert-danger">图表容器生成失败: {e}</div>'
    
    def generate_analysis_section(self, analysis_data: Dict[str, Any],
                                 section_title: str = "分析结果") -> str:
        """
        生成分析结果区块
        
        Args:
            analysis_data: 分析数据
            section_title: 区块标题
            
        Returns:
            str: 分析结果HTML
        """
        try:
            if not analysis_data:
                return f'<div class="alert alert-info">{section_title}暂无数据</div>'
            
            html_parts = []
            
            # 区块开始
            html_parts.append(f'''
            <div class="card analysis-card">
                <div class="card-header">
                    <h4><i class="fas fa-microscope me-2"></i>{section_title}</h4>
                </div>
                <div class="card-body">
            ''')
            
            # 分析内容
            for key, value in analysis_data.items():
                if isinstance(value, dict):
                    # 嵌套字典，生成子区块
                    html_parts.append(self._generate_nested_analysis_block(key, value))
                elif isinstance(value, list):
                    # 列表数据，生成列表
                    html_parts.append(self._generate_analysis_list(key, value))
                else:
                    # 简单值，生成段落
                    display_name = self._format_field_name(key)
                    display_value = self._format_field_value(value)
                    html_parts.append(f'<p><strong>{display_name}:</strong> {display_value}</p>')
            
            html_parts.append('''
                </div>
            </div>
            ''')
            
            return ''.join(html_parts)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成分析结果区块失败: {e}")
            return f'<div class="alert alert-danger">分析结果生成失败: {e}</div>'
    
    def generate_alert_box(self, message: str, alert_type: str = "info",
                          title: Optional[str] = None, dismissible: bool = False) -> str:
        """
        生成警告框
        
        Args:
            message: 消息内容
            alert_type: 警告类型 (info, warning, danger, success)
            title: 标题（可选）
            dismissible: 是否可关闭
            
        Returns:
            str: 警告框HTML
        """
        try:
            alert_class = f"alert alert-{alert_type}"
            if dismissible:
                alert_class += " alert-dismissible"
            
            icon_map = {
                "info": "fas fa-info-circle",
                "warning": "fas fa-exclamation-triangle", 
                "danger": "fas fa-exclamation-circle",
                "success": "fas fa-check-circle"
            }
            
            icon = icon_map.get(alert_type, "fas fa-info-circle")
            
            html_parts = []
            html_parts.append(f'<div class="{alert_class}" role="alert">')
            
            if dismissible:
                html_parts.append('''
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                ''')
            
            if title:
                html_parts.append(f'<h5 class="alert-heading"><i class="{icon} me-2"></i>{title}</h5>')
                html_parts.append(f'<p class="mb-0">{message}</p>')
            else:
                html_parts.append(f'<i class="{icon} me-2"></i>{message}')
            
            html_parts.append('</div>')
            
            return ''.join(html_parts)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成警告框失败: {e}")
            return f'<div class="alert alert-danger">警告框生成失败: {e}</div>'
    
    def generate_progress_bar(self, percentage: float, label: str = "",
                             color: str = "primary") -> str:
        """
        生成进度条
        
        Args:
            percentage: 百分比 (0-100)
            label: 标签文本
            color: 颜色主题
            
        Returns:
            str: 进度条HTML
        """
        try:
            percentage = max(0, min(100, percentage))  # 限制在0-100之间
            
            html = f'''
            <div class="progress-section mb-3">
                {f"<label>{label}</label>" if label else ""}
                <div class="progress">
                    <div class="progress-bar bg-{color}" role="progressbar" 
                         style="width: {percentage}%" 
                         aria-valuenow="{percentage}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        {percentage:.1f}%
                    </div>
                </div>
            </div>
            '''
            
            return html
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成进度条失败: {e}")
            return f'<div class="alert alert-danger">进度条生成失败: {e}</div>'
    
    def _format_field_name(self, field_name: str) -> str:
        """格式化字段名称"""
        # 常见字段名称映射
        name_mapping = {
            'total_maps': '总Map数量',
            'map_count': 'Map数量',
            'total_points': '总点数',
            'file_size': '文件大小',
            'parse_time': '解析时间',
            'generation_time': '生成时间',
            'accuracy_percentage': '准确率',
            'dominant_scene': '主导场景',
            'outdoor_count': '室外场景',
            'indoor_count': '室内场景',
            'night_count': '夜景场景'
        }
        
        return name_mapping.get(field_name, field_name.replace('_', ' ').title())
    
    def _format_field_value(self, value: Any) -> str:
        """格式化字段值"""
        if value is None:
            return "N/A"
        elif isinstance(value, bool):
            return "是" if value else "否"
        elif isinstance(value, float):
            if value < 1:
                return f"{value:.3f}"
            else:
                return f"{value:.2f}"
        elif isinstance(value, int):
            if value > 1000:
                return f"{value:,}"
            else:
                return str(value)
        else:
            return str(value)
    
    def _get_field_icon(self, field_name: str) -> str:
        """获取字段对应的图标"""
        icon_mapping = {
            'total_maps': 'fas fa-map',
            'map_count': 'fas fa-map-marker-alt',
            'total_points': 'fas fa-dot-circle',
            'file_size': 'fas fa-file',
            'parse_time': 'fas fa-clock',
            'generation_time': 'fas fa-stopwatch',
            'accuracy_percentage': 'fas fa-percentage',
            'dominant_scene': 'fas fa-crown',
            'outdoor_count': 'fas fa-sun',
            'indoor_count': 'fas fa-home',
            'night_count': 'fas fa-moon'
        }
        
        return icon_mapping.get(field_name, 'fas fa-info-circle')
    
    def _auto_generate_columns(self, sample_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """自动生成表格列定义"""
        columns = []
        
        for key, value in sample_data.items():
            col_type = "string"
            if isinstance(value, bool):
                col_type = "boolean"
            elif isinstance(value, int):
                col_type = "integer"
            elif isinstance(value, float):
                col_type = "float"
            
            columns.append({
                "key": key,
                "title": self._format_field_name(key),
                "type": col_type
            })
        
        return columns
    
    def _format_table_cell_value(self, value: Any, cell_type: str) -> str:
        """格式化表格单元格值"""
        if value is None:
            return ""
        elif cell_type == "boolean":
            return "✓" if value else "✗"
        elif cell_type == "float":
            return f"{value:.3f}" if isinstance(value, (int, float)) else str(value)
        elif cell_type == "integer":
            return f"{value:,}" if isinstance(value, int) and value > 1000 else str(value)
        else:
            return str(value)
    
    def _get_table_cell_class(self, value: Any, cell_type: str) -> str:
        """获取表格单元格CSS类"""
        classes = []
        
        if cell_type in ["integer", "float"]:
            classes.append("number-cell")
        elif cell_type == "boolean":
            classes.append("status-cell")
            if value:
                classes.append("status-success")
            else:
                classes.append("status-error")
        
        return " ".join(classes)
    
    def _generate_nested_analysis_block(self, title: str, data: Dict[str, Any]) -> str:
        """生成嵌套分析区块"""
        html_parts = []
        
        display_title = self._format_field_name(title)
        html_parts.append(f'<h6 class="mt-3">{display_title}</h6>')
        html_parts.append('<div class="ms-3">')
        
        for key, value in data.items():
            display_name = self._format_field_name(key)
            display_value = self._format_field_value(value)
            html_parts.append(f'<p><strong>{display_name}:</strong> {display_value}</p>')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def _generate_analysis_list(self, title: str, data: List[Any]) -> str:
        """生成分析列表"""
        html_parts = []
        
        display_title = self._format_field_name(title)
        html_parts.append(f'<h6 class="mt-3">{display_title}</h6>')
        html_parts.append('<ul>')
        
        for item in data[:10]:  # 限制显示前10项
            if isinstance(item, dict):
                # 如果是字典，显示主要信息
                main_info = item.get('name', item.get('title', str(item)))
                html_parts.append(f'<li>{main_info}</li>')
            else:
                html_parts.append(f'<li>{item}</li>')
        
        if len(data) > 10:
            html_parts.append(f'<li class="text-muted">... 还有 {len(data) - 10} 项</li>')
        
        html_parts.append('</ul>')
        
        return ''.join(html_parts)


# 全局内容服务实例
_content_service: Optional[HTMLContentService] = None


def get_html_content_service() -> HTMLContentService:
    """获取HTML内容服务实例"""
    global _content_service
    
    if _content_service is None:
        _content_service = HTMLContentService()
        logger.info("==liuq debug== 创建HTML内容服务实例")
    
    return _content_service