"""
EXIF字段显示配置管理器
统一管理EXIF字段的显示顺序、成对字段配置等
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PairedFieldConfig:
    """成对字段配置"""
    pair_field: str
    display_name: str


@dataclass
class TripleFieldConfig:
    """三字段组合配置"""
    second_field: str
    third_field: str
    display_name: str


class ExifDisplayConfigManager:
    """EXIF字段显示配置管理器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            # 默认配置文件路径
            config_path = Path(__file__).parent.parent.parent / "data" / "configs" / "exif_display_config.json"
        
        self.config_path = config_path
        self._config_data = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
                logger.info("==liuq debug== 成功加载EXIF显示配置: %s", self.config_path)
            else:
                logger.warning("==liuq debug== EXIF显示配置文件不存在: %s", self.config_path)
                self._config_data = self._get_default_config()
        except Exception as e:
            logger.error("==liuq debug== 加载EXIF显示配置失败: %s", e)
            self._config_data = self._get_default_config()
    
    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "priority_fields": [],
            "paired_fields": {},
            "triple_fields": {},
            "quick_select_groups": ["meta_data", "ealgo_data", "color_sensor", "stats_weight", "face_info", "face_cc"]
        }
    
    def get_priority_fields(self) -> List[str]:
        """获取优先字段列表"""
        return self._config_data.get("priority_fields", [])
    
    def get_paired_fields(self) -> Dict[str, Tuple[str, str]]:
        """获取成对字段配置，返回格式: {主字段: (配对字段, 显示名称)}"""
        paired_config = self._config_data.get("paired_fields", {})
        result = {}
        for main_field, config in paired_config.items():
            if isinstance(config, dict):
                result[main_field] = (config.get("pair_field", ""), config.get("display_name", main_field))
            else:
                # 兼容旧格式
                result[main_field] = config
        return result
    
    def get_triple_fields(self) -> Dict[str, Tuple[str, str, str]]:
        """获取三字段组合配置，返回格式: {主字段: (第二字段, 第三字段, 显示名称)}"""
        triple_config = self._config_data.get("triple_fields", {})
        result = {}
        for main_field, config in triple_config.items():
            if isinstance(config, dict):
                result[main_field] = (
                    config.get("second_field", "dummy"),
                    config.get("third_field", "dummy"),
                    config.get("display_name", main_field)
                )
        return result
    
    def get_quick_select_groups(self) -> List[str]:
        """获取快速选择分组"""
        return self._config_data.get("quick_select_groups", [])
    
    def add_field_to_priority(self, field_name: str, insert_after: Optional[str] = None):
        """添加字段到优先列表"""
        priority_fields = self.get_priority_fields()
        if field_name not in priority_fields:
            if insert_after and insert_after in priority_fields:
                index = priority_fields.index(insert_after) + 1
                priority_fields.insert(index, field_name)
            else:
                priority_fields.append(field_name)
            self._config_data["priority_fields"] = priority_fields
            self._save_config()
    
    def add_paired_field(self, main_field: str, pair_field: str, display_name: str):
        """添加成对字段配置"""
        if "paired_fields" not in self._config_data:
            self._config_data["paired_fields"] = {}
        
        self._config_data["paired_fields"][main_field] = {
            "pair_field": pair_field,
            "display_name": display_name
        }
        self._save_config()
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, ensure_ascii=False, indent=2)
            logger.info("==liuq debug== 成功保存EXIF显示配置: %s", self.config_path)
        except Exception as e:
            logger.error("==liuq debug== 保存EXIF显示配置失败: %s", e)
    
    def reload_config(self):
        """重新加载配置"""
        self._load_config()


# 全局配置管理器实例
_config_manager = None


def get_exif_display_config() -> ExifDisplayConfigManager:
    """获取全局EXIF显示配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ExifDisplayConfigManager()
    return _config_manager
