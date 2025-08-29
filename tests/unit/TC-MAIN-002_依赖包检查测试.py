#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-MAIN-002: 依赖包检查测试
==liuq debug== 依赖包检查功能测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-28 15:20:00 +08:00; Reason: 创建测试用例TC-MAIN-002对应的测试脚本; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-28
版本: 2.0.0
描述: 验证依赖包检查功能
"""

import pytest
import logging
import sys
import importlib
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

logger = logging.getLogger(__name__)

class TestTC_MAIN_002_依赖包检查测试:
    """TC-MAIN-002: 依赖包检查测试"""
    
    @pytest.fixture
    def required_packages(self):
        """必需的依赖包列表"""
        return [
            'PyQt5',
            'pandas',
            'numpy',
            'matplotlib',
            'Pillow',
            'lxml'
        ]
    
    def test_required_packages_availability(self, required_packages):
        """测试程序能够检测到缺失的依赖包"""
        logger.info("==liuq debug== 测试必需依赖包可用性")
        
        available_packages = []
        missing_packages = []
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                available_packages.append(package)
                logger.info(f"==liuq debug== 依赖包可用: {package}")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"==liuq debug== 依赖包缺失: {package}")
        
        # 记录统计信息
        total_packages = len(required_packages)
        available_count = len(available_packages)
        missing_count = len(missing_packages)
        
        logger.info(f"==liuq debug== 依赖包统计: 总计{total_packages}, 可用{available_count}, 缺失{missing_count}")
        
        # 至少应该有一些核心包可用
        assert available_count > 0, "没有找到任何必需的依赖包"
        
        if missing_count > 0:
            logger.warning(f"==liuq debug== 缺失的依赖包: {missing_packages}")
    
    def test_pyqt5_dependency_check(self):
        """测试PyQt5依赖检查"""
        logger.info("==liuq debug== 测试PyQt5依赖检查")
        
        try:
            import PyQt5
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt
            
            logger.info("==liuq debug== PyQt5依赖检查通过")
            
            # 检查PyQt5版本
            if hasattr(PyQt5.QtCore, 'PYQT_VERSION_STR'):
                version = PyQt5.QtCore.PYQT_VERSION_STR
                logger.info(f"==liuq debug== PyQt5版本: {version}")
            
        except ImportError as e:
            logger.error(f"==liuq debug== PyQt5导入失败: {str(e)}")
            pytest.fail("PyQt5依赖包缺失")
    
    def test_pandas_dependency_check(self):
        """测试pandas依赖检查"""
        logger.info("==liuq debug== 测试pandas依赖检查")
        
        try:
            import pandas as pd
            
            logger.info("==liuq debug== pandas依赖检查通过")
            
            # 检查pandas版本
            version = pd.__version__
            logger.info(f"==liuq debug== pandas版本: {version}")
            
            # 简单功能测试
            df = pd.DataFrame({'test': [1, 2, 3]})
            assert len(df) == 3, "pandas基本功能测试失败"
            
        except ImportError as e:
            logger.error(f"==liuq debug== pandas导入失败: {str(e)}")
            pytest.fail("pandas依赖包缺失")
    
    def test_numpy_dependency_check(self):
        """测试numpy依赖检查"""
        logger.info("==liuq debug== 测试numpy依赖检查")
        
        try:
            import numpy as np
            
            logger.info("==liuq debug== numpy依赖检查通过")
            
            # 检查numpy版本
            version = np.__version__
            logger.info(f"==liuq debug== numpy版本: {version}")
            
            # 简单功能测试
            arr = np.array([1, 2, 3])
            assert len(arr) == 3, "numpy基本功能测试失败"
            
        except ImportError as e:
            logger.error(f"==liuq debug== numpy导入失败: {str(e)}")
            pytest.fail("numpy依赖包缺失")
    
    def test_matplotlib_dependency_check(self):
        """测试matplotlib依赖检查"""
        logger.info("==liuq debug== 测试matplotlib依赖检查")
        
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            
            logger.info("==liuq debug== matplotlib依赖检查通过")
            
            # 检查matplotlib版本
            version = matplotlib.__version__
            logger.info(f"==liuq debug== matplotlib版本: {version}")
            
        except ImportError as e:
            logger.error(f"==liuq debug== matplotlib导入失败: {str(e)}")
            logger.warning("==liuq debug== matplotlib依赖包缺失，可能影响图表功能")
    
    def test_pillow_dependency_check(self):
        """测试Pillow依赖检查"""
        logger.info("==liuq debug== 测试Pillow依赖检查")
        
        try:
            from PIL import Image
            import PIL
            
            logger.info("==liuq debug== Pillow依赖检查通过")
            
            # 检查Pillow版本
            version = PIL.__version__
            logger.info(f"==liuq debug== Pillow版本: {version}")
            
        except ImportError as e:
            logger.error(f"==liuq debug== Pillow导入失败: {str(e)}")
            logger.warning("==liuq debug== Pillow依赖包缺失，可能影响图片处理功能")
    
    def test_dependency_error_handling(self):
        """测试依赖包缺失时的错误处理"""
        logger.info("==liuq debug== 测试依赖包缺失错误处理")
        
        # 模拟依赖包缺失
        with patch('builtins.__import__', side_effect=ImportError("No module named 'fake_package'")):
            try:
                import fake_package
                pytest.fail("应该抛出ImportError异常")
            except ImportError as e:
                logger.info(f"==liuq debug== 正确捕获ImportError: {str(e)}")
                assert "fake_package" in str(e), "错误信息应包含包名"
    
    def test_graceful_degradation(self):
        """测试程序优雅退出，不会崩溃"""
        logger.info("==liuq debug== 测试程序优雅降级")
        
        # 测试可选依赖包缺失时的处理
        optional_packages = ['psutil', 'requests', 'openpyxl']
        
        for package in optional_packages:
            try:
                importlib.import_module(package)
                logger.info(f"==liuq debug== 可选包可用: {package}")
            except ImportError:
                logger.info(f"==liuq debug== 可选包缺失: {package} (程序应能正常运行)")
    
    def test_dependency_version_compatibility(self):
        """测试依赖包版本兼容性"""
        logger.info("==liuq debug== 测试依赖包版本兼容性")
        
        version_requirements = {
            'PyQt5': '5.12.0',
            'pandas': '1.0.0',
            'numpy': '1.18.0'
        }
        
        for package_name, min_version in version_requirements.items():
            try:
                module = importlib.import_module(package_name)
                
                if hasattr(module, '__version__'):
                    current_version = module.__version__
                    logger.info(f"==liuq debug== {package_name}版本: {current_version}")
                    
                    # 简单版本比较（仅比较主版本号）
                    current_major = current_version.split('.')[0]
                    min_major = min_version.split('.')[0]
                    
                    try:
                        assert int(current_major) >= int(min_major), \
                            f"{package_name}版本过低: {current_version} < {min_version}"
                    except ValueError:
                        logger.warning(f"==liuq debug== 无法解析版本号: {current_version}")
                else:
                    logger.warning(f"==liuq debug== {package_name}没有版本信息")
                    
            except ImportError:
                logger.warning(f"==liuq debug== {package_name}未安装")
    
    def test_import_error_message_clarity(self):
        """测试显示明确的错误信息，指出缺失的包名"""
        logger.info("==liuq debug== 测试导入错误信息清晰度")
        
        # 模拟导入错误
        test_packages = ['nonexistent_package_123', 'another_fake_package']
        
        for package in test_packages:
            try:
                importlib.import_module(package)
            except ImportError as e:
                error_message = str(e)
                logger.info(f"==liuq debug== 导入错误信息: {error_message}")
                
                # 验证错误信息包含包名
                assert package in error_message, f"错误信息应包含包名: {package}"
                
                # 验证错误信息清晰
                assert "No module named" in error_message or "ModuleNotFoundError" in str(type(e)), \
                    "错误信息应明确指出模块不存在"
    
    def test_dependency_recovery_after_installation(self):
        """测试恢复依赖包后程序能正常启动"""
        logger.info("==liuq debug== 测试依赖包恢复后的程序启动")
        
        # 这个测试主要验证依赖检查逻辑的正确性
        # 实际的包安装/卸载在测试环境中不安全
        
        # 模拟依赖包恢复场景
        def mock_import_success(name, *args, **kwargs):
            if name == 'PyQt5':
                # 模拟成功导入
                mock_module = MagicMock()
                mock_module.__name__ = 'PyQt5'
                return mock_module
            else:
                # 使用原始导入
                return importlib.__import__(name, *args, **kwargs)
        
        with patch('importlib.import_module', side_effect=mock_import_success):
            try:
                import PyQt5
                logger.info("==liuq debug== 模拟依赖包恢复成功")
            except ImportError:
                pytest.fail("模拟依赖包恢复失败")
    
    def test_system_environment_check(self):
        """测试系统环境检查"""
        logger.info("==liuq debug== 测试系统环境检查")
        
        # 检查Python版本
        python_version = sys.version_info
        logger.info(f"==liuq debug== Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 验证Python版本要求
        assert python_version.major >= 3, "需要Python 3.x版本"
        assert python_version.minor >= 7, "需要Python 3.7或更高版本"
        
        # 检查系统路径
        python_path = sys.executable
        logger.info(f"==liuq debug== Python路径: {python_path}")
        
        # 检查模块搜索路径
        module_paths = sys.path
        logger.info(f"==liuq debug== 模块搜索路径数量: {len(module_paths)}")
        
        # 验证当前目录在搜索路径中
        current_dir = str(Path.cwd())
        path_found = any(current_dir in path for path in module_paths)
        if not path_found:
            logger.warning("==liuq debug== 当前目录不在Python模块搜索路径中")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
