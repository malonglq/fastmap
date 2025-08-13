# FastMapV2 技术架构设计文档

## 📐 架构概述

### 设计原则
- **高内聚、低耦合**：每个模块职责单一，模块间依赖最小化
- **可扩展性优先**：预留充分的扩展接口和插件机制
- **组件复用**：最大化复用现有的HTML报告生成和数据处理组件
- **分层架构**：清晰的分层结构，便于维护和测试

### 整体架构图
```
┌─────────────────────────────────────────────────────────────┐
│                    GUI Layer (PyQt)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │ Map分析界面  │ │ EXIF处理界面 │ │ 仿写功能界面 │ │ 报告界面 │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Service Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │MapAnalyzer  │ │ExifProcessor│ │OffsetCalc   │ │Reporter│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Core Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │ Data Models │ │ Interfaces  │ │ Managers    │ │ Utils  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │File I/O     │ │Config Mgmt  │ │ Logging     │ │ Plugins│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🏗️ 核心组件设计

### 1. 数据模型层 (core/models/)

#### MapData 模型
```python
@dataclass
class MapPoint:
    """Map点数据模型"""
    alias_name: str
    x: float
    y: float
    weight: float
    bv_range: Tuple[float, float]
    ir_range: Tuple[float, float]
    cct_range: Tuple[float, float]
    detect_flag: bool
    map_type: str  # 'enhance' | 'reduce'
    scene_type: str  # 'indoor' | 'outdoor' | 'night'

@dataclass
class MapConfiguration:
    """Map配置数据模型"""
    device_type: str  # 'reference' | 'debug'
    base_boundary: Dict[str, float]
    map_points: List[MapPoint]
    reference_points: List[Tuple[float, float]]
    metadata: Dict[str, Any]
```

#### ExifData 模型
```python
@dataclass
class ExifField:
    """EXIF字段数据模型"""
    name: str
    value: Any
    data_type: str
    is_processed: bool = False

@dataclass
class ExifData:
    """EXIF数据模型"""
    image_path: str
    device_type: str
    timestamp: datetime
    fields: Dict[str, ExifField]
    processed_data: Dict[str, Any] = field(default_factory=dict)
```

### 2. 服务层 (core/services/)

#### MapAnalyzer 服务
```python
class MapAnalyzer:
    """Map分析服务 - 高内聚的Map分析逻辑"""
    
    def __init__(self, visualizer: IVisualizer, reporter: IReporter):
        self.visualizer = visualizer
        self.reporter = reporter
    
    def analyze_map_distribution(self, map_config: MapConfiguration) -> AnalysisResult:
        """分析Map分布特征"""
        
    def classify_map_types(self, map_points: List[MapPoint]) -> Dict[str, List[MapPoint]]:
        """分类Map类型（强拉/减权重）"""
        
    def analyze_scene_coverage(self, map_points: List[MapPoint]) -> Dict[str, Any]:
        """分析场景覆盖情况"""
        
    def generate_visualization(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """生成可视化数据"""
```

#### ExifProcessor 服务
```python
class ExifProcessor:
    """EXIF处理服务 - 可扩展的字段处理"""
    
    def __init__(self, field_config: Dict[str, bool]):
        self.field_config = field_config
        self.processors = {}  # 可扩展的处理器注册表
    
    def register_processor(self, field_name: str, processor: Callable):
        """注册字段处理器"""
        
    def extract_fields(self, image_path: str) -> ExifData:
        """提取配置的EXIF字段"""
        
    def process_trend_data(self, exif_data_list: List[ExifData]) -> TrendAnalysisResult:
        """处理趋势分析数据"""
        
    def compare_devices(self, ref_data: List[ExifData], debug_data: List[ExifData]) -> ComparisonResult:
        """对比两台设备的数据"""
```

#### OffsetCalculator 服务
```python
class OffsetCalculator:
    """偏移计算服务 - 核心算法实现"""
    
    def calculate_reference_offset(self, ref_points: List[Tuple], debug_points: List[Tuple]) -> OffsetResult:
        """计算参考点偏移量"""
        
    def apply_offset_to_maps(self, map_points: List[MapPoint], offset: OffsetResult) -> List[MapPoint]:
        """应用偏移量到Map坐标"""
        
    def validate_calibration(self, original: List[MapPoint], calibrated: List[MapPoint]) -> ValidationResult:
        """验证校准结果的合理性"""
```

### 3. 复用组件集成策略

#### HTML报告生成器复用
```python
class UnifiedReportGenerator:
    """统一报告生成器 - 复用现有HTML生成能力"""
    
    def __init__(self):
        # 复用现有组件
        self.html_generator = HTMLGenerator()  # 来自0_csv_compare
        self.chart_generator = ChartGenerator()  # 来自0_csv_compare
        
        # 扩展Map专用模板
        self.map_templates = MapTemplateManager()
    
    def generate_map_analysis_report(self, analysis_result: AnalysisResult) -> str:
        """生成Map分析报告"""
        # 1. 数据适配：将Map分析结果转换为HTML生成器期望的格式
        # 2. 模板选择：选择Map专用的HTML模板
        # 3. 图表生成：扩展Chart.js支持Map可视化图表
        # 4. 报告组装：复用现有的HTML组装逻辑
        
    def generate_exif_trend_report(self, trend_result: TrendAnalysisResult) -> str:
        """生成EXIF趋势报告"""
        # 直接复用现有的趋势分析报告生成逻辑
        
    def generate_unified_report(self, map_result: AnalysisResult, exif_result: TrendAnalysisResult) -> str:
        """生成统一的综合报告"""
```

#### 数据处理组件复用
```python
class DataProcessorAdapter:
    """数据处理适配器 - 复用现有数据处理能力"""
    
    def __init__(self):
        # 复用现有组件
        self.trend_analyzer = TrendAnalyzer()  # 来自0_csv_compare
        self.statistics_calc = StatisticsCalculator()  # 来自0_csv_compare
    
    def adapt_exif_data_for_trend_analysis(self, exif_data: List[ExifData]) -> List[Dict]:
        """将EXIF数据适配为趋势分析器期望的格式"""
        
    def analyze_map_parameter_trends(self, map_data: List[MapConfiguration]) -> TrendAnalysisResult:
        """分析Map参数的趋势变化"""
```

## 🔌 扩展接口设计

### 1. 可视化接口
```python
class IVisualizer(ABC):
    """可视化接口 - 支持多种图表类型扩展"""
    
    @abstractmethod
    def create_scatter_plot(self, data: List[MapPoint]) -> PlotResult:
        """创建散点图"""
        
    @abstractmethod
    def create_heatmap(self, data: List[MapPoint]) -> PlotResult:
        """创建热力图"""
        
    @abstractmethod
    def create_range_chart(self, data: List[MapPoint]) -> PlotResult:
        """创建范围图"""

class MatplotlibVisualizer(IVisualizer):
    """Matplotlib实现 - 用于GUI内嵌显示"""
    
class ChartJSVisualizer(IVisualizer):
    """Chart.js实现 - 用于HTML报告"""
```

### 2. 数据处理接口
```python
class IDataProcessor(ABC):
    """数据处理接口 - 支持处理器插件扩展"""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """处理数据"""
        
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """验证数据"""

class ExifFieldProcessor(IDataProcessor):
    """EXIF字段处理器基类"""
    
class MapDataProcessor(IDataProcessor):
    """Map数据处理器基类"""
```

### 3. 特征点接口 (预留)
```python
class IFeaturePointManager(ABC):
    """特征点管理接口 - 预留AI扩展"""
    
    @abstractmethod
    def extract_features(self, image_path: str) -> List[FeaturePoint]:
        """提取特征点"""
        
    @abstractmethod
    def match_with_maps(self, features: List[FeaturePoint], maps: List[MapPoint]) -> MatchResult:
        """特征点与Map匹配"""

class ManualFeaturePointManager(IFeaturePointManager):
    """手动特征点管理器 - 当前实现"""
    
class AIFeaturePointManager(IFeaturePointManager):
    """AI特征点管理器 - 预留接口"""
```

## 🎨 PyQt GUI架构

### 主窗口设计
```python
class MainWindow(QMainWindow):
    """主窗口 - 采用标签页设计"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_services()
        self.setup_signal_slots()
    
    def setup_ui(self):
        """设置UI布局"""
        # 中央标签页控件
        self.tab_widget = QTabWidget()
        
        # 各功能标签页
        self.map_analysis_tab = MapAnalysisTab()
        self.exif_processing_tab = ExifProcessingTab()
        self.copywriting_tab = CopywritingTab()
        self.feature_point_tab = FeaturePointTab()
        self.report_tab = ReportTab()
```

### 标签页组件设计
```python
class MapAnalysisTab(QWidget):
    """Map分析标签页 - 模块化组件设计"""
    
    def __init__(self):
        super().__init__()
        self.map_analyzer = None  # 依赖注入
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI布局"""
        layout = QHBoxLayout()
        
        # 左侧配置面板
        config_panel = self.create_config_panel()
        layout.addWidget(config_panel, 1)
        
        # 右侧结果展示面板
        result_panel = self.create_result_panel()
        layout.addWidget(result_panel, 2)
        
        self.setLayout(layout)
    
    def create_config_panel(self) -> QWidget:
        """创建配置面板 - 可扩展的配置项"""
        
    def create_result_panel(self) -> QWidget:
        """创建结果展示面板 - 支持多种可视化"""
```

## 📊 数据流设计

### 1. Map分析数据流
```
XML文件 → XMLParser → MapConfiguration → MapAnalyzer → AnalysisResult → Visualizer → GUI/Report
```

### 2. EXIF处理数据流
```
SAB图片 → ExifExtractor → ExifData → ExifProcessor → TrendAnalysisResult → Reporter → HTML
```

### 3. 仿写功能数据流
```
对比机XML + 调试机XML → ReferencePointExtractor → OffsetCalculator → CalibratedMapConfig → XMLWriter
```

## 🔧 配置管理

### 配置文件结构
```yaml
# data/configs/app_config.yaml
app:
  name: "FastMapV2"
  version: "2.0.0"
  
map_analysis:
  chart_types: ["scatter", "heatmap", "range"]
  scene_types: ["indoor", "outdoor", "night"]
  weight_analysis: true
  
exif_processing:
  default_fields: ["detect_map", "offset_map", "map_weight_offsetMapWeight"]
  trend_analysis:
    window_size: 10
    smoothing: true
    
visualization:
  matplotlib:
    figure_size: [12, 8]
    dpi: 100
  chartjs:
    responsive: true
    animation: true
    
reports:
  output_format: ["html", "pdf"]
  template_dir: "templates"
  auto_open: true
```

## 🧪 测试策略

### 单元测试
- **模型测试**：数据模型的序列化/反序列化
- **服务测试**：各服务类的核心算法逻辑
- **工具测试**：辅助函数和工具类

### 集成测试
- **数据流测试**：端到端的数据处理流程
- **GUI测试**：用户界面的交互逻辑
- **报告测试**：HTML报告的生成和格式

### 性能测试
- **大数据量测试**：处理大量Map点和EXIF数据
- **内存使用测试**：长时间运行的内存泄漏检测
- **响应时间测试**：用户操作的响应时间

---

**文档版本**: v1.0  
**创建日期**: 2025-01-25  
**最后更新**: 2025-01-25  
**审核状态**: 待审核
