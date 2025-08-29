#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析报告Tab ViewModel
==liuq debug== FastMapV2 分析报告Tab ViewModel

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: 分析报告Tab的MVVM架构ViewModel，管理报告生成和管理相关的业务逻辑
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from PyQt5.QtCore import pyqtSignal

from core.infrastructure.base_view_model import BaseViewModel
from core.infrastructure.event_bus import EventType
from core.services.reporting.html_template_service import HTMLTemplateService
from core.services.reporting.html_style_service import HTMLStyleService
from core.services.reporting.html_content_service import HTMLContentService

logger = logging.getLogger(__name__)


class AnalysisReportTabViewModel(BaseViewModel):
    """
    分析报告Tab ViewModel
    
    管理分析报告Tab的状态和业务逻辑：
    - 报告类型选择和配置
    - 报告生成进度管理
    - 报告历史记录管理
    - 多种报告格式支持
    """
    
    # 自定义信号
    report_generation_started = pyqtSignal(str, dict)  # 报告类型, 配置参数
    report_generation_progress = pyqtSignal(int, str)  # 进度百分比, 当前步骤
    report_generation_completed = pyqtSignal(str, str, dict)  # 报告类型, 文件路径, 统计信息
    report_generation_failed = pyqtSignal(str, str)  # 报告类型, 错误信息
    report_history_updated = pyqtSignal(list)  # 历史记录列表
    report_type_selected = pyqtSignal(str, dict)  # 报告类型, 可用配置
    
    def __init__(self):
        """初始化分析报告Tab ViewModel"""
        super().__init__()
        
        # 数据状态
        self._available_report_types = ['EXIF对比分析', 'Map多维度分析', '综合分析报告']
        self._current_report_type: Optional[str] = None
        self._report_config: Dict[str, Any] = {}
        self._report_history: List[Dict[str, Any]] = []
        self._is_generating: bool = False
        self._generation_progress: int = 0
        
        # 获取服务
        self._html_template_service = self._di_container.resolve(HTMLTemplateService)
        self._html_style_service = self._di_container.resolve(HTMLStyleService)
        self._html_content_service = self._di_container.resolve(HTMLContentService)
        
        # 设置事件监听
        self._setup_event_listeners()
        
        # 初始化报告历史
        self._load_report_history()
        
        logger.info("==liuq debug== 分析报告Tab ViewModel初始化完成")
    
    @property
    def available_report_types(self) -> List[str]:
        """可用的报告类型"""
        return self._available_report_types
    
    @property
    def current_report_type(self) -> Optional[str]:
        """当前选择的报告类型"""
        return self._current_report_type
    
    @property
    def report_config(self) -> Dict[str, Any]:
        """报告配置"""
        return self._report_config
    
    @property
    def report_history(self) -> List[Dict[str, Any]]:
        """报告历史记录"""
        return self._report_history
    
    @property
    def is_generating(self) -> bool:
        """是否正在生成报告"""
        return self._is_generating
    
    @property
    def generation_progress(self) -> int:
        """生成进度（0-100）"""
        return self._generation_progress
    
    def select_report_type(self, report_type: str) -> bool:
        """
        选择报告类型
        
        Args:
            report_type: 报告类型名称
            
        Returns:
            bool: 选择是否成功
        """
        try:
            if report_type not in self._available_report_types:
                self.set_status_message(f"不支持的报告类型: {report_type}")
                return False
            
            self._current_report_type = report_type
            
            # 获取该报告类型的可用配置
            available_config = self._get_report_type_config(report_type)
            
            # 发送信号
            self.report_type_selected.emit(report_type, available_config)
            
            self.set_status_message(f"已选择报告类型: {report_type}")
            
            # 触发事件
            self._event_bus.emit(EventType.REPORT_TYPE_SELECTED, {
                'report_type': report_type,
                'available_config': available_config
            })
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 选择报告类型失败: {e}")
            self.set_status_message(f"选择报告类型失败: {e}")
            return False
    
    def configure_report(self, config: Dict[str, Any]):
        """
        配置报告参数
        
        Args:
            config: 配置参数字典
        """
        try:
            self._report_config = config.copy()
            self.set_status_message("报告配置已更新")
            
        except Exception as e:
            logger.error(f"==liuq debug== 配置报告参数失败: {e}")
    
    def generate_report(self, output_path: Optional[str] = None) -> bool:
        """
        生成报告
        
        Args:
            output_path: 输出路径，为空则使用默认路径
            
        Returns:
            bool: 启动是否成功
        """
        try:
            if self._is_generating:
                self.set_status_message("报告生成正在进行中")
                return False
            
            if not self._current_report_type:
                self.set_status_message("请先选择报告类型")
                return False
            
            # 设置输出路径
            if not output_path:
                output_path = str(Path.cwd() / f"{self._current_report_type}_{self.get_current_timestamp()}.html")
            
            self._is_generating = True
            self._generation_progress = 0
            
            # 发送开始信号
            self.report_generation_started.emit(self._current_report_type, self._report_config.copy())
            
            self.set_status_message(f"开始生成{self._current_report_type}报告...")
            
            # 触发事件
            self._event_bus.emit(EventType.REPORT_GENERATION_REQUESTED, {
                'report_type': self._current_report_type,
                'output_path': output_path,
                'config': self._report_config.copy()
            })
            
            # 执行报告生成
            self._execute_report_generation(output_path)
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成报告失败: {e}")
            self.set_status_message(f"生成报告失败: {e}")
            self._is_generating = False
            return False
    
    def cancel_generation(self):
        """取消报告生成"""
        try:
            if self._is_generating:
                self._is_generating = False
                self._generation_progress = 0
                self.set_status_message("报告生成已取消")
                
                # 触发事件
                self._event_bus.emit(EventType.REPORT_GENERATION_CANCELLED, {
                    'report_type': self._current_report_type,
                    'cancelled_at': self.get_current_timestamp()
                })
            
        except Exception as e:
            logger.error(f"==liuq debug== 取消报告生成失败: {e}")
    
    def open_report(self, report_path: str) -> bool:
        """
        打开报告文件
        
        Args:
            report_path: 报告文件路径
            
        Returns:
            bool: 打开是否成功
        """
        try:
            import webbrowser
            import os
            
            if not os.path.exists(report_path):
                self.set_status_message(f"报告文件不存在: {report_path}")
                return False
            
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
            self.set_status_message(f"已打开报告: {Path(report_path).name}")
            
            # 触发事件
            self.event_bus.emit(EventType.REPORT_OPENED, {
                'report_path': report_path,
                'opened_at': self.get_current_timestamp()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 打开报告失败: {e}")
            self.set_status_message(f"打开报告失败: {e}")
            return False
    
    def delete_report_from_history(self, report_id: str) -> bool:
        """
        从历史记录中删除报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 查找并删除报告记录
            original_count = len(self._report_history)
            self._report_history = [r for r in self._report_history if r.get('id') != report_id]
            
            if len(self._report_history) < original_count:
                # 保存历史记录
                self._save_report_history()
                
                # 发送信号
                self.report_history_updated.emit(self._report_history.copy())
                
                self.set_status_message("报告记录已删除")
                return True
            else:
                self.set_status_message("未找到指定的报告记录")
                return False
            
        except Exception as e:
            logger.error(f"==liuq debug== 删除报告记录失败: {e}")
            self.set_status_message(f"删除报告记录失败: {e}")
            return False
    
    def clear_report_history(self) -> bool:
        """
        清空报告历史记录
        
        Returns:
            bool: 清空是否成功
        """
        try:
            self._report_history.clear()
            self._save_report_history()
            
            # 发送信号
            self.report_history_updated.emit(self._report_history.copy())
            
            self.set_status_message("报告历史记录已清空")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 清空报告历史记录失败: {e}")
            self.set_status_message(f"清空报告历史记录失败: {e}")
            return False
    
    def get_report_statistics(self) -> Dict[str, Any]:
        """
        获取报告统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = {
                'total_reports': len(self._report_history),
                'report_types_count': {},
                'recent_reports': [],
                'is_generating': self._is_generating,
                'generation_progress': self._generation_progress
            }
            
            # 统计各种报告类型的数量
            for report in self._report_history:
                report_type = report.get('type', 'unknown')
                stats['report_types_count'][report_type] = stats['report_types_count'].get(report_type, 0) + 1
            
            # 获取最近的报告（最多5个）
            sorted_reports = sorted(self._report_history, key=lambda x: x.get('created_at', ''), reverse=True)
            stats['recent_reports'] = sorted_reports[:5]
            
            return stats
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取报告统计信息失败: {e}")
            return {}
    
    def _get_report_type_config(self, report_type: str) -> Dict[str, Any]:
        """获取报告类型的配置选项"""
        config_map = {
            'EXIF对比分析': {
                'supports_file_selection': True,
                'supports_field_configuration': True,
                'supports_parameter_settings': True,
                'output_formats': ['HTML', 'PDF'],
                'required_data': ['test_file', 'reference_file']
            },
            'Map多维度分析': {
                'supports_scene_classification': True,
                'supports_statistical_analysis': True,
                'supports_visualization': True,
                'output_formats': ['HTML', 'PDF', 'JSON'],
                'required_data': ['map_analysis_result']
            },
            '综合分析报告': {
                'supports_multiple_data_sources': True,
                'supports_custom_templates': True,
                'supports_interactive_charts': True,
                'output_formats': ['HTML', 'PDF'],
                'required_data': ['map_data', 'exif_data']
            }
        }
        
        return config_map.get(report_type, {})
    
    def _execute_report_generation(self, output_path: str):
        """执行报告生成（实际应该在后台线程中执行）"""
        try:
            # 模拟报告生成过程
            steps = [
                (10, "准备数据"),
                (30, "生成HTML模板"),
                (50, "应用样式"),
                (70, "生成内容"),
                (90, "保存文件"),
                (100, "生成完成")
            ]
            
            for progress, step in steps:
                if not self._is_generating:  # 检查是否取消
                    return
                
                self._generation_progress = progress
                self.report_generation_progress.emit(progress, step)
                
                # 模拟处理延时
                import time
                time.sleep(0.2)
            
            if self._is_generating:
                # 生成完成
                report_info = {
                    'id': f"report_{self.get_current_timestamp()}",
                    'type': self._current_report_type,
                    'path': output_path,
                    'created_at': self.get_current_timestamp(),
                    'config': self._report_config.copy(),
                    'file_size': 1024 * 150  # 模拟文件大小
                }
                
                # 添加到历史记录
                self._report_history.append(report_info)
                self._save_report_history()
                
                # 更新状态
                self._is_generating = False
                self._generation_progress = 100
                
                # 发送信号
                statistics = {'file_size': report_info['file_size'], 'generation_time': '0.8s'}
                self.report_generation_completed.emit(self._current_report_type, output_path, statistics)
                self.report_history_updated.emit(self._report_history.copy())
                
                self.set_status_message(f"{self._current_report_type}报告生成完成")
                
                # 触发事件
                self._event_bus.emit(EventType.REPORT_GENERATION_COMPLETED, {
                    'report_type': self._current_report_type,
                    'file_path': output_path,
                    'report_info': report_info
                })
            
        except Exception as e:
            logger.error(f"==liuq debug== 执行报告生成失败: {e}")
            self._is_generating = False
            self._generation_progress = 0
            self.report_generation_failed.emit(self._current_report_type, str(e))
    
    def _load_report_history(self):
        """加载报告历史记录"""
        try:
            # 这里应该从配置文件或数据库中加载
            # 暂时使用模拟数据
            self._report_history = []
            
        except Exception as e:
            logger.error(f"==liuq debug== 加载报告历史记录失败: {e}")
            self._report_history = []
    
    def _save_report_history(self):
        """保存报告历史记录"""
        try:
            # 这里应该保存到配置文件或数据库
            # 暂时跳过实际保存
            pass
            
        except Exception as e:
            logger.error(f"==liuq debug== 保存报告历史记录失败: {e}")
    
    def _setup_event_listeners(self):
        """设置事件监听"""
        # 监听Map分析完成事件
        self._event_bus.subscribe(EventType.MAP_ANALYSIS_COMPLETED, self._on_map_analysis_completed)
        
        # 监听EXIF处理完成事件
        self._event_bus.subscribe(EventType.EXIF_PROCESSING_COMPLETED, self._on_exif_processing_completed)
        
        # 监听Tab激活事件
        self._event_bus.subscribe(EventType.TAB_CHANGED, self._on_tab_changed)
    
    def _on_map_analysis_completed(self, event):
        """处理Map分析完成事件"""
        try:
            # 当Map分析完成时，可以自动启用相关报告类型
            analysis_result = event.data.get('analysis_result', {})
            if analysis_result:
                self.emit_status("Map分析数据已就绪，可生成多维度分析报告")
                
        except Exception as e:
            logger.error(f"==liuq debug== 处理Map分析完成事件失败: {e}")
    
    def _on_exif_processing_completed(self, event):
        """处理EXIF处理完成事件"""
        try:
            # 当EXIF处理完成时，可以自动启用相关报告类型
            result = event.data.get('result', {})
            if result:
                self.emit_status("EXIF处理数据已就绪，可生成对比分析报告")
                
        except Exception as e:
            logger.error(f"==liuq debug== 处理EXIF处理完成事件失败: {e}")
    
    def _on_tab_changed(self, event):
        """处理Tab切换事件"""
        try:
            tab_name = event.data.get('tab_name', '')
            if tab_name == '分析报告':
                # 当切换到分析报告Tab时，刷新可用数据状态
                logger.info("==liuq debug== 切换到分析报告Tab")
                
        except Exception as e:
            logger.error(f"==liuq debug== 处理Tab切换事件失败: {e}")


# 全局分析报告Tab ViewModel实例
_analysis_report_tab_viewmodel: Optional[AnalysisReportTabViewModel] = None


def get_analysis_report_tab_viewmodel() -> AnalysisReportTabViewModel:
    """获取分析报告Tab ViewModel实例"""
    global _analysis_report_tab_viewmodel
    
    if _analysis_report_tab_viewmodel is None:
        _analysis_report_tab_viewmodel = AnalysisReportTabViewModel()
        logger.info("==liuq debug== 创建分析报告Tab ViewModel实例")
    
    return _analysis_report_tab_viewmodel