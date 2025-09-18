from __future__ import annotations

from typing import Any, Dict, List

from core.services.reporting.infrastructure import TemplateRenderer


def _prepare_trend_chart_models(trend_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    charts: List[Dict[str, Any]] = []
    if not trend_data:
        return charts

    for field_name, data in trend_data.items():
        if not isinstance(data, dict):
            continue

        sequence_numbers = data.get('sequence_numbers', [])
        test_values = data.get('test_values', [])
        ref_values = data.get('ref_values', [])

        if not sequence_numbers or len(sequence_numbers) < 2:
            continue

        charts.append({
            'field_name': field_name,
            'sequence_numbers': sequence_numbers,
            'test_values': test_values,
            'ref_values': ref_values,
            'chart_id': f"chart_{field_name.replace(' ', '_')}"
        })

    return charts


def generate_trend_charts_html(trend_data: Dict[str, Any]) -> str:
    charts = _prepare_trend_chart_models(trend_data)
    if not charts:
        return "<p>没有趋势数据</p>"

    renderer = TemplateRenderer()
    return renderer.render(
        'reporting/domains/exif/_trend_charts_block.html',
        {
            'charts': charts,
            'mode': 'html',
        }
    )


def generate_chart_scripts(trend_data: Dict[str, Any]) -> str:
    charts = _prepare_trend_chart_models(trend_data)
    if not charts:
        return ''

    renderer = TemplateRenderer()
    return renderer.render(
        'reporting/domains/exif/_trend_charts_block.html',
        {
            'charts': charts,
            'mode': 'script',
        }
    )
