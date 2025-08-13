#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列名映射器
==liuq debug== 智能列名识别和映射模块

支持将CSV文件中的基础字段自动映射为_R和_B通道格式
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class ColumnMapper:
    """列名映射器类"""
    
    def __init__(self):
        """初始化列名映射器"""
        # 支持的基础字段列表
        self.base_fields = [
            "SGW_Gray",
            "AGW_Gray", 
            "Mix_csalgo",
            "After Fir",
            "After OTP",
            "After FACE Adjust",
            "After GSL Adjust"
        ]
        
        # 映射缓存
        self.display_to_original = {}  # 显示名称 -> 原始列名
        self.original_to_display = {}  # 原始列名 -> 显示名称
        
        logger.info("==liuq debug== 列名映射器初始化完成")
    
    def normalize_field_name(self, field_name: str) -> str:
        """
        标准化字段名用于匹配
        
        Args:
            field_name: 原始字段名
            
        Returns:
            标准化后的字段名
        """
        try:
            # 去除前后空格
            normalized = field_name.strip()
            
            # 转换为小写用于比较
            normalized = normalized.lower()
            
            # 去除多余的空格
            normalized = re.sub(r'\s+', ' ', normalized)
            
            return normalized
            
        except Exception as e:
            logger.error(f"==liuq debug== 字段名标准化失败: {e}")
            return field_name
    
    def fuzzy_match(self, column_name: str, base_field: str) -> bool:
        """
        模糊匹配列名和基础字段
        
        Args:
            column_name: CSV中的列名
            base_field: 基础字段名
            
        Returns:
            是否匹配
        """
        try:
            # 标准化两个字段名
            norm_column = self.normalize_field_name(column_name)
            norm_base = self.normalize_field_name(base_field)
            
            # 精确匹配
            if norm_column == norm_base:
                return True
            
            # 检查是否包含基础字段名
            if norm_base in norm_column:
                return True
            
            # 检查去除空格后的匹配
            if norm_column.replace(' ', '') == norm_base.replace(' ', ''):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"==liuq debug== 模糊匹配失败: {e}")
            return False
    
    def generate_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        生成列名映射
        
        Args:
            df: pandas DataFrame
            
        Returns:
            原始列名到显示名称的映射字典
        """
        try:
            mapping = {}
            columns = list(df.columns)
            
            logger.info(f"==liuq debug== 开始生成列名映射，共 {len(columns)} 列")
            
            i = 0
            while i < len(columns):
                current_col = columns[i]
                
                # 检查当前列是否匹配任何基础字段
                matched_base_field = None
                for base_field in self.base_fields:
                    if self.fuzzy_match(current_col, base_field):
                        matched_base_field = base_field
                        break
                
                if matched_base_field:
                    # 当前列映射为_R通道
                    r_channel_name = f"{matched_base_field}_R"
                    mapping[current_col] = r_channel_name
                    
                    logger.info(f"==liuq debug== 映射: {current_col} -> {r_channel_name}")
                    
                    # 检查下一列是否为Unnamed（_B通道）
                    if i + 1 < len(columns):
                        next_col = columns[i + 1]
                        if "Unnamed" in next_col or next_col.strip() == "":
                            b_channel_name = f"{matched_base_field}_B"
                            mapping[next_col] = b_channel_name
                            
                            logger.info(f"==liuq debug== 映射: {next_col} -> {b_channel_name}")
                            
                            # 跳过下一列，因为已经处理了
                            i += 1
                else:
                    # 不匹配的列保持原名
                    mapping[current_col] = current_col
                
                i += 1
            
            logger.info(f"==liuq debug== 列名映射生成完成，映射了 {len([k for k, v in mapping.items() if k != v])} 个字段")
            return mapping
            
        except Exception as e:
            logger.error(f"==liuq debug== 列名映射生成失败: {e}")
            # 返回原始映射（所有列名保持不变）
            return {col: col for col in df.columns}
    
    def apply_mapping(self, df: pd.DataFrame) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        应用列名映射
        
        Args:
            df: pandas DataFrame
            
        Returns:
            (original_to_display, display_to_original) 映射字典元组
        """
        try:
            # 生成映射
            original_to_display = self.generate_column_mapping(df)
            
            # 生成反向映射
            display_to_original = {v: k for k, v in original_to_display.items()}
            
            # 缓存映射结果
            self.original_to_display = original_to_display
            self.display_to_original = display_to_original
            
            logger.info(f"==liuq debug== 列名映射应用完成")
            return original_to_display, display_to_original
            
        except Exception as e:
            logger.error(f"==liuq debug== 列名映射应用失败: {e}")
            # 返回原始映射
            identity_mapping = {col: col for col in df.columns}
            return identity_mapping, identity_mapping
    
    def get_display_columns(self, df: pd.DataFrame) -> List[str]:
        """
        获取显示用的列名列表

        Args:
            df: pandas DataFrame

        Returns:
            显示用的列名列表
        """
        try:
            if not self.original_to_display:
                self.apply_mapping(df)

            display_columns = []
            display_name_counts = {}

            for col in df.columns:
                display_name = self.original_to_display.get(col, col)

                # 处理重复的显示名称
                if display_name in display_name_counts:
                    display_name_counts[display_name] += 1
                    unique_display_name = f"{display_name}_{display_name_counts[display_name]}"
                    logger.info(f"==liuq debug== 重复显示名称处理: {display_name} -> {unique_display_name}")
                else:
                    display_name_counts[display_name] = 0
                    unique_display_name = display_name

                display_columns.append(unique_display_name)

                # 更新映射关系
                self.original_to_display[col] = unique_display_name
                self.display_to_original[unique_display_name] = col

            return display_columns

        except Exception as e:
            logger.error(f"==liuq debug== 获取显示列名失败: {e}")
            return list(df.columns)
    
    def get_original_column(self, display_name: str) -> str:
        """
        根据显示名称获取原始列名
        
        Args:
            display_name: 显示名称
            
        Returns:
            原始列名
        """
        return self.display_to_original.get(display_name, display_name)
    
    def get_display_name(self, original_name: str) -> str:
        """
        根据原始列名获取显示名称
        
        Args:
            original_name: 原始列名
            
        Returns:
            显示名称
        """
        return self.original_to_display.get(original_name, original_name)
    
    def get_mapping_info(self) -> Dict[str, any]:
        """
        获取映射信息统计
        
        Returns:
            映射信息字典
        """
        try:
            mapped_count = len([k for k, v in self.original_to_display.items() if k != v])
            total_count = len(self.original_to_display)
            
            info = {
                'total_columns': total_count,
                'mapped_columns': mapped_count,
                'unmapped_columns': total_count - mapped_count,
                'mapping_rate': mapped_count / total_count if total_count > 0 else 0,
                'base_fields_found': len(set([v.rsplit('_', 1)[0] for k, v in self.original_to_display.items() 
                                            if k != v and ('_R' in v or '_B' in v)]))
            }
            
            return info
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取映射信息失败: {e}")
            return {}
