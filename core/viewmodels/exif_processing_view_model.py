#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF处理ViewModel
==liuq debug== FastMapV2 EXIF处理ViewModel

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: EXIF处理Tab的ViewModel，处理图片目录解析、字段选择、CSV导出等业务逻辑
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from PyQt5.QtCore import pyqtSignal, QThread

from core.infrastructure.base_view_model import BaseViewModel
from core.infrastructure.event_bus import Event, EventType
from core.services.exif_processing import ExifParserService, ExifCsvExporter, ExifRawExporter
from core.interfaces.exif_processing import ExifParseOptions

logger = logging.getLogger(__name__)


class ExifProcessingViewModel(BaseViewModel):
    """
    EXIF处理ViewModel
    
    负责处理：
    - 图片目录选择与扫描
    - EXIF字段发现
    - 字段选择管理
    - CSV导出
    - 进度管理
    """
    
    # 额外信号定义
    directory_selected = pyqtSignal(str)               # 目录选择
    fields_discovered = pyqtSignal(list)               # 字段发现完成
    export_progress = pyqtSignal(int, int, str)        # 导出进度 (processed, total, current_file)
    export_completed = pyqtSignal(str)                 # 导出完成
    export_failed = pyqtSignal(str)                    # 导出失败
    
    def __init__(self):
        super().__init__()
        
        # 解析依赖的服务
        self._exif_parser: ExifParserService = self.resolve_service(ExifParserService)
        self._csv_exporter: ExifCsvExporter = self.resolve_service(ExifCsvExporter)
        self._raw_exporter: ExifRawExporter = self.resolve_service(ExifRawExporter)
        
        # ViewModel状态
        self._source_directory: Optional[Path] = None
        self._available_fields: List[str] = []
        self._selected_fields: List[str] = []
        self._export_options: ExifParseOptions = ExifParseOptions()
        self._last_export_result: Optional[Any] = None
        
        # 工作线程
        self._discovery_worker: Optional[QThread] = None
        self._export_worker: Optional[QThread] = None
        
        # 初始化属性
        self._initialize_properties()
        
        logger.debug("==liuq debug== ExifProcessingViewModel 初始化完成")
    
    def _initialize_properties(self):
        """初始化属性"""
        self.set_property("source_directory", "", False)
        self.set_property("directory_name", "未选择目录", False)
        self.set_property("available_fields", [], False)
        self.set_property("selected_fields", [], False)
        self.set_property("recursive_scan", True, False)
        self.set_property("include_raw_json", False, False)
        self.set_property("output_path", "", False)
        self.set_property("can_discover_fields", False, False)
        self.set_property("can_export", False, False)
        self.set_property("export_progress_text", "", False)
    
    def _setup_event_subscriptions(self):
        """设置事件订阅"""
        # 订阅Tab切换事件
        self.subscribe_event(EventType.TAB_SWITCHED, self._on_tab_switched)
        
        # 订阅应用程序事件
        self.subscribe_event(EventType.APPLICATION_SHUTDOWN, self._on_application_shutdown)
    
    # 属性访问器
    @property
    def source_directory(self) -> str:
        """源目录路径"""
        return self.get_property("source_directory", "")
    
    @property
    def directory_name(self) -> str:
        """目录名称"""
        return self.get_property("directory_name", "未选择目录")
    
    @property
    def available_fields(self) -> List[str]:
        """可用字段列表"""
        return self.get_property("available_fields", [])
    
    @property
    def selected_fields(self) -> List[str]:
        """已选择字段列表"""
        return self.get_property("selected_fields", [])
    
    @property
    def recursive_scan(self) -> bool:
        """是否递归扫描子目录"""
        return self.get_property("recursive_scan", True)
    
    @property
    def include_raw_json(self) -> bool:
        """是否包含原始JSON"""
        return self.get_property("include_raw_json", False)
    
    @property
    def output_path(self) -> str:
        """输出文件路径"""
        return self.get_property("output_path", "")
    
    @property
    def can_discover_fields(self) -> bool:
        """是否可以发现字段"""
        return self.get_property("can_discover_fields", False)
    
    @property
    def can_export(self) -> bool:
        """是否可以导出"""
        return self.get_property("can_export", False)
    
    # 业务方法
    def select_source_directory(self, directory_path: str) -> bool:
        """
        选择源图片目录
        
        Args:
            directory_path: 目录路径
            
        Returns:
            bool: 是否选择成功
        """
        try:
            dir_path = Path(directory_path)
            if not dir_path.exists() or not dir_path.is_dir():
                self.handle_error(ValueError(f"目录不存在或不是有效目录: {directory_path}"))
                return False
            
            # 更新状态
            self._source_directory = dir_path
            self.set_property("source_directory", str(dir_path))
            self.set_property("directory_name", dir_path.name)
            self.set_property("can_discover_fields", True)
            
            # 清空之前的字段信息
            self._available_fields = []
            self._selected_fields = []
            self.set_property("available_fields", [])
            self.set_property("selected_fields", [])
            self.set_property("can_export", False)
            
            # 设置默认输出路径
            default_output = str(dir_path / "exif_export.csv")
            self.set_property("output_path", default_output)
            
            # 发布事件
            self.emit_event(EventType.EXIF_DIRECTORY_SELECTED, {
                "directory_path": str(dir_path),
                "directory_name": dir_path.name
            })
            
            self.directory_selected.emit(str(dir_path))
            self.emit_status(f"选择目录: {dir_path.name}")
            
            logger.info(f"==liuq debug== 选择EXIF源目录: {dir_path}")
            return True
            
        except Exception as e:
            self.handle_error(e, f"选择目录失败: {directory_path}")
            return False
    
    def discover_fields(self, sample_count: int = 5) -> bool:
        """
        发现EXIF字段
        
        Args:
            sample_count: 采样数量
            
        Returns:
            bool: 是否开始发现过程
        """
        try:
            if not self._source_directory:
                self.handle_error(ValueError("请先选择源目录"))
                return False
            
            # 如果已有工作线程在运行，先停止
            if self._discovery_worker and self._discovery_worker.isRunning():
                self._discovery_worker.quit()
                self._discovery_worker.wait()
            
            self.set_busy(True, f"正在发现EXIF字段（采样{sample_count}张图片）...")
            
            # 创建发现工作线程
            from gui.tabs.exif_processing_tab import _DiscoverWorker  # 复用现有的Worker
            self._discovery_worker = _DiscoverWorker(
                self._exif_parser, 
                self._source_directory, 
                self.recursive_scan, 
                sample_count
            )
            
            # 连接信号
            self._discovery_worker.finished.connect(self._on_fields_discovered)
            
            # 启动线程
            self._discovery_worker.start()
            
            logger.info(f"==liuq debug== 开始发现EXIF字段，目录: {self._source_directory}")
            return True
            
        except Exception as e:
            self.handle_error(e, "发现EXIF字段失败")
            return False
    
    def _on_fields_discovered(self, fields: List[str]):
        """字段发现完成处理"""
        try:
            self._available_fields = fields
            self.set_property("available_fields", fields)
            
            # 如果有字段，则可以进行导出
            if fields:
                self.set_property("can_export", True)
                
                # 发布事件
                self.emit_event(EventType.EXIF_FIELDS_DISCOVERED, {
                    "fields": fields,
                    "count": len(fields),
                    "directory": str(self._source_directory)
                })
                
                self.fields_discovered.emit(fields)
                self.emit_status(f"发现 {len(fields)} 个EXIF字段")
                
                logger.info(f"==liuq debug== EXIF字段发现完成: {len(fields)} 个字段")
            else:
                self.emit_status("未发现可用的EXIF字段")
                logger.warning("==liuq debug== 未发现可用的EXIF字段")
            
        except Exception as e:
            self.handle_error(e, "处理发现结果失败")
        finally:
            self.set_busy(False)
    
    def set_selected_fields(self, fields: List[str]):
        """
        设置选择的字段
        
        Args:
            fields: 选择的字段列表
        """
        try:
            # 验证字段是否在可用列表中
            valid_fields = [f for f in fields if f in self._available_fields]
            
            self._selected_fields = valid_fields
            self.set_property("selected_fields", valid_fields)
            
            # 更新导出状态
            can_export = len(valid_fields) > 0 and bool(self._source_directory)
            self.set_property("can_export", can_export)
            
            logger.debug(f"==liuq debug== 设置选择字段: {len(valid_fields)} 个")
            
        except Exception as e:
            self.handle_error(e, "设置选择字段失败")
    
    def set_export_options(self, recursive: bool = None, include_raw: bool = None, 
                          output_path: str = None):
        """
        设置导出选项
        
        Args:
            recursive: 是否递归扫描
            include_raw: 是否包含原始JSON
            output_path: 输出路径
        """
        try:
            if recursive is not None:
                self.set_property("recursive_scan", recursive)
            
            if include_raw is not None:
                self.set_property("include_raw_json", include_raw)
            
            if output_path is not None:
                self.set_property("output_path", output_path)
            
            logger.debug("==liuq debug== 导出选项已更新")
            
        except Exception as e:
            self.handle_error(e, "设置导出选项失败")
    
    def export_to_csv(self) -> bool:
        """
        导出到CSV文件
        
        Returns:
            bool: 是否开始导出过程
        """
        try:
            if not self.can_export:
                self.handle_error(ValueError("无法导出：请检查目录和字段选择"))
                return False
            
            if not self._selected_fields:
                self.handle_error(ValueError("请至少选择一个字段"))
                return False
            
            # 如果已有导出线程在运行，先停止
            if self._export_worker and self._export_worker.isRunning():
                self._export_worker.quit()
                self._export_worker.wait()
            
            self.set_busy(True, "正在导出EXIF数据...")
            
            # 构建导出选项
            export_options = ExifParseOptions(
                selected_fields=self._selected_fields,
                recursive=self.recursive_scan,
                keep_raw_json=self.include_raw_json,
                build_raw_flat=False,
                compute_available=False,
                debug_log_keys=False
            )
            
            output_path = Path(self.output_path)
            
            # 创建导出工作线程
            from gui.tabs.exif_processing_tab import _ExportWorker  # 复用现有的Worker
            self._export_worker = _ExportWorker(
                self._exif_parser,
                self._csv_exporter,
                self._source_directory,
                export_options,
                output_path,
                self._selected_fields
            )
            
            # 连接信号
            self._export_worker.progress.connect(self._on_export_progress)
            self._export_worker.finished_ok.connect(self._on_export_completed)
            self._export_worker.failed.connect(self._on_export_failed)
            
            # 启动线程
            self._export_worker.start()
            
            # 发布事件
            self.emit_event(EventType.EXIF_PROCESSING_STARTED, {
                "directory": str(self._source_directory),
                "output_path": str(output_path),
                "fields_count": len(self._selected_fields)
            })
            
            logger.info(f"==liuq debug== 开始导出EXIF数据到: {output_path}")
            return True
            
        except Exception as e:
            self.handle_error(e, "开始导出失败")
            return False
    
    def cancel_export(self):
        """取消导出"""
        try:
            if self._export_worker and self._export_worker.isRunning():
                self._export_worker.cancel()
                self.set_busy(False)
                self.set_property("export_progress_text", "已请求取消...")
                self.emit_status("导出已取消")
                
                logger.info("==liuq debug== 用户取消EXIF导出")
            
        except Exception as e:
            self.handle_error(e, "取消导出失败")
    
    def _on_export_progress(self, processed: int, total: int, current_file: str):
        """导出进度处理"""
        try:
            progress_text = f"进度: {processed}/{total} - {current_file}"
            self.set_property("export_progress_text", progress_text)
            
            # 发布事件
            self.emit_event(EventType.EXIF_PROCESSING_PROGRESS, {
                "processed": processed,
                "total": total,
                "current_file": current_file,
                "percentage": (processed / total * 100) if total > 0 else 0
            })
            
            self.export_progress.emit(processed, total, current_file)
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理导出进度失败: {e}")
    
    def _on_export_completed(self, result: Any, output_path: str):
        """导出完成处理"""
        try:
            self._last_export_result = result
            self.set_property("export_progress_text", "")
            
            # 发布事件
            self.emit_event(EventType.EXIF_PROCESSING_COMPLETED, {
                "output_path": output_path,
                "success": True,
                "result": result
            })
            
            self.emit_event(EventType.EXIF_EXPORT_COMPLETED, {
                "output_path": output_path
            })
            
            self.export_completed.emit(output_path)
            self.emit_status(f"导出完成: {output_path}")
            
            logger.info(f"==liuq debug== EXIF导出完成: {output_path}")
            
        except Exception as e:
            self.handle_error(e, "处理导出完成失败")
        finally:
            self.set_busy(False)
    
    def _on_export_failed(self, error_message: str):
        """导出失败处理"""
        try:
            self.set_property("export_progress_text", "")
            
            # 发布事件
            self.emit_event(EventType.EXIF_PROCESSING_COMPLETED, {
                "success": False,
                "error": error_message
            })
            
            self.export_failed.emit(error_message)
            self.handle_error(Exception(error_message), "EXIF导出失败")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理导出失败失败: {e}")
        finally:
            self.set_busy(False)
    
    # 事件处理器
    def _on_tab_switched(self, event: Event):
        """Tab切换事件处理"""
        if event.data and event.data.get("tab_name") == "EXIF处理":
            logger.debug("==liuq debug== 切换到EXIF处理Tab")
    
    def _on_application_shutdown(self, event: Event):
        """应用程序关闭事件处理"""
        self.cleanup()
    
    # 生命周期方法
    def cleanup(self):
        """清理资源"""
        try:
            # 停止工作线程
            if self._discovery_worker and self._discovery_worker.isRunning():
                self._discovery_worker.quit()
                self._discovery_worker.wait()
            
            if self._export_worker and self._export_worker.isRunning():
                self._export_worker.quit()
                self._export_worker.wait()
            
            # 清理状态
            self._source_directory = None
            self._available_fields = []
            self._selected_fields = []
            self._last_export_result = None
            
            logger.debug("==liuq debug== ExifProcessingViewModel 清理完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== ExifProcessingViewModel 清理失败: {e}")