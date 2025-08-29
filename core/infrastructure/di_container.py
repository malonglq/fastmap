#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入容器
==liuq debug== FastMapV2依赖注入容器

作者: 龙sir团队
创建时间: 2025-08-22
版本: 1.0.0
描述: 管理服务依赖关系，支持单例和瞬态服务注册
"""

import logging
from typing import Type, TypeVar, Dict, Any, Callable, Optional
from enum import Enum
import inspect
import threading

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """服务生命周期枚举"""
    SINGLETON = "singleton"  # 单例：整个应用生命周期内只有一个实例
    TRANSIENT = "transient"  # 瞬态：每次请求都创建新实例
    SCOPED = "scoped"       # 作用域：在特定作用域内为单例（预留）


class ServiceDescriptor:
    """服务描述符"""
    
    def __init__(self, service_type: Type, implementation: Type, lifetime: ServiceLifetime):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.instance = None


class DIContainer:
    """
    依赖注入容器
    
    支持功能：
    - 服务注册（单例/瞬态）
    - 自动依赖解析
    - 循环依赖检测
    - 线程安全
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._resolving: set = set()  # 用于检测循环依赖
        self._lock = threading.RLock()  # 线程安全锁
        
        logger.info("==liuq debug== 依赖注入容器初始化完成")
    
    def register_singleton(self, service_type: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """
        注册单例服务
        
        Args:
            service_type: 服务接口类型
            implementation: 具体实现类型，如果为None则使用service_type
        """
        return self._register(service_type, implementation or service_type, ServiceLifetime.SINGLETON)
    
    def register_transient(self, service_type: Type[T], implementation: Type[T] = None) -> 'DIContainer':
        """
        注册瞬态服务
        
        Args:
            service_type: 服务接口类型
            implementation: 具体实现类型，如果为None则使用service_type
        """
        return self._register(service_type, implementation or service_type, ServiceLifetime.TRANSIENT)
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """
        注册服务实例
        
        Args:
            service_type: 服务类型
            instance: 服务实例
        """
        with self._lock:
            descriptor = ServiceDescriptor(service_type, type(instance), ServiceLifetime.SINGLETON)
            descriptor.instance = instance
            self._services[service_type] = descriptor
            
            logger.debug(f"==liuq debug== 注册服务实例: {service_type.__name__}")
            return self
    
    def _register(self, service_type: Type, implementation: Type, lifetime: ServiceLifetime) -> 'DIContainer':
        """内部注册方法"""
        with self._lock:
            descriptor = ServiceDescriptor(service_type, implementation, lifetime)
            self._services[service_type] = descriptor
            
            logger.debug(f"==liuq debug== 注册服务: {service_type.__name__} -> {implementation.__name__} ({lifetime.value})")
            return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        解析服务实例
        
        Args:
            service_type: 要解析的服务类型
            
        Returns:
            服务实例
            
        Raises:
            ValueError: 当服务未注册或存在循环依赖时
        """
        with self._lock:
            # 检查循环依赖
            if service_type in self._resolving:
                raise ValueError(f"检测到循环依赖: {service_type.__name__}")
            
            # 检查服务是否已注册
            if service_type not in self._services:
                raise ValueError(f"服务未注册: {service_type.__name__}")
            
            descriptor = self._services[service_type]
            
            # 单例模式：返回已存在的实例
            if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.instance is not None:
                return descriptor.instance
            
            # 创建新实例
            try:
                self._resolving.add(service_type)
                instance = self._create_instance(descriptor)
                
                # 单例模式：缓存实例
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    descriptor.instance = instance
                
                logger.debug(f"==liuq debug== 解析服务成功: {service_type.__name__}")
                return instance
                
            finally:
                self._resolving.discard(service_type)
    
    def _create_instance(self, descriptor: ServiceDescriptor):
        """创建服务实例"""
        implementation = descriptor.implementation
        
        # 获取构造函数参数
        try:
            signature = inspect.signature(implementation.__init__)
            parameters = list(signature.parameters.values())[1:]  # 跳过self参数
            
            # 解析构造函数依赖
            args = []
            for param in parameters:
                if param.annotation != inspect.Parameter.empty:
                    # 检查类型注解是否为字符串或不支持的类型
                    if isinstance(param.annotation, str):
                        logger.warning(f"==liuq debug== 跳过字符串类型注解: {param.name} in {implementation.__name__}")
                        continue
                    
                    # 检查是否为泛型类型（如Optional、List等）
                    if hasattr(param.annotation, '__origin__'):
                        logger.warning(f"==liuq debug== 跳过泛型类型注解: {param.name} in {implementation.__name__}")
                        continue
                    
                    try:
                        # 递归解析依赖
                        dependency = self.resolve(param.annotation)
                        args.append(dependency)
                    except Exception as e:
                        logger.warning(f"==liuq debug== 无法解析依赖: {param.name} ({param.annotation}) in {implementation.__name__}, 错误: {e}")
                        # 如果有默认值，使用默认值
                        if param.default != inspect.Parameter.empty:
                            args.append(param.default)
                        # 否则跳过该参数
                else:
                    # 如果没有类型注解，尝试使用默认值
                    if param.default != inspect.Parameter.empty:
                        args.append(param.default)
                    else:
                        logger.warning(f"==liuq debug== 参数缺少类型注解: {param.name} in {implementation.__name__}")
            
            # 创建实例
            instance = implementation(*args)
            logger.debug(f"==liuq debug== 创建实例: {implementation.__name__} with {len(args)} dependencies")
            return instance
            
        except Exception as e:
            logger.error(f"==liuq debug== 创建实例失败: {implementation.__name__}, 错误: {e}")
            raise ValueError(f"无法创建服务实例 {implementation.__name__}: {e}")
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        with self._lock:
            return service_type in self._services
    
    def get_registered_services(self) -> Dict[str, str]:
        """获取已注册的服务信息"""
        with self._lock:
            return {
                service_type.__name__: f"{descriptor.implementation.__name__} ({descriptor.lifetime.value})"
                for service_type, descriptor in self._services.items()
            }
    
    def clear(self):
        """清空所有注册的服务"""
        with self._lock:
            self._services.clear()
            self._resolving.clear()
            logger.info("==liuq debug== 依赖注入容器已清空")


# 全局容器实例
_global_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_container() -> DIContainer:
    """获取全局容器实例（单例模式）"""
    global _global_container
    
    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = DIContainer()
                logger.info("==liuq debug== 创建全局依赖注入容器")
    
    return _global_container


def configure_services() -> DIContainer:
    """配置服务注册"""
    container = get_container()
    
    # 注册共享服务
    from core.services.shared import DataBindingManagerImpl, FieldRegistryService, FieldEditorFactory
    container.register_singleton(DataBindingManagerImpl)
    container.register_singleton(FieldRegistryService)
    container.register_singleton(FieldEditorFactory)
    
    # 注册Map分析服务
    from core.services.map_analysis import XMLParserService, XMLWriterService
    # MapAnalyzer、TemperatureSpanAnalyzer、MultiDimensionalAnalyzer需要特定参数，不在DI中注册
    container.register_singleton(XMLParserService)
    container.register_singleton(XMLWriterService)
    
    # 注册EXIF处理服务
    from core.services.exif_processing import ExifParserService, ExifCsvExporter, ExifRawExporter
    from core.services.exif_processing import ImageExportService, ImageExportWorkflowService
    container.register_singleton(ExifParserService)
    container.register_singleton(ExifCsvExporter)
    container.register_singleton(ExifRawExporter)
    container.register_singleton(ImageExportService)
    container.register_singleton(ImageExportWorkflowService)
    
    # 注册报告生成服务
    from core.services.reporting import UnifiedReportManager, UniversalHTMLGenerator, UniversalChartGenerator
    from core.services.reporting import ExifComparisonReportGenerator, MapMultiDimensionalReportGenerator
    container.register_singleton(UnifiedReportManager)
    container.register_singleton(UniversalHTMLGenerator)
    container.register_singleton(UniversalChartGenerator)
    container.register_singleton(ExifComparisonReportGenerator)
    container.register_singleton(MapMultiDimensionalReportGenerator)
    
    # 注册特征点服务
    from core.services.feature_points import ImageClassifierService
    container.register_singleton(ImageClassifierService)
    
    logger.info("==liuq debug== 服务配置完成")
    return container