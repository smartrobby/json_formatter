# JSON Viewer & Formatter

`JSON Viewer & Formatter`는 raw JSON 문자열을 붙여넣으면 자동으로 pretty format 또는 repair를 수행하고, 결과를 오른쪽 pane에 표시하는 `PySide6` 데스크톱 앱입니다.

## Features

- 좌측 `Raw JSON Input`, 우측 `Formatted / Repaired Output`의 2-pane UI
- 입력 변경 시 자동 처리
- strict JSON이면 즉시 pretty format
- strict parse 실패 시 `json-repair` 기반 repair
- output pane JSON syntax highlighting
  - key: blue
  - string: green
  - number: orange
  - `true` / `false` / `null`: red
  - braces / brackets / separators: gray
- `Ctrl + mouse wheel`로 pane별 폰트 크기 조절
  - 입력창과 출력창이 서로 독립적으로 확대/축소됨
  - 각 pane의 마지막 폰트 크기가 앱 재실행 후에도 유지됨
- `Copy Output`으로 clipboard 복사
- `Save Output`으로 UTF-8 JSON 파일 저장
- 데이터 손실을 줄이기 위한 강화된 JSON repair
  - 여러 top-level JSON 블록을 모두 추출해 JSON 배열로 출력
  - JSON Lines(`.jsonl`)와 record-separator 기반 JSON text sequence 입력 처리
  - SSE `data:` stream payload를 메시지 단위로 추출하고 `[DONE]` sentinel 무시
  - wrapping markdown code fence, UTF-8 BOM, NUL 문자를 정리
  - smart quotes를 일반 double quote로 정규화
  - HTML 같은 긴 string 값 안의 미escaped quote로 key/value가 잘리는 경우를 완화
- standalone Windows `.exe` 빌드 및 smoke-test 지원

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

입력창에 JSON을 붙여넣으면 앱이 자동으로 `format -> repair fallback` 순서로 처리합니다. 입력창이나 출력창 위에서 `Ctrl + mouse wheel`을 사용하면 각 pane의 폰트 크기를 개별적으로 조절할 수 있고, 재실행 후에도 복원됩니다.

## Repair Notes

다음과 같은 입력도 가능한 한 원본 데이터 손실을 줄이는 방향으로 복구합니다.

- trailing comma, single quote, unquoted key, missing bracket
- 여러 JSON object가 이어붙은 stream 입력
- `data:` prefix가 반복되는 SSE/event stream 입력
- JSON Lines / JSON text sequence 입력
- markdown code fence로 감싼 JSON
- UTF-8 BOM이나 smart quotes가 섞인 입력
- HTML/string payload 안의 잘못된 quote 때문에 key가 잘리는 입력

복구 결과가 여러 JSON document를 포함하면 output pane에는 JSON 배열 형태로 표시됩니다.

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

빌드 결과물은 `dist\json_formatter.exe`에 생성됩니다.

## Smoke Test For Built EXE

빌드된 `.exe`는 GUI 실행 외에 smoke-test 모드를 지원합니다.

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\json_formatter.exe --smoke-test --smoke-output .\dist\smoke-report.json
```

정상 동작 시 종료 코드는 `0`이고, `dist\smoke-report.json`에는 format 케이스와 repair 케이스 결과가 기록됩니다.

## Example Docs

- 자동 pretty format 테스트 예제: [doc/single-line-json-example.md](doc/single-line-json-example.md)
- 자동 repair 테스트 예제: [doc/invalid-json-example.md](doc/invalid-json-example.md)
- 구현 참고 문서: [doc/implementation-guide.md](doc/implementation-guide.md)

## Project Structure

- `main.py`: 실행 진입점
- `src/json_formatter/app.py`: 앱 부트스트랩, controller, smoke-test
- `src/json_formatter/ui/main_window.py`: 메인 UI와 per-pane font persistence
- `src/json_formatter/ui/highlighter.py`: output pane syntax highlighting
- `src/json_formatter/services/formatter.py`: strict formatter
- `src/json_formatter/services/repairer.py`: enhanced repair pipeline
- `tests/`: service, UI, smoke test

---

# English Version

`JSON Viewer & Formatter` is a `PySide6` desktop app that automatically pretty-formats or repairs raw JSON input and shows the result in the right-side output pane.

## Features

- 2-pane UI with `Raw JSON Input` on the left and `Formatted / Repaired Output` on the right
- Automatic processing when the input changes
- Automatic pretty formatting for valid strict JSON
- Automatic repair with `json-repair` when strict parsing fails
- JSON syntax highlighting in the output pane
  - keys: blue
  - strings: green
  - numbers: orange
  - `true` / `false` / `null`: red
  - braces / brackets / separators: gray
- Per-pane font zoom with `Ctrl + mouse wheel`
  - the input and output panes zoom independently
  - the last font size for each pane is restored after app restart
- Clipboard copy with `Copy Output`
- UTF-8 file export with `Save Output`
- Enhanced low-loss JSON repair
  - combines multiple top-level JSON documents into one JSON array
  - handles JSON Lines and record-separator JSON text sequences
  - extracts JSON payloads from SSE `data:` streams and skips `[DONE]`
  - strips wrapping markdown code fences, UTF-8 BOM, and NUL characters
  - normalizes smart quotes to standard double quotes
  - reduces accidental key splitting when broken quotes appear inside long string values such as HTML
- Standalone Windows `.exe` build and smoke-test support

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

When you paste JSON into the input pane, the app automatically runs `format -> repair fallback`. When you use `Ctrl + mouse wheel` over the input or output editor, only that pane changes size, and the size is restored on the next launch.

## Repair Notes

The repair path is designed to preserve as much original data as possible for malformed inputs such as:

- trailing commas, single quotes, unquoted keys, and missing brackets
- concatenated top-level JSON objects
- SSE or event-stream payloads with repeated `data:` lines
- JSON Lines and JSON text sequences
- markdown code fences around JSON
- UTF-8 BOM or smart quotes
- broken HTML or other long string payloads with unescaped quotes

If the input contains multiple JSON documents, the output pane renders them as a JSON array.

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

The built `.exe` supports a smoke-test mode in addition to normal GUI execution.

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\json_formatter.exe --smoke-test --smoke-output .\dist\smoke-report.json
```

On success, the process exits with code `0`, and `dist\smoke-report.json` contains both the format case and the repair case results.

## Example Docs

- Auto pretty-format test example: [doc/single-line-json-example.md](doc/single-line-json-example.md)
- Auto repair test example: [doc/invalid-json-example.md](doc/invalid-json-example.md)
- Implementation reference: [doc/implementation-guide.md](doc/implementation-guide.md)

## Project Structure

- `main.py`: application entry point
- `src/json_formatter/app.py`: app bootstrap, controller, and smoke-test flow
- `src/json_formatter/ui/main_window.py`: main UI and per-pane font persistence
- `src/json_formatter/ui/highlighter.py`: output pane syntax highlighting
- `src/json_formatter/services/formatter.py`: strict formatter
- `src/json_formatter/services/repairer.py`: enhanced repair pipeline
- `tests/`: service, UI, and smoke tests
