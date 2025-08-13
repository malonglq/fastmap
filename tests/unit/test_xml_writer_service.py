#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML写入服务单元测试
==liuq debug== FastMapV2 XML写入服务测试

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 14:45:00 +08:00; Reason: P1-LD-006-007 编写测试用例; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 测试XML写入服务的功能
"""

import unittest
import tempfile
import xml.etree.ElementTree as ET
import logging
from pathlib import Path

from core.services.xml_writer_service import XMLWriterService
from core.services.xml_parser_service import XMLParserService
from core.interfaces.xml_data_processor import ValidationLevel, XMLWriteError
from core.models.map_data import MapConfiguration, MapPoint, BaseBoundary

logger = logging.getLogger(__name__)


class TestXMLWriterService(unittest.TestCase):
    """XML写入服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.writer = XMLWriterService()
        self.parser = XMLParserService()
        
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp())
        self.temp_xml_path = self.temp_dir / "test_map.xml"
        
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
        
        # 写入测试XML文件
        with open(self.temp_xml_path, 'w', encoding='utf-8') as f:
            f.write(self.test_xml_content)
        
        logger.info(f"==liuq debug== 测试环境准备完成: {self.temp_xml_path}")
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        logger.info("==liuq debug== 测试环境清理完成")
    
    def test_xml_writer_service_initialization(self):
        """测试XML写入服务初始化"""
        logger.info("==liuq debug== 测试XML写入服务初始化")
        
        self.assertIsInstance(self.writer, XMLWriterService)
        self.assertEqual(self.writer.supported_versions, ["1.0", "1.1", "2.0"])
        self.assertEqual(self.writer.default_encoding, "utf-8")
        self.assertIsInstance(self.writer.field_definitions, list)
    
    def test_get_supported_versions(self):
        """测试获取支持的版本列表"""
        logger.info("==liuq debug== 测试获取支持的版本列表")
        
        versions = self.writer.get_supported_versions()
        self.assertIsInstance(versions, list)
        self.assertIn("2.0", versions)
        self.assertGreaterEqual(len(versions), 1)
    
    def test_validate_xml_basic(self):
        """测试基础XML验证"""
        logger.info("==liuq debug== 测试基础XML验证")
        
        result = self.writer.validate_xml(self.temp_xml_path, ValidationLevel.BASIC)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_xml_full(self):
        """测试完整XML验证"""
        logger.info("==liuq debug== 测试完整XML验证")
        
        result = self.writer.validate_xml(self.temp_xml_path, ValidationLevel.FULL)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_xml_nonexistent_file(self):
        """测试验证不存在的文件"""
        logger.info("==liuq debug== 测试验证不存在的文件")
        
        nonexistent_path = self.temp_dir / "nonexistent.xml"
        result = self.writer.validate_xml(nonexistent_path)
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_get_xml_metadata(self):
        """测试获取XML元数据"""
        logger.info("==liuq debug== 测试获取XML元数据")
        
        metadata = self.writer.get_xml_metadata(self.temp_xml_path)
        self.assertIsInstance(metadata, dict)
        self.assertIn("file_path", metadata)
        self.assertIn("file_size", metadata)
        self.assertIn("root_tag", metadata)
        self.assertEqual(metadata["root_tag"], "root")
    
    def test_backup_xml(self):
        """测试XML备份功能"""
        logger.info("==liuq debug== 测试XML备份功能")
        
        backup_path = self.writer.backup_xml(self.temp_xml_path)
        self.assertTrue(Path(backup_path).exists())
        
        # 验证备份文件内容
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        
        with open(self.temp_xml_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        self.assertEqual(backup_content, original_content)
    
    def test_restore_from_backup(self):
        """测试从备份恢复"""
        logger.info("==liuq debug== 测试从备份恢复")
        
        # 创建备份
        backup_path = self.writer.backup_xml(self.temp_xml_path)
        
        # 修改原文件
        with open(self.temp_xml_path, 'w', encoding='utf-8') as f:
            f.write("modified content")
        
        # 从备份恢复
        success = self.writer.restore_from_backup(backup_path, self.temp_xml_path)
        self.assertTrue(success)
        
        # 验证恢复内容
        with open(self.temp_xml_path, 'r', encoding='utf-8') as f:
            restored_content = f.read()
        
        self.assertIn("<?xml version", restored_content)
        self.assertIn("<root>", restored_content)
    
    def test_write_xml_basic_functionality(self):
        """测试XML写入基本功能"""
        logger.info("==liuq debug== 测试XML写入基本功能")
        
        # 首先解析XML文件
        config = self.parser.parse_xml(self.temp_xml_path, "test")
        self.assertIsInstance(config, MapConfiguration)
        
        # 修改配置数据
        if config.map_points:
            config.map_points[0].weight = 3.0
            config.map_points[0].alias_name = "Modified_Test_Point"
        
        # 写入XML文件
        success = self.writer.write_xml(config, self.temp_xml_path, backup=True)
        self.assertTrue(success)
        
        # 验证写入结果
        self.assertTrue(self.temp_xml_path.exists())
        
        # 重新解析验证
        updated_config = self.parser.parse_xml(self.temp_xml_path, "test")
        if updated_config.map_points:
            self.assertEqual(updated_config.map_points[0].weight, 3.0)
            self.assertEqual(updated_config.map_points[0].alias_name, "Modified_Test_Point")
    
    def test_write_xml_with_backup(self):
        """测试带备份的XML写入"""
        logger.info("==liuq debug== 测试带备份的XML写入")
        
        # 解析配置
        config = self.parser.parse_xml(self.temp_xml_path, "test")
        
        # 写入时创建备份
        success = self.writer.write_xml(config, self.temp_xml_path, backup=True)
        self.assertTrue(success)
        
        # 检查备份目录是否存在
        backup_dir = self.temp_xml_path.parent / "backups"
        self.assertTrue(backup_dir.exists())
        
        # 检查是否有备份文件
        backup_files = list(backup_dir.glob("*.xml"))
        self.assertGreater(len(backup_files), 0)
    
    def test_write_xml_nonexistent_file(self):
        """测试写入不存在的文件"""
        logger.info("==liuq debug== 测试写入不存在的文件")
        
        config = self.parser.parse_xml(self.temp_xml_path, "test")
        nonexistent_path = self.temp_dir / "nonexistent.xml"
        
        with self.assertRaises(XMLWriteError):
            self.writer.write_xml(config, nonexistent_path)
    
    def test_write_xml_invalid_config(self):
        """测试写入无效配置"""
        logger.info("==liuq debug== 测试写入无效配置")
        
        with self.assertRaises(Exception):
            self.writer.write_xml(None, self.temp_xml_path)


if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    unittest.main()
