#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI ViewModels模块

该模块包含所有GUI相关的ViewModel：
- 主窗口ViewModel
- Tab专用ViewModel
- 对话框ViewModel
"""

from .main_window_view_model import MainWindowViewModel, get_main_window_viewmodel
from .map_analysis_tab_view_model import MapAnalysisTabViewModel, get_map_analysis_tab_viewmodel
from .exif_processing_tab_view_model import ExifProcessingTabViewModel, get_exif_processing_tab_viewmodel
from .analysis_report_tab_view_model import AnalysisReportTabViewModel, get_analysis_report_tab_viewmodel
from .copywriting_tab_view_model import CopywritingTabViewModel, get_copywriting_tab_viewmodel
from .feature_point_tab_view_model import FeaturePointTabViewModel, get_feature_point_tab_viewmodel

__all__ = [
    'MainWindowViewModel',
    'get_main_window_viewmodel',
    'MapAnalysisTabViewModel',
    'get_map_analysis_tab_viewmodel',
    'ExifProcessingTabViewModel', 
    'get_exif_processing_tab_viewmodel',
    'AnalysisReportTabViewModel',
    'get_analysis_report_tab_viewmodel',
    'CopywritingTabViewModel',
    'get_copywriting_tab_viewmodel',
    'FeaturePointTabViewModel',
    'get_feature_point_tab_viewmodel'
]