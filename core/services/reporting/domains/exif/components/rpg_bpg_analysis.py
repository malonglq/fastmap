from __future__ import annotations

from typing import Any, Dict

# 向后兼容：当前实现仍复用旧 helper 中的具体逻辑
from ..helpers.comparison_helpers import (
    generate_per_image_rpg_bpg_analysis as _gen_per_image_rpg_bpg,
)


def generate_per_image_rpg_bpg_analysis(trend_data: Dict[str, Any]) -> str:
    return _gen_per_image_rpg_bpg(trend_data)
