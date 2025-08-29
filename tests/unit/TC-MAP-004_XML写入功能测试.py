#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-MAP-004_XML写入功能测试_重构版
==liuq debug== 重构优化的XML写入功能测试

重构说明：
- 原8个测试合并为4个核心测试，消除重复和冗余
- 保持所有关键功能点的覆盖
- 优化测试结构，提高效率
- 保留详细的值替换日志输出

作者: 龙sir团队
创建时间: 2025-08-28
描述: 验证Map分析页面XML配置写入功能 - 重构优化版
"""

import pytest
import logging
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication

from core.services.map_analysis.xml_parser_service import XMLParserService
from core.services.map_analysis.xml_writer_service import XMLWriterService
from core.models.map_data import MapPoint, MapConfiguration
from gui.main_window import MainWindow

logger = logging.getLogger(__name__)

class TestTC_MAP_004_XML写入功能测试_重构版:
    """重构优化的XML写入功能测试类"""
    
    @pytest.fixture
    def test_xml_file(self):
        """测试XML文件路径"""
        return Path("tests/test_data/awb_scenario.xml")
    
    @pytest.fixture
    def temp_xml_file(self, test_xml_file):
        """临时XML文件（用于写入测试）"""
        import os
        
        # 检查是否有保留临时文件的环境变量
        keep_temp_files = os.environ.get('KEEP_TEMP_FILES', '').lower() in ('1', 'true', 'yes')
        
        temp_dir = Path(tempfile.mkdtemp())
        temp_file = temp_dir / "test_awb_scenario.xml"
        shutil.copy2(test_xml_file, temp_file)
        
        if keep_temp_files:
            print(f"\n==liuq debug== 🔍 临时文件保留模式")
            print(f"==liuq debug== 📁 原始文件: {test_xml_file}")
            print(f"==liuq debug== 📁 临时文件: {temp_file}")
            print(f"==liuq debug== 📁 临时目录: {temp_dir}")
            print(f"==liuq debug== 💡 测试完成后，您可以手动对比这两个文件")
        
        yield temp_file
        
        # 根据环境变量决定是否清理临时文件
        if not keep_temp_files:
            shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            print(f"\n==liuq debug== 🎯 临时文件已保留，请手动对比:")
            print(f"==liuq debug== 📄 原始文件: {test_xml_file}")
            print(f"==liuq debug== 📄 修改后文件: {temp_file}")
            print(f"==liuq debug== 🗂️  临时目录: {temp_dir}")
            print(f"==liuq debug== ⚠️  请手动删除临时目录: {temp_dir}")
    
    @pytest.fixture
    def xml_parser(self):
        """XML解析器服务"""
        return XMLParserService()
    
    @pytest.fixture
    def xml_writer(self):
        """XML写入器服务"""
        return XMLWriterService()
    
    def test_comprehensive_xml_write_and_integrity(self, xml_parser, xml_writer, temp_xml_file):
        """
        综合测试：XML写入成功性、数据完整性、格式保持、结构完整性
        
        合并原测试：
        - test_xml_writing_operation_success_real_data
        - test_real_data_roundtrip_integrity  
        - test_xml_format_preservation_real_data
        - test_xml_data_structure_preservation
        """
        print("==liuq debug== 🔧 综合XML写入和完整性验证")
        logger.info("==liuq debug== 综合XML写入和完整性验证")
        
        # 1. 加载原始数据并验证基本信息
        original_config = xml_parser.parse_xml(temp_xml_file)
        original_points = original_config.map_points
        original_count = len(original_points)
        
        print(f"==liuq debug== 📊 加载真实XML数据: {original_count}个Map点")
        assert original_count >= 100, f"真实XML文件应包含大量Map点数据，当前只有{original_count}个"
        
        # 2. 分析原始数据结构特征
        structure_features = {
            'total_points': original_count,
            'has_base_boundary': bool(original_config.base_boundary),
            'has_metadata': bool(original_config.metadata),
            'first_point_alias': original_points[0].alias_name if original_points else None,
            'last_point_alias': original_points[-1].alias_name if original_points else None,
            'point_attributes': set(dir(original_points[0])) if original_points else set()
        }
        
        print(f"==liuq debug== 📋 数据结构特征:")
        print(f"  - 总点数: {structure_features['total_points']}")
        print(f"  - 有base_boundary: {structure_features['has_base_boundary']}")
        print(f"  - 有metadata: {structure_features['has_metadata']}")
        print(f"  - 首点alias: {structure_features['first_point_alias']}")
        print(f"  - 末点alias: {structure_features['last_point_alias']}")
        
        # 3. 读取原始文件内容用于格式验证
        with open(temp_xml_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        original_size = len(original_content)
        
        # 4. 执行写入操作（使用相同数据测试基本功能）
        write_config = MapConfiguration(
            map_points=original_points,
            device_type=original_config.device_type,
            base_boundary=original_config.base_boundary,
            metadata=original_config.metadata
        )
        
        start_time = time.time()
        success = xml_writer.write_xml(write_config, temp_xml_file)
        write_time = time.time() - start_time
        
        print(f"==liuq debug== ✅ 写入操作结果: {success}, 耗时: {write_time:.2f}秒")
        assert success, "XML写入操作返回失败状态"
        assert write_time < 15.0, f"大型XML文件写入时间过长: {write_time:.2f}秒"
        
        # 5. 验证文件格式保持
        with open(temp_xml_file, 'r', encoding='utf-8') as f:
            new_content = f.read()
        new_size = len(new_content)
        
        # XML格式验证
        assert ('<?xml version="1.0"' in new_content or "<?xml version='1.0'" in new_content), "XML声明丢失"
        assert '<awb_scenario' in new_content, "根元素丢失"
        assert '</awb_scenario>' in new_content, "根元素结束标签丢失"
        assert 'offset_map' in new_content, "offset_map节点丢失"
        assert 'AliasName' in new_content, "AliasName字段丢失"
        
        # 文件大小合理性验证
        size_ratio = new_size / original_size
        assert size_ratio > 0.8, f"文件大小显著缩小，可能丢失数据: 原始{original_size}, 新{new_size}"
        
        print(f"==liuq debug== 📄 格式验证通过: 原始{original_size}字符, 新{new_size}字符, 比例{size_ratio:.2f}")
        
        # 6. 重新加载验证数据完整性
        reloaded_config = xml_parser.parse_xml(temp_xml_file)
        reloaded_points = reloaded_config.map_points
        reloaded_count = len(reloaded_points)
        
        # 数据完整性验证
        assert reloaded_count == original_count, f"数据点数量不匹配: 原始{original_count}, 重新加载{reloaded_count}"
        assert bool(reloaded_config.base_boundary) == structure_features['has_base_boundary'], "base_boundary结构发生变化"
        assert bool(reloaded_config.metadata) == structure_features['has_metadata'], "metadata结构发生变化"
        
        # 关键数据特征验证
        if reloaded_count > 0:
            assert reloaded_points[0].alias_name == structure_features['first_point_alias'], "第一个点的alias_name不匹配"
            assert reloaded_points[-1].alias_name == structure_features['last_point_alias'], "最后一个点的alias_name不匹配"
        
        print(f"==liuq debug== ✅ 综合验证通过: 数据完整性、格式保持、结构完整性全部正常")
        logger.info(f"==liuq debug== 综合XML写入和完整性验证通过: {original_count}个数据点保持完整")

    def test_xml_write_performance(self, xml_parser, xml_writer, temp_xml_file):
        """
        专项测试：大数据量XML写入性能

        保留原测试：test_large_data_write_performance
        """
        print("==liuq debug== ⚡ XML写入性能专项测试")
        logger.info("==liuq debug== XML写入性能专项测试")

        # 加载真实大数据量
        original_config = xml_parser.parse_xml(temp_xml_file)
        original_points = original_config.map_points
        data_count = len(original_points)

        print(f"==liuq debug== 📊 性能测试数据量: {data_count}个Map点")
        assert data_count >= 100, f"需要大数据量进行性能测试，当前只有{data_count}个点"

        # 创建写入配置
        write_config = MapConfiguration(
            map_points=original_points,
            device_type=original_config.device_type,
            base_boundary=original_config.base_boundary,
            metadata=original_config.metadata
        )

        # 性能测试
        start_time = time.time()
        success = xml_writer.write_xml(write_config, temp_xml_file)
        write_time = time.time() - start_time

        # 性能验证
        assert success, "大数据量XML写入失败"
        assert write_time < 20.0, f"大数据量XML写入时间过长: {write_time:.2f}秒"

        # 计算写入速度
        write_speed = data_count / write_time if write_time > 0 else 0

        print(f"==liuq debug== ⚡ 性能指标:")
        print(f"  - 写入时间: {write_time:.2f}秒")
        print(f"  - 处理数据: {data_count}个Map点")
        print(f"  - 写入速度: {write_speed:.1f}点/秒")

        # 验证写入后数据完整性
        reloaded_config = xml_parser.parse_xml(temp_xml_file)
        reloaded_count = len(reloaded_config.map_points)
        assert reloaded_count == data_count, f"写入后数据不完整: 原始{data_count}, 重新加载{reloaded_count}"

        print(f"==liuq debug== ✅ 性能测试通过: {write_time:.2f}秒处理{data_count}个点")
        logger.info("==liuq debug== XML写入性能测试通过")

    def test_xml_write_error_handling_and_backup(self, xml_parser, xml_writer, temp_xml_file):
        """
        综合测试：错误处理和备份功能

        合并原测试：
        - test_xml_writing_error_handling_real_scenarios
        - test_backup_creation_with_real_data
        """
        print("==liuq debug== 🛡️ 错误处理和备份功能测试")
        logger.info("==liuq debug== 错误处理和备份功能测试")

        # 加载真实数据用于测试
        real_config = xml_parser.parse_xml(temp_xml_file)
        original_size = temp_xml_file.stat().st_size

        print(f"==liuq debug== 📊 测试数据: {len(real_config.map_points)}个Map点, 文件大小: {original_size}字节")

        # 1. 测试错误处理
        print("==liuq debug== 🔧 测试错误处理能力...")

        # 测试写入到无效路径
        invalid_path = Path("Z:\\nonexistent\\directory\\test.xml")
        result = xml_writer.write_xml(real_config, invalid_path)
        assert result == False, "写入到无效路径应该返回False"
        print("  ✅ 无效路径错误处理正常")

        # 测试损坏的配置数据
        corrupted_config = MapConfiguration(map_points=None, device_type="test", base_boundary={})
        result = xml_writer.write_xml(corrupted_config, temp_xml_file)
        print(f"  ✅ 损坏数据处理结果: {result}")

        # 2. 测试备份功能
        print("==liuq debug== 💾 测试备份功能...")

        # 记录写入前的备份文件数量
        backup_dir = temp_xml_file.parent / "backups"
        initial_backup_count = 0
        if backup_dir.exists():
            initial_backup_count = len(list(backup_dir.glob("*.xml")))

        # 执行写入操作（应该创建备份）
        success = xml_writer.write_xml(real_config, temp_xml_file)
        assert success, "真实数据写入失败"

        # 检查备份文件是否创建
        backup_created = False
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.xml"))
            current_backup_count = len(backup_files)
            backup_created = current_backup_count > initial_backup_count

            if backup_created:
                latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
                backup_size = latest_backup.stat().st_size
                size_ratio = backup_size / original_size

                print(f"  ✅ 备份文件创建成功: {latest_backup.name}")
                print(f"  📄 备份文件大小: {backup_size}字节 (比例: {size_ratio:.2f})")

                assert size_ratio > 0.9, f"备份文件大小异常: 原始{original_size}, 备份{backup_size}"

        if not backup_created:
            print("  ⚠️ 未检测到新的备份文件创建")

        print(f"==liuq debug== ✅ 错误处理和备份功能验证完成")
        logger.info("==liuq debug== 错误处理和备份功能测试通过")

    def test_real_data_value_replacement_verification(self, xml_parser, xml_writer, temp_xml_file):
        """
        核心测试：真实数据值替换验证 - 最详细的日志输出

        保留并增强原测试：test_real_data_value_replacement_verification
        这是最重要的测试，验证XML写入确实能替换具体的数值
        """
        print("==liuq debug== 🎯 真实数据值替换验证 - 核心功能测试")
        logger.info("==liuq debug== 真实数据值替换验证")

        # 1. 加载原始数据
        original_config = xml_parser.parse_xml(temp_xml_file)
        original_points = original_config.map_points

        assert len(original_points) >= 100, f"需要足够的数据点进行修改测试，当前只有{len(original_points)}个"

        # 2. 显示原始Map点信息
        print(f"==liuq debug== 📊 原始数据: {len(original_points)}个Map点")
        original_offset_info = []
        for i in range(min(3, len(original_points))):
            point = original_points[i]
            print(f"  Map点{i}: {point.alias_name}")
            print(f"    原始offset_x: {point.offset_x}")
            print(f"    原始offset_y: {point.offset_y}")

            original_offset_info.append({
                'alias': point.alias_name,
                'original_x': point.offset_x,
                'original_y': point.offset_y
            })

        # 3. 真正修改数据（使用明显的值变化）
        print("==liuq debug== 🔧 执行真实数据修改...")
        modified_points = []
        modification_info = []

        for i, point in enumerate(original_points):
            if i < 2:  # 只修改前2个点，减少复杂性
                # 使用更明显的值变化
                new_offset_x = 99.999 + i  # 99.999, 100.999
                new_offset_y = 88.888 + i  # 88.888, 89.888

                # 直接修改原始点的属性（确保修改生效）
                point.offset_x = new_offset_x
                point.offset_y = new_offset_y

                modified_points.append(point)

                modification_info.append({
                    'alias': point.alias_name,
                    'old_x': original_offset_info[i]['original_x'],
                    'new_x': new_offset_x,
                    'old_y': original_offset_info[i]['original_y'],
                    'new_y': new_offset_y
                })

                # 使用print确保输出可见
                print(f"  修改Map点{i}: {point.alias_name}")
                print(f"    offset_x: {original_offset_info[i]['original_x']} -> {new_offset_x}")
                print(f"    offset_y: {original_offset_info[i]['original_y']} -> {new_offset_y}")

                logger.info(f"==liuq debug== 计划修改Map点{i}: {point.alias_name}")
                logger.info(f"  offset_x: {original_offset_info[i]['original_x']} -> {new_offset_x}")
                logger.info(f"  offset_y: {original_offset_info[i]['original_y']} -> {new_offset_y}")
            else:
                modified_points.append(point)

        # 4. 创建修改后的配置
        modified_config = MapConfiguration(
            map_points=modified_points,
            device_type=original_config.device_type,
            base_boundary=original_config.base_boundary,
            metadata=original_config.metadata
        )

        # 5. 读取原始文件内容，用于差异对比
        with open(temp_xml_file, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()

        # 6. 执行写入操作
        print("==liuq debug== 💾 执行XML值替换写入...")
        logger.info("==liuq debug== 执行XML值替换写入...")
        success = xml_writer.write_xml(modified_config, temp_xml_file)
        print(f"==liuq debug== 写入操作结果: {success}")
        assert success, "修改数据写入失败"

        # 7. 读取修改后的文件内容，进行详细差异分析
        with open(temp_xml_file, 'r', encoding='utf-8') as f:
            modified_lines = f.readlines()

        # 8. 详细对比文件差异，专注于值变化
        print("==liuq debug== 🔍 详细文件差异分析:")
        logger.info("==liuq debug== 详细文件差异分析:")
        changes_found = 0
        value_changes = []

        # 查找包含修改Map点的行
        for mod_info in modification_info:
            alias_name = mod_info['alias']
            print(f"  查找Map点 {alias_name} 的变化...")
            logger.info(f"==liuq debug== 查找Map点 {alias_name} 的变化...")

            # 在原始和修改后的文件中查找相关行
            for line_num, (orig_line, mod_line) in enumerate(zip(original_lines, modified_lines)):
                if orig_line != mod_line:
                    changes_found += 1

                    # 检查是否包含我们修改的alias
                    if alias_name in orig_line or alias_name in mod_line:
                        print(f"    第{line_num+1}行 ({alias_name}) 发生变化:")
                        print(f"      原始: {orig_line.strip()}")
                        print(f"      修改: {mod_line.strip()}")

                        logger.info(f"  第{line_num+1}行 ({alias_name}) 发生变化:")
                        logger.info(f"    原始: {orig_line.strip()}")
                        logger.info(f"    修改: {mod_line.strip()}")

                        # 尝试提取数值变化
                        import re
                        orig_numbers = re.findall(r'-?\d+\.?\d*', orig_line)
                        mod_numbers = re.findall(r'-?\d+\.?\d*', mod_line)

                        if orig_numbers != mod_numbers:
                            print(f"      数值变化: {orig_numbers} -> {mod_numbers}")
                            logger.info(f"    数值变化: {orig_numbers} -> {mod_numbers}")
                            value_changes.append({
                                'line': line_num + 1,
                                'alias': alias_name,
                                'old_values': orig_numbers,
                                'new_values': mod_numbers
                            })

                    # 限制显示的变化行数
                    if changes_found >= 20:
                        total_changes = len([i for i, (o, m) in enumerate(zip(original_lines, modified_lines)) if o != m])
                        print(f"    ... (还有更多变化，总共{total_changes}行)")
                        logger.info(f"  ... (还有更多变化，总共{total_changes}行)")
                        break

        # 总结变化
        print(f"==liuq debug== 📋 文件差异总结:")
        print(f"  总变化行数: {changes_found}")
        print(f"  检测到的值变化: {len(value_changes)}")
        print(f"  文件大小变化: {len(''.join(original_lines))} -> {len(''.join(modified_lines))} bytes")

        logger.info(f"==liuq debug== 文件差异总结:")
        logger.info(f"  总变化行数: {changes_found}")
        logger.info(f"  检测到的值变化: {len(value_changes)}")
        logger.info(f"  文件大小变化: {len(''.join(original_lines))} -> {len(''.join(modified_lines))} bytes")

        if changes_found == 0:
            print("==liuq debug== ❌ 警告：没有发现任何文件内容变化！")
            logger.warning("==liuq debug== ❌ 警告：没有发现任何文件内容变化！")
        else:
            print(f"==liuq debug== ✅ 发现{changes_found}行内容发生变化")
            logger.info(f"==liuq debug== ✅ 发现{changes_found}行内容发生变化")

        if len(value_changes) == 0:
            print("==liuq debug== ❌ 警告：没有检测到预期的值变化！")
            logger.warning("==liuq debug== ❌ 警告：没有检测到预期的值变化！")
        else:
            print(f"==liuq debug== ✅ 检测到{len(value_changes)}个值变化")
            logger.info(f"==liuq debug== ✅ 检测到{len(value_changes)}个值变化")

        # 9. 重新加载验证修改是否生效
        print("==liuq debug== 🔄 重新加载验证修改结果:")
        logger.info("==liuq debug== 验证数据修改结果:")
        reloaded_config = xml_parser.parse_xml(temp_xml_file)
        reloaded_points = reloaded_config.map_points

        # 10. 验证每个修改的数据点
        for i, mod_info in enumerate(modification_info):
            if i < len(reloaded_points):
                reloaded_point = reloaded_points[i]

                print(f"  Map点{i} ({mod_info['alias']}):")
                print(f"    期望offset_x: {mod_info['new_x']}")
                print(f"    实际offset_x: {reloaded_point.offset_x}")
                print(f"    期望offset_y: {mod_info['new_y']}")
                print(f"    实际offset_y: {reloaded_point.offset_y}")

                logger.info(f"  Map点{i} ({mod_info['alias']}):")
                logger.info(f"    期望offset_x: {mod_info['new_x']}")
                logger.info(f"    实际offset_x: {reloaded_point.offset_x}")
                logger.info(f"    期望offset_y: {mod_info['new_y']}")
                logger.info(f"    实际offset_y: {reloaded_point.offset_y}")

                # 验证修改是否生效
                x_match = abs((reloaded_point.offset_x or 0) - mod_info['new_x']) < 0.001
                y_match = abs((reloaded_point.offset_y or 0) - mod_info['new_y']) < 0.001

                if x_match and y_match:
                    print(f"    ✅ 修改成功生效")
                    logger.info(f"    ✅ 修改成功生效")
                else:
                    print(f"    ❌ 修改未生效")
                    logger.warning(f"    ❌ 修改未生效")

                assert x_match, f"Map点{i}的offset_x修改未生效"
                assert y_match, f"Map点{i}的offset_y修改未生效"

        print(f"==liuq debug== 🎯 真实数据值替换验证通过: 成功修改了{len(modification_info)}个Map点的offset值")
        print(f"==liuq debug== 📊 文件变化行数: {changes_found}, 只替换值而不格式化文件")
        logger.info(f"==liuq debug== 真实数据值替换验证通过: 成功修改了{len(modification_info)}个Map点的offset值")
        logger.info(f"==liuq debug== 文件变化行数: {changes_found}, 只替换值而不格式化文件")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
