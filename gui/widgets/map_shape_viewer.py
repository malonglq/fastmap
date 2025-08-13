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

# 确保matplotlib使用正确的后端
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

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

            # 创建matplotlib图表
            self.figure = Figure(figsize=(5, 4), dpi=80, facecolor='white')
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setParent(self)

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
            # 创建一个简单的错误显示
            error_label = QLabel(f"初始化失败: {e}")
            error_label.setStyleSheet("color: red; padding: 10px;")
            layout = QVBoxLayout(self)
            layout.addWidget(error_label)
    
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

            # 更新信息标签
            self.update_base_boundary_info_label(base_boundary_point)



        except Exception as e:
            logger.error(f"==liuq debug== 显示base_boundary失败: {e}")
            self.show_error_state(str(e))

    def _redraw_all_layers(self):
        """重新绘制所有图层（支持叠加显示）"""
        try:
            # 清空图表
            self.ax.clear()

            # 设置固定坐标系（强制固定范围）
            self._setup_fixed_coordinate_system()

            # 绘制base_boundary0（底层）
            if self.current_base_boundary:
                self._draw_base_boundary_polygon(self.current_base_boundary)

            # 绘制当前选中的offset_map点（上层）
            if self.current_map_point:
                self._draw_offset_map_point(self.current_map_point)

            # 设置图表属性
            self._setup_fixed_plot_properties()

            # 更新画布
            self.canvas.draw_idle()
            self.canvas.flush_events()



        except Exception as e:
            logger.error(f"==liuq debug== 重绘所有图层失败: {e}")
            raise

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
        
        # 清空图表并显示错误信息
        self.ax.clear()
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

    
    def get_current_map_point(self) -> Optional[MapPoint]:
        """获取当前显示的Map点"""
        return self.current_map_point


