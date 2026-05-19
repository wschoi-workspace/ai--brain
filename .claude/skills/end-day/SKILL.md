---
name: end-day
description: 하루 마무리 루틴. "퇴근", "마무리", "end day", "하루 정리", "저녁 리뷰" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# End Day - 하루 마무리 루틴

매일 업무 종료 시 실행하는 5단계 루틴입니다.
오늘 활동을 정리하고, 내일을 준비합니다.

---

## Step 1: 오늘 활동 수집 (자동)

날짜 변수 계산:
```bash
TODAY=$(date +%Y-%m-%d)
TOMORROW=$(date -v+1d +%Y-%m-%d)
MONTH_DIR=$(date +%Y-%m)
```

### 1-1. 오늘 Daily Note 읽기
- 경로: `40-personal/41-daily/${MONTH_DIR}/${TODAY}.md`
- 없으면: "오늘 Daily Note가 없습니다. 생성할까요?" → 생성 후 진행
- Top 3 Tasks 완료 여부 확인
- 완료한 일 섹션 확인

### 1-2. Git Log (오늘)
```bash
git log --since="${TODAY} 00:00" --oneline --no-merges 2>/dev/null
```
- 결과 없으면: graceful skip

### 1-3. Todo 현황
- `40-personal/46-todos/active-todos.md` 읽기
- Today 섹션의 완료/미완료 항목 분리

---

## Step 2: 성과 정리 + 대화 (대화)

수집한 정보를 보여주고 사용자 피드백을 받습니다:

```
🌙 하루 마무리 (YYYY-MM-DD 요일)

📊 오늘 현황:
🎯 Top 3 Tasks:
  1. [x] 완료된 항목
  2. [ ] 미완료 항목
  3. [x] 완료된 항목

💻 Git 활동:
  - [커밋 요약 또는 "커밋 없음"]

📋 Todo:
  - 완료: N개
  - 미완료: M개

---
1. 오늘 잘한 점이 있다면?
2. 내일로 넘길 일이 있나요?
3. 추가로 기록할 것이 있나요?
```

사용자 답변을 수집합니다. 짧게 답해도 OK, 스킵도 가능.

---

## Step 3: Daily Note 업데이트 (자동)

오늘 Daily Note를 업데이트합니다:

### 3-1. 완료한 일 섹션 (`✅ 완료한 일`)
- Top 3에서 완료된 항목
- Git 커밋 요약
- 사용자가 추가로 언급한 성과

```markdown
## ✅ 완료한 일

### 주요 성과
- Top 1 완료
- Top 3 완료
- [사용자 언급 성과]

### 작은 승리
- [git 활동 요약]
```

### 3-2. Daily Reflection 섹션 (`🤔 Daily Reflection`)
- 사용자 답변 기반으로 작성

```markdown
## 🤔 Daily Reflection

### 잘한 점
- [사용자 답변]

### 개선할 점
- [미완료 항목 기반 또는 사용자 답변]

### 내일 우선순위
- [내일로 넘긴 항목]
- [사용자 언급 항목]
```

### 3-3. Top 3 체크박스 업데이트
- 완료된 항목: `- [ ]` → `- [x]`로 변경 (사용자 확인 기반)

---

## Step 4: Todo 정리 (자동)

`40-personal/46-todos/active-todos.md`를 정리합니다:

### 4-1. 완료 항목 처리
- Today 섹션의 `- [x]` 항목 → Completed 섹션으로 이동 (날짜 태그 추가)
```markdown
- [x] 완료된 작업 (2026-03-29)
```

### 4-2. 미완료 항목 유지
- Today 섹션의 `- [ ]` 항목은 그대로 유지 (내일 `/start-day`에서 확인)

### 4-3. 내일 항목 추가
- 사용자가 "내일 넘길 일"로 언급한 항목을 Today에 추가 (이미 있으면 스킵)

---

## Step 5: 마무리 (자동)

```
✅ 하루 마무리 완료!

📊 오늘 결산:
  - 완료: N개
  - 내일 이어갈 일: M개

🎯 내일 우선순위:
  1. [항목1]
  2. [항목2]
  3. [항목3]

수고하셨습니다! 🌙
```

---

## 참고

- Daily Note 경로: `40-personal/41-daily/YYYY-MM/YYYY-MM-DD.md`
- Todo 파일: `40-personal/46-todos/active-todos.md`
- Daily Note 템플릿: `00-system/01-templates/daily-note-template.md`
