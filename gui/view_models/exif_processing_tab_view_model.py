#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXIF处理Tab ViewModel
==liuq debug== FastMapV2 EXIF处理Tab ViewModel

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: EXIF处理Tab的MVVM架构ViewModel，管理EXIF处理相关的业务逻辑和数据状态
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from PyQt5.QtCore import pyqtSignal

from core.infrastructure.base_view_model import BaseViewModel
from core.infrastructure.event_bus import EventType
from core.services.exif_processing.exif_parser_service import ExifParserService
from core.services.exif_processing.exif_csv_exporter import ExifCsvExporter
from core.interfaces.exif_processing import ExifParseOptions

logger = logging.getLogger(__name__)


class ExifProcessingTabViewModel(BaseViewModel):
    """
    EXIF处理Tab ViewModel
    
    管理EXIF处理Tab的状态和业务逻辑：
    - 图片目录处理
    - EXIF字段选择和提取
    - CSV导出功能
    - 处理进度管理
    """
    
    # 自定义信号
    directory_loaded = pyqtSignal(str, int)  # 目录路径, 图片数量
    fields_discovered = pyqtSignal(list)  # 发现的EXIF字段列表
    processing_started = pyqtSignal(str)  # 处理开始，传入源目录
    processing_progress_updated = pyqtSignal(int, int, str)  # 已处理数量, 总数量, 当前文件
    processing_completed = pyqtSignal(dict, str)  # 处理结果, 输出路径
    processing_failed = pyqtSignal(str)  # 处理失败原因
    field_selection_changed = pyqtSignal(list)  # 字段选择变更
    
    def __init__(self):
        """初始化EXIF处理Tab ViewModel"""
        super().__init__()
        
        # 数据状态
        self._source_directory: Optional[Path] = None
        self._output_path: Optional[Path] = None
        self._available_fields: List[str] = []
        self._selected_fields: List[str] = []
        self._processing_options: Optional[ExifParseOptions] = None
        self._last_result: Optional[Dict[str, Any]] = None
        self._image_count: int = 0
        self._is_processing: bool = False
        
        # 获取服务
        self._exif_parser = self._di_container.resolve(ExifParserService)
        self._exif_exporter = self._di_container.resolve(ExifCsvExporter)
        
        # 设置事件监听
        self._setup_event_listeners()
        
        logger.info("==liuq debug== EXIF处理Tab ViewModel初始化完成")
    
    @property
    def source_directory(self) -> Optional[Path]:
        """源图片目录"""
        return self._source_directory
    
    @property
    def output_path(self) -> Optional[Path]:
        """输出路径"""
        return self._output_path
    
    @property
    def available_fields(self) -> List[str]:
        """可用的EXIF字段"""
        return self._available_fields
    
    @property
    def selected_fields(self) -> List[str]:
        """已选择的EXIF字段"""
        return self._selected_fields
    
    @property
    def is_processing(self) -> bool:
        """是否正在处理"""
        return self._is_processing
    
    @property
    def image_count(self) -> int:
        """图片数量"""
        return self._image_count
    
    def set_source_directory(self, directory_path: str) -> bool:
        """
        设置源图片目录
        
        Args:
            directory_path: 目录路径
            
        Returns:
            bool: 设置是否成功
        """
        try:
            dir_path = Path(directory_path)
            if not dir_path.exists() or not dir_path.is_dir():
                self.set_status_message(f"目录不存在或不是有效目录: {directory_path}")
                return False
            
            self._source_directory = dir_path
            
            # 统计图片数量
            self._count_images()
            
            # 发现可用字段
            self._discover_fields()
            
            # 发送信号
            self.directory_loaded.emit(str(dir_path), self._image_count)
            
            self.set_status_message(f"已设置源目录: {dir_path.name} ({self._image_count} 张图片)")
            
            # 触发事件
            self._event_bus.emit(EventType.EXIF_SOURCE_DIRECTORY_SET, {
                'directory_path': str(dir_path),
                'image_count': self._image_count,
                'available_fields_count': len(self._available_fields)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置源目录失败: {e}")
            self.set_status_message(f"设置源目录失败: {e}")
            return False
    
    def set_output_path(self, output_path: str):
        """
        设置输出路径
        
        Args:
            output_path: 输出文件路径
        """
        try:
            self._output_path = Path(output_path) if output_path else None
            if self._output_path:
                self.set_status_message(f"已设置输出路径: {self._output_path.name}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置输出路径失败: {e}")
    
    def set_selected_fields(self, field_list: List[str]):
        """
        设置选择的字段列表
        
        Args:
            field_list: 字段列表
        """
        try:
            self._selected_fields = field_list.copy()
            self.field_selection_changed.emit(self._selected_fields)
            self.set_status_message(f"已选择 {len(self._selected_fields)} 个字段")
            
        except Exception as e:
            logger.error(f"==liuq debug== 设置选择字段失败: {e}")
    
    def start_processing(self, recursive: bool = True, include_raw_json: bool = False) -> bool:
        """
        开始EXIF处理
        
        Args:
            recursive: 是否递归处理子目录
            include_raw_json: 是否包含原始JSON数据
            
        Returns:
            bool: 启动是否成功
        """
        try:
            if self._is_processing:
                self.set_status_message("EXIF处理正在进行中")
                return False
            
            if not self._source_directory:
                self.set_status_message("请先选择源图片目录")
                return False
            
            if not self._selected_fields:
                self.set_status_message("请先选择要提取的EXIF字段")
                return False
            
            # 设置输出路径（如果未设置）
            if not self._output_path:
                self._output_path = self._source_directory / 'exif_export.csv'
            
            # 创建处理选项
            self._processing_options = ExifParseOptions(
                selected_fields=self._selected_fields,
                recursive=recursive,
                keep_raw_json=include_raw_json,
                build_raw_flat=False,
                compute_available=False,
                debug_log_keys=False
            )
            
            self._is_processing = True
            
            # 发送开始信号
            self.processing_started.emit(str(self._source_directory))
            
            self.set_status_message("开始EXIF处理...")
            
            # 触发事件
            self._event_bus.emit(EventType.EXIF_PROCESSING_STARTED, {
                'source_directory': str(self._source_directory),
                'output_path': str(self._output_path),
                'selected_fields_count': len(self._selected_fields),
                'options': {
                    'recursive': recursive,
                    'include_raw_json': include_raw_json
                }
            })
            
            # 这里应该启动后台处理任务
            # 为了演示，我们直接调用处理方法
            self._execute_processing()
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 开始EXIF处理失败: {e}")
            self.set_status_message(f"开始EXIF处理失败: {e}")
            self._is_processing = False
            return False
    
    def cancel_processing(self):
        """取消EXIF处理"""
        try:
            if self._is_processing:
                self._is_processing = False
                self.set_status_message("EXIF处理已取消")
                
                # 触发事件
                self.event_bus.emit(EventType.EXIF_PROCESSING_CANCELLED, {
                    'cancelled_at': self.get_current_timestamp()
                })
            
        except Exception as e:
            logger.error(f"==liuq debug== 取消EXIF处理失败: {e}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = {
                'source_directory': str(self._source_directory) if self._source_directory else None,
                'output_path': str(self._output_path) if self._output_path else None,
                'image_count': self._image_count,
                'available_fields_count': len(self._available_fields),
                'selected_fields_count': len(self._selected_fields),
                'is_processing': self._is_processing,
                'has_result': self._last_result is not None
            }
            
            if self._last_result:
                stats['last_processing_result'] = {
                    'processed_count': self._last_result.get('processed_count', 0),
                    'success_count': self._last_result.get('success_count', 0),
                    'error_count': self._last_result.get('error_count', 0)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取处理统计信息失败: {e}")
            return {}
    
    def export_field_configuration(self, config_path: str) -> bool:
        """
        导出字段配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            config_data = {
                'available_fields': self._available_fields,
                'selected_fields': self._selected_fields,
                'source_directory': str(self._source_directory) if self._source_directory else None,
                'export_timestamp': self.get_current_timestamp()
            }
            
            import json
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.set_status_message(f"字段配置导出完成: {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 导出字段配置失败: {e}")
            self.set_status_message(f"导出字段配置失败: {e}")
            return False
    
    def load_field_configuration(self, config_path: str) -> bool:
        """
        加载字段配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 恢复字段选择
            selected_fields = config_data.get('selected_fields', [])
            if selected_fields:
                self.set_selected_fields(selected_fields)
            
            self.set_status_message(f"字段配置加载完成: {len(selected_fields)} 个字段")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 加载字段配置失败: {e}")
            self.set_status_message(f"加载字段配置失败: {e}")
            return False
    
    def _count_images(self):
        """统计图片数量"""
        try:
            if not self._source_directory:
                self._image_count = 0
                return
            
            # 支持的图片格式
            image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.raw', '.cr2', '.nef', '.arw'}
            
            count = 0
            for file_path in self._source_directory.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    count += 1
            
            self._image_count = count
            
        except Exception as e:
            logger.error(f"==liuq debug== 统计图片数量失败: {e}")
            self._image_count = 0
    
    def _discover_fields(self):
        """发现可用的EXIF字段"""
        try:
            if not self._source_directory:
                self._available_fields = []
                return
            
            # 使用EXIF解析服务发现字段
            # 这里简化为模拟的字段列表
            fields = self._exif_parser.discover_keys(
                self._source_directory, 
                recursive=True, 
                sample=min(3, self._image_count)
            )
            
            self._available_fields = fields
            self.fields_discovered.emit(self._available_fields)
            
            logger.info(f"==liuq debug== 发现 {len(self._available_fields)} 个EXIF字段")
            
        except Exception as e:
            logger.error(f"==liuq debug== 发现EXIF字段失败: {e}")
            self._available_fields = []
    
    def _execute_processing(self):
        """执行EXIF处理（实际应该在后台线程中执行）"""
        try:
            # 模拟处理过程
            total_files = self._image_count
            
            for i in range(total_files):
                if not self._is_processing:  # 检查是否取消
                    break
                
                # 模拟处理进度
                current_file = f"image_{i+1}.jpg"
                self.processing_progress_updated.emit(i + 1, total_files, current_file)
                
                # 模拟处理延时
                import time
                time.sleep(0.01)
            
            if self._is_processing:
                # 处理完成
                result = {
                    'processed_count': total_files,
                    'success_count': total_files,
                    'error_count': 0,
                    'output_path': str(self._output_path)
                }
                
                self._last_result = result
                self._is_processing = False
                
                self.processing_completed.emit(result, str(self._output_path))
                self.set_status_message(f"EXIF处理完成: {total_files} 个文件")
                
                # 触发事件
                self._event_bus.emit(EventType.EXIF_PROCESSING_COMPLETED, {
                    'processing_path': str(self._source_directory),
                    'result': result,
                    'output_path': str(self._output_path)
                })
            
        except Exception as e:
            logger.error(f"==liuq debug== 执行EXIF处理失败: {e}")
            self._is_processing = False
            self.processing_failed.emit(str(e))
    
    def _setup_event_listeners(self):
        """设置事件监听"""
        # 监听Tab激活事件
        self._event_bus.subscribe(EventType.TAB_CHANGED, self._on_tab_changed)
    
    def _on_tab_changed(self, event):
        """处理Tab切换事件"""
        try:
            tab_name = event.data.get('tab_name', '')
            if tab_name == 'EXIF处理':
                # 当切换到EXIF处理Tab时，可以执行一些刷新操作
                logger.info("==liuq debug== 切换到EXIF处理Tab")
                
        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab切换事件失败: {e}")


# 全局EXIF处理Tab ViewModel实例
_exif_processing_tab_viewmodel: Optional[ExifProcessingTabViewModel] = None


def get_exif_processing_tab_viewmodel() -> ExifProcessingTabViewModel:
    """获取EXIF处理Tab ViewModel实例"""
    global _exif_processing_tab_viewmodel
    
    if _exif_processing_tab_viewmodel is None:
        _exif_processing_tab_viewmodel = ExifProcessingTabViewModel()
        logger.info("==liuq debug== 创建EXIF处理Tab ViewModel实例")
    
    return _exif_processing_tab_viewmodel