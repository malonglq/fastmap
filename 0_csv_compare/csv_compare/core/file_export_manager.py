#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件导出管理器模块
处理图片文件的分类复制和导出操作
==liuq debug== 文件导出管理器实现
"""

import logging
import shutil
from typing import Dict, List, Any, Callable, Optional
from pathlib import Path
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class FileExportManager:
    """文件导出管理器"""
    
    def __init__(self):
        """初始化文件导出管理器"""
        # 支持的图片格式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
        
        # 导出统计
        self.export_stats = {
            'total_files': 0,
            'copied_files': 0,
            'skipped_files': 0,
            'error_files': 0,
            'start_time': None,
            'end_time': None
        }
        
        logger.info("==liuq debug== 文件导出管理器初始化完成")
    
    def export_images(self, 
                     export_config: Dict[str, Any],
                     progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, Any]:
        """
        执行图片导出
        
        Args:
            export_config: 导出配置
            progress_callback: 进度回调函数 (progress, message)
            
        Returns:
            导出结果统计
        """
        try:
            logger.info("==liuq debug== 开始执行图片导出")
            self.export_stats['start_time'] = datetime.now()
            
            # 解析配置
            source_dir = Path(export_config['source_directory'])
            output_dir = Path(export_config['output_directory'])
            export_categories = export_config['export_categories']
            classification_result = export_config['classification_result']
            
            # 创建输出目录结构
            category_dirs = self.create_output_directories(output_dir)

            # 验证源文件存在性
            if progress_callback:
                progress_callback(0, "正在验证源文件...")

            validation_result = self.validate_source_files(source_dir, classification_result)

            # 统计分类条目数（用于进度计算）
            total_files = self.count_files_to_export(classification_result, export_categories)
            self.export_stats['total_files'] = total_files

            # 统计实际文件数量
            actual_files_count = self.count_actual_files_to_export(source_dir, classification_result, export_categories)

            # 报告验证结果
            if progress_callback:
                found_rate = (validation_result['found_files'] / validation_result['total_files'] * 100) if validation_result['total_files'] > 0 else 0
                progress_callback(0, f"文件验证完成: {validation_result['found_files']}/{validation_result['total_files']} ({found_rate:.1f}%) 可用")

            if progress_callback:
                progress_callback(0, f"准备导出 {total_files} 个分类条目，预计实际复制 {actual_files_count} 个图片文件...")
            
            # 执行分类导出
            processed_files = 0
            
            for category, should_export in export_categories.items():
                if not should_export:
                    continue
                
                category_name = self.get_category_display_name(category)
                target_dir = category_dirs[category]
                images = classification_result[category]
                
                logger.info(f"==liuq debug== 开始导出 {category_name}: {len(images)} 个文件")
                
                for image_info in images:
                    try:
                        # 更新进度
                        processed_files += 1
                        progress = int((processed_files / total_files) * 100)

                        if progress_callback:
                            progress_callback(progress, f"正在复制: {image_info['image_name']} 及相关文件...")

                        # 使用新的按前缀复制方法，传递完整的图片信息以生成变化值文件名
                        copied_count = self.copy_images_by_prefix_with_change_value(
                            source_dir,
                            target_dir,
                            image_info
                        )

                        if copied_count > 0:
                            self.export_stats['copied_files'] += copied_count
                            logger.info(f"==liuq debug== {image_info['image_name']} 成功复制 {copied_count} 个相关文件")
                        else:
                            self.export_stats['skipped_files'] += 1
                            logger.warning(f"==liuq debug== {image_info['image_name']} 未复制任何文件")

                        # 短暂延迟，避免UI阻塞
                        time.sleep(0.01)

                    except Exception as e:
                        logger.error(f"==liuq debug== 复制文件 {image_info['image_name']} 失败: {e}")
                        self.export_stats['error_files'] += 1
            
            self.export_stats['end_time'] = datetime.now()

            if progress_callback:
                progress_callback(100, "图片分类导出完成！")

            logger.info(f"==liuq debug== 图片分类导出完成 - 成功复制: {self.export_stats['copied_files']} 个文件, "
                       f"跳过: {self.export_stats['skipped_files']} 个文件, 错误: {self.export_stats['error_files']} 个文件")

            return self.get_export_summary(output_dir)
            
        except Exception as e:
            logger.error(f"==liuq debug== 图片导出失败: {e}")
            raise
    
    def create_output_directories(self, output_dir: Path) -> Dict[str, Path]:
        """
        创建输出目录结构
        
        Args:
            output_dir: 输出根目录
            
        Returns:
            分类目录字典
        """
        try:
            # 创建主输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建分类子目录（简化命名）
            category_dirs = {
                'large_changes': output_dir / '大变化',
                'medium_changes': output_dir / '中变化',
                'small_changes': output_dir / '小变化',
                'no_changes': output_dir / '无变化'
            }
            
            for category, dir_path in category_dirs.items():
                dir_path.mkdir(exist_ok=True)
                logger.info(f"==liuq debug== 创建目录: {dir_path}")
            
            return category_dirs
            
        except Exception as e:
            logger.error(f"==liuq debug== 创建输出目录失败: {e}")
            raise
    
    def count_files_to_export(self,
                             classification_result: Dict[str, List[Dict[str, Any]]],
                             export_categories: Dict[str, bool]) -> int:
        """
        统计要导出的文件数量（基于分类结果中的条目数，不是实际文件数）

        Args:
            classification_result: 分类结果
            export_categories: 导出分类选择

        Returns:
            分类条目总数（用于进度计算）
        """
        total = 0
        for category, should_export in export_categories.items():
            if should_export:
                total += len(classification_result[category])
        return total

    def count_actual_files_to_export(self,
                                   source_dir: Path,
                                   classification_result: Dict[str, List[Dict[str, Any]]],
                                   export_categories: Dict[str, bool]) -> int:
        """
        统计实际要导出的文件数量（包括所有前缀匹配的文件）

        Args:
            source_dir: 源目录
            classification_result: 分类结果
            export_categories: 导出分类选择

        Returns:
            实际文件总数
        """
        try:
            import re
            total_files = 0
            processed_prefixes = set()  # 避免重复统计相同前缀

            for category, should_export in export_categories.items():
                if not should_export:
                    continue

                images = classification_result[category]
                for image_info in images:
                    image_name = image_info['image_name']

                    # 提取序号前缀
                    prefix_match = re.search(r'^(\d+)_', image_name)
                    if prefix_match:
                        prefix = prefix_match.group(1)

                        # 避免重复统计相同前缀
                        if prefix in processed_prefixes:
                            continue
                        processed_prefixes.add(prefix)

                        # 统计该前缀的文件数量
                        pattern = f"{prefix}_*"
                        matching_files = [
                            f for f in source_dir.glob(pattern)
                            if f.is_file() and f.suffix.lower() in self.supported_formats
                        ]
                        total_files += len(matching_files)


                    else:
                        # 没有前缀的文件按单个计算
                        total_files += 1

            logger.info(f"==liuq debug== 预计实际导出文件数量: {total_files}")
            return total_files

        except Exception as e:
            logger.error(f"==liuq debug== 统计实际文件数量失败: {e}")
            # 回退到基本统计
            return self.count_files_to_export(classification_result, export_categories)
    
    def copy_image_file(self, source_dir: Path, target_dir: Path, image_name: str) -> bool:
        """
        复制单个图片文件

        Args:
            source_dir: 源目录
            target_dir: 目标目录
            image_name: 图片文件名

        Returns:
            是否复制成功
        """
        try:
            # 查找源文件（支持多种格式和文件名变体）
            source_file = self.find_image_file_with_variants(source_dir, image_name)

            if not source_file:
                logger.warning(f"==liuq debug== 未找到图片文件: {image_name}")
                return False

            # 构建目标文件路径
            target_file = target_dir / source_file.name

            # 处理文件名冲突
            if target_file.exists():
                target_file = self.resolve_filename_conflict(target_file)

            # 复制文件（保持元数据）
            shutil.copy2(source_file, target_file)


            return True

        except Exception as e:
            logger.error(f"==liuq debug== 复制文件失败 {image_name}: {e}")
            return False

    def copy_images_by_prefix(self, source_dir: Path, target_dir: Path, image_name: str) -> int:
        """
        根据序号前缀复制所有相关图片文件

        Args:
            source_dir: 源目录
            target_dir: 目标目录
            image_name: 参考图片文件名

        Returns:
            成功复制的文件数量
        """
        try:
            # 提取序号前缀
            import re
            prefix_match = re.search(r'^(\d+)_', image_name)
            if not prefix_match:
                # 如果没有序号前缀，使用原有的单文件复制逻辑
                logger.info(f"==liuq debug== 文件 {image_name} 没有序号前缀，使用单文件复制")
                return 1 if self.copy_image_file(source_dir, target_dir, image_name) else 0

            prefix = prefix_match.group(1)
            logger.info(f"==liuq debug== 从 {image_name} 提取序号前缀: {prefix}")

            # 查找所有具有相同前缀的文件
            pattern = f"{prefix}_*"
            matching_files = []

            for file_path in source_dir.glob(pattern):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    matching_files.append(file_path)

            if not matching_files:
                logger.warning(f"==liuq debug== 未找到前缀为 {prefix} 的图片文件")
                return 0

            logger.info(f"==liuq debug== 找到 {len(matching_files)} 个前缀为 {prefix} 的文件: {[f.name for f in matching_files]}")

            # 复制所有匹配的文件
            copied_count = 0
            for source_file in matching_files:
                try:
                    # 构建目标文件路径
                    target_file = target_dir / source_file.name

                    # 处理文件名冲突
                    if target_file.exists():
                        target_file = self.resolve_filename_conflict(target_file)

                    # 复制文件（保持元数据）
                    shutil.copy2(source_file, target_file)
                    copied_count += 1



                except Exception as e:
                    logger.error(f"==liuq debug== 复制文件失败 {source_file}: {e}")

            logger.info(f"==liuq debug== 前缀 {prefix} 共复制 {copied_count}/{len(matching_files)} 个文件")
            return copied_count

        except Exception as e:
            logger.error(f"==liuq debug== 按前缀复制文件失败 {image_name}: {e}")
            return 0

    def copy_images_by_prefix_with_change_value(self, source_dir: Path, target_dir: Path, image_info: Dict[str, Any]) -> int:
        """
        根据序号前缀复制所有相关图片文件，并在文件名末尾添加变化值标识

        Args:
            source_dir: 源目录
            target_dir: 目标目录
            image_info: 图片信息对象，包含变化值数据

        Returns:
            成功复制的文件数量
        """
        try:
            image_name = image_info['image_name']

            # 提取序号前缀
            import re
            prefix_match = re.search(r'^(\d+)_', image_name)
            if not prefix_match:
                # 如果没有序号前缀，使用原有的单文件复制逻辑
                logger.info(f"==liuq debug== 文件 {image_name} 没有序号前缀，使用单文件复制")
                return 1 if self.copy_image_file_with_change_value(source_dir, target_dir, image_info) else 0

            prefix = prefix_match.group(1)
            logger.info(f"==liuq debug== 从 {image_name} 提取序号前缀: {prefix}")

            # 查找所有具有相同前缀的文件
            pattern = f"{prefix}_*"
            matching_files = []

            for file_path in source_dir.glob(pattern):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    matching_files.append(file_path)

            if not matching_files:
                logger.warning(f"==liuq debug== 未找到前缀为 {prefix} 的图片文件")
                return 0

            logger.info(f"==liuq debug== 找到 {len(matching_files)} 个前缀为 {prefix} 的文件: {[f.name for f in matching_files]}")

            # 生成变化值标识
            change_suffix = self.generate_change_value_suffix(image_info)

            # 复制所有匹配的文件
            copied_count = 0
            for source_file in matching_files:
                try:
                    # 构建带变化值的目标文件名
                    target_filename = self.add_change_value_to_filename(source_file.name, change_suffix)
                    target_file = target_dir / target_filename

                    # 处理文件名冲突
                    if target_file.exists():
                        target_file = self.resolve_filename_conflict(target_file)

                    # 复制文件（保持元数据）
                    shutil.copy2(source_file, target_file)
                    copied_count += 1



                except Exception as e:
                    logger.error(f"==liuq debug== 复制文件失败 {source_file}: {e}")

            logger.info(f"==liuq debug== 前缀 {prefix} 共复制 {copied_count}/{len(matching_files)} 个文件，添加变化值: {change_suffix}")
            return copied_count

        except Exception as e:
            logger.error(f"==liuq debug== 按前缀复制文件失败 {image_name}: {e}")
            return 0

    def generate_change_value_suffix(self, image_info: Dict[str, Any]) -> str:
        """
        根据图片信息生成变化值后缀

        Args:
            image_info: 图片信息对象

        Returns:
            变化值后缀字符串（如：+200k, -150k, +0.02, -0.01）
        """
        try:
            # 获取主字段信息
            primary_field_name = image_info.get('primary_field_name', 'sensorCCT')
            is_cct_field = image_info.get('is_cct_field', True)
            field_changes = image_info.get('field_changes', {})

            # 从field_changes中获取主字段的变化数据
            if primary_field_name in field_changes:
                field_data = field_changes[primary_field_name]
                absolute_change = field_data.get('absolute_change')

                if absolute_change is not None:
                    if is_cct_field:
                        # CCT字段使用K为单位，显示带符号的变化值
                        if absolute_change > 0:
                            return f"+{absolute_change:.0f}k"
                        elif absolute_change < 0:
                            return f"{absolute_change:.0f}k"  # 负号已包含
                        else:
                            return "+0k"
                    else:
                        # 非CCT字段保持原始数值格式，显示带符号的变化值
                        if absolute_change > 0:
                            return f"+{absolute_change:.2f}"
                        elif absolute_change < 0:
                            return f"{absolute_change:.2f}"  # 负号已包含
                        else:
                            return "+0.00"

            # 如果无法从field_changes获取，尝试从primary_field_change获取
            # 注意：primary_field_change对于CCT字段是绝对值，对于非CCT字段是百分比变化
            primary_field_change = image_info.get('primary_field_change', 0)
            if primary_field_change != 0:
                if is_cct_field:
                    # 对于CCT字段，primary_field_change是绝对值变化的绝对值
                    # 我们需要从原始数据计算实际的符号
                    pair_data = image_info.get('pair_data', {})
                    if pair_data:
                        row1 = pair_data.get('row1')
                        row2 = pair_data.get('row2')
                        if row1 is not None and row2 is not None and primary_field_name in row1 and primary_field_name in row2:
                            try:
                                before_value = float(row1[primary_field_name])
                                after_value = float(row2[primary_field_name])
                                actual_change = after_value - before_value
                                if actual_change > 0:
                                    return f"+{primary_field_change:.0f}k"
                                elif actual_change < 0:
                                    return f"-{primary_field_change:.0f}k"
                                else:
                                    return "+0k"
                            except (ValueError, TypeError):
                                pass
                    # 如果无法确定符号，默认为正值
                    return f"+{primary_field_change:.0f}k"
                else:
                    # 对于非CCT字段，primary_field_change是百分比变化的绝对值
                    # 同样需要从原始数据计算符号
                    pair_data = image_info.get('pair_data', {})
                    if pair_data:
                        row1 = pair_data.get('row1')
                        row2 = pair_data.get('row2')
                        if row1 is not None and row2 is not None and primary_field_name in row1 and primary_field_name in row2:
                            try:
                                before_value = float(row1[primary_field_name])
                                after_value = float(row2[primary_field_name])
                                actual_change = after_value - before_value
                                if actual_change > 0:
                                    return f"+{actual_change:.2f}"
                                elif actual_change < 0:
                                    return f"{actual_change:.2f}"  # 负号已包含
                                else:
                                    return "+0.00"
                            except (ValueError, TypeError):
                                pass
                    # 如果无法确定符号，默认为正值
                    return f"+{primary_field_change:.2f}"

            # 默认返回零变化
            return "+0k" if is_cct_field else "+0.00"

        except Exception as e:
            logger.error(f"==liuq debug== 生成变化值后缀失败: {e}")
            return "+0k"  # 默认返回零变化

    def add_change_value_to_filename(self, original_filename: str, change_suffix: str) -> str:
        """
        在文件名末尾添加变化值标识

        Args:
            original_filename: 原始文件名
            change_suffix: 变化值后缀

        Returns:
            带变化值的新文件名
        """
        try:
            # 分离文件名和扩展名
            name_part, ext_part = original_filename.rsplit('.', 1) if '.' in original_filename else (original_filename, '')

            # 构建新文件名：{原始名称}+{变化值}.{扩展名}
            new_filename = f"{name_part}{change_suffix}"
            if ext_part:
                new_filename += f".{ext_part}"

            # 处理文件名中的特殊字符，确保文件系统兼容性
            new_filename = self.sanitize_filename(new_filename)


            return new_filename

        except Exception as e:
            logger.error(f"==liuq debug== 添加变化值到文件名失败: {e}")
            return original_filename  # 失败时返回原始文件名

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名中的特殊字符，确保文件系统兼容性

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        try:
            import re
            # 替换Windows文件系统不支持的字符
            invalid_chars = r'[<>:"/\\|?*]'
            sanitized = re.sub(invalid_chars, '_', filename)

            # 确保文件名不以点开头或结尾
            sanitized = sanitized.strip('.')

            # 限制文件名长度（Windows限制为255字符）
            if len(sanitized) > 250:  # 留一些余量
                name_part, ext_part = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
                max_name_length = 250 - len(ext_part) - 1 if ext_part else 250
                sanitized = name_part[:max_name_length]
                if ext_part:
                    sanitized += f".{ext_part}"

            return sanitized

        except Exception as e:
            logger.error(f"==liuq debug== 清理文件名失败: {e}")
            return filename

    def copy_image_file_with_change_value(self, source_dir: Path, target_dir: Path, image_info: Dict[str, Any]) -> bool:
        """
        复制单个图片文件并添加变化值到文件名

        Args:
            source_dir: 源目录
            target_dir: 目标目录
            image_info: 图片信息对象

        Returns:
            是否复制成功
        """
        try:
            image_name = image_info['image_name']

            # 查找源文件（支持多种格式和文件名变体）
            source_file = self.find_image_file_with_variants(source_dir, image_name)

            if not source_file:
                logger.warning(f"==liuq debug== 未找到图片文件: {image_name}")
                return False

            # 生成变化值标识
            change_suffix = self.generate_change_value_suffix(image_info)

            # 构建带变化值的目标文件名
            target_filename = self.add_change_value_to_filename(source_file.name, change_suffix)
            target_file = target_dir / target_filename

            # 处理文件名冲突
            if target_file.exists():
                target_file = self.resolve_filename_conflict(target_file)

            # 复制文件（保持元数据）
            shutil.copy2(source_file, target_file)


            return True

        except Exception as e:
            logger.error(f"==liuq debug== 复制文件失败 {image_info.get('image_name', 'unknown')}: {e}")
            return False

    def find_image_file(self, source_dir: Path, image_name: str) -> Optional[Path]:
        """
        查找图片文件（支持多种格式）

        Args:
            source_dir: 源目录
            image_name: 图片文件名（可能不含扩展名）

        Returns:
            找到的文件路径，如果未找到则返回None
        """
        # 移除可能的扩展名
        base_name = Path(image_name).stem

        # 尝试各种格式
        for ext in self.supported_formats:
            candidate = source_dir / f"{base_name}{ext}"
            if candidate.exists():
                return candidate

        # 如果原始文件名包含扩展名，直接尝试
        original_file = source_dir / image_name
        if original_file.exists():
            return original_file

        return None

    def find_image_file_with_variants(self, source_dir: Path, image_name: str) -> Optional[Path]:
        """
        增强的图片文件查找，支持常见的文件名变体

        Args:
            source_dir: 源目录
            image_name: 图片文件名

        Returns:
            找到的文件路径，如果未找到则返回None
        """
        # 1. 精确匹配（原有逻辑）
        exact_file = self.find_image_file(source_dir, image_name)
        if exact_file:
            return exact_file

        # 2. 移除_ori后缀匹配
        if '_ori.' in image_name:
            name_without_ori = image_name.replace('_ori.', '.')
            variant_file = self.find_image_file(source_dir, name_without_ori)
            if variant_file:
                logger.info(f"==liuq debug== 找到文件名变体: {image_name} -> {name_without_ori}")
                return variant_file

        # 3. 基于时间戳的模糊匹配
        import re
        timestamp_match = re.search(r'IMG(\d{14})', image_name)
        if timestamp_match:
            timestamp = timestamp_match.group(1)
            # 遍历目录中的所有文件
            for file_path in source_dir.glob('*'):
                if file_path.is_file() and timestamp in file_path.name:
                    if file_path.suffix.lower() in self.supported_formats:
                        logger.info(f"==liuq debug== 找到时间戳匹配: {image_name} -> {file_path.name}")
                        return file_path

        # 4. 基于序号的匹配（提取文件名开头的数字）
        number_match = re.search(r'^(\d+)_', image_name)
        if number_match:
            number = number_match.group(1)
            for file_path in source_dir.glob(f"{number}_*"):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    logger.info(f"==liuq debug== 找到序号匹配: {image_name} -> {file_path.name}")
                    return file_path

        return None

    def validate_source_files(self, source_dir: Path, classification_result: Dict) -> Dict:
        """
        验证源文件存在性，在导出前检查文件可用性

        Args:
            source_dir: 源目录
            classification_result: 分类结果

        Returns:
            验证结果统计
        """
        validation_result = {
            'total_files': 0,
            'found_files': 0,
            'missing_files': [],
            'variant_matches': [],
            'exact_matches': []
        }

        logger.info(f"==liuq debug== 开始验证源文件存在性: {source_dir}")

        for category, images in classification_result.items():
            for image_info in images:
                image_name = image_info['image_name']
                validation_result['total_files'] += 1

                # 先尝试精确匹配
                exact_file = self.find_image_file(source_dir, image_name)
                if exact_file:
                    validation_result['found_files'] += 1
                    validation_result['exact_matches'].append(image_name)
                    continue

                # 再尝试变体匹配
                variant_file = self.find_image_file_with_variants(source_dir, image_name)
                if variant_file:
                    validation_result['found_files'] += 1
                    validation_result['variant_matches'].append({
                        'original': image_name,
                        'found': variant_file.name
                    })
                else:
                    validation_result['missing_files'].append(image_name)

        # 记录验证结果
        logger.info(f"==liuq debug== 文件验证完成:")
        logger.info(f"  总文件数: {validation_result['total_files']}")
        logger.info(f"  找到文件: {validation_result['found_files']}")
        logger.info(f"  精确匹配: {len(validation_result['exact_matches'])}")
        logger.info(f"  变体匹配: {len(validation_result['variant_matches'])}")
        logger.info(f"  缺失文件: {len(validation_result['missing_files'])}")

        if validation_result['variant_matches']:
            logger.info(f"==liuq debug== 文件名变体匹配示例:")
            for match in validation_result['variant_matches'][:5]:  # 只显示前5个
                logger.info(f"  {match['original']} -> {match['found']}")

        if validation_result['missing_files']:
            logger.warning(f"==liuq debug== 部分文件未找到，前5个示例:")
            for missing in validation_result['missing_files'][:5]:
                logger.warning(f"  {missing}")

        return validation_result

    def resolve_filename_conflict(self, target_file: Path) -> Path:
        """
        解决文件名冲突
        
        Args:
            target_file: 目标文件路径
            
        Returns:
            新的文件路径
        """
        base_name = target_file.stem
        extension = target_file.suffix
        parent_dir = target_file.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = parent_dir / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    

    def get_category_display_name(self, category_key: str) -> str:
        """获取分类显示名称"""
        names = {
            'large_changes': '大变化',
            'medium_changes': '中变化',
            'small_changes': '小变化',
            'no_changes': '无变化'
        }
        return names.get(category_key, category_key)
    
    def get_export_summary(self, output_dir: Path) -> Dict[str, Any]:
        """
        获取导出摘要
        
        Args:
            output_dir: 输出目录
            
        Returns:
            导出摘要字典
        """
        duration = None
        if self.export_stats['start_time'] and self.export_stats['end_time']:
            duration = self.export_stats['end_time'] - self.export_stats['start_time']
        
        return {
            'success': True,
            'output_directory': str(output_dir),
            'statistics': {
                'total_files': self.export_stats['total_files'],
                'copied_files': self.export_stats['copied_files'],
                'skipped_files': self.export_stats['skipped_files'],
                'error_files': self.export_stats['error_files'],
                'success_rate': round(
                    (self.export_stats['copied_files'] / max(self.export_stats['total_files'], 1)) * 100, 1
                )
            },
            'duration': str(duration).split('.')[0] if duration else None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
