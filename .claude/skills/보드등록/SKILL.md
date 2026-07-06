---
name: 보드등록
description: 회의록·회의본문·메일·지시 4유형 → PR 보드 카드 자동 등록. 입력을 분석해 /api/email-ingest로 본인 보드에 등록. "보드등록", "보드 등록", "카드 등록", "PR보드 등록", "보드에 올려", "카드로 만들어" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Bash
---

# /보드등록 — PR 보드 카드 자동 등록

4가지 입력 유형을 받아 분석 → `/api/email-ingest` 호출. 결과는 본인 보드의 📥 신규 카드로 등록된다.

> ⚠️ **본 스킬은 PR 보드 한정** (`https://pr-board-phi.vercel.app`). 다른 보드는 대상 아님.
> 전용 계정: **ws.choi@project-rent.com** (최원석)
>
> 🔧 **매칭 미구성**: 기존 프로젝트 매칭(§3)은 Supabase URL/ANON KEY + 본인 user_id가 있어야 동작한다.
> 현재 미보유라 **매칭을 생략하고 항상 신규 카드로 ingest**한다. 키 확보 시 §3을 복원한다.

---

## 0. 처리 가능한 4가지 입력 유형

| # | 유형 | 키워드 | source | 이모지 | 일반 예시 |
|---|---|---|---|---|---|
| 1 | **회의록** (정리본) | `회의록` | `meeting` | 📝 | `/회의록정리` 후 .md/.html 산출물 |
| 2 | **회의 본문** (원본) | `회의` | `meeting` | 🗓 | 회의 메모·전사·녹취 텍스트 |
| 3 | **메일** | `메일` | `mail` | 📧 | 메일 1건 (제목·발신자·본문) |
| 4 | **지시** | `지시` (또는 디폴트) | `directive` | 📌 | CEO/고객 지시·일반 텍스트 |

---

## 1. 입력 파싱

### 1-1. `$ARGUMENTS` 첫 토큰 검사
- `회의록` → 유형 1 (정리된 회의록 .md/.html)
- `회의` → 유형 2 (회의 원본 본문)
- `메일` → 유형 3
- `지시` 또는 미지정 → 유형 4 (디폴트)

### 1-2. 본문 패턴 자동 감지 (첫 토큰이 모호할 때)
- 본문이 `# 📝` 또는 `## 📋 회의 메타데이터` 포함 → **유형 1 (회의록 정리본)**
- 본문 첫 줄에 `제목:` `발신자:` `From:` 포함 → **유형 3 (메일)**
- 회의 일시·참석자 패턴 보이면 → **유형 2 (회의 본문)**
- 그 외 → **유형 4 (지시)**

### 1-3. 입력이 비어있을 때
```
어떤 내용을 카드로 등록할까요? 형식:

/보드등록 [회의록|회의|메일|지시] <본문 또는 파일 경로>

예시:
  /보드등록 회의록 ~/Library/CloudStorage/Dropbox/13-업무자동화/회의정리/정리본/2026-06-09_CJ온스타일.md
  /보드등록 메일
    제목: ...
    발신자: ...
    본문: ...
  /보드등록 지시
    최원석 대표가 ...

또는 본문만 붙여넣으면 '지시' 로 처리됩니다.
```

### 1-4. 파일 경로가 입력된 경우 (회의록 정리본 주로)
- 절대경로 → 파일 직접 읽기
- 파일명만 → `~/Library/CloudStorage/Dropbox/13-업무자동화/회의정리/정리본/` 에서 찾기
- 회의록 정리본 디폴트 폴더: 위와 동일

---

## 2. 유형별 분석 (요약 + 액션 추출)

### 공통 출력 필드
1. **subject** (50자 이내, 한 줄)
2. **from** (발신자·지시자·회의명)
3. **summary** (3~5문장, 인사말·서명·푸터 제외, 마감일·금액·일정 포함)
4. **actions** (0~5개, 본인이 직접 해야 할 일만)
5. **score** (1~10, 시급도)
6. **source** (`meeting` / `mail` / `directive`)

### 유형별 처리 차이

**유형 1: 회의록 (정리본)** — 9섹션 구조에서 추출
- subject = 회의명 (메타데이터 또는 `# 📝 {회의명}`에서)
- from = 회의 주제 / 주최자
- summary = `📌 회의 핵심 요약` 섹션 내용
- actions = 다음 섹션들의 항목을 텍스트로 변환·합집합:
  - `🎯 To do list` 각 행 → `"[담당:{owner}/기한:{due}] {액션}"`
  - `❓ 의사결정 필요사항` → `"[결정필요/{데드라인}] {사안}"`
  - `⚠️ 이슈 / 리스크` **🔴 위험**만 → `"[리스크] {이슈}"`
  - `🔜 이후 대응` → `"[후속/{시점}] {항목}"`
- score = 9
- 최대 5개 초과 시 우선순위 (🔴 리스크 > 결정필요 > To do > 후속)

**유형 2: 회의 본문 (원본)**
- subject = 회의 주제 한 줄 (추출)
- from = 회의명 또는 주최자
- summary = 본문 핵심 요약
- actions = 본문에서 "확인 필요" "회신 필요" "결정해야" 같은 패턴 추출
- score = 8

**유형 3: 메일**
- subject = 메일 제목 (그대로 또는 50자 압축)
- from = 발신자 이름·이메일
- summary = 본문 핵심
- actions = 본인 액션 ("견적서 회신", "5/28 미팅 확정")
- score = 본문 시급도 자동 판정 (마감 임박·금액 큼·CEO 발신 등)

**유형 4: 지시**
- subject = 핵심 안건 한 줄
- from = 지시자 (CEO 최원석·고객·본인 등)
- summary = 지시 내용 요약
- actions = 본인이 해야 할 일
- score = 10 (디폴트)

---

## 3. 매칭 시도 — 🔧 현재 비활성화 (키 확보 시 복원)

> **현재 정책**: Supabase 키·user_id 미보유 → 매칭 건너뛰고 §4 신규 ingest로 직행.
> 사용자에게 한 줄만 안내한 뒤 등록 진행:
> ```
> ℹ️ 매칭 미구성 상태 — 신규 카드(📥 내 보드)로 등록합니다.
> ```

<details>
<summary>키 확보 후 복원할 매칭 로직 (보존)</summary>

### 3-1. PR 보드 사용자 프로젝트 조회
`~/.claude/.pr_board_config.json` 또는 pr-board `.env.local`의
`NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` 읽고:

```
GET {SB_URL}/rest/v1/projects?select=id,name,description,visibility,owner_user_id&owner_user_id=eq.{내user_id}&order=updated_at.desc
```

→ 본인이 owner인 프로젝트 전부 (public·private 다).

### 3-2. 본문 키워드 매칭
subject·summary·본문에서 핵심 키워드 추출 후 프로젝트명·description과 단어 단위 비교:
- 회사명 정확 매칭 (예: "CJ온스타일", "노트러블랩", "KBO")
- 사업·프로젝트 키워드 (팝업·팩트시트·시즌3 등)
- 발신자 도메인 매칭

매칭 점수 높은 1~3개 후보 추출.

### 3-3. 사용자에게 후보 제시
```
🔎 매칭 후보:
  1) [기존 카드 추가] {프로젝트명1} — 매칭 근거: {1줄}
  2) [기존 카드 추가] {프로젝트명2} — 매칭 근거: {1줄}
  3) [신규 카드] 매칭 없음 → 새 프로젝트로 만들기

어디에 등록할까요? (1·2·3 중 하나)
```

후보 없으면 바로 "신규로 등록할까요?" 한 줄만.

### 3-4. 사용자 응답
- "1"/"2" → `targetProjectId` 지정해서 ingest 호출
- "3"/"신규" → `targetProjectId` 없이 ingest (새 프로젝트)
- "취소" → 종료
</details>

---

## 4. PR 보드 ingest 호출

POST `/api/email-ingest` payload:
```json
{
  "to": "ws.choi@project-rent.com",
  "messageId": "manual-{타임스탬프}-{랜덤}",
  "subject": "...",
  "from": "...",
  "receivedAt": "현재 시각 ISO",
  "score": 10,
  "summary": "...",
  "actions": ["...", "..."],
  "source": "meeting | mail | directive"
}
```

> 매칭 비활성 상태이므로 `targetProjectId` 필드는 항상 생략(신규 카드).

**시크릿**: `EMAIL_INGEST_SECRET` = `Pr-Mail-Ingest-K9x4f2j7Lq3w8r5n`

**Bash 명령** (heredoc):
```bash
curl -sS -X POST https://pr-board-phi.vercel.app/api/email-ingest \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Secret: Pr-Mail-Ingest-K9x4f2j7Lq3w8r5n" \
  --data-binary @- <<'PAYLOAD'
{...}
PAYLOAD
```

> 권한 거부 시 명령어만 사용자에게 출력. `!` 로 실행 안내.

---

## 5. 응답 처리

**`mode: "merged"`** — 기존 프로젝트에 세부업무 추가:
```
✅ 기존 프로젝트에 등록 완료

📍 {프로젝트명}
   └ [부모 todo] {subject}
       ├ 1. {액션1}
       ├ 2. {액션2}
       └ ...

🔗 https://pr-board-phi.vercel.app/projects/{targetProjectId}
```

**`mode: "new"`** — 신규 카드(프로젝트):
```
✅ 신규 카드 등록 완료 (내 보드)

📥 {subject}
   ├ 📋 원문 요약·메타 (코멘트에 from/시간/점수/링크)
   ├ 1. {액션1}
   └ ...

🔗 https://pr-board-phi.vercel.app/projects/{projectId}
```

**중복 (`duplicate: true`)**:
```
⚠️ 이미 등록된 카드입니다.
🔗 https://pr-board-phi.vercel.app/projects/{projectId}
```

**실패** (401·500 등):
```
❌ 등록 실패: {에러 메시지}
명령어 직접 실행:
{curl 명령어 그대로}
```

---

## 6. 중복 방지

`messageId` 같으면 서버가 자동 중복 처리. 수동 등록은 `manual-{timestamp}-{rand}` 형태라 충돌 X. 명시적으로 같은 ID로 재등록 원하면 `messageId` 인자 받기.

---

## 7. 사용자 확인 시점

본문 모호할 때만 (예: from·subject 추정 불가) 1회 확인:
```
질문 (한 번만):
  - from(지시자/발신자/회의명): {추정 or "미상"}
  - subject: {추정}
  맞나요? 수정 사항 있으면 알려주세요.
```

---

## 8. 안전 원칙

- 본인 인박스에만 들어감 (private). 팀 노출 0.
- 본문에 비밀번호·계좌번호 등 민감정보 있으면 요약 시 마스킹, 원문 코멘트 미포함.
- 등록 실패 시 사용자에게 명확히 보고. "완료" 거짓 보고 금지.
- **카드 삭제 절대 금지**: 사용자가 "지워"라고 명시하지 않는 한 DELETE 호출 X.

---

## 9. 후속 액션 (모드 종료 후)

회의록 유형(1)이고 actions가 5개 초과로 잘렸을 경우:
> "📝 To do 항목이 많아 5개로 압축했어요. 정밀 등록(항목별 개별 카드 + owner/due_date 매핑) 원하시면 'X번 분리' 또는 '다중 카드로 다시'."

(수동 분리·다중 INSERT는 Supabase REST가 필요하므로 키 확보 후 가능.)

---

## 10. 사용자 입력

$ARGUMENTS
