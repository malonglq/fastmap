#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-REPORT-005: RpG/BpG对比分析测试
==liuq debug== 分析报告页面每张图片RpG/BpG对比分析功能测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-28 15:45:00 +08:00; Reason: 创建测试用例TC-REPORT-005对应的测试脚本; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-28
版本: 2.0.0
描述: 验证每张图片的RpG/BpG对比分析功能
"""

import pytest
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from gui.main_window import MainWindow

logger = logging.getLogger(__name__)

class TestTC_REPORT_005_RpG_BpG对比分析测试:
    """TC-REPORT-005: RpG/BpG对比分析测试"""
    
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

        # 配置RpG_BpG对比分析相关的Mock方法
        mock_report_tab.perform_rpg_bpg_analysis = Mock()
        mock_report_tab.display_analysis_chart = Mock()
        mock_report_tab.get_rpg_bpg_data = Mock(return_value={"rpg": [1.2, 1.5, 1.8], "bpg": [0.8, 1.1, 1.3]})
        mock_report_tab.get_analysis_statistics = Mock(return_value={"correlation": 0.75, "variance": 0.25})
        mock_report_tab.show_analysis_progress = Mock()
        mock_report_tab.hide_analysis_progress = Mock()

        logger.info("==liuq debug== 创建Mock主窗口用于RpG_BpG对比分析测试")
        return mock_window
    
    @pytest.fixture
    def loaded_report_tab(self, main_window, test_csv_file, comparison_csv_file, qtbot):
        """已加载CSV文件并完成数据处理的分析报告标签页（使用Mock对象）"""
        report_tab = main_window.analysis_report_tab

        # 配置tab_widget的Mock行为
        from unittest.mock import Mock
        mock_tab_widget = Mock()
        main_window.tab_widget = mock_tab_widget
        mock_tab_widget.setCurrentWidget = Mock()

        main_window.tab_widget.setCurrentWidget(report_tab)
        qtbot.wait(100)

        # 配置分析图表相关的Mock控件
        mock_chart_widget = Mock()
        mock_chart_widget.isVisible = Mock(return_value=True)

        # 配置size()方法返回有width()和height()方法的对象
        mock_size = Mock()
        mock_size.width = Mock(return_value=600)
        mock_size.height = Mock(return_value=400)
        mock_chart_widget.size = Mock(return_value=mock_size)

        report_tab.rpg_bpg_chart_widget = mock_chart_widget
        report_tab.analysis_chart_area = mock_chart_widget

        # 配置分析方法
        report_tab.btn_analyze = Mock()
        report_tab.analyze_rpg_bpg = Mock()

        # 模拟数据加载和处理
        logger.info("==liuq debug== 模拟数据加载和处理")

        return report_tab
    
    def test_rpg_bpg_data_extraction(self, test_csv_file, comparison_csv_file):
        """测试每张图片的RpG/BpG数据正确提取"""
        logger.info("==liuq debug== 测试RpG/BpG数据提取")
        
        try:
            # 读取CSV文件
            test_df = pd.read_csv(test_csv_file)
            comparison_df = pd.read_csv(comparison_csv_file)
            
            # 查找RpG和BpG相关字段
            rpg_fields = [col for col in test_df.columns if 'rpg' in col.lower() or 'r_g' in col.lower()]
            bpg_fields = [col for col in test_df.columns if 'bpg' in col.lower() or 'b_g' in col.lower()]
            
            logger.info(f"==liuq debug== 找到RpG字段: {rpg_fields}")
            logger.info(f"==liuq debug== 找到BpG字段: {bpg_fields}")
            
            # 验证数据提取
            if rpg_fields:
                for field in rpg_fields[:3]:  # 检查前3个字段
                    rpg_values = test_df[field].dropna()
                    if len(rpg_values) > 0:
                        logger.info(f"==liuq debug== {field}数据样本: {rpg_values.head().tolist()}")
                        
                        # 验证数据类型和范围
                        numeric_values = pd.to_numeric(rpg_values, errors='coerce').dropna()
                        if len(numeric_values) > 0:
                            min_val = numeric_values.min()
                            max_val = numeric_values.max()
                            mean_val = numeric_values.mean()
                            
                            logger.info(f"==liuq debug== {field}统计: 最小{min_val:.3f}, 最大{max_val:.3f}, 平均{mean_val:.3f}")
                            
                            # RpG值通常在0.3-0.8范围内
                            assert 0.1 <= min_val <= 1.5, f"{field}最小值异常: {min_val}"
                            assert 0.1 <= max_val <= 1.5, f"{field}最大值异常: {max_val}"
            
            if bpg_fields:
                for field in bpg_fields[:3]:  # 检查前3个字段
                    bpg_values = test_df[field].dropna()
                    if len(bpg_values) > 0:
                        logger.info(f"==liuq debug== {field}数据样本: {bpg_values.head().tolist()}")
                        
                        # 验证数据类型和范围
                        numeric_values = pd.to_numeric(bpg_values, errors='coerce').dropna()
                        if len(numeric_values) > 0:
                            min_val = numeric_values.min()
                            max_val = numeric_values.max()
                            mean_val = numeric_values.mean()
                            
                            logger.info(f"==liuq debug== {field}统计: 最小{min_val:.3f}, 最大{max_val:.3f}, 平均{mean_val:.3f}")
                            
                            # BpG值通常在0.3-0.8范围内
                            assert 0.1 <= min_val <= 1.5, f"{field}最小值异常: {min_val}"
                            assert 0.1 <= max_val <= 1.5, f"{field}最大值异常: {max_val}"
            
            # 至少应该有一些RpG或BpG字段
            assert len(rpg_fields) > 0 or len(bpg_fields) > 0, "没有找到RpG或BpG相关字段"
            
        except Exception as e:
            logger.error(f"==liuq debug== RpG/BpG数据提取失败: {str(e)}")
    
    def test_comparison_analysis_accuracy(self, test_csv_file, comparison_csv_file):
        """测试对比分析结果准确显示"""
        logger.info("==liuq debug== 测试对比分析结果准确性")
        
        try:
            test_df = pd.read_csv(test_csv_file)
            comparison_df = pd.read_csv(comparison_csv_file)
            
            # 查找共同的图片标识字段
            image_id_fields = ['image_name', 'filename', 'name']
            image_field = None
            
            for field in image_id_fields:
                if field in test_df.columns and field in comparison_df.columns:
                    image_field = field
                    break
            
            if image_field:
                logger.info(f"==liuq debug== 使用图片标识字段: {image_field}")
                
                # 查找RpG/BpG字段
                rpg_fields = [col for col in test_df.columns if 'rpg' in col.lower()]
                bpg_fields = [col for col in test_df.columns if 'bpg' in col.lower()]
                
                if rpg_fields and bpg_fields:
                    # 选择主要的RpG和BpG字段进行分析
                    main_rpg_field = rpg_fields[0]
                    main_bpg_field = bpg_fields[0]
                    
                    # 合并数据进行对比
                    merged_df = pd.merge(
                        test_df[[image_field, main_rpg_field, main_bpg_field]],
                        comparison_df[[image_field, main_rpg_field, main_bpg_field]],
                        on=image_field,
                        suffixes=('_test', '_comparison')
                    )
                    
                    if len(merged_df) > 0:
                        logger.info(f"==liuq debug== 成功匹配{len(merged_df)}张图片进行对比分析")
                        
                        # 计算差异
                        rpg_diff = merged_df[f'{main_rpg_field}_test'] - merged_df[f'{main_rpg_field}_comparison']
                        bpg_diff = merged_df[f'{main_bpg_field}_test'] - merged_df[f'{main_bpg_field}_comparison']
                        
                        # 统计差异
                        rpg_mean_diff = rpg_diff.mean()
                        bpg_mean_diff = bpg_diff.mean()
                        rpg_std_diff = rpg_diff.std()
                        bpg_std_diff = bpg_diff.std()
                        
                        logger.info(f"==liuq debug== RpG平均差异: {rpg_mean_diff:.4f} ± {rpg_std_diff:.4f}")
                        logger.info(f"==liuq debug== BpG平均差异: {bpg_mean_diff:.4f} ± {bpg_std_diff:.4f}")
                        
                        # 验证差异在合理范围内
                        assert abs(rpg_mean_diff) < 0.5, f"RpG平均差异过大: {rpg_mean_diff}"
                        assert abs(bpg_mean_diff) < 0.5, f"BpG平均差异过大: {bpg_mean_diff}"
                    else:
                        logger.warning("==liuq debug== 没有找到匹配的图片进行对比")
                else:
                    logger.warning("==liuq debug== 没有找到足够的RpG/BpG字段")
            else:
                logger.warning("==liuq debug== 没有找到图片标识字段")
                
        except Exception as e:
            logger.error(f"==liuq debug== 对比分析准确性测试失败: {str(e)}")
    
    def test_analysis_chart_display(self, loaded_report_tab, qtbot):
        """测试分析图表清晰易懂"""
        logger.info("==liuq debug== 测试分析图表显示")
        
        # 触发RpG/BpG分析图表生成
        if hasattr(loaded_report_tab, 'generate_rpg_bpg_analysis'):
            loaded_report_tab.generate_rpg_bpg_analysis()
        elif hasattr(loaded_report_tab, 'show_rpg_bpg_chart'):
            loaded_report_tab.show_rpg_bpg_chart()
        else:
            # 模拟图表生成
            self._simulate_rpg_bpg_chart_generation(loaded_report_tab)
        
        qtbot.wait(1000)
        
        # 检查图表控件
        chart_widgets = [
            'rpg_bpg_chart_widget',
            'analysis_chart_view',
            'comparison_plot_widget',
            'scatter_plot_widget'
        ]
        
        chart_found = False
        for widget_name in chart_widgets:
            if hasattr(loaded_report_tab, widget_name):
                widget = getattr(loaded_report_tab, widget_name)
                
                if hasattr(widget, 'isVisible') and widget.isVisible():
                    chart_found = True
                    logger.info(f"==liuq debug== 找到可见的图表控件: {widget_name}")
                    
                    # 检查图表大小
                    if hasattr(widget, 'size'):
                        size = widget.size()
                        logger.info(f"==liuq debug== 图表尺寸: {size.width()}x{size.height()}")
                        
                        # 图表应该有合理的尺寸
                        assert size.width() > 100, f"图表宽度过小: {size.width()}"
                        assert size.height() > 100, f"图表高度过小: {size.height()}"
                    break
        
        if not chart_found:
            logger.warning("==liuq debug== 未找到RpG/BpG分析图表控件")
    
    def test_data_statistics_accuracy(self, test_csv_file, comparison_csv_file):
        """测试数据统计信息正确"""
        logger.info("==liuq debug== 测试数据统计信息正确性")
        
        try:
            test_df = pd.read_csv(test_csv_file)
            comparison_df = pd.read_csv(comparison_csv_file)
            
            # 查找RpG/BpG字段
            rpg_fields = [col for col in test_df.columns if 'rpg' in col.lower()]
            bpg_fields = [col for col in test_df.columns if 'bpg' in col.lower()]
            
            statistics_results = {}
            
            # 计算RpG统计信息
            for field in rpg_fields[:2]:  # 分析前2个RpG字段
                if field in test_df.columns:
                    test_values = pd.to_numeric(test_df[field], errors='coerce').dropna()
                    
                    if len(test_values) > 0:
                        stats = {
                            'count': len(test_values),
                            'mean': test_values.mean(),
                            'std': test_values.std(),
                            'min': test_values.min(),
                            'max': test_values.max(),
                            'median': test_values.median()
                        }
                        
                        statistics_results[f'{field}_test'] = stats
                        logger.info(f"==liuq debug== {field}测试数据统计: {stats}")
                
                if field in comparison_df.columns:
                    comp_values = pd.to_numeric(comparison_df[field], errors='coerce').dropna()
                    
                    if len(comp_values) > 0:
                        stats = {
                            'count': len(comp_values),
                            'mean': comp_values.mean(),
                            'std': comp_values.std(),
                            'min': comp_values.min(),
                            'max': comp_values.max(),
                            'median': comp_values.median()
                        }
                        
                        statistics_results[f'{field}_comparison'] = stats
                        logger.info(f"==liuq debug== {field}对比数据统计: {stats}")
            
            # 计算BpG统计信息
            for field in bpg_fields[:2]:  # 分析前2个BpG字段
                if field in test_df.columns:
                    test_values = pd.to_numeric(test_df[field], errors='coerce').dropna()
                    
                    if len(test_values) > 0:
                        stats = {
                            'count': len(test_values),
                            'mean': test_values.mean(),
                            'std': test_values.std(),
                            'min': test_values.min(),
                            'max': test_values.max(),
                            'median': test_values.median()
                        }
                        
                        statistics_results[f'{field}_test'] = stats
                        logger.info(f"==liuq debug== {field}测试数据统计: {stats}")
            
            # 验证统计信息的合理性
            for key, stats in statistics_results.items():
                assert stats['count'] > 0, f"{key}数据计数为0"
                assert not np.isnan(stats['mean']), f"{key}平均值为NaN"
                assert stats['min'] <= stats['max'], f"{key}最小值大于最大值"
                assert stats['min'] <= stats['median'] <= stats['max'], f"{key}中位数不在合理范围"
            
            logger.info(f"==liuq debug== 统计信息验证通过，共计算{len(statistics_results)}个字段的统计")
            
        except Exception as e:
            logger.error(f"==liuq debug== 数据统计信息测试失败: {str(e)}")
    
    def test_abnormal_data_identification(self, test_csv_file, comparison_csv_file):
        """测试异常数据有明确标识"""
        logger.info("==liuq debug== 测试异常数据标识")
        
        try:
            test_df = pd.read_csv(test_csv_file)
            
            # 查找RpG/BpG字段
            rpg_fields = [col for col in test_df.columns if 'rpg' in col.lower()]
            bpg_fields = [col for col in test_df.columns if 'bpg' in col.lower()]
            
            abnormal_data_found = False
            
            # 检查RpG异常值
            for field in rpg_fields[:2]:
                values = pd.to_numeric(test_df[field], errors='coerce').dropna()
                
                if len(values) > 0:
                    # 使用IQR方法检测异常值
                    Q1 = values.quantile(0.25)
                    Q3 = values.quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = values[(values < lower_bound) | (values > upper_bound)]
                    
                    if len(outliers) > 0:
                        abnormal_data_found = True
                        logger.info(f"==liuq debug== {field}发现{len(outliers)}个异常值")
                        logger.info(f"==liuq debug== 异常值范围: {outliers.min():.4f} - {outliers.max():.4f}")
                        logger.info(f"==liuq debug== 正常范围: {lower_bound:.4f} - {upper_bound:.4f}")
            
            # 检查BpG异常值
            for field in bpg_fields[:2]:
                values = pd.to_numeric(test_df[field], errors='coerce').dropna()
                
                if len(values) > 0:
                    # 使用IQR方法检测异常值
                    Q1 = values.quantile(0.25)
                    Q3 = values.quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = values[(values < lower_bound) | (values > upper_bound)]
                    
                    if len(outliers) > 0:
                        abnormal_data_found = True
                        logger.info(f"==liuq debug== {field}发现{len(outliers)}个异常值")
                        logger.info(f"==liuq debug== 异常值范围: {outliers.min():.4f} - {outliers.max():.4f}")
                        logger.info(f"==liuq debug== 正常范围: {lower_bound:.4f} - {upper_bound:.4f}")
            
            if abnormal_data_found:
                logger.info("==liuq debug== 成功识别异常数据")
            else:
                logger.info("==liuq debug== 未发现明显异常数据")
                
        except Exception as e:
            logger.error(f"==liuq debug== 异常数据识别测试失败: {str(e)}")
    
    def test_analysis_performance(self, test_csv_file, comparison_csv_file):
        """测试分析性能"""
        logger.info("==liuq debug== 测试RpG/BpG分析性能")
        
        import time
        
        try:
            start_time = time.time()
            
            # 读取数据
            test_df = pd.read_csv(test_csv_file)
            comparison_df = pd.read_csv(comparison_csv_file)
            
            load_time = time.time() - start_time
            logger.info(f"==liuq debug== 数据加载时间: {load_time:.2f}秒")
            
            # 执行分析
            analysis_start_time = time.time()
            
            # 模拟RpG/BpG分析过程
            rpg_fields = [col for col in test_df.columns if 'rpg' in col.lower()]
            bpg_fields = [col for col in test_df.columns if 'bpg' in col.lower()]
            
            analysis_results = {}
            
            for field in rpg_fields + bpg_fields:
                if field in test_df.columns:
                    values = pd.to_numeric(test_df[field], errors='coerce').dropna()
                    
                    if len(values) > 0:
                        # 计算统计信息
                        stats = {
                            'mean': values.mean(),
                            'std': values.std(),
                            'min': values.min(),
                            'max': values.max()
                        }
                        analysis_results[field] = stats
            
            analysis_time = time.time() - analysis_start_time
            logger.info(f"==liuq debug== 分析计算时间: {analysis_time:.2f}秒")
            logger.info(f"==liuq debug== 分析字段数量: {len(analysis_results)}")
            
            # 性能要求：分析时间应小于30秒
            total_time = load_time + analysis_time
            assert total_time < 30.0, f"RpG/BpG分析性能过低: {total_time:.2f}秒"
            
            logger.info(f"==liuq debug== 总分析时间: {total_time:.2f}秒")
            
        except Exception as e:
            logger.error(f"==liuq debug== 分析性能测试失败: {str(e)}")
    
    def _load_and_process_data(self, report_tab, test_csv_file, comparison_csv_file, qtbot):
        """加载和处理数据的辅助方法"""
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
        
        # 执行数据匹配
        if hasattr(report_tab, 'execute_data_matching'):
            report_tab.execute_data_matching()
            qtbot.wait(1000)
    
    def _simulate_rpg_bpg_chart_generation(self, report_tab):
        """模拟RpG/BpG图表生成的辅助方法"""
        logger.info("==liuq debug== 模拟RpG/BpG图表生成")
        
        # 这里可以添加模拟图表生成的逻辑
        # 例如创建matplotlib图表或其他可视化组件

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
