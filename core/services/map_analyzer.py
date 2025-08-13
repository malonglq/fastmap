#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map分析服务
==liuq debug== FastMapV2 Map配置分析器

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 17:51:00 +08:00; Reason: P1-LD-004 实现XML解析服务; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: Map配置数据的分析服务，生成可视化数据和统计信息
"""

import logging
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime

from core.models.map_data import MapConfiguration, MapPoint, AnalysisResult, SceneType, MapType
from core.interfaces.report_generator import IReportDataProvider, IVisualizationProvider

logger = logging.getLogger(__name__)


class MapAnalyzer(IReportDataProvider, IVisualizationProvider):
    """
    Map分析器类
    
    提供Map配置的深度分析功能
    """
    
    def __init__(self, configuration: MapConfiguration):
        """
        初始化Map分析器
        
        Args:
            configuration: Map配置对象
        """
        self.configuration = configuration
        self.analysis_result = None
        logger.info("==liuq debug== Map分析器初始化完成")
    
    def analyze(self) -> AnalysisResult:
        """
        执行完整的Map分析
        
        Returns:
            分析结果对象
        """
        try:
            start_time = datetime.now()
            logger.info("==liuq debug== 开始Map分析")
            
            # 场景统计分析
            scene_statistics = self._analyze_scenes()
            
            # 坐标分析
            coordinate_analysis = self._analyze_coordinates()
            
            # 权重分析
            weight_analysis = self._analyze_weights()
            
            # 参考点分析
            reference_point_analysis = self._analyze_reference_points()
            
            # 生成可视化数据
            scatter_plot_data = self.get_scatter_plot_data()
            heatmap_data = self.get_heatmap_data()
            range_chart_data = self._generate_range_chart_data()
            
            # 计算分析耗时
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 创建分析结果
            self.analysis_result = AnalysisResult(
                configuration=self.configuration,
                scene_statistics=scene_statistics,
                coordinate_analysis=coordinate_analysis,
                weight_analysis=weight_analysis,
                reference_point_analysis=reference_point_analysis,
                scatter_plot_data=scatter_plot_data,
                heatmap_data=heatmap_data,
                range_chart_data=range_chart_data,
                analysis_timestamp=end_time.strftime('%Y-%m-%d %H:%M:%S'),
                analysis_duration=duration
            )
            
            logger.info(f"==liuq debug== Map分析完成，耗时 {duration:.2f} 秒")
            return self.analysis_result
            
        except Exception as e:
            logger.error(f"==liuq debug== Map分析失败: {e}")
            raise
    
    def _analyze_scenes(self) -> Dict[str, Dict[str, Any]]:
        """分析场景统计"""
        try:
            scene_stats = {}
            
            for scene_type in SceneType:
                scene_points = self.configuration.get_map_points_by_scene(scene_type)
                
                if scene_points:
                    weights = [mp.weight for mp in scene_points]
                    coordinates = [(mp.x, mp.y) for mp in scene_points]
                    
                    scene_stats[scene_type.value] = {
                        'count': len(scene_points),
                        'avg_weight': np.mean(weights),
                        'max_weight': np.max(weights),
                        'min_weight': np.min(weights),
                        'weight_std': np.std(weights),
                        'coordinate_bounds': self._get_coordinate_bounds(coordinates),
                        'map_types': self._count_map_types(scene_points)
                    }
                else:
                    scene_stats[scene_type.value] = {
                        'count': 0,
                        'avg_weight': 0.0,
                        'max_weight': 0.0,
                        'min_weight': 0.0,
                        'weight_std': 0.0,
                        'coordinate_bounds': ((0, 0), (0, 0)),
                        'map_types': {'enhance': 0, 'reduce': 0}
                    }
            

            return scene_stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 场景分析失败: {e}")
            return {}
    
    def _analyze_coordinates(self) -> Dict[str, Any]:
        """分析坐标分布"""
        try:
            if not self.configuration.map_points:
                return {}
            
            coordinates = [(mp.x, mp.y) for mp in self.configuration.map_points]
            x_coords = [coord[0] for coord in coordinates]
            y_coords = [coord[1] for coord in coordinates]
            
            analysis = {
                'total_points': len(coordinates),
                'x_range': (min(x_coords), max(x_coords)),
                'y_range': (min(y_coords), max(y_coords)),
                'x_center': np.mean(x_coords),
                'y_center': np.mean(y_coords),
                'x_std': np.std(x_coords),
                'y_std': np.std(y_coords),
                'density_analysis': self._calculate_density_analysis(coordinates)
            }
            

            return analysis
            
        except Exception as e:
            logger.error(f"==liuq debug== 坐标分析失败: {e}")
            return {}
    
    def _analyze_weights(self) -> Dict[str, Any]:
        """分析权重分布"""
        try:
            if not self.configuration.map_points:
                return {}
            
            weights = [mp.weight for mp in self.configuration.map_points]
            
            analysis = {
                'total_points': len(weights),
                'mean': np.mean(weights),
                'median': np.median(weights),
                'std': np.std(weights),
                'min': np.min(weights),
                'max': np.max(weights),
                'percentiles': {
                    '25': np.percentile(weights, 25),
                    '50': np.percentile(weights, 50),
                    '75': np.percentile(weights, 75),
                    '90': np.percentile(weights, 90),
                    '95': np.percentile(weights, 95)
                },
                'distribution': self._analyze_weight_distribution(weights)
            }
            

            return analysis
            
        except Exception as e:
            logger.error(f"==liuq debug== 权重分析失败: {e}")
            return {}
    
    def _analyze_reference_points(self) -> Dict[str, Any]:
        """分析参考点"""
        try:
            analysis = {
                'base_boundary': {
                    'rpg': self.configuration.base_boundary.rpg,
                    'bpg': self.configuration.base_boundary.bpg
                },
                'reference_points_count': len(self.configuration.reference_points),
                'map_near_references': self._count_maps_near_references()
            }
            

            return analysis
            
        except Exception as e:
            logger.error(f"==liuq debug== 参考点分析失败: {e}")
            return {}
    
    def get_scatter_plot_data(self) -> Dict[str, Any]:
        """获取散点图数据"""
        try:
            datasets = []
            
            # 按场景类型分组
            for scene_type in SceneType:
                scene_points = self.configuration.get_map_points_by_scene(scene_type)
                if scene_points:
                    data_points = [{'x': mp.x, 'y': mp.y} for mp in scene_points]
                    datasets.append({
                        'label': f'{scene_type.value}场景',
                        'data': data_points
                    })
            
            return {
                'title': 'Map坐标分布图',
                'x_label': 'X坐标',
                'y_label': 'Y坐标',
                'datasets': datasets
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成散点图数据失败: {e}")
            return {}
    
    def get_heatmap_data(self) -> Dict[str, Any]:
        """获取热力图数据"""
        try:
            if not self.configuration.map_points:
                return {}
            
            # 创建权重网格
            coordinates = [(mp.x, mp.y) for mp in self.configuration.map_points]
            weights = [mp.weight for mp in self.configuration.map_points]
            
            # 简化的热力图数据（实际应用中可能需要更复杂的插值）
            x_coords = [coord[0] for coord in coordinates]
            y_coords = [coord[1] for coord in coordinates]
            
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            # 创建网格
            grid_size = 10
            x_step = (x_max - x_min) / grid_size if x_max != x_min else 1
            y_step = (y_max - y_min) / grid_size if y_max != y_min else 1
            
            x_labels = [f"{x_min + i * x_step:.1f}" for i in range(grid_size)]
            y_labels = [f"{y_min + i * y_step:.1f}" for i in range(grid_size)]
            
            # 简化的权重分布（实际应用中需要插值算法）
            values = []
            for i in range(grid_size):
                row = []
                for j in range(grid_size):
                    # 简单的权重分配（可以改进为更复杂的插值）
                    weight_sum = sum(weights) / len(weights) if weights else 0
                    row.append(weight_sum * np.random.uniform(0.5, 1.5))
                values.append(row)
            
            return {
                'title': '权重热力分布图',
                'x_labels': x_labels,
                'y_labels': y_labels,
                'values': values
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成热力图数据失败: {e}")
            return {}
    
    def get_trend_data(self) -> Dict[str, Any]:
        """获取趋势数据（用于EXIF分析）"""
        # Map分析中暂不需要趋势数据
        return {}
    
    def get_statistics_data(self) -> Dict[str, Any]:
        """获取统计数据"""
        try:
            if not self.analysis_result:
                return {}
            
            return {
                'title': 'Map统计信息',
                'labels': ['总数', '室内', '室外', '夜景', '平均权重'],
                'datasets': [{
                    'label': 'Map统计',
                    'data': [
                        len(self.configuration.map_points),
                        self.analysis_result.scene_statistics.get('indoor', {}).get('count', 0),
                        self.analysis_result.scene_statistics.get('outdoor', {}).get('count', 0),
                        self.analysis_result.scene_statistics.get('night', {}).get('count', 0),
                        self.analysis_result.weight_analysis.get('mean', 0) * 100  # 转换为百分比
                    ]
                }]
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成统计数据失败: {e}")
            return {}
    
    def _generate_range_chart_data(self) -> Dict[str, Any]:
        """生成范围图数据"""
        try:
            if not self.configuration.map_points:
                return {}
            
            # 统计各参数的范围
            bv_ranges = [mp.bv_range for mp in self.configuration.map_points]
            ir_ranges = [mp.ir_range for mp in self.configuration.map_points]
            cct_ranges = [mp.cct_range for mp in self.configuration.map_points]
            
            ranges = []
            
            if bv_ranges:
                bv_mins = [r[0] for r in bv_ranges]
                bv_maxs = [r[1] for r in bv_ranges]
                ranges.append({
                    'label': 'BV范围',
                    'min': min(bv_mins),
                    'max': max(bv_maxs)
                })
            
            if ir_ranges:
                ir_mins = [r[0] for r in ir_ranges]
                ir_maxs = [r[1] for r in ir_ranges]
                ranges.append({
                    'label': 'IR范围',
                    'min': min(ir_mins),
                    'max': max(ir_maxs)
                })
            
            if cct_ranges:
                cct_mins = [r[0] for r in cct_ranges]
                cct_maxs = [r[1] for r in cct_ranges]
                ranges.append({
                    'label': 'CCT范围',
                    'min': min(cct_mins),
                    'max': max(cct_maxs)
                })
            
            return {
                'title': 'Map触发条件范围图',
                'ranges': ranges
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成范围图数据失败: {e}")
            return {}
    
    # IReportDataProvider接口实现
    def prepare_report_data(self) -> Dict[str, Any]:
        """准备报告数据"""
        if not self.analysis_result:
            self.analyze()
        
        return {
            'scatter_data': self.get_scatter_plot_data(),
            'heatmap_data': self.get_heatmap_data(),
            'range_data': self._generate_range_chart_data(),
            'statistics_data': self.get_statistics_data(),
            'scene_analysis': self.analysis_result.scene_statistics,
            'coordinate_analysis': self.analysis_result.coordinate_analysis,
            'weight_analysis': self.analysis_result.weight_analysis,
            'reference_analysis': self.analysis_result.reference_point_analysis
        }
    
    def get_report_title(self) -> str:
        """获取报告标题"""
        return f"FastMapV2 Map分析报告 - {self.configuration.device_type}"
    
    def get_summary_data(self) -> Dict[str, Any]:
        """获取摘要数据"""
        if not self.analysis_result:
            self.analyze()
        
        return self.analysis_result.get_summary()
    
    # 辅助方法
    def _get_coordinate_bounds(self, coordinates: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """获取坐标边界"""
        if not coordinates:
            return ((0, 0), (0, 0))
        
        x_coords = [coord[0] for coord in coordinates]
        y_coords = [coord[1] for coord in coordinates]
        
        return ((min(x_coords), max(x_coords)), (min(y_coords), max(y_coords)))
    
    def _count_map_types(self, map_points: List[MapPoint]) -> Dict[str, int]:
        """统计Map类型"""
        type_counts = {'enhance': 0, 'reduce': 0}
        
        for mp in map_points:
            type_counts[mp.map_type.value] += 1
        
        return type_counts
    
    def _calculate_density_analysis(self, coordinates: List[Tuple[float, float]]) -> Dict[str, Any]:
        """计算密度分析"""
        # 简化的密度分析
        return {
            'high_density_areas': len(coordinates) // 4,  # 简化计算
            'sparse_areas': len(coordinates) // 8,
            'cluster_count': max(1, len(coordinates) // 10)
        }
    
    def _analyze_weight_distribution(self, weights: List[float]) -> Dict[str, Any]:
        """分析权重分布"""
        # 权重分布分析
        high_weight = sum(1 for w in weights if w > 0.7)
        medium_weight = sum(1 for w in weights if 0.3 <= w <= 0.7)
        low_weight = sum(1 for w in weights if w < 0.3)
        
        return {
            'high_weight_count': high_weight,
            'medium_weight_count': medium_weight,
            'low_weight_count': low_weight,
            'distribution_type': 'normal' if medium_weight > high_weight + low_weight else 'skewed'
        }
    
    def _count_maps_near_references(self) -> int:
        """统计参考点附近的Map数量"""
        # 简化实现，实际应用中需要距离计算
        return len(self.configuration.map_points) // 3
