#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理器工具类
==liuq debug== FastMapV2文件管理工具

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 17:48:00 +08:00; Reason: P1-LD-003 抽象化HTML/Chart生成器; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: 提供文件和目录管理的通用工具类
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from core.interfaces.report_generator import IFileManager

logger = logging.getLogger(__name__)


class FileManager(IFileManager):
    """
    文件管理器类
    
    提供文件和目录操作的通用接口
    """
    
    def __init__(self):
        """初始化文件管理器"""
        logger.info("==liuq debug== 文件管理器初始化完成")
    
    def ensure_directory(self, directory_path: Path) -> None:
        """
        确保目录存在
        
        Args:
            directory_path: 目录路径
        """
        try:
            directory_path.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"==liuq debug== 创建目录失败: {directory_path}, 错误: {e}")
            raise
    
    def generate_unique_filename(self, directory: Path, extension: str) -> str:
        """
        生成唯一文件名
        
        Args:
            directory: 目录路径
            extension: 文件扩展名（包含点号，如'.html'）
            
        Returns:
            唯一文件路径
        """
        try:
            # 确保目录存在
            self.ensure_directory(directory)
            
            # 生成基于时间戳的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"fastmapv2_report_{timestamp}"
            
            # 检查文件是否已存在，如果存在则添加序号
            counter = 1
            filename = f"{base_filename}{extension}"
            file_path = directory / filename
            
            while file_path.exists():
                filename = f"{base_filename}_{counter:03d}{extension}"
                file_path = directory / filename
                counter += 1
                
                # 防止无限循环
                if counter > 999:
                    raise RuntimeError("无法生成唯一文件名，请检查目录权限")
            
            logger.info(f"==liuq debug== 生成唯一文件名: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"==liuq debug== 生成唯一文件名失败: {e}")
            raise
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> None:
        """
        写入文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 编码格式
        """
        try:
            # 确保父目录存在
            parent_dir = Path(file_path).parent
            self.ensure_directory(parent_dir)
            
            # 写入文件
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            logger.info(f"==liuq debug== 文件写入成功: {file_path}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件写入失败: {file_path}, 错误: {e}")
            raise
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            encoding: 编码格式
            
        Returns:
            文件内容
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            

            return content
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件读取失败: {file_path}, 错误: {e}")
            raise
    
    def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否存在
        """
        exists = Path(file_path).exists()

        return exists
    
    def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        try:
            size = Path(file_path).stat().st_size

            return size
            
        except Exception as e:
            logger.error(f"==liuq debug== 获取文件大小失败: {file_path}, 错误: {e}")
            raise
    
    def delete_file(self, file_path: str) -> None:
        """
        删除文件
        
        Args:
            file_path: 文件路径
        """
        try:
            Path(file_path).unlink()
            logger.info(f"==liuq debug== 文件删除成功: {file_path}")
            
        except FileNotFoundError:
            logger.warning(f"==liuq debug== 文件不存在，无需删除: {file_path}")
        except Exception as e:
            logger.error(f"==liuq debug== 文件删除失败: {file_path}, 错误: {e}")
            raise
    
    def copy_file(self, source_path: str, destination_path: str) -> None:
        """
        复制文件
        
        Args:
            source_path: 源文件路径
            destination_path: 目标文件路径
        """
        try:
            import shutil
            
            # 确保目标目录存在
            dest_dir = Path(destination_path).parent
            self.ensure_directory(dest_dir)
            
            # 复制文件
            shutil.copy2(source_path, destination_path)
            logger.info(f"==liuq debug== 文件复制成功: {source_path} -> {destination_path}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件复制失败: {source_path} -> {destination_path}, 错误: {e}")
            raise
    
    def move_file(self, source_path: str, destination_path: str) -> None:
        """
        移动文件
        
        Args:
            source_path: 源文件路径
            destination_path: 目标文件路径
        """
        try:
            import shutil
            
            # 确保目标目录存在
            dest_dir = Path(destination_path).parent
            self.ensure_directory(dest_dir)
            
            # 移动文件
            shutil.move(source_path, destination_path)
            logger.info(f"==liuq debug== 文件移动成功: {source_path} -> {destination_path}")
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件移动失败: {source_path} -> {destination_path}, 错误: {e}")
            raise
    
    def list_files(self, directory_path: str, pattern: str = "*") -> list:
        """
        列出目录中的文件
        
        Args:
            directory_path: 目录路径
            pattern: 文件模式（如'*.xml'）
            
        Returns:
            文件路径列表
        """
        try:
            directory = Path(directory_path)
            if not directory.exists():
                logger.warning(f"==liuq debug== 目录不存在: {directory_path}")
                return []
            
            files = list(directory.glob(pattern))
            file_paths = [str(f) for f in files if f.is_file()]
            

            return file_paths
            
        except Exception as e:
            logger.error(f"==liuq debug== 列出文件失败: {directory_path}, 错误: {e}")
            raise
    
    def create_backup(self, file_path: str, backup_dir: Optional[str] = None) -> str:
        """
        创建文件备份
        
        Args:
            file_path: 原文件路径
            backup_dir: 备份目录（可选）
            
        Returns:
            备份文件路径
        """
        try:
            source_file = Path(file_path)
            if not source_file.exists():
                raise FileNotFoundError(f"源文件不存在: {file_path}")
            
            # 确定备份目录
            if backup_dir:
                backup_directory = Path(backup_dir)
            else:
                backup_directory = source_file.parent / "backups"
            
            self.ensure_directory(backup_directory)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{source_file.stem}_{timestamp}{source_file.suffix}"
            backup_path = backup_directory / backup_filename
            
            # 复制文件到备份位置
            self.copy_file(str(source_file), str(backup_path))
            
            logger.info(f"==liuq debug== 文件备份成功: {file_path} -> {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"==liuq debug== 文件备份失败: {file_path}, 错误: {e}")
            raise
