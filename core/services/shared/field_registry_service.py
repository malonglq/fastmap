#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字段注册服务实现
==liuq debug== FastMapV2 字段注册系统核心实现

{{CHENGQI:
Action: Added; Timestamp: 2025-07-28 10:45:00 +08:00; Reason: P1-LD-004 实现字段注册系统; Principle_Applied: SOLID-S单一职责原则;
}}

作者: 龙sir团队
创建时间: 2025-07-28
版本: 2.0.0
描述: 字段注册系统的具体实现，支持动态字段管理
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Set, Callable
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from core.interfaces.field_definition_provider import (
    FieldDefinitionProvider,
    FieldGroup,
    FieldRegistrationResult
)
from core.interfaces.xml_field_definition import (
    XMLFieldDefinition,
    FieldType,
    ValidationRule,
    ValidationRuleType,
    CommonValidationRules
)
from core.models.map_data import (
    XML_FIELD_CONFIG, XMLFieldNodeType, XMLFieldDataType
)

logger = logging.getLogger(__name__)


class FieldRegistryService(FieldDefinitionProvider):
    """
    字段注册服务实现

    采用单例模式的字段注册中心，负责管理所有XML字段定义。
    提供字段注册、查询、分组、导入导出等功能。

    设计特点：
    - 单例模式确保全局唯一的字段注册表
    - 支持字段的动态注册和注销
    - 提供完整的字段生命周期管理
    - 支持字段配置的持久化存储
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化字段注册服务"""
        if not self._initialized:
            # 字段存储
            self._fields: Dict[str, XMLFieldDefinition] = {}
            self._groups: Dict[FieldGroup, List[str]] = defaultdict(list)
            self._visible_fields: Set[str] = set()
            self._editable_fields: Set[str] = set()

            # 回调管理
            self._change_callbacks: Dict[str, Callable[[str, str], None]] = {}

            # 统计信息
            self._statistics = {
                'total_fields': 0,
                'visible_fields': 0,
                'editable_fields': 0,
                'group_counts': defaultdict(int),
                'type_counts': defaultdict(int)
            }

            # 初始化预定义字段
            self._register_predefined_fields()

            FieldRegistryService._initialized = True
            logger.info("==liuq debug== 字段注册服务初始化完成")

    def register_field(self, field_definition: XMLFieldDefinition,
                      override: bool = False) -> FieldRegistrationResult:
        """
        注册字段定义

        Args:
            field_definition: 字段定义对象
            override: 是否覆盖已存在的字段

        Returns:
            FieldRegistrationResult: 注册结果
        """
        try:
            field_id = field_definition.field_id

            # 验证字段定义
            validation_errors = self.validate_field_definition(field_definition)
            if validation_errors:
                return FieldRegistrationResult(
                    success=False,
                    field_id=field_id,
                    message=f"字段定义验证失败: {'; '.join(validation_errors)}",
                    conflicts=[],
                    warnings=validation_errors
                )

            # 检查字段ID是否已存在
            conflicts = []
            if field_id in self._fields:
                if not override:
                    return FieldRegistrationResult(
                        success=False,
                        field_id=field_id,
                        message=f"字段ID已存在: {field_id}",
                        conflicts=[field_id],
                        warnings=[]
                    )
                else:
                    conflicts.append(field_id)
                    logger.warning(f"==liuq debug== 覆盖已存在的字段: {field_id}")

            # 注册字段
            self._fields[field_id] = field_definition

            # 更新分组
            try:
                group = FieldGroup(field_definition.group)
            except ValueError:
                group = FieldGroup.CUSTOM
                # 注释掉不相关的日志：logger.warning(f"==liuq debug== 未知字段分组 {field_definition.group}，使用CUSTOM")

            if field_id not in self._groups[group]:
                self._groups[group].append(field_id)

            # 更新可见性和可编辑性集合
            if field_definition.is_visible:
                self._visible_fields.add(field_id)
            else:
                self._visible_fields.discard(field_id)

            if field_definition.is_editable:
                self._editable_fields.add(field_id)
            else:
                self._editable_fields.discard(field_id)

            # 更新统计信息
            self._update_statistics()

            # 触发变化回调
            self._trigger_change_callbacks(field_id, "registered")

            logger.info(f"==liuq debug== 字段注册成功: {field_id} -> 分组: {group.value}")

            return FieldRegistrationResult(
                success=True,
                field_id=field_id,
                message="字段注册成功",
                conflicts=conflicts,
                warnings=[]
            )

        except Exception as e:
            error_msg = f"字段注册失败: {e}"
            logger.error(f"==liuq debug== {error_msg}")
            return FieldRegistrationResult(
                success=False,
                field_id=field_definition.field_id,
                message=error_msg,
                conflicts=[],
                warnings=[]
            )

    def unregister_field(self, field_id: str) -> bool:
        """
        注销字段定义

        Args:
            field_id: 字段ID

        Returns:
            bool: 注销是否成功
        """
        try:
            if field_id not in self._fields:
                logger.warning(f"==liuq debug== 尝试注销不存在的字段: {field_id}")
                return False

            # 移除字段
            field_def = self._fields.pop(field_id)

            # 从分组中移除
            try:
                group = FieldGroup(field_def.group)
                if field_id in self._groups[group]:
                    self._groups[group].remove(field_id)
            except ValueError:
                pass

            # 从可见性和可编辑性集合中移除
            self._visible_fields.discard(field_id)
            self._editable_fields.discard(field_id)

            # 更新统计信息
            self._update_statistics()

            # 触发变化回调
            self._trigger_change_callbacks(field_id, "unregistered")

            logger.info(f"==liuq debug== 字段注销成功: {field_id}")
            return True

        except Exception as e:
            logger.error(f"==liuq debug== 字段注销失败: {field_id}, {e}")
            return False

    def get_field(self, field_id: str) -> Optional[XMLFieldDefinition]:
        """
        获取字段定义

        Args:
            field_id: 字段ID

        Returns:
            Optional[XMLFieldDefinition]: 字段定义对象，不存在则返回None
        """
        return self._fields.get(field_id)

    def get_all_fields(self) -> List[XMLFieldDefinition]:
        """
        获取所有字段定义

        Returns:
            List[XMLFieldDefinition]: 所有字段定义列表
        """
        return list(self._fields.values())

    def get_fields_by_group(self, group: FieldGroup) -> List[XMLFieldDefinition]:
        """
        根据分组获取字段定义

        Args:
            group: 字段分组

        Returns:
            List[XMLFieldDefinition]: 指定分组的字段定义列表
        """
        field_ids = self._groups.get(group, [])
        return [self._fields[field_id] for field_id in field_ids if field_id in self._fields]

    def get_visible_fields(self) -> List[XMLFieldDefinition]:
        """
        获取可见字段定义

        Returns:
            List[XMLFieldDefinition]: 可见字段定义列表
        """
        return [self._fields[field_id] for field_id in self._visible_fields
                if field_id in self._fields]

    def get_editable_fields(self) -> List[XMLFieldDefinition]:
        """
        获取可编辑字段定义

        Returns:
            List[XMLFieldDefinition]: 可编辑字段定义列表
        """
        return [self._fields[field_id] for field_id in self._editable_fields
                if field_id in self._fields]

    def set_field_visibility(self, field_id: str, visible: bool) -> bool:
        """
        设置字段可见性

        Args:
            field_id: 字段ID
            visible: 是否可见

        Returns:
            bool: 设置是否成功
        """
        if field_id not in self._fields:
            return False

        self._fields[field_id].is_visible = visible

        if visible:
            self._visible_fields.add(field_id)
        else:
            self._visible_fields.discard(field_id)

        self._update_statistics()
        self._trigger_change_callbacks(field_id, "visibility_changed")


        return True

    def set_field_editability(self, field_id: str, editable: bool) -> bool:
        """
        设置字段可编辑性

        Args:
            field_id: 字段ID
            editable: 是否可编辑

        Returns:
            bool: 设置是否成功
        """
        if field_id not in self._fields:
            return False

        self._fields[field_id].is_editable = editable

        if editable:
            self._editable_fields.add(field_id)
        else:
            self._editable_fields.discard(field_id)

        self._update_statistics()
        self._trigger_change_callbacks(field_id, "editability_changed")


        return True

    def get_field_groups(self) -> List[FieldGroup]:
        """
        获取所有字段分组

        Returns:
            List[FieldGroup]: 字段分组列表
        """
        return [group for group in FieldGroup if self._groups[group]]

    def get_fields_by_type(self, field_type: FieldType) -> List[XMLFieldDefinition]:
        """
        根据字段类型获取字段定义

        Args:
            field_type: 字段类型

        Returns:
            List[XMLFieldDefinition]: 指定类型的字段定义列表
        """
        return [field_def for field_def in self._fields.values()
                if field_def.field_type == field_type]

    def validate_field_definition(self, field_definition: XMLFieldDefinition) -> List[str]:
        """
        验证字段定义的有效性

        Args:
            field_definition: 字段定义对象

        Returns:
            List[str]: 验证错误信息列表，空列表表示验证通过
        """
        errors = []

        # 验证必填字段
        if not field_definition.field_id:
            errors.append("字段ID不能为空")

        if not field_definition.display_name:
            errors.append("显示名称不能为空")

        if not field_definition.xml_path:
            errors.append("XML路径不能为空")

        # 验证字段ID格式
        if field_definition.field_id and not field_definition.field_id.replace('_', '').isalnum():
            errors.append("字段ID只能包含字母、数字和下划线")

        # 验证XML路径格式
        if field_definition.xml_path and not field_definition.xml_path.startswith('.//'):
            errors.append("XML路径必须以'.//开头")

        return errors

    def export_field_definitions(self, file_path: str, groups: Optional[List[FieldGroup]] = None) -> bool:
        """
        导出字段定义到文件

        Args:
            file_path: 导出文件路径
            groups: 要导出的字段分组，None表示导出所有

        Returns:
            bool: 导出是否成功
        """
        try:
            # 确定要导出的字段
            if groups is None:
                fields_to_export = list(self._fields.values())
            else:
                fields_to_export = []
                for group in groups:
                    fields_to_export.extend(self.get_fields_by_group(group))

            # 转换为可序列化的格式
            export_data = {
                'version': '2.0.0',
                'export_time': datetime.now().isoformat(),
                'total_fields': len(fields_to_export),
                'fields': []
            }

            for field_def in fields_to_export:
                field_data = {
                    'field_id': field_def.field_id,
                    'display_name': field_def.display_name,
                    'field_type': field_def.field_type.value,
                    'xml_path': field_def.xml_path,
                    'default_value': field_def.default_value,
                    'is_editable': field_def.is_editable,
                    'is_visible': field_def.is_visible,
                    'group': field_def.group,
                    'description': field_def.description,
                    'custom_editor': field_def.custom_editor,
                    'sort_order': field_def.sort_order,
                    'width_hint': field_def.width_hint,
                    'tooltip': field_def.tooltip,
                    'placeholder': field_def.placeholder,
                    'format_string': field_def.format_string,
                    'enum_values': field_def.enum_values,
                    'metadata': field_def.metadata,
                    'validation_rules': [
                        {
                            'rule_type': rule.rule_type.value,
                            'value': rule.value,
                            'error_message': rule.error_message
                        }
                        for rule in field_def.validation_rules
                    ]
                }
                export_data['fields'].append(field_data)

            # 写入文件
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"==liuq debug== 字段定义导出成功: {file_path}, 共 {len(fields_to_export)} 个字段")
            return True

        except Exception as e:
            logger.error(f"==liuq debug== 字段定义导出失败: {e}")
            return False

    def import_field_definitions(self, file_path: str, override: bool = False) -> Dict[str, Any]:
        """
        从文件导入字段定义

        Args:
            file_path: 导入文件路径
            override: 是否覆盖已存在的字段

        Returns:
            Dict[str, Any]: 导入结果，包含成功数量、失败数量、错误信息等
        """
        result = {
            'success_count': 0,
            'failure_count': 0,
            'total_count': 0,
            'errors': [],
            'warnings': []
        }

        try:
            if not Path(file_path).exists():
                result['errors'].append(f"导入文件不存在: {file_path}")
                return result

            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            fields_data = import_data.get('fields', [])
            result['total_count'] = len(fields_data)

            for field_data in fields_data:
                try:
                    # 重建验证规则
                    validation_rules = []
                    for rule_data in field_data.get('validation_rules', []):
                        rule = ValidationRule(
                            rule_type=ValidationRuleType(rule_data['rule_type']),
                            value=rule_data.get('value'),
                            error_message=rule_data.get('error_message', '')
                        )
                        validation_rules.append(rule)

                    # 创建字段定义
                    field_def = XMLFieldDefinition(
                        field_id=field_data['field_id'],
                        display_name=field_data['display_name'],
                        field_type=FieldType(field_data['field_type']),
                        xml_path=field_data['xml_path'],
                        default_value=field_data.get('default_value'),
                        validation_rules=validation_rules,
                        is_editable=field_data.get('is_editable', True),
                        is_visible=field_data.get('is_visible', True),
                        group=field_data.get('group', 'default'),
                        description=field_data.get('description', ''),
                        custom_editor=field_data.get('custom_editor'),
                        sort_order=field_data.get('sort_order', 0),
                        width_hint=field_data.get('width_hint', 100),
                        tooltip=field_data.get('tooltip', ''),
                        placeholder=field_data.get('placeholder', ''),
                        format_string=field_data.get('format_string', ''),
                        enum_values=field_data.get('enum_values', []),
                        metadata=field_data.get('metadata', {})
                    )

                    # 注册字段
                    reg_result = self.register_field(field_def, override)
                    if reg_result.success:
                        result['success_count'] += 1
                        if reg_result.conflicts:
                            result['warnings'].append(f"字段 {field_def.field_id} 已覆盖")
                    else:
                        result['failure_count'] += 1
                        result['errors'].append(f"字段 {field_def.field_id} 导入失败: {reg_result.message}")

                except Exception as e:
                    result['failure_count'] += 1
                    result['errors'].append(f"字段数据解析失败: {e}")

            logger.info(f"==liuq debug== 字段定义导入完成: 成功 {result['success_count']}, 失败 {result['failure_count']}")
            return result

        except Exception as e:
            result['errors'].append(f"导入文件解析失败: {e}")
            logger.error(f"==liuq debug== 字段定义导入失败: {e}")
            return result

    def register_field_change_callback(self, callback: Callable[[str, str], None]) -> str:
        """
        注册字段变化回调函数

        Args:
            callback: 回调函数，参数为(field_id, change_type)

        Returns:
            str: 回调ID，用于后续注销
        """
        callback_id = str(uuid.uuid4())
        self._change_callbacks[callback_id] = callback

        return callback_id

    def unregister_field_change_callback(self, callback_id: str) -> bool:
        """
        注销字段变化回调函数

        Args:
            callback_id: 回调ID

        Returns:
            bool: 注销是否成功
        """
        if callback_id in self._change_callbacks:
            del self._change_callbacks[callback_id]

            return True
        return False

    def clear_all_fields(self, confirm: bool = False) -> bool:
        """
        清空所有字段定义（危险操作）

        Args:
            confirm: 确认执行危险操作

        Returns:
            bool: 清空是否成功
        """
        if not confirm:
            logger.warning("==liuq debug== 清空所有字段需要确认参数")
            return False

        try:
            field_count = len(self._fields)
            self._fields.clear()
            self._groups.clear()
            self._visible_fields.clear()
            self._editable_fields.clear()

            self._update_statistics()

            # 触发变化回调
            for callback in self._change_callbacks.values():
                try:
                    callback("*", "all_cleared")
                except Exception as e:
                    logger.warning(f"==liuq debug== 回调执行失败: {e}")

            logger.warning(f"==liuq debug== 已清空所有字段定义，共 {field_count} 个字段")
            return True

        except Exception as e:
            logger.error(f"==liuq debug== 清空字段定义失败: {e}")
            return False

    def get_field_statistics(self) -> Dict[str, Any]:
        """
        获取字段统计信息

        Returns:
            Dict[str, Any]: 统计信息，包含总数、分组统计、类型统计等
        """
        return dict(self._statistics)

    def _update_statistics(self):
        """更新统计信息"""
        self._statistics['total_fields'] = len(self._fields)
        self._statistics['visible_fields'] = len(self._visible_fields)
        self._statistics['editable_fields'] = len(self._editable_fields)

        # 重置计数器
        self._statistics['group_counts'].clear()
        self._statistics['type_counts'].clear()

        # 重新计算分组和类型统计
        for field_def in self._fields.values():
            self._statistics['group_counts'][field_def.group] += 1
            self._statistics['type_counts'][field_def.field_type.value] += 1

    def _trigger_change_callbacks(self, field_id: str, change_type: str):
        """触发字段变化回调"""
        for callback in self._change_callbacks.values():
            try:
                callback(field_id, change_type)
            except Exception as e:
                logger.warning(f"==liuq debug== 字段变化回调执行失败: {e}")

    def _register_predefined_fields(self):
        """
        注册预定义字段（重构版本 - 集成XML_FIELD_CONFIG）

        {{CHENGQI:
        Action: Modified; Timestamp: 2025-08-04 18:30:00 +08:00; Reason: 添加核心字段标记，解决40列问题; Principle_Applied: 动态配置原则;
        }}
        """
        # 定义核心字段列表（原始40列）
        core_field_ids = {
            'alias_name', 'offset_x', 'offset_y', 'weight', 'trans_step',
            'e_ratio_min', 'e_ratio_max', 'tran_bv_min', 'bv_min', 'bv_max', 'tran_bv_max',
            'tran_ctemp_min', 'ctemp_min', 'ctemp_max', 'tran_ctemp_max',
            'tran_ir_min', 'ir_min', 'ir_max', 'tran_ir_max',
            'tran_ac_min', 'ac_min', 'ac_max', 'tran_ac_max',
            'tran_count_min', 'count_min', 'count_max', 'tran_count_max',
            'tran_color_cct_min', 'color_cct_min', 'color_cct_max', 'tran_color_cct_max',
            'tran_diff_ctemp_min', 'diff_ctemp_min', 'diff_ctemp_max', 'tran_diff_ctemp_max',
            'tran_face_ctemp_min', 'face_ctemp_min', 'face_ctemp_max', 'tran_face_ctemp_max',
            'ml'
        }
        # 基础字段组（保持原有的基础字段）
        basic_fields = [
            XMLFieldDefinition(
                field_id="alias_name",
                display_name="MapList",
                field_type=FieldType.STRING,
                xml_path=".//AliasName",
                default_value="",
                validation_rules=[CommonValidationRules.alias_name_pattern()],
                group="basic",
                sort_order=0,
                width_hint=120,
                tooltip="Map点的别名标识",
                is_core_field=True  # 核心字段
            ),
            XMLFieldDefinition(
                field_id="x",
                display_name="X坐标",
                field_type=FieldType.FLOAT,
                xml_path=".//x",
                default_value=0.0,
                validation_rules=[CommonValidationRules.required()],
                group="basic",
                sort_order=2,
                width_hint=100,
                tooltip="X轴坐标值",
                is_core_field=False  # 非核心字段
            ),
            XMLFieldDefinition(
                field_id="y",
                display_name="Y坐标",
                field_type=FieldType.FLOAT,
                xml_path=".//y",
                default_value=0.0,
                validation_rules=[CommonValidationRules.required()],
                group="basic",
                sort_order=3,
                width_hint=100,
                tooltip="Y轴坐标值",
                is_core_field=False  # 非核心字段
            ),
            XMLFieldDefinition(
                field_id="weight",
                display_name="Weight",
                field_type=FieldType.FLOAT,
                xml_path=".//weight",
                default_value=1.0,
                validation_rules=[CommonValidationRules.positive_number()],
                group="basic",
                sort_order=3,
                width_hint=80,
                tooltip="Map点的权重值",
                is_core_field=True  # 核心字段
            ),
            XMLFieldDefinition(
                field_id="trans_step",
                display_name="Step",
                field_type=FieldType.INTEGER,
                xml_path=".//TransStep",
                default_value=0,
                group="basic",
                sort_order=4,
                width_hint=60,
                tooltip="转换步长值",
                is_core_field=True  # 核心字段
            )
        ]

        # 从XML_FIELD_CONFIG生成字段定义
        xml_config_fields = self._create_fields_from_xml_config(core_field_ids)

        # 范围字段组（保持原有的复合范围字段）
        range_fields = [
            XMLFieldDefinition(
                field_id="bv_range",
                display_name="BV范围",
                field_type=FieldType.RANGE,
                xml_path=".//bv_range",
                default_value=(0.0, 100.0),
                group="ranges",
                sort_order=10,
                width_hint=120,
                tooltip="BV值的有效范围",
                is_core_field=False  # 非核心字段
            ),
            XMLFieldDefinition(
                field_id="ir_range",
                display_name="IR范围",
                field_type=FieldType.RANGE,
                xml_path=".//ir_range",
                default_value=(0.0, 100.0),
                group="ranges",
                sort_order=11,
                width_hint=120,
                tooltip="IR值的有效范围",
                is_core_field=False  # 非核心字段
            ),
            XMLFieldDefinition(
                field_id="cct_range",
                display_name="CCT范围",
                field_type=FieldType.RANGE,
                xml_path=".//cct_range",
                default_value=(2000.0, 10000.0),
                group="ranges",
                sort_order=12,
                width_hint=120,
                tooltip="CCT值的有效范围",
                is_core_field=False  # 非核心字段
            )
        ]

        # 高级字段组
        advanced_fields = [
            XMLFieldDefinition(
                field_id="detect_flag",
                display_name="检测标志",
                field_type=FieldType.INTEGER,
                xml_path=".//DetectMapFlag",
                default_value=1,
                validation_rules=CommonValidationRules.range_value(0, 1),
                group="advanced",
                sort_order=20,
                width_hint=80,
                tooltip="检测标志，0=禁用，1=启用",
                is_core_field=False  # 非核心字段
            )
        ]

        # 批量注册所有字段
        # 计算字段组：新增计算列 - 跨越色温段（仅显示用）
        computed_fields = [
            XMLFieldDefinition(
                field_id="temperature_span_names",
                display_name="跨越色温段",
                field_type=FieldType.STRING,
                xml_path=".//_computed/temperature_span_names",
                default_value="",
                is_editable=False,
                is_visible=True,
                group="analysis",
                sort_order=200,
                width_hint=200,
                tooltip="该Map点与哪些色温段扇区有交集（近似判定）",
                is_core_field=False
            )
        ]

        # 批量注册所有字段
        all_fields = basic_fields + xml_config_fields + range_fields + advanced_fields + computed_fields

        # 汇总字段（包含计算字段）
        all_fields = basic_fields + xml_config_fields + range_fields + advanced_fields + computed_fields

        for field_def in all_fields:
            result = self.register_field(field_def, override=True)
            if not result.success:
                logger.warning(f"==liuq debug== 预定义字段注册失败: {field_def.field_id}")

        logger.info(f"==liuq debug== 预定义字段注册完成，共注册 {len(all_fields)} 个字段（包含 {len(xml_config_fields)} 个XML配置字段）")

    def _create_fields_from_xml_config(self, core_field_ids: set) -> List[XMLFieldDefinition]:
        """
        从XML_FIELD_CONFIG创建字段定义

        Args:
            core_field_ids: 核心字段ID集合

        Returns:
            List[XMLFieldDefinition]: 从XML配置生成的字段定义列表
        """
        xml_fields = []
        sort_order_base = 100  # 从100开始，避免与基础字段冲突

        for field_name, config in XML_FIELD_CONFIG.items():
            try:
                # 确定字段类型
                if config.data_type == XMLFieldDataType.DOUBLE:
                    field_type = FieldType.FLOAT
                elif config.data_type in [XMLFieldDataType.UINT, XMLFieldDataType.INT]:
                    field_type = FieldType.INTEGER
                else:
                    field_type = FieldType.FLOAT  # 默认为浮点数

                # 构建XML路径
                if config.node_type == XMLFieldNodeType.OFFSET:
                    xml_path = f".//offset/{config.xml_path[0]}"
                elif config.node_type == XMLFieldNodeType.RANGE:
                    if len(config.xml_path) == 1:
                        xml_path = f".//range/{config.xml_path[0]}"
                    elif len(config.xml_path) == 2:
                        xml_path = f".//range/{config.xml_path[0]}/{config.xml_path[1]}"
                    else:
                        xml_path = f".//range/{'/'.join(config.xml_path)}"
                else:
                    xml_path = f".//{'/'.join(config.xml_path)}"

                # 确定字段分组
                if config.is_tran_field:
                    group = "tran_fields"
                elif config.node_type == XMLFieldNodeType.OFFSET:
                    group = "basic"
                else:
                    group = "ranges"

                # 生成显示名称
                display_name = self._generate_display_name(field_name)

                # 为核心字段设置正确的sort_order
                if field_name in core_field_ids:
                    # 核心字段的排序顺序（与原始40列一致）
                    core_field_order = {
                        'alias_name': 0, 'offset_x': 1, 'offset_y': 2, 'weight': 3, 'trans_step': 4,
                        'e_ratio_min': 5, 'e_ratio_max': 6, 'tran_bv_min': 7, 'bv_min': 8, 'bv_max': 9, 'tran_bv_max': 10,
                        'tran_ctemp_min': 11, 'ctemp_min': 12, 'ctemp_max': 13, 'tran_ctemp_max': 14,
                        'tran_ir_min': 15, 'ir_min': 16, 'ir_max': 17, 'tran_ir_max': 18,
                        'tran_ac_min': 19, 'ac_min': 20, 'ac_max': 21, 'tran_ac_max': 22,
                        'tran_count_min': 23, 'count_min': 24, 'count_max': 25, 'tran_count_max': 26,
                        'tran_color_cct_min': 27, 'color_cct_min': 28, 'color_cct_max': 29, 'tran_color_cct_max': 30,
                        'tran_diff_ctemp_min': 31, 'diff_ctemp_min': 32, 'diff_ctemp_max': 33, 'tran_diff_ctemp_max': 34,
                        'tran_face_ctemp_min': 35, 'face_ctemp_min': 36, 'face_ctemp_max': 37, 'tran_face_ctemp_max': 38,
                        'ml': 39
                    }
                    sort_order = core_field_order.get(field_name, sort_order_base + len(xml_fields))
                else:
                    sort_order = sort_order_base + len(xml_fields)

                # 创建字段定义
                field_def = XMLFieldDefinition(
                    field_id=field_name,
                    display_name=display_name,
                    field_type=field_type,
                    xml_path=xml_path,
                    default_value=config.default_value,
                    validation_rules=[],  # 可以根据需要添加验证规则
                    group=group,
                    sort_order=sort_order,
                    width_hint=100,
                    tooltip=f"{display_name}字段",
                    is_core_field=field_name in core_field_ids  # 根据核心字段列表设置
                )

                xml_fields.append(field_def)


            except Exception as e:
                logger.warning(f"==liuq debug== 创建XML配置字段失败: {field_name}, {e}")
                continue

        logger.info(f"==liuq debug== 从XML_FIELD_CONFIG创建了 {len(xml_fields)} 个字段定义")
        return xml_fields

    def _generate_display_name(self, field_name: str) -> str:
        """
        生成字段的显示名称

        Args:
            field_name: 字段名称

        Returns:
            str: 显示名称
        """
        # 字段名称映射表（与原始硬编码版本完全一致）
        name_mapping = {
            'alias_name': 'MapList',
            'offset_x': 'Offset R/G',
            'offset_y': 'Offset B/G',
            'weight': 'Weight',
            'trans_step': 'Step',
            'e_ratio_min': 'ERatio Min',
            'e_ratio_max': 'ERatio Max',
            'tran_bv_min': 'BV Lower',
            'bv_min': 'BV Min',
            'bv_max': 'BV Max',
            'tran_bv_max': 'BV Upper',
            'tran_ctemp_min': 'Ctemp Lower',
            'ctemp_min': 'Ctemp Min',
            'ctemp_max': 'Ctemp Max',
            'tran_ctemp_max': 'Ctemp Upper',
            'tran_ir_min': 'IR Lower',
            'ir_min': 'IR Min',
            'ir_max': 'IR Max',
            'tran_ir_max': 'IR Upper',
            'tran_ac_min': 'AC Lower',
            'ac_min': 'AC Min',
            'ac_max': 'AC Max',
            'tran_ac_max': 'AC Upper',
            'tran_count_min': 'COUNT Lower',
            'count_min': 'COUNT Min',
            'count_max': 'COUNT Max',
            'tran_count_max': 'COUNT Upper',
            'tran_color_cct_min': 'ColorCCT Lower',
            'color_cct_min': 'ColorCCT Min',
            'color_cct_max': 'ColorCCT Max',
            'tran_color_cct_max': 'ColorCCT Upper',
            'tran_diff_ctemp_min': 'diffCtemp Lower',
            'diff_ctemp_min': 'diffCtemp Min',
            'diff_ctemp_max': 'diffCtemp Max',
            'tran_diff_ctemp_max': 'diffCtemp Upper',
            'tran_face_ctemp_min': 'FaceCtemp Lower',
            'face_ctemp_min': 'FaceCtemp Min',
            'face_ctemp_max': 'FaceCtemp Max',
            'tran_face_ctemp_max': 'FaceCtemp Upper',
            'ml': 'ml'
        }

        return name_mapping.get(field_name, field_name.replace('_', ' ').title())


# 全局字段注册中心实例
field_registry = FieldRegistryService()

logger.info("==liuq debug== 字段注册服务模块加载完成")
