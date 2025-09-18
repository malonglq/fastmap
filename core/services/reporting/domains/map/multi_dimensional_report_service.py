#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map多维度分析报告生成器（重构版）
==liuq debug== FastMapV2 Map多维度分析报告生成器

作者: 龙sir团队
创建时间: 2025-09-16
版本: 2.0.0
描述: 基于新架构的Map多维度分析报告生成器
"""

import logging
import json
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from core.interfaces.report_generator import IReportGenerator, ReportType
from core.services.map_analysis.map_analyzer import MapAnalyzer
from core.services.map_analysis.multi_dimensional_analyzer import MultiDimensionalAnalyzer
from core.services.reporting.engine.report_engine import ReportGenerator, ReportConfig
from core.services.reporting.infrastructure import ReportData
from core.models.map_data import MapConfiguration, MapPoint, MapType
from core.models.scene_classification_config import SceneClassificationConfig

logger = logging.getLogger(__name__)


class MapMultiDimensionalReportGenerator(IReportGenerator):
    """
    Map多维度分析报告生成器
    
    基于新架构实现，集成现有的Map分析组件，生成包含多维度场景分析的HTML报告
    """
    
    def __init__(self):
        """初始化Map多维度分析报告生成器"""
        self.report_generator = ReportGenerator()
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
                'template_name': str                    # 模板名称（可选，默认"reporting/domains/map/report.html"）
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
            template_name = data.get('template_name', 'reporting/domains/map/report.html')
            
            # 步骤1: 创建Map分析器
            logger.info("==liuq debug== 步骤1: 创建Map分析器")
            map_analyzer = MapAnalyzer(map_configuration)
            
            # 步骤2: 创建多维度分析器（如果需要）
            multi_dimensional_analyzer = None
            multi_dimensional_result: Dict[str, Any] = {}
            if include_multi_dimensional:
                logger.info("==liuq debug== 步骤2: 创建多维度分析器")
                if classification_config is None:
                    classification_config = SceneClassificationConfig()
                multi_dimensional_analyzer = MultiDimensionalAnalyzer(
                    map_configuration,
                    classification_config
                )
                try:
                    # 执行多维度分析
                    t_md = datetime.now()
                    multi_dimensional_result = multi_dimensional_analyzer.analyze()
                    logger.info("==liuq debug== 多维度分析已在报告生成前完成，用时%.2fs", (datetime.now()-t_md).total_seconds())
                except Exception as _e:
                    logger.warning('==liuq debug== 多维度分析执行失败，将继续但报告可能缺少多维度章节: %s', _e)
                    multi_dimensional_result = {}
            else:
                multi_dimensional_result = {}
            # 步骤3: 准备报告数据
            logger.info("==liuq debug== 步骤3: 准备报告数据")
            report_data = self._prepare_report_data(
                map_configuration,
                map_analyzer,
                multi_dimensional_analyzer,
                include_multi_dimensional
            )
            legacy_context = self._build_legacy_context(
                map_configuration,
                multi_dimensional_result
            )
            
            # 步骤4: 生成报告
            logger.info("==liuq debug== 步骤4: 生成报告")
            report_config = ReportConfig(
                title="Map多维度分析报告",
                output_path=output_path or f"output/map_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                template_name=self._resolve_template(template_name),
                metadata={
                    'map_configuration': map_configuration,
                    'include_multi_dimensional': include_multi_dimensional,
                    'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'analyzer_data': report_data,
                    'legacy_context': legacy_context
                }
            )
            
            html_content = self.report_generator.generate_report(report_config)
            logger.info(f"==liuq debug== Map多维度分析报告生成完成 {report_config.output_path}")
            return report_config.output_path
            
        except Exception as e:
            logger.error(f"==liuq debug== Map多维度分析报告生成失败: {e}")
            raise RuntimeError(f"Map多维度分析报告生成失败: {e}")
    

    def _resolve_template(self, template_name: Optional[str]) -> str:
        default_template = 'reporting/domains/map/report.html'
        if not template_name:
            return default_template
        return template_name

    def _prepare_report_data(self, map_configuration: MapConfiguration, 
                           map_analyzer: MapAnalyzer,
                           multi_dimensional_analyzer: Optional[MultiDimensionalAnalyzer],
                           include_multi_dimensional: bool) -> ReportData:
        """Prepare minimal report data for legacy compatibility."""
        return ReportData(
            title="Map multi-dimensional analysis report",
            sections=[],
            metadata={
                'device_type': map_configuration.device_type,
                'total_points': len(map_configuration.map_points),
                'include_multi_dimensional': include_multi_dimensional
            }
        )

    def _build_legacy_context(self, map_configuration: MapConfiguration,
                              multi_dimensional_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        map_points: List[MapPoint] = list(getattr(map_configuration, 'map_points', []) or [])
        temperature_span = {}
        if multi_dimensional_result:
            temperature_span = (multi_dimensional_result.get('temperature_span_analysis') or {}).get('spans_by_map', {})

        groups: Dict[Tuple[str, int], Dict[str, Dict[str, List[MapPoint]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )

        total_maps = len(map_points)
        for map_point in map_points:
            ml_label, ml_value = self._resolve_ml_label(map_point)
            span_entry = temperature_span.get(map_point.alias_name) or {}
            cct_label = self._resolve_cct_label(map_point, span_entry)
            bv_label = self._resolve_bv_label(map_point)
            groups[(ml_label, ml_value)][cct_label][bv_label].append(map_point)

        cct_order = ['<1500', '1500-2300', '2300-2800', '2800-4000', '4000-5000', '5000-6500', '6500-7500', '>7500']
        bv_order = ['BV>6', 'BV(2,6]', 'BV[-2,2]', 'BV<-2']

        ml_groups: List[Dict[str, Any]] = []
        sections: List[Dict[str, Any]] = []
        chart_payloads: List[List[Any]] = []
        ml_summary: List[Dict[str, Any]] = []

        for (ml_label, ml_value) in sorted(groups.keys(), key=lambda item: item[1]):
            cct_group = groups[(ml_label, ml_value)]
            rows: List[Dict[str, Any]] = []
            ml_total = 0

            for cct_label in cct_order:
                cells: List[Dict[str, Any]] = []
                bv_group = cct_group.get(cct_label, {})
                row_count = 0
                for bv_label in bv_order:
                    maps = bv_group.get(bv_label, [])
                    count = len(maps)
                    row_count += count
                    section_id = self._build_section_id(ml_label, ml_value, cct_label, bv_label) if count else ''
                    cells.append({
                        'count': count,
                        'section_id': section_id,
                        'bv_label': bv_label,
                    })
                    if count:
                        sorted_maps = sorted(maps, key=lambda mp: mp.alias_name)
                        section = {
                            'id': section_id,
                            'title': f"{ml_label}({ml_value}) | {cct_label} | {bv_label} （{count} 个）",
                            'ml_label': ml_label,
                            'ml_value': ml_value,
                            'cct_label': cct_label,
                            'bv_label': bv_label,
                            'count': count,
                            'table_rows': self._build_table_rows(sorted_maps),
                            'chart_payload': self._build_chart_payload(sorted_maps),
                        }
                        sections.append(section)
                        chart_payloads.append([section_id, section['chart_payload']])
                rows.append({
                    'cct_label': cct_label,
                    'cells': cells,
                    'has_data': row_count > 0,
                })
                ml_total += row_count

            ml_groups.append({
                'ml_label': ml_label,
                'ml_value': ml_value,
                'rows': rows,
            })
            ml_summary.append({
                'ml_label': ml_label,
                'ml_value': ml_value,
                'count': ml_total,
            })

        return {
            'title': 'Map 分类特性报告（离线版）',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_maps': total_maps,
            'ml_groups': ml_groups,
            'ml_summary': ml_summary,
            'sections': sections,
            'chart_payloads': chart_payloads,
            'chart_payloads_json': json.dumps(chart_payloads, ensure_ascii=False),
            'bv_order': bv_order,
            'cct_order': cct_order,
        }

    def _resolve_ml_label(self, map_point: MapPoint) -> Tuple[str, int]:
        ml_raw = 0
        if getattr(map_point, 'extra_attributes', None):
            try:
                ml_raw = int(map_point.extra_attributes.get('ml', 0))
            except (TypeError, ValueError):
                ml_raw = 0
        label_mapping = {
            65471: '强拉',
            65535: '减小权重',
        }
        if ml_raw in label_mapping:
            return label_mapping[ml_raw], ml_raw
        if getattr(map_point, 'map_type', None) == MapType.REDUCE:
            return '减小权重', ml_raw
        if getattr(map_point, 'map_type', None) == MapType.ENHANCE:
            return '强拉', ml_raw
        return f'ML{ml_raw}', ml_raw

    def _resolve_cct_label(self, map_point: MapPoint, span_entry: Dict[str, Any]) -> str:
        interval_to_bucket = {
            'Ultra-High': '>7500',
            'High-D75': '>7500',
            'D75-D65': '6500-7500',
            'D65-D50': '5000-6500',
            'D50-F': '4000-5000',
            'F-A': '2800-4000',
            'A-H': '2300-2800',
            'H-1500': '1500-2300',
            '1500-100K': '<1500',
        }
        interval_names = span_entry.get('interval_names') if span_entry else None
        if interval_names:
            first = interval_names[0]
            if first in interval_to_bucket:
                return interval_to_bucket[first]
        return self._fallback_cct_label(map_point)

    def _fallback_cct_label(self, map_point: MapPoint) -> str:
        cct_min = 0.0
        if getattr(map_point, 'ctemp_range', None):
            try:
                cct_min = float(map_point.ctemp_range[0])
            except (TypeError, ValueError):
                cct_min = 0.0
        thresholds = [1500, 2300, 2800, 4000, 5000, 6500, 7500]
        labels = ['<1500', '1500-2300', '2300-2800', '2800-4000', '4000-5000', '5000-6500', '6500-7500', '>7500']
        for idx, threshold in enumerate(thresholds):
            if cct_min < threshold:
                return labels[idx]
        return labels[-1]

    def _resolve_bv_label(self, map_point: MapPoint) -> str:
        bv_min = 0.0
        if getattr(map_point, 'bv_range', None):
            try:
                bv_min = float(map_point.bv_range[0])
            except (TypeError, ValueError):
                bv_min = 0.0
        if bv_min > 6:
            return 'BV>6'
        if bv_min > 2:
            return 'BV(2,6]'
        if bv_min >= -2:
            return 'BV[-2,2]'
        return 'BV<-2'

    def _build_section_id(self, ml_label: str, ml_value: int, cct_label: str, bv_label: str) -> str:
        ml_token = self._sanitize_identifier(ml_label)
        cct_token = self._sanitize_identifier(cct_label)
        bv_token = self._sanitize_identifier(bv_label)
        return f'sec_{ml_token}_{ml_value}_{cct_token}__{bv_token}'

    def _sanitize_identifier(self, value: str) -> str:
        if not value:
            return ''
        sanitized = []
        for ch in value:
            if ch.isalnum() or ch == '_' or '\u4e00' <= ch <= '\u9fff':
                sanitized.append(ch)
            else:
                sanitized.append('_')
        return ''.join(sanitized)

    def _build_chart_payload(self, map_points: List[MapPoint]) -> Dict[str, Any]:
        bv_mins, bv_maxs, bv_spans, bv_alias = [], [], [], []
        ir_mins, ir_maxs, ir_spans, ir_alias = [], [], [], []
        ctemp_mins, ctemp_maxs, ctemp_spans, ctemp_alias = [], [], [], []
        offsets_x, offsets_y, offsets_alias = [], [], []

        for mp in map_points:
            bv_min, bv_max = self._safe_range(mp.bv_range)
            ir_min, ir_max = self._safe_range(mp.ir_range)
            ctemp_min, ctemp_max = self._safe_range(mp.ctemp_range)
            bv_mins.append(bv_min)
            bv_maxs.append(bv_max)
            bv_spans.append(bv_max - bv_min)
            bv_alias.append(mp.alias_name)
            ir_mins.append(ir_min)
            ir_maxs.append(ir_max)
            ir_spans.append(ir_max - ir_min)
            ir_alias.append(mp.alias_name)
            ctemp_mins.append(ctemp_min)
            ctemp_maxs.append(ctemp_max)
            ctemp_spans.append(ctemp_max - ctemp_min)
            ctemp_alias.append(mp.alias_name)
            offsets_x.append(self._safe_float(getattr(mp, 'offset_x', 0.0)))
            offsets_y.append(self._safe_float(getattr(mp, 'offset_y', 0.0)))
            offsets_alias.append(mp.alias_name)

        return {
            'bv': {
                'mins': bv_mins,
                'maxs': bv_maxs,
                'spans': bv_spans,
                'alias': bv_alias,
            },
            'ir': {
                'mins': ir_mins,
                'maxs': ir_maxs,
                'spans': ir_spans,
                'alias': ir_alias,
            },
            'CTemp': {
                'mins': ctemp_mins,
                'maxs': ctemp_maxs,
                'spans': ctemp_spans,
                'alias': ctemp_alias,
            },
            'offsets': {
                'x': offsets_x,
                'y': offsets_y,
                'alias': offsets_alias,
            },
        }

    def _build_table_rows(self, map_points: List[MapPoint]) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for mp in map_points:
            bv_min, bv_max = self._safe_range(mp.bv_range)
            ir_min, ir_max = self._safe_range(mp.ir_range)
            ctemp_min, ctemp_max = self._safe_range(mp.ctemp_range)
            rows.append({
                'alias': mp.alias_name,
                'bv_range': f"[{self._format_number(bv_min)}, {self._format_number(bv_max)}]",
                'ir_range': f"[{self._format_number(ir_min)}, {self._format_number(ir_max)}]",
                'ctemp_range': f"[{self._format_number(ctemp_min)}, {self._format_number(ctemp_max)}]",
                'offset_x': self._format_number(getattr(mp, 'offset_x', 0.0)),
                'offset_y': self._format_number(getattr(mp, 'offset_y', 0.0)),
                'weight': self._format_number(getattr(mp, 'weight', 0.0)),
                'trans_step': getattr(mp, 'trans_step', 0),
            })
        return rows

    def _safe_range(self, value: Optional[Tuple[Any, Any]]) -> Tuple[float, float]:
        if not value:
            return 0.0, 0.0
        try:
            min_val = self._safe_float(value[0])
            max_val = self._safe_float(value[1])
            return min_val, max_val
        except (TypeError, ValueError, IndexError):
            return 0.0, 0.0

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _format_number(self, value: Any) -> str:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return '-'
        if abs(num - round(num)) < 1e-9:
            return str(int(round(num)))
        return f"{num:.3f}".rstrip('0').rstrip('.')

    def get_supported_templates(self) -> List[str]:
        """Return supported template identifiers."""
        return ["map_analysis", "default"]

    def get_default_classification_config(self) -> SceneClassificationConfig:
        """Return default scene classification configuration."""
        return SceneClassificationConfig()

    def get_report_name(self) -> str:
        """获取报告类型名称"""
        return "Map多维度分析报告"
    
    def get_report_type(self) -> ReportType:
        """获取报告类型"""
        return ReportType.MAP_MULTI_DIMENSIONAL
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证输入数据是否有效"""
        try:
            self._validate_input_data(data)
            return True
        except Exception as e:
            logger.warning(f"==liuq debug== 数据验证失败: {e}")
            return False
    
    def _validate_input_data(self, data: Dict[str, Any]):
        """Validate input data before report generation."""
        if 'map_configuration' not in data:
            raise ValueError('Missing required field: map_configuration')
        map_configuration = data['map_configuration']
        if not isinstance(map_configuration, MapConfiguration):
            raise ValueError('map_configuration must be a MapConfiguration instance')
        if not getattr(map_configuration, 'map_points', None):
            raise ValueError('map_configuration must contain map points')
        if 'include_multi_dimensional' in data and not isinstance(data['include_multi_dimensional'], bool):
            raise ValueError('include_multi_dimensional must be a boolean')
        if 'classification_config' in data and data['classification_config'] is not None:
            if not isinstance(data['classification_config'], SceneClassificationConfig):
                raise ValueError('classification_config must be a SceneClassificationConfig instance')
        if 'template_name' in data and data['template_name'] is not None:
            if not isinstance(data['template_name'], str):
                raise ValueError('template_name must be a string')
    def get_map_configuration_summary(self, map_configuration: MapConfiguration) -> Dict[str, Any]:
        """获取Map配置摘要信息"""
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
                scene_counts = {}
                weights = []
                x_coords = []
                y_coords = []
                
                for mp in map_configuration.map_points:
                    scene_type = mp.scene_type.value if hasattr(mp.scene_type, 'value') else str(mp.scene_type)
                    scene_counts[scene_type] = scene_counts.get(scene_type, 0) + 1
                    
                    weights.append(mp.weight)
                    x_coords.append(mp.x)
                    y_coords.append(mp.y)
                
                summary['scene_distribution'] = scene_counts
                
                summary['coordinate_range'] = {
                    'x_min': min(x_coords),
                    'x_max': max(x_coords),
                    'y_min': min(y_coords),
                    'y_max': max(y_coords)
                }
                
                summary['weight_range'] = {
                    'min': min(weights),
                    'max': max(weights),
                    'avg': sum(weights) / len(weights)
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"==liuq debug== 鑾峰彇Map閰嶇疆鎽樿澶辫触: {e}")
            return {}
    
    
