# Code Reference

이 문서는 `dev-robby` 브랜치에서 추가된 구현 변경 사항을 빠르게 파악하기 위한 코드 참조 문서입니다. 실제 구현은 UI panel 분리, repair metadata 확장, tree inspector, file input UX, repair mode, controller integration 중심으로 정리돼 있습니다.

## 변경 개요

`dev-robby`에서 반영된 핵심 변경은 다음 다섯 묶음입니다.

1. `Foundation`
   - `MainWindow` 중심 구조를 `InputPanel` + `OutputPanel` composition으로 분리
2. `Services`
   - `JsonResult` 확장
   - repair metadata, risk level, parsed value, error location, repair mode 추가
3. `Output UX`
   - `Change Summary`, `Warnings`, `Risk`
   - `Text View` / `Tree View`
   - tree search와 `Copy Path`
4. `Input UX`
   - parse error highlight
   - `Open File`, `Ctrl+O`, drag & drop
   - repair mode selector와 persistence
5. `Integration`
   - controller wiring
   - 문서 갱신
   - 전체 검증 및 exe smoke-test

## 주요 파일 맵

### Entry / Controller

- [main.py](/D:/workspace/wt-json_formatter-dev-robby/main.py)
  - 앱 진입점
  - `src`를 import path에 추가하고 `json_formatter.app.main()` 호출
- [app.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/app.py)
  - `QApplication` 생성
  - `JsonFormatterController`
  - smoke-test CLI

### Data Model

- [models.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/models.py)
  - `ProcessMode`
  - `RepairMode`
  - `StatusLabel`
  - `RiskLevel`
  - `JsonResult`

`JsonResult` 확장 필드:

- `change_summary`
- `repair_warnings`
- `risk_level`
- `detected_input_kind`
- `error_line`
- `error_column`
- `error_index`
- `parsed_value`

### Services

- [formatter.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/services/formatter.py)
  - strict `json.loads()` 수행
  - 성공 시 `parsed_value` 반환
  - 실패 시 line / column / index 포함
- [repairer.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/services/repairer.py)
  - repair pipeline 핵심
  - input normalization
  - fragment extraction
  - mode-aware repair
  - change summary / warnings / risk 계산
- [processor.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/services/processor.py)
  - `process_json(input_text, mode, repair_mode="safe")`

### UI

- [main_window.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/ui/main_window.py)
  - panel composition
  - status / toolbar
  - file dialog wiring
  - auto-processing
  - copy/save
  - pane font persistence
- [input_panel.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/ui/input_panel.py)
  - 입력 editor
  - parse error highlight
  - `Open File`
  - `Ctrl+O`
  - drag & drop
  - repair mode selector
  - `QSettings` persistence
- [output_panel.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/ui/output_panel.py)
  - output editor
  - summary / warnings / risk badge
  - text/tree tabs
  - tree search
  - selected path
  - `Copy Path`
- [json_tree_view.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/ui/json_tree_view.py)
  - JSON tree 렌더링
  - 검색, path 계산
- [highlighter.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/ui/highlighter.py)
  - output JSON syntax highlighting

## Controller 흐름

controller 핵심은 [app.py](/D:/workspace/wt-json_formatter-dev-robby/src/json_formatter/app.py) 의 `JsonFormatterController` 입니다.

처리 순서:

1. 입력이 비어 있으면
   - input error highlight clear
   - output clear
2. strict format 시도
3. strict format 성공 시
   - input highlight clear
   - pretty JSON 출력
   - `parsed_value`를 output tree에 전달
   - `Change Summary` / `Warnings` / `Risk`는 비움
4. strict format 실패 시
   - 현재 `RepairMode`를 읽어서 repair 수행
5. repair 성공 시
   - input highlight clear
   - repaired JSON 출력
   - `parsed_value`, `change_summary`, `repair_warnings`, `risk_level`을 output panel에 전달
6. repair 실패 시
   - strict format 에러 위치를 input panel에 highlight
   - combined error message 표시

## InputPanel 동작

핵심 기능:

- parse error highlight
- file open 요청 signal
- drag/drop file path signal
- repair mode 변경 signal

중요 settings key:

- `ui/repair_mode`
- `ui/last_open_path`

주요 API:

- `current_repair_mode()`
- `set_repair_mode(mode)`
- `set_last_open_path(path)`
- `clear_error_highlight()`
- `highlight_error(line, column, index)`

## OutputPanel 동작

핵심 기능:

- syntax-highlighted text output
- `Change Summary`
- `Warnings`
- `Risk` badge
- `Text View`
- `Tree View`
- search
- selected path 표시
- `Copy Path`

주요 API:

- `set_output_text(..., parsed_value=...)`
- `set_summary(change_summary, repair_warnings, risk_level)`
- `set_tree_value(value)`
- `copy_selected_path()`

## Repair Metadata 규칙

repair 경로는 단순히 문자열만 반환하지 않고, 아래 메타데이터를 같이 생성합니다.

### `detected_input_kind`

예시:

- `json`
- `json-lines`
- `json-seq`
- `event-stream`
- `concatenated-documents`
- `markdown-fenced-json`

### `change_summary`

예시:

- UTF-8 BOM 제거
- markdown code fence 제거
- smart quote 정규화
- event stream payload 추출
- `[DONE]` sentinel skip
- 여러 top-level document를 배열로 결합
- suspicious quote escape 적용

### `risk_level`

- `low`
  - 명백한 문법 정리만 수행
- `medium`
  - stream normalization, multiple document 결합
- `high`
  - string quote heuristic처럼 ambiguity가 높은 보정 포함

## Tree View 규칙

tree path 규칙:

- root: `$`
- object key: `$.key`
- array index: `$[0]`, `$[1]`

search는 key / value / type / path를 하나의 lowercase 비교 문자열로 합쳐 포함 검색합니다.

## 파일 입력 흐름

### Open File

1. `InputPanel`이 `openFileRequested(last_path)` emit
2. `MainWindow`가 file dialog open
3. 파일을 읽고 input text 반영
4. last-open path 저장
5. 기존 auto-process timer가 그대로 동작

### Drag & Drop

1. `InputPanel`이 local file drop만 허용
2. drop 시 `fileDropped(path)` emit
3. `MainWindow`가 동일한 load path로 처리

## 관련 테스트

- [test_services.py](/D:/workspace/wt-json_formatter-dev-robby/tests/test_services.py)
  - formatter / repairer / risk / repair mode
- [test_input_panel.py](/D:/workspace/wt-json_formatter-dev-robby/tests/test_input_panel.py)
  - error highlight
  - open shortcut
  - drag/drop
  - repair mode persistence
- [test_output_panel.py](/D:/workspace/wt-json_formatter-dev-robby/tests/test_output_panel.py)
  - summary / warnings / risk badge
  - tree rendering
  - search / path copy
- [test_ui.py](/D:/workspace/wt-json_formatter-dev-robby/tests/test_ui.py)
  - controller integration
  - file open wiring
  - mode 변경 후 재처리
  - stale highlight clear
- [test_smoke.py](/D:/workspace/wt-json_formatter-dev-robby/tests/test_smoke.py)
  - headless instantiation
  - smoke report

## 참고 문서

- [implementation-guide.md](/D:/workspace/wt-json_formatter-dev-robby/doc/implementation-guide.md)
- [README.md](/D:/workspace/wt-json_formatter-dev-robby/README.md)
