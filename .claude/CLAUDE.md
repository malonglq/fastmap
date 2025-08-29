# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

FastMapV2 是一个基于 PyQt5 的专业桌面应用程序，主要用于分析对比机和调试机的 Map 配置差异，提供可视化分析报告，并实现 Map 配置的自动校准和仿写功能。

## 核心架构

### 分层架构设计
- **表现层**: PyQt5 GUI 界面 (`gui/`)
- **服务层**: 业务逻辑处理 (`core/services/`)
- **数据层**: 模型和数据处理 (`core/models/`)
- **接口层**: 接口定义和适配器 (`core/interfaces/`, `core/adapters/`)

### 关键架构特性
1. **可扩展字段管理系统**: 基于字段注册机制的动态字段管理，支持运行时添加新XML字段而无需修改代码
2. **双向数据绑定**: GUI与XML数据实时同步的绑定机制
3. **模块化设计**: 高内聚、低耦合的模块设计，支持插件式扩展
4. **组件复用**: 统一的报告生成接口和Chart.js图表生成能力

## 开发命令

### 运行程序
```bash
python main.py
```

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行测试
```bash
# 所有测试
python -m pytest tests/

# 单元测试
python -m pytest tests/unit/

# 集成测试
python -m pytest tests/integration/

# 特定测试
python -m pytest tests/unit/test_field_registry_service.py
python -m pytest tests/unit/test_xml_parser_service.py

# 带覆盖率报告
python -m pytest --cov=core tests/
```

### 运行演示
```bash
python demos/temperature_span_demo.py
```

## 核心模块说明

### 1. 字段注册系统 (`core/services/field_registry_service.py`)
- 支持动态字段注册和注销
- 字段分组和类型管理
- 字段可见性和可编辑性控制
- 字段变更通知机制

### 2. XML处理服务 (`core/services/xml_parser_service.py`, `core/services/xml_writer_service.py`)
- XML文件解析和验证
- Map配置数据提取
- XML备份和恢复功能
- 支持多种XML格式版本

### 3. 数据绑定管理 (`core/interfaces/data_binding_manager.py`)
- GUI组件与XML数据的双向绑定
- 数据变更同步机制
- 字段验证和格式化

### 4. 报告生成系统 (`core/services/reporting/`)
- HTML模板渲染
- Chart.js图表集成
- 多维度分析报告生成
- 交互式报告界面

### 5. EXIF数据处理 (`core/services/exif/`)
- 批量EXIF数据提取
- 趋势分析和对比
- CSV导出功能
- 字段过滤和配置

## 重要注意事项

### 循环导入问题
当前存在循环导入问题：
- `core/services/html_generator.py` 与 `core/services/reporting/map_multi_dimensional_report_generator.py` 之间的循环导入
- 需要重构以消除循环依赖

### 测试框架
- 使用 pytest 作为测试框架
- 支持 PyQt 组件测试 (pytest-qt)
- 测试覆盖单元测试和集成测试
- 测试数据位于 `tests/test_data/`

### 数据模型
- 主要数据模型在 `core/models/` 目录
- 使用强类型字段定义
- 支持数据验证和转换

### GUI框架
- 使用 PyQt5 构建（注意：当前环境有PyQt6，但代码基于PyQt5）
- 主窗口：`gui/main_window.py`
- 自定义控件：`gui/widgets/`
- 对话框：`gui/dialogs/`

### 配置管理
- 配置文件位于 `data/configs/`
- JSON格式的字段映射和阈值配置
- 用户状态持久化

### 日志系统
- 日志文件位于 `data/logs/`
- 统一的日志配置和管理

## 开发规范

### 代码风格
- 使用 Black 进行代码格式化
- 使用 Flake8 进行代码检查
- 遵循 SOLID 设计原则
- 使用中文注释和文档

### 错误处理
- 完善的异常处理机制
- 用户友好的错误提示
- 详细的错误日志记录

### 字段添加流程
1. 在 `core/services/field_registry_service.py` 中定义字段
2. 注册字段到字段注册表
3. GUI会自动生成对应的界面组件
4. 数据绑定自动同步

## 项目状态

- **当前版本**: v0.2.0-alpha
- **开发状态**: 架构实施阶段
- **当前重点**: 修复循环导入问题，完善核心功能模块
- **已完成**: 核心架构设计、字段注册系统、基础GUI框架
- **进行中**: Map分析功能、EXIF数据处理集成、报告生成系统

## 可用 Subagents

### 代码审查专家 (code-reviewer)
**用途**: 主动审查代码的质量、安全性和可维护性。在编写或修改代码后立即使用。
**工具**: Read, Grep, Glob, Bash

**功能**:
- 系统性审查代码质量和安全性
- 分析设计模式和最佳实践
- 提供具体的改进建议和示例
- 评估性能影响和技术债务

### 调试专家 (debugger)
**用途**: 调试专家，专门处理复杂问题诊断、根本原因分析和系统性问题解决。在遇到任何问题时主动使用。
**工具**: Read, Edit, Bash, Grep, Glob

**功能**:
- 捕获错误消息和堆栈跟踪
- 应用系统性调试技术
- 提供根本原因解释和预防建议
- 确保修复的安全性和完整性

### 数据分析专家 (data-scientist)
**用途**: 数据分析专家，专门处理SQL查询、BigQuery操作和数据洞察。在数据分析任务和查询中主动使用。
**工具**: Bash, Read, Write

**功能**:
- 编写高效的SQL查询和BigQuery操作
- 分析和总结结果，清晰地呈现发现
- 提供数据驱动的建议和后续步骤
- 确保查询高效且具有成本效益

### 架构审查专家 (architect-reviewer)
**用途**: 架构审查专家，专门处理系统设计验证、架构模式和技术决策评估。专注于可扩展性分析、技术栈评估和演进架构。
**工具**: Read, Bash

**功能**:
- 评估系统设计和架构决策
- 分析可扩展性、安全性和演进潜力
- 提供技术选择和集成策略建议
- 识别架构风险和现代化机会

### 搜索专家 (search-specialist)
**用途**: 搜索专家，专门处理高级信息检索、查询优化和知识发现。专注于在海量多样来源中寻找精确信息。
**工具**: Read, Write, WebSearch, Grep

**功能**:
- 设计全面的搜索策略
- 优化查询和源选择
- 提供高质量、相关的信息结果
- 确保搜索的精确性和效率

### 重构专家 (refactoring-specialist)
**用途**: 重构专家，专门处理安全代码转换技术和设计模式应用。专注于改进代码结构、降低复杂性和增强可维护性。
**工具**: Read, Edit, Bash

**功能**:
- 检测代码异味和复杂度问题
- 应用系统性重构模式
- 确保重构的安全性和测试覆盖
- 提供代码质量改进建议

### 文档工程师 (documentation-engineer)
**用途**: 文档工程师，专门处理技术文档系统、API文档和开发者友好内容。掌握文档即代码、自动化生成和可维护文档。
**工具**: Read, Write, MultiEdit, Bash

**功能**:
- 设计和构建文档系统架构
- 自动化API文档生成
- 创建开发者友好的教程和指南
- 确保文档的准确性和可维护性