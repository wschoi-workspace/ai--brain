---
moc: project
project_key: "30-napkin-mag-sns"
org_folder: "napkin"
aliases: ["넵킨", "napkin", "냅킨 매거진"]
---

# 30-napkin-mag-sns

> 넵킨 매거진 브랜드 강화

## 🏢 조직 사고 (회의 corpus)

> arisa-project-memory 원본 임베드 — **읽기 전용**. 편집은 회의 후 `process_meeting.py`가 자동 수행.

### 결정 타임라인
![[napkin/02_decisions]]

### 미해결 Todo
![[napkin/03_todos]]

### 전략 분석
![[napkin/05_strategy_report]]

### 진행 로그
![[napkin/06_progress_log]]


## 🧠 개인 사고 (Second Brain inbox)

> `related_projects`에 이 프로젝트 key/alias가 박힌 캡처를 자동 수집.

```dataview
TABLE type AS "유형", summary AS "요약", created AS "캡처일"
FROM "20-operations/24-second-brain/00_inbox"
WHERE contains(related_projects, this.project_key)
   OR (this.aliases AND any(map(this.aliases, (a) => contains(related_projects, a))))
SORT created DESC
```


## ✍️ 교차 메모 (수동)

<!-- 자유 작성 영역 — 이 블록은 생성기가 덮어쓰지 않습니다.
     조직 사고와 개인 사고를 잇는 본인의 판단·연결·다음 액션을 적으세요. -->

-
