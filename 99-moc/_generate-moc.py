#!/usr/bin/env python3
"""
ARISA Obsidian MOC 생성기 (idempotent)

registry.json(24-second-brain)을 SSOT로 읽어 99-moc/ 하위에 프로젝트 허브 노트를 만든다.
이미 존재하는 MOC는 절대 덮어쓰지 않는다 → 사용자가 직접 쓴 '교차 메모' 블록 보존.
registry에 새 프로젝트가 추가되면 이 스크립트를 다시 돌려 누락분만 생성한다.

비파괴 원칙:
- arisa-project-memory의 org corpus 파일은 읽지도 쓰지도 않는다(임베드 링크만 텍스트로 박음).
- inbox frontmatter, registry.json은 읽기 전용.
- 출력은 전부 99-moc/ 안에만.
"""
import json
import os
import re

VAULT = "/Users/choi_ai/do-better-workspace"
REGISTRY = os.path.join(VAULT, "20-operations/24-second-brain/registry.json")
ORG_ROOT = os.path.join(VAULT, "20-operations/23-arisa/org-memory")  # symlink → arisa-project-memory/projects
INBOX_REL = "20-operations/24-second-brain/00_inbox"
MOC_DIR = os.path.join(VAULT, "99-moc")
PROJ_DIR = os.path.join(MOC_DIR, "projects")
TOPIC_DIR = os.path.join(MOC_DIR, "topics")

# registry key → org corpus 폴더명(arisa-project-memory). 폴더가 있는 프로젝트만 조직 사고 블록을 넣는다.
ORG_FOLDER = {
    "15-bongeunsa": "봉은사",
    "30-napkin-mag-sns": "napkin",
    "29-xescmenzl-sns": "세스크멘슬",
}
# registry key가 없지만 org corpus만 있는 폴더(메타/프로세스) → 단독 MOC
ORG_ONLY = {
    "브랜딩프로세스": {"aliases": ["브랜딩 프로세스", "브랜딩프로세스"], "desc": "브랜딩 프로세스 — 회의 corpus(조직 사고 전용)"},
}
# org corpus에서 임베드 후보(존재하는 것만)
ORG_EMBED_FILES = [
    ("02_decisions", "결정 타임라인", "embed"),
    ("03_todos", "미해결 Todo", "embed"),
    ("05_strategy_report", "전략 분석", "embed"),
    ("06_progress_log", "진행 로그", "embed"),
    ("PROJECT_MASTER", "마스터 현황판", "link"),
]


def org_block(folder):
    """org 폴더에 실제 존재하는 파일만 임베드/링크하는 블록 생성."""
    fdir = os.path.join(ORG_ROOT, folder)
    if not os.path.isdir(fdir):
        return ""
    lines = ["## 🏢 조직 사고 (회의 corpus)", "",
             "> arisa-project-memory 원본 임베드 — **읽기 전용**. 편집은 회의 후 `process_meeting.py`가 자동 수행.", ""]
    any_file = False
    for base, label, mode in ORG_EMBED_FILES:
        if os.path.isfile(os.path.join(fdir, base + ".md")):
            any_file = True
            ref = f"{folder}/{base}"  # 폴더명 포함 → 동명 파일 간 충돌 방지
            lines.append(f"### {label}")
            lines.append(f"![[{ref}]]" if mode == "embed" else f"[[{ref}]]")
            lines.append("")
    if not any_file:
        return ""
    return "\n".join(lines)


def personal_block(key):
    """이 프로젝트와 연결된 개인 inbox 생각을 Dataview로 수집 (D-3)."""
    return f"""## 🧠 개인 사고 (Second Brain inbox)

> `related_projects`에 이 프로젝트 key/alias가 박힌 캡처를 자동 수집.

```dataview
TABLE type AS "유형", summary AS "요약", created AS "캡처일"
FROM "{INBOX_REL}"
WHERE contains(related_projects, this.project_key)
   OR (this.aliases AND any(map(this.aliases, (a) => contains(related_projects, a))))
SORT created DESC
```
"""


CROSS_BLOCK = """## ✍️ 교차 메모 (수동)

<!-- 자유 작성 영역 — 이 블록은 생성기가 덮어쓰지 않습니다.
     조직 사고와 개인 사고를 잇는 본인의 판단·연결·다음 액션을 적으세요. -->

-
"""


def yaml_list(items):
    inner = ", ".join('"' + i.replace('"', '\\"') + '"' for i in items)
    return f"[{inner}]"


def write_if_absent(path, content):
    if os.path.exists(path):
        return "skip"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "new"


def make_project_moc(key, aliases, desc, org_folder=None):
    fm = ["---", "moc: project", f'project_key: "{key}"']
    if org_folder:
        fm.append(f'org_folder: "{org_folder}"')
    if aliases:
        fm.append(f"aliases: {yaml_list(aliases)}")
    fm += ["---", ""]
    parts = ["\n".join(fm), f"# {key}", "", f"> {desc}", ""]
    if org_folder:
        ob = org_block(org_folder)
        if ob:
            parts += [ob, ""]
    parts += [personal_block(key), "", CROSS_BLOCK]
    return "\n".join(parts)


def main():
    with open(REGISTRY, encoding="utf-8") as f:
        reg = json.load(f)

    created, skipped = [], []

    # 1) registry 프로젝트 MOC
    for p in reg["projects"]:
        key = p["key"]
        org = ORG_FOLDER.get(key)
        path = os.path.join(PROJ_DIR, key + ".md")
        content = make_project_moc(key, p.get("aliases", []), p.get("desc", ""), org)
        (created if write_if_absent(path, content) == "new" else skipped).append(key)

    # 2) org-only 단독 MOC (registry에 없는 corpus)
    for folder, meta in ORG_ONLY.items():
        path = os.path.join(PROJ_DIR, folder + ".md")
        fm = ["---", "moc: project", f'project_key: "{folder}"',
              f'org_folder: "{folder}"', f"aliases: {yaml_list(meta['aliases'])}", "---", ""]
        ob = org_block(folder)
        content = "\n".join(["\n".join(fm), f"# {folder}", "", f"> {meta['desc']}", "",
                             ob, "", CROSS_BLOCK])
        (created if write_if_absent(path, content) == "new" else skipped).append(folder + "(org-only)")

    # 3) ARISA-HOME 허브
    home = f"""---
moc: home
---

# 🧭 ARISA — 사고 그래프 홈

> 개인 사고(Second Brain inbox) ↔ 조직 사고(회의 corpus)를 잇는 통합 허브.
> 각 프로젝트 노드를 클릭하면 그 프로젝트의 조직 결정·개인 생각이 한 화면에 모입니다.

## 📂 프로젝트 허브
```dataview
TABLE org_folder AS "조직 corpus", join(aliases, ", ") AS "별칭"
FROM "99-moc/projects"
WHERE moc = "project"
SORT file.name ASC
```

## 📊 프로젝트별 개인 생각 활동량
```dataview
TABLE length(rows) AS "연결된 생각 수"
FROM "{INBOX_REL}"
FLATTEN related_projects AS proj
GROUP BY proj
SORT length(rows) DESC
```

## ⚡ 전역 다음 액션 (next_action 보유 캡처)
```dataview
TABLE related_projects AS "프로젝트", next_action AS "다음 행동", created AS "캡처일"
FROM "{INBOX_REL}"
WHERE next_action AND next_action != ""
SORT created DESC
LIMIT 40
```

## 🪺 고립 노트 점검
- [[inbox-triage]] — 어떤 프로젝트·주제에도 안 걸린 캡처 정리
"""
    (created if write_if_absent(os.path.join(MOC_DIR, "ARISA-HOME.md"), home) == "new" else skipped).append("ARISA-HOME")

    # 4) inbox triage (고립 노트 대시보드, D-5)
    triage = f"""---
moc: triage
---

# 🪺 inbox 고립 노트 점검

> 어떤 프로젝트·주제에도 연결되지 않은 캡처. 프로젝트/주제를 부여하거나 보관 처리할 후보.
> ⚠️ 분류는 봇이 frontmatter로 관리 — 여기서 직접 inbox 파일을 수정하지 말고, 필요 시 텔레그램으로 재분류 요청.

## 완전 고립 (related_projects·related_topics 모두 빈 값)
```dataview
TABLE created AS "캡처일", summary AS "요약"
FROM "{INBOX_REL}"
WHERE length(related_projects) = 0 AND length(related_topics) = 0
SORT created DESC
```

## 프로젝트 미연결 (주제만 있음)
```dataview
TABLE related_topics AS "주제", summary AS "요약"
FROM "{INBOX_REL}"
WHERE length(related_projects) = 0 AND length(related_topics) > 0
SORT created DESC
```

## 저신뢰 분류 (confidence < 0.6)
```dataview
TABLE confidence AS "신뢰도", related_projects AS "프로젝트", summary AS "요약"
FROM "{INBOX_REL}"
WHERE confidence AND confidence < 0.6
SORT confidence ASC
```
"""
    (created if write_if_absent(os.path.join(MOC_DIR, "inbox-triage.md"), triage) == "new" else skipped).append("inbox-triage")

    # 5) 주제 인덱스 허브 (개별 주제 노트는 사용자가 추가; 여기선 동적 목록만)
    topics_home = f"""---
moc: topics-home
---

# 🏷️ 주제(topic) 인덱스

> inbox 캡처의 `related_topics`로 본 주제 지형도. 특정 주제를 깊게 보려면
> `99-moc/topics/<주제명>.md`를 만들고 아래 쿼리 템플릿을 넣으세요.

## 주제별 캡처 분포
```dataview
TABLE length(rows) AS "캡처 수"
FROM "{INBOX_REL}"
FLATTEN related_topics AS topic
GROUP BY topic
SORT length(rows) DESC
```

---
### 주제 노트 템플릿 (복사용)
파일명을 주제명과 동일하게 만들면 아래 쿼리가 자동 작동합니다.
````
```dataview
LIST summary
FROM "{INBOX_REL}"
WHERE contains(related_topics, this.file.name)
SORT created DESC
```
````
"""
    (created if write_if_absent(os.path.join(TOPIC_DIR, "_topics-home.md"), topics_home) == "new" else skipped).append("topics/_topics-home")

    print(f"✅ 생성 {len(created)}개:")
    for c in created:
        print(f"   + {c}")
    if skipped:
        print(f"⏭️  스킵(이미 존재) {len(skipped)}개: {', '.join(skipped)}")


if __name__ == "__main__":
    main()
