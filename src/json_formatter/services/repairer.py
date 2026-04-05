from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from json_repair import repair_json

from ..models import JsonResult, RepairMode, RiskLevel, UiMessage
from .repair_diff import build_repair_diff

SMART_DOUBLE_QUOTES_TRANSLATION = str.maketrans(
    {
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u201f": '"',
        "\uff02": '"',
    }
)
RISK_PRIORITY: dict[RiskLevel, int] = {"low": 1, "medium": 2, "high": 3}


@dataclass(slots=True)
class RepairTrace:
    change_summary: list[UiMessage] = field(default_factory=list)
    repair_warnings: list[UiMessage] = field(default_factory=list)
    risk_level: RiskLevel | None = None
    detected_input_kind: str | None = None
    quote_heuristic_applied: bool = False

    def add_summary(self, code: str, **params: str | int) -> None:
        message = UiMessage(code=code, params=params)
        if message not in self.change_summary:
            self.change_summary.append(message)

    def add_warning(self, code: str, risk_level: RiskLevel, **params: str | int) -> None:
        message = UiMessage(code=code, params=params)
        if message not in self.repair_warnings:
            self.repair_warnings.append(message)
        self.raise_risk(risk_level)

    def raise_risk(self, risk_level: RiskLevel) -> None:
        if self.risk_level is None or RISK_PRIORITY[risk_level] > RISK_PRIORITY[self.risk_level]:
            self.risk_level = risk_level

    def set_detected_input_kind(self, input_kind: str) -> None:
        if self.detected_input_kind is None:
            self.detected_input_kind = input_kind


def repair_json_text(input_text: str, repair_mode: RepairMode = "safe") -> JsonResult:
    trace = RepairTrace()
    normalized_input = _prepare_repair_input(input_text, repair_mode, trace)

    if repair_mode == "strict":
        fragments = _extract_json_fragments(normalized_input)
        if len(fragments) > 1:
            trace.set_detected_input_kind(_detect_fragment_input_kind(input_text))
            return JsonResult(
                success=False,
                mode="repair",
                output_text="",
                error_message="Strict repair mode does not merge multiple top-level JSON documents.",
                status_label="error",
                change_summary=trace.change_summary,
                repair_warnings=trace.repair_warnings,
                risk_level=trace.risk_level,
                detected_input_kind=trace.detected_input_kind,
            )

    if repair_mode != "strict":
        extracted_result = _repair_extracted_fragments(normalized_input, repair_mode, trace)
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
            change_summary=trace.change_summary,
            repair_warnings=trace.repair_warnings,
            risk_level=trace.risk_level,
            detected_input_kind=trace.detected_input_kind,
        )

    if not isinstance(repaired_text, str):
        return JsonResult(
            success=False,
            mode="repair",
            output_text="",
            error_message="JSON repair did not return a text result.",
            status_label="error",
            change_summary=trace.change_summary,
            repair_warnings=trace.repair_warnings,
            risk_level=trace.risk_level,
            detected_input_kind=trace.detected_input_kind,
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
            change_summary=trace.change_summary,
            repair_warnings=trace.repair_warnings,
            risk_level=trace.risk_level,
            detected_input_kind=trace.detected_input_kind,
            error_line=exc.lineno,
            error_column=exc.colno,
            error_index=exc.pos,
        )

    return _build_success_result(parsed, trace, input_text)


def _build_success_result(parsed: object, trace: RepairTrace, original_input: str) -> JsonResult:
    formatted = json.dumps(parsed, indent=2, ensure_ascii=False, sort_keys=False)
    return JsonResult(
        success=True,
        mode="repair",
        output_text=formatted,
        error_message="",
        status_label="repaired",
        change_summary=trace.change_summary,
        repair_warnings=trace.repair_warnings,
        risk_level=trace.risk_level,
        detected_input_kind=trace.detected_input_kind,
        parsed_value=parsed,
        repair_diff=build_repair_diff(original_input, formatted),
    )


def _repair_extracted_fragments(
    input_text: str,
    repair_mode: RepairMode,
    trace: RepairTrace,
) -> JsonResult | None:
    fragments = _extract_json_fragments(input_text)
    if not fragments:
        return None

    if len(fragments) > 1 and repair_mode == "strict":
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

    if len(parsed_values) > 1:
        trace.set_detected_input_kind(_detect_fragment_input_kind(input_text))
        trace.add_summary("combined_top_level_documents", count=len(parsed_values))
        trace.add_warning(
            "combined_top_level_documents",
            "medium",
        )

    combined_value: object = parsed_values[0] if len(parsed_values) == 1 else parsed_values
    if trace.detected_input_kind is None:
        trace.set_detected_input_kind("json")
    return _build_success_result(combined_value, trace, input_text)


def _prepare_repair_input(input_text: str, repair_mode: RepairMode, trace: RepairTrace) -> str:
    normalized_input = input_text

    if "\ufeff" in normalized_input:
        normalized_input = normalized_input.replace("\ufeff", "")
        trace.add_summary("removed_utf8_bom")

    if "\x00" in normalized_input:
        normalized_input = normalized_input.replace("\x00", "")
        trace.add_summary("removed_nul_characters")

    if "\x1e" in normalized_input:
        normalized_input = normalized_input.replace("\x1e", "\n")
        trace.set_detected_input_kind("json-seq")
        trace.add_summary("normalized_json_seq")
        trace.add_warning(
            "normalized_json_seq",
            "medium",
        )

    translated = normalized_input.translate(SMART_DOUBLE_QUOTES_TRANSLATION)
    if translated != normalized_input:
        normalized_input = translated
        trace.add_summary("normalized_smart_double_quotes")

    stripped = _strip_wrapping_markdown_fence(normalized_input)
    if stripped != normalized_input:
        normalized_input = stripped
        trace.set_detected_input_kind("markdown-fenced-json")
        trace.add_summary("removed_markdown_fence")
        trace.raise_risk("low")

    if repair_mode != "strict":
        stream_normalized = _normalize_event_stream_text(normalized_input, trace)
        if stream_normalized != normalized_input:
            normalized_input = stream_normalized

    if _should_apply_quote_heuristic(normalized_input, repair_mode):
        escaped_input = _escape_unescaped_string_quotes(normalized_input)
        if escaped_input != normalized_input:
            normalized_input = escaped_input
            trace.quote_heuristic_applied = True
            trace.add_summary("escaped_suspicious_quotes")
            trace.add_warning(
                "escaped_suspicious_quotes",
                "high",
            )

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


def _normalize_event_stream_text(input_text: str, trace: RepairTrace) -> str:
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

    original_payload_count = len(payloads)
    if len(payloads) > 1 and any(_looks_like_json_payload(payload) for payload in payloads):
        filtered_payloads = [payload for payload in payloads if payload.strip() != "[DONE]"]
        if len(filtered_payloads) != len(payloads):
            trace.add_summary("skipped_done_sentinel")
        payloads = filtered_payloads

    if not payloads:
        return ""

    normalized_input = "\n\n".join(payloads)
    if normalized_input != input_text:
        trace.set_detected_input_kind("event-stream")
        trace.add_summary("extracted_event_stream_payloads", count=len(payloads))
        if original_payload_count > 1 or len(payloads) > 1:
            trace.add_warning(
                "event_stream_payloads",
                "medium",
            )

    return normalized_input


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


def _should_apply_quote_heuristic(input_text: str, repair_mode: RepairMode) -> bool:
    if repair_mode == "strict":
        return False

    if repair_mode == "aggressive":
        return '"' in input_text

    return any(token in input_text for token in ("<", "</", "src=", "href=", "style=", '""'))


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


def _detect_fragment_input_kind(input_text: str) -> str:
    if "\x1e" in input_text:
        return "json-seq"
    if _looks_like_event_stream(input_text):
        return "event-stream"
    if "\n" in input_text:
        return "concatenated-documents"
    return "json"


def _format_decode_error(error: json.JSONDecodeError) -> str:
    return f"{error.msg.strip() or 'Invalid JSON'} (line {error.lineno}, column {error.colno})"


def _format_repair_error(error: Exception) -> str:
    message = str(error).strip() or error.__class__.__name__
    return f"Unable to repair JSON: {message}"
