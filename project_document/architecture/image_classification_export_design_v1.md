# 图片分类导出功能需求规格说明书（FastMapV2）

{{CHENGQI:
Action: Modified; Timestamp: 2025-08-11 10:45:00 +08:00; Reason: 将设计文档升级为可执行的需求规格，便于他人/AI直接开发实现; Principle_Applied: KISS, SOLID, Testability;
}}

## 0. 概述
- 目标：在 EXIF 对比分析基础上，按“用户选定的主字段”的变化幅度对匹配到的图片进行分档分类，并按用户勾选导出到指定目录，文件名附带变化值标识。
- 禁止：不得复用 0_csv_compare 中的任何实现；仅可参考业务逻辑。
- 适配：遵循 FastMapV2 架构（core/interfaces、core/services、gui/dialogs），日志前缀统一 `==liuq debug==`。

## 1. 术语与数据
- 匹配对（Pair）：来自 EXIF 对比模块数字序列号匹配的单条匹配，含测试/对比两侧整行数据和原始文件名。
- 主字段（Primary Field）：用户在对话框中选择的用于分档的字段（如 SGW_Gray、sensorCCT 等）。
- CCT 字段：字段名包含 `sensorcct`（大小写不敏感）或用户明确指定为 CCT 时，按绝对值(K)规则分类；其余按百分比规则分类。

### 1.1 输入/输出契约
- 输入：
  - match_result: Dict，至少包含 `pairs: List[Pair]`；每个 Pair 须能访问到 test/reference 的该字段值与 `filename1`（源名）。
  - 用户配置：
    - primary_field: str（必选，由用户在对话框中选择）
    - selected_fields: List[str]（可选，用于在导出清单中展示详情）
    - thresholds: 见 2.2（可使用默认值）
    - categories_to_export: {large|medium|small|no_change}: bool
    - source_directory: str，output_directory: str
- 输出：
  - 分类结果 ClassificationResult：见 2.1
  - 导出统计 ExportStats：见 2.3

## 2. 业务规则
### 2.1 分类结果结构（必须遵循）
- categories: Dict[str, List[ImageInfo]] 四类键固定：`large_changes`/`medium_changes`/`small_changes`/`no_changes`
- ImageInfo：
  - image_name: str（来自 Pair.filename1）
  - primary_field_change: float（两侧差值：CCT 用绝对值(K)，百分比用 0–100）
  - is_cct_field: bool
  - primary_field_name: str
  - field_changes: Dict[str, {before, after, change_percentage(float|None), absolute_change(float|None)}]
  - pair_data: Any（原始 pair 透传，便于后续扩展）
- summary：每类 {count:int, percentage:float(1位小数)}，total: int

### 2.2 阈值与分档规则（默认值 + 可配置）
- CCT（单位：K）
  - 默认：大变化 >500；中变化 100–500；小变化 0–100(不含0)；无变化 =0
  - 计算：absolute_change = |after - before|，保留 2 位小数用于展示
- 非 CCT（百分比）
  - 默认：大变化 >10%；中变化 1%–10%；小变化 0%–1%(不含0)；无变化 =0%
  - 计算：
    - 若 before=0 且 after!=0 → 100%
    - 否则 percentage = |after - before| / |before| * 100
    - 保留 2 位小数用于展示
- 字段是否为 CCT 的判定优先级：用户指定 > 字段名包含“sensorcct” > 默认为百分比

### 2.3 导出规则与统计
- 目录结构：在 output_directory 下创建 4 个子目录：
  - `1_large_changes/`、`2_medium_changes/`、`3_small_changes/`、`4_no_changes/`
- 源文件查找（大小写不敏感，按以下顺序）：
  1) 精确匹配 image_name
  2) 若无扩展名或未找到：尝试 `.jpg,.jpeg,.png,.bmp`
  3) 常见尾缀变体：尝试移除/添加 `_ori`, `-ori`
  4) 若文件名以数字序列号开头（^\d+），在目录内优先查找同序号开头的候选；若命中多个则放弃该策略以避免误配
- 重命名：
  - 百分比：在扩展名前插入 `_chg{X.YY}pct`
  - CCT：在扩展名前插入 `_chg{int(K)}K`
  - 冲突：若目标已存在，按 `name(1).ext`, `name(2).ext` 递增
- 统计（ExportStats）：
  - started_at/finished_at、duration_seconds
  - copied_counts: per-category 与 total
  - missing_files: List[str]
  - chosen_categories: set

## 3. 非功能性需求
- 性能：以 5k 张图片为量级，分类在秒级，导出受 IO 限制；单线程即可，必要时预留并发开关（默认关闭）。
- 可靠性：找不到源文件不得中断；记录缺失清单。
- 可测试性：分类与导出逻辑完全可用单元测试验证；路径操作使用 pathlib。
- 可观察性：关键路径打印 `==liuq debug==` 日志（开始/阈值/各类数量/复制结果/缺失统计）。

## 4. 模块与接口
### 4.1 接口（core/interfaces）
- IImageClassifierService
  - classify(match_result: Dict, options: ClassificationOptions) -> ClassificationResult
- IImageExportService
  - export(classification: ClassificationResult, selection: ExportSelection, source_dir: Path, output_dir: Path, naming: NamingOptions, progress_cb: Optional[callable]=None) -> ExportStats

### 4.2 数据模型（建议 dataclass）
- ClassificationOptions: primary_field:str, selected_fields:List[str], thresholds:ChangeThresholds, is_cct_field:Optional[bool]
- ChangeThresholds:
  - cct_large_min=500, cct_medium_min=100, cct_medium_max=500
  - pct_large_min=10, pct_medium_min=1, pct_medium_max=10
- ExportSelection: export_large:bool, export_medium:bool, export_small:bool, export_no_change:bool
- NamingOptions: percent_format:'_chg{:.2f}pct', cct_format:'_chg{}K'
- ImageInfo / ClassificationResult / ExportStats：如 2.1 与 2.3 所述

## 5. GUI 需求（PyQt）
- 新建 `gui/dialogs/image_export_dialog.py`
  - 输入：match_result（由 EXIF 对话框传入）
  - 组件：
    - 统计卡（总数与四类数量）
    - 主字段选择下拉（从匹配字段中列出，允许搜索）
    - 阈值说明（随字段类型切换）
    - 导出类别复选（大/中/小/无），全选/全不选
    - 源目录、输出目录选择（QFileDialog）
    - 进度条（QProgressDialog），可取消
  - 行为：
    - 点击“开始导出”后禁用设置区；进度更新；完成后弹出摘要（导出数/缺失数/输出目录）
- 集成位置：`gui/dialogs/exif_comparison_dialog.py` 中新增“图片分类导出…”按钮；
  - 触发条件：已有 match_result，否则先调用预览匹配生成一次

## 6. 接口用例（伪代码）
- 分类
```
svc = ImageClassifierService()
opts = ClassificationOptions(primary_field='sgw_gray', selected_fields=['agw_gray'], thresholds=ChangeThresholds())
result = svc.classify(match_result, opts)
```
- 导出
```
exp = ImageExportService()
sel = ExportSelection(True, True, False, True)
stats = exp.export(result, sel, Path('D:/src'), Path('D:/out'), NamingOptions())
```

## 7. 验收标准（必须全部满足）
- 功能
  - 能正确读取 match_result 并按 2.2 规则产出分类结果（summary 与 categories 数量一致）
  - 导出时为每类创建子目录，复制文件并按 2.3 命名规范重命名；冲突时正确递增
  - 允许用户选择主字段与导出类别；GUI 可正常浏览目录并显示进度
- 健壮性
  - 源目录缺少文件不会中断；missing_files 记录真实缺失列表
  - before=0 的百分比计算按 100% 处理
  - 日志包含关键节点的 `==liuq debug==` 字样
- 代码质量
  - 不依赖 0_csv_compare 任何实现；代码位于新文件（interfaces/services/dialogs）
  - 单元测试覆盖：阈值边界、before=0、文件查找变体、命名冲突

## 8. 测试计划
- 单元测试（tests/unit）
  - test_image_classifier_service.py：CCT 与 百分比各 6 个边界用例
  - test_image_export_service.py：
    - 源文件大小写/扩展名/后缀变体/序号前缀辅助
    - 命名冲突生成
- 冒烟（demos/smoke_image_export.py）
  - 生成临时源目录与若干伪造对，运行导出并打印 ExportStats

## 9. 路径与任务
- 新增：
  - core/interfaces/image_classification.py
  - core/interfaces/image_export.py
  - core/services/image_classifier_service.py
  - core/services/image_export_service.py
  - gui/dialogs/image_export_dialog.py
  - demos/smoke_image_export.py
- 集成：在 exif_comparison_dialog.py 内新增按钮与调用

## 10. 里程碑与回滚
- 里程碑 M1：服务与单元测试完成（无 GUI）
- 里程碑 M2：GUI 对话框与集成完成
- 回滚策略：不改动现有 EXIF 报告功能；新功能为独立入口，异常时不影响原报告流程。

