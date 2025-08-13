# {{CHENGQI:
# Action: Added; Timestamp: 2025-08-04 16:30:00 +08:00; Reason: 创建场景分类配置模型以支持多维度分析报告功能; Principle_Applied: 配置驱动设计和可扩展性;
# }}

"""
场景分类配置模型

提供可配置的场景分类规则和阈值管理
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SceneClassificationConfig:
    """
    场景分类配置类
    
    管理场景分类的阈值参数，支持GUI配置和持久化存储
    """
    # BV阈值配置
    bv_outdoor_threshold: float = 7.0      # BV室外阈值（默认：7）
    bv_indoor_min: float = 1.0             # BV室内下限（默认：1）
    
    # IR阈值配置  
    ir_outdoor_threshold: float = 0.5      # IR室外阈值（默认：0.5）
    
    # 配置元数据
    config_name: str = "默认配置"
    description: str = "默认的场景分类配置"
    created_time: str = ""
    modified_time: str = ""
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.created_time:
            from datetime import datetime
            self.created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.modified_time = self.created_time
    
    def classify_scene_by_rules(self, bv_min: float, ir_ratio: float, alias_name: str = "") -> str:
        """
        根据配置的规则进行场景分类
        
        Args:
            bv_min: BV最小值
            ir_ratio: IR比值（ir_min）
            alias_name: 别名（可选，用于辅助判断）
            
        Returns:
            场景类型：'outdoor', 'indoor', 'night'
        """
        try:
            # 优先根据别名关键词判断
            if alias_name:
                alias_lower = alias_name.lower()
                if 'outdoor' in alias_lower:
                    return 'outdoor'
                elif 'indoor' in alias_lower:
                    return 'indoor'
                elif 'night' in alias_lower:
                    return 'night'
            
            # 根据配置的阈值进行判断
            # 夜景场景：bv_min < bv_indoor_min
            if bv_min < self.bv_indoor_min:
                return 'night'
            
            # 室外场景：bv_min > bv_outdoor_threshold 或 ir_ratio > ir_outdoor_threshold
            if bv_min > self.bv_outdoor_threshold or ir_ratio > self.ir_outdoor_threshold:
                return 'outdoor'
            
            # 室内场景：bv_indoor_min ≤ bv_min ≤ bv_outdoor_threshold 且 ir_ratio ≤ ir_outdoor_threshold
            if (self.bv_indoor_min <= bv_min <= self.bv_outdoor_threshold and 
                ir_ratio <= self.ir_outdoor_threshold):
                return 'indoor'
            
            # 默认返回室内
            return 'indoor'
            
        except Exception as e:
            logger.error(f"==liuq debug== 场景分类失败: {e}")
            return 'indoor'
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置的有效性
        
        Returns:
            验证结果字典
        """
        errors = []
        warnings = []
        
        # 检查阈值的合理性
        if self.bv_indoor_min >= self.bv_outdoor_threshold:
            errors.append("BV室内下限不能大于等于BV室外阈值")
        
        if self.bv_indoor_min < 0:
            warnings.append("BV室内下限小于0，可能不合理")
        
        if self.bv_outdoor_threshold > 20:
            warnings.append("BV室外阈值大于20，可能过高")
        
        if self.ir_outdoor_threshold < 0 or self.ir_outdoor_threshold > 1000:
            warnings.append("IR室外阈值超出常见范围[0-1000]")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'bv_outdoor_threshold': self.bv_outdoor_threshold,
            'bv_indoor_min': self.bv_indoor_min,
            'ir_outdoor_threshold': self.ir_outdoor_threshold,
            'config_name': self.config_name,
            'description': self.description,
            'created_time': self.created_time,
            'modified_time': self.modified_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneClassificationConfig':
        """从字典创建配置对象"""
        return cls(**data)
    
    def save_to_file(self, file_path: str) -> bool:
        """
        保存配置到文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            # 更新修改时间
            from datetime import datetime
            self.modified_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存到JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"==liuq debug== 场景分类配置已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 保存配置失败: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'SceneClassificationConfig':
        """
        从文件加载配置
        
        Args:
            file_path: 文件路径
            
        Returns:
            配置对象
        """
        try:
            if not Path(file_path).exists():
                logger.warning(f"==liuq debug== 配置文件不存在，使用默认配置: {file_path}")
                return cls()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = cls.from_dict(data)
            logger.info(f"==liuq debug== 场景分类配置已加载: {file_path}")
            return config
            
        except Exception as e:
            logger.error(f"==liuq debug== 加载配置失败，使用默认配置: {e}")
            return cls()


# 默认配置实例
DEFAULT_SCENE_CONFIG = SceneClassificationConfig()


def get_default_config_path() -> str:
    """获取默认配置文件路径"""
    return "data/configs/scene_classification_config.json"
