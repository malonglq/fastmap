from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape


def _fmt_num(value: Any, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


class TemplateRenderer:
    """Jinja2 renderer for external templates under `templates/`.

    This is additive to existing in-memory templates; use where convenient.
    """

    def __init__(self, templates_root: Optional[Path] = None) -> None:
        root = templates_root or Path('templates')
        loader = FileSystemLoader(str(root))
        self.env = Environment(
            loader=loader,
            autoescape=select_autoescape(['html', 'xml'])
        )
        # Filters
        self.env.filters['fmt_num'] = _fmt_num

    def render(self, template_path: str, context: Dict[str, Any]) -> str:
        tpl = self.env.get_template(template_path)
        return tpl.render(**context)

