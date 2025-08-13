#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XML数值格式化直接测试

直接测试XML写入服务中的数值格式化功能
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.services.xml_writer_service import format_number_for_xml


class TestXMLFormattingDirect(unittest.TestCase):
    """XML数值格式化直接测试类"""
    
    def test_format_number_for_xml_comprehensive(self):
        """全面测试format_number_for_xml函数"""
        
        # 测试整数值（应该显示为整数格式）
        test_cases_integer = [
            (1.0, "1"),
            (2.0, "2"),
            (0.0, "0"),
            (10.0, "10"),
            (-1.0, "-1"),
            (100.0, "100"),
            (1000.0, "1000"),
            (2700.0, "2700"),
            (6500.0, "6500")
        ]
        
        for input_val, expected in test_cases_integer:
            with self.subTest(input_val=input_val):
                result = format_number_for_xml(input_val)
                self.assertEqual(result, expected, 
                    f"输入 {input_val} 应该格式化为 '{expected}'，实际为 '{result}'")
        
        # 测试小数值（应该保持小数格式）
        test_cases_decimal = [
            (1.5, "1.5"),
            (2.3, "2.3"),
            (0.1, "0.1"),
            (10.75, "10.75"),
            (-1.5, "-1.5"),
            (0.001, "0.001"),
            (1000.5, "1000.5"),
            (2700.3, "2700.3")
        ]
        
        for input_val, expected in test_cases_decimal:
            with self.subTest(input_val=input_val):
                result = format_number_for_xml(input_val)
                self.assertEqual(result, expected, 
                    f"输入 {input_val} 应该格式化为 '{expected}'，实际为 '{result}'")
    
    def test_xml_element_direct_formatting(self):
        """直接测试XML元素的数值格式化"""
        # 创建XML元素
        root = ET.Element("test")
        
        # 测试整数值
        weight_elem = ET.SubElement(root, "weight")
        weight_elem.text = format_number_for_xml(5.0)
        self.assertEqual(weight_elem.text, "5")
        
        # 测试小数值
        offset_x_elem = ET.SubElement(root, "offset_x")
        offset_x_elem.text = format_number_for_xml(10.5)
        self.assertEqual(offset_x_elem.text, "10.5")
        
        # 测试TransStep
        trans_step_elem = ET.SubElement(root, "trans_step")
        trans_step_elem.text = format_number_for_xml(3.0)
        self.assertEqual(trans_step_elem.text, "3")
        
        # 测试范围值
        bv_min_elem = ET.SubElement(root, "bv_min")
        bv_min_elem.text = format_number_for_xml(1000.0)
        self.assertEqual(bv_min_elem.text, "1000")
        
        bv_max_elem = ET.SubElement(root, "bv_max")
        bv_max_elem.text = format_number_for_xml(2000.5)
        self.assertEqual(bv_max_elem.text, "2000.5")
    
    def test_xml_serialization(self):
        """测试XML序列化后的格式"""
        # 创建XML结构
        root = ET.Element("test")
        
        # 添加各种数值类型
        values_to_test = [
            ("weight", 5.0, "5"),
            ("offset_x", 10.0, "10"),
            ("offset_y", 20.5, "20.5"),
            ("trans_step", 3.0, "3"),
            ("bv_min", 1000.0, "1000"),
            ("bv_max", 2000.0, "2000"),
            ("ir_min", 500.5, "500.5"),
            ("cct_min", 2700.0, "2700")
        ]
        
        for tag, value, expected in values_to_test:
            elem = ET.SubElement(root, tag)
            elem.text = format_number_for_xml(value)
        
        # 序列化为字符串
        xml_string = ET.tostring(root, encoding='unicode')
        
        # 验证每个值
        for tag, value, expected in values_to_test:
            with self.subTest(tag=tag, value=value):
                self.assertIn(f"<{tag}>{expected}</{tag}>", xml_string,
                    f"XML中应该包含 '<{tag}>{expected}</{tag}>'")
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试None值
        self.assertEqual(format_number_for_xml(None), "0")
        
        # 测试字符串输入
        self.assertEqual(format_number_for_xml("1.0"), "1")
        self.assertEqual(format_number_for_xml("2.5"), "2.5")
        
        # 测试整数输入
        self.assertEqual(format_number_for_xml(1), "1")
        self.assertEqual(format_number_for_xml(2), "2")
        
        # 测试无效输入
        self.assertEqual(format_number_for_xml("invalid"), "invalid")
    
    def test_weight_step_transstep_formatting(self):
        """专门测试Weight、Step、TransStep字段的格式化"""
        # 这些是需求中明确提到的字段
        
        # Weight字段测试
        weight_cases = [
            (1.0, "1"),
            (2.0, "2"),
            (0.0, "0"),
            (1.5, "1.5"),
            (2.3, "2.3")
        ]
        
        for weight, expected in weight_cases:
            with self.subTest(field="weight", value=weight):
                result = format_number_for_xml(weight)
                self.assertEqual(result, expected,
                    f"Weight {weight} 应该格式化为 '{expected}'，实际为 '{result}'")
        
        # TransStep字段测试
        trans_step_cases = [
            (0.0, "0"),
            (1.0, "1"),
            (5.0, "5"),
            (10.0, "10"),
            (1.5, "1.5")  # 如果TransStep可能是小数
        ]
        
        for trans_step, expected in trans_step_cases:
            with self.subTest(field="trans_step", value=trans_step):
                result = format_number_for_xml(trans_step)
                self.assertEqual(result, expected,
                    f"TransStep {trans_step} 应该格式化为 '{expected}'，实际为 '{result}'")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
