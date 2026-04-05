from __future__ import annotations

from ..models import JsonResult, ProcessMode, RepairMode
from .formatter import format_json
from .repairer import repair_json_text


def process_json(
    input_text: str,
    mode: ProcessMode,
    repair_mode: RepairMode = "safe",
) -> JsonResult:
    if mode == "format":
        return format_json(input_text)
    if mode == "repair":
        return repair_json_text(input_text, repair_mode=repair_mode)

    raise ValueError(f"Unsupported mode: {mode}")
