# JSON Viewer & Formatter

`JSON Viewer & Formatter`는 `PySide6` 기반 데스크톱 앱입니다. 좌측 입력창에 raw JSON 또는 문법 오류가 있는 JSON 계열 텍스트를 붙여넣으면, 앱이 자동으로 strict format을 먼저 시도하고 실패하면 repair를 수행한 뒤 우측에 결과를 표시합니다.

## 주요 기능

- 좌측 `Raw JSON Input`, 우측 `Formatted / Repaired Output`의 2-pane UI
- 입력 변경 시 자동 처리
- strict JSON이면 즉시 pretty format
- strict parse 실패 시 `json-repair` 기반 repair + 추가 보정 규칙 수행
- 출력창 JSON syntax highlighting
- 입력창과 출력창의 `Ctrl + mouse wheel` 독립 폰트 확대/축소
- pane별 폰트 크기 영속 저장 및 재실행 후 복원
- `Open File` 버튼과 `Ctrl+O` 파일 열기
- 입력 panel drag & drop 파일 로드
- `Strict`, `Safe`, `Aggressive` repair mode 선택 및 재실행 후 복원
- format 실패 위치 입력창 하이라이트
- repair 결과의 `Change Summary`, `Warnings`, `Risk` 표시
- 우측 결과의 `Text View` / `Tree View` 전환
- tree 검색, 선택 경로 표시, `Copy Path`
- `Copy Output` 클립보드 복사
- `Save Output` UTF-8 파일 저장
- standalone Windows `.exe` 빌드와 smoke-test 지원

## Repair Mode

- `Strict`
  - aggressive 복구를 하지 않습니다.
  - 여러 top-level JSON document를 자동으로 배열로 합치지 않습니다.
- `Safe`
  - 기본값입니다.
  - 일반적인 문법 오류와 stream/event payload 정규화를 복구합니다.
- `Aggressive`
  - 더 넓은 heuristic을 허용합니다.
  - 데이터 손실을 줄이기 위한 추가 string quote 보정 등이 활성화될 수 있습니다.

## Output Inspector

repair가 수행되면 우측 output panel에 다음 메타데이터가 함께 표시될 수 있습니다.

- `Change Summary`
  - 예: trailing comma 제거, smart quotes 정규화, stream payload 추출, multiple document array 결합
- `Warnings`
  - 의미가 애매한 입력을 보정했을 때 경고 표시
- `Risk`
  - `Low`, `Medium`, `High`
  - heuristic 강도와 입력 ambiguity를 기준으로 계산

## Tree View

- `Text View`: pretty JSON 텍스트 출력
- `Tree View`: object/array/scalar 구조 탐색
- 검색창으로 key, value, path 검색
- 현재 선택된 JSON path 표시
- `Copy Path`로 선택 path 복사

## 지원 입력 예시

- strict JSON
- trailing comma, single quote, unquoted key, missing bracket
- JSON Lines (`.jsonl`)
- record-separator 기반 JSON text sequence
- SSE `data:` event stream
- markdown code fence로 감싼 JSON
- UTF-8 BOM 포함 입력
- smart quotes가 포함된 입력
- 여러 top-level JSON document가 이어진 입력

## Requirements

- Python 3.14+
- Windows PowerShell
- 반드시 `.venv` 가상환경 사용

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run From Source

```powershell
.\.venv\Scripts\activate
python main.py
```

## Test

```powershell
.\.venv\Scripts\activate
pytest -q
python -m compileall src tests main.py
```

## Build Standalone EXE

```powershell
.\.venv\Scripts\activate
python -m PyInstaller --clean --noconfirm json_formatter.spec
```

빌드 결과물은 `dist\json_formatter.exe` 입니다.

## Smoke Test For Built EXE

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\json_formatter.exe --smoke-test --smoke-output .\dist\smoke-report.json
```

정상 동작 시 종료 코드는 `0`이고, `dist\smoke-report.json`에 smoke-test 결과가 기록됩니다.

## Example Docs

- [doc/single-line-json-example.md](doc/single-line-json-example.md)
- [doc/invalid-json-example.md](doc/invalid-json-example.md)
- [doc/implementation-guide.md](doc/implementation-guide.md)

## Project Structure

- `main.py`: 실행 진입점
- `src/json_formatter/app.py`: 앱 bootstrap, controller, smoke-test
- `src/json_formatter/models.py`: `JsonResult`, `RepairMode`, risk/error metadata
- `src/json_formatter/services/formatter.py`: strict formatter
- `src/json_formatter/services/repairer.py`: repair pipeline, summaries, warnings, risk scoring
- `src/json_formatter/services/processor.py`: format/repair dispatch
- `src/json_formatter/ui/input_panel.py`: 입력 editor, error highlight, file open/drag-drop, repair mode
- `src/json_formatter/ui/output_panel.py`: output editor, summary, warnings, risk badge, text/tree tabs
- `src/json_formatter/ui/json_tree_view.py`: JSON tree rendering and search
- `src/json_formatter/ui/main_window.py`: panel composition, auto-processing, copy/save, font persistence
- `tests/`: service, panel, integration, smoke tests

---

# English Version

`JSON Viewer & Formatter` is a `PySide6` desktop app. Paste raw JSON or malformed JSON-like text into the left input pane and the app will automatically try strict formatting first, then fall back to repair, and render the result on the right.

## Features

- 2-pane UI with `Raw JSON Input` on the left and `Formatted / Repaired Output` on the right
- Automatic processing on input changes
- Immediate pretty formatting for valid strict JSON
- `json-repair` based recovery with extra heuristics when strict parsing fails
- JSON syntax highlighting in the output editor
- Independent `Ctrl + mouse wheel` font zoom for the input and output panes
- Per-pane font size persistence across app restarts
- `Open File` button and `Ctrl+O`
- Drag-and-drop file loading into the input panel
- `Strict`, `Safe`, and `Aggressive` repair modes with persistence
- Input error location highlighting when strict formatting fails
- `Change Summary`, `Warnings`, and `Risk` metadata for repaired results
- `Text View` and `Tree View` output tabs
- Tree search, selected path display, and `Copy Path`
- Clipboard copy with `Copy Output`
- UTF-8 export with `Save Output`
- Standalone Windows `.exe` build and smoke-test support

## Repair Modes

- `Strict`
  - avoids aggressive repair
  - does not merge multiple top-level JSON documents into an array
- `Safe`
  - default mode
  - repairs common syntax issues and clear stream/event payload normalization cases
- `Aggressive`
  - enables broader heuristics
  - can apply stronger string quote correction to preserve more data from malformed input

## Output Inspector

When a repair path is used, the output panel can also show:

- `Change Summary`
  - for example trailing comma cleanup, smart quote normalization, stream payload extraction, and document merging
- `Warnings`
  - shown when ambiguous or higher-risk heuristics were used
- `Risk`
  - `Low`, `Medium`, or `High`
  - derived from the level of heuristics and input ambiguity

## Tree View

- `Text View`: pretty-printed JSON text
- `Tree View`: structured object/array/scalar navigation
- Search by key, value, or path
- Display the currently selected JSON path
- Copy the selected path with `Copy Path`

## Supported Input Examples

- strict JSON
- trailing commas, single quotes, unquoted keys, missing brackets
- JSON Lines (`.jsonl`)
- record-separated JSON text sequences
- SSE `data:` event streams
- markdown-fenced JSON
- UTF-8 BOM-prefixed input
- smart quotes
- concatenated top-level JSON documents

## Requirements

- Python 3.14+
- Windows PowerShell
- Always use the `.venv` virtual environment

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run From Source

```powershell
.\.venv\Scripts\activate
python main.py
```

## Test

```powershell
.\.venv\Scripts\activate
pytest -q
python -m compileall src tests main.py
```

## Build Standalone EXE

```powershell
.\.venv\Scripts\activate
python -m PyInstaller --clean --noconfirm json_formatter.spec
```

The built executable is created at `dist\json_formatter.exe`.

## Smoke Test For Built EXE

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\json_formatter.exe --smoke-test --smoke-output .\dist\smoke-report.json
```

On success, the process exits with code `0` and writes the smoke-test report to `dist\smoke-report.json`.

## Example Docs

- [doc/single-line-json-example.md](doc/single-line-json-example.md)
- [doc/invalid-json-example.md](doc/invalid-json-example.md)
- [doc/implementation-guide.md](doc/implementation-guide.md)

## Project Structure

- `main.py`: entry point
- `src/json_formatter/app.py`: app bootstrap, controller, smoke-test flow
- `src/json_formatter/models.py`: `JsonResult`, `RepairMode`, and risk/error metadata
- `src/json_formatter/services/formatter.py`: strict formatter
- `src/json_formatter/services/repairer.py`: repair pipeline, summaries, warnings, and risk scoring
- `src/json_formatter/services/processor.py`: format/repair dispatch
- `src/json_formatter/ui/input_panel.py`: input editor, error highlight, file open/drag-drop, repair mode
- `src/json_formatter/ui/output_panel.py`: output editor, summary, warnings, risk badge, text/tree tabs
- `src/json_formatter/ui/json_tree_view.py`: JSON tree rendering and search
- `src/json_formatter/ui/main_window.py`: panel composition, auto-processing, copy/save, font persistence
- `tests/`: service, panel, integration, and smoke tests
