#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 原生拖拽文件支持 (WM_DROPFILES)
==liuq debug== utils.win_drop

在 Qt 内置拖拽不可用时，使用 Windows 原生事件捕获拖放。
仅在 Windows 上生效。
"""
from __future__ import annotations
import sys
import ctypes as C
import logging
from typing import Callable, List

logger = logging.getLogger(__name__)

try:
    from PyQt5.QtCore import QAbstractNativeEventFilter, QCoreApplication
except Exception:  # 非GUI环境时安全导入
    QAbstractNativeEventFilter = object  # type: ignore
    QCoreApplication = None  # type: ignore

# 常量
WM_DROPFILES = 0x0233
MAX_PATH = 260

# Win32 类型
aLPDWORD = C.POINTER(C.c_uint)
LPWSTR = C.c_wchar_p
UINT = C.c_uint
HDROP = C.c_void_p
HWND = C.c_void_p

# 函数原型
shell32 = None
user32 = None
if sys.platform.startswith('win'):
    shell32 = C.windll.shell32
    user32 = C.windll.user32
    shell32.DragAcceptFiles.argtypes = [HWND, C.c_bool]
    shell32.DragAcceptFiles.restype = None
    shell32.DragQueryFileW.argtypes = [HDROP, UINT, LPWSTR, UINT]
    shell32.DragQueryFileW.restype = UINT
    shell32.DragFinish.argtypes = [HDROP]
    shell32.DragFinish.restype = None

# === UIPI (User Interface Privilege Isolation) 兼容处理 ===
# 在以管理员身份运行时，低完整性进程（如资源管理器）向高完整性窗口发送的
# 拖拽/复制消息会被UIPI拦截，导致完全收不到WM_DROPFILES等消息。
# 通过 ChangeWindowMessageFilterEx 将必要消息加入白名单，恢复跨完整性级别的可用性。
try:
    if sys.platform.startswith('win'):
        # 常量定义
        MSGFLT_ADD = 1  # 允许
        # 某些系统/场景下需要同时允许以下消息，才能使拖拽/跨完整性通信更稳定
        WM_COPYGLOBALDATA = 0x0049
        WM_COPYDATA = 0x004A
        # ChangeWindowMessageFilterEx 原型
        class CHANGEFILTERSTRUCT(C.Structure):
            _fields_ = [("cbSize", C.c_uint), ("ExtStatus", C.c_uint)]
        user32.ChangeWindowMessageFilterEx.argtypes = [HWND, C.c_uint, C.c_uint, C.POINTER(CHANGEFILTERSTRUCT)]
        user32.ChangeWindowMessageFilterEx.restype = C.c_bool
except Exception:
    pass


def _allow_messages_through_uipi(hwnd: int):
    """将关键消息加入白名单，避免UIPI阻断。
    仅在Windows且user32可用时有效。
    """
    try:
        if not sys.platform.startswith('win') or user32 is None:
            return
        cfs = CHANGEFILTERSTRUCT()
        cfs.cbSize = C.sizeof(CHANGEFILTERSTRUCT)
        # 允许 WM_DROPFILES
        try:
            user32.ChangeWindowMessageFilterEx(HWND(hwnd), C.c_uint(WM_DROPFILES), C.c_uint(MSGFLT_ADD), C.byref(cfs))
        except Exception:
            pass
        # 允许 WM_COPYGLOBALDATA（实践中对文件拖拽稳定性有帮助）
        try:
            user32.ChangeWindowMessageFilterEx(HWND(hwnd), C.c_uint(0x0049), C.c_uint(MSGFLT_ADD), C.byref(cfs))
        except Exception:
            pass
    except Exception:
        # 静默失败，保持兼容性
        pass


class _WinDropFilter(QAbstractNativeEventFilter):  # type: ignore
    def __init__(self, on_files: Callable[[List[str]], None]):
        super().__init__()
        self._on_files = on_files

    def nativeEventFilter(self, eventType, message):  # type: ignore
        try:
            if not sys.platform.startswith('win'):
                return False, 0
            # PyQt5 传入的是 sip.voidptr，可转为整数地址
            addr = int(message)
            # 解析 MSG 结构: HWND, UINT, WPARAM, LPARAM, DWORD, POINT(x,y)
            # 仅取 message, wParam
            SIZEOF_HWND = C.sizeof(HWND)
            SIZEOF_UINT = C.sizeof(C.c_uint)
            PTR_SIZE = C.sizeof(C.c_void_p)
            # 读取 message (UINT)
            msg_id = C.c_uint.from_address(addr + SIZEOF_HWND).value
            if msg_id == WM_DROPFILES:
                logger.info("==liuq debug== win_drop检测到WM_DROPFILES消息")
                # 计算 wParam 偏移（对齐到指针大小）
                offset_wparam = SIZEOF_HWND + SIZEOF_UINT
                if PTR_SIZE == 8:
                    offset_wparam += 4  # Win64下对齐填充
                wparam = C.c_size_t.from_address(addr + offset_wparam).value
                hdrop = HDROP(wparam)
                files: List[str] = []
                # 先取数量
                count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                logger.info("==liuq debug== win_drop解析到%d个文件", count)
                for i in range(count):
                    # 先取长度
                    length = shell32.DragQueryFileW(hdrop, i, None, 0)
                    buf = C.create_unicode_buffer(length + 1)
                    shell32.DragQueryFileW(hdrop, i, buf, length + 1)
                    files.append(buf.value)
                logger.info("==liuq debug== win_drop文件列表: %s", files)
                try:
                    self._on_files(files)
                finally:
                    shell32.DragFinish(hdrop)
                return True, 0
        except Exception as e:
            try:
                logger.debug("==liuq debug== nativeEventFilter 解析MSG失败: %s", e)
            except Exception:
                pass
        return False, 0


def enable_win_drop_for_hwnd(hwnd: int):
    """启用指定窗口句柄的原生文件拖放"""
    if sys.platform.startswith('win') and shell32 is not None:
        try:
            logger.info("==liuq debug== DragAcceptFiles调用，hwnd=%s", hex(hwnd))
        except Exception:
            pass
        shell32.DragAcceptFiles(HWND(hwnd), True)


def install_win_drop(main_hwnd: int, on_files: Callable[[List[str]], None]):
    """在 QApplication 层安装原生 WM_DROPFILES 过滤器，并启用窗口句柄接受文件拖放"""
    if not sys.platform.startswith('win'):
        return None
    if QCoreApplication is None:
        return None
    # 允许跨UIPI消息
    _allow_messages_through_uipi(main_hwnd)
    # 接受 WM_DROPFILES
    enable_win_drop_for_hwnd(main_hwnd)
    flt = _WinDropFilter(on_files)
    app = QCoreApplication.instance()
    if app:
        app.installNativeEventFilter(flt)
        try:
            logger.info("==liuq debug== 原生事件过滤器安装成功")
        except Exception:
            pass
    return flt

