#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map点列表表格组件

提供详细的Map点信息表格视图，支持排序、筛选和选择联动

作者: AI Assistant
日期: 2025-08-25
"""

import logging
from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QLineEdit, QPushButton, QComboBox, QShortcut
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QDoubleValidator, QKeySequence

from core.models.map_data import MapConfiguration, MapPoint, BaseBoundary
from core.interfaces.xml_field_definition import TableColumnDefinition, TableConfiguration

from gui.widgets.map_table_data_manager import MapTableDataManager
from gui.widgets.map_table_filter import MapTableFilter
from gui.widgets.map_table_sorter import MapTableSorter
from gui.widgets.map_table_editor import MapTableEditor
from gui.widgets.map_table_styler import MapTableStyler
from gui.widgets.simple_header_view import SimpleHeaderView

logger = logging.getLogger(__name__)


class MapTableWidget(QWidget):
    """Map表格组件"""

    # 信号定义
    map_point_selected = pyqtSignal(object)  # Map点被选中
    base_boundary_selected = pyqtSignal(object)  # Base Boundary被选中
    data_changed = pyqtSignal(object, str, object)  # 数据改变

    def __init__(self, parent=None):
        super().__init__(parent)
        self.configuration: Optional[MapConfiguration] = None

        # 初始化UI
        self._init_ui()

        # 初始化组件
        self._init_components()

        # 设置连接
        self._setup_connections()

        logger.info("Map表格组件初始化完成")

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建控制区域
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(10, 10, 10, 5)

        # 名称搜索
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("名称/别名/坐标 搜索…")
        self.filter_input.setMaximumWidth(200)
        control_layout.addWidget(QLabel("名称:"))
        control_layout.addWidget(self.filter_input)

        # 区间筛选（与 REFERENCE_INTERVALS 完全一致）
        from utils.white_points import REFERENCE_INTERVALS
        self.interval_combo = QComboBox()
        self.interval_combo.addItem("全部")
        for a, b in REFERENCE_INTERVALS:
            self.interval_combo.addItem(f"{a}-{b}")
        control_layout.addWidget(QLabel("区间:"))
        control_layout.addWidget(self.interval_combo)

        # BV范围
        self.bv_min_edit = QLineEdit(); self.bv_min_edit.setPlaceholderText("Min")
        self.bv_max_edit = QLineEdit(); self.bv_max_edit.setPlaceholderText("Max")
        self.bv_min_edit.setMaximumWidth(80); self.bv_max_edit.setMaximumWidth(80)
        control_layout.addWidget(QLabel("BV范围:"))
        control_layout.addWidget(self.bv_min_edit)
        control_layout.addWidget(QLabel("~"))
        control_layout.addWidget(self.bv_max_edit)

        # 列选择（放宽下拉宽度，便于查看完整字段名）
        self.column_combo = QComboBox(); self.column_combo.addItem("所有列")
        try:
            self.column_combo.setMinimumWidth(200)
            self.column_combo.setMaximumWidth(320)
        except Exception:
            # 兼容低版本Qt
            self.column_combo.setMaximumWidth(240)
        control_layout.addWidget(self.column_combo)

        # 状态
        self.status_label = QLabel("显示: 0/0 行")
        control_layout.addWidget(self.status_label)

        control_layout.addStretch()

        # 应用/重置
        self.apply_button = QPushButton("应用")
        self.reset_button = QPushButton("重置")
        self.refresh_button = QPushButton("恢复自然排序")
        self.apply_button.setMaximumWidth(80)
        self.reset_button.setMaximumWidth(80)
        self.refresh_button.setMaximumWidth(120)
        control_layout.addWidget(self.apply_button)
        control_layout.addWidget(self.reset_button)
        control_layout.addWidget(self.refresh_button)

        layout.addLayout(control_layout)

        # 创建表格
        self.table_widget = QTableWidget()
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setShowGrid(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)

        # 设置表头
        header = SimpleHeaderView(Qt.Horizontal)
        self.table_widget.setHorizontalHeader(header)
        try:
            # 默认列宽更宽一些，展示更完整
            header.setDefaultSectionSize(150)
            header.setMinimumSectionSize(80)
            # 允许用户交互拖动
            if hasattr(QHeaderView, 'Interactive'):
                header.setSectionResizeMode(QHeaderView.Interactive)
        except Exception:
            pass

        layout.addWidget(self.table_widget)

        # 绑定保存快捷键 Ctrl+S
        try:
            self._save_shortcut = QShortcut(QKeySequence.Save, self)
            self._save_shortcut.activated.connect(self._on_save_shortcut)
            logger.info("==liuq debug== 绑定 Ctrl+S 保存快捷键 成功")
        except Exception as _e:
            logger.warning(f"==liuq debug== 绑定保存快捷键失败: {_e}")

    def _init_components(self):
        """初始化组件"""
        # 数据管理器
        self.data_manager = MapTableDataManager(self.table_widget)

        # 筛选器
        self.filter = MapTableFilter(self.table_widget)
        self.filter.set_filter_widgets(
            self.filter_input, self.status_label, self.column_combo,
            self.interval_combo, self.bv_min_edit, self.bv_max_edit
        )

        # 排序器
        self.sorter = MapTableSorter(self.table_widget)
        self.sorter.setup_header_sorting(self.table_widget.horizontalHeader())

        # 编辑器
        self.editor = MapTableEditor(self.table_widget)
        # 默认启用双击编辑
        try:
            self.editor.enable_cell_editing(True)
            logger.info("==liuq debug== 默认启用双击编辑功能")
        except Exception as _e:
            logger.warning(f"==liuq debug== 启用编辑失败: {_e}")

        # 样式管理器
        self.styler = MapTableStyler(self.table_widget)
        self.styler.apply_table_style()

    def _setup_connections(self):
        """设置连接"""
        # 表格选择事件
        self.table_widget.itemSelectionChanged.connect(self._on_selection_changed)

        # 表格编辑事件
        self.table_widget.itemChanged.connect(self.editor.on_item_changed)

        # 刷新按钮（恢复自然排序）
        self.refresh_button.clicked.connect(self.refresh_table)
        self.apply_button.clicked.connect(self.filter.apply_filters)
        self.reset_button.clicked.connect(self.filter.reset_filters)

        # 编辑器数据改变事件
        self.editor.data_changed.connect(self._on_data_changed)

    def set_configuration(self, configuration: MapConfiguration):
        """设置Map配置"""
        self.configuration = configuration
        self.data_manager.set_configuration(configuration)
        self.filter.set_configuration(configuration)
        self.editor.set_column_definitions(self.data_manager.column_definitions)

        # 更新列选择下拉框
        self._update_column_combo()

        # 刷新表格
        self.refresh_table()


    def set_xml_file_path(self, xml_file_path: str):
        """设置XML文件路径（为自动保存等功能预留接口）"""
        try:
            # 某些调用方依赖此方法存在；此处仅记录日志并保留路径
            self._xml_file_path = xml_file_path
            logger.info(f"==liuq debug== MapTableWidget 记录XML路径: {xml_file_path}")
        except Exception as _e:
            logger.warning(f"==liuq debug== MapTableWidget.set_xml_file_path失败: {_e}")

    def _update_column_combo(self):
        """更新列选择下拉框"""
        self.column_combo.clear()
        self.column_combo.addItem("所有列")

        if self.data_manager.column_definitions:
            for col_def in self.data_manager.column_definitions:
                self.column_combo.addItem(col_def.display_name)

    def _on_selection_changed(self):
        """选择改变事件"""
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        item = self.table_widget.item(row, 0)
        if item:
            data_object = item.data(Qt.UserRole)

            if isinstance(data_object, MapPoint):
                self.map_point_selected.emit(data_object)
            elif isinstance(data_object, BaseBoundary):
                self.base_boundary_selected.emit(data_object)

    def _on_data_changed(self, data_object, field_id, new_value):
        """数据改变事件"""
        self.data_changed.emit(data_object, field_id, new_value)

    def refresh_table(self):
        """刷新表格"""
        try:
            # 清空筛选
            self.filter.reset_filters()

            # 重新填充数据
            row_count = self.data_manager.populate_table()

            # 默认加宽列宽（不影响用户后续拖动调整）
            self._apply_default_column_widths()

            # 应用样式
            self.styler.apply_row_styles()

            logger.info(f"表格刷新完成，共{row_count}行")

        except Exception as e:
            logger.error(f"表格刷新失败: {e}")

    def _apply_default_column_widths(self):
        """根据列类型设置更合理的默认列宽。
        规则建议：别名列150px，坐标列120px，数值列100px，其他列130px。
        此方法在刷新填充后调用，不影响用户后续拖动调整。
        """
        try:
            if not getattr(self, 'data_manager', None) or not self.data_manager.column_definitions:
                return

            # 基于 field_id 的简单分类
            alias_keywords = ('alias', 'name')
            coord_keywords = ('x', 'y', 'rpg', 'bpg', 'offset')

            for i, col in enumerate(self.data_manager.column_definitions):
                fid = (getattr(col, 'field_id', '') or '').lower()
                w = 130  # 默认其他列
                if any(k in fid for k in alias_keywords):
                    w = 150
                elif any(k in fid for k in coord_keywords):
                    w = 120
                # 数值列由字段注册表已右对齐，这里给予 100 的较紧宽度
                if fid in ('weight',) or fid.endswith('_min') or fid.endswith('_max'):
                    w = 100
                try:
                    self.table_widget.setColumnWidth(i, w)
                except Exception:
                    pass
        except Exception as _e:
            logger.debug(f"==liuq debug== _apply_default_column_widths 失败: {_e}")

    def enable_cell_editing(self, enabled: bool):
        """启用/禁用单元格编辑"""
        self.editor.enable_cell_editing(enabled)

    def get_selected_map_point(self) -> Optional[MapPoint]:
        """获取选中的Map点"""
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        return self.data_manager.get_map_point_by_row(row)

    def get_selected_base_boundary(self) -> Optional[BaseBoundary]:
        """获取选中的Base Boundary"""
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        return self.data_manager.get_base_boundary_by_row(row)

    def get_visible_map_points(self) -> List[MapPoint]:
        """获取可见的Map点"""
        return self.filter.get_visible_map_points()

    def get_visible_base_boundary(self) -> Optional[BaseBoundary]:
        """获取可见的Base Boundary"""
        return self.filter.get_visible_base_boundary()

    def apply_filter(self, filter_text: str, column: int = -1):
        """应用筛选"""
        self.filter_input.setText(filter_text)
        if column >= 0:
            self.column_combo.setCurrentIndex(column + 1)
        self.filter.apply_filters()

    def clear_filter(self):
        """清除筛选"""
        self.filter.reset_filters()

    def apply_sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """应用排序"""
        self.sorter.current_sort_column = column
        self.sorter.current_sort_order = order
        self.sorter.apply_sort()

    def _on_save_shortcut(self):
        """处理 Ctrl+S 保存快捷键"""
        try:
            # 通过XML写入服务保存当前配置，保持格式与结构
            if not self.configuration:
                logger.warning("==liuq debug== 无可保存配置")
                return
            from core.services.map_analysis.xml_writer_service import XMLWriterService
            writer = XMLWriterService()
            # 若上层已通过 load_xml_for_editing 载入，可设置当前路径
            if hasattr(self, '_xml_file_path') and getattr(self, '_xml_file_path', None):
                # 装载当前xml到writer，以便优化写入保持原格式
                try:
                    writer.load_xml_for_editing(self._xml_file_path)
                except Exception as _e:
                    logger.warning(f"==liuq debug== 预载入XML以保持格式失败，继续直接写入: {_e}")
                # 标记已修改（编辑器on_item_changed时也可标记）
                try:
                    writer.mark_data_modified("用户快捷键保存")
                except Exception:
                    pass
                ok = writer.write_xml(self.configuration, self._xml_file_path, backup=True, preserve_format=True)
            else:
                # 未知路径时不保存，避免误写
                logger.warning("==liuq debug== 未设置XML路径，保存已跳过")
                ok = False
            if ok:
                logger.info("==liuq debug== Ctrl+S 保存成功")
            else:
                logger.error("==liuq debug== Ctrl+S 保存失败")
        except Exception as e:
            logger.error(f"==liuq debug== 保存快捷键处理异常: {e}")

    def set_style(self, style_config: Dict[str, Any]):
        """设置样式"""
        self.styler.update_style_config(style_config)