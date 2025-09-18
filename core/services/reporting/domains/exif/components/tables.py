from __future__ import annotations

from typing import Any, Dict, List, Tuple

from core.services.reporting.infrastructure import TemplateRenderer


def generate_comparison_table(matched_pairs, selected_fields, trend_data) -> str:
    if not matched_pairs or not selected_fields:
        return "<p>没有匹配数据</p>"

    def to_num(val):
        try:
            if val is None:
                return None
            s = str(val).strip()
            if s == '' or s.lower() == 'nan':
                return None
            return float(s)
        except Exception:
            return None

    rows = []
    for pair in matched_pairs:
        filename1 = pair.get('filename1', '')
        filename2 = pair.get('filename2', '')
        similarity = pair.get('similarity', 0)
        cells = []
        for field in selected_fields:
            t = pair.get('test_data', {}).get(field, 'N/A')
            r = pair.get('reference_data', {}).get(field, 'N/A')
            tn = to_num(t)
            rn = to_num(r)
            before_txt = f"{tn:.6f}" if tn is not None else str(t)
            after_txt = f"{rn:.6f}" if rn is not None else str(r)
            change_txt = 'N/A'
            cls = 'change-neutral'
            if tn is not None and rn is not None:
                change_pct = ((rn - tn) / tn * 100.0) if tn != 0 else 0.0
                change_txt = f"{change_pct:.2f}%"
                if change_pct > 0:
                    cls = 'change-positive'
                elif change_pct < 0:
                    cls = 'change-negative'
            cells.append({'before': before_txt, 'after': after_txt, 'change_pct': change_txt, 'cls': cls})
        rows.append({'filename1': filename1, 'filename2': filename2, 'similarity': similarity, 'cells': cells})

    renderer = TemplateRenderer()
    ctx = {
        'table_id': 'dataTable_all',
        'search_id': 'tableSearch_all',
        'selected_fields': selected_fields,
        'rows': rows,
    }
    return renderer.render('reporting/domains/exif/_comparison_table.html', ctx)


def generate_statistics_table(statistics_data: Dict[str, Any]) -> str:
    if not statistics_data:
        return "<p>没有统计数据</p>"
    rows = []
    for field_name, stats in statistics_data.items():
        rows.append({
            'field_name': field_name,
            'test_mean': stats.get('test_mean', 0),
            'ref_mean': stats.get('ref_mean', 0),
            'test_min': stats.get('test_min', 0),
            'test_max': stats.get('test_max', 0),
            'ref_min': stats.get('ref_min', 0),
            'ref_max': stats.get('ref_max', 0),
            'mean_diff': stats.get('mean_diff', 0),
            'mean_diff_percent': stats.get('mean_diff_percentage', 0),
        })
    renderer = TemplateRenderer()
    return renderer.render('reporting/domains/exif/_statistics_table.html', {'rows': rows})


def generate_topn_anomaly_table(trend_data: Dict[str, Any], topn: int = 10) -> str:
    if not trend_data:
        return "<p class=\"muted\">无异常样本</p>"
    rows = []
    for field, d in trend_data.items():
        seq = d.get('sequence_numbers', [])
        diffs_pct = d.get('diff_percentages', [])
        for i in range(min(len(seq), len(diffs_pct))):
            try:
                pct = float(diffs_pct[i])
            except Exception:
                continue
            rows.append({'field': field, 'sequence': seq[i], 'pct': pct})
    rows.sort(key=lambda x: abs(x['pct']), reverse=True)
    rows = rows[:topn]
    renderer = TemplateRenderer()
    return renderer.render('reporting/domains/exif/_topn_table.html', {'rows': rows})
