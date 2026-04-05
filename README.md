# JSON Viewer & Formatter

`JSON Viewer & Formatter`는 `PySide6` 기반 데스크톱 앱입니다. 왼쪽 `Raw JSON Input`에 raw JSON 또는 문법 오류가 있는 JSON 계열 텍스트를 붙여 넣으면, 앱이 먼저 strict format을 시도하고 실패하면 repair를 수행한 뒤 오른쪽 `Formatted / Repaired Output`에 결과를 표시합니다.

## 한국어 버전

### 주요 기능

- 좌측 `Raw JSON Input`, 우측 `Formatted / Repaired Output`의 2-pane UI
- 입력 변경 시 자동 format / repair
- `Korean` 기본, `English` 전환 지원
- `System`, `Light`, `Dark` 테마 전환 지원
- `Strict`, `Safe`, `Aggressive` repair mode 지원
- strict parse 실패 위치 input pane 하이라이트
- repaired 결과의 변경 token을 input/output 양쪽에서 반전 강조
- 전역 `수정 표시` 버튼으로 diff highlight on/off
- `수정 표시` 기본값은 `off`, 현재 실행 세션 동안 상태 유지
- `Change Summary`, `Warnings`, `Risk`는 `Raw JSON Input` 아래에 표시
- output pane은 `Text View` / `Tree View` 중심으로 더 크게 표시
- input / output / tree 각각 `Ctrl+F` 및 search button 기반 inline search
- `Tree View` 전체 `Expand All` / `Collapse All`
- tree node 우클릭 `Expand Subtree` / `Collapse Subtree`
- `Tree View`의 `Key` 컬럼 폭 확장
- `Open File`, `Ctrl+O`, drag & drop 지원
- pane별 `Ctrl + mouse wheel` 폰트 확대/축소 및 크기 유지
- `Copy Output`, `Save Output`
- standalone Windows `.exe` 빌드 및 smoke-test 지원

### 현재 레이아웃 변경점

- `수정 표시` 기본값이 `off`로 바뀌었습니다.
- repair 메타데이터 블록(`Change Summary`, `Warnings`, `Risk`)이 output pane에서 input pane 아래로 이동했습니다.
- output pane은 결과 확인용 영역으로 단순화되었습니다.
- `Tree View`의 첫 번째 `Key` 컬럼은 기본 폭보다 더 넓게 표시됩니다.

### Repair Mode

- `Strict`
  - 공격적인 heuristic을 거의 사용하지 않습니다.
  - 여러 top-level JSON document를 자동으로 배열로 합치지 않습니다.
- `Safe`
  - 기본값입니다.
  - 일반적인 문법 오류와 명확한 stream / payload 정규화를 복구합니다.
- `Aggressive`
  - 더 넓은 heuristic을 허용합니다.
  - ambiguity가 있는 입력에서도 데이터 유실을 줄이기 위한 복구를 시도합니다.

### Search / Diff Highlight

- `Ctrl+F` 또는 각 pane의 `Search` 버튼으로 inline search bar를 엽니다.
- text search는 case-insensitive substring 검색입니다.
- `Enter`는 다음 결과, `Shift+Enter`는 이전 결과로 이동합니다.
- repair가 수행되면 raw input과 repaired output의 변경 token을 반전 강조합니다.
- highlight 우선순위는 `error > active search > repair diff > passive search` 입니다.

### Tree View

- `Text View`: pretty JSON 텍스트 출력
- `Tree View`: object / array / scalar 구조 탐색
- key / value / path 검색
- 현재 선택된 JSON path 표시
- `Copy Path`
- `Expand All`, `Collapse All`
- 우클릭 context menu로 subtree 확장 / 축소

### 실행 환경

- Python 3.14+
- Windows PowerShell
- 항상 `.venv` 가상환경 사용

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Run From Source

```powershell
.\.venv\Scripts\activate
python main.py
```

### Test

```powershell
.\.venv\Scripts\activate
pytest -q
python -m compileall src tests main.py
```

### Build Standalone EXE

```powershell
.\.venv\Scripts\activate
python -m PyInstaller --clean --noconfirm json_formatter.spec
```

빌드 결과물은 `dist\json_formatter.exe` 입니다.

### Smoke Test For Built EXE

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\json_formatter.exe --smoke-test --smoke-output .\dist\smoke-report.json
```

성공 시 종료 코드는 `0`이고, `dist\smoke-report.json`에 smoke-test 결과가 저장됩니다.

### Documents

- 구현 가이드: [doc/implementation-guide.md](doc/implementation-guide.md)
- 코드 참조: [doc/code-ref.md](doc/code-ref.md)
- 테스트 데이터 설명: [test_data/README.md](test_data/README.md)

### Project Structure

- `main.py`: 실행 진입점
- `src/json_formatter/app.py`: app bootstrap, controller, smoke-test flow
- `src/json_formatter/models.py`: `JsonResult`, `UiMessage`, `RepairDiff`, `RepairMode`, `UiLanguage`, `ThemeMode`
- `src/json_formatter/services/formatter.py`: strict formatter
- `src/json_formatter/services/repairer.py`: repair pipeline, summary / warning / risk 계산
- `src/json_formatter/services/repair_diff.py`: repair diff span 계산
- `src/json_formatter/services/processor.py`: format / repair dispatch
- `src/json_formatter/ui/input_panel.py`: input editor, error highlight, repair metadata, file open, drag-drop, repair mode, search
- `src/json_formatter/ui/output_panel.py`: output editor, text/tree tabs, diff highlight, search
- `src/json_formatter/ui/json_tree_view.py`: JSON tree rendering, search, subtree control
- `src/json_formatter/ui/localization.py`: ko/en string catalog
- `src/json_formatter/ui/theme.py`: theme palette
- `src/json_formatter/ui/search_bar.py`: reusable inline search bar
- `src/json_formatter/ui/main_window.py`: panel composition, toolbar, auto-processing, copy/save, diff toggle

---

## English Version

`JSON Viewer & Formatter` is a `PySide6` desktop app. Paste raw JSON or malformed JSON-like text into the left input pane and the app will first try strict formatting, then fall back to repair, and render the result on the right.

### Features

- 2-pane UI with `Raw JSON Input` on the left and `Formatted / Repaired Output` on the right
- Automatic format / repair on input changes
- UI language switcher with `Korean` default and `English`
- Theme switcher with `System`, `Light`, and `Dark`
- `Strict`, `Safe`, and `Aggressive` repair modes
- Input error highlighting for strict parse failures
- Token-level reverse-highlight for repaired spans in both raw input and repaired output
- Global `Diff Highlight` toggle for input/output diff overlays
- `Diff Highlight` defaults to `off` and persists for the current app session
- Repair metadata (`Change Summary`, `Warnings`, `Risk`) is rendered below `Raw JSON Input`
- The output pane is kept larger and focused on `Text View` / `Tree View`
- Inline search bars for input, output text, and tree via `Ctrl+F` or search buttons
- Tree-wide `Expand All` / `Collapse All`
- Context-menu `Expand Subtree` / `Collapse Subtree`
- Widened `Key` column in `Tree View`
- `Open File`, `Ctrl+O`, and drag-and-drop support
- Per-pane `Ctrl + mouse wheel` font zoom with persistent sizes
- `Copy Output`, `Save Output`
- Standalone Windows `.exe` build and smoke-test support

### Repair Modes

- `Strict`
  - avoids aggressive heuristics
  - does not merge multiple top-level JSON documents into an array
- `Safe`
  - default mode
  - repairs common syntax issues and clear stream / payload normalization cases
- `Aggressive`
  - enables broader heuristics
  - prioritizes preserving data from ambiguous malformed input

### Search / Diff Highlight

- Open inline search with `Ctrl+F` or the view-specific `Search` buttons.
- Text search is case-insensitive substring matching.
- `Enter` moves to the next match and `Shift+Enter` moves to the previous match.
- When repair is used, changed tokens are reverse-highlighted in both the raw input pane and the repaired output text pane.
- Overlay priority is `error > active search > repair diff > passive search`.

### Tree View

- `Text View`: pretty-printed JSON text
- `Tree View`: structured object / array / scalar navigation
- Search by key, value, or path
- Display the currently selected JSON path
- `Copy Path`
- `Expand All` and `Collapse All`
- Right-click context menu for subtree expand / collapse

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Run From Source

```powershell
.\.venv\Scripts\activate
python main.py
```

### Test

```powershell
.\.venv\Scripts\activate
pytest -q
python -m compileall src tests main.py
```

### Build Standalone EXE

```powershell
.\.venv\Scripts\activate
python -m PyInstaller --clean --noconfirm json_formatter.spec
```

The built executable is `dist\json_formatter.exe`.
