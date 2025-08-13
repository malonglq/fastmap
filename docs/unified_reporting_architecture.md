# FastMapV2 统一报告中心架构与需求规格 v1.0

**版本**: 1.0
**状态**: 已批准
**创建日期**: 2025-08-06

## 1. 概述

### 1.1. 目标与原则

本文档旨在为 FastMapV2 项目的报告生成功能，定义一个统一、解耦且可扩展的架构。本次重构的目标是解决当前报告功能逻辑分散、与UI耦合过紧的问题，并将所有报告功能整合到“分析报告”标签页中，形成一个统一的报告中心。

遵循以下核心原则：

*   **单一职责 (Single Responsibility)**: 每个模块只做一件事。
*   **解耦 (Decoupling)**: UI层与核心报告生成逻辑完全分离。
*   **可扩展性 (Extensibility)**: 设计统一接口，方便未来增加新的报告类型。
*   **可复用性 (Reusability)**: 整合并封装现有算法，使其成为可在任何地方调用的核心服务。



## 2. 功能规格: 报告一 - EXIF 对比分析

### 2.1. 目标

通过量化对比“对比机”和“调试机”在相同SAB场景下的EXIF数据，直观地揭示两者的性能差异趋势，为参数调优提供数据支撑。

### 2.2. 需求规格

*   **入口**: “分析报告”标签页中的“EXIF 对比分析”按钮。
*   **输入**:
    1.  对比机 EXIF 数据 (CSV格式)。
    2.  调试机 EXIF 数据 (CSV格式)。
*   **数据匹配逻辑**:
    *   **匹配键**: 使用文件名开头的**数字序列号**作为唯一匹配键 (例如，从 `32_zhufeng_...jpg` 中提取 `32`)。
*   **核心分析指标**:
    *   **核心三项**: `color_sensor_irRatio`, `color_sensor_sensorCct`, `meta_data_currentFrame_bv`。
    *   **色彩增益**: `ealgo_data_SGW_gray_RpG`, `ealgo_data_SGW_gray_BpG`, `ealgo_data_AGW_gray_RpG`, `ealgo_data_AGW_gray_BpG`, `ealgo_data_Mix_gray_edge_RpG`, `ealgo_data_Mix_gray_edge_BpG`, `ealgo_data_Mix_csalgo_RpG`, `ealgo_data_Mix_csalgo_BpG`, `ealgo_data_After_face_RpG`, `ealgo_data_After_face_BpG`。
*   **HTML报告内容**:
    1.  **摘要区**: 显示对比文件名和匹配上的场景总数。
    2.  **趋势图区**: 为上述**每一个**核心指标生成独立的交互式折线图，包含“对比机”和“调试机”两条曲线。
    3.  **数据表区**: 显示所有匹配场景的核心指标数据、差值和差值百分比。
    4.  **差异高亮**: 根据一个可配置的JSON文件（复用 `0_csv_compare/config/thresholds.json` 的机制）对差异过大的单元格进行背景高亮。

## 3. 功能规格: 报告二 - Map 多维度分析

### 3.1. 目标

对单个XML配置文件进行全局扫描和深度分析，让用户能够快速、宏观地理解整个MAP的布局和配置策略。

### 3.2. 需求规格

*   **入口**: “分析报告”标签页中的“Map 多维度分析”按钮。
*   **输入**: 一个 `awb_scenario.xml` 文件。
*   **核心分析维度**:
    *   允许用户按“**场景**”（室内/室外/夜景）和“**Map类型**”（强拉/减小权重）对所有Map点进行筛选和聚合统计。
*   **关键可视化指标**:
    1.  **几何形状**: 在图上绘制每个Map点由 `polygon_vertices` 定义的**真实、封闭的多边形**。
    2.  **填充颜色**: 多边形的填充颜色由其所属的“**场景**”决定（如：室内-橙色，室外-蓝色，夜景-深灰色）。
    3.  **交互提示**: 鼠标悬浮在多边形上时，高亮其边框，并弹出信息框显示其核心参数（别名、权重、BV范围、CCT范围等）。
*   **特征点关联**: 本阶段仅做静态分析，将此高级功能留到下一迭代实现。
*   **HTML报告内容**:
    1.  **摘要区**: 显示文件名、总Map点数，以及一个按场景和Map类型分类的统计饼图或条形图。
    2.  **全局Map点分布图**: 上述定义的可视化图表，包含筛选器。
    3.  **分场景详细分析**: 为每个场景（室内、室外、夜景）提供一个详细的数据表格，列出该场景下所有Map点的详细配置。

## 4. 技术实施方案 (高级概述)

*   **文件结构变更**:
    *   **新建**:
        *   `core/interfaces/report_generator.py`
        *   `core/services/exif_comparison_report_generator.py`
        *   `core/services/map_multi_dimensional_report_generator.py`
        *   `gui/dialogs/exif_comparison_dialog.py`
        *   `gui/dialogs/map_analysis_dialog.py`
    *   **修改**:
        *   `core/services/unified_report_manager.py` (重构)
        *   `gui/tabs/analysis_report_tab.py` (UI重构)
        *   `gui/main_window.py` (移除旧按钮和逻辑)
*   **测试**: 为所有新的和重构的服务编写单元测试和集成测试。