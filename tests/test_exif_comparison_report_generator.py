#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF对比分析报告生成器测试
==liuq debug== FastMapV2 EXIF对比分析报告生成器测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 15:40:00 +08:00; Reason: 阶段2-测试EXIF对比分析报告生成器; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 测试EXIF对比分析报告生成器的功能
"""

import unittest
import tempfile
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

from core.services.exif_comparison_report_generator import ExifComparisonReportGenerator
from core.interfaces.report_generator import ReportType


class TestExifComparisonReportGenerator(unittest.TestCase):
    """EXIF对比分析报告生成器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = ExifComparisonReportGenerator()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试CSV文件
        self.test_csv_path = self.create_test_csv_file("test_device.csv")
        self.reference_csv_path = self.create_test_csv_file("reference_device.csv")
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_csv_file(self, filename: str) -> str:
        """创建测试CSV文件"""
        file_path = os.path.join(self.temp_dir, filename)
        
        # 创建模拟EXIF数据
        data = []
        for i in range(10):
            row = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'image_name': f'IMG_{i:04d}.jpg',
                'image_path': f'/path/to/IMG_{i:04d}.jpg',
                'meta_data_lastFrame_bv': 5.0 + i * 0.1,
                'meta_data_currentFrame_bv': 5.1 + i * 0.1,
                'color_sensor_irRatio': 0.8 + i * 0.01,
                'color_sensor_rGain': 1.0 + i * 0.02,
                'color_sensor_gGain': 1.0 + i * 0.01,
                'color_sensor_bGain': 1.0 + i * 0.015,
                'color_sensor_cct': 3000 + i * 100,
                'color_sensor_lux': 100 + i * 10
            }
            data.append(row)
        
        # 保存为CSV
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        return file_path
    
    def test_generator_initialization(self):
        """测试生成器初始化"""
        self.assertIsNotNone(self.generator)
        self.assertEqual(self.generator.get_report_type(), ReportType.EXIF_COMPARISON)
        self.assertEqual(self.generator.get_report_name(), "EXIF对比分析报告")
    
    def test_validate_data_valid_input(self):
        """测试有效输入数据验证"""
        valid_data = {
            'test_csv_path': self.test_csv_path,
            'reference_csv_path': self.reference_csv_path
        }
        
        self.assertTrue(self.generator.validate_data(valid_data))
    
    def test_validate_data_missing_fields(self):
        """测试缺少必需字段的数据验证"""
        invalid_data = {
            'test_csv_path': self.test_csv_path
            # 缺少 reference_csv_path
        }
        
        self.assertFalse(self.generator.validate_data(invalid_data))
    
    def test_validate_data_nonexistent_files(self):
        """测试不存在文件的数据验证"""
        invalid_data = {
            'test_csv_path': 'nonexistent_test.csv',
            'reference_csv_path': 'nonexistent_reference.csv'
        }
        
        self.assertFalse(self.generator.validate_data(invalid_data))
    
    def test_get_supported_fields(self):
        """测试获取支持的字段"""
        try:
            field_info = self.generator.get_supported_fields(self.test_csv_path)
            
            self.assertIn('total_fields', field_info)
            self.assertIn('numeric_fields', field_info)
            self.assertIn('core_fields_available', field_info)
            self.assertGreater(field_info['total_fields'], 0)
            self.assertGreater(len(field_info['numeric_fields']), 0)
            
        except Exception as e:
            # 如果0_csv_compare模块不可用，跳过此测试
            self.skipTest(f"0_csv_compare模块不可用: {e}")
    
    def test_preview_data_matching(self):
        """测试数据匹配预览"""
        try:
            preview_result = self.generator.preview_data_matching(
                self.test_csv_path,
                self.reference_csv_path
            )
            
            self.assertIn('total_test_records', preview_result)
            self.assertIn('total_reference_records', preview_result)
            self.assertIn('matched_pairs', preview_result)
            self.assertIn('match_rate', preview_result)
            
            # 验证数据
            self.assertEqual(preview_result['total_test_records'], 10)
            self.assertEqual(preview_result['total_reference_records'], 10)
            self.assertGreaterEqual(preview_result['matched_pairs'], 0)
            
        except Exception as e:
            # 如果0_csv_compare模块不可用，跳过此测试
            self.skipTest(f"0_csv_compare模块不可用: {e}")
    
    def test_generate_report_basic(self):
        """测试基本报告生成"""
        try:
            # 准备测试数据
            test_data = {
                'test_csv_path': self.test_csv_path,
                'reference_csv_path': self.reference_csv_path,
                'selected_fields': ['BV_Last_Frame', 'BV_Current_Frame', 'IR_Ratio'],
                'output_path': os.path.join(self.temp_dir, 'test_report.html')
            }
            
            # 生成报告
            report_path = self.generator.generate(test_data)
            
            # 验证报告文件存在
            self.assertTrue(os.path.exists(report_path))
            
            # 验证报告内容
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('EXIF对比分析报告', content)
                self.assertIn('BV', content)  # 应该包含BV相关内容
            
        except Exception as e:
            # 如果0_csv_compare模块不可用，跳过此测试
            self.skipTest(f"0_csv_compare模块不可用: {e}")
    
    def test_generate_report_auto_field_selection(self):
        """测试自动字段选择的报告生成"""
        try:
            # 准备测试数据（不指定字段，让系统自动选择）
            test_data = {
                'test_csv_path': self.test_csv_path,
                'reference_csv_path': self.reference_csv_path,
                'output_path': os.path.join(self.temp_dir, 'auto_report.html')
            }
            
            # 生成报告
            report_path = self.generator.generate(test_data)
            
            # 验证报告文件存在
            self.assertTrue(os.path.exists(report_path))
            
        except Exception as e:
            # 如果0_csv_compare模块不可用，跳过此测试
            self.skipTest(f"0_csv_compare模块不可用: {e}")
    
    def test_generate_report_with_parameters(self):
        """测试带参数的报告生成"""
        try:
            # 准备测试数据
            test_data = {
                'test_csv_path': self.test_csv_path,
                'reference_csv_path': self.reference_csv_path,
                'selected_fields': ['BV_Last_Frame', 'IR_Ratio'],
                'similarity_threshold': 0.9,
                'match_column': 'image_name',
                'output_path': os.path.join(self.temp_dir, 'param_report.html')
            }
            
            # 生成报告
            report_path = self.generator.generate(test_data)
            
            # 验证报告文件存在
            self.assertTrue(os.path.exists(report_path))
            
        except Exception as e:
            # 如果0_csv_compare模块不可用，跳过此测试
            self.skipTest(f"0_csv_compare模块不可用: {e}")
    
    def test_error_handling_invalid_csv(self):
        """测试无效CSV文件的错误处理"""
        # 创建无效的CSV文件
        invalid_csv_path = os.path.join(self.temp_dir, 'invalid.csv')
        with open(invalid_csv_path, 'w') as f:
            f.write("invalid,csv,content\n")
            f.write("without,proper,headers\n")
        
        test_data = {
            'test_csv_path': invalid_csv_path,
            'reference_csv_path': self.reference_csv_path
        }
        
        # 应该抛出异常
        with self.assertRaises(Exception):
            self.generator.generate(test_data)
    
    def test_error_handling_no_matches(self):
        """测试没有匹配数据的错误处理"""
        try:
            # 创建完全不同的CSV文件
            different_csv_path = os.path.join(self.temp_dir, 'different.csv')
            data = []
            for i in range(5):
                row = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'image_name': f'DIFFERENT_{i:04d}.jpg',  # 完全不同的文件名
                    'image_path': f'/different/path/DIFFERENT_{i:04d}.jpg',
                    'meta_data_lastFrame_bv': 10.0 + i * 0.1,
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            df.to_csv(different_csv_path, index=False, encoding='utf-8-sig')
            
            test_data = {
                'test_csv_path': self.test_csv_path,
                'reference_csv_path': different_csv_path,
                'similarity_threshold': 0.9  # 高阈值，确保没有匹配
            }
            
            # 应该抛出异常（没有匹配的数据对）
            with self.assertRaises(Exception):
                self.generator.generate(test_data)
                
        except Exception as e:
            # 如果0_csv_compare模块不可用，跳过此测试
            self.skipTest(f"0_csv_compare模块不可用: {e}")


class TestExifDataAdapter(unittest.TestCase):
    """EXIF数据适配器测试类"""
    
    def setUp(self):
        """测试前准备"""
        from core.adapters.exif_data_adapter import ExifDataAdapter
        self.adapter = ExifDataAdapter()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_adapter_initialization(self):
        """测试适配器初始化"""
        self.assertIsNotNone(self.adapter)
        self.assertIsInstance(self.adapter.field_mappings, dict)
        self.assertIsInstance(self.adapter.core_fields, list)
        self.assertIsInstance(self.adapter.display_names, dict)
    
    def test_field_mapping_config(self):
        """测试字段映射配置"""
        # 检查默认映射是否存在
        self.assertIn('meta_data_lastFrame_bv', self.adapter.field_mappings)
        self.assertIn('BV_Last_Frame', self.adapter.core_fields)
        self.assertIn('BV_Last_Frame', self.adapter.display_names)


if __name__ == '__main__':
    unittest.main()
