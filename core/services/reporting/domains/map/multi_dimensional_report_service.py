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
import math
from collections import Counter, defaultdict
from dataclasses import replace
from typing import Dict, List, Any, Optional, Sequence, Tuple
from datetime import datetime
from pathlib import Path

from core.interfaces.report_generator import IReportGenerator, ReportType
from core.services.map_analysis.map_analyzer import MapAnalyzer
from core.services.map_analysis.multi_dimensional_analyzer import MultiDimensionalAnalyzer
from core.services.map_analysis.offset_map_query_service import (
    OffsetMapQueryService,
    OffsetMapQuerySpec,
    RangeWindow,
    build_report_section,
)
from core.services.map_analysis.awb_offset_map_analysis_service import (
    AwbOffsetMapAnalysisService,
    AwbOffsetMapReport,
    OffsetMapAnalysisEntry,
    SceneSummary,
    PrimaryClassSummary,
)
from core.services.reporting.engine.report_engine import ReportGenerator, ReportConfig
from core.services.reporting.infrastructure import ReportData
from core.models.map_data import MapConfiguration, MapPoint, MapType, SceneType
from core.models.scene_classification_config import SceneClassificationConfig
from utils.geometry_utils import polygon_centroid

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
            offset_query_options = data.get('offset_query_options', {}) or {}
            include_awb_reduce = data.get('include_awb_reduce_analysis')
            output_path = data.get('output_path', None)
            template_name = data.get('template_name', 'reporting/domains/map/report.html')
            
            # 步骤1: 创建Map分析器
            logger.info("==liuq debug== 步骤1: 创建Map分析器")
            map_analyzer = MapAnalyzer(map_configuration)
            
            # 步骤2: 创建多维度分析器（如果需要）
            multi_dimensional_analyzer = None
            multi_dimensional_result: Dict[str, Any] = {}
            offset_query_sections: List[Dict[str, Any]] = []
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

            include_offset_queries = bool(offset_query_options.get('enabled'))
            if include_awb_reduce is not None:
                include_offset_queries = include_offset_queries or bool(include_awb_reduce)
            if include_offset_queries:
                offset_query_sections = self._build_offset_query_sections(
                    map_configuration,
                    offset_query_options,
                )

            include_awb_offset = data.get('include_awb_offset_analysis')
            awb_offset_options = data.get('awb_offset_analysis_options') or {}
            if include_awb_offset is None:
                include_awb_offset = bool(awb_offset_options)
            else:
                include_awb_offset = bool(include_awb_offset)

            awb_offset_analysis = None
            if include_awb_offset:
                awb_offset_analysis = self._build_awb_offset_analysis_context(
                    map_configuration,
                    awb_offset_options,
                )
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
                multi_dimensional_result,
                offset_query_sections,
                awb_offset_analysis,
            )
            
            # 步骤4: 生成报告
            logger.info("==liuq debug== 步骤4: 生成报告")
            # 可选嵌入开关（默认开启）
            options = {
                'embed_awb_overview': bool(data.get('embed_awb_overview', True)),
                'embed_awb_strategy': bool(data.get('embed_awb_strategy', True)),
            }

            report_config = ReportConfig(
                title="Map多维度分析报告",
                output_path=output_path or f"output/map_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                template_name=self._resolve_template(template_name),
                metadata={
                    'map_configuration': map_configuration,
                    'include_multi_dimensional': include_multi_dimensional,
                    'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'analyzer_data': report_data,
                    'legacy_context': legacy_context,
                    'options': options,
                }
            )
            
            html_content = self.report_generator.generate_report(report_config)
            logger.info(f"==liuq debug== Map多维度分析报告生成完成 {report_config.output_path}")
            return report_config.output_path

        except Exception as e:
            logger.error(f"==liuq debug== Map多维度分析报告生成失败: {e}")
            raise RuntimeError(f"Map多维度分析报告生成失败: {e}")
    

    def preview_analysis_scope(
        self,
        map_configuration: MapConfiguration,
        include_multi_dimensional: bool = True,
        classification_config: Optional[SceneClassificationConfig] = None
    ) -> Dict[str, Any]:
        """生成报告前的分析范围预览数据。"""
        if not map_configuration:
            raise ValueError('缺少Map配置，无法预览分析范围')

        map_points = list(getattr(map_configuration, 'map_points', []) or [])
        total_points = len(map_points)

        scene_distribution: Dict[str, int] = {}
        for point in map_points:
            scene_type = getattr(point, 'scene_type', None)
            if hasattr(scene_type, 'name'):
                key = scene_type.name
            elif scene_type is not None:
                key = str(scene_type)
            else:
                key = 'UNKNOWN'
            scene_distribution[key] = scene_distribution.get(key, 0) + 1

        analysis_scope = {
            'traditional_analysis': True,
            'multi_dimensional_analysis': bool(include_multi_dimensional),
            'scene_classification': bool(include_multi_dimensional),
        }

        estimated_seconds = max(0.1, 0.3 + total_points * 0.015)
        estimated_processing_time = f"约 {estimated_seconds:.2f} 秒"

        output_sections = [
            'Map 数据概览',
            '偏移散点 (offset_x vs offset_y)',
            'BV 跨度分析',
            'CTemp 跨度分析',
            'IR 跨度分析',
            'Top Map 列表',
        ]
        if include_multi_dimensional:
            output_sections.extend(['场景分类统计', '色温跨度分析'])

        classification_info: Dict[str, Any] = {}
        if include_multi_dimensional and classification_config:
            classification_info = {
                'indoor_bv_threshold': getattr(classification_config, 'indoor_bv_threshold', None),
                'night_bv_threshold': getattr(classification_config, 'night_bv_threshold', None),
                'ir_threshold': getattr(classification_config, 'ir_threshold', None),
            }

        return {
            'map_summary': {
                'device_type': getattr(map_configuration, 'device_type', 'unknown'),
                'total_map_points': total_points,
                'scene_distribution': scene_distribution,
            },
            'analysis_scope': analysis_scope,
            'estimated_processing_time': estimated_processing_time,
            'output_sections': output_sections,
            'classification_config': classification_info,
        }


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
                              multi_dimensional_result: Optional[Dict[str, Any]],
                              offset_query_sections: Optional[List[Dict[str, Any]]] = None,
                              awb_offset_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        map_points: List[MapPoint] = list(getattr(map_configuration, 'map_points', []) or [])
        temperature_span = {}
        temperature_span_analysis = {}
        if multi_dimensional_result:
            temperature_span_analysis = multi_dimensional_result.get('temperature_span_analysis') or {}
            temperature_span = temperature_span_analysis.get('spans_by_map', {})

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

        # 调整色温段显示顺序：从高到低排列
        cct_order = ['>7500', '6500-7500', '5000-6500', '4000-5000', '2800-4000', '2300-2800', '1500-2300', '<1500']
        bv_order = ['BV>6', 'BV(2,6]', 'BV[-2,2]', 'BV<-2']

        ml_groups: List[Dict[str, Any]] = []
        sections: List[Dict[str, Any]] = []
        chart_payloads: List[List[Any]] = []
        ml_summary: List[Dict[str, Any]] = []
        base_boundary_point = getattr(map_configuration, 'base_boundary_point', None)

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
                            'chart_payload': self._build_chart_payload(sorted_maps, base_boundary_point),
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
            'temperature_span_analysis': temperature_span_analysis,
            'offset_query_sections': offset_query_sections or [],
            'awb_offset_analysis': awb_offset_analysis,
        }

    def _build_offset_query_sections(self,
                                     map_configuration: MapConfiguration,
                                     options: Dict[str, Any]) -> List[Dict[str, Any]]:
        map_points = getattr(map_configuration, 'map_points', []) or []
        service = OffsetMapQueryService(map_points)

        specs_payload = options.get('queries') or []
        specs: List[OffsetMapQuerySpec] = []
        for payload in specs_payload:
            if isinstance(payload, OffsetMapQuerySpec):
                specs.append(payload)
            elif isinstance(payload, dict):
                specs.append(OffsetMapQuerySpec.from_dict(payload))

        if not specs:
            reduce_metadata: Dict[str, Any] = {'narrative_id': 'awb_reduce_default'}
            custom_methodology = options.get('methodology_lines')
            if custom_methodology:
                reduce_metadata['methodology_lines'] = custom_methodology
            default_title = options.get('default_title', 'BV(2,6) × 色温1500–3800 减权统计')
            specs.append(
                OffsetMapQuerySpec(
                    name='reduce_bv2_ct1500',
                    title=default_title,
                    ml=65535,
                    range_windows={
                        'bv': RangeWindow(key='bv', lower=2.0, upper=6.0, label='BV', description='BV ∈ (2, 6)'),
                        'ctemp': RangeWindow(key='ctemp', lower=1500.0, upper=3800.0, label='色温', description='色温段与 1500–3800 K 有交集'),
                    },
                    metadata=reduce_metadata,
                )
            )

            enhance_metadata: Dict[str, Any] = {'narrative_id': 'awb_enhance_default'}
            enhance_title = options.get('enhance_title', 'BV(2,6) 强拉映射统计')
            specs.append(
                OffsetMapQuerySpec(
                    name='enhance_bv2',
                    title=enhance_title,
                    ml=65471,
                    range_windows={
                        'bv': RangeWindow(key='bv', lower=2.0, upper=6.0, label='BV', description='BV ∈ (2, 6)'),
                    },
                    metadata=enhance_metadata,
                )
            )

        enriched_specs: List[OffsetMapQuerySpec] = []
        for spec in specs:
            metadata = dict(spec.metadata or {})
            metadata.setdefault('shared_records', service.records)
            enriched_specs.append(replace(spec, metadata=metadata))

        results = service.run_queries(enriched_specs)
        show_empty = bool(options.get('show_empty', False))
        sections: List[Dict[str, Any]] = []
        for result in results:
            section = build_report_section(result)
            if section.get('has_matches') or show_empty:
                sections.append(section)
        return sections

    def _build_awb_offset_analysis_context(self,
                                           map_configuration: MapConfiguration,
                                           options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        metadata = getattr(map_configuration, 'metadata', {}) or {}
        xml_path_value = options.get('xml_path') or metadata.get('source_file')
        if not xml_path_value:
            logger.warning('==liuq debug== 无法确定AWB offset分析的源XML路径，跳过该章节')
            return None

        xml_path = Path(xml_path_value)
        if not xml_path.exists():
            logger.warning('==liuq debug== AWB offset分析源文件不存在: %s', xml_path)
            return None

        reference_points = options.get('reference_points')
        service = AwbOffsetMapAnalysisService(reference_points=reference_points)
        try:
            report = service.analyze(xml_path)
        except Exception as exc:  # pragma: no cover - 防御性日志
            logger.warning('==liuq debug== AWB offset分析执行失败，将跳过该章节: %s', exc)
            return None

        return self._serialize_awb_offset_report(report, options)

    def _serialize_awb_offset_report(self, report: AwbOffsetMapReport,
                                     options: Dict[str, Any]) -> Dict[str, Any]:
        entries: List[OffsetMapAnalysisEntry] = list(getattr(report, 'entries', []) or [])
        total_maps = len(entries)
        enabled_maps = sum(1 for entry in entries if entry.map_enabled)
        disabled_maps = total_maps - enabled_maps

        ml_counter = Counter(entry.ml for entry in entries if entry.ml is not None)
        reference_counter = Counter(
            entry.nearest_reference for entry in entries if entry.nearest_reference
        )
        scene_counter = Counter(entry.scene_group for entry in entries if entry.scene_group)
        primary_counter = Counter(
            entry.primary_class for entry in entries if entry.primary_class
        )

        overview: List[str] = []
        source_name = getattr(report.xml_path, 'name', None)
        if source_name:
            overview.append(f'数据来源：{source_name}')
        overview.append(
            f'Offset map 总数：{total_maps}（启用 {enabled_maps}，禁用 {disabled_maps}）'
        )

        ml_text = self._format_counter(ml_counter, {65471: 'ml=65471', 65535: 'ml=65535'})
        if ml_text:
            overview.append(f'映射方式分布：{ml_text}')

        ref_text = self._format_counter(reference_counter)
        if ref_text:
            overview.append(f'主要参考白点：{ref_text}')

        scene_text = self._format_counter(scene_counter)
        if scene_text:
            overview.append(f'场景分布：{scene_text}')

        primary_text = self._format_counter(primary_counter)
        if primary_text:
            overview.append(f'主类分布：{primary_text}')

        scene_limit = int(options.get('scene_map_display_limit', 12) or 12)
        class_limit = int(options.get('class_map_display_limit', 10) or 10)

        scene_summaries: Sequence[SceneSummary] = (
            getattr(report, 'scene_summaries', []) or []
        )
        scene_summaries_payload: List[Dict[str, Any]] = []
        for summary in scene_summaries:
            scene_summaries_payload.append({
                'scene_group': summary.scene_group,
                'count': summary.count,
                'map_list': self._format_map_list(summary.map_tags, scene_limit),
                'primary_distribution': self._format_counter(summary.primary_counter),
                'ml_distribution': self._format_counter(
                    summary.ml_counter, {65471: 'ml=65471', 65535: 'ml=65535'}
                ),
                'reference_distribution': self._format_counter(summary.reference_counter),
                'weight_stats': self._calc_weight_stats(summary.weights),
                'bv_span': self._format_span(summary.bv_accumulator.span),
                'ct_span': self._format_span(summary.ct_accumulator.span),
                'ir_span': self._format_span(summary.ir_accumulator.span),
            })

        class_summaries: Sequence[PrimaryClassSummary] = (
            getattr(report, 'class_summaries', []) or []
        )
        class_summaries_payload: List[Dict[str, Any]] = []
        for summary in class_summaries:
            class_summaries_payload.append({
                'primary_class': summary.primary_class,
                'count': summary.count,
                'map_list': self._format_map_list(summary.map_tags, class_limit),
                'scene_distribution': self._format_counter(summary.scene_counter),
                'ml_distribution': self._format_counter(
                    summary.ml_counter, {65471: 'ml=65471', 65535: 'ml=65535'}
                ),
                'reference_distribution': self._format_counter(summary.reference_counter),
                'weight_stats': self._calc_weight_stats(summary.weights),
                'bv_span': self._format_span(summary.bv_accumulator.span),
                'ct_span': self._format_span(summary.ct_accumulator.span),
                'ir_span': self._format_span(summary.ir_accumulator.span),
            })

        include_disabled = bool(options.get('include_disabled', False))
        top_entry_limit = int(options.get('top_entry_count', 12) or 12)
        top_entries_payload: List[Dict[str, Any]] = []
        highlight_note_added = False
        if top_entry_limit > 0:
            filtered_entries = [
                entry for entry in entries if include_disabled or entry.map_enabled
            ]
            ranked_entries = self._rank_top_entries(filtered_entries)
            for ranked in ranked_entries[:top_entry_limit]:
                entry = ranked["entry"]
                top_entries_payload.append({
                    'tag': entry.tag,
                    'alias': entry.alias,
                    'scene_group': entry.scene_group,
                    'primary_class': entry.primary_class,
                    'strategy': entry.mapping_label or (
                        f'ml={entry.ml}' if entry.ml is not None else '-'
                    ),
                    'reference': entry.nearest_reference or '-',
                    'weight': self._format_float(entry.weight, digits=3),
                    'offset': self._format_coord_pair(entry.offset),
                    'bv': self._format_span(entry.ranges.get('bv')),
                    'ct': self._format_span(
                        entry.ranges.get('ctemp') or entry.ranges.get('colorCCT')
                    ),
                    'ir': self._format_span(entry.ranges.get('ir')),
                    'count': self._format_span(entry.ranges.get('count')),
                    'reason': ranked['reason'],
                })
            if top_entries_payload and not highlight_note_added:
                overview.append(
                    '重点 Map 通过“影响力评分”选出：以权重排序为基础，叠加映射策略和触发区间覆盖度等因素，优先展示排名靠前的条目。'
                )
                highlight_note_added = True

        top_headers = [
            'Map', '别名', '场景', '主类', '策略', '参考白点', '权重',
            '目标坐标', 'BV区间', 'CT区间', 'IR区间', 'Count区间', '入选依据'
        ] if top_entries_payload else []

        return {
            'title': options.get('title', 'AWB Offset Map概述'),
            'overview': overview,
            'scene_summaries': scene_summaries_payload,
            'class_summaries': class_summaries_payload,
            'top_entries_headers': top_headers,
            'top_entries': top_entries_payload,
        }

    def _rank_top_entries(self, entries: Sequence[OffsetMapAnalysisEntry]) -> List[Dict[str, Any]]:
        ranked: List[Dict[str, Any]] = []
        for entry in entries:
            score, reason = self._calculate_highlight_score(entry)
            ranked.append({
                'entry': entry,
                'score': score,
                'reason': reason,
            })
        ranked.sort(key=lambda item: (item['score'], item['entry'].weight, -item['entry'].index), reverse=True)
        return ranked

    def _calculate_highlight_score(self, entry: OffsetMapAnalysisEntry) -> Tuple[float, str]:
        weight = float(entry.weight or 0.0)
        score = weight
        reasons: List[str] = []

        formatted_weight = self._format_float(weight, digits=3)
        if weight >= 0.5:
            score += 0.2
            reasons.append(f'权重 {formatted_weight} 位于高影响策略')
        elif weight >= 0.3:
            score += 0.1
            reasons.append(f'权重 {formatted_weight} 属于核心范围')
        else:
            reasons.append(f'权重 {formatted_weight} 相对较低')

        if entry.ml == 65471:
            score += 0.12
            reasons.append('ml=65471 强拉单点，快速锁定白点')
        elif entry.ml == 65535:
            score += 0.08
            reasons.append('ml=65535 整体位移，保持统计形状')

        offset_x, offset_y = entry.offset
        if not math.isclose(offset_x, 0.0, abs_tol=1e-6) or not math.isclose(offset_y, 0.0, abs_tol=1e-6):
            score += 0.05
            reasons.append(f'offset={self._format_coord_pair(entry.offset)} 指向 {entry.nearest_reference or "灰区"}')

        count_span = entry.ranges.get('count')
        if count_span and all(value is not None for value in count_span):
            lower, upper = count_span
            span_width = upper - lower
            if span_width >= 500:
                score += 0.06
                reasons.append(f'count 覆盖范围宽（{self._format_span(count_span)}）')
            elif lower >= 800:
                score += 0.04
                reasons.append(f'count 下限高（≥{int(lower)}）需大面积触发')

        if entry.scene_group in ('室外', '夜景'):
            score += 0.03
            reasons.append(f'{entry.scene_group} 场景对整体白平衡影响大')

        if entry.nearest_reference:
            reasons.append(f'目标靠近 {entry.nearest_reference} 参考点')

        reason_text = '；'.join(reasons) if reasons else '按照权重排序入选'
        return score, reason_text

    @staticmethod
    def _format_float(value: Optional[float], digits: int = 4) -> str:
        if value is None:
            return '-'
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return '-'
        if not math.isfinite(numeric):
            return '-'
        if abs(numeric) >= 1000 or float(numeric).is_integer():
            return str(int(round(numeric)))
        formatted = f'{numeric:.{digits}f}'.rstrip('0').rstrip('.')
        return formatted or '0'

    @classmethod
    def _format_span(cls, span: Optional[Tuple[Optional[float], Optional[float]]]) -> str:
        if not span:
            return '-'
        lower, upper = span
        lower_text = cls._format_float(lower, digits=3) if lower is not None else '-'
        upper_text = cls._format_float(upper, digits=3) if upper is not None else '-'
        if lower_text == '-' and upper_text == '-':
            return '-'
        return f'{lower_text}–{upper_text}'

    @staticmethod
    def _format_counter(counter: Counter, label_map: Optional[Dict[Any, str]] = None) -> str:
        if not counter:
            return ''
        segments: List[str] = []
        for key, count in counter.most_common():
            label: Any
            if label_map and key in label_map:
                label = label_map[key]
            elif key in (None, ''):
                label = '未知'
            else:
                label = key
            segments.append(f'{label}×{count}')
        return '、'.join(str(segment) for segment in segments)

    @classmethod
    def _calc_weight_stats(cls, weights: Sequence[float]) -> str:
        if not weights:
            return ''
        try:
            minimum = min(weights)
            maximum = max(weights)
            average = sum(weights) / len(weights)
        except (TypeError, ValueError):
            return ''

        if math.isclose(minimum, maximum, rel_tol=1e-6, abs_tol=1e-6):
            range_text = cls._format_float(minimum, digits=3)
        else:
            range_text = f'{cls._format_float(minimum, digits=3)}–{cls._format_float(maximum, digits=3)}'
        return f'范围 {range_text}；平均≈{cls._format_float(average, digits=3)}'

    @staticmethod
    def _format_map_list(map_tags: Sequence[str], limit: int) -> str:
        tags = list(map_tags or [])
        if not tags:
            return '-'
        if limit and limit > 0 and len(tags) > limit:
            head = '、'.join(tags[:limit])
            return f'{head} 等{len(tags)}张'
        if limit == 0:
            return f'共 {len(tags)} 张'
        return '、'.join(tags)

    @classmethod
    def _format_coord_pair(cls, offset: Tuple[float, float]) -> str:
        try:
            x, y = offset
        except (TypeError, ValueError):
            return '-'
        return f'({cls._format_float(x, digits=4)}, {cls._format_float(y, digits=4)})'

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

    def _build_chart_payload(self,
                             map_points: List[MapPoint],
                             base_boundary_point: Optional[MapPoint] = None) -> Dict[str, Any]:
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
            'base_boundary_polygon': self._build_polygon_series(base_boundary_point),
            'offset_polygons': self._build_offset_polygons(map_points),
        }

    def _build_offset_polygons(self, map_points: List[MapPoint]) -> List[Dict[str, Any]]:
        polygons: List[Dict[str, Any]] = []
        for mp in map_points:
            polygon = self._build_polygon_series(mp)
            if polygon:
                # 计算多边形重心，用于在前端绘制映射箭头（重心 -> offset）
                cx, cy = (0.0, 0.0)
                try:
                    verts = list(zip(polygon['x'], polygon['y'])) if polygon['x'] and polygon['y'] else []
                    if verts:
                        cx, cy = polygon_centroid(verts)
                except Exception:
                    cx, cy = (0.0, 0.0)
                polygons.append({
                    'alias': mp.alias_name,
                    'x': polygon['x'],
                    'y': polygon['y'],
                    'cx': cx,
                    'cy': cy,
                    'ox': float(getattr(mp, 'offset_x', 0.0)),
                    'oy': float(getattr(mp, 'offset_y', 0.0)),
                })
        return polygons

    def _build_polygon_series(self, map_point: Optional[MapPoint]) -> Dict[str, List[float]]:
        if not map_point or not getattr(map_point, 'polygon_vertices', None):
            return {'x': [], 'y': []}

        vertices = map_point.polygon_vertices or []
        if not vertices:
            return {'x': [], 'y': []}

        xs = [float(v[0]) for v in vertices]
        ys = [float(v[1]) for v in vertices]
        return {'x': xs, 'y': ys}

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
    
    
