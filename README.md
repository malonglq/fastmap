# FastMapV2 - 对比机Map分析&仿写工具

## 📋 项目简介
FastMapV2是一个基于PyQt5的桌面应用程序，用于分析对比机和调试机的Map配置差异，提供可视化分析报告，并实现Map配置的自动校准和仿写功能。

## 🎯 主要功能
- **Map数据解析与可视化**: 支持XML解析、坐标散点图、权重热力图
- **可扩展XML字段管理**: 基于字段注册机制的动态字段管理系统
- **GUI内XML编辑**: 直接在界面中编辑XML内容，支持复制粘贴Map行
- **EXIF数据处理**: 批量处理SAB图片的EXIF数据，趋势分析
- **Map配置仿写**: 基于偏移量计算的自动校准和仿写功能
- **HTML分析报告**: 生成专业的交互式分析报告

## 🏗️ 核心架构特性
- **字段注册机制**: 添加新XML字段只需配置，无需修改代码
- **动态GUI生成**: 界面组件根据字段定义自动调整
- **双向数据绑定**: GUI与XML数据实时同步
- **类型安全**: 强类型字段定义和验证机制

## 🛠️ 技术栈
- **GUI框架**: PyQt5 - 现代化桌面应用界面
- **数据处理**: pandas, numpy - 高效数据分析
- **可视化**: matplotlib - 多样化图表展示
- **报告生成**: Jinja2, HTML/CSS/JS - 专业报告模板
- **文件处理**: xml.etree.ElementTree - 标准XML处理

## 🚀 快速开始

### 环境要求
- Python 3.8+
- PyQt5 5.15.0+
- 其他依赖见 requirements.txt

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行程序
```bash
python main.py
```

## 📁 项目结构
```
fastmapv2/
├── /core/                  # 核心业务逻辑模块
│   ├── models/            # 数据模型定义
│   ├── services/          # 业务服务层
│   ├── managers/          # 管理器类
│   └── interfaces/        # 接口定义
├── /gui/                   # PyQt GUI模块
│   ├── main_window.py     # 主窗口
│   ├── widgets/           # 自定义控件
│   └── dialogs/           # 对话框
├── /utils/                 # 工具类和辅助函数
│   ├── helpers/           # 通用辅助函数
│   ├── validators/        # 数据验证器
│   └── formatters/        # 格式化工具
├── /data/                  # 用户数据存储目录
│   ├── configs/           # 配置文件
│   └── logs/              # 日志文件
├── /docs/                  # 项目文档目录
├── /tests/                 # 测试代码目录
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── test_data/         # 测试数据
├── /demos/                 # 演示和示例代码
├── /output/                # 生成的报告输出
├── main.py                 # 项目入口点
├── README.md               # 项目说明文档
└── requirements.txt        # Python依赖
```

## 📚 开发文档
详细的开发文档请参考 `docs/` 目录：
- [需求分析文档](docs/requirements-analysis.md) - 项目需求和功能规划
- [架构设计文档](docs/architecture.md) - 系统架构和技术选型
- [XML数据管理架构](docs/xml_data_management_architecture.md) - 可扩展XML架构设计
- [开发状态文档](docs/development-status.md) - 开发进度和任务跟踪
- [项目结构说明](docs/project-structure.md) - 详细的目录结构和文件组织说明

## 🔧 开发指南

### 添加新XML字段
基于字段注册机制，添加新字段非常简单：

```python
# 1. 定义字段
new_field = XMLFieldDefinition(
    field_id="new_field",
    display_name="新字段",
    field_type=FieldType.STRING,
    xml_path=".//new_field",
    group="custom"
)

# 2. 注册字段
field_registry.register_field(new_field)
```

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/
```

## 📊 项目状态
- **当前版本**: v0.2.0-alpha
- **开发状态**: 架构设计阶段
- **完成度**: 架构设计完成，准备进入实施阶段

## 🤝 贡献指南
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证
本项目采用 MIT 许可证。

## 👥 开发团队
- **项目负责人**: 龙sir团队
- **架构设计**: AR (架构师)
- **开发实现**: LD (首席开发)
- **产品管理**: PDM (产品经理)
- **项目管理**: PM (项目经理)
- **文档管理**: DW (文档编写者)
