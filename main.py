#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastMapV2 - 对比机Map分析&仿写工具
==liuq debug== 主程序入口文件

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 17:42:00 +08:00; Reason: P1-LD-005 建立PyQt主窗口框架; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 2.0.0
描述: 基于PyQt的桌面应用程序，用于分析对比机和调试机的Map配置差异
"""

import sys
import os
import logging
from pathlib import Path

# 确保matplotlib使用正确的后端
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
def setup_logging():
    """配置日志系统"""
    log_dir = project_root / 'data' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'fastmapv2.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("==liuq debug== FastMapV2 日志系统初始化完成")
    return logger


def check_dependencies():
    """检查必要的依赖包是否已安装"""
    required_packages = [
        'PyQt5',
        'pandas',
        'numpy',
        'matplotlib',
        'jinja2',
        'chardet'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"==liuq debug== 依赖包 {package} 检查通过")
        except ImportError:
            missing_packages.append(package)
            print(f"==liuq debug== 缺少依赖包: {package}")
    
    if missing_packages:
        error_msg = f"缺少以下依赖包: {', '.join(missing_packages)}\n"
        error_msg += "请运行: pip install -r requirements.txt"
        return False, error_msg
    
    return True, "所有依赖包检查通过"


def create_application():
    """创建QApplication实例"""
    app = QApplication(sys.argv)
    app.setApplicationName("FastMapV2")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("龙sir团队")
    
    # 设置应用程序属性
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    return app


def main():
    """主程序入口函数"""
    # 设置日志
    logger = setup_logging()
    
    try:
        logger.info("==liuq debug== FastMapV2 应用程序启动")
        
        # 检查依赖
        deps_ok, deps_msg = check_dependencies()
        if not deps_ok:
            print(f"==liuq debug== 依赖检查失败: {deps_msg}")
            # 如果PyQt5可用，显示错误对话框
            try:
                app = create_application()
                QMessageBox.critical(None, "依赖检查失败", deps_msg)
            except:
                pass
            sys.exit(1)
        
        logger.info("==liuq debug== 依赖检查通过")
        
        # 创建应用程序
        app = create_application()
        logger.info("==liuq debug== QApplication创建成功")
        
        # 导入主窗口（延迟导入，确保依赖检查通过）
        try:
            from gui.main_window import MainWindow
            logger.info("==liuq debug== 主窗口模块导入成功")
        except ImportError as e:
            logger.error(f"==liuq debug== 主窗口模块导入失败: {e}")
            QMessageBox.critical(None, "程序错误", f"主窗口模块导入失败: {e}")
            sys.exit(1)
        
        # 配置依赖注入容器
        try:
            from core.infrastructure.di_container import configure_services
            configure_services()
            logger.info("==liuq debug== 依赖注入容器配置成功")
        except Exception as e:
            logger.error(f"==liuq debug== 配置依赖注入容器失败: {e}")
            QMessageBox.critical(None, "程序错误", f"配置依赖注入容器失败: {e}")
            sys.exit(1)
        
        # 创建主窗口
        try:
            main_window = MainWindow()
            main_window.show()
            logger.info("==liuq debug== 主窗口创建并显示成功")
        except Exception as e:
            logger.error(f"==liuq debug== 主窗口创建失败: {e}")
            QMessageBox.critical(None, "程序错误", f"主窗口创建失败: {e}")
            sys.exit(1)
        
        # 启动应用程序主循环
        logger.info("==liuq debug== 启动应用程序主循环")
        exit_code = app.exec_()
        
        logger.info(f"==liuq debug== 应用程序退出，退出码: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"==liuq debug== 应用程序启动失败: {e}")
        try:
            QMessageBox.critical(None, "严重错误", f"应用程序启动失败: {e}")
        except:
            print(f"严重错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
