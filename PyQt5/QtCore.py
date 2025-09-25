"""QtCore 模块的简化桩实现。"""

class QObject:
    def __init__(self, *_, **__):
        pass


class _Signal:
    def __init__(self, *_, **__):
        self._callbacks = []

    def connect(self, callback):  # pragma: no cover - 仅用于占位
        self._callbacks.append(callback)

    def emit(self, *args, **kwargs):  # pragma: no cover - 仅用于占位
        for callback in list(self._callbacks):
            callback(*args, **kwargs)


def pyqtSignal(*_, **__):  # pragma: no cover - 仅用于占位
    return _Signal()


class QTimer(QObject):
    def __init__(self, *_, **__):
        super().__init__()
        self.timeout = _Signal()

    def setSingleShot(self, *_):  # pragma: no cover
        pass

    def start(self, *_):  # pragma: no cover
        pass

    def stop(self):  # pragma: no cover
        pass


class Qt:  # pragma: no cover - 常量占位
    Horizontal = 1
    Vertical = 2


PYQT_VERSION = 0x051100


def qDebug(*args, **kwargs):  # pragma: no cover - 占位
    pass


def qWarning(*args, **kwargs):  # pragma: no cover - 占位
    pass


def qCritical(*args, **kwargs):  # pragma: no cover - 占位
    pass


def qFatal(*args, **kwargs):  # pragma: no cover - 占位
    pass


def pyqtSlot(*args, **kwargs):  # pragma: no cover - 占位
    def decorator(func):
        return func

    return decorator


def pyqtProperty(*args, **kwargs):  # pragma: no cover - 占位
    def decorator(func):
        return func

    return decorator


_message_handler = None


def qInstallMessageHandler(handler):  # pragma: no cover - 占位
    global _message_handler
    previous = _message_handler
    _message_handler = handler
    return previous
