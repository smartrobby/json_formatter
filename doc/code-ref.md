# Code Reference

이 문서는 현재 `dev-robby` 브랜치의 핵심 구현 지점을 빠르게 찾기 위한 코드 참조입니다.

## 최근 레이아웃 변경

- 전역 `수정 표시` 기본값: `off`
- repair metadata(`Change Summary`, `Warnings`, `Risk`) 위치: `InputPanel` 아래
- output pane: `Text View` / `Tree View` 중심
- tree key column: 기본 폭 대비 3배 확장

## 엔트리 포인트

- `main.py`
  - 실행 진입점
- `src/json_formatter/app.py`
  - `create_application()`
  - `JsonFormatterController`
  - smoke-test flow

## 모델

- `src/json_formatter/models.py`
  - `JsonResult`
  - `UiMessage`
  - `RepairDiff`
  - `RepairMode`
  - `UiLanguage`
  - `ThemeMode`

## 서비스

- `src/json_formatter/services/formatter.py`
  - strict format
  - parse error metadata
- `src/json_formatter/services/repairer.py`
  - repair pipeline
  - summary / warning / risk 계산
- `src/json_formatter/services/repair_diff.py`
  - input/output diff span 계산
- `src/json_formatter/services/processor.py`
  - format / repair dispatch

## UI

### `src/json_formatter/ui/main_window.py`

- toolbar 구성
- `수정 표시` toggle state
- auto-process debounce
- panel wiring
- copy/save
- search routing

중요 필드:

- `_diff_highlight_enabled`
- `_last_repair_diff`
- `_last_repair_status_label`

중요 메서드:

- `set_output_text(...)`
- `clear_output(...)`
- `set_success_state(...)`
- `set_error_state(...)`
- `_mark_output_stale()`
- `_handle_diff_highlight_toggled(...)`

### `src/json_formatter/ui/input_panel.py`

- input editor
- error highlight
- diff highlight
- search
- file open / drag-drop
- repair mode selector
- repair metadata 렌더링

중요 메서드:

- `set_summary(change_summary, repair_warnings, risk_level)`
- `highlight_error(...)`
- `set_diff_spans(...)`
- `set_diff_highlight_enabled(...)`

### `src/json_formatter/ui/output_panel.py`

- output text editor
- text/tree tabs
- output diff highlight
- search
- tree controls

중요 메서드:

- `set_output_text(...)`
- `set_tree_value(...)`
- `set_text_diff(...)`
- `set_diff_highlight_enabled(...)`
- `show_text_search()`
- `show_tree_search()`

### `src/json_formatter/ui/json_tree_view.py`

- JSON tree 렌더링
- search / selection
- subtree context menu
- key column width 확장

중요 메서드:

- `set_json_value(...)`
- `set_search_term(...)`
- `expand_subtree(...)`
- `collapse_subtree(...)`

## 문서와 테스트

- `README.md`
  - 사용자 관점 기능 설명
- `doc/implementation-guide.md`
  - 구조와 흐름 설명
- `tests/test_ui.py`
  - 통합 UI 동작
- `tests/test_input_panel.py`
  - input panel 동작
- `tests/test_output_panel.py`
  - output panel 동작
