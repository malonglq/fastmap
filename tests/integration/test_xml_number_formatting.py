#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XML数值格式化集成测试

测试XML写入服务中的数值格式化功能是否正确应用到实际的XML文件中
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.services.xml_writer_service import XMLWriterService, format_number_for_xml
from core.services.xml_parser_service import XMLParserService
from core.models.map_data import MapPoint, MapConfiguration, BaseBoundary, SceneType, MapType


class TestXMLNumberFormatting(unittest.TestCase):
    """XML数值格式化集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.writer = XMLWriterService()
        self.parser = XMLParserService()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.temp_xml_path = Path(self.temp_dir) / "test_formatting.xml"
        
        # 创建测试用的XML内容
        self.create_test_xml()
        
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        if self.temp_xml_path.exists():
            self.temp_xml_path.unlink()
        os.rmdir(self.temp_dir)
    
    def create_test_xml(self):
        """创建测试用的XML文件"""
        xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<root>
    <offset_map0>
        <offset>
            <x>1.0</x>
            <y>2.0</y>
        </offset>
        <weight>3.0</weight>
        <range>
            <bv>
                <min>1000.0</min>
                <max>2000.0</max>
            </bv>
            <ir>
                <min>500.0</min>
                <max>1500.0</max>
            </ir>
            <colorCCT>
                <min>2700.0</min>
                <max>6500.0</max>
            </colorCCT>
            <DetectMapFlag>1</DetectMapFlag>
        </range>
    </offset_map0>
    <offset_map0>
        <AliasName>Test_Point</AliasName>
        <TransStep>5.0</TransStep>
    </offset_map0>
</root>'''
        
        with open(self.temp_xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
    
    def test_format_number_for_xml_function(self):
        """测试format_number_for_xml函数"""
        # 测试整数值
        self.assertEqual(format_number_for_xml(1.0), "1")
        self.assertEqual(format_number_for_xml(2.0), "2")
        self.assertEqual(format_number_for_xml(0.0), "0")
        
        # 测试小数值
        self.assertEqual(format_number_for_xml(1.5), "1.5")
        self.assertEqual(format_number_for_xml(2.3), "2.3")
        
        # 测试整数输入
        self.assertEqual(format_number_for_xml(1), "1")
        self.assertEqual(format_number_for_xml(2), "2")
        
    def test_xml_writing_with_integer_formatting(self):
        """测试XML写入时的整数格式化"""
        # 解析现有XML
        config = self.parser.parse_xml(self.temp_xml_path, "test")
        self.assertIsInstance(config, MapConfiguration)

        print(f"==liuq debug== 解析到的map_points数量: {len(config.map_points) if config.map_points else 0}")

        # 修改数值为整数值
        if config.map_points:
            map_point = config.map_points[0]
            print(f"==liuq debug== 修改前: weight={map_point.weight}, offset_x={map_point.offset_x}")

            map_point.weight = 5.0  # 应该显示为 "5"
            map_point.offset_x = 10.0  # 应该显示为 "10"
            map_point.offset_y = 20.0  # 应该显示为 "20"
            map_point.trans_step = 3.0  # 应该显示为 "3"

            # 修改范围值为整数
            map_point.bv_range = (1000.0, 2000.0)  # 应该显示为 "1000", "2000"
            map_point.ir_range = (500.0, 1500.0)   # 应该显示为 "500", "1500"
            map_point.cct_range = (2700.0, 6500.0) # 应该显示为 "2700", "6500"

            print(f"==liuq debug== 修改后: weight={map_point.weight}, offset_x={map_point.offset_x}")
        else:
            print("==liuq debug== 没有找到map_points，跳过测试")
            self.skipTest("没有找到map_points")

        # 写入XML
        success = self.writer.write_xml(config, self.temp_xml_path, backup=False)
        self.assertTrue(success)

        # 验证XML内容
        self.verify_xml_integer_formatting()
    
    def test_xml_writing_with_decimal_formatting(self):
        """测试XML写入时的小数格式化"""
        # 解析现有XML
        config = self.parser.parse_xml(self.temp_xml_path, "test")
        self.assertIsInstance(config, MapConfiguration)
        
        # 修改数值为小数值
        if config.map_points:
            map_point = config.map_points[0]
            map_point.weight = 5.5  # 应该显示为 "5.5"
            map_point.offset_x = 10.3  # 应该显示为 "10.3"
            map_point.offset_y = 20.7  # 应该显示为 "20.7"
            
            # 修改范围值为小数
            map_point.bv_range = (1000.5, 2000.3)  # 应该显示为 "1000.5", "2000.3"
        
        # 写入XML
        success = self.writer.write_xml(config, self.temp_xml_path, backup=False)
        self.assertTrue(success)
        
        # 验证XML内容
        self.verify_xml_decimal_formatting()
    
    def verify_xml_integer_formatting(self):
        """验证XML中的整数格式化"""
        tree = ET.parse(self.temp_xml_path)
        root = tree.getroot()
        
        # 检查weight字段
        weight_elem = root.find('.//weight')
        if weight_elem is not None:
            self.assertEqual(weight_elem.text, "5", f"Weight应该显示为'5'，实际为'{weight_elem.text}'")
        
        # 检查offset坐标
        x_elem = root.find('.//offset/x')
        if x_elem is not None:
            self.assertEqual(x_elem.text, "10", f"Offset X应该显示为'10'，实际为'{x_elem.text}'")
        
        y_elem = root.find('.//offset/y')
        if y_elem is not None:
            self.assertEqual(y_elem.text, "20", f"Offset Y应该显示为'20'，实际为'{y_elem.text}'")
        
        # 检查范围值
        bv_min_elem = root.find('.//bv/min')
        if bv_min_elem is not None:
            self.assertEqual(bv_min_elem.text, "1000", f"BV Min应该显示为'1000'，实际为'{bv_min_elem.text}'")
        
        bv_max_elem = root.find('.//bv/max')
        if bv_max_elem is not None:
            self.assertEqual(bv_max_elem.text, "2000", f"BV Max应该显示为'2000'，实际为'{bv_max_elem.text}'")
    
    def verify_xml_decimal_formatting(self):
        """验证XML中的小数格式化"""
        tree = ET.parse(self.temp_xml_path)
        root = tree.getroot()
        
        # 检查weight字段
        weight_elem = root.find('.//weight')
        if weight_elem is not None:
            self.assertEqual(weight_elem.text, "5.5", f"Weight应该显示为'5.5'，实际为'{weight_elem.text}'")
        
        # 检查offset坐标
        x_elem = root.find('.//offset/x')
        if x_elem is not None:
            self.assertEqual(x_elem.text, "10.3", f"Offset X应该显示为'10.3'，实际为'{x_elem.text}'")
        
        y_elem = root.find('.//offset/y')
        if y_elem is not None:
            self.assertEqual(y_elem.text, "20.7", f"Offset Y应该显示为'20.7'，实际为'{y_elem.text}'")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
