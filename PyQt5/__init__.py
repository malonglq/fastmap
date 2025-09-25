"""PyQt5 最小化桩模块，便于在无 GUI 环境下运行单元测试。"""

from . import QtWidgets  # noqa: F401
from . import QtCore  # noqa: F401
from . import QtGui  # noqa: F401

__all__ = [
    "QtWidgets",
    "QtCore",
    "QtGui",
]
