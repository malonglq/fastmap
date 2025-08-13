#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证工具
==liuq debug== 数据验证和校验工具

提供各种数据验证功能
"""

import pandas as pd
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


class Validators:
    """数据验证器类"""
    
    def __init__(self):
        """初始化验证器"""
        self.supported_file_extensions = ['.csv', '.txt', '.tsv']
        self.required_columns = ['Image_name']
        logger.info("==liuq debug== 数据验证器初始化完成")
    
    def validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """
        验证文件路径
        
        Args:
            file_path: 文件路径
            
        Returns:
            验证结果字典
        """
        result = {
            'valid': False,
            'exists': False,
            'readable': False,
            'extension_valid': False,
            'size': 0,
            'errors': []
        }
        
        try:
            path_obj = Path(file_path)
            
            # 检查文件是否存在
            if not path_obj.exists():
                result['errors'].append(f"文件不存在: {file_path}")
                return result
            
            result['exists'] = True
            
            # 检查是否为文件（不是目录）
            if not path_obj.is_file():
                result['errors'].append(f"路径不是文件: {file_path}")
                return result
            
            # 检查文件扩展名
            if path_obj.suffix.lower() not in self.supported_file_extensions:
                result['errors'].append(f"不支持的文件类型: {path_obj.suffix}")
            else:
                result['extension_valid'] = True
            
            # 检查文件大小
            result['size'] = path_obj.stat().st_size
            if result['size'] == 0:
                result['errors'].append("文件为空")
            
            # 检查文件是否可读
            try:
                with open(file_path, 'r') as f:
                    f.read(1)  # 尝试读取一个字符
                result['readable'] = True
            except Exception as e:
                result['errors'].append(f"文件不可读: {e}")
            
            # 如果没有错误，标记为有效
            if not result['errors']:
                result['valid'] = True
            
            logger.info(f"==liuq debug== 文件路径验证: {file_path} - {'通过' if result['valid'] else '失败'}")
            
        except Exception as e:
            result['errors'].append(f"路径验证出错: {e}")
            logger.error(f"==liuq debug== 文件路径验证出错: {e}")
        
        return result
    
    def validate_dataframe(self, df: pd.DataFrame, name: str = "DataFrame") -> Dict[str, Any]:
        """
        验证DataFrame
        
        Args:
            df: 要验证的DataFrame
            name: DataFrame名称（用于日志）
            
        Returns:
            验证结果字典
        """
        result = {
            'valid': False,
            'empty': False,
            'has_required_columns': False,
            'column_count': 0,
            'row_count': 0,
            'missing_columns': [],
            'duplicate_columns': [],
            'errors': []
        }
        
        try:
            # 检查是否为空
            if df.empty:
                result['empty'] = True
                result['errors'].append(f"{name} 为空")
                return result
            
            result['row_count'] = len(df)
            result['column_count'] = len(df.columns)
            
            # 检查必需列（支持大小写不敏感匹配）
            df_columns_lower = {col.lower(): col for col in df.columns}
            missing_columns = []
            found_image_name_column = None

            for req_col in self.required_columns:
                # 尝试精确匹配
                if req_col in df.columns:
                    if req_col == 'Image_name':
                        found_image_name_column = req_col
                # 尝试大小写不敏感匹配
                elif req_col.lower() in df_columns_lower:
                    actual_col = df_columns_lower[req_col.lower()]
                    if req_col == 'Image_name':
                        found_image_name_column = actual_col
                    logger.info(f"==liuq debug== 找到列名变体: {req_col} -> {actual_col}")
                else:
                    missing_columns.append(req_col)

            if missing_columns:
                result['missing_columns'] = missing_columns
                logger.error(f"==liuq debug== {name} 可用列名: {list(df.columns)}")
                result['errors'].append(f"{name} 缺少必需列: {missing_columns}")
            else:
                result['has_required_columns'] = True
            
            # 检查重复列名
            duplicate_columns = df.columns[df.columns.duplicated()].tolist()
            if duplicate_columns:
                result['duplicate_columns'] = duplicate_columns
                result['errors'].append(f"{name} 存在重复列名: {duplicate_columns}")
            
            # 检查Image_name列的有效性
            if found_image_name_column:
                image_name_validation = self.validate_image_name_column(df[found_image_name_column])
                if not image_name_validation['valid']:
                    result['errors'].extend(image_name_validation['errors'])
            
            # 如果没有错误，标记为有效
            if not result['errors']:
                result['valid'] = True
            
            logger.info(f"==liuq debug== {name} 验证: {'通过' if result['valid'] else '失败'}")
            
        except Exception as e:
            result['errors'].append(f"{name} 验证出错: {e}")
            logger.error(f"==liuq debug== {name} 验证出错: {e}")
        
        return result
    
    def validate_image_name_column(self, image_name_series: pd.Series) -> Dict[str, Any]:
        """
        验证Image_name列
        
        Args:
            image_name_series: Image_name列的Series
            
        Returns:
            验证结果字典
        """
        result = {
            'valid': False,
            'null_count': 0,
            'empty_count': 0,
            'duplicate_count': 0,
            'invalid_format_count': 0,
            'errors': []
        }
        
        try:
            # 检查空值
            result['null_count'] = image_name_series.isnull().sum()
            if result['null_count'] > 0:
                result['errors'].append(f"Image_name列存在 {result['null_count']} 个空值")
            
            # 检查空字符串
            empty_mask = image_name_series.astype(str).str.strip() == ''
            result['empty_count'] = empty_mask.sum()
            if result['empty_count'] > 0:
                result['errors'].append(f"Image_name列存在 {result['empty_count']} 个空字符串")
            
            # 检查重复值
            result['duplicate_count'] = image_name_series.duplicated().sum()
            if result['duplicate_count'] > 0:
                result['errors'].append(f"Image_name列存在 {result['duplicate_count']} 个重复值")
            
            # 检查文件名格式
            invalid_format_count = 0
            for value in image_name_series.dropna():
                if not self.validate_filename_format(str(value)):
                    invalid_format_count += 1
            
            result['invalid_format_count'] = invalid_format_count
            if invalid_format_count > 0:
                result['errors'].append(f"Image_name列存在 {invalid_format_count} 个格式无效的文件名")
            
            # 如果没有错误，标记为有效
            if not result['errors']:
                result['valid'] = True
            
            logger.info(f"==liuq debug== Image_name列验证: {'通过' if result['valid'] else '失败'}")
            
        except Exception as e:
            result['errors'].append(f"Image_name列验证出错: {e}")
            logger.error(f"==liuq debug== Image_name列验证出错: {e}")
        
        return result
    
    def validate_filename_format(self, filename: str) -> bool:
        """
        验证文件名格式
        
        Args:
            filename: 文件名
            
        Returns:
            是否为有效格式
        """
        try:
            # 基本检查：不能为空
            if not filename or filename.strip() == '':
                return False
            
            # 检查是否包含非法字符
            illegal_chars = r'[<>:"/\\|?*]'
            if re.search(illegal_chars, filename):
                return False
            
            # 检查长度（Windows文件名限制）
            if len(filename) > 255:
                return False
            
            # 检查是否为保留名称（Windows）
            reserved_names = [
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            ]
            
            name_without_ext = Path(filename).stem.upper()
            if name_without_ext in reserved_names:
                return False
            
            return True
            
        except Exception:
            return False
    
    def validate_numeric_columns(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """
        验证数值列
        
        Args:
            df: DataFrame
            columns: 要验证的列名列表
            
        Returns:
            验证结果字典
        """
        result = {
            'valid': True,
            'column_results': {},
            'errors': []
        }
        
        try:
            for col in columns:
                if col not in df.columns:
                    result['errors'].append(f"列不存在: {col}")
                    result['valid'] = False
                    continue
                
                col_result = {
                    'is_numeric': False,
                    'null_count': 0,
                    'infinite_count': 0,
                    'min_value': None,
                    'max_value': None,
                    'errors': []
                }
                
                # 尝试转换为数值
                try:
                    numeric_series = pd.to_numeric(df[col], errors='coerce')
                    col_result['is_numeric'] = True
                    
                    # 检查空值
                    col_result['null_count'] = numeric_series.isnull().sum()
                    
                    # 检查无穷值
                    col_result['infinite_count'] = numeric_series.isin([float('inf'), float('-inf')]).sum()
                    
                    # 计算统计值
                    valid_values = numeric_series.dropna()
                    if len(valid_values) > 0:
                        col_result['min_value'] = valid_values.min()
                        col_result['max_value'] = valid_values.max()
                    
                except Exception as e:
                    col_result['errors'].append(f"数值转换失败: {e}")
                    result['valid'] = False
                
                result['column_results'][col] = col_result
            
            logger.info(f"==liuq debug== 数值列验证: {'通过' if result['valid'] else '失败'}")
            
        except Exception as e:
            result['errors'].append(f"数值列验证出错: {e}")
            result['valid'] = False
            logger.error(f"==liuq debug== 数值列验证出错: {e}")
        
        return result
    
    def validate_selected_fields(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                                selected_fields: List[str]) -> Dict[str, Any]:
        """
        验证用户选择的分析字段
        
        Args:
            df1: 第一个DataFrame
            df2: 第二个DataFrame
            selected_fields: 选择的字段列表
            
        Returns:
            验证结果字典
        """
        result = {
            'valid': True,
            'missing_in_df1': [],
            'missing_in_df2': [],
            'non_numeric_fields': [],
            'errors': []
        }
        
        try:
            if not selected_fields:
                result['errors'].append("未选择任何分析字段")
                result['valid'] = False
                return result
            
            # 检查字段是否存在
            for field in selected_fields:
                if field not in df1.columns:
                    result['missing_in_df1'].append(field)
                if field not in df2.columns:
                    result['missing_in_df2'].append(field)
            
            # 检查数值类型
            for field in selected_fields:
                if field in df1.columns and field in df2.columns:
                    # 检查是否为数值类型或可转换为数值
                    try:
                        pd.to_numeric(df1[field], errors='raise')
                        pd.to_numeric(df2[field], errors='raise')
                    except:
                        result['non_numeric_fields'].append(field)
            
            # 汇总错误
            if result['missing_in_df1']:
                result['errors'].append(f"文件1中缺少字段: {result['missing_in_df1']}")
                result['valid'] = False
            
            if result['missing_in_df2']:
                result['errors'].append(f"文件2中缺少字段: {result['missing_in_df2']}")
                result['valid'] = False
            
            if result['non_numeric_fields']:
                result['errors'].append(f"非数值字段: {result['non_numeric_fields']}")
                result['valid'] = False
            
            logger.info(f"==liuq debug== 选择字段验证: {'通过' if result['valid'] else '失败'}")
            
        except Exception as e:
            result['errors'].append(f"选择字段验证出错: {e}")
            result['valid'] = False
            logger.error(f"==liuq debug== 选择字段验证出错: {e}")
        
        return result
