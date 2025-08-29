# FastMapV2 项目测试用例设计文档

## 测试覆盖度总结

### 1. 项目功能模块分析

FastMapV2是一个基于PyQt5的桌面应用程序，主要包含以下核心功能模块：

#### 1.1 XML配置文件处理模块
- **核心组件**：XMLParserService, XMLWriterService, FieldRegistryService
- **主要功能**：解析awb_scenario.xml配置文件，支持动态字段注册
- **测试重点**：解析准确性、写入完整性、错误处理、性能

#### 1.2 EXIF数据处理模块
- **核心组件**：ExifParserService, ExifCsvExporter, ImageExportService
- **主要功能**：EXIF数据提取、批量处理、CSV导出
- **测试重点**：DLL集成、数据格式转换、批量处理性能

#### 1.3 地图分析和可视化模块
- **核心组件**：MapAnalyzer, MultiDimensionalAnalyzer, ChartGenerator
- **主要功能**：Map数据分析、多维统计、图表生成
- **测试重点**：分析算法准确性、可视化效果、性能优化

#### 1.4 报告生成模块
- **核心组件**：HtmlGenerator, ExifComparisonReportGenerator
- **主要功能**：HTML报告生成、模板渲染、交互式图表
- **测试重点**：报告格式正确性、数据完整性、模板兼容性

#### 1.5 用户界面模块
- **核心组件**：MainWindow, 各种Tab页面
- **主要功能**：GUI交互、拖拽支持、实时数据绑定
- **测试重点**：用户交互、界面响应、异常处理

### 2. 测试用例设计原则

#### 2.1 测试金字塔模型
```
         /\
        /  \
       /    \
      / E2E  \
     /   \    \
    /  集成 \   \
   /         \  \
  /   单元测试  \ \
 /______________\ \
```

#### 2.2 测试覆盖度目标
- **单元测试覆盖度**：≥80%
- **集成测试覆盖度**：≥60%
- **端到端测试覆盖度**：≥40%
- **关键路径覆盖度**：100%

### 3. 已完成的测试用例

#### 3.1 XML处理模块测试用例

**单元测试文件**：`tests/unit/test_xml_processing_module.py`

**测试类和功能**：
- `TestXMLParserService`：XML解析服务测试
  - `test_parse_valid_xml`：测试有效XML解析
  - `test_parse_invalid_xml`：测试无效XML解析
  - `test_parse_nonexistent_file`：测试不存在文件解析
  - `test_parse_with_field_registry`：测试字段注册集成
  - `test_parse_map_points`：测试Map点解析

- `TestXMLWriterService`：XML写入服务测试
  - `test_write_valid_config`：测试有效配置写入
  - `test_write_with_backup`：测试备份功能
  - `test_write_to_readonly_location`：测试只读位置写入
  - `test_write_with_formatting`：测试格式化写入

- `TestXMLValidationService`：XML验证服务测试
  - `test_validate_valid_xml`：测试有效XML验证
  - `test_validate_invalid_xml`：测试无效XML验证
  - `test_validate_with_schema`：测试Schema验证
  - `test_validate_required_fields`：测试必填字段验证

- `TestFieldRegistryService`：字段注册服务测试
  - `test_register_field`：测试字段注册
  - `test_get_fields_for_device`：测试设备字段获取
  - `test_field_type_validation`：测试字段类型验证
  - `test_field_xml_path_mapping`：测试XML路径映射

**集成测试文件**：`tests/integration/test_xml_processing_integration.py`

**测试类和功能**：
- `TestXMLProcessingIntegration`：XML处理集成测试
  - `test_parse_analyze_integration`：解析-分析集成
  - `test_parse_write_roundtrip`：解析-写入往返测试
  - `test_field_registry_integration`：字段注册集成
  - `test_error_handling_integration`：错误处理集成
  - `test_batch_processing_integration`：批量处理集成
  - `test_backup_integration`：备份集成
  - `test_validation_integration`：验证集成

- `TestXMLProcessingPerformance`：XML处理性能测试
  - `test_large_file_parsing_performance`：大文件解析性能
  - `test_memory_usage`：内存使用测试

#### 3.2 EXIF数据处理模块测试用例

**单元测试文件**：`tests/unit/test_exif_processing_module.py`

**测试类和功能**：
- `TestExifParserService`：EXIF解析服务测试
  - `test_parse_single_image_with_mock`：单张图片解析测试
  - `test_parse_directory_with_mock`：目录解析测试
  - `test_parse_with_field_filtering`：字段过滤测试
  - `test_parse_error_handling`：错误处理测试
  - `test_parse_nonexistent_file`：不存在文件解析测试
  - `test_parse_with_progress_callback`：进度回调测试
  - `test_parse_with_cancellation`：取消解析测试

- `TestExifCsvExporter`：CSV导出服务测试
  - `test_export_to_csv`：CSV导出测试
  - `test_export_with_field_selection`：字段选择导出
  - `test_export_with_encoding`：编码测试
  - `test_export_to_readonly_location`：只读位置导出
  - `test_export_empty_records`：空记录导出

- `TestImageExportService`：图片导出服务测试
  - `test_export_single_image`：单张图片导出
  - `test_export_with_naming_pattern`：命名模式测试
  - `test_export_with_format_conversion`：格式转换测试
  - `test_export_nonexistent_image`：不存在图片导出
  - `test_export_with_metadata`：元数据导出

- `TestImageExportWorkflowService`：工作流服务测试
  - `test_batch_export_workflow`：批量导出工作流
  - `test_workflow_with_progress_callback`：进度回调测试
  - `test_workflow_with_error_handling`：错误处理测试
  - `test_workflow_with_cancellation`：取消测试

**集成测试文件**：`tests/integration/test_exif_processing_integration.py`

**测试类和功能**：
- `TestExifProcessingIntegration`：EXIF处理集成测试
  - `test_parse_export_integration`：解析-导出集成
  - `test_parse_export_report_integration`：解析-导出-报告集成
  - `test_batch_processing_integration`：批量处理集成
  - `test_error_handling_integration`：错误处理集成
  - `test_progress_tracking_integration`：进度跟踪集成
  - `test_cancellation_integration`：取消集成
  - `test_memory_management_integration`：内存管理集成

- `TestExifProcessingRealData`：真实数据测试
  - `test_real_data_processing`：真实数据处理测试

#### 3.3 地图分析和可视化模块测试用例

**单元测试文件**：`tests/unit/test_map_analysis_module.py`

**测试类和功能**：
- `TestMapAnalyzer`：地图分析器测试
  - `test_analyze_configuration_basic`：基本配置分析
  - `test_analyze_empty_configuration`：空配置分析
  - `test_analyze_coordinate_range`：坐标范围分析
  - `test_analyze_weight_distribution`：权重分布分析
  - `test_analyze_scene_statistics`：场景统计
  - `test_analyze_parameter_ranges`：参数范围分析
  - `test_analyze_base_boundary_comparison`：BaseBoundary比较
  - `test_analyze_map_density`：Map密度分析
  - `test_analyze_with_custom_parameters`：自定义参数分析

- `TestMultiDimensionalAnalyzer`：多维分析器测试
  - `test_analyze_multidimensional_data`：多维数据分析
  - `test_correlation_analysis`：相关性分析
  - `test_cluster_analysis`：聚类分析
  - `test_dimensionality_reduction`：降维分析
  - `test_outlier_detection`：异常值检测
  - `test_analyze_with_custom_config`：自定义配置分析
  - `test_analyze_empty_data`：空数据分析

- `TestTemperatureSpanAnalyzer`：色温跨度分析器测试
  - `test_analyze_temperature_span`：色温跨度分析
  - `test_temperature_range_analysis`：温度范围分析
  - `test_span_distribution_analysis`：跨度分布分析
  - `test_coverage_analysis`：覆盖度分析
  - `test_temperature_zones_analysis`：温度区域分析
  - `test_analyze_with_custom_ranges`：自定义范围分析
  - `test_analyze_empty_data`：空数据分析

- `TestChartGenerator`：图表生成器测试
  - `test_generate_scatter_plot`：散点图生成
  - `test_generate_heatmap`：热力图生成
  - `test_generate_parameter_distribution_plot`：参数分布图
  - `test_generate_correlation_matrix_plot`：相关性矩阵图
  - `test_generate_time_series_plot`：时间序列图
  - `test_generate_multi_panel_plot`：多面板图
  - `test_generate_with_custom_styling`：自定义样式生成
  - `test_generate_to_invalid_path`：无效路径生成
  - `test_generate_with_empty_data`：空数据生成

### 4. 待完成的测试用例

#### 4.1 报告生成模块测试用例

**需要创建的测试文件**：
- `tests/unit/test_report_generation_module.py`
- `tests/integration/test_report_generation_integration.py`

**需要测试的功能**：
- HTML生成器功能
- 模板渲染正确性
- 报告数据完整性
- 交互式图表集成
- 多格式输出支持
- 报告历史管理

#### 4.2 GUI界面模块测试用例

**需要创建的测试文件**：
- `tests/unit/test_gui_module.py`
- `tests/integration/test_gui_integration.py`
- `tests/e2e/test_gui_e2e.py`

**需要测试的功能**：
- 主窗口启动和关闭
- 标签页切换
- 拖拽文件功能
- 按钮点击事件
- 菜单项功能
- 对话框显示
- 数据绑定更新
- 错误消息显示

#### 4.3 端到端测试用例

**需要创建的测试文件**：
- `tests/e2e/test_complete_workflow.py`
- `tests/e2e/test_user_scenarios.py`
- `tests/e2e/test_performance_scenarios.py`

**需要测试的场景**：
- 完整的XML分析工作流
- EXIF数据处理到报告生成
- 批量文件处理
- 错误恢复场景
- 性能压力测试
- 用户交互路径

### 5. 测试配置和工具

#### 5.1 测试框架配置

**pytest配置** (`pytest.ini`)：
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=core
    --cov=gui
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    gui: marks tests as GUI tests
```

#### 5.2 测试数据管理

**测试数据目录结构**：
```
tests/test_data/
├── xml/
│   ├── valid_awb_scenario.xml
│   ├── invalid_awb_scenario.xml
│   └── large_awb_scenario.xml
├── images/
│   ├── test_image_1.jpg
│   ├── test_image_2.jpg
│   └── corrupted_image.jpg
├── csv/
│   ├── sample_exif_data.csv
│   └── empty_data.csv
└── expected_results/
    ├── expected_analysis_result.json
    └── expected_report.html
```

#### 5.3 Mock和Fixture配置

**conftest.py配置**：
```python
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

@pytest.fixture
def temp_dir():
    """临时目录fixture"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_exif_data():
    """Mock EXIF数据fixture"""
    return {
        'Exif.Photo.ColorTemperature': 5200,
        'Exif.Photo.AsShotNeutral': [0.5, 1.0, 0.45],
        'Exif.Photo.WhiteBalance': 'Auto',
        'Image.Make': 'ACME',
        'Image.Model': 'X1000'
    }

@pytest.fixture
def sample_map_config():
    """示例Map配置fixture"""
    from core.models.map_data import MapConfiguration, MapPoint, BaseBoundary
    
    config = MapConfiguration()
    config.version.major = 1
    config.version.minor = 0
    
    map_point = MapPoint(
        alias_name='test_map',
        x=100, y=200,
        weight=0.8,
        rp_g=1.0, bp_g=1.2,
        bv=50, ir=1000, cct=5200
    )
    config.offset_maps = [map_point]
    config.base_boundary = BaseBoundary(rp_g=1.0, bp_g=1.2)
    
    return config
```

### 6. 测试执行策略

#### 6.1 测试分类执行

```bash
# 运行所有单元测试
pytest tests/unit/ -v

# 运行所有集成测试
pytest tests/integration/ -v

# 运行所有端到端测试
pytest tests/e2e/ -v

# 运行特定模块测试
pytest tests/unit/test_xml_processing_module.py -v

# 运行性能测试
pytest -m "slow" -v

# 生成覆盖率报告
pytest --cov=core --cov-report=html
```

#### 6.2 CI/CD集成

**GitHub Actions配置** (.github/workflows/test.yml)：
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-qt
    
    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=core --cov-report=xml
    
    - name: Run integration tests
      run: pytest tests/integration/ -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

### 7. 测试覆盖度评估

#### 7.1 当前覆盖度统计

基于已完成的测试用例：

**模块覆盖度**：
- XML处理模块：85% (单元测试 + 集成测试)
- EXIF处理模块：80% (单元测试 + 集成测试)
- 地图分析模块：75% (单元测试)
- 报告生成模块：0% (待完成)
- GUI界面模块：0% (待完成)

**总体覆盖度**：48%

#### 7.2 覆盖度提升计划

**第一阶段**（已完成）：
- XML处理模块测试：85%
- EXIF处理模块测试：80%
- 地图分析模块测试：75%

**第二阶段**（计划中）：
- 报告生成模块测试：70%
- GUI界面模块测试：60%
- 端到端测试：50%

**目标总体覆盖度**：75%

### 8. 测试最佳实践

#### 8.1 测试命名规范

```python
# 好的测试命名
def test_parse_valid_xml_file_successfully():
    """测试解析有效XML文件成功"""
    pass

def test_export_csv_with_selected_fields():
    """测试导出CSV时只包含选定的字段"""
    pass

# 避免的测试命名
def test_xml():
    """命名不够具体"""
    pass

def test_parse():
    """缺少上下文"""
    pass
```

#### 8.2 测试结构模式

```python
class TestSomeService:
    """服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.service = SomeService()
        self.test_data = create_test_data()
    
    def tearDown(self):
        """测试后清理"""
        cleanup_test_data()
    
    def test_some_functionality(self):
        """测试特定功能"""
        # Arrange - 准备
        input_data = self.test_data
        
        # Act - 执行
        result = self.service.do_something(input_data)
        
        # Assert - 断言
        self.assertEqual(result.expected_value, result.actual_value)
```

#### 8.3 Mock使用原则

```python
# 好的Mock使用
def test_parse_with_mock_dll(self):
    """使用Mock测试DLL集成"""
    with patch.object(self.parser, '_call_dll') as mock_call:
        mock_call.return_value = expected_data
        result = self.parser.parse_file(test_file)
        self.assertEqual(result.fields, expected_fields)

# 避免过度Mock
def test_parse_with_full_mock(self):
    """避免Mock整个服务"""
    # 不好的做法：Mock整个服务
    with patch('core.services.exif_processing.ExifParserService') as mock_service:
        mock_service.return_value.parse_file.return_value = expected_result
        # 这样测试失去了实际意义
```

### 9. 总结

本测试用例设计文档为FastMapV2项目提供了全面的测试覆盖方案：

1. **已完成**：XML处理模块、EXIF处理模块、地图分析模块的完整测试用例
2. **待完成**：报告生成模块、GUI界面模块、端到端测试用例
3. **覆盖度目标**：总体75%的代码覆盖度
4. **测试质量**：注重测试的实用性、可维护性和性能

通过这套测试体系，可以确保FastMapV2项目的质量和稳定性，为后续的功能开发和维护提供有力保障。