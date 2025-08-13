#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码检测工具
==liuq debug== 文件编码检测和处理工具

提供文件编码检测和转换功能
"""

import chardet
import logging
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class EncodingDetector:
    """编码检测器类"""
    
    def __init__(self):
        """初始化编码检测器"""
        self.common_encodings = [
            'utf-8', 'utf-8-sig',
            'gbk', 'gb2312', 'gb18030',
            'latin1', 'cp1252',
            'ascii'
        ]
        logger.info("==liuq debug== 编码检测器初始化完成")
    
    def detect_file_encoding(self, file_path: str, sample_size: int = 10240) -> Dict[str, any]:
        """
        检测文件编码
        
        Args:
            file_path: 文件路径
            sample_size: 采样大小（字节）
            
        Returns:
            检测结果字典
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            with open(file_path, 'rb') as file:
                raw_data = file.read(sample_size)
                
                if not raw_data:
                    logger.warning(f"==liuq debug== 文件为空: {file_path}")
                    return {
                        'encoding': 'utf-8',
                        'confidence': 0.0,
                        'language': None,
                        'file_size': 0
                    }
                
                # 使用chardet检测
                result = chardet.detect(raw_data)
                
                # 获取文件大小
                file_size = Path(file_path).stat().st_size
                
                detection_result = {
                    'encoding': result.get('encoding', 'utf-8').lower(),
                    'confidence': result.get('confidence', 0.0),
                    'language': result.get('language'),
                    'file_size': file_size,
                    'sample_size': len(raw_data)
                }
                
                logger.info(f"==liuq debug== 编码检测结果: {detection_result}")
                return detection_result
                
        except Exception as e:
            logger.error(f"==liuq debug== 编码检测失败: {e}")
            return {
                'encoding': 'utf-8',
                'confidence': 0.0,
                'language': None,
                'file_size': 0,
                'error': str(e)
            }
    
    def validate_encoding(self, file_path: str, encoding: str) -> bool:
        """
        验证指定编码是否能正确读取文件
        
        Args:
            file_path: 文件路径
            encoding: 编码格式
            
        Returns:
            是否能正确读取
        """
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                # 尝试读取前几行
                for i, line in enumerate(file):
                    if i >= 10:  # 只检查前10行
                        break
                    # 如果能读取到这里说明编码正确
                    pass
            
            logger.info(f"==liuq debug== 编码 {encoding} 验证通过")
            return True
            
        except UnicodeDecodeError:
            logger.warning(f"==liuq debug== 编码 {encoding} 验证失败")
            return False
        except Exception as e:
            logger.error(f"==liuq debug== 编码验证出错: {e}")
            return False
    
    def find_best_encoding(self, file_path: str) -> str:
        """
        寻找最佳编码格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            最佳编码格式
        """
        try:
            # 首先使用自动检测
            detection_result = self.detect_file_encoding(file_path)
            detected_encoding = detection_result['encoding']
            confidence = detection_result['confidence']
            
            # 如果置信度高，直接使用检测结果
            if confidence > 0.8 and self.validate_encoding(file_path, detected_encoding):
                logger.info(f"==liuq debug== 使用检测到的编码: {detected_encoding}")
                return detected_encoding
            
            # 如果置信度不高，尝试常见编码
            logger.info("==liuq debug== 检测置信度不高，尝试常见编码")
            
            for encoding in self.common_encodings:
                if self.validate_encoding(file_path, encoding):
                    logger.info(f"==liuq debug== 找到可用编码: {encoding}")
                    return encoding
            
            # 如果都不行，返回默认编码
            logger.warning("==liuq debug== 无法找到合适编码，使用UTF-8")
            return 'utf-8'
            
        except Exception as e:
            logger.error(f"==liuq debug== 寻找最佳编码失败: {e}")
            return 'utf-8'
    
    def convert_encoding(self, input_file: str, output_file: str, 
                        source_encoding: str, target_encoding: str = 'utf-8') -> bool:
        """
        转换文件编码
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            source_encoding: 源编码
            target_encoding: 目标编码
            
        Returns:
            转换是否成功
        """
        try:
            logger.info(f"==liuq debug== 开始编码转换: {source_encoding} -> {target_encoding}")
            
            with open(input_file, 'r', encoding=source_encoding) as infile:
                content = infile.read()
            
            with open(output_file, 'w', encoding=target_encoding) as outfile:
                outfile.write(content)
            
            logger.info(f"==liuq debug== 编码转换成功: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 编码转换失败: {e}")
            return False
    
    def get_encoding_info(self, encoding: str) -> Dict[str, str]:
        """
        获取编码信息
        
        Args:
            encoding: 编码名称
            
        Returns:
            编码信息字典
        """
        encoding_info = {
            'utf-8': {
                'name': 'UTF-8',
                'description': 'Unicode 8位编码',
                'language': '通用',
                'bom': False
            },
            'utf-8-sig': {
                'name': 'UTF-8 with BOM',
                'description': 'UTF-8编码（带BOM）',
                'language': '通用',
                'bom': True
            },
            'gbk': {
                'name': 'GBK',
                'description': '中文编码（扩展GB2312）',
                'language': '中文',
                'bom': False
            },
            'gb2312': {
                'name': 'GB2312',
                'description': '中文编码（简体中文）',
                'language': '中文',
                'bom': False
            },
            'gb18030': {
                'name': 'GB18030',
                'description': '中文编码（最新标准）',
                'language': '中文',
                'bom': False
            },
            'latin1': {
                'name': 'Latin-1',
                'description': 'ISO 8859-1编码',
                'language': '西欧',
                'bom': False
            }
        }
        
        return encoding_info.get(encoding.lower(), {
            'name': encoding.upper(),
            'description': '未知编码',
            'language': '未知',
            'bom': False
        })
