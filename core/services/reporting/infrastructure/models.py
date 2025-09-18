#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告数据结构定义
==liuq debug== 报告生成系统的标准数据结构

作者: 龙sir团队
创建时间: 2025-09-16
版本: 1.0.0
描述: 定义报告生成系统的标准数据结构和类型
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum


class SectionType(Enum):
    """报告段落类型"""
    TEXT = "text"
    TABLE = "table"
    CHART = "chart"
    KPI = "kpi"
    IMAGE = "image"
    HTML = "html"


class ChartType(Enum):
    """图表类型"""
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    PIE = "pie"


@dataclass
class ReportSection:
    """报告段落数据结构"""
    type: SectionType
    title: str
    content: Dict[str, Any]
    styles: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = ""


@dataclass
class TableData:
    """表格数据结构"""
    headers: List[str]
    rows: List[List[Any]]
    caption: str = ""
    styles: Dict[str, str] = field(default_factory=dict)
    sortable: bool = True
    searchable: bool = True


@dataclass
class ChartData:
    """图表数据结构"""
    type: ChartType
    title: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Dict[str, Any] = field(default_factory=dict)
    styles: Dict[str, str] = field(default_factory=dict)


@dataclass
class KPIData:
    """KPI指标数据结构"""
    title: str
    value: Union[str, int, float]
    unit: str = ""
    trend: Optional[str] = None  # "up", "down", "stable"
    change: Optional[float] = None
    description: str = ""


@dataclass
class ReportData:
    """报告数据结构"""
    title: str
    sections: List[ReportSection]
    metadata: Dict[str, Any] = field(default_factory=dict)
    styles: Dict[str, str] = field(default_factory=dict)
    scripts: List[str] = field(default_factory=list)
    
    def add_section(self, section: ReportSection) -> None:
        """添加报告段落"""
        if not section.id:
            section.id = f"section_{len(self.sections) + 1}"
        self.sections.append(section)
    
    def get_section_by_id(self, section_id: str) -> Optional[ReportSection]:
        """根据ID获取段落"""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None
    
    def get_sections_by_type(self, section_type: SectionType) -> List[ReportSection]:
        """根据类型获取段落"""
        return [section for section in self.sections if section.type == section_type]


@dataclass
class ReportConfig:
    """报告配置"""
    title: str
    output_path: str
    template_name: str = "reporting/domains/exif/new_report.html"
    include_styles: bool = True
    include_scripts: bool = True
    custom_styles: Dict[str, str] = field(default_factory=dict)
    custom_scripts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# 宸ュ巶鍑芥暟
def create_text_section(title: str, content: str, **kwargs) -> ReportSection:
    """创建文本段落"""
    return ReportSection(
        type=SectionType.TEXT,
        title=title,
        content={"text": content},
        **kwargs
    )


def create_table_section(title: str, table_data: TableData, **kwargs) -> ReportSection:
    """创建表格段落"""
    return ReportSection(
        type=SectionType.TABLE,
        title=title,
        content=table_data.__dict__,
        **kwargs
    )


def create_chart_section(title: str, chart_data: ChartData, **kwargs) -> ReportSection:
    """创建图表段落"""
    return ReportSection(
        type=SectionType.CHART,
        title=title,
        content=chart_data.__dict__,
        **kwargs
    )


def create_kpi_section(title: str, kpi_data: List[KPIData], **kwargs) -> ReportSection:
    """创建KPI段落"""
    return ReportSection(
        type=SectionType.KPI,
        title=title,
        content={"kpis": [kpi.__dict__ for kpi in kpi_data]},
        **kwargs
    )


def create_html_section(title: str, html_content: str, **kwargs) -> ReportSection:
    """创建HTML段落（用于兼容性）"""
    return ReportSection(
        type=SectionType.HTML,
        title=title,
        content={"html": html_content},
        **kwargs
    )
