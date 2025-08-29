#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map分析服务接口定义
==liuq debug== FastMapV2 Map分析服务抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    from core.models.map_data import MapConfiguration, MapPoint, AnalysisResult
except ImportError:
    MapConfiguration = Any
    MapPoint = Any
    AnalysisResult = Any

@dataclass
class AnalysisOptions:
    include_statistics: bool = True
    include_visualization: bool = True
    precision: int = 6

@dataclass
class AnalysisResult:
    success: bool
    configuration: Optional[MapConfiguration] = None
    statistics: Dict[str, Any] = None
    visualizations: Dict[str, Any] = None
    errors: List[str] = None
    analysis_time: Optional[float] = None
    
    def __post_init__(self):
        if self.statistics is None:
            self.statistics = {}
        if self.visualizations is None:
            self.visualizations = {}
        if self.errors is None:
            self.errors = []

class IMapAnalyzerService(ABC):
    """Map分析服务接口"""
    
    @abstractmethod
    def analyze_configuration(self, configuration: MapConfiguration,
                             options: Optional[AnalysisOptions] = None) -> AnalysisResult:
        pass
    
    @abstractmethod
    def analyze_coordinates(self, map_points: List[MapPoint]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def analyze_weights(self, map_points: List[MapPoint]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def analyze_ranges(self, map_points: List[MapPoint]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def compare_configurations(self, config1: MapConfiguration,
                             config2: MapConfiguration) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def export_analysis_report(self, result: AnalysisResult,
                             output_path: Union[str, Path]) -> bool:
        pass

class ITemperatureSpanAnalyzer(ABC):
    """温度跨度分析器接口"""
    
    @abstractmethod
    def analyze_temperature_spans(self, map_points: List[MapPoint]) -> Dict[str, Any]:
        pass

class IMultiDimensionalAnalyzer(ABC):
    """多维度分析器接口"""
    
    @abstractmethod
    def analyze_multi_dimensional(self, configuration: MapConfiguration,
                                dimensions: List[str]) -> Dict[str, Any]:
        pass

class IVisualizationService(ABC):
    """可视化服务接口"""
    
    @abstractmethod
    def generate_scatter_plot(self, map_points: List[MapPoint],
                            x_field: str, y_field: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def generate_heatmap(self, map_points: List[MapPoint],
                        value_field: str) -> Dict[str, Any]:
        pass

class MapAnalysisError(Exception):
    """Map分析错误"""
    pass

class OptimizationError(Exception):
    """优化错误"""
    pass

__version__ = "2.0.0"
