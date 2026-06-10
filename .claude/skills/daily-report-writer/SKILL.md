# daily-report-writer: GPT 업무보고 JSON → 구글시트 저장

GPT 일일업무보고 봇(v2)이 출력한 JSON 데이터를 구글시트에 자동 저장한다.
"업무보고 저장", "보고서 저장", "JSON 저장", "시트에 넣어줘", "daily report save" 등을 언급하거나
GPT 봇 출력 JSON을 붙여넣으면 자동 실행.

## 구글시트 정보

- **Spreadsheet ID**: `1izuwjWPiJfbaJZ-Ib-U_NO0_Ln1_5yRr1SIRAum-hi4`
- **시트1 핵심업무**: 날짜|이름|팀|역할|카테고리|업무내용|상태|프로세스|사용도구|산출물|이슈
- **시트2 서브업무**: 날짜|이름|팀|카테고리|업무명|상태
- **시트3 메타**: 날짜|이름|팀|내일계획|개선포인트|블로커종합

## 입력 포맷

사용자가 GPT 봇 v2의 JSON 출력을 붙여넣는다:

```json
{
  "date": "2026-06-09",
  "name": "홍길동",
  "team": "마케팅팀",
  "role": "시니어 마케터",
  "core_tasks": [
    {
      "task": "캠페인 기획서 작성",
      "category": "기획",
      "status": "진행중",
      "process": "브리프 수령 → 경쟁사 분석 → 초안 작성",
      "tools": "Figma, Notion",
      "output": "기획서 초안 v1",
      "issues": "디자인팀 리소스 부족"
    }
  ],
  "sub_tasks": [
    {"task": "팀 주간회의", "category": "커뮤니케이션", "status": "완료"},
    {"task": "메일 회신 5건", "category": "커뮤니케이션", "status": "완료"}
  ],
  "blockers": "디자인팀 리소스 부족",
  "tomorrow": "기획서 v2 완성",
  "improvement": "메일 회신 템플릿화"
}
```

## 처리 흐름

### Step 1: JSON 파싱

사용자 메시지에서 JSON 블록을 추출한다.
필수 필드 검증: `date`, `name`, `team`, `role`, `core_tasks`, `sub_tasks`

### Step 2: 시트1 핵심업무 append

`core_tasks` 배열의 각 항목을 1행씩 추가:

```bash
gws sheets spreadsheets values append \
  --params '{"spreadsheetId": "1izuwjWPiJfbaJZ-Ib-U_NO0_Ln1_5yRr1SIRAum-hi4", "range": "핵심업무!A1", "valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}' \
  --json '{"values": [["날짜","이름","팀","역할","카테고리","업무내용","상태","프로세스","사용도구","산출물","이슈"]]}'
```

각 core_task를 행으로 변환:
```
[date, name, team, role, task.category, task.task, task.status, task.process, task.tools, task.output, task.issues]
```

### Step 3: 시트2 서브업무 append

`sub_tasks` 배열의 각 항목을 1행씩 추가:

```bash
gws sheets spreadsheets values append \
  --params '{"spreadsheetId": "1izuwjWPiJfbaJZ-Ib-U_NO0_Ln1_5yRr1SIRAum-hi4", "range": "서브업무!A1", "valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}' \
  --json '{"values": [["날짜","이름","팀","카테고리","업무명","상태"]]}'
```

각 sub_task를 행으로 변환:
```
[date, name, team, task.category, task.task, task.status]
```

### Step 4: 시트3 메타 append

메타 정보를 1행으로 추가:

```bash
gws sheets spreadsheets values append \
  --params '{"spreadsheetId": "1izuwjWPiJfbaJZ-Ib-U_NO0_Ln1_5yRr1SIRAum-hi4", "range": "메타!A1", "valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}' \
  --json '{"values": [["날짜","이름","팀","내일계획","개선포인트","블로커종합"]]}'
```

변환:
```
[date, name, team, tomorrow, improvement, blockers]
```

### Step 5: 결과 보고

저장 완료 후 사용자에게 알림:

```
✅ 업무보고 저장 완료
- 핵심업무: N건 추가
- 서브업무: M건 추가
- 메타: 1건 추가
- 시트: https://docs.google.com/spreadsheets/d/1izuwjWPiJfbaJZ-Ib-U_NO0_Ln1_5yRr1SIRAum-hi4
```

## 중복 방지

같은 날짜 + 같은 이름의 데이터가 이미 있는지 확인하지 않는다 (append 방식).
중복 제거는 분석 단계에서 처리.

## Step 6: 텔레그램 전송 (관리자에게 정리된 보고서 발송)

시트 저장 완료 후, 정리된 보고서를 텔레그램으로 관리자에게 자동 전송한다.

```bash
BOT_TOKEN="8708336649:AAH1iYv8PujNZqBcG4Fo7iXeHAhAZnpyH80"
CHAT_ID="8123576679"

# JSON에서 텔레그램용 요약 메시지 생성
MESSAGE="📋 일일 업무보고 — {name} ({team})
📅 {date}

■ 핵심 업무
{core_tasks를 순번으로 정리}
1. [{category}] {task} — {status}
   → {process}
   산출물: {output}

■ 서브 업무
{sub_tasks를 한 줄씩}
- [{category}] {task} ({status})

■ 이슈: {blockers}
■ 내일: {tomorrow}
■ 개선: {improvement}"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg chat_id "$CHAT_ID" --arg text "$MESSAGE" '{chat_id: $chat_id, text: $text}')"
```

### 전송 완료 메시지

```
✅ 업무보고 저장 + 전송 완료
- 구글시트: 핵심 N건 + 서브 M건 + 메타 1건
- 텔레그램: 관리자에게 요약 전송 완료
```

---

## 에러 처리

- JSON 파싱 실패 → "JSON 형식을 확인해주세요" + 샘플 포맷 안내
- GWS CLI 실패 → 에러 메시지 표시 + `gws auth status` 확인 안내
- 필수 필드 누락 → 누락된 필드 안내
