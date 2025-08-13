# FastMapV2 项目结构说明

## 📁 目录结构概览

```
fastmapv2/
├── /0_3a_parser_py/        # 原有的3A解析器工具（保留）
├── /0_csv_compare/         # 原有的CSV比较工具（保留）
├── /0_showmap/             # 原有的showmap工具（保留）
├── /bak/                   # 备份文件目录
│   └── fastmapv2_0_ori/   # 原始版本备份
├── /core/                  # 核心业务逻辑模块
│   ├── interfaces/        # 接口定义
│   ├── managers/          # 管理器类
│   ├── models/            # 数据模型定义
│   └── services/          # 业务服务层
├── /data/                  # 用户数据存储目录
│   ├── configs/           # 配置文件
│   └── logs/              # 日志文件
├── /demos/                 # 演示和示例代码
│   ├── demo_final_enhanced_interaction.py
│   ├── demo_final_polygon_visualization.py
│   ├── demo_map_analysis.py
│   └── demo_polygon_coordinates.py
├── /docs/                  # 项目文档目录
│   ├── architecture.md                        # 系统架构文档
│   ├── code-review.md                         # 代码检查文档
│   ├── development-status.md                  # 开发状态文档
│   ├── requirements-analysis.md               # 需求分析文档
│   ├── xml_data_management_architecture.md    # XML架构设计文档
│   ├── 可扩展XML数据管理架构设计.md            # 架构设计任务文档
│   ├── Phase1_Map分析与报告生成.md            # Phase1任务文档
│   ├── GUI_FIX_SOLUTION.md                   # GUI修复方案
│   ├── HEADER_DISPLAY_FIX_FINAL.md           # 表头显示修复
│   ├── HEADER_DUPLICATE_FIX.md               # 表头重复修复
│   ├── HEADER_SIMPLIFICATION_GUIDE.md        # 表头简化指南
│   └── SORTING_FUNCTIONALITY_FIX.md          # 排序功能修复
├── /gui/                   # PyQt GUI模块
│   ├── dialogs/           # 对话框组件
│   ├── widgets/           # 自定义控件
│   ├── __pycache__/       # Python缓存文件
│   └── main_window.py     # 主窗口
├── /output/                # 生成的报告输出目录
│   ├── fastmapv2_report_20250725_182640.html
│   ├── fastmapv2_report_20250725_183218.html
│   ├── fastmapv2_report_20250725_193410.html
│   └── fastmapv2_report_20250725_193456.html
├── /tests/                 # 测试代码目录
│   ├── integration/       # 集成测试
│   ├── unit/              # 单元测试
│   ├── test_data/         # 测试数据
│   │   ├── awb_scenario.xml
│   │   └── simple_map.xml
│   ├── test_enhanced_map_interaction.py
│   ├── test_header_fix.py
│   ├── test_header_hover.py
│   ├── test_header_repaint_fix.py
│   ├── test_hover_simple.py
│   ├── test_map_shape_viewer.py
│   ├── test_new_layout.py
│   ├── test_polygon_visualization.py
│   ├── test_simple_header.py
│   ├── test_simple_polygon.py
│   ├── test_sorting_functionality.py
│   ├── test_table_header.py
│   └── test_table_populate.py
├── /utils/                 # 工具类和辅助函数
│   ├── helpers/           # 通用辅助函数
│   ├── validators/        # 数据验证器
│   ├── __pycache__/       # Python缓存文件
│   └── file_manager.py    # 文件管理工具
├── main.py                 # 项目入口点
├── README.md               # 项目说明文档
└── requirements.txt        # Python依赖列表
```

## 📋 目录说明

### 核心模块 (/core/)
- **interfaces/**: 定义系统的抽象接口，包括字段编辑器、数据处理器等
- **managers/**: 管理器类，如数据管理器、配置管理器、插件管理器
- **models/**: 数据模型定义，包括MapPoint、MapConfiguration等
- **services/**: 业务服务层，包括XML解析器、分析器、报告生成器等

### GUI模块 (/gui/)
- **main_window.py**: 主窗口实现，包含5个功能标签页
- **widgets/**: 自定义控件，如MapTableWidget、MapShapeViewer等
- **dialogs/**: 对话框组件，如字段配置对话框等

### 工具模块 (/utils/)
- **helpers/**: 通用辅助函数
- **validators/**: 数据验证器
- **file_manager.py**: 文件管理工具

### 文档目录 (/docs/)
- **核心设计文档**: 需求分析、架构设计、XML数据管理架构
- **开发文档**: 开发状态、代码检查、项目结构说明
- **修复文档**: 各种GUI修复方案和指南

### 测试目录 (/tests/)
- **unit/**: 单元测试，测试单个组件功能
- **integration/**: 集成测试，测试组件间协作
- **test_data/**: 测试用的XML文件和数据
- **test_*.py**: 各种功能测试文件

### 演示目录 (/demos/)
包含各种功能演示和示例代码，用于验证功能和学习参考

### 数据目录 (/data/)
- **configs/**: 用户配置文件
- **logs/**: 应用程序日志文件

### 输出目录 (/output/)
存放生成的HTML分析报告

## 🔧 文件组织原则

### 1. 按功能分类
- 核心业务逻辑放在 `/core/`
- GUI相关代码放在 `/gui/`
- 工具函数放在 `/utils/`

### 2. 按类型分类
- 所有文档放在 `/docs/`
- 所有测试放在 `/tests/`
- 所有演示放在 `/demos/`

### 3. 数据分离
- 用户数据放在 `/data/`
- 测试数据放在 `/tests/test_data/`
- 输出文件放在 `/output/`

### 4. 保留原有工具
- 原有的工具模块（0_*）保留在根目录
- 备份文件放在 `/bak/` 目录

## 📝 文件命名规范

### Python文件
- 模块文件：小写字母+下划线，如 `xml_parser.py`
- 类文件：与类名对应，如 `MapTableWidget` → `map_table_widget.py`
- 测试文件：以 `test_` 开头，如 `test_xml_parser.py`

### 文档文件
- 英文文档：小写字母+连字符，如 `requirements-analysis.md`
- 中文文档：中文名称，如 `可扩展XML数据管理架构设计.md`
- 修复文档：大写字母+下划线，如 `GUI_FIX_SOLUTION.md`

### 目录命名
- 英文目录：小写字母，如 `core`, `gui`, `tests`
- 保持简洁和语义明确

## 🚀 使用指南

### 开发时
1. 核心功能开发在 `/core/` 目录
2. GUI开发在 `/gui/` 目录
3. 工具函数在 `/utils/` 目录
4. 测试代码在 `/tests/` 目录

### 文档维护
1. 设计文档放在 `/docs/`
2. 及时更新 `development-status.md`
3. 重要变更记录在相应文档中

### 测试运行
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/unit/test_xml_parser.py
```

---

**文档版本**: v1.0  
**创建时间**: 2025-07-28  
**维护人员**: DW (文档编写者)  
**更新说明**: 项目目录整理后的结构说明
