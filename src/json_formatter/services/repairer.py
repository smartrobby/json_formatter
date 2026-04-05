from __future__ import annotations

import json
import re

from json_repair import repair_json

from ..models import JsonResult

SMART_DOUBLE_QUOTES_TRANSLATION = str.maketrans(
    {
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u201f": '"',
        "\uff02": '"',
    }
)


def repair_json_text(input_text: str) -> JsonResult:
    normalized_input = _prepare_repair_input(input_text)
    extracted_result = _repair_extracted_fragments(normalized_input)
    if extracted_result is not None:
        return extracted_result

    try:
        repaired_text = repair_json(
            normalized_input,
            ensure_ascii=False,
            indent=2,
            stream_stable=True,
        )
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


def _repair_extracted_fragments(input_text: str) -> JsonResult | None:
    fragments = _extract_json_fragments(input_text)
    if not fragments:
        return None

    parsed_values: list[object] = []
    try:
        for fragment in fragments:
            repaired_fragment = repair_json(
                fragment,
                ensure_ascii=False,
                stream_stable=True,
            )
            parsed_values.append(json.loads(repaired_fragment))
    except Exception:
        return None

    combined_value: object
    if len(parsed_values) == 1:
        combined_value = parsed_values[0]
    else:
        combined_value = parsed_values

    formatted = json.dumps(combined_value, indent=2, ensure_ascii=False, sort_keys=False)
    return JsonResult(
        success=True,
        mode="repair",
        output_text=formatted,
        error_message="",
        status_label="repaired",
    )


def _prepare_repair_input(input_text: str) -> str:
    normalized_input = input_text.replace("\ufeff", "").replace("\x00", "").replace("\x1e", "\n")
    normalized_input = normalized_input.translate(SMART_DOUBLE_QUOTES_TRANSLATION)
    normalized_input = _strip_wrapping_markdown_fence(normalized_input)
    normalized_input = _normalize_event_stream_text(normalized_input)
    normalized_input = _escape_unescaped_string_quotes(normalized_input)
    return normalized_input


def _strip_wrapping_markdown_fence(input_text: str) -> str:
    match = re.match(
        r"^\s*```(?:json|jsonc|javascript|js)?\s*\r?\n(?P<body>.*)\r?\n```\s*$",
        input_text,
        re.IGNORECASE | re.DOTALL,
    )
    if match is None:
        return input_text

    return match.group("body")


def _normalize_event_stream_text(input_text: str) -> str:
    if not _looks_like_event_stream(input_text):
        return input_text

    payloads: list[str] = []
    data_lines: list[str] = []

    def flush_message() -> None:
        payload = "\n".join(data_lines).strip()
        data_lines.clear()
        if payload:
            payloads.append(payload)

    for line in input_text.splitlines():
        stripped = line.lstrip()
        if not stripped:
            flush_message()
            continue

        if stripped.startswith(":"):
            continue

        if data_lines and not re.match(r"^(data|event|id|retry):", stripped):
            data_lines.append(line)
            continue

        if ":" not in stripped:
            continue

        field_name, value = stripped.split(":", 1)
        field_name = field_name.strip()
        value = value[1:] if value.startswith(" ") else value

        if field_name == "data":
            data_lines.append(value)
            continue

        if field_name in {"event", "id", "retry"}:
            continue

    flush_message()

    if not payloads:
        return input_text

    if len(payloads) > 1 and any(_looks_like_json_payload(payload) for payload in payloads):
        payloads = [payload for payload in payloads if payload.strip() != "[DONE]"]

    if not payloads:
        return ""

    return "\n\n".join(payloads)


def _looks_like_event_stream(input_text: str) -> bool:
    for line in input_text.splitlines():
        stripped = line.lstrip()
        if not stripped:
            continue
        if stripped.startswith(":"):
            return True
        if re.match(r"^(data|event|id|retry):", stripped):
            return True
    return False


def _looks_like_json_payload(payload: str) -> bool:
    stripped = payload.lstrip()
    if not stripped:
        return False

    return stripped[0] in '{["-0123456789tfn'


def _escape_unescaped_string_quotes(input_text: str) -> str:
    characters: list[str] = []
    in_double_string = False
    in_single_string = False
    escape_next = False

    for index, char in enumerate(input_text):
        if in_double_string:
            if escape_next:
                characters.append(char)
                escape_next = False
                continue

            if char == "\\":
                characters.append(char)
                escape_next = True
                continue

            if char == '"':
                if _is_likely_string_closer(input_text, index):
                    in_double_string = False
                    characters.append(char)
                else:
                    characters.append("\\")
                    characters.append(char)
                continue

            characters.append(char)
            continue

        if in_single_string:
            if escape_next:
                characters.append(char)
                escape_next = False
                continue

            if char == "\\":
                characters.append(char)
                escape_next = True
                continue

            if char == "'" and _is_likely_string_closer(input_text, index):
                in_single_string = False

            characters.append(char)
            continue

        if char == '"' and _is_likely_string_opener(input_text, index):
            in_double_string = True
            characters.append(char)
            continue

        if char == "'" and _is_likely_string_opener(input_text, index):
            in_single_string = True
            characters.append(char)
            continue

        characters.append(char)

    return "".join(characters)


def _is_likely_string_opener(input_text: str, quote_index: int) -> bool:
    previous_index = quote_index - 1
    while previous_index >= 0 and input_text[previous_index].isspace():
        previous_index -= 1

    if previous_index < 0:
        return True

    return input_text[previous_index] in "{[:,("


def _is_likely_string_closer(input_text: str, quote_index: int) -> bool:
    next_index = quote_index + 1
    while next_index < len(input_text) and input_text[next_index].isspace():
        next_index += 1

    if next_index >= len(input_text):
        return True

    return input_text[next_index] in {":", ",", "}", "]", ")"}


def _extract_json_fragments(input_text: str) -> list[str]:
    fragments: list[str] = []
    stack: list[str] = []
    fragment_start: int | None = None
    in_string = False
    escape_next = False
    string_delimiter = ""
    opening_tokens = {"{": "}", "[": "]"}
    closing_tokens = {"}": "{", "]": "["}

    # Extract top-level JSON-like chunks so stream-style or repeated payloads
    # can be repaired and rendered together instead of truncating to one value.
    for index, char in enumerate(input_text):
        if in_string:
            if escape_next:
                escape_next = False
            elif char == "\\":
                escape_next = True
            elif char == string_delimiter:
                in_string = False
            continue

        if char in {'"', "'"}:
            if fragment_start is not None:
                in_string = True
                string_delimiter = char
            continue

        if char in opening_tokens:
            if fragment_start is None:
                fragment_start = index
            stack.append(char)
            continue

        if char in closing_tokens:
            if not stack:
                continue

            if stack[-1] != closing_tokens[char]:
                continue

            stack.pop()
            if not stack and fragment_start is not None:
                fragment = input_text[fragment_start : index + 1].strip()
                if fragment:
                    fragments.append(fragment)
                fragment_start = None

    if fragment_start is not None:
        fragment = input_text[fragment_start:].strip()
        if fragment:
            fragments.append(fragment)

    return fragments


def _format_decode_error(error: json.JSONDecodeError) -> str:
    return f"{error.msg.strip() or 'Invalid JSON'} (line {error.lineno}, column {error.colno})"


def _format_repair_error(error: Exception) -> str:
    message = str(error).strip() or error.__class__.__name__
    return f"Unable to repair JSON: {message}"
