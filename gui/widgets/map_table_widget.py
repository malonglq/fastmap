#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map点列表表格组件

提供详细的Map点信息表格视图，支持排序、筛选和选择联动

{{CHENGQI:
Action: Modified; Timestamp: 2025-07-26 10:30:00 +08:00; Reason: 修复表头显示格式，实现多级表头结构; Principle_Applied: SOLID-S单一职责原则;
}}

作者: AI Assistant
日期: 2025-01-25
"""

import logging
from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QLineEdit, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QFont, QColor, QPainter, QPen

from core.models.map_data import (
    MapPoint, MapConfiguration, get_map_point_field_value, set_map_point_field_value
)
from core.services.data_binding_manager_impl import DataBindingManagerImpl
from core.services.field_editor_factory import field_editor_factory
from core.services.field_registry_service import field_registry
from core.services.xml_writer_service import format_number_for_xml
from core.interfaces.xml_field_definition import XMLFieldDefinition, TableColumnDefinition, TableConfiguration
from core.managers.table_column_manager import table_column_manager
from utils.natural_sort import natural_sort

logger = logging.getLogger(__name__)


def format_gui_number(value) -> str:
    """
    GUI专用的智能数值格式化函数

    使用与XML写入层相同的智能格式化逻辑，确保GUI显示与XML存储的完全一致性

    {{CHENGQI:
    Action: Added; Timestamp: 2025-08-02 10:30:00 +08:00; Reason: 修复GUI显示层格式化截断问题，使用智能格式化替代固定小数位; Principle_Applied: DRY原则，复用已验证的格式化逻辑;
    }}

    Args:
        value: 要格式化的数值

    Returns:
        str: 智能格式化后的字符串

    Examples:
        >>> format_gui_number(1.0)
        '1'
        >>> format_gui_number(0.75)
        '0.75'
        >>> format_gui_number(0.25)
        '0.25'
    """
    try:
        if value is None:
            return "0"

        # 使用与XML写入层相同的智能格式化逻辑
        result = format_number_for_xml(value)
        logger.debug(f"==liuq debug== GUI格式化: {value} -> {result}")
        return result

    except Exception as e:
        logger.warning(f"==liuq debug== GUI格式化失败: {value} - {e}")
        return str(value) if value is not None else "0"


class SimpleHeaderView(QHeaderView):
    """
    简化的单行表头视图

    移除复杂的多级表头设计，改为传统的单行表头显示
    所有文本居中对齐，使用清晰的列分隔线
    """

    def __init__(self, orientation, parent=None):
        """初始化单行表头"""
        super().__init__(orientation, parent)

        # 设置表头高度为单行
        self.setDefaultSectionSize(80)
        self.setMinimumHeight(35)
        self.setMaximumHeight(35)

        # 禁用默认的鼠标跟踪，减少不必要的重绘
        self.setMouseTracking(False)

    def paintSection(self, painter, rect, logicalIndex):
        """
        重写paintSection方法来绘制单个section

        简化的单行表头绘制，支持排序功能：
        - 绘制背景色
        - 绘制边框
        - 绘制居中对齐的文本
        - 绘制排序指示器
        """
        try:
            # 绘制背景
            painter.fillRect(rect, QColor(245, 245, 245))

            # 绘制边框
            painter.setPen(QPen(Qt.black, 1))
            painter.drawRect(rect)

            # 获取列标题文本和排序状态
            if logicalIndex < self.count():
                # 从模型获取表头数据
                model = self.model()
                if model:
                    header_text = model.headerData(logicalIndex, self.orientation(), Qt.DisplayRole)
                    if header_text:
                        # 设置字体
                        font = QFont("Arial", 9, QFont.Bold)
                        painter.setFont(font)
                        painter.setPen(Qt.black)

                        # 获取排序状态
                        sort_order = self.sortIndicatorOrder()
                        sort_section = self.sortIndicatorSection()

                        # 计算文本和排序指示器的区域
                        if sort_section == logicalIndex:
                            # 当前列有排序，为排序指示器留出空间
                            text_rect = rect.adjusted(2, 2, -18, -2)  # 右侧留出16px给排序箭头
                            arrow_rect = QRect(rect.right() - 16, rect.y() + 2, 14, rect.height() - 4)
                        else:
                            # 当前列无排序
                            text_rect = rect.adjusted(2, 2, -2, -2)

                        # 绘制居中对齐的文本
                        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextSingleLine, str(header_text))

                        # 绘制排序指示器
                        if sort_section == logicalIndex:
                            self._draw_sort_indicator(painter, arrow_rect, sort_order)

        except Exception as e:
            logger.warning(f"==liuq debug== paintSection失败: {e}")
            # 出错时使用默认绘制
            super().paintSection(painter, rect, logicalIndex)

    def _draw_sort_indicator(self, painter, rect, sort_order):
        """绘制排序指示器箭头"""
        try:
            painter.save()
            painter.setPen(QPen(Qt.black, 2))
            painter.setBrush(Qt.black)

            # 计算箭头的中心位置
            center_x = rect.center().x()
            center_y = rect.center().y()

            # 箭头大小
            arrow_size = 4

            if sort_order == Qt.AscendingOrder:
                # 向上箭头 (升序)
                points = [
                    QPoint(center_x, center_y - arrow_size),      # 顶点
                    QPoint(center_x - arrow_size, center_y + arrow_size),  # 左下
                    QPoint(center_x + arrow_size, center_y + arrow_size)   # 右下
                ]
            else:
                # 向下箭头 (降序)
                points = [
                    QPoint(center_x, center_y + arrow_size),      # 底点
                    QPoint(center_x - arrow_size, center_y - arrow_size),  # 左上
                    QPoint(center_x + arrow_size, center_y - arrow_size)   # 右上
                ]

            # 绘制箭头
            painter.drawPolygon(points)
            painter.restore()

        except Exception as e:
            logger.warning(f"==liuq debug== 绘制排序指示器失败: {e}")

    def mousePressEvent(self, event):
        """处理鼠标点击事件，确保排序功能正常工作"""
        try:
            # 调用父类方法处理排序
            super().mousePressEvent(event)

            # 强制重绘以显示排序指示器
            self.update()

        except Exception as e:
            logger.warning(f"==liuq debug== 表头鼠标点击处理失败: {e}")

    def sizeHint(self):
        """返回建议的大小"""
        size = super().sizeHint()
        size.setHeight(35)  # 设置单行表头高度
        return size








class MapTableWidget(QWidget):
    """
    Map点列表表格组件
    
    提供详细的Map点信息表格视图
    """
    
    # 自定义信号
    map_point_selected = pyqtSignal(object)  # 选中Map点时发出信号
    base_boundary_selected = pyqtSignal(object)  # 选中base_boundary时发出信号
    
    def __init__(self, parent=None):
        """初始化表格组件"""
        super().__init__(parent)

        self.configuration: Optional[MapConfiguration] = None
        self.map_points: List[MapPoint] = []  # 只包含offset_map点，不包含base_boundary0
        self.base_boundary_point: Optional[MapPoint] = None  # 单独存储base_boundary0
        self.current_xml_file: Optional[str] = None

        # 排序状态管理
        self.is_natural_sort = True  # 标记当前是否为自然排序状态
        self.user_sort_column = -1   # 用户排序的列索引
        self.user_sort_order = Qt.AscendingOrder  # 用户排序的顺序

        # 数据绑定管理器
        self.binding_manager = DataBindingManagerImpl()
        self.binding_manager.data_changed.connect(self.on_data_changed)
        self.binding_manager.validation_error.connect(self.on_validation_error)

        # 字段定义缓存
        self.field_definitions: List[XMLFieldDefinition] = []

        # 表格配置管理
        self.table_config: Optional[TableConfiguration] = None
        self.column_definitions: List[TableColumnDefinition] = []

        # 动态可编辑字段列表（基于字段注册系统）
        self.editable_fields = self._get_editable_fields_from_registry()

        # 自动保存定时器
        from PyQt5.QtCore import QTimer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self._perform_auto_save)
        self.auto_save_delay = 2000  # 2秒延迟保存

        # 初始化表格配置
        self._initialize_table_configuration()

        # 初始化表格配置
        self._initialize_table_configuration()

        self.setup_ui()
        self.load_field_definitions()

        # 启用编辑功能
        self.enable_cell_editing(True)

        logger.info("==liuq debug== Map点表格组件初始化完成")

    def _initialize_table_configuration(self):
        """
        初始化表格配置

        {{CHENGQI:
        Action: Added; Timestamp: 2025-08-04 16:45:00 +08:00; Reason: 添加动态表格配置初始化; Principle_Applied: SOLID-S单一职责原则;
        }}
        """
        try:
            # 获取当前表格配置
            self.table_config = table_column_manager.get_current_configuration()
            self.column_definitions = self.table_config.get_visible_columns()

            logger.info(f"==liuq debug== 表格配置初始化完成，共 {len(self.column_definitions)} 个可见列")

        except Exception as e:
            logger.error(f"==liuq debug== 表格配置初始化失败: {e}")
            # 使用默认配置
            self.table_config = table_column_manager.generate_default_configuration()
            self.column_definitions = self.table_config.get_visible_columns()

    def _get_editable_fields_from_registry(self) -> List[str]:
        """
        从字段注册系统获取可编辑字段列表

        Returns:
            List[str]: 可编辑字段ID列表
        """
        try:
            editable_fields = field_registry.get_editable_fields()
            logger.info(f"==liuq debug== 从字段注册系统获取到 {len(editable_fields)} 个可编辑字段")
            return list(editable_fields)
        except Exception as e:
            logger.error(f"==liuq debug== 获取可编辑字段失败: {e}")
            # 返回默认的可编辑字段列表
            return [
                'alias_name', 'offset_x', 'offset_y', 'weight', 'trans_step',
                'e_ratio_min', 'e_ratio_max',
                'bv_min', 'bv_max', 'tran_bv_min', 'tran_bv_max',
                'ctemp_min', 'ctemp_max', 'tran_ctemp_min', 'tran_ctemp_max',
                'ir_min', 'ir_max', 'tran_ir_min', 'tran_ir_max',
                'ac_min', 'ac_max', 'tran_ac_min', 'tran_ac_max',
                'count_min', 'count_max', 'tran_count_min', 'tran_count_max',
                'color_cct_min', 'color_cct_max', 'tran_color_cct_min', 'tran_color_cct_max',
                'diff_ctemp_min', 'diff_ctemp_max', 'tran_diff_ctemp_min', 'tran_diff_ctemp_max',
                'face_ctemp_min', 'face_ctemp_max', 'tran_face_ctemp_min', 'tran_face_ctemp_max',
                'ml'
            ]

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题和筛选区域
        header_layout = QHBoxLayout()
        
        # 标题
        title_label = QLabel("Map点列表")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(title_label)
        
        # 筛选输入框
        header_layout.addStretch()
        filter_label = QLabel("筛选:")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("输入Map名称筛选...")
        self.filter_input.textChanged.connect(self.filter_table)

        header_layout.addWidget(filter_label)
        header_layout.addWidget(self.filter_input)

        # 恢复自然排序按钮
        self.restore_sort_btn = QPushButton("恢复自然排序")
        self.restore_sort_btn.setToolTip("点击恢复按alias_name的自然排序")
        self.restore_sort_btn.clicked.connect(self.restore_natural_sort)
        header_layout.addWidget(self.restore_sort_btn)
        
        layout.addLayout(header_layout)
        
        # 创建表格
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        # 状态标签
        self.status_label = QLabel("请加载Map配置文件")
        self.status_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.status_label)
    
    def setup_table(self):
        """
        设置表格属性（动态列生成版本）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-04 16:50:00 +08:00; Reason: 重构为动态列生成，移除硬编码; Principle_Applied: 开闭原则;
        }}
        """
        # 使用动态列定义
        visible_columns = self.column_definitions

        logger.info(f"==liuq debug== 设置表格，共 {len(visible_columns)} 个可见列")

        # 设置列数
        self.table.setColumnCount(len(visible_columns))

        # 创建并设置简化的单行表头
        self.simple_header = SimpleHeaderView(Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(self.simple_header)

        # 设置列标题和宽度
        for i, column_def in enumerate(visible_columns):
            # 设置列标题
            header_item = QTableWidgetItem(column_def.display_name)
            if column_def.tooltip:
                header_item.setToolTip(column_def.tooltip)
            self.table.setHorizontalHeaderItem(i, header_item)

            # 设置列宽
            self.table.setColumnWidth(i, column_def.width)

        # 设置表格属性
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)

        # 初始禁用排序功能，保持自然排序状态
        self.table.setSortingEnabled(False)

        # 设置表头可点击
        self.simple_header.setSectionsClickable(True)
        self.simple_header.setSectionsMovable(False)  # 禁用列移动，保持列顺序

        # 连接表头点击事件以实现智能排序
        self.simple_header.sectionClicked.connect(self.on_header_clicked)

        # 不设置默认排序，保持自然排序状态

        # 设置列宽
        self.simple_header.setStretchLastSection(False)

        # 设置各列的宽度（调整为适合单行表头的宽度）
        column_widths = [
            # MapList (1列)
            120,
            # Offset (2列)
            80, 80,
            # Weight, Step, ERatio (4列)
            80, 60, 80, 80,
            # BV (4列)
            80, 70, 70, 80,
            # Ctemp (4列)
            90, 80, 80, 90,
            # IR (4列)
            80, 70, 70, 80,
            # AC (4列)
            80, 70, 70, 80,
            # COUNT (4列)
            90, 80, 80, 90,
            # ColorCCT (4列)
            100, 90, 90, 100,
            # diffCtemp (4列)
            100, 90, 90, 100,
            # FaceCtemp (4列)
            100, 90, 90, 100,
            # ml (1列)
            60
        ]

        for i, width in enumerate(column_widths):
            self.table.setColumnWidth(i, width)

        # 连接选择信号
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        # 连接编辑信号
        self.table.itemChanged.connect(self.on_item_changed)



    def load_field_definitions(self):
        """加载字段定义"""
        try:
            # 获取所有字段定义
            all_groups = field_registry.get_field_groups()
            self.field_definitions = []

            for group in all_groups:
                fields = field_registry.get_fields_by_group(group)
                self.field_definitions.extend(fields)

            logger.info(f"==liuq debug== 加载字段定义完成，共 {len(self.field_definitions)} 个字段")

        except Exception as e:
            logger.error(f"==liuq debug== 加载字段定义失败: {e}")
            self.field_definitions = []

    def enable_cell_editing(self, enable: bool = True):
        """启用/禁用单元格编辑功能"""
        try:
            from PyQt5.QtWidgets import QAbstractItemView

            if enable:
                # 启用编辑功能
                self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
                logger.info("==liuq debug== 启用表格单元格编辑功能")
            else:
                # 禁用编辑功能
                self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                logger.info("==liuq debug== 禁用表格单元格编辑功能")

        except Exception as e:
            logger.error(f"==liuq debug== 设置编辑功能失败: {e}")

    def on_data_changed(self, binding_id: str, old_value: Any, new_value: Any):
        """处理数据变化事件"""
        try:
            logger.info(f"==liuq debug== 数据变化: {binding_id} {old_value} -> {new_value}")

            # 触发自动保存（如果需要）
            self.auto_save_changes()

        except Exception as e:
            logger.error(f"==liuq debug== 处理数据变化失败: {e}")

    def on_validation_error(self, binding_id: str, error_message: str):
        """处理验证错误事件"""
        try:
            logger.warning(f"==liuq debug== 验证错误: {binding_id} - {error_message}")

            # 显示错误提示
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"验证错误: {error_message}")

            # 可以添加更多用户反馈，如弹窗提示
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "数据验证错误", f"输入的数据无效：\n{error_message}")

        except Exception as e:
            logger.error(f"==liuq debug== 处理验证错误失败: {e}")

    def on_item_changed(self, item):
        """处理表格项变化事件"""
        try:
            if not item:
                return

            row = item.row()
            col = item.column()
            new_value = item.text()

            logger.info(f"==liuq debug== 表格项变化: [{row}, {col}] = '{new_value}'")

            # 获取对应的MapPoint对象
            map_point = self.get_map_point_by_row(row)
            if not map_point:

                return

            # 获取字段ID
            field_id = self._get_field_id_by_column(col)
            if not field_id or field_id not in self.editable_fields:

                return

            # 查找字段定义
            field_definition = None
            for field_def in self.field_definitions:
                if field_def.field_id == field_id:
                    field_definition = field_def
                    break

            if not field_definition:
                # 为新增的范围字段创建默认的FLOAT类型定义
                logger.info(f"==liuq debug== 未找到字段定义，创建默认定义: {field_id}")
                from core.interfaces.xml_field_definition import XMLFieldDefinition, FieldType
                field_definition = XMLFieldDefinition(
                    field_id=field_id,
                    display_name=field_id.replace('_', ' ').title(),
                    field_type=FieldType.FLOAT,
                    xml_path=f".//{field_id}",
                    default_value=0.0,
                    validation_rules=[],  # 暂时不添加验证规则
                    is_editable=True,
                    is_visible=True,
                    group="dynamic",
                    description=f"动态创建的{field_id}字段"
                )

            # 验证和转换新值
            validated_value = self._validate_and_convert_value(new_value, field_definition)
            if validated_value is None:
                # 验证失败，恢复原值
                old_value = self._get_field_value_from_map_point(map_point, field_id)
                item.setText(str(old_value))
                self.on_validation_error(f"{field_id}_{id(map_point)}", f"无效的值: {new_value}")
                return

            # 获取旧值
            old_value = self._get_field_value_from_map_point(map_point, field_id)

            # 更新MapPoint对象
            self._set_field_value_to_map_point(map_point, field_id, validated_value)

            # 触发数据变化事件
            binding_id = f"map_point_{id(map_point)}_{field_id}"
            self.on_data_changed(binding_id, old_value, validated_value)

            logger.info(f"==liuq debug== 成功更新字段: {field_id} {old_value} -> {validated_value}")

        except Exception as e:
            logger.error(f"==liuq debug== 处理表格项变化失败: {e}")
            # 尝试恢复原值
            if item and hasattr(self, 'map_points'):
                try:
                    row = item.row()
                    col = item.column()
                    if row > 0:  # 跳过base_boundary行
                        map_point_index = row - 1
                        if 0 <= map_point_index < len(self.map_points):
                            map_point = self.map_points[map_point_index]
                            field_id = self._get_field_id_by_column(col)
                            if field_id:
                                old_value = self._get_field_value_from_map_point(map_point, field_id)
                                item.setText(str(old_value))
                except:
                    pass

    def auto_save_changes(self):
        """自动保存变更（延迟执行）"""
        try:
            if self.configuration and self.current_xml_file:
                # 重置定时器，实现延迟保存
                self.auto_save_timer.stop()
                self.auto_save_timer.start(self.auto_save_delay)

            else:
                # 不是错误，只是没有设置自动保存环境
                logger.debug("==liuq debug== 自动保存未启用：需要配置和文件路径")

        except Exception as e:
            logger.error(f"==liuq debug== 启动自动保存失败: {e}")

    def _perform_auto_save(self):
        """执行实际的自动保存操作"""
        try:
            if not self.configuration or not self.current_xml_file:

                return

            logger.info("==liuq debug== 开始执行自动保存...")

            # 使用XMLWriterService保存文件
            from core.services.xml_writer_service import XMLWriterService
            writer = XMLWriterService()

            success = writer.write_xml(self.configuration, self.current_xml_file, backup=True)

            if success:
                logger.info(f"==liuq debug== 自动保存成功: {self.current_xml_file}")
                # 可以在这里发出信号通知主窗口更新状态栏
                if hasattr(self.parent(), 'status_message'):
                    self.parent().status_message.emit("数据已自动保存")
            else:
                logger.error("==liuq debug== 自动保存失败")
                if hasattr(self.parent(), 'status_message'):
                    self.parent().status_message.emit("自动保存失败")

        except Exception as e:
            logger.error(f"==liuq debug== 执行自动保存失败: {e}")
            if hasattr(self.parent(), 'status_message'):
                self.parent().status_message.emit(f"自动保存失败: {e}")
    
    def set_configuration(self, configuration: MapConfiguration):
        """
        设置Map配置数据

        Args:
            configuration: Map配置对象
        """
        logger.info(f"==liuq debug== 开始设置Map配置，共 {len(configuration.map_points)} 个offset_map点")

        self.configuration = configuration
        self.map_points = configuration.map_points  # 只包含offset_map点
        self.base_boundary_point = configuration.base_boundary_point  # 单独的base_boundary0

        logger.info(f"==liuq debug== 设置后self.map_points长度: {len(self.map_points)}")
        logger.info(f"==liuq debug== base_boundary_point: {'存在' if self.base_boundary_point else '不存在'}")

        # 强制刷新表格
        self.populate_table()

        # 强制重绘
        self.table.update()
        self.update()

        logger.info(f"==liuq debug== Map配置设置完成，表格行数: {self.table.rowCount()}")

    def set_xml_file_path(self, xml_file_path: str):
        """
        设置XML文件路径，用于自动保存功能

        Args:
            xml_file_path: XML文件路径
        """
        self.current_xml_file = xml_file_path
        logger.info(f"==liuq debug== 设置XML文件路径: {xml_file_path}")

    def populate_table(self):
        """填充表格数据"""
        logger.info(f"==liuq debug== 开始填充表格数据，共 {len(self.map_points) if self.map_points else 0} 个Map点")

        try:
            # 计算总行数：1个base_boundary0 + offset_map点数量
            total_rows = 1 + len(self.map_points)  # +1 for base_boundary0

            if not self.base_boundary_point and not self.map_points:
                logger.info(f"==liuq debug== 没有数据，设置表格行数为0")
                self.table.setRowCount(0)
                self.status_label.setText("没有可显示的数据")
                return

            # 完全禁用排序，使用自定义排序逻辑
            logger.info(f"==liuq debug== 禁用表格默认排序，使用自定义排序")
            self.table.setSortingEnabled(False)

            logger.info(f"==liuq debug== 设置表格行数为 {total_rows} (1个base_boundary0 + {len(self.map_points)}个offset_map点)")
            # 设置行数
            self.table.setRowCount(total_rows)

            logger.info(f"==liuq debug== 开始逐行填充数据")

            # 第0行：固定填充base_boundary0
            if self.base_boundary_point:
                logger.info(f"==liuq debug== 正在填充第0行: {self.base_boundary_point.alias_name}")
                self.populate_row(0, self.base_boundary_point)
                # 为base_boundary0行设置特殊样式
                self._apply_base_boundary_style(0)

            # 第1行开始：填充offset_map点
            for i, map_point in enumerate(self.map_points):
                row = i + 1  # +1 because row 0 is base_boundary0
                if i < 5:  # 只对前5行输出详细日志
                    logger.info(f"==liuq debug== 正在填充第{row}行: {map_point.alias_name}")
                self.populate_row(row, map_point)

            # 更新状态
            status_text = f"共 {len(self.map_points)} 个offset_map点"
            if self.base_boundary_point:
                status_text += " + 1个base_boundary0"
            self.status_label.setText(status_text)

            # 调整列宽
            self.table.resizeColumnsToContents()

            # 先应用自然排序
            self.apply_natural_sort()
            logger.info(f"==liuq debug== 应用自然排序完成")

            # 保持自然排序状态，不自动启用表格排序
            # 用户点击表头时会动态启用排序功能
            self.is_natural_sort = True
            logger.info(f"==liuq debug== 保持自然排序状态，等待用户手动排序")

            logger.info(f"==liuq debug== 表格数据填充完成，{len(self.map_points)} 行")

            # 添加表格状态检查
            self.debug_table_state()

            # 添加权重分布检查
            self.debug_weight_distribution()

        except Exception as e:
            logger.error(f"==liuq debug== 填充表格数据失败: {e}")
            import traceback
            logger.error(f"==liuq debug== 异常详情: {traceback.format_exc()}")
            self.status_label.setText(f"数据加载失败: {e}")

    def _populate_base_boundary_row(self, row: int):
        """填充base_boundary行数据"""
        try:
            if not hasattr(self, 'configuration') or not self.configuration.base_boundary:
                logger.warning(f"==liuq debug== 没有base_boundary数据，跳过填充")
                return

            boundary_data = self.configuration.base_boundary
            col_index = 0

            # MapList列：显示"base_boundary0"
            self.set_table_item(row, col_index, "base_boundary0")
            col_index += 1

            # Offset R/G列：显示rpg值
            rpg_value = boundary_data.rpg
            self.set_table_item(row, col_index, format_gui_number(rpg_value))
            col_index += 1

            # Offset B/G列：显示bpg值
            bpg_value = boundary_data.bpg
            self.set_table_item(row, col_index, format_gui_number(bpg_value))
            col_index += 1

            # 其他列：显示"-"或空值
            while col_index < self.table.columnCount():
                self.set_table_item(row, col_index, "-")
                col_index += 1

            # 设置特殊样式以区分base_boundary行
            self._apply_base_boundary_style(row)

            logger.info(f"==liuq debug== base_boundary行填充完成: rpg={rpg_value:.3f}, bpg={bpg_value:.3f}")

        except Exception as e:
            logger.error(f"==liuq debug== 填充base_boundary行失败: {e}")

    def _apply_base_boundary_style(self, row: int):
        """为base_boundary行应用特殊样式"""
        try:
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QColor, QFont

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    # 设置背景色为浅灰色
                    item.setBackground(QColor(240, 240, 240))
                    # 设置字体为粗体
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                    # 设置文本居中
                    item.setTextAlignment(Qt.AlignCenter)

        except Exception as e:
            logger.error(f"==liuq debug== 应用base_boundary样式失败: {e}")

    def debug_table_state(self):
        """调试表格状态"""
        try:
            logger.info(f"==liuq debug== === 表格状态检查 ===")
            logger.info(f"==liuq debug== 表格行数: {self.table.rowCount()}")
            logger.info(f"==liuq debug== 表格列数: {self.table.columnCount()}")

            # 检查前5行的第一列内容
            for row in range(min(5, self.table.rowCount())):
                item = self.table.item(row, 0)
                if item:
                    logger.info(f"==liuq debug== 第{row}行第0列: '{item.text()}'")
                else:
                    logger.info(f"==liuq debug== 第{row}行第0列: None")

            # 检查第40行的内容（用户截图中有数据的行）
            if self.table.rowCount() > 40:
                item = self.table.item(40, 0)
                if item:
                    logger.info(f"==liuq debug== 第40行第0列: '{item.text()}'")
                else:
                    logger.info(f"==liuq debug== 第40行第0列: None")

            logger.info(f"==liuq debug== === 表格状态检查完成 ===")

        except Exception as e:
            logger.error(f"==liuq debug== 表格状态检查失败: {e}")

    def debug_weight_distribution(self):
        """调试权重分布"""
        try:
            logger.info(f"==liuq debug== === 权重分布检查 ===")

            # 检查前10个Map点的权重和名称
            for i, mp in enumerate(self.map_points[:10]):
                logger.info(f"==liuq debug== Map点{i}: {mp.alias_name}, 权重: {mp.weight:.3f}")

            # 统计权重分布
            weights = [mp.weight for mp in self.map_points]
            unique_weights = sorted(set(weights), reverse=True)
            logger.info(f"==liuq debug== 唯一权重值: {unique_weights}")

            # 统计每个权重的Map点数量
            for weight in unique_weights[:5]:  # 只显示前5个权重
                count = weights.count(weight)
                logger.info(f"==liuq debug== 权重 {weight:.3f}: {count} 个Map点")

            logger.info(f"==liuq debug== === 权重分布检查完成 ===")

        except Exception as e:
            logger.error(f"==liuq debug== 权重分布检查失败: {e}")
    
    def populate_row(self, row: int, map_point: MapPoint):
        """填充单行数据"""
        try:
            col_index = 0

            # 添加调试日志（前5行使用INFO级别）
            if row < 5:
                logger.info(f"==liuq debug== 填充第{row}行数据: {map_point.alias_name}")
                logger.info(f"==liuq debug== 坐标: ({map_point.x:.3f}, {map_point.y:.3f}), 权重: {map_point.weight:.3f}")
                logger.info(f"==liuq debug== tran_bv: {map_point.tran_bv_min:.1f}-{map_point.tran_bv_max:.1f}")
                logger.info(f"==liuq debug== bv_range: {map_point.bv_range}")
                logger.info(f"==liuq debug== tran_ctemp: {map_point.tran_ctemp_min:.0f}-{map_point.tran_ctemp_max:.0f}")
                logger.info(f"==liuq debug== cct_range: {map_point.cct_range}")
            else:





                logger.debug(f"==liuq debug== cct_range: {map_point.cct_range}")

            # MapList (1列): 显示Map点别名
            self.set_table_item(row, col_index, map_point.alias_name, map_point)
            col_index += 1

            # Offset (2列): R/G, B/G
            # 严格只从 offset_map[0]/offset/x 和 offset_map[0]/offset/y 取值
            self.set_table_item(row, col_index, format_gui_number(map_point.offset_x), map_point)
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(map_point.offset_y), map_point)
            col_index += 1

            # Weight (1列)
            self.set_table_item(row, col_index, format_gui_number(map_point.weight), map_point)
            col_index += 1

            # Step (1列) - 从XML节点 offset_map[1]/TransStep 直接取值
            self.set_table_item(row, col_index, f"{map_point.trans_step}", map_point)
            col_index += 1

            # ERatio (2列): Min, Max
            eratio_min, eratio_max = map_point.e_ratio_range
            self.set_table_item(row, col_index, format_gui_number(eratio_min), map_point)  # Min
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(eratio_max), map_point)  # Max
            col_index += 1

            # BV参数 (4列): Lower, Min, Max, Upper
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_bv_min), map_point)  # Lower
            col_index += 1
            bv_min, bv_max = map_point.bv_range
            self.set_table_item(row, col_index, format_gui_number(bv_min), map_point)  # Min
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(bv_max), map_point)  # Max
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_bv_max), map_point)  # Upper
            col_index += 1

            # Ctemp参数 (4列): Lower, Min, Max, Upper
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_ctemp_min), map_point)  # Lower
            col_index += 1
            ctemp_min, ctemp_max = map_point.ctemp_range
            self.set_table_item(row, col_index, format_gui_number(ctemp_min), map_point)  # Min (使用ctemp_range而非cct_range)
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(ctemp_max), map_point)  # Max (使用ctemp_range而非cct_range)
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_ctemp_max), map_point)  # Upper
            col_index += 1

            # IR参数 (4列): Lower, Min, Max, Upper
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_ir_min), map_point)  # Lower
            col_index += 1
            ir_min, ir_max = map_point.ir_range
            self.set_table_item(row, col_index, format_gui_number(ir_min), map_point)  # Min
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(ir_max), map_point)  # Max
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_ir_max), map_point)  # Upper
            col_index += 1

            # AC参数 (4列): Lower, Min, Max, Upper
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_ac_min), map_point)  # Lower
            col_index += 1
            ac_min, ac_max = map_point.ac_range
            self.set_table_item(row, col_index, format_gui_number(ac_min), map_point)  # Min
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(ac_max), map_point)  # Max
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_ac_max), map_point)  # Upper
            col_index += 1

            # COUNT参数 (4列): Lower, Min, Max, Upper
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_count_min), map_point)  # Lower
            col_index += 1
            count_min, count_max = map_point.count_range
            self.set_table_item(row, col_index, format_gui_number(count_min), map_point)  # Min
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(count_max), map_point)  # Max
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_count_max), map_point)  # Upper
            col_index += 1

            # ColorCCT参数 (4列): Lower, Min, Max, Upper
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_color_cct_min), map_point)  # Lower
            col_index += 1
            color_cct_min, color_cct_max = map_point.color_cct_range
            self.set_table_item(row, col_index, format_gui_number(color_cct_min), map_point)  # Min
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(color_cct_max), map_point)  # Max
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_color_cct_max), map_point)  # Upper
            col_index += 1

            # diffCtemp参数 (4列): Lower, Min, Max, Upper
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_diff_ctemp_min), map_point)  # Lower
            col_index += 1
            diff_ctemp_min, diff_ctemp_max = map_point.diff_ctemp_range
            self.set_table_item(row, col_index, format_gui_number(diff_ctemp_min), map_point)  # Min
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(diff_ctemp_max), map_point)  # Max
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_diff_ctemp_max), map_point)  # Upper
            col_index += 1

            # FaceCtemp参数 (4列): Lower, Min, Max, Upper
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_face_ctemp_min), map_point)  # Lower
            col_index += 1
            face_ctemp_min, face_ctemp_max = map_point.face_ctemp_range
            self.set_table_item(row, col_index, format_gui_number(face_ctemp_min), map_point)  # Min
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(face_ctemp_max), map_point)  # Max
            col_index += 1
            self.set_table_item(row, col_index, format_gui_number(map_point.tran_face_ctemp_max), map_point)  # Upper
            col_index += 1

            # ml (1列) - 从extra_attributes获取并应用特殊值转换
            ml_raw_value = map_point.extra_attributes.get('ml', 0)
            # 应用特殊值转换逻辑：65535→3, 65471→2
            if ml_raw_value == 65535:
                ml_value = 3
            elif ml_raw_value == 65471:
                ml_value = 2
            else:
                ml_value = ml_raw_value
            self.set_table_item(row, col_index, f"{ml_value}", map_point)

            # 存储MapPoint对象到第一列的item中，用于选择功能和行号映射
            first_item = self.table.item(row, 0)
            if first_item:
                first_item.setData(Qt.UserRole, map_point)


        except Exception as e:
            logger.error(f"==liuq debug== 填充第{row}行数据失败: {e}")
            import traceback
            logger.error(f"==liuq debug== 异常详情: {traceback.format_exc()}")
            # 即使出现异常，也要确保第一列有数据
            try:
                self.set_table_item(row, 0, map_point.alias_name)
            except:
                pass

    def set_table_item(self, row: int, col: int, text: str, map_point: Optional[MapPoint] = None):
        """设置表格项"""
        # 确保文本不为空，即使是0值也要显示
        if text is None or text == "":
            text = "0"

        # 添加调试日志（仅对前几行）
        if row < 5:
            logger.debug(f"==liuq debug== 设置表格项 [{row}, {col}]: '{text}'")

        # 使用普通表格项
        item = QTableWidgetItem(str(text))

        # 检查是否为可编辑字段
        field_id = self._get_field_id_by_column(col)
        is_editable = field_id in self.editable_fields and map_point is not None

        if is_editable:
            # 设置为可编辑
            item.setFlags(item.flags() | Qt.ItemIsEditable)

            # 创建数据绑定
            if map_point and field_id:
                self._create_field_binding(map_point, field_id, row, col)
        else:
            # 设置为只读
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        self.table.setItem(row, col, item)

    def apply_natural_sort(self):
        """应用自然排序到表格数据"""
        try:
            logger.info(f"==liuq debug== ========== 开始应用自然排序 ==========")

            # 对map_points进行自然排序
            if self.map_points:
                logger.info(f"==liuq debug== map_points数量: {len(self.map_points)}")

                # 记录排序前的顺序
                logger.info(f"==liuq debug== 排序前前10个: {[mp.alias_name for mp in self.map_points[:10]]}")

                # 使用utils工具函数进行自然排序
                sorted_map_points = natural_sort(
                    self.map_points,
                    key_func=lambda mp: mp.alias_name,
                    reverse=False
                )

                # 记录排序后的顺序
                logger.info(f"==liuq debug== 排序后前10个: {[mp.alias_name for mp in sorted_map_points[:10]]}")

                # 检查排序是否真的改变了顺序
                if [mp.alias_name for mp in self.map_points] != [mp.alias_name for mp in sorted_map_points]:
                    logger.info(f"==liuq debug== 排序确实改变了顺序")
                else:
                    logger.warning(f"==liuq debug== 排序没有改变顺序！")

                # 更新map_points列表
                self.map_points = sorted_map_points

                # 重新填充表格
                self._repopulate_sorted_table()

                logger.info(f"==liuq debug== ========== 自然排序应用完成 ==========")
            else:
                logger.warning(f"==liuq debug== map_points为空，跳过排序")

        except Exception as e:
            logger.error(f"==liuq debug== 应用自然排序失败: {e}")
            import traceback
            logger.error(f"==liuq debug== 异常详情: {traceback.format_exc()}")

    def _repopulate_sorted_table(self):
        """重新填充排序后的表格"""
        try:
            logger.info(f"==liuq debug== 重新填充排序后的表格")

            # 临时禁用排序
            self.table.setSortingEnabled(False)

            # 清空表格
            self.table.setRowCount(0)

            # 重新设置行数：1个base_boundary0 + offset_map点数量
            total_rows = 1 + len(self.map_points)
            self.table.setRowCount(total_rows)

            # 第0行：固定填充base_boundary0
            if self.base_boundary_point:
                self.populate_row(0, self.base_boundary_point)
                self._apply_base_boundary_style(0)

            # 第1行开始：填充排序后的offset_map点
            for i, map_point in enumerate(self.map_points):
                row = i + 1  # +1 because row 0 is base_boundary0
                self.populate_row(row, map_point)

            # 暂时不启用排序，保持自然排序的结果
            # self.table.setSortingEnabled(True)

            logger.info(f"==liuq debug== 排序后表格重新填充完成")

        except Exception as e:
            logger.error(f"==liuq debug== 重新填充排序后表格失败: {e}")

    def on_header_clicked(self, logical_index: int):
        """处理表头点击事件，实现数值排序（base_boundary0固定在第0行）"""
        try:
            logger.info(f"==liuq debug== 表头点击: 列{logical_index}")

            # 如果没有offset_map点，不进行排序
            if not self.map_points:
                logger.info(f"==liuq debug== 没有offset_map点，跳过排序")
                return

            # 确定排序顺序
            if self.user_sort_column == logical_index:
                # 同一列，切换排序顺序
                self.user_sort_order = Qt.DescendingOrder if self.user_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
            else:
                # 不同列，重置为升序
                self.user_sort_column = logical_index
                self.user_sort_order = Qt.AscendingOrder

            # 标记为用户排序状态
            self.is_natural_sort = False

            # 执行数值排序
            self._perform_numeric_sort(logical_index, self.user_sort_order)

            # 手动更新排序指示器
            self._update_sort_indicator(logical_index, self.user_sort_order)

            logger.info(f"==liuq debug== 数值排序完成: 列={self.user_sort_column}, 顺序={'升序' if self.user_sort_order == Qt.AscendingOrder else '降序'}")

        except Exception as e:
            logger.error(f"==liuq debug== 处理表头点击失败: {e}")

    def _perform_numeric_sort(self, column_index: int, sort_order: Qt.SortOrder):
        """执行数值排序（只对offset_map点排序，base_boundary0固定在第0行）"""
        try:
            logger.info(f"==liuq debug== 开始数值排序: 列{column_index}")

            # 获取列数据并排序
            def get_sort_key(map_point: MapPoint) -> float:
                """获取排序键值，强制数值排序"""
                try:
                    # 根据列索引获取对应的值
                    value = self._get_cell_value_for_sorting(map_point, column_index)

                    # 强制转换为数值
                    if value == "-" or value == "" or value is None:
                        return 0.0  # 空值当作0处理

                    try:
                        numeric_value = float(value)
                        return numeric_value
                    except (ValueError, TypeError):
                        # 无法转换为数值的，尝试提取数字部分
                        import re
                        numbers = re.findall(r'-?\d+\.?\d*', str(value))
                        if numbers:
                            return float(numbers[0])
                        else:
                            return 0.0  # 完全无法提取数字的，当作0处理

                except Exception as e:
                    logger.warning(f"==liuq debug== 获取排序键值失败: {e}")
                    return 0.0  # 错误值当作0处理

            # 对map_points进行排序
            reverse = (sort_order == Qt.DescendingOrder)
            self.map_points.sort(key=get_sort_key, reverse=reverse)

            # 重新填充表格
            self._repopulate_sorted_table()

            logger.info(f"==liuq debug== 数值排序完成")

        except Exception as e:
            logger.error(f"==liuq debug== 执行数值排序失败: {e}")

    def _get_cell_value_for_sorting(self, map_point: MapPoint, column_index: int) -> str:
        """获取指定列的单元格值用于排序"""
        try:
            # 根据列定义获取字段值
            if column_index == 0:  # MapList列 - 从名称中提取数字
                # 对于MapList列，尝试从alias_name中提取数字进行排序
                alias_name = map_point.alias_name
                if alias_name:
                    # 提取名称中的数字部分用于排序
                    import re
                    numbers = re.findall(r'\d+', alias_name)
                    if numbers:
                        # 如果有多个数字，取第一个作为主要排序依据
                        return numbers[0]
                    else:
                        # 如果没有数字，返回0
                        return "0"
                return "0"
            elif column_index == 1:  # Offset R/G列
                return str(map_point.offset_x)
            elif column_index == 2:  # Offset B/G列
                return str(map_point.offset_y)
            elif column_index == 3:  # Weight列
                return str(map_point.weight)
            elif column_index == 4:  # Step列
                return str(map_point.trans_step)
            elif column_index == 5:  # ERatio Min列
                return str(map_point.e_ratio_range[0] if hasattr(map_point, 'e_ratio_range') else 0)
            elif column_index == 6:  # ERatio Max列
                return str(map_point.e_ratio_range[1] if hasattr(map_point, 'e_ratio_range') else 0)
            elif column_index == 7:  # BV Lower列
                return str(getattr(map_point, 'tran_bv_min', 0))
            elif column_index == 8:  # BV Min列
                return str(map_point.bv_range[0])
            elif column_index == 9:  # BV Max列
                return str(map_point.bv_range[1])
            elif column_index == 10:  # BV Upper列
                return str(getattr(map_point, 'tran_bv_max', 0))
            elif column_index == 11:  # Ctemp Lower列
                return str(getattr(map_point, 'tran_ctemp_min', 0))
            elif column_index == 12:  # Ctemp Min列
                return str(map_point.ctemp_range[0] if hasattr(map_point, 'ctemp_range') and map_point.ctemp_range else 0)
            elif column_index == 13:  # Ctemp Max列
                return str(map_point.ctemp_range[1] if hasattr(map_point, 'ctemp_range') and map_point.ctemp_range else 0)
            elif column_index == 14:  # Ctemp Upper列
                return str(getattr(map_point, 'tran_ctemp_max', 0))
            elif column_index == 15:  # IR Lower列
                return str(getattr(map_point, 'tran_ir_min', 0))
            elif column_index == 16:  # IR Min列
                return str(map_point.ir_range[0] if map_point.ir_range else 0)
            elif column_index == 17:  # IR Max列
                return str(map_point.ir_range[1] if map_point.ir_range else 0)
            elif column_index == 18:  # IR Upper列
                return str(getattr(map_point, 'tran_ir_max', 0))
            elif column_index == 19:  # AC Lower列
                return str(getattr(map_point, 'tran_ac_min', 0))
            elif column_index == 20:  # AC Min列
                return str(map_point.ac_range[0] if hasattr(map_point, 'ac_range') and map_point.ac_range else 0)
            elif column_index == 21:  # AC Max列
                return str(map_point.ac_range[1] if hasattr(map_point, 'ac_range') and map_point.ac_range else 0)
            elif column_index == 22:  # AC Upper列
                return str(getattr(map_point, 'tran_ac_max', 0))
            elif column_index == 23:  # COUNT Lower列
                return str(getattr(map_point, 'tran_count_min', 0))
            elif column_index == 24:  # COUNT Min列
                return str(map_point.count_range[0] if hasattr(map_point, 'count_range') and map_point.count_range else 0)
            elif column_index == 25:  # COUNT Max列
                return str(map_point.count_range[1] if hasattr(map_point, 'count_range') and map_point.count_range else 0)
            elif column_index == 26:  # COUNT Upper列
                return str(getattr(map_point, 'tran_count_max', 0))
            elif column_index == 27:  # ColorCCT Lower列
                return str(getattr(map_point, 'tran_color_cct_min', 0))
            elif column_index == 28:  # ColorCCT Min列
                return str(map_point.color_cct_range[0] if hasattr(map_point, 'color_cct_range') and map_point.color_cct_range else 0)
            elif column_index == 29:  # ColorCCT Max列
                return str(map_point.color_cct_range[1] if hasattr(map_point, 'color_cct_range') and map_point.color_cct_range else 0)
            elif column_index == 30:  # ColorCCT Upper列
                return str(getattr(map_point, 'tran_color_cct_max', 0))
            elif column_index == 31:  # diffCtemp Lower列
                return str(getattr(map_point, 'tran_diff_ctemp_min', 0))
            elif column_index == 32:  # diffCtemp Min列
                return str(map_point.diff_ctemp_range[0] if hasattr(map_point, 'diff_ctemp_range') and map_point.diff_ctemp_range else 0)
            elif column_index == 33:  # diffCtemp Max列
                return str(map_point.diff_ctemp_range[1] if hasattr(map_point, 'diff_ctemp_range') and map_point.diff_ctemp_range else 0)
            elif column_index == 34:  # diffCtemp Upper列
                return str(getattr(map_point, 'tran_diff_ctemp_max', 0))
            elif column_index == 35:  # FaceCtemp Lower列
                return str(getattr(map_point, 'tran_face_ctemp_min', 0))
            elif column_index == 36:  # FaceCtemp Min列
                return str(map_point.face_ctemp_range[0] if hasattr(map_point, 'face_ctemp_range') and map_point.face_ctemp_range else 0)
            elif column_index == 37:  # FaceCtemp Max列
                return str(map_point.face_ctemp_range[1] if hasattr(map_point, 'face_ctemp_range') and map_point.face_ctemp_range else 0)
            elif column_index == 38:  # FaceCtemp Upper列
                return str(getattr(map_point, 'tran_face_ctemp_max', 0))
            elif column_index == 39:  # ml列
                return str(getattr(map_point, 'ml', 0))
            else:
                # 对于其他列，返回默认值
                return "0"

        except Exception as e:
            logger.warning(f"==liuq debug== 获取列{column_index}的值失败: {e}")
            return "0"

    def _update_sort_indicator(self, column_index: int, sort_order: Qt.SortOrder):
        """手动更新排序指示器"""
        try:
            # 清除所有列的排序指示器
            for i in range(self.table.columnCount()):
                self.simple_header.setSortIndicator(i, Qt.AscendingOrder)
                self.simple_header.setSortIndicatorShown(False)

            # 设置当前列的排序指示器
            self.simple_header.setSortIndicator(column_index, sort_order)
            self.simple_header.setSortIndicatorShown(True)

            # 强制重绘表头
            self.simple_header.update()

        except Exception as e:
            logger.warning(f"==liuq debug== 更新排序指示器失败: {e}")

    def restore_natural_sort(self):
        """恢复自然排序状态（base_boundary0固定在第0行）"""
        try:
            logger.info(f"==liuq debug== 恢复自然排序")

            # 重置排序状态
            self.is_natural_sort = True
            self.user_sort_column = -1
            self.user_sort_order = Qt.AscendingOrder

            # 清除排序指示器
            self.simple_header.setSortIndicatorShown(False)

            # 重新应用自然排序（只对offset_map点）
            self.apply_natural_sort()

            logger.info(f"==liuq debug== 自然排序恢复完成")

        except Exception as e:
            logger.error(f"==liuq debug== 恢复自然排序失败: {e}")

    def get_map_point_by_row(self, row: int) -> Optional[MapPoint]:
        """
        根据表格行号获取对应的MapPoint对象

        Args:
            row: 表格行号

        Returns:
            对应的MapPoint对象，如果不存在则返回None
        """
        try:
            # 第0行是base_boundary0，第1行开始是offset_map点
            if row == 0:
                # 返回base_boundary0
                if self.base_boundary_point:

                    return self.base_boundary_point
                else:
                    logger.warning(f"==liuq debug== 第0行应该是base_boundary0，但base_boundary_point为空")
                    return None

            # 第1行开始对应offset_map点
            map_point_index = row - 1  # -1 because row 0 is base_boundary0
            if map_point_index < 0 or map_point_index >= len(self.map_points):
                logger.warning(f"==liuq debug== 无效的offset_map点索引: {map_point_index}，行号: {row}")
                return None

            # 从map_points列表获取
            map_point = self.map_points[map_point_index]

            return map_point

        except Exception as e:
            logger.error(f"==liuq debug== 获取行{row}对应的MapPoint失败: {e}")
            return None

    def _get_field_id_by_column(self, col: int) -> Optional[str]:
        """
        根据列索引获取字段ID（动态版本）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-04 16:55:00 +08:00; Reason: 重构为基于动态列定义的字段ID获取; Principle_Applied: 开闭原则;
        }}

        Args:
            col: 列索引

        Returns:
            Optional[str]: 字段ID，如果列索引无效则返回None
        """
        try:
            if 0 <= col < len(self.column_definitions):
                return self.column_definitions[col].field_id
            else:
                logger.warning(f"==liuq debug== 列索引超出范围: {col}, 总列数: {len(self.column_definitions)}")
                return None
        except Exception as e:
            logger.error(f"==liuq debug== 获取字段ID失败: {e}")
            return None

    def _create_field_binding(self, map_point: MapPoint, field_id: str, row: int, col: int):
        """为字段创建数据绑定（现在只是记录绑定关系，实际编辑通过表格内置功能）"""
        try:
            # 查找字段定义
            field_definition = None
            for field_def in self.field_definitions:
                if field_def.field_id == field_id:
                    field_definition = field_def
                    break

            if not field_definition:
                logger.warning(f"==liuq debug== 未找到字段定义: {field_id}")
                return

            # 记录绑定关系（用于后续的数据同步）
            binding_id = f"map_point_{id(map_point)}_{field_id}"


            # 注意：我们不再创建独立的编辑器，而是使用表格的内置编辑功能
            # 实际的数据同步在on_item_changed方法中处理

        except Exception as e:
            logger.error(f"==liuq debug== 创建字段绑定失败: {field_id} - {e}")

    def _validate_and_convert_value(self, value_str: str, field_definition: XMLFieldDefinition):
        """验证并转换字符串值到正确的数据类型"""
        try:
            from core.interfaces.xml_field_definition import FieldType

            if field_definition.field_type == FieldType.INTEGER:
                # 对于INTEGER类型，先尝试转换为float再转为int，以支持"0.0"这样的输入
                try:
                    float_val = float(value_str)
                    return int(float_val)
                except ValueError:
                    return int(value_str)
            elif field_definition.field_type == FieldType.FLOAT:
                return float(value_str)
            elif field_definition.field_type == FieldType.BOOLEAN:
                return value_str.lower() in ('true', '1', 'yes', 'on')
            elif field_definition.field_type == FieldType.STRING:
                return str(value_str)
            else:
                return str(value_str)

        except (ValueError, TypeError) as e:
            logger.warning(f"==liuq debug== 值转换失败: {value_str} -> {field_definition.field_type}: {e}")
            return None

    def _get_field_value_from_map_point(self, map_point: MapPoint, field_id: str):
        """
        从MapPoint对象获取字段值（重构版本 - 使用配置驱动）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-01 13:15:00 +08:00; Reason: 使用新的配置驱动字段获取逻辑; Principle_Applied: DRY原则和配置驱动设计;
        }}
        """
        try:
            # 首先尝试使用新的配置驱动方法
            try:
                value = get_map_point_field_value(map_point, field_id)
                if value is not None:
                    logger.debug(f"==liuq debug== 使用配置驱动获取字段值: {field_id} = {value}")
                    return value
            except Exception as e:
                logger.debug(f"==liuq debug== 配置驱动获取字段值失败，使用传统方法: {field_id}, {e}")

            # 基础字段（保持向后兼容）
            if field_id == 'alias_name':
                return map_point.alias_name
            elif field_id == 'weight':
                return map_point.weight
            elif field_id == 'x':
                return map_point.x
            elif field_id == 'y':
                return map_point.y
            elif field_id == 'offset_x':
                return map_point.offset_x
            elif field_id == 'offset_y':
                return map_point.offset_y
            elif field_id == 'trans_step':
                return getattr(map_point, 'trans_step', 0)

            # ERatio字段
            elif field_id == 'e_ratio_min':
                return map_point.e_ratio_range[0] if hasattr(map_point, 'e_ratio_range') and map_point.e_ratio_range else 0
            elif field_id == 'e_ratio_max':
                return map_point.e_ratio_range[1] if hasattr(map_point, 'e_ratio_range') and map_point.e_ratio_range else 0

            # BV字段
            elif field_id == 'bv_min':
                return map_point.bv_range[0] if map_point.bv_range else 0
            elif field_id == 'bv_max':
                return map_point.bv_range[1] if map_point.bv_range else 0
            elif field_id == 'tran_bv_min':
                return getattr(map_point, 'tran_bv_min', 0)
            elif field_id == 'tran_bv_max':
                return getattr(map_point, 'tran_bv_max', 0)

            # Ctemp字段
            elif field_id == 'ctemp_min':
                return map_point.ctemp_range[0] if hasattr(map_point, 'ctemp_range') and map_point.ctemp_range else 0
            elif field_id == 'ctemp_max':
                return map_point.ctemp_range[1] if hasattr(map_point, 'ctemp_range') and map_point.ctemp_range else 0
            elif field_id == 'tran_ctemp_min':
                return getattr(map_point, 'tran_ctemp_min', 0)
            elif field_id == 'tran_ctemp_max':
                return getattr(map_point, 'tran_ctemp_max', 0)

            # IR字段
            elif field_id == 'ir_min':
                return map_point.ir_range[0] if map_point.ir_range else 0
            elif field_id == 'ir_max':
                return map_point.ir_range[1] if map_point.ir_range else 0
            elif field_id == 'tran_ir_min':
                return getattr(map_point, 'tran_ir_min', 0)
            elif field_id == 'tran_ir_max':
                return getattr(map_point, 'tran_ir_max', 0)

            # AC字段
            elif field_id == 'ac_min':
                return map_point.ac_range[0] if hasattr(map_point, 'ac_range') and map_point.ac_range else 0
            elif field_id == 'ac_max':
                return map_point.ac_range[1] if hasattr(map_point, 'ac_range') and map_point.ac_range else 0
            elif field_id == 'tran_ac_min':
                return getattr(map_point, 'tran_ac_min', 0)
            elif field_id == 'tran_ac_max':
                return getattr(map_point, 'tran_ac_max', 0)

            # COUNT字段
            elif field_id == 'count_min':
                return map_point.count_range[0] if hasattr(map_point, 'count_range') and map_point.count_range else 0
            elif field_id == 'count_max':
                return map_point.count_range[1] if hasattr(map_point, 'count_range') and map_point.count_range else 0
            elif field_id == 'tran_count_min':
                return getattr(map_point, 'tran_count_min', 0)
            elif field_id == 'tran_count_max':
                return getattr(map_point, 'tran_count_max', 0)

            # ColorCCT字段
            elif field_id == 'color_cct_min':
                return map_point.color_cct_range[0] if hasattr(map_point, 'color_cct_range') and map_point.color_cct_range else 0
            elif field_id == 'color_cct_max':
                return map_point.color_cct_range[1] if hasattr(map_point, 'color_cct_range') and map_point.color_cct_range else 0
            elif field_id == 'tran_color_cct_min':
                return getattr(map_point, 'tran_color_cct_min', 0)
            elif field_id == 'tran_color_cct_max':
                return getattr(map_point, 'tran_color_cct_max', 0)

            # diffCtemp字段
            elif field_id == 'diff_ctemp_min':
                return map_point.diff_ctemp_range[0] if hasattr(map_point, 'diff_ctemp_range') and map_point.diff_ctemp_range else 0
            elif field_id == 'diff_ctemp_max':
                return map_point.diff_ctemp_range[1] if hasattr(map_point, 'diff_ctemp_range') and map_point.diff_ctemp_range else 0
            elif field_id == 'tran_diff_ctemp_min':
                return getattr(map_point, 'tran_diff_ctemp_min', 0)
            elif field_id == 'tran_diff_ctemp_max':
                return getattr(map_point, 'tran_diff_ctemp_max', 0)

            # FaceCtemp字段
            elif field_id == 'face_ctemp_min':
                return map_point.face_ctemp_range[0] if hasattr(map_point, 'face_ctemp_range') and map_point.face_ctemp_range else 0
            elif field_id == 'face_ctemp_max':
                return map_point.face_ctemp_range[1] if hasattr(map_point, 'face_ctemp_range') and map_point.face_ctemp_range else 0
            elif field_id == 'tran_face_ctemp_min':
                return getattr(map_point, 'tran_face_ctemp_min', 0)
            elif field_id == 'tran_face_ctemp_max':
                return getattr(map_point, 'tran_face_ctemp_max', 0)

            # ml字段（GUI显示转换 - 修复数据转换bug）
            #
            # {{CHENGQI:
            # Action: Modified; Timestamp: 2025-08-01 13:55:00 +08:00; Reason: 添加ml字段GUI显示转换逻辑，保持用户友好性; Principle_Applied: 显示存储分离原则;
            # }}
            #
            elif field_id == 'ml':
                # 获取原始内部值
                raw_value = get_map_point_field_value(map_point, 'ml')

                # 转换为GUI显示值（仅在显示层转换）
                if raw_value == 65535:
                    return 3
                elif raw_value == 65471:
                    return 2
                else:
                    return raw_value

            else:
                logger.warning(f"==liuq debug== 未知字段ID: {field_id}")
                return None
        except Exception as e:
            logger.error(f"==liuq debug== 获取字段值失败: {field_id} - {e}")
            return None

    def _set_field_value_to_map_point(self, map_point: MapPoint, field_id: str, value):
        """
        设置MapPoint对象的字段值（重构版本 - 使用配置驱动）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-01 13:20:00 +08:00; Reason: 使用新的配置驱动字段设置逻辑; Principle_Applied: DRY原则和配置驱动设计;
        }}
        """
        try:
            # 首先尝试使用新的配置驱动方法
            success = set_map_point_field_value(map_point, field_id, value)
            if success:

                return



            # 基础字段（保持向后兼容）
            if field_id == 'alias_name':
                map_point.alias_name = str(value)
            elif field_id == 'weight':
                map_point.weight = float(value)
            elif field_id == 'x':
                map_point.x = float(value)
            elif field_id == 'y':
                map_point.y = float(value)
            elif field_id == 'offset_x':
                map_point.offset_x = float(value)
            elif field_id == 'offset_y':
                map_point.offset_y = float(value)
            elif field_id == 'trans_step':
                setattr(map_point, 'trans_step', float(value))

            # ERatio字段
            elif field_id == 'e_ratio_min':
                if not hasattr(map_point, 'e_ratio_range') or not map_point.e_ratio_range:
                    map_point.e_ratio_range = (0.0, 0.0)
                map_point.e_ratio_range = (float(value), map_point.e_ratio_range[1])
            elif field_id == 'e_ratio_max':
                if not hasattr(map_point, 'e_ratio_range') or not map_point.e_ratio_range:
                    map_point.e_ratio_range = (0.0, 0.0)
                map_point.e_ratio_range = (map_point.e_ratio_range[0], float(value))

            # BV字段
            elif field_id == 'bv_min':
                if not map_point.bv_range:
                    map_point.bv_range = (0.0, 0.0)
                map_point.bv_range = (float(value), map_point.bv_range[1])
            elif field_id == 'bv_max':
                if not map_point.bv_range:
                    map_point.bv_range = (0.0, 0.0)
                map_point.bv_range = (map_point.bv_range[0], float(value))
            elif field_id == 'tran_bv_min':
                setattr(map_point, 'tran_bv_min', float(value))
            elif field_id == 'tran_bv_max':
                setattr(map_point, 'tran_bv_max', float(value))

            # Ctemp字段
            elif field_id == 'ctemp_min':
                if not hasattr(map_point, 'ctemp_range') or not map_point.ctemp_range:
                    map_point.ctemp_range = (0.0, 0.0)
                map_point.ctemp_range = (float(value), map_point.ctemp_range[1])
            elif field_id == 'ctemp_max':
                if not hasattr(map_point, 'ctemp_range') or not map_point.ctemp_range:
                    map_point.ctemp_range = (0.0, 0.0)
                map_point.ctemp_range = (map_point.ctemp_range[0], float(value))
            elif field_id == 'tran_ctemp_min':
                setattr(map_point, 'tran_ctemp_min', float(value))
            elif field_id == 'tran_ctemp_max':
                setattr(map_point, 'tran_ctemp_max', float(value))

            # IR字段
            elif field_id == 'ir_min':
                if not map_point.ir_range:
                    map_point.ir_range = (0.0, 0.0)
                map_point.ir_range = (float(value), map_point.ir_range[1])
            elif field_id == 'ir_max':
                if not map_point.ir_range:
                    map_point.ir_range = (0.0, 0.0)
                map_point.ir_range = (map_point.ir_range[0], float(value))
            elif field_id == 'tran_ir_min':
                setattr(map_point, 'tran_ir_min', float(value))
            elif field_id == 'tran_ir_max':
                setattr(map_point, 'tran_ir_max', float(value))

            # AC字段
            elif field_id == 'ac_min':
                if not hasattr(map_point, 'ac_range') or not map_point.ac_range:
                    map_point.ac_range = (0.0, 0.0)
                map_point.ac_range = (float(value), map_point.ac_range[1])
            elif field_id == 'ac_max':
                if not hasattr(map_point, 'ac_range') or not map_point.ac_range:
                    map_point.ac_range = (0.0, 0.0)
                map_point.ac_range = (map_point.ac_range[0], float(value))
            elif field_id == 'tran_ac_min':
                setattr(map_point, 'tran_ac_min', float(value))
            elif field_id == 'tran_ac_max':
                setattr(map_point, 'tran_ac_max', float(value))

            # COUNT字段
            elif field_id == 'count_min':
                if not hasattr(map_point, 'count_range') or not map_point.count_range:
                    map_point.count_range = (0.0, 0.0)
                map_point.count_range = (float(value), map_point.count_range[1])
            elif field_id == 'count_max':
                if not hasattr(map_point, 'count_range') or not map_point.count_range:
                    map_point.count_range = (0.0, 0.0)
                map_point.count_range = (map_point.count_range[0], float(value))
            elif field_id == 'tran_count_min':
                setattr(map_point, 'tran_count_min', float(value))
            elif field_id == 'tran_count_max':
                setattr(map_point, 'tran_count_max', float(value))

            # ColorCCT字段
            elif field_id == 'color_cct_min':
                if not hasattr(map_point, 'color_cct_range') or not map_point.color_cct_range:
                    map_point.color_cct_range = (0.0, 0.0)
                map_point.color_cct_range = (float(value), map_point.color_cct_range[1])
            elif field_id == 'color_cct_max':
                if not hasattr(map_point, 'color_cct_range') or not map_point.color_cct_range:
                    map_point.color_cct_range = (0.0, 0.0)
                map_point.color_cct_range = (map_point.color_cct_range[0], float(value))
            elif field_id == 'tran_color_cct_min':
                setattr(map_point, 'tran_color_cct_min', float(value))
            elif field_id == 'tran_color_cct_max':
                setattr(map_point, 'tran_color_cct_max', float(value))

            # diffCtemp字段
            elif field_id == 'diff_ctemp_min':
                if not hasattr(map_point, 'diff_ctemp_range') or not map_point.diff_ctemp_range:
                    map_point.diff_ctemp_range = (0.0, 0.0)
                map_point.diff_ctemp_range = (float(value), map_point.diff_ctemp_range[1])
            elif field_id == 'diff_ctemp_max':
                if not hasattr(map_point, 'diff_ctemp_range') or not map_point.diff_ctemp_range:
                    map_point.diff_ctemp_range = (0.0, 0.0)
                map_point.diff_ctemp_range = (map_point.diff_ctemp_range[0], float(value))
            elif field_id == 'tran_diff_ctemp_min':
                setattr(map_point, 'tran_diff_ctemp_min', float(value))
            elif field_id == 'tran_diff_ctemp_max':
                setattr(map_point, 'tran_diff_ctemp_max', float(value))

            # FaceCtemp字段
            elif field_id == 'face_ctemp_min':
                if not hasattr(map_point, 'face_ctemp_range') or not map_point.face_ctemp_range:
                    map_point.face_ctemp_range = (0.0, 0.0)
                map_point.face_ctemp_range = (float(value), map_point.face_ctemp_range[1])
            elif field_id == 'face_ctemp_max':
                if not hasattr(map_point, 'face_ctemp_range') or not map_point.face_ctemp_range:
                    map_point.face_ctemp_range = (0.0, 0.0)
                map_point.face_ctemp_range = (map_point.face_ctemp_range[0], float(value))
            elif field_id == 'tran_face_ctemp_min':
                setattr(map_point, 'tran_face_ctemp_min', float(value))
            elif field_id == 'tran_face_ctemp_max':
                setattr(map_point, 'tran_face_ctemp_max', float(value))

            # ml字段 - 实现GUI输入值到内部值的反向转换
            #
            # {{CHENGQI:
            # Action: Modified; Timestamp: 2025-08-01 16:05:00 +08:00; Reason: 实现ml字段GUI输入值到内部值的反向转换逻辑; Principle_Applied: 显示存储分离原则;
            # }}
            #
            elif field_id == 'ml':
                # 将GUI输入值转换为内部存储值
                input_value = float(value)

                # 反向转换：GUI友好值 → 内部值
                if input_value == 2:
                    internal_value = 65471
                elif input_value == 3:
                    internal_value = 65535
                else:
                    # 其他值直接使用
                    internal_value = input_value

                # 存储到extra_attributes中（保持与XML结构一致）
                if not hasattr(map_point, 'extra_attributes') or map_point.extra_attributes is None:
                    map_point.extra_attributes = {}
                map_point.extra_attributes['ml'] = internal_value



            else:
                logger.warning(f"==liuq debug== 未知字段ID: {field_id}")
        except Exception as e:
            logger.error(f"==liuq debug== 设置字段值失败: {field_id} = {value} - {e}")

    def filter_table(self):
        """筛选表格"""
        filter_text = self.filter_input.text().lower()

        visible_count = 0
        for row in range(self.table.rowCount()):
            # 检查MapList列是否包含筛选文本
            map_name_item = self.table.item(row, 0)
            if map_name_item:
                map_name = map_name_item.text().lower()
                should_show = filter_text in map_name
                self.table.setRowHidden(row, not should_show)
                if should_show:
                    visible_count += 1

        # 更新状态
        total_count = self.table.rowCount()
        self.status_label.setText(f"显示 {visible_count} / {total_count} 个Map点")

    def on_selection_changed(self):
        """处理选择变化"""
        try:
            current_row = self.table.currentRow()
            if current_row >= 0:
                if current_row == 0:
                    # 第0行是base_boundary0行
                    if hasattr(self, 'base_boundary_point') and self.base_boundary_point:
                        self.base_boundary_selected.emit(self.base_boundary_point)

                else:
                    # 其他行是map_point行
                    first_item = self.table.item(current_row, 0)
                    if first_item:
                        map_point = first_item.data(Qt.UserRole)
                        if map_point:
                            self.map_point_selected.emit(map_point)


        except Exception as e:
            logger.warning(f"==liuq debug== 处理选择变化失败: {e}")

    def clear(self):
        """清空表格"""
        self.table.setRowCount(0)
        self.configuration = None
        self.map_points = []
        self.status_label.setText("请加载Map配置文件")


    def get_selected_map_point(self) -> Optional[MapPoint]:
        """获取当前选中的Map点"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            first_item = self.table.item(current_row, 0)
            if first_item:
                return first_item.data(Qt.UserRole)
        return None
