# FastMapV2 测试运行指南

## 概述

本指南介绍如何运行FastMapV2项目的测试用例脚本。目前已创建11个测试脚本，覆盖了Map分析、EXIF处理、分析报告、主程序和GUI等核心功能。

## 测试环境要求

### 系统要求
- Windows 10/11 (推荐)
- Python 3.7+ 
- PowerShell 5.0+

### 依赖包要求
```bash
pip install pytest
pip install pytest-qt
pip install PyQt5
pip install pandas
pip install numpy
pip install matplotlib
pip install Pillow
pip install lxml
pip install psutil
```

## 测试数据准备

确保以下测试数据文件存在：
```
tests/test_data/
├── awb_scenario.xml                    # Map分析XML配置文件
├── 221_Swangoose_IMG20250101064635_sim.jpg  # EXIF测试图片
├── ceshiji.csv                         # 分析报告测试CSV文件
├── duibij.csv                          # 分析报告对比CSV文件
└── exif_awb_export.csv                 # EXIF导出标准对比文件
```

## 运行测试的方法

### 1. 批量运行所有测试（推荐）

```bash
# 进入项目根目录
cd e:\code\3__My\22_tool_fastmapv2\0_fastmapv2_latest

# 运行批量测试脚本
python tests/run_test_cases.py
```

这将：
- 自动发现所有TC-开头的测试脚本
- 按顺序执行每个测试
- 生成详细的测试报告
- 保存结果到 `tests/test_execution_report.md`

### 2. 运行单个测试脚本

```bash
# Map分析页面测试
python -m pytest tests/unit/TC-MAP-001_XML文件加载测试.py -v
python -m pytest tests/unit/TC-MAP-004_XML写入功能测试.py -v -s --log-cli-level=INFO
python -m pytest tests/unit/TC-MAP-005_筛选功能测试.py -v
python -m pytest tests/unit/TC-MAP-006_拖拽图片显示EXIF功能测试.py -v

# EXIF处理页面测试
python -m pytest tests/unit/TC-EXIF-001_EXIF解析测试.py -v
python -m pytest tests/unit/TC-EXIF-002_特定字段显示测试.py -v
python -m pytest tests/unit/TC-EXIF-003_CSV导出与对比测试.py -v

# 分析报告页面测试
python -m pytest tests/unit/TC-REPORT-001_分析报告页面加载CSV文件测试.py -v

# 主程序和GUI测试
python -m pytest tests/unit/TC-MAIN-001_主程序正常启动测试.py -v
python -m pytest tests/unit/TC-MAIN-002_依赖包检查测试.py -v
python -m pytest tests/unit/TC-MAIN-003_日志系统测试.py -v
python -m pytest tests/unit/TC-GUI-001_主窗口初始化测试.py -v
```

### 3. 按模块运行测试

```bash
# 运行Map分析模块的所有测试
python -m pytest tests/unit/TC-MAP-*.py -v

# 运行EXIF处理模块的所有测试
python -m pytest tests/unit/TC-EXIF-*.py -v

# 运行分析报告模块的所有测试
python -m pytest tests/unit/TC-REPORT-*.py -v

# 运行主程序模块的所有测试
python -m pytest tests/unit/TC-MAIN-*.py -v

# 运行GUI模块的所有测试
python -m pytest tests/unit/TC-GUI-*.py -v
```

### 4. 运行测试并生成详细报告

```bash
# 生成HTML报告
python -m pytest tests/unit/ --html=tests/report.html --self-contained-html -v

# 生成覆盖率报告
python -m pytest tests/unit/ --cov=gui --cov=core --cov-report=html -v
```

## 测试结果解读

### 成功输出示例
```
==liuq debug== 运行测试: TC-MAP-001_XML文件加载测试.py
✓ 通过: TC-MAP-001_XML文件加载测试.py
==liuq debug== 运行测试: TC-EXIF-001_EXIF解析测试.py
✓ 通过: TC-EXIF-001_EXIF解析测试.py
```

### 失败输出示例
```
==liuq debug== 运行测试: TC-MAP-001_XML文件加载测试.py
✗ 失败: TC-MAP-001_XML文件加载测试.py
==liuq debug== 错误信息: AssertionError: XML文件不存在...
```

### 测试报告内容
- 执行统计（总计、通过、失败、成功率）
- 详细结果（每个测试的状态和错误信息）
- 执行时间和性能数据

## 常见问题解决

### 1. 测试数据文件缺失
```
错误: 测试图片文件不存在: tests/test_data/221_Swangoose_IMG20250101064635_sim.jpg
解决: 确保所有测试数据文件都存在于tests/test_data/目录中
```

### 2. 依赖包缺失
```
错误: ModuleNotFoundError: No module named 'PyQt5'
解决: pip install PyQt5
```

### 3. GUI测试在无头环境中失败
```
错误: QApplication: invalid style override passed
解决: 在有图形界面的环境中运行GUI测试，或使用虚拟显示
```

### 4. 权限问题
```
错误: PermissionError: [Errno 13] Permission denied
解决: 以管理员权限运行PowerShell，或检查文件权限
```

## 测试脚本特点

### 日志标记
所有测试脚本都使用 `==liuq debug==` 标记日志信息，便于识别和过滤。

### 测试结构
每个测试脚本包含：
- 文件头注释（测试用例ID、描述、作者信息）
- 测试类（以TestTC_开头）
- Fixture方法（提供测试数据和环境）
- 测试方法（具体的测试用例实现）

### 错误处理
测试脚本包含完善的错误处理机制：
- 文件不存在的处理
- 依赖包缺失的处理
- GUI组件不存在的处理
- 超时和性能问题的处理

## 持续集成建议

### 1. 自动化测试流程
```bash
# 创建测试脚本
tests/run_automated_tests.bat

# 内容：
@echo off
cd /d "e:\code\3__My\22_tool_fastmapv2\0_fastmapv2_latest"
python tests/run_test_cases.py
if %errorlevel% neq 0 (
    echo 测试失败，请检查测试报告
    exit /b 1
) else (
    echo 所有测试通过
    exit /b 0
)
```

### 2. 定期测试计划
- 每日构建：运行核心功能测试
- 每周回归：运行完整测试套件
- 发布前：运行所有测试并生成报告

### 3. 测试结果通知
- 测试失败时发送邮件通知
- 生成测试趋势报告
- 集成到项目管理工具

## 下一步计划

1. **完成剩余测试脚本**：还有8个测试脚本需要创建
2. **增加性能测试**：添加内存使用、响应时间等性能指标
3. **集成测试**：添加模块间交互的集成测试
4. **端到端测试**：使用Playwright进行完整的用户流程测试
5. **测试数据管理**：建立测试数据的版本控制和管理机制

## 联系信息

如有测试相关问题，请联系：
- 作者：龙sir团队
- 创建时间：2025-08-28
- 版本：2.0.0
