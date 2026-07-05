"""Engine D — Decision Log 축적 (봇 공용).

ARISA 2.0 DEFINITION의 Engine D(Decision Engine)를 데이터 축적으로 제품화한 것.
직원 보고에 묻혀 있던 `decision_needed`(텍스트 1개)를 구조화 JSON으로 뽑아
`20-operations/23-arisa/decisions/decisions.jsonl`에 append-only로 쌓는다.

원칙(DEFINITION):
  - "화면보다 데이터 먼저" — 이 로그가 arisa2 Decision Window의 읽기 소스가 된다.
  - decision_needed가 비면 skip(과잉 방지). 없는 결정을 지어내지 않는다.
  - 각 봇이 report dict를 그대로 넘기면 된다(도메인 로직은 봇에 남긴다).

스키마(1줄=1결정): date/project/decision_type/decision_needed/urgency/
  owner/source_employee/related_output/status/logged_at
맥미니 복구 후 arisa2 `data/decisions/`로 symlink/rsync 정합 예정.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

# shared → 02-scripts → 00-system → do-better-workspace
_WORKSPACE = Path(__file__).resolve().parents[3]
_DECISIONS_DIR = _WORKSPACE / "20-operations" / "23-arisa" / "decisions"
_LOG_PATH = _DECISIONS_DIR / "decisions.jsonl"

DEFAULT_OWNER = "최원석"
_VALID_URGENCY = {"high", "medium", "low"}


def save_decision_log(report: dict, owner: str = DEFAULT_OWNER) -> bool:
    """report에서 Decision을 구조화해 JSONL 1줄 append. 결정 없으면 False.

    report 기대 필드:
      - decision_needed (str)         : Engine C가 채운 결정 텍스트 (필수 트리거)
      - decision (dict, 선택)          : {project, decision_type, urgency, related_output}
      - date / name (source_employee)
    """
    needed = (report.get("decision_needed") or "").strip()
    if not needed:
        return False  # 결정 없음 — 축적 skip

    meta = report.get("decision") or {}
    urgency = (meta.get("urgency") or "medium").strip().lower()
    if urgency not in _VALID_URGENCY:
        urgency = "medium"

    entry = {
        "date": report.get("date", ""),
        "project": (meta.get("project") or "").strip(),
        "decision_type": (meta.get("decision_type") or "").strip(),
        "decision_needed": needed,
        "urgency": urgency,
        "owner": owner,
        "source_employee": report.get("name", ""),
        "related_output": (meta.get("related_output") or "").strip(),
        "status": "open",
        "logged_at": datetime.now().isoformat(timespec="seconds"),
    }
    try:
        _DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def close_decision(logged_at: str, resolution: str = "", closed_by: str = DEFAULT_OWNER) -> bool:
    """결정을 해결(close)한다. logged_at로 대상 식별 → status를 resolved로 변경.

    ARISA 2.0 Decision Window에서 유일한 close 화면으로 호출됨.
    JSONL 전체를 읽어 해당 항목을 수정 후 재기록(append-only 깨짐 — 항목 수가 적어 허용).
    """
    if not _LOG_PATH.exists():
        return False
    lines = _LOG_PATH.read_text(encoding="utf-8").splitlines()
    found = False
    updated: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            updated.append(line)
            continue
        if e.get("logged_at") == logged_at and e.get("status", "open") == "open":
            e["status"] = "resolved"
            e["resolution"] = resolution
            e["closed_by"] = closed_by
            e["closed_at"] = datetime.now().isoformat(timespec="seconds")
            found = True
        updated.append(json.dumps(e, ensure_ascii=False))
    if not found:
        return False
    try:
        with _lock_decision:
            _LOG_PATH.write_text("\n".join(updated) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False


_lock_decision = __import__("threading").Lock()


def load_open_decisions(max_age_days: int = 14, today: str | None = None) -> list[dict]:
    """미해결(status=open) 결정을 최신순으로 반환. carry-over(이월)용.

    - max_age_days: 경과일이 이보다 크면 stale로 간주해 제외(무한 증식 방지).
      데이터는 지우지 않고 노출만 중단 — 실제 close/해결은 arisa2 Decision Window에서.
    - 각 항목에 age_days(경과일)를 부가한다.
    - today: 기준일 "YYYY-MM-DD"(미지정 시 오늘). age = today - date.

    ※ 지금은 close 화면이 없어 age 컷오프가 유일한 만료 기준이다.
      arisa2 Part 2에서 수동 해결(status→resolved)이 붙으면 그때 자연히 사라진다.
    """
    if not _LOG_PATH.exists():
        return []
    base = datetime.strptime(today, "%Y-%m-%d").date() if today else datetime.now().date()
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
            if (e.get("status") or "open") != "open":
                continue
            d = (e.get("date") or "").strip()
            try:
                age = (base - datetime.strptime(d, "%Y-%m-%d").date()).days
            except Exception:
                age = 0  # 날짜 파싱 실패 시 최신 취급(제외하지 않음)
            if age > max_age_days or age < 0:
                continue
            e["age_days"] = age
            out.append(e)
    except Exception:
        return []
    # 오래된 미결일수록 위로(경과일 내림차순) — "며칠째 안 정한 것"을 먼저 보이게
    out.sort(key=lambda x: x.get("age_days", 0), reverse=True)
    return out
