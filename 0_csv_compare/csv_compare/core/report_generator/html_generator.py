#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML报告生成器
==liuq debug== HTML报告生成和模板处理

生成完整的HTML分析报告
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from jinja2 import Template, Environment, FileSystemLoader

from core.report_generator.chart_generator import ChartGenerator
from utils.file_utils import FileUtils

logger = logging.getLogger(__name__)


class HTMLGenerator:
    """HTML报告生成器类"""
    
    def __init__(self):
        """初始化HTML生成器"""
        self.chart_generator = ChartGenerator()
        self.file_utils = FileUtils()
        self.template_dir = Path(__file__).parent.parent.parent / 'templates'
        
        # 确保模板目录存在
        self.file_utils.ensure_directory(self.template_dir)
        
        logger.info("==liuq debug== HTML报告生成器初始化完成")
    
    def generate_report(self, analysis_results: Dict[str, Any],
                       match_result: Dict[str, Any],
                       statistics_results: Dict[str, Any],
                       output_path: Optional[str] = None,
                       mapping_info: Optional[Dict[str, Any]] = None) -> str:
        """
        生成完整的HTML报告
        
        Args:
            analysis_results: 分析结果
            match_result: 匹配结果
            statistics_results: 统计结果
            output_path: 输出路径
            
        Returns:
            生成的HTML文件路径
        """
        try:
            logger.info("==liuq debug== 开始生成HTML报告")
            
            # 准备报告数据
            report_data = self.prepare_report_data(
                analysis_results, match_result, statistics_results, mapping_info
            )
            
            # 生成HTML内容
            html_content = self.generate_html_content(report_data)
            
            # 确定输出路径
            if not output_path:
                output_dir = Path(__file__).parent.parent.parent / 'output'
                self.file_utils.ensure_directory(output_dir)
                # 直接使用output_dir作为目录，让generate_unique_filename生成文件名
                output_path = self.file_utils.generate_unique_filename(
                    output_dir, '.html'
                )
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"==liuq debug== HTML报告生成完成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"==liuq debug== HTML报告生成失败: {e}")
            raise
    
    def prepare_report_data(self, analysis_results: Dict[str, Any],
                          match_result: Dict[str, Any],
                          statistics_results: Dict[str, Any],
                           mapping_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        准备报告数据
        
        Args:
            analysis_results: 分析结果
            match_result: 匹配结果
            statistics_results: 统计结果
            
        Returns:
            报告数据字典
        """
        try:
            # 基本信息
            report_data = {
                'title': 'CSV数据对比分析报告',
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'summary': analysis_results.get('summary', {}),
                'match_result': match_result,
                'field_analyses': analysis_results.get('field_analyses', {}),
                'overall_statistics': analysis_results.get('overall_statistics', {}),
                'statistics_results': statistics_results,
                'trend_data': analysis_results.get('trend_data', {})
            }
            
            # 获取列名映射关系
            original_to_display = {}
            if mapping_info:
                original_to_display = mapping_info.get('original_to_display', {})

            # 处理字段分析数据
            processed_fields = []
            for field, analysis in report_data['field_analyses'].items():
                if 'error' not in analysis:
                    # 获取显示名称
                    display_name = original_to_display.get(field, field)

                    field_data = {
                        'name': display_name,  # 使用显示名称
                        'original_name': field,  # 保留原始名称用于数据访问
                        'analysis': analysis,
                        'trend_data': report_data['trend_data'].get(field, {}),
                        'statistics': statistics_results.get(field, {}),
                        'safe_name': display_name.replace(' ', '_').replace('-', '_').replace(':', '_')
                    }
                    processed_fields.append(field_data)
            
            report_data['processed_fields'] = processed_fields
            
            # 生成图表脚本 - 传递处理后的字段信息
            report_data['chart_scripts'] = self.chart_generator.generate_all_charts_script_with_mapping(
                analysis_results, processed_fields
            )
            
            # 生成数据表格
            report_data['data_table'] = self.generate_data_table(match_result, processed_fields)
            
            return report_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 准备报告数据失败: {e}")
            raise
    
    def generate_data_table(self, match_result: Dict[str, Any], 
                          processed_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        生成数据表格
        
        Args:
            match_result: 匹配结果
            processed_fields: 处理后的字段数据
            
        Returns:
            表格数据列表
        """
        try:
            table_data = []
            matched_pairs = match_result.get('pairs', [])
            
            for pair in matched_pairs:
                row_data = {
                    'filename1': pair.get('filename1', ''),
                    'filename2': pair.get('filename2', ''),
                    'similarity': pair.get('similarity', 0),
                    'fields': {}
                }
                
                row1 = pair.get('row1')
                row2 = pair.get('row2')
                
                for field_data in processed_fields:
                    display_name = field_data['name']  # 显示名称
                    original_name = field_data.get('original_name', display_name)  # 原始名称

                    if (row1 is not None and original_name in row1.index and
                        row2 is not None and original_name in row2.index):

                        try:
                            val1 = float(row1[original_name])
                            val2 = float(row2[original_name])
                            change = val2 - val1
                            change_percent = (change / val1 * 100) if val1 != 0 else 0

                            row_data['fields'][display_name] = {
                                'before': val1,
                                'after': val2,
                                'change': change,
                                'change_percent': change_percent,
                                'change_category': self.categorize_change(change_percent)
                            }
                        except:
                            row_data['fields'][display_name] = {
                                'before': 'N/A',
                                'after': 'N/A',
                                'change': 'N/A',
                                'change_percent': 'N/A',
                                'change_category': 'invalid'
                            }
                
                table_data.append(row_data)
            
            return table_data
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成数据表格失败: {e}")
            return []
    
    def categorize_change(self, change_percent: float) -> str:
        """分类变化幅度"""
        try:
            if change_percent > 10:
                return 'large_increase'
            elif change_percent > 1:
                return 'medium_increase'
            elif change_percent > 0:
                return 'small_increase'
            elif change_percent == 0:
                return 'no_change'
            elif change_percent > -1:
                return 'small_decrease'
            elif change_percent > -10:
                return 'medium_decrease'
            else:
                return 'large_decrease'
        except:
            return 'invalid'
    
    def generate_html_content(self, report_data: Dict[str, Any]) -> str:
        """
        生成HTML内容
        
        Args:
            report_data: 报告数据
            
        Returns:
            HTML内容字符串
        """
        try:
            # 使用内置模板
            template_content = self.get_default_template()
            
            # 创建Jinja2模板
            template = Template(template_content)
            
            # 渲染模板
            html_content = template.render(**report_data)
            
            return html_content
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成HTML内容失败: {e}")
            # 返回简单的错误页面
            return self.generate_error_page(str(e))
    
    def get_default_template(self) -> str:
        """获取默认HTML模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }
        .main-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin: 20px;
            padding: 30px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border-radius: 10px;
        }
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }
        .stats-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            border-left: 4px solid #007bff;
        }
        .change-positive { color: #28a745; font-weight: bold; }
        .change-negative { color: #dc3545; font-weight: bold; }
        .change-neutral { color: #6c757d; }
        .table-container {
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid #dee2e6;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1><i class="fas fa-chart-line"></i> {{ title }}</h1>
            <p class="mb-0">生成时间: {{ generation_time }}</p>
            <p class="mb-0">分析文件数量: {{ match_result.matched_pairs }} 对</p>
        </div>

        <!-- 概览统计 -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="stats-card">
                    <h5><i class="fas fa-file-csv"></i> 文件1</h5>
                    <h3>{{ match_result.total_file1 }}</h3>
                    <small>数据行数</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <h5><i class="fas fa-file-csv"></i> 文件2</h5>
                    <h3>{{ match_result.total_file2 }}</h3>
                    <small>数据行数</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <h5><i class="fas fa-link"></i> 匹配成功</h5>
                    <h3>{{ match_result.matched_pairs }}</h3>
                    <small>数据对</small>
                </div>
            </div>
            <div class="col-md-3">
                <div class="stats-card">
                    <h5><i class="fas fa-percentage"></i> 匹配率</h5>
                    <h3>{{ "%.1f"|format(match_result.match_rate) }}%</h3>
                    <small>成功率</small>
                </div>
            </div>
        </div>

        <!-- 多字段概览图表 -->
        {% if processed_fields|length > 1 %}
        <div class="row mb-4">
            <div class="col-12">
                <h3><i class="fas fa-chart-bar"></i> 多字段变化概览</h3>
                <div class="chart-container">
                    <canvas id="overviewChart"></canvas>
                </div>
            </div>
        </div>
        {% endif %}

        <!-- 字段分析 -->
        {% for field in processed_fields %}
        <div class="row mb-5">
            <div class="col-12">
                <h3><i class="fas fa-chart-line"></i> {{ field.name }} 分析</h3>
                
                <!-- 趋势图表 -->
                <div class="row">
                    <div class="col-md-8">
                        <h5>趋势对比</h5>
                        <div class="chart-container">
                            <canvas id="trendChart_{{ field.safe_name }}_{{ loop.index0 }}"></canvas>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <h5>变化分布</h5>
                        <div class="chart-container">
                            <canvas id="changeChart_{{ field.safe_name }}_{{ loop.index0 }}"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- 统计对比 -->
                <div class="row mt-3">
                    <div class="col-12">
                        <h5>统计指标对比</h5>
                        <div class="chart-container">
                            <canvas id="statsChart_{{ field.safe_name }}_{{ loop.index0 }}"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- 统计摘要 -->
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="stats-card">
                            <h6>趋势分析</h6>
                            <p><strong>趋势:</strong> {{ field.analysis.trend_classification.trend }}</p>
                            <p><strong>置信度:</strong> {{ "%.2f"|format(field.analysis.trend_classification.confidence) }}</p>
                            <p><strong>有效数据对:</strong> {{ field.analysis.valid_pairs }}</p>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="stats-card">
                            <h6>变化统计</h6>
                            <p><strong>正向变化:</strong> {{ field.analysis.change_stats.positive_changes }}</p>
                            <p><strong>负向变化:</strong> {{ field.analysis.change_stats.negative_changes }}</p>
                            <p><strong>无变化:</strong> {{ field.analysis.change_stats.no_changes }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}

        <!-- 详细数据表格 -->
        <div class="row mb-4">
            <div class="col-12">
                <h3><i class="fas fa-table"></i> 详细数据对比表</h3>
                <!-- 添加搜索框 -->
                <div class="mb-3">
                    <input type="text" id="tableSearch" class="form-control" placeholder="🔍 搜索表格内容..." style="max-width: 300px;">
                </div>
                <div class="table-container">
                    <table id="dataTable" class="table table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th onclick="sortTable(0)" style="cursor: pointer;">文件1 <i class="fas fa-sort"></i></th>
                                <th onclick="sortTable(1)" style="cursor: pointer;">文件2 <i class="fas fa-sort"></i></th>
                                <th onclick="sortTable(2)" style="cursor: pointer;">相似度 <i class="fas fa-sort"></i></th>
                                {% for field in processed_fields %}
                                <th colspan="3">{{ field.name }}</th>
                                {% endfor %}
                            </tr>
                            <tr>
                                <th></th>
                                <th></th>
                                <th></th>
                                {% for field in processed_fields %}
                                <th onclick="sortTable({{ loop.index0 * 3 + 3 }})" style="cursor: pointer;">处理前 <i class="fas fa-sort"></i></th>
                                <th onclick="sortTable({{ loop.index0 * 3 + 4 }})" style="cursor: pointer;">处理后 <i class="fas fa-sort"></i></th>
                                <th onclick="sortTable({{ loop.index0 * 3 + 5 }})" style="cursor: pointer;">变化% <i class="fas fa-sort"></i></th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in data_table %}
                            <tr>
                                <td>{{ row.filename1 }}</td>
                                <td>{{ row.filename2 }}</td>
                                <td>{{ "%.3f"|format(row.similarity) }}</td>
                                {% for field in processed_fields %}
                                {% set field_data = row.fields.get(field.name, {}) %}
                                <td>{{ field_data.before }}</td>
                                <td>{{ field_data.after }}</td>
                                <td class="{% if field_data.change_percent > 0 %}change-positive{% elif field_data.change_percent < 0 %}change-negative{% else %}change-neutral{% endif %}">
                                    {% if field_data.change_percent != 'N/A' %}{{ "%.2f"|format(field_data.change_percent) }}%{% else %}N/A{% endif %}
                                </td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- 页脚 -->
        <div class="text-center mt-4">
            <p class="text-muted">
                <i class="fas fa-tools"></i> 
                CSV数据对比分析工具 v1.0.0 | 
                生成时间: {{ generation_time }}
            </p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 等待DOM完全加载后再执行图表脚本
        document.addEventListener('DOMContentLoaded', function() {
            console.log('==liuq debug== DOM 已加载，开始初始化图表');

            // 检查Chart.js是否加载
            console.log('==liuq debug== Chart.js 检查:', typeof Chart !== 'undefined' ? 'OK' : 'FAILED');
            if (typeof Chart === 'undefined') {
                console.error('==liuq debug== Chart.js 未加载，图表将无法显示');
                const containers = document.querySelectorAll('.chart-container');
                containers.forEach(container => {
                    container.innerHTML = '<div style="text-align: center; padding: 50px; color: #dc3545;"><i class="fas fa-exclamation-triangle"></i><br>图表加载失败<br><small>Chart.js 未正确加载</small></div>';
                });
                return;
            }

            console.log('==liuq debug== Chart.js 版本:', Chart.version);

            try {
                {{ chart_scripts|safe }}
                console.log('==liuq debug== 图表脚本执行完成');
            } catch (error) {
                console.error('==liuq debug== 图表脚本执行失败:', error);
                // 显示错误信息
                const containers = document.querySelectorAll('.chart-container');
                containers.forEach(container => {
                    container.innerHTML = '<div style="text-align: center; padding: 50px; color: #dc3545;"><i class="fas fa-exclamation-triangle"></i><br>图表渲染失败<br><small>' + error.message + '</small></div>';
                });
            }

            // 表格搜索功能
            const searchInput = document.getElementById('tableSearch');
            if (searchInput) {
                searchInput.addEventListener('keyup', function() {
                    const filter = this.value.toLowerCase();
                    const table = document.getElementById('dataTable');
                    if (table) {
                        const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

                        for (let i = 0; i < rows.length; i++) {
                            const row = rows[i];
                            const text = row.textContent.toLowerCase();
                            row.style.display = text.includes(filter) ? '' : 'none';
                        }
                    }
                });
            }
        });

        // 表格排序功能 - 支持正序倒序切换
        let sortDirection = {}; // 记录每列的排序方向

        function sortTable(columnIndex) {
            const table = document.getElementById('dataTable');
            if (!table) return;

            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = Array.from(tbody.getElementsByTagName('tr'));

            // 切换排序方向
            sortDirection[columnIndex] = sortDirection[columnIndex] === 'asc' ? 'desc' : 'asc';
            const isAscending = sortDirection[columnIndex] === 'asc';

            rows.sort((a, b) => {
                const aVal = a.cells[columnIndex].textContent.trim();
                const bVal = b.cells[columnIndex].textContent.trim();

                let result = 0;

                // 尝试数字比较（处理百分比，使用绝对值排序）
                const aNum = parseFloat(aVal.replace('%', ''));
                const bNum = parseFloat(bVal.replace('%', ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    result = Math.abs(aNum) - Math.abs(bNum);
                } else {
                    // 字符串比较
                    result = aVal.localeCompare(bVal);
                }

                // 根据排序方向返回结果
                return isAscending ? result : -result;
            });

            // 重新插入排序后的行
            rows.forEach(row => tbody.appendChild(row));

            // 更新表头排序图标
            updateSortIcons(columnIndex, isAscending);
        }

        // 更新排序图标显示
        function updateSortIcons(activeColumn, isAscending) {
            const table = document.getElementById('dataTable');
            if (!table) return;

            const headers = table.querySelectorAll('th[onclick]');
            headers.forEach((header, index) => {
                const icon = header.querySelector('i');
                if (icon) {
                    if (index === activeColumn) {
                        // 当前排序列显示方向图标
                        icon.className = isAscending ? 'fas fa-sort-up' : 'fas fa-sort-down';
                    } else {
                        // 其他列显示默认排序图标
                        icon.className = 'fas fa-sort';
                    }
                }
            });
        }
    </script>
</body>
</html>'''
    
    def generate_error_page(self, error_message: str) -> str:
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
