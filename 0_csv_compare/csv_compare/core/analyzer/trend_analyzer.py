#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势分析器
==liuq debug== 数据趋势分析算法

实现数据变化趋势分析和计算
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from utils.config_manager import ConfigManager, ThresholdConfig

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """趋势分析器类"""
    
    def __init__(self):
        """初始化趋势分析器"""
        self.analysis_results = {}
        self.trend_data = {}

        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.load_thresholds_from_config()

        # 注册为配置观察者
        self.config_manager.register_observer(self.on_config_updated)

        logger.info("==liuq debug== 趋势分析器初始化完成")

    def load_thresholds_from_config(self):
        """从配置管理器加载阈值"""
        try:
            config = self.config_manager.get_config()

            # 加载百分比阈值用于变化分类
            self.large_threshold = config.percentage_large_min
            self.medium_threshold_min = config.percentage_medium_min
            self.medium_threshold_max = config.percentage_medium_max
            self.small_threshold = config.percentage_small_max

            logger.info(f"==liuq debug== 阈值配置: 大变化>{self.large_threshold}%, "
                        f"中变化{self.medium_threshold_min}%-{self.medium_threshold_max}%, "
                        f"小变化<{self.small_threshold}%")

        except Exception as e:
            logger.error(f"==liuq debug== 从配置加载阈值失败: {e}")
            # 使用默认值
            self.large_threshold = 10.0
            self.medium_threshold_min = 1.0
            self.medium_threshold_max = 10.0
            self.small_threshold = 1.0

    def on_config_updated(self, config: ThresholdConfig):
        """配置更新回调"""
        try:
            logger.info("==liuq debug== 趋势分析器收到配置更新通知")
            self.load_thresholds_from_config()
        except Exception as e:
            logger.error(f"==liuq debug== 处理配置更新失败: {e}")
    
    def analyze_field_trends(self, matched_data: List[Dict[str, Any]], 
                           selected_fields: List[str]) -> Dict[str, Any]:
        """
        分析字段趋势
        
        Args:
            matched_data: 匹配的数据对列表
            selected_fields: 选择的分析字段
            
        Returns:
            趋势分析结果字典
        """
        try:
            logger.info(f"==liuq debug== 开始分析字段趋势，字段数: {len(selected_fields)}")
            
            analysis_results = {
                'field_analyses': {},
                'summary': {
                    'total_pairs': len(matched_data),
                    'analyzed_fields': len(selected_fields),
                    'analysis_time': datetime.now().isoformat()
                },
                'trend_data': {}
            }
            
            for field in selected_fields:
                logger.info(f"==liuq debug== 分析字段: {field}")
                field_analysis = self.analyze_single_field(matched_data, field)
                analysis_results['field_analyses'][field] = field_analysis
                
                # 生成趋势数据用于图表
                trend_data = self.generate_trend_data(matched_data, field)
                analysis_results['trend_data'][field] = trend_data
            
            # 计算整体统计
            overall_stats = self.calculate_overall_statistics(analysis_results['field_analyses'])
            analysis_results['overall_statistics'] = overall_stats
            
            self.analysis_results = analysis_results
            logger.info("==liuq debug== 字段趋势分析完成")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"==liuq debug== 字段趋势分析失败: {e}")
            raise
    
    def analyze_single_field(self, matched_data: List[Dict[str, Any]], 
                           field: str) -> Dict[str, Any]:
        """
        分析单个字段
        
        Args:
            matched_data: 匹配的数据对列表
            field: 字段名
            
        Returns:
            单字段分析结果
        """
        try:
            values_before = []
            values_after = []
            changes = []
            change_percentages = []
            valid_pairs = 0
            
            for pair in matched_data:
                try:
                    row1 = pair['row1']
                    row2 = pair['row2']
                    
                    if field in row1.index and field in row2.index:
                        val1 = pd.to_numeric(row1[field], errors='coerce')
                        val2 = pd.to_numeric(row2[field], errors='coerce')
                        
                        if pd.notna(val1) and pd.notna(val2):
                            values_before.append(val1)
                            values_after.append(val2)
                            
                            change = val2 - val1
                            changes.append(change)
                            
                            # 计算变化百分比
                            if val1 != 0:
                                change_percent = (change / val1) * 100
                            else:
                                change_percent = 0 if change == 0 else float('inf')
                            
                            change_percentages.append(change_percent)
                            valid_pairs += 1
                            
                except Exception as e:
                    logger.warning(f"==liuq debug== 处理数据对失败: {e}")
                    continue
            
            if not values_before:
                return {
                    'field_name': field,
                    'valid_pairs': 0,
                    'error': '没有有效的数值数据'
                }
            
            # 计算统计指标
            analysis_result = {
                'field_name': field,
                'valid_pairs': valid_pairs,
                'before_stats': self.calculate_statistics(values_before),
                'after_stats': self.calculate_statistics(values_after),
                'change_stats': self.calculate_change_statistics(changes, change_percentages),
                'trend_classification': self.classify_trend(changes),
                'outliers': self.detect_outliers(changes),
                'correlation': self.calculate_correlation(values_before, values_after)
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"==liuq debug== 单字段分析失败: {e}")
            return {
                'field_name': field,
                'valid_pairs': 0,
                'error': str(e)
            }
    
    def calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """
        计算基础统计指标
        
        Args:
            values: 数值列表
            
        Returns:
            统计指标字典
        """
        try:
            if not values:
                return {}
            
            values_array = np.array(values)
            
            stats = {
                'count': len(values),
                'mean': float(np.mean(values_array)),
                'median': float(np.median(values_array)),
                'std': float(np.std(values_array)),
                'min': float(np.min(values_array)),
                'max': float(np.max(values_array)),
                'q25': float(np.percentile(values_array, 25)),
                'q75': float(np.percentile(values_array, 75)),
                'range': float(np.max(values_array) - np.min(values_array))
            }
            
            # 计算变异系数
            if stats['mean'] != 0:
                stats['cv'] = stats['std'] / abs(stats['mean'])
            else:
                stats['cv'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 统计计算失败: {e}")
            return {}
    
    def calculate_change_statistics(self, changes: List[float], 
                                  change_percentages: List[float]) -> Dict[str, Any]:
        """
        计算变化统计指标
        
        Args:
            changes: 绝对变化列表
            change_percentages: 百分比变化列表
            
        Returns:
            变化统计指标字典
        """
        try:
            if not changes:
                return {}
            
            # 过滤无穷值
            finite_percentages = [p for p in change_percentages if np.isfinite(p)]
            
            change_stats = {
                'absolute_change': self.calculate_statistics(changes),
                'percentage_change': self.calculate_statistics(finite_percentages) if finite_percentages else {},
                'positive_changes': sum(1 for c in changes if c > 0),
                'negative_changes': sum(1 for c in changes if c < 0),
                'no_changes': sum(1 for c in changes if c == 0),
                'total_changes': len(changes)
            }
            
            # 计算变化比例
            if change_stats['total_changes'] > 0:
                change_stats['positive_ratio'] = change_stats['positive_changes'] / change_stats['total_changes']
                change_stats['negative_ratio'] = change_stats['negative_changes'] / change_stats['total_changes']
                change_stats['no_change_ratio'] = change_stats['no_changes'] / change_stats['total_changes']
            
            # 分类变化幅度
            change_stats['change_categories'] = self.categorize_changes(finite_percentages)
            
            return change_stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 变化统计计算失败: {e}")
            return {}
    
    def categorize_changes(self, change_percentages: List[float]) -> Dict[str, int]:
        """
        分类变化幅度
        
        Args:
            change_percentages: 百分比变化列表
            
        Returns:
            变化分类统计
        """
        try:
            categories = {
                'large_increase': 0,    # >large_threshold%
                'medium_increase': 0,   # medium_min%-large_threshold%
                'small_increase': 0,    # 0-small_threshold%
                'no_change': 0,         # 0%
                'small_decrease': 0,    # 0 to -small_threshold%
                'medium_decrease': 0,   # -small_threshold% to -large_threshold%
                'large_decrease': 0     # <-large_threshold%
            }

            for change in change_percentages:
                if change > self.large_threshold:
                    categories['large_increase'] += 1
                elif change > self.medium_threshold_min:
                    categories['medium_increase'] += 1
                elif change > 0:
                    categories['small_increase'] += 1
                elif change == 0:
                    categories['no_change'] += 1
                elif change > -self.small_threshold:
                    categories['small_decrease'] += 1
                elif change > -self.large_threshold:
                    categories['medium_decrease'] += 1
                else:
                    categories['large_decrease'] += 1
            
            return categories
            
        except Exception as e:
            logger.error(f"==liuq debug== 变化分类失败: {e}")
            return {}
    
    def classify_trend(self, changes: List[float]) -> Dict[str, Any]:
        """
        分类趋势
        
        Args:
            changes: 变化列表
            
        Returns:
            趋势分类结果
        """
        try:
            if not changes:
                return {'trend': 'unknown', 'confidence': 0}
            
            positive_count = sum(1 for c in changes if c > 0)
            negative_count = sum(1 for c in changes if c < 0)
            zero_count = sum(1 for c in changes if c == 0)
            total_count = len(changes)
            
            positive_ratio = positive_count / total_count
            negative_ratio = negative_count / total_count
            
            # 趋势分类
            if positive_ratio > 0.7:
                trend = 'increasing'
                confidence = positive_ratio
            elif negative_ratio > 0.7:
                trend = 'decreasing'
                confidence = negative_ratio
            elif abs(positive_ratio - negative_ratio) < 0.2:
                trend = 'stable'
                confidence = 1 - abs(positive_ratio - negative_ratio)
            else:
                trend = 'mixed'
                confidence = max(positive_ratio, negative_ratio)
            
            return {
                'trend': trend,
                'confidence': confidence,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'zero_ratio': zero_count / total_count
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 趋势分类失败: {e}")
            return {'trend': 'unknown', 'confidence': 0}
    
    def detect_outliers(self, values: List[float]) -> Dict[str, Any]:
        """
        检测异常值
        
        Args:
            values: 数值列表
            
        Returns:
            异常值检测结果
        """
        try:
            if len(values) < 4:
                return {'outliers': [], 'outlier_count': 0}
            
            values_array = np.array(values)
            q1 = np.percentile(values_array, 25)
            q3 = np.percentile(values_array, 75)
            iqr = q3 - q1
            
            # IQR方法检测异常值
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = []
            for i, value in enumerate(values):
                if value < lower_bound or value > upper_bound:
                    outliers.append({
                        'index': i,
                        'value': value,
                        'type': 'low' if value < lower_bound else 'high'
                    })
            
            return {
                'outliers': outliers,
                'outlier_count': len(outliers),
                'outlier_ratio': len(outliers) / len(values),
                'bounds': {
                    'lower': lower_bound,
                    'upper': upper_bound,
                    'q1': q1,
                    'q3': q3,
                    'iqr': iqr
                }
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 异常值检测失败: {e}")
            return {'outliers': [], 'outlier_count': 0}
    
    def calculate_correlation(self, values1: List[float], 
                            values2: List[float]) -> Dict[str, float]:
        """
        计算相关性
        
        Args:
            values1: 第一组数值
            values2: 第二组数值
            
        Returns:
            相关性结果
        """
        try:
            if len(values1) != len(values2) or len(values1) < 2:
                return {'correlation': 0, 'p_value': 1}
            
            # 计算皮尔逊相关系数
            correlation = np.corrcoef(values1, values2)[0, 1]
            
            # 简单的显著性检验（需要更复杂的统计方法）
            n = len(values1)
            t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2))
            
            return {
                'correlation': float(correlation) if not np.isnan(correlation) else 0,
                't_statistic': float(t_stat) if not np.isnan(t_stat) else 0,
                'sample_size': n
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 相关性计算失败: {e}")
            return {'correlation': 0, 'sample_size': 0}
    
    def generate_trend_data(self, matched_data: List[Dict[str, Any]], 
                          field: str) -> Dict[str, Any]:
        """
        生成趋势数据用于图表
        
        Args:
            matched_data: 匹配的数据对列表
            field: 字段名
            
        Returns:
            趋势数据字典
        """
        try:
            chart_data = {
                'labels': [],
                'before_values': [],
                'after_values': [],
                'changes': [],
                'change_percentages': []
            }
            
            for i, pair in enumerate(matched_data):
                try:
                    row1 = pair['row1']
                    row2 = pair['row2']
                    
                    if field in row1.index and field in row2.index:
                        val1 = pd.to_numeric(row1[field], errors='coerce')
                        val2 = pd.to_numeric(row2[field], errors='coerce')
                        
                        if pd.notna(val1) and pd.notna(val2):
                            # 使用文件名作为标签
                            label = pair.get('filename1', f'数据点{i+1}')
                            
                            chart_data['labels'].append(label)
                            chart_data['before_values'].append(float(val1))
                            chart_data['after_values'].append(float(val2))
                            
                            change = val2 - val1
                            chart_data['changes'].append(float(change))
                            
                            if val1 != 0:
                                change_percent = (change / val1) * 100
                            else:
                                change_percent = 0
                            chart_data['change_percentages'].append(float(change_percent))
                            
                except Exception as e:
                    logger.warning(f"==liuq debug== 生成图表数据点失败: {e}")
                    continue
            
            return chart_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成趋势数据失败: {e}")
            return {}
    
    def calculate_overall_statistics(self, field_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算整体统计
        
        Args:
            field_analyses: 字段分析结果字典
            
        Returns:
            整体统计结果
        """
        try:
            overall_stats = {
                'total_fields': len(field_analyses),
                'successful_analyses': 0,
                'failed_analyses': 0,
                'trend_summary': {
                    'increasing': 0,
                    'decreasing': 0,
                    'stable': 0,
                    'mixed': 0
                },
                'average_change_ratios': {
                    'positive': 0,
                    'negative': 0,
                    'no_change': 0
                }
            }
            
            valid_analyses = []
            
            for field, analysis in field_analyses.items():
                if 'error' in analysis:
                    overall_stats['failed_analyses'] += 1
                else:
                    overall_stats['successful_analyses'] += 1
                    valid_analyses.append(analysis)
                    
                    # 统计趋势
                    trend = analysis.get('trend_classification', {}).get('trend', 'unknown')
                    if trend in overall_stats['trend_summary']:
                        overall_stats['trend_summary'][trend] += 1
            
            # 计算平均变化比例
            if valid_analyses:
                total_positive = sum(a.get('change_stats', {}).get('positive_ratio', 0) for a in valid_analyses)
                total_negative = sum(a.get('change_stats', {}).get('negative_ratio', 0) for a in valid_analyses)
                total_no_change = sum(a.get('change_stats', {}).get('no_change_ratio', 0) for a in valid_analyses)
                
                count = len(valid_analyses)
                overall_stats['average_change_ratios'] = {
                    'positive': total_positive / count,
                    'negative': total_negative / count,
                    'no_change': total_no_change / count
                }
            
            return overall_stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 整体统计计算失败: {e}")
            return {}
    
    def get_analysis_results(self) -> Dict[str, Any]:
        """
        获取分析结果
        
        Returns:
            分析结果字典
        """
        return self.analysis_results.copy()

    def cleanup(self):
        """清理资源"""
        try:
            # 取消注册配置观察者
            self.config_manager.unregister_observer(self.on_config_updated)

        except Exception as e:
            logger.error(f"==liuq debug== 清理趋势分析器资源失败: {e}")
    
    def export_analysis_summary(self) -> str:
        """
        导出分析摘要
        
        Returns:
            分析摘要文本
        """
        try:
            if not self.analysis_results:
                return "没有分析结果"
            
            summary_lines = []
            summary_lines.append("=== CSV数据对比分析摘要 ===")
            summary_lines.append(f"分析时间: {self.analysis_results['summary']['analysis_time']}")
            summary_lines.append(f"数据对数量: {self.analysis_results['summary']['total_pairs']}")
            summary_lines.append(f"分析字段数: {self.analysis_results['summary']['analyzed_fields']}")
            summary_lines.append("")
            
            # 字段分析摘要
            for field, analysis in self.analysis_results['field_analyses'].items():
                if 'error' in analysis:
                    summary_lines.append(f"字段 {field}: 分析失败 - {analysis['error']}")
                else:
                    trend = analysis.get('trend_classification', {})
                    change_stats = analysis.get('change_stats', {})
                    
                    summary_lines.append(f"字段 {field}:")
                    summary_lines.append(f"  有效数据对: {analysis['valid_pairs']}")
                    summary_lines.append(f"  趋势: {trend.get('trend', '未知')} (置信度: {trend.get('confidence', 0):.2f})")
                    summary_lines.append(f"  正向变化: {change_stats.get('positive_changes', 0)}")
                    summary_lines.append(f"  负向变化: {change_stats.get('negative_changes', 0)}")
                    summary_lines.append("")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            logger.error(f"==liuq debug== 导出分析摘要失败: {e}")
            return f"导出摘要失败: {e}"
