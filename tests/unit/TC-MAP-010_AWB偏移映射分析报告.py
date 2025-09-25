#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-MAP-010: AWB Offset Map 自动分析报告生成验证

目标：
- 调用 AwbOffsetMapAnalysisService 对 `tests/test_data/awb_scenario_1x.xml` 执行自动解析
- 覆盖单张 map 信息与室外 / 室内 / 夜景等大类的聚合统计
- 生成 Markdown 与 HTML 报告文件，便于后续截图展示
"""

from __future__ import annotations

import html
import sys
import types
from pathlib import Path


def _ensure_pyqt_stub() -> None:
    """在测试环境下构造 PyQt5 空壳模块，避免 GUI 依赖。"""

    if "PyQt5" in sys.modules:
        return

    pyqt_mod = types.ModuleType("PyQt5")
    sys.modules["PyQt5"] = pyqt_mod

    class _DynamicModule(types.ModuleType):
        def __getattr__(self, item: str):  # pragma: no cover - 动态属性
            cls = type(item, (), {})
            setattr(self, item, cls)
            return cls

    qtwidgets = _DynamicModule("PyQt5.QtWidgets")
    sys.modules["PyQt5.QtWidgets"] = qtwidgets

    qtgui = _DynamicModule("PyQt5.QtGui")
    sys.modules["PyQt5.QtGui"] = qtgui

    qtcore = types.ModuleType("PyQt5.QtCore")

    class _Signal:
        def __init__(self, *_, **__):
            self._callbacks = []

        def connect(self, callback):  # pragma: no cover - 测试无需触发
            self._callbacks.append(callback)

        def emit(self, *args, **kwargs):  # pragma: no cover - 测试无需触发
            for callback in list(self._callbacks):
                callback(*args, **kwargs)

    class _QObject:
        def __init__(self, *_, **__):
            pass

    class _QTimer:
        def __init__(self, *_, **__):
            self.timeout = _Signal()

        def setSingleShot(self, *_):  # pragma: no cover - 测试无需触发
            pass

        def start(self, *_):  # pragma: no cover - 测试无需触发
            pass

        def stop(self):  # pragma: no cover - 测试无需触发
            pass

    def _pyqtSignal(*_, **__):  # pragma: no cover - 测试无需触发
        return _Signal()

    qtcore.QObject = _QObject
    qtcore.QTimer = _QTimer
    qtcore.pyqtSignal = _pyqtSignal
    qtcore.Qt = type("Qt", (), {})
    sys.modules["PyQt5.QtCore"] = qtcore


_ensure_pyqt_stub()

from core.services.map_analysis.awb_offset_map_analysis_service import AwbOffsetMapAnalysisService
from core.services.reporting.domains.map.multi_dimensional_report_service import (
    MapMultiDimensionalReportGenerator,
)


class TestTCMAP010AwbOffsetMapReport:
    """验证 offset map 自动化分析报告生成流程。"""

    XML_PATH = Path("tests/test_data/awb_scenario_1x.xml")

    def test_generate_awb_offset_map_report(self) -> None:
        service = AwbOffsetMapAnalysisService()
        report = service.analyze(self.XML_PATH)

        # 基础断言：涵盖 offset_map01–116 共 116 条记录
        assert len(report.entries) == 116

        first_entry = report.entries[0]
        assert first_entry.tag == "offset_map01"
        assert first_entry.nearest_reference == "D50"
        assert first_entry.mapping_label == "强拉至单点"

        map10 = next(entry for entry in report.entries if entry.tag == "offset_map10")
        assert map10.map_enabled is False
        assert map10.vertex_count == 0  # XML 中 Num=0

        outdoor_summary = next(summary for summary in report.scene_summaries if summary.scene_group == "室外")
        indoor_summary = next(summary for summary in report.scene_summaries if summary.scene_group == "室内")
        night_summary = next(summary for summary in report.scene_summaries if summary.scene_group == "夜景")

        assert outdoor_summary.count == 40
        assert indoor_summary.count == 51
        assert night_summary.count == 25

        bluesky_summary = next(summary for summary in report.class_summaries if summary.primary_class == "BlueSky")
        assert bluesky_summary.count == 8

        markdown = report.to_markdown()
        assert "offset_map01 — 1_BlueSky_HgihEV" in markdown

        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        md_path = output_dir / "awb_offset_map_report.md"
        md_path.write_text(markdown, encoding="utf-8")

        html_path = output_dir / "awb_offset_map_report.html"
        html_body = html.escape(markdown)
        html_content = (
            "<html><head><meta charset='utf-8'></head><body>"
            "<pre style='white-space:pre-wrap;font-family:monospace'>"
            f"{html_body}"
            "</pre></body></html>"
        )
        html_path.write_text(html_content, encoding="utf-8")

        assert md_path.exists()
        assert html_path.exists()

        generator = MapMultiDimensionalReportGenerator()
        context = generator._serialize_awb_offset_report(
            report,
            {'top_entry_count': 5},
        )
        assert context['top_entries']
        first_reason = context['top_entries'][0]['reason']
        assert '权重' in first_reason or '按照权重排序入选' in first_reason
        assert context['top_entries_headers'][-1] == '入选依据'
