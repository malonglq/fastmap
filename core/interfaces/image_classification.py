#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接口与数据模型: 图片分类
==liuq debug== FastMapV2 Image Classification Interfaces

{{CHENGQI:
Action: Added; Timestamp: 2025-08-11 10:55:00 +08:00; Reason: 新增图片分类接口与模型; Principle_Applied: SOLID-ISP;
}}
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
from pathlib import Path


@dataclass
class ChangeThresholds:
    # CCT 绝对值(K)
    cct_large_min: float = 500.0
    cct_medium_min: float = 100.0
    cct_medium_max: float = 500.0
    # 百分比(%)
    pct_large_min: float = 10.0
    pct_medium_min: float = 1.0
    pct_medium_max: float = 10.0
    # 新增：无变化上限（用于字段对比的百分比分类）；None 表示使用旧逻辑(仅0视为无变化)
    pct_no_change_max: Optional[float] = None


@dataclass
class ClassificationOptions:
    primary_field: str
    selected_fields: List[str] = field(default_factory=list)
    thresholds: ChangeThresholds = field(default_factory=ChangeThresholds)
    is_cct_field: Optional[bool] = None  # None=自动判断
    # 新增：字段对比模式（compare_pair!=None 表示启用）
    # compare_pair: [fieldA, fieldB]
    compare_pair: Optional[List[str]] = None
    # 变化度量：'percent_spc'（默认）、'percent_rc'、'abs'
    metric: str = 'percent_spc'
    # 零值保护阈值（用于percent_rc）
    epsilon: float = 1e-6


@dataclass
class FieldChange:
    before: Any
    after: Any
    change_percentage: Optional[float]  # 非CCT时为百分比，CCT时可为None
    absolute_change: Optional[float]     # CCT时为K变化量，百分比模式下为数值差


@dataclass
class ImageInfo:
    image_name: str
    primary_field_change: float
    primary_field_name: str
    is_cct_field: bool
    field_changes: Dict[str, FieldChange]
    pair_data: Dict[str, Any]


@dataclass
class ClassificationSummaryItem:
    count: int
    percentage: float


@dataclass
class ClassificationResult:
    categories: Dict[str, List[ImageInfo]]
    summary: Dict[str, ClassificationSummaryItem]
    total: int


class IImageClassifierService(Protocol):
    def classify(self, match_result: Dict[str, Any], options: ClassificationOptions) -> ClassificationResult:
        ...


@dataclass
class ExportSelection:
    export_large: bool
    export_medium: bool
    export_small: bool
    export_no_change: bool


@dataclass
class NamingOptions:
    # 模板中可用占位: {field} 字段名, {sign} '+' 或 '-', {value} 数值
    percent_format: str = "_{field}{sign}{value:.2f}%"
    cct_format: str = "_{field}{sign}{value}K"


@dataclass
class ExportStats:
    started_at: float
    finished_at: float
    duration_seconds: float
    copied_counts: Dict[str, int]
    total_copied: int
    missing_files: List[str]
    chosen_categories: List[str]


class IImageExportService(Protocol):
    def export(self,
               classification: ClassificationResult,
               selection: ExportSelection,
               source_dir: Path,
               output_dir: Path,
               naming: NamingOptions,
               progress_cb: Optional[callable] = None) -> ExportStats:
        ...



# ==== Stats 面板与工作流门面 ====
from typing import Callable


@dataclass
class StatsCardItem:
    key: str
    title: str
    count: int
    percentage: float
    color: str


@dataclass
class StatsPanel:
    cards: List[StatsCardItem]
    total: int
    primary_field: str
    is_cct_field: bool


class IImageExportWorkflowService(Protocol):
    def compute_classification(self, match_result: Dict[str, Any], options: ClassificationOptions) -> ClassificationResult:
        ...

    def build_stats_panel(self, result: ClassificationResult) -> StatsPanel:
        ...

    def export_images(self,
                      result: ClassificationResult,
                      selection: ExportSelection,
                      source_dir: Path,
                      output_dir: Path,
                      naming: NamingOptions,
                      progress_cb: Optional[Callable] = None) -> ExportStats:
        ...
