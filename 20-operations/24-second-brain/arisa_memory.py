"""ARISA 메모리 레이어 (bot.py가 import) — B단계: mem0 2.x 직접 통합.

A단계의 subprocess 격리를 제거. second-brain 전용 venv(.venv311, openai 2.x +
mem0 2.x 호환)에서 mem0를 직접 import해 상주 인스턴스로 재사용한다(매 호출 init 없음).

설계 원칙:
1) mem0는 '의미 인덱스'로만 쓴다. mem0 2.x는 fact를 영어로 정규화해 저장하지만,
   사용자에게 보여주는 재부상 텍스트는 항상 inbox 원문(.md의 한국어 summary)이다.
   → 원문 보존(fidelity) + 한국어 UX. (검색 자체는 다국어 임베딩이라 한국어 쿼리로 잘 매칭)
2) 보조 레이어다. 어떤 함수도 예외를 던지지 않는다. 실패 시 add=None / recall=[].
"""
from __future__ import annotations

import re
import os
import atexit
import logging
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger("arisa-memory")

# mem0 내부 ThreadPoolExecutor + qdrant 로컬 SQLite 스레드 가드 우회(같은 프로세스 내 안전)
_orig_connect = sqlite3.connect
def _patched_connect(*a, **k):
    k["check_same_thread"] = False
    return _orig_connect(*a, **k)
sqlite3.connect = _patched_connect

BASE = Path(__file__).resolve().parent
INBOX = BASE / "00_inbox"
DB_PATH = BASE / ".mem0-data"          # mem0 2.x 전용 컬렉션
USER_ID = "wonseok"
RECALL_MIN_SCORE = 0.35

_memory = None
_lock = threading.Lock()
_init_failed = False


def _get_memory():
    """mem0 Memory 상주 인스턴스(최초 1회 init 후 재사용). 실패하면 None(봇 보호)."""
    global _memory, _init_failed
    if _memory is not None:
        return _memory
    if _init_failed or not os.getenv("OPENAI_API_KEY"):
        return None
    with _lock:
        if _memory is not None:
            return _memory
        try:
            from mem0 import Memory
            cfg = {
                "vector_store": {"provider": "qdrant",
                                 "config": {"path": str(DB_PATH), "on_disk": True}},
                "llm": {"provider": "openai",
                        "config": {"model": "gpt-4o-mini", "temperature": 0.1}},
                "embedder": {"provider": "openai",
                             "config": {"model": "text-embedding-3-small"}},
            }
            _memory = Memory.from_config(cfg)
            logger.info("mem0 2.x 메모리 레이어 init 완료")
            return _memory
        except Exception:
            logger.exception("mem0 init 실패 — 메모리 레이어 비활성")
            _init_failed = True
            return None


@atexit.register
def _shutdown():
    """인터프리터 종료 전에 qdrant 로컬 클라이언트를 닫아, __del__ 단계의
    'sys.meta_path is None' traceback(무해하지만 로그 노이즈)을 방지."""
    global _memory
    try:
        if _memory is not None:
            _memory.vector_store.client.close()
    except Exception:
        pass


def is_enabled() -> bool:
    return _get_memory() is not None


# 호환: bot.py가 _mem.ENABLED 를 참조 → 속성 접근 시점에 평가
class _EnabledProxy:
    def __bool__(self):
        return is_enabled()
ENABLED = _EnabledProxy()


# ─── inbox 원문 summary 추출(재부상 표시용 한국어 텍스트) ───
def _summary_of(source_file: str) -> str | None:
    if not source_file:
        return None
    p = INBOX / source_file
    if not p.exists():
        return None
    try:
        txt = p.read_text(encoding="utf-8")
        m = re.search(r'^summary:\s*"?(.+?)"?\s*$', txt, re.M)
        if m:
            return m.group(1).strip()
        # frontmatter 본문 첫 줄 fallback
        body = txt.split("---", 2)[-1].strip()
        return body.splitlines()[0][:80] if body else None
    except Exception:
        return None


def add(text: str, metadata: dict | None = None, user_id: str = USER_ID) -> int | None:
    """생각을 mem0에 적재. 추출 fact 수 반환(실패 None). 원문은 호출측이 .md로 보존."""
    mem = _get_memory()
    if mem is None:
        return None
    try:
        # infer=False: mem0 2.x의 LLM fact추출(영어 정규화)을 끄고 한국어 원문 그대로 저장.
        # → 한국어 검색 정확 + 원문보존(fidelity) + LLM 비용 0. 분류·summary는 이미 inbox에 있음.
        res = mem.add(text, user_id=user_id, metadata=metadata or {}, infer=False)
        added = res.get("results", res) if isinstance(res, dict) else res
        return len(added) if added else 0
    except Exception:
        logger.exception("mem0 add 실패")
        return None


def recall(query: str, user_id: str = USER_ID, limit: int = 5,
           exclude_source: str | None = None,
           min_score: float = RECALL_MIN_SCORE) -> list[dict]:
    """관련 과거 생각 재부상. 노트(source_file) 단위로 dedup하고, 표시 텍스트는
    inbox 원문 summary(한국어). 반환 [{memory, score, source_file}](실패/무관 시 [])."""
    mem = _get_memory()
    if mem is None:
        return []
    try:
        res = mem.search(query, filters={"user_id": user_id}, limit=max(limit * 2, 6))
        hits = res.get("results", res) if isinstance(res, dict) else res
    except Exception:
        logger.exception("mem0 search 실패")
        return []
    out, seen = [], set()
    for h in (hits or []):
        if h.get("score", 0) < min_score:
            continue
        sf = (h.get("metadata") or {}).get("source_file", "")
        if exclude_source and sf == exclude_source:
            continue
        if sf in seen:
            continue
        seen.add(sf)
        display = _summary_of(sf) or h.get("memory", "")   # 한국어 원문 우선, 없으면 fact
        out.append({"memory": display, "score": round(h.get("score", 0), 3), "source_file": sf})
        if len(out) >= limit:
            break
    return out
