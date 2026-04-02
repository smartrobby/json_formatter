# JSON Viewer & Formatter Implementation Guide

이 문서는 `D:\workspace\json_formatter` 프로젝트를 다음 채팅 세션에서 빠르게 다시 이해하기 위한 참고용이다. 현재 앱은 `PySide6` 기반 데스크톱 JSON viewer/formatter이고, 좌측 입력과 우측 출력의 2-pane 구조를 사용한다.

## 목적

- raw JSON 문자열을 입력창에 붙여넣거나 수정하면 자동으로 처리한다.
- strict JSON이면 바로 pretty format 결과를 출력한다.
- strict parse가 실패하면 `json_repair`로 복구를 시도하고, 복구 성공 시 pretty JSON을 출력한다.
- format 또는 repair가 완료된 output pane에는 JSON syntax highlighting을 적용한다.
- 입력창 또는 출력창 위에서 `Ctrl + mouse wheel`을 사용하면 두 pane의 공통 폰트 크기를 조정한다.
- 결과 JSON은 `Copy Output`으로 clipboard에 복사하고 `Save Output`으로 파일로 저장할 수 있다.

## 실행 환경

- Python 가상환경은 반드시 `.venv`를 사용한다.
- Windows 활성화:

```powershell
.\.venv\Scripts\activate
```

- 의존성 설치:

```powershell
python -m pip install -r requirements.txt
```

## 실행 및 테스트

- 앱 실행:

```powershell
python main.py
```

- 테스트:

```powershell
pytest -q
```

- 정적 import/문법 확인:

```powershell
python -m compileall src tests main.py
```

- 빌드:

```powershell
python -m PyInstaller --clean --noconfirm json_formatter.spec
```

- 빌드된 exe smoke-test:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\dist\json_formatter.exe --smoke-test --smoke-output .\dist\smoke-report.json
```

## 프로젝트 구조

- `main.py`: 루트 실행 진입점. `src`를 `sys.path`에 추가한 뒤 `json_formatter.app.main()`을 호출한다.
- `src/json_formatter/app.py`: `QApplication`, `MainWindow`, `JsonFormatterController`, CLI smoke-test를 연결한다.
- `src/json_formatter/ui/main_window.py`: 메인 UI. 좌측 `input_edit`, 우측 `output_edit`, 자동 처리 debounce, `Copy Output`, `Save Output`, status bar를 담당한다.
- `src/json_formatter/ui/highlighter.py`: output pane JSON syntax highlighting을 담당한다.
- `src/json_formatter/services/formatter.py`: strict JSON pretty formatter.
- `src/json_formatter/services/repairer.py`: `json_repair` 기반 복구 + 재검증 + pretty output.
- `src/json_formatter/services/processor.py`: `mode`에 따라 `format` 또는 `repair`를 호출한다.
- `src/json_formatter/models.py`: `JsonResult`, `ProcessMode`, `StatusLabel`.
- `tests/`: service, UI, smoke test.

## 핵심 클래스와 함수

- `JsonFormatterController`
  - `MainWindow.autoProcessRequested`를 받아 자동 처리 흐름을 실행한다.
  - 처리 순서는 `format` 우선, 실패 시 `repair` fallback이다.
  - 둘 다 실패하면 format/repair 에러를 함께 묶어 상태바에 보여준다.
- `MainWindow`
  - `input_edit`는 편집 가능, `output_edit`는 read-only.
  - 입력 변경 시 `QTimer` debounce 후 `autoProcessRequested`를 emit 한다.
  - `output_edit`에는 `JsonSyntaxHighlighter`가 붙어서 key, string, number, literal, punctuation에 색을 입힌다.
  - `Ctrl + mouse wheel`을 입력창이나 출력창 위에서 사용하면 두 pane의 공통 폰트 크기를 함께 조정한다.
  - 결과가 성공일 때만 `Copy Output`, `Save Output`이 활성화된다.
  - `Ctrl+S`는 저장 shortcut이다.
- `ZoomableTextEdit`
  - `Ctrl + wheel` 이벤트를 감지하고 `fontZoomRequested` signal을 emit 한다.
  - 실제 폰트 크기 변경은 `MainWindow.adjust_editor_font_size()`가 공통으로 적용한다.
- `JsonSyntaxHighlighter`
  - key: blue
  - string: green
  - number: orange
  - `true` / `false` / `null`: red
  - braces / brackets / separators: gray
- `format_json(input_text)`
  - `json.loads()`로 strict parse.
  - 성공 시 `json.dumps(indent=2, ensure_ascii=False, sort_keys=False)` 반환.
  - 실패 시 line/column 포함 에러 메시지 반환.
- `repair_json_text(input_text)`
  - `json_repair.repair_json(..., ensure_ascii=False, indent=2)` 사용.
  - 복구 후 `json.loads()`로 다시 검증한다.
  - 복구 실패 시 `Unable to repair JSON: ...` 형태의 메시지를 반환한다.

## 이벤트 흐름

1. 사용자가 좌측 `Raw JSON Input`에 JSON 문자열을 붙여넣거나 수정한다.
2. `MainWindow`가 `textChanged`를 받아 debounce timer를 시작한다.
3. timer 만료 후 `autoProcessRequested`를 emit 한다.
4. `JsonFormatterController`가 strict `format`을 먼저 시도한다.
5. strict `format` 성공 시:
   - 우측 `output_edit`에 pretty JSON을 표시한다.
   - syntax highlighting이 자동 적용된다.
   - 사용자는 이후 `Ctrl + mouse wheel`로 두 pane 폰트 크기를 함께 조절할 수 있다.
   - status는 `Valid JSON`.
   - 기본 저장 파일명은 `formatted.json`.
6. strict `format` 실패 후 `repair` 성공 시:
   - 우측 `output_edit`에 복구된 pretty JSON을 표시한다.
   - syntax highlighting이 자동 적용된다.
   - 사용자는 이후 `Ctrl + mouse wheel`로 두 pane 폰트 크기를 함께 조절할 수 있다.
   - status는 `Repaired JSON`.
   - 기본 저장 파일명은 `repaired.json`.
7. 둘 다 실패 시:
   - 우측 출력은 갱신하지 않는다.
   - status는 `Unable to process input`.
   - error label에 format/repair 실패 메시지를 함께 표시한다.

## Copy / Save 동작

- `Copy Output`
  - 성공 결과가 있을 때만 활성화된다.
  - `QApplication.clipboard().setText(text)`를 사용한다.
- `Save Output`
  - 성공 결과가 있을 때만 활성화된다.
  - `QFileDialog.getSaveFileName()`으로 경로를 선택한 뒤 UTF-8로 저장한다.
  - 마지막 성공 모드에 따라 기본 파일명이 `formatted.json` 또는 `repaired.json`으로 바뀐다.

## 테스트 포인트

- service test
  - valid JSON pretty format.
  - invalid JSON format 에러에 line/column 포함.
  - malformed JSON repair 성공.
  - Unicode 보존.
- UI/controller test
  - 좌우 pane 구성.
  - 우측 출력 read-only.
  - output document에 `JsonSyntaxHighlighter` 연결 여부.
  - `Ctrl + mouse wheel`로 두 pane 폰트 크기 동기 조절 여부.
  - 입력 변경 시 `autoProcessRequested` 발생.
  - valid 입력 자동 format.
  - invalid 입력 자동 repair.
  - save 동작이 실제 파일로 기록되는지 확인.
- smoke test
  - headless 환경에서 `MainWindow` 생성 가능 여부 확인.
  - source 실행과 built exe 양쪽에서 smoke-test CLI 성공 여부 확인.

## 확장 포인트

- output color theme 커스터마이즈
  - `JsonSyntaxHighlighter`의 색상 포맷만 바꾸면 된다.
- debounce interval 조정
  - 현재는 `MainWindow.auto_process_timer`로 제어한다.
- 입력 규모가 큰 경우 백그라운드 worker 도입
  - 현재는 UI thread에서 동기 처리한다.
- input pane highlighting
  - 현재는 output pane만 색상을 적용한다.
- tree view
  - 현재는 text output만 제공한다. 별도 JSON tree pane 추가 가능.
- schema validation
  - `JsonFormatterController` 뒤 또는 별도 service layer로 확장 가능.
