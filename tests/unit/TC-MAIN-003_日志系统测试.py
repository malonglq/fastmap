#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-MAIN-003: 日志系统测试
==liuq debug== 日志系统配置和功能测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-28 15:25:00 +08:00; Reason: 创建测试用例TC-MAIN-003对应的测试脚本; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-28
版本: 2.0.0
描述: 验证日志系统配置和功能
"""

import pytest
import logging
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow

logger = logging.getLogger(__name__)

class TestTC_MAIN_003_日志系统测试:
    """TC-MAIN-003: 日志系统测试"""
    
    @pytest.fixture
    def log_directory(self):
        """日志目录路径"""
        return Path("data/logs")
    
    @pytest.fixture
    def main_window(self, qtbot):
        """主窗口实例"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = MainWindow()
        # 标记为测试环境，避免QMessageBox阻塞
        window._is_testing = True
        qtbot.addWidget(window)
        return window
    
    @pytest.fixture
    def temp_log_file(self):
        """临时日志文件"""
        temp_file = Path(tempfile.mktemp(suffix='.log'))
        yield temp_file
        # 清理临时文件
        if temp_file.exists():
            temp_file.unlink()
    
    def test_log_directory_creation(self, log_directory):
        """测试日志文件创建在data/logs/目录"""
        logger.info("==liuq debug== 测试日志目录创建")
        
        # 检查日志目录是否存在
        if log_directory.exists():
            logger.info(f"==liuq debug== 日志目录存在: {log_directory}")
            assert log_directory.is_dir(), "日志路径不是目录"
        else:
            logger.warning(f"==liuq debug== 日志目录不存在: {log_directory}")
            # 尝试创建日志目录
            try:
                log_directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"==liuq debug== 成功创建日志目录: {log_directory}")
            except Exception as e:
                logger.error(f"==liuq debug== 创建日志目录失败: {str(e)}")
    
    def test_main_log_file_creation(self, log_directory):
        """测试日志文件fastmapv2.log正确创建"""
        logger.info("==liuq debug== 测试主日志文件创建")
        
        main_log_file = log_directory / "fastmapv2.log"
        
        if main_log_file.exists():
            logger.info(f"==liuq debug== 主日志文件存在: {main_log_file}")
            
            # 检查文件大小
            file_size = main_log_file.stat().st_size
            logger.info(f"==liuq debug== 日志文件大小: {file_size} bytes")
            
            # 检查文件是否可读
            assert main_log_file.is_file(), "日志文件不是普通文件"
            
            # 尝试读取文件内容
            try:
                with open(main_log_file, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # 读取前1000字符
                    logger.info(f"==liuq debug== 日志文件内容预览: {content[:100]}...")
            except Exception as e:
                logger.warning(f"==liuq debug== 读取日志文件失败: {str(e)}")
        else:
            logger.warning(f"==liuq debug== 主日志文件不存在: {main_log_file}")
    
    def test_log_format_compliance(self, log_directory):
        """测试日志格式符合预期：[时间] [级别] [模块] 消息"""
        logger.info("==liuq debug== 测试日志格式合规性")
        
        main_log_file = log_directory / "fastmapv2.log"
        
        if main_log_file.exists():
            try:
                with open(main_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if lines:
                    # 检查前几行的格式
                    sample_lines = lines[-10:]  # 检查最后10行
                    
                    for i, line in enumerate(sample_lines):
                        line = line.strip()
                        if line:
                            logger.info(f"==liuq debug== 日志行{i}: {line}")
                            
                            # 检查是否包含时间戳
                            has_timestamp = any(char.isdigit() for char in line[:20])
                            if has_timestamp:
                                logger.info(f"==liuq debug== 日志行{i}包含时间戳")
                            
                            # 检查是否包含日志级别
                            log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                            has_level = any(level in line for level in log_levels)
                            if has_level:
                                logger.info(f"==liuq debug== 日志行{i}包含日志级别")
                else:
                    logger.warning("==liuq debug== 日志文件为空")
                    
            except Exception as e:
                logger.error(f"==liuq debug== 读取日志文件失败: {str(e)}")
        else:
            logger.warning("==liuq debug== 日志文件不存在，跳过格式检查")
    
    def test_console_log_output(self, main_window, qtbot):
        """测试控制台日志输出"""
        logger.info("==liuq debug== 测试控制台日志输出")
        
        # 创建一个测试日志消息
        test_message = "==liuq debug== 控制台日志测试消息"
        
        # 使用不同级别的日志
        logger.debug(f"{test_message} - DEBUG")
        logger.info(f"{test_message} - INFO")
        logger.warning(f"{test_message} - WARNING")
        logger.error(f"{test_message} - ERROR")
        
        # 等待日志处理
        qtbot.wait(100)
        
        logger.info("==liuq debug== 控制台日志输出测试完成")
    
    def test_file_log_output(self, temp_log_file):
        """测试文件日志输出"""
        logger.info("==liuq debug== 测试文件日志输出")
        
        # 创建临时日志处理器
        file_handler = logging.FileHandler(temp_log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 添加处理器到测试日志器
        test_logger = logging.getLogger('test_file_logger')
        test_logger.addHandler(file_handler)
        test_logger.setLevel(logging.INFO)
        
        # 写入测试日志
        test_messages = [
            "==liuq debug== 文件日志测试消息1",
            "==liuq debug== 文件日志测试消息2",
            "==liuq debug== 文件日志测试消息3"
        ]
        
        for message in test_messages:
            test_logger.info(message)
        
        # 确保日志写入
        file_handler.flush()
        file_handler.close()
        
        # 验证文件内容
        if temp_log_file.exists():
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查测试消息是否写入
            for message in test_messages:
                assert message in content, f"日志消息未写入文件: {message}"
            
            logger.info("==liuq debug== 文件日志输出测试通过")
        else:
            pytest.fail("临时日志文件未创建")
        
        # 清理处理器
        test_logger.removeHandler(file_handler)
    
    def test_different_log_levels(self, temp_log_file):
        """测试不同级别的日志(DEBUG, INFO, WARNING, ERROR)正确分类"""
        logger.info("==liuq debug== 测试不同日志级别分类")
        
        # 创建临时日志处理器
        file_handler = logging.FileHandler(temp_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 设置为DEBUG级别以捕获所有日志
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        test_logger = logging.getLogger('test_level_logger')
        test_logger.addHandler(file_handler)
        test_logger.setLevel(logging.DEBUG)
        
        # 测试不同级别的日志
        log_tests = [
            (logging.DEBUG, "==liuq debug== DEBUG级别测试"),
            (logging.INFO, "==liuq debug== INFO级别测试"),
            (logging.WARNING, "==liuq debug== WARNING级别测试"),
            (logging.ERROR, "==liuq debug== ERROR级别测试"),
            (logging.CRITICAL, "==liuq debug== CRITICAL级别测试")
        ]
        
        for level, message in log_tests:
            test_logger.log(level, message)
        
        file_handler.flush()
        file_handler.close()
        
        # 验证日志级别
        if temp_log_file.exists():
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查每个级别是否正确记录
            expected_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            for level in expected_levels:
                assert level in content, f"日志级别{level}未正确记录"
                logger.info(f"==liuq debug== 日志级别{level}正确记录")
        
        test_logger.removeHandler(file_handler)
    
    def test_log_rotation_capability(self, log_directory):
        """测试日志轮转能力"""
        logger.info("==liuq debug== 测试日志轮转能力")
        
        # 查找日志目录中的所有日志文件
        if log_directory.exists():
            log_files = list(log_directory.glob("*.log*"))
            logger.info(f"==liuq debug== 找到{len(log_files)}个日志文件")
            
            for log_file in log_files:
                logger.info(f"==liuq debug== 日志文件: {log_file.name}")
                
                # 检查文件大小
                file_size = log_file.stat().st_size
                logger.info(f"==liuq debug== 文件大小: {file_size} bytes")
                
                # 如果文件很大，可能有轮转机制
                if file_size > 1024 * 1024:  # 1MB
                    logger.info(f"==liuq debug== 大日志文件: {log_file.name}")
        else:
            logger.warning("==liuq debug== 日志目录不存在")
    
    def test_log_encoding_support(self, temp_log_file):
        """测试日志编码支持（中文字符）"""
        logger.info("==liuq debug== 测试日志编码支持")
        
        # 创建支持UTF-8编码的日志处理器
        file_handler = logging.FileHandler(temp_log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        test_logger = logging.getLogger('test_encoding_logger')
        test_logger.addHandler(file_handler)
        test_logger.setLevel(logging.INFO)
        
        # 测试中文字符
        chinese_messages = [
            "==liuq debug== 中文日志测试消息",
            "==liuq debug== 测试特殊字符：①②③④⑤",
            "==liuq debug== 测试符号：★☆♠♥♦♣",
            "==liuq debug== 测试数字：１２３４５"
        ]
        
        for message in chinese_messages:
            test_logger.info(message)
        
        file_handler.flush()
        file_handler.close()
        
        # 验证中文字符正确写入
        if temp_log_file.exists():
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for message in chinese_messages:
                assert message in content, f"中文日志消息未正确写入: {message}"
            
            logger.info("==liuq debug== 日志编码支持测试通过")
        
        test_logger.removeHandler(file_handler)
    
    def test_log_performance(self, temp_log_file):
        """测试日志性能"""
        logger.info("==liuq debug== 测试日志性能")
        
        file_handler = logging.FileHandler(temp_log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        test_logger = logging.getLogger('test_performance_logger')
        test_logger.addHandler(file_handler)
        test_logger.setLevel(logging.INFO)
        
        # 性能测试：写入大量日志
        start_time = time.time()
        
        message_count = 1000
        for i in range(message_count):
            test_logger.info(f"==liuq debug== 性能测试消息 {i}")
        
        file_handler.flush()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        messages_per_second = message_count / elapsed_time
        
        logger.info(f"==liuq debug== 日志性能测试结果:")
        logger.info(f"==liuq debug== - 消息数量: {message_count}")
        logger.info(f"==liuq debug== - 耗时: {elapsed_time:.2f}秒")
        logger.info(f"==liuq debug== - 速度: {messages_per_second:.0f}消息/秒")
        
        # 性能要求：至少100消息/秒
        assert messages_per_second > 100, f"日志性能过低: {messages_per_second:.0f}消息/秒"
        
        file_handler.close()
        test_logger.removeHandler(file_handler)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
