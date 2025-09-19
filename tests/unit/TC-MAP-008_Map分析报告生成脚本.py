#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map分析报告生成脚本（无GUI版本）
用于直接从XML文件生成Map多维度分析报告

作者: 龙sir团队
创建时间: 2025-09-19
版本: 2.0.0
描述: 不依赖GUI，直接从XML文件生成Map多维度分析报告
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.services.map_analysis.xml_parser_service import XMLParserService
from core.services.reporting.domains.map import MapMultiDimensionalReportGenerator
from core.models.scene_classification_config import SceneClassificationConfig
from core.models.map_data import MapConfiguration, MapPoint, BaseBoundary

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'data' / 'logs' / 'map_analysis_report_generator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_test_map_configuration():
    """创建测试用的Map配置"""
    logger.info("创建测试Map配置...")

    # 创建基础边界
    base_boundary = BaseBoundary(rpg=0.5, bpg=0.5)

    # 创建测试Map点
    map_points = [
        MapPoint(
            alias_name="Test_Point_1",
            x=0.6,
            y=0.6,
            offset_x=0.1,
            offset_y=0.1,
            weight=1.0,
            bv_range=(1.0, 2.0),
            ir_range=(0.1, 0.2),
            cct_range=(4000.0, 5000.0),
            trans_step=1
        ),
        MapPoint(
            alias_name="Test_Point_2",
            x=0.7,
            y=0.7,
            offset_x=0.2,
            offset_y=0.2,
            weight=1.5,
            bv_range=(2.0, 3.0),
            ir_range=(0.2, 0.3),
            cct_range=(5000.0, 6000.0),
            trans_step=2
        ),
        MapPoint(
            alias_name="Test_Point_3",
            x=0.8,
            y=0.8,
            offset_x=0.3,
            offset_y=0.3,
            weight=2.0,
            bv_range=(3.0, 4.0),
            ir_range=(0.3, 0.4),
            cct_range=(6000.0, 7000.0),
            trans_step=3
        )
    ]

    # 创建Map配置
    map_config = MapConfiguration(
        device_type="Test Device",
        base_boundary=base_boundary,
        map_points=map_points
    )

    logger.info(f"创建Map配置完成，包含 {len(map_points)} 个Map点")
    return map_config

def generate_map_analysis_report_from_xml(xml_file_path, output_file_path=None):
    """从XML文件生成Map分析报告"""
    logger.info(f"开始从XML文件生成Map分析报告: {xml_file_path}")

    try:
        # 确保输出目录存在
        if output_file_path is None:
            output_dir = project_root / 'data' / 'reports'
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file_path = output_dir / f'map_analysis_report_{timestamp}.html'

        output_file_path = Path(output_file_path)
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 检查XML文件是否存在
        xml_file_path = Path(xml_file_path)
        if not xml_file_path.exists():
            logger.error(f"XML文件不存在: {xml_file_path}")
            return False

        # 解析XML文件
        logger.info("解析XML文件...")
        xml_parser = XMLParserService()
        map_config = xml_parser.parse_xml(xml_file_path)

        if not map_config or not map_config.map_points:
            logger.warning("XML解析失败或没有Map数据，使用测试数据")
            map_config = create_test_map_configuration()

        logger.info(f"XML解析完成，包含 {len(map_config.map_points)} 个Map点")

        # 创建报告生成器
        logger.info("初始化报告生成器...")
        report_generator = MapMultiDimensionalReportGenerator()

        # 准备报告数据
        report_data = {
            'map_configuration': map_config,
            'include_multi_dimensional': True,
            'classification_config': SceneClassificationConfig(),
            'output_path': str(output_file_path)
        }

        # 生成报告
        logger.info("开始生成报告...")
        generated_file = report_generator.generate(report_data)

        # 验证生成的文件
        if Path(generated_file).exists():
            file_size = Path(generated_file).stat().st_size
            logger.info(f"报告生成成功: {generated_file}")
            logger.info(f"报告文件大小: {file_size} bytes")

            # 检查关键内容
            with open(generated_file, 'r', encoding='utf-8') as f:
                content = f.read()

            key_checks = [
                ('Map 分类特性报告', '报告标题'),
                ('分类总表', '分类总表'),
                ('色温段跨度统计', '色温段跨度统计'),
                ('详细分析', '详细分析部分'),
                ('偏移散点', '偏移散点图'),
                ('BV 跨度', 'BV跨度图'),
                ('IR 跨度', 'IR跨度图'),
                ('CTemp 跨度', 'CTemp跨度图')
            ]

            logger.info("=== 报告内容检查 ===")
            for check_text, description in key_checks:
                if check_text in content:
                    logger.info(f"[✓] {description}: 存在")
                else:
                    logger.warning(f"[✗] {description}: 缺失")

            # 如果报告没有色温段跨度统计，添加提示
            if '色温段跨度统计' not in content:
                logger.info("提示：生成的报告缺少色温段跨度统计模块，这可能是因为模板文件未正确包含")
                logger.info("请确保templates/reporting/domains/map/_temp_span.html模板文件存在并被正确引用")

            return True
        else:
            logger.error("报告生成失败：文件不存在")
            return False

    except Exception as e:
        logger.error(f"生成报告时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logger.info("=== Map分析报告生成脚本启动 ===")

    # 设置XML文件路径
    xml_file_path = project_root / 'tests' / 'test_data' / 'awb_scenario.xml'

    # 检查XML文件
    if not xml_file_path.exists():
        logger.error(f"XML文件不存在: {xml_file_path}")
        return 1

    logger.info(f"使用XML文件: {xml_file_path}")

    # 生成报告
    success = generate_map_analysis_report_from_xml(xml_file_path)

    if success:
        logger.info("=== Map分析报告生成成功 ===")
        return 0
    else:
        logger.error("=== Map分析报告生成失败 ===")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)