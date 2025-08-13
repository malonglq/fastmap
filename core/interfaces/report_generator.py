#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成器接口定义
==liuq debug== FastMapV2报告生成抽象接口

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 17:45:00 +08:00; Reason: P1-LD-003 抽象化HTML/Chart生成器; Principle_Applied: SOLID-I接口隔离原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: 定义报告生成器的抽象接口，支持不同类型的数据和报告格式
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum


class ReportType(Enum):
    """报告类型枚举"""
    EXIF_COMPARISON = "exif_comparison"
    MAP_MULTI_DIMENSIONAL = "map_multi_dimensional"
    RESERVED = "reserved"


class IReportGenerator(ABC):
    """报告生成器基础接口"""

    @abstractmethod
    def generate(self, data: Dict[str, Any]) -> str:
        """
        生成报告并返回文件路径

        Args:
            data: 报告生成所需的数据

        Returns:
            生成的报告文件路径
        """
        pass

    @abstractmethod
    def get_report_name(self) -> str:
        """
        获取报告类型名称

        Returns:
            报告类型名称
        """
        pass

    @abstractmethod
    def get_report_type(self) -> ReportType:
        """
        获取报告类型

        Returns:
            报告类型枚举
        """
        pass

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        验证输入数据是否有效

        Args:
            data: 待验证的数据

        Returns:
            数据是否有效
        """
        pass


class IReportDataProvider(ABC):
    """报告数据提供者接口"""
    
    @abstractmethod
    def prepare_report_data(self) -> Dict[str, Any]:
        """
        准备报告数据
        
        Returns:
            报告数据字典
        """
        pass
    
    @abstractmethod
    def get_report_title(self) -> str:
        """
        获取报告标题
        
        Returns:
            报告标题
        """
        pass
    
    @abstractmethod
    def get_summary_data(self) -> Dict[str, Any]:
        """
        获取摘要数据
        
        Returns:
            摘要数据字典
        """
        pass


class IChartGenerator(ABC):
    """图表生成器接口"""
    
    @abstractmethod
    def generate_scatter_chart(self, data: Dict[str, Any], chart_id: str) -> str:
        """
        生成散点图
        
        Args:
            data: 图表数据
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        pass
    
    @abstractmethod
    def generate_heatmap_chart(self, data: Dict[str, Any], chart_id: str) -> str:
        """
        生成热力图
        
        Args:
            data: 图表数据
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        pass
    
    @abstractmethod
    def generate_trend_chart(self, data: Dict[str, Any], chart_id: str) -> str:
        """
        生成趋势图
        
        Args:
            data: 图表数据
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        pass
    
    @abstractmethod
    def generate_statistics_chart(self, data: Dict[str, Any], chart_id: str) -> str:
        """
        生成统计图表
        
        Args:
            data: 图表数据
            chart_id: 图表ID
            
        Returns:
            JavaScript代码字符串
        """
        pass


class ITemplateProvider(ABC):
    """模板提供者接口"""
    
    @abstractmethod
    def get_template_content(self, template_name: str) -> str:
        """
        获取模板内容
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板内容字符串
        """
        pass
    
    @abstractmethod
    def get_available_templates(self) -> List[str]:
        """
        获取可用模板列表
        
        Returns:
            模板名称列表
        """
        pass


class IHTMLReportGenerator(ABC):
    """HTML报告生成器接口"""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass


class IVisualizationProvider(ABC):
    """可视化数据提供者接口"""
    
    @abstractmethod
    def get_scatter_plot_data(self) -> Dict[str, Any]:
        """
        获取散点图数据
        
        Returns:
            散点图数据字典
        """
        pass
    
    @abstractmethod
    def get_heatmap_data(self) -> Dict[str, Any]:
        """
        获取热力图数据
        
        Returns:
            热力图数据字典
        """
        pass
    
    @abstractmethod
    def get_trend_data(self) -> Dict[str, Any]:
        """
        获取趋势数据
        
        Returns:
            趋势数据字典
        """
        pass
    
    @abstractmethod
    def get_statistics_data(self) -> Dict[str, Any]:
        """
        获取统计数据
        
        Returns:
            统计数据字典
        """
        pass


class IFileManager(ABC):
    """文件管理器接口"""
    
    @abstractmethod
    def ensure_directory(self, directory_path: Path) -> None:
        """
        确保目录存在
        
        Args:
            directory_path: 目录路径
        """
        pass
    
    @abstractmethod
    def generate_unique_filename(self, directory: Path, extension: str) -> str:
        """
        生成唯一文件名
        
        Args:
            directory: 目录路径
            extension: 文件扩展名
            
        Returns:
            唯一文件路径
        """
        pass
    
    @abstractmethod
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> None:
        """
        写入文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 编码格式
        """
        pass


class ReportGeneratorConfig:
    """报告生成器配置类"""
    
    def __init__(self):
        self.template_dir = "templates"
        self.output_dir = "output"
        self.chart_colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
        ]
        self.default_template = "default"
        self.auto_open_report = True
        self.include_raw_data = False
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'template_dir': self.template_dir,
            'output_dir': self.output_dir,
            'chart_colors': self.chart_colors,
            'default_template': self.default_template,
            'auto_open_report': self.auto_open_report,
            'include_raw_data': self.include_raw_data
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ReportGeneratorConfig':
        """从字典创建配置"""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config
