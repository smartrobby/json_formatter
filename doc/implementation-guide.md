# JSON Viewer & Formatter Implementation Guide

이 문서는 `D:\workspace\json_formatter` 프로젝트를 다음 채팅 세션에서 빠르게 다시 이해하기 위한 참고용이다. 현재 앱은 `PySide6` 기반 데스크톱 JSON viewer/formatter이며, 좌측 입력 / 우측 출력의 2-pane 구조를 가진다.

## 목적

- raw JSON 문자열을 붙여 넣고 `Format`으로 pretty print 한다.
- JSON 문법 오류가 있으면 `Repair`로 로컬 규칙 기반 복구를 시도한다.
- 결과 JSON을 `Copy Output`으로 클립보드에 복사하고 `Save Output`으로 파일에 저장한다.

## 실행 환경

- Python 가상환경은 반드시 `.venv`를 사용한다.
- Windows 기준 활성화:

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

## 프로젝트 구조

- `main.py`: `src`를 `sys.path`에 넣고 `json_formatter.app.main()`을 실행하는 루트 진입점.
- `src/json_formatter/app.py`: `QApplication` 생성, `MainWindow` 생성, `JsonFormatterController` 연결.
- `src/json_formatter/ui/main_window.py`: UI 전부. 좌측 입력, 우측 출력, 버튼, status bar, copy/save 동작.
- `src/json_formatter/services/formatter.py`: strict JSON pretty formatter.
- `src/json_formatter/services/repairer.py`: `json_repair` 기반 복구 + 검증 + pretty output.
- `src/json_formatter/services/processor.py`: `mode`에 따라 `format` 또는 `repair`로 라우팅.
- `src/json_formatter/models.py`: `JsonResult`, `ProcessMode`, `StatusLabel`.
- `tests/`: 서비스, UI, smoke 테스트.

## 핵심 클래스와 함수

- `JsonFormatterController`
  - `formatRequested`, `repairRequested` 시그널을 받아 처리한다.
  - `process_json()`를 호출하고 결과를 `MainWindow`에 반영한다.
- `MainWindow`
  - 좌측 `input_edit`는 편집 가능.
  - 우측 `output_edit`는 read-only.
  - `Format`, `Repair`, `Copy Output`, `Save Output` 버튼을 제공한다.
  - `Ctrl+Enter`는 format, `Ctrl+Shift+Enter`는 repair, `Ctrl+S`는 save.
- `format_json(input_text)`
  - `json.loads()`로 strict parse.
  - 성공 시 `json.dumps(indent=2, ensure_ascii=False, sort_keys=False)` 반환.
  - 실패 시 line/column 포함 에러를 `JsonResult`로 반환.
- `repair_json_text(input_text)`
  - `json_repair.repair_json(..., ensure_ascii=False, indent=2)` 사용.
  - 복구 결과를 `json.loads()`로 다시 검증한다.
  - 복구 실패 시 `Unable to repair JSON: ...` 형태로 반환한다.

## 이벤트 흐름

1. 사용자가 좌측 `input_edit`에 JSON 문자열을 넣는다.
2. `Format` 또는 `Repair` 버튼을 누르거나 단축키를 누른다.
3. `MainWindow`가 `formatRequested` 또는 `repairRequested`를 emit 한다.
4. `JsonFormatterController`가 `process_json(input_text, mode)`를 호출한다.
5. 성공하면:
   - 우측 `output_edit`에 pretty JSON이 들어간다.
   - status bar가 `Valid JSON` 또는 `Repaired JSON`으로 갱신된다.
   - `Copy Output`, `Save Output`이 활성화된다.
6. 실패하면:
   - 우측 출력은 유지되거나 비워질 수 있다.
   - status bar는 `Format failed` 또는 `Repair failed`가 된다.
   - error label에 구체적인 메시지가 표시된다.

## Format vs Repair

- `Format`
  - 오직 strict JSON만 허용한다.
  - syntax error가 있으면 자동 수정하지 않는다.
  - 에러 메시지는 line/column 정보를 포함한다.
- `Repair`
  - 일반적인 깨진 JSON을 최대한 복구한다.
  - 예시: single quotes, trailing commas, unquoted keys 같은 문제를 처리할 수 있다.
  - 복구 후에도 `json.loads()`로 다시 검증하므로, 결과가 실제 JSON이 아닌 경우는 실패로 처리한다.

## Copy / Save 동작

- `Copy Output`
  - 성공 결과가 있을 때만 활성화된다.
  - `QApplication.clipboard().setText(text)`를 사용한다.
- `Save Output`
  - 성공 결과가 있을 때만 활성화된다.
  - `QFileDialog.getSaveFileName()`으로 경로를 고른 뒤 UTF-8로 저장한다.
  - 기본 파일명은 format 성공 시 `formatted.json`, repair 성공 시 `repaired.json`이다.

## 테스트 포인트

- 서비스 테스트
  - 유효한 JSON이 2-space pretty output으로 출력되는지 확인한다.
  - invalid JSON에서 line/column 에러가 나오는지 확인한다.
  - repair가 대표적인 malformed JSON을 복구하는지 확인한다.
  - Unicode가 `ensure_ascii=False`로 유지되는지 확인한다.
- UI 테스트
  - 좌우 pane이 존재하는지 확인한다.
  - 우측 출력이 read-only인지 확인한다.
  - 버튼 enable/disable 상태가 올바른지 확인한다.
  - save 동작이 실제 파일로 저장되는지 확인한다.
- smoke 테스트
  - headless 환경에서 `MainWindow`가 생성되는지 확인한다.

## 확장 포인트

- 실시간 자동 미리보기
  - 현재는 버튼 기반이다.
  - 입력 debounce를 추가하면 자동 preview로 확장할 수 있다.
- JSON tree view
  - 현재는 텍스트 viewer다.
  - 우측 출력 대신 트리 구조 렌더링을 붙일 수 있다.
- syntax highlighting
  - `QSyntaxHighlighter`를 추가하면 가독성을 높일 수 있다.
- schema validation
  - `process_json()` 앞단 또는 별도 서비스로 확장 가능하다.

## 주의 사항

- 이 프로젝트는 `src` 레이아웃을 사용하므로 `python main.py` 또는 `pytest` 실행 시 루트 기준으로 동작을 확인한다.
- `doc/implementation-guide.md`는 코드의 현재 상태를 설명하는 문서다. 구현이 바뀌면 같이 갱신해야 한다.

