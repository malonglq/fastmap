#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接口与数据模型: EXIF AWB 解析
==liuq debug== FastMapV2 EXIF Processing Interfaces

{{CHENGQI:
Action: Added; Timestamp: 2025-08-11 12:20:00 +08:00; Reason: 新增EXIF解析数据模型与接口; Principle_Applied: SOLID-ISP;
}}
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Set, Callable

# 规范化字段常量（已移除）
# 根据需求，EXIF字段改为完全使用原始JSON扁平键名进行选择与导出
ExifField: Dict[str, str] = {}


@dataclass
class ExifParseOptions:
    # selected_fields 现在完全使用原始扁平键名，由GUI按优先顺序组织
    selected_fields: List[str] = field(default_factory=list)
    recursive: bool = True
    extensions: List[str] = field(default_factory=lambda: ['.jpg', '.jpeg', '.png', '.bmp'])
    include_source_columns: bool = False  # 默认不在CSV中包含“来源键名”列
    # 性能优化相关开关（导出场景推荐：keep_raw_json=GUI勾选时才True；其余False）
    keep_raw_json: bool = False        # 是否保留每条记录的 raw_json
    build_raw_flat: bool = True        # 是否构建 raw_flat（完整扁平化字典）
    compute_available: bool = True     # 是否统计 raw_available_keys/order 与 available_fields
    debug_log_keys: bool = True        # 是否打印首样本keys与写调试JSON（影响磁盘IO）
    # 进度与取消（用于GUI线程化）
    on_progress: Optional[Callable[[int, int, str], None]] = None  # processed, total, stage
    cancel_check: Optional[Callable[[], bool]] = None


@dataclass
class ExifRecord:
    image_path: Path
    image_name: str
    fields: Dict[str, Any] = field(default_factory=dict)  # 规范化字段或原始键 -> 值
    field_sources: Dict[str, str] = field(default_factory=dict)  # 字段 -> 实际使用的原始键名
    raw_json: Dict[str, Any] = field(default_factory=dict)
    raw_flat: Dict[str, Any] = field(default_factory=dict)
    errors: Optional[str] = None


@dataclass
class ExifParseResult:
    records: List[ExifRecord]
    total: int
    errors: List[str] = field(default_factory=list)
    available_fields: Set[str] = field(default_factory=set)  # 规范化字段集合（保留字段，不再使用）
    raw_available_keys: Set[str] = field(default_factory=set)  # 原始JSON扁平键集合（向后兼容）
    raw_available_order: List[str] = field(default_factory=list)  # 原始JSON扁平键“出现顺序”（用于UI排序）


class IExifParserService(Protocol):
    def parse_directory(self, root_dir: Path, options: ExifParseOptions) -> ExifParseResult:
        ...
    def discover_keys(self, root_dir: Path, recursive: bool = True, sample: int = 3) -> List[str]:
        ...


class IExifCsvExporter(Protocol):
    def export_csv(
        self,
        result: ExifParseResult,
        csv_path: Path,
        selected_fields: List[str],
        include_source_columns: bool = False,
        include_raw_json: bool = False,
        include_timestamp: bool = False,
        include_image_path: bool = False,
    ) -> Path:
        ...


class IExifRawExporter(Protocol):
    def export_raw_json(self, result: ExifParseResult, out_path: Path) -> Path:
        ...

