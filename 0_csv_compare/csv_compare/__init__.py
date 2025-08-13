#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV数据对比分析工具
==liuq debug== 项目根包初始化文件

版本: 1.0.0
作者: AI Assistant
描述: 专业的CSV文件数据对比分析工具
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "CSV数据对比分析工具"

# 导出主要模块
import core
import gui
import utils

__all__ = [
    'core',
    'gui', 
    'utils',
    '__version__',
    '__author__',
    '__description__'
]
