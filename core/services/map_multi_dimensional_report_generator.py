#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map多维度分析报告生成器
==liuq debug== FastMapV2 Map多维度分析报告生成器

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 16:10:00 +08:00; Reason: 阶段3-创建Map多维度分析报告生成器; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 实现Map多维度分析报告生成功能
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from core.interfaces.report_generator import IReportGenerator, ReportType
from core.services.map_analyzer import MapAnalyzer
from core.services.multi_dimensional_analyzer import MultiDimensionalAnalyzer
from core.services.combined_report_data_provider import CombinedReportDataProvider
from core.services.html_generator import UniversalHTMLGenerator
from core.models.map_data import MapConfiguration
from core.models.scene_classification_config import SceneClassificationConfig

logger = logging.getLogger(__name__)


class MapMultiDimensionalReportGenerator(IReportGenerator):
    """
    Map多维度分析报告生成器
    
    集成现有的Map分析组件，生成包含多维度场景分析的HTML报告
    """
    
    def __init__(self):
        """初始化Map多维度分析报告生成器"""
        logger.info("==liuq debug== Map多维度分析报告生成器初始化完成")
    
    def generate(self, data: Dict[str, Any]) -> str:
        """
        生成Map多维度分析报告
        
        Args:
            data: {
                'map_configuration': MapConfiguration,  # Map配置对象
                'include_multi_dimensional': bool,      # 是否包含多维度分析（可选，默认True）
                'classification_config': SceneClassificationConfig,  # 场景分类配置（可选）
                'output_path': str,                     # 输出路径（可选）
                'template_name': str                    # 模板名称（可选，默认"map_analysis"）
            }
            
        Returns:
            生成的报告文件路径
        """
        try:
            logger.info("==liuq debug== 开始生成Map多维度分析报告")
            
            # 验证输入数据
            self._validate_input_data(data)
            
            # 提取参数
            map_configuration = data['map_configuration']
            include_multi_dimensional = data.get('include_multi_dimensional', True)
            classification_config = data.get('classification_config', None)
            output_path = data.get('output_path', None)
            template_name = data.get('template_name', 'map_analysis')
            
            # 步骤1: 创建Map分析器
            logger.info("==liuq debug== 步骤1: 创建Map分析器")
            map_analyzer = MapAnalyzer(map_configuration)
            
            # 步骤2: 创建多维度分析器（如果需要）
            multi_dimensional_analyzer = None
            if include_multi_dimensional:
                logger.info("==liuq debug== 步骤2: 创建多维度分析器")
                if classification_config is None:
                    classification_config = SceneClassificationConfig()
                multi_dimensional_analyzer = MultiDimensionalAnalyzer(
                    map_configuration, 
                    classification_config
                )
            
            # 步骤3: 创建组合数据提供者
            logger.info("==liuq debug== 步骤3: 创建组合数据提供者")
            combined_data_provider = CombinedReportDataProvider(
                map_analyzer,
                multi_dimensional_analyzer,
                include_multi_dimensional
            )
            
            # 步骤4: 生成HTML报告
            logger.info("==liuq debug== 步骤4: 生成HTML报告")
            html_generator = UniversalHTMLGenerator()
            
            report_path = html_generator.generate_report(
                combined_data_provider,
                template_name=template_name,
                output_path=output_path
            )
            
            logger.info(f"==liuq debug== Map多维度分析报告生成完成: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"==liuq debug== Map多维度分析报告生成失败: {e}")
            raise RuntimeError(f"Map多维度分析报告生成失败: {e}")
    
    def get_report_name(self) -> str:
        """获取报告类型名称"""
        return "Map多维度分析报告"
    
    def get_report_type(self) -> ReportType:
        """获取报告类型"""
        return ReportType.MAP_MULTI_DIMENSIONAL
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        验证输入数据是否有效
        
        Args:
            data: 待验证的数据
            
        Returns:
            数据是否有效
        """
        try:
            self._validate_input_data(data)
            return True
        except Exception as e:
            logger.warning(f"==liuq debug== 数据验证失败: {e}")
            return False
    
    def _validate_input_data(self, data: Dict[str, Any]):
        """验证输入数据"""
        # 检查必需字段
        if 'map_configuration' not in data:
            raise ValueError("缺少必需字段: map_configuration")
        
        map_configuration = data['map_configuration']
        
        # 检查map_configuration类型
        if not isinstance(map_configuration, MapConfiguration):
            raise ValueError("map_configuration必须是MapConfiguration类型")
        
        # 检查Map配置的基本完整性
        if not map_configuration.map_points:
            raise ValueError("Map配置中没有Map点数据")
        
        if len(map_configuration.map_points) == 0:
            raise ValueError("Map配置中Map点数量为0")
        
        # 检查可选参数的类型
        if 'include_multi_dimensional' in data:
            if not isinstance(data['include_multi_dimensional'], bool):
                raise ValueError("include_multi_dimensional必须是布尔类型")
        
        if 'classification_config' in data and data['classification_config'] is not None:
            if not isinstance(data['classification_config'], SceneClassificationConfig):
                raise ValueError("classification_config必须是SceneClassificationConfig类型")
        
        if 'template_name' in data:
            if not isinstance(data['template_name'], str):
                raise ValueError("template_name必须是字符串类型")
    
    def get_map_configuration_summary(self, map_configuration: MapConfiguration) -> Dict[str, Any]:
        """
        获取Map配置摘要信息
        
        Args:
            map_configuration: Map配置对象
            
        Returns:
            配置摘要信息
        """
        try:
            summary = {
                'device_type': map_configuration.device_type,
                'total_map_points': len(map_configuration.map_points),
                'has_base_boundary': map_configuration.base_boundary is not None,
                'has_reference_points': len(map_configuration.reference_points) > 0,
                'scene_distribution': {},
                'coordinate_range': {},
                'weight_range': {}
            }
            
            if map_configuration.map_points:
                # 场景分布统计
                scene_counts = {}
                weights = []
                x_coords = []
                y_coords = []
                
                for mp in map_configuration.map_points:
                    # 场景统计
                    scene_type = mp.scene_type.value if hasattr(mp.scene_type, 'value') else str(mp.scene_type)
                    scene_counts[scene_type] = scene_counts.get(scene_type, 0) + 1
                    
                    # 权重和坐标收集
                    weights.append(mp.weight)
                    x_coords.append(mp.x)
                    y_coords.append(mp.y)
                
                summary['scene_distribution'] = scene_counts
                
                # 坐标范围
                summary['coordinate_range'] = {
                    'x_min': min(x_coords),
                    'x_max': max(x_coords),
                    'y_min': min(y_coords),
                    'y_max': max(y_coords)
                }
                
                # 权重范围
                summary['weight_range'] = {
                    'min': min(weights),
                    'max': max(weights),
                    'avg': sum(weights) / len(weights)
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取Map配置摘要失败: {e}")
            return {}
    
    def preview_analysis_scope(self, map_configuration: MapConfiguration,
                              include_multi_dimensional: bool = True,
                              classification_config: Optional[SceneClassificationConfig] = None) -> Dict[str, Any]:
        """
        预览分析范围
        
        Args:
            map_configuration: Map配置对象
            include_multi_dimensional: 是否包含多维度分析
            classification_config: 场景分类配置
            
        Returns:
            分析范围预览信息
        """
        try:
            preview = {
                'map_summary': self.get_map_configuration_summary(map_configuration),
                'analysis_scope': {
                    'traditional_analysis': True,
                    'multi_dimensional_analysis': include_multi_dimensional,
                    'scene_classification': include_multi_dimensional
                },
                'estimated_processing_time': self._estimate_processing_time(map_configuration, include_multi_dimensional),
                'output_sections': []
            }
            
            # 输出章节预览
            preview['output_sections'] = [
                '1. Map配置概览',
                '2. 场景统计分析',
                '3. 坐标分布分析',
                '4. 权重分析',
                '5. 可视化图表'
            ]
            
            if include_multi_dimensional:
                preview['output_sections'].extend([
                    '6. 多维度场景分析',
                    '7. 参数分布分析',
                    '8. 分类准确性分析'
                ])
            
            return preview
            
        except Exception as e:
            logger.error(f"==liuq debug== 预览分析范围失败: {e}")
            return {}
    
    def _estimate_processing_time(self, map_configuration: MapConfiguration, 
                                include_multi_dimensional: bool) -> str:
        """估算处理时间"""
        try:
            map_count = len(map_configuration.map_points)
            
            # 基础分析时间估算
            base_time = max(1, map_count // 50)  # 每50个点约1秒
            
            # 多维度分析额外时间
            if include_multi_dimensional:
                base_time += max(1, map_count // 100)  # 额外时间
            
            if base_time <= 3:
                return "约1-3秒"
            elif base_time <= 10:
                return "约3-10秒"
            elif base_time <= 30:
                return "约10-30秒"
            else:
                return "约30秒以上"
                
        except Exception:
            return "无法估算"
    
    def get_supported_templates(self) -> List[str]:
        """获取支持的报告模板"""
        return ["map_analysis", "default"]
    
    def get_default_classification_config(self) -> SceneClassificationConfig:
        """获取默认的场景分类配置"""
        return SceneClassificationConfig()
