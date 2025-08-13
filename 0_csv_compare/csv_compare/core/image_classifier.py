#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片分类器模块
根据CSV数据分析结果对图片进行变化幅度分类
==liuq debug== 图片分类器核心功能实现
"""

import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path
import statistics

from utils.config_manager import ConfigManager, ThresholdConfig

logger = logging.getLogger(__name__)


class ImageClassifier:
    """图片分类器类"""

    def __init__(self, match_result: Dict[str, Any], selected_fields: List[str]):
        """
        初始化图片分类器

        Args:
            match_result: 数据匹配结果
            selected_fields: 选中的分析字段
        """
        self.match_result = match_result
        self.selected_fields = selected_fields

        # 确定用于分类的主字段（使用第一个选择的字段）
        self.primary_field = selected_fields[0] if selected_fields else 'sensorCCT'

        # 初始化配置管理器
        self.config_manager = ConfigManager()

        # 从配置管理器获取阈值
        self.load_thresholds_from_config()

        # 注册为配置观察者
        self.config_manager.register_observer(self.on_config_updated)

        # 判断主字段类型
        self.is_primary_field_cct = self.is_cct_field(self.primary_field)

        logger.info(f"==liuq debug== 图片分类器初始化完成，字段数: {len(selected_fields)}")
        logger.info(f"==liuq debug== 使用主字段进行分类: {self.primary_field}")
        logger.info(f"==liuq debug== 主字段类型: {'CCT字段' if self.is_primary_field_cct else '非CCT字段'}")

        self.log_current_thresholds()

    def load_thresholds_from_config(self):
        """从配置管理器加载阈值"""
        try:
            config = self.config_manager.get_config()

            # 加载CCT阈值
            self.cct_large_threshold = config.cct_large_min
            self.cct_medium_threshold_min = config.cct_medium_min
            self.cct_medium_threshold_max = config.cct_medium_max
            self.cct_small_threshold = config.cct_small_max

            # 加载百分比阈值
            self.percentage_large_threshold = config.percentage_large_min
            self.percentage_medium_threshold_min = config.percentage_medium_min
            self.percentage_medium_threshold_max = config.percentage_medium_max
            self.percentage_small_threshold = config.percentage_small_max



        except Exception as e:
            logger.error(f"==liuq debug== 从配置加载阈值失败: {e}")
            # 使用默认值
            self.cct_large_threshold = 500.0
            self.cct_medium_threshold_min = 100.0
            self.cct_medium_threshold_max = 500.0
            self.cct_small_threshold = 100.0
            self.percentage_large_threshold = 10.0
            self.percentage_medium_threshold_min = 1.0
            self.percentage_medium_threshold_max = 10.0
            self.percentage_small_threshold = 1.0

    def log_current_thresholds(self):
        """记录当前阈值"""
        if self.is_primary_field_cct:
            logger.info(f"==liuq debug== CCT阈值 - 大变化: >{self.cct_large_threshold}K, "
                       f"中变化: {self.cct_medium_threshold_min}K-{self.cct_medium_threshold_max}K, "
                       f"小变化: <{self.cct_small_threshold}K")
        else:
            logger.info(f"==liuq debug== 百分比阈值 - 大变化: >{self.percentage_large_threshold}%, "
                       f"中变化: {self.percentage_medium_threshold_min}%-{self.percentage_medium_threshold_max}%, "
                       f"小变化: <{self.percentage_small_threshold}%")

    def on_config_updated(self, config: ThresholdConfig):
        """配置更新回调"""
        try:
            logger.info("==liuq debug== 图片分类器收到配置更新通知")
            self.load_thresholds_from_config()
            self.log_current_thresholds()
        except Exception as e:
            logger.error(f"==liuq debug== 处理配置更新失败: {e}")

    def is_cct_field(self, field_name: str) -> bool:
        """
        判断字段是否为CCT（色温）字段

        Args:
            field_name: 字段名

        Returns:
            是否为CCT字段
        """
        try:
            if not field_name:
                return False

            # 转换为小写进行比较
            field_lower = field_name.lower()

            # 检查字段名是否包含CCT相关关键词
            cct_keywords = ['cct', 'color_temperature', 'colortemperature', 'sensor_cct', 'sensorcct']

            for keyword in cct_keywords:
                if keyword in field_lower:
                    return True

            return False

        except Exception as e:
            logger.warning(f"==liuq debug== 判断CCT字段失败: {e}")
            return False
    
    def classify_images(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        对图片进行分类
        
        Returns:
            分类结果字典，包含三个类别的图片列表
        """
        try:
            logger.info("==liuq debug== 开始图片分类")
            
            # 根据字段类型设置分类描述
            if self.is_primary_field_cct:
                classification_result = {
                    'large_changes': [],    # 大变化 (>500K)
                    'medium_changes': [],   # 中变化 (100K-500K)
                    'small_changes': [],    # 小变化 (0K-100K，但不包括0K)
                    'no_changes': []        # 无变化 (=0K)
                }
            else:
                classification_result = {
                    'large_changes': [],    # 大变化 (>10%)
                    'medium_changes': [],   # 中变化 (1%-10%)
                    'small_changes': [],    # 小变化 (0%-1%，但不包括0%)
                    'no_changes': []        # 无变化 (=0%)
                }

            # 获取匹配的数据对
            pairs = self.match_result.get('pairs', [])

            for pair in pairs:
                try:
                    # 计算主字段的变化值（根据字段类型选择计算方式）
                    primary_field_change = self.calculate_primary_field_change(pair)

                    # 创建图片信息对象
                    image_info = {
                        'image_name': pair.get('filename1', ''),
                        'primary_field_change': primary_field_change,
                        'primary_field_name': self.primary_field,
                        'is_cct_field': self.is_primary_field_cct,
                        'field_changes': self.get_field_changes(pair),
                        'pair_data': pair
                    }

                    # 根据字段类型和变化幅度分类
                    if self.is_primary_field_cct:
                        # CCT字段使用绝对值阈值
                        if primary_field_change == 0:
                            classification_result['no_changes'].append(image_info)
                        elif primary_field_change > self.cct_large_threshold:
                            classification_result['large_changes'].append(image_info)
                        elif primary_field_change >= self.cct_medium_threshold_min:
                            classification_result['medium_changes'].append(image_info)
                        else:
                            classification_result['small_changes'].append(image_info)
                    else:
                        # 非CCT字段使用百分比阈值
                        if primary_field_change == 0:
                            classification_result['no_changes'].append(image_info)
                        elif primary_field_change > self.percentage_large_threshold:
                            classification_result['large_changes'].append(image_info)
                        elif primary_field_change >= self.percentage_medium_threshold_min:
                            classification_result['medium_changes'].append(image_info)
                        else:
                            classification_result['small_changes'].append(image_info)
                        
                except Exception as e:
                    logger.warning(f"==liuq debug== 处理图片 {pair.get('filename1', 'unknown')} 时出错: {e}")
                    continue
            
            # 记录分类统计
            total_images = len(pairs)
            large_count = len(classification_result['large_changes'])
            medium_count = len(classification_result['medium_changes'])
            small_count = len(classification_result['small_changes'])
            no_change_count = len(classification_result['no_changes'])

            logger.info(f"==liuq debug== 图片分类完成 - 总数: {total_images}, "
                       f"大变化: {large_count}, 中变化: {medium_count}, 小变化: {small_count}, 无变化: {no_change_count}")
            
            return classification_result
            
        except Exception as e:
            logger.error(f"==liuq debug== 图片分类失败: {e}")
            raise
    
    def calculate_overall_change_percentage(self, pair: Dict[str, Any]) -> float:
        """
        计算图片的整体变化百分比
        
        Args:
            pair: 数据对
            
        Returns:
            整体变化百分比
        """
        try:
            field_changes = []
            
            for field in self.selected_fields:
                # 获取字段的前后值
                before_key = f"{field}_before"
                after_key = f"{field}_after"
                
                if before_key in pair and after_key in pair:
                    before_value = pair[before_key]
                    after_value = pair[after_key]
                    
                    # 计算单个字段的变化百分比
                    change_pct = self.calculate_field_change_percentage(before_value, after_value)
                    if change_pct is not None:
                        field_changes.append(change_pct)
            
            # 如果没有有效的字段变化，返回0
            if not field_changes:
                return 0.0
            
            # 使用所有字段变化的平均值作为整体变化
            overall_change = statistics.mean(field_changes)
            
            return round(overall_change, 2)
            
        except Exception as e:
            logger.warning(f"==liuq debug== 计算整体变化百分比失败: {e}")
            return 0.0

    def calculate_primary_field_change(self, pair: Dict[str, Any]) -> float:
        """
        计算主字段的变化值（根据字段类型选择计算方式）

        Args:
            pair: 数据对

        Returns:
            主字段的变化值（CCT字段返回绝对值变化，其他字段返回百分比变化）
        """
        try:
            # 从pair中获取row1和row2数据
            row1 = pair.get('row1')
            row2 = pair.get('row2')

            if row1 is None or row2 is None:
                logger.warning(f"==liuq debug== 数据对中缺少row1或row2")
                return 0.0

            # 检查主字段是否存在
            if self.primary_field not in row1 or self.primary_field not in row2:
                logger.warning(f"==liuq debug== 未找到主字段: {self.primary_field}")
                return 0.0

            before_value = row1[self.primary_field]
            after_value = row2[self.primary_field]

            # 转换为数值类型
            before_num = float(before_value)
            after_num = float(after_value)

            if self.is_primary_field_cct:
                # CCT字段使用绝对值变化
                absolute_change = abs(after_num - before_num)

                return round(absolute_change, 2)
            else:
                # 非CCT字段使用百分比变化
                if before_num == 0:
                    # 如果原值为0，后值不为0，则认为是100%变化
                    percentage_change = 100.0 if after_num != 0 else 0.0
                else:
                    # 计算变化百分比：|新值 - 旧值| / |旧值| * 100%
                    percentage_change = abs(after_num - before_num) / abs(before_num) * 100


                return round(percentage_change, 2)

        except (ValueError, TypeError) as e:
            logger.warning(f"==liuq debug== 计算{self.primary_field}变化失败: {e}")
            return 0.0

    def calculate_field_change_percentage(self, before_value: Any, after_value: Any) -> float:
        """
        计算单个字段的变化百分比
        
        Args:
            before_value: 变化前的值
            after_value: 变化后的值
            
        Returns:
            变化百分比，如果无法计算则返回None
        """
        try:
            # 转换为数值类型
            before_num = float(before_value)
            after_num = float(after_value)
            
            # 避免除零错误
            if before_num == 0:
                # 如果原值为0，后值不为0，则认为是100%变化
                return 100.0 if after_num != 0 else 0.0
            
            # 计算变化百分比：|新值 - 旧值| / |旧值| * 100%
            change_percentage = abs(after_num - before_num) / abs(before_num) * 100
            
            return round(change_percentage, 2)
            
        except (ValueError, TypeError):
            # 无法转换为数值的情况
            return None
    
    def get_field_changes(self, pair: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        获取图片的所有字段变化详情
        
        Args:
            pair: 数据对
            
        Returns:
            字段变化详情字典
        """
        field_changes = {}
        
        # 从pair中获取row1和row2数据
        row1 = pair.get('row1')
        row2 = pair.get('row2')

        if row1 is None or row2 is None:
            logger.warning(f"==liuq debug== 数据对中缺少row1或row2")
            return field_changes

        for field in self.selected_fields:
            if field in row1 and field in row2:
                before_value = row1[field]
                after_value = row2[field]
                change_pct = self.calculate_field_change_percentage(before_value, after_value)

                # 计算绝对变化
                try:
                    absolute_change = float(after_value) - float(before_value) if change_pct is not None else None
                except (ValueError, TypeError):
                    absolute_change = None

                field_changes[field] = {
                    'before': before_value,
                    'after': after_value,
                    'change_percentage': change_pct,
                    'absolute_change': absolute_change
                }

                # 如果是sensorCCT字段，添加额外信息
                if field == 'sensorCCT' and absolute_change is not None:
                    field_changes[field]['absolute_change_k'] = f"{abs(absolute_change):.1f}K"
        
        return field_changes
    
    def get_classification_summary(self, classification_result: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        获取分类统计摘要
        
        Args:
            classification_result: 分类结果
            
        Returns:
            统计摘要
        """
        total_images = sum(len(images) for images in classification_result.values())
        
        summary = {
            'total_images': total_images,
            'large_changes': {
                'count': len(classification_result['large_changes']),
                'percentage': 0.0
            },
            'medium_changes': {
                'count': len(classification_result['medium_changes']),
                'percentage': 0.0
            },
            'small_changes': {
                'count': len(classification_result['small_changes']),
                'percentage': 0.0
            },
            'no_changes': {
                'count': len(classification_result['no_changes']),
                'percentage': 0.0
            }
        }

        # 计算百分比
        if total_images > 0:
            for category in ['large_changes', 'medium_changes', 'small_changes', 'no_changes']:
                count = summary[category]['count']
                summary[category]['percentage'] = round(count / total_images * 100, 1)
        
        return summary
    
    def update_thresholds(self, large_threshold: float, medium_threshold_min: float, medium_threshold_max: float = None, is_cct: bool = None):
        """
        更新分类阈值

        Args:
            large_threshold: 大变化阈值
            medium_threshold_min: 中变化最小阈值
            medium_threshold_max: 中变化最大阈值，默认等于large_threshold
            is_cct: 是否为CCT字段，None表示使用当前主字段类型
        """
        # 确定字段类型
        field_is_cct = is_cct if is_cct is not None else self.is_primary_field_cct

        if field_is_cct:
            # 更新CCT阈值
            self.cct_large_threshold = large_threshold
            self.cct_medium_threshold_min = medium_threshold_min
            self.cct_medium_threshold_max = medium_threshold_max or large_threshold
            self.cct_small_threshold = medium_threshold_min
            logger.info(f"==liuq debug== CCT分类阈值已更新 - 大变化: >{large_threshold}K, "
                       f"中变化: {medium_threshold_min}K-{self.cct_medium_threshold_max}K, "
                       f"小变化: <{medium_threshold_min}K")
        else:
            # 更新百分比阈值
            self.percentage_large_threshold = large_threshold
            self.percentage_medium_threshold_min = medium_threshold_min
            self.percentage_medium_threshold_max = medium_threshold_max or large_threshold
            self.percentage_small_threshold = medium_threshold_min
            logger.info(f"==liuq debug== 百分比分类阈值已更新 - 大变化: >{large_threshold}%, "
                       f"中变化: {medium_threshold_min}%-{self.percentage_medium_threshold_max}%, "
                       f"小变化: <{medium_threshold_min}%")

    def cleanup(self):
        """清理资源"""
        try:
            # 取消注册配置观察者
            self.config_manager.unregister_observer(self.on_config_updated)

        except Exception as e:
            logger.error(f"==liuq debug== 清理图片分类器资源失败: {e}")
