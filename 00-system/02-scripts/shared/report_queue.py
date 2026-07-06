"""시트 저장 실패 보고의 로컬 유실 방지 큐.

gws 인증 장애(2026-07-03 invalid_rapt로 5명 보고 유실) 재발 시에도 보고가 사라지지 않도록,
append 실패 행을 JSONL 큐에 보관하고 백필 배치(retry-failed-reports.py)가 비운다.
daily-report-bot / basket-ops-bot / 백필 배치가 공유. stdlib만 사용.

엔트리 1행 = 실패한 append 1건:
  {id, report_key: "날짜|이름", queued_at, source: "daily-report"|"basket",
   sheet_id, tab, vio, row, dedup_cols, attempts, last_error}
dedup_cols = 백필 시 중복 검사할 컬럼 인덱스(이미 저장된 행 재-append 방지).
"""
from __future__ import annotations

import fcntl
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

QUEUE_DIR = Path(__file__).resolve().parent.parent / "failed-reports"
QUEUE = QUEUE_DIR / "queue.jsonl"
ARCHIVE = QUEUE_DIR / "archive.jsonl"


def make_entry(source: str, sheet_id: str, tab: str, row: list,
               report_key: str, dedup_cols: list[int],
               vio: str = "RAW", last_error: str = "") -> dict:
    """큐 엔트리 생성 (타임스탬프·id 자동)."""
    return {
        "id": uuid.uuid4().hex[:8],
        "report_key": report_key,
        "queued_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "sheet_id": sheet_id,
        "tab": tab,
        "vio": vio,
        "row": row,
        "dedup_cols": dedup_cols,
        "attempts": 0,
        "last_error": last_error,
    }


def enqueue(entries: list[dict]) -> bool:
    """엔트리들을 큐에 append(flock+fsync). 실패 시 마지막 안전망으로 내용을 로그에 덤프."""
    if not entries:
        return True
    try:
        QUEUE_DIR.mkdir(exist_ok=True)
        with open(QUEUE, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
            fcntl.flock(f, fcntl.LOCK_UN)
        logger.info(f"report_queue: {len(entries)}건 큐 보관 ({entries[0].get('report_key','')})")
        return True
    except Exception as ex:  # noqa: BLE001
        # 큐 기록마저 실패 — 최후 수단으로 로그에 원문 덤프(수동 복구용)
        logger.error(f"report_queue enqueue 실패: {ex} — 원문 덤프:")
        for e in entries:
            logger.error(f"LOST-ROW {json.dumps(e, ensure_ascii=False)}")
        return False


def load_pending() -> list[dict]:
    """큐의 모든 대기 엔트리. 깨진 행은 건너뛰고 경고."""
    if not QUEUE.exists():
        return []
    out = []
    for i, line in enumerate(QUEUE.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:  # noqa: BLE001
            logger.warning(f"report_queue: {i}행 파싱 실패 — 건너뜀: {line[:120]}")
    return out


def rewrite(remaining: list[dict], done: list[dict]) -> None:
    """큐를 remaining으로 원자 교체, done은 archive.jsonl로 이동."""
    QUEUE_DIR.mkdir(exist_ok=True)
    if done:
        with open(ARCHIVE, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            for e in done:
                e = dict(e, archived_at=datetime.now().isoformat(timespec="seconds"))
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
            fcntl.flock(f, fcntl.LOCK_UN)
    tmp = QUEUE.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for e in remaining:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, QUEUE)
