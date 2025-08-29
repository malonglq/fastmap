#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML解析服务接口定义
==liuq debug== FastMapV2 XML解析服务抽象接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    from core.models.map_data import MapConfiguration, MapPoint, BaseBoundary
except ImportError:
    MapConfiguration = Any
    MapPoint = Any
    BaseBoundary = Any

class XMLVersion(Enum):
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"
    UNKNOWN = "unknown"

@dataclass
class ParseOptions:
    mode: str = "lenient"
    validate_structure: bool = True
    validate_content: bool = True
    encoding: str = "utf-8"
    device_type: str = "unknown"

@dataclass
class ParseResult:
    success: bool
    configuration: Optional[MapConfiguration] = None
    errors: List[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class WriteOptions:
    backup: bool = True
    preserve_format: bool = True
    encoding: str = "utf-8"
    validate_before_write: bool = True

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []

class IXMLParserService(ABC):
    """XML解析服务接口"""
    
    @abstractmethod
    def parse_xml(self, xml_path: Union[str, Path], 
                  options: Optional[ParseOptions] = None) -> ParseResult:
        pass
    
    @abstractmethod
    def write_xml(self, configuration: MapConfiguration, 
                  xml_path: Union[str, Path],
                  options: Optional[WriteOptions] = None) -> bool:
        pass
    
    @abstractmethod
    def validate_xml(self, xml_path: Union[str, Path]) -> ValidationResult:
        pass
    
    @abstractmethod
    def get_supported_versions(self) -> List[XMLVersion]:
        pass
    
    @abstractmethod
    def get_xml_metadata(self, xml_path: Union[str, Path]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def backup_xml(self, xml_path: Union[str, Path], 
                   backup_dir: Optional[Union[str, Path]] = None) -> str:
        pass
    
    @abstractmethod
    def extract_map_points(self, xml_path: Union[str, Path]) -> List[MapPoint]:
        pass
    
    @abstractmethod
    def extract_base_boundary(self, xml_path: Union[str, Path]) -> Optional[BaseBoundary]:
        pass

class IXMLWriterService(ABC):
    """XML写入服务接口"""
    
    @abstractmethod
    def write_configuration(self, configuration: MapConfiguration,
                           xml_path: Union[str, Path],
                           options: Optional[WriteOptions] = None) -> bool:
        pass

class IXMLValidatorService(ABC):
    """XML验证服务接口"""
    
    @abstractmethod
    def validate_structure(self, xml_path: Union[str, Path]) -> ValidationResult:
        pass
    
    @abstractmethod
    def validate_content(self, xml_path: Union[str, Path]) -> ValidationResult:
        pass

class IXMLMetadataService(ABC):
    """XML元数据服务接口"""
    
    @abstractmethod
    def get_version(self, xml_path: Union[str, Path]) -> XMLVersion:
        pass
    
    @abstractmethod
    def get_device_type(self, xml_path: Union[str, Path]) -> str:
        pass
    
    @abstractmethod
    def get_creation_time(self, xml_path: Union[str, Path]) -> Optional[str]:
        pass

class XMLParseError(Exception):
    """XML解析错误"""
    pass

class XMLWriteError(Exception):
    """XML写入错误"""
    pass

class XMLValidationError(Exception):
    """XML验证错误"""
    pass

class XMLBackupError(Exception):
    """XML备份错误"""
    pass

class ParseMode(Enum):
    """解析模式"""
    STRICT = "strict"
    LENIENT = "lenient"
    VALIDATE_ONLY = "validate_only"

@dataclass
class WriteOptions:
    """写入选项"""
    backup: bool = True
    format_output: bool = True
    encoding: str = "utf-8"
    version: XMLVersion = XMLVersion.V1_0

__version__ = "2.0.0"
