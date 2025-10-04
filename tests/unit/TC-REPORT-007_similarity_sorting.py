#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证EXIF对比报告根据相似度排序的能力。"""

from __future__ import annotations

from core.services.reporting.domains.exif.comparison_report_service import (
    ExifComparisonReportGenerator,
)


def _build_pair(name: str, similarity: float, before: float, after: float) -> dict:
    return {
        'filename1': f'test_{name}.jpg',
        'filename2': f'ref_{name}.jpg',
        'similarity': similarity,
        'test_data': {'demo_field': before},
        'reference_data': {'demo_field': after},
    }


def test_comparison_rows_keeps_original_order_when_not_sorted():
    generator = ExifComparisonReportGenerator()
    pairs = [
        _build_pair('a', 0.75, 1.0, 1.2),
        _build_pair('b', 0.95, 2.0, 2.1),
        _build_pair('c', 0.65, 3.0, 2.7),
    ]

    rows = generator._build_comparison_rows(pairs, ['demo_field'], sort_by_similarity=False)

    assert [row['filename1'] for row in rows] == [
        'test_a.jpg',
        'test_b.jpg',
        'test_c.jpg',
    ]
    assert [row['rank'] for row in rows] == [1, 2, 3]


def test_comparison_rows_sorted_by_similarity_descending():
    generator = ExifComparisonReportGenerator()
    pairs = [
        _build_pair('a', 0.75, 1.0, 1.2),
        _build_pair('b', 0.95, 2.0, 2.1),
        _build_pair('c', 0.65, 3.0, 2.7),
    ]

    rows = generator._build_comparison_rows(pairs, ['demo_field'], sort_by_similarity=True)

    assert [row['filename1'] for row in rows] == [
        'test_b.jpg',
        'test_a.jpg',
        'test_c.jpg',
    ]
    assert [row['rank'] for row in rows] == [1, 2, 3]
    assert rows[0]['cells'][0]['change_pct'] == '5.00%'
