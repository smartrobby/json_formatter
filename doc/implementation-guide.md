# JSON Viewer & Formatter Implementation Guide

이 문서는 `D:\workspace\json_formatter` 프로젝트를 다음 채팅 세션에서 빠르게 다시 이해하기 위한 참고 문서다. 현재 앱은 `PySide6` 기반 데스크톱 JSON viewer/formatter이고, 좌측 입력과 우측 출력의 2-pane 구조를 사용한다.

## 목적

- raw JSON 문자열을 입력창에 붙여넣거나 수정하면 자동으로 처리한다.
- strict JSON이면 바로 pretty format 결과를 출력한다.
- strict parse가 실패하면 `json_repair`와 추가 전처리 규칙으로 복구를 시도한다.
- 여러 JSON document가 섞여 있으면 가능한 한 모두 살려 JSON 배열로 출력한다.
- output pane에는 JSON syntax highlighting을 적용한다.
- 입력창과 출력창은 각각 `Ctrl + mouse wheel`로 독립적인 폰트 크기 조절이 가능하다.
- 각 pane의 마지막 폰트 크기는 `QSettings`로 저장되어 앱 재실행 후에도 복원된다.
- 결과 JSON은 `Copy Output`으로 clipboard에 복사하고 `Save Output`으로 파일로 저장할 수 있다.

## 실행 환경

- Python 가상환경은 반드시 `.venv`를 사용한다.
- Windows PowerShell 기준 실행:

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

- 전체 테스트:

```powershell
pytest -q
```

- 정적 import/문법 확인:

```powershell
python -m compileall src tests main.py
```

- standalone exe 빌드:

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
- `src/json_formatter/ui/main_window.py`: 메인 UI. 좌측 `input_edit`, 우측 `output_edit`, 자동 처리 debounce, per-pane font persistence, `Copy Output`, `Save Output`, status bar를 담당한다.
- `src/json_formatter/ui/highlighter.py`: output pane JSON syntax highlighting을 담당한다.
- `src/json_formatter/services/formatter.py`: strict JSON pretty formatter.
- `src/json_formatter/services/repairer.py`: 전처리 + fragment 추출 + `json_repair` 기반 복구 파이프라인.
- `src/json_formatter/services/processor.py`: `mode`에 따라 `format` 또는 `repair`를 호출한다.
- `src/json_formatter/models.py`: `JsonResult`, `ProcessMode`, `StatusLabel`.
- `tests/`: service, UI, smoke test.

## 주요 동작 흐름

### 자동 처리

1. 사용자가 좌측 `Raw JSON Input`에 JSON 문자열을 붙여넣거나 수정한다.
2. `MainWindow`가 `textChanged`를 받아 debounce timer를 시작한다.
3. timer 만료 후 `autoProcessRequested`를 emit 한다.
4. `JsonFormatterController`가 strict `format`을 먼저 시도한다.
5. strict `format` 성공 시:
   - 우측 `output_edit`에 pretty JSON을 표시한다.
   - syntax highlighting이 자동 적용된다.
   - status는 `Valid JSON`.
   - 기본 저장 파일명은 `formatted.json`.
6. strict `format` 실패 후 `repair` 성공 시:
   - 우측 `output_edit`에 복구된 pretty JSON을 표시한다.
   - syntax highlighting이 자동 적용된다.
   - status는 `Repaired JSON`.
   - 기본 저장 파일명은 `repaired.json`.
7. 둘 다 실패하면:
   - status는 `Unable to process input`.
   - error label에 format/repair 실패 메시지를 함께 표시한다.

### 폰트 저장 흐름

1. `create_application()`이 `smartrobby` organization name과 앱 이름을 설정한다.
2. `MainWindow` 초기화 시 `QSettings()`를 만들고 저장된 input/output 폰트 크기를 읽는다.
3. 저장값이 없거나 잘못된 경우 기본값 `10pt`를 사용한다.
4. 입력창 위에서 `Ctrl + mouse wheel`을 사용하면 입력창 크기만 변경되고 `ui/font_size/input`에 즉시 저장된다.
5. 출력창 위에서 `Ctrl + mouse wheel`을 사용하면 출력창 크기만 변경되고 `ui/font_size/output`에 즉시 저장된다.
6. 다음 실행 시 두 pane는 각각 마지막 저장값으로 복원된다.

## Repair 파이프라인

`repair_json_text()`는 데이터 손실을 줄이기 위해 단일 `json_repair()` 호출만 사용하지 않고, 여러 단계의 정규화와 복구를 수행한다.

### 1. 입력 전처리

`_prepare_repair_input()`이 다음 정규화를 수행한다.

- UTF-8 BOM(`U+FEFF`) 제거
- NUL 문자 제거
- JSON text sequence의 record separator(`0x1E`)를 줄바꿈으로 변환
- smart double quotes를 일반 `"`로 정규화
- 전체 입력이 markdown code fence로 감싸져 있으면 내부 JSON 본문만 추출
- SSE/event stream처럼 보이면 `data:` payload를 메시지 단위로 재구성
- 문자열 내부의 미escaped quote를 가능한 범위에서 escape 처리

### 2. SSE / event stream 정규화

`_normalize_event_stream_text()`는 `text/event-stream` 형태 입력을 처리한다.

- `data:` 라인을 메시지 payload로 모은다.
- 빈 줄이 나오면 하나의 메시지를 종료한다.
- `event:`, `id:`, `retry:` 필드는 무시한다.
- `:` 로 시작하는 comment line은 무시한다.
- JSON payload가 여러 개 있는 경우 `[DONE]` sentinel은 버린다.
- 결과는 payload block들의 텍스트로 다시 반환된다.

이 단계는 공식 SSE 형식과 실제 API stream 입력을 기준으로 넣었다.

### 3. fragment 추출

`_extract_json_fragments()`는 전처리 후 텍스트에서 top-level object/array fragment를 모두 찾는다.

- 여러 JSON object가 이어붙은 경우 각 object를 별도 fragment로 분리한다.
- JSON Lines, repeated payload stream, concatenated object log 같은 입력을 모두 여기서 흡수한다.
- fragment가 여러 개면 모두 유지하고, 최종 출력은 JSON 배열로 묶는다.

### 4. fragment별 복구

`_repair_extracted_fragments()`는 각 fragment를 별도로 복구한다.

- 각 fragment에 `repair_json(..., stream_stable=True)`를 적용한다.
- 복구된 문자열을 `json.loads()`로 다시 검증한다.
- fragment가 하나면 단일 value를 출력하고, 여러 개면 배열을 출력한다.

이 단계가 성공하면 fragment 기준 결과를 그대로 사용한다.

### 5. 단일 패스 fallback

fragment 복구가 불가능한 경우 전체 입력에 대해 `repair_json(..., stream_stable=True, indent=2)`를 수행한다.

- 복구 결과는 다시 `json.loads()`로 검증한다.
- 성공 시 pretty JSON으로 다시 직렬화한다.
- 실패 시 line/column 포함 에러 메시지를 반환한다.

## 현재 복구 가능한 대표 입력

- trailing comma
- single quote 기반 pseudo JSON
- unquoted key
- missing closing bracket or brace
- 여러 top-level JSON object가 이어붙은 입력
- JSON Lines(`.jsonl`) 입력
- JSON text sequence(`0x1E` prefix) 입력
- SSE `data:` stream 입력
- markdown code fence 내부 JSON
- UTF-8 BOM 포함 입력
- smart quotes가 섞인 입력
- HTML 같은 긴 string 안의 깨진 quote로 인해 key/value가 잘리던 입력

## 주의점

- 복구는 항상 원본을 완벽하게 재구성할 수 있는 작업이 아니다.
- 특히 미escaped quote가 많은 긴 문자열은 휴리스틱으로 보정하므로, 손실 가능성은 줄였지만 100% 보존을 보장하지는 않는다.
- 여러 document를 배열로 합치는 동작은 원본이 단일 document가 아니라는 신호를 보존하기 위한 선택이다.

## 테스트 범위

### service test

- valid JSON pretty format
- invalid JSON format 에러의 line/column 포함 여부
- trailing comma, single quote, unquoted key 복구
- Unicode 보존
- 여러 top-level object를 배열로 결합하는지 확인
- 기존 valid array document 보존
- `data:` prefix payload 여러 개를 배열로 추출하는지 확인
- BOM 제거
- smart quotes 정규화
- SSE stream과 `[DONE]` sentinel 처리
- HTML/string payload가 가짜 key로 분해되지 않는지 확인

### UI/controller test

- 좌우 pane 구성
- 우측 출력 read-only
- output document에 `JsonSyntaxHighlighter` 연결 여부
- 입력창과 출력창의 `Ctrl + mouse wheel`이 독립적으로 폰트 크기를 조절하는지 확인
- pane별 폰트 크기가 `QSettings`를 통해 재실행 후 복원되는지 확인
- 입력 변경 시 `autoProcessRequested` 발생
- valid 입력 자동 format
- invalid 입력 자동 repair
- save 동작이 실제 파일로 기록되는지 확인

### smoke test

- headless 환경에서 `MainWindow` 생성 가능 여부 확인
- source 실행과 built exe 양쪽에서 smoke-test CLI 성공 여부 확인

## 확장 포인트

- output color theme 커스터마이즈
  - `JsonSyntaxHighlighter`의 색상 매핑만 바꾸면 된다.
- debounce interval 조정
  - 현재는 `MainWindow.auto_process_timer`에서 제어한다.
- 대용량 입력에 대한 background worker 도입
  - 현재는 UI thread에서 처리한다.
- input pane highlighting
  - 현재는 output pane에만 색상을 적용한다.
- tree view
  - 현재는 text output만 제공한다. 별도 JSON tree pane 추가 가능.
- schema validation
  - `JsonFormatterController` 또는 별도 service layer로 확장 가능.
