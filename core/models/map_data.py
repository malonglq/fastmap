#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map数据模型定义
==liuq debug== FastMapV2核心数据模型

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 17:40:00 +08:00; Reason: P1-LD-002 设计核心数据模型; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: Map配置数据的标准化模型定义
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional, Union
from enum import Enum
from decimal import Decimal
from utils.number_formatter import format_decimal_precise

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class MapType(Enum):
    """Map类型枚举"""
    ENHANCE = "enhance"  # 强拉类型
    REDUCE = "reduce"    # 减小权重类型


class SceneType(Enum):
    """场景类型枚举"""
    INDOOR = "indoor"    # 室内场景
    OUTDOOR = "outdoor"  # 室外场景
    NIGHT = "night"      # 夜景场景


class XMLFieldNodeType(Enum):
    """XML字段节点类型枚举"""
    OFFSET = "offset"    # offset节点中的字段
    RANGE = "range"      # range节点中的字段


class XMLFieldDataType(Enum):
    """XML字段数据类型枚举"""
    DOUBLE = "double"    # 双精度浮点数
    UINT = "uint"        # 无符号整数
    INT = "int"          # 有符号整数


@dataclass
class MapPoint:
    """
    Map点数据模型

    表示XML中的单个offset_map配置项
    支持单点坐标和多边形坐标两种模式
    """
    alias_name: str                    # 别名，如"Indoor_BV_4000_IR_1000"
    x: float                          # X坐标（单点模式）或多边形重心X坐标
    y: float                          # Y坐标（单点模式）或多边形重心Y坐标
    offset_x: float                   # 严格来自offset/x的坐标值
    offset_y: float                   # 严格来自offset/y的坐标值
    weight: float                     # 权重值
    bv_range: Tuple[float, float]     # BV范围 (min, max)
    ir_range: Tuple[float, float]     # IR范围 (min, max)
    cct_range: Tuple[float, float]    # CCT范围 (min, max)

    # 有默认值的字段必须在最后
    trans_step: int = 0               # TransStep值，来自offset_map[1]/TransStep
    ctemp_range: Tuple[float, float] = (0.0, 0.0)  # Ctemp范围 (min, max)，独立于colorCCT
    e_ratio_range: Tuple[float, float] = (0.0, 0.0)  # ERatio范围 (min, max)
    ac_range: Tuple[float, float] = (0.0, 0.0)      # AC范围 (min, max)
    count_range: Tuple[float, float] = (0.0, 0.0)   # COUNT范围 (min, max)
    color_cct_range: Tuple[float, float] = (0.0, 0.0)  # ColorCCT范围 (min, max)
    diff_ctemp_range: Tuple[float, float] = (0.0, 0.0)  # diffCtemp范围 (min, max)
    face_ctemp_range: Tuple[float, float] = (0.0, 0.0)  # FaceCtemp范围 (min, max)
    detect_flag: bool = True          # 检测标志
    map_type: MapType = MapType.ENHANCE  # Map类型
    scene_type: SceneType = SceneType.INDOOR  # 场景类型

    # 多边形坐标支持
    polygon_vertices: List[Tuple[float, float]] = field(default_factory=list)  # 多边形顶点坐标列表
    is_polygon: bool = False          # 是否为多边形模式

    # 详细范围参数 - BV相关
    tran_bv_min: float = 0.0         # tranBv_min
    tran_bv_max: float = 0.0         # tranBv_max

    # 详细范围参数 - 色温相关
    tran_ctemp_min: float = 0.0      # tranCtemp_min
    tran_ctemp_max: float = 0.0      # tranCtemp_max

    # 详细范围参数 - IR相关
    tran_ir_min: float = 0.0         # tranir_min
    tran_ir_max: float = 0.0         # tranir_max

    # 详细范围参数 - AC相关
    tran_ac_min: float = 0.0         # tranac_min
    tran_ac_max: float = 0.0         # tranac_max

    # 详细范围参数 - Count相关
    tran_count_min: float = 0.0      # tranCount_min
    tran_count_max: float = 0.0      # tranCount_max

    # 详细范围参数 - ColorCCT相关
    tran_color_cct_min: float = 0.0  # tranColorCCT_min
    tran_color_cct_max: float = 0.0  # tranColorCCT_max

    # 详细范围参数 - diffCtemp相关
    tran_diff_ctemp_min: float = 0.0  # tranDiffCtemp_min
    tran_diff_ctemp_max: float = 0.0  # tranDiffCtemp_max

    # 详细范围参数 - FaceCtemp相关
    tran_face_ctemp_min: float = 0.0  # tranFaceCtemp_min
    tran_face_ctemp_max: float = 0.0  # tranFaceCtemp_max

    # 检测标志
    detect_map_flag: bool = True     # DetectMapFlag

    # 扩展字段，用于存储其他XML属性
    extra_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理，自动推断场景类型"""
        if not hasattr(self, '_scene_inferred'):
            self.scene_type = self._infer_scene_type()
            self._scene_inferred = True
    

    def _infer_scene_type(self) -> SceneType:
        """
        根据别名和参数范围推断场景类型

        Returns:
            推断的场景类型
        """
        alias_lower = self.alias_name.lower()

        # 根据别名关键词判断
        if 'indoor' in alias_lower:
            return SceneType.INDOOR
        elif 'outdoor' in alias_lower:
            return SceneType.OUTDOOR
        elif 'night' in alias_lower:
            return SceneType.NIGHT

        # 根据BV值范围判断（夜景通常BV值较低）
        bv_min, bv_max = self.bv_range
        if bv_max < 2000:  # 经验阈值
            return SceneType.NIGHT
        elif bv_min > 5000:  # 经验阈值
            return SceneType.OUTDOOR
        else:
            return SceneType.INDOOR
    
    def get_coordinate_tuple(self) -> Tuple[float, float]:
        """获取坐标元组"""
        return (self.x, self.y)
    
    def is_in_range(self, bv: float, ir: float, cct: float) -> bool:
        """
        检查给定参数是否在此Map点的范围内

        Args:
            bv: BV值
            ir: IR值
            cct: CCT值

        Returns:
            是否在范围内
        """
        bv_min, bv_max = self.bv_range
        ir_min, ir_max = self.ir_range
        cct_min, cct_max = self.cct_range

        return (bv_min <= bv <= bv_max and
                ir_min <= ir <= ir_max and
                cct_min <= cct <= cct_max)

    def get_polygon_vertex_count(self) -> int:
        """
        获取多边形顶点数量

        Returns:
            顶点数量，如果不是多边形则返回0
        """
        return len(self.polygon_vertices) if self.is_polygon else 0

    def calculate_polygon_centroid(self) -> Tuple[float, float]:
        """
        计算多边形重心坐标

        Returns:
            重心坐标(x, y)，如果不是多边形则返回(self.x, self.y)
        """
        if not self.is_polygon or not self.polygon_vertices:
            return (self.x, self.y)

        x_sum = sum(vertex[0] for vertex in self.polygon_vertices)
        y_sum = sum(vertex[1] for vertex in self.polygon_vertices)
        count = len(self.polygon_vertices)

        return (x_sum / count, y_sum / count)

    def get_coordinate_mode(self) -> str:
        """
        获取坐标模式描述

        Returns:
            坐标模式字符串
        """
        if self.is_polygon:
            return f"多边形({len(self.polygon_vertices)}个顶点)"
        else:
            return "单点坐标"

    def get_detailed_range_info(self) -> Dict[str, Dict[str, float]]:
        """
        获取详细的范围参数信息

        Returns:
            包含所有范围参数的字典
        """
        return {
            "BV": {
                "tran_min": self.tran_bv_min,
                "min": self.bv_range[0],
                "max": self.bv_range[1],
                "tran_max": self.tran_bv_max
            },
            "ERatio": {
                "tran_min": 0.0,  # ERatio没有tran值，使用0
                "min": self.e_ratio_range[0],
                "max": self.e_ratio_range[1],
                "tran_max": 0.0   # ERatio没有tran值，使用0
            },
            "色温": {
                "tran_min": self.tran_ctemp_min,
                "min": self.cct_range[0],
                "max": self.cct_range[1],
                "tran_max": self.tran_ctemp_max
            },
            "IR": {
                "tran_min": self.tran_ir_min,
                "min": self.ir_range[0],
                "max": self.ir_range[1],
                "tran_max": self.tran_ir_max
            },
            "AC": {
                "tran_min": self.tran_ac_min,
                "min": self.ac_range[0],
                "max": self.ac_range[1],
                "tran_max": self.tran_ac_max
            },
            "Count": {
                "tran_min": self.tran_count_min,
                "min": self.count_range[0],
                "max": self.count_range[1],
                "tran_max": self.tran_count_max
            },
            "ColorCCT": {
                "tran_min": self.tran_color_cct_min,
                "min": self.color_cct_range[0],
                "max": self.color_cct_range[1],
                "tran_max": self.tran_color_cct_max
            },
            "diffCtemp": {
                "tran_min": self.tran_diff_ctemp_min,
                "min": self.diff_ctemp_range[0],
                "max": self.diff_ctemp_range[1],
                "tran_max": self.tran_diff_ctemp_max
            },
            "FaceCtemp": {
                "tran_min": self.tran_face_ctemp_min,
                "min": self.face_ctemp_range[0],
                "max": self.face_ctemp_range[1],
                "tran_max": self.tran_face_ctemp_max
            }
        }


# XML字段配置系统
# {{CHENGQI:
# Action: Added; Timestamp: 2025-08-01 10:30:00 +08:00; Reason: 创建统一的XML字段元数据配置系统; Principle_Applied: DRY原则和配置驱动设计;
# }}

@dataclass
class XMLFieldConfig:
    """XML字段配置类"""
    field_name: str                    # 字段名称（如bv_min）
    xml_path: Tuple[str, ...]         # XML路径元组（如('bv', 'min')）
    node_type: XMLFieldNodeType       # 节点类型（offset或range）
    data_type: XMLFieldDataType       # 数据类型（double, uint, int）
    is_tran_field: bool = False       # 是否为tran字段
    default_value: Any = 0            # 默认值


# 统一的XML字段配置字典
XML_FIELD_CONFIG: Dict[str, XMLFieldConfig] = {
    # Offset节点字段
    'offset_x': XMLFieldConfig(
        field_name='offset_x',
        xml_path=('x',),
        node_type=XMLFieldNodeType.OFFSET,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=0.0
    ),
    'offset_y': XMLFieldConfig(
        field_name='offset_y',
        xml_path=('y',),
        node_type=XMLFieldNodeType.OFFSET,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=0.0
    ),

    # Range节点字段 - BV字段组
    'bv_min': XMLFieldConfig(
        field_name='bv_min',
        xml_path=('bv', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=0.0
    ),
    'bv_max': XMLFieldConfig(
        field_name='bv_max',
        xml_path=('bv', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=100.0
    ),
    'tran_bv_min': XMLFieldConfig(
        field_name='tran_bv_min',
        xml_path=('tranBv', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        is_tran_field=True,
        default_value=0.0
    ),
    'tran_bv_max': XMLFieldConfig(
        field_name='tran_bv_max',
        xml_path=('tranBv', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        is_tran_field=True,
        default_value=100.0
    ),

    # Range节点字段 - 色温字段组
    'ctemp_min': XMLFieldConfig(
        field_name='ctemp_min',
        xml_path=('ctemp', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=1500
    ),
    'ctemp_max': XMLFieldConfig(
        field_name='ctemp_max',
        xml_path=('ctemp', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=12000
    ),
    'tran_ctemp_min': XMLFieldConfig(
        field_name='tran_ctemp_min',
        xml_path=('tranCtemp', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=1500
    ),
    'tran_ctemp_max': XMLFieldConfig(
        field_name='tran_ctemp_max',
        xml_path=('tranCtemp', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=12000
    ),

    # Range节点字段 - 红外字段组
    'ir_min': XMLFieldConfig(
        field_name='ir_min',
        xml_path=('ir', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=0.0
    ),
    'ir_max': XMLFieldConfig(
        field_name='ir_max',
        xml_path=('ir', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=999.0
    ),
    'tran_ir_min': XMLFieldConfig(
        field_name='tran_ir_min',
        xml_path=('tranir', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        is_tran_field=True,
        default_value=0.0
    ),
    'tran_ir_max': XMLFieldConfig(
        field_name='tran_ir_max',
        xml_path=('tranir', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        is_tran_field=True,
        default_value=999.0
    ),

    # Range节点字段 - AC字段组
    'ac_min': XMLFieldConfig(
        field_name='ac_min',
        xml_path=('ac', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=0.0
    ),
    'ac_max': XMLFieldConfig(
        field_name='ac_max',
        xml_path=('ac', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=999.0
    ),
    'tran_ac_min': XMLFieldConfig(
        field_name='tran_ac_min',
        xml_path=('tranac', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        is_tran_field=True,
        default_value=0.0
    ),
    'tran_ac_max': XMLFieldConfig(
        field_name='tran_ac_max',
        xml_path=('tranac', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        is_tran_field=True,
        default_value=999.0
    ),

    # Range节点字段 - 计数字段组
    'count_min': XMLFieldConfig(
        field_name='count_min',
        xml_path=('count', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=0
    ),
    'count_max': XMLFieldConfig(
        field_name='count_max',
        xml_path=('count', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=3072
    ),
    'tran_count_min': XMLFieldConfig(
        field_name='tran_count_min',
        xml_path=('tranCount', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=0
    ),
    'tran_count_max': XMLFieldConfig(
        field_name='tran_count_max',
        xml_path=('tranCount', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=3072
    ),

    # Range节点字段 - 色彩CCT字段组
    'color_cct_min': XMLFieldConfig(
        field_name='color_cct_min',
        xml_path=('colorCCT', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=1
    ),
    'color_cct_max': XMLFieldConfig(
        field_name='color_cct_max',
        xml_path=('colorCCT', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=12000
    ),
    'tran_color_cct_min': XMLFieldConfig(
        field_name='tran_color_cct_min',
        xml_path=('tranColorCCT', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=0
    ),
    'tran_color_cct_max': XMLFieldConfig(
        field_name='tran_color_cct_max',
        xml_path=('tranColorCCT', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=12500
    ),

    # Range节点字段 - 差分色温字段组
    'diff_ctemp_min': XMLFieldConfig(
        field_name='diff_ctemp_min',
        xml_path=('diffCtemp', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=0
    ),
    'diff_ctemp_max': XMLFieldConfig(
        field_name='diff_ctemp_max',
        xml_path=('diffCtemp', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=9000
    ),
    'tran_diff_ctemp_min': XMLFieldConfig(
        field_name='tran_diff_ctemp_min',
        xml_path=('tranDiffCtemp', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=0
    ),
    'tran_diff_ctemp_max': XMLFieldConfig(
        field_name='tran_diff_ctemp_max',
        xml_path=('tranDiffCtemp', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=13500
    ),

    # Range节点字段 - 面部色温字段组
    'face_ctemp_min': XMLFieldConfig(
        field_name='face_ctemp_min',
        xml_path=('faceCtemp', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=0
    ),
    'face_ctemp_max': XMLFieldConfig(
        field_name='face_ctemp_max',
        xml_path=('faceCtemp', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        default_value=9000
    ),
    'tran_face_ctemp_min': XMLFieldConfig(
        field_name='tran_face_ctemp_min',
        xml_path=('tranFaceCtemp', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=0
    ),
    'tran_face_ctemp_max': XMLFieldConfig(
        field_name='tran_face_ctemp_max',
        xml_path=('tranFaceCtemp', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.UINT,
        is_tran_field=True,
        default_value=13500
    ),

    # Range节点字段 - ML字段
    'ml': XMLFieldConfig(
        field_name='ml',
        xml_path=('ml',),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.INT,
        default_value=0
    ),

    # {{CHENGQI:
    # Action: Added; Timestamp: 2025-08-02 16:30:00 +08:00; Reason: 添加缺失的基础字段配置以修复GUI编辑后XML文件未更新的问题; Principle_Applied: 配置驱动设计和数据一致性;
    # }}

    # 基础字段 - Weight字段
    'weight': XMLFieldConfig(
        field_name='weight',
        xml_path=('weight',),
        node_type=XMLFieldNodeType.OFFSET,  # weight字段位于offset节点中
        data_type=XMLFieldDataType.DOUBLE,
        default_value=1.0
    ),

    # 基础字段 - TransStep字段
    'trans_step': XMLFieldConfig(
        field_name='trans_step',
        xml_path=('TransStep',),
        node_type=XMLFieldNodeType.OFFSET,  # TransStep字段位于offset节点中
        data_type=XMLFieldDataType.INT,
        default_value=0
    ),

    # Range节点字段 - ERatio字段组
    'e_ratio_min': XMLFieldConfig(
        field_name='e_ratio_min',
        xml_path=('e_ratio', 'min'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=0.0
    ),
    'e_ratio_max': XMLFieldConfig(
        field_name='e_ratio_max',
        xml_path=('e_ratio', 'max'),
        node_type=XMLFieldNodeType.RANGE,
        data_type=XMLFieldDataType.DOUBLE,
        default_value=100.0
    ),
}


def get_field_xml_path(field_name: str) -> Tuple[str, ...]:
    """
    根据字段名获取XML路径元组

    Args:
        field_name: 字段名称

    Returns:
        XML路径元组
    """
    config = XML_FIELD_CONFIG.get(field_name)
    if config:
        return config.xml_path
    return ()


def get_field_node_type(field_name: str) -> XMLFieldNodeType:
    """
    确定字段所在的节点类型

    Args:
        field_name: 字段名称

    Returns:
        节点类型
    """
    config = XML_FIELD_CONFIG.get(field_name)
    if config:
        return config.node_type
    return XMLFieldNodeType.RANGE  # 默认为range节点


def get_field_data_type(field_name: str) -> XMLFieldDataType:
    """
    获取字段的数据类型

    Args:
        field_name: 字段名称

    Returns:
        数据类型
    """
    config = XML_FIELD_CONFIG.get(field_name)
    if config:
        return config.data_type
    return XMLFieldDataType.DOUBLE  # 默认为double类型


def is_tran_field(field_name: str) -> bool:
    """
    判断是否为tran字段

    Args:
        field_name: 字段名称

    Returns:
        是否为tran字段
    """
    config = XML_FIELD_CONFIG.get(field_name)
    if config:
        return config.is_tran_field
    return False


def parse_field_value(value: str, field_name: str) -> Any:
    """
    根据字段类型解析字段值

    Args:
        value: 字符串值
        field_name: 字段名称

    Returns:
        解析后的值
    """
    try:
        data_type = get_field_data_type(field_name)

        if data_type == XMLFieldDataType.DOUBLE:
            return float(value)
        elif data_type == XMLFieldDataType.UINT:
            return int(float(value))  # 先转float再转int，处理"1.0"这种情况
        elif data_type == XMLFieldDataType.INT:
            return int(float(value))
        else:
            return value
    except (ValueError, TypeError):
        config = XML_FIELD_CONFIG.get(field_name)
        return config.default_value if config else 0


def format_field_value(value: Any, field_name: str) -> str:
    """
    根据字段类型格式化字段值 - 基于成熟的decimal.js算法实现

    采用业界验证的精度处理方案：
    1. 优先保持原始字符串精度（避免浮点转换损失）
    2. 使用Python Decimal库进行精确计算（类似decimal.js）
    3. 智能处理整数和小数的显示格式
    4. 完全避免浮点精度问题

    Args:
        value: 字段值
        field_name: 字段名称

    Returns:
        格式化后的字符串
    """
    try:
        if value is None:
            config = XML_FIELD_CONFIG.get(field_name)
            value = config.default_value if config else 0

        data_type = get_field_data_type(field_name)

        if data_type == XMLFieldDataType.DOUBLE:
            # {{CHENGQI:
            # Action: Modified; Timestamp: 2025-08-02 11:00:00 +08:00; Reason: 重构使用统一的格式化核心算法，消除代码重复; Principle_Applied: DRY原则;
            # }}
            result = format_decimal_precise(value)
            # 关键精度日志

            return result

        elif data_type in [XMLFieldDataType.UINT, XMLFieldDataType.INT]:
            result = str(int(float(value)))

            return result
        else:
            result = str(value)

            return result
    except (ValueError, TypeError):
        config = XML_FIELD_CONFIG.get(field_name)
        result = str(config.default_value if config else 0)

        return result


# {{CHENGQI:
# Action: Removed; Timestamp: 2025-08-02 11:00:00 +08:00; Reason: 删除重复的内部格式化函数，使用统一的工具模块; Principle_Applied: DRY原则;
# }}
# _format_decimal_with_precision, _is_valid_number_string 和 _format_decimal_result 函数已移动到 utils/number_formatter.py


def set_map_point_field_value(map_point: 'MapPoint', field_name: str, value: Any) -> bool:
    """
    设置MapPoint对象的字段值

    Args:
        map_point: MapPoint对象
        field_name: 字段名称
        value: 字段值

    Returns:
        bool: 是否设置成功
    """
    try:
        # 直接属性设置
        if hasattr(map_point, field_name):
            setattr(map_point, field_name, value)
            return True

        # 特殊字段映射
        if field_name == 'bv_min':
            if not map_point.bv_range:
                map_point.bv_range = (value, 100.0)
            else:
                map_point.bv_range = (value, map_point.bv_range[1])
            return True
        elif field_name == 'bv_max':
            if not map_point.bv_range:
                map_point.bv_range = (0.0, value)
            else:
                map_point.bv_range = (map_point.bv_range[0], value)
            return True
        elif field_name == 'ir_min':
            if not map_point.ir_range:
                map_point.ir_range = (value, 999.0)
            else:
                map_point.ir_range = (value, map_point.ir_range[1])
            return True
        elif field_name == 'ir_max':
            if not map_point.ir_range:
                map_point.ir_range = (0.0, value)
            else:
                map_point.ir_range = (map_point.ir_range[0], value)
            return True
        elif field_name == 'ctemp_min':
            if not map_point.ctemp_range:
                map_point.ctemp_range = (value, 12000)
            else:
                map_point.ctemp_range = (value, map_point.ctemp_range[1])
            return True
        elif field_name == 'ctemp_max':
            if not map_point.ctemp_range:
                map_point.ctemp_range = (1500, value)
            else:
                map_point.ctemp_range = (map_point.ctemp_range[0], value)
            return True
        # {{CHENGQI:
        # Action: Added; Timestamp: 2025-08-02 16:50:00 +08:00; Reason: 添加e_ratio字段设置逻辑以修复GUI编辑后XML文件未更新的问题; Principle_Applied: 数据一致性和完整性;
        # }}
        elif field_name == 'e_ratio_min':
            if not map_point.e_ratio_range:
                map_point.e_ratio_range = (value, 100.0)
            else:
                map_point.e_ratio_range = (value, map_point.e_ratio_range[1])
            return True
        elif field_name == 'e_ratio_max':
            if not map_point.e_ratio_range:
                map_point.e_ratio_range = (0.0, value)
            else:
                map_point.e_ratio_range = (map_point.e_ratio_range[0], value)
            return True
        elif field_name == 'ml':
            # ml字段的GUI输入值到内部值的反向转换
            #
            # {{CHENGQI:
            # Action: Modified; Timestamp: 2025-08-01 16:10:00 +08:00; Reason: 在配置驱动函数中添加ml字段反向转换逻辑; Principle_Applied: 显示存储分离原则;
            # }}
            #
            if not hasattr(map_point, 'extra_attributes'):
                map_point.extra_attributes = {}

            # 将GUI输入值转换为内部存储值
            input_value = float(value)

            # 反向转换：GUI友好值 → 内部值
            if input_value == 2:
                internal_value = 65471
            elif input_value == 3:
                internal_value = 65535
            else:
                # 其他值直接使用
                internal_value = input_value

            map_point.extra_attributes['ml'] = internal_value

            return True

        # Tran字段设置
        elif field_name.startswith('tran_'):
            setattr(map_point, field_name, value)
            return True

        return False

    except Exception as e:
        logger.error(f"==liuq debug== 设置字段值失败: {field_name} = {value}, {e}")
        return False


def create_field_processor():
    """
    创建统一的字段处理器

    Returns:
        字段处理器字典，包含解析和格式化函数
    """
    return {
        'parse': parse_field_value,
        'format': format_field_value,
        'get_path': get_field_xml_path,
        'get_node_type': get_field_node_type,
        'get_data_type': get_field_data_type,
        'is_tran': is_tran_field,
        'config': XML_FIELD_CONFIG
    }


def get_fields_by_node_type(node_type: XMLFieldNodeType) -> List[str]:
    """
    获取指定节点类型的所有字段名

    Args:
        node_type: 节点类型

    Returns:
        字段名列表
    """
    return [
        field_name for field_name, config in XML_FIELD_CONFIG.items()
        if config.node_type == node_type
    ]


def get_range_field_groups() -> Dict[str, List[str]]:
    """
    获取range节点字段的分组

    Returns:
        字段分组字典
    """
    return {
        'bv_fields': ['bv_min', 'bv_max', 'tran_bv_min', 'tran_bv_max'],
        'ctemp_fields': ['ctemp_min', 'ctemp_max', 'tran_ctemp_min', 'tran_ctemp_max'],
        'ir_fields': ['ir_min', 'ir_max', 'tran_ir_min', 'tran_ir_max'],
        'ac_fields': ['ac_min', 'ac_max', 'tran_ac_min', 'tran_ac_max'],
        'count_fields': ['count_min', 'count_max', 'tran_count_min', 'tran_count_max'],
        'color_cct_fields': ['color_cct_min', 'color_cct_max', 'tran_color_cct_min', 'tran_color_cct_max'],
        'diff_ctemp_fields': ['diff_ctemp_min', 'diff_ctemp_max', 'tran_diff_ctemp_min', 'tran_diff_ctemp_max'],
        'face_ctemp_fields': ['face_ctemp_min', 'face_ctemp_max', 'tran_face_ctemp_min', 'tran_face_ctemp_max'],
        'ml_fields': ['ml']
    }


def get_map_point_field_value(map_point: 'MapPoint', field_name: str) -> Any:
    """
    从MapPoint对象获取字段值

    Args:
        map_point: MapPoint对象
        field_name: 字段名称

    Returns:
        字段值
    """
    # 直接属性访问
    if hasattr(map_point, field_name):
        return getattr(map_point, field_name)

    # 特殊字段映射
    field_mapping = {
        'bv_min': lambda obj: obj.bv_range[0] if obj.bv_range else 0.0,
        'bv_max': lambda obj: obj.bv_range[1] if obj.bv_range else 100.0,
        'ir_min': lambda obj: obj.ir_range[0] if obj.ir_range else 0.0,
        'ir_max': lambda obj: obj.ir_range[1] if obj.ir_range else 999.0,
        'ctemp_min': lambda obj: obj.ctemp_range[0] if obj.ctemp_range else 1500,
        'ctemp_max': lambda obj: obj.ctemp_range[1] if obj.ctemp_range else 12000,
        'ac_min': lambda obj: obj.ac_range[0] if obj.ac_range else 0.0,
        'ac_max': lambda obj: obj.ac_range[1] if obj.ac_range else 999.0,
        'count_min': lambda obj: obj.count_range[0] if obj.count_range else 0,
        'count_max': lambda obj: obj.count_range[1] if obj.count_range else 3072,
        'color_cct_min': lambda obj: obj.color_cct_range[0] if obj.color_cct_range else 1,
        'color_cct_max': lambda obj: obj.color_cct_range[1] if obj.color_cct_range else 12000,
        'diff_ctemp_min': lambda obj: obj.diff_ctemp_range[0] if obj.diff_ctemp_range else 0,
        'diff_ctemp_max': lambda obj: obj.diff_ctemp_range[1] if obj.diff_ctemp_range else 9000,
        'face_ctemp_min': lambda obj: obj.face_ctemp_range[0] if obj.face_ctemp_range else 0,
        'face_ctemp_max': lambda obj: obj.face_ctemp_range[1] if obj.face_ctemp_range else 9000,
        # {{CHENGQI:
        # Action: Added; Timestamp: 2025-08-02 16:35:00 +08:00; Reason: 添加e_ratio字段映射以修复GUI编辑后XML文件未更新的问题; Principle_Applied: 数据一致性和完整性;
        # }}
        'e_ratio_min': lambda obj: obj.e_ratio_range[0] if obj.e_ratio_range else 0.0,
        'e_ratio_max': lambda obj: obj.e_ratio_range[1] if obj.e_ratio_range else 100.0,
        'ml': lambda obj: obj.extra_attributes.get('ml', 0)
    }

    if field_name in field_mapping:
        try:
            return field_mapping[field_name](map_point)
        except (AttributeError, IndexError, TypeError):
            pass

    # 返回默认值
    config = XML_FIELD_CONFIG.get(field_name)
    return config.default_value if config else 0


@dataclass
class BaseBoundary:
    """基础边界数据模型"""
    rpg: float  # RpG参考值
    bpg: float  # BpG参考值


@dataclass
class MapConfiguration:
    """
    Map配置数据模型
    
    表示完整的XML配置文件内容
    """
    device_type: str                           # 设备类型 'reference' | 'debug'
    base_boundary: BaseBoundary               # 基础边界数据
    map_points: List[MapPoint]                # Map点列表（不包含base_boundary0）
    base_boundary_point: Optional[MapPoint] = None  # base_boundary0作为MapPoint（单独存储）
    reference_points: List[Tuple[float, float]] = field(default_factory=list)  # 参考点坐标
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def __post_init__(self):
        """初始化后处理"""
        # 保持Map点的原始XML顺序，不进行权重排序
        # 这样可以确保Map点与XML节点的正确映射关系
        pass
    
    def get_map_points_by_scene(self, scene_type: SceneType) -> List[MapPoint]:
        """
        根据场景类型获取Map点
        
        Args:
            scene_type: 场景类型
            
        Returns:
            指定场景的Map点列表
        """
        return [mp for mp in self.map_points if mp.scene_type == scene_type]
    
    def get_map_points_by_type(self, map_type: MapType) -> List[MapPoint]:
        """
        根据Map类型获取Map点
        
        Args:
            map_type: Map类型
            
        Returns:
            指定类型的Map点列表
        """
        return [mp for mp in self.map_points if mp.map_type == map_type]
    
    def get_coordinate_bounds(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        获取所有Map点的坐标边界
        
        Returns:
            ((x_min, x_max), (y_min, y_max))
        """
        if not self.map_points:
            return ((0, 0), (0, 0))
        
        x_coords = [mp.x for mp in self.map_points]
        y_coords = [mp.y for mp in self.map_points]
        
        return ((min(x_coords), max(x_coords)), 
                (min(y_coords), max(y_coords)))
    
    def get_weight_statistics(self) -> Dict[str, float]:
        """
        获取权重统计信息
        
        Returns:
            权重统计字典
        """
        if not self.map_points:
            return {}
        
        weights = [mp.weight for mp in self.map_points]
        return {
            'min': min(weights),
            'max': max(weights),
            'mean': sum(weights) / len(weights),
            'count': len(weights)
        }
    
    def find_map_point_by_alias(self, alias_name: str) -> Optional[MapPoint]:
        """
        根据别名查找Map点
        
        Args:
            alias_name: 别名
            
        Returns:
            找到的Map点，如果不存在则返回None
        """
        for mp in self.map_points:
            if mp.alias_name == alias_name:
                return mp
        return None


@dataclass
class AnalysisResult:
    """
    分析结果数据模型
    
    存储Map分析的结果数据
    """
    configuration: MapConfiguration           # 原始配置
    scene_statistics: Dict[str, Dict[str, Any]]  # 场景统计
    coordinate_analysis: Dict[str, Any]       # 坐标分析
    weight_analysis: Dict[str, Any]          # 权重分析
    reference_point_analysis: Dict[str, Any] # 参考点分析
    
    # 可视化数据
    scatter_plot_data: Dict[str, Any] = field(default_factory=dict)
    heatmap_data: Dict[str, Any] = field(default_factory=dict)
    range_chart_data: Dict[str, Any] = field(default_factory=dict)
    
    # 报告元数据
    analysis_timestamp: str = ""
    analysis_duration: float = 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取分析结果摘要
        
        Returns:
            分析摘要字典
        """
        return {
            'total_map_points': len(self.configuration.map_points),
            'scene_distribution': {
                scene.value: len(self.configuration.get_map_points_by_scene(scene))
                for scene in SceneType
            },
            'weight_stats': self.configuration.get_weight_statistics(),
            'coordinate_bounds': self.configuration.get_coordinate_bounds(),
            'analysis_time': self.analysis_timestamp,
            'processing_duration': f"{self.analysis_duration:.2f}s"
        }
