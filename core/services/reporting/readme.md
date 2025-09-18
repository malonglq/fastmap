# Reporting 模块结构说明

`core/services/reporting/` 负责 FastMapV2 报告体系的核心逻辑，按“基础设施 → 引擎 → 领域”分层构建，同时通过 `manager.py` 对外提供统一入口。本说明总结该目录下的组织规则与开发要点。

> 注：模板文件位于 `templates/reporting/`，不在本文范围内。

## 目录总览

```
core/services/reporting/
├── __init__.py                # 汇总导出，对外屏蔽内部层级
├── common/                    # 预留跨领域共享工具（当前为空壳）
├── domains/                   # 按业务域划分的报告服务
│   ├── exif/                  # EXIF 对比分析
│   └── map/                   # MAP 多维分析
├── engine/                    # 报告编排与调度引擎
├── infrastructure/            # 模型、模板、渲染等基础设施
└── manager.py                 # 统一报告管理入口
```

## 各目录职责

### `__init__.py`
- 暴露 `ReportGenerator`、`EXIFReportGenerator`、领域服务与辅助函数。
- 作为外部唯一入口，避免直接依赖内部文件结构。

### `common/`
- 存放跨领域复用的通用能力（工具、常量、抽象基类等）。
- 当前为空；如需要共享逻辑建议先放置于此，再由各领域引用。

### `domains/`
- 每个子目录代表一个业务域，对应一套报告实现。
- 典型结构：
  - `<domain>_report_service.py`：领域服务入口，负责数据准备与 `ReportEngine` 协作。
  - `components/`：模板化输出（KPI 卡片、表格、图表等纯渲染逻辑）。
  - `helpers/`：复杂数据整理、兼容旧逻辑的辅助方法。
- 现有域：
  - `exif/`：EXIF 对比报告，包含匹配、统计、KPI、趋势分析等能力。
  - `map/`：MAP 多维度分析报告。
- 规则：
  - 允许依赖 `infrastructure/` 与 `common/`，禁止跨领域互相引用。
  - 模块命名使用 `snake_case`，组件按功能命名（如 `tables.py`、`charts.py`）。

### `engine/`
- `report_engine.py` 提供基础 `ReportGenerator` 及 `EXIFReportGenerator`，负责：
  - 组装 `ReportData`、调度领域 helpers、调用模板渲染。
  - 写入最终输出文件。
- 引擎层不直接处理具体业务数据，依赖领域服务提供的结构化信息。

### `infrastructure/`
- 提供通用基础设施：
  - `models.py`：`ReportConfig`、`ReportSection`、`SectionType` 等数据结构。
  - `template_renderer.py`：Jinja2 渲染封装。
  - `resources.py` 与 `html/`：模板、样式资源加载服务。
- 要求保持无业务逻辑、可在多领域间复用。

### `manager.py`
- 提供 `UnifiedReportManager`、`ReportHistoryItem` 等高层 API。
- 负责在 GUI / 服务与报告引擎之间协调选择、配置与历史记录。

## 依赖关系约束

```
外部调用 → manager.py → engine/ → domains/<domain>
                                ↘ common/
engine/ ↔ infrastructure/
```

- 领域层可以：依赖 `infrastructure/`、`common/`、自身子模块。
- 领域层禁止：跨域直接访问（例如 `map` 不应引用 `domains/exif`）。
- 基础设施层不依赖领域或上层模块。

## 开发指南

1. **新增报告类型**
   - 在 `domains/<new>/` 按现有结构创建服务、组件、辅助模块。
   - 在 `domains/__init__.py` 与 `core/services/reporting/__init__.py` 注册导出。
   - 如需专用配置，更新 `manager.py` 与模板。

2. **复用逻辑下沉**
   - 多领域共用的函数优先放入 `common/` 或 `infrastructure/`。
   - 避免在领域层复制粘贴业务无关代码。

3. **模板与样式**
   - 结构化数据只在 Python 层准备，展示效果在 `templates/reporting/` 中维护。
   - 修改模板后，如需额外片段，可在 `infrastructure/resources.py` 登记。

4. **命名与导入**
   - 模块名 `snake_case`，类名 `PascalCase`。保持绝对导入。
   - 领域服务文件命名统一为 `<domain>_report_service.py`，组件/辅助按职责命名。

5. **测试与扩展**
   - 新增领域或引擎能力时请补充单元测试（`tests/unit/TC-REPORT-*`）。
   - 导入新的外部资源需同步更新 README 及相关配置。

通过遵守以上约定，可在保持结构清晰的前提下扩展 FastMapV2 报告体系，降低跨领域嵌套依赖与维护成本。
