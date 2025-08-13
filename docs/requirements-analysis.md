# 对比机Map分析&仿写工具 - 需求分析文档

## 📋 项目概述

### 项目名称
FastMapV2 - 对比机Map分析&仿写工具

### 项目目标
开发一个基于PyQt的桌面应用程序，用于分析对比机和调试机的Map配置差异，提供可视化分析报告，并实现Map配置的自动校准和仿写功能。

### 核心价值
- **提高调试效率**：通过对比机参考数据快速校准调试机Map配置
- **可视化分析**：直观展示Map分布、权重、触发条件等关键信息
- **自动化仿写**：基于偏移量计算自动生成校准后的Map配置
- **标准化流程**：建立统一的Map分析和校准工作流程

## 🎯 功能需求

### Phase 1: Map画图展示与分析报告 (优先级: 最高)

#### 1.1 Map数据解析与处理
- **XML解析器**：扩展现有showmap.py的XML处理能力
  - 解析offset_map数据：AliasName、坐标(x,y)、权重、触发条件
  - 提取BaseBoundary数据：RpG、BpG参考值
  - 支持批量XML文件处理
  - 数据验证和错误处理

#### 1.2 Map可视化功能
- **坐标散点图**：显示所有Map点的x,y坐标分布
- **权重热力图**：根据weight值生成热力分布图
- **触发条件范围图**：展示BV、IR、CCT等参数的范围分布
- **场景分类统计**：室内外夜景等场景的Map分布统计

#### 1.3 分析报告生成
- **场景分析**：
  - 室内场景Map分布和特征
  - 室外场景Map分布和特征  
  - 夜景场景Map分布和特征
- **参考点分析**：识别哪些参考点附近设置了Map
- **Map类型分析**：区分强拉类型和减小权重类型的Map
- **HTML报告**：复用现有HTML生成器，生成交互式分析报告

### Phase 2: EXIF读取与处理 (优先级: 高)

#### 2.1 EXIF数据提取
- **字段选择器**：可配置的字段提取功能
  - 核心字段：detect_map、offset_map、map_weight_offsetMapWeight
  - 扩展字段接口：支持后续添加更多字段
- **批量处理**：支持SAB场景图片的批量EXIF提取
- **数据格式化**：统一的数据格式和结构

#### 2.2 趋势分析功能
- **参数趋势分析**：分析IR、sensorCCT、BV等参数的变化趋势
- **对比机vs调试机**：同场景下两台设备的参数对比
- **数据处理管道**：可扩展的数据处理函数接口（占位符实现）

#### 2.3 HTML报告集成
- **复用报告生成器**：与Phase 1的HTML报告功能整合
- **趋势图表**：集成Chart.js生成交互式趋势图
- **统计分析**：详细的统计指标和分析结论

### Phase 3: 仿写功能 (优先级: 中)

#### 3.1 偏移量计算
- **参考点解析**：从XML中提取对比机和调试机的参考点
- **偏移算法**：计算坐标偏移量(Δx, Δy)和参数偏移
- **统计分析**：偏移量的统计分布和显著性检验

#### 3.2 Map坐标校准
- **坐标变换**：基于偏移量计算校准后的Map坐标
- **参数调整**：权重和触发条件的智能调整建议
- **验证机制**：校准结果的合理性验证

#### 3.3 XML覆写功能
- **安全备份**：原始XML文件的自动备份
- **精确覆写**：只修改需要校准的Map配置项
- **格式保持**：保持原XML文件的格式和结构
- **操作日志**：详细记录所有修改操作

### Phase 4: 特征点功能 (优先级: 低，预留接口)

#### 4.1 接口设计
- **FeaturePointManager**：特征点管理器接口
- **手动标注支持**：JSON格式的特征点数据处理
- **AI标注预留**：为未来AI自动标注功能预留接口

#### 4.2 关联匹配
- **特征点与Map关联**：建立特征点和Map配置的对应关系
- **场景识别**：基于特征点的场景自动识别
- **匹配算法**：智能匹配算法的接口定义

## 🏗️ 技术架构

### 架构原则
- **高内聚、低耦合**：模块间依赖最小化，功能内聚性最大化
- **可扩展性**：预留充分的扩展接口和插件机制
- **可复用性**：核心业务逻辑可在不同模块间复用
- **可测试性**：每个模块都支持独立的单元测试

### 技术栈
- **GUI框架**：PyQt5/6 - 现代化的桌面应用界面
- **数据处理**：pandas, numpy - 高效的数据分析和处理
- **可视化**：matplotlib, Chart.js - 多样化的图表展示
- **报告生成**：Jinja2, HTML/CSS/JS - 专业的报告模板
- **文件处理**：xml.etree.ElementTree, json - 标准的文件格式支持

## 🔧 可扩展XML数据管理架构

### 架构概述
采用**字段注册机制**和**动态GUI生成**的设计理念，通过抽象接口和工厂模式实现高度可扩展的XML数据管理系统。该架构解决了以下核心需求：

1. **XML字段管理系统**：支持动态添加新的XML字段（如detectmap、base_boundary1等）
2. **GUI内XML编辑功能**：用户可在GUI界面直接编辑XML内容
3. **数据持久化**：编辑后的内容正确回写到XML文件
4. **复制粘贴功能**：支持Map行数据的复制粘贴操作

### 核心组件设计

#### 1. 字段定义系统
```python
# 字段类型枚举
class FieldType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    RANGE = "range"        # (min, max)元组
    COORDINATE = "coordinate"  # (x, y)坐标
    ARRAY = "array"        # 数组类型
    POLYGON = "polygon"    # 多边形顶点

# 字段定义数据类
@dataclass
class XMLFieldDefinition:
    field_id: str                    # 唯一标识符
    display_name: str               # 显示名称
    field_type: FieldType           # 字段类型
    xml_path: str                   # XML路径表达式
    default_value: Any              # 默认值
    validation_rules: List[ValidationRule] = None
    is_editable: bool = True        # 是否可编辑
    is_visible: bool = True         # 是否默认显示
    group: str = "default"          # 字段分组
    description: str = ""           # 字段描述
```

#### 2. 字段注册中心
```python
class FieldRegistry:
    """字段注册中心 - 管理所有可用字段"""

    def register_field(self, field_def: XMLFieldDefinition):
        """注册新字段"""

    def get_field(self, field_id: str) -> Optional[XMLFieldDefinition]:
        """获取字段定义"""

    def get_visible_fields(self) -> List[XMLFieldDefinition]:
        """获取可见字段"""

    def get_fields_by_group(self, group: str) -> List[XMLFieldDefinition]:
        """按组获取字段"""
```

#### 3. 字段编辑器接口
```python
class FieldEditor(ABC):
    """字段编辑器抽象接口"""

    @abstractmethod
    def create_widget(self, parent: QWidget) -> QWidget:
        """创建编辑控件"""

    @abstractmethod
    def set_value(self, value: Any) -> None:
        """设置值"""

    @abstractmethod
    def get_value(self) -> Any:
        """获取值"""

    @abstractmethod
    def validate(self) -> bool:
        """验证输入"""
```

#### 4. 数据绑定系统
```python
class XMLDataBinder:
    """XML数据绑定器 - 负责GUI与XML数据的双向绑定"""

    def bind_field(self, field_id: str, widget: QWidget, editor: FieldEditor):
        """绑定字段到控件"""

    def sync_from_data_source(self):
        """从数据源同步到GUI"""

    def sync_to_data_source(self):
        """从GUI同步到数据源"""
```

### GUI组件扩展

#### 5. 动态表格组件
```python
class DynamicMapTableWidget(QTableWidget):
    """动态Map表格控件 - 根据字段定义自动生成列"""

    def configure_fields(self, field_ids: List[str]):
        """配置要显示的字段"""

    def copy_selected_row(self):
        """复制选中的行"""

    def paste_row(self):
        """粘贴行到新位置"""
```

#### 6. 字段配置界面
```python
class FieldConfigDialog(QDialog):
    """字段配置对话框 - 用户可选择显示哪些字段"""

    def setup_ui(self):
        """根据字段分组设置界面"""
```

### XML读写统一处理

#### 7. 增强的XML解析器
```python
class EnhancedXMLParser(XMLParser):
    """增强的XML解析器 - 支持动态字段解析"""

    def parse_xml_with_dynamic_fields(self, xml_path: str) -> MapConfiguration:
        """使用动态字段解析XML"""
```

#### 8. XML写入器
```python
class XMLWriter:
    """XML写入器 - 支持新增Map点和字段回写"""

    def write_configuration(self, config: MapConfiguration, output_path: str):
        """写入配置到XML文件"""

    def add_new_map_point(self, root: ET.Element, map_point: MapPoint, map_index: int):
        """添加新的Map点到XML"""
```

### 扩展新字段的标准流程

#### 添加新字段示例（如base_boundary1）
```python
# 1. 定义字段
base_boundary1_field = XMLFieldDefinition(
    field_id="base_boundary1",
    display_name="基础边界1",
    field_type=FieldType.COORDINATE,
    xml_path=".//base_boundary1",
    default_value=(0.0, 0.0),
    group="boundaries"
)

# 2. 注册字段
field_registry.register_field(base_boundary1_field)

# 3. 扩展数据模型（如需要）
@dataclass
class MapConfiguration:
    base_boundary1: Optional[BaseBoundary] = None  # 新增字段

# 4. 扩展XML解析器（如需要）
def _extract_base_boundary1_data(self, root: ET.Element):
    """提取base_boundary1数据"""
```

**修改文件数量**：3个文件，约10-15行代码

#### 复制粘贴Map行功能
支持完整的Map行复制粘贴，包括：
- offset_mapXX[0]的所有字段（offset、range、weight等）
- offset_mapXX[1]的所有字段（RpG、BpG、AliasName等）
- 自动生成新的Map ID
- 完整的XML结构复制

**修改文件数量**：4个文件，约100-150行代码

### 架构优势

1. **高度可扩展性**：通过字段注册机制，添加新字段只需要配置，无需修改核心代码
2. **类型安全**：每个字段都有明确的类型定义和验证规则
3. **GUI自适应**：界面组件根据字段定义自动调整
4. **数据一致性**：双向绑定确保GUI和XML数据的实时同步
5. **向后兼容**：扩展现有代码而不破坏已有功能
6. **用户友好**：提供字段配置界面，用户可以自定义显示字段

### 实施计划

1. **第一阶段**：实现核心接口和字段注册系统
2. **第二阶段**：扩展现有MapTableWidget支持动态列
3. **第三阶段**：实现基本字段编辑器和数据绑定
4. **第四阶段**：添加字段配置界面和XML写入功能
5. **第五阶段**：实现复制粘贴功能和高级编辑器

### 核心组件复用策略

#### HTML报告生成器复用
```python
# 现有组件
HTMLGenerator (0_csv_compare/core/report_generator/html_generator.py)
ChartGenerator (0_csv_compare/core/report_generator/chart_generator.py)

# 复用方案
1. 抽象化报告生成接口
2. 扩展图表类型支持Map可视化
3. 模板化报告结构，支持不同数据类型
4. 统一的数据准备和格式化流程
```

#### 数据处理组件复用
```python
# 现有组件  
CSVReader (0_csv_compare/core/data_processor/csv_reader.py)
TrendAnalyzer (0_csv_compare/core/analyzer/trend_analyzer.py)
StatisticsCalculator (0_csv_compare/core/analyzer/statistics.py)

# 复用方案
1. 抽象化数据读取接口，支持XML和EXIF数据
2. 扩展趋势分析算法，适配Map数据特征
3. 统一的统计计算框架
4. 可配置的数据处理管道
```

## 📁 项目目录结构

```
/fastmapv2/
├── /core/                  # 核心业务逻辑模块
│   ├── models/            # 数据模型定义
│   │   ├── map_data.py    # Map数据模型
│   │   ├── exif_data.py   # EXIF数据模型
│   │   └── analysis_result.py # 分析结果模型
│   ├── services/          # 业务服务层
│   │   ├── map_analyzer.py    # Map分析服务
│   │   ├── exif_processor.py  # EXIF处理服务
│   │   ├── offset_calculator.py # 偏移计算服务
│   │   └── report_generator.py # 报告生成服务
│   ├── managers/          # 管理器类
│   │   ├── data_manager.py    # 数据管理器
│   │   ├── config_manager.py  # 配置管理器
│   │   └── plugin_manager.py  # 插件管理器
│   └── interfaces/        # 接口定义
│       ├── data_processor.py  # 数据处理接口
│       ├── visualizer.py     # 可视化接口
│       └── feature_point.py  # 特征点接口
├── /gui/                   # PyQt GUI模块
│   ├── main_window.py     # 主窗口
│   ├── widgets/           # 自定义控件
│   ├── dialogs/           # 对话框
│   └── resources/         # 资源文件
├── /utils/                 # 工具类和辅助函数
│   ├── helpers/           # 通用辅助函数
│   ├── validators/        # 数据验证器
│   ├── formatters/        # 格式化工具
│   └── constants/         # 常量定义
├── /data/                  # 用户数据存储目录
│   ├── configs/           # 配置文件
│   ├── logs/              # 日志文件
│   └── backups/           # 备份文件
├── /docs/                  # 项目文档目录
│   ├── development-status.md    # 开发状态跟踪文档
│   ├── code-review.md          # 代码检查与问题记录文档
│   ├── api-documentation.md    # API文档
│   ├── user-guide.md          # 用户指南
│   └── architecture.md        # 架构文档
├── /tests/                 # 测试代码目录
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── fixtures/          # 测试数据和模拟对象
├── main.py                 # 项目入口点
├── README.md               # 项目说明文档
└── requirements.txt        # Python依赖
```

## 🔧 开发计划

### Phase 1 开发计划 (2-3周) - Map画图展示与分析报告
1. **Week 1**:
   - 项目架构搭建，按标准目录结构创建项目
   - PyQt主界面框架，5个标签页的基础布局
   - 复用现有HTML生成器和Chart生成器组件
2. **Week 2**:
   - 扩展XML解析功能，支持Map数据提取和分类
   - 实现Map可视化功能（散点图、热力图、范围图）
   - 场景分析逻辑（室内外夜景、Map类型识别）
3. **Week 3**:
   - 集成HTML报告生成，扩展Map专用模板
   - GUI与服务层集成，完善用户交互
   - 单元测试和功能测试

### Phase 2 开发计划 (2-3周) - EXIF读取与处理
1. **Week 1**:
   - 扩展现有EXIF处理模块，实现字段过滤功能
   - 设计可配置的字段选择器界面
   - 实现数据处理管道的占位符接口
2. **Week 2**:
   - 复用现有趋势分析算法，适配EXIF数据
   - 实现IR、sensorCCT、BV趋势分析功能
   - 对比机vs调试机的数据对比逻辑
3. **Week 3**:
   - 集成HTML报告生成，复用现有图表组件
   - 完善EXIF处理界面和用户体验
   - 集成测试和性能优化

### Phase 3 开发计划 (2-3周) - 仿写功能
1. **Week 1**:
   - 实现参考点解析和偏移量计算算法
   - 设计XML安全读写机制，支持备份和恢复
   - 坐标变换和校准算法实现
2. **Week 2**:
   - 实现Map坐标校准和参数调整功能
   - XML覆写功能，保持原文件格式
   - 校准结果验证和合理性检查
3. **Week 3**:
   - 完善仿写功能界面和操作流程
   - 安全机制和错误处理
   - 功能测试和用户验收

### Phase 4 开发计划 (1周) - 特征点功能预留
1. **接口设计**:
   - 定义FeaturePointManager接口
   - 设计手动标注和AI标注的统一接口
2. **占位实现**:
   - 实现基础的占位符功能和界面
   - JSON格式特征点数据的读写支持
3. **文档完善**:
   - 扩展接口的使用文档和示例
   - 为未来AI集成预留的技术方案

## 📊 验收标准

### 功能验收
- **Map分析准确性**：正确识别和分类不同类型的Map
- **可视化效果**：图表清晰、交互流畅、信息完整
- **报告质量**：HTML报告内容丰富、格式专业、可打印
- **处理性能**：单组数据分析时间<30秒
- **偏移计算精度**：坐标偏移量计算精度达到小数点后2位

### 技术验收
- **代码质量**：遵循PEP8规范，代码覆盖率>80%
- **架构合理性**：模块间耦合度低，扩展性好
- **用户体验**：界面友好，操作直观，错误处理完善
- **兼容性**：支持Windows 10+，Python 3.8+

## 🚀 扩展规划

### 短期扩展 (3-6个月)
- **AI特征点标注**：集成机器学习模型自动标注特征点
- **批处理功能**：支持多组数据的批量分析和处理
- **高级可视化**：3D Map分布图、动态趋势图

### 长期扩展 (6-12个月)
- **云端协作**：支持团队协作和数据共享
- **移动端支持**：开发移动端查看和简单操作功能
- **API接口**：提供REST API供其他系统集成

---

**文档版本**: v1.0  
**创建日期**: 2025-01-25  
**最后更新**: 2025-01-25  
**审核状态**: 待审核
