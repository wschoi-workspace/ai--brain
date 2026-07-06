---
moc: topics-home
---

# 🏷️ 주제(topic) 인덱스

> inbox 캡처의 `related_topics`로 본 주제 지형도. 특정 주제를 깊게 보려면
> `99-moc/topics/<주제명>.md`를 만들고 아래 쿼리 템플릿을 넣으세요.

## 🗂️ 주제 노트
- [[프로젝트 관리]]
- [[매장 운영]]
- [[브랜딩]]
- [[업무 자동화]]
- [[문화 융합]]

## 주제별 캡처 분포
```dataview
TABLE length(rows) AS "캡처 수"
FROM "20-operations/24-second-brain/00_inbox"
FLATTEN related_topics AS topic
GROUP BY topic
SORT length(rows) DESC
```

---
### 주제 노트 템플릿 (복사용)
frontmatter `topic_terms`에 동의어 주제들을 나열하면, 그중 하나라도 걸리는 캡처를 모읍니다.
(표기가 흔들리는 주제 어휘를 alias처럼 흡수 — 단일 `file.name` 매칭보다 견고)
````
---
moc: topic
topic_terms: ["주제명", "동의어1", "동의어2"]
---
```dataview
TABLE related_projects AS "프로젝트", summary AS "요약", created AS "캡처일"
FROM "20-operations/24-second-brain/00_inbox"
WHERE any(map(this.topic_terms, (t) => contains(related_topics, t)))
SORT created DESC
```
````
