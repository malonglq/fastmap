#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成器主模块
==liuq debug== 报告生成器的核心协调器

作者: 龙sir团队
创建时间: 2025-09-16
版本: 1.0.0
描述: 负责协调整个报告生成流程，统一管理数据处理和模板渲染
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.services.reporting.infrastructure import (
    TemplateRenderer,
    HTMLTemplateService,
    ReportData,
    ReportConfig,
    ReportSection,
    SectionType,
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器 - 核心协调器"""
    
    def __init__(self):
        self.template_service = HTMLTemplateService()
        self.template_renderer = TemplateRenderer()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 设置默认模板
        self.default_template = "reporting/domains/exif/new_report.html"
    
    def generate_report(self, config: ReportConfig) -> str:
        """
        生成完整报告
        
        Args:
            config: 报告配置
            
        Returns:
            生成的HTML内容
        """
        try:
            self.logger.info(f"开始生成报告: {config.title}")
            
            # 准备报告数据结构
            report_data = ReportData(
                title=config.title,
                sections=[],
                metadata=config.metadata
            )
            
            # 处理报告数据
            self._process_report_data(report_data, config)
            
            # 渲染报告模板
            html_content = self._render_report(report_data, config)
            
            # 写入文件
            if config.output_path:
                self._write_report(html_content, config.output_path)
            
            self.logger.info(f"报告生成完成: {config.title}")
            return html_content
            
        except Exception as e:
            self.logger.error(f"报告生成失败: {e}")
            raise
    
    def _process_report_data(self, report_data: ReportData, config: ReportConfig) -> None:
        """处理报告数据（由子类实现具体逻辑）"""
        # 基础实现：添加标题段
        title_section = ReportSection(
            type=SectionType.TEXT,
            title="报告标题",
            content={"text": config.title},
            metadata={"auto_generated": True}
        )
        report_data.add_section(title_section)
    
    def _render_report(self, report_data: ReportData, config: ReportConfig) -> str:
        """渲染报告模板"""
        template_name = config.template_name or self.default_template
        template_context = {
            'report': report_data,
            'config': config,
            'styles': config.custom_styles,
            'scripts': config.custom_scripts
        }
        
        return self.template_renderer.render(template_name, template_context)
    
    def _write_report(self, html_content: str, output_path: str) -> None:
        """写入报告文件"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"报告已写入: {output_path}")


class EXIFReportGenerator(ReportGenerator):
    """EXIF报告生成器"""
    
    def __init__(self):
        super().__init__()
        from core.services.reporting.domains.exif import (
            generate_statistics_table,
            generate_kpi_cards,
            generate_topn_anomaly_table,
            generate_comparison_table,
            generate_per_image_rpg_bpg_analysis,
            generate_sgw_baseline_analysis
        )
        self.helpers = {
            'statistics_table': generate_statistics_table,
            'kpi_cards': generate_kpi_cards,
            'topn_anomaly': generate_topn_anomaly_table,
            'comparison': generate_comparison_table,
            'rpg_bpg_trend': generate_per_image_rpg_bpg_analysis,
            'sgw_baseline': generate_sgw_baseline_analysis
        }
    
    def _process_report_data(self, report_data: ReportData, config: ReportConfig) -> None:
        """处理EXIF报告数据"""
        super()._process_report_data(report_data, config)
        
        # 获取数据源
        data_source = config.metadata.get('data_source')
        if not data_source:
            self.logger.warning("没有提供数据源")
            return
        
        # 生成KPI卡片
        try:
            kpi_data = self.helpers['kpi_cards'](data_source)
            kpi_section = ReportSection(
                type=SectionType.KPI,
                title="关键指标",
                content=kpi_data['content'],
                metadata=kpi_data.get('metadata', {})
            )
            report_data.add_section(kpi_section)
        except Exception as e:
            self.logger.error(f"生成KPI卡片失败: {e}")
        
        # 生成统计数据表格
        try:
            statistics_data = config.metadata.get('statistics_data', {})
            table_data = self.helpers['statistics_table'](statistics_data)
            stats_section = ReportSection(
                type=SectionType.TABLE,
                title="统计数据",
                content=table_data['content'],
                metadata=table_data.get('metadata', {})
            )
            report_data.add_section(stats_section)
        except Exception as e:
            self.logger.error(f"生成统计数据表格失败: {e}")
        
        # 生成对比表格
        try:
            matched_pairs = config.metadata.get('matched_pairs', [])
            selected_fields = config.metadata.get('selected_fields', [])
            trend_data = config.metadata.get('trend_data', data_source)
            
            if matched_pairs and selected_fields:
                comparison_data = self.helpers['comparison'](matched_pairs, selected_fields, trend_data)
                comparison_section = ReportSection(
                    type=SectionType.TABLE,
                    title="数据对比",
                    content=comparison_data['content'],
                    metadata=comparison_data.get('metadata', {})
                )
                report_data.add_section(comparison_section)
        except Exception as e:
            self.logger.error(f"生成对比表格失败: {e}")
        
        # 生成趋势分析
        try:
            rpg_bpg_data = self.helpers['rpg_bpg_trend'](trend_data)
            trend_section = ReportSection(
                type=SectionType.CHART,
                title="趋势分析",
                content=rpg_bpg_data['content'],
                metadata=rpg_bpg_data.get('metadata', {})
            )
            report_data.add_section(trend_section)
        except Exception as e:
            self.logger.error(f"生成趋势分析失败: {e}")
        
        # 生成基线分析
        try:
            baseline_data = self.helpers['sgw_baseline'](trend_data)
            baseline_section = ReportSection(
                type=SectionType.TABLE,
                title="基线分析",
                content=baseline_data['content'],
                metadata=baseline_data.get('metadata', {})
            )
            report_data.add_section(baseline_section)
        except Exception as e:
            self.logger.error(f"生成基线分析失败: {e}")
        
        # 生成异常分析
        try:
            anomaly_data = self.helpers['topn_anomaly'](trend_data, topn=10)
            anomaly_section = ReportSection(
                type=SectionType.TABLE,
                title="异常分析",
                content=anomaly_data['content'],
                metadata=anomaly_data.get('metadata', {})
            )
            report_data.add_section(anomaly_section)
        except Exception as e:
            self.logger.error(f"生成异常分析失败: {e}")


# 工厂函数
def create_report_generator(report_type: str = "exif") -> ReportGenerator:
    """创建报告生成器实例"""
    generators = {
        'exif': EXIFReportGenerator,
        'general': ReportGenerator
    }
    
    generator_class = generators.get(report_type, ReportGenerator)
    return generator_class()
