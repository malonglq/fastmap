#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML元数据提取服务
==liuq debug== FastMapV2 XML元数据提取服务

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: XML文件元数据提取服务，从XMLParserService中拆分
"""

import xml.etree.ElementTree as ET
import logging
from typing import Dict, List, Any, Union, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class XMLMetadataService:
    """
    XML元数据提取服务
    
    专门负责XML文件的元数据提取功能：
    - 文件基础信息提取
    - XML结构信息分析
    - 内容统计信息生成
    - 版本和设备信息识别
    """
    
    def __init__(self):
        """初始化XML元数据服务"""
        self.supported_versions = ["1.0", "1.1", "2.0"]
        logger.debug("==liuq debug== XML元数据服务初始化完成")
    
    def extract_file_metadata(self, xml_path: Union[str, Path]) -> Dict[str, Any]:
        """
        提取XML文件的基础元数据
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            Dict[str, Any]: 文件元数据字典
        """
        metadata = {}
        
        try:
            xml_path = Path(xml_path)
            
            # 文件基本信息
            if xml_path.exists():
                stat = xml_path.stat()
                metadata.update({
                    'file_size': stat.st_size,
                    'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'file_name': xml_path.name,
                    'file_path': str(xml_path.absolute())
                })
                
                # 文件大小分析
                file_size = stat.st_size
                if file_size == 0:
                    metadata['file_status'] = 'empty'
                elif file_size > 50 * 1024 * 1024:  # 50MB
                    metadata['file_status'] = 'large'
                elif file_size < 1024:  # 1KB
                    metadata['file_status'] = 'small'
                else:
                    metadata['file_status'] = 'normal'
            else:
                metadata['error'] = f"文件不存在: {xml_path}"
                return metadata
            
            return metadata
            
        except Exception as e:
            logger.error(f"==liuq debug== 提取文件元数据失败: {e}")
            return {"error": f"提取文件元数据失败: {e}"}
    
    def extract_xml_structure_metadata(self, xml_path: Union[str, Path]) -> Dict[str, Any]:
        """
        提取XML结构元数据
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            Dict[str, Any]: XML结构元数据字典
        """
        metadata = {}
        
        try:
            xml_path = Path(xml_path)
            
            # 解析XML结构
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                
                metadata.update({
                    'root_tag': root.tag,
                    'element_count': len(list(root.iter())),
                    'encoding': getattr(tree, 'docinfo', {}).get('encoding', 'unknown') if hasattr(tree, 'docinfo') else 'unknown'
                })
                
                # 分析XML层级结构
                max_depth = self._calculate_xml_depth(root)
                metadata['max_depth'] = max_depth
                
                # 统计不同类型的元素
                element_types = {}
                for elem in root.iter():
                    tag = elem.tag
                    element_types[tag] = element_types.get(tag, 0) + 1
                
                metadata['element_types'] = element_types
                metadata['unique_element_count'] = len(element_types)
                
                # 检查根元素有效性
                if root.tag in ['awb_scenario', 'root', 'configuration']:
                    metadata['root_tag_valid'] = True
                else:
                    metadata['root_tag_valid'] = False
                    metadata['root_tag_warning'] = f"根元素名称不常见: {root.tag}"
                
            except ET.ParseError as e:
                metadata['parse_error'] = str(e)
                metadata['is_valid_xml'] = False
                return metadata
            
            metadata['is_valid_xml'] = True
            return metadata
            
        except Exception as e:
            logger.error(f"==liuq debug== 提取XML结构元数据失败: {e}")
            return {"error": f"提取XML结构元数据失败: {e}"}
    
    def extract_content_metadata(self, xml_path: Union[str, Path]) -> Dict[str, Any]:
        """
        提取XML内容元数据
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            Dict[str, Any]: 内容元数据字典
        """
        metadata = {}
        
        try:
            xml_path = Path(xml_path)
            
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 提取版本信息
            version_elem = root.find('.//version')
            if version_elem is not None and version_elem.text:
                metadata['xml_version'] = version_elem.text.strip()
                metadata['version_supported'] = metadata['xml_version'] in self.supported_versions
            else:
                metadata['xml_version'] = 'unknown'
                metadata['version_supported'] = False
            
            # 提取设备信息
            device_elem = root.find('.//device')
            if device_elem is not None and device_elem.text:
                metadata['device_type'] = device_elem.text.strip()
            
            # 提取创建时间
            created_elem = root.find('.//created')
            if created_elem is not None and created_elem.text:
                metadata['xml_created_time'] = created_elem.text.strip()
            
            # 统计Map相关信息
            map_count = self._count_map_elements(root)
            metadata.update(map_count)
            
            # 检查必需元素
            required_elements = ['base_boundary', 'offset_map']
            missing_elements = []
            present_elements = []
            
            for elem_name in required_elements:
                if root.find(f".//{elem_name}") is not None:
                    present_elements.append(elem_name)
                else:
                    missing_elements.append(elem_name)
            
            metadata['required_elements'] = {
                'present': present_elements,
                'missing': missing_elements,
                'all_present': len(missing_elements) == 0
            }
            
            # 分析数据质量
            metadata['data_quality'] = self._analyze_data_quality(root)
            
            return metadata
            
        except ET.ParseError as e:
            return {"error": f"XML格式错误: {e}"}
        except Exception as e:
            logger.error(f"==liuq debug== 提取XML内容元数据失败: {e}")
            return {"error": f"提取内容元数据失败: {e}"}
    
    def extract_complete_metadata(self, xml_path: Union[str, Path]) -> Dict[str, Any]:
        """
        提取完整的XML元数据（整合所有元数据类型）
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            Dict[str, Any]: 完整元数据字典
        """
        try:
            # 提取各类元数据
            file_metadata = self.extract_file_metadata(xml_path)
            structure_metadata = self.extract_xml_structure_metadata(xml_path)
            content_metadata = self.extract_content_metadata(xml_path)
            
            # 整合元数据
            complete_metadata = {
                'extraction_time': datetime.now().isoformat(),
                'source_file': str(Path(xml_path).absolute()),
                'file_info': file_metadata,
                'structure_info': structure_metadata,
                'content_info': content_metadata
            }
            
            # 计算综合评分
            complete_metadata['quality_score'] = self._calculate_quality_score(
                file_metadata, structure_metadata, content_metadata
            )
            
            logger.debug(f"==liuq debug== 完整元数据提取完成: {xml_path}")
            return complete_metadata
            
        except Exception as e:
            logger.error(f"==liuq debug== 提取完整元数据失败: {e}")
            return {
                'extraction_time': datetime.now().isoformat(),
                'source_file': str(Path(xml_path).absolute()),
                'error': f"提取完整元数据失败: {e}"
            }
    
    def _calculate_xml_depth(self, element: ET.Element, current_depth: int = 0) -> int:
        """计算XML元素的最大深度"""
        if len(element) == 0:
            return current_depth
        
        max_child_depth = current_depth
        for child in element:
            child_depth = self._calculate_xml_depth(child, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth
    
    def _count_map_elements(self, root: ET.Element) -> Dict[str, int]:
        """统计Map相关元素数量"""
        counts = {}
        
        # 统计不同类型的Map元素
        map_elements = root.findall('.//Map')
        offset_maps = root.findall('.//offset_map')
        base_boundary = root.findall('.//base_boundary')
        
        counts['map_count'] = len(map_elements)
        counts['offset_map_count'] = len(offset_maps)
        counts['base_boundary_count'] = len(base_boundary)
        counts['total_map_elements'] = len(map_elements) + len(offset_maps)
        
        # 分析offset_map结构
        if offset_maps:
            valid_offset_maps = 0
            empty_offset_maps = 0
            
            for offset_map in offset_maps[:50]:  # 只检查前50个，避免性能问题
                if self._is_valid_offset_map(offset_map):
                    valid_offset_maps += 1
                else:
                    empty_offset_maps += 1
            
            counts['valid_offset_map_count'] = valid_offset_maps
            counts['empty_offset_map_count'] = empty_offset_maps
            
            if len(offset_maps) > 50:
                counts['sample_size'] = 50
                counts['total_offset_maps'] = len(offset_maps)
        
        return counts
    
    def _is_valid_offset_map(self, offset_map: ET.Element) -> bool:
        """检查offset_map是否有效（非空）"""
        try:
            # 检查是否有基本的坐标信息
            x_elements = offset_map.findall('.//x')
            y_elements = offset_map.findall('.//y')
            
            if not x_elements or not y_elements:
                return False
            
            # 检查是否有非零的坐标值
            for x_elem in x_elements:
                if x_elem.text and x_elem.text.strip() != '0':
                    return True
            
            for y_elem in y_elements:
                if y_elem.text and y_elem.text.strip() != '0':
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _analyze_data_quality(self, root: ET.Element) -> Dict[str, Any]:
        """分析数据质量"""
        quality = {
            'has_version': root.find('.//version') is not None,
            'has_device_info': root.find('.//device') is not None,
            'has_creation_time': root.find('.//created') is not None,
            'has_base_boundary': root.find('.//base_boundary') is not None,
            'has_map_data': len(root.findall('.//offset_map')) > 0 or len(root.findall('.//Map')) > 0
        }
        
        # 计算完整性分数
        quality_items = [
            quality['has_version'],
            quality['has_device_info'], 
            quality['has_creation_time'],
            quality['has_base_boundary'],
            quality['has_map_data']
        ]
        
        quality['completeness_score'] = sum(quality_items) / len(quality_items)
        
        # 数据质量等级
        if quality['completeness_score'] >= 0.8:
            quality['quality_level'] = 'excellent'
        elif quality['completeness_score'] >= 0.6:
            quality['quality_level'] = 'good'
        elif quality['completeness_score'] >= 0.4:
            quality['quality_level'] = 'fair'
        else:
            quality['quality_level'] = 'poor'
        
        return quality
    
    def _calculate_quality_score(self, file_metadata: Dict, structure_metadata: Dict, 
                                content_metadata: Dict) -> float:
        """计算综合质量评分"""
        score = 0.0
        max_score = 0.0
        
        try:
            # 文件质量评分 (20%)
            if 'error' not in file_metadata:
                if file_metadata.get('file_status') == 'normal':
                    score += 20
                elif file_metadata.get('file_status') in ['small', 'large']:
                    score += 15
                else:
                    score += 10
            max_score += 20
            
            # XML结构质量评分 (30%)
            if 'error' not in structure_metadata:
                if structure_metadata.get('is_valid_xml', False):
                    score += 15
                    if structure_metadata.get('root_tag_valid', False):
                        score += 10
                    if structure_metadata.get('max_depth', 0) < 10:  # 合理的深度
                        score += 5
                max_score += 30
            
            # 内容质量评分 (50%)
            if 'error' not in content_metadata:
                content_quality = content_metadata.get('data_quality', {})
                completeness = content_quality.get('completeness_score', 0)
                score += completeness * 50
                max_score += 50
            
            # 计算最终分数 (0-100)
            final_score = (score / max_score * 100) if max_score > 0 else 0
            return round(final_score, 2)
            
        except Exception as e:
            logger.warning(f"==liuq debug== 计算质量评分失败: {e}")
            return 0.0


# 全局元数据服务实例
_metadata_service: Optional[XMLMetadataService] = None


def get_xml_metadata_service() -> XMLMetadataService:
    """获取XML元数据服务实例"""
    global _metadata_service
    
    if _metadata_service is None:
        _metadata_service = XMLMetadataService()
        logger.info("==liuq debug== 创建XML元数据服务实例")
    
    return _metadata_service