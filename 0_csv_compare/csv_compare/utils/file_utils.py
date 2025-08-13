#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件操作工具
==liuq debug== 文件操作和路径处理工具

提供文件操作相关的工具函数
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class FileUtils:
    """文件操作工具类"""
    
    def __init__(self):
        """初始化文件工具"""
        logger.info("==liuq debug== 文件工具初始化完成")
    
    @staticmethod
    def ensure_directory(directory_path: Union[str, Path]) -> bool:
        """
        确保目录存在，如果不存在则创建
        
        Args:
            directory_path: 目录路径
            
        Returns:
            是否成功
        """
        try:
            path_obj = Path(directory_path)
            path_obj.mkdir(parents=True, exist_ok=True)
            logger.info(f"==liuq debug== 目录确保存在: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"==liuq debug== 创建目录失败: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                return {'exists': False, 'error': '文件不存在'}
            
            stat = path_obj.stat()
            
            info = {
                'exists': True,
                'name': path_obj.name,
                'stem': path_obj.stem,
                'suffix': path_obj.suffix,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'is_file': path_obj.is_file(),
                'is_directory': path_obj.is_dir(),
                'absolute_path': str(path_obj.absolute()),
                'parent_directory': str(path_obj.parent)
            }
            

            return info
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取文件信息失败: {e}")
            return {'exists': False, 'error': str(e)}
    
    @staticmethod
    def generate_unique_filename(base_path: Union[str, Path], 
                                extension: str = '.html') -> str:
        """
        生成唯一的文件名
        
        Args:
            base_path: 基础路径
            extension: 文件扩展名
            
        Returns:
            唯一的文件路径
        """
        try:
            base_path = Path(base_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 如果base_path是目录，生成默认文件名
            if base_path.is_dir() or not base_path.suffix:
                filename = f"csv_compare_report_{timestamp}{extension}"
                full_path = base_path / filename
            else:
                # 如果base_path已经是文件路径，在文件名中添加时间戳
                stem = base_path.stem
                suffix = base_path.suffix or extension
                filename = f"{stem}_{timestamp}{suffix}"
                full_path = base_path.parent / filename
            
            # 如果文件已存在，添加序号
            counter = 1
            original_path = full_path
            while full_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                filename = f"{stem}_{counter:03d}{suffix}"
                full_path = original_path.parent / filename
                counter += 1
            
            logger.info(f"==liuq debug== 生成唯一文件名: {full_path}")
            return str(full_path)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成唯一文件名失败: {e}")
            # 返回一个基本的文件名
            return f"csv_compare_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"
    
    @staticmethod
    def backup_file(file_path: Union[str, Path], 
                   backup_dir: Optional[Union[str, Path]] = None) -> Optional[str]:
        """
        备份文件
        
        Args:
            file_path: 要备份的文件路径
            backup_dir: 备份目录（可选）
            
        Returns:
            备份文件路径，失败返回None
        """
        try:
            source_path = Path(file_path)
            
            if not source_path.exists():
                logger.error(f"==liuq debug== 备份失败，源文件不存在: {file_path}")
                return None
            
            # 确定备份目录
            if backup_dir:
                backup_path = Path(backup_dir)
            else:
                backup_path = source_path.parent / 'backup'
            
            # 确保备份目录存在
            FileUtils.ensure_directory(backup_path)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_path.stem}_backup_{timestamp}{source_path.suffix}"
            backup_file_path = backup_path / backup_filename
            
            # 复制文件
            shutil.copy2(source_path, backup_file_path)
            
            logger.info(f"==liuq debug== 文件备份成功: {backup_file_path}")
            return str(backup_file_path)
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件备份失败: {e}")
            return None
    
    @staticmethod
    def clean_old_files(directory: Union[str, Path], 
                       pattern: str = "*.html", 
                       max_files: int = 10) -> int:
        """
        清理旧文件，保留最新的几个
        
        Args:
            directory: 目录路径
            pattern: 文件模式
            max_files: 保留的最大文件数
            
        Returns:
            删除的文件数量
        """
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return 0
            
            # 获取匹配的文件列表
            files = list(dir_path.glob(pattern))
            
            if len(files) <= max_files:
                return 0
            
            # 按修改时间排序，最新的在前
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 删除多余的文件
            files_to_delete = files[max_files:]
            deleted_count = 0
            
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"==liuq debug== 删除旧文件: {file_path}")
                except Exception as e:
                    logger.warning(f"==liuq debug== 删除文件失败: {file_path}, {e}")
            
            logger.info(f"==liuq debug== 清理完成，删除 {deleted_count} 个旧文件")
            return deleted_count
            
        except Exception as e:
            logger.error(f"==liuq debug== 清理旧文件失败: {e}")
            return 0
    
    @staticmethod
    def get_available_space(path: Union[str, Path]) -> Dict[str, int]:
        """
        获取磁盘可用空间
        
        Args:
            path: 路径
            
        Returns:
            空间信息字典
        """
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(path)),
                    ctypes.pointer(free_bytes),
                    ctypes.pointer(total_bytes),
                    None
                )
                
                return {
                    'free_bytes': free_bytes.value,
                    'total_bytes': total_bytes.value,
                    'free_mb': round(free_bytes.value / (1024 * 1024), 2),
                    'total_mb': round(total_bytes.value / (1024 * 1024), 2),
                    'free_gb': round(free_bytes.value / (1024 * 1024 * 1024), 2),
                    'total_gb': round(total_bytes.value / (1024 * 1024 * 1024), 2)
                }
            else:  # Unix/Linux
                statvfs = os.statvfs(str(path))
                free_bytes = statvfs.f_frsize * statvfs.f_bavail
                total_bytes = statvfs.f_frsize * statvfs.f_blocks
                
                return {
                    'free_bytes': free_bytes,
                    'total_bytes': total_bytes,
                    'free_mb': round(free_bytes / (1024 * 1024), 2),
                    'total_mb': round(total_bytes / (1024 * 1024), 2),
                    'free_gb': round(free_bytes / (1024 * 1024 * 1024), 2),
                    'total_gb': round(total_bytes / (1024 * 1024 * 1024), 2)
                }
                
        except Exception as e:
            logger.error(f"==liuq debug== 获取磁盘空间失败: {e}")
            return {
                'free_bytes': 0,
                'total_bytes': 0,
                'free_mb': 0,
                'total_mb': 0,
                'free_gb': 0,
                'total_gb': 0,
                'error': str(e)
            }
    
    @staticmethod
    def open_file_location(file_path: Union[str, Path]) -> bool:
        """
        在文件管理器中打开文件位置
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                logger.error(f"==liuq debug== 文件不存在: {file_path}")
                return False
            
            if os.name == 'nt':  # Windows
                os.startfile(str(path_obj.parent))
            elif os.name == 'posix':  # macOS/Linux
                if sys.platform == 'darwin':  # macOS
                    os.system(f'open "{path_obj.parent}"')
                else:  # Linux
                    os.system(f'xdg-open "{path_obj.parent}"')
            
            logger.info(f"==liuq debug== 打开文件位置: {path_obj.parent}")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 打开文件位置失败: {e}")
            return False
