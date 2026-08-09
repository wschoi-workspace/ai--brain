"""R4 회의 결과 → Context Delta 결정론 투영 (vNext P2 WS6).

Delta 생성에 LLM을 쓰지 않는다 — 원천(F_changes·decisions·H_risks·G_open_issues·
routing)이 전부 R4가 이미 구조화해 낸 것이다. 투영이므로 비용 0, 재현 가능, 멱등.
arisa2가 같은 회의록을 두 번 파싱해 문구가 전부 다른 delta 2건을 만든 것이
정확히 "생성을 LLM에 맡긴" 방식의 산물이었다.

원칙(shared 규약): 순수 함수만. 파일 I/O는 호출측(dashboard-server) 책임.
"""
from __future__ import annotations

import hashlib
import re

SCOPES = ("REQUIREMENT", "SCHEDULE", "BUDGET", "SCOPE", "OWNER", "DELIVERABLE", "STRATEGY")


def transcript_hash(text) -> str:
    """전사 지문 — 공백·개행 정규화 후 sha1. 다른 세션 ID로 같은 전사를 재분석해도
    이 지문이 같아 중복 적용이 차단된다(arisa2가 놓친 지점)."""
    norm = re.sub(r"\s+", "", text or "")
    if not norm:
        return ""
    return "sha1:" + hashlib.sha1(norm.encode("utf-8")).hexdigest()


def _clean(s, limit=300) -> str:
    return str(s or "").strip()[:limit]


def project_delta(result, pid, ts, created_at="") -> dict:
    """R4 제출 result(analysis+routing 등) → delta dict.

    ref = "<pid>|<ts>" — provenance.meeting_ref와 동일 규격, 새 ID 체계를 만들지 않는다.
    ts는 문서함 ts와 같아 delta·문서·history가 한 키로 조인된다.
    """
    result = result or {}
    mins = result.get("minutes") or {}
    changes = []
    for c in (mins.get("F_changes") or []):
        if not isinstance(c, dict):
            continue
        sc = _clean(c.get("scope"), 20).upper()
        changes.append({
            "scope": sc if sc in SCOPES else "SCOPE",
            "what": _clean(c.get("what")), "before": _clean(c.get("before")),
            "after": _clean(c.get("after")), "why": _clean(c.get("why")),
            "impact": [_clean(x) for x in (c.get("impact") or []) if _clean(x)][:5]})
    decisions = []
    for d in (result.get("decisions") or []):
        if not isinstance(d, dict) or not _clean(d.get("title")):
            continue
        decisions.append({"id": _clean(d.get("id"), 10), "title": _clean(d.get("title")),
                          "status": _clean(d.get("status"), 20) or "CONFIRMED",
                          "rationale": _clean(d.get("rationale")),
                          "decidedBy": [_clean(x, 40) for x in (d.get("decidedBy") or [])][:5]})
    risks = []
    for r in (mins.get("H_risks") or []):
        if not isinstance(r, dict) or not _clean(r.get("risk")):
            continue
        risks.append({"risk": _clean(r.get("risk")),
                      "severity": _clean(r.get("severity"), 10) or "MEDIUM",
                      "response": _clean(r.get("response"))})
    open_issues = []
    for g in (mins.get("G_open_issues") or []):
        if not isinstance(g, dict) or not _clean(g.get("issue")):
            continue
        open_issues.append({"issue": _clean(g.get("issue")),
                            "needed_decision": _clean(g.get("needed_decision")),
                            "decider": _clean(g.get("decider"), 40),
                            "deadline": _clean(g.get("deadline"), 20)})
    rt = result.get("routing") or {}
    routing = {k: [x for x in (rt.get(k) or []) if isinstance(x, dict)][:5]
               for k in ("ceo", "lead", "member")}
    meta = result.get("meta") or {}
    return {
        "ref": f"{pid}|{ts}", "r4SessionId": _clean(result.get("r4SessionId"), 30),
        "createdAt": created_at, "meetingDate": _clean(meta.get("date"), 20),
        "title": _clean(meta.get("title"), 100),
        "transcriptHash": "",   # 호출측이 transcript_hash()로 채운다 (전사는 result 밖에 있다)
        "changes": changes, "decisions": decisions, "risks": risks,
        "openIssues": open_issues, "routing": routing,
        # 액션·산출물은 회의록(문서함 JSON)이 SSOT — 여기엔 개수만 (meeting_link 원칙:
        # "의존성을 복제 저장하지 않고 문서함을 조회한다"의 delta판)
        "actionCount": len(result.get("actions") or []),
        "outputCount": len(result.get("outputs") or []),
    }
