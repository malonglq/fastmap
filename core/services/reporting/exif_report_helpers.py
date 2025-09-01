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
    # 为前两列添加sticky定位类
    top_row_cells = [
        f'<th class="sticky-col sticky-col-1" onclick="sortTable_all(0)" style="cursor: pointer; min-width: 200px;">文件1 (image_name) <i class="fas fa-sort"></i></th>',
        f'<th class="sticky-col sticky-col-2" onclick="sortTable_all(1)" style="cursor: pointer; min-width: 200px;">文件2 (sequence_number) <i class="fas fa-sort"></i></th>',
        f'<th onclick="sortTable_all(2)" style="cursor: pointer;">相似度 <i class="fas fa-sort"></i></th>'
    ]
    for field in selected_fields:
        top_row_cells.append(f'<th colspan="3">{field}</th>')
    top_row = "<tr>" + "".join(top_row_cells) + "</tr>"

    # 第二行表头：空 | 空 | 空 | 处理前/处理后/变化% × fields
    # 为前两列添加sticky定位类
    second_row_cells = [
        '<th class="sticky-col sticky-col-1"></th>',
        '<th class="sticky-col sticky-col-2"></th>',
        '<th></th>'
    ]
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
        # 为前两列添加sticky定位类
        row_cells = [
            f'<td class="sticky-col sticky-col-1">{file1}</td>',
            f'<td class="sticky-col sticky-col-2">{file2}</td>',
            f"<td>{float(similarity):.3f}</td>"
        ]

        for field in selected_fields:
            test_val = pair.get('test_data', {}).get(field, 'N/A')
            ref_val = pair.get('reference_data', {}).get(field, 'N/A')
            before_txt = test_val
            after_txt = ref_val
            change_txt = 'N/A'
            cls = 'change-neutral'
            try:
                # 安全转换：空字符串/非法值 -> NaN；0 值保留为有效数值
                import pandas as _pd
                _t = _pd.to_numeric(_pd.Series([test_val]), errors='coerce').iloc[0]
                _r = _pd.to_numeric(_pd.Series([ref_val]),  errors='coerce').iloc[0]
                if _pd.notna(_t) and _pd.notna(_r):
                    t = float(_t)
                    r = float(_r)
                    before_txt = f"{t:.6f}"
                    after_txt = f"{r:.6f}"
                    change_pct = ((r - t) / t * 100.0) if t != 0 else 0.0
                    if change_pct > 0:
                        cls = 'change-positive'
                    elif change_pct < 0:
                        cls = 'change-negative'
                    change_txt = f"{change_pct:.2f}%"
                else:
                    # 任一侧为 NaN：保留默认的 'N/A' 展示
                    pass
            except Exception:
                # 保持静默失败，不影响其他字段渲染
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


def _create_case_insensitive_field_mapping(trend_data):
    """创建大小写不敏感的字段映射"""
    field_mapping = {}

    # 创建小写到原始字段名的映射
    for original_field in trend_data.keys():
        normalized_field = original_field.lower()
        field_mapping[normalized_field] = original_field

    return field_mapping


def _find_actual_field_name(expected_field, field_mapping):
    """根据期望的字段名找到实际的字段名"""
    # 先尝试精确匹配
    if expected_field in field_mapping.values():
        return expected_field

    # 尝试大小写不敏感匹配
    normalized_expected = expected_field.lower()
    if normalized_expected in field_mapping:
        return field_mapping[normalized_expected]

    # 尝试模糊匹配（处理不同的命名约定）
    for normalized_actual, actual_field in field_mapping.items():
        # 移除下划线和转换为小写进行比较
        expected_clean = expected_field.replace('_', '').lower()
        actual_clean = normalized_actual.replace('_', '').lower()

        if expected_clean == actual_clean:
            return actual_field

    return None


def generate_per_image_rpg_bpg_analysis(trend_data):
    """生成RpG/BpG综合趋势图分析"""
    if not trend_data:
        return "<p class=\"muted\">无可用数据进行RpG/BpG分析</p>"

    logger.info("==liuq debug== 开始生成RpG/BpG综合趋势图分析")

    # 重组数据：从按字段组织改为综合趋势图格式
    integrated_data = _reorganize_rpg_bpg_data_for_integrated_trend(trend_data)

    if not integrated_data or not integrated_data.get('datasets'):
        return "<p class=\"muted\">无足够的RpG/BpG数据进行分析</p>"

    # 生成HTML和JavaScript
    chart_html = _generate_integrated_trend_chart_html(integrated_data)
    chart_scripts = _generate_integrated_trend_chart_scripts(integrated_data)

    return f"""
    <div class="field-section">
        <h3><i class="fas fa-chart-line"></i> RpG/BpG综合趋势分析</h3>
        <p class="muted">显示所有图片在不同算法下的RpG和BpG数值变化趋势，实线表示RpG，虚线表示BpG</p>
        {chart_html}
    </div>
    <script>
    {chart_scripts}
    </script>
    """


def generate_sgw_baseline_analysis(trend_data):
    """生成基于SGW基准的趋势分析（保留作为备用）"""
    if not trend_data:
        return "<p class=\"muted\">无可用数据进行SGW基准分析</p>"

    # 创建大小写不敏感的字段映射
    field_mapping = _create_case_insensitive_field_mapping(trend_data)

    # 定义分析组（使用标准化的字段名模式）
    rpg_group = {
        'baseline': 'ealgo_data_SGW_gray_RpG',
        'targets': [
            'ealgo_data_AGW_gray_RpG',
            'ealgo_data_Mix_csalgo_RpG',
            'ealgo_data_After_face_RpG',
            'ealgo_data_cnvgEst_RpG'
        ]
    }

    bpg_group = {
        'baseline': 'ealgo_data_SGW_gray_BpG',
        'targets': [
            'ealgo_data_AGW_gray_BpG',
            'ealgo_data_Mix_csalgo_BpG',
            'ealgo_data_After_face_BpG',
            'ealgo_data_cnvgEst_BpG'
        ]
    }

    html_sections = []

    # 分析RpG组（使用字段映射）
    rpg_analysis = _analyze_baseline_group(trend_data, rpg_group, "RpG组", field_mapping)
    if rpg_analysis:
        html_sections.append(rpg_analysis)

    # 分析BpG组（使用字段映射）
    bpg_analysis = _analyze_baseline_group(trend_data, bpg_group, "BpG组", field_mapping)
    if bpg_analysis:
        html_sections.append(bpg_analysis)

    if not html_sections:
        return "<p class=\"muted\">无足够数据进行SGW基准分析</p>"

    return f"""
    <div class="field-section">
        <h3><i class="fas fa-chart-line"></i> SGW基准趋势分析</h3>
        <p class="muted">以SGW_gray为基准，分析其他算法的增长或下降趋势</p>
        {''.join(html_sections)}
    </div>
    """


def _reorganize_rpg_bpg_data_for_integrated_trend(trend_data):
    """重组RpG/BpG数据：从按字段组织改为综合趋势图格式"""
    try:
        logger.info("==liuq debug== 开始重组RpG/BpG数据为综合趋势图格式")

        # 创建大小写不敏感的字段映射
        field_mapping = _create_case_insensitive_field_mapping(trend_data)

        # 定义算法字段映射和颜色（按图例顺序：SGW → AGW_noMap → AGW → Mix → After_face → cnvgEst）
        algorithm_config = {
            'SGW': {
                'rpg_field': 'ealgo_data_SGW_gray_RpG',
                'bpg_field': 'ealgo_data_SGW_gray_BpG',
                'color': '#e91e63'  # 红色
            },
            'AGW_noMap': {
                'rpg_field': 'ealgo_data_AGW_noMap_RpG',
                'bpg_field': 'ealgo_data_AGW_noMap_BpG',
                'color': '#00bcd4'  # 青色
            },
            'AGW': {
                'rpg_field': 'ealgo_data_AGW_gray_RpG',
                'bpg_field': 'ealgo_data_AGW_gray_BpG',
                'color': '#3f51b5'  # 蓝色
            },
            'Mix': {
                'rpg_field': 'ealgo_data_Mix_csalgo_RpG',
                'bpg_field': 'ealgo_data_Mix_csalgo_BpG',
                'color': '#4caf50'  # 绿色
            },
            'After_face': {
                'rpg_field': 'ealgo_data_After_face_RpG',
                'bpg_field': 'ealgo_data_After_face_BpG',
                'color': '#ff9800'  # 橙色
            },
            'cnvgEst': {
                'rpg_field': 'ealgo_data_cnvgEst_RpG',
                'bpg_field': 'ealgo_data_cnvgEst_BpG',
                'color': '#9c27b0'  # 紫色
            }
        }

        # 收集有效的算法数据和确定图片数量
        valid_datasets = []
        image_count = 0
        image_labels = []

        for algo_name, config in algorithm_config.items():
            # 查找实际的字段名
            actual_rpg_field = _find_actual_field_name(config['rpg_field'], field_mapping)
            actual_bpg_field = _find_actual_field_name(config['bpg_field'], field_mapping)

            if actual_rpg_field and actual_bpg_field:
                rpg_data = trend_data[actual_rpg_field]
                bpg_data = trend_data[actual_bpg_field]

                rpg_values = rpg_data.get('test_values', [])
                bpg_values = bpg_data.get('test_values', [])

                if rpg_values and bpg_values and len(rpg_values) == len(bpg_values):
                    # 设置图片数量和标签（只需要设置一次）
                    if image_count == 0:
                        image_count = len(rpg_values)
                        image_labels = [f'图片_{i+1:03d}' for i in range(image_count)]

                    # 解析颜色为RGB
                    color_hex = config['color'].lstrip('#')
                    r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))

                    # 创建RpG数据集（实线）
                    rpg_dataset = {
                        'label': f'{algo_name}_RpG',
                        'data': [float(v) for v in rpg_values],
                        'borderColor': config['color'],
                        'borderDash': [],  # 实线
                        'backgroundColor': f'rgba({r},{g},{b},0.1)',
                        'tension': 0.3,
                        'pointRadius': 4,
                        'pointHoverRadius': 6,
                        'borderWidth': 2,
                        'fill': False
                    }

                    # 创建BpG数据集（虚线）
                    bpg_dataset = {
                        'label': f'{algo_name}_BpG',
                        'data': [float(v) for v in bpg_values],
                        'borderColor': config['color'],
                        'borderDash': [5, 5],  # 虚线
                        'backgroundColor': f'rgba({r},{g},{b},0.05)',
                        'tension': 0.3,
                        'pointRadius': 4,
                        'pointHoverRadius': 6,
                        'borderWidth': 2,
                        'fill': False
                    }

                    valid_datasets.extend([rpg_dataset, bpg_dataset])
                    logger.info(f"==liuq debug== 算法 {algo_name} 有效，数据点数: {len(rpg_values)}")
                else:
                    logger.warning(f"==liuq debug== 算法 {algo_name} 数据不完整或长度不匹配")
            else:
                logger.warning(f"==liuq debug== 算法 {algo_name} 字段未找到: {config['rpg_field']}, {config['bpg_field']}")

        if not valid_datasets:
            logger.warning("==liuq debug== 没有找到有效的RpG/BpG算法数据")
            return {'image_labels': [], 'datasets': []}

        result = {
            'image_labels': image_labels,
            'datasets': valid_datasets,
            'image_count': image_count
        }

        logger.info(f"==liuq debug== 综合趋势图数据重组完成，图片数: {image_count}, 数据集数: {len(valid_datasets)}")
        return result

    except Exception as e:
        logger.error(f"==liuq debug== 重组综合趋势图数据失败: {e}")
        return {'image_labels': [], 'datasets': []}


def _generate_integrated_trend_chart_html(integrated_data):
    """生成综合趋势图的HTML结构"""
    try:
        datasets = integrated_data.get('datasets', [])
        if not datasets:
            return "<p class=\"muted\">没有可用的趋势数据</p>"

        # 统计算法数量
        algorithm_count = len(set(ds['label'].rsplit('_', 1)[0] for ds in datasets))

        html = f'''
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">
                            <i class="fas fa-chart-line"></i> RpG/BpG综合趋势图
                            <small class="text-muted">({algorithm_count}种算法，{integrated_data.get('image_count', 0)}张图片)</small>
                        </h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container" style="height: 500px;">
                            <canvas id="integrated_rpg_bpg_trend_chart" style="width:100%;height:100%;display:block;"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-3">
            <div class="col-12">
                <div class="alert alert-info">
                    <h6><i class="fas fa-info-circle"></i> 图表说明</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>线条样式：</strong></p>
                            <ul class="mb-0">
                                <li><strong>实线</strong> - RpG数值（红/绿比值）</li>
                                <li><strong>虚线</strong> - BpG数值（蓝/绿比值）</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <p><strong>算法颜色：</strong></p>
                            <ul class="mb-0">
                                <li><span style="color: #e91e63; font-weight: bold;">●</span> SGW算法</li>
                                <li><span style="color: #00bcd4; font-weight: bold;">●</span> AGW_noMap算法</li>
                                <li><span style="color: #3f51b5; font-weight: bold;">●</span> AGW算法</li>
                                <li><span style="color: #4caf50; font-weight: bold;">●</span> Mix算法</li>
                                <li><span style="color: #ff9800; font-weight: bold;">●</span> After_face算法</li>
                                <li><span style="color: #9c27b0; font-weight: bold;">●</span> cnvgEst算法</li>
                            </ul>
                        </div>
                    </div>
                    <hr>
                    <small class="text-muted">
                        <i class="fas fa-mouse-pointer"></i> 点击图例可显示/隐藏对应的算法线条
                        | <i class="fas fa-search-plus"></i> 鼠标悬停查看具体数值
                        | <i class="fas fa-arrows-alt"></i> 支持缩放和平移操作
                    </small>
                </div>
            </div>
        </div>
        '''

        return html

    except Exception as e:
        logger.error(f"==liuq debug== 生成综合趋势图HTML失败: {e}")
        return f"<p class=\"text-danger\">生成综合趋势图HTML失败: {e}</p>"


def _generate_integrated_trend_chart_scripts(integrated_data):
    """生成综合趋势图的JavaScript代码"""
    try:
        datasets = integrated_data.get('datasets', [])
        image_labels = integrated_data.get('image_labels', [])

        if not datasets or not image_labels:
            return "// 没有可用的趋势数据"

        import json

        script = f"""
// RpG/BpG综合趋势图渲染
(function() {{
    function renderIntegratedTrendChart() {{
        if (typeof Chart === 'undefined') {{
            console.warn('==liuq debug== Chart.js 未加载，等待中...');
            setTimeout(renderIntegratedTrendChart, 200);
            return;
        }}

        console.log('==liuq debug== 开始渲染RpG/BpG综合趋势图');

        var ctx = document.getElementById('integrated_rpg_bpg_trend_chart');
        if (ctx) {{
            var c = ctx.getContext('2d');
            new Chart(c, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(image_labels)},
                    datasets: {json.dumps(datasets)}
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        intersect: false,
                        mode: 'index'
                    }},
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'RpG/BpG综合趋势分析',
                            font: {{ size: 16, weight: 'bold' }}
                        }},
                        legend: {{
                            display: true,
                            position: 'top',
                            onClick: function(e, legendItem, legend) {{
                                // 默认的图例点击行为（显示/隐藏数据集）
                                const index = legendItem.datasetIndex;
                                const chart = legend.chart;
                                const meta = chart.getDatasetMeta(index);
                                meta.hidden = meta.hidden === null ? !chart.data.datasets[index].hidden : null;
                                chart.update();
                            }},
                            labels: {{
                                usePointStyle: true,
                                generateLabels: function(chart) {{
                                    const datasets = chart.data.datasets;
                                    return datasets.map((dataset, i) => {{
                                        const meta = chart.getDatasetMeta(i);
                                        const style = meta.controller.getStyle(0, false);

                                        return {{
                                            text: dataset.label,
                                            fillStyle: dataset.borderColor,
                                            strokeStyle: dataset.borderColor,
                                            lineWidth: dataset.borderWidth,
                                            lineDash: dataset.borderDash || [],
                                            hidden: meta.hidden,
                                            datasetIndex: i
                                        }};
                                    }});
                                }}
                            }}
                        }},
                        tooltip: {{
                            callbacks: {{
                                title: function(context) {{
                                    return context[0].label;
                                }},
                                label: function(context) {{
                                    const label = context.dataset.label;
                                    const value = context.parsed.y.toFixed(3);
                                    const dataType = label.includes('RpG') ? 'RpG' : 'BpG';
                                    const algorithm = label.substring(0, label.lastIndexOf('_'));
                                    return `${{algorithm}} ${{dataType}}: ${{value}}`;
                                }},
                                labelColor: function(context) {{
                                    return {{
                                        borderColor: context.dataset.borderColor,
                                        backgroundColor: context.dataset.borderColor,
                                        borderWidth: 2,
                                        borderDash: context.dataset.borderDash || []
                                    }};
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            display: true,
                            title: {{
                                display: true,
                                text: '图片序列',
                                font: {{ size: 14, weight: 'bold' }}
                            }},
                            grid: {{
                                display: true,
                                color: 'rgba(0,0,0,0.1)'
                            }}
                        }},
                        y: {{
                            display: true,
                            title: {{
                                display: true,
                                text: 'RpG/BpG数值',
                                font: {{ size: 14, weight: 'bold' }}
                            }},
                            grid: {{
                                display: true,
                                color: 'rgba(0,0,0,0.1)'
                            }},
                            beginAtZero: false
                        }}
                    }},
                    elements: {{
                        point: {{
                            hoverRadius: 8
                        }},
                        line: {{
                            tension: 0.3
                        }}
                    }}
                }}
            }});
        }} else {{
            console.error('==liuq debug== 找不到canvas元素: integrated_rpg_bpg_trend_chart');
        }}
    }}

    // 启动图表渲染
    renderIntegratedTrendChart();
}})();
"""

        return script

    except Exception as e:
        logger.error(f"==liuq debug== 生成综合趋势图JavaScript失败: {e}")
        return f"// 生成综合趋势图JavaScript失败: {e}"


def _reorganize_rpg_bpg_data_by_image(trend_data):
    """重组RpG/BpG数据：从按字段组织改为按图片组织"""
    try:
        logger.info("==liuq debug== 开始重组RpG/BpG数据")

        # 创建大小写不敏感的字段映射
        field_mapping = _create_case_insensitive_field_mapping(trend_data)

        # 定义算法字段映射
        algorithm_fields = {
            'SGW': ('ealgo_data_SGW_gray_RpG', 'ealgo_data_SGW_gray_BpG'),
            'AGW_noMap': ('ealgo_data_AGW_noMap_RpG', 'ealgo_data_AGW_noMap_BpG'),
            'AGW': ('ealgo_data_AGW_gray_RpG', 'ealgo_data_AGW_gray_BpG'),
            'Mix': ('ealgo_data_Mix_csalgo_RpG', 'ealgo_data_Mix_csalgo_BpG'),
            'After_face': ('ealgo_data_After_face_RpG', 'ealgo_data_After_face_BpG'),
            'cnvgEst': ('ealgo_data_cnvgEst_RpG', 'ealgo_data_cnvgEst_BpG')
        }

        # 收集有效的算法数据
        valid_algorithms = {}
        image_count = 0

        for algo_name, (rpg_field, bpg_field) in algorithm_fields.items():
            # 查找实际的字段名
            actual_rpg_field = _find_actual_field_name(rpg_field, field_mapping)
            actual_bpg_field = _find_actual_field_name(bpg_field, field_mapping)

            if actual_rpg_field and actual_bpg_field:
                rpg_data = trend_data[actual_rpg_field]
                bpg_data = trend_data[actual_bpg_field]

                rpg_values = rpg_data.get('test_values', [])
                bpg_values = bpg_data.get('test_values', [])

                if rpg_values and bpg_values and len(rpg_values) == len(bpg_values):
                    valid_algorithms[algo_name] = {
                        'rpg_values': rpg_values,
                        'bpg_values': bpg_values
                    }
                    image_count = max(image_count, len(rpg_values))
                    logger.info(f"==liuq debug== 算法 {algo_name} 有效，数据点数: {len(rpg_values)}")
                else:
                    logger.warning(f"==liuq debug== 算法 {algo_name} 数据不完整或长度不匹配")
            else:
                logger.warning(f"==liuq debug== 算法 {algo_name} 字段未找到: {rpg_field}, {bpg_field}")

        if not valid_algorithms:
            logger.warning("==liuq debug== 没有找到有效的RpG/BpG算法数据")
            return {'image_count': 0, 'algorithm_names': [], 'images': []}

        # 按图片重组数据
        images = []
        algorithm_names = list(valid_algorithms.keys())

        for i in range(image_count):
            image_data = {
                'index': i,
                'filename': f'图片_{i+1:03d}',  # 默认文件名，可以后续改进
                'algorithms': {}
            }

            for algo_name in algorithm_names:
                algo_data = valid_algorithms[algo_name]
                if i < len(algo_data['rpg_values']) and i < len(algo_data['bpg_values']):
                    image_data['algorithms'][algo_name] = {
                        'RpG': float(algo_data['rpg_values'][i]),
                        'BpG': float(algo_data['bpg_values'][i])
                    }

            images.append(image_data)

        result = {
            'image_count': image_count,
            'algorithm_names': algorithm_names,
            'images': images
        }

        logger.info(f"==liuq debug== 数据重组完成，图片数: {image_count}, 算法数: {len(algorithm_names)}")
        return result

    except Exception as e:
        logger.error(f"==liuq debug== 重组RpG/BpG数据失败: {e}")
        return {'image_count': 0, 'algorithm_names': [], 'images': []}


def _generate_per_image_charts_html(per_image_data):
    """生成每张图片的RpG/BpG图表HTML结构"""
    try:
        images = per_image_data['images']
        if not images:
            return "<p class=\"muted\">没有图片数据</p>"

        html_parts = []
        html_parts.append('<div class="row">')

        for i, image_data in enumerate(images):
            # 每行显示3个图表，响应式布局
            if i > 0 and i % 3 == 0:
                html_parts.append('</div><div class="row">')

            chart_id = f"rpg_bpg_image_{image_data['index']}"

            html_parts.append(f'''
                <div class="col-lg-4 col-md-6 col-sm-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">
                                <i class="fas fa-image"></i> {image_data['filename']}
                                <small class="text-muted">(#{image_data['index'] + 1})</small>
                            </h6>
                        </div>
                        <div class="card-body">
                            <div class="chart-container" style="height: 300px;">
                                <canvas id="{chart_id}" style="width:100%;height:100%;display:block;"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            ''')

        html_parts.append('</div>')

        # 添加图例说明
        html_parts.append('''
            <div class="row mt-3">
                <div class="col-12">
                    <div class="alert alert-info">
                        <h6><i class="fas fa-info-circle"></i> 图例说明</h6>
                        <div class="row">
                            <div class="col-md-6">
                                <span style="color: #e91e63; font-weight: bold;">● RpG</span> - 红色/绿色比值
                            </div>
                            <div class="col-md-6">
                                <span style="color: #3f51b5; font-weight: bold;">● BpG</span> - 蓝色/绿色比值
                            </div>
                        </div>
                        <small class="text-muted">X轴表示不同算法，Y轴表示比值大小。每张图片显示该图片在各算法下的RpG和BpG数值。</small>
                    </div>
                </div>
            </div>
        ''')

        return ''.join(html_parts)

    except Exception as e:
        logger.error(f"==liuq debug== 生成图表HTML失败: {e}")
        return f"<p class=\"text-danger\">生成图表HTML失败: {e}</p>"


def _generate_per_image_charts_scripts(per_image_data):
    """生成每张图片的RpG/BpG图表JavaScript代码"""
    try:
        images = per_image_data['images']
        algorithm_names = per_image_data['algorithm_names']

        if not images or not algorithm_names:
            return "// 没有图片数据或算法数据"

        scripts = []

        for image_data in images:
            chart_id = f"rpg_bpg_image_{image_data['index']}"

            # 准备数据
            rpg_values = []
            bpg_values = []

            for algo_name in algorithm_names:
                algo_data = image_data['algorithms'].get(algo_name, {})
                rpg_values.append(algo_data.get('RpG', 0))
                bpg_values.append(algo_data.get('BpG', 0))

            # 生成图表脚本
            script = f"""
// RpG/BpG图表渲染: {image_data['filename']}
(function() {{
    function renderChart() {{
        if (typeof Chart === 'undefined') {{
            console.warn('==liuq debug== Chart.js 未加载，等待中... {image_data['filename']}');
            setTimeout(renderChart, 200);
            return;
        }}

        console.log('==liuq debug== 开始渲染RpG/BpG图表: {image_data['filename']}');

        var ctx = document.getElementById('{chart_id}');
        if (ctx) {{
            var c = ctx.getContext('2d');
            new Chart(c, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(algorithm_names)},
                    datasets: [
                        {{
                            "label": "RpG",
                            "data": {json.dumps(rpg_values)},
                            "borderColor": "#e91e63",
                            "backgroundColor": "rgba(233,30,99,0.1)",
                            "tension": 0.3,
                            "pointRadius": 4,
                            "pointHoverRadius": 6,
                            "borderWidth": 2
                        }},
                        {{
                            "label": "BpG",
                            "data": {json.dumps(bpg_values)},
                            "borderColor": "#3f51b5",
                            "backgroundColor": "rgba(63,81,181,0.1)",
                            "tension": 0.3,
                            "pointRadius": 4,
                            "pointHoverRadius": 6,
                            "borderWidth": 2
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        intersect: false,
                        mode: 'index'
                    }},
                    plugins: {{
                        title: {{
                            display: true,
                            text: '{image_data['filename']} - RpG/BpG对比',
                            font: {{ size: 14 }}
                        }},
                        legend: {{
                            display: true,
                            position: 'top'
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(3);
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            display: true,
                            title: {{
                                display: true,
                                text: '算法类型'
                            }},
                            grid: {{
                                display: true,
                                color: 'rgba(0,0,0,0.1)'
                            }}
                        }},
                        y: {{
                            display: true,
                            title: {{
                                display: true,
                                text: '数值'
                            }},
                            grid: {{
                                display: true,
                                color: 'rgba(0,0,0,0.1)'
                            }},
                            beginAtZero: false
                        }}
                    }}
                }}
            }});
        }} else {{
            console.error('==liuq debug== 找不到canvas元素: {chart_id}');
        }}
    }}

    // 启动图表渲染
    renderChart();
}})();
"""
            scripts.append(script)

        return '\n'.join(scripts)

    except Exception as e:
        logger.error(f"==liuq debug== 生成图表JavaScript失败: {e}")
        return f"// 生成图表JavaScript失败: {e}"


def _analyze_baseline_group(trend_data, group_config, group_name, field_mapping):
    """分析单个基准组的趋势"""
    baseline_field = group_config['baseline']
    target_fields = group_config['targets']

    # 使用字段映射查找实际的基准字段名
    actual_baseline_field = _find_actual_field_name(baseline_field, field_mapping)
    if not actual_baseline_field:
        # 提供更详细的错误信息，包括可用字段
        available_fields = list(trend_data.keys())
        similar_fields = [f for f in available_fields if 'sgw' in f.lower() and ('rpg' in f.lower() if 'RpG' in baseline_field else 'bpg' in f.lower())]
        error_msg = f"<p class=\"muted\">{group_name}: 基准字段 {baseline_field} 不存在"
        if similar_fields:
            error_msg += f"<br>可能的相似字段: {', '.join(similar_fields)}"
        error_msg += "</p>"
        return error_msg

    baseline_data = trend_data[actual_baseline_field]
    baseline_values = baseline_data.get('test_values', [])

    if not baseline_values:
        return f"<p class=\"muted\">{group_name}: 基准字段无有效数据</p>"

    # 分析每个目标字段相对于基准的趋势
    trend_results = []

    for target_field in target_fields:
        # 使用字段映射查找实际的目标字段名
        actual_target_field = _find_actual_field_name(target_field, field_mapping)
        if not actual_target_field:
            continue

        target_data = trend_data[actual_target_field]
        target_values = target_data.get('test_values', [])

        if not target_values:
            continue

        # 计算相对于基准的趋势
        trend_analysis = _calculate_relative_trend(baseline_values, target_values, actual_baseline_field, actual_target_field)
        if trend_analysis:
            trend_results.append(trend_analysis)

    if not trend_results:
        return f"<p class=\"muted\">{group_name}: 无有效的目标字段数据</p>"

    # 生成HTML表格
    table_html = f"""
    <div class="mb-4">
        <h4>{group_name} 趋势分析</h4>
        <div class="table-container" style="max-height: 300px;">
            <table class="table table-striped table-hover">
                <thead class="table-dark">
                    <tr>
                        <th>目标字段</th>
                        <th>平均相对变化</th>
                        <th>趋势方向</th>
                        <th>变化幅度</th>
                        <th>稳定性</th>
                        <th>样本数</th>
                    </tr>
                </thead>
                <tbody>
    """

    for result in trend_results:
        trend_icon = "📈" if result['trend_direction'] == "上升" else "📉" if result['trend_direction'] == "下降" else "➡️"
        stability_color = "#2e7d32" if result['stability'] == "稳定" else "#ef6c00" if result['stability'] == "中等" else "#d32f2f"

        table_html += f"""
                    <tr>
                        <td>{result['target_field'].replace('ealgo_data_', '').replace('_', ' ')}</td>
                        <td>{result['avg_relative_change']:.2f}%</td>
                        <td>{trend_icon} {result['trend_direction']}</td>
                        <td>{result['magnitude']}</td>
                        <td style="color: {stability_color};">{result['stability']}</td>
                        <td>{result['sample_count']}</td>
                    </tr>
        """

    table_html += """
                </tbody>
            </table>
        </div>
    </div>
    """

    return table_html


def _calculate_relative_trend(baseline_values, target_values, baseline_field, target_field):
    """计算目标字段相对于基准字段的趋势"""
    try:
        # 确保两个数组长度一致
        min_length = min(len(baseline_values), len(target_values))
        if min_length == 0:
            return None

        baseline_vals = baseline_values[:min_length]
        target_vals = target_values[:min_length]

        # 计算相对变化百分比
        relative_changes = []
        for baseline, target in zip(baseline_vals, target_vals):
            if baseline != 0:
                relative_change = ((target - baseline) / baseline) * 100
                relative_changes.append(relative_change)

        if not relative_changes:
            return None

        # 计算统计指标
        avg_change = sum(relative_changes) / len(relative_changes)
        abs_changes = [abs(change) for change in relative_changes]
        avg_abs_change = sum(abs_changes) / len(abs_changes)

        # 判断趋势方向
        if avg_change > 2:
            trend_direction = "上升"
        elif avg_change < -2:
            trend_direction = "下降"
        else:
            trend_direction = "稳定"

        # 判断变化幅度
        if avg_abs_change < 5:
            magnitude = "小幅"
        elif avg_abs_change < 15:
            magnitude = "中幅"
        else:
            magnitude = "大幅"

        # 判断稳定性（基于标准差）
        if len(relative_changes) > 1:
            mean_change = sum(relative_changes) / len(relative_changes)
            variance = sum((x - mean_change) ** 2 for x in relative_changes) / len(relative_changes)
            std_dev = variance ** 0.5

            if std_dev < 5:
                stability = "稳定"
            elif std_dev < 15:
                stability = "中等"
            else:
                stability = "波动"
        else:
            stability = "单点"

        return {
            'target_field': target_field,
            'avg_relative_change': avg_change,
            'trend_direction': trend_direction,
            'magnitude': magnitude,
            'stability': stability,
            'sample_count': len(relative_changes)
        }

    except Exception as e:
        logger.warning(f"==liuq debug== 计算相对趋势失败 {target_field}: {e}")
        return None


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
