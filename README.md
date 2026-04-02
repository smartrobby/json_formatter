# JSON Viewer & Formatter

`JSON Viewer & Formatter`는 raw JSON 문자열을 붙여넣거나 수정하면 자동으로 pretty format 또는 repair를 수행해서 우측 pane에 결과를 보여주는 `PySide6` 데스크톱 앱이다.

## Features

- 좌측 `Raw JSON Input`, 우측 `Formatted / Repaired Output`의 2-pane UI
- 입력 변경 시 자동 처리
- strict JSON이면 자동 pretty format
- strict parse 실패 시 `json-repair` 기반 자동 repair
- output pane의 JSON syntax highlighting
  - key: blue
  - string: green
  - number: orange
  - `true` / `false` / `null`: red
  - braces / brackets / separators: gray
- `Ctrl + mouse wheel` over either JSON pane to zoom the shared editor font size
- `Copy Output`으로 clipboard 복사
- `Save Output`으로 UTF-8 JSON 파일 저장
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

입력창에 JSON을 붙여넣으면 앱이 자동으로 `format -> repair fallback` 순서로 처리한다.
입력창이나 출력창 위에서 `Ctrl + mouse wheel`을 사용하면 두 pane의 공통 폰트 크기를 확대/축소할 수 있다.

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

빌드 결과물은 `dist\json_formatter.exe`에 생성된다.

## Smoke Test For Built EXE

빌드된 `.exe`는 GUI 실행 외에 검증용 smoke-test 모드를 지원한다.

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\json_formatter.exe --smoke-test --smoke-output .\dist\smoke-report.json
```

정상 동작 시 종료 코드는 `0`이고, `dist\smoke-report.json`에는 format 케이스와 repair 케이스 결과가 기록된다.

## Example Docs

- 자동 pretty format 테스트용 예제: [doc/single-line-json-example.md](doc/single-line-json-example.md)
- 자동 repair 테스트용 예제: [doc/invalid-json-example.md](doc/invalid-json-example.md)
- 구현 참고 문서: [doc/implementation-guide.md](doc/implementation-guide.md)

## Project Structure

- `main.py`: 실행 진입점
- `src/json_formatter/app.py`: 앱 부트스트랩, controller, smoke-test
- `src/json_formatter/ui/main_window.py`: 메인 UI
- `src/json_formatter/ui/highlighter.py`: output pane syntax highlighting
- `src/json_formatter/services/formatter.py`: strict formatter
- `src/json_formatter/services/repairer.py`: repair logic
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
- `Ctrl + mouse wheel` over either JSON pane to zoom the shared editor font size
- Clipboard copy with `Copy Output`
- UTF-8 file export with `Save Output`
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

When you paste JSON into the input pane, the app automatically runs `format -> repair fallback`.
When you use `Ctrl + mouse wheel` over either editor, both panes update to the same larger or smaller font size.

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
- `src/json_formatter/ui/main_window.py`: main UI
- `src/json_formatter/ui/highlighter.py`: output pane syntax highlighting
- `src/json_formatter/services/formatter.py`: strict formatter
- `src/json_formatter/services/repairer.py`: repair logic
- `tests/`: service, UI, and smoke tests
