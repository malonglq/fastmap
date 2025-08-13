#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地冒烟脚本：生成一份最小EXIF对比报告并通过默认浏览器打开
==liuq debug== 仅用于快速验证路径与默认浏览器打开逻辑
"""
import os
from pathlib import Path
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 尝试导入pandas
try:
    import pandas as pd  # type: ignore
except Exception as _e:
    pd = None

from utils.browser_utils import open_html_report


def make_demo_csv(path: Path, n: int = 8):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(1, n + 1):
        image_name = f"{i:03d}_demo.jpg"  # 序列号在前，便于匹配
        rows.append({
            'image_name': image_name,
            'color_sensor_irRatio': 0.8 + i * 0.01,
            'color_sensor_sensorCct': 3000 + i * 10,
            'meta_data_currentFrame_bv': 5.0 + i * 0.05,
            # 其余字段可缺省，生成器会自动仅使用存在的字段
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, encoding='utf-8-sig')


def main():
    base = Path('output') / 'smoke'
    base.mkdir(parents=True, exist_ok=True)
    test_csv = base / 'test_exif.csv'
    ref_csv = base / 'ref_exif.csv'

    # 生成两份CSV（ref略有不同）
    make_demo_csv(test_csv, 8)
    make_demo_csv(ref_csv, 8)

    # 轻微改动对比机数据
    df_ref = pd.read_csv(ref_csv, encoding='utf-8-sig')
    df_ref['color_sensor_irRatio'] = df_ref['color_sensor_irRatio'] + 0.02
    df_ref.to_csv(ref_csv, index=False, encoding='utf-8-sig')

    out_html = base / 'smoke_exif_report.html'

    if pd is None:
        # 回退：不生成真实报告，直接写一个简易HTML验证打开逻辑
        html = '<html><body><h1>Smoke (no pandas env)</h1></body></html>'
        out_html.write_text(html, encoding='utf-8')
        print('==liuq debug== pandas 不可用，使用简易HTML进行打开验证')
        report_path = str(out_html)
    else:
        # 生成器依赖pandas，只有在pandas可用时才执行
        try:
            from core.services.exif_comparison_report_generator import ExifComparisonReportGenerator
            generator = ExifComparisonReportGenerator()
            config = {
                'test_csv_path': str(test_csv),
                'reference_csv_path': str(ref_csv),
                'output_path': str(out_html)
            }
            print('==liuq debug== 开始生成冒烟报告...')
            report_path = generator.generate(config)
            print('==liuq debug== 报告路径:', report_path)
        except Exception as e:
            print('==liuq debug== 生成器路径不可用，回退到简易HTML:', e)
            html = '<html><body><h1>Smoke (generator import failed)</h1></body></html>'
            out_html.write_text(html, encoding='utf-8')
            report_path = str(out_html)

    print('==liuq debug== 尝试打开报告(默认浏览器)...')
    ok = open_html_report(report_path)
    print('==liuq debug== 打开结果:', ok)


if __name__ == '__main__':
    main()

