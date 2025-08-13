#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF数据模型定义
==liuq debug== FastMapV2 EXIF数据处理模型

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 17:41:00 +08:00; Reason: P1-LD-002 设计核心数据模型; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: EXIF数据的标准化模型定义，用于Phase 2功能
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class ExifFieldType(Enum):
    """EXIF字段类型枚举"""
    DETECT_MAP = "detect_map"
    OFFSET_MAP = "offset_map"
    MAP_WEIGHT = "map_weight_offsetMapWeight"
    SENSOR_CCT = "sensorCCT"
    BV = "BV"
    IR = "IR"
    OTHER = "other"


@dataclass
class ExifField:
    """
    EXIF字段数据模型
    
    表示单个EXIF字段的数据
    """
    name: str                          # 字段名称
    value: Any                         # 字段值
    data_type: str                     # 数据类型
    field_type: ExifFieldType = ExifFieldType.OTHER  # 字段类型
    is_processed: bool = False         # 是否已处理
    processing_notes: str = ""         # 处理备注
    
    def __post_init__(self):
        """初始化后处理，自动推断字段类型"""
        if self.field_type == ExifFieldType.OTHER:
            self.field_type = self._infer_field_type()
    
    def _infer_field_type(self) -> ExifFieldType:
        """
        根据字段名推断字段类型
        
        Returns:
            推断的字段类型
        """
        name_lower = self.name.lower()
        
        if 'detect_map' in name_lower:
            return ExifFieldType.DETECT_MAP
        elif 'offset_map' in name_lower:
            return ExifFieldType.OFFSET_MAP
        elif 'map_weight' in name_lower and 'offsetmapweight' in name_lower:
            return ExifFieldType.MAP_WEIGHT
        elif 'sensorcct' in name_lower:
            return ExifFieldType.SENSOR_CCT
        elif name_lower == 'bv':
            return ExifFieldType.BV
        elif name_lower == 'ir':
            return ExifFieldType.IR
        else:
            return ExifFieldType.OTHER
    
    def get_numeric_value(self) -> Optional[float]:
        """
        获取数值类型的值
        
        Returns:
            数值，如果无法转换则返回None
        """
        try:
            if isinstance(self.value, (int, float)):
                return float(self.value)
            elif isinstance(self.value, str):
                # 尝试解析字符串中的数值
                import re
                numbers = re.findall(r'-?\d+\.?\d*', self.value)
                if numbers:
                    return float(numbers[0])
            return None
        except (ValueError, TypeError):
            return None


@dataclass
class ExifRecord:
    """
    EXIF记录数据模型
    
    表示单张图片的完整EXIF数据
    """
    filename: str                      # 文件名
    filepath: str                      # 文件路径
    fields: List[ExifField]           # EXIF字段列表
    timestamp: datetime = field(default_factory=datetime.now)  # 提取时间
    metadata: Dict[str, Any] = field(default_factory=dict)     # 元数据
    
    def get_field_by_name(self, field_name: str) -> Optional[ExifField]:
        """
        根据字段名获取EXIF字段
        
        Args:
            field_name: 字段名
            
        Returns:
            找到的字段，如果不存在则返回None
        """
        for field in self.fields:
            if field.name == field_name:
                return field
        return None
    
    def get_fields_by_type(self, field_type: ExifFieldType) -> List[ExifField]:
        """
        根据字段类型获取EXIF字段列表
        
        Args:
            field_type: 字段类型
            
        Returns:
            指定类型的字段列表
        """
        return [field for field in self.fields if field.field_type == field_type]
    
    def get_core_parameters(self) -> Dict[str, Optional[float]]:
        """
        获取核心参数值
        
        Returns:
            核心参数字典
        """
        core_params = {}
        
        # 获取BV值
        bv_field = self.get_field_by_name('BV')
        core_params['bv'] = bv_field.get_numeric_value() if bv_field else None
        
        # 获取IR值
        ir_field = self.get_field_by_name('IR')
        core_params['ir'] = ir_field.get_numeric_value() if ir_field else None
        
        # 获取sensorCCT值
        cct_fields = self.get_fields_by_type(ExifFieldType.SENSOR_CCT)
        if cct_fields:
            core_params['sensor_cct'] = cct_fields[0].get_numeric_value()
        else:
            core_params['sensor_cct'] = None
        
        return core_params


@dataclass
class ExifDataset:
    """
    EXIF数据集模型
    
    表示一组图片的EXIF数据集合
    """
    records: List[ExifRecord]          # EXIF记录列表
    dataset_name: str = ""             # 数据集名称
    device_type: str = ""              # 设备类型 'reference' | 'debug'
    extraction_config: Dict[str, Any] = field(default_factory=dict)  # 提取配置
    
    def get_field_names(self) -> List[str]:
        """
        获取所有字段名称
        
        Returns:
            字段名称列表
        """
        field_names = set()
        for record in self.records:
            for field in record.fields:
                field_names.add(field.name)
        return sorted(list(field_names))
    
    def get_records_by_field_value(self, field_name: str, value: Any) -> List[ExifRecord]:
        """
        根据字段值筛选记录
        
        Args:
            field_name: 字段名
            value: 字段值
            
        Returns:
            匹配的记录列表
        """
        matching_records = []
        for record in self.records:
            field = record.get_field_by_name(field_name)
            if field and field.value == value:
                matching_records.append(record)
        return matching_records
    
    def get_parameter_trends(self) -> Dict[str, List[float]]:
        """
        获取参数趋势数据
        
        Returns:
            参数趋势字典，键为参数名，值为数值列表
        """
        trends = {
            'bv': [],
            'ir': [],
            'sensor_cct': []
        }
        
        for record in self.records:
            core_params = record.get_core_parameters()
            for param_name, param_value in core_params.items():
                if param_value is not None:
                    trends[param_name].append(param_value)
                else:
                    # 用前一个值填充，如果没有前一个值则用0
                    if trends[param_name]:
                        trends[param_name].append(trends[param_name][-1])
                    else:
                        trends[param_name].append(0.0)
        
        return trends
    
    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        获取数据集统计信息
        
        Returns:
            统计信息字典
        """
        trends = self.get_parameter_trends()
        statistics = {}
        
        for param_name, values in trends.items():
            if values:
                statistics[param_name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / len(values),
                    'std': self._calculate_std(values)
                }
            else:
                statistics[param_name] = {
                    'count': 0,
                    'min': 0,
                    'max': 0,
                    'mean': 0,
                    'std': 0
                }
        
        return statistics
    
    def _calculate_std(self, values: List[float]) -> float:
        """
        计算标准差
        
        Args:
            values: 数值列表
            
        Returns:
            标准差
        """
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5


@dataclass
class TrendAnalysisResult:
    """
    趋势分析结果模型
    
    存储EXIF数据的趋势分析结果
    """
    dataset: ExifDataset               # 原始数据集
    parameter_trends: Dict[str, List[float]]  # 参数趋势
    statistics: Dict[str, Dict[str, float]]   # 统计信息
    comparison_results: Dict[str, Any] = field(default_factory=dict)  # 对比结果
    
    # 可视化数据
    trend_chart_data: Dict[str, Any] = field(default_factory=dict)
    distribution_data: Dict[str, Any] = field(default_factory=dict)
    
    # 分析元数据
    analysis_timestamp: str = ""
    analysis_config: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取趋势分析摘要
        
        Returns:
            分析摘要字典
        """
        return {
            'total_records': len(self.dataset.records),
            'device_type': self.dataset.device_type,
            'parameter_count': len(self.parameter_trends),
            'statistics_summary': {
                param: stats.get('mean', 0) 
                for param, stats in self.statistics.items()
            },
            'analysis_time': self.analysis_timestamp
        }
