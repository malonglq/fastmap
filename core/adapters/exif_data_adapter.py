#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF数据适配器
==liuq debug== FastMapV2 EXIF数据适配器

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 15:15:00 +08:00; Reason: 阶段2-创建EXIF数据适配器; Principle_Applied: 适配器模式;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 处理EXIF CSV数据的适配和标准化
"""

import logging
import pandas as pd
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ExifDataAdapter:
    """
    EXIF数据适配器
    
    负责处理EXIF CSV数据的读取、验证、标准化和字段映射
    """
    
    def __init__(self, field_mapping_config: Optional[str] = None):
        """
        初始化EXIF数据适配器
        
        Args:
            field_mapping_config: 字段映射配置文件路径
        """
        self.field_mapping_config = field_mapping_config or "data/configs/exif_field_mapping.json"
        self.field_mappings = {}
        self.core_fields = []
        self.display_names = {}
        
        # 加载字段映射配置
        self._load_field_mapping_config()
        
        logger.info("==liuq debug== EXIF数据适配器初始化完成")
    
    def _load_field_mapping_config(self):
        """加载字段映射配置"""
        try:
            config_path = Path(self.field_mapping_config)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.field_mappings = config.get('field_mappings', {})
                    self.core_fields = config.get('core_fields', [])
                    self.display_names = config.get('display_names', {})
                logger.info(f"==liuq debug== 加载字段映射配置: {len(self.field_mappings)}个映射")
            else:
                # 创建默认配置
                self._create_default_config()
                logger.info("==liuq debug== 创建默认字段映射配置")
        except Exception as e:
            logger.warning(f"==liuq debug== 加载字段映射配置失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认字段映射配置"""
        default_config = {
            "field_mappings": {
                "meta_data_lastFrame_bv": "BV_Last_Frame",
                "meta_data_currentFrame_bv": "BV_Current_Frame",
                "color_sensor_irRatio": "IR_Ratio",
                "color_sensor_rGain": "R_Gain",
                "color_sensor_gGain": "G_Gain", 
                "color_sensor_bGain": "B_Gain",
                "color_sensor_cct": "CCT",
                "color_sensor_lux": "Lux"
            },
            "core_fields": [
                "BV_Last_Frame", "BV_Current_Frame", "IR_Ratio",
                "R_Gain", "G_Gain", "B_Gain", "CCT", "Lux"
            ],
            "display_names": {
                "BV_Last_Frame": "BV值(上一帧)",
                "BV_Current_Frame": "BV值(当前帧)",
                "IR_Ratio": "红外比值",
                "R_Gain": "红色增益",
                "G_Gain": "绿色增益",
                "B_Gain": "蓝色增益",
                "CCT": "色温",
                "Lux": "照度"
            }
        }
        
        # 保存默认配置
        try:
            config_path = Path(self.field_mapping_config)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"==liuq debug== 保存默认配置失败: {e}")
        
        self.field_mappings = default_config['field_mappings']
        self.core_fields = default_config['core_fields']
        self.display_names = default_config['display_names']
    
    def read_exif_csv(self, csv_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
        """
        读取EXIF CSV文件

        Args:
            csv_path: CSV文件路径
            encoding: 文件编码

        Returns:
            pandas DataFrame
        """
        try:
            logger.info(f"==liuq debug== 开始读取EXIF CSV文件: {csv_path}")

            # 验证文件存在
            if not Path(csv_path).exists():
                raise FileNotFoundError(f"文件不存在: {csv_path}")

            # 检测正确的header行
            header_row = self._detect_header_row(csv_path, encoding)

            # 尝试不同的编码
            encodings_to_try = [encoding, 'utf-8-sig', 'gbk', 'gb2312']
            df = None

            for enc in encodings_to_try:
                try:
                    df = pd.read_csv(
                        csv_path,
                        encoding=enc,
                        header=header_row,
                        low_memory=False,
                        na_values=['', 'NULL', 'null', 'NaN', 'nan'],
                        keep_default_na=True
                    )
                    logger.info(f"==liuq debug== 使用编码 {enc} 读取成功")
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise Exception(f"无法使用任何编码读取文件: {csv_path}")

            # 清理列名
            df.columns = df.columns.str.strip()

            # 验证关键列存在
            if 'Image_name' not in df.columns:
                # 尝试查找类似的列名
                image_name_candidates = [col for col in df.columns if 'image' in col.lower() and 'name' in col.lower()]
                if image_name_candidates:
                    logger.warning(f"==liuq debug== 未找到'Image_name'列，使用候选列: {image_name_candidates[0]}")
                    df = df.rename(columns={image_name_candidates[0]: 'Image_name'})
                else:
                    raise ValueError("CSV文件中缺少关键的'Image_name'列")

            logger.info(f"==liuq debug== CSV文件读取成功，行数: {len(df)}, 列数: {len(df.columns)}")
            logger.info(f"==liuq debug== 列名: {list(df.columns)}")
            return df

        except Exception as e:
            logger.error(f"==liuq debug== 读取EXIF CSV文件失败: {e}")
            raise

    def _detect_header_row(self, csv_path: str, encoding: str) -> int:
        """
        检测CSV文件中真正的header行位置

        Args:
            csv_path: CSV文件路径
            encoding: 文件编码

        Returns:
            header行的索引（0-based）
        """
        try:
            # 读取前几行来分析
            with open(csv_path, 'r', encoding=encoding) as f:
                lines = [f.readline().strip() for _ in range(5)]

            # 查找包含"Image_name"的行
            for i, line in enumerate(lines):
                if line and 'Image_name' in line:
                    logger.info(f"==liuq debug== 检测到header行在第{i+1}行: {line[:100]}...")
                    return i

            # 如果没找到Image_name，查找最可能的header行
            for i, line in enumerate(lines):
                if line and len(line.split(',')) > 5:
                    fields = line.split(',')
                    # 检查是否包含常见的列名模式
                    if any(field.strip() for field in fields):
                        logger.info(f"==liuq debug== 推测header行在第{i+1}行")
                        return i

            logger.warning(f"==liuq debug== 未能检测到明确的header行，使用默认第1行")
            return 0

        except Exception as e:
            logger.error(f"==liuq debug== header行检测失败: {e}")
            return 0

    def validate_exif_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证EXIF数据格式
        
        Args:
            df: pandas DataFrame
            
        Returns:
            验证结果字典
        """
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'info': {
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'required_fields_found': [],
                    'mapped_fields_found': [],
                    'numeric_fields': []
                }
            }
            
            # 检查必需字段（大小写不敏感）
            required_fields = ['timestamp', 'image_name']
            for field in required_fields:
                found = False
                for col in df.columns:
                    if col.lower() == field.lower():
                        validation_result['info']['required_fields_found'].append(col)
                        found = True
                        break

                if not found:
                    validation_result['errors'].append(f"缺少必需字段: {field}")
                    validation_result['is_valid'] = False
            
            # 检查可映射字段
            for original_field, mapped_field in self.field_mappings.items():
                if original_field in df.columns:
                    validation_result['info']['mapped_fields_found'].append({
                        'original': original_field,
                        'mapped': mapped_field
                    })
            
            # 检查数值字段
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    validation_result['info']['numeric_fields'].append(col)
            
            # 数据质量检查
            if len(df) == 0:
                validation_result['errors'].append("数据文件为空")
                validation_result['is_valid'] = False
            
            # 检查时间戳格式
            if 'timestamp' in df.columns:
                try:
                    pd.to_datetime(df['timestamp'].dropna().iloc[:5])
                except Exception as e:
                    validation_result['warnings'].append(f"时间戳格式可能有问题: {e}")
            
            logger.info(f"==liuq debug== 数据验证完成，有效性: {validation_result['is_valid']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"==liuq debug== 数据验证失败: {e}")
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': [],
                'info': {}
            }
    
    def standardize_field_names(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        标准化字段名
        
        Args:
            df: 原始DataFrame
            
        Returns:
            (标准化后的DataFrame, 字段映射关系)
        """
        try:
            standardized_df = df.copy()
            applied_mappings = {}
            
            # 应用字段映射
            for original_field, mapped_field in self.field_mappings.items():
                if original_field in standardized_df.columns:
                    standardized_df = standardized_df.rename(columns={original_field: mapped_field})
                    applied_mappings[original_field] = mapped_field
                    logger.debug(f"==liuq debug== 字段映射: {original_field} -> {mapped_field}")
            
            logger.info(f"==liuq debug== 字段标准化完成，应用了 {len(applied_mappings)} 个映射")
            return standardized_df, applied_mappings
            
        except Exception as e:
            logger.error(f"==liuq debug== 字段标准化失败: {e}")
            raise
    
    def filter_and_clean_data(self, df: pd.DataFrame, selected_fields: Optional[List[str]] = None) -> pd.DataFrame:
        """
        过滤和清洗数据
        
        Args:
            df: DataFrame
            selected_fields: 选中的字段列表
            
        Returns:
            清洗后的DataFrame
        """
        try:
            cleaned_df = df.copy()
            
            # 如果指定了字段，只保留这些字段（加上必需字段）
            if selected_fields:
                # 查找实际的必需字段名（大小写不敏感）
                required_fields = []

                # 查找timestamp字段
                for col in cleaned_df.columns:
                    if col.lower() == 'timestamp':
                        required_fields.append(col)
                        break

                # 查找image_name字段
                for col in cleaned_df.columns:
                    if col.lower() == 'image_name':
                        required_fields.append(col)
                        break

                # 查找image_path字段
                for col in cleaned_df.columns:
                    if col.lower() == 'image_path':
                        required_fields.append(col)
                        break

                fields_to_keep = list(set(required_fields + selected_fields))
                available_fields = [f for f in fields_to_keep if f in cleaned_df.columns]
                cleaned_df = cleaned_df[available_fields]
                logger.info(f"==liuq debug== 字段过滤完成，保留 {len(available_fields)} 个字段: {available_fields}")
            
            # 数据清洗
            initial_rows = len(cleaned_df)
            
            # 移除完全空的行
            cleaned_df = cleaned_df.dropna(how='all')
            
            # 处理数值字段的异常值
            for col in cleaned_df.columns:
                if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                    # 移除无穷大值
                    cleaned_df = cleaned_df[~cleaned_df[col].isin([float('inf'), float('-inf')])]
            
            final_rows = len(cleaned_df)
            if final_rows < initial_rows:
                logger.info(f"==liuq debug== 数据清洗完成，移除了 {initial_rows - final_rows} 行无效数据")
            
            return cleaned_df
            
        except Exception as e:
            logger.error(f"==liuq debug== 数据清洗失败: {e}")
            raise
    
    def get_available_fields(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取可用字段信息
        
        Args:
            df: DataFrame
            
        Returns:
            字段信息字典
        """
        try:
            field_info = {
                'total_fields': len(df.columns),
                'numeric_fields': [],
                'text_fields': [],
                'core_fields_available': [],
                'mapped_fields': []
            }
            
            for col in df.columns:
                field_data = {
                    'name': col,
                    'dtype': str(df[col].dtype),
                    'non_null_count': df[col].count(),
                    'null_count': df[col].isnull().sum(),
                    'is_numeric': pd.api.types.is_numeric_dtype(df[col])
                }
                
                if field_data['is_numeric']:
                    if field_data['non_null_count'] > 0:
                        field_data.update({
                            'min_value': float(df[col].min()),
                            'max_value': float(df[col].max()),
                            'mean_value': float(df[col].mean())
                        })
                    field_info['numeric_fields'].append(field_data)
                else:
                    field_info['text_fields'].append(field_data)
                
                # 检查是否为核心字段
                if col in self.core_fields:
                    field_info['core_fields_available'].append(col)
                
                # 检查是否为映射字段
                if col in self.field_mappings.values():
                    original_field = next((k for k, v in self.field_mappings.items() if v == col), None)
                    field_info['mapped_fields'].append({
                        'original': original_field,
                        'mapped': col,
                        'display_name': self.display_names.get(col, col)
                    })
            
            logger.info(f"==liuq debug== 字段信息分析完成，数值字段: {len(field_info['numeric_fields'])}")
            return field_info
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取字段信息失败: {e}")
            raise
    
    def prepare_for_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为对比分析准备数据
        
        Args:
            df: 原始DataFrame
            
        Returns:
            准备好的DataFrame
        """
        try:
            # 确保有匹配列（用于数据匹配）
            image_name_col = None
            for col in df.columns:
                if col.lower() == 'image_name':
                    image_name_col = col
                    break

            if image_name_col is None:
                raise ValueError("缺少image_name字段，无法进行数据匹配")

            # 如果列名不是标准的'image_name'，重命名它
            if image_name_col != 'image_name':
                df = df.rename(columns={image_name_col: 'image_name'})
            
            # 确保时间戳格式正确
            if 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                except Exception as e:
                    logger.warning(f"==liuq debug== 时间戳转换失败: {e}")
            
            # 按时间戳排序
            if 'timestamp' in df.columns:
                df = df.sort_values('timestamp')
            
            logger.info("==liuq debug== 数据准备完成")
            return df
            
        except Exception as e:
            logger.error(f"==liuq debug== 数据准备失败: {e}")
            raise
