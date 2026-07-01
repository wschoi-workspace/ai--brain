---
name: 주간분장
description: 주간 업무분장 생성 — 대표가 팀별 업무 텍스트를 입력하면 파싱→HTML 제작→구글시트 등록→팀별 텔레그램 발송. "주간분장", "주간 분장", "업무분장", "이번주 할일", "weekly assignment", "분장표" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# 주간 업무분장 — Weekly Task Assignment

대표가 팀별 업무를 자유 텍스트로 입력하면:
1. 파싱: 팀 섹션 분리 → 항목 추출 (번호/내용/담당/마감/우선순위)
2. HTML 생성: project-rent 디자인가이드 적용
3. 시트 등록: 구글시트 '주간분장' 탭에 append
4. 아카이브: `20-operations/23-arisa/weekly/assignment-YYYY-WXX.html` 저장
5. 텔레그램: 팀별로 해당 팀 분장만 발송, 대표에겐 전체

---

## Step 0: 입력 수집

사용자에게 팀별 업무 텍스트를 요청한다. 자유 형식(마크다운, 번호, 불릿 등)을 모두 허용.

입력 예시:
```
## 기획팀
1. CJ 시안 수정 @양지혜 ~수요일 (최우선)
2. 봉은사 중간보고 자료 @정예은 ~금요일
3. 구비 답십리 현장조사 @조나연

## 공간팀
1. 봉은사 도면 리뷰 @김가은 ~화요일 (최우선)
2. 서촌 공간 레이아웃 @김예진
```

텍스트가 이미 메시지에 포함되어 있으면 바로 파싱 단계로 진행한다.

---

## Step 1: 파싱

### 명부 로드
```bash
cat 00-system/02-scripts/arisa-employees.json
```

### 파싱 규칙

1. **팀 섹션 감지**: `##`, `###`, `[팀명]`, `팀명:` 등의 패턴으로 팀 구분
   - 팀명은 명부의 team 필드와 매칭: 경영, 사업기획, 공간팀, 기획팀, 운영팀, 감사
   - 유사 표현 정규화: "기획" → "기획팀", "공간" → "공간팀", "운영" → "운영팀", "사업" → "사업기획"

2. **항목 추출**: 각 줄에서 다음을 추출
   - **업무내용**: 번호/불릿 제거 후 본문
   - **담당자**: `@이름`, `@이름님` 패턴. 명부에서 매칭하여 정규화.
     - 담당 미지정 → 담당 = "팀" (팀 레벨 업무)
   - **마감**: `~요일`, `~M/D`, `까지`, `마감:` 패턴. 이번 주 날짜로 변환.
   - **우선순위**: `(최우선)`, `(긴급)`, `!!` → "최우선" / `(참고)`, `FYI` → "참고" / 그 외 → "일반"

3. **주차 계산**: 현재 날짜 기준 ISO 주차 (W27 등)

4. **항목번호**: 팀 내에서 01, 02, ... 자동 부여

---

## Step 2: HTML 생성

기존 분장 HTML 패턴(`20-operations/weekly-task-assignment-*.html`)의 CSS를 재사용한다.
디자인가이드(`00-system/04-design/project-rent-design-guide.md`)를 참조하여 다크테마 적용.

HTML 구조:
- 커버: 주차 + 기간 표시
- 팀별 섹션: 각 팀 이름 + 업무 테이블(번호/내용/담당/마감/우선순위/상태)
- 상태 기본값: "미착수"
- 우선순위별 시각 구분: 최우선=빨강, 일반=기본, 참고=회색

---

## Step 3: 구글시트 '주간분장' 탭 등록

### 헤더 확인/생성
먼저 탭이 있는지 확인:
```bash
gws sheets spreadsheets values get --params '{"spreadsheetId":"'"$DAILY_REPORT_SHEET_ID"'","range":"주간분장!A1:J1"}'
```

빈 결과이면 헤더 행 삽입:
```bash
gws sheets spreadsheets values append --params '{"spreadsheetId":"'"$DAILY_REPORT_SHEET_ID"'","range":"주간분장!A1","valueInputOption":"RAW","insertDataOption":"INSERT_ROWS"}' --json '{"values":[["주차","팀","항목번호","업무내용","담당자","마감","우선순위","상태","등록일","소스"]]}'
```

### 데이터 등록
파싱된 각 항목을 행으로 append:
```bash
gws sheets spreadsheets values append --params '{"spreadsheetId":"'"$DAILY_REPORT_SHEET_ID"'","range":"주간분장!A1","valueInputOption":"RAW","insertDataOption":"INSERT_ROWS"}' --json '{"values":[["W27","기획팀","01","CJ 시안 수정","양지혜","2026-07-02","최우선","미착수","2026-07-01","skill"]]}'
```

DAILY_REPORT_SHEET_ID는 .env에서 추출:
```bash
grep '^DAILY_REPORT_SHEET_ID=' .env | cut -d= -f2-
```

---

## Step 4: 아카이브 저장

```
20-operations/23-arisa/weekly/assignment-YYYY-WXX.html
```

---

## Step 5: 텔레그램 발송

### 대표에게 전체 요약 발송
.env에서 토큰 추출:
```bash
BOT_TOKEN="$(grep '^DAILY_REPORT_MANAGER_BOT_TOKEN=' .env | cut -d= -f2-)"
CHAT_ID="8123576679"
```

메시지 형식:
```
📋 주간 업무분장 — W27 (7/1~7/6)

[기획팀] 3건
  🔴 CJ 시안 수정 — @양지혜 (~수)
  ⬜ 봉은사 중간보고 — @정예은 (~금)
  ⬜ 구비 답십리 현장조사 — @조나연

[공간팀] 2건
  🔴 봉은사 도면 리뷰 — @김가은 (~화)
  ⬜ 서촌 공간 레이아웃 — @김예진

총 5건 · 최우선 2건
```

### 팀별 발송
명부의 `by_telegram_id`에서 해당 팀 소속 직원 chat_id를 찾아 각자에게 자기 팀 분장만 발송.
팀 리더(`team_leads`)에게는 우선 발송.

발송 형식 (팀원용):
```
📋 이번 주 업무분장 — W27

🔴 CJ 시안 수정 — @양지혜 (~수)
⬜ 봉은사 중간보고 — @정예은 (~금)
⬜ 구비 답십리 현장조사 — @조나연

총 3건 · 최우선 1건
```

curl로 발송:
```bash
curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"CHAT_ID","text":"메시지","parse_mode":"Markdown"}'
```

팀원 발송은 직원봇(DAILY_REPORT_BOT_TOKEN)으로:
```bash
STAFF_BOT="$(grep '^DAILY_REPORT_BOT_TOKEN=' .env | cut -d= -f2-)"
```

---

## 최종 출력

사용자에게 보고:
1. 파싱 결과 요약 (팀별 건수, 담당 미지정 항목 경고)
2. HTML 파일 경로
3. 시트 등록 건수
4. 텔레그램 발송 현황 (성공/실패)
