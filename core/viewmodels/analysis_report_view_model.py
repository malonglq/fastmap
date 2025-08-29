#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析报告ViewModel
==liuq debug== FastMapV2 分析报告ViewModel

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: 分析报告Tab的ViewModel，处理统一报告生成、历史记录管理等业务逻辑
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from PyQt5.QtCore import pyqtSignal

from core.infrastructure.base_view_model import BaseViewModel
from core.infrastructure.event_bus import Event, EventType
from core.services.reporting import UnifiedReportManager, ExifComparisonReportGenerator
from core.services.reporting import MapMultiDimensionalReportGenerator
from core.interfaces.report_generator import ReportType

logger = logging.getLogger(__name__)


class AnalysisReportViewModel(BaseViewModel):
    """
    分析报告ViewModel
    
    负责处理：
    - 统一报告生成管理
    - 报告历史记录
    - EXIF对比报告生成
    - Map多维度报告生成
    - 报告文件管理
    """
    
    # 额外信号定义
    report_generated = pyqtSignal(str, str)            # 报告生成完成 (type, path)
    report_history_updated = pyqtSignal(list)         # 历史记录更新
    report_opened = pyqtSignal(str)                   # 报告打开
    
    def __init__(self):
        super().__init__()
        
        # 解析依赖的服务
        self._report_manager: UnifiedReportManager = self.resolve_service(UnifiedReportManager)
        self._exif_report_generator: ExifComparisonReportGenerator = self.resolve_service(ExifComparisonReportGenerator)
        self._map_report_generator: MapMultiDimensionalReportGenerator = self.resolve_service(MapMultiDimensionalReportGenerator)
        
        # ViewModel状态
        self._report_history: List[Dict] = []
        self._current_map_data: Optional[Any] = None
        self._current_exif_data: Optional[Any] = None
        
        # 初始化属性
        self._initialize_properties()
        
        # 注册报告生成器
        self._register_report_generators()
        
        logger.debug("==liuq debug== AnalysisReportViewModel 初始化完成")
    
    def _initialize_properties(self):
        """初始化属性"""
        self.set_property("report_history", [], False)
        self.set_property("can_generate_exif_report", False, False)
        self.set_property("can_generate_map_report", False, False)
        self.set_property("available_report_types", [], False)
        self.set_property("selected_report_path", "", False)
    
    def _setup_event_subscriptions(self):
        """设置事件订阅"""
        # 订阅Map相关事件
        self.subscribe_event(EventType.MAP_LOADED, self._on_map_loaded)
        self.subscribe_event(EventType.MAP_ANALYZED, self._on_map_analyzed)
        
        # 订阅EXIF相关事件
        self.subscribe_event(EventType.EXIF_EXPORT_COMPLETED, self._on_exif_export_completed)
        self.subscribe_event(EventType.EXIF_PROCESSING_COMPLETED, self._on_exif_processing_completed)
        
        # 订阅报告生成事件
        self.subscribe_event(EventType.REPORT_GENERATION_COMPLETED, self._on_report_generation_completed)
        
        # 订阅Tab切换事件
        self.subscribe_event(EventType.TAB_SWITCHED, self._on_tab_switched)
        
        # 订阅应用程序事件
        self.subscribe_event(EventType.APPLICATION_SHUTDOWN, self._on_application_shutdown)
    
    def _register_report_generators(self):
        """注册报告生成器"""
        try:
            # 注册EXIF对比报告生成器
            if ReportType.EXIF_COMPARISON not in self._report_manager.get_available_report_types():
                self._report_manager.register_generator(self._exif_report_generator)
            
            # 注册Map多维度报告生成器
            if ReportType.MAP_MULTI_DIMENSIONAL not in self._report_manager.get_available_report_types():
                self._report_manager.register_generator(self._map_report_generator)
            
            # 更新可用报告类型
            available_types = [rt.value for rt in self._report_manager.get_available_report_types()]
            self.set_property("available_report_types", available_types)
            
            logger.info("==liuq debug== 报告生成器注册完成")
            
        except Exception as e:
            self.handle_error(e, "注册报告生成器失败")
    
    # 属性访问器
    @property
    def report_history(self) -> List[Dict]:
        """报告历史记录"""
        return self.get_property("report_history", [])
    
    @property
    def can_generate_exif_report(self) -> bool:
        """是否可以生成EXIF报告"""
        return self.get_property("can_generate_exif_report", False)
    
    @property
    def can_generate_map_report(self) -> bool:
        """是否可以生成Map报告"""
        return self.get_property("can_generate_map_report", False)
    
    @property
    def available_report_types(self) -> List[str]:
        """可用报告类型"""
        return self.get_property("available_report_types", [])
    
    # 业务方法
    def refresh_report_history(self):
        """刷新报告历史记录"""
        try:
            history = self._report_manager.get_history()
            history_data = []
            
            for item in history:
                history_data.append({
                    "report_name": item.report_name,
                    "report_type": item.report_type.value,
                    "file_path": item.file_path,
                    "generation_time": item.generation_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "success": item.success
                })
            
            self._report_history = history_data
            self.set_property("report_history", history_data)
            
            # 发布事件
            self.report_history_updated.emit(history_data)
            
            logger.debug(f"==liuq debug== 报告历史记录刷新: {len(history_data)} 条")
            
        except Exception as e:
            self.handle_error(e, "刷新报告历史记录失败")
    
    def generate_exif_comparison_report(self, config: Dict[str, Any]) -> Optional[str]:
        """
        生成EXIF对比报告
        
        Args:
            config: 报告配置
            
        Returns:
            str: 报告文件路径，失败返回None
        """
        try:
            if not self.can_generate_exif_report:
                self.handle_error(ValueError("无法生成EXIF对比报告：数据不足"))
                return None
            
            self.set_busy(True, "正在生成EXIF对比报告...")
            
            # 发布报告生成开始事件
            self.emit_event(EventType.REPORT_GENERATION_STARTED, {
                "report_type": "exif_comparison",
                "source": "AnalysisReportViewModel"
            })
            
            # 生成报告
            report_path = self._report_manager.generate_report(
                ReportType.EXIF_COMPARISON,
                config
            )
            
            if report_path:
                # 刷新历史记录
                self.refresh_report_history()
                
                # 发布成功事件
                self.emit_event(EventType.REPORT_GENERATION_COMPLETED, {
                    "report_type": "exif_comparison",
                    "report_path": report_path,
                    "success": True
                })
                
                self.report_generated.emit("exif_comparison", report_path)
                self.emit_status(f"EXIF对比报告生成成功: {Path(report_path).name}")
                
                logger.info(f"==liuq debug== EXIF对比报告生成成功: {report_path}")
                return report_path
            else:
                self.handle_error(ValueError("EXIF对比报告生成失败"))
                return None
            
        except Exception as e:
            self.handle_error(e, "生成EXIF对比报告失败")
            return None
        finally:
            self.set_busy(False)
    
    def generate_map_multi_dimensional_report(self, config: Dict[str, Any]) -> Optional[str]:
        """
        生成Map多维度报告
        
        Args:
            config: 报告配置
            
        Returns:
            str: 报告文件路径，失败返回None
        """
        try:
            if not self.can_generate_map_report:
                self.handle_error(ValueError("无法生成Map多维度报告：Map数据不足"))
                return None
            
            self.set_busy(True, "正在生成Map多维度报告...")
            
            # 发布报告生成开始事件
            self.emit_event(EventType.REPORT_GENERATION_STARTED, {
                "report_type": "map_multi_dimensional",
                "source": "AnalysisReportViewModel"
            })
            
            # 生成报告
            report_path = self._report_manager.generate_report(
                ReportType.MAP_MULTI_DIMENSIONAL,
                config
            )
            
            if report_path:
                # 刷新历史记录
                self.refresh_report_history()
                
                # 发布成功事件
                self.emit_event(EventType.REPORT_GENERATION_COMPLETED, {
                    "report_type": "map_multi_dimensional",
                    "report_path": report_path,
                    "success": True
                })
                
                self.report_generated.emit("map_multi_dimensional", report_path)
                self.emit_status(f"Map多维度报告生成成功: {Path(report_path).name}")
                
                logger.info(f"==liuq debug== Map多维度报告生成成功: {report_path}")
                return report_path
            else:
                self.handle_error(ValueError("Map多维度报告生成失败"))
                return None
            
        except Exception as e:
            self.handle_error(e, "生成Map多维度报告失败")
            return None
        finally:
            self.set_busy(False)
    
    def open_report_file(self, file_path: str) -> bool:
        """
        打开报告文件
        
        Args:
            file_path: 报告文件路径
            
        Returns:
            bool: 是否打开成功
        """
        try:
            if not file_path or not Path(file_path).exists():
                self.handle_error(FileNotFoundError(f"报告文件不存在: {file_path}"))
                return False
            
            # 使用浏览器工具打开
            from utils.browser_utils import open_html_report
            open_html_report(file_path)
            
            # 发布事件
            self.emit_event(EventType.REPORT_OPENED, {
                "file_path": file_path
            })
            
            self.report_opened.emit(file_path)
            self.emit_status(f"已打开报告: {Path(file_path).name}")
            
            logger.info(f"==liuq debug== 打开报告文件: {file_path}")
            return True
            
        except Exception as e:
            self.handle_error(e, f"打开报告文件失败: {file_path}")
            return False
    
    def delete_report_file(self, file_path: str) -> bool:
        """
        删除报告文件
        
        Args:
            file_path: 报告文件路径
            
        Returns:
            bool: 是否删除成功
        """
        try:
            report_path = Path(file_path)
            if report_path.exists():
                report_path.unlink()
                
                # 从历史记录中移除
                self._report_manager.remove_from_history(file_path)
                self.refresh_report_history()
                
                self.emit_status(f"报告文件已删除: {report_path.name}")
                logger.info(f"==liuq debug== 删除报告文件: {file_path}")
                return True
            else:
                self.emit_status(f"报告文件不存在: {file_path}")
                return False
            
        except Exception as e:
            self.handle_error(e, f"删除报告文件失败: {file_path}")
            return False
    
    def clear_report_history(self) -> bool:
        """
        清空报告历史记录
        
        Returns:
            bool: 是否清空成功
        """
        try:
            self._report_manager.clear_history()
            self.refresh_report_history()
            
            self.emit_status("报告历史记录已清空")
            logger.info("==liuq debug== 报告历史记录已清空")
            return True
            
        except Exception as e:
            self.handle_error(e, "清空报告历史记录失败")
            return False
    
    # 事件处理器
    def _on_map_loaded(self, event: Event):
        """Map加载事件处理"""
        try:
            if event.data:
                self._current_map_data = event.data.get("map_data")
                
                # 检查是否可以生成Map报告
                can_generate = self._current_map_data is not None
                self.set_property("can_generate_map_report", can_generate)
                
                logger.debug("==liuq debug== Map数据已加载，更新报告生成状态")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Map加载事件失败: {e}")
    
    def _on_map_analyzed(self, event: Event):
        """Map分析事件处理"""
        try:
            if event.data:
                self._current_map_data = event.data.get("analysis_result")
                
                # 更新可以生成Map报告的状态
                can_generate = self._current_map_data is not None
                self.set_property("can_generate_map_report", can_generate)
                
                logger.debug("==liuq debug== Map分析完成，可以生成Map报告")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Map分析事件失败: {e}")
    
    def _on_exif_export_completed(self, event: Event):
        """EXIF导出完成事件处理"""
        try:
            if event.data:
                # 更新可以生成EXIF报告的状态
                self.set_property("can_generate_exif_report", True)
                
                logger.debug("==liuq debug== EXIF导出完成，可以生成EXIF报告")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理EXIF导出完成事件失败: {e}")
    
    def _on_exif_processing_completed(self, event: Event):
        """EXIF处理完成事件处理"""
        try:
            if event.data and event.data.get("success"):
                self._current_exif_data = event.data.get("result")
                
                # 更新可以生成EXIF报告的状态
                can_generate = self._current_exif_data is not None
                self.set_property("can_generate_exif_report", can_generate)
                
                logger.debug("==liuq debug== EXIF处理完成，可以生成EXIF报告")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理EXIF处理完成事件失败: {e}")
    
    def _on_report_generation_completed(self, event: Event):
        """报告生成完成事件处理"""
        try:
            if event.data:
                report_type = event.data.get("report_type")
                success = event.data.get("success", False)
                
                if success:
                    # 刷新历史记录
                    self.refresh_report_history()
                
                logger.debug(f"==liuq debug== 报告生成完成: {report_type}, 成功: {success}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理报告生成完成事件失败: {e}")
    
    def _on_tab_switched(self, event: Event):
        """Tab切换事件处理"""
        try:
            if event.data and event.data.get("tab_name") == "分析报告":
                # 切换到分析报告Tab时刷新历史记录
                self.refresh_report_history()
                logger.debug("==liuq debug== 切换到分析报告Tab")
            
        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab切换事件失败: {e}")
    
    def _on_application_shutdown(self, event: Event):
        """应用程序关闭事件处理"""
        self.cleanup()
    
    # 生命周期方法
    def initialize(self):
        """初始化"""
        try:
            # 初始化时刷新历史记录
            self.refresh_report_history()
            
            logger.debug("==liuq debug== AnalysisReportViewModel 初始化完成")
            
        except Exception as e:
            self.handle_error(e, "AnalysisReportViewModel 初始化失败")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 清理状态
            self._current_map_data = None
            self._current_exif_data = None
            self._report_history = []
            
            logger.debug("==liuq debug== AnalysisReportViewModel 清理完成")
            
        except Exception as e:
            logger.error(f"==liuq debug== AnalysisReportViewModel 清理失败: {e}")
