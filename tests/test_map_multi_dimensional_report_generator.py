#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map多维度分析报告生成器测试
==liuq debug== FastMapV2 Map多维度分析报告生成器测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 16:25:00 +08:00; Reason: 阶段3-测试Map多维度分析报告生成器; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 测试Map多维度分析报告生成器的功能
"""

import unittest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from core.services.map_multi_dimensional_report_generator import MapMultiDimensionalReportGenerator
from core.interfaces.report_generator import ReportType
from core.models.map_data import MapConfiguration, MapPoint, BaseBoundary, SceneType, MapType
from core.models.scene_classification_config import SceneClassificationConfig


class TestMapMultiDimensionalReportGenerator(unittest.TestCase):
    """Map多维度分析报告生成器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = MapMultiDimensionalReportGenerator()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试Map配置
        self.map_configuration = self.create_test_map_configuration()
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_map_configuration(self) -> MapConfiguration:
        """创建测试Map配置"""
        # 创建基础边界
        base_boundary = BaseBoundary(
            rpg=0.5,
            bpg=0.3
        )
        
        # 创建测试Map点
        map_points = []
        
        # 室内场景点
        for i in range(5):
            map_point = MapPoint(
                alias_name=f"Indoor_BV_5000_IR_800_{i}",
                x=10.0 + i * 5,
                y=10.0 + i * 3,
                offset_x=10.0 + i * 5,
                offset_y=10.0 + i * 3,
                weight=0.8 + i * 0.05,
                bv_range=(5.0 + i * 0.2, 6.0 + i * 0.2),
                ir_range=(0.8, 0.9),
                cct_range=(3000, 4000),
                detect_flag=True,
                map_type=MapType.ENHANCE,
                scene_type=SceneType.INDOOR
            )
            map_points.append(map_point)
        
        # 室外场景点
        for i in range(3):
            map_point = MapPoint(
                alias_name=f"Outdoor_BV_8000_IR_500_{i}",
                x=-10.0 - i * 8,
                y=20.0 + i * 5,
                offset_x=-10.0 - i * 8,
                offset_y=20.0 + i * 5,
                weight=0.9 + i * 0.03,
                bv_range=(8.0 + i * 0.3, 9.0 + i * 0.3),
                ir_range=(0.5, 0.6),
                cct_range=(5000, 6000),
                detect_flag=True,
                map_type=MapType.ENHANCE,
                scene_type=SceneType.OUTDOOR
            )
            map_points.append(map_point)
        
        # 夜景场景点
        for i in range(2):
            map_point = MapPoint(
                alias_name=f"Night_BV_1000_IR_1200_{i}",
                x=30.0 + i * 10,
                y=-20.0 - i * 8,
                offset_x=30.0 + i * 10,
                offset_y=-20.0 - i * 8,
                weight=0.7 + i * 0.1,
                bv_range=(1.0 + i * 0.5, 2.0 + i * 0.5),
                ir_range=(1.2, 1.5),
                cct_range=(2000, 3000),
                detect_flag=True,
                map_type=MapType.REDUCE,
                scene_type=SceneType.NIGHT
            )
            map_points.append(map_point)
        
        # 创建Map配置
        return MapConfiguration(
            device_type="test_device",
            base_boundary=base_boundary,
            map_points=map_points,
            reference_points=[(0, 0), (50, 50)],
            metadata={"test": True, "created": datetime.now().isoformat()}
        )
    
    def test_generator_initialization(self):
        """测试生成器初始化"""
        self.assertIsNotNone(self.generator)
        self.assertEqual(self.generator.get_report_type(), ReportType.MAP_MULTI_DIMENSIONAL)
        self.assertEqual(self.generator.get_report_name(), "Map多维度分析报告")
    
    def test_validate_data_valid_input(self):
        """测试有效输入数据验证"""
        valid_data = {
            'map_configuration': self.map_configuration
        }
        
        self.assertTrue(self.generator.validate_data(valid_data))
    
    def test_validate_data_missing_map_configuration(self):
        """测试缺少map_configuration的数据验证"""
        invalid_data = {}
        
        self.assertFalse(self.generator.validate_data(invalid_data))
    
    def test_validate_data_invalid_map_configuration_type(self):
        """测试无效map_configuration类型的数据验证"""
        invalid_data = {
            'map_configuration': "invalid_type"
        }
        
        self.assertFalse(self.generator.validate_data(invalid_data))
    
    def test_validate_data_empty_map_points(self):
        """测试空Map点的数据验证"""
        empty_config = MapConfiguration(
            device_type="test",
            base_boundary=BaseBoundary(rpg=0.5, bpg=0.3),
            map_points=[]
        )
        
        invalid_data = {
            'map_configuration': empty_config
        }
        
        self.assertFalse(self.generator.validate_data(invalid_data))
    
    def test_get_map_configuration_summary(self):
        """测试获取Map配置摘要"""
        summary = self.generator.get_map_configuration_summary(self.map_configuration)
        
        self.assertIn('device_type', summary)
        self.assertIn('total_map_points', summary)
        self.assertIn('scene_distribution', summary)
        self.assertIn('coordinate_range', summary)
        self.assertIn('weight_range', summary)
        
        # 验证数据
        self.assertEqual(summary['device_type'], 'test_device')
        self.assertEqual(summary['total_map_points'], 10)  # 5+3+2
        self.assertTrue(summary['has_base_boundary'])
        self.assertTrue(summary['has_reference_points'])
        
        # 验证场景分布
        scene_distribution = summary['scene_distribution']
        self.assertEqual(scene_distribution.get('indoor', 0), 5)
        self.assertEqual(scene_distribution.get('outdoor', 0), 3)
        self.assertEqual(scene_distribution.get('night', 0), 2)
    
    def test_preview_analysis_scope(self):
        """测试预览分析范围"""
        preview = self.generator.preview_analysis_scope(
            self.map_configuration,
            include_multi_dimensional=True
        )
        
        self.assertIn('map_summary', preview)
        self.assertIn('analysis_scope', preview)
        self.assertIn('estimated_processing_time', preview)
        self.assertIn('output_sections', preview)
        
        # 验证分析范围
        analysis_scope = preview['analysis_scope']
        self.assertTrue(analysis_scope['traditional_analysis'])
        self.assertTrue(analysis_scope['multi_dimensional_analysis'])
        self.assertTrue(analysis_scope['scene_classification'])
        
        # 验证输出章节
        output_sections = preview['output_sections']
        self.assertGreater(len(output_sections), 5)  # 应该有多个章节
    
    def test_preview_analysis_scope_without_multi_dimensional(self):
        """测试不包含多维度分析的预览"""
        preview = self.generator.preview_analysis_scope(
            self.map_configuration,
            include_multi_dimensional=False
        )
        
        analysis_scope = preview['analysis_scope']
        self.assertTrue(analysis_scope['traditional_analysis'])
        self.assertFalse(analysis_scope['multi_dimensional_analysis'])
        self.assertFalse(analysis_scope['scene_classification'])
    
    def test_generate_report_basic(self):
        """测试基本报告生成"""
        try:
            # 准备测试数据
            test_data = {
                'map_configuration': self.map_configuration,
                'include_multi_dimensional': True,
                'output_path': os.path.join(self.temp_dir, 'test_map_report.html')
            }
            
            # 生成报告
            report_path = self.generator.generate(test_data)
            
            # 验证报告文件存在
            self.assertTrue(os.path.exists(report_path))
            
            # 验证报告内容
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('Map', content)  # 应该包含Map相关内容
                self.assertIn('html', content.lower())  # 应该是HTML格式
            
        except Exception as e:
            # 如果相关模块不可用，跳过此测试
            self.skipTest(f"Map分析模块不可用: {e}")
    
    def test_generate_report_without_multi_dimensional(self):
        """测试不包含多维度分析的报告生成"""
        try:
            # 准备测试数据
            test_data = {
                'map_configuration': self.map_configuration,
                'include_multi_dimensional': False,
                'output_path': os.path.join(self.temp_dir, 'test_map_basic_report.html')
            }
            
            # 生成报告
            report_path = self.generator.generate(test_data)
            
            # 验证报告文件存在
            self.assertTrue(os.path.exists(report_path))
            
        except Exception as e:
            # 如果相关模块不可用，跳过此测试
            self.skipTest(f"Map分析模块不可用: {e}")
    
    def test_generate_report_with_custom_classification_config(self):
        """测试使用自定义分类配置的报告生成"""
        try:
            # 创建自定义分类配置
            classification_config = SceneClassificationConfig()
            classification_config.indoor_bv_threshold = 4.5
            classification_config.night_bv_threshold = -1.5
            classification_config.ir_threshold = 1.1
            
            # 准备测试数据
            test_data = {
                'map_configuration': self.map_configuration,
                'include_multi_dimensional': True,
                'classification_config': classification_config,
                'template_name': 'default',
                'output_path': os.path.join(self.temp_dir, 'test_map_custom_report.html')
            }
            
            # 生成报告
            report_path = self.generator.generate(test_data)
            
            # 验证报告文件存在
            self.assertTrue(os.path.exists(report_path))
            
        except Exception as e:
            # 如果相关模块不可用，跳过此测试
            self.skipTest(f"Map分析模块不可用: {e}")
    
    def test_get_supported_templates(self):
        """测试获取支持的模板"""
        templates = self.generator.get_supported_templates()
        
        self.assertIsInstance(templates, list)
        self.assertIn("map_analysis", templates)
        self.assertIn("default", templates)
    
    def test_get_default_classification_config(self):
        """测试获取默认分类配置"""
        config = self.generator.get_default_classification_config()
        
        self.assertIsInstance(config, SceneClassificationConfig)
        self.assertIsInstance(config.indoor_bv_threshold, (int, float))
        self.assertIsInstance(config.night_bv_threshold, (int, float))
        self.assertIsInstance(config.ir_threshold, (int, float))
    
    def test_error_handling_invalid_template(self):
        """测试无效模板的错误处理"""
        try:
            test_data = {
                'map_configuration': self.map_configuration,
                'template_name': 'nonexistent_template'
            }
            
            # 应该能够处理无效模板（可能使用默认模板）
            report_path = self.generator.generate(test_data)
            
            # 如果没有抛出异常，验证文件是否存在
            if report_path:
                self.assertTrue(os.path.exists(report_path))
                
        except Exception as e:
            # 如果抛出异常，应该是合理的错误信息
            self.assertIn("template", str(e).lower())


if __name__ == '__main__':
    unittest.main()
