"""Reporting domain packages (EXIF, MAP, etc.)."""

from .exif import (
    ExifComparisonReportGenerator,
    generate_trend_charts_html,
    generate_chart_scripts,
    generate_comparison_table,
    generate_statistics_table,
    generate_topn_anomaly_table,
    generate_kpi_cards,
    generate_per_image_rpg_bpg_analysis,
    legacy_generate_statistics_table,
    legacy_generate_kpi_cards,
    legacy_generate_comparison_table,
    legacy_generate_per_image_rpg_bpg_analysis,
    generate_sgw_baseline_analysis,
    legacy_generate_topn_anomaly_table,
)
from .map import MapMultiDimensionalReportGenerator

__all__ = [
    'ExifComparisonReportGenerator',
    'generate_trend_charts_html',
    'generate_chart_scripts',
    'generate_comparison_table',
    'generate_statistics_table',
    'generate_topn_anomaly_table',
    'generate_kpi_cards',
    'generate_per_image_rpg_bpg_analysis',
    'legacy_generate_statistics_table',
    'legacy_generate_kpi_cards',
    'legacy_generate_comparison_table',
    'legacy_generate_per_image_rpg_bpg_analysis',
    'generate_sgw_baseline_analysis',
    'legacy_generate_topn_anomaly_table',
    'MapMultiDimensionalReportGenerator',
]
