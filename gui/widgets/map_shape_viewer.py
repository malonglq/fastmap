#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map形状查看器组件

专门用于显示单个Map点的形状可视化

作者: AI Assistant
日期: 2025-01-25
"""

import logging
import os
import sys
from typing import Optional

# 强制使用 PyQt5 后端，避免与应用的 PyQt5 QApplication 混用 PyQt6
import os
os.environ.setdefault('QT_API', 'pyqt5')
import matplotlib
try:
    matplotlib.use('Qt5Agg')
except Exception:
    pass

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 标准光源白点与色温带（仅XML白点；等色温带使用锚点）
from utils.white_points import REFERENCE_INTERVALS, SEGMENT_BANDS, DEFAULT_BAND, load_white_points_from_xml, TEMPERATURE_ANCHORS

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
import numpy as np

# 配置matplotlib中文字体支持
def setup_chinese_font():
    """配置matplotlib中文字体"""
    try:
        # Windows系统字体路径
        if sys.platform.startswith('win'):
            font_paths = [
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simsun.ttc'
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    from matplotlib.font_manager import FontProperties
                    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
                    break
        else:
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']

        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['font.size'] = 10

    except Exception as e:
        print(f"==liuq debug== 字体配置失败: {e}")
        # 使用默认字体
        plt.rcParams['font.sans-serif'] = ['Arial']

# 初始化字体配置
setup_chinese_font()

from core.models.map_data import MapPoint

logger = logging.getLogger(__name__)

class MapShapeViewer(QWidget):
    """
    Map形状查看器

    支持固定坐标系和叠加显示的Map点可视化
    """

    def __init__(self, parent=None):
        """初始化形状查看器"""
        super().__init__(parent)

        self.current_map_point: Optional[MapPoint] = None
        self.current_base_boundary: Optional[MapPoint] = None  # 当前显示的base_boundary0
        # 色温带显示开关（默认显示）
        self.show_temperature_bands: bool = True
        # 可选：从XML加载的白点参考点 { '5000': (rpg,bpg), ... }
        self.xml_white_points: Optional[dict] = None
        # 运行期锚点（可由XML白点校准），默认拷贝 TEMPERATURE_ANCHORS
        self.runtime_anchors = dict(TEMPERATURE_ANCHORS)


        self.setup_ui()
        logger.info("==liuq debug== Map形状查看器初始化完成")

    def setup_ui(self):
        """设置用户界面"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)

            # 标题
            self.title_label = QLabel("Map形状可视化")
            self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
            self.title_label.setAlignment(Qt.AlignCenter)
            self.title_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc;")
            layout.addWidget(self.title_label)

            # 顶部右侧开关控制区
            top_bar = QHBoxLayout()
            top_bar.addStretch()
            self.temp_toggle = QCheckBox("显示色温带")
            self.temp_toggle.setChecked(True)
            self.temp_toggle.setToolTip("切换等色温带的显示/隐藏")
            self.temp_toggle.toggled.connect(self.on_temperature_toggle)
            top_bar.addWidget(self.temp_toggle)
            layout.addLayout(top_bar)

            # 创建matplotlib图表
            self.figure = Figure(figsize=(5, 4), dpi=80, facecolor='white')
            self.canvas = FigureCanvas(self.figure)
            # 设置canvas的最小尺寸
            self.canvas.setMinimumSize(200, 200)

            # 创建子图
            self.ax = self.figure.add_subplot(111)

            # 设置图表的紧凑布局
            self.figure.tight_layout(pad=1.0)

            layout.addWidget(self.canvas, 1)  # 给canvas更多空间

            # 信息标签
            self.info_label = QLabel("请在左侧表格中选择Map点")
            self.info_label.setAlignment(Qt.AlignCenter)
            self.info_label.setWordWrap(True)
            self.info_label.setStyleSheet("color: #666; padding: 8px; background-color: #f9f9f9; border: 1px solid #ddd;")
            self.info_label.setMaximumHeight(80)
            layout.addWidget(self.info_label)

            # 初始化空状态
            self.show_empty_state()

            logger.info("==liuq debug== Map形状查看器UI设置完成")

        except Exception as e:
            logger.error(f"==liuq debug== Map形状查看器UI设置失败: {e}")
            # 创建一个简单的错误显示（避免重复添加layout）
            try:
                if self.layout() is None:
                    lay = QVBoxLayout(self)
                else:
                    lay = self.layout()
                error_label = QLabel(f"初始化失败: {e}")
                error_label.setStyleSheet("color: red; padding: 10px;")
                lay.addWidget(error_label)
            except Exception:
                pass

    def show_map_point(self, map_point: MapPoint):
        """
        显示Map点形状（支持叠加显示）

        Args:
            map_point: Map点对象
        """
        try:
            self.current_map_point = map_point

            # 更新标题
            self.title_label.setText(f"Map形状: {map_point.alias_name}")

            # 重新绘制整个图表（包括base_boundary0和当前map_point）
            self._redraw_all_layers()

            # 更新信息标签
            self.update_info_label(map_point)



        except Exception as e:
            logger.error(f"==liuq debug== 显示Map形状失败: {e}")
            self.show_error_state(str(e))

    def show_base_boundary(self, base_boundary_point: MapPoint):
        """
        显示base_boundary0多边形（支持叠加显示）

        Args:
            base_boundary_point: base_boundary0的MapPoint对象
        """
        try:
            self.current_base_boundary = base_boundary_point

            # 更新标题
            self.title_label.setText("Base Boundary")

            # 重新绘制整个图表（包括base_boundary0和当前map_point）
            self._redraw_all_layers()
            # 强制立即生效，避免可见延迟
            try:
                self.force_immediate_redraw()
            except Exception:
                pass

            # 更新信息标签
            self.update_base_boundary_info_label(base_boundary_point)



        except Exception as e:
            logger.error(f"==liuq debug== 显示base_boundary失败: {e}")
            self.show_error_state(str(e))

    def _redraw_all_layers(self):
        """重新绘制所有图层（支持叠加显示）"""
        try:
            logger.info("==liuq debug== 重绘开始: show_temperature_bands=%s, has_base=%s, has_map=%s", self.show_temperature_bands, bool(self.current_base_boundary), bool(self.current_map_point))

            # 清空图表
            self.ax.clear()

            # 设置固定坐标系（强制固定范围）并固定比例与缩放
            self._setup_fixed_coordinate_system()
            try:
                self.ax.set_autoscale_on(False)
                self.ax.set_aspect('auto')
            except Exception:
                pass

            # 优先绘制等色温带（背景层）
            if self.show_temperature_bands:
                try:
                    self._draw_temperature_bands()
                except Exception as _e:
                    logger.warning(f"==liuq debug== 绘制等色温带失败: {_e}")
            else:
                logger.debug("==liuq debug== 色温带显示开关关闭，跳过绘制")

            # 绘制base_boundary0（底层之上）
            if self.current_base_boundary:
                self._draw_base_boundary_polygon(self.current_base_boundary)

            # 绘制当前选中的offset_map点（更上层）
            if self.current_map_point:
                self._draw_offset_map_point(self.current_map_point)

            # 设置图表属性
            self._setup_fixed_plot_properties()

            # 绘制XML白点（若已加载）
            try:
                self._draw_white_points()
            except Exception as _e2:
                logger.warning(f"==liuq debug== 绘制白点失败: {_e2}")

            # 更新画布（立即重绘，避免draw_idle导致的延迟）
            self.canvas.draw()
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()

        except Exception as e:
            logger.error(f"==liuq debug== 重绘所有图层失败: {e}")
            raise

    def force_immediate_redraw(self):
        """强制立即重绘并处理事件队列，消除可见延迟。"""
        try:
            self.canvas.draw()
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            logger.debug("==liuq debug== 已执行force_immediate_redraw()")
        except Exception as e:
            logger.warning(f"==liuq debug== force_immediate_redraw失败: {e}")

    def _setup_fixed_coordinate_system(self):
        """设置强制固定坐标系"""
        try:
            # 设置固定的坐标范围（强制固定，不允许改变）
            self.ax.set_xlim(0.0, 2.53)  # X轴固定范围
            self.ax.set_ylim(0.0, 1.7)   # Y轴固定范围

            # 禁用自动缩放
            self.ax.set_autoscale_on(False)

            # 设置坐标轴比例（不强制相等，保持固定范围）
            self.ax.set_aspect('auto')



        except Exception as e:
            logger.warning(f"==liuq debug== 设置固定坐标系失败: {e}")

    def _draw_base_boundary_polygon(self, base_boundary_point: MapPoint):
        """绘制base_boundary0多边形（底层）"""
        try:
            if not base_boundary_point.polygon_vertices:
                logger.warning("==liuq debug== base_boundary0没有多边形坐标")
                return

            # 创建多边形（最底层，z-index最低）
            from matplotlib.patches import Polygon
            polygon = Polygon(
                base_boundary_point.polygon_vertices,
                facecolor='lightgray',       # 浅灰色填充
                edgecolor='black',           # 黑色边框
                alpha=0.3,                   # 半透明
                linewidth=1.5,
                zorder=1                     # 最低层级
            )
            self.ax.add_patch(polygon)

            # 标记重心
            self.ax.plot(base_boundary_point.x, base_boundary_point.y, 'rs',
                        markersize=8, label='base_boundary0', zorder=2)



        except Exception as e:
            logger.warning(f"==liuq debug== 绘制base_boundary0多边形失败: {e}")

    def _draw_offset_map_point(self, map_point: MapPoint):
        """绘制offset_map点（上层）"""
        try:
            # 场景颜色映射
            from core.models.map_data import SceneType
            scene_colors = {
                SceneType.INDOOR: '#FF6B6B',    # 红色 - 室内
                SceneType.OUTDOOR: '#4ECDC4',   # 青色 - 室外
                SceneType.NIGHT: '#45B7D1'      # 蓝色 - 夜景
            }

            color = scene_colors.get(map_point.scene_type, '#666666')  # 默认灰色

            if map_point.is_polygon and map_point.polygon_vertices:
                # 绘制多边形
                from matplotlib.patches import Polygon
                polygon = Polygon(
                    map_point.polygon_vertices,
                    facecolor=color,
                    edgecolor='black',
                    alpha=0.7,
                    linewidth=2.0,
                    zorder=10                # 高层级，显示在base_boundary之上
                )
                self.ax.add_patch(polygon)

                # 标记重心
                self.ax.plot(map_point.x, map_point.y, 'ko', markersize=6,
                           label=f'{map_point.alias_name}重心', zorder=15)

                # 标记顶点
                vertices = np.array(map_point.polygon_vertices)
                self.ax.plot(vertices[:, 0], vertices[:, 1], 'ko', markersize=3, alpha=0.6, zorder=12)
            else:
                # 绘制单点
                self.ax.plot(map_point.x, map_point.y, 'o',
                           color=color, markersize=10,
                           markeredgecolor='black', markeredgewidth=1.5,
                           label=map_point.alias_name, zorder=10)



        except Exception as e:
            logger.warning(f"==liuq debug== 绘制offset_map点失败: {e}")

    def _setup_fixed_plot_properties(self):
        """设置固定图表属性"""
        try:
            # 设置标题
            title_parts = []
            if self.current_base_boundary:
                title_parts.append("base_boundary0")
            if self.current_map_point:
                title_parts.append(self.current_map_point.alias_name)

            title = " + ".join(title_parts) if title_parts else "Map可视化"
            self.ax.set_title(title, fontsize=11, fontweight='bold', pad=15)

            # 设置坐标轴标签
            self.ax.set_xlabel('R/G', fontsize=10)
            self.ax.set_ylabel('B/G', fontsize=10)

            # 添加网格
            self.ax.grid(True, alpha=0.3, zorder=0)  # 网格在最底层

            # 添加图例（如果有内容）
            if self.current_base_boundary or self.current_map_point:
                self.ax.legend(loc='upper right', fontsize=8)
        except Exception as e:
            logger.warning(f"==liuq debug== 设置固定图表属性失败: {e}")

    def on_temperature_toggle(self, checked: bool):
        """色温带显示切换回调"""
        try:
            self.show_temperature_bands = bool(checked)
            self._redraw_all_layers()
        except Exception as e:
            logger.warning(f"==liuq debug== 切换色温带显示失败: {e}")

    def set_xml_white_points(self, xml_path: Optional[str]):
        """外部设置白点XML，由主窗口在加载XML时调用。设置后立即重绘。"""
        try:
            if xml_path and os.path.exists(xml_path):
                from utils.white_points import load_white_points_from_xml
                pts = load_white_points_from_xml(xml_path)
                self.xml_white_points = pts if pts else None
                logger.info("==liuq debug== set_xml_white_points: 加载 %s 成功 cnt=%d", os.path.basename(xml_path), len(pts))
            else:
                self.xml_white_points = None
        except Exception as e:
            self.xml_white_points = None
            logger.warning(f"==liuq debug== set_xml_white_points失败: {e}")

            self.xml_white_points = None
            logger.warning(f"==liuq debug== set_xml_white_points失败: {e}")

        # 使用XML白点校准运行期锚点
        try:
            self._calibrate_runtime_anchors_with_xml()
        except Exception as _cal_e:
            logger.warning(f"==liuq debug== 运行期锚点校准失败: {_cal_e}")

        # 任务3：XML切换时立即重绘
        try:
            self._redraw_all_layers()
        except Exception as _e:
            logger.warning(f"==liuq debug== set_xml_white_points后重绘失败: {_e}")
    def _calibrate_runtime_anchors_with_xml(self):
        """若XML白点包含标准名（如'6500','5000','7500'），将其用于校准 D65/D50/D75。
        只在运行期更新 self.runtime_anchors，不修改全局常量。
        """
        try:
            if not getattr(self, 'xml_white_points', None):
                return
            # 每次以默认常量为基准再做校准
            self.runtime_anchors = dict(TEMPERATURE_ANCHORS)

            # 直接命名覆盖
            direct_map = {
                '6500': 'D65',
                '5000': 'D50',
                '7500': 'D75',
                '4000': 'F',      # 常见F附近
                '2850': 'A',      # A光近似
                '2300': 'H',      # H光近似
                '1500': '1500',   # 低端
                '9000': 'High',   # 高色温常见键
                '10000': 'High',  # 常见键
                '12000': 'High',  # 常见键
            }
            updated = []
            for xml_key, name in direct_map.items():
                if xml_key in self.xml_white_points:
                    self.runtime_anchors[name] = tuple(self.xml_white_points[xml_key])
                    updated.append(name)

            # 就近匹配（默认±300K，高低端适当放宽）
            fuzzy_targets = [
                (6500, 'D65', 300),
                (5000, 'D50', 300),
                (7500, 'D75', 300),
                (4000, 'F',   400),
                (2850, 'A',   400),
                (2300, 'H',   500),
                (1500, '1500', 500),
            ]
            for target, std_name, tol in fuzzy_targets:
                if std_name in updated:
                    continue
                try:
                    keys = [int(k) for k in self.xml_white_points.keys() if k.isdigit()]
                    if not keys:
                        continue
                    nearest = min(keys, key=lambda v: abs(v - target))
                    if abs(nearest - target) <= tol:
                        self.runtime_anchors[std_name] = tuple(self.xml_white_points[str(nearest)])
                        updated.append(std_name)
                except Exception:
                    continue
            # High 锚点兜底校准：优先选择XML中最高的 >=8000K 白点
            if 'High' not in updated:
                try:
                    keys = [int(k) for k in self.xml_white_points.keys() if isinstance(k, str) and k.isdigit()]
                    high_candidates = [v for v in keys if v >= 8000]
                    if high_candidates:
                        best = max(high_candidates)
                        self.runtime_anchors['High'] = tuple(self.xml_white_points[str(best)])
                        updated.append('High')
                        logger.info("==liuq debug== High锚点已用XML白点校准: %sK -> %s", best, str(self.runtime_anchors['High']))
                    else:
                        hx, hy = TEMPERATURE_ANCHORS['High']
                        logger.info("==liuq debug== High锚点未找到XML白点(>=8000K)，保持默认: (%.6f, %.6f)", hx, hy)
                except Exception as he:
                    logger.warning("==liuq debug== High锚点校准异常: %s", he)

            if updated:
                logger.info("==liuq debug== 已用XML白点校准锚点: %s", ','.join(updated))
        except Exception as e:
            logger.warning(f"==liuq debug== 锚点校准失败: {e}")

        except Exception as e:
            self.xml_white_points = None
            logger.warning(f"==liuq debug== set_xml_white_points失败: {e}")
        # 任务3：XML切换时立即重绘
        try:
            self._redraw_all_layers()
        except Exception as _e:
            logger.warning(f"==liuq debug== set_xml_white_points后重绘失败: {_e}")

    def _draw_white_points(self):
        """在坐标系中仅绘制来自XML的白点参考点与标签。
        若当前未加载或XML中无有效白点，则不绘制任何白点。
        """
        try:
            if not getattr(self, 'xml_white_points', None):
                return
            # XML 白点：键为数字字符串（如 '5000'），值为(rpg,bpg)
            items = []
            try:
                items = sorted(self.xml_white_points.items(), key=lambda kv: int(kv[0]), reverse=True)
            except Exception:
                items = list(self.xml_white_points.items())
            for ctemp_str, (x, y) in items:
                # 过滤无效坐标
                if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                    continue
                label = f"{ctemp_str}K"
                self.ax.plot(x, y, marker='+', color='red', markersize=8, markeredgewidth=2, zorder=50)
                self.ax.annotate(label, xy=(x, y), xytext=(5, 5), textcoords='offset points',
                                 fontsize=8, color='red', zorder=51,
                                 bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.6))
        except Exception as e:
            logger.warning(f"==liuq debug== 绘制白点参考点失败: {e}")

    def clear_current_selections(self):
        """清空当前选择"""
        self.current_map_point = None
        self.current_base_boundary = None
        self.show_empty_state()

    def draw_base_boundary(self, base_boundary):
        """绘制base_boundary边界"""
        try:
            rpg = base_boundary.rpg
            bpg = base_boundary.bpg

            # 绘制边界点
            self.ax.plot(rpg, bpg, 'rs', markersize=20, label='Base Boundary',
                        markerfacecolor='red', markeredgecolor='darkred', markeredgewidth=2)

            # 绘制边界框（假设以该点为中心的矩形区域）
            boundary_size = 0.1  # 边界框大小
            rect_x = [rpg - boundary_size, rpg + boundary_size, rpg + boundary_size, rpg - boundary_size, rpg - boundary_size]
            rect_y = [bpg - boundary_size, bpg - boundary_size, bpg + boundary_size, bpg + boundary_size, bpg - boundary_size]

            self.ax.plot(rect_x, rect_y, 'r--', linewidth=2, alpha=0.7, label='Boundary Area')

            # 添加文本标注
            self.ax.annotate(f'({rpg:.3f}, {bpg:.3f})',
                           xy=(rpg, bpg), xytext=(10, 10),
                           textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                           arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        except Exception as e:
            logger.error(f"==liuq debug== 绘制base_boundary失败: {e}")
            raise

    def setup_base_boundary_plot_properties(self, base_boundary):
        """设置base_boundary图表属性"""
        try:
            # 设置标题
            title_text = f"Base Boundary\nRpG: {base_boundary.rpg:.3f}, BpG: {base_boundary.bpg:.3f}"
            self.ax.set_title(title_text, fontsize=11, fontweight='bold', pad=15)

            # 设置坐标轴标签
            self.ax.set_xlabel('R/G', fontsize=10)
            self.ax.set_ylabel('B/G', fontsize=10)

            # 设置坐标轴范围（以base_boundary为中心）
            margin = 0.2
            self.ax.set_xlim(base_boundary.rpg - margin, base_boundary.rpg + margin)
            self.ax.set_ylim(base_boundary.bpg - margin, base_boundary.bpg + margin)

            # 添加网格
            self.ax.grid(True, alpha=0.3)

            # 添加图例
            self.ax.legend(loc='upper right', fontsize=9)

            # 设置坐标轴比例相等
            self.ax.set_aspect('equal', adjustable='box')

        except Exception as e:
            logger.error(f"==liuq debug== 设置base_boundary图表属性失败: {e}")
            raise

    def update_base_boundary_info_label(self, base_boundary_point: MapPoint):
        """更新base_boundary信息标签"""
        try:
            info_text = f"Base Boundary: {base_boundary_point.alias_name}"
            if base_boundary_point.polygon_vertices:
                info_text += f" (多边形，{len(base_boundary_point.polygon_vertices)}个顶点)"
            self.info_label.setText(info_text)
        except Exception as e:
            logger.warning(f"==liuq debug== 更新base_boundary信息标签失败: {e}")

    def draw_polygon(self, map_point: MapPoint):
        """绘制多边形"""
        try:
            # 创建多边形
            polygon = Polygon(
                map_point.polygon_vertices,
                facecolor='lightblue',
                edgecolor='navy',
                alpha=0.7,
                linewidth=2.0
            )
            self.ax.add_patch(polygon)

            # 标记重心
            self.ax.plot(map_point.x, map_point.y, 'ro', markersize=8, label='重心')

            # 标记顶点
            vertices = np.array(map_point.polygon_vertices)
            self.ax.plot(vertices[:, 0], vertices[:, 1], 'ko', markersize=4, alpha=0.6)

            # 设置坐标轴范围
            x_coords = vertices[:, 0]
            y_coords = vertices[:, 1]

            x_margin = (x_coords.max() - x_coords.min()) * 0.1 + 0.01
            y_margin = (y_coords.max() - y_coords.min()) * 0.1 + 0.01

            self.ax.set_xlim(x_coords.min() - x_margin, x_coords.max() + x_margin)
            self.ax.set_ylim(y_coords.min() - y_margin, y_coords.max() + y_margin)

        except Exception as e:
            logger.warning(f"==liuq debug== 绘制多边形失败: {e}")
            raise

    def draw_single_point(self, map_point: MapPoint):
        """绘制单点"""
        try:
            # 绘制单点
            self.ax.plot(map_point.x, map_point.y, 'bo', markersize=15, label='Map点')

            # 设置坐标轴范围
            margin = 0.1
            self.ax.set_xlim(map_point.x - margin, map_point.x + margin)
            self.ax.set_ylim(map_point.y - margin, map_point.y + margin)

        except Exception as e:
            logger.warning(f"==liuq debug== 绘制单点失败: {e}")
            raise

    def setup_plot_properties(self, map_point: MapPoint):
        """设置图表属性"""
        try:
            # 设置标题 - 使用英文避免字体问题
            title_text = f"{map_point.alias_name}\nWeight: {map_point.weight:.3f}"
            self.ax.set_title(title_text, fontsize=11, fontweight='bold', pad=15)

            # 设置坐标轴标签 - 使用英文
            self.ax.set_xlabel('X Coordinate', fontsize=9)
            self.ax.set_ylabel('Y Coordinate', fontsize=9)

            # 设置网格
            self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

            # 设置纵横比
            self.ax.set_aspect('equal', adjustable='box')

            # 添加图例
            if map_point.is_polygon:
                self.ax.legend(loc='upper right', fontsize=8, framealpha=0.8)

            # 设置坐标轴样式
            self.ax.tick_params(axis='both', which='major', labelsize=8)

            # 调整布局
            self.figure.tight_layout(pad=1.5)

        except Exception as e:
            logger.warning(f"==liuq debug== 设置图表属性失败: {e}")

    def update_info_label(self, map_point: MapPoint):
        """更新信息标签"""
        try:
            info_lines = []

            # 基本信息
            info_lines.append(f"名称: {map_point.alias_name}")
            info_lines.append(f"坐标模式: {map_point.get_coordinate_mode()}")
            info_lines.append(f"重心: ({map_point.x:.6f}, {map_point.y:.6f})")
            info_lines.append(f"权重: {map_point.weight:.3f}")

            # 多边形特有信息
            if map_point.is_polygon:
                info_lines.append(f"顶点数量: {len(map_point.polygon_vertices)}")

                # 计算面积（简单多边形）
                if len(map_point.polygon_vertices) >= 3:
                    vertices = np.array(map_point.polygon_vertices)
                    area = self.calculate_polygon_area(vertices)
                    info_lines.append(f"近似面积: {area:.6f}")

            # 参数范围
            bv_min, bv_max = map_point.bv_range
            if bv_min != 0 or bv_max != 0:
                info_lines.append(f"BV范围: {bv_min:.1f} ~ {bv_max:.1f}")

            self.info_label.setText("\n".join(info_lines))

        except Exception as e:
            logger.warning(f"==liuq debug== 更新信息标签失败: {e}")
            self.info_label.setText(f"信息显示错误: {e}")

    def calculate_polygon_area(self, vertices: np.ndarray) -> float:
        """计算多边形面积（使用鞋带公式）"""
        try:
            x = vertices[:, 0]
            y = vertices[:, 1]
            return 0.5 * abs(sum(x[i] * y[i+1] - x[i+1] * y[i]
                               for i in range(-1, len(x)-1)))
        except:
            return 0.0

    def show_empty_state(self):
        """显示空状态"""
        try:
            self.current_map_point = None
            self.title_label.setText("Map形状可视化")

            # 清空图表
            self.ax.clear()

            # 使用英文文本避免字体问题
            self.ax.text(0.5, 0.5, 'Please select a Map point\nfrom the left table',
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=12, color='gray',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))

            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_title('Map Shape Viewer', fontsize=14, pad=10)

            # 添加边框
            for spine in self.ax.spines.values():
                spine.set_visible(True)
                spine.set_color('lightgray')

            # 强制刷新canvas
            self.canvas.draw_idle()
            self.canvas.flush_events()

            self.info_label.setText("请在左侧表格中选择Map点")



        except Exception as e:
            logger.error(f"==liuq debug== 显示空状态失败: {e}")
            # 简单的错误处理
            try:
                self.ax.clear()
                self.ax.text(0.5, 0.5, f'Error: {str(e)}',
                            horizontalalignment='center', verticalalignment='center',
                            transform=self.ax.transAxes, fontsize=10, color='red')
                self.canvas.draw_idle()
            except:
                pass

    def show_error_state(self, error_message: str):
        """显示错误状态"""
        self.title_label.setText("Map形状可视化 - 错误")

        # 清空图表并显示错误信息（容错，避免在初始化失败时再次报错）
        try:
            if hasattr(self, 'ax') and hasattr(self, 'canvas'):
                self.ax.clear()
            else:
                # 若画布未初始化，尽量更新信息标签
                if hasattr(self, 'info_label'):
                    self.info_label.setText(f"错误: {error_message}")
        except Exception:
            pass
        self.ax.text(0.5, 0.5, f'显示错误:\n{error_message}',
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes, fontsize=12, color='red')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self.canvas.draw()

        self.info_label.setText(f"显示错误: {error_message}")

    def clear(self):
        """清空显示"""
        self.show_empty_state()


    def _draw_temperature_bands(self):
        """按从右上角圆点出发的扇形（楔形）方式绘制等色温段。
        逻辑：以坐标系右上角(Corner)为锚点，针对每个区间(a,b)，分别计算从Corner指向a、b两点的射线
        与坐标边界矩形的交点，使用 [Corner, P(a), P(b)] 三点构成楔形，着色为半透明色带。
        """
        try:
            # 颜色方案：依序使用从冷到暖的色调
            colors = ['#6FA8DC', '#76A5AF', '#93C47D', '#FFD966', '#F6B26B', '#E06666', '#CC0000']
            color_idx = 0

            # 获取坐标矩形范围
            xmin, xmax = self.ax.get_xlim()
            ymin, ymax = self.ax.get_ylim()
            corner_x, corner_y = xmax, ymax

            # 在右上角画一个小圆点作为锚点提示
            self.ax.plot(corner_x, corner_y, 'o', color='#333333', markersize=4, zorder=20)

            def ray_to_rect_intersection(x0, y0, x1, y1):
                """从(x0,y0)指向(x1,y1)的射线与矩形边界的交点（落在边界上且t>0）。"""
                dx, dy = x1 - x0, y1 - y0
                t_candidates = []
                eps = 1e-9
                if abs(dx) > eps:
                    t_to_xmin = (xmin - x0) / dx
                    t_to_xmax = (xmax - x0) / dx
                    # 射线向内，corner在右上，通常命中xmin
                    for t in (t_to_xmin, t_to_xmax):
                        if t > 0:
                            y_hit = y0 + t * dy
                            if ymin - eps <= y_hit <= ymax + eps:
                                t_candidates.append((t, xmin if t == t_to_xmin else xmax, y_hit))
                if abs(dy) > eps:
                    t_to_ymin = (ymin - y0) / dy
                    t_to_ymax = (ymax - y0) / dy
                    for t in (t_to_ymin, t_to_ymax):
                        if t > 0:
                            x_hit = x0 + t * dx
                            if xmin - eps <= x_hit <= xmax + eps:
                                t_candidates.append((t, x_hit, ymin if t == t_to_ymin else ymax))
                if not t_candidates:
                    return x1, y1
                # 选择最小正t（离corner最近的边界命中）
                t_candidates.sort(key=lambda v: v[0])
                _, ix, iy = t_candidates[0]
                return ix, iy

            for (a, b) in REFERENCE_INTERVALS:
                # 运行期锚点优先；若没有则回退到默认常量
                if a not in TEMPERATURE_ANCHORS or b not in TEMPERATURE_ANCHORS:
                    continue
                ax0, ay0 = self.runtime_anchors.get(a, TEMPERATURE_ANCHORS[a])
                bx0, by0 = self.runtime_anchors.get(b, TEMPERATURE_ANCHORS[b])

                # 计算两条射线与矩形的交点
                pa_x, pa_y = ray_to_rect_intersection(corner_x, corner_y, ax0, ay0)
                pb_x, pb_y = ray_to_rect_intersection(corner_x, corner_y, bx0, by0)

                poly_xy = np.array([
                    [corner_x, corner_y], [pa_x, pa_y], [pb_x, pb_y]
                ])

                patch = Polygon(poly_xy, closed=True,
                                facecolor=colors[color_idx % len(colors)],
                                edgecolor='none', alpha=0.22, zorder=3)
                self.ax.add_patch(patch)

                # 在楔形中部标注区间标签（沿着两射线的中间方向偏移）
                mid_x = (pa_x + pb_x) / 2.0
                mid_y = (pa_y + pb_y) / 2.0
                label_x = (corner_x * 0.35) + (mid_x * 0.65)
                label_y = (corner_y * 0.35) + (mid_y * 0.65)
                self.ax.text(label_x, label_y, f"{a}-{b}", fontsize=9, color='black',
                             ha='center', va='center', alpha=0.75,
                             bbox=dict(boxstyle='round,pad=0.15', facecolor='white', alpha=0.5), zorder=6)

                color_idx += 1
        except Exception as e:
            logger.warning(f"==liuq debug== 绘制色温带异常: {e}")


    def get_current_map_point(self) -> Optional[MapPoint]:
        """获取当前显示的Map点"""
        return self.current_map_point


