from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from ..models import RepairDiff

TOKEN_PATTERN = re.compile(
    r'"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\])*'"
    r"|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?"
    r"|[A-Za-z_][A-Za-z0-9_\-]*"
    r"|[{}\[\]:,]"
    r"|[^\s]"
)


@dataclass(frozen=True, slots=True)
class DiffToken:
    text: str
    start: int
    end: int


def build_repair_diff(input_text: str, output_text: str) -> RepairDiff | None:
    input_tokens = _tokenize(input_text)
    output_tokens = _tokenize(output_text)
    if not input_tokens or not output_tokens:
        return None

    matcher = SequenceMatcher(
        a=[token.text for token in input_tokens],
        b=[token.text for token in output_tokens],
        autojunk=False,
    )

    input_spans: list[tuple[int, int]] = []
    output_spans: list[tuple[int, int]] = []
    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == "equal":
            continue

        input_spans.extend(_input_spans_for_opcode(input_tokens, i1, i2))
        output_spans.extend((token.start, token.end) for token in output_tokens[j1:j2])

        if opcode == "insert" and not input_spans and input_tokens:
            neighbor = _nearest_input_span(input_tokens, i1)
            if neighbor is not None:
                input_spans.append(neighbor)

    merged_input = _merge_spans(input_spans)
    merged_output = _merge_spans(output_spans)
    if not merged_input and not merged_output:
        return None
    return RepairDiff(input_spans=merged_input, output_spans=merged_output)


def _tokenize(text: str) -> list[DiffToken]:
    return [DiffToken(match.group(0), match.start(), match.end()) for match in TOKEN_PATTERN.finditer(text)]


def _input_spans_for_opcode(tokens: list[DiffToken], start: int, end: int) -> list[tuple[int, int]]:
    if start < end:
        return [(token.start, token.end) for token in tokens[start:end]]

    nearest = _nearest_input_span(tokens, start)
    return [nearest] if nearest is not None else []


def _nearest_input_span(tokens: list[DiffToken], index: int) -> tuple[int, int] | None:
    if not tokens:
        return None
    if index <= 0:
        token = tokens[0]
        return token.start, token.end
    if index >= len(tokens):
        token = tokens[-1]
        return token.start, token.end

    previous = tokens[index - 1]
    current = tokens[index]
    return previous.start, current.end


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not spans:
        return []

    ordered = sorted(spans)
    merged: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        previous_start, previous_end = merged[-1]
        if start <= previous_end:
            merged[-1] = (previous_start, max(previous_end, end))
            continue
        merged.append((start, end))
    return merged
