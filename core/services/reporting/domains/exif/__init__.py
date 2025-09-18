"""EXIF reporting domain exports."""

from .comparison_report_service import ExifComparisonReportGenerator
from .components.charts import generate_trend_charts_html, generate_chart_scripts
from .components.kpi_cards import generate_kpi_cards
from .components.tables import (
    generate_comparison_table,
    generate_statistics_table,
    generate_topn_anomaly_table,
)
from .components.rpg_bpg_analysis import generate_per_image_rpg_bpg_analysis
from .helpers.comparison_helpers import (
    generate_sgw_baseline_analysis,
    generate_statistics_table as legacy_generate_statistics_table,
    generate_kpi_cards as legacy_generate_kpi_cards,
    generate_comparison_table as legacy_generate_comparison_table,
    generate_per_image_rpg_bpg_analysis as legacy_generate_per_image_rpg_bpg_analysis,
    generate_topn_anomaly_table as legacy_generate_topn_anomaly_table,
)

__all__ = [
    'ExifComparisonReportGenerator',
    'generate_trend_charts_html',
    'generate_chart_scripts',
    'generate_kpi_cards',
    'generate_comparison_table',
    'generate_per_image_rpg_bpg_analysis',
    'generate_statistics_table',
    'generate_topn_anomaly_table',
    'generate_sgw_baseline_analysis',
    'legacy_generate_statistics_table',
    'legacy_generate_kpi_cards',
    'legacy_generate_comparison_table',
    'legacy_generate_per_image_rpg_bpg_analysis',
    'legacy_generate_topn_anomaly_table',
]
