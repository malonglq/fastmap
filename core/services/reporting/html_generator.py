#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用HTML报告生成器
==liuq debug== FastMapV2通用HTML报告生成器

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 17:47:00 +08:00; Reason: P1-LD-003 抽象化HTML/Chart生成器; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: 基于现有HTMLGenerator抽象化的通用HTML报告生成器
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
# 移除Jinja2 Template导入，使用HTMLTemplateService统一管理

from core.interfaces.report_generator import (
    IHTMLReportGenerator, IReportDataProvider, ITemplateProvider,
    IFileManager, ReportGeneratorConfig
)
from core.services.reporting.chart_generator import UniversalChartGenerator
from core.services.reporting.html_template_service import HTMLTemplateService
from utils.file_manager import FileManager

logger = logging.getLogger(__name__)


# 移除重复的DefaultTemplateProvider类，使用HTMLTemplateService统一管理模板


class UniversalHTMLGenerator(IHTMLReportGenerator):
    """
    通用HTML报告生成器类

    基于现有HTMLGenerator抽象化，支持不同类型的数据报告
    """


    def __init__(self,
                 config: Optional[ReportGeneratorConfig] = None,
                 template_provider: Optional[ITemplateProvider] = None,
                 file_manager: Optional[IFileManager] = None):
        """
        初始化通用HTML报告生成器

        Args:
            config: 报告生成器配置
            template_provider: 模板提供者（现在使用HTMLTemplateService）
            file_manager: 文件管理器
        """
        self.config = config or ReportGeneratorConfig()
        # 使用HTMLTemplateService统一管理模板，而不是重复的DefaultTemplateProvider
        self.template_service = HTMLTemplateService()
        self.file_manager = file_manager or FileManager()
        self.chart_generator = UniversalChartGenerator(self.config)

        logger.info("==liuq debug== 通用HTML报告生成器初始化完成，使用统一模板服务")

    def generate_report(self,
                       data_provider: IReportDataProvider,
                       output_path: Optional[str] = None,
                       template_name: str = "default") -> str:
        """
        生成HTML报告

        Args:
            data_provider: 数据提供者
            output_path: 输出路径
            template_name: 模板名称

        Returns:
            生成的HTML文件路径
        """
        try:
            logger.info("==liuq debug== 开始生成HTML报告")

            # 准备报告数据
            report_data = data_provider.prepare_report_data()

            # 添加基本信息
            summary_data = data_provider.get_summary_data()
            report_data.update({
                'title': data_provider.get_report_title(),
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': summary_data,
                'configuration': report_data.get('configuration', None),
                'scene_analysis': report_data.get('scene_analysis', {}),
                'weight_analysis': report_data.get('weight_analysis', {}),
                'coordinate_analysis': report_data.get('coordinate_analysis', {})
            })

            # 生成HTML内容
            html_content = self.generate_html_content(report_data, template_name)

            # 确定输出路径
            if not output_path:
                output_dir = Path(self.config.output_dir)
                self.file_manager.ensure_directory(output_dir)
                output_path = self.file_manager.generate_unique_filename(output_dir, '.html')

            # 写入文件
            self.file_manager.write_file(output_path, html_content)

            logger.info(f"==liuq debug== HTML报告生成完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"==liuq debug== HTML报告生成失败: {e}")
            raise

    def generate_html_content(self, report_data: Dict[str, Any],
                            template_name: str = "default") -> str:
        """
        生成HTML内容

        Args:
            report_data: 报告数据
            template_name: 模板名称

        Returns:
            HTML内容字符串
        """
        try:
            # 确保基本变量存在
            if 'title' not in report_data:
                report_data['title'] = 'FastMapV2 Map分析报告'
            if 'generation_time' not in report_data:
                report_data['generation_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 使用现有的summary数据（由CombinedReportDataProvider提供）
            if 'summary' not in report_data:
                report_data['summary'] = {}

            # 生成图表脚本
            chart_scripts = self._generate_chart_scripts(report_data)
            report_data['chart_scripts'] = chart_scripts

            # 生成图表HTML容器
            chart_content = self._generate_chart_content(report_data)
            report_data['chart_content'] = chart_content

            # 生成多维度分析内容（如果包含）
            if report_data.get('include_multi_dimensional', False):
                multi_dimensional_content = self._generate_multi_dimensional_section(report_data)
                report_data['multi_dimensional_content'] = multi_dimensional_content

            # 使用HTMLTemplateService渲染模板，避免重复创建Template对象
            html_content = self.template_service.render_template(template_name, report_data)

            return html_content

        except Exception as e:
            logger.error(f"==liuq debug== 生成HTML内容失败: {e}")
            # 返回简单的错误页面
            return self._generate_error_page(str(e))

    def _generate_chart_scripts(self, report_data: Dict[str, Any]) -> str:
        """生成图表JavaScript脚本"""
        scripts = []
        scripts.append("// FastMapV2 图表脚本")
        scripts.append(f"// 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        scripts.append("")

        # 根据数据类型生成相应图表
        if 'scatter_data' in report_data:
            script = self.chart_generator.generate_scatter_chart(
                report_data['scatter_data'], 'scatterChart'
            )
            scripts.append(script)

        if 'heatmap_data' in report_data:
            script = self.chart_generator.generate_heatmap_chart(
                report_data['heatmap_data'], 'heatmapChart'
            )
            scripts.append(script)

        if 'range_data' in report_data:
            script = self.chart_generator.generate_range_chart(
                report_data['range_data'], 'rangeChart'
            )
            scripts.append(script)

        if 'trend_data' in report_data:
            script = self.chart_generator.generate_trend_chart(
                report_data['trend_data'], 'trendChart'
            )
            scripts.append(script)

        return '\n'.join(scripts)

    def _generate_chart_content(self, report_data: Dict[str, Any]) -> str:
        """生成图表HTML容器"""
        content = []

        if 'scatter_data' in report_data:
            content.append('<div class="chart-container"><canvas id="scatterChart"></canvas></div>')

        if 'heatmap_data' in report_data:
            content.append('<div class="chart-container"><canvas id="heatmapChart"></canvas></div>')

        if 'range_data' in report_data:
            content.append('<div class="chart-container"><canvas id="rangeChart"></canvas></div>')

        if 'trend_data' in report_data:
            content.append('<div class="chart-container"><canvas id="trendChart"></canvas></div>')

        return '\n'.join(content)

    def _generate_error_page(self, error_message: str) -> str:
        """生成错误页面"""
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>报告生成错误</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="alert alert-danger">
            <h4 class="alert-heading">报告生成失败</h4>
            <p>{error_message}</p>
            <hr>
            <p class="mb-0">请检查数据格式和分析结果，然后重试。</p>
        </div>
    </div>
</body>
</html>'''

    def _generate_multi_dimensional_section(self, report_data: Dict[str, Any]) -> str:
        """
        生成多维度分析HTML内容

        Args:
            report_data: 报告数据

        Returns:
            多维度分析HTML内容
        """
        try:
            multi_data = report_data.get('multi_dimensional_analysis', {})
            if not multi_data:
                return ""

            html_parts = []

            # 多维度分析标题
            html_parts.append('''
            <div class="row mt-5">
                <div class="col-12">
                    <h2 class="text-primary border-bottom pb-2">
                        <i class="fas fa-chart-pie me-2"></i>多维度场景分析
                    </h2>
                </div>
            </div>
            ''')

            # 分析概览
            html_parts.append(self._generate_multi_dimensional_overview(multi_data))

            # 场景分类统计
            html_parts.append(self._generate_scene_classification_section(multi_data))

            # 参数分布分析
            html_parts.append(self._generate_parameter_distribution_section(multi_data))

            # 分类准确性分析
            html_parts.append(self._generate_accuracy_analysis_section(multi_data))

            # 色温段跨度统计
            html_parts.append(self._generate_temperature_span_section(multi_data))

            return "".join(html_parts)

        except Exception as e:
            logger.error(f"==liuq debug== 生成多维度分析内容失败: {e}")
            return f'<div class="alert alert-warning">多维度分析内容生成失败: {e}</div>'

    def _generate_multi_dimensional_overview(self, multi_data: Dict[str, Any]) -> str:
        """生成多维度分析概览"""
        try:
            summary_stats = multi_data.get('summary_statistics', {})
            classification_config = multi_data.get('classification_config', {})

            total_maps = summary_stats.get('total_map_count', 0)
            dominant_scene = summary_stats.get('dominant_scene', '未知')
            scene_distribution = summary_stats.get('scene_distribution', {})

            # 场景分布数据
            outdoor_count = scene_distribution.get('outdoor', {}).get('count', 0)
            indoor_count = scene_distribution.get('indoor', {}).get('count', 0)
            night_count = scene_distribution.get('night', {}).get('count', 0)

            outdoor_pct = scene_distribution.get('outdoor', {}).get('percentage', 0)
            indoor_pct = scene_distribution.get('indoor', {}).get('percentage', 0)
            night_pct = scene_distribution.get('night', {}).get('percentage', 0)

            return f'''
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0">分析概览</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>总Map数量:</strong> {total_maps}</p>
                            <p><strong>主导场景:</strong> {dominant_scene}</p>
                            <hr>
                            <h6>场景分布:</h6>
                            <ul class="list-unstyled">
                                <li>🏞️ 室外场景: {outdoor_count} 个 ({outdoor_pct:.1f}%)</li>
                                <li>🏠 室内场景: {indoor_count} 个 ({indoor_pct:.1f}%)</li>
                                <li>🌙 夜景场景: {night_count} 个 ({night_pct:.1f}%)</li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-secondary text-white">
                            <h5 class="mb-0">分类规则</h5>
                        </div>
                        <div class="card-body">
                            <h6>当前阈值设置:</h6>
                            <ul class="list-unstyled">
                                <li><strong>BV室外阈值:</strong> {classification_config.get('bv_outdoor_threshold', 7)}</li>
                                <li><strong>BV室内下限:</strong> {classification_config.get('bv_indoor_min', 1)}</li>
                                <li><strong>IR室外阈值:</strong> {classification_config.get('ir_outdoor_threshold', 0.5)}</li>
                            </ul>
                            <hr>
                            <small class="text-muted">
                                室外: BV_min > {classification_config.get('bv_outdoor_threshold', 7)} 或 IR_min > {classification_config.get('ir_outdoor_threshold', 0.5)}<br>
                                室内: {classification_config.get('bv_indoor_min', 1)} ≤ BV_min ≤ {classification_config.get('bv_outdoor_threshold', 7)} 且 IR_min ≤ {classification_config.get('ir_outdoor_threshold', 0.5)}<br>
                                夜景: BV_min < {classification_config.get('bv_indoor_min', 1)}
                            </small>
                        </div>
                    </div>
                </div>
            </div>
            '''

        except Exception as e:
            logger.error(f"==liuq debug== 生成多维度分析概览失败: {e}")
            return f'<div class="alert alert-warning">概览生成失败: {e}</div>'

    def _generate_scene_classification_section(self, multi_data: Dict[str, Any]) -> str:
        """生成场景分类统计表格"""
        try:
            formatted_scene_stats = multi_data.get('formatted_scene_stats', {})

            if not formatted_scene_stats:
                return '<div class="alert alert-info">暂无场景分类数据</div>'

            html_parts = ['''
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h5 class="mb-0">场景分类详细统计</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped table-hover">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>场景类型</th>
                                            <th>Map数量</th>
                                            <th>占比(%)</th>
                                            <th>平均权重</th>
                                            <th>代表性Map</th>
                                        </tr>
                                    </thead>
                                    <tbody>
            ''']

            for scene_type, scene_data in formatted_scene_stats.items():
                representative_maps = scene_data.get('representative_maps', [])
                map_names = [m.get('alias_name', '未知') for m in representative_maps[:3]]
                map_list = ', '.join(map_names) if map_names else '无'

                html_parts.append(f'''
                                        <tr>
                                            <td><strong>{scene_data.get('name', scene_type)}</strong></td>
                                            <td>{scene_data.get('count', 0)}</td>
                                            <td>{scene_data.get('percentage', 0):.1f}%</td>
                                            <td>{scene_data.get('avg_weight', 0):.2f}</td>
                                            <td><small>{map_list}</small></td>
                                        </tr>
                ''')

            html_parts.append('''
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            ''')

            return "".join(html_parts)

        except Exception as e:
            logger.error(f"==liuq debug== 生成场景分类统计失败: {e}")
            return f'<div class="alert alert-warning">场景分类统计生成失败: {e}</div>'

    def _generate_parameter_distribution_section(self, multi_data: Dict[str, Any]) -> str:
        """生成参数分布分析"""
        try:
            formatted_parameter_stats = multi_data.get('formatted_parameter_stats', {})

            if not formatted_parameter_stats:
                return '<div class="alert alert-info">暂无参数分布数据</div>'

            html_parts = ['''
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-warning text-dark">
                            <h5 class="mb-0">参数分布分析</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>参数</th>
                                            <th>最小值</th>
                                            <th>最大值</th>
                                            <th>平均值</th>
                                            <th>标准差</th>
                                            <th>中位数</th>
                                        </tr>
                                    </thead>
                                    <tbody>
            ''']

            for param_name, param_data in formatted_parameter_stats.items():
                html_parts.append(f'''
                                        <tr>
                                            <td><strong>{param_data.get('display_name', param_name)}</strong></td>
                                            <td>{param_data.get('min', 0):.2f}</td>
                                            <td>{param_data.get('max', 0):.2f}</td>
                                            <td>{param_data.get('mean', 0):.2f}</td>
                                            <td>{param_data.get('std', 0):.2f}</td>
                                            <td>{param_data.get('median', 0):.2f}</td>
                                        </tr>
                ''')

            html_parts.append('''
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            ''')

            return "".join(html_parts)

        except Exception as e:
            logger.error(f"==liuq debug== 生成参数分布分析失败: {e}")
            return f'<div class="alert alert-warning">参数分布分析生成失败: {e}</div>'

    def _generate_accuracy_analysis_section(self, multi_data: Dict[str, Any]) -> str:
        """生成分类准确性分析"""
        try:
            formatted_accuracy_stats = multi_data.get('formatted_accuracy_stats', {})

            if not formatted_accuracy_stats:
                return '<div class="alert alert-info">暂无准确性分析数据</div>'

            total_maps = formatted_accuracy_stats.get('total_maps', 0)
            consistent_count = formatted_accuracy_stats.get('consistent_count', 0)

            inconsistent_count = formatted_accuracy_stats.get('inconsistent_count', 0)
            accuracy_percentage = formatted_accuracy_stats.get('accuracy_percentage', 0)
            inconsistent_examples = formatted_accuracy_stats.get('inconsistent_examples', [])

            html_parts = [f'''
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0">分类准确性分析</h5>
                        </div>
                        <div class="card-body">
                            <div class="row text-center">
                                <div class="col-6">
                                    <h3 class="text-success">{accuracy_percentage:.1f}%</h3>
                                    <p class="text-muted">准确率</p>
                                </div>
                                <div class="col-6">
                                    <h3 class="text-info">{total_maps}</h3>
                                    <p class="text-muted">总Map数</p>
                                </div>
                            </div>
                            <hr>
                            <p><strong>一致分类:</strong> {consistent_count} 个</p>
                            <p><strong>不一致分类:</strong> {inconsistent_count} 个</p>
                            <small class="text-muted">注：准确率是指新分类规则与原始分类的一致性程度</small>
                        </div>
                    </div>
                </div>
            ''']

            # 不一致案例
            if inconsistent_examples:
                html_parts.append('''
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-danger text-white">
                            <h5 class="mb-0">不一致分类案例</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>Map名称</th>
                                            <th>原始</th>
                                            <th>新分类</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                ''')

                for example in inconsistent_examples[:5]:
                    alias_name = example.get('alias_name', '未知')
                    if len(alias_name) > 20:
                        alias_name = alias_name[:17] + "..."

                    html_parts.append(f'''
                                        <tr>
                                            <td><small>{alias_name}</small></td>
                                            <td><small>{example.get('original', '未知')}</small></td>
                                            <td><small>{example.get('new', '未知')}</small></td>
                                        </tr>
                    ''')

                html_parts.append('''
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                ''')
            else:
                html_parts.append('''
                <div class="col-md-6">
                    <div class="alert alert-success">
                        <h6>🎉 完美一致!</h6>
                        <p class="mb-0">所有Map的分类结果都与原始分类一致。</p>
                    </div>
                </div>
                ''')

            html_parts.append('</div>')

            return "".join(html_parts)

        except Exception as e:
            logger.error(f"==liuq debug== 生成准确性分析失败: {e}")
            return f'<div class="alert alert-warning">准确性分析生成失败: {e}</div>'

    def _generate_temperature_span_section(self, multi_data: Dict[str, Any]) -> str:
        """生成色温段跨度统计区块"""
        try:
            temp_span = multi_data.get('temperature_span_analysis', {})
            top20 = temp_span.get('top20', [])
            spans_by_map = temp_span.get('spans_by_map', {})
            if not spans_by_map:
                return '<div class="alert alert-info">暂无色温段跨度数据</div>'

            html_parts = ['''
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0">色温段跨度统计（Top 20）</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped table-hover">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>排名</th>
                                            <th>Map点名称</th>
                                            <th>跨越色温段</th>
                                            <th>跨度数量</th>
                                            <th>坐标(RpG, BpG)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
            ''']

            for idx, item in enumerate(top20, start=1):
                alias = item.get('alias_name', '-')
                names = item.get('interval_names', [])
                count = item.get('count', 0)
                coords = item.get('coords', (0, 0))
                names_str = ', '.join(names)
                html_parts.append(f'''<tr>
                    <td>{idx}</td>
                    <td>{alias}</td>
                    <td><small>{names_str}</small></td>
                    <td>{count}</td>
                    <td>({coords[0]:.3f}, {coords[1]:.3f})</td>
                </tr>''')

            html_parts.append('''
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            ''')

            return ''.join(html_parts)
        except Exception as e:
            logger.error(f"==liuq debug== 生成色温段跨度统计失败: {e}")
            return f'<div class="alert alert-warning">色温段跨度统计生成失败: {e}</div>'
