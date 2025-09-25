"""QtWidgets 模块的简化桩实现。"""

class QWidget:
    def __init__(self, parent=None, *_, **__):
        self._parent = parent


class QLineEdit(QWidget):
    def __init__(self, parent=None, *_, **__):
        super().__init__(parent)
        self._text = ""

    def setText(self, text):  # pragma: no cover - 占位
        self._text = text

    def text(self):  # pragma: no cover - 占位
        return self._text


class QSpinBox(QWidget):
    def __init__(self, parent=None, *_, **__):
        super().__init__(parent)
        self._value = 0

    def setValue(self, value):  # pragma: no cover - 占位
        self._value = int(value)

    def value(self):  # pragma: no cover - 占位
        return self._value


class QDoubleSpinBox(QWidget):
    def __init__(self, parent=None, *_, **__):
        super().__init__(parent)
        self._value = 0.0

    def setValue(self, value):  # pragma: no cover - 占位
        self._value = float(value)

    def value(self):  # pragma: no cover - 占位
        return self._value


class QCheckBox(QWidget):
    def __init__(self, parent=None, *_, **__):
        super().__init__(parent)
        self._checked = False

    def setChecked(self, checked):  # pragma: no cover - 占位
        self._checked = bool(checked)

    def isChecked(self):  # pragma: no cover - 占位
        return self._checked


class QComboBox(QWidget):
    def __init__(self, parent=None, *_, **__):
        super().__init__(parent)
        self._items = []
        self._index = -1

    def addItem(self, text):  # pragma: no cover - 占位
        self._items.append(text)
        if self._index == -1:
            self._index = 0

    def currentIndex(self):  # pragma: no cover - 占位
        return self._index

    def setCurrentIndex(self, index):  # pragma: no cover - 占位
        self._index = index

    def currentText(self):  # pragma: no cover - 占位
        if 0 <= self._index < len(self._items):
            return self._items[self._index]
        return ""


class QSlider(QWidget):
    def __init__(self, parent=None, *_, **__):
        super().__init__(parent)
        self._value = 0

    def setValue(self, value):  # pragma: no cover - 占位
        self._value = int(value)

    def value(self):  # pragma: no cover - 占位
        return self._value


class QDateEdit(QWidget):
    def __init__(self, parent=None, *_, **__):
        super().__init__(parent)


class QTimeEdit(QWidget):
    def __init__(self, parent=None, *_, **__):
        super().__init__(parent)


class QApplication:
    _instance = None

    def __init__(self, *_):  # pragma: no cover - 占位
        QApplication._instance = self
        self._quit_on_last_window_closed = True

    @classmethod
    def instance(cls):  # pragma: no cover - 占位
        return cls._instance

    def exec_(self):  # pragma: no cover - 占位
        return 0

    def quit(self):  # pragma: no cover - 占位
        QApplication._instance = None

    def processEvents(self):  # pragma: no cover - 占位
        pass

    @staticmethod
    def setQuitOnLastWindowClosed(flag):  # pragma: no cover - 占位
        QApplication._instance and setattr(
            QApplication._instance, "_quit_on_last_window_closed", bool(flag)
        )


__all__ = [
    "QWidget",
    "QLineEdit",
    "QSpinBox",
    "QDoubleSpinBox",
    "QCheckBox",
    "QComboBox",
    "QSlider",
    "QDateEdit",
    "QTimeEdit",
    "QApplication",
]
