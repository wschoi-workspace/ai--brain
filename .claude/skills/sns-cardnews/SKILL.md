---
name: sns-cardnews
description: >
  GPT 대화 → SNS 카드뉴스 자동화 오케스트레이터. ChatGPT 커스텀GPT가 구글드라이브에 적재한
  카드뉴스 소스(JSON)를 불러와, 콘텐츠 기획 → 최원석 문체 적용 → 헤드카피 고도화로 다듬은 뒤,
  Canva Enterprise Autofill API로 지정 브랜드 템플릿에 자동 채워 카드뉴스 초안(Canva 디자인)을
  만들고, Google Sheet에 기록한다. "카드뉴스 자동화", "sns 자동화", "GPT 대화 카드뉴스",
  "카드뉴스 소스 처리", "캔바 카드뉴스" 등을 언급하면 실행.
  ⚠️ 기존 /card-news(수동 HTML 제작·Buffer)와 역할이 다르다 — 이 스킬은 GPT수집→Canva 자동 파이프라인.
user-invocable: true
model: opus
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
---

# /sns-cardnews — GPT 대화 → Canva 카드뉴스 초안 자동화

> 본질은 카드뉴스 "제작"이 아니라 **대표의 생각을 SNS 콘텐츠로 번역**하는 것.
> 데이터 배관(Drive·Canva·Sheet)은 스크립트가, **관점·문체·헤드카피 판단은 내가 직접** 한다.

## 사전 조건 (없으면 사용자에게 안내)
- `.env`: `CANVA_CLIENT_ID/SECRET/REFRESH_TOKEN`, `CANVA_BRAND_TEMPLATE_ID`, `SNS_DRIVE_INPUT_FOLDER_ID`, `SNS_DRIVE_OUTPUT_FOLDER_ID`, `SNS_SHEET_ID`
- Canva 브랜드 템플릿이 만들어져 있고 데이터 필드가 지정돼 있을 것 (필드 키는 1단계에서 `dataset`으로 확인)
- 헬퍼: `00-system/02-scripts/canva_autofill.py` (최초 1회 `python3 ... auth` 완료)

---

## 워크플로우 (6단계)

### 1단계 · Ingest — Drive에서 최신 소스 불러오기
- 입력 폴더의 최신 JSON을 찾아 다운로드. gws CLI(raw `files` 리소스) 사용:
  ```bash
  # 최신 파일 조회 (input 폴더 + JSON + 미처리)
  gws drive files list --params '{
    "q": "'"'"'<INPUT_FOLDER_ID>'"'"' in parents and mimeType=\"application/json\" and trashed=false",
    "orderBy": "modifiedTime desc",
    "pageSize": 5,
    "fields": "files(id,name,modifiedTime)"
  }'
  # 내용 다운로드 (alt=media)
  gws drive files download --params '{"fileId":"<fileId>"}' -o /tmp/sns-source.json
  ```
  (q 문자열의 따옴표 이스케이프가 번거로우면, 위 JSON을 파일로 써서 `--params @/tmp/q.json` 형태로 넘겨도 됨.)
- 사용자가 특정 파일/주제를 지정하면 그걸 우선. 인자로 로컬 JSON 경로를 줄 수도 있음(테스트용).
- 파싱 후 `topic`을 사용자에게 보여주고 "이 소스로 진행" 확인.

### 2단계 · Validate — 구조 검증
- 체크: `card_news` 3개? 각 `points` 3개? `main_message`/`caption_draft`/`hashtags` 존재?
- 누락 시: 가능한 건 소스 맥락으로 보완하고, 판단이 필요한 결손은 사용자에게 묻는다.
- 통계·연구·고유명사가 있으면 **CLAUDE.md 숫자 3중 검증**(추출→웹대조→재대조)을 여기서 수행. 불확실하면 자리표시자로 두고 확인 요청.

### 3단계 · 고도화 — 콘텐츠 기획 + 문체 + 헤드카피 ⭐ (핵심)
> 이 단계가 이 스킬의 존재 이유. 절대 기계적으로 넘기지 말 것.
- **반드시 먼저 읽는다**:
  - `.claude/skills/문체/references/style-dna.md` (10규칙)
  - `.claude/skills/문체/references/format-guide.md` (SNS 포맷: 200~500자, 단문 리듬→비유 1개→수사질문 1회→단언 마무리)
- **기획**: 3카드의 논리 흐름(문제→전개→전환)이 살아있는지 점검하고, 약한 카드는 관점을 더 날카롭게 재구성.
- **문체 적용 (De-AI → R-Voice)**: 각 카드의 `main_message`, 포인트 설명, `caption_draft`를 최원석 문체로 리라이팅. `source_quotes`(대표 실제 발화)를 재료로 살린다.
- **헤드카피 고도화**: 각 카드 `title`을 스크롤을 멈추게 하는 헤드카피로. "A가 아니라 B" 대조·재정의, 단정조. 축약·유치·과장 금지.
- **자가검증 출력**: 문체 스킬의 R-Voice 체크리스트(De-AI/리듬/대조/수사질문/과용)를 카드별로 첨부.
- 결과를 정리본으로 구성(아래 산출 구조). 사용자에게 Before/After를 보여주고 확인받은 뒤 다음 단계.

### 4단계 · Canva 매핑 — 데이터 필드에 맞추기
- 템플릿 필드 키 확인:
  ```bash
  python3 00-system/02-scripts/canva_autofill.py dataset
  ```
- 정리된 콘텐츠를 필드 키에 1:1 매핑한 **평면 JSON**을 만든다. 네이밍 규약(예):
  `card1_title, card1_main, card1_point1_title, card1_point1_desc, … card3_point3_desc`
- `/tmp/sns-canva-payload.json`로 저장. (필드 키는 실제 dataset 출력에 맞춰 조정)

### 5단계 · Autofill — Canva 디자인 생성
```bash
python3 00-system/02-scripts/canva_autofill.py autofill \
  --data /tmp/sns-canva-payload.json \
  --title "<topic> 카드뉴스 초안"
```
- 출력 JSON에서 `edit_url`(편집), `view_url`(보기), `thumbnail` 획득.
- edit_url은 30일 유효 — 사용자가 Canva에서 바로 다듬을 수 있음.

### 6단계 · 기록·정리
- **Google Sheet 기록** (gws CLI append, daily-report-bot 패턴):
  ```bash
  gws sheets spreadsheets values append \
    --params '{"spreadsheetId":"'"$SNS_SHEET_ID"'","range":"카드뉴스!A1","valueInputOption":"RAW","insertDataOption":"INSERT_ROWS"}' \
    --json '{"values":[[ID, 생성일, 주제, 카드1제목, 카드2제목, 카드3제목, "Draft", edit_url, 캡션, 해시태그]]}'
  ```
- **정리본 저장**: 최종 콘텐츠를 `10-projects/26-card-news/output/<slug>-content.md` 와 `.json`으로 저장. 가능하면 `gws drive +upload`로 `SNS_DRIVE_OUTPUT_FOLDER_ID`에도 올림.
- **input 파일 이동**: 처리한 소스를 `processed/`로 이동(중복 처리 방지). gws CLI move 또는 메타 표시.
- 마무리 보고: 주제 / Canva edit_url / 시트 기록 / 정리본 경로를 한 번에 제시.

---

## 산출 정리본 구조 (output .md)
```
# <topic> — 카드뉴스 초안

핵심 메시지: <core_message>
타깃: <target_audience> · 톤: <tone>

## 카드 1 — <헤드카피>
- 핵심: <main_message (문체 적용)>
- 포인트1 / 2 / 3 + 설명
🔎 R-Voice 자가검증: …

## 카드 2 …
## 카드 3 …

## SNS 본문 (캡션)
<caption (문체 적용)>

## 해시태그
<hashtags>

---
Canva 초안: <edit_url>
상태: Draft
by Project Rent
```

## 폴백 (Canva 장애·미설정 시)
- Canva 단계가 막히면 정리본(.md/.json)까지는 완성하고, 기존 `10-projects/26-card-news/topic1-design-end.html` 템플릿 + `/playwright`로 HTML 렌더 폴백을 제안.

## 주의
- 발행(Buffer/예약)은 이 스킬 범위 밖(초안까지). 발행은 별도 단계에서 `/card-news`(Buffer) 연계.
- 크레딧 표기는 항상 **by Project Rent**.
