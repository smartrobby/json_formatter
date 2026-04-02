# Invalid JSON Example

아래 예제는 문법 오류가 있는 JSON이다. `Raw JSON Input`에 붙여넣으면 자동 repair와 output pane 색상 적용을 확인할 수 있다.

- 포함된 오류:
  - single quotes 사용
  - 일부 key에 quotes 누락
  - trailing comma 포함

```json
{'user':{'id':101,name:'Alice','roles':['admin','editor',],'active':true,'profile':{'email':'alice@example.com','timezone':'Asia/Seoul',},},'meta':{'requestId':'req-001','version':1,}}
```
