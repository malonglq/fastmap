#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF AWB 解析服务（集成 DLL + 解析器注册表）
==liuq debug== FastMapV2 ExifParserService

{{CHENGQI:
Action: Modified; Timestamp: 2025-08-11 13:10:00 +08:00; Reason: 集成 3a_parser.dll 并增强字段解析容错; Principle_Applied: KISS, SecureCoding-ErrorHandling;
}}
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import os
import logging
import ctypes as C
from ctypes import c_void_p, byref

# JSON 加速：优先使用 orjson（条件启用）
try:
    import orjson as _fastjson  # type: ignore
    def _loads_bytes(b: bytes):
        return _fastjson.loads(b)
    _FASTJSON_LIB = "orjson"
except Exception:
    import json as _fastjson  # fallback
    def _loads_bytes(b: bytes):
        try:
            return _fastjson.loads(b.decode('utf-8', errors='ignore'))
        except Exception:
            return {}
    _FASTJSON_LIB = "json"

from core.interfaces.exif_processing import (
    IExifParserService, ExifParseOptions, ExifParseResult, ExifRecord
)

logger = logging.getLogger(__name__)


def _safe_float(x) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None


def _flatten(d: Dict[str, Any], parent: str = '', sep: str = '_') -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in (d or {}).items():
        nk = f"{parent}{sep}{k}" if parent else str(k)
        if isinstance(v, dict):
            out.update(_flatten(v, nk, sep))
        else:
            out[nk] = v
    return out

# 仅返回键名的扁平化，避免构建大字典降低内存/时间开销
def _flatten_keys_only(d: Dict[str, Any], parent: str = '', sep: str = '_'):
    for k, v in (d or {}).items():
        nk = f"{parent}{sep}{k}" if parent else str(k)
        if isinstance(v, dict):
            for sub in _flatten_keys_only(v, nk, sep):
                yield sub
        else:
            yield nk

# 迭代产生(扁平键, 值)，避免构建完整大字典
def _flatten_items(d: Dict[str, Any], parent: str = '', sep: str = '_'):
    for k, v in (d or {}).items():
        nk = f"{parent}{sep}{k}" if parent else str(k)
        if isinstance(v, dict):
            for it in _flatten_items(v, nk, sep):
                yield it
        else:
            yield nk, v



def _get_by_flat_key(d: Dict[str, Any], flat_key: str, sep: str = '_'):
    cur = d
    for seg in str(flat_key).split(sep):
        if not isinstance(cur, dict) or seg not in cur:
            return None
        cur = cur[seg]
    return cur


class ExifParserService(IExifParserService):
    """
    解析策略：
    - 优先使用注入的 file_reader（便于单测）
    - 否则尝试调用 DLL (dll/Release/3a_parser.dll) 的 getAwbExifJson 返回 JSON 并解析
    - 字段解析使用“注册表 + 模糊匹配”两步：先精确键，再对扁平化key进行关键词匹配
    """

    def __init__(self, file_reader: Optional[Callable[[Path], Dict[str, Any]]] = None):
        self.file_reader = file_reader
        self._dll_loaded = False
        self._dll_lib = None
        self._dll_handle = c_void_p(None)
        self._debug_dumped = False
        # 字段解析器注册表（已废弃：改为直接取原始扁平键值）
        self.field_resolvers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        # 字段映射规范（用于GUI透明化展示）（保留接口，但不再使用）
        self._field_mapping_spec = {}

    # ===== DLL 相关 =====
    def _try_init_dll(self):
        if self._dll_loaded:
            return
        try:
            base = Path(__file__).resolve().parents[2]
            candidates = [
                base / '0_3a_parser_py' / 'dll' / 'Release' / '3a_parser.dll',
                base / 'dll' / 'Release' / '3a_parser.dll',
            ]
            dll_path = None
            for c in candidates:
                if c.exists():
                    dll_path = c
                    break
            if not dll_path:
                logger.warning("==liuq debug== 未找到 3a_parser.dll，候选路径: %s", candidates)
                return
            logger.info("==liuq debug== 加载 DLL: %s", dll_path)
            lib = C.cdll.LoadLibrary(str(dll_path))
            init = lib.init
            init.argtypes = [C.POINTER(c_void_p)]
            init.restype = None
            init(byref(self._dll_handle))
            self._dll_lib = lib
            self._dll_loaded = True
            logger.info("==liuq debug== DLL 初始化完成: handle=%s", self._dll_handle)
        except Exception as e:
            # 无 DLL / 无法加载，保持未加载状态
            logger.error("==liuq debug== DLL 加载失败: %s", e)
            self._dll_loaded = False
            self._dll_lib = None

    def _dll_get_awb_raw(self, file_path: Path) -> Dict[str, Any]:
        try:
            import time as _t
            if not self._dll_loaded:
                self._try_init_dll()
            if not self._dll_loaded or not self._dll_lib:
                return {}
            func = self._dll_lib.getAwbExifJson
            func.argtypes = [C.c_void_p, C.c_char_p, C.c_char_p, C.c_bool, C.c_bool]
            func.restype = C.c_char_p
            # 路径编码注意：含中文路径时，DLL可能使用ACP解析，采用'mbcs'传参
            raw_path = str(file_path)
            has_nonascii = any(ord(ch) > 127 for ch in raw_path)
            path_bytes = raw_path.encode('mbcs', errors='ignore') if has_nonascii else raw_path.encode('utf-8')
            in_str = C.c_char_p(path_bytes)
            # 传入 None 作为 exif_ptr；尝试 is_reverse=True 可提升兼容性
            t0 = _t.time()
            out = func(self._dll_handle, in_str, None, C.c_bool(True), C.c_bool(False))
            t1 = _t.time()
            b = bytes(out) if out else b'{}'
            data = _loads_bytes(b)
            t2 = _t.time()
            try:
                logger.debug("==liuq debug== profile dll=%.1fms json=%.1fms lib=%s", (t1 - t0) * 1000.0, (t2 - t1) * 1000.0, _FASTJSON_LIB)
            except Exception:
                pass
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error("==liuq debug== DLL 调用失败: %s", e)
    def get_field_mapping_table(self) -> Dict[str, Dict[str, Any]]:
        # 兼容接口：当前所有字段视为原始键名，映射为“来源=自身，无候选”
        return {}

    # ===== 字段解析器（已移除：统一按原始键名取值） =====
    def _build_field_resolvers(self) -> Dict[str, Callable[[Dict[str, Any]], Any]]:
        return {}

    # ===== 工具 =====
    def _iter_images(self, root: Path, options: ExifParseOptions) -> List[Path]:
        exts = set([e.lower() for e in options.extensions])
        files: List[Path] = []
        root = Path(root)
        if options.recursive:
            for dirpath, _, filenames in os.walk(root):
                for n in filenames:
                    p = Path(dirpath) / n
                    if p.suffix.lower() in exts:
                        files.append(p)
        else:
            for p in root.iterdir():
                if p.is_file() and p.suffix.lower() in exts:
                    files.append(p)
        try:
            logger.info("==liuq debug== 扫描目录: %s, 递归: %s, 扩展: %s, 文件数: %d", str(root), options.recursive, sorted(list(exts)), len(files))
        except Exception:
            pass
        return files

    def _read_raw_exif(self, file_path: Path) -> Dict[str, Any]:
        # 1) 注入的 file_reader 优先（单测使用）
        if self.file_reader:
            try:
                return self.file_reader(file_path)
            except Exception:
                return {}
        # 2) DLL 解析
        raw = self._dll_get_awb_raw(file_path)
        return raw or {}

    # ===== 主流程 =====
    def parse_directory(self, root_dir: Path, options: ExifParseOptions) -> ExifParseResult:
        import time as _t
        root_dir = Path(root_dir)
        t0 = _t.time()
        errors: List[str] = []
        records: List[ExifRecord] = []
        available_fields = set()
        raw_available_keys = set()

        logger.info("==liuq debug== parse_directory 开始: root=%s, recursive=%s, fields=%s", str(root_dir), getattr(options, 'recursive', None), getattr(options, 'selected_fields', None))
        files = self._iter_images(root_dir, options)
        total = len(files)
        raw_order: List[str] = []
        for idx, fp in enumerate(files):
            # 取消检查（来自GUI）
            if options.cancel_check and options.cancel_check():
                errors.append("用户取消")
                break
            rec = ExifRecord(image_path=fp, image_name=fp.name)
            try:
                raw = self._read_raw_exif(fp)
                # 保留原始JSON（按需）
                if options.keep_raw_json:
                    rec.raw_json = raw
                # 构建 raw_flat（按需）
                if options.build_raw_flat:
                    flat = _flatten(raw)
                    rec.raw_flat = flat
                # 统计可用集合/顺序（按需）
                if options.compute_available:
                    for k in _flatten_keys_only(raw):
                        if k not in raw_available_keys:
                            raw_order.append(k)
                        raw_available_keys.add(k)
                    if idx == 0 and options.debug_log_keys and not self._debug_dumped:
                        keys_sample = raw_order[:120]
                        logger.info("==liuq debug== EXIF扁平键样例(前120): %s", keys_sample)
                        self._debug_dumped = True
                # 仅抓取选定字段（定位式索引 + 失败回退扫描）
                if options.selected_fields:
                    _t0_sel = _t.time()
                    hit = {}
                    for k in options.selected_fields:
                        v = _get_by_flat_key(raw, k)
                        if v is None:
                            # 回退：精确扫描（仅当前键）
                            for fk, fv in _flatten_items(raw):
                                if fk == k:
                                    v = fv
                                    break
                        if v is not None:
                            hit[k] = v
                            rec.field_sources[k] = k
                            available_fields.add(k)
                    rec.fields.update(hit)
                    _t1_sel = _t.time()
                    try:
                        if idx == 0 or (idx % 50 == 0):
                            logger.info("==liuq debug== profile select=%.1fms sel_fields=%d hits=%d file=%s", (_t1_sel - _t0_sel) * 1000.0, len(options.selected_fields or []), len(hit), rec.image_name)
                    except Exception:
                        pass
            except Exception as e:
                rec.errors = str(e)
                errors.append(f"读取 {fp.name} 失败: {e}")
            finally:
                records.append(rec)
                # 进度回调（来自GUI）
                if options.on_progress:
                    try:
                        options.on_progress(len(records), total, rec.image_name)
                    except Exception:
                        pass

        res = ExifParseResult(
            records=records,
            total=len(records),
            errors=errors,
            available_fields=available_fields,
            raw_available_keys=raw_available_keys if options.compute_available else set(),
            raw_available_order=raw_order if options.compute_available else []
        )
        try:
            dt = int((_t.time() - t0) * 1000)
            logger.info("==liuq debug== parse_directory 完成: files=%d, ms=%d, keep_raw=%s, flat=%s, avail=%s",
                        len(records), dt, options.keep_raw_json, options.build_raw_flat, options.compute_available)
        except Exception:
            pass
        return res

    # ===== 轻量键名发现 =====
    def discover_keys(self, root_dir: Path, recursive: bool = True, sample: int = 3) -> List[str]:
        """
        采样若干图片，仅解析原始JSON并返回扁平化键名的“首见顺序”。
        - 不构建 ExifRecord，不保存 raw_json，尽可能减少内存与IO
        - sample 最小为 1
        """
        root = Path(root_dir)
        opts = ExifParseOptions(selected_fields=[], recursive=recursive)
        files = self._iter_images(root, opts)
        if not files:
            return []
        n = max(1, int(sample or 1))
        keys: List[str] = []
        seen = set()
        for fp in files[:n]:
            try:
                raw = self._read_raw_exif(fp)
                for k in _flatten_keys_only(raw):
                    if k not in seen:
                        keys.append(k)
                        seen.add(k)
            except Exception:
                continue
        return keys
