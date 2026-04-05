# Test Data Guide

이 폴더의 raw 예시 파일은 앱에서 바로 `Open File` / drag & drop / 복사-붙여넣기 테스트를 할 수 있도록 순수 입력 데이터만 담고 있습니다.  
그래서 설명 주석은 raw 파일 안이 아니라 이 문서에 정리했습니다.

## 01-valid-unformatted-a4.json

<!-- 테스트 용도: strict format, syntax highlighting, tree view, search, save, copy output -->

- 용도: 줄바꿈과 들여쓰기가 없는 큰 valid JSON을 붙여넣었을 때 자동 pretty format 되는지 확인
- 기대 결과:
  - `Valid JSON`
  - `Change Summary` / `Warnings` / `Risk` 비어 있음
  - `Tree View`에서 탐색 가능

## 02-invalid-syntax-a4.txt

<!-- 테스트 용도: 대형 malformed JSON repair, summary/warning/risk, safe mode 기본 동작 -->

- 용도: A4 1페이지 분량의 문법 오류 JSON 계열 텍스트를 repair 하는지 확인
- 포함 오류:
  - single quotes
  - unquoted keys
  - trailing commas
  - smart quotes
- 기대 결과:
  - `Repaired JSON`
  - `Change Summary`와 `Warnings` 표시
  - `Risk`는 `Low` 또는 `Medium`

## 03-unrecoverable-error-highlight.txt

<!-- 테스트 용도: format 실패 + repair 실패, 입력창 error highlight -->

- 용도: format과 repair가 모두 실패하는 입력에서 입력창 error highlight가 유지되는지 확인
- 기대 결과:
  - `Unable to process input`
  - 입력창 첫 줄 highlight
  - output 비어 있음

## 04-concatenated-documents.txt

<!-- 테스트 용도: 여러 top-level JSON document를 배열로 결합 -->

- 용도: 여러 JSON object가 이어붙은 입력을 배열로 결합하는지 확인
- 기대 결과:
  - `Repaired JSON`
  - `Change Summary`에 document merge 관련 항목 표시
  - `Risk`는 보통 `Medium`

## 05-event-stream.txt

<!-- 테스트 용도: SSE data stream, [DONE] sentinel skip -->

- 용도: `data:` event stream 입력을 payload 배열로 복구하는지 확인
- 기대 결과:
  - `Repaired JSON`
  - `Change Summary`에 payload extraction 표시
  - `[DONE]` sentinel skip 관련 summary 표시

## 06-json-lines.jsonl

<!-- 테스트 용도: JSON Lines file open / drag-drop / repair -->

- 용도: `.jsonl` 파일을 직접 열었을 때 여러 line JSON이 배열로 복구되는지 확인
- 기대 결과:
  - `Repaired JSON`
  - `Tree View`에서 각 line이 배열 원소로 보임

## 07-markdown-fenced-json.txt

<!-- 테스트 용도: markdown code fence stripping -->

- 용도: fenced JSON 입력에서 wrapper code fence를 제거하고 JSON 본문만 처리하는지 확인
- 기대 결과:
  - `Repaired JSON`
  - `Change Summary`에 markdown code fence 제거 표시

## 08-aggressive-html-string.txt

<!-- 테스트 용도: 긴 HTML string 안의 깨진 quote 복구, aggressive mode / high risk -->

- 용도: HTML string 내부의 잘못된 quote 때문에 key/value가 잘리는 케이스를 테스트
- 권장 모드: `Aggressive`
- 기대 결과:
  - `Repaired JSON`
  - `Change Summary`에 suspicious quote escape 표시
  - `Warnings` 표시
  - `Risk`는 `High`

## 09-tree-view-search.json

<!-- 테스트 용도: tree view, search, selected path, copy path -->

- 용도: 중첩 구조가 많은 valid JSON으로 tree view와 검색 기능을 테스트
- 추천 검색어:
  - `battery`
  - `ticket`
  - `warehouse`
  - `$.regions[1].sites[0].devices[1]`
- 기대 결과:
  - `Valid JSON`
  - `Tree View`에서 path 탐색과 `Copy Path` 확인 가능
