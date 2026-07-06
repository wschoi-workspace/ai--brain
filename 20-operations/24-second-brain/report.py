#!/usr/bin/env python3
"""Second Brain 수집기 — Claude 심층 레포트의 입력 생성기.

inbox에서 특정 프로젝트/주제의 생각을 registry 키·별칭으로 해석해 모은 뒤,
구조화 마크다운으로 출력한다. Claude Code가 이 출력을 읽어 team/lecture 레포트로 분석한다.

사용:
  python3 report.py <프로젝트|키워드>
  예) python3 report.py 봉은사   /   python3 report.py 리진
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bot import INBOX, read_thought, load_registry  # noqa: E402


def _norm(s: str) -> str:
    return (s or "").lower().replace(" ", "")


def resolve_keys(query: str) -> set[str]:
    """query가 registry의 key/별칭과 겹치는 프로젝트들의 key 집합."""
    q = _norm(query)
    keys = set()
    for p in load_registry().get("projects", []):
        for cand in [p.get("key", "")] + p.get("aliases", []):
            c = _norm(cand)
            if c and (q in c or c in q):
                keys.add(p["key"])
                break
    return keys


def collect(query: str):
    """키 매칭(related_projects) ∪ 본문/요약/태그 매칭."""
    keys = resolve_keys(query)
    q = _norm(query)
    hits = []
    for p in sorted(INBOX.glob("*.md")):
        m, b = read_thought(p)
        rp = m.get("related_projects", [])
        rp = rp if isinstance(rp, list) else []
        tags = m.get("tags", [])
        tags = tags if isinstance(tags, list) else []
        topics = m.get("related_topics", [])
        topics = topics if isinstance(topics, list) else []
        hay = _norm(" ".join(rp + tags + topics) + str(m.get("summary", "")) + b)
        if (keys & set(rp)) or (q in hay):
            hits.append((m, b))
    return keys, hits


def render(query: str, keys: set[str], hits) -> str:
    out = [
        f"# Second Brain 수집: {query}",
        f"매칭 프로젝트 키: {', '.join(sorted(keys)) or '(키 없음 — 본문 매칭)'}",
        f"수집 건수: {len(hits)}\n",
    ]
    if not hits:
        out.append("_관련 생각이 없습니다._")
        return "\n".join(out)
    for i, (m, b) in enumerate(hits, 1):
        out.append(f"## {i}. [{m.get('type','')}] {m.get('summary') or b[:40]}")
        out.append(f"- projects: {m.get('related_projects')} | tags: {m.get('tags')} | topics: {m.get('related_topics')}")
        out.append(f"- possible_use: {m.get('possible_use')} | next_action: {m.get('next_action')}")
        out.append(f"- created: {m.get('created')} | source: {m.get('source')}/{m.get('input_type')}")
        out.append(f"- 원문: {b}\n")
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 report.py <프로젝트|키워드>")
        sys.exit(1)
    q = " ".join(sys.argv[1:])
    keys, hits = collect(q)
    print(render(q, keys, hits))
