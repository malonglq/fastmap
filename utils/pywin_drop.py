#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows OLE Drag&Drop via pywin32 (pythoncom)
==liuq debug== utils.pywin_drop

使用 pythoncom.IDropTarget + pythoncom.RegisterDragDrop，实现稳定的拖拽回调。
支持：
- CF_HDROP（资源管理器文件）
- FileGroupDescriptorW + FileContents（虚拟文件，流式落盘）
"""
from __future__ import annotations
import sys
import logging
from typing import Callable, List

logger = logging.getLogger(__name__)

if not sys.platform.startswith('win'):
    def install_pywin_drop(hwnd: int, on_files: Callable[[List[str]], None]):
        return None
    def revoke_pywin_drop(hwnd: int):
        return None
else:
    import pythoncom
    from win32com.server.util import wrap
    from ctypes import windll, create_unicode_buffer, c_void_p, c_uint32, string_at
    import ctypes as C
    import os, tempfile
    import win32clipboard  # 修复：RegisterClipboardFormat 应来自 win32clipboard

    DROPEFFECT_COPY = 1
    # 修复：使用 win32clipboard.RegisterClipboardFormat 而非 pythoncom
    try:
        CFSTR_FILEDESCRIPTORW = win32clipboard.RegisterClipboardFormat("FileGroupDescriptorW")
        CFSTR_FILECONTENTS = win32clipboard.RegisterClipboardFormat("FileContents")
        logger.info("==liuq debug== pywin 已注册剪贴板格式: FileGroupDescriptorW/FileContents")
    except Exception as e:
        CFSTR_FILEDESCRIPTORW = 0
        CFSTR_FILECONTENTS = 0
        logger.info("==liuq debug== 注册剪贴板格式失败: %s", e)

    class _DropTarget(object):
        _public_methods_ = ['DragEnter', 'DragOver', 'DragLeave', 'Drop']
        _com_interfaces_ = [pythoncom.IID_IDropTarget]

        def __init__(self, on_files: Callable[[List[str]], None]):
            self._on_files = on_files

        def DragEnter(self, data_object, key_state, point, effect):
            try:
                logger.info("==liuq debug== pywin.DragEnter")
            except Exception:
                pass
            return DROPEFFECT_COPY

        def DragOver(self, key_state, point, effect):
            return DROPEFFECT_COPY

        def DragLeave(self):
            try:
                logger.info("==liuq debug== pywin.DragLeave")
            except Exception:
                pass

        def _extract_cf_hdrop(self, data_object) -> List[str]:
            files: List[str] = []
            fmtetc = (pythoncom.CF_HDROP, None, pythoncom.DVASPECT_CONTENT, -1, pythoncom.TYMED_HGLOBAL)
            try:
                stg = data_object.GetData(fmtetc)
                hdrop = stg.data_handle
                cnt = windll.shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                for i in range(cnt):
                    ln = windll.shell32.DragQueryFileW(hdrop, i, None, 0)
                    buf = create_unicode_buffer(ln + 1)
                    windll.shell32.DragQueryFileW(hdrop, i, buf, ln + 1)
                    files.append(buf.value)
            except Exception as e:
                logger.debug("==liuq debug== pywin CF_HDROP 解析异常: %s", e)
            return files

        def _extract_virtual_files(self, data_object) -> List[str]:
            results: List[str] = []
            try:
                # 读取 FileGroupDescriptorW，解析文件数与名称
                fmt_fd = (CFSTR_FILEDESCRIPTORW, None, pythoncom.DVASPECT_CONTENT, -1, pythoncom.TYMED_HGLOBAL)
                stg = data_object.GetData(fmt_fd)
                hglobal = stg.data_handle
                base = windll.kernel32.GlobalLock(hglobal)
                if not base:
                    return results
                try:
                    count = c_uint32.from_address(base).value
                    FDW_SIZE = 592  # 经验值，FILEDESCRIPTORW 结构大小
                    NAME_OFF = 72   # cFileName 偏移
                    for i in range(min(count, 16)):
                        name_ptr = base + 4 + i * FDW_SIZE + NAME_OFF
                        name = C.wstring_at(name_ptr, 260).rstrip('\x00')
                        if not name:
                            name = f"virtual_{i}.jpg"
                        # 获取对应内容流
                        path = self._get_virtual_file_content(data_object, i, name)
                        if path:
                            results.append(path)
                finally:
                    windll.kernel32.GlobalUnlock(hglobal)
            except Exception as e:
                logger.debug("==liuq debug== 读取 FileGroupDescriptorW 异常: %s", e)
            return results

        def _get_virtual_file_content(self, data_object, index: int, file_name: str) -> str:
            # 先尝试 IStream
            try:
                fmt_stream = (CFSTR_FILECONTENTS, None, pythoncom.DVASPECT_CONTENT, index, pythoncom.TYMED_ISTREAM)
                stg2 = data_object.GetData(fmt_stream)
                stream = stg2.data  # PyIStream
                tmp_path = self._mk_temp_path(file_name)
                with open(tmp_path, 'wb') as f:
                    while True:
                        chunk = stream.Read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
                logger.info("==liuq debug== pywin 虚拟文件 ISTREAM 已落盘: %s", tmp_path)
                return tmp_path
            except Exception as e:
                logger.debug("==liuq debug== 读取 FileContents IStream 异常(index=%d): %s", index, e)
            # 再尝试 HGLOBAL
            try:
                fmt_hg = (CFSTR_FILECONTENTS, None, pythoncom.DVASPECT_CONTENT, index, pythoncom.TYMED_HGLOBAL)
                stg3 = data_object.GetData(fmt_hg)
                hmem = stg3.data_handle
                ptr = windll.kernel32.GlobalLock(hmem)
                if not ptr:
                    return ""
                try:
                    size = windll.kernel32.GlobalSize(hmem)
                    if size and size > 0:
                        buf = string_at(ptr, size)
                        tmp_path = self._mk_temp_path(file_name)
                        with open(tmp_path, 'wb') as f:
                            f.write(buf)
                        logger.info("==liuq debug== pywin 虚拟文件 HGLOBAL 已落盘: %s", tmp_path)
                        return tmp_path
                finally:
                    windll.kernel32.GlobalUnlock(hmem)
            except Exception as e:
                logger.debug("==liuq debug== 读取 FileContents HGLOBAL 异常(index=%d): %s", index, e)
            return ""

        def _mk_temp_path(self, file_name: str) -> str:
            root = tempfile.gettempdir()
            name = os.path.basename(file_name)
            if not name.lower().endswith(('.jpg', '.jpeg')):
                # 强制加后缀，保证 EXIF 路径能识别
                name = name + ".jpg"
            return os.path.join(root, f"fmv2_dnd_{os.getpid()}_{name}")

        def Drop(self, data_object, key_state, point, effect):
            files: List[str] = []
            try:
                files = self._extract_cf_hdrop(data_object)
                if not files:
                    files = self._extract_virtual_files(data_object)
                logger.info("==liuq debug== pywin.Drop 解析结果: %s", files)
                if files:
                    try:
                        self._on_files(files)
                    except Exception as e:
                        logger.error("==liuq debug== pywin.Drop 回调异常: %s", e)
            except Exception as e:
                logger.error("==liuq debug== pywin.Drop 异常: %s", e)
            return DROPEFFECT_COPY

    _g_targets = {}

    def install_pywin_drop(hwnd: int, on_files: Callable[[List[str]], None]):
        try:
            # 确保 COM 初始化
            try:
                pythoncom.OleInitialize()
                logger.info("==liuq debug== pywin OleInitialize 成功")
            except Exception as _e:
                logger.info("==liuq debug== pywin OleInitialize 返回: %s", _e)
            # 尝试撤销已有注册（避免 DRAGDROP_E_ALREADYREGISTERED）
            try:
                pythoncom.RevokeDragDrop(hwnd)
            except Exception:
                pass
            # 注册拖拽：必须传入 COM 包装对象
            dt = _DropTarget(on_files)
            com_obj = wrap(dt, usePolicy=True)
            pythoncom.RegisterDragDrop(hwnd, com_obj)
            _g_targets[hwnd] = com_obj
            logger.info("==liuq debug== pywin IDropTarget 注册成功 hwnd=%s", hex(hwnd))
            return com_obj
        except Exception as e:
            try:
                import traceback
                logger.info("==liuq debug== pywin RegisterDragDrop 异常: %s\n%s", e, traceback.format_exc())
            except Exception:
                logger.info("==liuq debug== pywin RegisterDragDrop 异常: %s", e)
            return None

    def revoke_pywin_drop(hwnd: int):
        try:
            if hwnd in _g_targets:
                pythoncom.RevokeDragDrop(hwnd)
                _g_targets.pop(hwnd, None)
                logger.info("==liuq debug== pywin IDropTarget 已撤销 hwnd=%s", hex(hwnd))
        except Exception as e:
            logger.debug("==liuq debug== pywin RevokeDragDrop 异常: %s", e)

