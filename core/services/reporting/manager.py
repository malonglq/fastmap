#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一报告管理器，兼容旧版接口."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterable

from core.interfaces.report_generator import IReportGenerator, ReportType

logger = logging.getLogger(__name__)


def _sanitize_config(value: Any) -> Any:
    """将配置信息转换为可序列化的结构."""
    from pathlib import Path as _Path

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, _Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _sanitize_config(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_config(v) for v in value]
    if hasattr(value, "to_dict") and callable(getattr(value, "to_dict")):
        try:
            return _sanitize_config(value.to_dict())
        except Exception:  # pragma: no cover
            return str(value)
    return str(value)


@dataclass
class ReportHistoryItem:
    """报告历史记录条目."""

    report_type: ReportType
    report_name: str
    file_path: str
    generation_time: datetime
    configuration: Dict[str, Any]
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_type": self.report_type.value,
            "report_name": self.report_name,
            "file_path": self.file_path,
            "generation_time": self.generation_time.isoformat(),
            "configuration": _sanitize_config(self.configuration),
            "success": self.success,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReportHistoryItem":
        try:
            report_type = ReportType(data["report_type"])
        except Exception:
            report_type = ReportType.EXIF_COMPARISON
        generation_time = data.get("generation_time")
        if isinstance(generation_time, str):
            try:
                generation_time = datetime.fromisoformat(generation_time)
            except ValueError:
                generation_time = datetime.now()
        elif not isinstance(generation_time, datetime):
            generation_time = datetime.now()
        return cls(
            report_type=report_type,
            report_name=data.get("report_name", report_type.value),
            file_path=data.get("file_path", ""),
            generation_time=generation_time,
            configuration=_sanitize_config(data.get("configuration", {})),
            success=bool(data.get("success", True)),
        )


class UnifiedReportManager:
    """统一的报告生成与历史记录管理器."""

    def __init__(self, history_path: Optional[Path] = None) -> None:
        self._generators: Dict[ReportType, IReportGenerator] = {}
        self._history_file = Path(history_path or Path("data") / "configs" / "report_history.json")
        self._history: List[ReportHistoryItem] = []
        self._load_history()

    # --------------------------- 报告生成器管理 ---------------------------
    def register_generator(self, generator: IReportGenerator) -> None:
        report_type = generator.get_report_type()
        self._generators[report_type] = generator
        logger.debug("注册报告生成器: %s (%s)", generator.get_report_name(), report_type.value)

    def unregister_generator(self, report_type: ReportType) -> None:
        self._generators.pop(report_type, None)
        logger.debug("注销报告生成器: %s", report_type.value)

    def get_available_report_types(self) -> List[ReportType]:
        return list(self._generators.keys())

    # --------------------------- 报告生成流程 ---------------------------
    def generate_report(self, report_type: ReportType, data: Dict[str, Any]) -> str:
        generator = self._generators.get(report_type)
        if not generator:
            raise ValueError(f"未注册的报告类型: {report_type}")

        if hasattr(generator, "validate_data"):
            if not generator.validate_data(data):
                raise ValueError("报告数据校验失败")

        report_path = generator.generate(data)
        history_item = ReportHistoryItem(
            report_type=report_type,
            report_name=generator.get_report_name(),
            file_path=report_path,
            generation_time=datetime.now(),
            configuration=_sanitize_config(data),
            success=True,
        )
        self._add_history_item(history_item)
        return report_path

    # --------------------------- 历史记录管理 ---------------------------
    def get_history(self, limit: Optional[int] = None) -> List[ReportHistoryItem]:
        items = sorted(self._history, key=lambda item: item.generation_time, reverse=True)
        if limit is not None:
            return items[:limit]
        return items

    def clear_history(self) -> None:
        self._history = []
        if self._history_file.exists():
            try:
                self._history_file.unlink()
            except OSError as exc:
                logger.warning("删除历史文件失败: %s", exc)
        logger.debug("历史记录已清空")

    def remove_from_history(self, file_path: str) -> None:
        original_len = len(self._history)
        self._history = [item for item in self._history if item.file_path != file_path]
        if len(self._history) != original_len:
            self._save_history()
            logger.debug("已从历史记录移除: %s", file_path)

    def reload_history(self) -> None:
        self._load_history()

    # --------------------------- 内部工具 ---------------------------
    def _add_history_item(self, item: ReportHistoryItem) -> None:
        self._history = [existing for existing in self._history if existing.file_path != item.file_path]
        self._history.append(item)
        self._save_history()

    def _load_history(self) -> None:
        if not self._history_file.exists():
            self._history = []
            return
        try:
            data = json.loads(self._history_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self._history = [ReportHistoryItem.from_dict(entry) for entry in data]
            else:
                self._history = []
        except Exception as exc:
            logger.warning("读取报告历史失败: %s", exc)
            self._history = []

    def _save_history(self) -> None:
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            serialized: Iterable[Dict[str, Any]] = [item.to_dict() for item in self._history]
            self._history_file.write_text(
                json.dumps(list(serialized), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error("保存报告历史失败: %s", exc)


__all__ = ["UnifiedReportManager", "ReportHistoryItem"]
