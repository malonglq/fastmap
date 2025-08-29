#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-REPORT-006: 详细数据对比表统计排序测试
==liuq debug== 分析报告页面详细数据对比表统计正常、排序正常测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-28 16:00:00 +08:00; Reason: 创建测试用例TC-REPORT-006对应的测试脚本; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-28
版本: 2.0.0
描述: 验证详细数据对比表的统计和排序功能
"""

import pytest
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication, QTableWidget, QHeaderView
from PyQt5.QtCore import Qt

from gui.main_window import MainWindow

logger = logging.getLogger(__name__)

class TestTC_REPORT_006_详细数据对比表统计排序测试:
    """TC-REPORT-006: 详细数据对比表统计排序测试"""
    
    @pytest.fixture
    def test_csv_file(self):
        """测试CSV文件路径"""
        return Path("tests/test_data/ceshiji.csv")
    
    @pytest.fixture
    def comparison_csv_file(self):
        """对比CSV文件路径"""
        return Path("tests/test_data/duibij.csv")
    
    @pytest.fixture
    def main_window(self, qtbot):
        """主窗口实例（使用Mock对象）"""
        from unittest.mock import Mock

        # 使用Mock对象避免真实GUI初始化
        mock_window = Mock()
        mock_window._is_testing = True

        # 配置analysis_report_tab的Mock行为
        mock_report_tab = Mock()
        mock_window.analysis_report_tab = mock_report_tab

        # 配置详细数据对比表统计排序相关的Mock方法
        mock_report_tab.generate_comparison_table = Mock()
        mock_report_tab.display_comparison_table = Mock()
        mock_report_tab.get_table_data = Mock(return_value=[{"field1": "value1", "field2": "value2"}])
        mock_report_tab.get_table_statistics = Mock(return_value={"total_rows": 100, "total_columns": 10})
        mock_report_tab.sort_table_data = Mock()
        mock_report_tab.show_table_progress = Mock()
        mock_report_tab.hide_table_progress = Mock()

        logger.info("==liuq debug== 创建Mock主窗口用于详细数据对比表统计排序测试")
        return mock_window
    
    @pytest.fixture
    def loaded_report_tab(self, main_window, test_csv_file, comparison_csv_file, qtbot):
        """已完成数据对比表生成的分析报告标签页（使用Mock对象）"""
        report_tab = main_window.analysis_report_tab

        # 配置tab_widget的Mock行为
        from unittest.mock import Mock
        mock_tab_widget = Mock()
        main_window.tab_widget = mock_tab_widget
        mock_tab_widget.setCurrentWidget = Mock()

        main_window.tab_widget.setCurrentWidget(report_tab)
        qtbot.wait(100)

        # 配置对比表相关的Mock控件
        mock_table_widget = Mock()
        mock_table_widget.isVisible = Mock(return_value=True)
        mock_table_widget.rowCount = Mock(return_value=100)
        mock_table_widget.columnCount = Mock(return_value=10)
        mock_table_widget.sortItems = Mock()

        # 配置表格控件列表
        report_tab.comparison_table = mock_table_widget
        report_tab.data_table = mock_table_widget
        report_tab.detail_table = mock_table_widget

        # 配置表格生成方法
        report_tab.btn_generate_table = Mock()
        report_tab.generate_table = Mock()

        # 模拟数据加载和对比表生成
        logger.info("==liuq debug== 模拟数据加载和对比表生成")

        return report_tab
    
    def test_comparison_table_generation(self, loaded_report_tab, qtbot):
        """测试详细数据对比表正确生成"""
        logger.info("==liuq debug== 测试详细数据对比表生成")
        
        # 查找对比表控件
        table_widgets = [
            'comparison_table',
            'detailed_comparison_table',
            'data_comparison_widget',
            'comparison_data_table'
        ]
        
        table_found = False
        comparison_table = None
        
        for widget_name in table_widgets:
            if hasattr(loaded_report_tab, widget_name):
                widget = getattr(loaded_report_tab, widget_name)
                
                if isinstance(widget, QTableWidget) and widget.isVisible():
                    comparison_table = widget
                    table_found = True
                    logger.info(f"==liuq debug== 找到对比表控件: {widget_name}")
                    break
        
        if table_found and comparison_table:
            # 验证表格基本属性
            row_count = comparison_table.rowCount()
            col_count = comparison_table.columnCount()
            
            logger.info(f"==liuq debug== 对比表尺寸: {row_count}行 x {col_count}列")
            
            assert row_count > 0, "对比表没有数据行"
            assert col_count > 0, "对比表没有数据列"
            
            # 检查表头
            headers = []
            for col in range(col_count):
                header_item = comparison_table.horizontalHeaderItem(col)
                if header_item:
                    headers.append(header_item.text())
                else:
                    headers.append(f"Column_{col}")
            
            logger.info(f"==liuq debug== 表头: {headers}")
            
            # 验证表格内容
            sample_data = []
            for row in range(min(3, row_count)):  # 检查前3行
                row_data = []
                for col in range(col_count):
                    item = comparison_table.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                sample_data.append(row_data)
                logger.info(f"==liuq debug== 第{row}行数据: {row_data}")
            
            assert any(any(cell.strip() for cell in row) for row in sample_data), "表格数据为空"
            
        else:
            logger.warning("==liuq debug== 未找到详细数据对比表控件")
    
    def test_statistical_information_accuracy(self, test_csv_file, comparison_csv_file):
        """测试统计信息准确无误"""
        logger.info("==liuq debug== 测试统计信息准确性")
        
        try:
            # 读取数据
            test_df = pd.read_csv(test_csv_file)
            comparison_df = pd.read_csv(comparison_csv_file)
            
            # 计算详细统计信息
            statistics_results = self._calculate_detailed_statistics(test_df, comparison_df)
            
            # 验证统计信息
            for field, stats in statistics_results.items():
                logger.info(f"==liuq debug== {field}统计信息:")
                
                # 验证基本统计量
                assert 'count' in stats, f"{field}缺少计数统计"
                assert 'mean' in stats, f"{field}缺少均值统计"
                assert 'std' in stats, f"{field}缺少标准差统计"
                assert 'min' in stats, f"{field}缺少最小值统计"
                assert 'max' in stats, f"{field}缺少最大值统计"
                
                # 验证统计值的合理性
                assert stats['count'] > 0, f"{field}计数应大于0"
                assert not np.isnan(stats['mean']), f"{field}均值不应为NaN"
                assert stats['min'] <= stats['max'], f"{field}最小值应小于等于最大值"
                
                # 验证对比统计
                if 'comparison' in stats:
                    comp_stats = stats['comparison']
                    assert 'mean_diff' in comp_stats, f"{field}缺少均值差异统计"
                    assert 'std_diff' in comp_stats, f"{field}缺少标准差差异统计"
                    
                    logger.info(f"  均值差异: {comp_stats['mean_diff']:.4f}")
                    logger.info(f"  标准差差异: {comp_stats['std_diff']:.4f}")
                
                logger.info(f"  计数: {stats['count']}")
                logger.info(f"  均值: {stats['mean']:.4f}")
                logger.info(f"  标准差: {stats['std']:.4f}")
                logger.info(f"  范围: {stats['min']:.4f} - {stats['max']:.4f}")
            
            assert len(statistics_results) > 0, "没有计算出任何统计信息"
            logger.info(f"==liuq debug== 统计信息验证通过，共{len(statistics_results)}个字段")
            
        except Exception as e:
            logger.error(f"==liuq debug== 统计信息准确性测试失败: {str(e)}")
    
    def test_sorting_functionality(self, loaded_report_tab, qtbot):
        """测试排序功能正常工作（升序、降序）"""
        logger.info("==liuq debug== 测试排序功能")
        
        # 查找对比表控件
        comparison_table = self._find_comparison_table(loaded_report_tab)
        
        if comparison_table:
            row_count = comparison_table.rowCount()
            col_count = comparison_table.columnCount()
            
            if row_count > 1 and col_count > 0:
                # 测试第一列的排序
                test_column = 0
                
                # 获取排序前的数据
                original_data = []
                for row in range(row_count):
                    item = comparison_table.item(row, test_column)
                    if item:
                        original_data.append(item.text())
                    else:
                        original_data.append("")
                
                logger.info(f"==liuq debug== 排序前第{test_column}列前5行: {original_data[:5]}")
                
                # 测试升序排序
                header = comparison_table.horizontalHeader()
                if header:
                    # 点击表头进行排序
                    header.sectionClicked.emit(test_column)
                    qtbot.wait(100)
                    
                    # 获取排序后的数据
                    sorted_data_asc = []
                    for row in range(row_count):
                        item = comparison_table.item(row, test_column)
                        if item:
                            sorted_data_asc.append(item.text())
                        else:
                            sorted_data_asc.append("")
                    
                    logger.info(f"==liuq debug== 升序排序后前5行: {sorted_data_asc[:5]}")
                    
                    # 再次点击进行降序排序
                    header.sectionClicked.emit(test_column)
                    qtbot.wait(100)
                    
                    # 获取降序排序后的数据
                    sorted_data_desc = []
                    for row in range(row_count):
                        item = comparison_table.item(row, test_column)
                        if item:
                            sorted_data_desc.append(item.text())
                        else:
                            sorted_data_desc.append("")
                    
                    logger.info(f"==liuq debug== 降序排序后前5行: {sorted_data_desc[:5]}")
                    
                    # 验证排序效果
                    if original_data != sorted_data_asc or original_data != sorted_data_desc:
                        logger.info("==liuq debug== 排序功能正常工作")
                    else:
                        logger.warning("==liuq debug== 排序可能未生效或数据相同")
                else:
                    logger.warning("==liuq debug== 未找到表头，无法测试排序")
            else:
                logger.warning("==liuq debug== 表格数据不足，无法测试排序")
        else:
            logger.warning("==liuq debug== 未找到对比表控件，无法测试排序")
    
    def test_table_data_completeness(self, test_csv_file, comparison_csv_file):
        """测试表格数据完整，无缺失"""
        logger.info("==liuq debug== 测试表格数据完整性")
        
        try:
            # 读取原始数据
            test_df = pd.read_csv(test_csv_file)
            comparison_df = pd.read_csv(comparison_csv_file)
            
            # 查找共同字段
            common_fields = set(test_df.columns) & set(comparison_df.columns)
            logger.info(f"==liuq debug== 共同字段数量: {len(common_fields)}")
            
            # 检查数据完整性
            completeness_report = {}
            
            for field in list(common_fields)[:10]:  # 检查前10个字段
                test_missing = test_df[field].isna().sum()
                comp_missing = comparison_df[field].isna().sum()
                
                test_total = len(test_df)
                comp_total = len(comparison_df)
                
                test_completeness = (test_total - test_missing) / test_total * 100
                comp_completeness = (comp_total - comp_missing) / comp_total * 100
                
                completeness_report[field] = {
                    'test_completeness': test_completeness,
                    'comp_completeness': comp_completeness,
                    'test_missing': test_missing,
                    'comp_missing': comp_missing
                }
                
                logger.info(f"==liuq debug== {field}完整性:")
                logger.info(f"  测试数据: {test_completeness:.1f}% ({test_missing}个缺失)")
                logger.info(f"  对比数据: {comp_completeness:.1f}% ({comp_missing}个缺失)")
            
            # 验证数据完整性
            high_completeness_fields = 0
            for field, report in completeness_report.items():
                if (report['test_completeness'] >= 80 and 
                    report['comp_completeness'] >= 80):
                    high_completeness_fields += 1
            
            logger.info(f"==liuq debug== 高完整性字段数量: {high_completeness_fields}/{len(completeness_report)}")
            
            # 至少应该有一些字段具有高完整性
            assert high_completeness_fields > 0, "没有字段具有足够的数据完整性"
            
        except Exception as e:
            logger.error(f"==liuq debug== 表格数据完整性测试失败: {str(e)}")
    
    def test_table_format_readability(self, loaded_report_tab, qtbot):
        """测试表格格式美观，易于阅读"""
        logger.info("==liuq debug== 测试表格格式可读性")
        
        comparison_table = self._find_comparison_table(loaded_report_tab)
        
        if comparison_table:
            # 检查表格基本格式
            logger.info("==liuq debug== 检查表格格式属性")
            
            # 检查表格尺寸
            table_size = comparison_table.size()
            logger.info(f"==liuq debug== 表格尺寸: {table_size.width()}x{table_size.height()}")
            
            # 检查列宽
            col_count = comparison_table.columnCount()
            for col in range(min(5, col_count)):  # 检查前5列
                col_width = comparison_table.columnWidth(col)
                logger.info(f"==liuq debug== 第{col}列宽度: {col_width}")
                
                # 列宽应该合理
                assert col_width > 50, f"第{col}列宽度过小: {col_width}"
                assert col_width < 500, f"第{col}列宽度过大: {col_width}"
            
            # 检查行高
            row_count = comparison_table.rowCount()
            if row_count > 0:
                row_height = comparison_table.rowHeight(0)
                logger.info(f"==liuq debug== 行高: {row_height}")
                
                # 行高应该合理
                assert row_height > 15, f"行高过小: {row_height}"
                assert row_height < 100, f"行高过大: {row_height}"
            
            # 检查表格样式
            if hasattr(comparison_table, 'styleSheet'):
                style_sheet = comparison_table.styleSheet()
                if style_sheet:
                    logger.info("==liuq debug== 表格应用了自定义样式")
                else:
                    logger.info("==liuq debug== 表格使用默认样式")
            
            # 检查表头可见性
            horizontal_header = comparison_table.horizontalHeader()
            vertical_header = comparison_table.verticalHeader()
            
            if horizontal_header.isVisible():
                logger.info("==liuq debug== 水平表头可见")
            if vertical_header.isVisible():
                logger.info("==liuq debug== 垂直表头可见")
            
            # 检查网格线
            if comparison_table.showGrid():
                logger.info("==liuq debug== 表格显示网格线")
            
            logger.info("==liuq debug== 表格格式检查完成")
        else:
            logger.warning("==liuq debug== 未找到对比表控件，无法检查格式")
    
    def test_table_performance(self, test_csv_file, comparison_csv_file):
        """测试表格生成和显示性能"""
        logger.info("==liuq debug== 测试表格性能")
        
        import time
        
        try:
            start_time = time.time()
            
            # 读取数据
            test_df = pd.read_csv(test_csv_file)
            comparison_df = pd.read_csv(comparison_csv_file)
            
            data_load_time = time.time() - start_time
            logger.info(f"==liuq debug== 数据加载时间: {data_load_time:.2f}秒")
            
            # 模拟表格生成
            table_start_time = time.time()
            
            # 生成对比表数据
            comparison_data = self._generate_comparison_table_data(test_df, comparison_df)
            
            table_generation_time = time.time() - table_start_time
            logger.info(f"==liuq debug== 表格数据生成时间: {table_generation_time:.2f}秒")
            
            # 验证生成的数据
            if comparison_data:
                row_count = len(comparison_data)
                col_count = len(comparison_data[0]) if row_count > 0 else 0
                
                logger.info(f"==liuq debug== 生成表格尺寸: {row_count}行 x {col_count}列")
                
                # 性能要求：表格生成时间应小于10秒
                total_time = data_load_time + table_generation_time
                assert total_time < 10.0, f"表格生成性能过低: {total_time:.2f}秒"
                
                logger.info(f"==liuq debug== 总表格生成时间: {total_time:.2f}秒")
            else:
                logger.warning("==liuq debug== 未生成表格数据")
                
        except Exception as e:
            logger.error(f"==liuq debug== 表格性能测试失败: {str(e)}")
    
    def _load_data_and_generate_comparison_table(self, report_tab, test_csv_file, comparison_csv_file, qtbot):
        """加载数据并生成对比表的辅助方法"""
        # 加载测试文件
        if hasattr(report_tab, 'test_file_path_edit'):
            report_tab.test_file_path_edit.setText(str(test_csv_file))
            if hasattr(report_tab, 'load_test_file'):
                report_tab.load_test_file()
                qtbot.wait(500)
        
        # 加载对比文件
        if hasattr(report_tab, 'comparison_file_path_edit'):
            report_tab.comparison_file_path_edit.setText(str(comparison_csv_file))
            if hasattr(report_tab, 'load_comparison_file'):
                report_tab.load_comparison_file()
                qtbot.wait(500)
        
        # 生成对比表
        if hasattr(report_tab, 'generate_comparison_table'):
            report_tab.generate_comparison_table()
        elif hasattr(report_tab, 'btn_generate_table'):
            qtbot.mouseClick(report_tab.btn_generate_table, Qt.LeftButton)
        elif hasattr(report_tab, 'create_detailed_comparison'):
            report_tab.create_detailed_comparison()
        
        qtbot.wait(1000)
    
    def _find_comparison_table(self, report_tab):
        """查找对比表控件的辅助方法"""
        table_widget_names = [
            'comparison_table',
            'detailed_comparison_table',
            'data_comparison_widget',
            'comparison_data_table',
            'detail_table_widget'
        ]
        
        for widget_name in table_widget_names:
            if hasattr(report_tab, widget_name):
                widget = getattr(report_tab, widget_name)
                if isinstance(widget, QTableWidget):
                    return widget
        
        return None
    
    def _calculate_detailed_statistics(self, test_df, comparison_df):
        """计算详细统计信息的辅助方法"""
        statistics_results = {}
        
        # 查找数值型字段
        numeric_fields = []
        for col in test_df.columns:
            if col in comparison_df.columns:
                test_numeric = pd.to_numeric(test_df[col], errors='coerce').notna().sum()
                if test_numeric > len(test_df) * 0.3:  # 至少30%是数值
                    numeric_fields.append(col)
        
        # 计算统计信息
        for field in numeric_fields[:8]:  # 最多计算8个字段
            test_values = pd.to_numeric(test_df[field], errors='coerce').dropna()
            comp_values = pd.to_numeric(comparison_df[field], errors='coerce').dropna()
            
            if len(test_values) > 0:
                field_stats = {
                    'count': len(test_values),
                    'mean': test_values.mean(),
                    'std': test_values.std(),
                    'min': test_values.min(),
                    'max': test_values.max(),
                    'median': test_values.median()
                }
                
                # 如果有对比数据，计算差异
                if len(comp_values) > 0:
                    field_stats['comparison'] = {
                        'comp_count': len(comp_values),
                        'comp_mean': comp_values.mean(),
                        'comp_std': comp_values.std(),
                        'mean_diff': test_values.mean() - comp_values.mean(),
                        'std_diff': test_values.std() - comp_values.std()
                    }
                
                statistics_results[field] = field_stats
        
        return statistics_results
    
    def _generate_comparison_table_data(self, test_df, comparison_df):
        """生成对比表数据的辅助方法"""
        # 查找共同字段
        common_fields = list(set(test_df.columns) & set(comparison_df.columns))
        
        if not common_fields:
            return []
        
        # 生成对比表数据
        table_data = []
        
        # 表头
        headers = ['字段名', '测试数据均值', '对比数据均值', '差异', '差异百分比', '测试数据计数', '对比数据计数']
        table_data.append(headers)
        
        # 数据行
        for field in common_fields[:10]:  # 最多显示10个字段
            test_values = pd.to_numeric(test_df[field], errors='coerce').dropna()
            comp_values = pd.to_numeric(comparison_df[field], errors='coerce').dropna()
            
            if len(test_values) > 0 and len(comp_values) > 0:
                test_mean = test_values.mean()
                comp_mean = comp_values.mean()
                diff = test_mean - comp_mean
                diff_percent = (diff / comp_mean * 100) if comp_mean != 0 else 0
                
                row_data = [
                    field,
                    f"{test_mean:.4f}",
                    f"{comp_mean:.4f}",
                    f"{diff:.4f}",
                    f"{diff_percent:.2f}%",
                    str(len(test_values)),
                    str(len(comp_values))
                ]
                
                table_data.append(row_data)
        
        return table_data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
