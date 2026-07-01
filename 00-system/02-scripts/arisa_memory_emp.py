"""ARISA 직원 메모리 레이어 (daily-report-bot이 import) — 직원 사고의 거울(MVP2).

직원 보고를 직원별(user_id)로 mem0에 누적하고, 보고 시 그 직원의 과거 사고를
재부상한다. second-brain의 arisa_memory.py와 같은 원리지만 3가지가 다르다:
  1) 저장소 분리: `.mem0-data-employees` (second-brain의 .mem0-data와 별도 →
     두 봇이 qdrant 로컬을 동시에 잠그는 충돌 회피)
  2) user_id를 직원별로 받는다(개인 거울 — 본인 사고만 누적·재부상)
  3) inbox .md가 없으므로(원문은 구글시트 보존) 재부상 표시는 mem0 원문 그대로.
     add는 infer=False라 한국어 원문이 보존됨.

설계 원칙: 보조 레이어. 어떤 함수도 예외를 안 던진다(실패 시 add=None/recall=[]).
"""
from __future__ import annotations

import os

# ⚠️ mem0 import보다 먼저 설정해야 함:
# mem0 2.x는 `~/.mem0/migrations_qdrant`(전역)를 모든 인스턴스가 공유 → second-brain 봇이
# 먼저 잠그면 직원봇 거울 init이 매번 lock 충돌(BlockingIOError)로 실패한다(매일 무작동 원인).
# 직원봇 전용 mem0 홈으로 분리해 migrations_qdrant까지 독립시킨다.
os.environ["MEM0_DIR"] = os.path.expanduser("~/.mem0-employees")

import time
import atexit
import logging
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger("arisa-memory-emp")

# mem0 내부 ThreadPoolExecutor + qdrant 로컬 SQLite 스레드 가드 우회(같은 프로세스 내 안전)
_orig_connect = sqlite3.connect
def _patched_connect(*a, **k):
    k["check_same_thread"] = False
    return _orig_connect(*a, **k)
sqlite3.connect = _patched_connect

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / ".mem0-data-employees"     # 직원 전용 컬렉션(second-brain과 분리)
RECALL_MIN_SCORE = 0.35                      # second-brain과 통일(재부상 누락 방지)

_memory = None
_lock = threading.Lock()


def _get_memory():
    """qdrant 로컬 단일접근 충돌(BlockingIOError)에 대비해 짧게 재시도한다.
    실패해도 '영구 비활성'하지 않는다 — 일시적 lock이면 다음 보고 때 다시 시도(거울 복구).
    봇이 늘면(basket-ops 등) 같은 머신에서 mem0 접근이 순간 겹칠 수 있으므로 견고화."""
    global _memory
    if _memory is not None:
        return _memory
    if not os.getenv("OPENAI_API_KEY"):
        return None
    with _lock:
        if _memory is not None:
            return _memory
        from mem0 import Memory
        cfg = {
            "vector_store": {"provider": "qdrant",
                             "config": {"path": str(DB_PATH), "on_disk": True}},
            "llm": {"provider": "openai",
                    "config": {"model": "gpt-4o-mini", "temperature": 0.1}},
            "embedder": {"provider": "openai",
                         "config": {"model": "text-embedding-3-small"}},
        }
        last_err = None
        for attempt in range(3):
            try:
                _memory = Memory.from_config(cfg)
                logger.info("ARISA 직원 메모리 레이어 init 완료")
                return _memory
            except Exception as e:
                last_err = e
                time.sleep(0.8)   # lock 충돌이면 잠깐 후 재시도
        # 3회 실패 — 이번 보고만 거울 스킵, 영구 비활성은 안 함(다음 보고 때 재시도)
        logger.warning("직원 mem0 init 3회 실패(다음 보고 때 재시도): %s", last_err)
        return None


@atexit.register
def _shutdown():
    global _memory
    try:
        if _memory is not None:
            _memory.vector_store.client.close()
    except Exception:
        pass


def is_enabled() -> bool:
    return _get_memory() is not None


class _EnabledProxy:
    def __bool__(self):
        return is_enabled()
ENABLED = _EnabledProxy()


def add(text: str, user_id: str, metadata: dict | None = None) -> int | None:
    """직원 보고를 mem0에 적재(infer=False로 한국어 원문 보존). 원문은 구글시트에도 별도 보존."""
    mem = _get_memory()
    if mem is None or not text.strip():
        return None
    try:
        res = mem.add(text, user_id=str(user_id), metadata=metadata or {}, infer=False)
        added = res.get("results", res) if isinstance(res, dict) else res
        return len(added) if added else 0
    except Exception:
        logger.exception("직원 mem0 add 실패")
        return None


def recall(query: str, user_id: str, limit: int = 3,
           min_score: float = RECALL_MIN_SCORE) -> list[dict]:
    """그 직원(user_id)의 과거 사고만 재부상. [{memory, score, date}] (실패/무관 시 [])."""
    mem = _get_memory()
    if mem is None or not query.strip():
        return []
    try:
        res = mem.search(query, filters={"user_id": str(user_id)}, limit=max(limit * 2, 5))
        hits = res.get("results", res) if isinstance(res, dict) else res
    except Exception:
        logger.exception("직원 mem0 search 실패")
        return []
    out = []
    for h in (hits or []):
        if h.get("score", 0) < min_score:
            continue
        out.append({
            "memory": h.get("memory", ""),
            "score": round(h.get("score", 0), 3),
            "date": (h.get("metadata") or {}).get("date", ""),
        })
        if len(out) >= limit:
            break
    return out
