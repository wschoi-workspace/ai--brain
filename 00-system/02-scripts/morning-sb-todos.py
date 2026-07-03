#!/usr/bin/env python3
"""세컨드브레인(00_inbox)에서 최원석이 남긴 할일(next_action)을 모아 출력.

/morning 체크리스트에 "🧠 내가 남긴 할일(세컨드브레인)" 섹션으로 주입하기 위한 헬퍼.
status=classified + next_action 비어있지 않은 캡처만 수집, 최신순.

사용:
  python3 morning-sb-todos.py            # 기본: 체크리스트 텍스트
  python3 morning-sb-todos.py --json     # JSON (다른 도구 연동용)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

INBOX = Path.home() / "do-better-workspace/20-operations/24-second-brain/00_inbox"


def parse_frontmatter(text: str) -> dict:
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    fm: dict = {}
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def _clean(s: str) -> str:
    return (s or "").strip().strip('"')


def collect() -> list[dict]:
    todos = []
    for f in sorted(INBOX.glob("*.md")):
        try:
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        na = _clean(fm.get("next_action", ""))
        if not na:
            continue
        proj = _clean(fm.get("related_projects", "[]")).strip("[]").replace('"', "")
        todos.append({
            "next_action": na,
            "projects": proj or "미지정",
            "created": _clean(fm.get("created", ""))[:10],
            "summary": _clean(fm.get("summary", "")),
            "file": f.name,
        })
    todos.sort(key=lambda t: t["created"], reverse=True)
    return todos


def main():
    todos = collect()
    if "--json" in sys.argv:
        print(json.dumps(todos, ensure_ascii=False, indent=2))
        return
    if not todos:
        print("🧠 세컨드브레인 할일: (없음)")
        return
    print(f"🧠 *내가 남긴 할일 (세컨드브레인 · {len(todos)}건)*")
    for t in todos:
        print(f"□ {t['next_action']}  _({t['projects']} · {t['created']})_")


if __name__ == "__main__":
    main()
