#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EXIF comparison report generator adapter."""

import logging
import difflib
from typing import Dict, List, Any, Optional, Tuple, Set, Mapping
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.interfaces.report_generator import IReportGenerator, ReportType
from core.services.reporting.engine.report_engine import EXIFReportGenerator, ReportConfig


logger = logging.getLogger(__name__)


class ExifComparisonReportGenerator(IReportGenerator):
    """Bridge legacy EXIF comparison workflows to the new reporting engine."""

    def __init__(self) -> None:
        self.generator = EXIFReportGenerator()
        self.display_names = getattr(self.generator, 'display_names', {}) or {}
        self._last_match_result: Optional[Dict[str, Any]] = None
        logger.info('==liuq debug== EXIF comparison report generator adapter initialized')

    def generate(self, data: Dict[str, Any]) -> str:
        """Generate an EXIF comparison report and return the output path."""
        try:
            self._validate_input_data(data)

            test_csv_path = data['test_csv_path']
            reference_csv_path = data['reference_csv_path']
            selected_fields = data['selected_fields']
            output_path_cfg = data.get('output_path')
            match_column = data.get('match_column') or data.get('match_method') or 'image_name'
            similarity_threshold = self._sanitize_similarity_threshold(data.get('similarity_threshold', 0.8))
            include_charts = bool(data.get('include_charts', True))
            template_name = data.get('template_name') or 'reporting/domains/exif/new_report.html'
            now = datetime.now()
            if output_path_cfg:
                output_path_obj = Path(output_path_cfg)
            else:
                output_path_obj = Path(f"output/exif_comparison_report_{now.strftime('%Y%m%d_%H%M%S')}.html")
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            shape_analysis_cfg = data.get('shape_analysis') or {}
            sort_by_similarity = bool(data.get('sort_by_similarity', True))
            shape_analysis_result: Optional[Dict[str, Any]] = None

            test_df = self._read_csv_file(test_csv_path)
            reference_df = self._read_csv_file(reference_csv_path)

            match_result = self._match_dataframes(
                test_df,
                reference_df,
                match_column=match_column,
                similarity_threshold=similarity_threshold,
            )
            self._last_match_result = match_result

            if shape_analysis_cfg.get('enabled'):
                try:
                    from core.services.reporting.domains.exif.helpers.shape_analysis import StatsShapeAnalyzer

                    analyzer = StatsShapeAnalyzer()
                    image_output_path = output_path_obj.with_name(f"{output_path_obj.stem}_shape_analysis.png")
                    analysis = analyzer.analyze(
                        test_image_path=shape_analysis_cfg.get('test_image_path'),
                        reference_image_path=shape_analysis_cfg.get('reference_image_path'),
                        output_image_path=image_output_path,
                    )
                    analysis['enabled'] = True
                    analysis['image_path'] = str(image_output_path)
                    analysis['image_filename'] = image_output_path.name
                    shape_analysis_result = analysis
                except Exception as exc:  # noqa: BLE001
                    logger.warning('==liuq debug== 统计点形状分析失败: %s', exc)
                    shape_analysis_result = {
                        'enabled': True,
                        'error': str(exc),
                        'test_image_path': shape_analysis_cfg.get('test_image_path'),
                        'reference_image_path': shape_analysis_cfg.get('reference_image_path'),
                    }
            else:
                shape_analysis_result = {
                    'enabled': False,
                    'test_image_path': shape_analysis_cfg.get('test_image_path'),
                    'reference_image_path': shape_analysis_cfg.get('reference_image_path'),
                }

            matched_pairs = match_result['pairs']
            trend_data = self._build_trend_data(selected_fields, matched_pairs)
            statistics_data = self._build_statistics(trend_data)
            kpi_metrics = self._build_kpi_metrics(trend_data)
            comparison_rows = self._build_comparison_rows(
                matched_pairs,
                selected_fields,
                sort_by_similarity=sort_by_similarity,
            )
            trend_charts = self._build_trend_chart_models(trend_data)
            integrated_trend = self._build_integrated_trend(trend_data)

            statistics_rows = [
                {
                    'field': field,
                    **stats,
                }
                for field, stats in statistics_data.items()
            ]

            field_details = [
                {
                    'name': field,
                    'display_name': self.display_names.get(field, field),
                }
                for field in selected_fields
            ]

            match_summary = {
                'total_test': match_result['total_test_records'],
                'total_reference': match_result['total_reference_records'],
                'matched_pairs': match_result['matched_pairs'],
                'unmatched_test': match_result['unmatched_test'],
                'unmatched_reference': match_result['unmatched_reference'],
                'match_rate': match_result['match_rate'],
                'match_rate_percent': match_result['match_rate'] * 100 if match_result['match_rate'] is not None else 0,
                'similarity_threshold': similarity_threshold,
            }

            report_config = ReportConfig(
                title='EXIF Comparison Analysis Report',
                output_path=str(output_path_obj),
                template_name=template_name,
                metadata={
                    'test_file': Path(test_csv_path).name,
                    'reference_file': Path(reference_csv_path).name,
                    'generation_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'match_column': match_column,
                    'match_method': match_column,
                    'selected_fields': selected_fields,
                    'selected_field_details': field_details,
                    'selected_fields_count': len(selected_fields),
                    'include_charts': include_charts,
                    'test_csv_path': test_csv_path,
                    'reference_csv_path': reference_csv_path,
                    'matched_pairs': matched_pairs,
                    'comparison_rows': comparison_rows,
                    'comparison_sorting': {
                        'enabled': sort_by_similarity,
                        'method': 'similarity',
                        'order': 'desc',
                    },
                    'statistics_data': statistics_data,
                    'statistics_rows': statistics_rows,
                    'trend_data': trend_data,
                    'data_source': trend_data,
                    'similarity_threshold': similarity_threshold,
                    'match_summary': match_summary,
                    'kpi_metrics': kpi_metrics,
                    'trend_charts': trend_charts,
                    'integrated_trend': integrated_trend,
                    'shape_analysis': shape_analysis_result,
                },
            )

            self.generator.generate_report(report_config)
            logger.info('==liuq debug== EXIF comparison report generated: %s', report_config.output_path)
            return report_config.output_path

        except Exception as exc:  # noqa: BLE001
            logger.error('==liuq debug== EXIF comparison report generation failed: %s', exc)
            raise RuntimeError(f'EXIF comparison report generation failed: {exc}') from exc

    def get_report_name(self) -> str:
        """Return the human readable report name."""
        return 'EXIF Comparison Analysis Report'

    def get_report_type(self) -> ReportType:
        """Return the report type enum value."""
        return ReportType.EXIF_COMPARISON

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate configuration data and return whether it is usable."""
        try:
            self._validate_input_data(data)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning('==liuq debug== Data validation failed: %s', exc)
            return False

    def _validate_input_data(self, data: Dict[str, Any]) -> None:
        required_fields = ['test_csv_path', 'reference_csv_path', 'selected_fields']
        for field in required_fields:
            if field not in data:
                raise ValueError(f'Missing required field: {field}')

        test_csv_path = Path(data['test_csv_path'])
        reference_csv_path = Path(data['reference_csv_path'])
        if not test_csv_path.exists():
            raise ValueError(f'Test CSV file does not exist: {test_csv_path}')
        if not reference_csv_path.exists():
            raise ValueError(f'Reference CSV file does not exist: {reference_csv_path}')

        selected_fields = data['selected_fields']
        if not isinstance(selected_fields, list) or not selected_fields:
            raise ValueError('selected_fields must be a non-empty list')

        shape_cfg = data.get('shape_analysis') or {}
        if shape_cfg.get('enabled'):
            test_image = Path(str(shape_cfg.get('test_image_path', '')).strip())
            reference_image = Path(str(shape_cfg.get('reference_image_path', '')).strip())
            if not test_image.exists():
                raise ValueError(f'Shape analysis test image does not exist: {test_image}')
            if not reference_image.exists():
                raise ValueError(f'Shape analysis reference image does not exist: {reference_image}')

    def preview_data_matching(
        self,
        test_csv_path: str,
        reference_csv_path: str,
        match_column: str = 'image_name',
        similarity_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """Preview the matching summary for the provided CSV files."""
        threshold = self._sanitize_similarity_threshold(similarity_threshold)
        test_df = self._read_csv_file(test_csv_path)
        reference_df = self._read_csv_file(reference_csv_path)

        match_result = self._match_dataframes(
            test_df,
            reference_df,
            match_column=match_column,
            similarity_threshold=threshold,
        )
        self._last_match_result = match_result

        sample_matches: List[Dict[str, Any]] = []
        sorted_pairs = sorted(
            match_result['pairs'],
            key=lambda item: float(item.get('similarity', 0.0) or 0.0),
            reverse=True,
        )
        for pair in sorted_pairs[:10]:
            sample_matches.append(
                {
                    'test_name': pair.get('filename1') or pair.get('match_value', ''),
                    'reference_name': pair.get('filename2') or pair.get('reference_value', ''),
                    'similarity': pair.get('similarity', 0.0),
                }
            )

        preview = {
            'total_test_records': match_result['total_test_records'],
            'total_reference_records': match_result['total_reference_records'],
            'matched_pairs': match_result['matched_pairs'],
            'unmatched_test': match_result['unmatched_test'],
            'unmatched_reference': match_result['unmatched_reference'],
            'match_rate': match_result['match_rate'],
            'sample_matches': sample_matches,
            'pairs': match_result['pairs'],
        }
        logger.info('==liuq debug== Matching preview ready: %s pairs', match_result['matched_pairs'])
        return preview

    def get_supported_fields(self, csv_path: str) -> Dict[str, Any]:
        """Inspect a CSV file and describe available fields."""
        df = self._read_csv_file(csv_path)
        all_fields = []
        numeric_fields = []

        for column in df.columns:
            series = df[column]
            non_null_count = int(series.notna().sum())
            numeric_series = pd.to_numeric(series, errors='coerce')
            is_numeric = numeric_series.notna().any()
            info = {
                'name': column,
                'display_name': self.display_names.get(column, column),
                'dtype': str(series.dtype),
                'is_numeric': bool(is_numeric),
                'non_null_count': non_null_count,
                'sample_values': [str(v) for v in series.dropna().head(3).tolist()],
            }
            if is_numeric:
                numeric_values = numeric_series.dropna()
                if not numeric_values.empty:
                    info['min_value'] = float(numeric_values.min())
                    info['max_value'] = float(numeric_values.max())
                numeric_fields.append(info)
            all_fields.append(info)

        total_fields = len(df.columns)
        numeric_field_count = len(numeric_fields)
        columns = list(df.columns)
        return {
            'available_fields': columns,
            'fields': columns,
            'original_columns': columns,
            'field_count': total_fields,
            'total_fields': total_fields,
            'numeric_field_count': numeric_field_count,
            'row_count': len(df),
            'numeric_fields': numeric_fields,
            'all_fields_detailed': all_fields,
            'sample_data': df.head(3).to_dict('records'),
        }

    def preview_report_scope(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide a lightweight preview for the report scope."""
        test_info = self.get_supported_fields(data['test_csv_path'])
        reference_info = self.get_supported_fields(data['reference_csv_path'])
        preview = {
            'test_file': Path(data['test_csv_path']).name,
            'reference_file': Path(data['reference_csv_path']).name,
            'selected_fields': data.get('selected_fields', []),
            'test_field_count': test_info['field_count'],
            'reference_field_count': reference_info['field_count'],
            'test_row_count': test_info['row_count'],
            'reference_row_count': reference_info['row_count'],
            'estimated_processing_time': self._estimate_processing_time(
                test_info['row_count'], reference_info['row_count']
            ),
            'output_sections': [
                'Overview',
                'KPI Cards',
                'Data Comparison',
                'Trend Analysis',
                'Statistics',
                'Anomaly Review',
            ],
        }
        logger.info('==liuq debug== Report scope preview computed')
        return preview

    def _estimate_processing_time(self, test_rows: int, reference_rows: int) -> str:
        total_rows = test_rows + reference_rows
        if total_rows <= 100:
            return '1-3s'
        if total_rows <= 1000:
            return '3-10s'
        if total_rows <= 10000:
            return '10-30s'
        return '30s+'

    def get_supported_templates(self) -> List[str]:
        """Return the list of supported report templates."""
        return [
            'reporting/domains/exif/new_report.html',
        ]

    def get_default_template(self) -> str:
        """Return the default template path."""
        return 'reporting/domains/exif/new_report.html'

    def _read_csv_file(self, file_path: str, encoding: Optional[str] = None) -> pd.DataFrame:
        encodings = []
        if encoding:
            encodings.append(encoding)
        encodings.extend(['utf-8-sig', 'utf-8', 'gbk', 'gb18030'])

        last_error: Optional[Exception] = None
        for enc in encodings:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                logger.info('==liuq debug== CSV loaded: %s rows=%s cols=%s', file_path, len(df), len(df.columns))
                return df
            except UnicodeDecodeError as decode_error:
                last_error = decode_error
                continue
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                break
        raise RuntimeError(f'Failed to read CSV file {file_path}: {last_error}')

    def _match_dataframes(
        self,
        test_df: pd.DataFrame,
        reference_df: pd.DataFrame,
        match_column: str,
        similarity_threshold: float,
    ) -> Dict[str, Any]:
        if match_column not in test_df.columns:
            raise ValueError(f'Matching column missing from test data: {match_column}')
        if match_column not in reference_df.columns:
            raise ValueError(f'Matching column missing from reference data: {match_column}')

        threshold = self._sanitize_similarity_threshold(similarity_threshold)
        test_values = [self._normalize_match_value(v) for v in test_df[match_column].tolist()]
        reference_values = [self._normalize_match_value(v) for v in reference_df[match_column].tolist()]

        reference_map: Dict[str, List[int]] = {}
        for idx, value in enumerate(reference_values):
            if not value:
                continue
            reference_map.setdefault(value.lower(), []).append(idx)

        used_reference: Set[int] = set()
        pairs: List[Dict[str, Any]] = []
        unmatched_test = 0

        # 优先尝试按文件名中的数字编号进行一一配对（例如 190_xxx.jpg ↔ 190_xxx.jpg）
        def extract_numeric_id(text: str) -> Optional[str]:
            if not text:
                return None
            import re
            m = re.search(r"(?<!\d)(\d{2,})(?!\d)", text)
            return m.group(1) if m else None

        test_ids = [extract_numeric_id(v) for v in test_values]
        ref_ids = [extract_numeric_id(v) for v in reference_values]
        ref_id_map: Dict[str, List[int]] = {}
        for idx, rid in enumerate(ref_ids):
            if not rid:
                continue
            ref_id_map.setdefault(rid, []).append(idx)

        for test_idx, value in enumerate(test_values):
            if not value:
                unmatched_test += 1
                continue

            normalized = value.lower()
            ref_idx: Optional[int] = None
            similarity = 0.0

            # Step 1: 数字编号精确配对（不改变原有列名匹配逻辑，只是优先匹配）
            t_id = test_ids[test_idx]
            if t_id and t_id in ref_id_map:
                # 找到第一个尚未使用的参考索引
                for candidate in ref_id_map[t_id]:
                    if candidate not in used_reference:
                        ref_idx = candidate
                        similarity = 1.0
                        break

            for candidate in reference_map.get(normalized, []):
                if candidate not in used_reference:
                    ref_idx = candidate
                    similarity = 1.0
                    break

            if ref_idx is None and threshold < 1.0:
                ref_idx, similarity = self._find_best_fuzzy_match(value, reference_values, used_reference)
                if similarity < threshold:
                    ref_idx = None

            if ref_idx is None:
                unmatched_test += 1
                continue

            used_reference.add(ref_idx)
            test_row = test_df.iloc[test_idx]
            reference_row = reference_df.iloc[ref_idx]
            test_data = test_row.to_dict()
            reference_data = reference_row.to_dict()
            sequence_value = (
                self._extract_sequence_value(test_row)
                or self._extract_sequence_value(reference_row)
                or t_id
                or test_idx
            )
            pair = {
                'test_index': int(test_idx),
                'reference_index': int(ref_idx),
                'match_column': match_column,
                'match_value': value,
                'reference_value': reference_values[ref_idx],
                'similarity': float(round(similarity, 4)),
                'test_data': test_data,
                'reference_data': reference_data,
                'filename1': self._extract_display_name(test_row, match_column),
                'filename2': self._extract_display_name(reference_row, match_column),
                'test': self._extract_display_name(test_row, match_column),
                'reference': self._extract_display_name(reference_row, match_column),
                'match_score': float(round(similarity, 4)),
                'sequence_number': self._coerce_sequence_label(sequence_value),
                'pair_numeric_id': t_id,
            }
            pairs.append(pair)

        total_test = len(test_df)
        total_reference = len(reference_df)
        matched_pairs = len(pairs)
        unmatched_reference = total_reference - len(used_reference)
        match_rate = matched_pairs / total_test if total_test else 0.0

        return {
            'pairs': pairs,
            'total_test_records': total_test,
            'total_reference_records': total_reference,
            'matched_pairs': matched_pairs,
            'unmatched_test': unmatched_test,
            'unmatched_reference': max(unmatched_reference, 0),
            'match_rate': match_rate,
            'match_column': match_column,
            'similarity_threshold': threshold,
        }

    def _find_best_fuzzy_match(
        self,
        value: str,
        reference_values: List[str],
        used_reference: Set[int],
    ) -> Tuple[Optional[int], float]:
        best_idx: Optional[int] = None
        best_similarity = 0.0
        for idx, candidate in enumerate(reference_values):
            if idx in used_reference or not candidate:
                continue
            similarity = difflib.SequenceMatcher(None, value, candidate).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_idx = idx
                if best_similarity >= 0.9999:
                    break
        return best_idx, best_similarity

    @staticmethod
    def _normalize_match_value(value: Any) -> str:
        if value is None:
            return ''
        if isinstance(value, float) and pd.isna(value):
            return ''
        return str(value).strip()

    @staticmethod
    def _extract_display_name(row: pd.Series, match_column: str) -> str:
        candidates = ['image_name', 'file_name', 'filename', 'name', 'image_path']
        for column in candidates:
            if column in row and pd.notna(row[column]):
                text = str(row[column]).strip()
                if text:
                    return text
        fallback = row.get(match_column)
        return '' if (isinstance(fallback, float) and pd.isna(fallback)) else str(fallback or '').strip()

    @staticmethod
    def _extract_sequence_value(row: Mapping[str, Any]) -> Optional[Any]:
        candidates = [
            'sequence_number',
            'sequence',
            'seq',
            'frame_index',
            'frame_id',
            'index',
            'image_index',
        ]
        for column in candidates:
            value: Any = None
            if isinstance(row, pd.Series):
                if column in row and pd.notna(row[column]):
                    value = row[column]
            else:
                if column in row:
                    candidate = row[column]
                    if candidate is not None and (not isinstance(candidate, float) or not pd.isna(candidate)):
                        value = candidate
            if value is None:
                continue
            if isinstance(value, float) and pd.isna(value):
                continue
            return value
        return None

    @staticmethod
    def _coerce_sequence_label(value: Any) -> str:
        if value is None:
            return ''
        if isinstance(value, float) and pd.isna(value):
            return ''
        text = str(value).strip()
        return text

    @staticmethod
    def _sanitize_similarity_threshold(value: Any) -> float:
        try:
            threshold = float(value)
        except (TypeError, ValueError):
            threshold = 0.8
        return max(0.0, min(1.0, threshold))

    @staticmethod
    def _find_first_common_column(
        test_df: pd.DataFrame,
        reference_df: pd.DataFrame,
        candidates: List[str],
    ) -> Optional[str]:
        for column in candidates:
            if column in test_df.columns and column in reference_df.columns:
                return column
        return None

    def _match_by_sequence_number(self, test_df: pd.DataFrame, reference_df: pd.DataFrame) -> Dict[str, Any]:
        """Match data using common sequence-like columns."""
        candidates = [
            'sequence_number',
            'sequence',
            'seq',
            'frame_index',
            'frame_id',
            'index',
        ]
        match_column = self._find_first_common_column(test_df, reference_df, candidates)
        if not match_column:
            fallback = ['image_name', 'filename', 'file_name']
            match_column = self._find_first_common_column(test_df, reference_df, fallback)
        if not match_column:
            raise ValueError('No common column available for sequence matching')

        result = self._match_dataframes(test_df, reference_df, match_column, similarity_threshold=1.0)
        self._last_match_result = result
        logger.info('==liuq debug== Sequence based matching complete: %s pairs', result['matched_pairs'])
        return result

    def _build_trend_data(self, selected_fields: List[str], pairs: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Any]]]:
        trend: Dict[str, Dict[str, List[Any]]] = {}
        for field in selected_fields:
            trend[field] = {
                'test_values': [],
                'reference_values': [],
                'differences': [],
                'diff_percentages': [],
                'sequence_numbers': [],
            }

        for pair in pairs:
            test_data = pair.get('test_data', {})
            reference_data = pair.get('reference_data', {})
            sequence_candidate = (
                pair.get('sequence_number')
                or self._extract_sequence_value(test_data)
                or self._extract_sequence_value(reference_data)
            )
            base_sequence_label = self._coerce_sequence_label(sequence_candidate)

            for field in selected_fields:
                test_value = self._coerce_float(test_data.get(field))
                reference_value = self._coerce_float(reference_data.get(field))
                if test_value is None or reference_value is None:
                    continue

                field_bucket = trend[field]
                field_bucket['test_values'].append(test_value)
                field_bucket['reference_values'].append(reference_value)
                diff = test_value - reference_value
                field_bucket['differences'].append(diff)

                base = reference_value if reference_value not in (0.0, 0) else (test_value if test_value not in (0.0, 0) else None)
                if base:
                    diff_pct = (diff / base) * 100
                else:
                    diff_pct = 0.0
                field_bucket['diff_percentages'].append(diff_pct)

                label = base_sequence_label or self._coerce_sequence_label(test_data.get('sequence_number'))
                if not label:
                    label = str(len(field_bucket['sequence_numbers']) + 1)
                field_bucket['sequence_numbers'].append(label)

        # 绉婚櫎娌℃湁鏈夋晥鏁版嵁鐨勫瓧娈?        trend = {field: data for field, data in trend.items() if data['test_values'] and data['reference_values']}
        return trend

    def _build_statistics(self, trend_data: Dict[str, Dict[str, List[Any]]]) -> Dict[str, Dict[str, float]]:
        stats: Dict[str, Dict[str, float]] = {}
        for field, data in trend_data.items():
            test_values = data.get('test_values', [])
            reference_values = data.get('reference_values', [])
            if not test_values or not reference_values:
                continue

            differences = data.get('differences', [])
            diff_percentages = data.get('diff_percentages', [])

            stats[field] = {
                'test_mean': float(sum(test_values) / len(test_values)),
                'ref_mean': float(sum(reference_values) / len(reference_values)),
                'test_min': float(min(test_values)),
                'test_max': float(max(test_values)),
                'ref_min': float(min(reference_values)),
                'ref_max': float(max(reference_values)),
                'mean_diff': float(sum(differences) / len(differences)) if differences else 0.0,
                'mean_diff_percentage': float(sum(diff_percentages) / len(diff_percentages)) if diff_percentages else 0.0,
            }
        return stats

    def _build_kpi_metrics(self, trend_data: Dict[str, Dict[str, List[Any]]]) -> List[Dict[str, Any]]:
        icon_map = {
            'color_sensor_irRatio': 'fas fa-eye',
            'meta_data_currentFrame_bv': 'fas fa-sun',
            'meta_data_currentFrame_iso': 'fas fa-camera',
            'meta_data_currentFrame_exposureTime': 'fas fa-clock',
            'meta_data_currentFrame_fNumber': 'fas fa-adjust',
            'meta_data_currentFrame_focalLength': 'fas fa-search',
            'default': 'fas fa-chart-bar',
        }

        metrics: List[Dict[str, Any]] = []
        for field, data in trend_data.items():
            test_values = data.get('test_values', [])
            reference_values = data.get('reference_values', [])
            if not test_values or not reference_values:
                continue

            n = min(len(test_values), len(reference_values))
            if n == 0:
                continue

            pairs = list(zip(test_values[:n], reference_values[:n]))
            diffs = [tv - rv for tv, rv in pairs]
            mae = sum(abs(d) for d in diffs) / n
            rmse = (sum(d ** 2 for d in diffs) / n) ** 0.5

            ref_mean = sum(rv for _, rv in pairs) / n
            ss_tot = sum((rv - ref_mean) ** 2 for _, rv in pairs)
            ss_res = sum((tv - rv) ** 2 for tv, rv in pairs)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot else 0.0

            diff_percentages = data.get('diff_percentages', [])
            anomaly_count = sum(1 for pct in diff_percentages if abs(pct) > 10)
            anomaly_rate = (anomaly_count / len(diff_percentages) * 100) if diff_percentages else 0.0

            if anomaly_rate < 5:
                rate_class = 'positive'
            elif anomaly_rate < 15:
                rate_class = 'warning'
            else:
                rate_class = 'negative'

            metrics.append({
                'field': field,
                'display_name': self.display_names.get(field, field),
                'icon': icon_map.get(field, icon_map['default']),
                'mae': mae,
                'rmse': rmse,
                'r2': r_squared,
                'anomaly_rate': anomaly_rate,
                'rate_class': rate_class,
            })

        metrics.sort(key=lambda item: item['anomaly_rate'], reverse=True)
        return metrics

    def _build_comparison_rows(
        self,
        matched_pairs: List[Dict[str, Any]],
        selected_fields: List[str],
        *,
        sort_by_similarity: bool = False,
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for pair in matched_pairs:
            test_data = pair.get('test_data', {})
            reference_data = pair.get('reference_data', {})

            row = {
                'filename1': pair.get('filename1') or pair.get('test') or '',
                'filename2': pair.get('filename2') or pair.get('reference') or '',
                'similarity': float(pair.get('similarity', 0.0) or 0.0),
                'cells': [],
            }

            for field in selected_fields:
                test_raw = test_data.get(field)
                ref_raw = reference_data.get(field)
                test_value = self._coerce_float(test_raw)
                ref_value = self._coerce_float(ref_raw)

                before_text = self._format_cell_value(test_value, test_raw)
                after_text = self._format_cell_value(ref_value, ref_raw)
                change_text = 'N/A'
                change_class = 'change-neutral'

                if test_value is not None and ref_value is not None:
                    denominator = test_value if test_value not in (0.0, 0) else None
                    if denominator:
                        change = (ref_value - test_value) / denominator * 100
                        change_text = f'{change:.2f}%'
                        change_class = self._classify_change(change)
                    else:
                        change_text = '0.00%'

                row['cells'].append({
                    'before': before_text,
                    'after': after_text,
                    'change_pct': change_text,
                    'change_class': change_class,
                })

            rows.append(row)

        if sort_by_similarity:
            rows.sort(
                key=lambda item: (
                    -(item.get('similarity') or 0.0),
                    str(item.get('filename1', '')),
                    str(item.get('filename2', '')),
                )
            )

        for index, row in enumerate(rows, start=1):
            row.setdefault('rank', index)

        return rows

    def _build_trend_chart_models(self, trend_data: Dict[str, Dict[str, List[Any]]]) -> List[Dict[str, Any]]:
        charts: List[Dict[str, Any]] = []
        for field, data in trend_data.items():
            charts.append({
                'field': field,
                'display_name': self.display_names.get(field, field),
                'chart_id': self._sanitize_chart_id(field),
                'sequence_numbers': data.get('sequence_numbers', []),
                'test_values': data.get('test_values', []),
                'reference_values': data.get('reference_values', []),
                'diff_percentages': data.get('diff_percentages', []),
            })
        return charts

    def _build_integrated_trend(self, trend_data: Dict[str, Dict[str, List[Any]]]) -> Dict[str, Any]:
        if not trend_data:
            return {'datasets': [], 'image_labels': [], 'image_count': 0, 'algorithm_count': 0}

        field_map = {name.lower(): name for name in trend_data.keys()}

        def resolve(field_name: str) -> Optional[str]:
            return field_map.get(field_name.lower())

        # 调整顺序：将 AGW_noMap 放在 AGW 之前
        algorithm_config = {
            'SGW': {'rpg': 'ealgo_data_SGW_gray_RpG', 'bpg': 'ealgo_data_SGW_gray_BpG', 'color': '#e91e63'},
            'AGW_noMap': {'rpg': 'ealgo_data_AGW_noMap_RpG', 'bpg': 'ealgo_data_AGW_noMap_BpG', 'color': '#00bcd4'},
            'AGW': {'rpg': 'ealgo_data_AGW_gray_RpG', 'bpg': 'ealgo_data_AGW_gray_BpG', 'color': '#3f51b5'},
            'Mix': {'rpg': 'ealgo_data_Mix_csalgo_RpG', 'bpg': 'ealgo_data_Mix_csalgo_BpG', 'color': '#4caf50'},
            'After_face': {'rpg': 'ealgo_data_After_face_RpG', 'bpg': 'ealgo_data_After_face_BpG', 'color': '#ff9800'},
            'cnvgEst': {'rpg': 'ealgo_data_cnvgEst_RpG', 'bpg': 'ealgo_data_cnvgEst_BpG', 'color': '#9c27b0'},
        }

        datasets: List[Dict[str, Any]] = []
        image_labels: List[str] = []
        image_count = 0

        for algo_name, mapping in algorithm_config.items():
            rpg_field = resolve(mapping['rpg'])
            bpg_field = resolve(mapping['bpg'])
            if not rpg_field or not bpg_field:
                continue

            rpg_bucket = trend_data.get(rpg_field, {})
            bpg_bucket = trend_data.get(bpg_field, {})

            rpg_values = rpg_bucket.get('test_values', [])
            bpg_values = bpg_bucket.get('test_values', [])
            if not rpg_values or not bpg_values or len(rpg_values) != len(bpg_values):
                continue

            if not image_labels:
                labels = rpg_bucket.get('sequence_numbers') or []
                if labels and len(labels) == len(rpg_values):
                    image_labels = [str(label) for label in labels]
                else:
                    image_labels = [f'鍥剧墖_{idx + 1:03d}' for idx in range(len(rpg_values))]
                image_count = len(image_labels)

            if not image_count:
                continue

            color_hex = mapping['color'].lstrip('#')
            r, g, b = (int(color_hex[i:i + 2], 16) for i in (0, 2, 4))

            datasets.append({
                'label': f'{algo_name}_RpG',
                'data': [float(v) for v in rpg_values[:image_count]],
                'borderColor': mapping['color'],
                'borderDash': [],
                'backgroundColor': f'rgba({r},{g},{b},0.10)',
                'tension': 0.3,
                'pointRadius': 4,
                'pointHoverRadius': 6,
                'borderWidth': 2,
                'fill': False,
            })

            datasets.append({
                'label': f'{algo_name}_BpG',
                'data': [float(v) for v in bpg_values[:image_count]],
                'borderColor': mapping['color'],
                'borderDash': [5, 5],
                'backgroundColor': f'rgba({r},{g},{b},0.05)',
                'tension': 0.3,
                'pointRadius': 4,
                'pointHoverRadius': 6,
                'borderWidth': 2,
                'fill': False,
            })

        return {
            'datasets': datasets,
            'image_labels': image_labels,
            'image_count': image_count,
            'algorithm_count': len({ds['label'].split('_', 1)[0] for ds in datasets}),
        }

    @staticmethod
    def _sanitize_chart_id(field_name: str) -> str:
        sanitized = ''.join(ch if ch.isalnum() else '_' for ch in field_name)
        return f'chart_{sanitized}'

    @staticmethod
    def _format_cell_value(numeric_value: Optional[float], raw_value: Any) -> str:
        if numeric_value is None:
            if raw_value in (None, ''):
                return 'N/A'
            return str(raw_value)
        return f'{numeric_value:.3f}'

    @staticmethod
    def _classify_change(change: float) -> str:
        # 调整颜色语义：处理后“增加”为红色，减少为绿色
        # 正值（after > before）标记为 negative 类（红色），负值标记为 positive 类（绿色）
        if change > 0:
            return 'change-negative'
        if change < 0:
            return 'change-positive'
        return 'change-neutral'

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        try:
            if value is None:
                return None
            result = float(value)
            if pd.isna(result):
                return None
            return result
        except Exception:  # noqa: BLE001
            return None

