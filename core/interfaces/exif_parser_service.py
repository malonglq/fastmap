#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF解析服务接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

class ExifDataType(Enum):
    RAW = "raw"
    PROCESSED = "processed"
    METADATA = "metadata"

@dataclass
class ExifParseOptionsExtended:
    directory: Path
    recursive: bool = True
    include_subdirs: bool = True
    file_patterns: List[str] = None
    
    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["*.jpg", "*.jpeg", "*.png"]

@dataclass
class ExifParseResultExtended:
    success: bool
    data: Dict[str, Any] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

@dataclass
class ExifExportOptions:
    output_path: Path
    format: str = "csv"
    include_headers: bool = True
    encoding: str = "utf-8"

class IExifParserService(ABC):
    """EXIF解析服务主接口"""
    
    @abstractmethod
    def parse_directory(self, options: ExifParseOptionsExtended) -> ExifParseResultExtended:
        pass
    
    @abstractmethod
    def parse_single_file(self, file_path: Path) -> Dict[str, Any]:
        pass

class IExifDataProcessor(ABC):
    """EXIF数据处理接口"""
    
    @abstractmethod
    def process_raw_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def flatten_exif_data(self, exif_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class IExifExporter(ABC):
    """EXIF导出接口"""
    
    @abstractmethod
    def export_to_csv(self, data: List[Dict[str, Any]], options: ExifExportOptions) -> bool:
        pass
    
    @abstractmethod
    def export_to_json(self, data: List[Dict[str, Any]], options: ExifExportOptions) -> bool:
        pass

class ExifParseError(Exception):
    """EXIF解析错误"""
    pass

class ExifExportError(Exception):
    """EXIF导出错误"""
    pass

class DllInitializationError(Exception):
    """DLL初始化错误"""
    pass

__version__ = "2.0.0"