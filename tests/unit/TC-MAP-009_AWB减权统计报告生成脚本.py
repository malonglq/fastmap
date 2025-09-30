#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""TC-MAP-009: 生成包含 AWB 减权统计章节的离线报告."""

import sys
import logging
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.services.map_analysis.xml_parser_service import XMLParserService
from core.services.reporting.domains.map import MapMultiDimensionalReportGenerator
from core.models.scene_classification_config import SceneClassificationConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'data' / 'logs' / 'tc_map009_awb_reduce.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def generate_report(output_dir: Path | None = None) -> Path:
    xml_path = project_root / 'tests' / 'test_data' / 'awb_scenario_1x.xml'
    if output_dir is None:
        output_dir = project_root / 'data' / 'reports'
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'map_analysis_awb_reduce_{timestamp}.html'

    parser = XMLParserService()
    config = parser.parse_xml(xml_path)

    generator = MapMultiDimensionalReportGenerator()
    report_request = {
        'map_configuration': config,
        'include_multi_dimensional': True,
        'classification_config': SceneClassificationConfig(),
        'output_path': str(output_file),
        'include_awb_reduce_analysis': True,
        'offset_query_options': {
            'default_title': 'BV(2,6) × 色温1500–3800 减权统计',
        },
        'include_awb_offset_analysis': True,
        'awb_offset_analysis_options': {
            'title': 'AWB Offset Map概述',
            'xml_path': str(xml_path),
            'top_entry_count': 8,
        },
    }

    generated_path = Path(generator.generate(report_request))
    if not generated_path.exists():
        raise FileNotFoundError(f'生成报告失败: {generated_path}')
    logger.info('报告生成成功: %s', generated_path)
    return generated_path


def verify_section(report_path: Path) -> None:
    content = report_path.read_text(encoding='utf-8')
    required_snippets = [
        'BV(2,6) × 色温1500–3800 减权统计',
        'ml=65535',
        '### 统计概览'.replace('### ', ''),
        '策略洞察',
        '混合光条目',
        '门店/特定场景',
        '色彩极端场景',
        '组合策略',
        'BV(2,6) 强拉映射统计',
        'ml=65471',
        '高 IR 门限主要用于强拉',
        '结论：在 BV 2–6 的亮度带上',
        'AWB Offset Map概述',
        'AWB Offset Map策略分析',
        '场景大类拆解',
        '重点 Map 列表',
    ]
    for snippet in required_snippets:
        if snippet not in content:
            raise AssertionError(f'报告缺少关键内容: {snippet}')
    logger.info('报告内容校验通过，包含 AWB 减权统计章节。')


if __name__ == '__main__':
    try:
        report = generate_report()
        verify_section(report)
        print(f'生成报告: {report}')
    except Exception as exc:
        logger.exception('生成报告失败: %s', exc)
        sys.exit(1)
