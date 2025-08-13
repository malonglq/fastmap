#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML解析服务单元测试
==liuq debug== FastMapV2 XML解析服务测试

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 11:15:00 +08:00; Reason: P1-LD-005 实现XML解析服务; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 测试XML解析服务的功能
"""

import unittest
import tempfile
import xml.etree.ElementTree as ET
import logging
from pathlib import Path

from core.services.xml_parser_service import XMLParserService
from core.interfaces.xml_data_processor import ValidationLevel, XMLParseError
from core.models.map_data import MapConfiguration, MapPoint, BaseBoundary

logger = logging.getLogger(__name__)


class TestXMLParserService(unittest.TestCase):
    """XML解析服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.parser = XMLParserService()
        
        # 创建测试XML内容
        self.test_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <version>2.0</version>
    <device>test_device</device>
    <created>2025-07-28</created>
    <base_boundary>
        <rpg>0.5</rpg>
        <bpg>0.3</bpg>
    </base_boundary>
    <Maps>
        <Map>
            <AliasName>Indoor_BV_4000</AliasName>
            <x>100.5</x>
            <y>200.3</y>
            <offset>
                <x>100.5</x>
                <y>200.3</y>
            </offset>
            <weight>1.5</weight>
            <bv_range>10.0,90.0</bv_range>
            <ir_range>5.0,95.0</ir_range>
            <cct_range>2500.0,8000.0</cct_range>
            <detect_flag>true</detect_flag>
            <TransStep>1</TransStep>
        </Map>
        <Map>
            <AliasName>Outdoor_IR_2000</AliasName>
            <x>150.0</x>
            <y>250.0</y>
            <offset>
                <x>150.0</x>
                <y>250.0</y>
            </offset>
            <weight>2.0</weight>
            <bv_range>20.0,80.0</bv_range>
            <ir_range>10.0,90.0</ir_range>
            <cct_range>3000.0,7000.0</cct_range>
            <detect_flag>false</detect_flag>
            <TransStep>2</TransStep>
        </Map>
    </Maps>
</root>'''
    
    def create_test_xml_file(self, content: str = None) -> str:
        """创建测试XML文件"""
        if content is None:
            content = self.test_xml_content
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name
    
    def test_parse_xml_success(self):
        """测试成功解析XML"""
        xml_file = self.create_test_xml_file()
        
        try:
            config = self.parser.parse_xml(xml_file, "test")
            
            # 验证基本信息
            self.assertIsInstance(config, MapConfiguration)
            self.assertEqual(config.device_type, "test")
            self.assertIn('source_file', config.metadata)
            self.assertIn('parse_time', config.metadata)
            self.assertIn('total_points', config.metadata)
            
            # 验证基础边界
            self.assertIsInstance(config.base_boundary, BaseBoundary)
            self.assertEqual(config.base_boundary.rpg, 0.5)
            self.assertEqual(config.base_boundary.bpg, 0.3)
            
            # 验证Map点
            self.assertEqual(len(config.map_points), 2)
            
            # 验证Map点（按权重排序，权重高的在前）
            # 第一个Map点应该是权重2.0的Outdoor_IR_2000
            point1 = config.map_points[0]
            self.assertEqual(point1.alias_name, "Outdoor_IR_2000")
            self.assertEqual(point1.x, 150.0)
            self.assertEqual(point1.y, 250.0)
            self.assertEqual(point1.weight, 2.0)

            # 第二个Map点应该是权重1.5的Indoor_BV_4000
            point2 = config.map_points[1]
            self.assertEqual(point2.alias_name, "Indoor_BV_4000")
            self.assertEqual(point2.x, 100.5)
            self.assertEqual(point2.y, 200.3)
            self.assertEqual(point2.weight, 1.5)
            
        finally:
            Path(xml_file).unlink(missing_ok=True)
    
    def test_parse_xml_file_not_found(self):
        """测试文件不存在的情况"""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_xml("non_existent_file.xml")
    
    def test_parse_xml_invalid_format(self):
        """测试无效XML格式"""
        invalid_xml = "<?xml version='1.0'?><root><unclosed_tag></root>"
        xml_file = self.create_test_xml_file(invalid_xml)
        
        try:
            with self.assertRaises(XMLParseError):
                self.parser.parse_xml(xml_file)
        finally:
            Path(xml_file).unlink(missing_ok=True)
    
    def test_validate_xml_basic(self):
        """测试基础XML验证"""
        xml_file = self.create_test_xml_file()
        
        try:
            result = self.parser.validate_xml(xml_file, ValidationLevel.BASIC)
            
            self.assertTrue(result.is_valid)
            self.assertEqual(result.level, ValidationLevel.BASIC)
            self.assertEqual(len(result.errors), 0)
            
        finally:
            Path(xml_file).unlink(missing_ok=True)
    
    def test_validate_xml_structure(self):
        """测试结构XML验证"""
        xml_file = self.create_test_xml_file()
        
        try:
            result = self.parser.validate_xml(xml_file, ValidationLevel.STRUCTURE)
            
            self.assertTrue(result.is_valid)
            self.assertEqual(result.level, ValidationLevel.STRUCTURE)
            self.assertIn('root_tag', result.metadata)
            self.assertIn('element_count', result.metadata)
            
        finally:
            Path(xml_file).unlink(missing_ok=True)
    
    def test_validate_xml_content(self):
        """测试内容XML验证"""
        xml_file = self.create_test_xml_file()
        
        try:
            result = self.parser.validate_xml(xml_file, ValidationLevel.CONTENT)

            # 如果验证失败，打印错误信息以便调试
            if not result.is_valid:
                print(f"验证失败，错误: {result.errors}")
                print(f"警告: {result.warnings}")

            self.assertTrue(result.is_valid)
            self.assertEqual(result.level, ValidationLevel.CONTENT)
            self.assertIn('map_point_count', result.metadata)
            self.assertEqual(result.metadata['map_point_count'], 2)
            
        finally:
            Path(xml_file).unlink(missing_ok=True)
    
    def test_validate_xml_full(self):
        """测试完整XML验证"""
        xml_file = self.create_test_xml_file()
        
        try:
            result = self.parser.validate_xml(xml_file, ValidationLevel.FULL)
            
            self.assertTrue(result.is_valid)
            self.assertEqual(result.level, ValidationLevel.FULL)
            self.assertIn('root_tag', result.metadata)
            self.assertIn('element_count', result.metadata)
            self.assertIn('map_point_count', result.metadata)
            
        finally:
            Path(xml_file).unlink(missing_ok=True)
    
    def test_get_supported_versions(self):
        """测试获取支持的版本"""
        versions = self.parser.get_supported_versions()
        
        self.assertIsInstance(versions, list)
        self.assertIn("1.0", versions)
        self.assertIn("2.0", versions)
    
    def test_get_xml_metadata(self):
        """测试获取XML元数据"""
        xml_file = self.create_test_xml_file()
        
        try:
            metadata = self.parser.get_xml_metadata(xml_file)
            
            self.assertIsInstance(metadata, dict)
            self.assertIn('file_size', metadata)
            self.assertIn('file_name', metadata)
            self.assertIn('root_tag', metadata)
            self.assertIn('map_count', metadata)
            self.assertEqual(metadata['map_count'], 2)
            
        finally:
            Path(xml_file).unlink(missing_ok=True)
    
    def test_backup_xml(self):
        """测试XML备份功能"""
        xml_file = self.create_test_xml_file()
        
        try:
            backup_path = self.parser.backup_xml(xml_file)
            
            self.assertTrue(Path(backup_path).exists())
            self.assertIn('backup', backup_path)
            
            # 清理备份文件
            Path(backup_path).unlink(missing_ok=True)
            
        finally:
            Path(xml_file).unlink(missing_ok=True)
    
    def test_restore_from_backup(self):
        """测试从备份恢复"""
        xml_file = self.create_test_xml_file()
        
        try:
            # 创建备份
            backup_path = self.parser.backup_xml(xml_file)
            
            # 创建目标文件路径
            with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as f:
                target_path = f.name
            
            try:
                # 从备份恢复
                success = self.parser.restore_from_backup(backup_path, target_path)
                
                self.assertTrue(success)
                self.assertTrue(Path(target_path).exists())
                
                # 验证恢复的文件内容
                with open(target_path, 'r', encoding='utf-8') as f:
                    restored_content = f.read()
                
                self.assertIn('<root>', restored_content)
                self.assertIn('Indoor_BV_4000', restored_content)
                
            finally:
                Path(target_path).unlink(missing_ok=True)
                Path(backup_path).unlink(missing_ok=True)
                
        finally:
            Path(xml_file).unlink(missing_ok=True)
    
    def test_extract_base_boundary(self):
        """测试提取基础边界数据"""
        xml_content = '''<?xml version="1.0"?>
<root>
    <base_boundary>
        <rpg>1.5</rpg>
        <bpg>2.3</bpg>
    </base_boundary>
</root>'''
        
        root = ET.fromstring(xml_content)
        boundary = self.parser._extract_base_boundary(root)
        
        self.assertIsInstance(boundary, BaseBoundary)
        self.assertEqual(boundary.rpg, 1.5)
        self.assertEqual(boundary.bpg, 2.3)
    
    def test_extract_base_boundary_missing(self):
        """测试缺少基础边界数据的情况"""
        xml_content = '''<?xml version="1.0"?>
<root>
    <other_data>test</other_data>
</root>'''
        
        root = ET.fromstring(xml_content)
        boundary = self.parser._extract_base_boundary(root)
        
        self.assertIsInstance(boundary, BaseBoundary)
        self.assertEqual(boundary.rpg, 0.0)
        self.assertEqual(boundary.bpg, 0.0)
    
    def test_extract_map_point_data(self):
        """测试提取Map点数据"""
        map_xml = '''<Map>
    <AliasName>Test_Map</AliasName>
    <x>123.45</x>
    <y>678.90</y>
    <weight>2.5</weight>
</Map>'''
        
        map_elem = ET.fromstring(map_xml)
        data = self.parser._extract_map_point_data(map_elem)
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get('alias_name'), 'Test_Map')
        self.assertEqual(data.get('x'), 123.45)
        self.assertEqual(data.get('y'), 678.90)
        self.assertEqual(data.get('weight'), 2.5)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.DEBUG)
    
    # 运行测试
    unittest.main()
