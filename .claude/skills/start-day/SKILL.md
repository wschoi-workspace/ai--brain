---
name: start-day
description: 아침 루틴 시작. "출근", "시작", "모닝", "start day", "아침 루틴" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Start Day - 아침 루틴

매일 아침 업무 시작 시 실행하는 6단계 루틴입니다.
모든 단계를 순차적으로 진행하고, 대화가 필요한 단계에서만 사용자 입력을 받습니다.

---

## Step 1: Daily Note 확인/생성 (자동)

날짜 변수 계산:
```bash
TODAY=$(date +%Y-%m-%d)
WEEKDAY=$(date +%A)  # locale에 따라 한글/영문
YESTERDAY=$(date -v-1d +%Y-%m-%d)
TOMORROW=$(date -v+1d +%Y-%m-%d)
WEEK=$(date +%Y-W%V)
MONTH_DIR=$(date +%Y-%m)
```

한글 요일 매핑: Monday=월요일, Tuesday=화요일, Wednesday=수요일, Thursday=목요일, Friday=금요일, Saturday=토요일, Sunday=일요일

1. Daily Note 경로: `40-personal/41-daily/${MONTH_DIR}/${TODAY}.md`
2. 월 폴더 없으면 `mkdir -p`로 생성
3. 파일이 없으면:
   - `00-system/01-templates/daily-note-template.md` 읽기
   - 변수 치환: `{{date}}` → TODAY, `{{weekday}}` → 한글요일, `{{yesterday}}` → YESTERDAY, `{{tomorrow}}` → TOMORROW, `{{week}}` → WEEK
   - 새 파일 생성
4. 파일이 있으면: 내용 읽기 (Step 4에서 활용)

---

## Step 2: 어제 리뷰 (자동)

어제의 활동을 자동 수집합니다:

### 2-1. 어제 Daily Note 확인
- 경로: `40-personal/41-daily/${YESTERDAY_MONTH_DIR}/${YESTERDAY}.md`
  - YESTERDAY_MONTH_DIR: 어제 날짜의 YYYY-MM (월이 다를 수 있으므로 별도 계산)
- 있으면: Top 3 Tasks 완료 여부, 완료한 일, Daily Reflection 섹션 추출
- 없으면: "어제 기록이 없습니다" → 스킵

### 2-2. Git Log
```bash
git log --since="${YESTERDAY} 00:00" --until="${TODAY} 00:00" --oneline --no-merges 2>/dev/null
```
- 결과 없으면: graceful skip

### 2-3. 밀린 Todo 확인
- `40-personal/46-todos/active-todos.md` 읽기
- 미완료 항목 (`- [ ]`) 수집

---

## Step 3: 미회신 메일 체크 (자동)

### 3-1. Gmail 스크립트 실행
```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/gmail_unreplied.py 2>/dev/null
```

**credentials.json 없는 경우** (error: credentials_missing 또는 dependencies_missing):
- "📧 Gmail 미설정 상태입니다. 설정하려면: `.claude/skills/start-day/scripts/SETUP-GMAIL.md` 참조"
- 메일 체크 스킵하고 Step 4로 진행

**정상 실행된 경우**:
1. JSON 결과 파싱
2. 각 메일을 AI가 판단:
   - **업무 관련 (회신 필요)**: 거래처, 클라이언트, 동료, 파트너로부터의 메일. 요청/질문/확인이 포함된 메일
   - **제외**: 뉴스레터, 자동 알림, 광고, 마케팅 메일, 소셜 미디어 알림, 배송 알림
3. 업무 메일이 있으면 텔레그램 전송:
```bash
tgcli send text --to "업무요청" --message "📬 미회신 업무 메일 (최근 3일)

1. [발신자] 제목 (N일 전)
2. [발신자] 제목 (N일 전)
..."
```
4. 전송 실패 시: 에러 로그 출력 후 계속 진행
5. 업무 메일 0건: 스킵 (텔레그램 미전송)

---

## Step 4: 대화형 체크인 (대화)

수집한 정보를 요약하여 사용자에게 보여줍니다:

```
☀️ Good morning! (YYYY-MM-DD 요일)

📊 어제 요약:
- [어제 Top 3 완료 현황 또는 "기록 없음"]
- [git log 요약 또는 "커밋 없음"]

📬 미회신 메일:
- [업무 메일 목록 또는 "미회신 업무 메일 없음" 또는 "Gmail 미설정"]

📋 밀린 Todo:
- [미완료 항목 또는 "없음"]

---
오늘 Top 3 Tasks는 무엇인가요?
(어제 미완료 항목 이어가기, 새 작업 추가 등)
```

**중복 실행 감지**: 오늘 Daily Note에 Top 3가 이미 작성되어 있으면 (`- [ ]` 빈칸이 아닌 실제 내용):
```
이미 오늘 Top 3가 작성되어 있습니다:
1. [기존 항목1]
2. [기존 항목2]
3. [기존 항목3]

수정하시겠어요? (Y/N)
```
- N이면 Step 6으로 스킵

---

## Step 5: Daily Note 업데이트 (자동)

사용자의 답변을 바탕으로 오늘 Daily Note를 업데이트합니다:

1. **Top 3 Tasks** 섹션에 사용자가 말한 우선순위 작성
2. **스케줄** 섹션에 언급된 일정 작성 (있을 경우)
3. `active-todos.md`에도 Today 항목 동기화

---

## Step 6: 마무리 (자동)

```
✅ 아침 루틴 완료!

🎯 오늘 포커스:
1. [Top 1]
2. [Top 2]
3. [Top 3]

📅 일정: [있으면 표시]
💪 좋은 하루 되세요!
```

---

## 참고

- Daily Note 템플릿: `00-system/01-templates/daily-note-template.md`
- Todo 파일: `40-personal/46-todos/active-todos.md`
- 텔레그램 전송: `tgcli send text --to "대화방" --message "내용"`
- Gmail 셋업: `${CLAUDE_SKILL_DIR}/scripts/SETUP-GMAIL.md`
