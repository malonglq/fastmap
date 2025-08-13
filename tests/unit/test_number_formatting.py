#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数值格式化功能测试

测试XML写入服务中的智能数值格式化函数
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.services.xml_writer_service import format_number_for_xml


class TestNumberFormatting(unittest.TestCase):
    """数值格式化测试类"""
    
    def test_integer_values(self):
        """测试整数值格式化"""
        # 整数应该显示为整数格式（不带小数点）
        self.assertEqual(format_number_for_xml(1.0), "1")
        self.assertEqual(format_number_for_xml(2.0), "2")
        self.assertEqual(format_number_for_xml(0.0), "0")
        self.assertEqual(format_number_for_xml(10.0), "10")
        self.assertEqual(format_number_for_xml(-1.0), "-1")
        self.assertEqual(format_number_for_xml(100.0), "100")
        
    def test_float_values(self):
        """测试小数值格式化"""
        # 小数应该保持小数格式
        self.assertEqual(format_number_for_xml(1.5), "1.5")
        self.assertEqual(format_number_for_xml(2.3), "2.3")
        self.assertEqual(format_number_for_xml(0.1), "0.1")
        self.assertEqual(format_number_for_xml(10.75), "10.75")
        self.assertEqual(format_number_for_xml(-1.5), "-1.5")
        self.assertEqual(format_number_for_xml(0.001), "0.001")
        
    def test_integer_input(self):
        """测试整数输入"""
        # 整数输入应该显示为整数格式
        self.assertEqual(format_number_for_xml(1), "1")
        self.assertEqual(format_number_for_xml(2), "2")
        self.assertEqual(format_number_for_xml(0), "0")
        self.assertEqual(format_number_for_xml(-1), "-1")
        
    def test_string_input(self):
        """测试字符串输入"""
        # 可转换的字符串应该正确格式化
        self.assertEqual(format_number_for_xml("1.0"), "1")
        self.assertEqual(format_number_for_xml("2.5"), "2.5")
        self.assertEqual(format_number_for_xml("0"), "0")
        self.assertEqual(format_number_for_xml("10.0"), "10")
        
    def test_none_input(self):
        """测试None输入"""
        # None应该返回"0"
        self.assertEqual(format_number_for_xml(None), "0")
        
    def test_invalid_input(self):
        """测试无效输入"""
        # 无效输入应该返回字符串形式
        self.assertEqual(format_number_for_xml("invalid"), "invalid")
        self.assertEqual(format_number_for_xml("abc"), "abc")
        
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试一些边界情况
        self.assertEqual(format_number_for_xml(0.0000001), "1e-7")  # 科学计数法（更简洁的格式）
        self.assertEqual(format_number_for_xml(1000000.0), "1000000")  # 大整数
        self.assertEqual(format_number_for_xml(1000000.5), "1000000.5")  # 大小数


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
