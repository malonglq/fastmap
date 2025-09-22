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

## AWB算法里面的说明
- 在 XML 里有两类多边形：base_boundary0 和 offset_map01…116。它们真实的几何位置就是由各自节点里第一组 RpG、BpG 数组描述的绝对坐标。传感器采集到的统计点被归类进这些多边形内部，AWB/AGW 算法也在这些真实坐标空间里进行运算。
- “offset” 是把上述多边形（连同其中的统计点）映射到另一块坐标区域的描述。这个映射位置由 offset_mapXX[0].offset.{x,y}、base_boundary0[0].offset.{x,y} 给出。可以把它想成一个箭头：起点是原多边形的真实坐标，终点是 offset 平面上的落点，箭头方向就是映射关系。
- 映射也要分两种，一种是ml的类型为强拉（65471），就是映射到一个单点，它映射的目标一般都是在base_boudary的范围里面。还有一种映射是减小权重(65535)，它是整体位移，它的目标的计算方式应该是第一组 RpG、BpG 绝对坐标定义的真实几何位置+offset ，整个map的多边形做一个整体的位移
- OffsetMap分类说明，包括greenzone、HiMixLow、MidMixLow、LowMixHigh、special(包括oppo店、华为店、等等)，ExtremeLow、BlueMoment、MixLight、pureyellow或者pureblue等颜色、sunset、bluesky、Bightoutdoor、OutdoorScene、Starbucks等