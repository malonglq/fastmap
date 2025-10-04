#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TC-MAP-013: 验证统计点形状分析相似度评分。"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from core.services.reporting.domains.exif.helpers.shape_analysis import StatsShapeAnalyzer


def test_shape_analyzer_generates_score(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    test_image = repo_root / "tests/test_data/SZAWBAE1770_1X_25001_S_IMG20250101064624.jpg"
    reference_image = repo_root / "tests/test_data/SZAWBAE1770_1X_24087_S_IMG20250929164322.jpg"

    output_path = tmp_path / "shape_analysis.png"
    analyzer = StatsShapeAnalyzer(bins=32)
    result = analyzer.analyze(test_image, reference_image, output_path)

    assert output_path.exists(), "应生成形状对比图"
    assert 0 <= result['score'] <= 100
    assert 'histogram_similarity' in result
    assert 'centroid_similarity' in result
    assert 'coverage_overlap' in result


def test_coverage_overlap_ignores_global_translation():
    analyzer = StatsShapeAnalyzer(bins=16)
    base = np.array(
        [
            [0.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
            [0.5, 0.25],
            [0.25, 0.75],
        ]
    )
    shifted = base + np.array([5.0, -3.0])

    metrics = analyzer._compute_metrics(base, shifted)

    assert metrics.coverage_overlap > 0.98, "整体平移后应保持高覆盖重叠率"


def test_coverage_overlap_handles_rotation():
    analyzer = StatsShapeAnalyzer(bins=16)
    base = np.array(
        [
            [-1.0, 0.0],
            [1.0, 0.0],
            [0.0, 0.5],
            [0.0, -0.5],
        ]
    )

    theta = np.deg2rad(60)
    rotation = np.array(
        [
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ]
    )
    rotated = base @ rotation.T

    metrics = analyzer._compute_metrics(base, rotated)

    assert metrics.coverage_overlap > 0.95, "旋转后的形状应保持高覆盖重叠率"
