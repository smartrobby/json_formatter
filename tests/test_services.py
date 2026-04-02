from __future__ import annotations

from json_formatter.services.formatter import format_json
from json_formatter.services.repairer import repair_json_text


def test_format_json_pretty_prints_valid_json() -> None:
    result = format_json('{"b":2,"a":"hello"}')

    assert result.success is True
    assert result.mode == "format"
    assert result.status_label == "valid"
    assert result.error_message == ""
    assert result.output_text == '{\n  "b": 2,\n  "a": "hello"\n}'


def test_format_json_returns_line_and_column_on_error() -> None:
    result = format_json('{"a": 1,,}')

    assert result.success is False
    assert result.mode == "format"
    assert result.status_label == "error"
    assert "line" in result.error_message
    assert "column" in result.error_message


def test_repair_json_fixes_common_malformed_json() -> None:
    result = repair_json_text("{'name': 'Alice', trailing: true,}")

    assert result.success is True
    assert result.mode == "repair"
    assert result.status_label == "repaired"
    assert result.output_text == '{\n  "name": "Alice",\n  "trailing": true\n}'


def test_repair_json_preserves_unicode() -> None:
    result = repair_json_text("{'message': '\\uac15\\uc544',}")

    assert result.success is True
    assert "\uac15\uc544" in result.output_text
