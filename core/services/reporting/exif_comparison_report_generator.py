#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF对比分析报告生成器
==liuq debug== FastMapV2 EXIF对比分析报告生成器

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 15:25:00 +08:00; Reason: 阶段2-创建EXIF对比分析报告生成器; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 实现EXIF对比分析报告生成功能
"""

import logging
import re
import csv
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from core.interfaces.report_generator import IReportGenerator, ReportType
from core.services.reporting.html_template_service import HTMLTemplateService

logger = logging.getLogger(__name__)


class ExifComparisonReportGenerator(IReportGenerator):
    """
    EXIF对比分析报告生成器
    
    集成EXIF数据适配器和CSV对比分析适配器，
    生成完整的EXIF对比分析报告
    """
    
    def __init__(self):
        """初始化EXIF对比分析报告生成器"""
        # 初始化HTML模板服务，统一管理模板
        self.template_service = HTMLTemplateService()

        # 按照文档需求定义核心字段
        self.core_fields = [
            'color_sensor_irRatio',
            'color_sensor_sensorCct',
            'meta_data_currentFrame_bv'
        ]

        # 按照文档需求定义色彩增益字段
        self.color_gain_fields = [
            'ealgo_data_SGW_gray_RpG', 'ealgo_data_SGW_gray_BpG',
            'ealgo_data_AGW_gray_RpG', 'ealgo_data_AGW_gray_BpG',
            'ealgo_data_Mix_gray_edge_RpG', 'ealgo_data_Mix_gray_edge_BpG',
            'ealgo_data_Mix_csalgo_RpG', 'ealgo_data_Mix_csalgo_BpG',
            'ealgo_data_After_face_RpG', 'ealgo_data_After_face_BpG'
        ]

        # 定义优先字段列表（用户指定的自动勾选字段）
        self.priority_fields = [
            'meta_data_currentFrame_ctemp',
            'meta_data_after_face_Ctemp',
            'meta_data_outputCtemp',
            'meta_data_lastFrame_ctemp',
            'stats_weight_triggerCtemp',
            'face_info_lux_index',
            'meta_data_resultCcmatrix',
            'ealgo_data_SGW_gray_RpG',
            'ealgo_data_SGW_gray_BpG',
            'ealgo_data_AGW_gray_RpG',
            'ealgo_data_AGW_gray_BpG',
            'ealgo_data_Mix_csalgo_RpG',
            'ealgo_data_Mix_csalgo_BpG',
            'ealgo_data_After_face_RpG',
            'ealgo_data_After_face_BpG',
            'ealgo_data_cnvgEst_RpG',
            'ealgo_data_cnvgEst_BpG',
            'meta_data_gslpos',
            'meta_data_gslGain_rgain',
            'meta_data_gslGain_bgain',
            'color_sensor_irRatio',
            'color_sensor_acRatio',
            'color_sensor_sensorCct',
            'face_info_light_skin_target_rg',
            'face_info_light_skin_target_bg',
            'face_info_dark_skin_target_rg',
            'face_info_dark_skin_target_bg',
            'face_info_light_skin_cct',
            'face_info_dark_skin_cct',
            'face_info_light_skin_weight',
            'face_info_skin_target_dist_ratio',
            'face_info_faceawb_weight',
            'face_info_final_skin_cct'
        ]

        # 所有需要分析的字段
        self.required_fields = self.core_fields + self.color_gain_fields

        # 字段显示名称映射（为了兼容GUI）
        self.display_names = {
            'color_sensor_irRatio': 'IR比率',
            'color_sensor_sensorCct': '传感器CCT',
            'meta_data_currentFrame_bv': '当前帧BV',
            'ealgo_data_SGW_gray_RpG': 'SGW灰度RpG',
            'ealgo_data_SGW_gray_BpG': 'SGW灰度BpG',
            'ealgo_data_AGW_gray_RpG': 'AGW灰度RpG',
            'ealgo_data_AGW_gray_BpG': 'AGW灰度BpG',
            'ealgo_data_Mix_gray_edge_RpG': 'Mix边缘RpG',
            'ealgo_data_Mix_gray_edge_BpG': 'Mix边缘BpG',
            'ealgo_data_Mix_csalgo_RpG': 'Mix算法RpG',
            'ealgo_data_Mix_csalgo_BpG': 'Mix算法BpG',
            'ealgo_data_After_face_RpG': '人脸后RpG',
            'ealgo_data_After_face_BpG': '人脸后BpG'
        }

        logger.info("==liuq debug== EXIF对比分析报告生成器初始化完成")
    
    def generate(self, data: Dict[str, Any]) -> str:
        """
        生成EXIF对比分析报告

        Args:
            data: {
                'test_csv_path': str,           # 测试机CSV文件路径
                'reference_csv_path': str,      # 对比机CSV文件路径
                'selected_fields': List[str],   # 选中的字段列表（可选）
                'output_path': str,             # 输出路径（可选）
            }

        Returns:
            生成的报告文件路径
        """
        try:
            logger.info("==liuq debug== 开始生成EXIF对比分析报告")

            # 验证输入数据
            self._validate_input_data(data)

            # 提取参数
            test_csv_path = data['test_csv_path']
            reference_csv_path = data['reference_csv_path']
            selected_fields = data.get('selected_fields', None)
            output_path = data.get('output_path', None)

            # 步骤1: 读取CSV数据
            logger.info("==liuq debug== 步骤1: 读取CSV数据")
            test_df = self._read_csv_file(test_csv_path)
            reference_df = self._read_csv_file(reference_csv_path)

            # 步骤2: 确定分析字段（按照文档需求使用指定字段）
            if selected_fields is None:
                # 使用文档中指定的13个字段
                selected_fields = self.required_fields.copy()
                logger.info(f"==liuq debug== 使用文档指定字段: {selected_fields}")

            # 验证字段是否存在
            available_columns_test = set(test_df.columns)
            available_columns_ref = set(reference_df.columns)

            missing_fields = []
            for field in selected_fields:
                if field not in available_columns_test:
                    missing_fields.append(f"测试机缺少字段: {field}")
                if field not in available_columns_ref:
                    missing_fields.append(f"对比机缺少字段: {field}")

            if missing_fields:
                logger.warning(f"==liuq debug== 部分字段缺失: {missing_fields}")
                # 只使用存在的字段
                selected_fields = [f for f in selected_fields
                                 if f in available_columns_test and f in available_columns_ref]
                logger.info(f"==liuq debug== 实际使用字段: {selected_fields}")

            if not selected_fields:
                raise ValueError("没有可用的分析字段，请检查CSV文件是否包含必需的EXIF字段")

            # 步骤3: 数据匹配（使用数字序列号匹配）
            logger.info("==liuq debug== 步骤3: 数据匹配（数字序列号匹配）")
            match_result = self._match_by_sequence_number(test_df, reference_df)

            matched_pairs = match_result.get('pairs', [])
            if not matched_pairs:
                raise ValueError("没有找到匹配的数据对，请检查数据文件和文件名格式")

            logger.info(f"==liuq debug== 找到 {len(matched_pairs)} 个匹配数据对")

            # 步骤4: 生成分析数据
            logger.info("==liuq debug== 步骤4: 生成分析数据")
            analysis_data = self._generate_analysis_data(matched_pairs, selected_fields)

            # 计算匹配摘要（用于报告封面和匹配质量）
            matching_summary = {
                'total_test': match_result.get('total_test', 0),
                'total_reference': match_result.get('total_reference', 0),
                'matched_pairs': len(matched_pairs),
                'unmatched_test': match_result.get('unmatched1', 0),
                'unmatched_reference': match_result.get('unmatched2', 0),
                'match_rate': (len(matched_pairs) / max(match_result.get('total_test', 1), 1)) if match_result else 0.0,
                'method': match_result.get('match_method', 'sequence_number')
            }

            # 步骤5: 生成HTML报告
            logger.info("==liuq debug== 步骤5: 生成HTML报告")
            report_path = self._generate_html_report(
                analysis_data,
                test_csv_path,
                reference_csv_path,
                output_path,
                matching_summary
            )

            logger.info(f"==liuq debug== EXIF对比分析报告生成完成: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"==liuq debug== EXIF对比分析报告生成失败: {e}")
            raise RuntimeError(f"EXIF对比分析报告生成失败: {e}")
    
    def get_report_name(self) -> str:
        """获取报告类型名称"""
        return "EXIF对比分析报告"
    
    def get_report_type(self) -> ReportType:
        """获取报告类型"""
        return ReportType.EXIF_COMPARISON
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        验证输入数据是否有效
        
        Args:
            data: 待验证的数据
            
        Returns:
            数据是否有效
        """
        try:
            self._validate_input_data(data)
            return True
        except Exception as e:
            logger.warning(f"==liuq debug== 数据验证失败: {e}")
            return False
    
    def _validate_input_data(self, data: Dict[str, Any]):
        """验证输入数据"""
        # 检查必需字段
        required_fields = ['test_csv_path', 'reference_csv_path']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")
        
        # 检查文件是否存在
        test_path = Path(data['test_csv_path'])
        reference_path = Path(data['reference_csv_path'])
        
        if not test_path.exists():
            raise FileNotFoundError(f"测试机CSV文件不存在: {test_path}")
        if not reference_path.exists():
            raise FileNotFoundError(f"对比机CSV文件不存在: {reference_path}")
        
        # 检查文件扩展名
        if test_path.suffix.lower() != '.csv':
            raise ValueError(f"测试机文件不是CSV格式: {test_path}")
        if reference_path.suffix.lower() != '.csv':
            raise ValueError(f"对比机文件不是CSV格式: {reference_path}")
        
        # 检查可选参数的类型
        if 'selected_fields' in data and data['selected_fields'] is not None:
            if not isinstance(data['selected_fields'], list):
                raise ValueError("selected_fields必须是列表类型")
        
        if 'similarity_threshold' in data:
            threshold = data['similarity_threshold']
            if not isinstance(threshold, (int, float)) or not (0 <= threshold <= 1):
                raise ValueError("similarity_threshold必须是0-1之间的数值")
        
        if 'match_column' in data:
            if not isinstance(data['match_column'], str):
                raise ValueError("match_column必须是字符串类型")
    
    def get_supported_fields(self, csv_path: str) -> Dict[str, Any]:
        """
        获取CSV文件支持的字段信息

        Args:
            csv_path: CSV文件路径

        Returns:
            字段信息字典
        """
        try:
            # 读取CSV文件
            df = self._read_csv_file(csv_path)

            # 获取所有列名
            all_columns = list(df.columns)

            # 检查哪些必需字段存在
            available_required_fields = [field for field in self.required_fields if field in all_columns]
            missing_required_fields = [field for field in self.required_fields if field not in all_columns]

            # 检查数值字段并收集详细信息
            numeric_fields = []
            for col in all_columns:
                try:
                    # 尝试转换为数值
                    numeric_series = pd.to_numeric(df[col], errors='coerce')
                    # 如果转换后不全是NaN，则认为是数值字段
                    if not numeric_series.isna().all():
                        # 收集字段详细信息
                        valid_values = numeric_series.dropna()
                        field_info = {
                            'name': col,
                            'type': 'numeric',
                            'dtype': str(df[col].dtype),
                            'non_null_count': len(valid_values),
                            'total_count': len(df[col]),
                            'null_count': len(df[col]) - len(valid_values)
                        }

                        # 如果有有效数值，计算统计信息
                        if len(valid_values) > 0:
                            field_info.update({
                                'min_value': float(valid_values.min()),
                                'max_value': float(valid_values.max()),
                                'mean_value': float(valid_values.mean()),
                                'std_value': float(valid_values.std()) if len(valid_values) > 1 else 0.0
                            })

                        numeric_fields.append(field_info)
                except Exception as e:
                    # 记录详细错误信息但不中断处理
                    logger.debug(f"==liuq debug== 字段 {col} 不是数值字段: {e}")
                    continue

            field_info = {
                'original_columns': all_columns,
                'required_fields': self.required_fields,
                'available_required_fields': available_required_fields,
                'missing_required_fields': missing_required_fields,
                'numeric_fields': numeric_fields,  # 使用详细的字段信息
                'core_fields_available': [field for field in self.core_fields if field in all_columns],
                'color_gain_fields_available': [field for field in self.color_gain_fields if field in all_columns],
                'total_fields': len(all_columns),  # GUI期望的字段名
                'total_rows': len(df),
                'file_info': {
                    'path': csv_path,
                    'columns_count': len(all_columns),
                    'rows_count': len(df)
                }
            }

            return field_info

        except Exception as e:
            logger.error(f"==liuq debug== 获取字段信息失败: {e}")
            raise
    
    def preview_data_matching(self, test_csv_path: str, reference_csv_path: str,
                            match_column: str = 'image_name',
                            similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        预览数据匹配结果

        Args:
            test_csv_path: 测试机CSV路径
            reference_csv_path: 对比机CSV路径
            match_column: 匹配列名（已弃用，使用数字序列号匹配）
            similarity_threshold: 相似度阈值（已弃用，使用数字序列号匹配）

        Returns:
            匹配预览结果
        """
        try:
            # 读取数据
            test_df = self._read_csv_file(test_csv_path)
            reference_df = self._read_csv_file(reference_csv_path)

            # 执行数字序列号匹配
            match_result = self._match_by_sequence_number(test_df, reference_df)
            
            # 准备预览结果
            pairs = match_result.get('pairs', [])
            unmatched1 = match_result.get('unmatched1', match_result.get('unmatched_file1', []))
            unmatched2 = match_result.get('unmatched2', match_result.get('unmatched_file2', []))

            # 处理可能的数字格式
            if isinstance(unmatched1, int):
                unmatched1_count = unmatched1
            else:
                unmatched1_count = len(unmatched1) if unmatched1 else 0

            if isinstance(unmatched2, int):
                unmatched2_count = unmatched2
            else:
                unmatched2_count = len(unmatched2) if unmatched2 else 0

            preview_result = {
                'total_test_records': len(test_df),
                'total_reference_records': len(reference_df),
                'matched_pairs': len(pairs),
                'unmatched_test': unmatched1_count,
                'unmatched_reference': unmatched2_count,
                'match_rate': len(pairs) / max(len(test_df), 1),
                'sample_matches': []
            }
            
            # 添加样例匹配
            pairs = match_result.get('pairs', [])
            for i, pair in enumerate(pairs[:5]):  # 只显示前5个
                sample = {
                    'test_name': pair.get('filename1', ''),
                    'reference_name': pair.get('filename2', ''),
                    'similarity': pair.get('similarity', 0)
                }
                preview_result['sample_matches'].append(sample)
            
            return preview_result
            
        except Exception as e:
            logger.error(f"==liuq debug== 数据匹配预览失败: {e}")
            raise

    def _match_by_sequence_number(self, test_df, reference_df):
        """
        按照文档需求使用数字序列号进行匹配

        从文件名开头提取数字序列号作为匹配键
        例如：从 '32_zhufeng_...jpg' 中提取 '32'

        Args:
            test_df: 测试机数据
            reference_df: 对比机数据

        Returns:
            匹配结果字典
        """
        import re

        try:
            logger.info("==liuq debug== 开始数字序列号匹配")

            # 提取数字序列号的函数
            def extract_sequence_number(filename):
                if pd.isna(filename) or not isinstance(filename, str):
                    return None
                s = filename.strip()
                # 匹配文件名开头的数字序列
                match = re.match(r'^(\d+)', s)
                return match.group(1) if match else None

            # 为测试机数据添加序列号列
            test_df = test_df.copy()
            test_df['sequence_number'] = test_df['image_name'].apply(extract_sequence_number)

            # 为对比机数据添加序列号列
            reference_df = reference_df.copy()
            reference_df['sequence_number'] = reference_df['image_name'].apply(extract_sequence_number)

            # 移除没有序列号的行
            test_df_valid = test_df.dropna(subset=['sequence_number'])
            reference_df_valid = reference_df.dropna(subset=['sequence_number'])

            logger.info(f"==liuq debug== 测试机有效数据: {len(test_df_valid)}, 对比机有效数据: {len(reference_df_valid)}")

            # 基于序列号进行匹配
            matched_pairs = []
            test_sequences = set(test_df_valid['sequence_number'])
            ref_sequences = set(reference_df_valid['sequence_number'])
            common_sequences = test_sequences.intersection(ref_sequences)

            logger.info(f"==liuq debug== 找到共同序列号: {len(common_sequences)}")

            for seq_num in common_sequences:
                test_row = test_df_valid[test_df_valid['sequence_number'] == seq_num].iloc[0]
                ref_row = reference_df_valid[reference_df_valid['sequence_number'] == seq_num].iloc[0]

                pair = {
                    'filename1': test_row['image_name'],
                    'filename2': ref_row['image_name'],
                    'sequence_number': seq_num,
                    'similarity': 1.0,  # 序列号完全匹配
                    'test_data': test_row.to_dict(),
                    'reference_data': ref_row.to_dict()
                }
                matched_pairs.append(pair)

            # 计算未匹配的数据
            unmatched_test = len(test_df_valid) - len(matched_pairs)
            unmatched_reference = len(reference_df_valid) - len(matched_pairs)

            match_result = {
                'pairs': matched_pairs,
                'unmatched1': unmatched_test,
                'unmatched2': unmatched_reference,
                'total_test': len(test_df),
                'total_reference': len(reference_df),
                'match_method': 'sequence_number'
            }

            logger.info(f"==liuq debug== 匹配完成: {len(matched_pairs)} 对, 测试机未匹配: {unmatched_test}, 对比机未匹配: {unmatched_reference}")

            return match_result

        except Exception as e:
            logger.error(f"==liuq debug== 数字序列号匹配失败: {e}")
            raise

    def _read_csv_file(self, csv_path: str):
        """读取CSV文件"""
        try:
            # 尝试不同的编码（优先utf-8-sig以剥离BOM）
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']

            last_err = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    # 规范化列名：去BOM、去首尾空白、统一小写
                    def _canonical(x: object) -> str:
                        s = str(x)
                        for bad in ('\ufeff', '\u200b', '\xa0'):
                            s = s.replace(bad, ' ')
                        s = s.strip().lower()
                        # 将连续空白替换为下划线，并去除非字母数字和下划线
                        s = re.sub(r'\s+', '_', s)
                        s = re.sub(r'[^a-z0-9_]', '', s)
                        # 常见等价：imagename -> image_name
                        if s == 'imagename':
                            s = 'image_name'
                        return s

                    df.columns = [_canonical(c) for c in df.columns]

                    # 如果未发现 image_name，尝试自动识别“多行表头”
                    if 'image_name' not in df.columns:
                        try:
                            # 先用csv.Sniffer侦测分隔符，再扫描前50行查找包含 image_name 的行
                            with open(csv_path, 'r', encoding=encoding, errors='replace') as f:
                                sample = f.read(4096)
                                f.seek(0)
                                try:
                                    dialect = csv.Sniffer().sniff(sample)
                                    delimiter = dialect.delimiter
                                except Exception:
                                    delimiter = ','
                                reader = csv.reader(f, delimiter=delimiter)
                                header_row_idx = None
                                for i, row in enumerate(reader):
                                    if i >= 5:
                                        break
                                    row_vals = [_canonical(v) for v in row]
                                    if 'image_name' in row_vals:
                                        header_row_idx = i
                                        break
                            if header_row_idx is None:
                                # Fallback: 使用pandas自动分隔推断再扫描
                                try:
                                    head_probe_df = pd.read_csv(csv_path, encoding=encoding, header=None, nrows=5, engine='python', sep=None)
                                    for i in range(len(head_probe_df)):
                                        row_vals = [_canonical(v) for v in list(head_probe_df.iloc[i].values)]
                                        if 'image_name' in row_vals:
                                            header_row_idx = i
                                            break
                                except Exception as _e2:
                                    logger.info(f"==liuq debug== 表头自动识别(pandas探测)失败: {_e2}")
                            if header_row_idx is not None:
                                df = pd.read_csv(csv_path, encoding=encoding, header=header_row_idx, sep=delimiter)
                                df.columns = [_canonical(c) for c in df.columns]
                                logger.info(f"==liuq debug== 自动识别表头在第 {header_row_idx+1} 行(1-based), 分隔符: '{delimiter}'")
                            else:
                                logger.info("==liuq debug== 未能在前50行定位到 'image_name'，保留原始第一行作为表头")
                        except Exception as _e:
                            logger.info(f"==liuq debug== 表头自动识别跳过: {_e}")

                    # 别名兜底（常见变体统一为 image_name）
                    alias_map = {
                        'image_name': 'image_name',
                        'imagename': 'image_name',
                        'image': 'image_name',
                        'file_name': 'image_name',
                        'filename': 'image_name',
                        'file': 'image_name',
                        'name': 'image_name',
                        'image_name列': 'image_name',
                    }
                    for k, v in list(alias_map.items()):
                        if k in df.columns and 'image_name' not in df.columns:
                            df.rename(columns={k: v}, inplace=True)
                    logger.info(f"==liuq debug== 成功读取CSV文件: {csv_path}, 编码: {encoding}; 列: {list(df.columns)[:6]}...")
                    return df
                except UnicodeDecodeError as e:
                    last_err = e
                    continue
                except Exception as e:
                    last_err = e
                    continue

            # 如果所有编码都失败，使用默认编码并规范化列名，并尝试自动识别表头
            df = pd.read_csv(csv_path)
            def _canonical(x: object) -> str:
                s = str(x)
                for bad in ('\ufeff', '\u200b', '\xa0'):
                    s = s.replace(bad, ' ')
                s = s.strip().lower()
                s = re.sub(r'\s+', '_', s)
                s = re.sub(r'[^a-z0-9_]', '', s)
                if s == 'imagename':
                    s = 'image_name'
                return s
            df.columns = [_canonical(c) for c in df.columns]
            if 'image_name' not in df.columns:
                try:
                    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                        sample = f.read(4096)
                        f.seek(0)
                        try:
                            dialect = csv.Sniffer().sniff(sample)
                            delimiter = dialect.delimiter
                        except Exception:
                            delimiter = ','
                        reader = csv.reader(f, delimiter=delimiter)
                        header_row_idx = None
                        for i, row in enumerate(reader):
                            if i >= 50:
                                break
                            row_vals = [_canonical(v) for v in row]
                            if 'image_name' in row_vals:
                                header_row_idx = i
                                break
                    if header_row_idx is None:
                        try:
                            head_probe_df = pd.read_csv(csv_path, header=None, nrows=50, engine='python', sep=None)
                            for i in range(len(head_probe_df)):
                                row_vals = [_canonical(v) for v in list(head_probe_df.iloc[i].values)]
                                if 'image_name' in row_vals:
                                    header_row_idx = i
                                    break
                        except Exception as _e2:
                            logger.info(f"==liuq debug== 表头自动识别(默认编码, pandas探测)失败: {_e2}")
                    if header_row_idx is not None:
                        df = pd.read_csv(csv_path, header=header_row_idx, sep=delimiter)
                        df.columns = [_canonical(c) for c in df.columns]
                        logger.info(f"==liuq debug== 自动识别表头在第 {header_row_idx+1} 行(1-based), 分隔符: '{delimiter}'")
                    else:
                        logger.info("==liuq debug== 未能在前50行定位到 'image_name'，保留原始第一行作为表头")
                except Exception as _e:
                    logger.info(f"==liuq debug== 表头自动识别(默认编码)跳过: {_e}")
            logger.info(f"==liuq debug== 使用默认编码读取CSV文件: {csv_path}")
            return df

        except Exception as e:
            logger.error(f"==liuq debug== 读取CSV文件失败: {csv_path}, 错误: {e}")
            raise

    def _generate_analysis_data(self, matched_pairs, selected_fields):
        """生成分析数据"""
        try:
            analysis_data = {
                'matched_pairs': matched_pairs,
                'selected_fields': selected_fields,
                'trend_data': {},
                'statistics_data': {},
                'comparison_data': []
            }

            # 为每个字段生成趋势数据
            for field in selected_fields:
                test_values = []
                ref_values = []
                sequence_numbers = []

                for pair in matched_pairs:
                    test_data = pair.get('test_data', {})
                    ref_data = pair.get('reference_data', {})

                    if field in test_data and field in ref_data:
                        try:
                            # 将值安全转换为数值，空字符串/非法数值转为 NaN；0 保留为有效数值
                            import pandas as _pd
                            _v1 = _pd.to_numeric(_pd.Series([test_data[field]]), errors='coerce').iloc[0]
                            _v2 = _pd.to_numeric(_pd.Series([ref_data[field]]),  errors='coerce').iloc[0]
                            if _pd.notna(_v1) and _pd.notna(_v2):
                                test_val = float(_v1)
                                ref_val  = float(_v2)
                                test_values.append(test_val)
                                ref_values.append(ref_val)
                                sequence_numbers.append(pair.get('sequence_number', ''))
                            else:
                                # 任一侧为 NaN 则跳过该对
                                pass
                        except (Exception,):
                            # 跳过无法转换为数字的值
                            continue

                if test_values and ref_values:
                    # 计算差值和差值百分比
                    differences = [t - r for t, r in zip(test_values, ref_values)]
                    diff_percentages = []
                    for t, r in zip(test_values, ref_values):
                        if r != 0:
                            diff_percentages.append((t - r) / r * 100)
                        else:
                            diff_percentages.append(0)

                    analysis_data['trend_data'][field] = {
                        'test_values': test_values,
                        'reference_values': ref_values,
                        'differences': differences,
                        'diff_percentages': diff_percentages,
                        'sequence_numbers': sequence_numbers
                    }

                    # 统计数据
                    analysis_data['statistics_data'][field] = {
                        'test_mean': sum(test_values) / len(test_values),
                        'ref_mean': sum(ref_values) / len(ref_values),
                        'test_min': min(test_values),
                        'test_max': max(test_values),
                        'ref_min': min(ref_values),
                        'ref_max': max(ref_values),
                        'mean_diff': sum(differences) / len(differences),
                        'mean_diff_percentage': sum(diff_percentages) / len(diff_percentages)
                    }

            return analysis_data

        except Exception as e:
            logger.error(f"==liuq debug== 生成分析数据失败: {e}")
            raise

    def _generate_html_report(self, analysis_data, test_csv_path, reference_csv_path, output_path=None, matching_summary=None):
        """生成HTML报告"""
        try:
            from datetime import datetime

            if output_path is None:
                # 生成默认输出路径
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = output_dir / f"exif_comparison_report_{timestamp}.html"

            # 准备报告数据
            matched_pairs = analysis_data['matched_pairs']
            selected_fields = analysis_data['selected_fields']
            trend_data = analysis_data['trend_data']
            statistics_data = analysis_data['statistics_data']

            # 生成HTML内容
            html_content = self._generate_html_content(
                test_csv_path, reference_csv_path,
                matched_pairs, selected_fields,
                trend_data, statistics_data,
                matching_summary or {}
            )

            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # 方案A：将本地 Chart.js 写入 output/assets/chart.umd.min.js
            try:
                assets_dir = Path(output_path).parent / 'assets'
                assets_dir.mkdir(parents=True, exist_ok=True)
                vendor_srcs = [
                    Path('core')/ 'services' / 'vendor' / 'chart.umd.min.js',
                    Path('vendor') / 'chart.umd.min.js'
                ]
                src_file = None
                for p in vendor_srcs:
                    if p.exists():
                        src_file = p; break
                if src_file is None:
                    # 如果仓库内未内置，写入一个占位说明，依赖CDN回退
                    placeholder = assets_dir / 'chart.umd.min.js'
                    if not placeholder.exists():
                        placeholder.write_text("/* ==liuq debug== placeholder: Chart.js not bundled. CDN fallback will be used. */", encoding='utf-8')
                else:
                    target = assets_dir / 'chart.umd.min.js'
                    if not target.exists() or target.stat().st_size == 0:
                        target.write_bytes(src_file.read_bytes())
            except Exception as _e:
                logger.warning(f"==liuq debug== 复制本地Chart.js失败: {_e}")

            # 统一返回绝对路径，避免后续误用相对路径
            output_path = Path(output_path).resolve()
            logger.info(f"==liuq debug== HTML报告已保存: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"==liuq debug== 生成HTML报告失败: {e}")
            raise

    def _generate_html_content(self, test_csv_path, reference_csv_path, matched_pairs, selected_fields, trend_data, statistics_data, matching_summary=None):
        """生成HTML内容（增强版）"""
        from datetime import datetime
        matching_summary = matching_summary or {}

        # 基础HTML模板（使用双大括号转义），新增“匹配质量、KPI卡片、异常TopN”占位
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EXIF对比分析报告</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    {chart_loader_script}
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            margin: 0;
            padding: 0;
        }}
        .main-container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin: 20px;
            padding: 30px;
            min-height: calc(100vh - 40px);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border-radius: 10px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 300;
        }}
        .header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        h2 {{
            color: #667eea;
            margin-top: 40px;
            margin-bottom: 20px;
            font-weight: 400;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }}
        .summary {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 25px;
            border-radius: 10px;
            margin: 30px 0;
            border: 1px solid #dee2e6;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        .summary h3 {{
            color: #495057;
            margin-top: 0;
            margin-bottom: 20px;
            font-weight: 500;
        }}
        .chart-container {{
            margin: 30px 0;
            height: 400px;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }}
        th, td {{
            border: none;
            padding: 12px 15px;
            text-align: center;
        }}
        th {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #e3f2fd;
            transition: background-color 0.3s ease;
        }}
        .highlight-high {{
            background: linear-gradient(135deg, #ffebee, #ffcdd2) !important;
            color: #c62828;
        }}
        .highlight-medium {{
            background: linear-gradient(135deg, #fff3e0, #ffe0b2) !important;
            color: #ef6c00;
        }}
        .change-positive {{ color: #2e7d32; font-weight: 600; }}
        .change-negative {{ color: #d32f2f; font-weight: 600; }}
        .change-neutral {{ color: #616161; font-weight: 500; }}
        .table-container {{
            max-height: 500px;
            overflow: auto;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            position: relative;
        }}
        /* 固定列样式 - 文件名和序列号列 */
        .sticky-col {{
            position: sticky;
            left: 0;
            background: inherit;
            z-index: 10;
            border-right: 2px solid #dee2e6;
        }}
        .sticky-col-1 {{
            left: 0;
        }}
        .sticky-col-2 {{
            left: 220px; /* 第一列的宽度 + 边框 */
        }}
        /* 确保固定列的背景色与表头保持一致 */
        thead .sticky-col {{
            background: linear-gradient(45deg, #667eea, #764ba2) !important;
            color: white;
        }}
        tbody .sticky-col {{
            background: white;
        }}
        tbody tr:nth-child(even) .sticky-col {{
            background-color: #f8f9fa;
        }}
        tbody tr:hover .sticky-col {{
            background-color: #e3f2fd;
        }}
        .field-section {{
            margin: 40px 0;
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #e9ecef;
        }}
        .kpi-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .kpi-card {{
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }}
        .kpi-title {{
            color: #6c757d;
            font-size: 0.9rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}
        .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            margin: 10px 0;
            color: #495057;
        }}
        .muted {{
            color: #6c757d;
            font-size: 0.85rem;
            font-style: italic;
        }}
        .pill {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 15px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            font-size: 0.8rem;
            font-weight: 500;
            margin-left: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        @media (max-width: 768px) {{
            .main-container {{
                margin: 10px;
                padding: 20px;
            }}
            .kpi-cards {{
                grid-template-columns: 1fr;
            }}
            .header h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1><i class="fas fa-camera"></i> EXIF对比分析报告</h1>
            <p>生成时间: {generation_time}</p>
            <p>分析字段数量: {field_count} 个</p>
        </div>

        <div class="summary">
            <h3><i class="fas fa-info-circle"></i> 报告摘要</h3>
            <div class="row">
                <div class="col-md-6">
                    <p><strong><i class="fas fa-file-csv"></i> 测试机文件:</strong> {test_file}</p>
                    <p><strong><i class="fas fa-file-csv"></i> 对比机文件:</strong> {reference_file}</p>
                </div>
                <div class="col-md-6">
                    <p><strong><i class="fas fa-link"></i> 匹配场景数:</strong> {matched_count} <span class="pill">覆盖率 {match_rate}%</span> <span class="pill">方法 {match_method}</span></p>
                    <p class="muted"><i class="fas fa-exclamation-triangle"></i> 未匹配 测试机: {unmatched_test} | 对比机: {unmatched_reference}</p>
                </div>
            </div>
        </div>

        <h2><i class="fas fa-tachometer-alt"></i> 核心KPI总览</h2>
        {kpi_cards}

        <h2><i class="fas fa-chart-line"></i> 核心指标趋势图</h2>
        {trend_charts}

        <h2><i class="fas fa-chart-area"></i> 每张图片RpG/BpG对比分析</h2>
        {per_image_rpg_bpg_analysis}

        <h2><i class="fas fa-exclamation-triangle"></i> 异常样本 TopN</h2>
        {topn_table}

        <h2><i class="fas fa-table"></i> 详细数据对比表</h2>
        {comparison_table}

        <h2><i class="fas fa-chart-bar"></i> 统计摘要</h2>
        {statistics_table}
    </div>

    <script>
        {chart_scripts}
    </script>
</body>
</html>
        """

        # 准备数据
        test_file = Path(test_csv_path).name
        reference_file = Path(reference_csv_path).name
        matched_count = len(matched_pairs)
        field_count = len(selected_fields)
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        match_rate = round((matching_summary.get('match_rate', 0.0) * 100), 2)
        unmatched_test = matching_summary.get('unmatched_test', 0)
        unmatched_reference = matching_summary.get('unmatched_reference', 0)
        match_method = matching_summary.get('method', '-')

        # 导入辅助方法
        from .exif_report_helpers import (
            generate_trend_charts_html, generate_chart_scripts,
            generate_comparison_table, generate_statistics_table,
            generate_kpi_cards, generate_topn_anomaly_table,
            generate_per_image_rpg_bpg_analysis
        )

        # 生成增强内容
        trend_charts = generate_trend_charts_html(trend_data)
        chart_scripts = generate_chart_scripts(trend_data)
        comparison_table = generate_comparison_table(matched_pairs, selected_fields, trend_data)
        statistics_table = generate_statistics_table(statistics_data)
        kpi_cards = generate_kpi_cards(trend_data)
        topn_table = generate_topn_anomaly_table(trend_data)
        per_image_rpg_bpg_analysis = generate_per_image_rpg_bpg_analysis(trend_data)

        # 填充模板
        # 构造本地Chart加载脚本（优先内联，保证100%可用；失败则使用本地assets，再失败回退CDN）
        try:
            vendor_js = Path('core')/'services'/'vendor'/'chart.umd.min.js'
            if vendor_js.exists() and vendor_js.stat().st_size > 100000:
                code = vendor_js.read_text(encoding='utf-8', errors='ignore')
                chart_loader_script = '<script>' + code + '</script>'
            else:
                raise FileNotFoundError('vendor Chart.js missing or too small')
        except Exception as _e:
            chart_loader_script = (
                "<script>\n"
                "console.log('==liuq debug== 开始加载Chart.js');\n"
                "(function(){\n"
                "  var cdnUrls = [\n"
                "    'assets/chart.umd.min.js',\n"
                "    'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',\n"
                "    'https://unpkg.com/chart.js@4.4.1/dist/chart.umd.min.js',\n"
                "    'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js'\n"
                "  ];\n"
                "  var currentIndex = 0;\n"
                "  \n"
                "  function loadChart() {\n"
                "    if (currentIndex >= cdnUrls.length) {\n"
                "      console.error('==liuq debug== 所有Chart.js CDN都加载失败');\n"
                "      return;\n"
                "    }\n"
                "    \n"
                "    var url = cdnUrls[currentIndex];\n"
                "    console.log('==liuq debug== 尝试加载Chart.js:', url);\n"
                "    \n"
                "    var script = document.createElement('script');\n"
                "    script.src = url;\n"
                "    script.onload = function() {\n"
                "      console.log('==liuq debug== Chart.js加载成功:', url);\n"
                "      console.log('==liuq debug== Chart对象检查:', typeof Chart !== 'undefined' ? 'OK' : 'FAILED');\n"
                "    };\n"
                "    script.onerror = function() {\n"
                "      console.warn('==liuq debug== Chart.js加载失败:', url);\n"
                "      currentIndex++;\n"
                "      setTimeout(loadChart, 100);\n"
                "    };\n"
                "    \n"
                "    document.head.appendChild(script);\n"
                "  }\n"
                "  \n"
                "  loadChart();\n"
                "})();\n"
                "</script>"
            )

        html_content = html_template.format(
            test_file=test_file,
            reference_file=reference_file,
            matched_count=matched_count,
            field_count=field_count,
            generation_time=generation_time,
            match_rate=match_rate,
            unmatched_test=unmatched_test,
            unmatched_reference=unmatched_reference,
            match_method=match_method,
            kpi_cards=kpi_cards,
            trend_charts=trend_charts,
            per_image_rpg_bpg_analysis=per_image_rpg_bpg_analysis,
            topn_table=topn_table,
            comparison_table=comparison_table,
            statistics_table=statistics_table,
            chart_scripts=chart_scripts,
            chart_loader_script=chart_loader_script
        )

        return html_content
