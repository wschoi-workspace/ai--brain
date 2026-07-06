---
moc: project
project_key: "29-salthouse-sns"
aliases: ["소금집", "소금집 델리", "소금집공방", "Salt House", "salthouse", "소금집 망원", "소금집 안국"]
---

# 29-salthouse-sns

> 소금집(Salt House) — 샤퀴테리·잠봉뵈르 델리 브랜드 SNS 감정분석 (경쟁: 세스크멘슬·메종조·샤퀴테리아)

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
