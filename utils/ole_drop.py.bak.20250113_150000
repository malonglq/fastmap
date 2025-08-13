#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows OLE Drag&Drop (IDropTarget) fallback for file drop
==liuq debug== utils.ole_drop

完全绕过 PyQt5 拖拽系统，使用 RegisterDragDrop + IDropTarget 接收文件拖拽。
仅处理 CF_HDROP（文件路径列表）。
"""
from __future__ import annotations
import sys
import ctypes as C
import logging
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

if not sys.platform.startswith('win'):
    # 非Windows平台直接提供空实现
    def install_ole_droptarget(hwnd: int, on_files: Callable[[List[str]], None]):
        return None
    def revoke_ole_droptarget(hwnd: int):
        return None
else:
    # Windows ctypes 定义
    ole32 = C.windll.ole32
    shell32 = C.windll.shell32
    user32 = C.windll.user32
    kernel32 = C.windll.kernel32

    # 常量
    S_OK = 0
    E_NOINTERFACE = 0x80004002
    CF_HDROP = 15
    DVASPECT_CONTENT = 1
    TYMED_HGLOBAL = 1
    TYMED_ISTREAM = 4
    DROPEFFECT_NONE = 0
    DROPEFFECT_COPY = 1

    # 额外的剪贴板格式（虚拟文件）
    try:
        CFSTR_FILEDESCRIPTORW = user32.RegisterClipboardFormatW("FileGroupDescriptorW")
        CFSTR_FILECONTENTS = user32.RegisterClipboardFormatW("FileContents")
    except Exception:
        CFSTR_FILEDESCRIPTORW = 0
        CFSTR_FILECONTENTS = 0

    # comtypes 定义（标准 COM 接口）
    try:
        import comtypes
        from comtypes import IUnknown, GUID as CGUID, HRESULT, COMMETHOD, COMObject
        from comtypes.automation import FORMATETC as C_FORMATETC, STGMEDIUM as C_STGMEDIUM
        from ctypes import c_ulong, POINTER, c_int

        class POINTL(C.Structure):
            _fields_ = [("x", C.c_long), ("y", C.c_long)]

        class IDataObject(IUnknown):
            _iid_ = CGUID("0000010E-0000-0000-C000-000000000046")
            _methods_ = [
                COMMETHOD([], HRESULT, 'GetData', (['in'], POINTER(C_FORMATETC), 'pformatetcIn'), (['out'], POINTER(C_STGMEDIUM), 'pmedium')),
            ]

        class IDropTarget(IUnknown):
            _iid_ = CGUID("00000122-0000-0000-C000-000000000046")
            _methods_ = [
                COMMETHOD([], HRESULT, 'DragEnter', (['in'], POINTER(IDataObject), 'pDataObj'), (['in'], c_ulong, 'grfKeyState'), (['in'], POINTER(POINTL), 'pt'), (['in','out'], POINTER(c_ulong), 'pdwEffect')),
                COMMETHOD([], HRESULT, 'DragOver', (['in'], c_ulong, 'grfKeyState'), (['in'], POINTER(POINTL), 'pt'), (['in','out'], POINTER(c_ulong), 'pdwEffect')),
                COMMETHOD([], HRESULT, 'DragLeave'),
                COMMETHOD([], HRESULT, 'Drop', (['in'], POINTER(IDataObject), 'pDataObj'), (['in'], c_ulong, 'grfKeyState'), (['in'], POINTER(POINTL), 'pt'), (['in','out'], POINTER(c_ulong), 'pdwEffect')),
            ]

        class DropTargetCom(COMObject):
            _com_interfaces_ = [IDropTarget]
            def __init__(self, on_files):
                super().__init__()
                self._on_files = on_files

            def DragEnter(self, pDataObj, grfKeyState, pt, pdwEffect):
                try:
                    logger.info("==liuq debug== OLE.DragEnter (comtypes)")
                except Exception:
                    pass
                pdwEffect[0] = DROPEFFECT_COPY
                return S_OK

            def DragOver(self, grfKeyState, pt, pdwEffect):
                pdwEffect[0] = DROPEFFECT_COPY
                return S_OK

            def DragLeave(self):
                try:
                    logger.info("==liuq debug== OLE.DragLeave (comtypes)")
                except Exception:
                    pass
                return S_OK

            def Drop(self, pDataObj, grfKeyState, pt, pdwEffect):
                try:
                    files = []
                    # 先尝试 CF_HDROP
                    try:
                        fmt = C_FORMATETC(); fmt.cfFormat = CF_HDROP; fmt.ptd=None; fmt.dwAspect=DVASPECT_CONTENT; fmt.lindex=-1; fmt.tymed=TYMED_HGLOBAL
                        stg = C_STGMEDIUM()
                        hr = pDataObj.GetData(fmt, stg)
                        if hr == S_OK and stg.tymed == TYMED_HGLOBAL and stg.hGlobal:
                            hdrop = C.c_void_p(stg.hGlobal)
                            cnt = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                            for i in range(cnt):
                                ln = shell32.DragQueryFileW(hdrop, i, None, 0)
                                buf = C.create_unicode_buffer(ln + 1)
                                shell32.DragQueryFileW(hdrop, i, buf, ln + 1)
                                files.append(buf.value)
                    except Exception as e:
                        logger.debug("==liuq debug== comtypes CF_HDROP 解析异常: %s", e)
                    # TODO: 后续补充 FILEDESCRIPTORW/FILECONTENTS
                    try:
                        logger.info("==liuq debug== OLE.Drop (comtypes) 解析结果: %s", files)
                    except Exception:
                        pass
                    if files:
                        try:
                            self._on_files(files)
                        except Exception as e:
                            logger.error("==liuq debug== OLE.Drop 回调异常: %s", e)
                    pdwEffect[0] = DROPEFFECT_COPY
                    return S_OK
                except Exception as e:
                    logger.error("==liuq debug== OLE.Drop(comtypes) 异常: %s", e)
                    pdwEffect[0] = DROPEFFECT_NONE
                    return S_OK
        _comtypes_available = True
    except Exception as e:
        logger.debug("==liuq debug== comtypes 初始化失败: %s", e)
        _comtypes_available = False

    # 结构与类型
    class GUID(C.Structure):
        _fields_ = [
            ("Data1", C.c_uint32),
            ("Data2", C.c_uint16),
            ("Data3", C.c_uint16),
            ("Data4", C.c_ubyte * 8),
        ]
        def __init__(self, guid_str: str = None):
            super().__init__()
            if guid_str is not None:
                import uuid
                u = uuid.UUID(guid_str)
                self.Data1 = u.time_low
                self.Data2 = u.time_mid
                self.Data3 = u.time_hi_version
                d4 = list(u.bytes[8:])
                self.Data4[:] = (C.c_ubyte * 8)(*d4)

    def _guid_equal(a: GUID, b: GUID) -> bool:
        try:
            if a.Data1 != b.Data1 or a.Data2 != b.Data2 or a.Data3 != b.Data3:
                return False
            for i in range(8):
                if a.Data4[i] != b.Data4[i]:
                    return False
            return True
        except Exception:
            return False

    IID_IUnknown = GUID('00000000-0000-0000-C000-000000000046')
    IID_IDropTarget = GUID('00000122-0000-0000-C000-000000000046')
    IID_IDataObject = GUID('0000010e-0000-0000-C000-000000000046')

    class POINTL(C.Structure):
        _fields_ = [("x", C.c_long), ("y", C.c_long)]

    class FORMATETC(C.Structure):
        _fields_ = [
            ("cfFormat", C.c_ushort),
            ("ptd", C.c_void_p),
            ("dwAspect", C.c_uint),
            ("lindex", C.c_long),
            ("tymed", C.c_uint),
        ]

    class STGMEDIUM(C.Structure):
        _fields_ = [
            ("tymed", C.c_uint),
            ("hGlobal", C.c_void_p),
            ("pUnkForRelease", C.c_void_p),
        ]

    # IDataObject vtable（仅声明我们要用的方法 GetData at index 3）
    # typedef struct IDataObjectVtbl {
    #   HRESULT (STDMETHODCALLTYPE *QueryInterface)(...);
    #   ULONG (STDMETHODCALLTYPE *AddRef)(...);
    #   ULONG (STDMETHODCALLTYPE *Release)(...);
    #   HRESULT (STDMETHODCALLTYPE *GetData)(IDataObject*, FORMATETC*, STGMEDIUM*);
    #   ...
    # };
    GetDataProto = C.WINFUNCTYPE(C.c_long, C.c_void_p, C.POINTER(FORMATETC), C.POINTER(STGMEDIUM))

    class IDataObjectVTbl(C.Structure):
        _fields_ = [
            ("QueryInterface", C.c_void_p),
            ("AddRef", C.c_void_p),
            ("Release", C.c_void_p),
            ("GetData", GetDataProto),
        ]

    class IDataObject(C.Structure):
        _fields_ = [("lpVtbl", C.POINTER(IDataObjectVTbl))]

    # IDropTarget vtable 原型
    # IUnknown
    QI = C.WINFUNCTYPE(C.c_long, C.c_void_p, C.POINTER(GUID), C.POINTER(C.c_void_p))
    ADDREF = C.WINFUNCTYPE(C.c_ulong, C.c_void_p)
    RELEASE = C.WINFUNCTYPE(C.c_ulong, C.c_void_p)
    # IDropTarget
    DRAGENTER = C.WINFUNCTYPE(C.c_long, C.c_void_p, C.POINTER(IDataObject), C.c_uint, C.POINTER(POINTL), C.POINTER(C.c_ulong))
    DRAGOVER = C.WINFUNCTYPE(C.c_long, C.c_void_p, C.c_uint, C.POINTER(POINTL), C.POINTER(C.c_ulong))
    DRAGLEAVE = C.WINFUNCTYPE(C.c_long, C.c_void_p)
    DROP = C.WINFUNCTYPE(C.c_long, C.c_void_p, C.POINTER(IDataObject), C.c_uint, C.POINTER(POINTL), C.POINTER(C.c_ulong))

    class IDropTargetVTbl(C.Structure):
        _fields_ = [
            ("QueryInterface", QI),
            ("AddRef", ADDREF),
            ("Release", RELEASE),
            ("DragEnter", DRAGENTER),
            ("DragOver", DRAGOVER),
            ("DragLeave", DRAGLEAVE),
            ("Drop", DROP),
        ]

    class IDropTarget(C.Structure):
        pass

    # 引用计数/回调持有
    class DropTargetImpl:
        def __init__(self, on_files: Callable[[List[str]], None]):
            # 分配 COM 对象与 vtable
            self._refcnt = C.c_ulong(1)
            self._on_files = on_files
            # 绑定方法
            self._qi = QI(self.QueryInterface)
            self._addref = ADDREF(self.AddRef)
            self._release = RELEASE(self.Release)
            self._dragenter = DRAGENTER(self.DragEnter)
            self._dragover = DRAGOVER(self.DragOver)
            self._dragleave = DRAGLEAVE(self.DragLeave)
            self._drop = DROP(self.Drop)
            self._vtbl = IDropTargetVTbl(self._qi, self._addref, self._release, self._dragenter, self._dragover, self._dragleave, self._drop)
            # 真正的 COM 对象需要一个包含 vtbl 指针的结构体
            class _COMOBJ(C.Structure):
                _fields_ = [("lpVtbl", C.POINTER(IDropTargetVTbl))]
            self._comobj = _COMOBJ(C.pointer(self._vtbl))
            # 暴露原始指针
            self.pIDropTarget = C.pointer(self._comobj)

        # IUnknown
        def QueryInterface(self, this, riid, ppv):
            try:
                iid = riid.contents
                if _guid_equal(iid, IID_IUnknown) or _guid_equal(iid, IID_IDropTarget):
                    ppv[0] = C.cast(self.pIDropTarget, C.c_void_p)
                    self._refcnt.value += 1
                    try:
                        logger.debug("==liuq debug== OLE.QI 命中 IDropTarget/IUnknown, ref=%s", self._refcnt.value)
                    except Exception:
                        pass
                    return S_OK
                ppv[0] = None
                try:
                    logger.debug("==liuq debug== OLE.QI 未命中所需接口，返回 E_NOINTERFACE")
                except Exception:
                    pass
                return E_NOINTERFACE
            except Exception as e:
                logger.debug("==liuq debug== OLE.QueryInterface 异常: %s", e)
                return E_NOINTERFACE

        def AddRef(self, this):
            self._refcnt.value += 1
            return self._refcnt.value

        def Release(self, this):
            if self._refcnt.value > 0:
                self._refcnt.value -= 1
            return self._refcnt.value

        # IDropTarget
        def DragEnter(self, this, pDataObj, grfKeyState, pt, pdwEffect):
            try:
                # 记录进入事件，并尝试探测是否具备 CF_HDROP
                try:
                    logger.info("==liuq debug== OLE.DragEnter")
                except Exception:
                    pass
                has_hdrop = False
                try:
                    fmt = FORMATETC(); fmt.cfFormat = CF_HDROP; fmt.ptd=None; fmt.dwAspect=DVASPECT_CONTENT; fmt.lindex=-1; fmt.tymed=TYMED_HGLOBAL
                    stg = STGMEDIUM()
                    hr = pDataObj.contents.lpVtbl.contents.GetData(pDataObj, C.byref(fmt), C.byref(stg))
                    if hr == S_OK and stg.tymed == TYMED_HGLOBAL and stg.hGlobal:
                        has_hdrop = True
                        # 立即释放，Drop 时再取
                        try:
                            ole32.ReleaseStgMedium(C.byref(stg))
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    logger.info("==liuq debug== OLE.DragEnter has_hdrop=%s", has_hdrop)
                except Exception:
                    pass
                pdwEffect[0] = DROPEFFECT_COPY
                return S_OK
            except Exception:
                pdwEffect[0] = DROPEFFECT_NONE
                return S_OK

        def DragOver(self, this, grfKeyState, pt, pdwEffect):
            try:
                pdwEffect[0] = DROPEFFECT_COPY
                return S_OK
            except Exception:
                pdwEffect[0] = DROPEFFECT_NONE
                return S_OK

        def DragLeave(self, this):
            try:
                logger.info("==liuq debug== OLE.DragLeave")
            except Exception:
                pass
            return S_OK

        def Drop(self, this, pDataObj, grfKeyState, pt, pdwEffect):
            try:
                files = self._extract_files_from_dataobj(pDataObj)
                try:
                    logger.info("==liuq debug== OLE.Drop 尝试解析，结果: %s", files)
                except Exception:
                    pass
                if files:
                    try:
                        self._on_files(files)
                    except Exception as e:
                        logger.error("==liuq debug== OLE.Drop 回调异常: %s", e)
                pdwEffect[0] = DROPEFFECT_COPY
                return S_OK
            except Exception as e:
                logger.error("==liuq debug== OLE.Drop 解析失败: %s", e)
                pdwEffect[0] = DROPEFFECT_NONE
                return S_OK

        def _extract_files_from_dataobj(self, pDataObj) -> List[str]:
            # 优先尝试 CF_HDROP
            files = self._extract_cf_hdrop(pDataObj)
            if files:
                return files
            # 其次尝试虚拟文件：FileGroupDescriptorW + FileContents
            try:
                vfiles = self._extract_virtual_files(pDataObj)
                if vfiles:
                    return vfiles
            except Exception as e:
                logger.debug("==liuq debug== 虚拟文件解析异常: %s", e)
            return []

        def _extract_cf_hdrop(self, pDataObj) -> List[str]:
            fmt = FORMATETC(); fmt.cfFormat = CF_HDROP; fmt.ptd=None; fmt.dwAspect=DVASPECT_CONTENT; fmt.lindex=-1; fmt.tymed=TYMED_HGLOBAL
            stg = STGMEDIUM()
            hr = pDataObj.contents.lpVtbl.contents.GetData(pDataObj, C.byref(fmt), C.byref(stg))
            if hr != S_OK or stg.tymed != TYMED_HGLOBAL or not stg.hGlobal:
                return []
            try:
                hdrop = C.c_void_p(stg.hGlobal)
                count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                results: List[str] = []
                for i in range(count):
                    length = shell32.DragQueryFileW(hdrop, i, None, 0)
                    buf = C.create_unicode_buffer(length + 1)
                    shell32.DragQueryFileW(hdrop, i, buf, length + 1)
                    results.append(buf.value)
                return results
            finally:
                try:
                    ole32.ReleaseStgMedium(C.byref(stg))
                except Exception:
                    pass

        def _extract_virtual_files(self, pDataObj) -> List[str]:
            # 解析 FileGroupDescriptorW 获取文件名，然后用 FileContents 取每个流，临时落盘
            results: List[str] = []
            if CFSTR_FILEDESCRIPTORW == 0 or CFSTR_FILECONTENTS == 0:
                return results
            # FileGroupDescriptorW 的 STGMEDIUM.hGlobal 指向一组 FILEDESCRIPTORW 结构
            class FILETIME(C.Structure):
                _fields_ = [("dwLowDateTime", C.c_uint32), ("dwHighDateTime", C.c_uint32)]
            class FILEDESCRIPTORW(C.Structure):
                _fields_ = [
                    ("dwFlags", C.c_uint32),
                    ("clsid", GUID),
                    ("sizel", C.c_int64),  # 简化
                    ("pointl", C.c_int64),  # 简化
                    ("dwFileAttributes", C.c_uint32),
                    ("ftCreationTime", FILETIME),
                    ("ftLastAccessTime", FILETIME),
                    ("ftLastWriteTime", FILETIME),
                    ("nFileSizeHigh", C.c_uint32),
                    ("nFileSizeLow", C.c_uint32),
                    ("cFileName", C.c_wchar * 260),
                ]
            # 取描述符
            fmt = FORMATETC(); fmt.cfFormat = CFSTR_FILEDESCRIPTORW; fmt.ptd=None; fmt.dwAspect=DVASPECT_CONTENT; fmt.lindex=-1; fmt.tymed=TYMED_HGLOBAL
            stg = STGMEDIUM()
            hr = pDataObj.contents.lpVtbl.contents.GetData(pDataObj, C.byref(fmt), C.byref(stg))
            if hr != S_OK or stg.tymed != TYMED_HGLOBAL or not stg.hGlobal:
                return results
            try:
                # 锁定 HGLOBAL 读取头部第一个 DWORD 表示文件数（规范实际更复杂，这里做常见兼容）
                kernel32.GlobalLock.argtypes = [C.c_void_p]
                kernel32.GlobalLock.restype = C.c_void_p
                kernel32.GlobalUnlock.argtypes = [C.c_void_p]
                base = kernel32.GlobalLock(stg.hGlobal)
                if not base:
                    return results
                try:
                    count = C.c_uint32.from_address(base).value
                    # 描述符数组紧随其后
                    array_ptr = base + 4
                    for i in range(min(count, 10)):
                        desc = FILEDESCRIPTORW.from_address(array_ptr + i * C.sizeof(FILEDESCRIPTORW))
                        name = desc.cFileName
                        # 用 FileContents 取第 i 个流
                        stream = self._get_file_stream_by_index(pDataObj, i)
                        if stream is None:
                            continue
                        # 将流保存为临时文件
                        try:
                            import tempfile, os
                            fd, tmp = tempfile.mkstemp(suffix="_dnd_" + (name or "temp"))
                            with os.fdopen(fd, 'wb') as f:
                                data = stream.Read(1 << 20)  # 读取1MB块，循环封装在 comtypes IStream 封装中；此处简化
                                if data:
                                    f.write(bytes(data))
                            results.append(tmp)
                        except Exception as e:
                            logger.debug("==liuq debug== 保存虚拟文件失败: %s", e)
                finally:
                    kernel32.GlobalUnlock(stg.hGlobal)
            finally:
                try:
                    ole32.ReleaseStgMedium(C.byref(stg))
                except Exception:
                    pass
            return results

    # RegisterDragDrop / RevokeDragDrop
    RegisterDragDrop = ole32.RegisterDragDrop
    RegisterDragDrop.argtypes = [C.c_void_p, C.c_void_p]
    RegisterDragDrop.restype = C.c_long

    RevokeDragDrop = ole32.RevokeDragDrop
    RevokeDragDrop.argtypes = [C.c_void_p]
    RevokeDragDrop.restype = C.c_long

    OleInitialize = ole32.OleInitialize
    OleInitialize.argtypes = [C.c_void_p]
    OleInitialize.restype = C.c_long

    _g_targets = {}
    _ole_inited = False

    def install_ole_droptarget(hwnd: int, on_files: Callable[[List[str]], None]):
        global _ole_inited
        if not _ole_inited:
            try:
                hr = OleInitialize(None)
                if hr == S_OK:
                    _ole_inited = True
                    logger.info("==liuq debug== OLE 初始化成功")
                else:
                    # 已初始化或其他返回，也继续
                    _ole_inited = True
                    logger.info("==liuq debug== OLE 初始化返回: 0x%x", hr)
            except Exception as e:
                logger.debug("==liuq debug== OLE 初始化异常: %s", e)
        try:
            # 预先尝试撤销旧注册，避免 DRAGDROP_E_ALREADYREGISTERED
            try:
                RevokeDragDrop(C.c_void_p(hwnd))
            except Exception:
                pass
            # 构建 DropTarget 并注册（优先使用 comtypes 实现）
            if _comtypes_available:
                dt = DropTargetCom(on_files)
                hr = RegisterDragDrop(C.c_void_p(hwnd), dt)
                if hr == S_OK:
                    _g_targets[hwnd] = dt
                    logger.info("==liuq debug== OLE IDropTarget 注册成功 hwnd=%s", hex(hwnd))
                    return dt
                else:
                    logger.info("==liuq debug== OLE RegisterDragDrop 失败: 0x%x", hr)
                    return None
            else:
                dt = DropTargetImpl(on_files)
                hr = RegisterDragDrop(C.c_void_p(hwnd), dt.pIDropTarget)
                if hr == S_OK:
                    _g_targets[hwnd] = dt
                    logger.info("==liuq debug== OLE IDropTarget 注册成功 hwnd=%s", hex(hwnd))
                    return dt
                else:
                    logger.info("==liuq debug== OLE RegisterDragDrop 失败: 0x%x", hr)
                    return None
        except Exception as e:
            logger.info("==liuq debug== 安装 OLE IDropTarget 异常: %s", e)
            return None

    def revoke_ole_droptarget(hwnd: int):
        try:
            if hwnd in _g_targets:
                RevokeDragDrop(C.c_void_p(hwnd))
                _g_targets.pop(hwnd, None)
                logger.info("==liuq debug== OLE IDropTarget 已撤销 hwnd=%s", hex(hwnd))
        except Exception as e:
            logger.debug("==liuq debug== 撤销 OLE IDropTarget 异常: %s", e)

