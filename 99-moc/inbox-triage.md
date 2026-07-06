---
moc: triage
---

# 🪺 inbox 고립 노트 점검

> 어떤 프로젝트·주제에도 연결되지 않은 캡처. 프로젝트/주제를 부여하거나 보관 처리할 후보.
> ⚠️ 분류는 봇이 frontmatter로 관리 — 여기서 직접 inbox 파일을 수정하지 말고, 필요 시 텔레그램으로 재분류 요청.

## 완전 고립 (related_projects·related_topics 모두 빈 값)
```dataview
TABLE created AS "캡처일", summary AS "요약"
FROM "20-operations/24-second-brain/00_inbox"
WHERE length(related_projects) = 0 AND length(related_topics) = 0
SORT created DESC
```

## 프로젝트 미연결 (주제만 있음)
```dataview
TABLE related_topics AS "주제", summary AS "요약"
FROM "20-operations/24-second-brain/00_inbox"
WHERE length(related_projects) = 0 AND length(related_topics) > 0
SORT created DESC
```

## 저신뢰 분류 (confidence < 0.6)
```dataview
TABLE confidence AS "신뢰도", related_projects AS "프로젝트", summary AS "요약"
FROM "20-operations/24-second-brain/00_inbox"
WHERE confidence AND confidence < 0.6
SORT confidence ASC
```
