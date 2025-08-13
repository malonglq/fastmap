任务1：图片分类导出重构为公共服务
1.1 现状与问题
现状
分类逻辑：core/services/image_classifier_service.py 已独立
导出逻辑：core/services/image_export_service.py 已独立（含重命名后缀）
UI 逻辑：gui/dialogs/image_export_dialog.py 内部串联“选择字段 → 计算统计 → 导出”
问题
复用不便：其它模块需要重复组织分类/统计/导出流程
统计卡片组装逻辑分散在对话框中
1.2 重构目标
保持 ImageExportDialog 功能不变与外观不变
引入一个“工作流服务”作为公共门面，统一封装：
计算分类（传入 match_result + 选中字段）
生成统计卡片数据模型（由 ClassificationResult 派生）
执行导出（传入选择项、命名选项、目录）
UI 仅负责展示/响应，业务流由工作流服务驱动
1.3 新增接口与数据模型
文件：core/interfaces/image_classification.py（在现有接口旁新增）

新增数据模型
StatsCardItem
key: str 例如 total/large_changes/…
title: str
count: int
percentage: float
color: str
StatsPanel
cards: List[StatsCardItem]
total: int
primary_field: str
is_cct_field: bool
新增门面接口
IImageExportWorkflowService
compute_classification(match_result: Dict, options: ClassificationOptions) -> ClassificationResult
build_stats_panel(result: ClassificationResult) -> StatsPanel
export_images(result: ClassificationResult, selection: ExportSelection, source_dir: Path, output_dir: Path, naming: NamingOptions, progress_cb: callable|None) -> ExportStats
备注

不改变 ImageClassifierService 和 ImageExportService 的现有接口
StatsPanel 仅做展示模型，源数据仍来自 ClassificationResult
1.4 新增工作流服务实现
文件：core/services/image_export_workflow_service.py

依赖：
ImageClassifierService
ImageExportService
主要职责：
compute_classification：直接调用 classifier.classify
build_stats_panel：将 ClassificationResult 转为 StatsPanel（卡片标题、颜色、百分比格式化）
export_images：直接调用 exporter.export
设计原则：
KISS：薄门面，不重复已有业务；只负责编排/转换
面向接口编程：便于单元测试替换
1.5 对 ImageExportDialog 的最小化调整
现有 UI 布局与交互不变
内部逻辑变更：
初始化：新建 workflow = ImageExportWorkflowService()
统计卡片刷新：由 workflow.build_stats_panel(result) 提供 StatsPanel，并用现有卡片 UI 更新数值与描述
导出：仍然从 dialog 收集 selection/src/out/naming，调用 workflow.export_images
保障点：
统计卡片的数据来源仍为 classify 的 ClassificationResult
重命名后缀功能不变（NamingOptions + ImageExportService._add_suffix 已按要求实现）
1.6 验收与测试
验收
对话框打开即显示统计；切换主字段统计实时刷新；导出文件命名与之前一致
其它模块可以通过 workflow 复用“分类+统计+导出”
单元测试
新增 tests/unit/test_image_export_workflow.py
mock classifier/exporter，验证工作流编排
build_stats_panel 结果与分类 summary 对应关系
回归 tests/unit/test_image_export_naming.py：确保命名仍正确
任务2：AWB EXIF 解析与导出（新功能）
2.1 目标与边界
目标：
输入：图片文件夹路径（jpg/jpeg/png/bmp）
输出：CSV，包含每张图片的 AWB 相关 EXIF 数据
仅实现 AWB 相关字段解析，不追求全量 EXIF
边界：
复用 0_3a_parser_py 的 DLL 代码，可以新建一个目录存放dll
2.2 接口与数据模型
文件：core/interfaces/exif_processing.py

ExifField 枚举或常量集合（规范化字段名，初始建议）
sensorCCT（色温，K）
AsShotNeutral_R / G / B
RG_Ratio, BG_Ratio（推导值）
WhiteBalanceMode（自动/手动等）
Make, Model（设备信息，便于后续适配）
ExifParseOptions
selected_fields: List[str]
recursive: bool
extensions: List[str] = [".jpg",".jpeg",".png",".bmp"]
ExifRecord
image_path: Path
image_name: str
fields: Dict[str, Any]
errors: Optional[str]
ExifParseResult
records: List[ExifRecord]
total: int
errors: List[str]
available_fields: Set[str]（实际解析到的字段集合）
IExifParserService
parse_directory(root_dir: Path, options: ExifParseOptions) -> ExifParseResult
IExifCsvExporter
export_csv(result: ExifParseResult, csv_path: Path, selected_fields: List[str]) -> Path
说明

字段集合可扩展；解析服务通过“字段解析器注册表”统一管理映射
CSV 导出时动态生成表头（按用户选中的字段）
2.3 服务设计
文件：core/services/exif_parser_service.py

依赖建议：exifread
优点：无损读取 JPEG/TIFF EXIF 标签；跨平台；社区成熟
解析策略：从常见的 EXIF/MakerNote 标签中寻找 AWB 相关信息
字段解析器（FieldResolvers）
设计为一组“规则函数”，从 EXIF 字典中抽取规范化字段；例如：
sensorCCT：
优先从常见标签中读取（如 “Exif.Photo.ColorTemperature”、厂商 MakerNote 映射）
若无，则尝试由 AsShotNeutral 推算（近似，非强制）
WhiteBalanceMode：读取常见标签（Exif.Photo.WhiteBalance 等）
AsShotNeutral_*：读取 “Exif.Photo.AsShotNeutral”
RG_Ratio / BG_Ratio：如能读取各通道增益，则计算比值
错误处理与容错
单张失败不影响整体；记录到 ExifRecord.errors 并继续
CSV 导出
按 selected_fields 生成列
统一加前导列：timestamp, image_name, image_path
缺失字段输出空值
2.4 GUI 设计（新增 Tab）
文件：gui/tabs/exif_processing_tab.py

布局
源图片目录选择（浏览按钮）
字段选择区域（复选框列表）
常用 AWB 字段默认勾选：sensorCCT, WhiteBalanceMode, RG_Ratio, BG_Ratio
全选/全不选按钮
输出 CSV 位置（浏览/默认同目录）
操作区：解析并导出、打开文件夹、打开导出对话框（集成点，见下）
预览表（可选）：解析后显示前 N 行
交互流程
用户选择目录与字段 → 点击“解析并导出”
调用 IExifParserService.parse_directory → 得到 ExifParseResult
调用 IExifCsvExporter.export_csv → 生成 CSV
完成提示，允许打开 CSV/目录
集成按钮：“图片分类导出…”（可选）
初期方案：跳转到 ImageExportDialog，但 available_fields 由 AWB 字段列表提供
后续可扩展“双目录对比”供分类服务使用
2.5 与“图片分类导出”的集成方案
第一阶段（当前交付）
轻集成：新增 Tab 仅完成“解析并导出 CSV”
打开“图片分类导出”时，将 AWB 字段加入可选字段列表（例如 sensorCCT）以便用户在已有流程中选择
若用户需要“对比分类”，仍使用当前的 match_result 来源（对比机/参考机数据）
第二阶段（可选扩展）
在 EXIF Tab 增加“参考目录”输入，实现“双目录对比解析”（test vs reference），将解析结果转为 match_result 结构（pairs）：
以文件名对齐两目录
将解析出的字段填入 pair 的 row1/row2
直接使用 ImageExportWorkflowService 进行分类与导出
优点：整个工作流闭环在 EXIF Tab 内完成
2.6 字段选择与动态列
字段选择界面
从 IExifParserService 暴露的字段注册表/可用字段列表提供候选
默认预选常用字段；支持搜索/全选/全不选
CSV 动态列生成
按 selected_fields 生成列头，未选不导出
兼容导出后用于 DataFrame/后续处理
2.7 测试策略
单元测试
tests/unit/test_exif_parser_service.py
使用小型样例图片或 mock exifread 输出
验证字段解析器、异常容错、记录统计
tests/unit/test_exif_csv_exporter.py
验证动态列生成与空值输出
集成测试（可选）
tests/integration/test_exif_processing_flow.py
指向一个包含少量图片的测试目录，整体跑通并校验 CSV 列头与行数
GUI 冒烟（pytest-qt）
打开 tab、选择目录、点击导出并捕获提示
2.8 依赖与合规
新依赖建议：exifread
安装：pip install exifread
不在本次提交中安装；待您确认后我再按包管理规范添加
目录与文件变更清单（设计）
新增
core/services/image_export_workflow_service.py
core/interfaces/exif_processing.py
core/services/exif_parser_service.py
gui/tabs/exif_processing_tab.py
仅引用（不改或最小改）
gui/dialogs/image_export_dialog.py（改为调用 workflow 服务，但保持功能与UI不变）
core/interfaces/image_classification.py（新增 StatsCardItem/StatsPanel/IImageExportWorkflowService；不破坏现有类型）
测试
tests/unit/test_image_export_workflow.py
tests/unit/test_exif_parser_service.py
tests/unit/test_exif_csv_exporter.py
tests/integration/test_exif_processing_flow.py（可选）
验收标准
公共服务重构
ImageExportDialog 打开 → 统计卡片显示一致；切换主字段统计实时刷新；导出命名符合 +/-% 与字段名规范
新 workflow 服务可在其它模块使用，无需了解具体分类/导出细节
EXIF 解析
单目录解析 + CSV 导出完成；字段选择生效；导出的 CSV 与选中字段一致
CSV 第一列包含 timestamp、image_name、image_path；其后为选中字段
GUI 新 Tab 可完成解析导出流程，支持打开导出文件夹
文档与测试
上述测试用例可运行通过（若需 mock 则提供稳定模拟）
README/帮助内提供“使用说明与注意事项”
风险与应对
AWB 字段跨设备差异大
方案：字段解析器采用“多别名映射+尽力解析”，缺失字段输出空值并记录日志
CCT 推算准确性
方案：尽量使用现成标签；推算作为可选；文档声明误差风险
与分类功能的深度集成
当前仅轻集成；如需对比分类，进入第二阶段“双目录对比”扩展