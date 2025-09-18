# {{CHENGQI:
# Action: Added; Timestamp: 2025-08-04 16:40:00 +08:00; Reason: 创建分析配置对话框以支持多维度分析报告的阈值配置功能; Principle_Applied: 用户界面设计和配置管理;
# }}

"""
分析配置对话框

提供场景分类阈值的GUI配置界面
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                           QLabel, QDoubleSpinBox, QLineEdit, QTextEdit, 
                           QPushButton, QGroupBox, QMessageBox, QFileDialog,
                           QDialogButtonBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.models.scene_classification_config import SceneClassificationConfig, get_default_config_path

logger = logging.getLogger(__name__)


class AnalysisConfigDialog(QDialog):
    """
    分析配置对话框
    
    提供场景分类阈值的可视化配置界面
    """
    
    # 配置更新信号
    config_updated = pyqtSignal(SceneClassificationConfig)
    
    def __init__(self, parent=None, config: SceneClassificationConfig = None):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
            config: 初始配置对象
        """
        super().__init__(parent)
        self.config = config or SceneClassificationConfig()
        self.setup_ui()
        self.load_config_to_ui()
        
        logger.info("==liuq debug== 分析配置对话框初始化完成")
    
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("多维度分析配置")
        self.setModal(True)
        self.resize(500, 600)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("Map数据多维度分析配置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # 配置信息组
        self.create_config_info_group(main_layout)
        
        # 阈值配置组
        self.create_threshold_group(main_layout)
        
        # 分类规则说明组
        self.create_rules_explanation_group(main_layout)
        
        # 按钮组
        self.create_button_group(main_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QDoubleSpinBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
        """)
    
    def create_config_info_group(self, parent_layout):
        """创建配置信息组"""
        group = QGroupBox("配置信息")
        layout = QFormLayout(group)
        
        # 配置名称
        self.config_name_edit = QLineEdit()
        self.config_name_edit.setPlaceholderText("输入配置名称")
        layout.addRow("配置名称:", self.config_name_edit)
        
        # 配置描述
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("输入配置描述")
        layout.addRow("配置描述:", self.description_edit)
        
        parent_layout.addWidget(group)
    
    def create_threshold_group(self, parent_layout):
        """创建阈值配置组"""
        group = QGroupBox("分类阈值配置")
        layout = QFormLayout(group)
        
        # BV室外阈值
        self.bv_outdoor_spin = QDoubleSpinBox()
        self.bv_outdoor_spin.setRange(0.0, 100.0)
        self.bv_outdoor_spin.setDecimals(1)
        self.bv_outdoor_spin.setSuffix(" (BV值)")
        self.bv_outdoor_spin.setToolTip("BV值大于此阈值时判断为室外场景")
        layout.addRow("BV室外阈值:", self.bv_outdoor_spin)
        
        # BV室内下限
        self.bv_indoor_min_spin = QDoubleSpinBox()
        self.bv_indoor_min_spin.setRange(0.0, 50.0)
        self.bv_indoor_min_spin.setDecimals(1)
        self.bv_indoor_min_spin.setSuffix(" (BV值)")
        self.bv_indoor_min_spin.setToolTip("BV值小于此值时判断为夜景场景")
        layout.addRow("BV室内下限:", self.bv_indoor_min_spin)
        
        # IR室外阈值
        self.ir_outdoor_spin = QDoubleSpinBox()
        self.ir_outdoor_spin.setRange(0.0, 1000.0)
        self.ir_outdoor_spin.setDecimals(1)
        self.ir_outdoor_spin.setSuffix(" (IR值)")
        self.ir_outdoor_spin.setToolTip("IR值大于此阈值时判断为室外场景")
        layout.addRow("IR室外阈值:", self.ir_outdoor_spin)
        
        parent_layout.addWidget(group)
    
    def create_rules_explanation_group(self, parent_layout):
        """创建分类规则说明组"""
        group = QGroupBox("分类规则说明")
        layout = QVBoxLayout(group)
        
        rules_text = """
<b>场景分类规则：</b><br>
<br>
<b>🌃 夜景场景：</b><br>
• BV_min < BV室内下限<br>
<br>
<b>🏞️ 室外场景：</b><br>
• BV_min > BV室外阈值，或<br>
• IR_min > IR室外阈值<br>
<br>
<b>🏠 室内场景：</b><br>
• BV室内下限 ≤ BV_min ≤ BV室外阈值，且<br>
• IR_min ≤ IR室外阈值<br>
<br>
<i>注：直接使用IR范围的最小值进行判断</i>
        """
        
        rules_label = QLabel(rules_text)
        rules_label.setWordWrap(True)
        rules_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        layout.addWidget(rules_label)
        
        parent_layout.addWidget(group)
    
    def create_button_group(self, parent_layout):
        """创建按钮组"""
        button_layout = QHBoxLayout()
        
        # 加载配置按钮
        load_btn = QPushButton("加载配置")
        load_btn.clicked.connect(self.load_config_from_file)
        button_layout.addWidget(load_btn)
        
        # 保存配置按钮
        save_btn = QPushButton("保存配置")
        save_btn.clicked.connect(self.save_config_to_file)
        button_layout.addWidget(save_btn)
        
        # 重置按钮
        reset_btn = QPushButton("重置默认")
        reset_btn.clicked.connect(self.reset_to_default)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        # 标准对话框按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_config)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)
        
        parent_layout.addLayout(button_layout)
    
    def load_config_to_ui(self):
        """将配置加载到UI"""
        try:
            self.config_name_edit.setText(self.config.config_name)
            self.description_edit.setPlainText(self.config.description)
            
            self.bv_outdoor_spin.setValue(self.config.bv_outdoor_threshold)
            self.bv_indoor_min_spin.setValue(self.config.bv_indoor_min)
            self.ir_outdoor_spin.setValue(self.config.ir_outdoor_threshold)
            
            logger.info("==liuq debug== 配置已加载到UI")
            
        except Exception as e:
            logger.error(f"==liuq debug== 加载配置到UI失败: {e}")
    
    def save_ui_to_config(self):
        """将UI数据保存到配置"""
        try:
            self.config.config_name = self.config_name_edit.text() or "未命名配置"
            self.config.description = self.description_edit.toPlainText()
            
            self.config.bv_outdoor_threshold = self.bv_outdoor_spin.value()
            self.config.bv_indoor_min = self.bv_indoor_min_spin.value()
            self.config.ir_outdoor_threshold = self.ir_outdoor_spin.value()
            
            # 更新修改时间
            from datetime import datetime
            self.config.modified_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info("==liuq debug== UI数据已保存到配置")
            
        except Exception as e:
            logger.error(f"==liuq debug== 保存UI数据到配置失败: {e}")
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 临时保存UI数据到配置
            temp_config = SceneClassificationConfig()
            temp_config.bv_outdoor_threshold = self.bv_outdoor_spin.value()
            temp_config.bv_indoor_min = self.bv_indoor_min_spin.value()
            temp_config.ir_outdoor_threshold = self.ir_outdoor_spin.value()
            
            # 验证配置
            validation_result = temp_config.validate_config()
            
            if not validation_result['is_valid']:
                error_msg = "配置验证失败：\n" + "\n".join(validation_result['errors'])
                QMessageBox.warning(self, "配置错误", error_msg)
                return False
            
            if validation_result['warnings']:
                warning_msg = "配置警告：\n" + "\n".join(validation_result['warnings'])
                reply = QMessageBox.question(self, "配置警告",
                                           warning_msg + "\n\n是否继续？",
                                           QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 配置验证失败: {e}")
            QMessageBox.critical(self, "验证错误", f"配置验证时发生错误：{e}")
            return False
    
    def accept_config(self):
        """接受配置"""
        if self.validate_config():
            self.save_ui_to_config()
            self.config_updated.emit(self.config)
            self.accept()
    
    def load_config_from_file(self):
        """从文件加载配置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "加载配置文件", get_default_config_path(),
                "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if file_path:
                self.config = SceneClassificationConfig.load_from_file(file_path)
                self.load_config_to_ui()
                QMessageBox.information(self, "成功", "配置文件加载成功")
                
        except Exception as e:
            logger.error(f"==liuq debug== 加载配置文件失败: {e}")
            QMessageBox.critical(self, "加载失败", f"加载配置文件失败：{e}")
    
    def save_config_to_file(self):
        """保存配置到文件"""
        try:
            if not self.validate_config():
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存配置文件", get_default_config_path(),
                "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if file_path:
                self.save_ui_to_config()
                if self.config.save_to_file(file_path):
                    QMessageBox.information(self, "成功", "配置文件保存成功")
                else:
                    QMessageBox.critical(self, "保存失败", "配置文件保存失败")
                    
        except Exception as e:
            logger.error(f"==liuq debug== 保存配置文件失败: {e}")
            QMessageBox.critical(self, "保存失败", f"保存配置文件失败：{e}")
    
    def reset_to_default(self):
        """重置为默认配置"""
        reply = QMessageBox.question(self, "确认重置",
                                   "确定要重置为默认配置吗？当前修改将丢失。",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config = SceneClassificationConfig()
            self.load_config_to_ui()
    
    def get_config(self) -> SceneClassificationConfig:
        """获取当前配置"""
        return self.config
