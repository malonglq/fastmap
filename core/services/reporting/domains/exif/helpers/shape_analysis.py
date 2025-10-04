#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计点形状分析工具。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils.awb_stats_tools import (
    get_stats_points,
    StatsPointSet,
    parse_awb_stats_from_json_file,
)

logger = logging.getLogger(__name__)


@dataclass
class ShapeAnalysisMetrics:
    """统计点形状分析的量化结果。"""

    histogram_similarity: float
    centroid_similarity: float
    coverage_overlap: float
    score: float
    histogram_l1_distance: float
    centroid_distance_ratio: float


class StatsShapeAnalyzer:
    """负责比较两组AWB统计点的形状相似度并输出图像。"""

    def __init__(self, bins: int = 64) -> None:
        self.bins = max(8, bins)

    def analyze(
        self,
        test_image_path: str | Path,
        reference_image_path: str | Path,
        output_image_path: str | Path,
    ) -> Dict[str, Any]:
        """执行形状分析并返回结果字典。"""

        test_stats = self._load_stats_points(test_image_path)
        reference_stats = self._load_stats_points(reference_image_path)

        if test_stats is None:
            raise ValueError(f"无法解析测试机统计点: {test_image_path}")
        if reference_stats is None:
            raise ValueError(f"无法解析对比机统计点: {reference_image_path}")

        test_points = np.array(test_stats.to_xy(corrected=True), dtype=float)
        reference_points = np.array(reference_stats.to_xy(corrected=True), dtype=float)
        if test_points.size == 0 or reference_points.size == 0:
            raise ValueError("统计点数量为空，无法进行形状分析")

        metrics = self._compute_metrics(test_points, reference_points)
        self._render_figure(
            test_points,
            reference_points,
            metrics,
            test_image_path,
            reference_image_path,
            output_image_path,
        )

        return {
            'score': round(metrics.score * 100, 2),
            'histogram_similarity': round(metrics.histogram_similarity, 4),
            'centroid_similarity': round(metrics.centroid_similarity, 4),
            'coverage_overlap': round(metrics.coverage_overlap, 4),
            'histogram_l1_distance': round(metrics.histogram_l1_distance, 4),
            'centroid_distance_ratio': round(metrics.centroid_distance_ratio, 4),
            'test_points': len(test_points),
            'reference_points': len(reference_points),
            'test_image_path': str(Path(test_image_path).resolve()),
            'reference_image_path': str(Path(reference_image_path).resolve()),
            'summary': self._build_summary(metrics),
        }

    def _load_stats_points(self, path: str | Path) -> Optional[StatsPointSet]:
        source = Path(path)
        try:
            stats = get_stats_points(source)
            if stats:
                return stats
        except Exception as exc:  # noqa: BLE001
            logger.warning("==liuq debug== 加载统计点失败 %s: %s", source, exc)

        if source.suffix.lower() != '.json':
            for suffix in ('.awb.json', '.json'):
                candidate = source.with_suffix(suffix)
                if candidate.exists():
                    try:
                        return parse_awb_stats_from_json_file(candidate)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("==liuq debug== JSON备选解析失败 %s: %s", candidate, exc)
        return None

    def _compute_metrics(self, test_pts: np.ndarray, reference_pts: np.ndarray) -> ShapeAnalysisMetrics:
        combined = np.vstack((test_pts, reference_pts))
        min_vals = combined.min(axis=0)
        max_vals = combined.max(axis=0)
        span = np.maximum(max_vals - min_vals, 1e-6)
        margin = span * 0.05
        min_vals -= margin
        max_vals += margin

        bins = self.bins
        hist_test, xedges, yedges = np.histogram2d(
            test_pts[:, 0],
            test_pts[:, 1],
            bins=bins,
            range=[[min_vals[0], max_vals[0]], [min_vals[1], max_vals[1]]],
        )
        hist_ref, _, _ = np.histogram2d(
            reference_pts[:, 0],
            reference_pts[:, 1],
            bins=[xedges, yedges],
        )

        hist_test_norm = self._normalize_hist(hist_test)
        hist_ref_norm = self._normalize_hist(hist_ref)

        l1_distance = float(np.abs(hist_test_norm - hist_ref_norm).sum())
        histogram_similarity = max(0.0, 1.0 - 0.5 * l1_distance)

        centroid_test = test_pts.mean(axis=0)
        centroid_ref = reference_pts.mean(axis=0)
        diagonal = float(np.linalg.norm(max_vals - min_vals)) or 1.0
        centroid_distance = float(np.linalg.norm(centroid_test - centroid_ref))
        centroid_distance_ratio = centroid_distance / diagonal
        centroid_similarity = max(0.0, 1.0 - centroid_distance_ratio)

        coverage_overlap = self._compute_coverage_overlap(test_pts, reference_pts)

        score = histogram_similarity * 0.7 + centroid_similarity * 0.2 + coverage_overlap * 0.1

        return ShapeAnalysisMetrics(
            histogram_similarity=histogram_similarity,
            centroid_similarity=centroid_similarity,
            coverage_overlap=coverage_overlap,
            score=score,
            histogram_l1_distance=l1_distance,
            centroid_distance_ratio=centroid_distance_ratio,
        )

    @staticmethod
    def _normalize_hist(hist: np.ndarray) -> np.ndarray:
        total = hist.sum()
        if total <= 0:
            return hist
        return hist / total

    def _compute_coverage_overlap(
        self,
        test_pts: np.ndarray,
        reference_pts: np.ndarray,
    ) -> float:
        """在归一化坐标系中计算覆盖重叠率，避免整体偏移的影响。"""

        norm_test, norm_ref = self._align_shape_points(test_pts, reference_pts)

        if norm_test.size == 0 or norm_ref.size == 0:
            return 0.0

        distances = np.linalg.norm(
            norm_test[:, None, :] - norm_ref[None, :, :],
            axis=2,
        )
        min_dist_test = distances.min(axis=1)
        min_dist_ref = distances.min(axis=0)
        avg_min_dist = float((min_dist_test.mean() + min_dist_ref.mean()) / 2.0)

        combined = np.vstack((norm_test, norm_ref))
        scale = float(np.linalg.norm(combined.max(axis=0) - combined.min(axis=0)))
        if scale <= 1e-6:
            scale = 1.0
        normalized_dist = min(avg_min_dist / scale, 1.0)
        return max(0.0, 1.0 - normalized_dist)

    @staticmethod
    def _align_shape_points(
        test_pts: np.ndarray,
        reference_pts: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """通过Procrustes对齐实现平移、缩放、旋转不变的形状比较。"""

        if test_pts.size == 0 or reference_pts.size == 0:
            return test_pts, reference_pts

        test_centered = test_pts - test_pts.mean(axis=0)
        ref_centered = reference_pts - reference_pts.mean(axis=0)

        test_norm = float(np.linalg.norm(test_centered))
        ref_norm = float(np.linalg.norm(ref_centered))

        if test_norm <= 1e-12 or ref_norm <= 1e-12:
            return test_centered, ref_centered

        test_scaled = test_centered / test_norm
        ref_scaled = ref_centered / ref_norm

        covariance = test_scaled.T @ ref_scaled
        U, _, Vt = np.linalg.svd(covariance)
        rotation = U @ Vt

        if np.linalg.det(rotation) < 0:
            U[:, -1] *= -1
            rotation = U @ Vt

        aligned_test = test_scaled @ rotation
        return aligned_test, ref_scaled

    def _render_figure(
        self,
        test_pts: np.ndarray,
        reference_pts: np.ndarray,
        metrics: ShapeAnalysisMetrics,
        test_image_path: str | Path,
        reference_image_path: str | Path,
        output_image_path: str | Path,
    ) -> None:
        output_path = Path(output_image_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        axes[0].scatter(test_pts[:, 0], test_pts[:, 1], s=8, c='#1f77b4', alpha=0.6)
        axes[0].set_title('测试机统计点')
        axes[0].set_xlabel('R/G')
        axes[0].set_ylabel('B/G')
        axes[0].grid(True, linestyle='--', alpha=0.3)
        axes[0].set_xlim(0.0, 1.7)
        axes[0].set_ylim(0.0, 2.0)

        axes[1].scatter(reference_pts[:, 0], reference_pts[:, 1], s=8, c='#d62728', alpha=0.6)
        axes[1].set_title('对比机统计点')
        axes[1].set_xlabel('R/G')
        axes[1].set_ylabel('B/G')
        axes[1].grid(True, linestyle='--', alpha=0.3)
        axes[1].set_xlim(0.0, 1.7)
        axes[1].set_ylim(0.0, 2.0)

        axes[2].scatter(test_pts[:, 0], test_pts[:, 1], s=6, c='#1f77b4', alpha=0.35, label='测试机')
        axes[2].scatter(reference_pts[:, 0], reference_pts[:, 1], s=6, c='#d62728', alpha=0.35, label='对比机')
        axes[2].legend(loc='best')
        axes[2].set_title(f"相似度评分: {metrics.score * 100:.1f}")
        axes[2].set_xlabel('R/G')
        axes[2].set_ylabel('B/G')
        axes[2].grid(True, linestyle='--', alpha=0.3)
        axes[2].set_xlim(0.0, 1.7)
        axes[2].set_ylim(0.0, 2.0)

        summary = self._build_summary(metrics)
        fig.suptitle(
            f"统计点形状分析\n{summary}",
            fontsize=12,
            y=0.95,
        )

        fig.tight_layout()
        fig.savefig(output_path, dpi=160)
        plt.close(fig)

    @staticmethod
    def _build_summary(metrics: ShapeAnalysisMetrics) -> str:
        return (
            f"直方图相似度 {metrics.histogram_similarity * 100:.1f}% | "
            f"质心相似度 {metrics.centroid_similarity * 100:.1f}% | "
            f"覆盖重叠 {metrics.coverage_overlap * 100:.1f}%"
        )


__all__ = ['StatsShapeAnalyzer', 'ShapeAnalysisMetrics']
