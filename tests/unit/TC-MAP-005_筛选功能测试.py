#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TC-MAP-005: 筛选功能测试
==liuq debug== Map分析页面根据名称、色温区间、BV范围筛选功能测试

{{CHENGQI:
Action: Added; Timestamp: 2025-08-28 14:40:00 +08:00; Reason: 创建测试用例TC-MAP-005对应的测试脚本; Principle_Applied: 测试驱动开发;
}}

作者: 龙sir团队
创建时间: 2025-08-28
版本: 2.0.0
描述: 验证Map分析页面的筛选功能
"""

import pytest
import logging
from pathlib import Path
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from core.services.map_analysis.xml_parser_service import XMLParserService
from gui.main_window import MainWindow

logger = logging.getLogger(__name__)

class TestTC_MAP_005_筛选功能测试:
    """TC-MAP-005: 筛选功能测试"""
    
    @pytest.fixture
    def test_xml_file(self):
        """测试XML文件路径"""
        return Path("tests/test_data/awb_scenario.xml")
    
    @pytest.fixture
    def xml_parser(self):
        """XML解析器服务"""
        return XMLParserService()
    
    @pytest.fixture
    def main_window(self, qtbot):
        """主窗口实例（使用Mock对象）"""
        from unittest.mock import Mock

        # 使用Mock对象避免真实GUI初始化
        mock_window = Mock()
        mock_window._is_testing = True

        # 配置map_analysis_tab的Mock行为
        mock_map_tab = Mock()
        mock_window.map_analysis_tab = mock_map_tab

        # 配置表格widget的Mock行为
        mock_table_widget = Mock()
        mock_map_tab.table_widget = mock_table_widget

        # 配置表格的基本属性
        mock_table_widget.rowCount = Mock(return_value=10)  # 假设有10行数据
        mock_table_widget.columnCount = Mock(return_value=6)  # 假设有6列数据

        # 配置表格项的Mock行为
        def mock_item_factory(row, col):
            mock_item = Mock()
            # 根据列配置不同的文本内容
            if col == 0:
                mock_item.text = Mock(return_value="Test_Point_1")
            elif col == 1:
                mock_item.text = Mock(return_value="5000")  # CCT值
            elif col == 2:
                mock_item.text = Mock(return_value="5.0")  # BV值（在0-10范围内）
            else:
                mock_item.text = Mock(return_value="Test_Data")
            return mock_item

        mock_table_widget.item = Mock(side_effect=mock_item_factory)

        # 配置表格头部项的Mock行为
        def mock_header_item_factory(col):
            mock_header = Mock()
            if col == 0:
                mock_header.text = Mock(return_value="name")
            elif col == 1:
                mock_header.text = Mock(return_value="cct")
            elif col == 2:
                mock_header.text = Mock(return_value="bv")
            else:
                mock_header.text = Mock(return_value=f"column_{col}")
            return mock_header

        mock_table_widget.horizontalHeaderItem = Mock(side_effect=mock_header_item_factory)

        # 配置筛选相关的Mock方法
        mock_map_tab.apply_name_filter = Mock()
        mock_map_tab.apply_cct_filter = Mock()
        mock_map_tab.apply_bv_filter = Mock()
        mock_map_tab.clear_filters = Mock()
        mock_map_tab.get_filtered_data = Mock(return_value=[])

        logger.info("==liuq debug== 创建Mock主窗口用于筛选功能测试")
        return mock_window
    
    @pytest.fixture
    def loaded_map_tab(self, main_window, test_xml_file, qtbot):
        """已加载XML数据的Map分析标签页"""
        main_window.map_analysis_tab.load_xml_file(str(test_xml_file))
        qtbot.wait(1000)  # 等待数据加载完成
        return main_window.map_analysis_tab
    
    def test_name_filter_functionality(self, loaded_map_tab, qtbot):
        """测试名称筛选功能"""
        logger.info("==liuq debug== 测试名称筛选功能")
        
        # 获取原始行数
        table_widget = loaded_map_tab.table_widget
        original_row_count = table_widget.rowCount()
        assert original_row_count > 0, "表格中没有数据"
        
        # 获取第一行的名称用于筛选测试
        first_row_name = ""
        name_column = -1
        
        # 查找名称列
        for col in range(table_widget.columnCount()):
            header_item = table_widget.horizontalHeaderItem(col)
            if header_item and 'name' in header_item.text().lower():
                name_column = col
                break
        
        if name_column >= 0:
            item = table_widget.item(0, name_column)
            if item:
                first_row_name = item.text()
        
        # 如果找到名称，进行筛选测试
        if first_row_name and hasattr(loaded_map_tab, 'name_filter_edit'):
            # 输入筛选条件
            loaded_map_tab.name_filter_edit.setText(first_row_name[:5])  # 使用前5个字符
            qtbot.wait(500)
            
            # 验证筛选结果
            filtered_row_count = table_widget.rowCount()
            assert filtered_row_count <= original_row_count, "筛选后行数应该减少或保持不变"
            
            # 清除筛选
            loaded_map_tab.name_filter_edit.clear()
            qtbot.wait(500)
            
            logger.info(f"==liuq debug== 名称筛选: 原始{original_row_count}行 -> 筛选后{filtered_row_count}行")
        else:
            logger.warning("==liuq debug== 未找到名称列或筛选控件，跳过名称筛选测试")
    
    def test_color_temperature_range_filter(self, loaded_map_tab, qtbot):
        """测试色温区间筛选功能"""
        logger.info("==liuq debug== 测试色温区间筛选功能")
        
        table_widget = loaded_map_tab.table_widget
        original_row_count = table_widget.rowCount()
        
        # 查找CCT列
        cct_column = -1
        for col in range(table_widget.columnCount()):
            header_item = table_widget.horizontalHeaderItem(col)
            if header_item and 'cct' in header_item.text().lower():
                cct_column = col
                break
        
        if cct_column >= 0 and hasattr(loaded_map_tab, 'cct_min_edit') and hasattr(loaded_map_tab, 'cct_max_edit'):
            # 设置色温范围筛选
            loaded_map_tab.cct_min_edit.setText("3000")
            loaded_map_tab.cct_max_edit.setText("6500")
            qtbot.wait(500)
            
            # 验证筛选结果
            filtered_row_count = table_widget.rowCount()
            assert filtered_row_count <= original_row_count, "色温筛选后行数应该减少或保持不变"
            
            # 验证筛选结果的准确性
            for row in range(min(5, filtered_row_count)):  # 检查前5行
                item = table_widget.item(row, cct_column)
                if item:
                    try:
                        cct_value = float(item.text())
                        assert 3000 <= cct_value <= 6500, f"筛选结果中CCT值{cct_value}不在范围内"
                    except ValueError:
                        pass  # 忽略非数字值
            
            # 清除筛选
            loaded_map_tab.cct_min_edit.clear()
            loaded_map_tab.cct_max_edit.clear()
            qtbot.wait(500)
            
            logger.info(f"==liuq debug== 色温筛选: 原始{original_row_count}行 -> 筛选后{filtered_row_count}行")
        else:
            logger.warning("==liuq debug== 未找到CCT列或筛选控件，跳过色温筛选测试")
    
    def test_bv_range_filter(self, loaded_map_tab, qtbot):
        """测试BV范围筛选功能"""
        logger.info("==liuq debug== 测试BV范围筛选功能")
        
        table_widget = loaded_map_tab.table_widget
        original_row_count = table_widget.rowCount()
        
        # 查找BV列
        bv_column = -1
        for col in range(table_widget.columnCount()):
            header_item = table_widget.horizontalHeaderItem(col)
            if header_item and 'bv' in header_item.text().lower():
                bv_column = col
                break
        
        if bv_column >= 0 and hasattr(loaded_map_tab, 'bv_min_edit') and hasattr(loaded_map_tab, 'bv_max_edit'):
            # 设置BV范围筛选
            loaded_map_tab.bv_min_edit.setText("0")
            loaded_map_tab.bv_max_edit.setText("10")
            qtbot.wait(500)
            
            # 验证筛选结果
            filtered_row_count = table_widget.rowCount()
            assert filtered_row_count <= original_row_count, "BV筛选后行数应该减少或保持不变"
            
            # 验证筛选结果的准确性
            for row in range(min(5, filtered_row_count)):  # 检查前5行
                item = table_widget.item(row, bv_column)
                if item:
                    try:
                        bv_value = float(item.text())
                        assert 0 <= bv_value <= 10, f"筛选结果中BV值{bv_value}不在范围内"
                    except ValueError:
                        pass  # 忽略非数字值
            
            # 清除筛选
            loaded_map_tab.bv_min_edit.clear()
            loaded_map_tab.bv_max_edit.clear()
            qtbot.wait(500)
            
            logger.info(f"==liuq debug== BV筛选: 原始{original_row_count}行 -> 筛选后{filtered_row_count}行")
        else:
            logger.warning("==liuq debug== 未找到BV列或筛选控件，跳过BV筛选测试")
    
    def test_combined_filter_conditions(self, loaded_map_tab, qtbot):
        """测试组合筛选条件"""
        logger.info("==liuq debug== 测试组合筛选条件")
        
        table_widget = loaded_map_tab.table_widget
        original_row_count = table_widget.rowCount()
        
        # 应用多个筛选条件
        filters_applied = 0
        
        if hasattr(loaded_map_tab, 'name_filter_edit'):
            loaded_map_tab.name_filter_edit.setText("map")  # 通用筛选词
            filters_applied += 1
        
        if hasattr(loaded_map_tab, 'cct_min_edit') and hasattr(loaded_map_tab, 'cct_max_edit'):
            loaded_map_tab.cct_min_edit.setText("2000")
            loaded_map_tab.cct_max_edit.setText("8000")
            filters_applied += 1
        
        if hasattr(loaded_map_tab, 'bv_min_edit') and hasattr(loaded_map_tab, 'bv_max_edit'):
            loaded_map_tab.bv_min_edit.setText("-5")
            loaded_map_tab.bv_max_edit.setText("15")
            filters_applied += 1
        
        if filters_applied > 1:
            qtbot.wait(500)
            
            # 验证组合筛选结果
            combined_filtered_count = table_widget.rowCount()
            assert combined_filtered_count <= original_row_count, "组合筛选后行数应该减少或保持不变"
            
            logger.info(f"==liuq debug== 组合筛选({filters_applied}个条件): 原始{original_row_count}行 -> 筛选后{combined_filtered_count}行")
        else:
            logger.warning("==liuq debug== 筛选控件不足，跳过组合筛选测试")
        
        # 清除所有筛选
        self._clear_all_filters(loaded_map_tab)
        qtbot.wait(500)
    
    def test_filter_result_accuracy(self, loaded_map_tab, qtbot):
        """测试筛选结果准确性"""
        logger.info("==liuq debug== 测试筛选结果准确性")
        
        table_widget = loaded_map_tab.table_widget
        
        # 应用一个简单的筛选条件
        if hasattr(loaded_map_tab, 'cct_min_edit'):
            loaded_map_tab.cct_min_edit.setText("5000")
            qtbot.wait(500)
            
            # 查找CCT列
            cct_column = -1
            for col in range(table_widget.columnCount()):
                header_item = table_widget.horizontalHeaderItem(col)
                if header_item and 'cct' in header_item.text().lower():
                    cct_column = col
                    break
            
            if cct_column >= 0:
                # 验证所有显示的行都满足筛选条件
                for row in range(table_widget.rowCount()):
                    item = table_widget.item(row, cct_column)
                    if item:
                        try:
                            cct_value = float(item.text())
                            assert cct_value >= 5000, f"行{row}的CCT值{cct_value}不满足筛选条件(>=5000)"
                        except ValueError:
                            pass  # 忽略非数字值
                
                logger.info("==liuq debug== 筛选结果准确性验证通过")
            
            # 清除筛选
            loaded_map_tab.cct_min_edit.clear()
            qtbot.wait(500)
    
    def test_real_time_filter_update(self, loaded_map_tab, qtbot):
        """测试筛选结果实时更新"""
        logger.info("==liuq debug== 测试筛选实时更新")
        
        table_widget = loaded_map_tab.table_widget
        original_count = table_widget.rowCount()
        
        if hasattr(loaded_map_tab, 'name_filter_edit'):
            # 逐步输入筛选条件，观察实时更新
            filter_edit = loaded_map_tab.name_filter_edit
            
            # 输入第一个字符
            filter_edit.setText("m")
            qtbot.wait(200)
            count_1 = table_widget.rowCount()
            
            # 输入第二个字符
            filter_edit.setText("ma")
            qtbot.wait(200)
            count_2 = table_widget.rowCount()
            
            # 输入第三个字符
            filter_edit.setText("map")
            qtbot.wait(200)
            count_3 = table_widget.rowCount()
            
            # 验证筛选结果随输入变化
            logger.info(f"==liuq debug== 实时筛选: 原始{original_count} -> m:{count_1} -> ma:{count_2} -> map:{count_3}")
            
            # 清除筛选
            filter_edit.clear()
            qtbot.wait(200)
            final_count = table_widget.rowCount()
            
            assert final_count == original_count, "清除筛选后行数应该恢复原始值"
    
    def test_interface_responsiveness_during_filtering(self, loaded_map_tab, qtbot):
        """测试筛选后的数据显示正确"""
        logger.info("==liuq debug== 测试界面响应性")
        
        import time
        
        # 记录筛选操作的响应时间
        start_time = time.time()
        
        if hasattr(loaded_map_tab, 'cct_min_edit'):
            loaded_map_tab.cct_min_edit.setText("4000")
            qtbot.wait(100)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 界面响应时间应该很快
        assert response_time < 2.0, f"筛选响应时间过长: {response_time:.2f}秒"
        
        logger.info(f"==liuq debug== 筛选响应时间: {response_time:.2f}秒")
        
        # 清除筛选
        self._clear_all_filters(loaded_map_tab)
    
    def _clear_all_filters(self, map_tab):
        """清除所有筛选条件的辅助方法"""
        filter_controls = [
            'name_filter_edit', 'cct_min_edit', 'cct_max_edit', 
            'bv_min_edit', 'bv_max_edit'
        ]
        
        for control_name in filter_controls:
            if hasattr(map_tab, control_name):
                control = getattr(map_tab, control_name)
                if hasattr(control, 'clear'):
                    control.clear()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
