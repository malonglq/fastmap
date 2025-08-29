#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成服务接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

class OutputFormat(Enum):
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    JSON = "json"

@dataclass
class ReportOptions:
    output_format: OutputFormat
    output_path: Path
    template_path: Optional[Path] = None
    include_charts: bool = True
    include_statistics: bool = True

@dataclass
class ReportResult:
    success: bool
    output_path: Path
    generation_time: float
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class IReportGeneratorService(ABC):
    """报告生成服务主接口"""
    
    @abstractmethod
    def generate_report(self, data: Dict[str, Any], options: ReportOptions) -> ReportResult:
        pass

class IChartGeneratorService(ABC):
    """图表生成服务接口"""
    
    @abstractmethod
    def generate_chart(self, chart_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def save_chart(self, chart_data: Dict[str, Any], output_path: Path) -> bool:
        pass

class ITemplateManager(ABC):
    """模板管理接口"""
    
    @abstractmethod
    def load_template(self, template_path: Path) -> str:
        pass
    
    @abstractmethod
    def render_template(self, template: str, data: Dict[str, Any]) -> str:
        pass

class ReportGenerationError(Exception):
    """报告生成错误"""
    pass

class TemplateError(Exception):
    """模板错误"""
    pass

__version__ = "2.0.0"