#!/usr/bin/env python3
"""
ARISA 메모리 레이어 PoC — mem0 (OSS 로컬)

목적: 현재 "1회성 GPT 분류 후 죽은 데이터" 문제를 mem0의 시맨틱 메모리로
      살아있는 재부상(recall) 망으로 바꿀 수 있는지 실증.

안전 경계:
- 기존 봇(bot.py) / launchd 프로세스를 일절 건드리지 않는 독립 스크립트.
- 데이터는 로컬 디스크(.mem0-poc-data/)에만 영구 저장 — 외부 전송 없음.
- 외부 노출은 기존에 쓰던 OpenAI 호출(임베딩+fact추출)과 동일 수준.

사용:
  source ~/arisa-project-memory/.env   # OPENAI_API_KEY
  .venv-mem0-poc/bin/python mem0_poc.py ingest   # inbox 노트 → mem0 적재
  .venv-mem0-poc/bin/python mem0_poc.py search "봉은사 카페 어떻게"
  .venv-mem0-poc/bin/python mem0_poc.py demo      # 적재 + 재부상 시연 일괄
"""
import os
import re
import sys
import glob
import sqlite3
from pathlib import Path

# mem0 0.1.x는 add()를 내부 ThreadPoolExecutor로 처리하는데 history SQLite가
# check_same_thread=True여서 "created in another thread" 에러가 난다.
# PoC 한정: 모든 sqlite3 연결을 check_same_thread=False로 강제(같은 프로세스 내 안전).
_orig_connect = sqlite3.connect
def _patched_connect(*a, **k):
    k["check_same_thread"] = False   # qdrant 로컬이 명시적으로 True를 넘기므로 강제 덮어씀
    return _orig_connect(*a, **k)
sqlite3.connect = _patched_connect

BASE = Path(__file__).resolve().parent
INBOX = BASE / "00_inbox"
DB_PATH = BASE / ".mem0-poc-data"          # 영구 저장(휘발 방지)
USER_ID = "wonseok"

# --- mem0 설정: OSS 로컬, 디스크 영속 Qdrant + 비용 절감용 경량 모델 ---
def get_memory():
    from mem0 import Memory
    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {"path": str(DB_PATH), "on_disk": True},
        },
        "llm": {
            "provider": "openai",
            "config": {"model": "gpt-4o-mini", "temperature": 0.1},
        },
        "embedder": {
            "provider": "openai",
            "config": {"model": "text-embedding-3-small"},
        },
    }
    return Memory.from_config(config)


# --- frontmatter 간단 파서(외부 의존성 최소화) ---
def parse_note(path: Path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        fm, body = m.group(1), m.group(2).strip()
        for line in fm.splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, body


def ingest():
    mem = get_memory()
    files = sorted(glob.glob(str(INBOX / "*.md")))
    print(f"[ingest] inbox 노트 {len(files)}개 → mem0 적재 시작\n")
    for f in files:
        p = Path(f)
        meta, body = parse_note(p)
        summary = meta.get("summary", "")
        # mem0에 넣을 텍스트 = 본문(+요약). 원문은 inbox .md에 그대로 보존됨.
        content = body if not summary else f"{body}\n(요약: {summary})"
        md = {
            "project": meta.get("related_projects", ""),
            "type": meta.get("type", ""),
            "tags": meta.get("tags", ""),
            "date": meta.get("created", "")[:10],
            "source_file": p.name,
        }
        res = mem.add(content, user_id=USER_ID, metadata=md)
        added = res.get("results", res) if isinstance(res, dict) else res
        print(f"  ✓ {p.name[:40]:42} → {len(added) if added else 0} fact")
    print("\n[ingest] 완료. 저장 위치:", DB_PATH)


def search(query: str):
    mem = get_memory()
    res = mem.search(query, user_id=USER_ID, limit=5)
    hits = res.get("results", res) if isinstance(res, dict) else res
    print(f"\n🔍 재부상 검색: \"{query}\"\n" + "─" * 60)
    if not hits:
        print("  (관련 기억 없음)")
        return
    for i, h in enumerate(hits, 1):
        score = h.get("score", 0)
        memory = h.get("memory", "")
        src = (h.get("metadata") or {}).get("source_file", "")
        print(f"  {i}. [{score:.3f}] {memory}")
        if src:
            print(f"      ↳ 출처: {src}")


def demo():
    ingest()
    for q in [
        "봉은사 카페는 어떻게 만들지",
        "리진 디저트 방향성",
        "세스크맨스 계약 관련 할 일",
    ]:
        search(q)


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY 없음. `source ~/arisa-project-memory/.env` 먼저 실행하세요.")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if cmd == "ingest":
        ingest()
    elif cmd == "search":
        search(" ".join(sys.argv[2:]) or "봉은사")
    else:
        demo()
