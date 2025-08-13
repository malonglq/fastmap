#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据匹配器
==liuq debug== 基于Image_name的数据匹配算法

实现两个CSV文件之间的数据行匹配逻辑
"""

import pandas as pd
import logging
import re
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DataMatcher:
    """数据匹配器类"""
    
    def __init__(self):
        """初始化数据匹配器"""
        self.match_column = 'Image_name'
        self.matched_pairs = []
        self.unmatched_file1 = []
        self.unmatched_file2 = []
        logger.info("==liuq debug== 数据匹配器初始化完成")
    
    def extract_prefix(self, filename: str) -> str:
        """
        从文件名中提取前缀序号
        
        Args:
            filename: 文件名
            
        Returns:
            提取的前缀序号
        """
        try:
            # 处理各种文件名格式
            # 例如: "123_zhufeng_IMG20250101214007_ori.jpg" -> "123"
            # 或者: "123_zhufeng_IMG20250101214007.jpg" -> "123"
            
            # 移除路径部分，只保留文件名
            filename = Path(filename).name
            
            # 使用正则表达式提取开头的数字
            match = re.match(r'^(\d+)', filename)
            if match:
                prefix = match.group(1)

                return prefix
            
            # 如果没有找到数字前缀，尝试其他模式
            # 例如处理没有数字前缀的情况
            parts = filename.split('_')
            if parts:
                # 尝试从第一部分提取数字
                first_part = parts[0]
                numbers = re.findall(r'\d+', first_part)
                if numbers:
                    prefix = numbers[0]

                    return prefix
            
            # 如果都没有找到，返回原文件名（去除扩展名）
            prefix = Path(filename).stem

            return prefix
            
        except Exception as e:
            logger.error(f"==liuq debug== 前缀提取失败: {e}")
            return filename
    
    def normalize_filename(self, filename: str) -> str:
        """
        标准化文件名用于匹配
        
        Args:
            filename: 原始文件名
            
        Returns:
            标准化后的文件名
        """
        try:
            # 移除路径
            filename = Path(filename).name
            
            # 转换为小写
            filename = filename.lower()
            
            # 移除常见的后缀标识
            filename = re.sub(r'_ori\.(jpg|jpeg|png|bmp|tiff?)$', r'.\1', filename)
            filename = re.sub(r'_original\.(jpg|jpeg|png|bmp|tiff?)$', r'.\1', filename)
            filename = re.sub(r'_processed\.(jpg|jpeg|png|bmp|tiff?)$', r'.\1', filename)
            
            return filename
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件名标准化失败: {e}")
            return filename
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """
        计算两个文件名的相似度
        
        Args:
            name1: 文件名1
            name2: 文件名2
            
        Returns:
            相似度分数 (0-1)
        """
        try:
            # 提取前缀进行比较
            prefix1 = self.extract_prefix(name1)
            prefix2 = self.extract_prefix(name2)
            
            # 如果前缀完全相同，相似度很高
            if prefix1 == prefix2:
                return 0.9
            
            # 标准化文件名进行比较
            norm1 = self.normalize_filename(name1)
            norm2 = self.normalize_filename(name2)
            
            # 简单的字符串相似度计算
            if norm1 == norm2:
                return 1.0
            
            # 计算公共子串长度
            common_length = 0
            min_length = min(len(norm1), len(norm2))
            
            for i in range(min_length):
                if norm1[i] == norm2[i]:
                    common_length += 1
                else:
                    break
            
            similarity = common_length / max(len(norm1), len(norm2))
            return similarity
            
        except Exception as e:
            logger.error(f"==liuq debug== 相似度计算失败: {e}")
            return 0.0
    
    def match_data(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                   similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        匹配两个DataFrame中的数据
        
        Args:
            df1: 第一个DataFrame
            df2: 第二个DataFrame
            similarity_threshold: 相似度阈值
            
        Returns:
            匹配结果字典
        """
        try:
            logger.info("==liuq debug== 开始数据匹配")
            
            # 重置匹配结果
            self.matched_pairs = []
            self.unmatched_file1 = []
            self.unmatched_file2 = []
            
            # 验证必需列存在
            if self.match_column not in df1.columns:
                raise ValueError(f"DataFrame1 中缺少列: {self.match_column}")
            if self.match_column not in df2.columns:
                raise ValueError(f"DataFrame2 中缺少列: {self.match_column}")
            
            # 创建已匹配标记
            matched_indices_df2 = set()
            
            # 遍历第一个DataFrame的每一行
            for idx1, row1 in df1.iterrows():
                filename1 = str(row1[self.match_column])
                best_match_idx = None
                best_similarity = 0.0
                
                # 在第二个DataFrame中寻找最佳匹配
                for idx2, row2 in df2.iterrows():
                    if idx2 in matched_indices_df2:
                        continue  # 已经被匹配过
                    
                    filename2 = str(row2[self.match_column])
                    similarity = self.calculate_similarity(filename1, filename2)
                    
                    if similarity > best_similarity and similarity >= similarity_threshold:
                        best_similarity = similarity
                        best_match_idx = idx2
                
                # 如果找到匹配
                if best_match_idx is not None:
                    matched_row2 = df2.iloc[best_match_idx]
                    self.matched_pairs.append({
                        'index1': idx1,
                        'index2': best_match_idx,
                        'row1': row1,
                        'row2': matched_row2,
                        'similarity': best_similarity,
                        'filename1': filename1,
                        'filename2': str(matched_row2[self.match_column])
                    })
                    matched_indices_df2.add(best_match_idx)

                else:
                    self.unmatched_file1.append({
                        'index': idx1,
                        'row': row1,
                        'filename': filename1
                    })

            
            # 记录第二个DataFrame中未匹配的行
            for idx2, row2 in df2.iterrows():
                if idx2 not in matched_indices_df2:
                    filename2 = str(row2[self.match_column])
                    self.unmatched_file2.append({
                        'index': idx2,
                        'row': row2,
                        'filename': filename2
                    })

            
            # 生成匹配结果统计
            result = {
                'total_file1': len(df1),
                'total_file2': len(df2),
                'matched_pairs': len(self.matched_pairs),
                'unmatched_file1': len(self.unmatched_file1),
                'unmatched_file2': len(self.unmatched_file2),
                'match_rate': len(self.matched_pairs) / max(len(df1), len(df2)) * 100,
                'pairs': self.matched_pairs,
                'unmatched1': self.unmatched_file1,
                'unmatched2': self.unmatched_file2
            }
            
            logger.info(f"==liuq debug== 数据匹配完成")
            logger.info(f"==liuq debug== 文件1总数: {result['total_file1']}")
            logger.info(f"==liuq debug== 文件2总数: {result['total_file2']}")
            logger.info(f"==liuq debug== 成功匹配: {result['matched_pairs']} 对")
            logger.info(f"==liuq debug== 匹配率: {result['match_rate']:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"==liuq debug== 数据匹配失败: {e}")
            raise
    
    def get_matched_dataframe(self, selected_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        获取匹配结果的DataFrame
        
        Args:
            selected_columns: 选择的列名列表
            
        Returns:
            包含匹配结果的DataFrame
        """
        try:
            if not self.matched_pairs:
                logger.warning("==liuq debug== 没有匹配的数据对")
                return pd.DataFrame()
            
            matched_data = []
            
            for pair in self.matched_pairs:
                row1 = pair['row1']
                row2 = pair['row2']
                
                # 创建合并行
                merged_row = {
                    'Image_name_1': pair['filename1'],
                    'Image_name_2': pair['filename2'],
                    'similarity': pair['similarity']
                }
                
                # 添加选定的列
                if selected_columns:
                    for col in selected_columns:
                        if col in row1.index:
                            merged_row[f'{col}_file1'] = row1[col]
                        if col in row2.index:
                            merged_row[f'{col}_file2'] = row2[col]
                        
                        # 计算变化
                        if col in row1.index and col in row2.index:
                            try:
                                val1 = pd.to_numeric(row1[col], errors='coerce')
                                val2 = pd.to_numeric(row2[col], errors='coerce')
                                if pd.notna(val1) and pd.notna(val2):
                                    change = val2 - val1
                                    change_percent = (change / val1 * 100) if val1 != 0 else 0
                                    merged_row[f'{col}_change'] = change
                                    merged_row[f'{col}_change_percent'] = change_percent
                            except:
                                pass
                
                matched_data.append(merged_row)
            
            result_df = pd.DataFrame(matched_data)
            logger.info(f"==liuq debug== 生成匹配结果DataFrame，行数: {len(result_df)}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成匹配结果DataFrame失败: {e}")
            raise
