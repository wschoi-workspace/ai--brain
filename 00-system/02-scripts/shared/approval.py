"""승인 체인·권한 매트릭스 — R4 개편 2차 (2026-07-25).

가이드 구조: 실무 담당자 → 파트 리더 → 프로젝트 PM → 대표.
dashboard-server의 _can_approve(대표 전체·리더는 자기 팀원)를 프로젝트 맥락까지
일반화한 단일 출처. 순수함수만 둔다 — 파일 I/O·로드는 호출측(dashboard) 책임.

용어:
  emp   = arisa-employees.json dict (by_name/team_leads)
  project = 포트폴리오 프로젝트 dict (pm/partLeads/aliases…) 또는 None
  rules = approval-rules.json dict (levels/rules/defaults)
"""
from __future__ import annotations

LEVELS = ("담당자", "파트리더", "PM", "대표")


def _team_of(assignee, emp):
    return ((emp or {}).get("by_name", {}).get(assignee, {}) or {}).get("team") or ""


def part_lead_for(assignee, project, emp):
    """담당자의 파트리더 — 프로젝트별 지정(project.partLeads[팀]) 우선,
    없으면 조직 기본(team_leads[팀]) 폴백. 공석이면 ""."""
    team = _team_of(assignee, emp)
    if not team:
        return ""
    pl = ((project or {}).get("partLeads") or {}).get(team)
    return pl or ((emp or {}).get("team_leads") or {}).get(team) or ""


def chain_for(assignee, project, emp):
    """승인 체인 [(레벨, 사람)] — 공석·중복(리더=PM 등)은 접는다. 대표는 표시상 생략
    (대표는 모든 단계를 대신할 수 있으므로 체인에 명시하지 않음)."""
    chain = [("담당자", assignee or "")]
    pl = part_lead_for(assignee, project, emp)
    pm = ((project or {}).get("pm") or "").strip()
    if pl and pl != assignee:
        chain.append(("파트리더", pl))
    if pm and pm not in (assignee, pl):
        chain.append(("PM", pm))
    return chain


def next_step(status, assignee, project, emp):
    """대기 상태의 다음 처리 단계 — ("파트리더"|"PM"|"대표", 담당자명 또는 "").

    완료(담당자 완료 보고) → 파트리더 검토. 리더 공석이면 PM, 둘 다 없으면 대표.
    승인대기(검토 통과) → PM 클리어. PM 공석이면 대표.
    """
    pl = part_lead_for(assignee, project, emp)
    pm = ((project or {}).get("pm") or "").strip()
    if status == "완료":
        if pl and pl != assignee:
            return ("파트리더", pl)
        if pm and pm != assignee:
            return ("PM", pm)
        return ("대표", "")
    if status == "승인대기":
        if pm and pm != assignee:
            return ("PM", pm)
        return ("대표", "")
    return ("", "")


def level_of(uid, assignee, project, emp, admin=False, lead_teams=()):
    """이 사용자가 이 분장 건에 대해 갖는 최고 레벨. 해당 없으면 ""."""
    if admin:
        return "대표"
    if ((project or {}).get("pm") or "") == uid:
        return "PM"
    if part_lead_for(assignee, project, emp) == uid:
        return "파트리더"
    if _team_of(assignee, emp) in set(lead_teams or ()):
        return "파트리더"  # 조직 리더 폴백 (기존 _can_approve 동작 보존)
    if uid == assignee:
        return "담당자"
    return ""


def can_clear(uid, assignee, project, emp, admin=False, lead_teams=()):
    """PM 클리어·검토 통과·최종 승인 권한 — 파트리더 이상."""
    return level_of(uid, assignee, project, emp, admin, lead_teams) in ("파트리더", "PM", "대표")


def required_level(item, rules):
    """결재 항목의 최소 승인 단계 — approval-rules.json 매칭.

    item: {"type": "...", "amount": 숫자(원, 선택)}. 매칭 규칙이 여러 개면 가장 높은 단계.
    """
    levels = list((rules or {}).get("levels") or LEVELS)
    best = (rules or {}).get("defaults", {}).get("minLevel") or "파트리더"
    itype = ((item or {}).get("type") or "").strip()
    try:
        amount = float((item or {}).get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0

    def rank(lv):
        return levels.index(lv) if lv in levels else 0

    for r in (rules or {}).get("rules") or []:
        hit = False
        if r.get("type") and r["type"] == itype:
            hit = True
        if r.get("amountOver") is not None and amount > float(r["amountOver"]):
            hit = True
        if hit and rank(r.get("minLevel") or "") > rank(best):
            best = r["minLevel"]
    return best


# PM 클리어 선택지 → 효과 (dashboard /api/pm-clear가 소비)
#   to: 시트 H열 전이 (None=상태 유지) / escalate: decisions.jsonl 에스컬레이션 타입
PM_CLEAR_EFFECTS = {
    "정상완료":     {"to": "승인",   "escalate": None,              "urgency": None},
    "수정필요":     {"to": "진행중", "escalate": None,              "urgency": None},
    "지연":         {"to": None,     "escalate": None,              "urgency": None},
    "패스":         {"to": "패스",   "escalate": None,              "urgency": None},
    "대표보고필요": {"to": None,     "escalate": "pm-report",       "urgency": "medium"},
    "대표결정필요": {"to": None,     "escalate": "pm-decision",     "urgency": "high"},
    "대표지원필요": {"to": None,     "escalate": "pm-intervention", "urgency": "high"},
}
