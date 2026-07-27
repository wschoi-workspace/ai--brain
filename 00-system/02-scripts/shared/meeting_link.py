"""회의 액션 ↔ 분장 연결 — 선후관계·차단 요인 조회 (WS1, 2026-07-27).

배경: 회의 시뮬레이터가 2개로 갈라져 있다.
  엔진 A (dashboard-server 내장) — block_5_todos.ours. 분장 시트로 실제 등록되는 경로.
  엔진 B (meeting-simulator-server, R4 Meeting OS 8781) — actions[].dependencies,
         supportRequests[].blockingLevel/blockedWithout. 시트로 가는 경로가 없다.
따라서 "이미 뽑은 의존성이 등록 시 소실된다"가 아니라 미추출 + 미연결이었다.
이 모듈은 양쪽 스키마를 모두 받아 같은 모양으로 돌려준다.

설계 선택 — 저장하지 않는다:
  의존성 본문은 이미 문서함 JSON(DOC_DIR/<pid>/<ts>.json 의 doc["result"])에 있고,
  조회 키(N열 source_ref = "<pid>|<ts>[|액션ID]")도 이미 시트에 있다. 시트에 열을 더하면
  회의록을 수정할 때 두 사본이 어긋난다 — 회의록이 회의 정보의 SSOT다.

표시 전용이다. G9 의존성 엔진(연쇄 재계산·선행 미완료 시 이동 차단·임계경로)은
조직 규모 대비 과잉으로 도입 보류 결정이 유지된다(23-progress.md). 여기서는 어떤
쓰기도 막지 않고, 사람이 판단할 정보만 카드에 얹는다.

원칙: 순수함수 + 경로 주입(provenance·approval과 동일 — I/O 소유는 호출측).
"""
from __future__ import annotations

import json
from pathlib import Path

_LEVELS = ("BLOCKING", "IMPORTANT", "REFERENCE")


def load_result(doc_dir, pid: str, ts: str) -> dict:
    """문서함 JSON → doc["result"]. 없거나 깨졌으면 {} (화면이 죽지 않게)."""
    if not (doc_dir and pid and ts):
        return {}
    try:
        p = Path(doc_dir) / pid / f"{ts}.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return (doc or {}).get("result") or {}


def _clean_level(raw) -> str:
    s = (raw or "").strip().upper()
    return s if s in _LEVELS else "IMPORTANT"


def action_index(result: dict) -> dict:
    """회의 분석 결과 → {액션ID: {"title", "depends_on":[선행 업무명], "blocking":[...]}}.

    엔진 B가 있으면 그쪽을 쓴다(정보가 더 많다). 없으면 엔진 A의 5블록 to-do를 읽는다.
    엔진 B의 dependencies는 액션 **ID** 목록이므로 사람이 읽을 제목으로 바꿔서 돌려준다.
    """
    result = result or {}
    idx: dict = {}

    acts = result.get("actions")
    if isinstance(acts, list) and acts:                      # ── 엔진 B (R4)
        by_id = {}
        for a in acts:
            aid = str((a or {}).get("id") or "").strip()
            if aid:
                by_id[aid] = str(a.get("title") or "").strip()
        for a in acts:
            aid = str((a or {}).get("id") or "").strip()
            if not aid:
                continue
            deps = []
            for d in (a.get("dependencies") or []):
                d = str(d or "").strip()
                if not d:
                    continue
                deps.append(by_id.get(d) or d)   # 못 찾으면 원문 유지(예외 아님)
            idx[aid] = {"title": by_id.get(aid, ""), "depends_on": deps, "blocking": []}
        for s in (result.get("supportRequests") or []):
            aid = str((s or {}).get("actionId") or "").strip()
            if aid not in idx:
                continue                          # 존재하지 않는 액션 참조는 무시
            without = str(s.get("blockedWithout") or "").strip()
            who = str(s.get("stakeholderName") or "").strip()
            if not (without or who):
                continue
            idx[aid]["blocking"].append({"who": who, "level": _clean_level(s.get("blockingLevel")),
                                         "without": without})
        return idx

    ours = ((result.get("block_5_todos") or {}).get("ours") or [])   # ── 엔진 A
    for i, t in enumerate(ours, 1):
        t = t or {}
        deps = [str(d or "").strip() for d in (t.get("depends_on") or []) if str(d or "").strip()]
        blocked = str(t.get("blocked_by") or "").strip()
        idx[f"A{i}"] = {
            "title": str(t.get("task") or "").strip(),
            "depends_on": deps,
            # 엔진 A의 blocked_by는 "못 받으면 멈추는 것" — 대상(who)은 없고 조건만 있다
            "blocking": ([{"who": "", "level": "BLOCKING", "without": blocked}] if blocked else []),
        }
    return idx


def deps_for(assign: dict, doc_dir, pv_mod, cache: dict | None = None):
    """분장 1건 → {"depends_on", "blocking"} 또는 None(연결 정보 없음).

    cache: {(pid, ts): action_index} — 목록 API에서 같은 회의 문서를 N번 읽지 않도록
    호출측이 dict 하나를 만들어 넘긴다.
    """
    if not pv_mod.is_meeting_action(assign):
        return None
    pid, ts, aid = pv_mod.parse_meeting_ref3((assign or {}).get("source_ref"))
    if not (pid and ts):
        return None
    key = (pid, ts)
    if cache is not None and key in cache:
        idx = cache[key]
    else:
        idx = action_index(load_result(doc_dir, pid, ts))
        if cache is not None:
            cache[key] = idx
    if not idx:
        return None
    dep = idx.get(aid) if aid else None
    if dep is None:
        # 레거시 2세그먼트 참조 — 업무명 정확일치 폴백.
        # 업무명은 편집될 수 있으므로 신규 등록은 액션 ID를 함께 남긴다(meeting_ref 3세그먼트).
        task = str((assign or {}).get("task") or "").strip()
        if task:
            for v in idx.values():
                if v.get("title") and v["title"] == task:
                    dep = v
                    break
    if not dep or not (dep.get("depends_on") or dep.get("blocking")):
        return None
    return {"depends_on": list(dep.get("depends_on") or []),
            "blocking": list(dep.get("blocking") or [])}


def deps_summary(dep: dict) -> str:
    """표시용 한 줄. 카드가 좁으므로 선행 2건까지만 보이고 나머지는 개수로 접는다."""
    if not dep:
        return ""
    parts = []
    deps = dep.get("depends_on") or []
    if deps:
        head = " · ".join(d[:24] for d in deps[:2])
        parts.append(f"선행: {head}" + (f" 외 {len(deps) - 2}건" if len(deps) > 2 else ""))
    for b in (dep.get("blocking") or []):
        if b.get("level") != "BLOCKING":
            continue
        who = b.get("who") or ""
        without = (b.get("without") or "")[:30]
        parts.append(f"🚧 {who + ' ' if who else ''}미수신 시 중단" + (f": {without}" if without else ""))
        break
    return " · ".join(parts)


def has_blocking(dep: dict) -> bool:
    """BLOCKING 등급 차단 요인이 있는가 — 카드 강조(빨강) 판정용."""
    return any((b or {}).get("level") == "BLOCKING" for b in ((dep or {}).get("blocking") or []))
