from __future__ import annotations

import json

from json_formatter.models import UiMessage
from json_formatter.services.formatter import format_json
from json_formatter.services.processor import process_json
from json_formatter.services.repairer import repair_json_text
from json_formatter.ui.localization import render_ui_message, render_ui_warning


def test_format_json_pretty_prints_valid_json_with_parsed_value() -> None:
    result = format_json('{"b":2,"a":"hello"}')

    assert result.success is True
    assert result.mode == "format"
    assert result.status_label == "valid"
    assert result.error_message == ""
    assert result.output_text == '{\n  "b": 2,\n  "a": "hello"\n}'
    assert result.parsed_value == {"b": 2, "a": "hello"}
    assert result.change_summary == []
    assert result.repair_warnings == []
    assert result.detected_input_kind == "json"
    assert result.repair_diff is None


def test_format_json_returns_location_metadata_on_error() -> None:
    result = format_json('{"a": 1,,}')

    assert result.success is False
    assert result.mode == "format"
    assert result.status_label == "error"
    assert "line" in result.error_message
    assert "column" in result.error_message
    assert result.error_line == 1
    assert result.error_column is not None
    assert result.error_index is not None


def test_repair_json_fixes_common_malformed_json_without_forced_summary() -> None:
    result = repair_json_text("{'name': 'Alice', trailing: true,}")

    assert result.success is True
    assert result.mode == "repair"
    assert result.status_label == "repaired"
    assert result.output_text == '{\n  "name": "Alice",\n  "trailing": true\n}'
    assert result.change_summary == []
    assert result.risk_level is None
    assert result.repair_diff is not None


def test_repair_json_preserves_unicode() -> None:
    result = repair_json_text("{'message': '\\uac15\\uc544',}")

    assert result.success is True
    assert "강아" in result.output_text


def test_repair_json_combines_multiple_top_level_objects_into_array_with_warning() -> None:
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
    assert result.detected_input_kind == "concatenated-documents"
    assert UiMessage("combined_top_level_documents", {"count": 2}) in result.change_summary
    assert UiMessage("combined_top_level_documents", {}) in result.repair_warnings
    assert result.risk_level == "medium"
    assert result.repair_diff is not None
    assert result.repair_diff.output_spans


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
    assert result.detected_input_kind == "event-stream"
    assert UiMessage("extracted_event_stream_payloads", {"count": 2}) in result.change_summary


def test_repair_json_ignores_bom_prefix() -> None:
    result = repair_json_text('\ufeff{"alpha": 1,}')

    assert result.success is True
    assert json.loads(result.output_text) == {"alpha": 1}
    assert UiMessage("removed_utf8_bom") in result.change_summary


def test_repair_json_normalizes_smart_double_quotes() -> None:
    result = repair_json_text('{\n  \u201cusers\u201d: [{\u201cname\u201d: \u201crobby\u201d, \u201cage\u201d: 20}]\n}')

    assert result.success is True
    parsed = json.loads(result.output_text)
    assert parsed["users"][0]["name"] == "robby"
    assert parsed["users"][0]["age"] == 20
    assert UiMessage("normalized_smart_double_quotes") in result.change_summary


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
    assert UiMessage("skipped_done_sentinel") in result.change_summary
    assert UiMessage("event_stream_payloads") in result.repair_warnings


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
    assert result.risk_level == "high"
    assert UiMessage("escaped_suspicious_quotes") in result.change_summary


def test_strict_mode_is_more_conservative_for_stream_documents() -> None:
    input_text = '{"a": 1}\n{"b": 2}'

    strict_result = repair_json_text(input_text, repair_mode="strict")
    safe_result = repair_json_text(input_text, repair_mode="safe")

    assert safe_result.success is True
    assert json.loads(safe_result.output_text) == [{"a": 1}, {"b": 2}]
    assert strict_result.success is False or json.loads(strict_result.output_text) != [{"a": 1}, {"b": 2}]


def test_aggressive_mode_recovers_ambiguous_broken_quotes_better_than_safe() -> None:
    input_text = '{"note": "alpha "beta" gamma", "ok": true}'

    safe_result = repair_json_text(input_text, repair_mode="safe")
    aggressive_result = repair_json_text(input_text, repair_mode="aggressive")

    assert safe_result.success is True
    assert aggressive_result.success is True
    assert json.loads(aggressive_result.output_text)["note"] == 'alpha "beta" gamma'
    assert json.loads(safe_result.output_text)["note"] == 'alpha "beta" gamma'
    assert safe_result.risk_level is None
    assert aggressive_result.risk_level == "high"
    assert aggressive_result.repair_warnings == [UiMessage("escaped_suspicious_quotes")]


def test_process_json_passes_repair_mode_to_repairer() -> None:
    result = process_json('{"note": "alpha "beta" gamma", "ok": true}', "repair", repair_mode="aggressive")

    assert result.success is True
    assert json.loads(result.output_text)["note"] == 'alpha "beta" gamma'


def test_localized_message_templates_render_consistently() -> None:
    message = UiMessage("extracted_event_stream_payloads", {"count": 2})
    warning = UiMessage("combined_top_level_documents")

    assert render_ui_message("en", message) == "Extracted 2 JSON payload(s) from event stream input."
    assert render_ui_message("ko", message) == "event-stream 입력에서 JSON payload 2개를 추출했습니다."
    assert render_ui_warning("en", warning) == "Multiple top-level JSON documents were merged into a single JSON array."
    assert render_ui_warning("ko", warning) == "여러 top-level JSON document를 하나의 JSON array로 병합했습니다."
