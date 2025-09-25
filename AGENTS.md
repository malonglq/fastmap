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
不同的光有不同的光谱能量分布，不同的 sensor 对光的响应也不一样。AWB 算法需要通过测量在每个光源下 sensor 对于标准灰卡的响应，得到 R/G、B/G ratio，使用这些 ratio 组成参考点。算法利用参考点构建 gray zone，结合拍摄场景的统计分布实现白平衡还原。

### 参考点系统
- **含义**：每个光源具有不同的光谱能量分布，每个传感器具有不同的光谱灵敏度。
- **参考点定义**：在每种标准光源下测量的灰色 R/G 和 B/G 比率，必须针对每个传感器进行测量。
- **标准光源序列**：HighCCT12000K、D75、D65、D50、CWF4100K、F4000K、TL843800K、A2850K、H2300K、LOWCCT1500K（共 10 个点）。
- **坐标系**：在二维 R/G B/G 空间中描述色彩偏差，而非传统的 RGB 三维空间。

### 核心架构三要素
1. **参考点系统**：`utils/white_points.py` 解析的标准光源参考点，建立灰区判断基础。
2. **base_boundary**：定义灰区边界的多边形（0-11 号），指示统计点是否处于灰区。
3. **offset_map**：具体调整策略的多边形（01-116 号），定义主要的 AWB 调整策略。

### 几何映射机制
- **真实坐标**：由 RpG、BpG 数组描述的绝对坐标，传感器采集的统计点被归类进这些多边形内部。
- **offset 映射**：将多边形（连同其中的统计点）映射到另一块坐标区域，映射位置由 `offset_mapXX[0].offset.{x,y}`、`base_boundary0[0].offset.{x,y}` 给出，可理解为箭头：起点是真实坐标，终点是 offset 平面的落点。
- **映射类型**：
  - **强拉映射（ml=65471）**：映射到单点，目标通常在 base_boundary 范围内。
  - **位移映射（ml=65535）**：整体位移，目标为真实几何位置 + offset，使整个多边形整体移动。
- **坐标与增益关系**：offset 目标越靠近左上角意味着 R/G 减小、B/G 增大，对应的 R 通道增益（1÷R/G）会增大、B 通道增益减小，整体呈现更暖的校正倾向；越靠右下则相反，更偏冷。

### 权重系统的重要性
- **weight 参数**：定义 map 在映射新位置的权重，决定对最终白平衡的影响程度。
- **多 map 协同**：多个 offset_map 可同时生效，按权重组合结果。
- **权重示例**：`offset_map01` weight=0.2，`offset_map03` weight=0.5。

### 场景识别与分类
- **greenzone**：绿色植物场景。
- **HiMixLow/MidMixLow/LowMixHigh**：不同混合光照条件。
- **special**：特殊场景（如 OPPO 店、华为店等）。
- **ExtremeLow/BlueMoment**：极端光照条件。
- **pureyellow/pureblue**：纯色场景。
- **sunset/bluesky/Brightoutdoor/OutdoorScene/Starbucks**：自然与人文场景。

### 算法工作流程
1. **数据采集**：传感器采集场景统计数据，计算 R/G、B/G 比率。
2. **几何分析**：确定统计点落在哪些多边形内，计算与参考点距离权重。
3. **场景判断**：基于统计分布特征识别场景类型，激活相应 offset_map 策略。
4. **映射计算**：根据 ml 类型进行强拉或位移映射，按权重组合多个 map 结果。
5. **增益输出**：基于映射后的统计点计算 AWB 增益，输出 R、G、B 通道增益系数。

### 参数配置精妙设计
- **范围控制**：每个 map 都有严格的 range 限制（色温、IR、亮度等）。
- **过渡处理**：`tranBv`、`tranCtemp` 等参数定义过渡范围，避免切换突兀。
- **多维度筛选**：通过 bv、ctemp、ir、YLevel 等多维度参数精确控制。

### Baseboundary 的灰区作用
根据经验基于参考点和参考线定义的区域，用于筛选给定场景的统计数据。给定统计数据的距离权重代表该统计点为灰色统计数据的可能性。统计点与参考点之间的距离决定其灰度概率的重要性。

### 工程实现特点
将复杂的色彩科学问题转化为可配置、可优化的几何映射问题，通过基于几何映射的智能白平衡系统，实现场景化的精细化调整策略。
