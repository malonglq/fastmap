#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
==liuq debug== 阈值配置管理器

提供阈值配置的保存、读取、验证和默认值管理功能
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class ThresholdConfig:
    """阈值配置数据类"""

    # CCT阈值配置（绝对值，单位：K）
    cct_small_max: float = 100.0      # 小变化: <100K
    cct_medium_min: float = 100.0     # 中变化: 100K-500K
    cct_medium_max: float = 500.0
    cct_large_min: float = 500.0      # 大变化: >500K

    # 百分比阈值配置（相对值，单位：%）
    percentage_small_max: float = 1.0      # 小变化: <1%
    percentage_medium_min: float = 1.0     # 中变化: 1%-10%
    percentage_medium_max: float = 10.0
    percentage_large_min: float = 10.0     # 大变化: >10%
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "thresholds": {
                "cct": {
                    "small_max": self.cct_small_max,
                    "medium_min": self.cct_medium_min,
                    "medium_max": self.cct_medium_max,
                    "large_min": self.cct_large_min
                },
                "percentage": {
                    "small_max": self.percentage_small_max,
                    "medium_min": self.percentage_medium_min,
                    "medium_max": self.percentage_medium_max,
                    "large_min": self.percentage_large_min
                }
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThresholdConfig':
        """从字典创建配置对象"""
        try:
            thresholds = data.get("thresholds", {})
            cct = thresholds.get("cct", {})
            percentage = thresholds.get("percentage", {})
            
            return cls(
                cct_small_max=float(cct.get("small_max", 100.0)),
                cct_medium_min=float(cct.get("medium_min", 100.0)),
                cct_medium_max=float(cct.get("medium_max", 500.0)),
                cct_large_min=float(cct.get("large_min", 500.0)),
                percentage_small_max=float(percentage.get("small_max", 1.0)),
                percentage_medium_min=float(percentage.get("medium_min", 1.0)),
                percentage_medium_max=float(percentage.get("medium_max", 10.0)),
                percentage_large_min=float(percentage.get("large_min", 10.0))
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"==liuq debug== 配置数据解析失败，使用默认值: {e}")
            return cls()
    
    def validate(self) -> List[str]:
        """验证配置的合理性"""
        errors = []

        # 验证CCT阈值
        if self.cct_small_max <= 0:
            errors.append("CCT小变化阈值必须大于0")
        if self.cct_medium_min <= 0:
            errors.append("CCT中变化最小阈值必须大于0")
        if self.cct_medium_max < self.cct_medium_min:
            errors.append("CCT中变化最大阈值必须大于等于最小阈值")
        if self.cct_large_min < self.cct_medium_max:
            errors.append("CCT大变化阈值必须大于等于中变化最大阈值")

        # 验证百分比阈值
        if self.percentage_small_max <= 0:
            errors.append("百分比小变化阈值必须大于0")
        if self.percentage_medium_min <= 0:
            errors.append("百分比中变化最小阈值必须大于0")
        if self.percentage_medium_max < self.percentage_medium_min:
            errors.append("百分比中变化最大阈值必须大于等于最小阈值")
        if self.percentage_large_min < self.percentage_medium_max:
            errors.append("百分比大变化阈值必须大于等于中变化最大阈值")

        return errors


class ConfigManager:
    """配置管理器（单例模式）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config_file = Path("config/thresholds.json")
        self.config = ThresholdConfig()
        self.observers: List[Callable[[ThresholdConfig], None]] = []
        
        # 确保配置目录存在
        self.config_file.parent.mkdir(exist_ok=True)
        
        # 加载配置
        self.load_config()
        
        logger.info("==liuq debug== 配置管理器初始化完成")
    
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.config = ThresholdConfig.from_dict(data)
                
                # 验证配置
                errors = self.config.validate()
                if errors:
                    logger.warning(f"==liuq debug== 配置验证失败: {errors}")
                    self.config = ThresholdConfig()  # 使用默认配置
                    self.save_config()  # 保存默认配置
                    return False
                
                logger.info("==liuq debug== 配置文件加载成功")
                return True
            else:
                # 配置文件不存在，创建默认配置
                logger.info("==liuq debug== 配置文件不存在，创建默认配置")
                self.save_config()
                return True
                
        except Exception as e:
            logger.error(f"==liuq debug== 配置文件加载失败: {e}")
            self.config = ThresholdConfig()  # 使用默认配置
            self.save_config()  # 保存默认配置
            return False
    
    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info("==liuq debug== 配置文件保存成功")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 配置文件保存失败: {e}")
            return False
    
    def update_config(self, new_config: ThresholdConfig) -> bool:
        """更新配置"""
        try:
            # 验证新配置
            errors = new_config.validate()
            if errors:
                logger.error(f"==liuq debug== 配置验证失败: {errors}")
                return False
            
            # 更新配置
            self.config = new_config
            
            # 保存到文件
            if not self.save_config():
                return False
            
            # 通知观察者
            self.notify_observers()
            
            logger.info("==liuq debug== 配置更新成功")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 配置更新失败: {e}")
            return False
    
    def get_config(self) -> ThresholdConfig:
        """获取当前配置"""
        return self.config
    
    def register_observer(self, callback: Callable[[ThresholdConfig], None]):
        """注册观察者"""
        if callback not in self.observers:
            self.observers.append(callback)

    
    def unregister_observer(self, callback: Callable[[ThresholdConfig], None]):
        """取消注册观察者"""
        if callback in self.observers:
            self.observers.remove(callback)

    
    def notify_observers(self):
        """通知所有观察者"""
        for callback in self.observers:
            try:
                callback(self.config)
            except Exception as e:
                logger.error(f"==liuq debug== 通知观察者失败: {callback.__name__}, {e}")
    
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        try:
            default_config = ThresholdConfig()
            return self.update_config(default_config)
        except Exception as e:
            logger.error(f"==liuq debug== 重置配置失败: {e}")
            return False
    
    def get_cct_thresholds(self) -> Dict[str, float]:
        """获取CCT阈值"""
        return {
            "small_max": self.config.cct_small_max,
            "medium_min": self.config.cct_medium_min,
            "medium_max": self.config.cct_medium_max,
            "large_min": self.config.cct_large_min
        }
    
    def get_percentage_thresholds(self) -> Dict[str, float]:
        """获取百分比阈值"""
        return {
            "small_max": self.config.percentage_small_max,
            "medium_min": self.config.percentage_medium_min,
            "medium_max": self.config.percentage_medium_max,
            "large_min": self.config.percentage_large_min
        }


# 全局配置管理器实例
config_manager = ConfigManager()
