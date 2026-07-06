---
moc: project
project_key: "R_define"
aliases: ["R 정의", "R define", "프로젝트렌트 정의", "아이덴티티"]
---

# R_define

> 프로젝트렌트 & 최원석 정의 프로젝트

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
