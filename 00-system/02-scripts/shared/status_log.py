"""분장 상태 변경 이력 — append-only 감사 로그 (G5, 2026-07-18 노션 갭 분석).

주간분장 시트 H열(상태)을 바꾸는 모든 경로가 전이 1건 = JSONL 1줄을 남긴다.
decisions.jsonl과 동일 패턴: 화면보다 데이터 먼저 — 쌓아두면 조회 화면은 후속.

기록 지점(5곳): dashboard(/api/assign-status·분장 일괄삭제·프로젝트 삭제),
daily-brief(보고 기반 자동 완료), weekly(키워드 매칭 자동 갱신).

원칙: 로깅 실패가 운영 경로를 절대 깨지 않는다(전부 try/except, False 반환).
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

# shared → 02-scripts → 00-system → do-better-workspace
_WORKSPACE = Path(__file__).resolve().parents[3]
_LOG_DIR = _WORKSPACE / "20-operations" / "23-arisa" / "status-log"
_LOG_PATH = _LOG_DIR / "assign-status.jsonl"
_lock = threading.Lock()


def log_status_change(source: str, by: str, to_status: str, from_status: str = "",
                      row=None, date: str = "", project: str = "", pid: str = "",
                      task: str = "", assignee: str = "", note: str = "") -> bool:
    """상태 전이 1건 append. 실패해도 예외를 올리지 않는다(운영 경로 보호).

    source: dashboard | dashboard-bulk-delete | project-delete | daily-brief-auto | weekly-auto
    by: 변경 주체 (계정명 또는 'auto')
    note: 전이 근거 한 줄 (예: 자동 완료의 보고 근거 문장) — G7 이력 뷰 표시용
    """
    entry = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "source": (source or "").strip(),
        "by": (by or "").strip(),
        "row": row,
        "date": (date or "").strip(),
        "project": (project or "").strip(),
        "pid": (pid or "").strip(),
        "task": (task or "").strip(),
        "assignee": (assignee or "").strip(),
        "from": (from_status or "").strip(),
        "to": (to_status or "").strip(),
        "note": (note or "").strip()[:200],
    }
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _lock, _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def load_history(task: str = "", assignee: str = "", pid: str = "", limit: int = 50) -> list[dict]:
    """전이 이력 조회 (G7 — 태스크 이력 뷰). 필터는 AND, 최신순.

    task는 정확 일치(공백 정규화). 필터 전부 비면 최근 limit건.
    """
    if not _LOG_PATH.exists():
        return []
    tq = (task or "").strip()
    aq = (assignee or "").strip()
    pq = (pid or "").strip()
    out: list[dict] = []
    try:
        for line in _LOG_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if tq and (e.get("task") or "").strip() != tq:
                continue
            if aq and (e.get("assignee") or "").strip() != aq:
                continue
            if pq and (e.get("pid") or "").strip() != pq:
                continue
            out.append(e)
    except Exception:
        return []
    # 파일 append 순서 = 시간순 — 역순이 최신순 (같은 초 내 전이도 순서 보존)
    out.reverse()
    return out[:limit]
