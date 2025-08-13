#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF报告生成辅助方法
==liuq debug== EXIF报告生成辅助方法

作者: 龙sir团队
创建时间: 2025-08-06
版本: 1.0.0
描述: EXIF对比分析报告生成的辅助方法
"""

import json
import logging

logger = logging.getLogger(__name__)


def generate_trend_charts_html(trend_data):
    """生成趋势图区域HTML：每字段1行2列（左折线趋势，右环形变化分布）"""
    charts_html = ""
    for field_name, data in trend_data.items():
        base_id = field_name.replace('.', '_').replace(' ', '_').replace('-', '_')
        line_id = f"chart_{base_id}"
        donut_id = f"dist_{base_id}"
        import html
        safe_field_name = html.escape(field_name)
        charts_html += f"""
        <div class=\"field-section\">
          <div class=\"d-flex align-items-center mb-2\">
            <h3 class=\"me-2 mb-0\">{safe_field_name}</h3>
            <span class=\"pill\">趋势对比</span>
          </div>
          <div class=\"row\">
            <div class=\"col-md-8\">
              <div class=\"chart-container\" style=\"height:320px;\">
                <canvas id=\"{line_id}\" style=\"width:100%;height:100%;display:block;\"></canvas>
              </div>
            </div>
            <div class=\"col-md-4\">
              <div class=\"mb-2\"><strong>变化分布</strong></div>
              <div class=\"chart-container\" style=\"height:320px;\">
                <canvas id=\"{donut_id}\" style=\"width:100%;height:100%;display:block;\"></canvas>
              </div>
            </div>
          </div>
        </div>
        """
    return charts_html


def generate_chart_scripts(trend_data):
    """生成趋势折线与变化分布环形图脚本（简化版，避免语法错误）"""
    scripts = ""
    for field_name, data in trend_data.items():
        base_id = field_name.replace('.', '_').replace(' ', '_').replace('-', '_')
        line_id = f"chart_{base_id}"
        donut_id = f"dist_{base_id}"

        sequence_numbers = data.get('sequence_numbers', [])
        test_values = data.get('test_values', [])
        reference_values = data.get('reference_values', [])

        # 计算变化百分比分布桶：>10%, 1~10%, 0%, -1~-10%, <-10%
        diffs_pct_raw = data.get('diff_percentages', [])
        buckets = {'>10%':0, '1~10%':0, '0%':0, '-1~-10%':0, '<-10%':0}
        for v in diffs_pct_raw:
            try:
                x = float(v)
                if x > 10:
                    buckets['>10%'] += 1
                elif x > 1:
                    buckets['1~10%'] += 1
                elif -1 <= x <= 1:
                    buckets['0%'] += 1
                elif x >= -10:
                    buckets['-1~-10%'] += 1
                else:
                    buckets['<-10%'] += 1
            except Exception:
                continue

        labels = list(buckets.keys())
        values = [buckets[k] for k in labels]
        colors = ['#2ecc71', '#95a5a6', '#3498db', '#f39c12', '#e74c3c']

        safe_title = json.dumps(f"{field_name} 趋势对比")

        script = f"""
// 图表渲染: {field_name}
(function() {{
  function renderChart() {{
    if (typeof Chart === 'undefined') {{
      console.warn('==liuq debug== Chart.js 未加载，等待中... {field_name}');
      setTimeout(renderChart, 200);
      return;
    }}

    console.log('==liuq debug== 开始渲染图表: {field_name}');

    // 折线图
    var ctx = document.getElementById('{line_id}');
    if (ctx) {{
      var c = ctx.getContext('2d');
      new Chart(c, {{
        type: 'line',
        data: {{
          labels: {json.dumps(sequence_numbers)},
          datasets: [
            {{
              label: '测试机',
              data: {json.dumps(test_values)},
              borderColor: '#e91e63',
              backgroundColor: 'rgba(233,30,99,0.15)',
              tension: 0.2,
              pointRadius: 2
            }},
            {{
              label: '对比机',
              data: {json.dumps(reference_values)},
              borderColor: '#3f51b5',
              backgroundColor: 'rgba(63,81,181,0.15)',
              tension: 0.2,
              pointRadius: 2
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            title: {{
              display: true,
              text: {safe_title}
            }},
            legend: {{
              display: true,
              position: 'top'
            }}
          }},
          scales: {{
            x: {{
              display: true,
              title: {{
                display: true,
                text: '序列号'
              }}
            }},
            y: {{
              display: true,
              title: {{
                display: true,
                text: '数值'
              }}
            }}
          }}
        }}
      }});
    }}

    // 环形图
    var dctx = document.getElementById('{donut_id}');
    if (dctx) {{
      var dc = dctx.getContext('2d');
      new Chart(dc, {{
        type: 'doughnut',
        data: {{
          labels: {json.dumps(labels)},
          datasets: [{{
            data: {json.dumps(values)},
            backgroundColor: {json.dumps(colors)},
            hoverOffset: 4
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{
              display: true,
              position: 'right'
            }},
            title: {{
              display: true,
              text: '变化分布'
            }}
          }}
        }}
      }});
    }}
  }}

  // 启动图表渲染
  renderChart();
}})();

"""
        scripts += script
    return scripts


def generate_comparison_table(matched_pairs, selected_fields, trend_data):
    """生成单张多字段的详细数据对比表（参考样式，合并所有字段）"""
    if not matched_pairs or not selected_fields:
        return "<p>没有匹配的数据</p>"

    table_id = "dataTable_all"
    search_id = "tableSearch_all"

    # 第一行表头：文件1 | 文件2 | 相似度 | 每字段名(colspan=3)
    top_row_cells = [
        f'<th onclick="sortTable_all(0)" style="cursor: pointer;">文件1 <i class="fas fa-sort"></i></th>',
        f'<th onclick="sortTable_all(1)" style="cursor: pointer;">文件2 <i class="fas fa-sort"></i></th>',
        f'<th onclick="sortTable_all(2)" style="cursor: pointer;">相似度 <i class="fas fa-sort"></i></th>'
    ]
    for field in selected_fields:
        top_row_cells.append(f'<th colspan="3">{field}</th>')
    top_row = "<tr>" + "".join(top_row_cells) + "</tr>"

    # 第二行表头：空 | 空 | 空 | 处理前/处理后/变化% × fields
    second_row_cells = ["<th></th>", "<th></th>", "<th></th>"]
    # 列索引：前3列已占用，后续列按 3 + i*3 + (0..2)
    col_index = 3
    for _ in selected_fields:
        second_row_cells.append(f'<th onclick="sortTable_all({col_index})" style="cursor: pointer;">处理前 <i class="fas fa-sort"></i></th>'); col_index += 1
        second_row_cells.append(f'<th onclick="sortTable_all({col_index})" style="cursor: pointer;">处理后 <i class="fas fa-sort"></i></th>'); col_index += 1
        second_row_cells.append(f'<th onclick="sortTable_all({col_index})" style="cursor: pointer;">变化% <i class="fas fa-sort"></i></th>'); col_index += 1
    second_row = "<tr>" + "".join(second_row_cells) + "</tr>"

    # 组装表头
    header_html = f"""
<div class=\"mb-3\">\n  <input type=\"text\" id=\"{search_id}\" class=\"form-control\" placeholder=\"🔍 搜索表格内容...\" style=\"max-width: 300px;\">\n</div>\n<div class=\"table-container\">\n  <table id=\"{table_id}\" class=\"table table-striped table-hover\">\n    <thead class=\"table-dark\">\n      {top_row}\n      {second_row}\n    </thead>\n    <tbody>\n"""

    # 数据行
    body_rows = []
    for pair in matched_pairs:
        file1 = pair.get('filename1', '')
        file2 = pair.get('filename2', '')
        similarity = pair.get('similarity', 0)
        row_cells = [f"<td>{file1}</td>", f"<td>{file2}</td>", f"<td>{float(similarity):.3f}</td>"]

        for field in selected_fields:
            test_val = pair.get('test_data', {}).get(field, 'N/A')
            ref_val = pair.get('reference_data', {}).get(field, 'N/A')
            before_txt = test_val
            after_txt = ref_val
            change_txt = 'N/A'
            cls = 'change-neutral'
            try:
                t = float(test_val)
                r = float(ref_val)
                before_txt = f"{t:.6f}"
                after_txt = f"{r:.6f}"
                denom = t if t != 0 else 1.0
                change_pct = (r - t) / denom * 100.0
                if change_pct > 0:
                    cls = 'change-positive'
                elif change_pct < 0:
                    cls = 'change-negative'
                change_txt = f"{change_pct:.2f}%"
            except Exception:
                pass
            row_cells.extend([f"<td>{before_txt}</td>", f"<td>{after_txt}</td>", f"<td class=\"{cls}\">{change_txt}</td>"])
        body_rows.append("<tr>" + "".join(row_cells) + "</tr>")

    footer_html = """
    </tbody>
  </table>
</div>
"""

    # 搜索与排序脚本（与参考逻辑一致，基于单表）
    script_html = f"""
<script>
(function(){{
  // 搜索
  var input=document.getElementById('{search_id}');
  if(input){{
    input.addEventListener('keyup',function(){{
      var filter=this.value.toLowerCase();
      var table=document.getElementById('{table_id}');
      if(!table) return; var rows=table.tBodies[0].rows; for(var i=0;i<rows.length;i++){{
        var txt=rows[i].textContent.toLowerCase(); rows[i].style.display = txt.indexOf(filter)!==-1? '':'none';
      }}
    }});
  }}
  // 排序（按绝对值排序数值/百分比；字符串则字典序）
  var sortDirection = {{}};
  window.sortTable_all=function(col){{
    var table=document.getElementById('{table_id}'); if(!table) return; var tbody=table.tBodies[0]; var rows=Array.prototype.slice.call(tbody.rows);
    sortDirection[col] = sortDirection[col] === 'asc' ? 'desc' : 'asc';
    var asc = sortDirection[col] === 'asc';
    rows.sort(function(a,b){{
      var av=a.cells[col].textContent.trim(); var bv=b.cells[col].textContent.trim();
      var an=parseFloat(av.replace('%','')); var bn=parseFloat(bv.replace('%',''));
      var res=0; if(!isNaN(an)&&!isNaN(bn)) res=Math.abs(an)-Math.abs(bn); else res=av.localeCompare(bv);
      return asc?res:-res;
    }});
    rows.forEach(function(r){{tbody.appendChild(r);}});
  }}
}})();
</script>
"""

    return header_html + "".join(body_rows) + footer_html + script_html



def _calc_basic_metrics(test_values, ref_values):
    """计算基础误差指标: MAE, RMSE, R2"""
    try:
        n = min(len(test_values), len(ref_values))
        if n == 0:
            return {'mae': 0.0, 'rmse': 0.0, 'r2': 0.0}
        tv = test_values[:n]
        rv = ref_values[:n]
        diffs = [t - r for t, r in zip(tv, rv)]
        mae = sum(abs(d) for d in diffs) / n
        rmse = (sum(d*d for d in diffs) / n) ** 0.5
        mean_r = sum(rv) / n
        ss_tot = sum((r - mean_r)**2 for r in rv)
        ss_res = sum((t - r)**2 for t, r in zip(tv, rv))
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        return {'mae': mae, 'rmse': rmse, 'r2': r2}
    except Exception:
        return {'mae': 0.0, 'rmse': 0.0, 'r2': 0.0}


def generate_kpi_cards(trend_data):
    """生成KPI卡片：每字段 MAE / RMSE / R² / 异常率"""
    if not trend_data:
        return "<p class=\"muted\">无可用数据</p>"
    cards = ["<div class=\"kpi-cards\">"]

    # 定义图标映射
    field_icons = {
        'color_sensor_irRatio': 'fas fa-eye',
        'meta_data_currentFrame_bv': 'fas fa-sun',
        'meta_data_currentFrame_iso': 'fas fa-camera',
        'meta_data_currentFrame_exposureTime': 'fas fa-clock',
        'meta_data_currentFrame_fNumber': 'fas fa-adjust',
        'meta_data_currentFrame_focalLength': 'fas fa-search',
        'default': 'fas fa-chart-bar'
    }

    for field, d in trend_data.items():
        test_vals = d.get('test_values', [])
        ref_vals = d.get('reference_values', [])
        diffs_pct = d.get('diff_percentages', [])
        m = _calc_basic_metrics(test_vals, ref_vals)

        # 简单异常率：|差值%|>10% 视为异常
        abnormal = 0
        total = len(diffs_pct)
        for v in diffs_pct:
            try:
                if abs(float(v)) > 10:
                    abnormal += 1
            except Exception:
                pass
        rate = (abnormal * 100.0 / total) if total else 0.0

        # 选择合适的图标
        icon = field_icons.get(field, field_icons['default'])

        # 格式化字段名显示
        display_name = field.replace('_', ' ').replace('meta data', '').replace('currentFrame', '').strip()
        if not display_name:
            display_name = field

        # 确定异常率的颜色
        rate_color = '#2e7d32' if rate < 5 else '#ef6c00' if rate < 15 else '#d32f2f'

        cards.append(f"""
            <div class='kpi-card'>
                <div class='kpi-title'>
                    <i class='{icon}'></i> {display_name}
                </div>
                <div class='row text-center'>
                    <div class='col-6'>
                        <div class='kpi-value' style='font-size: 1.2rem; color: #495057;'>
                            {m['mae']:.3f}
                        </div>
                        <small class='text-muted'>MAE</small>
                    </div>
                    <div class='col-6'>
                        <div class='kpi-value' style='font-size: 1.2rem; color: #495057;'>
                            {m['rmse']:.3f}
                        </div>
                        <small class='text-muted'>RMSE</small>
                    </div>
                </div>
                <div class='row text-center mt-2'>
                    <div class='col-6'>
                        <div class='kpi-value' style='font-size: 1.2rem; color: #495057;'>
                            {m['r2']:.3f}
                        </div>
                        <small class='text-muted'>R²</small>
                    </div>
                    <div class='col-6'>
                        <div class='kpi-value' style='font-size: 1.2rem; color: {rate_color};'>
                            {rate:.1f}%
                        </div>
                        <small class='text-muted'>异常率</small>
                    </div>
                </div>
            </div>
        """)
    cards.append("</div>")
    return "".join(cards)


def generate_topn_anomaly_table(trend_data, topn=10):
    """生成异常样本TopN表：按任意字段的绝对差值%排序，取全局TopN"""
    if not trend_data:
        return "<p class=\"muted\">无异常样本</p>"
    rows = []
    for field, d in trend_data.items():
        seq = d.get('sequence_numbers', [])
        diffs_pct = d.get('diff_percentages', [])
        for i in range(min(len(seq), len(diffs_pct))):
            try:
                rows.append((abs(float(diffs_pct[i])), field, seq[i], diffs_pct[i]))
            except Exception:
                continue
    rows.sort(reverse=True, key=lambda x: x[0])
    rows = rows[:topn]
    if not rows:
        return "<p class=\"muted\">无异常样本</p>"
    html = [
        "<table><thead><tr><th>字段</th><th>序列号</th><th>差值%</th></tr></thead><tbody>"
    ]
    for _, field, seq, pct in rows:
        cls = 'highlight-high' if abs(float(pct)) > 10 else ('highlight-medium' if abs(float(pct)) > 5 else '')
        html.append(f"<tr class='{cls}'><td>{field}</td><td>{seq}</td><td>{float(pct):.2f}%</td></tr>")
    html.append("</tbody></table>")
    return "".join(html)


def generate_statistics_table(statistics_data):
    """生成统计摘要表"""
    if not statistics_data:
        return "<p>没有统计数据</p>"

    table_html = """
    <table>
        <thead>
            <tr>
                <th>字段名</th>
                <th>测试机均值</th>
                <th>对比机均值</th>
                <th>测试机范围</th>
                <th>对比机范围</th>
                <th>平均差值</th>
                <th>平均差值百分比</th>
            </tr>
        </thead>
        <tbody>
    """

    for field_name, stats in statistics_data.items():
        test_mean = stats.get('test_mean', 0)
        ref_mean = stats.get('ref_mean', 0)
        test_min = stats.get('test_min', 0)
        test_max = stats.get('test_max', 0)
        ref_min = stats.get('ref_min', 0)
        ref_max = stats.get('ref_max', 0)
        mean_diff = stats.get('mean_diff', 0)
        mean_diff_percent = stats.get('mean_diff_percentage', 0)

        # 设置高亮
        highlight_class = ''
        if abs(mean_diff_percent) > 10:
            highlight_class = 'highlight-high'
        elif abs(mean_diff_percent) > 5:
            highlight_class = 'highlight-medium'

        table_html += f"""
            <tr>
                <td>{field_name}</td>
                <td>{test_mean:.4f}</td>
                <td>{ref_mean:.4f}</td>
                <td>{test_min:.4f} ~ {test_max:.4f}</td>
                <td>{ref_min:.4f} ~ {ref_max:.4f}</td>
                <td class="{highlight_class}">{mean_diff:.4f}</td>
                <td class="{highlight_class}">{mean_diff_percent:.2f}%</td>
            </tr>
        """

    table_html += """
        </tbody>
    </table>
    """

    return table_html
