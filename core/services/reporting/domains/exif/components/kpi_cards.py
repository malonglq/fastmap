from __future__ import annotations

from typing import Any, Dict

from math import sqrt
from core.services.reporting.infrastructure import TemplateRenderer


def _calc_basic_metrics(test_vals, ref_vals):
    try:
        n = min(len(test_vals), len(ref_vals))
        if n == 0:
            return {'mae': 0.0, 'rmse': 0.0, 'r2': 0.0}
        tv = [float(x) for x in test_vals[:n]]
        rv = [float(x) for x in ref_vals[:n]]
        mae = sum(abs(t - r) for t, r in zip(tv, rv)) / n
        rmse = sqrt(sum((t - r) ** 2 for t, r in zip(tv, rv)) / n)
        mean_r = sum(rv) / n
        ss_tot = sum((r - mean_r) ** 2 for r in rv)
        ss_res = sum((t - r) ** 2 for t, r in zip(tv, rv))
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        return {'mae': mae, 'rmse': rmse, 'r2': r2}
    except Exception:
        return {'mae': 0.0, 'rmse': 0.0, 'r2': 0.0}


def generate_kpi_cards(trend_data: Dict[str, Any]) -> str:
    if not trend_data:
        return "<p class=\"muted\">无可用数据</p>"

    field_icons = {
        'color_sensor_irRatio': 'fas fa-eye',
        'meta_data_currentFrame_bv': 'fas fa-sun',
        'meta_data_currentFrame_iso': 'fas fa-camera',
        'meta_data_currentFrame_exposureTime': 'fas fa-clock',
        'meta_data_currentFrame_fNumber': 'fas fa-adjust',
        'meta_data_currentFrame_focalLength': 'fas fa-search',
        'default': 'fas fa-chart-bar'
    }

    items = []
    for field, d in trend_data.items():
        test_vals = d.get('test_values', [])
        ref_vals = d.get('reference_values', [])
        diffs_pct = d.get('diff_percentages', [])
        metrics = _calc_basic_metrics(test_vals, ref_vals)

        abnormal = 0
        total = len(diffs_pct)
        for v in diffs_pct:
            try:
                if abs(float(v)) > 10:
                    abnormal += 1
            except Exception:
                pass
        rate = (abnormal * 100.0 / total) if total else 0.0

        icon = field_icons.get(field, field_icons['default'])
        display_name = field.replace('_', ' ').replace('meta data', '').replace('currentFrame', '').strip() or field
        rate_color = '#2e7d32' if rate < 5 else ('#ef6c00' if rate < 15 else '#d32f2f')

        items.append({
            'field': field,
            'display_name': display_name,
            'icon': icon,
            'metrics': metrics,
            'abnormal_rate': rate,
            'rate_color': rate_color,
        })

    renderer = TemplateRenderer()
    return renderer.render('reporting/domains/exif/_kpi_cards.html', {'items': items})
