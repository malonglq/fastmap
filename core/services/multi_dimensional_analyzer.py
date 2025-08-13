# {{CHENGQI:
# Action: Added; Timestamp: 2025-08-04 16:35:00 +08:00; Reason: 创建多维度分析器服务以支持Map数据的多维度分析报告功能; Principle_Applied: 单一职责原则和服务层设计;
# }}

"""
多维度分析器服务

提供Map数据的多维度分析功能，支持可配置的场景分类和统计分析
"""

import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
import numpy as np

from core.models.map_data import MapConfiguration, MapPoint, SceneType
from core.models.scene_classification_config import SceneClassificationConfig

logger = logging.getLogger(__name__)


class MultiDimensionalAnalyzer:
    """
    多维度分析器
    
    基于可配置的分类规则对Map数据进行多维度分析
    """
    
    def __init__(self, configuration: MapConfiguration, 
                 classification_config: SceneClassificationConfig = None):
        """
        初始化分析器
        
        Args:
            configuration: Map配置数据
            classification_config: 场景分类配置
        """
        self.configuration = configuration
        self.classification_config = classification_config or SceneClassificationConfig()
        self.analysis_result = None
        
        logger.info("==liuq debug== 多维度分析器初始化完成")
    
    def analyze(self) -> Dict[str, Any]:
        """
        执行多维度分析
        
        Returns:
            分析结果字典
        """
        try:
            start_time = datetime.now()
            logger.info("==liuq debug== 开始多维度分析")
            
            # 1. 场景分类分析
            scene_analysis = self._analyze_scenes()
            
            # 2. 参数分布分析
            parameter_analysis = self._analyze_parameters()
            
            # 3. 分类准确性分析
            accuracy_analysis = self._analyze_classification_accuracy()
            
            # 4. 统计摘要
            summary_stats = self._generate_summary_statistics(scene_analysis)
            
            # 计算分析耗时
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 构建分析结果
            self.analysis_result = {
                'scene_analysis': scene_analysis,
                'parameter_analysis': parameter_analysis,
                'accuracy_analysis': accuracy_analysis,
                'summary_statistics': summary_stats,
                'classification_config': self.classification_config.to_dict(),
                'analysis_metadata': {
                    'timestamp': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_seconds': duration,
                    'total_map_points': len(self.configuration.map_points),
                    'analyzer_version': '1.0.0'
                }
            }
            
            logger.info(f"==liuq debug== 多维度分析完成，耗时 {duration:.2f} 秒")
            return self.analysis_result
            
        except Exception as e:
            logger.error(f"==liuq debug== 多维度分析失败: {e}")
            raise
    
    def _analyze_scenes(self) -> Dict[str, Any]:
        """分析场景分类"""
        try:
            scene_data = {
                'outdoor': {'maps': [], 'count': 0, 'percentage': 0.0},
                'indoor': {'maps': [], 'count': 0, 'percentage': 0.0},
                'night': {'maps': [], 'count': 0, 'percentage': 0.0}
            }
            
            total_maps = len(self.configuration.map_points)
            
            for map_point in self.configuration.map_points:
                # 获取BV和IR参数
                bv_min = map_point.bv_range[0] if map_point.bv_range else 0.0
                ir_ratio = map_point.ir_range[0] if map_point.ir_range else 0.0  # 直接使用ir_min
                
                # 使用配置的规则进行分类
                scene_type = self.classification_config.classify_scene_by_rules(
                    bv_min, ir_ratio, map_point.alias_name
                )
                
                # 构建Map信息
                map_info = {
                    'alias_name': map_point.alias_name,
                    'bv_min': bv_min,
                    'ir_ratio': ir_ratio,
                    'weight': map_point.weight,
                    'coordinates': (map_point.x, map_point.y),
                    'original_scene_type': map_point.scene_type.value if hasattr(map_point.scene_type, 'value') else str(map_point.scene_type)
                }
                
                # 添加到对应场景
                scene_data[scene_type]['maps'].append(map_info)
                scene_data[scene_type]['count'] += 1
            
            # 计算百分比
            for scene_type in scene_data:
                if total_maps > 0:
                    scene_data[scene_type]['percentage'] = (scene_data[scene_type]['count'] / total_maps) * 100
            
            return scene_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 场景分析失败: {e}")
            return {}
    
    def _analyze_parameters(self) -> Dict[str, Any]:
        """分析参数分布"""
        try:
            bv_values = []
            ir_values = []
            weight_values = []
            
            for map_point in self.configuration.map_points:
                if map_point.bv_range:
                    bv_values.append(map_point.bv_range[0])
                ir_values.append(map_point.ir_range[0] if map_point.ir_range else 0.0)  # 使用ir_min
                weight_values.append(map_point.weight)
            
            parameter_stats = {}
            
            # BV参数统计
            if bv_values:
                parameter_stats['bv_min'] = {
                    'min': float(np.min(bv_values)),
                    'max': float(np.max(bv_values)),
                    'mean': float(np.mean(bv_values)),
                    'std': float(np.std(bv_values)),
                    'median': float(np.median(bv_values)),
                    'distribution': self._get_distribution_info(bv_values)
                }
            
            # IR参数统计
            if ir_values:
                parameter_stats['ir_min'] = {
                    'min': float(np.min(ir_values)),
                    'max': float(np.max(ir_values)),
                    'mean': float(np.mean(ir_values)),
                    'std': float(np.std(ir_values)),
                    'median': float(np.median(ir_values)),
                    'distribution': self._get_distribution_info(ir_values)
                }
            
            # 权重统计
            if weight_values:
                parameter_stats['weight'] = {
                    'min': float(np.min(weight_values)),
                    'max': float(np.max(weight_values)),
                    'mean': float(np.mean(weight_values)),
                    'std': float(np.std(weight_values)),
                    'median': float(np.median(weight_values)),
                    'distribution': self._get_distribution_info(weight_values)
                }
            
            return parameter_stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 参数分析失败: {e}")
            return {}
    
    def _analyze_classification_accuracy(self) -> Dict[str, Any]:
        """分析分类准确性"""
        try:
            total_maps = len(self.configuration.map_points)
            consistent_count = 0
            inconsistent_maps = []
            
            for map_point in self.configuration.map_points:
                bv_min = map_point.bv_range[0] if map_point.bv_range else 0.0
                ir_ratio = map_point.ir_range[0] if map_point.ir_range else 0.0  # 使用ir_min
                
                # 新分类结果
                new_classification = self.classification_config.classify_scene_by_rules(
                    bv_min, ir_ratio, map_point.alias_name
                )
                
                # 原始分类结果
                original_classification = map_point.scene_type.value if hasattr(map_point.scene_type, 'value') else str(map_point.scene_type)
                
                if new_classification == original_classification:
                    consistent_count += 1
                else:
                    inconsistent_maps.append({
                        'alias_name': map_point.alias_name,
                        'original': original_classification,
                        'new': new_classification,
                        'bv_min': bv_min,
                        'ir_ratio': ir_ratio
                    })
            
            accuracy = (consistent_count / total_maps * 100) if total_maps > 0 else 0
            
            return {
                'total_maps': total_maps,
                'consistent_count': consistent_count,
                'inconsistent_count': len(inconsistent_maps),
                'accuracy_percentage': accuracy,
                'inconsistent_maps': inconsistent_maps[:10]  # 只返回前10个不一致的案例
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 分类准确性分析失败: {e}")
            return {}
    
    def _generate_summary_statistics(self, scene_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成统计摘要"""
        try:
            total_maps = sum(scene_data['count'] for scene_data in scene_analysis.values())
            
            summary = {
                'total_map_count': total_maps,
                'scene_distribution': {
                    scene_type: {
                        'count': scene_data['count'],
                        'percentage': scene_data['percentage']
                    }
                    for scene_type, scene_data in scene_analysis.items()
                },
                'dominant_scene': max(scene_analysis.keys(), 
                                    key=lambda x: scene_analysis[x]['count']) if scene_analysis else 'unknown',
                'classification_thresholds': {
                    'bv_outdoor_threshold': self.classification_config.bv_outdoor_threshold,
                    'bv_indoor_min': self.classification_config.bv_indoor_min,
                    'ir_outdoor_threshold': self.classification_config.ir_outdoor_threshold
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"==liuq debug== 统计摘要生成失败: {e}")
            return {}
    
    def _get_distribution_info(self, values: List[float]) -> Dict[str, Any]:
        """获取数值分布信息"""
        try:
            if not values:
                return {}
            
            # 计算分位数
            percentiles = [25, 50, 75, 90, 95]
            distribution = {}
            
            for p in percentiles:
                distribution[f'p{p}'] = float(np.percentile(values, p))
            
            return distribution
            
        except Exception as e:
            logger.error(f"==liuq debug== 分布信息计算失败: {e}")
            return {}
    
    def get_analysis_result(self) -> Dict[str, Any]:
        """获取分析结果"""
        return self.analysis_result.copy() if self.analysis_result else {}
    
    def export_scene_maps(self, scene_type: str) -> List[Dict[str, Any]]:
        """
        导出指定场景的Map列表
        
        Args:
            scene_type: 场景类型 ('outdoor', 'indoor', 'night')
            
        Returns:
            Map列表
        """
        if not self.analysis_result:
            return []
        
        scene_analysis = self.analysis_result.get('scene_analysis', {})
        scene_data = scene_analysis.get(scene_type, {})
        
        return scene_data.get('maps', [])
