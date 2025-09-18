#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML template service (clean, single class)
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from jinja2 import Template, Environment, BaseLoader, TemplateNotFound

logger = logging.getLogger(__name__)


class HTMLTemplateService:
    def __init__(self):
        self.templates_root = Path('templates') / 'reporting'
        self.builtin_templates = self._load_builtin_templates()
        self.custom_templates: Dict[str, str] = {}
        all_templates = {**self.builtin_templates, **self.custom_templates}
        self.environment = Environment(loader=InMemoryTemplateLoader(all_templates))
        logger.debug("HTMLTemplateService ready")

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        try:
            full_context = self._prepare_template_context(context)
            template = self.environment.get_template(template_name)
            return template.render(**full_context)
        except TemplateNotFound:
            logger.error("Template not found: %s", template_name)
            return self._get_error_template().render(
                error_message=f"模板 '{template_name}' 未找到",

                **context
            )
        except Exception as e:
            logger.error("Template render failed: %s", e)
            return self._get_error_template().render(
                error_message=f"模板渲染失败: {e}",

                **context
            )

    def register_template(self, name: str, content: str):
        self.custom_templates[name] = content
        all_templates = {**self.builtin_templates, **self.custom_templates}
        self.environment = Environment(loader=InMemoryTemplateLoader(all_templates))

    def load_template_from_file(self, file_path: Path, name: Optional[str] = None) -> str:
        template_name = name or file_path.stem
        content = file_path.read_text(encoding='utf-8')
        self.register_template(template_name, content)
        return template_name

    def get_available_templates(self) -> List[str]:
        return list(self.builtin_templates.keys()) + list(self.custom_templates.keys())

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        content = (self.builtin_templates.get(template_name) or
                   self.custom_templates.get(template_name))
        if content is None:
            return {"error": f"模板 '{template_name}' 不存在"}
        return {
            "name": template_name,
            "type": "builtin" if template_name in self.builtin_templates else "custom",
            "content_length": len(content),
            "variables": self._extract_template_variables(content)
        }

    def _prepare_template_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        full_context = {
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'app_name': 'FastMapV2',
            'app_version': '2.0.0'
        }
        full_context.update(context)
        full_context.setdefault('title', 'FastMapV2 分析报告')
        full_context.setdefault('generation_time', full_context['current_time'])
        return full_context

    def _extract_template_variables(self, content: str) -> List[str]:
        try:
            import re
            pattern = r'\{\{\s*([^}]+)\s*\}\}'
            matches = re.findall(pattern, content)
            variables: List[str] = []
            for match in matches:
                var_name = match.split('|')[0].split('.')[0].strip()
                if var_name and var_name not in variables:
                    variables.append(var_name)
            return variables
        except Exception:
            return []

    def _read_template_text(self, template_path: Path) -> Optional[str]:
        try:
            return Path(template_path).read_text(encoding='utf-8')
        except FileNotFoundError:
            return None
        except Exception as exc:
            logger.error('读取模板失败: %s (%s)', template_path, exc)
            return None

    def _get_error_template(self) -> Template:
        error_path = self.templates_root / 'shared' / 'error.html'
        try:
            content = error_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            logger.error('错误模板缺失: %s', error_path)
            return Template('模板错误: {{ error_message }}')
        except Exception as exc:
            logger.error('读取错误模板失败: %s', exc)
            return Template('模板错误: {{ error_message }}')
        return Template(content)

    def _load_builtin_templates(self) -> Dict[str, str]:
        mapping = {
            'reporting/domains/map/report.html': self.templates_root / 'domains' / 'map' / 'report.html',
            'reporting/domains/exif/new_report.html': self.templates_root / 'domains' / 'exif' / 'new_report.html',
        }
        templates: Dict[str, str] = {}
        for name, path in mapping.items():
            content = self._read_template_text(path)
            if content is not None:
                templates[name] = content
            else:
                logger.warning("内置模板缺失: %s (%s)", name, path)
        return templates

class InMemoryTemplateLoader(BaseLoader):
    def __init__(self, templates: Optional[Dict[str, str]] = None):
        self.templates = templates or {}

    def get_source(self, environment, template):
        if template not in self.templates:
            raise TemplateNotFound(template)
        source = self.templates[template]
        return source, None, lambda: True


_template_service: Optional[HTMLTemplateService] = None


def get_html_template_service() -> HTMLTemplateService:
    global _template_service
    if _template_service is None:
        _template_service = HTMLTemplateService()
        logger.info("Created HTMLTemplateService singleton")
    return _template_service
