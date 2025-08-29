#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest配置文件
==liuq debug== 测试配置和fixture定义
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['PYTEST_CURRENT_TEST'] = 'true'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# 强制使用PyQt5，避免版本冲突
import sys
if 'PyQt6' in sys.modules:
    # 如果已经导入了PyQt6，先清除
    for module in list(sys.modules.keys()):
        if 'PyQt6' in module:
            del sys.modules[module]

# 确保使用PyQt5
from PyQt5.QtWidgets import QApplication

# 全局测试状态管理
_test_patches = []
_test_container = None

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """自动设置测试环境"""
    print("==liuq debug== 自动设置测试环境")

    global _test_patches, _test_container

    try:
        # 创建测试专用的DI容器
        _test_container = create_test_container()

        # 使用patch替换全局容器
        container_patch = patch('core.infrastructure.di_container.get_container', return_value=_test_container)
        global_container_patch = patch('core.infrastructure.di_container._global_container', _test_container)

        container_patch.start()
        global_container_patch.start()
        _test_patches.extend([container_patch, global_container_patch])

        # 设置Qt应用程序
        setup_qt_application()

        # 模拟ViewModel工厂
        vm_patches = setup_mock_viewmodel_factories()
        _test_patches.extend(vm_patches)

        print("==liuq debug== 测试环境设置完成")

        yield

    finally:
        # 清理测试环境
        cleanup_test_environment()

def create_test_container():
    """创建测试专用的DI容器"""
    try:
        from core.infrastructure.di_container import DIContainer

        # 创建新的测试容器
        test_container = DIContainer()

        # 注册模拟服务
        register_mock_services(test_container)

        print("==liuq debug== 测试容器创建完成")
        return test_container

    except Exception as e:
        print(f"==liuq debug== 创建测试容器失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 返回一个基本的容器
        from core.infrastructure.di_container import DIContainer
        return DIContainer()

def register_mock_services(container):
    """注册模拟服务到容器"""
    try:
        # 创建XML解析服务的模拟实例
        mock_xml_parser = Mock()
        mock_xml_parser.parse_xml = Mock(return_value={"test": "data"})
        mock_xml_parser.load_xml_file = Mock(return_value=True)
        mock_xml_parser.get_map_points = Mock(return_value=[])

        # 创建EXIF解析服务的模拟实例
        mock_exif_parser = Mock()
        mock_exif_parser.parse_exif_data = Mock(return_value={"Make": "Test", "Model": "Test"})
        # 创建模拟的解析记录
        mock_record1 = Mock()
        mock_record1.image_path = "/mock/test/image1.jpg"
        mock_record1.image_name = "image1.jpg"
        mock_record1.raw_flat = {"meta_data_currentFrame_ctemp": 5000, "face_info_lux_index": 100}

        mock_record2 = Mock()
        mock_record2.image_path = "/mock/test/image2.jpg"
        mock_record2.image_name = "image2.jpg"
        mock_record2.raw_flat = {"meta_data_outputCtemp": 4800, "color_sensor_sensorCct": 5200}

        mock_records = [mock_record1, mock_record2]
        mock_available_keys = [
            "meta_data_currentFrame_ctemp", "meta_data_outputCtemp", "meta_data_awb_gain_r_gain",
            "meta_data_awb_gain_g_gain", "meta_data_awb_gain_b_gain", "meta_data_exposure_time",
            "face_info_lux_index", "face_info_face_count", "color_sensor_sensorCct",
            "ealgo_data_ae_target", "stats_weight_center_weight"
        ]
        mock_errors = []
        mock_exif_parser.parse_directory = Mock(return_value=(mock_records, mock_available_keys, mock_errors))
        mock_exif_parser.init_dll_compatibility = Mock(return_value=True)
        mock_exif_parser._read_raw_exif = Mock(return_value={"test": "exif_data"})

        # 创建报告生成器的模拟实例
        mock_report_generator = Mock()
        mock_report_generator.generate_report = Mock(return_value="<html>Test Report</html>")

        # 创建CSV导出器的模拟实例
        mock_csv_exporter = Mock()
        mock_csv_exporter.export_to_csv = Mock(return_value="/tmp/test.csv")

        # 注册服务到容器 - 使用具体类而不是接口
        try:
            # 注册XML解析服务
            from core.services.map_analysis.xml_parser_service import XMLParserService
            container.register_instance(XMLParserService, mock_xml_parser)

            # 也注册接口版本（如果存在）
            try:
                from core.interfaces.xml_parser_service import IXMLParserService
                container.register_instance(IXMLParserService, mock_xml_parser)
            except ImportError:
                pass
        except ImportError:
            print("==liuq debug== XMLParserService导入失败")

        try:
            # 注册EXIF解析服务
            from core.services.exif_processing.exif_parser_service import ExifParserService
            container.register_instance(ExifParserService, mock_exif_parser)

            # 也注册接口版本（如果存在）
            try:
                from core.interfaces.exif_parser_service import IExifParserService
                container.register_instance(IExifParserService, mock_exif_parser)
            except ImportError:
                pass
        except ImportError:
            print("==liuq debug== ExifParserService导入失败")

        try:
            from core.interfaces.report_generator import IReportGenerator
            container.register_instance(IReportGenerator, mock_report_generator)
        except ImportError:
            print("==liuq debug== IReportGenerator导入失败")

        try:
            from core.services.exif_processing import ExifCsvExporter
            container.register_instance(ExifCsvExporter, mock_csv_exporter)
        except ImportError:
            print("==liuq debug== ExifCsvExporter导入失败")

        # 注册其他必要的服务
        try:
            from core.services.shared.data_binding_manager import DataBindingManagerImpl
            mock_data_binding = Mock()
            container.register_instance(DataBindingManagerImpl, mock_data_binding)
        except ImportError:
            print("==liuq debug== DataBindingManagerImpl导入失败")

        try:
            from core.services.shared.field_registry_service import FieldRegistryService
            mock_field_registry = Mock()
            container.register_instance(FieldRegistryService, mock_field_registry)
        except ImportError:
            print("==liuq debug== FieldRegistryService导入失败")

        print("==liuq debug== 模拟服务注册完成")

    except Exception as e:
        print(f"==liuq debug== 注册模拟服务失败: {str(e)}")
        import traceback
        traceback.print_exc()

def setup_qt_application():
    """设置Qt应用程序"""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            app.setQuitOnLastWindowClosed(False)

        print("==liuq debug== Qt应用程序设置完成")

    except Exception as e:
        print(f"==liuq debug== 设置Qt应用程序失败: {str(e)}")

def setup_mock_viewmodel_factories():
    """设置模拟ViewModel工厂"""
    patches = []

    try:
        # 创建模拟ViewModel
        mock_viewmodel = Mock()
        mock_viewmodel.status_message = Mock()
        mock_viewmodel.progress_value = Mock()
        mock_viewmodel.is_busy = Mock()
        mock_viewmodel.xml_file_loaded = Mock()
        mock_viewmodel.status_message_changed = Mock()
        mock_viewmodel.cleanup = Mock()
        mock_viewmodel.disconnect = Mock()

        # 创建模拟Tab管理器
        mock_tab_manager = Mock()
        mock_tab_manager.cleanup = Mock()
        mock_tab_manager.disconnect = Mock()

        # 使用patch替换工厂函数
        vm_patch = patch('gui.view_models.main_window_view_model.get_main_window_viewmodel',
                        return_value=mock_viewmodel)
        tcm_patch = patch('gui.managers.tab_communication_manager.get_tab_communication_manager',
                         return_value=mock_tab_manager)

        vm_patch.start()
        tcm_patch.start()
        patches.extend([vm_patch, tcm_patch])

        print("==liuq debug== ViewModel工厂配置完成")

    except Exception as e:
        print(f"==liuq debug== 设置ViewModel工厂失败: {str(e)}")

    return patches

def cleanup_test_environment():
    """清理测试环境"""
    global _test_patches, _test_container

    try:
        print("==liuq debug== 开始清理测试环境")

        # 停止所有patch
        for p in _test_patches:
            try:
                p.stop()
            except:
                pass

        _test_patches.clear()
        _test_container = None

        print("==liuq debug== 测试环境清理完成")
    except Exception as e:
        print(f"==liuq debug== 清理测试环境失败: {str(e)}")

@pytest.fixture(scope="session")
def qapp():
    """Session级别的QApplication fixture"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        app.setQuitOnLastWindowClosed(False)
    yield app

@pytest.fixture
def qtbot(qapp, qtbot):
    """增强的qtbot fixture"""
    return qtbot

@pytest.fixture
def main_window(qtbot):
    """统一的主窗口fixture，用于所有GUI测试（完全模拟版本）"""
    # 在测试环境中，我们完全使用模拟对象，避免真实GUI初始化导致的问题
    print("==liuq debug== 创建模拟主窗口")

    # 直接创建模拟窗口，不尝试创建真实窗口
    mock_window = Mock()
    mock_window._is_testing = True

    # 模拟窗口基本属性
    mock_window.windowTitle = Mock(return_value="FastMapV2 - 对比机Map分析&仿写工具 v2.0.0")
    mock_window.setWindowTitle = Mock()
    mock_window.isVisible = Mock(return_value=True)
    mock_window.isMaximized = Mock(return_value=False)

    # 使用变量来跟踪窗口状态
    window_state = {"minimized": False, "maximized": False, "visible": True}

    def set_minimized():
        window_state["minimized"] = True
        window_state["maximized"] = False
        window_state["visible"] = False

    def set_maximized():
        window_state["minimized"] = False
        window_state["maximized"] = True
        window_state["visible"] = True

    def set_normal():
        window_state["minimized"] = False
        window_state["maximized"] = False
        window_state["visible"] = True

    mock_window.isMinimized = Mock(side_effect=lambda: window_state["minimized"])
    mock_window.isMaximized = Mock(side_effect=lambda: window_state["maximized"])
    mock_window.isVisible = Mock(side_effect=lambda: window_state["visible"])
    mock_window.showMinimized = Mock(side_effect=set_minimized)
    mock_window.showMaximized = Mock(side_effect=set_maximized)
    mock_window.showNormal = Mock(side_effect=set_normal)
    mock_window.show = Mock(side_effect=set_normal)
    mock_window.close = Mock()
    mock_window.resize = Mock()
    mock_window.setMinimumSize = Mock()
    mock_window.setAttribute = Mock()

    # 模拟窗口尺寸
    mock_size = Mock()
    mock_size.width = Mock(return_value=1400)
    mock_size.height = Mock(return_value=900)
    mock_window.size = Mock(return_value=mock_size)

    mock_min_size = Mock()
    mock_min_size.width = Mock(return_value=1200)
    mock_min_size.height = Mock(return_value=800)
    mock_window.minimumSize = Mock(return_value=mock_min_size)

    # 模拟菜单栏
    mock_menu_bar = Mock()
    mock_window.menuBar = Mock(return_value=mock_menu_bar)

    # 模拟状态栏
    mock_status_bar = Mock()
    mock_status_bar.showMessage = Mock()
    mock_window.statusBar = Mock(return_value=mock_status_bar)

    # 模拟标签页控件
    mock_tab_widget = Mock()
    mock_tab_widget.count = Mock(return_value=5)

    # 使用一个变量来跟踪当前标签页索引
    current_tab_index = [0]  # 使用列表以便在闭包中修改

    def set_current_index(index):
        current_tab_index[0] = index

    def get_current_index():
        return current_tab_index[0]

    mock_tab_widget.currentIndex = Mock(side_effect=get_current_index)
    mock_tab_widget.setCurrentIndex = Mock(side_effect=set_current_index)
    mock_tab_widget.setCurrentWidget = Mock()
    mock_tab_widget.currentWidget = Mock()
    mock_tab_widget.tabText = Mock(side_effect=lambda i: ["Map分析", "EXIF处理", "仿写功能", "特征点功能", "分析报告"][i] if i < 5 else "未知标签")
    mock_window.tab_widget = mock_tab_widget

    # 模拟各个标签页
    mock_exif_tab = Mock()
    mock_exif_tab.edit_src = Mock()
    mock_exif_tab.field_list_widget = Mock()
    mock_window.exif_processing_tab = mock_exif_tab

    mock_map_tab = Mock()
    # 配置拖拽相关的方法
    mock_map_tab.show_exif_dialog = Mock(return_value=True)
    mock_map_tab.handle_multiple_images = Mock(return_value=True)
    mock_map_tab.setAcceptDrops = Mock()
    mock_map_tab.dragEnterEvent = Mock()
    mock_map_tab.dropEvent = Mock()
    mock_window.map_analysis_tab = mock_map_tab

    mock_report_tab = Mock()
    mock_window.analysis_report_tab = mock_report_tab

    print("==liuq debug== 模拟主窗口创建完成")

    yield mock_window

    print("==liuq debug== 模拟主窗口清理完成")

@pytest.fixture
def mock_services():
    """提供模拟服务的fixture"""
    return {
        'xml_parser': Mock(),
        'exif_parser': Mock(),
        'report_generator': Mock(),
        'csv_exporter': Mock(),
        'image_export': Mock(),
        'field_registry': Mock(),
        'data_binding': Mock(),
        'html_generator': Mock(),
        'chart_generator': Mock()
    }
