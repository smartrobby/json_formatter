from __future__ import annotations

import json

from json_repair import repair_json

from ..models import JsonResult


def repair_json_text(input_text: str) -> JsonResult:
    try:
        repaired_text = repair_json(input_text, ensure_ascii=False, indent=2)
    except Exception as exc:  # pragma: no cover - defensive against third-party failures
        return JsonResult(
            success=False,
            mode="repair",
            output_text="",
            error_message=_format_repair_error(exc),
            status_label="error",
        )

    if not isinstance(repaired_text, str):
        return JsonResult(
            success=False,
            mode="repair",
            output_text="",
            error_message="JSON repair did not return a text result.",
            status_label="error",
        )

    try:
        parsed = json.loads(repaired_text)
    except json.JSONDecodeError as exc:
        return JsonResult(
            success=False,
            mode="repair",
            output_text="",
            error_message=_format_decode_error(exc),
            status_label="error",
        )

    formatted = json.dumps(parsed, indent=2, ensure_ascii=False, sort_keys=False)
    return JsonResult(
        success=True,
        mode="repair",
        output_text=formatted,
        error_message="",
        status_label="repaired",
    )


def _format_decode_error(error: json.JSONDecodeError) -> str:
    return f"{error.msg.strip() or 'Invalid JSON'} (line {error.lineno}, column {error.colno})"


def _format_repair_error(error: Exception) -> str:
    message = str(error).strip() or error.__class__.__name__
    return f"Unable to repair JSON: {message}"
