from __future__ import annotations

from ..models import UiLanguage, UiMessage


STRINGS: dict[str, dict[UiLanguage, str]] = {
    "app.title": {"ko": "JSON Viewer & Formatter", "en": "JSON Viewer & Formatter"},
    "toolbar.auto_mode": {
        "ko": "붙여넣기 또는 편집 시 자동 format/repair",
        "en": "Auto format/repair on paste or edit",
    },
    "toolbar.language": {"ko": "언어", "en": "Language"},
    "toolbar.theme": {"ko": "테마", "en": "Theme"},
    "button.copy_output": {"ko": "Copy Output", "en": "Copy Output"},
    "button.save_output": {"ko": "Save Output", "en": "Save Output"},
    "button.diff_highlight": {"ko": "수정 표시", "en": "Diff Highlight"},
    "button.open_file": {"ko": "Open File", "en": "Open File"},
    "button.search": {"ko": "검색", "en": "Search"},
    "button.prev": {"ko": "Prev", "en": "Prev"},
    "button.next": {"ko": "Next", "en": "Next"},
    "button.close": {"ko": "Close", "en": "Close"},
    "button.copy_path": {"ko": "Copy Path", "en": "Copy Path"},
    "button.expand_all": {"ko": "Expand All", "en": "Expand All"},
    "button.collapse_all": {"ko": "Collapse All", "en": "Collapse All"},
    "label.repair_mode": {"ko": "Repair Mode", "en": "Repair Mode"},
    "label.risk": {"ko": "위험도: {level}", "en": "Risk: {level}"},
    "label.selected_path": {"ko": "선택된 경로: {path}", "en": "Selected path: {path}"},
    "label.summary": {"ko": "Change Summary", "en": "Change Summary"},
    "label.warnings": {"ko": "Warnings", "en": "Warnings"},
    "label.tree_matches": {"ko": "{count}개 일치", "en": "{count} matches"},
    "label.search_none": {"ko": "0개 일치", "en": "0 matches"},
    "label.search_progress": {"ko": "{current}/{total}개 일치", "en": "{current}/{total} matches"},
    "label.input_title": {"ko": "Raw JSON Input", "en": "Raw JSON Input"},
    "label.output_title": {"ko": "Formatted / Repaired Output", "en": "Formatted / Repaired Output"},
    "label.text_view": {"ko": "Text View", "en": "Text View"},
    "label.tree_view": {"ko": "Tree View", "en": "Tree View"},
    "label.search_placeholder": {"ko": "검색어 입력", "en": "Enter search term"},
    "placeholder.input": {"ko": "여기에 JSON을 붙여넣거나 입력하세요", "en": "Paste or type JSON here"},
    "placeholder.output": {"ko": "여기에 format/repair 결과가 표시됩니다", "en": "Formatted JSON will appear here"},
    "placeholder.summary": {
        "ko": "repair 변경 사항이 여기에 표시됩니다",
        "en": "Repair changes will appear here",
    },
    "placeholder.warnings": {
        "ko": "repair 경고가 여기에 표시됩니다",
        "en": "Repair warnings will appear here",
    },
    "placeholder.tree_search": {"ko": "key, value, path 검색", "en": "Search key, value, or path"},
    "dialog.open_json_input": {"ko": "JSON 입력 열기", "en": "Open JSON Input"},
    "dialog.save_json_output": {"ko": "JSON 출력 저장", "en": "Save JSON Output"},
    "dialog.app_name": {"ko": "JSON Viewer & Formatter", "en": "JSON Viewer & Formatter"},
    "status.ready": {"ko": "준비됨", "en": "Ready"},
    "status.updating": {"ko": "업데이트 중...", "en": "Updating..."},
    "status.processing": {"ko": "처리 중...", "en": "Processing..."},
    "status.valid_json": {"ko": "유효한 JSON", "en": "Valid JSON"},
    "status.repaired_json": {"ko": "Repaired JSON", "en": "Repaired JSON"},
    "status.unable_to_process": {"ko": "입력을 처리할 수 없습니다", "en": "Unable to process input"},
    "status.copied_output": {"ko": "출력을 clipboard에 복사했습니다", "en": "Copied output to clipboard"},
    "status.saved_to": {"ko": "{path}에 저장했습니다", "en": "Saved to {path}"},
    "status.input_font_size": {"ko": "입력 폰트 크기: {size}pt", "en": "Input font size: {size}pt"},
    "status.output_font_size": {"ko": "출력 폰트 크기: {size}pt", "en": "Output font size: {size}pt"},
    "error.no_output_copy": {"ko": "복사할 출력이 없습니다.", "en": "No output available to copy."},
    "error.no_output_save": {"ko": "저장할 출력이 없습니다.", "en": "No output available to save."},
    "error.open_file_failed": {"ko": "파일을 열 수 없습니다: {error}", "en": "Failed to open file: {error}"},
    "error.save_file_failed": {"ko": "파일을 저장할 수 없습니다: {error}", "en": "Failed to save file: {error}"},
    "combo.language.ko": {"ko": "한국어", "en": "Korean"},
    "combo.language.en": {"ko": "English", "en": "English"},
    "combo.theme.system": {"ko": "System", "en": "System"},
    "combo.theme.light": {"ko": "Light", "en": "Light"},
    "combo.theme.dark": {"ko": "Dark", "en": "Dark"},
    "combo.mode.strict": {"ko": "Strict", "en": "Strict"},
    "combo.mode.safe": {"ko": "Safe", "en": "Safe"},
    "combo.mode.aggressive": {"ko": "Aggressive", "en": "Aggressive"},
    "tree.key": {"ko": "Key", "en": "Key"},
    "tree.value": {"ko": "Value", "en": "Value"},
    "tree.type": {"ko": "Type", "en": "Type"},
    "tree.context.expand_subtree": {"ko": "Expand Subtree", "en": "Expand Subtree"},
    "tree.context.collapse_subtree": {"ko": "Collapse Subtree", "en": "Collapse Subtree"},
    "message.removed_utf8_bom": {"ko": "UTF-8 BOM을 제거했습니다.", "en": "Removed UTF-8 BOM."},
    "message.removed_nul_characters": {"ko": "NUL 문자를 제거했습니다.", "en": "Removed NUL characters."},
    "message.normalized_json_seq": {
        "ko": "JSON text sequence record separator를 정규화했습니다.",
        "en": "Normalized JSON text sequence record separators.",
    },
    "message.normalized_smart_double_quotes": {
        "ko": "smart double quotes를 정규화했습니다.",
        "en": "Normalized smart double quotes.",
    },
    "message.removed_markdown_fence": {
        "ko": "wrapping markdown code fence를 제거했습니다.",
        "en": "Removed wrapping markdown code fence.",
    },
    "message.skipped_done_sentinel": {
        "ko": "[DONE] stream sentinel을 건너뛰었습니다.",
        "en": "Skipped [DONE] stream sentinel.",
    },
    "message.extracted_event_stream_payloads": {
        "ko": "event-stream 입력에서 JSON payload {count}개를 추출했습니다.",
        "en": "Extracted {count} JSON payload(s) from event stream input.",
    },
    "message.escaped_suspicious_quotes": {
        "ko": "string content 안의 의심스러운 quote를 escape했습니다.",
        "en": "Escaped suspicious unescaped quotes inside string content.",
    },
    "message.combined_top_level_documents": {
        "ko": "top-level JSON document {count}개를 하나의 array로 결합했습니다.",
        "en": "Combined {count} top-level JSON documents into one array.",
    },
    "warning.normalized_json_seq": {
        "ko": "record-separated JSON message를 repair 전에 정규화했습니다.",
        "en": "Record-separated JSON messages were normalized before repair.",
    },
    "warning.event_stream_payloads": {
        "ko": "event-stream payload를 repair 전에 정규화했습니다.",
        "en": "Event stream payloads were normalized before repair.",
    },
    "warning.combined_top_level_documents": {
        "ko": "여러 top-level JSON document를 하나의 JSON array로 병합했습니다.",
        "en": "Multiple top-level JSON documents were merged into a single JSON array.",
    },
    "warning.escaped_suspicious_quotes": {
        "ko": "string content 안의 의심스러운 quote를 heuristic으로 escape했습니다.",
        "en": "Suspicious quotes inside string content were escaped heuristically.",
    },
}


def translate(language: UiLanguage, key: str, **params: str | int) -> str:
    localized = STRINGS.get(key)
    if localized is None:
        fallback = key
    else:
        fallback = localized.get(language) or localized.get("en") or key
    return fallback.format(**params)


def render_ui_message(language: UiLanguage, message: UiMessage) -> str:
    return translate(language, f"message.{message.code}", **message.params)


def render_ui_warning(language: UiLanguage, message: UiMessage) -> str:
    return translate(language, f"warning.{message.code}", **message.params)
