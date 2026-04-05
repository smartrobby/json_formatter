# JSON Viewer & Formatter Implementation Guide

이 문서는 현재 `dev-robby` 기준 구현을 빠르게 다시 파악하기 위한 참고 문서다. 최신 구조는 `InputPanel` + `OutputPanel` + `MainWindow` composition과 controller 중심의 자동 처리 흐름으로 정리되어 있다.

## 목표

- raw JSON 또는 JSON 계열 텍스트를 입력하면 자동으로 처리한다.
- strict JSON이면 pretty format 결과를 바로 보여준다.
- strict parse 실패 시 repair mode에 따라 복구를 시도한다.
- 복구가 수행되면 무엇이 바뀌었는지, 얼마나 공격적인 보정이었는지 같이 보여준다.
- 큰 JSON은 text view와 tree view 둘 다에서 탐색할 수 있어야 한다.

## 실행 환경

반드시 프로젝트 루트의 `.venv`를 사용한다.

```powershell
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

검증 명령:

```powershell
pytest -q
python -m compileall src tests main.py
python -m PyInstaller --clean --noconfirm json_formatter.spec
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\json_formatter.exe --smoke-test --smoke-output .\dist\smoke-report.json
```

## 현재 구조

- `main.py`
  - 루트 실행 진입점
  - `json_formatter.app.main()` 호출
- `src/json_formatter/app.py`
  - `QApplication` 생성
  - `JsonFormatterController` 정의
  - smoke-test CLI 흐름 제공
- `src/json_formatter/models.py`
  - `JsonResult`
  - `RepairMode`
  - risk/error metadata 정의
- `src/json_formatter/services/formatter.py`
  - strict `json.loads()` + pretty format
  - 실패 시 `error_line`, `error_column`, `error_index` 반환
- `src/json_formatter/services/repairer.py`
  - repair pipeline
  - `change_summary`, `repair_warnings`, `risk_level`, `detected_input_kind` 생성
  - `strict`, `safe`, `aggressive` mode 처리
- `src/json_formatter/services/processor.py`
  - `process_json(input_text, mode, repair_mode="safe")`
- `src/json_formatter/ui/input_panel.py`
  - 입력 editor
  - `Open File`, `Ctrl+O`, drag & drop
  - repair mode selector
  - parse error highlight
  - last-open-path, repair mode persistence
- `src/json_formatter/ui/output_panel.py`
  - text output editor
  - summary / warnings / risk badge
  - `Text View` / `Tree View`
  - search, selected path, `Copy Path`
- `src/json_formatter/ui/json_tree_view.py`
  - JSON tree 렌더링
  - key/value/path 기반 검색
- `src/json_formatter/ui/main_window.py`
  - panel 조립
  - auto-process timer
  - file open wiring
  - copy/save
  - 입력/출력 pane별 font persistence

## MainWindow 역할

`MainWindow`는 더 이상 모든 UI 세부 구현을 직접 소유하지 않는다. 지금 역할은 다음으로 제한된다.

- `InputPanel` / `OutputPanel` 배치
- toolbar, status bar 관리
- auto-processing debounce timer
- `InputPanel` signal wiring
- controller가 전달한 결과를 각 panel API로 분배
- `Copy Output`, `Save Output`
- pane별 `Ctrl + mouse wheel` font zoom persistence

### 연결된 주요 signal

- `input_edit.textChanged`
  - debounce timer 시작
- `auto_process_timer.timeout`
  - `autoProcessRequested` emit
- `input_panel.openFileRequested`
  - file dialog 열기
- `input_panel.fileDropped`
  - 파일 직접 로드
- `input_panel.repairModeChanged`
  - 현재 입력이 있으면 자동 재처리
- `input_edit.fontZoomRequested`
  - 입력 pane font size 조절
- `output_edit.fontZoomRequested`
  - 출력 pane font size 조절

## InputPanel 상세

`InputPanel`은 입력 UX 전용 컴포넌트다.

### 포함 기능

- `ZoomableTextEdit`
- `Open File` 버튼
- `Ctrl+O` shortcut
- `Repair Mode` combo
- drag enter / drop 처리
- parse error highlight

### persistence

- `ui/repair_mode`
  - 마지막 선택 repair mode 저장
- `ui/last_open_path`
  - 마지막 파일 경로 저장

### 에러 하이라이트

- `highlight_error(line, column, index)`
  - `QTextEdit.ExtraSelection`으로 line highlight 생성
  - cursor를 해당 위치로 이동
- `clear_error_highlight()`
  - 이전 에러 표시 제거

## OutputPanel 상세

`OutputPanel`은 결과 표시와 탐색용 UI다.

### 포함 기능

- syntax-highlighted text output
- `Change Summary`
- `Warnings`
- `Risk` badge
- `Text View`
- `Tree View`
- 검색창
- match count
- selected path label
- `Copy Path`

### tree view

- root path는 `$`
- object key는 `$.key`
- array element는 `$[0]`, `$[1]`
- search는 key/value/type/path를 하나의 lowercase haystack으로 만들어 포함 검색

## Controller 흐름

`JsonFormatterController`는 `MainWindow.autoProcessRequested`를 받아 format/repair를 조정한다.

### 처리 순서

1. 입력이 비어 있으면
   - output clear
   - input error highlight clear
2. strict format 시도
3. strict format 성공 시
   - output text 설정
   - parsed tree 설정
   - summary/warnings/risk 비움
   - stale highlight 제거
   - status는 `Valid JSON`
4. strict format 실패 시
   - 현재 `repair_mode`를 `MainWindow.current_repair_mode()`에서 읽음
5. repair 성공 시
   - output text 설정
   - parsed tree 설정
   - change summary / warnings / risk badge 반영
   - stale highlight 제거
   - status는 `Repaired JSON`
6. repair도 실패 시
   - strict format error 위치를 입력창에 highlight
   - combined error text 표시
   - output clear
   - status는 `Unable to process input`

## Repair Mode 의미

- `strict`
  - 여러 top-level document를 자동 배열 결합하지 않는다.
  - aggressive quote heuristic을 적용하지 않는다.
- `safe`
  - 기본값
  - 일반적인 malformed JSON과 명확한 stream normalization을 처리한다.
- `aggressive`
  - 더 넓은 salvage heuristic 허용
  - ambiguity가 큰 입력에서 `risk_level`이 높아질 수 있다.

## Summary / Warning / Risk 생성 규칙

`repairer.py`는 repair 전처리와 fragment 처리 과정에서 trace를 누적한다.

대표 예시는 다음과 같다.

- `Removed UTF-8 BOM.`
- `Normalized smart double quotes.`
- `Removed wrapping markdown code fence.`
- `Extracted N JSON payload(s) from event stream input.`
- `Skipped [DONE] stream sentinel.`
- `Combined N top-level JSON documents into one array.`
- `Escaped suspicious unescaped quotes inside string content.`

경고와 risk는 heuristic 강도에 따라 올라간다.

- `low`
  - 명백한 문법 정리 수준
- `medium`
  - event stream normalization, concatenated document merge
- `high`
  - string quote heuristic 같이 ambiguity가 높은 보정

## 파일 입력 흐름

### Open File

1. `InputPanel`이 `openFileRequested(last_path)` emit
2. `MainWindow.open_input_file_dialog()`가 dialog open
3. 선택한 파일을 `utf-8-sig`로 읽음
4. `InputPanel.set_last_open_path()` 저장
5. input text에 반영
6. 기존 auto-processing debounce가 그대로 동작

### Drag & Drop

1. `InputPanel`이 local file drop만 허용
2. drop 시 `fileDropped(path)` emit
3. `MainWindow.load_input_file(path)` 재사용

## Font Zoom Persistence

pane별로 각각 저장된다.

- `ui/font_size/input`
- `ui/font_size/output`

입력창과 출력창 모두 `Ctrl + mouse wheel`을 지원하지만 서로 독립적으로 크기가 바뀐다.

## Smoke Test

`app.py`의 `_run_smoke_test()`는 GUI를 띄우지 않고 다음 두 케이스를 검증한다.

- strict format 성공
- repair 성공

결과는 JSON report로 저장할 수 있고, built exe 검증에도 같은 경로를 사용한다.

## 테스트 구성

- `tests/test_services.py`
  - formatter / repairer 동작
  - repair mode
  - stream / fragment / heuristic regression
- `tests/test_input_panel.py`
  - repair mode persistence
  - open button / shortcut
  - drag-drop
  - error highlight
- `tests/test_output_panel.py`
  - summary / warnings / risk badge
  - tree rendering
  - search / path copy
- `tests/test_ui.py`
  - controller integration
  - file open wiring
  - mode change reprocess
  - stale highlight clear
  - font persistence
- `tests/test_smoke.py`
  - headless instantiation
  - smoke runner report

## 확장 포인트

- 대용량 입력은 현재 UI thread에서 처리한다.
  - 필요하면 worker thread와 progress/cancel을 추가할 수 있다.
- tree view는 현재 `QTreeWidget` 기반이다.
  - 대용량 최적화가 필요하면 model/view 구조로 옮길 수 있다.
- risk 계산은 heuristic 기반 상대 지표다.
  - 더 정교한 score 체계를 도입할 수 있다.
- 현재는 JSON schema validation이 없다.
  - 별도 service layer를 추가하면 확장 가능하다.
