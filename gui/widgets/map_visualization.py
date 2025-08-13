#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map可视化组件
==liuq debug== FastMapV2 GUI Map可视化控件

{{CHENGQI:
Action: Added; Timestamp: 2025-07-25 18:00:00 +08:00; Reason: P1-LD-006 实现Map可视化组件; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-25
版本: 1.0.0
描述: 基于matplotlib的Map可视化控件，集成到PyQt界面
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QPushButton, QCheckBox, QGroupBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Polygon
import matplotlib.patches as mpatches
import numpy as np

from core.models.map_data import MapConfiguration, MapPoint, SceneType, MapType

logger = logging.getLogger(__name__)


class MapVisualizationWidget(QWidget):
    """
    Map可视化控件
    
    提供Map点分布的交互式可视化
    """
    
    # 自定义信号
    map_point_selected = pyqtSignal(object)  # 选中Map点时发出信号
    filter_changed = pyqtSignal()  # 筛选条件改变时发出信号
    
    def __init__(self, parent=None):
        """初始化可视化控件"""
        super().__init__(parent)
        
        self.configuration = None
        self.current_scene_filter = "all"
        self.current_type_filter = "all"
        self.show_weight_size = True
        
        self.setup_ui()
        self.setup_matplotlib()
        
        logger.info("==liuq debug== Map可视化控件初始化完成")
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 创建图表区域
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 设置布局比例
        layout.setStretchFactor(control_panel, 0)
        layout.setStretchFactor(self.canvas, 1)
    
    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QGroupBox("可视化控制")
        layout = QHBoxLayout(panel)
        
        # 场景筛选
        scene_label = QLabel("场景筛选:")
        self.scene_combo = QComboBox()
        self.scene_combo.addItems(["全部", "室内", "室外", "夜景"])
        self.scene_combo.currentTextChanged.connect(self.on_scene_filter_changed)
        
        # Map类型筛选
        type_label = QLabel("Map类型:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部", "强拉类型", "减小权重类型"])
        self.type_combo.currentTextChanged.connect(self.on_type_filter_changed)
        
        # 显示选项
        self.weight_size_checkbox = QCheckBox("权重大小显示")
        self.weight_size_checkbox.setChecked(True)
        self.weight_size_checkbox.toggled.connect(self.on_weight_size_toggled)
        
        self.grid_checkbox = QCheckBox("显示网格")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.toggled.connect(self.on_grid_toggled)
        
        # 操作按钮
        self.refresh_btn = QPushButton("刷新图表")
        self.refresh_btn.clicked.connect(self.refresh_plot)
        
        self.export_btn = QPushButton("导出图片")
        self.export_btn.clicked.connect(self.export_plot)
        
        # 添加到布局
        layout.addWidget(scene_label)
        layout.addWidget(self.scene_combo)
        layout.addWidget(type_label)
        layout.addWidget(self.type_combo)
        layout.addWidget(self.weight_size_checkbox)
        layout.addWidget(self.grid_checkbox)
        layout.addStretch()
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.export_btn)
        
        return panel
    
    def setup_matplotlib(self):
        """设置matplotlib"""
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建子图
        self.ax = self.figure.add_subplot(111)
        self.figure.tight_layout(pad=3.0)
        
        # 连接鼠标事件
        self.canvas.mpl_connect('button_press_event', self.on_plot_click)
        

    
    def set_configuration(self, configuration: MapConfiguration):
        """
        设置Map配置数据
        
        Args:
            configuration: Map配置对象
        """
        self.configuration = configuration
        self.refresh_plot()
        logger.info(f"==liuq debug== 设置Map配置，共 {len(configuration.map_points)} 个Map点")
    
    def get_filtered_map_points(self) -> List[MapPoint]:
        """获取筛选后的Map点"""
        if not self.configuration:
            return []
        
        points = self.configuration.map_points
        
        # 场景筛选
        if self.current_scene_filter != "all":
            scene_map = {
                "室内": SceneType.INDOOR,
                "室外": SceneType.OUTDOOR,
                "夜景": SceneType.NIGHT
            }
            if self.current_scene_filter in scene_map:
                points = [p for p in points if p.scene_type == scene_map[self.current_scene_filter]]
        
        # 类型筛选
        if self.current_type_filter != "all":
            type_map = {
                "强拉类型": MapType.ENHANCE,
                "减小权重类型": MapType.REDUCE
            }
            if self.current_type_filter in type_map:
                points = [p for p in points if p.map_type == type_map[self.current_type_filter]]
        
        return points
    
    def refresh_plot(self):
        """刷新图表"""
        try:
            self.ax.clear()
            
            if not self.configuration:
                self.ax.text(0.5, 0.5, '请加载Map配置文件', 
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.ax.transAxes, fontsize=14)
                self.canvas.draw()
                return
            
            # 获取筛选后的数据
            filtered_points = self.get_filtered_map_points()
            
            if not filtered_points:
                self.ax.text(0.5, 0.5, '没有符合筛选条件的Map点', 
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.ax.transAxes, fontsize=12)
                self.canvas.draw()
                return
            
            # 绘制散点图
            self.plot_scatter(filtered_points)
            
            # 设置图表属性
            self.setup_plot_properties()
            
            self.canvas.draw()

            
        except Exception as e:
            logger.error(f"==liuq debug== 刷新图表失败: {e}")
            self.ax.text(0.5, 0.5, f'图表绘制错误: {e}', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=self.ax.transAxes, fontsize=10, color='red')
            self.canvas.draw()
    
    def plot_scatter(self, map_points: List[MapPoint]):
        """绘制散点图和多边形"""
        # 按场景类型分组
        scene_groups = {
            SceneType.INDOOR: [],
            SceneType.OUTDOOR: [],
            SceneType.NIGHT: []
        }

        for point in map_points:
            scene_groups[point.scene_type].append(point)

        # 场景颜色映射
        scene_colors = {
            SceneType.INDOOR: '#FF6B6B',    # 红色 - 室内
            SceneType.OUTDOOR: '#4ECDC4',   # 青色 - 室外
            SceneType.NIGHT: '#45B7D1'      # 蓝色 - 夜景
        }

        scene_labels = {
            SceneType.INDOOR: '室内场景',
            SceneType.OUTDOOR: '室外场景',
            SceneType.NIGHT: '夜景场景'
        }

        # 用于图例的标记
        legend_elements = []

        # 绘制各场景的点和多边形
        for scene_type, points in scene_groups.items():
            if not points:
                continue

            base_color = scene_colors[scene_type]

            # 分离多边形和单点
            polygon_points = [p for p in points if p.is_polygon]
            single_points = [p for p in points if not p.is_polygon]

            # 绘制多边形
            if polygon_points:
                self._plot_polygons(polygon_points, base_color, scene_type)
                # 添加多边形图例
                polygon_patch = mpatches.Patch(
                    color=base_color, alpha=0.6,
                    label=f'{scene_labels[scene_type]} (多边形)'
                )
                legend_elements.append(polygon_patch)

            # 绘制单点
            if single_points:
                self._plot_single_points(single_points, base_color, scene_type)
                # 添加单点图例
                point_patch = mpatches.Patch(
                    color=base_color, alpha=1.0,
                    label=f'{scene_labels[scene_type]} (单点)'
                )
                legend_elements.append(point_patch)

        # 添加图例
        if legend_elements:
            self.ax.legend(handles=legend_elements, loc='upper right')

        # 添加标签显示
        self._add_labels(map_points)

    def _plot_polygons(self, polygon_points: List[MapPoint], base_color: str, scene_type: SceneType):
        """绘制多边形Map点"""
        for point in polygon_points:
            if not point.polygon_vertices:
                continue

            # 计算颜色强度（基于权重）
            alpha = min(0.8, max(0.3, point.weight))  # 权重越高，透明度越低（颜色越深）

            # 创建多边形
            polygon = Polygon(
                point.polygon_vertices,
                facecolor=base_color,
                edgecolor='black',
                alpha=alpha,
                linewidth=1.0,
                picker=True
            )

            # 存储点击信息
            polygon._map_point = point

            # 添加到图表
            self.ax.add_patch(polygon)

    def _plot_single_points(self, single_points: List[MapPoint], base_color: str, scene_type: SceneType):
        """绘制单点Map点"""
        if not single_points:
            return

        x_coords = [p.x for p in single_points]
        y_coords = [p.y for p in single_points]

        # 根据权重设置点的大小和颜色强度
        if self.show_weight_size:
            sizes = [max(20, p.weight * 200) for p in single_points]
        else:
            sizes = [50] * len(single_points)

        # 绘制散点
        scatter = self.ax.scatter(
            x_coords, y_coords,
            c=base_color,
            s=sizes,
            alpha=0.8,
            edgecolors='black',
            linewidth=0.5,
            picker=True
        )

        # 存储点击信息
        for i, point in enumerate(single_points):
            scatter._map_points = single_points

    def _add_labels(self, map_points: List[MapPoint]):
        """添加标签显示"""
        for point in map_points:
            # 只为权重较高的点显示标签，避免过于拥挤
            if point.weight > 0.8:
                # 显示权重信息
                label_text = f"{point.weight:.1f}"
                self.ax.annotate(
                    label_text,
                    xy=(point.x, point.y),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8,
                    alpha=0.7,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7)
                )

    def setup_plot_properties(self):
        """设置图表属性"""
        self.ax.set_xlabel('X坐标', fontsize=12)
        self.ax.set_ylabel('Y坐标', fontsize=12)
        self.ax.set_title('Map点分布图', fontsize=14, fontweight='bold')
        
        # 设置网格
        if self.grid_checkbox.isChecked():
            self.ax.grid(True, alpha=0.3)
        
        # 设置坐标轴范围
        if self.configuration and self.configuration.map_points:
            x_coords = [p.x for p in self.configuration.map_points]
            y_coords = [p.y for p in self.configuration.map_points]
            
            x_margin = (max(x_coords) - min(x_coords)) * 0.1
            y_margin = (max(y_coords) - min(y_coords)) * 0.1
            
            self.ax.set_xlim(min(x_coords) - x_margin, max(x_coords) + x_margin)
            self.ax.set_ylim(min(y_coords) - y_margin, max(y_coords) + y_margin)
        
        # 设置纵横比
        self.ax.set_aspect('equal', adjustable='box')
    
    def on_plot_click(self, event):
        """处理图表点击事件"""
        if event.inaxes != self.ax:
            return

        if not self.configuration:
            return

        click_x, click_y = event.xdata, event.ydata
        if click_x is None or click_y is None:
            return

        # 首先检查是否点击了多边形
        clicked_point = self._check_polygon_click(click_x, click_y)

        # 如果没有点击多边形，检查单点
        if not clicked_point:
            clicked_point = self._check_point_click(click_x, click_y)

        if clicked_point:
            self.map_point_selected.emit(clicked_point)


    def _check_polygon_click(self, click_x: float, click_y: float) -> Optional[MapPoint]:
        """检查是否点击了多边形"""
        for patch in self.ax.patches:
            if hasattr(patch, '_map_point') and isinstance(patch, Polygon):
                # 检查点是否在多边形内
                if patch.contains_point((click_x, click_y)):
                    return patch._map_point
        return None

    def _check_point_click(self, click_x: float, click_y: float) -> Optional[MapPoint]:
        """检查是否点击了单点"""
        min_distance = float('inf')
        closest_point = None
        threshold = 0.05  # 相对于坐标系的阈值

        filtered_points = self.get_filtered_map_points()
        for point in filtered_points:
            if not point.is_polygon:  # 只检查单点
                distance = ((point.x - click_x) ** 2 + (point.y - click_y) ** 2) ** 0.5
                if distance < min_distance and distance < threshold:
                    min_distance = distance
                    closest_point = point

        return closest_point
    
    def on_scene_filter_changed(self, text: str):
        """场景筛选改变"""
        filter_map = {
            "全部": "all",
            "室内": "室内",
            "室外": "室外", 
            "夜景": "夜景"
        }
        self.current_scene_filter = filter_map.get(text, "all")
        self.refresh_plot()
        self.filter_changed.emit()
    
    def on_type_filter_changed(self, text: str):
        """类型筛选改变"""
        filter_map = {
            "全部": "all",
            "强拉类型": "强拉类型",
            "减小权重类型": "减小权重类型"
        }
        self.current_type_filter = filter_map.get(text, "all")
        self.refresh_plot()
        self.filter_changed.emit()
    
    def on_weight_size_toggled(self, checked: bool):
        """权重大小显示切换"""
        self.show_weight_size = checked
        self.refresh_plot()
    
    def on_grid_toggled(self, checked: bool):
        """网格显示切换"""
        self.refresh_plot()
    
    def export_plot(self):
        """导出图片"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "导出图片", "map_visualization.png",
                "PNG files (*.png);;JPG files (*.jpg);;PDF files (*.pdf)"
            )
            
            if filename:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                logger.info(f"==liuq debug== 图片导出成功: {filename}")
                
        except Exception as e:
            logger.error(f"==liuq debug== 图片导出失败: {e}")
    
    def get_statistics_info(self) -> Dict[str, Any]:
        """获取当前显示的统计信息"""
        filtered_points = self.get_filtered_map_points()
        
        if not filtered_points:
            return {}
        
        # 场景统计
        scene_counts = {
            SceneType.INDOOR: 0,
            SceneType.OUTDOOR: 0,
            SceneType.NIGHT: 0
        }
        
        # 权重统计
        weights = []
        
        for point in filtered_points:
            scene_counts[point.scene_type] += 1
            weights.append(point.weight)
        
        return {
            'total_points': len(filtered_points),
            'scene_distribution': {
                'indoor': scene_counts[SceneType.INDOOR],
                'outdoor': scene_counts[SceneType.OUTDOOR],
                'night': scene_counts[SceneType.NIGHT]
            },
            'weight_stats': {
                'min': min(weights) if weights else 0,
                'max': max(weights) if weights else 0,
                'mean': sum(weights) / len(weights) if weights else 0
            },
            'current_filters': {
                'scene': self.current_scene_filter,
                'type': self.current_type_filter
            }
        }
