#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一报告管理器测试
==liuq debug== FastMapV2统一报告管理器测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 14:45:00 +08:00; Reason: 阶段1基础架构重构-测试统一报告管理器; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 测试统一报告管理器的基本功能
"""

import unittest
import tempfile
import os
from typing import Dict, Any

from core.services.unified_report_manager import UnifiedReportManager, ReportHistoryItem
from core.interfaces.report_generator import IReportGenerator, ReportType


class MockReportGenerator(IReportGenerator):
    """模拟报告生成器"""
    
    def __init__(self, report_type: ReportType, report_name: str):
        self.report_type = report_type
        self.report_name = report_name
    
    def generate(self, data: Dict[str, Any]) -> str:
        """生成模拟报告"""
        # 创建临时文件作为报告
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(f"<html><body><h1>{self.report_name}</h1></body></html>")
            return f.name
    
    def get_report_name(self) -> str:
        """获取报告名称"""
        return self.report_name
    
    def get_report_type(self) -> ReportType:
        """获取报告类型"""
        return self.report_type
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据"""
        return True  # 简单验证，总是返回True


class TestUnifiedReportManager(unittest.TestCase):
    """统一报告管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 使用临时文件作为历史记录文件
        self.temp_history_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_history_file.close()
        
        # 创建报告管理器
        self.manager = UnifiedReportManager(history_file=self.temp_history_file.name)
        
        # 创建模拟报告生成器
        self.exif_generator = MockReportGenerator(
            ReportType.EXIF_COMPARISON, 
            "EXIF对比分析报告"
        )
        self.map_generator = MockReportGenerator(
            ReportType.MAP_MULTI_DIMENSIONAL, 
            "Map多维度分析报告"
        )
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时文件
        if os.path.exists(self.temp_history_file.name):
            os.unlink(self.temp_history_file.name)
    
    def test_register_generator(self):
        """测试注册报告生成器"""
        # 注册生成器
        self.manager.register_generator(self.exif_generator)
        self.manager.register_generator(self.map_generator)
        
        # 检查可用报告类型
        available_types = self.manager.get_available_report_types()
        self.assertIn(ReportType.EXIF_COMPARISON, available_types)
        self.assertIn(ReportType.MAP_MULTI_DIMENSIONAL, available_types)
        self.assertEqual(len(available_types), 2)
    
    def test_unregister_generator(self):
        """测试注销报告生成器"""
        # 先注册
        self.manager.register_generator(self.exif_generator)
        self.manager.register_generator(self.map_generator)
        
        # 注销一个
        self.manager.unregister_generator(ReportType.EXIF_COMPARISON)
        
        # 检查结果
        available_types = self.manager.get_available_report_types()
        self.assertNotIn(ReportType.EXIF_COMPARISON, available_types)
        self.assertIn(ReportType.MAP_MULTI_DIMENSIONAL, available_types)
        self.assertEqual(len(available_types), 1)
    
    def test_generate_report(self):
        """测试生成报告"""
        # 注册生成器
        self.manager.register_generator(self.exif_generator)
        
        # 生成报告
        test_data = {"test": "data"}
        report_path = self.manager.generate_report(
            ReportType.EXIF_COMPARISON, 
            test_data
        )
        
        # 检查报告文件是否存在
        self.assertTrue(os.path.exists(report_path))
        
        # 检查历史记录
        history = self.manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].report_type, ReportType.EXIF_COMPARISON)
        self.assertEqual(history[0].report_name, "EXIF对比分析报告")
        
        # 清理生成的文件
        os.unlink(report_path)
    
    def test_generate_report_unsupported_type(self):
        """测试生成不支持的报告类型"""
        with self.assertRaises(ValueError):
            self.manager.generate_report(
                ReportType.RESERVED, 
                {"test": "data"}
            )
    
    def test_history_management(self):
        """测试历史记录管理"""
        # 注册生成器
        self.manager.register_generator(self.exif_generator)
        self.manager.register_generator(self.map_generator)
        
        # 生成多个报告
        report_paths = []
        for i in range(3):
            report_type = ReportType.EXIF_COMPARISON if i % 2 == 0 else ReportType.MAP_MULTI_DIMENSIONAL
            path = self.manager.generate_report(report_type, {"test": f"data_{i}"})
            report_paths.append(path)
        
        # 检查历史记录
        history = self.manager.get_history()
        self.assertEqual(len(history), 3)
        
        # 检查按类型过滤
        exif_history = self.manager.get_history(report_type=ReportType.EXIF_COMPARISON)
        self.assertEqual(len(exif_history), 2)
        
        map_history = self.manager.get_history(report_type=ReportType.MAP_MULTI_DIMENSIONAL)
        self.assertEqual(len(map_history), 1)
        
        # 检查限制数量
        limited_history = self.manager.get_history(limit=2)
        self.assertEqual(len(limited_history), 2)
        
        # 清空历史记录
        self.manager.clear_history()
        history = self.manager.get_history()
        self.assertEqual(len(history), 0)
        
        # 清理生成的文件
        for path in report_paths:
            if os.path.exists(path):
                os.unlink(path)
    
    def test_get_generator_info(self):
        """测试获取生成器信息"""
        # 注册生成器
        self.manager.register_generator(self.exif_generator)
        
        # 获取信息
        info = self.manager.get_generator_info(ReportType.EXIF_COMPARISON)
        self.assertIsNotNone(info)
        self.assertEqual(info['type'], ReportType.EXIF_COMPARISON.value)
        self.assertEqual(info['name'], "EXIF对比分析报告")
        self.assertEqual(info['class'], "MockReportGenerator")
        
        # 获取不存在的生成器信息
        info = self.manager.get_generator_info(ReportType.RESERVED)
        self.assertIsNone(info)


if __name__ == '__main__':
    unittest.main()
