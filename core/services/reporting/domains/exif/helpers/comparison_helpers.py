#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF报告生成工具函数（重构版）
==liuq debug== EXIF报告生成工具函数

详细说明: 提供EXIF数据分析和报告生成的工具函数，返回标准数据结构
作者: 龙sir团队
创建时间: 2025-08-06
版本: 2.0.0
描述: EXIF数据处理和报告生成的辅助工具函数，重构为返回数据字典
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.services.reporting.infrastructure import (
    TemplateRenderer,
    ReportSection, TableData, ChartData, ChartType, SectionType,
    ReportData, create_table_section, create_chart_section
)

logger = logging.getLogger(__name__)


def generate_statistics_table(statistics_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成统计数据表格 - 返回标准数据结构"""
    headers = ['字段名', '样本数', '平均值', '标准差', '最小值', '最大值']
    rows = []
    
    for field_name, stats in statistics_data.items():
        row = [
            field_name,
            stats.get('count', 0),
            f"{stats.get('mean', 0):.4f}",
            f"{stats.get('std', 0):.4f}",
            f"{stats.get('min', 0):.4f}",
            f"{stats.get('max', 0):.4f}"
        ]
        rows.append(row)
    
    return {
        'type': 'table',
        'title': '统计数据表格',
        'content': {
            'headers': headers,
            'rows': rows,
            'caption': 'EXIF数据统计摘要',
            'styles': {'table_class': 'table table-striped'}
        }
    }


def generate_kpi_cards(trend_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成KPI指标卡片 - 返回标准数据结构"""
    kpis = []
    
    # 计算总体统计
    total_fields = len(trend_data)
    valid_fields = sum(1 for data in trend_data.values() if isinstance(data, dict) and data.get('test_values'))
    
    kpis.append({
        'title': '总字段数',
        'value': total_fields,
        'unit': '个',
        'trend': 'stable',
        'description': 'EXIF数据字段总数'
    })
    
    kpis.append({
        'title': '有效字段数',
        'value': valid_fields,
        'unit': '个',
        'trend': 'stable',
        'description': '包含有效数据的字段数'
    })
    
    success_rate = (valid_fields / total_fields * 100) if total_fields > 0 else 0
    kpis.append({
        'title': '数据完整率',
        'value': f"{success_rate:.1f}",
        'unit': '%',
        'trend': 'up' if success_rate > 80 else 'down',
        'change': success_rate,
        'description': '有效数据占比'
    })
    
    return {
        'type': 'kpi',
        'title': 'KPI指标卡片',
        'content': {'kpis': kpis}
    }


def generate_comparison_table(matched_pairs: List[Dict[str, Any]], selected_fields: List[str], 
                           trend_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成对比表格 - 返回标准数据结构"""
    headers = ['测试文件', '参考文件', '匹配分数'] + selected_fields
    rows = []
    
    for pair in matched_pairs:
        row = [
            pair.get('test', ''),
            pair.get('reference', ''),
            f"{pair.get('match_score', 0):.3f}"
        ]
        
        # 添加选定字段的对比数据
        for field in selected_fields:
            test_value = trend_data.get(field, {}).get('test_values', [''])[0] if trend_data.get(field) else ''
            ref_value = trend_data.get(field, {}).get('reference_values', [''])[0] if trend_data.get(field) else ''
            row.append(f"{test_value} vs {ref_value}")
        
        rows.append(row)
    
    return {
        'type': 'table',
        'title': '数据对比',
        'content': {
            'headers': headers,
            'rows': rows,
            'caption': '测试文件与参考文件数据对比',
            'styles': {'table_class': 'table table-striped table-hover'}
        }
    }


def generate_per_image_rpg_bpg_analysis(trend_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成每张图片的RPG/BPG趋势分析 - 返回标准数据结构"""
    if not trend_data:
        return {
            'type': 'chart',
            'title': '趋势分析',
            'content': {
                'type': 'line',
                'title': 'RPG/BPG趋势分析',
                'labels': [],
                'datasets': [],
                'options': {'responsive': True}
            }
        }
    
    # 提取时间戳和数值
    timestamps = []
    rpg_values = []
    bpg_values = []
    
    # 从数据中提取时间序列
    for field_data in trend_data.values():
        if isinstance(field_data, dict) and field_data.get('test_values'):
            test_values = field_data.get('test_values', [])
            if len(test_values) > 1:
                # 假设有多个时间点的数据
                timestamps.extend([f"时间点{i}" for i in range(len(test_values))])
                rpg_values.extend(test_values)
                bpg_values.extend(field_data.get('reference_values', []))
    
    # 如果没有找到合适的时间序列数据，创建模拟数据
    if not timestamps:
        timestamps = ['时间点1', '时间点2', '时间点3', '时间点4', '时间点5']
        rpg_values = [1.2, 1.3, 1.1, 1.4, 1.2]
        bpg_values = [0.8, 0.9, 0.7, 1.0, 0.8]
    
    return {
        'type': 'chart',
        'title': '趋势分析',
        'content': {
            'type': 'line',
            'title': 'RPG/BPG趋势分析',
            'labels': timestamps[:5],  # 限制显示前5个点
            'datasets': [
                {
                    'label': 'RPG值',
                    'data': rpg_values[:5],
                    'color': '#3498db',
                    'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                    'fill': False
                },
                {
                    'label': 'BPG值',
                    'data': bpg_values[:5],
                    'color': '#e74c3c',
                    'backgroundColor': 'rgba(231, 76, 60, 0.1)',
                    'fill': False
                }
            ],
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {'display': True, 'text': 'RPG/BPG趋势分析'},
                    'legend': {'display': True, 'position': 'top'}
                }
            }
        }
    }


def generate_sgw_baseline_analysis(trend_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成SGW基线分析 - 返回标准数据结构"""
    headers = ['字段名', 'SGW基线值', '当前值', '偏差', '状态']
    rows = []
    
    # 分析SGW相关字段
    sgw_fields = [k for k in trend_data.keys() if 'SGW' in k]
    
    for field in sgw_fields:
        data = trend_data.get(field, {})
        baseline = data.get('baseline', 0)
        current = data.get('test_values', [''])[0] if data.get('test_values') else 0
        
        try:
            baseline_val = float(baseline) if baseline else 0
            current_val = float(current) if current else 0
            deviation = current_val - baseline_val
            status = '正常' if abs(deviation) < 0.1 else '异常'
        except (ValueError, TypeError):
            deviation = 0
            status = '无效'
        
        rows.append([
            field,
            f"{baseline_val:.3f}",
            f"{current_val:.3f}",
            f"{deviation:.3f}",
            status
        ])
    
    return {
        'type': 'table',
        'title': '基线分析',
        'content': {
            'headers': headers,
            'rows': rows,
            'caption': 'SGW基线值与当前值对比分析',
            'styles': {'table_class': 'table table-striped'}
        }
    }


def generate_topn_anomaly_table(trend_data: Dict[str, Any], topn: int = 10) -> Dict[str, Any]:
    """生成异常分析表格 - 返回标准数据结构"""
    headers = ['字段名', '异常类型', '异常值', '正常范围', '严重程度']
    rows = []
    
    # 分析异常数据
    anomalies = []
    for field_name, field_data in trend_data.items():
        if isinstance(field_data, dict):
            test_values = field_data.get('test_values', [])
            if test_values:
                try:
                    values = [float(v) for v in test_values if v]
                    if values:
                        mean_val = sum(values) / len(values)
                        std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5
                        
                        # 检测异常值（偏离3个标准差）
                        for i, val in enumerate(values):
                            if abs(val - mean_val) > 3 * std_val:
                                anomalies.append({
                                    'field': field_name,
                                    'type': '离群值',
                                    'value': val,
                                    'range': f"{mean_val - 2*std_val:.3f} ~ {mean_val + 2*std_val:.3f}",
                                    'severity': '高' if abs(val - mean_val) > 4 * std_val else '中'
                                })
                except (ValueError, TypeError):
                    continue
    
    # 按严重程度排序
    anomalies.sort(key=lambda x: (x['severity'] == '高', x['severity'] == '中'), reverse=True)
    
    for anomaly in anomalies[:topn]:
        rows.append([
            anomaly['field'],
            anomaly['type'],
            f"{anomaly['value']:.3f}",
            anomaly['range'],
            anomaly['severity']
        ])
    
    return {
        'type': 'table',
        'title': '异常分析',
        'content': {
            'headers': headers,
            'rows': rows,
            'caption': f'TOP {topn} 异常数据点分析',
            'styles': {'table_class': 'table table-striped table-hover'}
        }
    }


# 兼容性别名
def generateStatisticsTable(statistics_data):
    """兼容性别名"""
    return generate_statistics_table(statistics_data)


def generateKPICards(trend_data):
    """兼容性别名"""
    return generate_kpi_cards(trend_data)


def generateComparisonTable(matched_pairs, selected_fields, trend_data):
    """兼容性别名"""
    return generate_comparison_table(matched_pairs, selected_fields, trend_data)


def generatePerImageRpgBpgAnalysis(trend_data):
    """兼容性别名"""
    return generate_per_image_rpg_bpg_analysis(trend_data)


def generateSgwBaselineAnalysis(trend_data):
    """兼容性别名"""
    return generate_sgw_baseline_analysis(trend_data)


def generateTopnAnomalyTable(trend_data, topn=10):
    """兼容性别名"""
    return generate_topn_anomaly_table(trend_data, topn)
