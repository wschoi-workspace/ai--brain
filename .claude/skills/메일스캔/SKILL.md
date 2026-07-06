---
name: 메일스캔
description: ws.choi Gmail 받은편지함을 스캔해 PR 보드 인박스로 카드 등록. gws CLI로 메일을 읽고 분석→/api/email-ingest. "메일스캔", "메일 스캔", "받은편지함 스캔", "보드 메일 동기화", "새 메일 보드에", "메일 카드화" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Bash
---

# /메일스캔 — Gmail → PR 보드 인박스 동기화 (gws CLI 방식)

ws.choi@project-rent.com 받은편지함의 새 메일을 gws CLI로 읽어 분석한 뒤, 업무성 메일을
PR 보드(`https://pr-board-phi.vercel.app`) 인박스에 📥 신규 카드로 등록한다.

> 전용 계정: **ws.choi@project-rent.com** (최원석 / macOS)
> Apps Script·웹앱 URL·토큰 불필요 — 이미 인증된 `gws` CLI를 직접 사용한다.

---

## 1. 인증 가드 (먼저 실행)

```bash
gws auth status 2>&1 | grep -iE "userinfo|valid|expired"
```

- 인증이 유효하고 계정이 `ws.choi@project-rent.com`이면 진행.
- 만료/다른 계정이면 중단하고 안내:
  > "GWS 인증이 필요합니다. 터미널에 `! gws auth login --full` 을 입력해 ws.choi@project-rent.com으로 로그인해주세요."

---

## 2. 스캔 범위 결정 (`$ARGUMENTS`)

| 입력 | Gmail 쿼리 |
|---|---|
| (없음) | `is:unread` (안읽은 메일 전체) |
| `업무` | `label:업무 is:unread` |
| `3일` / `최근` | `newer_than:3d` |
| `오늘` | `newer_than:1d` |
| 그 외 텍스트 | 그대로 Gmail 검색 쿼리로 사용 |

최대 건수는 기본 20 (`--max 20`). "전체"·"많이"면 `--max 50`까지.

```bash
gws gmail +triage --query '<쿼리>' --max 20 --format json
```

→ 각 항목에서 `id`, `from`(발신자), `subject`, `date` 확보.

---

## 3. 메일별 본문 읽기

triage로 얻은 각 `id`에 대해:

```bash
gws gmail +read --id <ID> --format json
```

→ JSON 키: `subject`, `from`, `date`, **`body_text`**(plain text 본문), `body_html`, `to`, `cc`.
> ⚠️ 본문 필드는 `body_text`다 (`body` 아님). `body_text`가 비면 `body_html`에서 텍스트 추출.

> 본문이 길면 앞 1500자 + 마감일·금액·일정 키워드 주변만 발췌. 인사말·서명·푸터·이전 인용은 제외.

---

## 4. 메일별 분석 (보드등록 §2 유형 3 동일)

각 메일에서 추출:
1. **subject** — 메일 제목 (50자 이내 압축)
2. **from** — 발신자 이름·이메일
3. **summary** — 본문 핵심 3~5문장 (마감일·금액·일정 포함, 서명/인사말 제외)
4. **actions** — 본인이 직접 해야 할 일 0~5개 ("견적서 회신", "5/28 미팅 확정" 등)
5. **score** — 시급도 1~10 (마감 임박·금액 큼·CEO/클라이언트 발신 → 높게)
6. **source** — `"mail"` 고정

### 스킵 규칙 (카드화 제외)
- 광고·뉴스레터·자동발송(no-reply)·영수증·시스템 알림 → 카드화 안 함 (processed엔 집계, cardified 제외)
- 업무 관련성이 명확한 메일만 등록. 애매하면 등록하되 score 낮게.

---

## 5. PR 보드 ingest 호출 (메일 1건 = 카드 1건)

카드화 대상 각 메일에 대해 POST `/api/email-ingest`:

```bash
curl -sS -X POST https://pr-board-phi.vercel.app/api/email-ingest \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Secret: Pr-Mail-Ingest-K9x4f2j7Lq3w8r5n" \
  --data-binary @- <<PAYLOAD
{
  "to": "ws.choi@project-rent.com",
  "messageId": "gmail-<Gmail메시지ID>",
  "subject": "...",
  "from": "...",
  "receivedAt": "<메일 date ISO>",
  "score": 7,
  "summary": "...",
  "actions": ["..."],
  "source": "mail"
}
PAYLOAD
```

- **중복 방지**: `messageId`를 `gmail-<Gmail ID>`로 고정 → 같은 메일 재스캔 시 서버가 자동 중복 처리(`duplicate: true`). 안전하게 반복 실행 가능.
- 매칭(기존 프로젝트 합치기)은 보드등록과 동일하게 **현재 비활성** → `targetProjectId` 생략, 항상 신규 카드.
- 권한 거부 시 curl 명령만 출력하고 `!` 실행 안내.

---

## 6. 결과 보고

```
✅ 메일스캔 완료

📊 스캔: {triage 건수}건
📨 카드화: {ok+new 건수}건  (⏭ 중복 {duplicate}건 · 스킵 {광고/시스템}건)

등록된 카드:
  📥 {subject1} — {from1} (score {n})
  📥 {subject2} — {from2} (score {n})

🔗 https://pr-board-phi.vercel.app/?tab=personal
```

실패 건이 있으면 메일별로 명확히 표기. "완료" 거짓 보고 금지.

---

## 7. 안전 원칙

- **읽기 전용**: gws는 메일을 수정/삭제하지 않는다 (`+triage`/`+read` 모두 read-only).
- 메일 본문의 비밀번호·계좌번호 등 민감정보는 summary에서 마스킹.
- 카드는 본인 보드(private)에만. 팀 노출 0.
- **카드 삭제 절대 금지** (보드등록과 동일 정책).

---

## 8. 참고 — 자동 백그라운드 동기화 (선택)

`/메일스캔`은 호출 시 동작한다. 5분/주기 자동 동기화를 원하면 launchd로
이 스캔 로직을 래핑한 셸 스크립트를 주기 실행하도록 등록할 수 있다(별도 요청 시 구성).
기존 `morning` 텔레그램 자동화(launchd)와 동일한 패턴.

---

## 9. 사용자 입력

$ARGUMENTS
