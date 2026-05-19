---
name: morning
description: 아침 업무 브리핑. "모닝", "아침 브리핑", "morning", "메일 체크", "오늘 할일", "업무 정리", "오늘할일", "오늘일정", "굿모닝", "일일보고", "#오늘할일", "#오늘일정", "#굿모닝", "#일일보고" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Morning Briefing — 아침 업무 브리핑

GWS CLI를 사용하여 메일과 캘린더를 자동 검색하고, 업무 관련 메일만 필터링하여 레이블 추가 후 써머리를 제공합니다.

---

## 사전 확인

```bash
gws auth status 2>&1 | grep -E '"token_valid"|"user"'
```

- `token_valid: true`이고 `user: ws.choi@project-rent.com`이면 진행
- 토큰이 만료되었거나 다른 계정이면:
  - "GWS 인증이 필요합니다. `! gws auth login --full`을 실행하고 ws.choi@project-rent.com으로 로그인해주세요." 안내 후 중단

---

## Step 1: 메일 수집 (최근 3일)

### 1-1. ws.choi@project-rent.com 메일 검색

projectrent43@gmail.com → ws.choi@project-rent.com 자동 전달 설정됨 (2026-04-22).
ws.choi 메일함 하나만 검색하면 양쪽 메일이 모두 포함됨.

```bash
gws gmail users messages list --params '{"userId": "me", "q": "newer_than:3d -category:promotions -category:social -from:noreply -from:no-reply -from:notifications -from:mailer-daemon -from:calendar-notification -label:광고/비업무", "maxResults": 50}'
```

### 1-2. 각 메일 상세 조회

각 message ID에 대해:
```bash
gws gmail users messages get --params '{"userId": "me", "id": "MESSAGE_ID", "format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]}'
```

snippet, labelIds(UNREAD 여부), From, Subject, Date 추출

### 1-3. 업무 메일 필터링

AI가 각 메일을 판단하여 분류:

**업무 메일 (포함)**:
- 거래처, 클라이언트, 동료, 파트너로부터의 메일
- 업무 요청, 질문, 확인, 자료 송부, 미팅 관련
- 매출 리포트, 세금계산서, 계약서 등 비즈니스 문서
- 모니터링 리포트 (Brand24 등 업무에 직접 관련된 것)
- Slack 결제/알림 등 업무 인프라 관련

**제외**:
- 캘린더 초대/공유 알림
- 서비스 가입 확인 (Fly.io, Buffer 초기 설정 등)
- 순수 뉴스레터, 광고, 소셜 미디어 알림
- Google 보안 알림

### 1-4. "업무" 레이블 추가

먼저 "업무" 레이블 존재 확인:
```bash
gws gmail users labels list --params '{"userId": "me"}'
```

레이블이 없으면 생성:
```bash
gws gmail users labels create --params '{"userId": "me"}' --json '{"name": "업무", "labelListVisibility": "labelShow", "messageListVisibility": "show"}'
```

업무 메일에 레이블 적용:
```bash
gws gmail users messages modify --params '{"userId": "me", "id": "MESSAGE_ID"}' --json '{"addLabelIds": ["LABEL_ID"]}'
```

### 1-5. 회신 필요 여부 판단

각 업무 메일에 대해:
- **내가 보낸 메일 (From: ws.choi)** → 회신 대기 상태 표시
- **받은 메일 + UNREAD** → 🔴 회신 필요
- **받은 메일 + READ + 요청/질문 포함** → 🔴 회신 필요
- **받은 메일 + READ + 정보 공유/리포트** → 확인 완료

---

## Step 2: 캘린더 수집 (오늘 + 내일)

### 대상 캘린더 (4개)

| 캘린더 | ID |
|--------|-----|
| ws.choi (메인) | `ws.choi@project-rent.com` |
| timehora (개인) | `timehora@gmail.com` |
| PROJECT RENT | `f8apotjh6dkg5i8e90onoeim5k@group.calendar.google.com` |
| filament필라멘트 | `g4pn2cr0p2hle0e94rp9c5q7cs@group.calendar.google.com` |

### 날짜 계산

```bash
TODAY=$(date +%Y-%m-%d)
TOMORROW=$(date -v+1d +%Y-%m-%d)
DAY_AFTER=$(date -v+2d +%Y-%m-%d)
```

### 각 캘린더 일정 조회

```bash
gws calendar events list --params '{"calendarId": "CALENDAR_ID", "timeMin": "${TODAY}T00:00:00+09:00", "timeMax": "${DAY_AFTER}T00:00:00+09:00", "singleEvents": true, "orderBy": "startTime", "maxResults": 20}'
```

### 일정 병합 및 중복 제거

4개 캘린더의 일정을 시간순으로 정렬하고, 동일한 이벤트(제목+시간 일치)는 중복 제거

### 일정 충돌 감지

같은 시간대에 2개 이상 일정이 있으면 ⚠️ 표시

---

## Step 2.5: 임대료/매출정산 송금 일정 확인 (오늘~3일 이내)

### 마스터 데이터 참조

임대료/관리비/매출정산 마스터 시트:
- **Google Sheet**: https://docs.google.com/spreadsheets/d/1GnRavajuMx4jpD4gyHo9bKDVEwDg79eV
- 캘린더 일정의 description에 금액/계좌 정보가 포함되어 있으나, 최신 금액은 위 시트를 기준으로 한다.

모든 대상 캘린더(ws.choi, timehora)에서 송금 관련 키워드를 검색한다.

```bash
TODAY=$(date +%Y-%m-%d)
PLUS3=$(date -v+3d +%Y-%m-%d)
```

### 검색 대상

| 캘린더 | ID |
|--------|-----|
| ws.choi (메인) | `ws.choi@project-rent.com` |
| timehora (개인) | `timehora@gmail.com` |

### 검색 키워드 (각 캘린더마다 모두 실행)

```bash
# 키워드: "임대료", "매출정산", "송금"
for CAL_ID in "ws.choi@project-rent.com" "timehora@gmail.com"; do
  for KEYWORD in "임대료" "매출정산" "송금"; do
    gws calendar events list --params "{\"calendarId\": \"$CAL_ID\", \"q\": \"$KEYWORD\", \"singleEvents\": true, \"orderBy\": \"startTime\", \"timeMin\": \"${TODAY}T00:00:00+09:00\", \"timeMax\": \"${PLUS3}T23:59:59+09:00\", \"maxResults\": 10}"
  done
done
```

### 결과 처리

- 중복 제거 (동일 이벤트 ID)
- description 필드에서 송금액, 받는 사람, 은행, 계좌 정보를 추출하여 테이블로 표시
- 결과가 있으면 **💰 임대료 송금 섹션**에 표시하고, **✅ 오늘 할 일 우선순위**에도 "임대료 송금 처리 — {장소} {금액}" 항목을 추가
- 결과가 없으면 "해당 기간 송금 예정 없음"과 함께 다음 송금일을 안내

---

## Step 2.6: 프로젝트 현황 수집

```bash
find /Users/choi_ai/do-better-workspace/10-projects/ -name "email-history.md" -type f
```

각 파일을 Read로 읽어서 프로젝트명, 상태, 미회신/대기 항목을 추출한다.
미완료 대기 항목(`- [ ]`)이 있는 프로젝트만 리포트에 포함한다.

---

## Step 3: HTML 리포트 생성

수집된 데이터를 HTML 파일로 생성하여 `40-personal/41-daily/YYYY-MM/morning-YYYY-MM-DD.html`에 저장한다.
저장 후 `open` 명령으로 브라우저에서 자동 열기.

```bash
open /Users/choi_ai/do-better-workspace/40-personal/41-daily/YYYY-MM/morning-YYYY-MM-DD.html
```

### HTML 템플릿

아래 구조를 기반으로 **실제 수집된 데이터**를 채워 HTML 파일을 Write한다.
각 섹션은 데이터가 있을 때만 표시한다.

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>모닝 브리핑 — YYYY년 M월 D일</title>
<style>
  :root {
    --bg: #0f0f0f;
    --surface: #1a1a2e;
    --surface2: #16213e;
    --accent: #e94560;
    --accent2: #0f3460;
    --text: #eee;
    --text-dim: #999;
    --green: #00c853;
    --yellow: #ffd600;
    --red: #ff1744;
    --blue: #448aff;
    --border: #2a2a4a;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 2rem;
    max-width: 960px;
    margin: 0 auto;
    line-height: 1.6;
  }
  .header {
    text-align: center;
    padding: 2rem 0 1.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
  }
  .header h1 {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #e94560, #0f3460);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .header .date {
    color: var(--text-dim);
    font-size: 0.95rem;
    margin-top: 0.3rem;
  }
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
  }
  .stat-card .number {
    font-size: 2rem;
    font-weight: 800;
  }
  .stat-card .label {
    font-size: 0.8rem;
    color: var(--text-dim);
    margin-top: 0.2rem;
  }
  .stat-card.urgent .number { color: var(--red); }
  .stat-card.pending .number { color: var(--yellow); }
  .stat-card.schedule .number { color: var(--blue); }
  .stat-card.project .number { color: var(--green); }

  .section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }
  .section-title {
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .section-title .icon {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
  }
  .icon-mail { background: rgba(233,69,96,0.2); }
  .icon-cal { background: rgba(68,138,255,0.2); }
  .icon-money { background: rgba(255,214,0,0.2); }
  .icon-project { background: rgba(0,200,83,0.2); }
  .icon-todo { background: rgba(233,69,96,0.2); }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }
  th {
    text-align: left;
    padding: 0.6rem 0.8rem;
    color: var(--text-dim);
    font-weight: 600;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border);
  }
  td {
    padding: 0.7rem 0.8rem;
    border-bottom: 1px solid rgba(42,42,74,0.5);
    vertical-align: top;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.02); }

  a.mail-link {
    color: var(--text);
    text-decoration: none;
    border-bottom: 1px dashed var(--text-dim);
    transition: all 0.2s;
  }
  a.mail-link:hover {
    color: var(--blue);
    border-bottom-color: var(--blue);
  }

  .badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  .badge-red { background: rgba(255,23,68,0.15); color: var(--red); }
  .badge-yellow { background: rgba(255,214,0,0.15); color: var(--yellow); }
  .badge-green { background: rgba(0,200,83,0.15); color: var(--green); }
  .badge-blue { background: rgba(68,138,255,0.15); color: var(--blue); }
  .badge-gray { background: rgba(153,153,153,0.15); color: var(--text-dim); }

  .conflict { color: var(--yellow); font-weight: 600; }
  .time { color: var(--blue); font-weight: 500; font-variant-numeric: tabular-nums; }

  .todo-list {
    list-style: none;
    counter-reset: todo;
  }
  .todo-list li {
    counter-increment: todo;
    padding: 0.7rem 0;
    border-bottom: 1px solid rgba(42,42,74,0.5);
    display: flex;
    align-items: center;
    gap: 0.8rem;
  }
  .todo-list li:last-child { border-bottom: none; }
  .todo-list li::before {
    content: counter(todo);
    background: var(--accent);
    color: #fff;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    flex-shrink: 0;
  }

  .empty-state {
    color: var(--text-dim);
    text-align: center;
    padding: 1.5rem;
    font-size: 0.9rem;
  }

  .footer {
    text-align: center;
    color: var(--text-dim);
    font-size: 0.75rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    margin-top: 1rem;
  }
</style>
</head>
<body>

<div class="header">
  <h1>☀️ 모닝 브리핑</h1>
  <div class="date">YYYY년 M월 D일 (요일)</div>
</div>

<!-- ── 요약 카드 ── -->
<div class="stats">
  <div class="stat-card urgent">
    <div class="number">{회신필요수}</div>
    <div class="label">회신 필요</div>
  </div>
  <div class="stat-card pending">
    <div class="number">{대기수}</div>
    <div class="label">발신/대기</div>
  </div>
  <div class="stat-card schedule">
    <div class="number">{오늘일정수}</div>
    <div class="label">오늘 일정</div>
  </div>
  <div class="stat-card project">
    <div class="number">{프로젝트수}</div>
    <div class="label">활성 프로젝트</div>
  </div>
</div>

<!-- ── 📬 업무 메일 ── -->
<div class="section">
  <div class="section-title">
    <span class="icon icon-mail">📬</span> 업무 메일 (최근 3일)
  </div>

  <!-- 회신 필요: 제목을 Gmail 링크로 감싸서 클릭 시 해당 메일로 이동 -->
  <!-- Gmail 링크 형식: https://mail.google.com/mail/u/0/#inbox/MESSAGE_ID -->
  <h4 style="color:var(--red); margin-bottom:0.5rem; font-size:0.85rem;">🔴 회신 필요</h4>
  <table>
    <tr><th>발신자</th><th>제목</th><th>요약</th><th>상태</th></tr>
    <tr>
      <td>{발신자}</td>
      <td><a class="mail-link" href="https://mail.google.com/mail/u/0/#inbox/{MESSAGE_ID}" target="_blank">{제목}</a></td>
      <td>{요약}</td>
      <td><span class="badge badge-red">{상태}</span></td>
    </tr>
  </table>

  <!-- 발신/회신 대기 -->
  <h4 style="color:var(--yellow); margin:1rem 0 0.5rem; font-size:0.85rem;">📋 발신/회신 대기</h4>
  <table>
    <tr><th>발신자</th><th>제목</th><th>상태</th></tr>
    <tr>
      <td>{발신자}</td>
      <td><a class="mail-link" href="https://mail.google.com/mail/u/0/#inbox/{MESSAGE_ID}" target="_blank">{제목}</a></td>
      <td><span class="badge badge-yellow">{상태}</span></td>
    </tr>
  </table>

  <!-- 모니터링/참고 -->
  <h4 style="color:var(--blue); margin:1rem 0 0.5rem; font-size:0.85rem;">📊 모니터링/참고</h4>
  <table>
    <tr><th>발신자</th><th>제목</th><th>조치</th></tr>
    <tr>
      <td>{발신자}</td>
      <td><a class="mail-link" href="https://mail.google.com/mail/u/0/#inbox/{MESSAGE_ID}" target="_blank">{제목}</a></td>
      <td><span class="badge badge-blue">{조치}</span></td>
    </tr>
  </table>
</div>

<!-- ── 📅 일정 ── -->
<div class="section">
  <div class="section-title">
    <span class="icon icon-cal">📅</span> 오늘 일정 (M/D 요일)
  </div>
  <table>
    <tr><th>시간</th><th>일정</th><th>비고</th></tr>
    <tr>
      <td class="time">{시간}</td>
      <td>{일정명}</td>
      <td>{비고 또는 <span class="conflict">⚠️ 충돌</span>}</td>
    </tr>
  </table>
</div>

<div class="section">
  <div class="section-title">
    <span class="icon icon-cal">📅</span> 내일 일정 (M/D 요일)
  </div>
  <table>
    <tr><th>시간</th><th>일정</th><th>비고</th></tr>
    <tr>
      <td class="time">{시간}</td>
      <td>{일정명}</td>
      <td>{비고}</td>
    </tr>
  </table>
</div>

<!-- ── 💰 임대료 송금 ── -->
<!-- 송금 예정이 있을 때만 이 섹션 표시 -->
<div class="section">
  <div class="section-title">
    <span class="icon icon-money">💰</span> 임대료 송금 알림 (3일 이내)
  </div>
  <table>
    <tr><th>송금일</th><th>장소</th><th>금액</th><th>받는 사람</th><th>계좌</th></tr>
    <tr>
      <td>{송금일}</td>
      <td>{장소}</td>
      <td>{금액}</td>
      <td>{받는사람}</td>
      <td>{계좌}</td>
    </tr>
  </table>
  <!-- 없으면: <div class="empty-state">해당 기간 송금 예정 없음. 다음 송금일: MM/DD (장소)</div> -->
</div>

<!-- ── 📂 프로젝트 현황 ── -->
<div class="section">
  <div class="section-title">
    <span class="icon icon-project">📂</span> 프로젝트 현황
  </div>
  <table>
    <tr><th>#</th><th>프로젝트</th><th>상태</th><th>긴급 액션</th></tr>
    <tr>
      <td>1</td>
      <td>{프로젝트명}</td>
      <td><span class="badge badge-red">{상태}</span></td>
      <td>{긴급액션}</td>
    </tr>
  </table>
</div>

<!-- ── ✅ 오늘 할 일 ── -->
<div class="section">
  <div class="section-title">
    <span class="icon icon-todo">✅</span> 오늘 할 일 우선순위
  </div>
  <ol class="todo-list">
    <li>{가장 긴급한 회신/처리}</li>
    <li>{마감 임박 건}</li>
    <li>{오늘 일정 준비}</li>
  </ol>
</div>

<div class="footer">
  Generated by Claude Code · /morning · {timestamp}
</div>

</body>
</html>
```

### 템플릿 사용 규칙

- `{플레이스홀더}` 부분을 실제 데이터로 치환하여 HTML 파일을 Write한다
- 데이터가 없는 섹션은 해당 `<div class="section">` 블록 자체를 생략한다
- 회신 필요 메일이 없으면 "🔴 회신 필요" 서브섹션 생략, 대신 다른 서브섹션만 표시
- 일정이 없으면 `<div class="empty-state">일정 없음</div>` 표시
- 프로젝트는 미완료 대기 항목이 있는 것만 표시
- badge 클래스: 긴급=badge-red, 대기=badge-yellow, 완료=badge-green, 참고=badge-blue, 비활성=badge-gray
- 상태 뱃지 매핑: 🔴 → badge-red, 🟡 → badge-yellow, 완료 → badge-green
- stats 카드의 숫자는 실제 카운트로 채운다
- 파일 저장 후 `open` 명령으로 브라우저에서 자동 열기

### 터미널 요약 출력

HTML 파일 생성 후 터미널에도 **한 줄 요약**을 출력한다:

```
모닝 브리핑 저장 완료: 40-personal/41-daily/YYYY-MM/morning-YYYY-MM-DD.html
📬 회신필요 {N}건 | 📅 오늘 일정 {N}건 | 📂 활성 프로젝트 {N}건
```

### 우선순위 결정 기준

1. 마감 기한이 있는 회신 (금주 중, 오늘까지 등)
2. 다운로드 기한이 있는 자료
3. 오늘 일정 관련 준비
4. 의사결정이 필요한 건 (유료전환, 승인 등)
5. 내일 일정 준비
6. 일반 확인/참고 사항

---

## 참고

- GWS CLI 인증: `gws auth login --full` (ws.choi@project-rent.com)
- projectrent43@gmail.com → ws.choi@project-rent.com 자동 전달 설정됨 (별도 체크 불필요)
- 양쪽 계정에 "광고/비업무" 레이블 + Gmail 필터 설정됨 (자동 분류)
- 레이블 ID는 세션마다 다를 수 있으므로 매번 labels list로 확인 필요
