# {{CHENGQI:
# Action: Added; Timestamp: 2025-08-04 17:10:00 +08:00; Reason: 创建组合报告数据提供者以支持传统分析和多维度分析的统一HTML报告生成; Principle_Applied: 组合模式和数据统一性;
# }}

"""
组合报告数据提供者

将传统Map分析和多维度分析结果组合，提供统一的HTML报告数据
"""

import logging
from typing import Dict, Any
from datetime import datetime

from core.interfaces.report_generator import IReportDataProvider
from core.services.map_analyzer import MapAnalyzer
from core.services.multi_dimensional_analyzer import MultiDimensionalAnalyzer

logger = logging.getLogger(__name__)


class CombinedReportDataProvider(IReportDataProvider):
    """
    组合报告数据提供者
    
    将传统Map分析器和多维度分析器的结果组合，
    提供统一的HTML报告数据接口
    """
    
    def __init__(self, 
                 map_analyzer: MapAnalyzer, 
                 multi_dimensional_analyzer: MultiDimensionalAnalyzer = None,
                 include_multi_dimensional: bool = True):
        """
        初始化组合数据提供者
        
        Args:
            map_analyzer: 传统Map分析器
            multi_dimensional_analyzer: 多维度分析器（可选）
            include_multi_dimensional: 是否包含多维度分析内容
        """
        self.map_analyzer = map_analyzer
        self.multi_dimensional_analyzer = multi_dimensional_analyzer
        self.include_multi_dimensional = include_multi_dimensional and multi_dimensional_analyzer is not None
        
        logger.info("==liuq debug== 组合报告数据提供者初始化完成")
    
    def prepare_report_data(self) -> Dict[str, Any]:
        """
        准备报告数据
        
        Returns:
            包含传统分析和多维度分析的完整报告数据
        """
        try:
            # 获取传统分析数据
            traditional_data = self._prepare_traditional_analysis_data()
            
            # 获取多维度分析数据（如果启用）
            multi_dimensional_data = {}
            if self.include_multi_dimensional:
                multi_dimensional_data = self._prepare_multi_dimensional_analysis_data()
            
            # 组合数据
            combined_data = {
                **traditional_data,
                'multi_dimensional_analysis': multi_dimensional_data,
                'include_multi_dimensional': self.include_multi_dimensional,
                'report_metadata': {
                    'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'includes_multi_dimensional': self.include_multi_dimensional,
                    'data_source_consistency': True  # 标记数据源一致性
                }
            }
            
            logger.info("==liuq debug== 组合报告数据准备完成")
            return combined_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 准备组合报告数据失败: {e}")
            raise
    
    def _prepare_traditional_analysis_data(self) -> Dict[str, Any]:
        """准备传统分析数据"""
        try:
            # 获取传统分析器的报告数据
            if hasattr(self.map_analyzer, 'prepare_report_data'):
                return self.map_analyzer.prepare_report_data()
            else:
                # 如果map_analyzer没有prepare_report_data方法，手动构建数据
                analysis_result = self.map_analyzer.get_analysis_result() if hasattr(self.map_analyzer, 'get_analysis_result') else self.map_analyzer.analysis_result
                
                return {
                    'analysis_result': analysis_result,
                    'configuration': self.map_analyzer.configuration,
                    'scatter_plot_data': self.map_analyzer.get_scatter_plot_data() if hasattr(self.map_analyzer, 'get_scatter_plot_data') else {},
                    'heatmap_data': self.map_analyzer.get_heatmap_data() if hasattr(self.map_analyzer, 'get_heatmap_data') else {}
                }
                
        except Exception as e:
            logger.error(f"==liuq debug== 准备传统分析数据失败: {e}")
            return {}
    
    def _prepare_multi_dimensional_analysis_data(self) -> Dict[str, Any]:
        """准备多维度分析数据"""
        try:
            if not self.multi_dimensional_analyzer:
                return {}
            
            # 获取多维度分析结果
            multi_result = self.multi_dimensional_analyzer.get_analysis_result()
            
            if not multi_result:
                logger.warning("==liuq debug== 多维度分析结果为空")
                return {}
            
            # 处理和格式化多维度分析数据
            formatted_data = {
                'scene_analysis': multi_result.get('scene_analysis', {}),
                'parameter_analysis': multi_result.get('parameter_analysis', {}),
                'accuracy_analysis': multi_result.get('accuracy_analysis', {}),
                'summary_statistics': multi_result.get('summary_statistics', {}),
                'classification_config': multi_result.get('classification_config', {}),
                'analysis_metadata': multi_result.get('analysis_metadata', {}),
                
                # 为HTML生成准备的格式化数据
                'formatted_scene_stats': self._format_scene_statistics(multi_result.get('scene_analysis', {})),
                'formatted_parameter_stats': self._format_parameter_statistics(multi_result.get('parameter_analysis', {})),
                'formatted_accuracy_stats': self._format_accuracy_statistics(multi_result.get('accuracy_analysis', {}))
            }
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 准备多维度分析数据失败: {e}")
            return {}
    
    def _format_scene_statistics(self, scene_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """格式化场景统计数据用于HTML显示"""
        try:
            formatted_stats = {}
            
            scene_name_map = {
                'outdoor': '室外场景',
                'indoor': '室内场景',
                'night': '夜景场景'
            }
            
            for scene_type, scene_data in scene_analysis.items():
                scene_name = scene_name_map.get(scene_type, scene_type)
                maps = scene_data.get('maps', [])
                
                # 计算平均权重
                avg_weight = sum(m.get('weight', 0) for m in maps) / len(maps) if maps else 0
                
                formatted_stats[scene_type] = {
                    'name': scene_name,
                    'count': scene_data.get('count', 0),
                    'percentage': scene_data.get('percentage', 0),
                    'avg_weight': avg_weight,
                    'representative_maps': maps[:5]  # 前5个代表性Map
                }
            
            return formatted_stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 格式化场景统计数据失败: {e}")
            return {}
    
    def _format_parameter_statistics(self, parameter_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """格式化参数统计数据用于HTML显示"""
        try:
            formatted_stats = {}
            
            param_name_map = {
                'bv_min': 'BV最小值',
                'ir_min': 'IR最小值',
                'weight': '权重'
            }
            
            for param_name, param_stats in parameter_analysis.items():
                display_name = param_name_map.get(param_name, param_name)
                
                formatted_stats[param_name] = {
                    'display_name': display_name,
                    'min': param_stats.get('min', 0),
                    'max': param_stats.get('max', 0),
                    'mean': param_stats.get('mean', 0),
                    'std': param_stats.get('std', 0),
                    'median': param_stats.get('median', 0),
                    'distribution': param_stats.get('distribution', {})
                }
            
            return formatted_stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 格式化参数统计数据失败: {e}")
            return {}
    
    def _format_accuracy_statistics(self, accuracy_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """格式化准确性统计数据用于HTML显示"""
        try:
            return {
                'total_maps': accuracy_analysis.get('total_maps', 0),
                'consistent_count': accuracy_analysis.get('consistent_count', 0),
                'inconsistent_count': accuracy_analysis.get('inconsistent_count', 0),
                'accuracy_percentage': accuracy_analysis.get('accuracy_percentage', 0),
                'inconsistent_examples': accuracy_analysis.get('inconsistent_maps', [])[:5]  # 前5个不一致案例
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 格式化准确性统计数据失败: {e}")
            return {}
    
    def get_summary_data(self) -> Dict[str, Any]:
        """获取摘要数据"""
        try:
            summary = {}
            
            # 传统分析摘要
            if hasattr(self.map_analyzer, 'get_summary_data'):
                summary.update(self.map_analyzer.get_summary_data())
            
            # 多维度分析摘要
            if self.include_multi_dimensional and self.multi_dimensional_analyzer:
                multi_result = self.multi_dimensional_analyzer.get_analysis_result()
                if multi_result:
                    summary_stats = multi_result.get('summary_statistics', {})
                    summary.update({
                        'multi_dimensional_summary': {
                            'total_map_count': summary_stats.get('total_map_count', 0),
                            'dominant_scene': summary_stats.get('dominant_scene', '未知'),
                            'scene_distribution': summary_stats.get('scene_distribution', {})
                        }
                    })
            
            return summary
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取摘要数据失败: {e}")
            return {}
    
    def get_report_title(self) -> str:
        """获取报告标题"""
        base_title = "FastMapV2 Map分析报告"
        if self.include_multi_dimensional:
            return f"{base_title} - 包含多维度场景分析"
        return base_title
    
    def get_chart_data(self) -> Dict[str, Any]:
        """获取图表数据"""
        try:
            chart_data = {}
            
            # 传统分析图表数据
            if hasattr(self.map_analyzer, 'get_chart_data'):
                chart_data.update(self.map_analyzer.get_chart_data())
            
            # 多维度分析图表数据
            if self.include_multi_dimensional and self.multi_dimensional_analyzer:
                multi_result = self.multi_dimensional_analyzer.get_analysis_result()
                if multi_result:
                    scene_analysis = multi_result.get('scene_analysis', {})
                    
                    # 场景分布饼图数据
                    pie_chart_data = []
                    for scene_type, scene_data in scene_analysis.items():
                        scene_name_map = {
                            'outdoor': '室外场景',
                            'indoor': '室内场景',
                            'night': '夜景场景'
                        }
                        pie_chart_data.append({
                            'name': scene_name_map.get(scene_type, scene_type),
                            'value': scene_data.get('count', 0),
                            'percentage': scene_data.get('percentage', 0)
                        })
                    
                    chart_data['multi_dimensional_charts'] = {
                        'scene_distribution_pie': pie_chart_data
                    }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取图表数据失败: {e}")
            return {}
