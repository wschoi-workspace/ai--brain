# SNS 카드뉴스 자동화 — 셋업 가이드

GPT 프로젝트 대화 → 구글드라이브 → (Claude) 콘텐츠 기획·문체·헤드카피 → Canva 카드뉴스 초안.
이 문서는 **사용자가 직접 채워야 하는 준비물**과 **단계별 검증** 순서를 정리한다.

> 구현 플랜 원본: `~/.claude/plans/sns-sunny-dahl.md`
> 코드 위치: `00-system/02-scripts/canva_autofill.py`, `00-system/02-scripts/sns-webhook.gs`,
> `.claude/skills/sns-cardnews/SKILL.md`, `10-projects/26-card-news/gpt-*`

---

## 0. 준비물 체크리스트 (사용자 작업)

| # | 항목 | 어디서 | .env 키 |
|---|------|--------|---------|
| 1 | Canva Enterprise + Developer 앱(Client ID/Secret) | canva.com/developers | `CANVA_CLIENT_ID`, `CANVA_CLIENT_SECRET` |
| 2 | Canva 앱 Redirect URL 등록: `http://127.0.0.1:8910/callback` | Developer Portal | — |
| 3 | 카드뉴스 **브랜드 템플릿** 제작 + 데이터 필드 지정 → 템플릿 ID | Canva | `CANVA_BRAND_TEMPLATE_ID` |
| 4 | Drive 폴더 2개 생성: `SNS_Automation/input`, `/output` → 각 ID | Google Drive | `SNS_DRIVE_INPUT_FOLDER_ID`, `SNS_DRIVE_OUTPUT_FOLDER_ID` |
| 5 | 결과 기록 Google Sheet 생성(탭 이름 `카드뉴스`) → ID | Google Sheets | `SNS_SHEET_ID` |
| 6 | 공유시크릿 문자열 정하기(길고 랜덤) | 임의 | `SNS_WEBHOOK_SECRET` |
| 7 | Apps Script 웹앱 배포 → 배포 URL | script.google.com | (URL은 GPT Action에) |
| 8 | ChatGPT 커스텀GPT 생성 + 지침/Action 등록 | chat.openai.com | — |

`.env`는 `.env.template`의 "SNS 카드뉴스 자동화" 블록을 복사해 채운다.

---

## 1. Canva 브랜드 템플릿 — 데이터 필드 네이밍 규약

1080×1080 카드 3~4장짜리 브랜드 템플릿을 만들고, 각 텍스트 요소에 **데이터 필드(named)** 를 지정한다.
필드 키는 아래처럼 콘텐츠 구조와 1:1 대응시키는 걸 권장(실제 키는 자유, 단 일관되게):

```
topic
card1_title   card1_main   card1_point1   card1_point2   card1_point3
card2_title   card2_main   card2_point1   card2_point2   card2_point3
card3_title   card3_main   card3_point1   card3_point2   card3_point3
caption
```

템플릿을 만든 뒤 실제 필드 키를 확인:
```bash
python3 00-system/02-scripts/canva_autofill.py dataset
```
→ 출력된 필드 키에 맞춰 스킬 4단계의 매핑을 조정한다. (텍스트 필드만 MVP 대상)

---

## 2. 단계별 검증 (위험도 높은 순)

### ① Canva 단건 — 가장 먼저
```bash
# 최초 1회 인가 (브라우저 열림 → refresh_token이 .env에 저장됨)
python3 00-system/02-scripts/canva_autofill.py auth

# 필드 키 확인
python3 00-system/02-scripts/canva_autofill.py dataset

# 단건 생성 테스트 (아래 sample-canva-payload.json은 dataset 필드에 맞춰 직접 작성)
python3 00-system/02-scripts/canva_autofill.py autofill \
  --data /tmp/sample-canva-payload.json --title "테스트 카드뉴스"
# → edit_url 출력. 브라우저로 열어 카드가 채워졌는지 확인.
```

### ② 웹훅 → Drive
```bash
curl -X POST "<Apps Script 배포 URL>" \
  -H "Content-Type: application/json" \
  --data-binary @10-projects/26-card-news/sample-source.json \
  --data-urlencode  # (secret은 sample에 없으므로 아래처럼 넣어 테스트)
```
실제 테스트는 sample-source.json에 `"secret":"<SNS_WEBHOOK_SECRET>"` 한 줄을 추가해 POST.
→ Drive `SNS_Automation/input`에 `YYYYMMDD-HHMMSS-*.json` 생성 확인.

### ③ 커스텀GPT
`gpt-instructions.md` 지침 + `gpt-action-openapi.yml`(servers.url을 배포 URL로 교체) 등록 →
GPT와 대화 후 "저장해줘" → Drive에 파일 생성 확인.

### ④ 전체 (Claude 스킬)
```
/sns-cardnews
```
→ Drive 최신 소스 불러오기 → 구조 검증 → (Claude) 문체·헤드카피 고도화 Before/After →
Canva edit_url → Sheet 기록 → 정리본(output) 저장까지 일괄 확인.
로컬 테스트는 `sample-source.json`을 input 폴더에 올리거나, 스킬에 경로를 직접 지정.

---

## 3. 범위·후속
- **MVP = 카드뉴스 초안(Canva edit_url)까지.** 발행(Buffer/예약)은 후속 — `/card-news`(Buffer) 연계.
- 후속 확장: 이미지 필드(Canva Asset 업로드), Buffer Draft 자동 업로드, 예약 발행.
- 크레딧 표기는 항상 **by Project Rent**.
