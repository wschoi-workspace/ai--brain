# Payment — 결제/송금 대시보드

HR포탈 결제시스템의 구글시트 마스터를 읽어서 결제 현황을 정리하고 HTML 대시보드로 표시한다.

---

## 트리거

"payment", "결제", "결제현황", "송금현황", "결제 승인", "오늘 결제", "결제 대시보드" 등을 언급하면 자동 실행.

---

## 데이터 소스

### 1. HR포탈 마스터시트

```
Google Sheet ID: 1kWSzNqv5UX97EUYFm6LBEWe2kDuH0CAbtUC3sHEF7so
URL: https://docs.google.com/spreadsheets/d/1kWSzNqv5UX97EUYFm6LBEWe2kDuH0CAbtUC3sHEF7so
```

Google Drive MCP의 `read_file_content` 도구로 시트 전체를 읽는다.

### 2. 시트 구조

| 시트(테이블) | 용도 | 핵심 컬럼 |
|-------------|------|----------|
| **결제요청** | 법인 결제/송금 요청 | 월, No, 신청일, 신청자, 팀, 금액, 거래처, 담당자명, 연락처, 이메일, 비고, 상태, 발행회사, 드라이브_링크 |
| **일용직급여** | 프리랜서/일용직 급여 지급 | 월, No, 근로일시, 수령인, 주민번호, 은행, 계좌번호, 소득유형, 총지급액, 소득세, 지방소득세, 원천징수합계, 실수령액, 지급희망일, 입력자, 비용귀속회사, 드라이브_링크, 상태 |

### 3. 임대료 마스터시트 (정기 송금)

```
Google Sheet ID: 1GnRavajuMx4jpD4gyHo9bKDVEwDg79eV
URL: https://docs.google.com/spreadsheets/d/1GnRavajuMx4jpD4gyHo9bKDVEwDg79eV
```

정기 임대료/관리비/수수료 정보. 캘린더와 연동되어 있으므로 3일 이내 송금 예정건만 표시.

---

## Step 1: 데이터 수집

### 1-1. HR포탈 마스터시트 읽기

Google Drive MCP `read_file_content`로 시트 내용을 읽는다.

### 1-2. 데이터 파싱

시트에서 다음 테이블을 분리하여 파싱:
- **결제요청 테이블**: `신청일 | 신청자 | 팀 | 금액 | 거래처 | ...` 컬럼 구조
- **일용직급여 테이블**: `근로일시 | 수령인 | 주민번호 | 은행 | ...` 컬럼 구조

### 1-3. 상태별 분류

각 건을 상태별로 분류:
- **대기**: 아직 승인/반려되지 않은 건 → 🔴 처리 필요
- **승인**: 승인 완료, 송금 대기 → 🟡 송금 처리
- **반려**: 반려된 건 → ⬜ 참고
- **완료**: 송금 완료 → ✅ 완료

### 1-4. 정기 송금 확인 (3일 이내)

캘린더에서 3일 이내 임대료/매출정산 송금 일정도 함께 조회:

```bash
TODAY=$(date +%Y-%m-%d)
PLUS3=$(date -v+3d +%Y-%m-%d)
for CAL_ID in "ws.choi@project-rent.com" "timehora@gmail.com"; do
  for KEYWORD in "임대료" "매출정산" "송금" "관리비" "운영비" "수도요금"; do
    gws calendar events list --params "{\"calendarId\": \"$CAL_ID\", \"q\": \"$KEYWORD\", \"singleEvents\": true, \"orderBy\": \"startTime\", \"timeMin\": \"${TODAY}T00:00:00+09:00\", \"timeMax\": \"${PLUS3}T23:59:59+09:00\", \"maxResults\": 10}"
  done
done
```

---

## Step 2: HTML 대시보드 생성

`40-personal/41-daily/YYYY-MM/payment-YYYY-MM-DD.html`에 저장한다.

### HTML 구조

```
┌─────────────────────────────────────────┐
│  💳 결제 대시보드 — YYYY년 M월 D일       │
├─────────────────────────────────────────┤
│  [대기 N건] [승인 N건] [완료 N건] [반려 N건] │  ← 요약 카드
├─────────────────────────────────────────┤
│  🔴 처리 필요 (대기)                      │  ← 대기 건 테이블
│  신청일 | 신청자 | 금액 | 거래처 | 내용    │
├─────────────────────────────────────────┤
│  🟡 송금 대기 (승인 완료)                  │  ← 승인 건 테이블
│  신청일 | 금액 | 수취인 | 은행 | 계좌     │
├─────────────────────────────────────────┤
│  💰 정기 송금 (3일 이내)                   │  ← 임대료/관리비
│  송금일 | 장소 | 금액 | 받는사람 | 계좌   │
├─────────────────────────────────────────┤
│  📊 월간 요약                             │  ← 이번 달 전체 통계
│  총 결제액, 건수, 카테고리별 분류          │
├─────────────────────────────────────────┤
│  ⬜ 반려 내역 (접이식)                     │  ← 반려 건 (기본 접힘)
└─────────────────────────────────────────┘
```

### 디자인 가이드

- /morning과 동일한 다크 테마 사용 (--bg: #0f0f0f, --surface: #1a1a2e)
- Pretendard 폰트
- 금액은 천단위 콤마 + 우측 정렬
- 드라이브 링크가 있는 건은 📎 아이콘으로 링크 연결
- 주민번호 등 민감정보는 마스킹 (앞6자리만 표시)

### 터미널 요약 출력

```
결제 대시보드 저장 완료: 40-personal/41-daily/YYYY-MM/payment-YYYY-MM-DD.html
🔴 대기 {N}건 | 🟡 승인 {N}건 (송금 대기 {총액}원) | 💰 정기송금 {N}건
```

---

## Step 3: 브라우저 열기

```bash
open /path/to/payment-YYYY-MM-DD.html
```

---

## Step 4: 결제건 관리 (삭제/상태변경)

사용자가 "결제 삭제", "반려건 삭제", "중복 삭제" 등을 요청하면 실행한다.

### 4-1. 삭제 대상 확인

대시보드 생성 시 반려(중복) 건이 있으면 터미널에 안내:
```
⚠️ 반려(중복) {N}건 발견. "반려건 삭제해줘"로 정리 가능
```

### 4-2. 구글시트에서 행 삭제

```bash
# 세금계산서 시트(sheetId: 252652606)에서 특정 행 삭제
# startIndex/endIndex는 0-indexed (헤더=0, 데이터 1행=1)
gws sheets spreadsheets batchUpdate \
  --params '{"spreadsheetId": "1kWSzNqv5UX97EUYFm6LBEWe2kDuH0CAbtUC3sHEF7so"}' \
  --json '{
    "requests": [{
      "deleteDimension": {
        "range": {
          "sheetId": 252652606,
          "dimension": "ROWS",
          "startIndex": START,
          "endIndex": END
        }
      }
    }]
  }'
```

**주의**: 행 삭제 시 뒤의 행이 위로 당겨지므로, 삭제는 아래→위 순서로 하거나 한번에 범위 지정한다.

### 4-3. HR포탈 캐시 갱신

시트 삭제 후 HR포탈 캐시를 리프레시:
```bash
curl -s -X POST "https://rent-hr-portal.fly.dev/api/master/refresh"
```

### 4-4. 삭제 후 확인

```bash
# 시트 재조회로 삭제 확인
gws sheets spreadsheets values get \
  --params '{"spreadsheetId": "...", "range": "세금계산서!A1:N20"}'
```

### 시트 구조 참고

| 시트 이름 | sheetId | 용도 |
|-----------|---------|------|
| 결제 | 2070694914 | 결제요청 (물품/용역) |
| 세금계산서 | 252652606 | 세금계산서 발행 요청 |
| 휴가 | 919700074 | 휴가 신청 |
| 야근 | 896676193 | 야근/초과근무 |
| 일용직 | 1484172241 | 일용직/프리랜서 급여 |
| 직원 | 1238586416 | 직원 마스터 |
| 프로젝트 | 525246559 | 프로젝트 목록 |
| 재직증명서 | 918577308 | 재직증명서 발급 |

### HR포탈 API 참고

| 엔드포인트 | 메서드 | 용도 |
|-----------|--------|------|
| /api/invoice/list?month=YYYY-MM | GET | 세금계산서 목록 조회 |
| /api/payment/list?month=YYYY-MM | GET | 결제요청 목록 조회 |
| /api/daily/list?month=YYYY-MM | GET | 일용직급여 목록 조회 |
| /api/master/refresh | POST | 마스터시트 캐시 갱신 |
| /api/analytics/summary?month=YYYY-MM | GET | 월간 분석 요약 |

**인증 필요 시**: GWS spreadsheets 쓰기 스코프 필요 → `! gws auth login --full` 실행

---

## 참고

- HR포탈 URL: https://rent-hr-portal.fly.dev
- 결제 드라이브 폴더: https://drive.google.com/drive/folders/14dX5ElvZHEmd3ROXuZHKupgRKY4YzYBY
- 임대료 마스터시트: https://docs.google.com/spreadsheets/d/1GnRavajuMx4jpD4gyHo9bKDVEwDg79eV
- HR포탈 마스터시트: https://docs.google.com/spreadsheets/d/1kWSzNqv5UX97EUYFm6LBEWe2kDuH0CAbtUC3sHEF7so
- 결제요청의 각 건에 드라이브_링크가 있으면 첨부파일(영수증/견적서 등) 확인 가능
