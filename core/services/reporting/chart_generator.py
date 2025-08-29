#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用图表生成器
==liuq debug== FastMapV2通用Chart.js图表生成器

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 17:46:00 +08:00; Reason: P1-LD-003 抽象化HTML/Chart生成器; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: 基于现有ChartGenerator抽象化的通用图表生成器，支持Map可视化
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from core.interfaces.report_generator import IChartGenerator, ReportGeneratorConfig

logger = logging.getLogger(__name__)


class UniversalChartGenerator(IChartGenerator):
    """
    通用图表生成器类
    
    基于现有ChartGenerator抽象化，支持多种图表类型
    """
    
    def __init__(self, config: Optional[ReportGeneratorConfig] = None):
        """初始化图表生成器"""
        self.config = config or ReportGeneratorConfig()
        self.chart_colors = self.config.chart_colors
        logger.info("==liuq debug== 通用图表生成器初始化完成")
    
    def generate_scatter_chart(self, data: Dict[str, Any], chart_id: str) -> str:
        """
        生成散点图（Map坐标分布）
        
        Args:
            data: 散点图数据，格式：{
                'title': '图表标题',
                'x_label': 'X轴标签',
                'y_label': 'Y轴标签',
                'datasets': [
                    {
                        'label': '数据集名称',
                        'data': [{'x': x_val, 'y': y_val}, ...],
                        'backgroundColor': '颜色'
                    }
                ]
            }
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        try:
            title = data.get('title', '散点图')
            x_label = data.get('x_label', 'X坐标')
            y_label = data.get('y_label', 'Y坐标')
            datasets = data.get('datasets', [])
            
            # 为数据集分配颜色
            for i, dataset in enumerate(datasets):
                if 'backgroundColor' not in dataset:
                    dataset['backgroundColor'] = self.chart_colors[i % len(self.chart_colors)]
                if 'borderColor' not in dataset:
                    dataset['borderColor'] = dataset['backgroundColor']
            
            chart_config = {
                'type': 'scatter',
                'data': {
                    'datasets': datasets
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': title,
                            'font': {'size': 16}
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        },
                        'tooltip': {
                            'callbacks': {
                                'label': 'function(context) { return context.dataset.label + ": (" + context.parsed.x + ", " + context.parsed.y + ")"; }'
                            }
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': x_label
                            },
                            'type': 'linear'
                        },
                        'y': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': y_label
                            },
                            'type': 'linear'
                        }
                    }
                }
            }
            
            js_code = f"""
// 散点图 - {title}
const {chart_id}Config = {json.dumps(chart_config, indent=2)};
const {chart_id}Ctx = document.getElementById('{chart_id}').getContext('2d');
const {chart_id} = new Chart({chart_id}Ctx, {chart_id}Config);
"""
            
            return js_code
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成散点图失败: {e}")
            return f"// 生成散点图失败: {e}"
    
    def generate_heatmap_chart(self, data: Dict[str, Any], chart_id: str) -> str:
        """
        生成热力图（权重分布）
        
        Args:
            data: 热力图数据，格式：{
                'title': '图表标题',
                'x_labels': ['x1', 'x2', ...],
                'y_labels': ['y1', 'y2', ...],
                'values': [[v11, v12, ...], [v21, v22, ...], ...]
            }
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        try:
            title = data.get('title', '热力图')
            x_labels = data.get('x_labels', [])
            y_labels = data.get('y_labels', [])
            values = data.get('values', [])
            
            # 将二维数组转换为Chart.js热力图数据格式
            heatmap_data = []
            for y_idx, row in enumerate(values):
                for x_idx, value in enumerate(row):
                    heatmap_data.append({
                        'x': x_idx,
                        'y': y_idx,
                        'v': value
                    })
            
            chart_config = {
                'type': 'scatter',  # 使用散点图模拟热力图
                'data': {
                    'datasets': [{
                        'label': '权重值',
                        'data': heatmap_data,
                        'backgroundColor': 'function(context) { const value = context.parsed.v; return `rgba(255, ${255-Math.floor(value*255)}, ${255-Math.floor(value*255)}, 0.8)`; }',
                        'pointRadius': 'function(context) { return Math.max(3, context.parsed.v * 20); }'
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': title,
                            'font': {'size': 16}
                        },
                        'legend': {
                            'display': True,
                            'position': 'top'
                        },
                        'tooltip': {
                            'callbacks': {
                                'label': 'function(context) { return "权重: " + context.parsed.v.toFixed(3); }'
                            }
                        }
                    },
                    'scales': {
                        'x': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': 'X坐标区间'
                            },
                            'type': 'linear'
                        },
                        'y': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': 'Y坐标区间'
                            },
                            'type': 'linear'
                        }
                    }
                }
            }
            
            js_code = f"""
// 热力图 - {title}
const {chart_id}Config = {json.dumps(chart_config, indent=2)};
const {chart_id}Ctx = document.getElementById('{chart_id}').getContext('2d');
const {chart_id} = new Chart({chart_id}Ctx, {chart_id}Config);
"""
            
            return js_code
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成热力图失败: {e}")
            return f"// 生成热力图失败: {e}"
    
    def generate_trend_chart(self, data: Dict[str, Any], chart_id: str) -> str:
        """
        生成趋势图（复用现有实现）
        
        Args:
            data: 趋势数据
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        try:
            title = data.get('title', '趋势图')
            datasets = data.get('datasets', [])
            
            # 为数据集分配颜色
            for i, dataset in enumerate(datasets):
                if 'borderColor' not in dataset:
                    dataset['borderColor'] = self.chart_colors[i % len(self.chart_colors)]
                if 'backgroundColor' not in dataset:
                    dataset['backgroundColor'] = dataset['borderColor'] + '20'  # 添加透明度
                dataset['fill'] = False
            
            chart_config = {
                'type': 'line',
                'data': {
                    'datasets': datasets
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
                            'text': title,
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
                                'text': '数值'
                            }
                        }
                    }
                }
            }
            
            js_code = f"""
// 趋势图 - {title}
const {chart_id}Config = {json.dumps(chart_config, indent=2)};
const {chart_id}Ctx = document.getElementById('{chart_id}').getContext('2d');
const {chart_id} = new Chart({chart_id}Ctx, {chart_id}Config);
"""
            
            return js_code
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成趋势图失败: {e}")
            return f"// 生成趋势图失败: {e}"
    
    def generate_statistics_chart(self, data: Dict[str, Any], chart_id: str) -> str:
        """
        生成统计图表（复用现有实现）
        
        Args:
            data: 统计数据
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        try:
            title = data.get('title', '统计图表')
            labels = data.get('labels', [])
            datasets = data.get('datasets', [])
            
            # 为数据集分配颜色
            for i, dataset in enumerate(datasets):
                if 'backgroundColor' not in dataset:
                    dataset['backgroundColor'] = self.chart_colors[i % len(self.chart_colors)]
                if 'borderColor' not in dataset:
                    dataset['borderColor'] = dataset['backgroundColor']
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': datasets
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': title,
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
// 统计图表 - {title}
const {chart_id}Config = {json.dumps(chart_config, indent=2)};
const {chart_id}Ctx = document.getElementById('{chart_id}').getContext('2d');
const {chart_id} = new Chart({chart_id}Ctx, {chart_id}Config);
"""
            
            return js_code
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成统计图表失败: {e}")
            return f"// 生成统计图表失败: {e}"
    
    def generate_range_chart(self, data: Dict[str, Any], chart_id: str) -> str:
        """
        生成范围图（Map触发条件范围）
        
        Args:
            data: 范围数据，格式：{
                'title': '图表标题',
                'ranges': [
                    {
                        'label': '范围名称',
                        'min': 最小值,
                        'max': 最大值,
                        'color': '颜色'
                    }
                ]
            }
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        try:
            title = data.get('title', '范围图')
            ranges = data.get('ranges', [])
            
            labels = []
            min_values = []
            max_values = []
            colors = []
            
            for i, range_data in enumerate(ranges):
                labels.append(range_data.get('label', f'范围{i+1}'))
                min_values.append(range_data.get('min', 0))
                max_values.append(range_data.get('max', 0))
                colors.append(range_data.get('color', self.chart_colors[i % len(self.chart_colors)]))
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [
                        {
                            'label': '最小值',
                            'data': min_values,
                            'backgroundColor': [color + '80' for color in colors],
                            'borderColor': colors,
                            'borderWidth': 1
                        },
                        {
                            'label': '最大值',
                            'data': max_values,
                            'backgroundColor': [color + '40' for color in colors],
                            'borderColor': colors,
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
                            'text': title,
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
                                'text': '参数类型'
                            }
                        },
                        'y': {
                            'display': True,
                            'title': {
                                'display': True,
                                'text': '参数值'
                            }
                        }
                    }
                }
            }
            
            js_code = f"""
// 范围图 - {title}
const {chart_id}Config = {json.dumps(chart_config, indent=2)};
const {chart_id}Ctx = document.getElementById('{chart_id}').getContext('2d');
const {chart_id} = new Chart({chart_id}Ctx, {chart_id}Config);
"""
            
            return js_code
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成范围图失败: {e}")
            return f"// 生成范围图失败: {e}"
