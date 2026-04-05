# JSON Viewer & Formatter Implementation Guide

이 문서는 현재 `dev-robby` 기준 구현을 빠르게 다시 파악하기 위한 참고 문서입니다.

## 개요

- 앱은 `InputPanel` + `OutputPanel` + `MainWindow` composition 구조입니다.
- 입력이 바뀌면 debounce 후 strict format을 먼저 시도하고, 실패하면 현재 `repair_mode`로 repair를 수행합니다.
- repair 성공 시 `Change Summary`, `Warnings`, `Risk`는 `Raw JSON Input` 아래에 표시됩니다.
- output pane은 `Text View` / `Tree View` 중심으로 유지됩니다.
- 전역 `수정 표시` 토글은 input/output diff overlay만 제어하며 기본값은 `off`입니다.

## 실행 및 검증

프로젝트 루트의 `.venv`를 사용합니다.

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

## 주요 구성 요소

### `src/json_formatter/app.py`

- `QApplication` 생성
- `JsonFormatterController` 정의
- `autoProcessRequested` 수신 후 format / repair 수행
- 결과를 `MainWindow`에 반영
- smoke-test 실행 경로 제공

### `src/json_formatter/ui/main_window.py`

- toolbar, splitter, status bar 구성
- `Language`, `Theme`, `수정 표시`, `Copy Output`, `Save Output` 관리
- `InputPanel` / `OutputPanel` 연결
- input 변경 시 auto-process debounce
- `Ctrl+F`를 현재 포커스된 view의 search bar로 라우팅
- pane별 font zoom persistence 관리

현재 기본 동작:

- `수정 표시` 기본값: `off`
- 초기 창 크기: 기존 기본값 유지
- repair metadata 전달 위치: `InputPanel`

### `src/json_formatter/ui/input_panel.py`

- raw input editor
- `Open File`, `Ctrl+O`, drag & drop
- repair mode selector
- parse error highlight
- input diff highlight
- input search bar
- repair metadata block
  - `Change Summary`
  - `Warnings`
  - `Risk`

메타데이터 블록은 input editor 아래에 위치하며, repair 성공 시만 표시됩니다.

### `src/json_formatter/ui/output_panel.py`

- output text editor
- `Text View` / `Tree View`
- output diff highlight
- text search / tree search
- `Expand All`, `Collapse All`
- `Copy Path`

이 panel은 결과 확인과 탐색에 집중하며, repair metadata는 더 이상 여기서 표시하지 않습니다.

### `src/json_formatter/ui/json_tree_view.py`

- `QTreeWidget` 기반 JSON tree 렌더링
- key / value / path 검색
- subtree expand / collapse context menu
- tree populate 후 `Key` 컬럼 폭을 기본 section width 대비 3배로 확장

### Services

- `formatter.py`
  - strict `json.loads()`
  - format 성공 시 pretty output
  - 실패 시 line / column / index metadata 반환
- `repairer.py`
  - repair pipeline
  - `UiMessage` 기반 summary / warning / risk 생성
  - `strict`, `safe`, `aggressive` mode 처리
- `repair_diff.py`
  - input/output token sequence 비교
  - diff highlight span 계산

## UI 흐름

1. 사용자가 input pane에 텍스트를 붙여 넣거나 수정
2. debounce 후 controller가 strict format 시도
3. strict format 성공
   - output text/tree 갱신
   - input error, diff, metadata 초기화
4. strict format 실패 후 repair 성공
   - output text/tree 갱신
   - input 아래 summary / warnings / risk 표시
   - diff span 저장
   - `수정 표시`가 `on`일 때만 input/output diff overlay 표시
5. strict format / repair 모두 실패
   - input error highlight 표시
   - output 및 metadata clear

## Search / Highlight 우선순위

input/output text editor highlight 우선순위:

1. parse error
2. active search match
3. repair diff
4. passive search matches

`수정 표시`를 끄면 diff overlay만 숨기고 search / error highlight는 유지합니다.

## Settings

`QSettings`로 유지되는 값:

- `ui/font_size/input`
- `ui/font_size/output`
- `ui/language`
- `ui/theme`
- `ui/repair_mode`
- `ui/last_open_path`

세션 메모리 상태만 유지되는 값:

- 전역 `수정 표시` on/off
- 마지막 repair diff

## 테스트 포인트

- `tests/test_ui.py`
  - main window wiring
  - diff toggle 기본값과 세션 유지
  - controller format / repair 흐름
  - metadata 위치 변경 반영
- `tests/test_input_panel.py`
  - file open / drag-drop
  - search / error / diff 공존
  - summary / warnings / risk 렌더링
- `tests/test_output_panel.py`
  - text/tree search
  - diff highlight
  - tree expand / collapse
  - widened key column
