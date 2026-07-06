# 26 카드뉴스 — 프로그레스

> SNS 카드뉴스 자동화: GPT 대화 → 구글드라이브 → Claude(기획·문체·헤드카피) → Canva Autofill 카드뉴스 초안.
> 기존 `/card-news`(수동 HTML+Buffer)와 역할 분리. 본 파이프라인은 GPT수집→Canva 자동.

---

## 2026-06-21 — 설계 확정 + 스캐폴딩 완료

### 결정 사항
- **수집**: ChatGPT 커스텀GPT의 Action 웹훅 → Apps Script Web App → 구글드라이브 `SNS_Automation/input` 적재 → 시스템이 Drive에서 불러옴
- **제작**: Canva **Enterprise** Autofill API — 지정 브랜드 템플릿(데이터 필드)에 정리된 콘텐츠 자동 채우기
- **구현**: `/sns-cardnews` 스킬 오케스트레이션(model: opus). 문체는 `.claude/skills/문체/references/style-dna.md`를 스킬이 직접 읽어 적용(문체 스킬은 프로그래밍 호출 불가라 우회)
- **MVP 범위**: 카드뉴스 **초안(Canva edit_url)까지**. 발행(Buffer/예약)은 후속

### 검증된 제약(설계 전제)
1. ChatGPT 앱/프로젝트 대화는 API 자동수집 불가 → GPT가 구조화 JSON 출력 + Action 중계로 우회
2. Canva Autofill API = 개발자·사용자 모두 **Enterprise 소속 + MFA** 필요. 스코프 `brandtemplate:content:read`, `design:content:write`. 요청 `type:"create_from_brand_template"`, 응답 `result.design.urls.edit_url`(30일 유효)
3. 문체 스킬은 다른 스킬/스크립트에서 호출 불가 → Claude가 직접 적용

### 산출물(작성·검증 완료, 실연동 미완)
- `00-system/02-scripts/canva_autofill.py` — stdlib only(urllib). CLI: `auth`(OAuth PKCE→refresh_token .env 저장) / `dataset`(필드 키 조회) / `autofill`(생성→폴링→edit_url)
- `00-system/02-scripts/sns-webhook.gs` — Apps Script `doPost(e)`: 공유시크릿 검증 → Drive `input` 폴더에 `YYYYMMDD-HHMMSS-{slug}.json` 생성. `doGet` 헬스체크
- `.claude/skills/sns-cardnews/SKILL.md` — 6단계: ①Ingest(gws `drive files list/download`) ②Validate(3카드×3포인트+숫자3중검증) ③문체·헤드카피 고도화⭐ ④Canva 매핑 ⑤Autofill ⑥Sheet 기록·output 저장·input→processed
- `10-projects/26-card-news/gpt-instructions.md`, `gpt-action-openapi.yml`(OpenAPI 3.1), `sample-source.json`, `sns-automation-setup.md`(준비물 체크리스트+검증순서)
- `.env.template` — `CANVA_CLIENT_ID/SECRET/REFRESH_TOKEN`, `CANVA_BRAND_TEMPLATE_ID`, `SNS_DRIVE_INPUT/OUTPUT_FOLDER_ID`, `SNS_SHEET_ID`, `SNS_WEBHOOK_SECRET` 추가

### 액션 아이템 (사용자 직접)
- [ ] **[블로커] Canva 개발자 통합 생성 → Client ID/Secret** — Claude가 헤드리스로 직접 시도했으나 **Canva 봇 차단(Cloudflare)으로 포털 진입 불가**. 자격증명 발급은 사람이 직접. 값 확보 시 `.env` 기록→`auth`→`dataset`까지 Claude가 자동 이어감
- [ ] Canva 브랜드 템플릿 제작 + 데이터 필드 지정(`card1_title`…) → `CANVA_BRAND_TEMPLATE_ID`
- [ ] Drive 폴더 2개(`input`/`output`) → 폴더 ID
- [ ] Google Sheet(탭 `카드뉴스`) → `SNS_SHEET_ID`
- [ ] `SNS_WEBHOOK_SECRET` 정하기
- [ ] Apps Script 웹앱 배포 → URL을 GPT Action `servers.url`에 입력
- [ ] 커스텀GPT 생성(지침+Action 등록)

### 검증 순서(위험도 높은 순)
① Canva 단건(`auth`→`dataset`→`autofill`) → ② 웹훅(curl) → ③ 커스텀GPT → ④ 전체 `/sns-cardnews`

### 후속(2차)
- 이미지 필드(Canva Asset 업로드), Buffer Draft 자동 발행, 예약 업로드
- 크레딧 표기 항상 **by Project Rent**

> 메모리: `project_sns_cardnews_automation` · 플랜: `~/.claude/plans/sns-sunny-dahl.md`
