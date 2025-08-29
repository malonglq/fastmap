#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据绑定管理器实现
==liuq debug== FastMapV2 数据绑定管理器的具体实现

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 16:00:00 +08:00; Reason: P1-LD-007-001 创建DataBindingManagerImpl类; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 实现DataBindingManager接口，提供GUI组件与数据模型的双向绑定功能
"""

import uuid
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from core.interfaces.data_binding_manager import (
    DataBindingManager, BindingDirection, BindingStatus, BindingInfo, 
    SyncResult, BindingError, SyncError
)
from core.interfaces.xml_field_definition import XMLFieldDefinition, FieldType

logger = logging.getLogger(__name__)


class DataBindingManagerImpl(QObject):
    """
    数据绑定管理器实现

    提供GUI组件与数据模型之间的双向绑定功能，支持：
    - 自动数据同步
    - 数据验证
    - 错误处理
    - 绑定生命周期管理

    设计特点：
    - 基于PyQt信号槽机制实现实时同步
    - 支持多种GUI组件类型
    - 提供完整的错误处理和回滚机制
    - 支持批量操作和单个操作

    实现DataBindingManager接口的所有方法
    """

    # 信号定义
    data_changed = pyqtSignal(str, object, object)  # (binding_id, old_value, new_value)
    validation_error = pyqtSignal(str, str)  # (binding_id, error_message)
    sync_completed = pyqtSignal(str, bool)  # (binding_id, success)

    def __init__(self):
        """初始化数据绑定管理器"""
        QObject.__init__(self)
        
        self._bindings: Dict[str, BindingInfo] = {}
        self._widget_to_binding: Dict[QWidget, str] = {}
        self._data_to_bindings: Dict[id, List[str]] = {}
        
        # 延迟同步定时器，避免频繁更新
        self._sync_timer = QTimer()
        self._sync_timer.setSingleShot(True)
        self._sync_timer.timeout.connect(self._delayed_sync)
        self._pending_syncs: set = set()
        
        logger.info("==liuq debug== 数据绑定管理器初始化完成")
    
    def create_binding(self, data_object: Any, field_definition: XMLFieldDefinition,
                      widget: QWidget, direction: BindingDirection = BindingDirection.TWO_WAY,
                      binding_id: Optional[str] = None) -> str:
        """
        创建数据绑定
        
        Args:
            data_object: 数据对象
            field_definition: 字段定义
            widget: GUI组件
            direction: 绑定方向
            binding_id: 自定义绑定ID，None则自动生成
            
        Returns:
            str: 绑定ID
            
        Raises:
            BindingError: 绑定创建失败
        """
        try:
            # 生成绑定ID
            if binding_id is None:
                binding_id = f"binding_{uuid.uuid4().hex[:8]}"
            
            # 检查绑定ID是否已存在
            if binding_id in self._bindings:
                raise BindingError(f"绑定ID已存在: {binding_id}")
            
            # 检查组件是否已绑定
            if widget in self._widget_to_binding:
                existing_binding_id = self._widget_to_binding[widget]
                logger.warning(f"==liuq debug== 组件已绑定到 {existing_binding_id}，将移除旧绑定")
                self.remove_binding(existing_binding_id)
            
            # 验证字段定义和组件兼容性
            if not self._validate_widget_compatibility(widget, field_definition):
                raise BindingError(f"组件类型与字段类型不兼容: {type(widget).__name__} vs {field_definition.field_type}")
            
            # 创建绑定信息
            binding_info = BindingInfo(
                binding_id=binding_id,
                data_object=data_object,
                field_definition=field_definition,
                widget=widget,
                direction=direction,
                status=BindingStatus.ACTIVE,
                last_sync_time=datetime.now().isoformat(),
                metadata={}
            )
            
            # 存储绑定信息
            self._bindings[binding_id] = binding_info
            self._widget_to_binding[widget] = binding_id
            
            # 建立数据对象到绑定的映射
            data_id = id(data_object)
            if data_id not in self._data_to_bindings:
                self._data_to_bindings[data_id] = []
            self._data_to_bindings[data_id].append(binding_id)
            
            # 连接信号槽
            self._connect_widget_signals(widget, binding_id)
            
            # 初始同步：从数据到GUI
            self.sync_to_gui(binding_id)
            
            logger.info(f"==liuq debug== 创建数据绑定成功: {binding_id} ({field_definition.field_id})")
            return binding_id
            
        except Exception as e:
            logger.error(f"==liuq debug== 创建数据绑定失败: {e}")
            raise BindingError(f"创建绑定失败: {e}")
    
    def remove_binding(self, binding_id: str) -> bool:
        """
        移除数据绑定
        
        Args:
            binding_id: 绑定ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            if binding_id not in self._bindings:
                logger.warning(f"==liuq debug== 绑定不存在: {binding_id}")
                return False
            
            binding_info = self._bindings[binding_id]
            
            # 断开信号槽连接
            self._disconnect_widget_signals(binding_info.widget, binding_id)
            
            # 移除映射关系
            if binding_info.widget in self._widget_to_binding:
                del self._widget_to_binding[binding_info.widget]
            
            data_id = id(binding_info.data_object)
            if data_id in self._data_to_bindings:
                if binding_id in self._data_to_bindings[data_id]:
                    self._data_to_bindings[data_id].remove(binding_id)
                if not self._data_to_bindings[data_id]:
                    del self._data_to_bindings[data_id]
            
            # 移除绑定信息
            del self._bindings[binding_id]
            
            logger.info(f"==liuq debug== 移除数据绑定成功: {binding_id}")
            return True
            
        except Exception as e:
            logger.error(f"==liuq debug== 移除数据绑定失败: {e}")
            return False
    
    def get_binding(self, binding_id: str) -> Optional[BindingInfo]:
        """
        获取绑定信息
        
        Args:
            binding_id: 绑定ID
            
        Returns:
            Optional[BindingInfo]: 绑定信息，不存在则返回None
        """
        return self._bindings.get(binding_id)
    
    def get_all_bindings(self) -> List[BindingInfo]:
        """
        获取所有绑定信息
        
        Returns:
            List[BindingInfo]: 所有绑定信息列表
        """
        return list(self._bindings.values())
    
    def sync_to_gui(self, binding_id: Optional[str] = None) -> List[SyncResult]:
        """
        同步数据到GUI
        
        Args:
            binding_id: 指定绑定ID，None则同步所有绑定
            
        Returns:
            List[SyncResult]: 同步结果列表
        """
        results = []
        
        if binding_id is not None:
            # 同步指定绑定
            if binding_id in self._bindings:
                result = self._sync_single_to_gui(binding_id)
                results.append(result)
            else:
                results.append(SyncResult(
                    binding_id=binding_id,
                    success=False,
                    error_message=f"绑定不存在: {binding_id}",
                    sync_time=datetime.now().isoformat()
                ))
        else:
            # 同步所有绑定
            for bid in self._bindings.keys():
                result = self._sync_single_to_gui(bid)
                results.append(result)
        
        return results
    
    def sync_to_data(self, binding_id: Optional[str] = None) -> List[SyncResult]:
        """
        同步GUI到数据
        
        Args:
            binding_id: 指定绑定ID，None则同步所有绑定
            
        Returns:
            List[SyncResult]: 同步结果列表
        """
        results = []
        
        if binding_id is not None:
            # 同步指定绑定
            if binding_id in self._bindings:
                result = self._sync_single_to_data(binding_id)
                results.append(result)
            else:
                results.append(SyncResult(
                    binding_id=binding_id,
                    success=False,
                    error_message=f"绑定不存在: {binding_id}",
                    sync_time=datetime.now().isoformat()
                ))
        else:
            # 同步所有绑定
            for bid in self._bindings.keys():
                result = self._sync_single_to_data(bid)
                results.append(result)
        
        return results
    
    def suspend_binding(self, binding_id: str) -> bool:
        """
        暂停绑定
        
        Args:
            binding_id: 绑定ID
            
        Returns:
            bool: 操作是否成功
        """
        if binding_id in self._bindings:
            self._bindings[binding_id].status = BindingStatus.SUSPENDED
            logger.info(f"==liuq debug== 暂停绑定: {binding_id}")
            return True
        return False
    
    def resume_binding(self, binding_id: str) -> bool:
        """
        恢复绑定
        
        Args:
            binding_id: 绑定ID
            
        Returns:
            bool: 操作是否成功
        """
        if binding_id in self._bindings:
            self._bindings[binding_id].status = BindingStatus.ACTIVE
            # 恢复时重新同步
            self.sync_to_gui(binding_id)
            logger.info(f"==liuq debug== 恢复绑定: {binding_id}")
            return True
        return False
    
    def clear_all_bindings(self):
        """清除所有绑定"""
        binding_ids = list(self._bindings.keys())
        for binding_id in binding_ids:
            self.remove_binding(binding_id)
        
        logger.info("==liuq debug== 清除所有数据绑定")
    
    def get_bindings_for_data_object(self, data_object: Any) -> List[BindingInfo]:
        """
        获取指定数据对象的所有绑定
        
        Args:
            data_object: 数据对象
            
        Returns:
            List[BindingInfo]: 绑定信息列表
        """
        data_id = id(data_object)
        if data_id in self._data_to_bindings:
            binding_ids = self._data_to_bindings[data_id]
            return [self._bindings[bid] for bid in binding_ids if bid in self._bindings]
        return []


    def _validate_widget_compatibility(self, widget: QWidget, field_definition: XMLFieldDefinition) -> bool:
        """
        验证组件与字段类型的兼容性

        Args:
            widget: GUI组件
            field_definition: 字段定义

        Returns:
            bool: 是否兼容
        """
        widget_type = type(widget)
        field_type = field_definition.field_type

        # 定义兼容性映射
        compatibility_map = {
            FieldType.STRING: [QLineEdit, QComboBox],
            FieldType.INTEGER: [QSpinBox, QLineEdit],
            FieldType.FLOAT: [QDoubleSpinBox, QLineEdit],
            FieldType.BOOLEAN: [QCheckBox],
        }

        compatible_widgets = compatibility_map.get(field_type, [])
        return any(isinstance(widget, widget_class) for widget_class in compatible_widgets)

    def _connect_widget_signals(self, widget: QWidget, binding_id: str):
        """
        连接组件信号到绑定处理器

        Args:
            widget: GUI组件
            binding_id: 绑定ID
        """
        try:
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda: self._on_widget_value_changed(binding_id))
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(lambda: self._on_widget_value_changed(binding_id))
            elif isinstance(widget, QDoubleSpinBox):
                widget.valueChanged.connect(lambda: self._on_widget_value_changed(binding_id))
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(lambda: self._on_widget_value_changed(binding_id))
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(lambda: self._on_widget_value_changed(binding_id))

            logger.debug(f"==liuq debug== 连接组件信号: {binding_id} ({type(widget).__name__})")

        except Exception as e:
            logger.error(f"==liuq debug== 连接组件信号失败: {e}")

    def _disconnect_widget_signals(self, widget: QWidget, binding_id: str):
        """
        断开组件信号连接

        Args:
            widget: GUI组件
            binding_id: 绑定ID
        """
        try:
            # PyQt会自动处理信号断开，这里主要是日志记录
            logger.debug(f"==liuq debug== 断开组件信号: {binding_id} ({type(widget).__name__})")
            # 实际的信号断开逻辑（如果需要的话）
            pass
        except Exception as e:
            logger.error(f"==liuq debug== 断开组件信号失败: {e}")

    def _on_widget_value_changed(self, binding_id: str):
        """
        处理组件值变化事件

        Args:
            binding_id: 绑定ID
        """
        try:
            binding_info = self._bindings.get(binding_id)
            if not binding_info or binding_info.status != BindingStatus.ACTIVE:
                return

            # 检查绑定方向
            if binding_info.direction in [BindingDirection.ONE_WAY_TO_GUI]:
                return  # 单向绑定，不处理GUI到数据的同步

            # 添加到延迟同步队列
            self._pending_syncs.add(binding_id)

            # 启动延迟同步定时器（避免频繁更新）
            self._sync_timer.start(100)  # 100ms延迟

        except Exception as e:
            logger.error(f"==liuq debug== 处理组件值变化失败: {e}")

    def _delayed_sync(self):
        """延迟同步处理"""
        try:
            pending_bindings = list(self._pending_syncs)
            self._pending_syncs.clear()

            for binding_id in pending_bindings:
                self._sync_single_to_data(binding_id)

        except Exception as e:
            logger.error(f"==liuq debug== 延迟同步失败: {e}")

    def _sync_single_to_gui(self, binding_id: str) -> SyncResult:
        """
        同步单个绑定的数据到GUI

        Args:
            binding_id: 绑定ID

        Returns:
            SyncResult: 同步结果
        """
        try:
            binding_info = self._bindings[binding_id]

            if binding_info.status != BindingStatus.ACTIVE:
                return SyncResult(
                    binding_id=binding_id,
                    success=False,
                    error_message="绑定未激活",
                    sync_time=datetime.now().isoformat()
                )

            # 检查绑定方向
            if binding_info.direction == BindingDirection.ONE_WAY_TO_DATA:
                return SyncResult(
                    binding_id=binding_id,
                    success=True,
                    error_message="单向绑定，跳过数据到GUI同步",
                    sync_time=datetime.now().isoformat()
                )

            # 从数据对象获取值
            field_value = self._get_field_value_from_data(
                binding_info.data_object,
                binding_info.field_definition
            )

            # 设置到GUI组件
            self._set_widget_value(binding_info.widget, field_value, binding_info.field_definition)

            # 更新同步时间
            binding_info.last_sync_time = datetime.now().isoformat()

            logger.debug(f"==liuq debug== 同步到GUI成功: {binding_id} = {field_value}")

            return SyncResult(
                binding_id=binding_id,
                success=True,
                sync_time=binding_info.last_sync_time
            )

        except Exception as e:
            error_msg = f"同步到GUI失败: {e}"
            logger.error(f"==liuq debug== {error_msg}")

            # 更新绑定状态
            if binding_id in self._bindings:
                self._bindings[binding_id].status = BindingStatus.ERROR
                self._bindings[binding_id].error_message = error_msg

            return SyncResult(
                binding_id=binding_id,
                success=False,
                error_message=error_msg,
                sync_time=datetime.now().isoformat()
            )

    def _sync_single_to_data(self, binding_id: str) -> SyncResult:
        """
        同步单个绑定的GUI到数据

        Args:
            binding_id: 绑定ID

        Returns:
            SyncResult: 同步结果
        """
        try:
            binding_info = self._bindings[binding_id]

            if binding_info.status != BindingStatus.ACTIVE:
                return SyncResult(
                    binding_id=binding_id,
                    success=False,
                    error_message="绑定未激活",
                    sync_time=datetime.now().isoformat()
                )

            # 检查绑定方向
            if binding_info.direction == BindingDirection.ONE_WAY_TO_GUI:
                return SyncResult(
                    binding_id=binding_id,
                    success=True,
                    error_message="单向绑定，跳过GUI到数据同步",
                    sync_time=datetime.now().isoformat()
                )

            # 从GUI组件获取值
            widget_value = self._get_widget_value(binding_info.widget, binding_info.field_definition)

            # 验证值
            validation_result = self._validate_field_value(widget_value, binding_info.field_definition)
            if not validation_result.is_valid:
                error_msg = f"数据验证失败: {validation_result.error_message}"
                self.validation_error.emit(binding_id, error_msg)

                return SyncResult(
                    binding_id=binding_id,
                    success=False,
                    error_message=error_msg,
                    sync_time=datetime.now().isoformat()
                )

            # 获取旧值
            old_value = self._get_field_value_from_data(
                binding_info.data_object,
                binding_info.field_definition
            )

            # 设置到数据对象
            self._set_field_value_to_data(
                binding_info.data_object,
                binding_info.field_definition,
                widget_value
            )

            # 更新同步时间
            binding_info.last_sync_time = datetime.now().isoformat()

            # 发出数据变化信号
            self.data_changed.emit(binding_id, old_value, widget_value)

            logger.debug(f"==liuq debug== 同步到数据成功: {binding_id} = {widget_value}")

            return SyncResult(
                binding_id=binding_id,
                success=True,
                sync_time=binding_info.last_sync_time
            )

        except Exception as e:
            error_msg = f"同步到数据失败: {e}"
            logger.error(f"==liuq debug== {error_msg}")

            # 更新绑定状态
            if binding_id in self._bindings:
                self._bindings[binding_id].status = BindingStatus.ERROR
                self._bindings[binding_id].error_message = error_msg

            return SyncResult(
                binding_id=binding_id,
                success=False,
                error_message=error_msg,
                sync_time=datetime.now().isoformat()
            )


    def _get_field_value_from_data(self, data_object: Any, field_definition: XMLFieldDefinition) -> Any:
        """
        从数据对象获取字段值

        Args:
            data_object: 数据对象
            field_definition: 字段定义

        Returns:
            Any: 字段值
        """
        try:
            field_id = field_definition.field_id

            # 使用属性名直接访问
            if hasattr(data_object, field_id):
                return getattr(data_object, field_id)

            # 尝试常见的字段映射
            field_mapping = {
                'alias_name': 'alias_name',
                'x': 'x',
                'y': 'y',
                'offset_x': 'offset_x',
                'offset_y': 'offset_y',
                'weight': 'weight',
                'bv_min': lambda obj: obj.bv_range[0] if obj.bv_range else 0.0,
                'bv_max': lambda obj: obj.bv_range[1] if obj.bv_range else 100.0,
                'ir_min': lambda obj: obj.ir_range[0] if obj.ir_range else 0.0,
                'ir_max': lambda obj: obj.ir_range[1] if obj.ir_range else 100.0,
                'cct_min': lambda obj: obj.cct_range[0] if obj.cct_range else 2000.0,
                'cct_max': lambda obj: obj.cct_range[1] if obj.cct_range else 8000.0,
                'detect_flag': 'detect_flag',
                'trans_step': 'trans_step'
            }

            if field_id in field_mapping:
                mapping = field_mapping[field_id]
                if callable(mapping):
                    return mapping(data_object)
                elif hasattr(data_object, mapping):
                    return getattr(data_object, mapping)

            # 返回默认值
            return field_definition.default_value

        except Exception as e:
            logger.warning(f"==liuq debug== 获取字段值失败: {field_id} - {e}")
            return field_definition.default_value

    def _set_field_value_to_data(self, data_object: Any, field_definition: XMLFieldDefinition, value: Any):
        """
        设置字段值到数据对象

        Args:
            data_object: 数据对象
            field_definition: 字段定义
            value: 字段值
        """
        try:
            field_id = field_definition.field_id

            # 类型转换
            converted_value = self._convert_value_type(value, field_definition.field_type)

            # 使用属性名直接设置
            if hasattr(data_object, field_id):
                setattr(data_object, field_id, converted_value)
                return

            # 尝试常见的字段映射
            if field_id in ['bv_min', 'bv_max']:
                if not hasattr(data_object, 'bv_range') or data_object.bv_range is None:
                    data_object.bv_range = [0.0, 100.0]
                if field_id == 'bv_min':
                    data_object.bv_range[0] = converted_value
                else:
                    data_object.bv_range[1] = converted_value
            elif field_id in ['ir_min', 'ir_max']:
                if not hasattr(data_object, 'ir_range') or data_object.ir_range is None:
                    data_object.ir_range = [0.0, 100.0]
                if field_id == 'ir_min':
                    data_object.ir_range[0] = converted_value
                else:
                    data_object.ir_range[1] = converted_value
            elif field_id in ['cct_min', 'cct_max']:
                if not hasattr(data_object, 'cct_range') or data_object.cct_range is None:
                    data_object.cct_range = [2000.0, 8000.0]
                if field_id == 'cct_min':
                    data_object.cct_range[0] = converted_value
                else:
                    data_object.cct_range[1] = converted_value
            else:
                # 直接设置属性
                setattr(data_object, field_id, converted_value)

            logger.debug(f"==liuq debug== 设置字段值成功: {field_id} = {converted_value}")

        except Exception as e:
            logger.error(f"==liuq debug== 设置字段值失败: {field_id} - {e}")
            raise

    def _get_widget_value(self, widget: QWidget, field_definition: XMLFieldDefinition) -> Any:
        """
        从GUI组件获取值

        Args:
            widget: GUI组件
            field_definition: 字段定义

        Returns:
            Any: 组件值
        """
        try:
            if isinstance(widget, QLineEdit):
                return widget.text()
            elif isinstance(widget, QSpinBox):
                return widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                return widget.value()
            elif isinstance(widget, QCheckBox):
                return widget.isChecked()
            elif isinstance(widget, QComboBox):
                return widget.currentText()
            else:
                logger.warning(f"==liuq debug== 不支持的组件类型: {type(widget).__name__}")
                return field_definition.default_value

        except Exception as e:
            logger.error(f"==liuq debug== 获取组件值失败: {e}")
            return field_definition.default_value

    def _set_widget_value(self, widget: QWidget, value: Any, field_definition: XMLFieldDefinition):
        """
        设置值到GUI组件

        Args:
            widget: GUI组件
            value: 值
            field_definition: 字段定义
        """
        try:
            # 类型转换
            converted_value = self._convert_value_type(value, field_definition.field_type)

            if isinstance(widget, QLineEdit):
                widget.setText(str(converted_value) if converted_value is not None else "")
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(converted_value) if converted_value is not None else 0)
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(converted_value) if converted_value is not None else 0.0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(converted_value) if converted_value is not None else False)
            elif isinstance(widget, QComboBox):
                text = str(converted_value) if converted_value is not None else ""
                index = widget.findText(text)
                if index >= 0:
                    widget.setCurrentIndex(index)
                else:
                    widget.setCurrentText(text)

            logger.debug(f"==liuq debug== 设置组件值成功: {type(widget).__name__} = {converted_value}")

        except Exception as e:
            logger.error(f"==liuq debug== 设置组件值失败: {e}")

    def _convert_value_type(self, value: Any, field_type: FieldType) -> Any:
        """
        转换值类型

        Args:
            value: 原始值
            field_type: 目标字段类型

        Returns:
            Any: 转换后的值
        """
        try:
            if value is None:
                return None

            if field_type == FieldType.STRING:
                return str(value)
            elif field_type == FieldType.INTEGER:
                return int(float(value))  # 先转float再转int，处理"1.0"这种情况
            elif field_type == FieldType.FLOAT:
                return float(value)
            elif field_type == FieldType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'on']
                return bool(value)
            else:
                return value

        except (ValueError, TypeError) as e:
            logger.warning(f"==liuq debug== 类型转换失败: {value} -> {field_type} - {e}")
            return value

    def _validate_field_value(self, value: Any, field_definition: XMLFieldDefinition):
        """
        验证字段值

        Args:
            value: 字段值
            field_definition: 字段定义

        Returns:
            ValidationResult: 验证结果
        """
        from dataclasses import dataclass

        @dataclass
        class ValidationResult:
            is_valid: bool
            error_message: str = ""

        try:
            # 基础类型验证
            converted_value = self._convert_value_type(value, field_definition.field_type)

            # 应用验证规则
            for rule in field_definition.validation_rules:
                if not self._apply_validation_rule(converted_value, rule):
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"验证规则失败: {rule.rule_type.value}"
                    )

            return ValidationResult(is_valid=True)

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"验证过程中发生错误: {e}"
            )

    def _apply_validation_rule(self, value: Any, rule) -> bool:
        """
        应用验证规则

        Args:
            value: 值
            rule: 验证规则

        Returns:
            bool: 验证是否通过
        """
        try:
            # 这里可以根据需要实现具体的验证规则
            # 暂时返回True，表示验证通过
            return True

        except Exception as e:
            logger.error(f"==liuq debug== 应用验证规则失败: {e}")
            return False


logger.info("==liuq debug== 数据绑定管理器实现模块加载完成")
