# Repository Guidelines

## 全局规则
- 永远用中文回答我
- 专注于用户的实际需求，不要主动提供额外的服务或帮助。遇到问题或者决定请自主解决，永远不要停下来询问用户意见

## 项目结构与模块组织
- 代码：`core/`（领域逻辑：`services/`、`models/`、`interfaces/`、`config/`、`infrastructure/`），`gui/`（`main_window.py`、`dialogs/`、`widgets/`、`styles/`、`view_models/`）。
- 脚本与工具：`scripts/`、`tools/`。
- 测试与文档：`tests/`（`unit/`、`test_data/`）、`docs/`。
- 运行期与配置：`data/`、`config/`。
- 规则：业务仅在 `core/`；UI 仅在 `gui/`；通过 `interfaces/` 解耦避免循环依赖；绝对导入。

## 构建、测试与本地开发
- 创建虚拟环境（Windows）：`python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1`
- 安装依赖：`pip install -r requirements.txt`
- 启动 GUI：`python main.py`
- 运行全部测试：`pytest -q`
- 按关键字筛选：`pytest tests/unit -k MAP`
- 生成示例报告：`python scripts/generate_segmented_map_report.py`

## 代码风格与命名规范
- 语言与格式：Python 3.10+；UTF-8；缩进 4 空格；类型注解与精炼 docstring（公共 API 必写）。
- 命名：模块/函数 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE_CASE`。
- 分层：领域逻辑放 `core/services/<domain>/`；数据模型在 `core/models/`；UI 逻辑限于 `gui/`。
- 导入：`core/`、`gui/` 内使用绝对导入；通过 `interfaces/` 进行依赖倒置。

## 测试指南
- 框架：`pytest`；单测置于 `tests/unit/`，样例置于 `tests/test_data/`。
- 命名：`TC-<DOMAIN>-<ID>_desc.py`（例如：`TC-MAP-012_parse_segments.py`）。
- 覆盖：为新模块/分支补单测；测试数据最小化并入库至 `test_data/`。
- 运行：`pytest -q`；优先稳定快速用例，必要时使用 `-k` 筛选。

## 提交与 Pull Request
- 提交粒度小且可回滚；必要时添加前缀标签如 `[core]`、`[gui]`、`[tests]`、`[tools]`。
- PR 需附：问题背景、变更说明、关联 Issue；UI/报表变更请附截图或示例 HTML；说明测试范围与手动验证。

## 安全与配置提示（重要）
- 禁止提交密钥/凭据与外部机密。
- `core/0_3a_parser_py/dll/` 二进制文件不改动（除非经明确批准）。
- 修改 `config/` 或 `data/configs/` JSON 时保持向后兼容；字段变更需同步更新测试。

## 额外说明
- 在子目录新增代码时，若存在本文件同级或上级 `AGENTS.md`，其作用域覆盖该目录树；更深层的同名文件优先生效。

## AWB算法核心原理与工作机制

### 算法理论基础
不同的光有不同的光谱能量分布，不同的sensor对光的响应也是不一样的。AWB算法需要通过测量在每个光源下sensor对于标准灰卡的响应，测量出它的R/G B/G ratio，用R/G B/G ratio组成参考点。AWB算法就用这些测量出的参考点，做出一个gray zone来，在拍出的场景利用grayzone和stats的分布，来进行白平衡的还原。

### 参考点系统
- **含义**：每个光源具有不同的光谱能量分布，每个传感器具有不同的光谱灵敏度
- **参考点定义**：在每种标准光源下测量的灰色 R/G 和 B/G 比率，必须针对每个传感器进行测量
- **标准光源序列**：HighCCT12000K、D75、D65、D50、CWF4100K、F4000K、TL843800K、A2850K、H2300K、LOWCCT1500K（共10个点）
- **坐标系**：在二维 R/G B/G 空间中描述色彩偏差，而非传统的RGB三维空间

### 核心架构三要素
1. **参考点系统**：`utils/white_points.py`解析的标准光源参考点，建立灰区判断基础
2. **base_boundary**：定义灰区边界的多边形（0-11号），指示stats是否处于灰区
3. **offset_map**：具体调整策略的多边形（01-116号），定义主要的AWB调整策略

### 几何映射机制
- **真实坐标**：由RpG、BpG数组描述的绝对坐标，传感器采集的统计点被归类进这些多边形内部
- **offset映射**：将多边形（连同其中的统计点）映射到另一块坐标区域
  - 映射位置由`offset_mapXX[0].offset.{x,y}`、`base_boundary0[0].offset.{x,y}`给出
  - 可理解为箭头：起点是原多边形的真实坐标，终点是offset平面的落点
- **映射类型**：
  - **强拉映射（ml=65471）**：映射到单点，目标通常在base_boundary范围内
  - **位移映射（ml=65535）**：整体位移，目标计算为真实几何位置+offset，整个多边形做整体位移

### 权重系统的重要性
- **weight参数**：定义该map在映射新位置的权重，决定对最终白平衡的影响程度
- **多map协同**：多个offset_map可同时生效，按权重组合结果
- **权重示例**：offset_map01 weight=0.2，offset_map03 weight=0.5

### 场景识别与分类
- **greenzone**：绿色植物场景
- **HiMixLow/MidMixLow/LowMixHigh**：不同混合光照条件
- **special**：特殊场景（OPPO店、华为店等）
- **ExtremeLow/BlueMoment**：极端光照条件
- **pureyellow/pureblue**：纯色场景
- **sunset/bluesky/Brightoutdoor/OutdoorScene/Starbucks**：自然和人文场景

### 算法工作流程
1. **数据采集**：传感器采集场景统计数据，计算R/G、B/G比率
2. **几何分析**：确定stats点落在哪些多边形内，计算与参考点距离权重
3. **场景判断**：基于stats分布特征识别场景类型，激活相应offset_map策略
4. **映射计算**：根据ml类型进行强拉或位移映射，按权重组合多个map结果
5. **增益输出**：基于映射后的stats计算AWB增益，输出R、G、B通道增益系数

### 参数配置精妙设计
- **范围控制**：每个map都有严格的range限制（色温、IR、亮度等）
- **过渡处理**：`tranBv`、`tranCtemp`等参数定义过渡范围，避免切换突兀
- **多维度筛选**：通过bv、ctemp、ir、YLevel等多维度参数精确控制

### Baseboundary的灰区作用
根据经验基于参考点和参考线定义的区域，用于筛选给定场景的统计数据。给定统计数据的距离权重是统计数据的一种概率，代表给定统计数据是灰色统计数据的可能性。基于以下观察：部分统计数据由于其与参考点和参考线之间的相对距离极有可能是灰色统计数据。与参考点之间的距离表示统计数据是灰色数据的重要性。

### 工程实现特点
将复杂的色彩科学问题转化为可配置、可优化的几何映射问题，通过基于几何映射的智能白平衡系统，实现场景化的精细化调整策略。