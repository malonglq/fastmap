#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV文件读取器
==liuq debug== CSV文件读取和编码处理模块

支持多种编码格式的CSV文件读取，自动检测分隔符和编码
"""

import pandas as pd
import chardet
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import csv

# 导入列名映射器
from utils.column_mapper import ColumnMapper

logger = logging.getLogger(__name__)


class CSVReader:
    """CSV文件读取器类"""

    def __init__(self):
        """初始化CSV读取器"""
        self.supported_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
        self.supported_separators = [',', ';', '\t', '|']
        self.column_mapper = ColumnMapper()
        logger.info("==liuq debug== CSV读取器初始化完成")
    
    def detect_encoding(self, file_path: str) -> str:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            检测到的编码格式
        """
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(10240)  # 读取前10KB用于检测
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
                
                logger.info(f"==liuq debug== 检测到编码: {encoding}, 置信度: {confidence:.2f}")
                
                # 如果置信度太低，使用默认编码
                if confidence < 0.7:
                    logger.warning(f"==liuq debug== 编码检测置信度较低，使用UTF-8")
                    return 'utf-8'
                
                return encoding.lower() if encoding else 'utf-8'
                
        except Exception as e:
            logger.error(f"==liuq debug== 编码检测失败: {e}")
            return 'utf-8'
    
    def detect_separator(self, file_path: str, encoding: str) -> str:
        """
        检测CSV分隔符
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            检测到的分隔符
        """
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                # 读取前几行用于检测
                sample_lines = []
                for i, line in enumerate(file):
                    if i >= 5:  # 只读取前5行
                        break
                    sample_lines.append(line)
                
                sample_text = '\n'.join(sample_lines)
                
                # 使用csv.Sniffer检测分隔符
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample_text, delimiters=',;\t|').delimiter
                
                logger.info(f"==liuq debug== 检测到分隔符: '{delimiter}'")
                return delimiter
                
        except Exception as e:
            logger.warning(f"==liuq debug== 分隔符检测失败: {e}, 使用默认逗号")
            return ','

    def _detect_header_row(self, file_path: str, encoding: str, separator: str) -> int:
        """
        检测CSV文件中真正的header行位置

        Args:
            file_path: CSV文件路径
            encoding: 文件编码
            separator: 分隔符

        Returns:
            header行的索引（0-based）
        """
        try:
            # 读取前几行来分析
            with open(file_path, 'r', encoding=encoding) as f:
                lines = [f.readline().strip() for _ in range(5)]

            # 查找包含"Image_name"的行
            for i, line in enumerate(lines):
                if line and 'Image_name' in line:
                    logger.info(f"==liuq debug== 检测到header行在第{i+1}行: {line[:100]}...")
                    return i

            # 如果没找到Image_name，查找最可能的header行
            # 通常是第一个包含多个非空字段的行
            for i, line in enumerate(lines):
                if line and len(line.split(separator)) > 5:
                    fields = line.split(separator)
                    # 检查是否包含常见的列名模式
                    if any(field.strip() for field in fields):
                        logger.info(f"==liuq debug== 推测header行在第{i+1}行")
                        return i

            logger.warning(f"==liuq debug== 未能检测到明确的header行，使用默认第1行")
            return 0

        except Exception as e:
            logger.error(f"==liuq debug== header行检测失败: {e}")
            return 0
    
    def read_csv(self, file_path: str, encoding: Optional[str] = None, 
                 separator: Optional[str] = None) -> pd.DataFrame:
        """
        读取CSV文件
        
        Args:
            file_path: 文件路径
            encoding: 指定编码（可选，自动检测）
            separator: 指定分隔符（可选，自动检测）
            
        Returns:
            pandas DataFrame对象
        """
        try:
            # 验证文件存在
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 自动检测编码
            if encoding is None:
                encoding = self.detect_encoding(file_path)
            
            # 自动检测分隔符
            if separator is None:
                separator = self.detect_separator(file_path, encoding)
            
            logger.info(f"==liuq debug== 开始读取CSV文件: {file_path}")
            logger.info(f"==liuq debug== 使用编码: {encoding}, 分隔符: '{separator}'")

            # 检测正确的header行
            header_row = self._detect_header_row(file_path, encoding, separator)

            # 读取CSV文件
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=separator,
                header=header_row,
                low_memory=False,
                na_values=['', 'NULL', 'null', 'NaN', 'nan'],
                keep_default_na=True
            )

            # 清理列名（去除前后空格）
            df.columns = df.columns.str.strip()
            
            logger.info(f"==liuq debug== CSV文件读取成功，行数: {len(df)}, 列数: {len(df.columns)}")
            logger.info(f"==liuq debug== 列名: {list(df.columns)}")
            
            return df
            
        except UnicodeDecodeError as e:
            logger.error(f"==liuq debug== 编码错误: {e}")
            # 尝试其他编码
            for alt_encoding in self.supported_encodings:
                if alt_encoding != encoding:
                    try:
                        logger.info(f"==liuq debug== 尝试使用编码: {alt_encoding}")
                        df = pd.read_csv(file_path, encoding=alt_encoding, sep=separator)
                        logger.info(f"==liuq debug== 使用编码 {alt_encoding} 读取成功")
                        return df
                    except:
                        continue
            raise Exception(f"无法使用任何支持的编码读取文件: {file_path}")
            
        except Exception as e:
            logger.error(f"==liuq debug== CSV文件读取失败: {e}")
            raise
    
    def get_column_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取DataFrame的列信息
        
        Args:
            df: pandas DataFrame
            
        Returns:
            包含列信息的字典
        """
        try:
            column_info = {
                'total_columns': len(df.columns),
                'total_rows': len(df),
                'columns': []
            }
            
            for col in df.columns:
                col_data = {
                    'name': col,
                    'dtype': str(df[col].dtype),
                    'non_null_count': df[col].count(),
                    'null_count': df[col].isnull().sum(),
                    'is_numeric': pd.api.types.is_numeric_dtype(df[col])
                }
                
                # 如果是数值列，添加统计信息
                if col_data['is_numeric']:
                    col_data.update({
                        'min_value': df[col].min(),
                        'max_value': df[col].max(),
                        'mean_value': df[col].mean()
                    })
                
                column_info['columns'].append(col_data)
            
            logger.info(f"==liuq debug== 列信息分析完成，共 {column_info['total_columns']} 列")
            return column_info
            
        except Exception as e:
            logger.error(f"==liuq debug== 列信息分析失败: {e}")
            raise
    
    def validate_csv_structure(self, df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> bool:
        """
        验证CSV文件结构
        
        Args:
            df: pandas DataFrame
            required_columns: 必需的列名列表
            
        Returns:
            验证是否通过
        """
        try:
            # 检查是否为空
            if df.empty:
                logger.error("==liuq debug== CSV文件为空")
                return False
            
            # 检查必需列
            if required_columns:
                missing_columns = set(required_columns) - set(df.columns)
                if missing_columns:
                    logger.error(f"==liuq debug== 缺少必需列: {missing_columns}")
                    return False
            
            # 检查Image_name列（这是匹配的关键列）
            if 'Image_name' not in df.columns:
                logger.error("==liuq debug== 缺少关键列 'Image_name'")
                return False
            
            logger.info("==liuq debug== CSV文件结构验证通过")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== CSV文件结构验证失败: {e}")
            return False

    def apply_column_mapping(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        应用列名映射

        Args:
            df: 原始DataFrame

        Returns:
            (DataFrame, mapping_info) 元组，DataFrame保持不变，mapping_info包含映射信息
        """
        try:
            # 应用列名映射
            original_to_display, display_to_original = self.column_mapper.apply_mapping(df)

            # 获取映射统计信息
            mapping_info = self.column_mapper.get_mapping_info()
            mapping_info.update({
                'original_to_display': original_to_display,
                'display_to_original': display_to_original,
                'display_columns': self.column_mapper.get_display_columns(df)
            })

            logger.info(f"==liuq debug== 列名映射应用完成，映射了 {mapping_info.get('mapped_columns', 0)} 个字段")

            return df, mapping_info

        except Exception as e:
            logger.error(f"==liuq debug== 列名映射应用失败: {e}")
            # 返回原始数据和空映射信息
            identity_mapping = {col: col for col in df.columns}
            mapping_info = {
                'original_to_display': identity_mapping,
                'display_to_original': identity_mapping,
                'display_columns': list(df.columns),
                'total_columns': len(df.columns),
                'mapped_columns': 0,
                'unmapped_columns': len(df.columns),
                'mapping_rate': 0,
                'base_fields_found': 0
            }
            return df, mapping_info

    def get_display_column_info(self, df: pd.DataFrame, mapping_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取显示用的列信息（使用映射后的列名）

        Args:
            df: pandas DataFrame
            mapping_info: 列名映射信息

        Returns:
            包含显示列信息的字典
        """
        try:
            original_to_display = mapping_info.get('original_to_display', {})
            display_columns = mapping_info.get('display_columns', list(df.columns))

            column_info = {
                'total_columns': len(display_columns),
                'total_rows': len(df),
                'columns': [],
                'mapping_info': mapping_info
            }

            for original_col, display_col in original_to_display.items():
                col_data = {
                    'name': display_col,  # 使用显示名称
                    'original_name': original_col,  # 保留原始名称
                    'dtype': str(df[original_col].dtype),
                    'non_null_count': df[original_col].count(),
                    'null_count': df[original_col].isnull().sum(),
                    'is_numeric': pd.api.types.is_numeric_dtype(df[original_col])
                }

                # 如果是数值列，添加统计信息
                if col_data['is_numeric']:
                    col_data.update({
                        'min_value': df[original_col].min(),
                        'max_value': df[original_col].max(),
                        'mean_value': df[original_col].mean()
                    })

                column_info['columns'].append(col_data)

            logger.info(f"==liuq debug== 显示列信息分析完成，共 {column_info['total_columns']} 列")
            return column_info

        except Exception as e:
            logger.error(f"==liuq debug== 显示列信息分析失败: {e}")
            # 回退到原始列信息
            return self.get_column_info(df)
