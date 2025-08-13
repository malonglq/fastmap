#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map分析集成测试
==liuq debug== FastMapV2 Map分析集成测试

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 18:05:00 +08:00; Reason: P1-LD-008 实现单元测试; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: Map分析功能的集成测试
"""

import pytest
import tempfile
import os
from pathlib import Path

# 添加项目根目录到路径
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.services.xml_parser import XMLParser
from core.services.map_analyzer import MapAnalyzer
from core.services.html_generator import UniversalHTMLGenerator
from core.models.map_data import MapConfiguration, SceneType


class TestMapAnalysisIntegration:
    """Map分析集成测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.sample_xml_content = self._create_comprehensive_xml()
    
    def _create_comprehensive_xml(self) -> str:
        """创建综合性的XML测试数据"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <base_boundary0>
        <RpG>1.0</RpG>
        <BpG>2.0</BpG>
    </base_boundary0>
    <base_boundary0>
        <RpG>1.5</RpG>
        <BpG>2.5</BpG>
    </base_boundary0>
    
    <!-- 室内场景Map点 -->
    <offset_map01>
        <weight>0.8</weight>
        <offset>
            <x>100.0</x>
            <y>200.0</y>
        </offset>
        <range>
            <bv>
                <min>1000</min>
                <max>3000</max>
            </bv>
            <ir>
                <min>500</min>
                <max>1000</max>
            </ir>
            <colorCCT>
                <min>2700</min>
                <max>5000</max>
            </colorCCT>
            <DetectMapFlag>true</DetectMapFlag>
        </range>
    </offset_map01>
    <offset_map01>
        <AliasName>Indoor_BV_2000_IR_750</AliasName>
        <RpG>1.2</RpG>
        <BpG>2.3</BpG>
    </offset_map01>
    
    <!-- 室外场景Map点 -->
    <offset_map02>
        <weight>0.6</weight>
        <offset>
            <x>300.0</x>
            <y>400.0</y>
        </offset>
        <range>
            <bv>
                <min>6000</min>
                <max>10000</max>
            </bv>
            <ir>
                <min>800</min>
                <max>1200</max>
            </ir>
            <colorCCT>
                <min>4000</min>
                <max>7000</max>
            </colorCCT>
            <DetectMapFlag>true</DetectMapFlag>
        </range>
    </offset_map02>
    <offset_map02>
        <AliasName>Outdoor_BV_8000_IR_1000</AliasName>
        <RpG>1.3</RpG>
        <BpG>2.4</BpG>
    </offset_map02>
    
    <!-- 夜景场景Map点 -->
    <offset_map03>
        <weight>0.9</weight>
        <offset>
            <x>150.0</x>
            <y>100.0</y>
        </offset>
        <range>
            <bv>
                <min>100</min>
                <max>1000</max>
            </bv>
            <ir>
                <min>300</min>
                <max>600</max>
            </ir>
            <colorCCT>
                <min>2000</min>
                <max>3500</max>
            </colorCCT>
            <DetectMapFlag>true</DetectMapFlag>
        </range>
    </offset_map03>
    <offset_map03>
        <AliasName>Night_BV_500_IR_450</AliasName>
        <RpG>1.1</RpG>
        <BpG>2.1</BpG>
    </offset_map03>
</root>'''
    
    def _create_temp_xml_file(self, content: str) -> str:
        """创建临时XML文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name
    
    def test_complete_map_analysis_workflow(self):
        """测试完整的Map分析工作流"""
        xml_file = self._create_temp_xml_file(self.sample_xml_content)
        
        try:
            # 1. XML解析
            parser = XMLParser()
            configuration = parser.parse_xml_file(xml_file, "integration_test")
            
            # 验证解析结果
            assert isinstance(configuration, MapConfiguration)
            assert len(configuration.map_points) == 3
            assert configuration.device_type == "integration_test"
            
            # 2. Map分析
            analyzer = MapAnalyzer(configuration)
            analysis_result = analyzer.analyze()
            
            # 验证分析结果
            assert analysis_result is not None
            assert analysis_result.configuration == configuration
            assert len(analysis_result.scene_statistics) > 0
            assert analysis_result.analysis_timestamp != ""
            assert analysis_result.analysis_duration > 0
            
            # 3. 验证场景分析
            scene_stats = analysis_result.scene_statistics
            assert 'indoor' in scene_stats
            assert 'outdoor' in scene_stats
            assert 'night' in scene_stats
            
            # 验证场景分布
            indoor_count = scene_stats['indoor']['count']
            outdoor_count = scene_stats['outdoor']['count']
            night_count = scene_stats['night']['count']
            
            assert indoor_count + outdoor_count + night_count == 3
            assert indoor_count >= 1  # 至少有一个室内场景
            assert outdoor_count >= 1  # 至少有一个室外场景
            assert night_count >= 1   # 至少有一个夜景场景
            
            # 4. 验证可视化数据
            scatter_data = analyzer.get_scatter_plot_data()
            assert 'title' in scatter_data
            assert 'datasets' in scatter_data
            assert len(scatter_data['datasets']) > 0
            
            heatmap_data = analyzer.get_heatmap_data()
            assert 'title' in heatmap_data
            
            # 5. 验证报告数据
            report_data = analyzer.prepare_report_data()
            assert 'scatter_data' in report_data
            assert 'scene_analysis' in report_data
            assert 'weight_analysis' in report_data
            
            summary = analyzer.get_summary_data()
            assert 'total_map_points' in summary
            assert summary['total_map_points'] == 3
            
        finally:
            os.unlink(xml_file)
    
    def test_html_report_generation(self):
        """测试HTML报告生成"""
        xml_file = self._create_temp_xml_file(self.sample_xml_content)

        try:
            # 解析和分析
            parser = XMLParser()
            configuration = parser.parse_xml_file(xml_file, "report_test")

            analyzer = MapAnalyzer(configuration)
            analyzer.analyze()

            # 生成HTML报告
            html_generator = UniversalHTMLGenerator()

            # 测试完整报告生成
            report_path = html_generator.generate_report(analyzer, template_name="default")

            # 验证报告文件存在
            assert os.path.exists(report_path)

            # 读取并验证HTML内容
            with open(report_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            assert "<!DOCTYPE html>" in html_content
            assert "FastMapV2" in html_content or "Map" in html_content

            # 清理生成的报告文件
            os.unlink(report_path)

        finally:
            os.unlink(xml_file)
    
    def test_scene_type_inference(self):
        """测试场景类型推断"""
        xml_file = self._create_temp_xml_file(self.sample_xml_content)
        
        try:
            parser = XMLParser()
            configuration = parser.parse_xml_file(xml_file)
            
            # 验证场景类型推断
            scene_counts = {
                SceneType.INDOOR: 0,
                SceneType.OUTDOOR: 0,
                SceneType.NIGHT: 0
            }
            
            for map_point in configuration.map_points:
                scene_counts[map_point.scene_type] += 1
            
            # 应该有各种场景类型
            assert scene_counts[SceneType.INDOOR] > 0
            assert scene_counts[SceneType.OUTDOOR] > 0
            assert scene_counts[SceneType.NIGHT] > 0
            
        finally:
            os.unlink(xml_file)
    
    def test_weight_analysis(self):
        """测试权重分析"""
        xml_file = self._create_temp_xml_file(self.sample_xml_content)
        
        try:
            parser = XMLParser()
            configuration = parser.parse_xml_file(xml_file)
            
            analyzer = MapAnalyzer(configuration)
            analysis_result = analyzer.analyze()
            
            weight_analysis = analysis_result.weight_analysis
            
            # 验证权重统计
            assert 'mean' in weight_analysis
            assert 'min' in weight_analysis
            assert 'max' in weight_analysis
            assert 'std' in weight_analysis
            
            # 验证权重范围合理性
            assert 0 <= weight_analysis['min'] <= 1
            assert 0 <= weight_analysis['max'] <= 1
            assert weight_analysis['min'] <= weight_analysis['mean'] <= weight_analysis['max']
            
        finally:
            os.unlink(xml_file)
    
    def test_coordinate_analysis(self):
        """测试坐标分析"""
        xml_file = self._create_temp_xml_file(self.sample_xml_content)
        
        try:
            parser = XMLParser()
            configuration = parser.parse_xml_file(xml_file)
            
            analyzer = MapAnalyzer(configuration)
            analysis_result = analyzer.analyze()
            
            coord_analysis = analysis_result.coordinate_analysis
            
            # 验证坐标统计
            assert 'total_points' in coord_analysis
            assert 'x_range' in coord_analysis
            assert 'y_range' in coord_analysis
            assert 'x_center' in coord_analysis
            assert 'y_center' in coord_analysis
            
            # 验证坐标范围
            x_range = coord_analysis['x_range']
            y_range = coord_analysis['y_range']
            
            assert x_range[0] <= x_range[1]  # min <= max
            assert y_range[0] <= y_range[1]  # min <= max
            
            # 验证中心点在范围内
            assert x_range[0] <= coord_analysis['x_center'] <= x_range[1]
            assert y_range[0] <= coord_analysis['y_center'] <= y_range[1]
            
        finally:
            os.unlink(xml_file)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试空XML文件（有效但无内容）
        empty_xml = "<?xml version='1.0'?><root></root>"
        xml_file = self._create_temp_xml_file(empty_xml)

        try:
            parser = XMLParser()
            configuration = parser.parse_xml_file(xml_file)

            # 应该能解析，但没有Map点
            assert len(configuration.map_points) == 0

            # 分析空配置应该不会崩溃
            analyzer = MapAnalyzer(configuration)
            analysis_result = analyzer.analyze()

            assert analysis_result is not None

        finally:
            os.unlink(xml_file)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
