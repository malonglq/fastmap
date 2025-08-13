#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计计算器
==liuq debug== 统计指标计算和数据分析

提供各种统计计算功能
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math

logger = logging.getLogger(__name__)


class StatisticsCalculator:
    """统计计算器类"""
    
    def __init__(self):
        """初始化统计计算器"""
        logger.info("==liuq debug== 统计计算器初始化完成")
    
    def calculate_descriptive_statistics(self, values: List[float]) -> Dict[str, float]:
        """
        计算描述性统计
        
        Args:
            values: 数值列表
            
        Returns:
            描述性统计结果字典
        """
        try:
            if not values:
                return {}
            
            values_array = np.array(values)
            valid_values = values_array[~np.isnan(values_array)]
            
            if len(valid_values) == 0:
                return {}
            
            stats = {
                # 基本统计量
                'count': len(valid_values),
                'mean': float(np.mean(valid_values)),
                'median': float(np.median(valid_values)),
                'mode': self.calculate_mode(valid_values),
                'std': float(np.std(valid_values, ddof=1)) if len(valid_values) > 1 else 0,
                'variance': float(np.var(valid_values, ddof=1)) if len(valid_values) > 1 else 0,
                
                # 极值
                'min': float(np.min(valid_values)),
                'max': float(np.max(valid_values)),
                'range': float(np.max(valid_values) - np.min(valid_values)),
                
                # 分位数
                'q1': float(np.percentile(valid_values, 25)),
                'q2': float(np.percentile(valid_values, 50)),  # 中位数
                'q3': float(np.percentile(valid_values, 75)),
                'iqr': float(np.percentile(valid_values, 75) - np.percentile(valid_values, 25)),
                
                # 其他百分位数
                'p5': float(np.percentile(valid_values, 5)),
                'p10': float(np.percentile(valid_values, 10)),
                'p90': float(np.percentile(valid_values, 90)),
                'p95': float(np.percentile(valid_values, 95)),
                
                # 形状统计量
                'skewness': self.calculate_skewness(valid_values),
                'kurtosis': self.calculate_kurtosis(valid_values),
                
                # 相对统计量
                'cv': self.calculate_coefficient_of_variation(valid_values),
                'mad': self.calculate_mad(valid_values),  # 平均绝对偏差
                'sem': self.calculate_sem(valid_values)   # 标准误差
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 描述性统计计算失败: {e}")
            return {}
    
    def calculate_mode(self, values: np.ndarray) -> float:
        """计算众数"""
        try:
            from scipy import stats
            mode_result = stats.mode(values, keepdims=True)
            return float(mode_result.mode[0])
        except:
            # 如果scipy不可用，使用简单方法
            unique, counts = np.unique(values, return_counts=True)
            return float(unique[np.argmax(counts)])
    
    def calculate_skewness(self, values: np.ndarray) -> float:
        """计算偏度"""
        try:
            if len(values) < 3:
                return 0.0
            
            mean = np.mean(values)
            std = np.std(values, ddof=1)
            
            if std == 0:
                return 0.0
            
            n = len(values)
            skewness = (n / ((n - 1) * (n - 2))) * np.sum(((values - mean) / std) ** 3)
            return float(skewness)
            
        except Exception as e:
            logger.warning(f"==liuq debug== 偏度计算失败: {e}")
            return 0.0
    
    def calculate_kurtosis(self, values: np.ndarray) -> float:
        """计算峰度"""
        try:
            if len(values) < 4:
                return 0.0
            
            mean = np.mean(values)
            std = np.std(values, ddof=1)
            
            if std == 0:
                return 0.0
            
            n = len(values)
            kurtosis = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * np.sum(((values - mean) / std) ** 4) - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
            return float(kurtosis)
            
        except Exception as e:
            logger.warning(f"==liuq debug== 峰度计算失败: {e}")
            return 0.0
    
    def calculate_coefficient_of_variation(self, values: np.ndarray) -> float:
        """计算变异系数"""
        try:
            mean = np.mean(values)
            std = np.std(values, ddof=1)
            
            if mean == 0:
                return 0.0
            
            return float(std / abs(mean))
            
        except Exception as e:
            logger.warning(f"==liuq debug== 变异系数计算失败: {e}")
            return 0.0
    
    def calculate_mad(self, values: np.ndarray) -> float:
        """计算平均绝对偏差"""
        try:
            mean = np.mean(values)
            mad = np.mean(np.abs(values - mean))
            return float(mad)
            
        except Exception as e:
            logger.warning(f"==liuq debug== 平均绝对偏差计算失败: {e}")
            return 0.0
    
    def calculate_sem(self, values: np.ndarray) -> float:
        """计算标准误差"""
        try:
            if len(values) <= 1:
                return 0.0
            
            std = np.std(values, ddof=1)
            sem = std / np.sqrt(len(values))
            return float(sem)
            
        except Exception as e:
            logger.warning(f"==liuq debug== 标准误差计算失败: {e}")
            return 0.0
    
    def calculate_confidence_interval(self, values: List[float], 
                                   confidence_level: float = 0.95) -> Dict[str, float]:
        """
        计算置信区间
        
        Args:
            values: 数值列表
            confidence_level: 置信水平
            
        Returns:
            置信区间结果
        """
        try:
            if len(values) < 2:
                return {}
            
            values_array = np.array(values)
            valid_values = values_array[~np.isnan(values_array)]
            
            if len(valid_values) < 2:
                return {}
            
            mean = np.mean(valid_values)
            sem = self.calculate_sem(valid_values)
            
            # 使用t分布
            from scipy import stats
            alpha = 1 - confidence_level
            df = len(valid_values) - 1
            t_critical = stats.t.ppf(1 - alpha/2, df)
            
            margin_error = t_critical * sem
            
            return {
                'mean': float(mean),
                'sem': float(sem),
                'margin_error': float(margin_error),
                'lower_bound': float(mean - margin_error),
                'upper_bound': float(mean + margin_error),
                'confidence_level': confidence_level,
                'degrees_freedom': df
            }
            
        except ImportError:
            # 如果scipy不可用，使用正态分布近似
            try:
                mean = np.mean(valid_values)
                sem = self.calculate_sem(valid_values)
                
                # 使用正态分布的临界值
                z_critical = 1.96 if confidence_level == 0.95 else 2.576 if confidence_level == 0.99 else 1.645
                margin_error = z_critical * sem
                
                return {
                    'mean': float(mean),
                    'sem': float(sem),
                    'margin_error': float(margin_error),
                    'lower_bound': float(mean - margin_error),
                    'upper_bound': float(mean + margin_error),
                    'confidence_level': confidence_level,
                    'method': 'normal_approximation'
                }
                
            except Exception as e:
                logger.error(f"==liuq debug== 置信区间计算失败: {e}")
                return {}
        
        except Exception as e:
            logger.error(f"==liuq debug== 置信区间计算失败: {e}")
            return {}
    
    def perform_normality_test(self, values: List[float]) -> Dict[str, Any]:
        """
        正态性检验
        
        Args:
            values: 数值列表
            
        Returns:
            正态性检验结果
        """
        try:
            if len(values) < 8:
                return {'test': 'insufficient_data', 'is_normal': None}
            
            values_array = np.array(values)
            valid_values = values_array[~np.isnan(values_array)]
            
            if len(valid_values) < 8:
                return {'test': 'insufficient_data', 'is_normal': None}
            
            try:
                from scipy import stats
                
                # Shapiro-Wilk检验（适用于小样本）
                if len(valid_values) <= 5000:
                    statistic, p_value = stats.shapiro(valid_values)
                    test_name = 'shapiro_wilk'
                else:
                    # Kolmogorov-Smirnov检验（适用于大样本）
                    statistic, p_value = stats.kstest(valid_values, 'norm')
                    test_name = 'kolmogorov_smirnov'
                
                is_normal = p_value > 0.05
                
                return {
                    'test': test_name,
                    'statistic': float(statistic),
                    'p_value': float(p_value),
                    'is_normal': is_normal,
                    'alpha': 0.05,
                    'sample_size': len(valid_values)
                }
                
            except ImportError:
                # 如果scipy不可用，使用简单的正态性指标
                skewness = self.calculate_skewness(valid_values)
                kurtosis = self.calculate_kurtosis(valid_values)
                
                # 简单判断：偏度和峰度都接近0表示接近正态分布
                is_normal = abs(skewness) < 1 and abs(kurtosis) < 1
                
                return {
                    'test': 'simple_check',
                    'skewness': float(skewness),
                    'kurtosis': float(kurtosis),
                    'is_normal': is_normal,
                    'note': 'Based on skewness and kurtosis only'
                }
                
        except Exception as e:
            logger.error(f"==liuq debug== 正态性检验失败: {e}")
            return {'test': 'failed', 'error': str(e)}
    
    def calculate_effect_size(self, values1: List[float], 
                            values2: List[float]) -> Dict[str, float]:
        """
        计算效应量
        
        Args:
            values1: 第一组数值
            values2: 第二组数值
            
        Returns:
            效应量结果
        """
        try:
            if not values1 or not values2:
                return {}
            
            array1 = np.array(values1)
            array2 = np.array(values2)
            
            valid1 = array1[~np.isnan(array1)]
            valid2 = array2[~np.isnan(array2)]
            
            if len(valid1) == 0 or len(valid2) == 0:
                return {}
            
            mean1 = np.mean(valid1)
            mean2 = np.mean(valid2)
            std1 = np.std(valid1, ddof=1)
            std2 = np.std(valid2, ddof=1)
            
            # Cohen's d
            pooled_std = np.sqrt(((len(valid1) - 1) * std1**2 + (len(valid2) - 1) * std2**2) / 
                               (len(valid1) + len(valid2) - 2))
            
            cohens_d = (mean2 - mean1) / pooled_std if pooled_std != 0 else 0
            
            # Glass's delta
            glass_delta = (mean2 - mean1) / std1 if std1 != 0 else 0
            
            # Hedges' g (修正的Cohen's d)
            j = 1 - (3 / (4 * (len(valid1) + len(valid2)) - 9))
            hedges_g = cohens_d * j
            
            return {
                'cohens_d': float(cohens_d),
                'glass_delta': float(glass_delta),
                'hedges_g': float(hedges_g),
                'pooled_std': float(pooled_std),
                'mean_difference': float(mean2 - mean1),
                'interpretation': self.interpret_effect_size(abs(cohens_d))
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 效应量计算失败: {e}")
            return {}
    
    def interpret_effect_size(self, effect_size: float) -> str:
        """解释效应量大小"""
        if effect_size < 0.2:
            return 'negligible'
        elif effect_size < 0.5:
            return 'small'
        elif effect_size < 0.8:
            return 'medium'
        else:
            return 'large'
    
    def calculate_percentage_changes(self, values_before: List[float], 
                                   values_after: List[float]) -> Dict[str, Any]:
        """
        计算百分比变化统计
        
        Args:
            values_before: 变化前数值
            values_after: 变化后数值
            
        Returns:
            百分比变化统计结果
        """
        try:
            if len(values_before) != len(values_after):
                return {}
            
            percentage_changes = []
            absolute_changes = []
            
            for before, after in zip(values_before, values_after):
                if pd.notna(before) and pd.notna(after):
                    absolute_change = after - before
                    absolute_changes.append(absolute_change)
                    
                    if before != 0:
                        percentage_change = (absolute_change / before) * 100
                        percentage_changes.append(percentage_change)
                    elif after == 0:
                        percentage_changes.append(0)
                    # 如果before=0但after!=0，跳过这个点
            
            if not percentage_changes:
                return {}
            
            # 计算统计量
            stats = {
                'absolute_changes': self.calculate_descriptive_statistics(absolute_changes),
                'percentage_changes': self.calculate_descriptive_statistics(percentage_changes),
                'change_distribution': self.analyze_change_distribution(percentage_changes),
                'summary': {
                    'total_pairs': len(values_before),
                    'valid_changes': len(percentage_changes),
                    'positive_changes': sum(1 for c in percentage_changes if c > 0),
                    'negative_changes': sum(1 for c in percentage_changes if c < 0),
                    'no_changes': sum(1 for c in percentage_changes if c == 0)
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 百分比变化计算失败: {e}")
            return {}
    
    def analyze_change_distribution(self, percentage_changes: List[float]) -> Dict[str, int]:
        """分析变化分布"""
        try:
            distribution = {
                'extreme_decrease': 0,  # < -50%
                'large_decrease': 0,    # -50% to -10%
                'moderate_decrease': 0, # -10% to -1%
                'small_decrease': 0,    # -1% to 0%
                'no_change': 0,         # 0%
                'small_increase': 0,    # 0% to 1%
                'moderate_increase': 0, # 1% to 10%
                'large_increase': 0,    # 10% to 50%
                'extreme_increase': 0   # > 50%
            }
            
            for change in percentage_changes:
                if change < -50:
                    distribution['extreme_decrease'] += 1
                elif change < -10:
                    distribution['large_decrease'] += 1
                elif change < -1:
                    distribution['moderate_decrease'] += 1
                elif change < 0:
                    distribution['small_decrease'] += 1
                elif change == 0:
                    distribution['no_change'] += 1
                elif change <= 1:
                    distribution['small_increase'] += 1
                elif change <= 10:
                    distribution['moderate_increase'] += 1
                elif change <= 50:
                    distribution['large_increase'] += 1
                else:
                    distribution['extreme_increase'] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"==liuq debug== 变化分布分析失败: {e}")
            return {}
    
    def generate_summary_report(self, statistics_results: Dict[str, Any]) -> str:
        """
        生成统计摘要报告
        
        Args:
            statistics_results: 统计结果字典
            
        Returns:
            摘要报告文本
        """
        try:
            report_lines = []
            report_lines.append("=== 统计分析摘要报告 ===")
            report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # 基本统计信息
            if 'descriptive_stats' in statistics_results:
                stats = statistics_results['descriptive_stats']
                report_lines.append("描述性统计:")
                report_lines.append(f"  样本数量: {stats.get('count', 0)}")
                report_lines.append(f"  平均值: {stats.get('mean', 0):.4f}")
                report_lines.append(f"  中位数: {stats.get('median', 0):.4f}")
                report_lines.append(f"  标准差: {stats.get('std', 0):.4f}")
                report_lines.append(f"  最小值: {stats.get('min', 0):.4f}")
                report_lines.append(f"  最大值: {stats.get('max', 0):.4f}")
                report_lines.append("")
            
            # 变化分析
            if 'change_analysis' in statistics_results:
                change = statistics_results['change_analysis']
                summary = change.get('summary', {})
                report_lines.append("变化分析:")
                report_lines.append(f"  总数据对: {summary.get('total_pairs', 0)}")
                report_lines.append(f"  有效变化: {summary.get('valid_changes', 0)}")
                report_lines.append(f"  正向变化: {summary.get('positive_changes', 0)}")
                report_lines.append(f"  负向变化: {summary.get('negative_changes', 0)}")
                report_lines.append(f"  无变化: {summary.get('no_changes', 0)}")
                report_lines.append("")
            
            # 效应量
            if 'effect_size' in statistics_results:
                effect = statistics_results['effect_size']
                report_lines.append("效应量分析:")
                report_lines.append(f"  Cohen's d: {effect.get('cohens_d', 0):.4f}")
                report_lines.append(f"  效应大小: {effect.get('interpretation', '未知')}")
                report_lines.append(f"  平均差异: {effect.get('mean_difference', 0):.4f}")
                report_lines.append("")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成摘要报告失败: {e}")
            return f"生成摘要报告失败: {e}"
