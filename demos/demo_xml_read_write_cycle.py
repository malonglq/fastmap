#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML读写循环演示
==liuq debug== FastMapV2 XML读写循环功能演示

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 15:00:00 +08:00; Reason: P1-LD-006 演示XML写入服务功能; Principle_Applied: 演示驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 演示XML读取、修改、写入的完整循环功能
"""

import sys
import logging
from pathlib import Path
import tempfile

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.services.xml_parser_service import XMLParserService
from core.services.xml_writer_service import XMLWriterService
from core.models.map_data import MapConfiguration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_demo_xml_file(xml_path: str):
    """创建演示XML文件"""
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <version>2.0</version>
    <device>demo_device</device>
    <created>2025-07-28</created>
    <base_boundary>
        <rpg>0.8</rpg>
        <bpg>0.6</bpg>
    </base_boundary>
    <Maps>
        <Map>
            <AliasName>Demo_Indoor_Point</AliasName>
            <x>200.0</x>
            <y>300.0</y>
            <offset>
                <x>200.0</x>
                <y>300.0</y>
            </offset>
            <weight>1.8</weight>
            <bv_range>15.0,85.0</bv_range>
            <ir_range>8.0,92.0</ir_range>
            <cct_range>2800.0,7200.0</cct_range>
            <detect_flag>true</detect_flag>
            <TransStep>2</TransStep>
        </Map>
        <Map>
            <AliasName>Demo_Outdoor_Point</AliasName>
            <x>400.0</x>
            <y>500.0</y>
            <offset>
                <x>400.0</x>
                <y>500.0</y>
            </offset>
            <weight>2.5</weight>
            <bv_range>25.0,75.0</bv_range>
            <ir_range>12.0,88.0</ir_range>
            <cct_range>3200.0,6800.0</cct_range>
            <detect_flag>false</detect_flag>
            <TransStep>3</TransStep>
        </Map>
        <Map>
            <AliasName>Demo_Night_Point</AliasName>
            <x>600.0</x>
            <y>700.0</y>
            <offset>
                <x>600.0</x>
                <y>700.0</y>
            </offset>
            <weight>3.2</weight>
            <bv_range>5.0,95.0</bv_range>
            <ir_range>2.0,98.0</ir_range>
            <cct_range>2200.0,8200.0</cct_range>
            <detect_flag>true</detect_flag>
            <TransStep>1</TransStep>
        </Map>
    </Maps>
</root>'''
    
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    logger.info(f"==liuq debug== 创建演示XML文件: {xml_path}")


def demonstrate_xml_read_write_cycle():
    """演示XML读写循环功能"""
    print("=" * 80)
    print("FastMapV2 XML读写循环功能演示")
    print("=" * 80)
    
    # 创建临时目录和文件
    temp_dir = Path(tempfile.mkdtemp())
    xml_file = temp_dir / "demo_map_config.xml"
    
    try:
        # 步骤1：创建演示XML文件
        print("\n--- 步骤1：创建演示XML文件 ---")
        create_demo_xml_file(xml_file)
        print(f"✓ 演示XML文件已创建: {xml_file.name}")
        
        # 步骤2：读取XML文件
        print("\n--- 步骤2：读取XML文件 ---")
        parser = XMLParserService()
        config = parser.parse_xml(xml_file, "demo")
        
        print(f"✓ XML文件解析成功")
        print(f"  - 设备类型: {config.device_type}")
        print(f"  - Map点数量: {len(config.map_points)}")
        print(f"  - 基础边界: RpG={config.base_boundary.rpg}, BpG={config.base_boundary.bpg}")
        
        # 显示原始Map点信息
        print("\n  原始Map点信息:")
        for i, point in enumerate(config.map_points):
            print(f"    {i+1}. {point.alias_name}: 权重={point.weight}, 坐标=({point.x}, {point.y})")
        
        # 步骤3：修改配置数据
        print("\n--- 步骤3：修改配置数据 ---")
        
        # 修改第一个Map点
        if config.map_points:
            original_weight = config.map_points[0].weight
            original_alias = config.map_points[0].alias_name
            
            config.map_points[0].weight = 5.0
            config.map_points[0].alias_name = "Modified_Demo_Point"
            config.map_points[0].x = 250.0
            config.map_points[0].y = 350.0
            
            print(f"✓ 修改第一个Map点:")
            print(f"  - 别名: {original_alias} → {config.map_points[0].alias_name}")
            print(f"  - 权重: {original_weight} → {config.map_points[0].weight}")
            print(f"  - 坐标: (200.0, 300.0) → ({config.map_points[0].x}, {config.map_points[0].y})")
        
        # 修改基础边界
        config.base_boundary.rpg = 0.9
        config.base_boundary.bpg = 0.7
        print(f"✓ 修改基础边界: RpG=0.9, BpG=0.7")
        
        # 步骤4：写入XML文件
        print("\n--- 步骤4：写入XML文件 ---")
        writer = XMLWriterService()
        
        success = writer.write_xml(config, xml_file, backup=True)
        
        if success:
            print("✓ XML文件写入成功")
            
            # 检查备份文件
            backup_dir = xml_file.parent / "backups"
            if backup_dir.exists():
                backup_files = list(backup_dir.glob("*.xml"))
                if backup_files:
                    print(f"✓ 自动备份已创建: {backup_files[0].name}")
        else:
            print("✗ XML文件写入失败")
            return
        
        # 步骤5：验证写入结果
        print("\n--- 步骤5：验证写入结果 ---")
        
        # 重新读取文件
        updated_config = parser.parse_xml(xml_file, "demo")
        
        print(f"✓ 重新读取XML文件成功")
        print(f"  - Map点数量: {len(updated_config.map_points)}")
        print(f"  - 基础边界: RpG={updated_config.base_boundary.rpg}, BpG={updated_config.base_boundary.bpg}")
        
        # 验证修改是否生效
        print("\n  更新后的Map点信息:")
        for i, point in enumerate(updated_config.map_points):
            print(f"    {i+1}. {point.alias_name}: 权重={point.weight}, 坐标=({point.x}, {point.y})")
        
        # 验证具体修改
        if updated_config.map_points:
            first_point = updated_config.map_points[0]
            if (first_point.alias_name == "Modified_Demo_Point" and 
                first_point.weight == 5.0 and 
                first_point.x == 250.0 and 
                first_point.y == 350.0):
                print("✓ 数据修改验证成功")
            else:
                print("✗ 数据修改验证失败")
        
        # 步骤6：XML验证
        print("\n--- 步骤6：XML验证 ---")
        validation_result = writer.validate_xml(xml_file)
        
        if validation_result.is_valid:
            print("✓ XML文件验证通过")
        else:
            print("✗ XML文件验证失败")
            for error in validation_result.errors:
                print(f"  错误: {error}")
        
        # 步骤7：获取XML元数据
        print("\n--- 步骤7：XML元数据 ---")
        metadata = writer.get_xml_metadata(xml_file)
        
        print(f"✓ XML元数据:")
        print(f"  - 文件大小: {metadata.get('file_size', 0)} 字节")
        print(f"  - 根标签: {metadata.get('root_tag', 'unknown')}")
        print(f"  - Map数量: {metadata.get('map_count', 0)}")
        
        print("\n" + "=" * 80)
        print("XML读写循环演示完成！")
        print("=" * 80)
        
        print(f"\n演示文件位置: {xml_file}")
        print("您可以查看生成的XML文件和备份文件。")
        
    except Exception as e:
        logger.error(f"==liuq debug== 演示过程中发生错误: {e}")
        print(f"\n✗ 演示失败: {e}")
    
    finally:
        # 清理临时文件（可选）
        # import shutil
        # if temp_dir.exists():
        #     shutil.rmtree(temp_dir)
        pass


if __name__ == "__main__":
    demonstrate_xml_read_write_cycle()
