#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML备份服务

负责XML文件的备份和恢复功能

作者: AI Assistant
日期: 2025-08-25
"""

import shutil
import logging
from typing import Optional, Union
from pathlib import Path
from datetime import datetime

from core.interfaces.xml_data_processor import BackupError

logger = logging.getLogger(__name__)


class XMLBackupService:
    """XML备份服务"""
    
    def __init__(self):
        """初始化XML备份服务"""
        self.default_backup_dir = "backups"
        self.max_backup_count = 50
        
    def backup_xml(self, xml_path: Union[str, Path], 
                   backup_dir: Optional[Union[str, Path]] = None) -> str:
        """
        创建XML文件备份

        Args:
            xml_path: 源XML文件路径
            backup_dir: 备份目录，None则使用默认备份目录

        Returns:
            str: 备份文件路径

        Raises:
            BackupError: 备份创建失败
        """
        try:
            xml_path = Path(xml_path)

            if not xml_path.exists():
                raise BackupError(f"源文件不存在: {xml_path}")

            # 确定备份目录
            if backup_dir is None:
                backup_dir = xml_path.parent / self.default_backup_dir
            else:
                backup_dir = Path(backup_dir)

            # 创建备份目录
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 清理旧备份（如果超过最大数量）
            self._cleanup_old_backups(backup_dir, xml_path.stem)

            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{xml_path.stem}_backup_{timestamp}{xml_path.suffix}"
            backup_path = backup_dir / backup_name

            # 复制文件
            shutil.copy2(xml_path, backup_path)

            logger.info(f"XML备份创建成功: {backup_path}")
            return str(backup_path)

        except Exception as e:
            error_msg = f"创建备份失败: {e}"
            logger.error(error_msg)
            raise BackupError(error_msg)

    def restore_from_backup(self, backup_path: Union[str, Path],
                           target_path: Union[str, Path]) -> bool:
        """
        从备份恢复XML文件

        Args:
            backup_path: 备份文件路径
            target_path: 目标文件路径

        Returns:
            bool: 恢复是否成功
        """
        try:
            backup_path = Path(backup_path)
            target_path = Path(target_path)

            if not backup_path.exists():
                logger.error(f"备份文件不存在: {backup_path}")
                return False

            # 在恢复前创建备份
            if target_path.exists():
                try:
                    self.backup_xml(target_path)
                except Exception as e:
                    logger.warning(f"恢复前备份失败: {e}")

            # 复制备份文件到目标位置
            shutil.copy2(backup_path, target_path)

            logger.info(f"从备份恢复成功: {target_path}")
            return True

        except Exception as e:
            logger.error(f"从备份恢复失败: {e}")
            return False

    def get_backup_list(self, xml_path: Union[str, Path]) -> list:
        """
        获取指定XML文件的备份列表

        Args:
            xml_path: 原始XML文件路径

        Returns:
            list: 备份文件信息列表
        """
        try:
            xml_path = Path(xml_path)
            backup_dir = xml_path.parent / self.default_backup_dir

            if not backup_dir.exists():
                return []

            backup_files = []
            backup_pattern = f"{xml_path.stem}_backup_*{xml_path.suffix}"

            for backup_file in backup_dir.glob(backup_pattern):
                try:
                    stat = backup_file.stat()
                    backup_files.append({
                        'path': str(backup_file),
                        'name': backup_file.name,
                        'size': stat.st_size,
                        'created_time': datetime.fromtimestamp(stat.st_ctime),
                        'modified_time': datetime.fromtimestamp(stat.st_mtime)
                    })
                except Exception as e:
                    logger.warning(f"获取备份文件信息失败: {backup_file} - {e}")

            # 按创建时间倒序排列
            backup_files.sort(key=lambda x: x['created_time'], reverse=True)
            return backup_files

        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
            return []

    def delete_backup(self, backup_path: Union[str, Path]) -> bool:
        """
        删除指定的备份文件

        Args:
            backup_path: 备份文件路径

        Returns:
            bool: 删除是否成功
        """
        try:
            backup_path = Path(backup_path)

            if not backup_path.exists():
                logger.warning(f"备份文件不存在: {backup_path}")
                return False

            backup_path.unlink()
            logger.info(f"备份文件删除成功: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"删除备份文件失败: {e}")
            return False

    def cleanup_all_backups(self, xml_path: Union[str, Path]) -> int:
        """
        清理指定XML文件的所有备份

        Args:
            xml_path: 原始XML文件路径

        Returns:
            int: 删除的备份文件数量
        """
        try:
            backup_list = self.get_backup_list(xml_path)
            deleted_count = 0

            for backup_info in backup_list:
                if self.delete_backup(backup_info['path']):
                    deleted_count += 1

            logger.info(f"清理完成，删除了 {deleted_count} 个备份文件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理备份失败: {e}")
            return 0

    def _cleanup_old_backups(self, backup_dir: Path, file_stem: str):
        """
        清理旧的备份文件

        Args:
            backup_dir: 备份目录
            file_stem: 文件名（不含扩展名）
        """
        try:
            backup_pattern = f"{file_stem}_backup_*"
            backup_files = list(backup_dir.glob(backup_pattern))

            if len(backup_files) <= self.max_backup_count:
                return

            # 按修改时间排序，删除最旧的文件
            backup_files.sort(key=lambda x: x.stat().st_mtime)

            files_to_delete = len(backup_files) - self.max_backup_count
            for i in range(files_to_delete):
                try:
                    backup_files[i].unlink()
                    logger.debug(f"删除旧备份: {backup_files[i]}")
                except Exception as e:
                    logger.warning(f"删除旧备份失败: {backup_files[i]} - {e}")

        except Exception as e:
            logger.warning(f"清理旧备份失败: {e}")


# 全局备份服务实例
_backup_service: Optional[XMLBackupService] = None


def get_xml_backup_service() -> XMLBackupService:
    """获取XML备份服务实例"""
    global _backup_service
    
    if _backup_service is None:
        _backup_service = XMLBackupService()
        logger.info("创建XML备份服务实例")
    
    return _backup_service