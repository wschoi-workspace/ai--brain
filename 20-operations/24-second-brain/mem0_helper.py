#!/usr/bin/env python3
"""mem0 헬퍼 CLI — Second Brain 봇이 subprocess로 호출하는 격리 실행기.

봇(arisa venv, openai 2.x)과 mem0(openai 1.x)의 의존성 충돌을 피하려고
mem0 작업은 전용 venv(.venv-mem0-poc)에서 이 스크립트로 분리 실행한다.

I/O 계약 (봇과의 인터페이스):
  add    : stdin으로 JSON {text, metadata, user_id} → stdout JSON {ok, count}
  recall : argv[2]=query, --user ID, --limit N → stdout JSON {ok, results:[{memory,score,source_file}]}
모든 출력은 마지막 줄에 JSON 한 줄(봇이 파싱). 에러도 {ok:false, error} 로.
"""
import os
import sys
import json
import sqlite3
from pathlib import Path

# mem0 0.1.x ThreadPoolExecutor + qdrant 로컬 SQLite 스레드 가드 우회(같은 프로세스 내 안전)
_orig_connect = sqlite3.connect
def _patched_connect(*a, **k):
    k["check_same_thread"] = False
    return _orig_connect(*a, **k)
sqlite3.connect = _patched_connect

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / ".mem0-poc-data"          # PoC와 동일 저장소(연속성)


def get_memory():
    from mem0 import Memory
    config = {
        "vector_store": {"provider": "qdrant",
                         "config": {"path": str(DB_PATH), "on_disk": True}},
        "llm": {"provider": "openai",
                "config": {"model": "gpt-4o-mini", "temperature": 0.1}},
        "embedder": {"provider": "openai",
                     "config": {"model": "text-embedding-3-small"}},
    }
    return Memory.from_config(config)


def cmd_add():
    payload = json.loads(sys.stdin.read() or "{}")
    text = (payload.get("text") or "").strip()
    if not text:
        print(json.dumps({"ok": False, "error": "empty text"}))
        return
    mem = get_memory()
    res = mem.add(text,
                  user_id=payload.get("user_id", "wonseok"),
                  metadata=payload.get("metadata") or {})
    added = res.get("results", res) if isinstance(res, dict) else res
    print(json.dumps({"ok": True, "count": len(added) if added else 0}))


def cmd_recall(query, user_id, limit):
    mem = get_memory()
    res = mem.search(query, user_id=user_id, limit=limit)
    hits = res.get("results", res) if isinstance(res, dict) else res
    out = [{"memory": h.get("memory", ""),
            "score": round(h.get("score", 0), 3),
            "source_file": (h.get("metadata") or {}).get("source_file", "")}
           for h in (hits or [])]
    print(json.dumps({"ok": True, "results": out}, ensure_ascii=False))


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print(json.dumps({"ok": False, "error": "no OPENAI_API_KEY"}))
        return
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "add":
            cmd_add()
        elif cmd == "recall":
            query = sys.argv[2] if len(sys.argv) > 2 else ""
            user = "wonseok"
            limit = 5
            if "--user" in sys.argv:
                user = sys.argv[sys.argv.index("--user") + 1]
            if "--limit" in sys.argv:
                limit = int(sys.argv[sys.argv.index("--limit") + 1])
            cmd_recall(query, user, limit)
        else:
            print(json.dumps({"ok": False, "error": f"unknown cmd: {cmd}"}))
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"}))


if __name__ == "__main__":
    main()
