#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用示例数据生成带统计点形状分析的EXIF对比报告。"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
import types

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

for name in list(sys.modules.keys()):
    if name.startswith('PyQt5'):
        del sys.modules[name]

qt_module = types.ModuleType('PyQt5')
qtwidgets_module = types.ModuleType('PyQt5.QtWidgets')
qtgui_module = types.ModuleType('PyQt5.QtGui')
qtcore_module = types.ModuleType('PyQt5.QtCore')


class _DummyWidget:
    def __init__(self, *args, **kwargs):
        pass


class _DummyApplication(_DummyWidget):
    @staticmethod
    def instance():
        return None

    def setQuitOnLastWindowClosed(self, value):
        return None

    def exec_(self):
        return 0


qtwidgets_module.QApplication = _DummyApplication
qtwidgets_module.QWidget = _DummyWidget
qtwidgets_module.QLineEdit = _DummyWidget
qtwidgets_module.QSpinBox = _DummyWidget
qtwidgets_module.QDoubleSpinBox = _DummyWidget
qtwidgets_module.QCheckBox = _DummyWidget
qtwidgets_module.QComboBox = _DummyWidget
qtwidgets_module.QSlider = _DummyWidget
qtwidgets_module.__getattr__ = lambda name: _DummyWidget


class _DummyTimer(_DummyWidget):
    def start(self, *args, **kwargs):
        return None

    def stop(self):
        return None

    def setInterval(self, interval):
        return None


class _DummySignal:
    def __init__(self, *args, **kwargs):
        self._callbacks = []

    def connect(self, callback):
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs):
        for cb in list(self._callbacks):
            try:
                cb(*args, **kwargs)
            except Exception:
                pass


qtcore_module.QCoreApplication = _DummyApplication
qtcore_module.QObject = _DummyWidget
qtcore_module.QEvent = _DummyWidget
qtcore_module.QTimer = _DummyTimer
qtcore_module.pyqtSignal = lambda *args, **kwargs: _DummySignal()
qtcore_module.pyqtSlot = lambda *args, **kwargs: (lambda func: func)
qtcore_module.pyqtProperty = lambda *args, **kwargs: (lambda func: func)
qtcore_module.PYQT_VERSION = 0x050f00
qtcore_module.PYQT_VERSION_STR = '5.15.0'
qtcore_module.qDebug = staticmethod(lambda *args, **kwargs: None)
qtcore_module.qWarning = staticmethod(lambda *args, **kwargs: None)
qtcore_module.qCritical = staticmethod(lambda *args, **kwargs: None)
qtcore_module.qFatal = staticmethod(lambda *args, **kwargs: None)
qtcore_module.__getattr__ = lambda name: _DummyWidget

qtgui_module.QGuiApplication = _DummyApplication

qt_module.QtWidgets = qtwidgets_module
qt_module.QtGui = qtgui_module
qt_module.QtCore = qtcore_module
qt_module.PYQT_VERSION_STR = '5.15.0'

sys.modules['PyQt5'] = qt_module
sys.modules['PyQt5.QtWidgets'] = qtwidgets_module
sys.modules['PyQt5.QtGui'] = qtgui_module
sys.modules['PyQt5.QtCore'] = qtcore_module

from core.services.reporting.domains.exif import ExifComparisonReportGenerator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    repo_root = REPO_ROOT
    test_csv = repo_root / "tests/test_data/ceshiji.csv"
    reference_csv = repo_root / "tests/test_data/duibij.csv"
    test_image = repo_root / "tests/test_data/SZAWBAE1770_1X_25001_S_IMG20250101064624.jpg"
    reference_image = repo_root / "tests/test_data/SZAWBAE1770_1X_24087_S_IMG20250929164322.jpg"
    output_path = repo_root / "output/exif_shape_analysis_demo.html"

    selected_fields = [
        "meta_data_outputCtemp",
        "ealgo_data_AGW_gray_RpG",
        "ealgo_data_AGW_gray_BpG",
        "meta_data_gslGain_rgain",
        "meta_data_gslGain_bgain",
    ]

    generator = ExifComparisonReportGenerator()
    config = {
        "test_csv_path": str(test_csv),
        "reference_csv_path": str(reference_csv),
        "selected_fields": selected_fields,
        "output_path": str(output_path),
        "match_column": "image_name",
        "similarity_threshold": 0.8,
        "sort_by_similarity": True,
        "shape_analysis": {
            "enabled": True,
            "test_image_path": str(test_image),
            "reference_image_path": str(reference_image),
        },
    }

    logger.info("开始生成示例EXIF对比报告...")
    report_path = generator.generate(config)
    logger.info("报告已生成: %s", report_path)
    print(report_path)


if __name__ == "__main__":
    main()
