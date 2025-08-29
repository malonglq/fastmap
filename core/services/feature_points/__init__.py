#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特征点功能服务模块

该模块包含所有与特征点功能相关的服务：
- 图像分类
- 特征提取 (预留)
- 模式识别 (预留)
"""

# 导入主要服务
from .image_classifier_service import ImageClassifierService

__all__ = [
    'ImageClassifierService'
]