#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML模板服务
==liuq debug== FastMapV2 HTML模板处理服务

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: HTML模板处理服务，从HTMLGenerator中拆分
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from jinja2 import Template, Environment, BaseLoader, TemplateNotFound

logger = logging.getLogger(__name__)


class HTMLTemplateService:
    """
    HTML模板服务
    
    专门负责HTML模板的加载、管理和渲染功能：
    - 内置模板管理
    - 自定义模板加载
    - 模板变量处理
    - 模板继承和包含
    """
    
    def __init__(self):
        """初始化HTML模板服务"""
        self.builtin_templates = self._load_builtin_templates()
        self.custom_templates = {}
        # 使用所有模板初始化加载器
        all_templates = {**self.builtin_templates, **self.custom_templates}
        self.environment = Environment(loader=InMemoryTemplateLoader(all_templates))
        logger.debug("==liuq debug== HTML模板服务初始化完成")
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        渲染模板
        
        Args:
            template_name: 模板名称
            context: 模板上下文变量
            
        Returns:
            str: 渲染后的HTML内容
        """
        try:
            # 添加默认上下文变量
            full_context = self._prepare_template_context(context)
            
            # 获取模板
            template = self.environment.get_template(template_name)
            
            # 渲染模板
            html_content = template.render(**full_context)
            
            logger.debug(f"==liuq debug== 模板渲染完成: {template_name}")
            return html_content
            
        except TemplateNotFound:
            logger.error(f"==liuq debug== 模板未找到: {template_name}")
            return self._get_error_template().render(
                error_message=f"模板 '{template_name}' 未找到",
                **context
            )
        except Exception as e:
            logger.error(f"==liuq debug== 模板渲染失败: {e}")
            return self._get_error_template().render(
                error_message=f"模板渲染失败: {e}",
                **context
            )
    
    def register_template(self, name: str, content: str):
        """
        注册自定义模板
        
        Args:
            name: 模板名称
            content: 模板内容
        """
        try:
            self.custom_templates[name] = content
            # 更新环境加载器
            all_templates = {**self.builtin_templates, **self.custom_templates}
            self.environment = Environment(loader=InMemoryTemplateLoader(all_templates))
            
            logger.debug(f"==liuq debug== 注册自定义模板: {name}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 注册模板失败: {e}")
    
    def load_template_from_file(self, file_path: Path, name: Optional[str] = None) -> str:
        """
        从文件加载模板
        
        Args:
            file_path: 模板文件路径
            name: 模板名称（可选，默认使用文件名）
            
        Returns:
            str: 模板名称
        """
        try:
            template_name = name or file_path.stem
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.register_template(template_name, content)
            
            logger.debug(f"==liuq debug== 从文件加载模板: {file_path} -> {template_name}")
            return template_name
            
        except Exception as e:
            logger.error(f"==liuq debug== 从文件加载模板失败: {e}")
            raise
    
    def get_available_templates(self) -> List[str]:
        """
        获取可用模板列表
        
        Returns:
            List[str]: 模板名称列表
        """
        return list(self.builtin_templates.keys()) + list(self.custom_templates.keys())
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板信息
        
        Args:
            template_name: 模板名称
            
        Returns:
            Dict[str, Any]: 模板信息
        """
        try:
            template_source = None
            template_type = None
            
            if template_name in self.builtin_templates:
                template_source = "builtin"
                template_type = "内置模板"
            elif template_name in self.custom_templates:
                template_source = "custom"
                template_type = "自定义模板"
            else:
                return {"error": f"模板 '{template_name}' 不存在"}
            
            # 获取模板内容长度
            content = (self.builtin_templates.get(template_name) or 
                      self.custom_templates.get(template_name, ""))
            
            return {
                "name": template_name,
                "type": template_type,
                "source": template_source,
                "content_length": len(content),
                "variables": self._extract_template_variables(content)
            }
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取模板信息失败: {e}")
            return {"error": f"获取模板信息失败: {e}"}
    
    def _prepare_template_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """准备模板上下文，添加默认变量"""
        full_context = {
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'app_name': 'FastMapV2',
            'app_version': '2.0.0'
        }
        
        # 合并用户提供的上下文
        full_context.update(context)
        
        # 确保必需的变量存在
        if 'title' not in full_context:
            full_context['title'] = 'FastMapV2 分析报告'
        if 'generation_time' not in full_context:
            full_context['generation_time'] = full_context['current_time']
        
        return full_context
    
    def _extract_template_variables(self, content: str) -> List[str]:
        """提取模板中使用的变量"""
        try:
            import re
            # 匹配Jinja2变量语法 {{ variable }}
            pattern = r'\{\{\s*([^}]+)\s*\}\}'
            matches = re.findall(pattern, content)
            
            # 清理和去重
            variables = []
            for match in matches:
                var_name = match.split('|')[0].split('.')[0].strip()
                if var_name and var_name not in variables:
                    variables.append(var_name)
            
            return variables
            
        except Exception as e:
            logger.warning(f"==liuq debug== 提取模板变量失败: {e}")
            return []
    
    def _get_error_template(self) -> Template:
        """获取错误模板"""
        error_template_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>模板错误</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="alert alert-danger">
            <h4 class="alert-heading">模板处理错误</h4>
            <p>{{ error_message }}</p>
            <hr>
            <p class="mb-0">生成时间: {{ current_time }}</p>
        </div>
    </div>
</body>
</html>'''
        return Template(error_template_content)
    
    def _load_builtin_templates(self) -> Dict[str, str]:
        """加载内置模板"""
        templates = {}
        
        # 默认报告模板
        templates['default'] = self._get_default_report_template()
        
        # 简单报告模板
        templates['simple'] = self._get_simple_report_template()
        
        # 详细报告模板
        templates['detailed'] = self._get_detailed_report_template()

        # EXIF对比报告模板
        templates['exif_comparison'] = self._get_exif_comparison_template()

        # Map分析报告模板（复用详细模板）
        templates['map_analysis'] = self._get_detailed_report_template()

        return templates
    
    def _get_default_report_template(self) -> str:
        """获取默认报告模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .report-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .chart-container { position: relative; height: 400px; margin: 20px 0; }
        .summary-card { border-left: 4px solid #007bff; }
        .analysis-section { margin-top: 30px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- 报告头部 -->
        <div class="row report-header p-4 mb-4">
            <div class="col-12">
                <h1 class="display-4">{{ title }}</h1>
                <p class="lead">生成时间: {{ generation_time }}</p>
            </div>
        </div>
        
        <!-- 概览信息 -->
        {% if summary %}
        <div class="row mb-4">
            <div class="col-12">
                <div class="card summary-card">
                    <div class="card-header">
                        <h3>分析概览</h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            {% for key, value in summary.items() %}
                            <div class="col-md-3 mb-2">
                                <strong>{{ key }}:</strong> {{ value }}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- 图表内容 -->
        {% if chart_content %}
        <div class="row analysis-section">
            <div class="col-12">
                <h2>数据可视化</h2>
                {{ chart_content | safe }}
            </div>
        </div>
        {% endif %}
        
        <!-- 多维度分析 -->
        {% if multi_dimensional_content %}
        {{ multi_dimensional_content | safe }}
        {% endif %}
        
        <!-- 其他内容 -->
        {% if additional_content %}
        <div class="row analysis-section">
            <div class="col-12">
                {{ additional_content | safe }}
            </div>
        </div>
        {% endif %}
    </div>
    
    <!-- JavaScript -->
    {% if chart_scripts %}
    <script>
        {{ chart_scripts | safe }}
    </script>
    {% endif %}
</body>
</html>'''
    
    def _get_simple_report_template(self) -> str:
        """获取简单报告模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { border-bottom: 2px solid #333; padding-bottom: 10px; }
        .summary { background: #f5f5f5; padding: 15px; margin: 20px 0; }
        .content { margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>生成时间: {{ generation_time }}</p>
    </div>
    
    {% if summary %}
    <div class="summary">
        <h2>概览</h2>
        {% for key, value in summary.items() %}
        <p><strong>{{ key }}:</strong> {{ value }}</p>
        {% endfor %}
    </div>
    {% endif %}
    
    <div class="content">
        {{ content | safe }}
    </div>
</body>
</html>'''
    
    def _get_detailed_report_template(self) -> str:
        """获取详细报告模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .report-header { background: linear-gradient(45deg, #1e3c72 0%, #2a5298 100%); color: white; }
        .chart-container { position: relative; height: 450px; margin: 25px 0; }
        .summary-card { border-left: 5px solid #28a745; }
        .analysis-card { border-left: 5px solid #17a2b8; }
        .warning-card { border-left: 5px solid #ffc107; }
        .danger-card { border-left: 5px solid #dc3545; }
        .toc { position: sticky; top: 20px; }
        .section-divider { border-top: 2px solid #e9ecef; margin: 40px 0 30px 0; }

        /* Map分析专用样式优化 - 模仿原始报告效果 */
        .map-stats-overview {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(79, 172, 254, 0.3);
        }
        .map-stats-item {
            text-align: center;
            padding: 15px;
        }
        .map-stats-item h6 {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-bottom: 8px;
        }
        .map-stats-item .stats-number {
            font-size: 2rem;
            font-weight: 300;
            margin: 0;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- 详细报告头部 -->
        <div class="row report-header p-5 mb-4">
            <div class="col-12 text-center">
                <h1 class="display-3"><i class="fas fa-chart-line me-3"></i>{{ title }}</h1>
                <p class="lead fs-4">详细分析报告</p>
                <p class="fs-5">生成时间: {{ generation_time }}</p>
            </div>
        </div>
        
        <div class="row">
            <!-- 目录 -->
            <div class="col-md-3">
                <div class="toc">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-list me-2"></i>目录</h5>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                <li><a href="#summary">分析概览</a></li>
                                <li><a href="#charts">数据可视化</a></li>
                                <li><a href="#detailed-analysis">详细分析</a></li>
                                <li><a href="#conclusions">结论建议</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 主要内容 -->
            <div class="col-md-9">
                <!-- 概览信息 -->
                {% if summary %}
                <section id="summary">
                    <!-- Map分析专用统计展示 -->
                    {% if title and 'Map' in title %}
                    <div class="map-stats-overview mb-4">
                        <div class="row">
                            <div class="col-md-2 map-stats-item">
                                <h6>总Map点数</h6>
                                <p class="stats-number">{{ summary.get('total_map_count', summary.get('total_points', 0)) }}</p>
                            </div>
                            <div class="col-md-2 map-stats-item">
                                <h6>室内场景</h6>
                                <p class="stats-number">{{ summary.get('scene_distribution', {}).get('indoor', summary.get('indoor_count', 0)) }}</p>
                            </div>
                            <div class="col-md-2 map-stats-item">
                                <h6>室外场景</h6>
                                <p class="stats-number">{{ summary.get('scene_distribution', {}).get('outdoor', summary.get('outdoor_count', 0)) }}</p>
                            </div>
                            <div class="col-md-2 map-stats-item">
                                <h6>夜景场景</h6>
                                <p class="stats-number">{{ summary.get('scene_distribution', {}).get('night', summary.get('night_count', 0)) }}</p>
                            </div>
                            <div class="col-md-2 map-stats-item">
                                <h6>平均权重</h6>
                                <p class="stats-number">{{ "%.3f"|format(summary.get('avg_weight', summary.get('mean', 0))) }}</p>
                            </div>
                            <div class="col-md-2 map-stats-item">
                                <h6>处理时长</h6>
                                <p class="stats-number">{{ summary.get('processing_duration', '0.00s') }}</p>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <!-- 通用统计展示 -->
                    <div class="card summary-card mb-4">
                        <div class="card-header">
                            <h3><i class="fas fa-info-circle me-2"></i>分析概览</h3>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                {% for key, value in summary.items() %}
                                <div class="col-lg-4 col-md-6 mb-3">
                                    <div class="card h-100">
                                        <div class="card-body text-center">
                                            <h5 class="card-title">{{ key }}</h5>
                                            <p class="card-text display-6 text-primary">{{ value }}</p>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                    {% endif %}
                </section>
                {% endif %}
                
                <!-- 图表内容 -->
                {% if chart_content %}
                <div class="section-divider"></div>
                <section id="charts">
                    <div class="card analysis-card mb-4">
                        <div class="card-header">
                            <h3><i class="fas fa-chart-bar me-2"></i>数据可视化</h3>
                        </div>
                        <div class="card-body">
                            {{ chart_content | safe }}
                        </div>
                    </div>
                </section>
                {% endif %}
                
                <!-- 详细分析 -->
                {% if detailed_analysis %}
                <div class="section-divider"></div>
                <section id="detailed-analysis">
                    <div class="card analysis-card mb-4">
                        <div class="card-header">
                            <h3><i class="fas fa-microscope me-2"></i>详细分析</h3>
                        </div>
                        <div class="card-body">
                            {{ detailed_analysis | safe }}
                        </div>
                    </div>
                </section>
                {% endif %}
                
                <!-- 多维度分析 -->
                {% if multi_dimensional_content %}
                <div class="section-divider"></div>
                {{ multi_dimensional_content | safe }}
                {% endif %}
                
                <!-- 结论建议 -->
                {% if conclusions %}
                <div class="section-divider"></div>
                <section id="conclusions">
                    <div class="card warning-card mb-4">
                        <div class="card-header">
                            <h3><i class="fas fa-lightbulb me-2"></i>结论与建议</h3>
                        </div>
                        <div class="card-body">
                            {{ conclusions | safe }}
                        </div>
                    </div>
                </section>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- JavaScript -->
    {% if chart_scripts %}
    <script>
        {{ chart_scripts | safe }}
    </script>
    {% endif %}
    
    <!-- 平滑滚动 -->
    <script>
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>
</body>
</html>'''

    def _get_exif_comparison_template(self) -> str:
        """获取EXIF对比报告模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EXIF对比分析报告</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    {{ chart_loader_script | safe }}
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            margin: 0;
            padding: 0;
        }
        .main-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin: 20px;
            padding: 30px;
        }
        .report-header {
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            text-align: center;
        }
        .summary-card {
            background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .data-table {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            max-height: 600px;
            overflow-y: auto;
        }
        .table th {
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            font-weight: 600;
        }
        .table td {
            border-color: #e9ecef;
            vertical-align: middle;
        }
        .print-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }
        @media print {
            .print-btn { display: none; }
            .main-container { box-shadow: none; margin: 0; }
            .chart-container { height: 300px; }
        }
    </style>
</head>
<body>
    <button class="btn btn-primary print-btn" onclick="window.print()">
        <i class="fas fa-print"></i> 打印报告
    </button>

    <div class="main-container">
        <!-- 报告标题 -->
        <div class="report-header">
            <h1 class="display-4 mb-3">
                <i class="fas fa-chart-line"></i> {{ title }}
            </h1>
            <p class="lead">生成时间: {{ generation_time }}</p>
        </div>

        <!-- 摘要信息 -->
        {% if summary %}
        <div class="summary-card">
            <h3><i class="fas fa-info-circle"></i> 分析摘要</h3>
            <div class="row text-center mt-3">
                {% for key, value in summary.items() %}
                <div class="col-md-3 mb-2">
                    <h5>{{ key }}</h5>
                    <h3>{{ value }}</h3>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- 图表区域 -->
        {% if chart_content %}
        <div class="row mb-4">
            <div class="col-12">
                <h3><i class="fas fa-chart-bar"></i> 数据可视化</h3>
                {{ chart_content | safe }}
            </div>
        </div>
        {% endif %}

        <!-- 详细数据表格 -->
        {% if data_table %}
        <div class="row">
            <div class="col-12">
                <h3><i class="fas fa-table"></i> 详细数据</h3>
                <div class="data-table">
                    {{ data_table | safe }}
                </div>
            </div>
        </div>
        {% endif %}

        <!-- 报告尾部 -->
        <div class="row">
            <div class="col-12 text-center">
                <hr class="my-4">
                <p class="text-muted">
                    <i class="fas fa-robot"></i>
                    FastMapV2 - EXIF对比分析工具 v2.0.0 |
                    龙sir团队 |
                    报告生成时间: {{ generation_time }}
                </p>
            </div>
        </div>
    </div>

    <script>
        // 图表脚本
        {{ chart_scripts | safe }}
    </script>
</body>
</html>'''


class InMemoryTemplateLoader(BaseLoader):
    """内存模板加载器"""
    
    def __init__(self, templates: Optional[Dict[str, str]] = None):
        self.templates = templates or {}
    
    def get_source(self, environment, template):
        if template not in self.templates:
            raise TemplateNotFound(template)
        
        source = self.templates[template]
        return source, None, lambda: True


# 全局模板服务实例
_template_service: Optional[HTMLTemplateService] = None


def get_html_template_service() -> HTMLTemplateService:
    """获取HTML模板服务实例"""
    global _template_service
    
    if _template_service is None:
        _template_service = HTMLTemplateService()
        logger.info("==liuq debug== 创建HTML模板服务实例")
    
    return _template_service