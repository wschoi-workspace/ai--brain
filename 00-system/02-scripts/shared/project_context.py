"""Project Context — 회의가 갱신하는 프로젝트의 기계용 누적 상태 (vNext P2 WS6).

arisa2 master_context의 의미(델타를 반영해 현재 상태를 재정리)만 가져오고 구현은
새로 한다. arisa2의 두 실패를 반대로 설계한 것:
  · 전부 문자열 배열이라 "이 요구사항이 어느 회의에서 왔나"를 물을 수 없었다
    → 모든 항목이 since(meeting_ref)를 갖는다.
  · 같은 회의 재파싱이 중복 delta를 만들었다
    → appliedRefs + transcriptHash 2중 멱등 가드.

사람용 요약(p["brief"])과 역할이 다르다 — brief는 PM 승인을 거치고, context는
무승인 자동 적용된다. 자동 적용이 정당한 이유가 revert_ref다: 전 항목이 출처
ref를 달고 있어 오적용 회의를 통째로 되돌릴 수 있다.

원칙(shared 규약): 순수 함수만. 파일 I/O·저장 경로는 호출측 책임.
"""
from __future__ import annotations

import re


def _norm(s) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", str(s or "").lower())


def new_context(pid) -> dict:
    return {"pid": pid, "updatedAt": "", "appliedRefs": [], "transcriptHashes": [],
            "requirements": [], "risks": [], "decisions": [],
            "openQuestions": [], "decisionNeeded": [], "timeline": []}


def is_applied(ctx, delta) -> bool:
    """멱등 가드 — ref 일치 또는 (해시가 있을 때) 전사 지문 일치."""
    ctx = ctx or {}
    if delta.get("ref") in (ctx.get("appliedRefs") or []):
        return True
    h = delta.get("transcriptHash") or ""
    return bool(h) and h in (ctx.get("transcriptHashes") or [])


def apply_delta(ctx, delta, now="") -> tuple:
    """(새 ctx, 적용 로그). 이미 적용된 delta면 (원본 그대로, ["skip: ..."]).

    가환성은 보장하지 않는다(회의는 시간순이 의미다) — 대신 멱등만 엄격히 지킨다.
    """
    if is_applied(ctx, delta):
        return (ctx, [f"skip: {delta.get('ref')} 이미 적용됨"])
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in (ctx or new_context("")).items()}
    ref = delta.get("ref") or ""
    log = []

    # 요구사항 — scope=REQUIREMENT 변경만. before="없음"이면 추가, 아니면 기존 항목 개정.
    reqs = [dict(r) for r in out.get("requirements") or []]
    for c in (delta.get("changes") or []):
        if c.get("scope") != "REQUIREMENT":
            continue
        after, before = c.get("after") or "", c.get("before") or ""
        if not after:
            continue
        if before and before != "없음":
            hit = next((r for r in reqs
                        if r.get("status") == "ACTIVE" and _norm(before)
                        and (_norm(before) in _norm(r.get("text")) or _norm(r.get("text")) in _norm(before))),
                       None)
            if hit:
                hit["text"] = after
                hit.setdefault("changedBy", []).append(ref)
                log.append(f"요구사항 개정: {after[:40]}")
                continue
        if not any(_norm(r.get("text")) == _norm(after) for r in reqs):
            reqs.append({"text": after, "status": "ACTIVE", "since": ref, "changedBy": []})
            log.append(f"요구사항 추가: {after[:40]}")
    out["requirements"] = reqs

    # 리스크 — 정규화 신규만 추가 (닫는 것은 사람·후속 회의의 몫, 여기서 지우지 않는다)
    risks = [dict(r) for r in out.get("risks") or []]
    for r in (delta.get("risks") or []):
        if not any(_norm(x.get("text")) == _norm(r.get("risk")) for x in risks):
            risks.append({"text": r.get("risk"), "severity": r.get("severity") or "MEDIUM",
                          "status": "OPEN", "since": ref})
            log.append(f"리스크: {(r.get('risk') or '')[:40]}")
    out["risks"] = risks

    # 결정 — 제목 정규화 dedupe. arisa2처럼 "문자열로 뭉개지" 않고 구조를 유지한다.
    decs = [dict(d) for d in out.get("decisions") or []]
    for d in (delta.get("decisions") or []):
        if not any(_norm(x.get("title")) == _norm(d.get("title")) for x in decs):
            decs.append({"title": d.get("title"), "status": d.get("status") or "CONFIRMED",
                         "rationale": d.get("rationale") or "", "since": ref})
            log.append(f"결정: {(d.get('title') or '')[:40]}")
    out["decisions"] = decs

    # 미결 — 같은 사안이 다시 나오면 최신 회의 기준으로 갱신(decider·기한이 바뀔 수 있다)
    oq = [dict(x) for x in out.get("openQuestions") or []]
    for g in (delta.get("openIssues") or []):
        hit = next((x for x in oq if _norm(x.get("text")) == _norm(g.get("issue"))), None)
        if hit:
            hit.update({"decider": g.get("decider") or hit.get("decider"),
                        "deadline": g.get("deadline") or hit.get("deadline"), "since": ref})
        else:
            oq.append({"text": g.get("issue"), "decider": g.get("decider") or "",
                       "deadline": g.get("deadline") or "", "since": ref})
    out["openQuestions"] = oq

    # 대표 판단 필요 — routing.ceo에서. arisa2의 owner="대표"/urgency="high" 하드코딩과 달리
    # LLM이 판정한 항목만 들어온다.
    dn = [dict(x) for x in out.get("decisionNeeded") or []]
    for item in ((delta.get("routing") or {}).get("ceo") or []):
        if not any(_norm(x.get("content")) == _norm(item.get("item")) for x in dn):
            dn.append({"content": item.get("item"), "why": item.get("why") or "", "since": ref})
    out["decisionNeeded"] = dn

    out.setdefault("timeline", []).append({
        "ref": ref, "date": delta.get("meetingDate") or "", "title": delta.get("title") or "",
        "changeCount": len(delta.get("changes") or []),
        "decisionCount": len(delta.get("decisions") or [])})
    out.setdefault("appliedRefs", []).append(ref)
    if delta.get("transcriptHash"):
        out.setdefault("transcriptHashes", []).append(delta["transcriptHash"])
    out["updatedAt"] = now
    return (out, log or ["변경 없음(빈 delta)"])


def revert_ref(ctx, ref) -> dict:
    """오적용 회의 되돌리기 — since==ref 항목 제거, 개정(changedBy)은 표식만 제거.

    개정 전 원문 복원은 호출측이 history/{ts}.json 스냅샷으로 한다(여기선 구조 정리만).
    무승인 자동 적용을 정당화하는 함수이므로 반드시 유지한다.
    """
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in (ctx or {}).items()}
    for key in ("requirements", "risks", "decisions", "openQuestions", "decisionNeeded"):
        kept = []
        for item in out.get(key) or []:
            if item.get("since") == ref:
                continue
            if ref in (item.get("changedBy") or []):
                item = dict(item, changedBy=[r for r in item["changedBy"] if r != ref])
            kept.append(item)
        out[key] = kept
    out["timeline"] = [t for t in out.get("timeline") or [] if t.get("ref") != ref]
    out["appliedRefs"] = [r for r in out.get("appliedRefs") or [] if r != ref]
    return out
