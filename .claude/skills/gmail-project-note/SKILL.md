---
name: gmail-project-note
description: >
  Gmail 메일을 프로젝트별로 분류하여 업무이력 노트 자동 생성/업데이트.
  "프로젝트 메일 정리", "메일 이력", "업무이력 노트", "gmail project",
  "프로젝트 노트", "거래처 이력", "메일 정리", "이메일 이력",
  "프로젝트 이력", "메일 노트", "project note", "email history" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
user-invocable: true
---

# Gmail Project Note — 프로젝트별 이메일 업무이력 노트

Gmail에서 프로젝트별로 주고받은 이메일을 자동 수집·분류하여 업무이력 노트를 생성합니다.
노트에는 담당자, 연락처, 프로젝트 요약, 현황, 이슈, 날짜별 이력, 행정정보(사업자, 계좌, 계약, 정산)가 포함됩니다.

---

## 사전 확인

```bash
gws auth status 2>&1 | grep -E '"token_valid"|"user"'
```

- `token_valid: true` + `user: ws.choi@project-rent.com` 이면 진행
- 실패 시: "GWS 인증이 필요합니다. `! gws auth login --full`을 실행하고 ws.choi@project-rent.com으로 로그인해주세요." 안내 후 중단

---

## Step 0: 실행 모드 결정

사용자 입력에 따라 3가지 모드 중 하나를 선택한다. 명시하지 않으면 질문한다:

| 모드 | 트리거 예시 | 동작 |
|------|-----------|------|
| **전체 스캔** | "프로젝트 메일 전체 정리", "메일 이력 정리" | 최근 60일 업무 메일 전부 수집 → 프로젝트별 자동 분류 |
| **특정 프로젝트** | "봉은사 메일 정리", "XX 프로젝트 메일" | 해당 프로젝트 키워드로만 검색 |
| **특정 발신자** | "홍길동 주고받은 메일 정리" | 해당 발신자 메일만 수집 |

사용자가 모드를 명시하지 않으면:
```
어떤 방식으로 정리할까요?
1. 전체 스캔 (최근 2개월 업무 메일 전부 분류)
2. 특정 프로젝트 (프로젝트명 또는 키워드 지정)
3. 특정 발신자 (이름 또는 이메일 지정)
```

---

## Step 1: Gmail 메일 수집

### 1-1. 검색 쿼리

**전체 스캔 모드**:
```bash
gws gmail users messages list --params '{"userId":"me","q":"newer_than:60d -category:promotions -category:social -from:noreply -from:no-reply -from:notifications -from:mailer-daemon -from:calendar-notification -label:광고/비업무","maxResults":200}'
```

**특정 프로젝트 모드** (예: "봉은사"):
```bash
gws gmail users messages list --params '{"userId":"me","q":"newer_than:60d (봉은사 OR bongeunsa) -category:promotions -category:social","maxResults":50}'
```

**특정 발신자 모드** (예: "hong@example.com"):
```bash
gws gmail users messages list --params '{"userId":"me","q":"newer_than:60d (from:hong@example.com OR to:hong@example.com)","maxResults":50}'
```

**200건 초과 시 페이지네이션**:
nextPageToken이 있으면 반복 호출:
```bash
gws gmail users messages list --params '{"userId":"me","q":"...","maxResults":200,"pageToken":"NEXT_TOKEN"}'
```

### 1-2. 메일 상세 조회 (metadata)

각 message ID에 대해 metadata 형식으로 조회 (효율성 우선):
```bash
gws gmail users messages get --params '{"userId":"me","id":"MSG_ID","format":"metadata","metadataHeaders":["From","To","Cc","Subject","Date","Reply-To"]}'
```

추출 항목:
- `From`, `To`, `Cc` — 발신자/수신자 정보
- `Subject` — 제목
- `Date` — 날짜
- `snippet` — 본문 미리보기
- `threadId` — 스레드 그룹핑용
- `labelIds` — SENT 여부로 내가 보낸건지 판단

### 1-3. 업무 메일 필터링 (AI 판단)

**포함 (업무 메일)**:
- 거래처, 클라이언트, 동료, 파트너로부터의 메일
- 업무 요청, 질문, 확인, 자료 송부, 미팅 관련
- 매출 리포트, 세금계산서, 계약서 등 비즈니스 문서
- 보험, 법률, 특허, NDA 등 행정 업무
- Slack 결제/알림 등 업무 인프라 관련

**제외 (비업무)**:
- 캘린더 초대/공유 알림
- 서비스 가입 확인 (Vercel, Fly.io 등)
- 순수 뉴스레터, 광고, 소셜 미디어 알림
- Google/Apple 보안 알림
- 자동 발송 모니터링 (단, Brand24 등 업무 직접 관련은 포함)

---

## Step 2: 프로젝트 그룹핑

### 2-1. 1차 그룹핑: threadId 기반

같은 `threadId`를 가진 메일들을 하나의 대화 묶음으로 그룹핑한다.
Gmail 스레드는 동일 주제의 주고받은 메일을 자동으로 묶으므로 가장 신뢰도 높은 단위.

### 2-2. 2차 그룹핑: AI 프로젝트 클러스터링

수집된 스레드들의 (Subject, From, snippet, Date) 목록을 분석하여 프로젝트별로 분류한다.

**분류 기준**:
1. **동일 조직/담당자 + 유사 주제** = 같은 프로젝트
2. **제목에 프로젝트명/브랜드명 포함** = 명시적 분류 (예: "[봉은사]", "[리스테린]")
3. **같은 사업적 맥락** = 같은 프로젝트 (같은 계약, 같은 제안)

**AI 분류 출력 형식**:
```
프로젝트 1: "봉은사 템플스테이 리뉴얼"
  - 스레드: [thread_id_1, thread_id_2]
  - 주요 담당자: 김OO (봉은사)

프로젝트 2: "리스테린 올리브영 팝업"
  - 스레드: [thread_id_3, thread_id_4]
  - 주요 담당자: 정예은 (프로젝트렌트)
```

### 2-3. 3차: 기존 프로젝트 폴더 매칭

```bash
ls /Users/choi_ai/do-better-workspace/10-projects/
```

AI가 분류한 프로젝트명과 기존 폴더명을 매칭:
- **매칭됨**: 해당 폴더에 노트 생성/업데이트
- **매칭 안됨**: 새 폴더 생성 여부를 사용자에게 확인

### 2-4. 제외 조건 적용

1. **최종 메일이 60일 이전**: 해당 프로젝트의 가장 최근 메일 날짜 기준
2. **완결된 프로젝트**: `90-archive/` 폴더에 있는 경우

제외 전 사용자에게 안내:
```
다음 프로젝트는 최근 활동이 없어 제외합니다:
- "OO 프로젝트" (마지막 메일: 2026-01-15, 70일 전)
포함시킬 프로젝트가 있으면 말씀해주세요.
```

---

## Step 3: 사용자 확인

분류 결과를 테이블로 제시하고 확인받는다:

```
### 프로젝트 분류 결과

| # | 프로젝트명 | 스레드 수 | 메일 수 | 최근 활동 | 기존 폴더 |
|---|----------|----------|---------|----------|----------|
| 1 | 봉은사 리뉴얼 | 3 | 8 | 2026-04-20 | 15-bongeunsa/ |
| 2 | 리스테린 팝업 | 2 | 5 | 2026-04-24 | ❌ 없음 |

### 제외됨
- "OO 건" (마지막: 2026-02-10)

이대로 진행할까요? 수정할 사항이 있으면 말씀해주세요.
```

새 폴더 생성이 필요한 경우:
```
"리스테린 팝업"에 대한 프로젝트 폴더가 없습니다.
1. 새 폴더 생성 (17-listerine-popup/)
2. 기존 폴더에 배정
3. 건너뛰기
```

---

## Step 4: 상세 정보 추출

### 4-1. 스레드 전체 조회

프로젝트별로 분류된 스레드를 full 조회한다. 스레드 조회가 개별 메시지보다 효율적:
```bash
gws gmail users threads get --params '{"userId":"me","id":"THREAD_ID"}'
```

### 4-2. AI 정보 추출 항목

각 프로젝트의 전체 메일 내용에서 다음을 추출:

| 추출 항목 | 소스 | 방법 |
|-----------|------|------|
| **프로젝트명** | Subject + 본문 맥락 | AI가 가장 적절한 명칭 결정 |
| **담당자** (이름, 소속) | From/To + 서명란 | 이메일 헤더 + 본문 서명 |
| **이메일** | From 헤더 | 직접 추출 |
| **전화번호** | 본문 서명란 | 패턴: `\d{2,3}-\d{3,4}-\d{4}` |
| **프로젝트 요약** | 전체 맥락 | AI가 메일 흐름에서 3-5문장 요약 |
| **현재 현황** | 최신 메일 기준 | 가장 최근 상태 + 다음 액션 |
| **이슈사항** | 본문 키워드 | "문제", "지연", "확인 필요", "이슈" 등 |
| **날짜별 이력** | Date + 본문 | 시간순 각 메일 핵심 내용 2-3줄 |
| **사업자등록번호** | 본문/첨부 | 패턴: `\d{3}-\d{2}-\d{5}` |
| **은행/계좌** | 본문 | 은행명 + 계좌번호 패턴 |
| **계약일자** | 본문 키워드 | "계약일", "계약 체결", "서명일" 근처 날짜 |
| **정산일정** | 본문 키워드 | "정산", "입금", "지급", "결제" 근처 조건 |
| **계약금액** | 본문 | 금액 패턴 + "계약", "견적" 키워드 |

**행정 정보가 발견되지 않은 항목은 "⚠️ 미확인"으로 표시**한다.

---

## Step 5: 노트 생성/업데이트

### 5-1. 기존 노트 확인

```bash
ls /Users/choi_ai/do-better-workspace/10-projects/{프로젝트폴더}/email-history.md 2>/dev/null
```

### 5-2. 신규 생성 (기존 노트 없는 경우)

파일명: `10-projects/{프로젝트폴더}/email-history.md`

**노트 템플릿**:

```markdown
# {프로젝트명} — 이메일 업무이력

> 자동 생성: {YYYY-MM-DD} | 마지막 업데이트: {YYYY-MM-DD}
> 소스: Gmail (ws.choi@project-rent.com)

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | {프로젝트명} |
| **상태** | {진행중/대기/완료} |
| **시작일** | {최초 메일 날짜} |
| **최근 활동** | {최신 메일 날짜} |

---

## 담당자 & 연락처

| 이름 | 소속 | 이메일 | 전화번호 | 역할 |
|------|------|--------|----------|------|
| {이름} | {소속} | {이메일} | {전화번호} | {역할} |

---

## 프로젝트 요약

{AI가 메일 흐름에서 파악한 프로젝트 전체 요약. 3-5문장.}

---

## 현재 현황

{가장 최근 메일 기준 현재 상태. 다음 액션이 필요한 사항.}

---

## 이슈사항

- {이슈 1}
- {이슈 2}

---

## 행정 정보

| 항목 | 내용 |
|------|------|
| **사업자등록번호** | {있으면 기재 / ⚠️ 미확인} |
| **은행/계좌** | {있으면 기재 / ⚠️ 미확인} |
| **계약일자** | {있으면 기재 / ⚠️ 미확인} |
| **정산일정** | {있으면 기재 / ⚠️ 미확인} |
| **계약금액** | {있으면 기재 / ⚠️ 미확인} |

---

## 날짜별 이력

### {YYYY-MM-DD} — {메일 제목 요약}
- **발신**: {발신자 이름 (소속)}
- **내용**: {핵심 내용 2-3줄 요약}
- **액션**: {요청사항 또는 결정사항}

### {YYYY-MM-DD} — {메일 제목 요약}
- **발신**: {발신자 이름 (소속)}
- **내용**: {핵심 내용 2-3줄 요약}
- **액션**: {요청사항 또는 결정사항}

(오래된 순 → 최신 순으로 정렬)

---

## 미회신/대기 항목

- [ ] {회신이 필요한 메일 또는 대기 중인 액션}

---

*이 노트는 `/gmail-project-note` 스킬로 자동 생성되었습니다.*
*마지막 스캔: {YYYY-MM-DD HH:MM}*
```

### 5-3. 증분 업데이트 (기존 노트 있는 경우)

기존 노트를 Read로 읽고 "마지막 스캔" 날짜를 확인한 후:

1. **"날짜별 이력"** — 마지막 스캔 이후 새 메일만 하단에 append
2. **"현재 현황"** — 최신 상태로 덮어쓰기
3. **"이슈사항"** — 기존 유지 + 새 이슈 추가
4. **"담당자 & 연락처"** — 새 담당자 발견 시 행 추가
5. **"행정 정보"** — "⚠️ 미확인" 항목에 새로 발견된 정보 채우기
6. **"미회신/대기 항목"** — 갱신 (해결된 건 체크, 새 건 추가)
7. **"마지막 업데이트" 및 "마지막 스캔" 타임스탬프** 갱신

Edit 도구를 사용하여 섹션별로 정밀 업데이트한다.

---

## Step 6: Notion 동기화

마크다운 노트 생성 후 Notion에도 페이지를 생성/업데이트한다.

### 6-1. Notion 토큰 확인

```bash
echo $NOTION_TOKEN | head -c 10
```

토큰이 없으면: "Notion 동기화를 건너뜁니다. 필요시 `export NOTION_TOKEN=...` 설정 후 다시 실행해주세요." 안내

### 6-2. 프로젝트별 Notion 페이지 생성

notion-handler 스킬의 `scripts/notion_api.py`를 활용한다:

```bash
# 기존 페이지 검색
python3 ~/.claude/skills/notion-handler/scripts/notion_api.py search \
  --query "{프로젝트명}" --type page

# 페이지가 없으면 새로 생성
python3 ~/.claude/skills/notion-handler/scripts/notion_api.py create-page \
  --parent "{PARENT_PAGE_ID}" \
  --title "{프로젝트명} — 이메일 업무이력"

# 블록 추가 (노트 내용을 Notion 블록으로 변환)
python3 ~/.claude/skills/notion-handler/scripts/notion_api.py append-blocks \
  --id "{PAGE_ID}" \
  --blocks '[
    {"type": "heading_2", "text": "프로젝트 개요"},
    {"type": "paragraph", "text": "프로젝트명: {프로젝트명} | 상태: 진행중"},
    {"type": "divider"},
    {"type": "heading_2", "text": "담당자 & 연락처"},
    {"type": "paragraph", "text": "{이름} ({소속}) — {이메일} / {전화번호}"},
    {"type": "divider"},
    {"type": "heading_2", "text": "프로젝트 요약"},
    {"type": "paragraph", "text": "{요약 내용}"},
    {"type": "divider"},
    {"type": "heading_2", "text": "현재 현황"},
    {"type": "paragraph", "text": "{현황}"},
    {"type": "divider"},
    {"type": "heading_2", "text": "행정 정보"},
    {"type": "paragraph", "text": "사업자: {번호} | 계좌: {계좌} | 계약일: {날짜} | 정산: {일정}"},
    {"type": "divider"},
    {"type": "heading_2", "text": "날짜별 이력"},
    {"type": "heading_3", "text": "{YYYY-MM-DD} — {제목}"},
    {"type": "paragraph", "text": "{이력 내용}"}
  ]'
```

### 6-3. 기존 Notion 페이지 업데이트

기존 페이지가 있으면 clear-page 후 전체 내용을 재작성한다:
```bash
python3 ~/.claude/skills/notion-handler/scripts/notion_api.py clear-page --id "{PAGE_ID}"
python3 ~/.claude/skills/notion-handler/scripts/notion_api.py append-blocks --id "{PAGE_ID}" --blocks '[...]'
```

---

## Step 7: 결과 보고

최종 결과를 테이블로 출력한다:

```
## 프로젝트 이메일 이력 정리 완료

### 생성/업데이트된 노트
| # | 프로젝트 | 메일 수 | 스레드 수 | 상태 | 파일 | Notion |
|---|---------|---------|----------|------|------|--------|
| 1 | 봉은사 리뉴얼 | 8 | 3 | 신규 생성 | 15-bongeunsa/email-history.md | ✅ |
| 2 | 리스테린 팝업 | 5 | 2 | 신규 생성 | 17-listerine-popup/email-history.md | ✅ |

### 제외된 프로젝트
- "OO 건" — 마지막 메일 2026-02-10 (75일 전)

### 미분류 메일 (N통)
| 발신자 | 제목 | 날짜 |
|--------|------|------|
| ... | ... | ... |

미분류 메일을 특정 프로젝트에 배정하시겠어요?
```

---

## 에러 핸들링

| 상황 | 처리 |
|------|------|
| GWS 인증 만료 | "GWS 인증이 필요합니다" 안내 후 중단 |
| API 쿼터 초과 | 부분 결과 저장 후 "나머지는 다시 실행해주세요" 안내 |
| 메일 0건 | "해당 조건에 맞는 메일이 없습니다" 안내 |
| Notion 토큰 없음 | 마크다운 노트만 생성, Notion 건너뜀 안내 |
| 기존 노트 파싱 실패 | 백업 생성 후 새로 작성 제안 |

---

## 참고

- GWS CLI 인증: `gws auth login --full` (ws.choi@project-rent.com)
- projectrent43@gmail.com → ws.choi@project-rent.com 자동 전달 설정됨 (별도 검색 불필요)
- Notion API: `~/.claude/skills/notion-handler/scripts/notion_api.py`
- 노트 저장 위치: `/Users/choi_ai/do-better-workspace/10-projects/{프로젝트폴더}/email-history.md`
