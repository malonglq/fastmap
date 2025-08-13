#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表生成器
==liuq debug== HTML/JavaScript图表代码生成器

生成Chart.js图表的JavaScript代码
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ChartGenerator:
    """图表生成器类"""
    
    def __init__(self):
        """初始化图表生成器"""
        self.chart_colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
            '#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56'
        ]
        logger.info("==liuq debug== 图表生成器初始化完成")
    
    def generate_trend_chart(self, field_name: str, trend_data: Dict[str, Any], 
                           chart_id: str = "trendChart") -> str:
        """
        生成趋势对比图表
        
        Args:
            field_name: 字段名
            trend_data: 趋势数据
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        try:
            labels = trend_data.get('labels', [])
            before_values = trend_data.get('before_values', [])
            after_values = trend_data.get('after_values', [])
            
            # 限制显示的数据点数量（避免图表过于拥挤）
            max_points = 50
            if len(labels) > max_points:
                step = len(labels) // max_points
                labels = labels[::step]
                before_values = before_values[::step]
                after_values = after_values[::step]
            
            chart_config = {
                'type': 'line',
                'data': {
                    'labels': labels,
                    'datasets': [
                        {
                            'label': f'{field_name} (处理前)',
                            'data': before_values,
                            'borderColor': self.chart_colors[0],
                            'backgroundColor': self.chart_colors[0] + '20',
                            'borderWidth': 2,
                            'fill': False,
                            'tension': 0.1
                        },
                        {
                            'label': f'{field_name} (处理后)',
                            'data': after_values,
                            'borderColor': self.chart_colors[1],
                            'backgroundColor': self.chart_colors[1] + '20',
                            'borderWidth': 2,
                            'fill': False,
                            'tension': 0.1
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'interaction': {
                        'intersect': False,
                        'mode': 'index'
                    },
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': f'{field_name} 趋势对比图',
                            'font': {'size': 16}
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        },
                        'tooltip': {
                            'callbacks': {}
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': '数据点'
                            },
                            'ticks': {
                                'maxTicksLimit': 10
                            }
                        },
                        'y': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': field_name
                            }
                        }
                    }
                }
            }
            
            js_code = f"""
// 趋势图表 - {field_name}
const {chart_id}Config = {json.dumps(chart_config, indent=2)};
const {chart_id}Ctx = document.getElementById('{chart_id}').getContext('2d');
const {chart_id} = new Chart({chart_id}Ctx, {chart_id}Config);
"""
            
            return js_code
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成趋势图表失败: {e}")
            return f"// 生成趋势图表失败: {e}"
    
    def generate_change_distribution_chart(self, field_name: str, 
                                         change_categories: Dict[str, int],
                                         chart_id: str = "changeChart") -> str:
        """
        生成变化分布图表
        
        Args:
            field_name: 字段名
            change_categories: 变化分类数据
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        try:
            # 准备数据
            labels = []
            data = []
            colors = []
            
            category_mapping = {
                'large_increase': ('大幅增加 (>10%)', '#28a745'),
                'medium_increase': ('中等增加 (1-10%)', '#6f42c1'),
                'small_increase': ('小幅增加 (0-1%)', '#17a2b8'),
                'no_change': ('无变化 (0%)', '#6c757d'),
                'small_decrease': ('小幅减少 (0 to -1%)', '#fd7e14'),
                'medium_decrease': ('中等减少 (-1 to -10%)', '#dc3545'),
                'large_decrease': ('大幅减少 (<-10%)', '#721c24')
            }
            
            for category, count in change_categories.items():
                if count > 0 and category in category_mapping:
                    label, color = category_mapping[category]
                    labels.append(label)
                    data.append(count)
                    colors.append(color)
            
            chart_config = {
                'type': 'doughnut',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': data,
                        'backgroundColor': colors,
                        'borderWidth': 2,
                        'borderColor': '#ffffff'
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': f'{field_name} 变化分布',
                            'font': {'size': 16}
                        },
                        'legend': {
                            'display': True,
                            'position': 'right'
                        },
                        'tooltip': {
                            'callbacks': {}
                        }
                    }
                }
            }
            
            js_code = f"""
// 变化分布图表 - {field_name}
const {chart_id}Config = {json.dumps(chart_config, indent=2)};
const {chart_id}Ctx = document.getElementById('{chart_id}').getContext('2d');
const {chart_id} = new Chart({chart_id}Ctx, {chart_id}Config);
"""
            
            return js_code
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成变化分布图表失败: {e}")
            return f"// 生成变化分布图表失败: {e}"
    
    def generate_statistics_chart(self, field_name: str, 
                                before_stats: Dict[str, float],
                                after_stats: Dict[str, float],
                                chart_id: str = "statsChart") -> str:
        """
        生成统计对比图表
        
        Args:
            field_name: 字段名
            before_stats: 处理前统计
            after_stats: 处理后统计
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        try:
            # 选择要显示的统计指标
            stats_to_show = ['mean', 'median', 'std', 'min', 'max']
            labels = ['平均值', '中位数', '标准差', '最小值', '最大值']
            
            before_data = []
            after_data = []
            
            for stat in stats_to_show:
                before_data.append(before_stats.get(stat, 0))
                after_data.append(after_stats.get(stat, 0))
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [
                        {
                            'label': '处理前',
                            'data': before_data,
                            'backgroundColor': self.chart_colors[0] + '80',
                            'borderColor': self.chart_colors[0],
                            'borderWidth': 1
                        },
                        {
                            'label': '处理后',
                            'data': after_data,
                            'backgroundColor': self.chart_colors[1] + '80',
                            'borderColor': self.chart_colors[1],
                            'borderWidth': 1
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': f'{field_name} 统计指标对比',
                            'font': {'size': 16}
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': '统计指标'
                            }
                        },
                        'y': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': '数值'
                            }
                        }
                    }
                }
            }
            
            js_code = f"""
// 统计对比图表 - {field_name}
const {chart_id}Config = {json.dumps(chart_config, indent=2)};
const {chart_id}Ctx = document.getElementById('{chart_id}').getContext('2d');
const {chart_id} = new Chart({chart_id}Ctx, {chart_id}Config);
"""
            
            return js_code
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成统计图表失败: {e}")
            return f"// 生成统计图表失败: {e}"
    
    def generate_multi_field_overview_chart(self, fields_data: Dict[str, Dict[str, Any]],
                                          chart_id: str = "overviewChart") -> str:
        """
        生成多字段概览图表
        
        Args:
            fields_data: 多字段数据
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        try:
            labels = list(fields_data.keys())
            positive_changes = []
            negative_changes = []
            no_changes = []
            
            for field, data in fields_data.items():
                change_stats = data.get('change_stats', {})
                positive_changes.append(change_stats.get('positive_changes', 0))
                negative_changes.append(change_stats.get('negative_changes', 0))
                no_changes.append(change_stats.get('no_changes', 0))
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [
                        {
                            'label': '正向变化',
                            'data': positive_changes,
                            'backgroundColor': '#28a745',
                            'borderColor': '#28a745',
                            'borderWidth': 1
                        },
                        {
                            'label': '负向变化',
                            'data': negative_changes,
                            'backgroundColor': '#dc3545',
                            'borderColor': '#dc3545',
                            'borderWidth': 1
                        },
                        {
                            'label': '无变化',
                            'data': no_changes,
                            'backgroundColor': '#6c757d',
                            'borderColor': '#6c757d',
                            'borderWidth': 1
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': '多字段变化概览',
                            'font': {'size': 16}
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': '字段'
                            }
                        },
                        'y': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': '数据点数量'
                            },
                            'stacked': True
                        }
                    }
                }
            }
            
            js_code = f"""
// 多字段概览图表
const {chart_id}Config = {json.dumps(chart_config, indent=2)};
const {chart_id}Ctx = document.getElementById('{chart_id}').getContext('2d');
const {chart_id} = new Chart({chart_id}Ctx, {chart_id}Config);
"""
            
            return js_code
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成多字段概览图表失败: {e}")
            return f"// 生成多字段概览图表失败: {e}"
    
    def generate_all_charts_script(self, analysis_results: Dict[str, Any]) -> str:
        """
        生成所有图表的JavaScript代码
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            完整的JavaScript代码
        """
        try:
            js_scripts = []
            js_scripts.append("// CSV数据对比分析图表")
            js_scripts.append(f"// 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            js_scripts.append("")
            
            # 多字段概览图表 - 只有多个字段时才生成
            field_analyses = analysis_results.get('field_analyses', {})
            if len(field_analyses) > 1:
                overview_script = self.generate_multi_field_overview_chart(field_analyses, 'overviewChart')
                js_scripts.append(overview_script)
                js_scripts.append("")
            
            # 为每个字段生成图表
            trend_data = analysis_results.get('trend_data', {})
            
            for i, (field, analysis) in enumerate(field_analyses.items()):
                if 'error' in analysis:
                    continue
                
                field_safe = field.replace(' ', '_').replace('-', '_')
                
                # 趋势图表
                if field in trend_data:
                    trend_script = self.generate_trend_chart(
                        field, trend_data[field], f'trendChart_{field_safe}_{i}'
                    )
                    js_scripts.append(trend_script)
                    js_scripts.append("")
                
                # 变化分布图表
                change_stats = analysis.get('change_stats', {})
                change_categories = change_stats.get('change_categories', {})
                if change_categories:
                    change_script = self.generate_change_distribution_chart(
                        field, change_categories, f'changeChart_{field_safe}_{i}'
                    )
                    js_scripts.append(change_script)
                    js_scripts.append("")
                
                # 统计对比图表
                before_stats = analysis.get('before_stats', {})
                after_stats = analysis.get('after_stats', {})
                if before_stats and after_stats:
                    stats_script = self.generate_statistics_chart(
                        field, before_stats, after_stats, f'statsChart_{field_safe}_{i}'
                    )
                    js_scripts.append(stats_script)
                    js_scripts.append("")
            
            return "\n".join(js_scripts)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成所有图表脚本失败: {e}")
            return f"// 生成所有图表脚本失败: {e}"

    def generate_all_charts_script_with_mapping(self, analysis_results: Dict[str, Any],
                                              processed_fields: List[Dict[str, Any]]) -> str:
        """
        生成所有图表的JavaScript代码（使用映射后的字段信息）

        Args:
            analysis_results: 分析结果
            processed_fields: 处理后的字段数据（包含显示名称和原始名称的映射）

        Returns:
            完整的JavaScript代码
        """
        try:
            js_scripts = []
            js_scripts.append("// CSV数据对比分析图表")
            js_scripts.append(f"// 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            js_scripts.append("")

            # 构建原始名称到显示名称的映射
            original_to_display = {}
            for field_data in processed_fields:
                original_name = field_data.get('original_name', field_data['name'])
                display_name = field_data['name']
                original_to_display[original_name] = display_name

            # 多字段概览图表 - 只有多个字段时才生成
            field_analyses = analysis_results.get('field_analyses', {})
            if len(processed_fields) > 1 and field_analyses:
                # 转换字段分析数据，使用显示名称作为键
                display_field_analyses = {}
                for original_field, analysis in field_analyses.items():
                    display_field = original_to_display.get(original_field, original_field)
                    display_field_analyses[display_field] = analysis

                overview_script = self.generate_multi_field_overview_chart(display_field_analyses, 'overviewChart')
                js_scripts.append(overview_script)
                js_scripts.append("")

            # 为每个字段生成图表
            trend_data = analysis_results.get('trend_data', {})

            for i, field_data in enumerate(processed_fields):
                display_name = field_data['name']
                original_name = field_data.get('original_name', display_name)
                safe_name = field_data['safe_name']

                # 检查是否有分析数据
                analysis = field_analyses.get(original_name, {})
                if 'error' in analysis:
                    continue

                # 趋势图表
                if original_name in trend_data:
                    trend_script = self.generate_trend_chart(
                        display_name, trend_data[original_name], f'trendChart_{safe_name}_{i}'
                    )
                    js_scripts.append(trend_script)
                    js_scripts.append("")

                # 变化分布图表
                change_stats = analysis.get('change_stats', {})
                change_categories = change_stats.get('change_categories', {})
                if change_categories:
                    change_script = self.generate_change_distribution_chart(
                        display_name, change_categories, f'changeChart_{safe_name}_{i}'
                    )
                    js_scripts.append(change_script)
                    js_scripts.append("")

                # 统计对比图表
                before_stats = analysis.get('before_stats', {})
                after_stats = analysis.get('after_stats', {})
                if before_stats and after_stats:
                    stats_script = self.generate_statistics_chart(
                        display_name, before_stats, after_stats, f'statsChart_{safe_name}_{i}'
                    )
                    js_scripts.append(stats_script)
                    js_scripts.append("")

            return '\n'.join(js_scripts)

        except Exception as e:
            logger.error(f"==liuq debug== 生成映射图表脚本失败: {e}")
            return f"// 生成映射图表脚本失败: {e}"
