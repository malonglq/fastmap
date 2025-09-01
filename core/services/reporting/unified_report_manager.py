#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一报告管理器
==liuq debug== FastMapV2统一报告管理器

{{CHENGQI:
Action: Added; Timestamp: 2025-08-05 14:30:00 +08:00; Reason: 阶段1基础架构重构-创建统一报告管理器; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-08-05
版本: 1.0.0
描述: 统一管理不同类型的报告生成器，提供统一的报告生成接口
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from core.interfaces.report_generator import (
    IReportGenerator, ReportType
)

logger = logging.getLogger(__name__)


class ReportHistoryItem:
    """报告历史记录项"""

    def __init__(self,
                 report_type: ReportType,
                 report_name: str,
                 file_path: str,
                 generation_time: datetime,
                 configuration: Dict[str, Any]):
        self.report_type = report_type
        self.report_name = report_name
        self.file_path = file_path
        self.generation_time = generation_time
        self.configuration = configuration

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'report_type': self.report_type.value,
            'report_name': self.report_name,
            'file_path': self.file_path,
            'generation_time': self.generation_time.isoformat(),
            'configuration': self.configuration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportHistoryItem':
        """从字典创建"""
        return cls(
            report_type=ReportType(data['report_type']),
            report_name=data['report_name'],
            file_path=data['file_path'],
            generation_time=datetime.fromisoformat(data['generation_time']),
            configuration=data['configuration']
        )


class UnifiedReportManager:
    """
    统一报告管理器

    负责管理所有类型的报告生成器，提供统一的报告生成接口，
    并维护报告历史记录。
    """

    def __init__(self, history_file: Optional[str] = None):
        """
        初始化统一报告管理器

        Args:
            history_file: 历史记录文件路径
        """
        self.report_generators: Dict[ReportType, IReportGenerator] = {}
        self.history_file = history_file or "data/configs/report_history.json"
        self.history: List[ReportHistoryItem] = []

        # 确保历史记录目录存在
        Path(self.history_file).parent.mkdir(parents=True, exist_ok=True)

        # 加载历史记录
        self._load_history()

        logger.info("==liuq debug== 统一报告管理器初始化完成")

    def register_generator(self, generator: IReportGenerator) -> None:
        """
        注册报告生成器

        Args:
            generator: 报告生成器实例
        """
        report_type = generator.get_report_type()
        self.report_generators[report_type] = generator
        logger.info(f"==liuq debug== 注册报告生成器: {report_type.value}")

    def unregister_generator(self, report_type: ReportType) -> None:
        """
        注销报告生成器

        Args:
            report_type: 报告类型
        """
        if report_type in self.report_generators:
            del self.report_generators[report_type]
            logger.info(f"==liuq debug== 注销报告生成器: {report_type.value}")

    def get_available_report_types(self) -> List[ReportType]:
        """
        获取可用的报告类型

        Returns:
            可用报告类型列表
        """
        return list(self.report_generators.keys())

    def generate_report(self,
                       report_type: ReportType,
                       data: Dict[str, Any],
                       save_to_history: bool = True) -> str:
        """
        生成报告

        Args:
            report_type: 报告类型
            data: 报告数据
            save_to_history: 是否保存到历史记录

        Returns:
            生成的报告文件路径

        Raises:
            ValueError: 不支持的报告类型
            RuntimeError: 报告生成失败
        """
        # 检查报告生成器是否存在
        if report_type not in self.report_generators:
            raise ValueError(f"不支持的报告类型: {report_type.value}")

        try:
            generator = self.report_generators[report_type]

            # 验证数据
            if not generator.validate_data(data):
                raise ValueError("输入数据验证失败")

            logger.info(f"==liuq debug== 开始生成报告: {report_type.value}")

            # 生成报告
            report_path = generator.generate(data)

            # 保存到历史记录
            if save_to_history:
                history_item = ReportHistoryItem(
                    report_type=report_type,
                    report_name=generator.get_report_name(),
                    file_path=report_path,
                    generation_time=datetime.now(),
                    configuration=data.copy()
                )
                self.add_to_history(history_item)

            logger.info(f"==liuq debug== 报告生成完成: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"==liuq debug== 报告生成失败: {e}")
            raise RuntimeError(f"报告生成失败: {e}")

    def add_to_history(self, item: ReportHistoryItem) -> None:
        """
        添加到历史记录

        Args:
            item: 历史记录项
        """
        self.history.insert(0, item)  # 最新的在前面

        # 限制历史记录数量（保留最近100条）
        if len(self.history) > 100:
            self.history = self.history[:100]

        # 保存历史记录
        self._save_history()

    def get_history(self,
                   report_type: Optional[ReportType] = None,
                   limit: Optional[int] = None) -> List[ReportHistoryItem]:
        """
        获取历史记录

        Args:
            report_type: 报告类型过滤
            limit: 限制数量

        Returns:
            历史记录列表
        """
        history = self.history

        # 按报告类型过滤
        if report_type:
            history = [item for item in history if item.report_type == report_type]

        # 限制数量
        if limit:
            history = history[:limit]

        return history

    def clear_history(self) -> None:
        """清空历史记录"""
        self.history.clear()
        self._save_history()
        logger.info("==liuq debug== 历史记录已清空")

    def _load_history(self) -> None:
        """加载历史记录"""
        try:
            if Path(self.history_file).exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = [ReportHistoryItem.from_dict(item) for item in data]
                logger.info(f"==liuq debug== 加载历史记录: {len(self.history)}条")
        except Exception as e:
            logger.warning(f"==liuq debug== 加载历史记录失败: {e}")
            self.history = []


    def reload_history(self) -> None:
        """从磁盘重新加载历史记录（用于多实例间同步）"""
        try:
            self._load_history()
            logger.debug("==liuq debug== 历史记录已从磁盘重新加载")
        except Exception as e:
            logger.warning(f"==liuq debug== 重新加载历史记录失败: {e}")

    def _save_history(self) -> None:
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                data = [item.to_dict() for item in self.history]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"==liuq debug== 保存历史记录失败: {e}")

    def get_generator_info(self, report_type: ReportType) -> Optional[Dict[str, str]]:
        """
        获取报告生成器信息

        Args:
            report_type: 报告类型

        Returns:
            生成器信息字典
        """
        if report_type in self.report_generators:
            generator = self.report_generators[report_type]
            return {
                'type': report_type.value,
                'name': generator.get_report_name(),
                'class': generator.__class__.__name__
            }
        return None
