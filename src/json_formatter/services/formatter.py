from __future__ import annotations

import json

from ..models import JsonResult


def format_json(input_text: str) -> JsonResult:
    try:
        parsed = json.loads(input_text)
    except json.JSONDecodeError as exc:
        return JsonResult(
            success=False,
            mode="format",
            output_text="",
            error_message=_format_decode_error(exc),
            status_label="error",
            error_line=exc.lineno,
            error_column=exc.colno,
            error_index=exc.pos,
        )
    except ValueError as exc:
        return JsonResult(
            success=False,
            mode="format",
            output_text="",
            error_message=str(exc),
            status_label="error",
        )

    formatted = json.dumps(parsed, indent=2, ensure_ascii=False, sort_keys=False)
    return JsonResult(
        success=True,
        mode="format",
        output_text=formatted,
        error_message="",
        status_label="valid",
        parsed_value=parsed,
        detected_input_kind="json",
    )


def _format_decode_error(error: json.JSONDecodeError) -> str:
    location = f"line {error.lineno}, column {error.colno}"
    message = error.msg.strip() or "Invalid JSON"
    if location:
        return f"{message} ({location})"
    return message
