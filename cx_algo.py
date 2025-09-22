#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standalone helper that reuses the offset-map query service for AWB analysis."""

from pathlib import Path

from core.services.map_analysis.xml_parser_service import XMLParserService
from core.services.map_analysis.offset_map_query_service import (
    OffsetMapQueryService,
    OffsetMapQuerySpec,
    RangeWindow,
    build_report_section,
)

BV_WINDOW = (2.0, 6.0)
CT_WINDOW = (1500.0, 3800.0)
REDUCE_WEIGHT_ML = 65535


def build_default_spec() -> OffsetMapQuerySpec:
    return OffsetMapQuerySpec(
        name="BV(2,6)_CT(1500,3800)_ml65535",
        title="BV(2,6) × 色温1500–3800 减权统计",
        ml=REDUCE_WEIGHT_ML,
        range_windows={
            'bv': RangeWindow(key='bv', lower=BV_WINDOW[0], upper=BV_WINDOW[1], label='BV', description='BV ∈ (2, 6)'),
            'ctemp': RangeWindow(key='ctemp', lower=CT_WINDOW[0], upper=CT_WINDOW[1], label='色温', description='色温段与 1500–3800 K 有交集'),
        },
        metadata={
            'narrative_id': 'awb_reduce_default',
            'methodology_lines': [
                "- 直接解析项目自带的 `tests/test_data/awb_scenario.xml` 场景文件，在每个 `offset_map` 的 `<range>` 段里读取 BV、色温、权重与 `ml`，并结合同名节点下的 `<AliasName>` 获取别名信息，确认这些节点既包含原始量程也标注了 `ml=65535`（减小权重）的场景。",
            ],
        },
    )


def print_section(section: dict) -> None:
    print("### 统计方法")
    for line in section.get('methodology', []):
        print(line)
    print()

    print("### 统计概览")
    for line in section.get('overview', []):
        print(line)
    print()

    table = section.get('table', {})
    headers = table.get('headers', [])
    rows = table.get('rows', [])
    if headers and rows:
        print("### 详细列表")
        print("| " + " | ".join(headers) + " |")
        print("| " + " | ".join(['---'] * len(headers)) + " |")
        for row in rows:
            axis_values = list(row['ranges'].values())
            values = [row['tag'], row['alias'], row['weight'], *axis_values]
            print("| " + " | ".join(values) + " |")
        print()

    highlights = section.get('highlights', [])
    if highlights:
        print("### 重点说明")
        for line in highlights:
            print(line)
        print()


def main() -> None:
    xml_path = Path('tests/test_data/awb_scenario.xml')
    parser = XMLParserService()
    config = parser.parse_xml(xml_path)

    service = OffsetMapQueryService(config.map_points)
    spec = build_default_spec()
    result = service.run_query(spec)
    section = build_report_section(result)
    print_section(section)


if __name__ == '__main__':
    main()
