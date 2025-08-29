#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单张图片 EXIF 快速查看对话框
==liuq debug== ExifQuickViewDialog

{{CHENGQI:
Action: Added; Timestamp: 2025-08-12 16:30:00 +08:00; Reason: 新增拖拽图片后单张EXIF快速查看功能; Principle_Applied: KISS, UX-Feedback;
}}

{{CHENGQI:
Action: Modified; Timestamp: 2025-08-13 10:15:00 +08:00; Reason: 优化CCM矩阵和SGW字段显示格式，CCM矩阵显示为3x3格式，SGW字段合并显示; Principle_Applied: UX-Enhancement, Data-Visualization;
}}

{{CHENGQI:
Action: Modified; Timestamp: 2025-08-13 10:25:00 +08:00; Reason: 扩展成对字段合并显示功能，支持AGW、Mix_csalgo、After_face、cnvgEst、gslGain等字段对的合并显示; Principle_Applied: DRY, UX-Enhancement;
}}

{{CHENGQI:
Action: Modified; Timestamp: 2025-08-13 10:35:00 +08:00; Reason: 扩展CCM矩阵字段支持face_cc_face_ccm和face_cc_orig_face_ccm，添加Ctemp权重字段成对显示; Principle_Applied: UX-Enhancement, Data-Visualization;
}}
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List

import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt

from core.services.exif_processing.exif_parser_service import ExifParserService
from core.interfaces.exif_processing import ExifParseOptions
from gui.tabs.exif_processing_tab import ExifProcessingTab


class ExifQuickViewDialog(QDialog):
    def __init__(self, image_path: Path, parent=None):
        super().__init__(parent)
        self._image_path = Path(image_path)
        self._parser = ExifParserService()
        self._fields = ExifProcessingTab._priority_list()
        self._values: Dict[str, Any] = {}
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        self.setWindowTitle(self._image_path.name)
        self.resize(700, 860)
        self.setModal(True)

        layout = QVBoxLayout(self)
        # Scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        grid = QGridLayout(container)
        # 还原为两列布局：字段名/温度范围(3) : 数值(7)
        grid.setColumnStretch(0, 3)  # 字段名/温度范围列
        grid.setColumnStretch(1, 7)  # 数值列
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        # 留给填充用
        self._grid = grid
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # footer buttons
        footer = QHBoxLayout()
        footer.addStretch(1)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        footer.addWidget(btn_close)
        layout.addLayout(footer)

    def _fmt(self, v: Any, field_name: str = None) -> str:
        if v is None:
            return "N/A"
        try:
            # 特殊处理CCM矩阵字段
            ccm_fields = ['meta_data_resultCcmatrix', 'face_cc_face_ccm', 'face_cc_orig_face_ccm']
            if field_name in ccm_fields and isinstance(v, (list, tuple)) and len(v) == 9:
                # 将9个数值重新排列为3x3矩阵格式，保留6位小数，右对齐
                matrix_lines = []
                for i in range(3):
                    row_values = []
                    for j in range(3):
                        idx = i * 3 + j
                        if isinstance(v[idx], (int, float)):
                            formatted_val = f"{float(v[idx]):>10.6f}"
                        else:
                            formatted_val = f"{str(v[idx]):>10}"
                        row_values.append(formatted_val)
                    matrix_lines.append("  ".join(row_values))
                return "\n".join(matrix_lines)

            if isinstance(v, float):
                s = f"{v:.4f}"
                return s.rstrip('0').rstrip('.')
            if isinstance(v, (list, tuple)):
                parts = []
                for it in v:
                    if isinstance(it, float):
                        s = f"{it:.4f}".rstrip('0').rstrip('.')
                        parts.append(s)
                    else:
                        parts.append(str(it))
                return ", ".join(parts)
            if isinstance(v, dict):
                try:
                    return json.dumps(v, ensure_ascii=False)
                except Exception:
                    return str(v)
            return str(v)
        except Exception:
            return str(v)

    def _create_ctemp_weight_display(self, count_data, weight_data, start_row):
        """
        创建ctemp_weight字段的特殊两列显示

        Args:
            count_data: ctemp_weight_Ctemp_count字段的数据
            weight_data: ctemp_weight_Ctemp_weight字段的数据
            start_row: 起始行号

        Returns:
            int: 下一个可用的行号
        """
        # 解析count和weight数据
        count_values = self._parse_ctemp_data(count_data)
        weight_values = self._parse_ctemp_data(weight_data)

        # 生成40组温度区间（从1500到13500，每组300K）
        temp_ranges = []
        for i in range(40):
            temp_start = 1500 + i * 300
            temp_end = temp_start + 300
            temp_ranges.append(f"CT {temp_start}--{temp_end}")

        # 显示字段名标题行
        title_name_lbl = QLabel("ctemp_weight_Ctemp_weight")
        title_name_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        title_name_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px; background-color: #F5F5F5;")

        title_val_lbl = QLabel("Count                Weight")
        title_val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        title_val_lbl.setAlignment(Qt.AlignRight)  # 标题右对齐
        title_val_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px; background-color: #F5F5F5; font-family: 'Courier New', monospace;")

        self._grid.addWidget(title_name_lbl, start_row, 0)
        self._grid.addWidget(title_val_lbl, start_row, 1)
        current_row = start_row + 1

        # 显示40组数据
        for i in range(40):
            # 第一列：温度范围
            temp_range_lbl = QLabel(temp_ranges[i])
            temp_range_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            temp_range_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px;")

            # 第二列：count和weight值，优化格式
            count_val = count_values[i] if i < len(count_values) else 0
            weight_val = weight_values[i] if i < len(weight_values) else 0.0

            # count显示为整型，weight保留小数，移除分隔符，使用空格分隔
            count_str = f"{int(count_val):<6}"  # 左对齐，宽度6
            weight_str = f"{weight_val:>15.6f}"  # 右对齐，宽度15，保留6位小数
            value_text = f"{count_str}    {weight_str}"  # 使用4个空格分隔，移除逗号

            value_lbl = QLabel(value_text)
            value_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_lbl.setAlignment(Qt.AlignRight)  # 整个标签右对齐
            value_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px; font-family: 'Courier New', monospace;")

            self._grid.addWidget(temp_range_lbl, current_row, 0)
            self._grid.addWidget(value_lbl, current_row, 1)
            current_row += 1

        return current_row



    def _create_offset_map_triple_display(self, combined_data, weight_data, dummy_data, start_row):
        """
        创建offset_map三字段的特殊两列显示

        Args:
            combined_data: 包含offsetMapCount和offsetMapYCount的字典数据
            weight_data: map_weight_offsetMapWeight字段的数据
            dummy_data: 占位参数（保持接口兼容）
            start_row: 起始行号

        Returns:
            int: 下一个可用的行号
        """
        # 从组合数据中提取count和y_count值
        count_values, y_count_values = self._parse_offset_map_combined_data(combined_data)
        weight_values = self._parse_ctemp_data(weight_data)

        # 确定显示的行数（通常是120行，对应120个offset map点）
        max_rows = max(len(count_values), len(y_count_values), len(weight_values), 120)

        # 显示字段名标题行
        title_name_lbl = QLabel("offset_map")
        title_name_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        title_name_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px; background-color: #F5F5F5;")

        title_val_lbl = QLabel("Count    YCount        Weight")
        title_val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        title_val_lbl.setAlignment(Qt.AlignRight)  # 标题右对齐
        title_val_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px; background-color: #F5F5F5; font-family: 'Courier New', monospace;")

        self._grid.addWidget(title_name_lbl, start_row, 0)
        self._grid.addWidget(title_val_lbl, start_row, 1)
        current_row = start_row + 1

        # 显示120行offset_map数据
        for i in range(max_rows):
            # 第一列：Map索引标识
            map_index_text = f"offset_map{i+1:02d}"

            map_index_lbl = QLabel(map_index_text)
            map_index_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            map_index_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px;")

            # 第二列：count、y_count和weight值，优化格式
            count_val = count_values[i] if i < len(count_values) else 0
            y_count_val = y_count_values[i] if i < len(y_count_values) else 0
            weight_val = weight_values[i] if i < len(weight_values) else 0.0

            # 格式化三列数据：count(整数), y_count(整数), weight(小数)
            count_str = f"{int(count_val):<8}"      # 左对齐，宽度8
            y_count_str = f"{int(y_count_val):<8}"  # 左对齐，宽度8
            weight_str = f"{weight_val:>15.6f}"     # 右对齐，宽度15，保留6位小数
            value_text = f"{count_str}  {y_count_str}  {weight_str}"  # 使用2个空格分隔

            value_lbl = QLabel(value_text)
            value_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_lbl.setAlignment(Qt.AlignRight)  # 整个标签右对齐
            value_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px; font-family: 'Courier New', monospace;")

            self._grid.addWidget(map_index_lbl, current_row, 0)
            self._grid.addWidget(value_lbl, current_row, 1)
            current_row += 1

        return current_row

    def _parse_offset_map_combined_data(self, data):
        """
        解析包含offsetMapCount和offsetMapYCount的组合数据

        Args:
            data: 可能是字典列表或单个字典，包含offsetMapCount和offsetMapYCount数据

        Returns:
            Tuple[List[float], List[float]]: (count_values, y_count_values)
        """
        count_values = []
        y_count_values = []

        if data is None:
            return count_values, y_count_values

        # 处理列表格式：[{'offsetMapCount': 0, 'offsetMapYCount': 0}, ...]
        if isinstance(data, (list, tuple)):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    count_val = item.get('offsetMapCount', 0)
                    y_count_val = item.get('offsetMapYCount', 0)
                    try:
                        count_values.append(float(count_val))
                        y_count_values.append(float(y_count_val))
                    except (ValueError, TypeError):
                        count_values.append(0.0)
                        y_count_values.append(0.0)
                else:
                    count_values.append(0.0)
                    y_count_values.append(0.0)

        # 处理字典格式
        elif isinstance(data, dict):
            # 按索引顺序提取offsetMapCount和offsetMapYCount值
            count_dict = {}
            y_count_dict = {}

            for key, value in data.items():
                if key == 'offsetMapCount':
                    # 直接的offsetMapCount键
                    try:
                        count_dict[0] = float(value)
                    except (ValueError, TypeError):
                        count_dict[0] = 0.0
                elif key == 'offsetMapYCount':
                    # 直接的offsetMapYCount键
                    try:
                        y_count_dict[0] = float(value)
                    except (ValueError, TypeError):
                        y_count_dict[0] = 0.0
                elif 'offsetMapCount' in key and key != 'offsetMapCount':
                    # 带索引的offsetMapCount键，如offsetMapCount01, offsetMapCount02等
                    try:
                        # 提取索引号
                        index_str = key.replace('offsetMapCount', '')
                        if index_str.isdigit():
                            index = int(index_str)
                            count_dict[index] = float(value)
                    except (ValueError, TypeError):
                        continue
                elif 'offsetMapYCount' in key and key != 'offsetMapYCount':
                    # 带索引的offsetMapYCount键
                    try:
                        # 提取索引号
                        index_str = key.replace('offsetMapYCount', '')
                        if index_str.isdigit():
                            index = int(index_str)
                            y_count_dict[index] = float(value)
                    except (ValueError, TypeError):
                        continue

            # 按索引顺序构建列表（最多120个）
            for i in range(120):
                count_val = count_dict.get(i, 0.0)
                y_count_val = y_count_dict.get(i, 0.0)
                count_values.append(count_val)
                y_count_values.append(y_count_val)

        # 确保至少有120个数据点
        while len(count_values) < 120:
            count_values.append(0.0)
        while len(y_count_values) < 120:
            y_count_values.append(0.0)

        return count_values, y_count_values

    def _parse_offset_map_data(self, data):
        """
        解析offset_map数据，提取数值列表

        Args:
            data: 原始数据（可能是字符串、列表、字典或其他格式）

        Returns:
            List[float]: 解析后的数值列表
        """
        if data is None:
            return []

        if isinstance(data, dict):
            # 如果是字典，尝试提取数值
            values = []
            for key, value in data.items():
                try:
                    if isinstance(value, (int, float)):
                        values.append(float(value))
                    elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                        values.append(float(value))
                except (ValueError, TypeError):
                    continue
            return values

        if isinstance(data, (list, tuple)):
            # 如果已经是列表，递归处理每个元素
            values = []
            for item in data:
                if isinstance(item, dict):
                    # 递归处理字典元素
                    sub_values = self._parse_offset_map_data(item)
                    values.extend(sub_values)
                elif isinstance(item, (int, float)):
                    values.append(float(item))
                elif isinstance(item, str):
                    try:
                        values.append(float(item))
                    except (ValueError, TypeError):
                        continue
            return values

        if isinstance(data, str):
            # 如果是字符串，尝试解析
            try:
                # 移除方括号和多余空格，按逗号分割
                cleaned = data.strip('[]').replace(' ', '')
                if cleaned:
                    values = [float(x.strip()) for x in cleaned.split(',') if x.strip()]
                    return values
            except (ValueError, AttributeError):
                pass

        # 如果是单个数值
        try:
            return [float(data)]
        except (ValueError, TypeError):
            return []

    def _parse_ctemp_data(self, data):
        """
        解析ctemp数据，提取数值列表

        Args:
            data: 原始数据（可能是字符串、列表、字典或其他格式）

        Returns:
            List[float]: 解析后的数值列表
        """
        if data is None:
            return []

        if isinstance(data, dict):
            # 如果是字典，尝试提取数值
            values = []
            for key, value in data.items():
                try:
                    if isinstance(value, (int, float)):
                        values.append(float(value))
                    elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
                        values.append(float(value))
                    elif isinstance(value, (list, tuple)):
                        # 递归处理嵌套列表
                        sub_values = self._parse_ctemp_data(value)
                        values.extend(sub_values)
                except (ValueError, TypeError):
                    continue
            return values

        if isinstance(data, (list, tuple)):
            # 如果已经是列表，递归处理每个元素
            values = []
            for item in data:
                try:
                    if isinstance(item, dict):
                        # 递归处理字典元素
                        sub_values = self._parse_ctemp_data(item)
                        values.extend(sub_values)
                    elif isinstance(item, (int, float)):
                        values.append(float(item))
                    elif isinstance(item, str):
                        values.append(float(item))
                    elif item is not None:
                        values.append(float(item))
                    else:
                        values.append(0.0)
                except (ValueError, TypeError):
                    values.append(0.0)
            return values

        if isinstance(data, str):
            # 如果是字符串，尝试解析
            try:
                # 移除方括号和多余空格，按逗号分割
                cleaned = data.strip('[]').replace(' ', '')
                if cleaned:
                    values = [float(x.strip()) for x in cleaned.split(',') if x.strip()]
                    return values
            except (ValueError, AttributeError):
                pass

        # 如果是单个数值
        try:
            return [float(data)]
        except (ValueError, TypeError):
            return []

    def _load_values(self):
        try:
            opts = ExifParseOptions(
                selected_fields=self._fields,
                recursive=False,
                build_raw_flat=False,
                compute_available=False,
                debug_log_keys=False,
            )
            # 复用服务的单文件解析
            # 为兼容：如果服务未暴露 parse_file，则退回内部调用
            if hasattr(self._parser, 'parse_file'):
                values = self._parser.parse_file(self._image_path, opts)  # type: ignore
            else:
                # 兼容路径：直接读取raw并用定位索引
                from core.services.exif_processing.exif_parser_service import _get_by_flat_key, _flatten_items
                raw = self._parser._read_raw_exif(self._image_path)  # type: ignore
                values = {}
                for k in self._fields:
                    v = _get_by_flat_key(raw, k)
                    if v is None:
                        for fk, fv in _flatten_items(raw):
                            if fk == k:
                                v = fv
                                break
                    if v is not None:
                        values[k] = v
            self._values = values or {}
            # 渲染到网格
            row = 0
            skip_fields = set()  # 用于跳过已经合并显示的字段

            # 定义成对字段的映射关系
            paired_fields = {
                'ealgo_data_SGW_gray_RpG': ('ealgo_data_SGW_gray_BpG', 'ealgo_data_SGW_gray'),
                'ealgo_data_AGW_gray_RpG': ('ealgo_data_AGW_gray_BpG', 'ealgo_data_AGW_gray'),
                'ealgo_data_Mix_csalgo_RpG': ('ealgo_data_Mix_csalgo_BpG', 'ealgo_data_Mix_csalgo'),
                'ealgo_data_After_face_RpG': ('ealgo_data_After_face_BpG', 'ealgo_data_After_face'),
                'ealgo_data_cnvgEst_RpG': ('ealgo_data_cnvgEst_BpG', 'ealgo_data_cnvgEst'),
                'meta_data_gslGain_rgain': ('meta_data_gslGain_bgain', 'meta_data_gslGain'),
                'ctemp_weight_Ctemp_count': ('ctemp_weight_Ctemp_weight', 'ctemp_weight'),
            }

            # 定义三字段组合的映射关系（用于offset_map相关字段）
            triple_fields = {
                'offset_map': ('map_weight_offsetMapWeight', 'dummy', 'offset_map_data'),
            }

            for key in self._fields:
                # 跳过已经合并显示的字段
                if key in skip_fields:
                    continue

                # 处理三字段组合显示（offset_map相关）
                if key in triple_fields:
                    second_field, third_field, display_name = triple_fields[key]
                    first_val = self._values.get(key)  # offset_map字典数据
                    second_val = self._values.get(second_field)  # map_weight_offsetMapWeight数据

                    if first_val is not None and second_val is not None:
                        # 为offset_map三字段创建特殊的两列显示
                        row = self._create_offset_map_triple_display(first_val, second_val, None, row)
                        skip_fields.add(second_field)  # 标记跳过第二个字段
                        continue

                # 处理成对字段合并显示
                if key in paired_fields:
                    pair_field, display_name = paired_fields[key]
                    first_val = self._values.get(key)
                    second_val = self._values.get(pair_field)

                    if first_val is not None and second_val is not None:
                        # 特殊处理Ctemp权重字段
                        if key == 'ctemp_weight_Ctemp_count':
                            # 为ctemp_weight字段创建特殊的两列显示
                            row = self._create_ctemp_weight_display(first_val, second_val, row)
                        else:
                            # 常规成对字段处理 - 两列布局
                            name_lbl = QLabel(display_name)
                            name_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                            name_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px;")

                            # 格式化两个值显示在第二列
                            first_formatted = self._fmt(first_val, key)
                            second_formatted = self._fmt(second_val, pair_field)
                            combined_val = f"{first_formatted}，{second_formatted}"
                            val_lbl = QLabel(combined_val)
                            val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                            val_lbl.setWordWrap(True)
                            val_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px;")

                            self._grid.addWidget(name_lbl, row, 0)
                            self._grid.addWidget(val_lbl, row, 1)
                            row += 1
                        skip_fields.add(pair_field)  # 标记跳过配对字段
                        continue
                    else:
                        # 如果其中一个值为空，则按原来的方式单独显示
                        pass

                # 常规字段处理 - 两列布局
                name_lbl = QLabel(key)
                name_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                name_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px;")

                val = self._fmt(self._values.get(key), key)  # 传递字段名
                val_lbl = QLabel(val)
                val_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
                val_lbl.setWordWrap(True)
                val_lbl.setStyleSheet("border: 1px solid #CCCCCC; padding: 4px;")

                self._grid.addWidget(name_lbl, row, 0)
                self._grid.addWidget(val_lbl, row, 1)
                row += 1
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解析图片失败: {e}")
            self.reject()

