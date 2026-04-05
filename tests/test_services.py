from __future__ import annotations

import json

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


def test_repair_json_combines_multiple_top_level_objects_into_array() -> None:
    result = repair_json_text(
        """{
  "users": [
    {
      "name": "robby",
      "age": 20
    },
    {
      "name": "alex",
      "age": 25
    }
  ]
},
{
  "users": [
    {
      "name": "robby",
      "age": 20
    },
    {
      "name": "alex",
      "age": 25
    }
  ]
}
]"""
    )

    assert result.success is True
    parsed = json.loads(result.output_text)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0]["users"][0]["name"] == "robby"
    assert parsed[1]["users"][1]["name"] == "alex"


def test_repair_json_preserves_valid_array_documents() -> None:
    result = repair_json_text(
        """[
\t{
\t  "users": [
\t\t{
\t\t  "name": "robby",
\t\t  "age": 20
\t\t},
\t\t{
\t\t  "name": "alex",
\t\t  "age": 25
\t\t}
\t  ]
\t},
\t{
\t  "users": [
\t\t{
\t\t  "name": "robby",
\t\t  "age": 20
\t\t},
\t\t{
\t\t  "name": "alex",
\t\t  "age": 25
\t\t}
\t  ]
\t}
]"""
    )

    assert result.success is True
    parsed = json.loads(result.output_text)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0]["users"][0]["age"] == 20
    assert parsed[1]["users"][1]["age"] == 25


def test_repair_json_extracts_multiple_data_prefixed_payloads() -> None:
    result = repair_json_text(
        """data: {
  "users": [
    {
      "name": "robby",
      "age": 20
    },
    {
      "name": "alex",
      "age": 25
    }
  ]
}

data:

data: {
  "users": [
    {
      "name": "robby",
      "age": 20
    },
    {
      "name": "alex",
      "age": 25
    }
  ]
}"""
    )

    assert result.success is True
    parsed = json.loads(result.output_text)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0]["users"][0]["name"] == "robby"
    assert parsed[1]["users"][1]["name"] == "alex"


def test_repair_json_ignores_bom_prefix() -> None:
    result = repair_json_text('\ufeff{"alpha": 1,}')

    assert result.success is True
    assert json.loads(result.output_text) == {"alpha": 1}


def test_repair_json_normalizes_smart_double_quotes() -> None:
    result = repair_json_text('{\n  “users”: [{“name”: “robby”, “age”: 20}]\n}')

    assert result.success is True
    parsed = json.loads(result.output_text)
    assert parsed["users"][0]["name"] == "robby"
    assert parsed["users"][0]["age"] == 20


def test_repair_json_normalizes_sse_messages_and_skips_done_sentinel() -> None:
    result = repair_json_text(
        """: keep-alive

event: userconnect
data: {"username": "bobby", "time": "02:33:48"}

id: 2
data: {"username": "sean", "time": "02:34:36"}

data: [DONE]
"""
    )

    assert result.success is True
    parsed = json.loads(result.output_text)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0]["username"] == "bobby"
    assert parsed[1]["username"] == "sean"


def test_repair_json_preserves_html_like_string_content_without_splitting_keys() -> None:
    result = repair_json_text(
        """{
  "html_content": "<!DOCTYPE html>
<html lang="zh">
<body>
<img src="https://via.placeholder.com/600x300" style="width: 100%; max-width: 600px; height: auto;">
</body>
</html>",
  "output_filename": "converted_document.docx"
}"""
    )

    assert result.success is True
    parsed = json.loads(result.output_text)
    assert set(parsed) == {"html_content", "output_filename"}
    assert 'src="https://via.placeholder.com/600x300"' in parsed["html_content"]
    assert 'style="width: 100%; max-width: 600px; height: auto;"' in parsed["html_content"]
    assert parsed["output_filename"] == "converted_document.docx"
