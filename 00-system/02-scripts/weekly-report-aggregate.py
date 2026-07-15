#!/usr/bin/env python3
"""ARISA 주간 업무 대시보드 — 일일보고 2시트를 모아 개인별·파트별 주간 집계 + HTML 대시보드.

파이프라인: fetch(gws) → normalize → aggregate(개인/파트) → build_data → render(HTML) → save/notify
하이브리드 축: 실용 집계(업무량·완료율·카테고리·블로커·도구·미해결결정)를 산출하고,
ARISA 성장지표(해상도·Growth6)는 자리만 마련(placeholder)해 추후 compute_growth로 점진 연결.

런타임: 24-second-brain/.venv311 (gws CLI는 subprocess). 자동화: 월 08:30 launchd.
사용:
  python weekly-report-aggregate.py --week last [--open] [--no-telegram]
  --week last  : 직전 월~일 (기본). --week YYYY-MM-DD : 그 날이 속한 주
"""
from __future__ import annotations

import os
import sys
import json
import html
import copy
import argparse
import subprocess
from datetime import datetime, timedelta, date
from pathlib import Path
from collections import Counter, defaultdict

# ─── 경로/설정 ───
SCRIPTS = Path(__file__).resolve().parent
WORKSPACE = SCRIPTS.parent.parent
EMP_PATH = SCRIPTS / "arisa-employees.json"
OUT_DIR = WORKSPACE / "20-operations" / "23-arisa" / "weekly"
ENV_PATHS = [WORKSPACE / ".env", Path.home() / "arisa-project-memory" / ".env"]


def load_env():
    for p in ENV_PATHS:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
load_env()

DAILY_SHEET = os.environ.get("DAILY_REPORT_SHEET_ID", "")
BASKET_SHEET = os.environ.get("BASKET_REPORT_SHEET_ID", "")
MANAGER_BOT_TOKEN = os.environ.get("DAILY_REPORT_MANAGER_BOT_TOKEN", "")
MANAGER_CHAT_ID = os.environ.get("DAILY_REPORT_MANAGER_CHAT_ID", "")
# 알림 속 대시보드 링크 — .env의 DASHBOARD_BASE_URL 우선 (daily-brief-aggregate.py와 동일 정책)
DASHBOARD_BASE_URL = os.environ.get("DASHBOARD_BASE_URL", "https://server-mini-macmini.tail7739de.ts.net")

# 차트 6색 팔레트 (project-rent)
PALETTE = ["#6C5CE7", "#A29BFE", "#6F8AA3", "#8FA37E", "#D9A34B", "#E17055", "#B0B0B0"]
TEAM_ORDER = ["경영", "사업기획", "공간팀", "기획팀", "운영팀", "감사"]

# ─── ARISA 성장지표 (측정설계 v2) ───
# 14요소 사전. daily 기대셋(일일보고 기준): 필수 4 + 선택 4. (중요도·난이도 가중은 자가표시
# 수집 전이라 1차에선 무가중 = 요소 동일가중. 측정설계 §3 가중은 데이터 쌓인 뒤 도입.)
DAILY_REQUIRED = ["output", "outcome", "problem", "approach"]      # 산출물·의미·문제·해결방향
DAILY_OPTIONAL = ["timeline", "support", "decision", "next"]       # 일정·요청·의사결정·실행계획
GROWTH_PROMPT = """너는 ARISA 측정 엔진이다. 직원의 한 주간 업무보고 '원문(raw)'을 읽고,
14개 사고요소가 얼마나 채워졌고 얼마나 구체적인지 채점한다.

[엄격 규칙 — fidelity]
- 원문에 실제 있는 내용만 근거로 한다. 추측·관대한 해석 금지.
- 근거가 없거나 형식적이면 filled=false, depth=0.
- 정리·요약하지 말고 '있는가/얼마나 구체적인가'만 본다.

[깊이 0~3 공통 눈금] 0=비었거나 형식적 / 1=언급만 / 2=구체적 / 3=구체 디테일+핵심 명확

[14요소] (키: 정의 — 깊이 갈림)
status: 현황 — "진행중"→단계·완료율 / why: 목적 — 막연→상위목표 연결 /
problem: 문제·블로커 — "어렵다"→원인·범위·영향 / approach: 해결방향 — "열심히"→선택지·근거 /
output: 산출물 — 업무명반복→구체결과물 / outcome: 의미 — "잘됨"→무엇이 달라졌나 /
timeline: 일정 — "곧"→날짜·마일스톤 / risk: 리스크 — 누락→발생가능성·대비 /
support: 요청 — "도와주세요"→누가·무엇 / decision: 의사결정 — 모호→선택지+추천+기한 /
budget: 예산 — 누락→금액·항목 / impact: 기대효과 — 막연→정량·정성 /
next: 실행계획 — "진행"→단계별액션 / reflection: 회고 — 형식적→구체관찰

반드시 아래 JSON만 출력(14키 전부):
{"elements":{"status":{"filled":false,"depth":0},"why":{...},...,"reflection":{...}}}"""

_growth_client = None
def _get_growth_client():
    global _growth_client
    if _growth_client is None:
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            return None
        try:
            from openai import OpenAI
            _growth_client = OpenAI(api_key=key)
        except Exception:
            return None
    return _growth_client

# basket 항목 컬럼(D~N) → (canonical 카테고리). 비어있지 않은 칸을 1건으로 분해.
BASKET_FIELDS = [
    (3, "매출", "관리"), (4, "지출", "관리"), (5, "송금·승인", "관리"),
    (6, "특이사항", "기타"), (7, "장비", "관리"), (8, "업무보고", "실행"),
    (9, "대관", "커뮤니케이션"), (10, "스태프", "관리"), (11, "구매", "관리"),
    (12, "입점제안", "기획"), (13, "복기", "리서치"),
]
# 과거 데이터 영문/변형 이름 → 명부 정규명 (명부연동 이전분 흡수)
NAME_ALIASES = {
    "yang eun jung": "양은정", "yangeunjung": "양은정", "eun jung": "양은정",
    "준호 김": "김준호", "김 준호": "김준호", "bro callme": "최원석",
}


# ─── 명부·정규화·gws (shared 코어 위임 — Phase 1) ───
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared.employee import load_employees as _load_emp
from shared import normalize as _N, gws as _gws


def load_employees() -> dict:
    return _load_emp(EMP_PATH)

EMP = load_employees()
BY_NAME = EMP.get("by_name", {})


def normalize_name(s: str) -> str:
    return _N.normalize_name(s, BY_NAME, NAME_ALIASES)


def team_of(name: str) -> str:
    return _N.team_of(name, BY_NAME)


def normalize_date(s: str) -> str | None:
    return _N.normalize_date(s)


def _gws_values_get(sheet_id: str, rng: str, retries: int = 3) -> list[list]:
    return _gws.values_get(sheet_id, rng, retries)


def fetch_daily() -> dict:
    return {
        "core": _gws_values_get(DAILY_SHEET, "핵심업무!A2:L5000"),
        "sub":  _gws_values_get(DAILY_SHEET, "서브업무!A2:F5000"),
        "meta": _gws_values_get(DAILY_SHEET, "메타!A2:L5000"),
    }


def fetch_assignments(week_start: date, week_end: date) -> list[dict]:
    """주간분장 탭에서 해당 주(월~일) 항목 fetch → dict 리스트.
    실스키마(셸 '내 업무' AI 분장, 2026-07 전환): 날짜(0)|프로젝트명(1)|팀구분(2)|담당자(3)|
    업무내용(4)|일정완료예상(5)|결과물(6)|상태(7)|이해관계자(8)|우선순위(9)
    (구 W주차 라벨 스키마는 폐기 — daily-brief-aggregate.fetch_assignments와 동일 기준)"""
    rows = _gws_values_get(DAILY_SHEET, "주간분장!A2:J5000")
    items = []
    for r in rows:
        r = r + [""] * (10 - len(r))
        nd = normalize_date(r[0])
        if not nd:
            continue
        rd = datetime.strptime(nd, "%Y-%m-%d").date()
        if not (week_start <= rd <= week_end):
            continue
        if not (r[4] or "").strip():
            continue
        items.append({
            "date": nd, "project": (r[1] or "").strip(),
            "team": (r[2] or "").strip(),
            "assignee": normalize_name(r[3]),
            "task": (r[4] or "").strip(), "deadline": (r[5] or "").strip(),
            "status": (r[7] or "미착수").strip(),
            "priority": (r[9] or "일반").strip(),
        })
    return items


def match_assignments_to_daily(assignments: list[dict], records: list[dict]) -> list[dict]:
    """분장 항목 vs 일일보고 업무를 키워드 매칭하여 상태 추정.
    매칭 로직: 분장 업무 키워드가 일일보고 task에 2개 이상 포함 → 진행중/완료로 업데이트.
    """
    import re
    for a in assignments:
        if a["status"] in ("완료", "승인"):
            continue
        # 분장 업무에서 핵심 키워드 추출 (2자 이상 단어)
        words = [w for w in re.split(r'[\s/·,\-]+', a["task"]) if len(w) >= 2]
        if not words:
            continue
        matched_tasks = []
        for r in records:
            if r["source"] not in WORK_SRC:
                continue
            # 담당자 매칭(있으면 우선 필터)
            if a["assignee"] and a["assignee"] != "팀":
                if r["name"] != a["assignee"]:
                    continue
            # 키워드 매칭
            rtask = r.get("task", "")
            hits = sum(1 for w in words if w in rtask)
            if hits >= min(2, len(words)):
                matched_tasks.append(r)
        if matched_tasks:
            has_done = any("완료" in (r.get("status") or "") for r in matched_tasks)
            a["status"] = "완료" if has_done else "진행중"
    return assignments


def update_assignment_status_in_sheet(assignments: list[dict]) -> int:
    """시트 '주간분장' 탭의 상태 컬럼(H열)을 매칭 결과로 업데이트."""
    rows = _gws_values_get(DAILY_SHEET, "주간분장!A2:J5000")
    updated = 0
    for a in assignments:
        if a["status"] in ("미착수",):
            continue
        for i, r in enumerate(rows):
            r = r + [""] * (10 - len(r))
            if (normalize_date(r[0]) == a["date"] and (r[4] or "").strip() == a["task"]
                    and normalize_name(r[3]) == a["assignee"]):
                if (r[7] or "").strip() != a["status"]:
                    row_num = i + 2  # 1-indexed header
                    _gws.values_update(
                        DAILY_SHEET, f"주간분장!H{row_num}",
                        [[a["status"]]], timeout=10,
                    )
                    updated += 1
                break
    return updated


def fetch_basket() -> list[list]:
    return _gws_values_get(BASKET_SHEET, "일일보고!A2:O5000")


# ─── 정규화 → 공통 레코드 ───
def _rec(**kw) -> dict:
    base = dict(date=None, name="", team="", category="기타", task="", status="",
                tools="", output="", issue="", outcome="", blocker="",
                decision_needed="", support_needed="", reflection="", raw="", source="")
    base.update(kw)
    return base


def normalize_daily(daily: dict) -> list[dict]:
    out = []
    # 핵심업무: 날짜·이름·팀·역할·카테고리·업무내용·상태·프로세스·도구·산출물·이슈·outcome
    for r in daily["core"]:
        r = r + [""] * (12 - len(r))
        d = normalize_date(r[0])
        nm = normalize_name(r[1])
        if not d or not nm:
            continue
        out.append(_rec(date=d, name=nm, team=team_of(nm), category=(r[4] or "기타").strip(),
                        task=r[5], status=(r[6] or "").strip(), tools=r[8], output=r[9],
                        issue=r[10], outcome=r[11], source="daily-core"))
    # 서브업무: 날짜·이름·팀·카테고리·업무명·상태
    for r in daily["sub"]:
        r = r + [""] * (6 - len(r))
        d = normalize_date(r[0]); nm = normalize_name(r[1])
        if not d or not nm:
            continue
        out.append(_rec(date=d, name=nm, team=team_of(nm), category=(r[3] or "기타").strip(),
                        task=r[4], status=(r[5] or "").strip(), source="daily-sub"))
    # 메타: 날짜·이름·팀·내일·개선·블로커·첨부·결정·지원·reflection·raw·질문
    for r in daily["meta"]:
        r = r + [""] * (12 - len(r))
        d = normalize_date(r[0]); nm = normalize_name(r[1])
        if not d or not nm:
            continue
        out.append(_rec(date=d, name=nm, team=team_of(nm), category="_meta",
                        blocker=r[5], decision_needed=r[7], support_needed=r[8],
                        reflection=r[9], raw=r[10], source="daily-meta"))
    return out


def normalize_basket(rows: list[list]) -> list[dict]:
    out = []
    for r in rows:
        r = r + [""] * (15 - len(r))
        d = normalize_date(r[1])
        nm = normalize_name(r[2])
        if not d or not nm:
            continue
        team = team_of(nm) if BY_NAME.get(nm) else "운영팀"
        # 비어있지 않은 항목칸을 각각 1건으로 분해
        any_field = False
        for idx, label, cat in BASKET_FIELDS:
            v = (r[idx] or "").strip()
            if not v:
                continue
            any_field = True
            rec = _rec(date=d, name=nm, team=team, category=cat, task=f"[{label}] {v[:80]}",
                       status="N/A", source="basket")  # basket은 상태없음 → 완료율 분모 제외
            if label == "복기":
                rec["reflection"] = v
            elif label == "특이사항":
                rec["blocker"] = v
            elif label == "송금·승인":
                rec["decision_needed"] = v
            out.append(rec)
        if not any_field:  # 빈 껍데기 행 — 스킵(과거 데이터 방어)
            continue
    return out


# ─── 집계 ───
WORK_SRC = {"daily-core", "daily-sub", "basket"}  # 실제 업무 레코드(메타 제외)


def _completion(recs: list[dict]) -> tuple[int, float | None]:
    """완료율: status가 N/A가 아닌 업무만 분모. (분모0이면 None)"""
    work = [r for r in recs if r["source"] in WORK_SRC]
    scored = [r for r in work if r["status"] and r["status"] != "N/A"]
    if not scored:
        return len(work), None
    done = sum(1 for r in scored if "완료" in r["status"])
    return len(work), round(done / len(scored) * 100)


def _blockers(recs: list[dict]) -> list[str]:
    items = []
    for r in recs:
        for v in (r["blocker"], r["issue"]):
            v = (v or "").strip()
            if v and v not in ("없음", "-", "없어요"):
                items.append(v[:60])
    # 중복 제거(앞부분 기준), 최대 4
    seen, out = set(), []
    for it in items:
        k = it[:15]
        if k not in seen:
            seen.add(k); out.append(it)
    return out[:4]


def _tools(recs: list[dict]) -> list[str]:
    c = Counter()
    for r in recs:
        for t in (r["tools"] or "").replace(",", "/").split("/"):
            t = t.strip()
            if t and t not in ("없음", "-"):
                c[t] += 1
    return [t for t, _ in c.most_common(6)]


def _categories(recs: list[dict]) -> dict:
    c = Counter()
    for r in recs:
        if r["source"] in WORK_SRC:
            c[r["category"] or "기타"] += 1
    return dict(c.most_common())


def _open_decisions(recs: list[dict]) -> list[str]:
    out = []
    for r in recs:
        v = (r["decision_needed"] or "").strip()
        if v and v not in ("없음", "-"):
            out.append(v[:70])
    return out[:5]


def _empty_growth() -> dict:
    return {"status": "collecting", "resolution": None,
            "metrics": {"clarity": None, "evidence": None, "structure": None,
                        "output_quality": None, "outcome_quality": None, "decision_thinking": None}}


def compute_growth(recs: list[dict]) -> dict:
    """ARISA 성장지표(측정설계 v2): 직원 주간 raw 원문을 LLM으로 14요소 채점 →
    해상도 = Coverage × Depth (daily 기대셋 기준, 0~3 정규화). fidelity: raw 없으면 collecting,
    추측 채점 금지(LLM 프롬프트가 강제). 6지표는 깊이 채점 렌즈로 흡수."""
    raws = [r["raw"] for r in recs if r.get("source") == "daily-meta" and (r.get("raw") or "").strip()]
    if not raws:
        return _empty_growth()  # 원문 없음(basket 등) → 수집 중 유지
    client = _get_growth_client()
    if client is None:
        return _empty_growth()
    text = "\n\n---\n\n".join(raws)[:6000]
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini", temperature=0.1,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": GROWTH_PROMPT},
                      {"role": "user", "content": f"[직원 주간 보고 원문]\n{text}"}],
        )
        el = json.loads(resp.choices[0].message.content or "{}").get("elements", {})
    except Exception as e:
        sys.stderr.write(f"[growth err] {e}\n")
        return _empty_growth()

    def d(k):  # 요소 깊이(0~3), 미채움/누락은 0
        v = el.get(k) or {}
        return int(v.get("depth", 0)) if v.get("filled") else 0
    def filled(k):
        v = el.get(k) or {}
        return bool(v.get("filled"))

    expected = DAILY_REQUIRED + DAILY_OPTIONAL
    cov_n = sum(1 for k in expected if filled(k))
    coverage = cov_n / len(expected)
    filled_all = [k for k in el if filled(k)]
    depth_avg = (sum(d(k) for k in filled_all) / len(filled_all)) if filled_all else 0.0
    resolution = round(coverage * (depth_avg / 3) * 100)  # 0~100
    glob = round(depth_avg)  # 전역 깊이 렌즈(clarity/structure/evidence)
    return {
        "status": "scored", "resolution": resolution,
        "coverage": round(coverage * 100), "depth_avg": round(depth_avg, 1),
        "metrics": {"clarity": glob, "structure": glob, "evidence": glob,
                    "output_quality": d("output"), "outcome_quality": d("outcome"),
                    "decision_thinking": d("decision")},
    }


def aggregate_person(name: str, recs: list[dict]) -> dict:
    vol, comp = _completion(recs)
    return {
        "name": name, "team": team_of(name),
        "task_count": vol,
        "completion_rate": comp,
        "categories": _categories(recs),
        "blockers": _blockers(recs),
        "tools": _tools(recs),
        "open_decisions": _open_decisions(recs),
        "growth": compute_growth(recs),
    }


def aggregate_team(team: str, recs: list[dict], members: list[str]) -> dict:
    vol, comp = _completion(recs)
    # 공통 블로커: 2명 이상 언급
    by_person_blockers = defaultdict(set)
    for r in recs:
        for v in (r["blocker"], r["issue"]):
            v = (v or "").strip()
            if v and v not in ("없음", "-"):
                by_person_blockers[v[:15]].add(r["name"])
    common = [(v, len(ppl)) for v, ppl in by_person_blockers.items() if len(ppl) >= 2]
    common.sort(key=lambda x: -x[1])
    active = sorted({r["name"] for r in recs if r["source"] in WORK_SRC})
    return {
        "team": team, "members": members, "active_members": active,
        "task_count": vol, "per_capita": round(vol / max(len(active), 1), 1),
        "completion_rate": comp,
        "categories": _categories(recs),
        "common_blockers": common[:4],
        "tools": _tools(recs),
    }


# ─── 주차 계산 ───
def week_range(spec: str) -> tuple[date, date]:
    if spec in ("last", "", None):
        today = datetime.now().date()
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(days=7)
        return last_monday, last_monday + timedelta(days=6)
    base = datetime.strptime(spec, "%Y-%m-%d").date()
    mon = base - timedelta(days=base.weekday())
    return mon, mon + timedelta(days=6)


def build_dashboard_data(week_start: date, week_end: date) -> dict:
    daily = fetch_daily()
    basket = fetch_basket()
    records = normalize_daily(daily) + normalize_basket(basket)
    # 주간 필터
    ws, we = week_start.isoformat(), week_end.isoformat()
    wk = [r for r in records if r["date"] and ws <= r["date"] <= we]

    # 미매칭 이름 가시화
    unmatched = sorted({r["name"] for r in wk if r["name"] not in BY_NAME})

    by_person = defaultdict(list)
    by_team = defaultdict(list)
    for r in wk:
        by_person[r["name"]].append(r)
        by_team[r["team"]].append(r)

    persons = [aggregate_person(n, rs) for n, rs in by_person.items()]
    persons.sort(key=lambda p: (TEAM_ORDER.index(p["team"]) if p["team"] in TEAM_ORDER else 99, -p["task_count"]))

    # 팀 멤버(명부 기준)
    team_members = defaultdict(list)
    for nm, e in BY_NAME.items():
        team_members[e.get("team") or "미지정"].append(nm)
    teams = []
    for t in sorted(by_team, key=lambda x: TEAM_ORDER.index(x) if x in TEAM_ORDER else 99):
        teams.append(aggregate_team(t, by_team[t], team_members.get(t, [])))

    _, avg_comp = _completion(wk)
    total_decisions = sum(len(p["open_decisions"]) for p in persons)

    # ─── 주간분장 ↔ 일일보고 교차 매칭 ───
    assignments = fetch_assignments(week_start, week_end)
    if assignments:
        assignments = match_assignments_to_daily(assignments, wk)
        updated = update_assignment_status_in_sheet(assignments)
        if updated:
            sys.stderr.write(f"[assign] {updated}건 상태 업데이트\n")
    # 팀별 분장 달성률 계산
    assign_by_team = defaultdict(list)
    for a in assignments:
        assign_by_team[a["team"]].append(a)
    for t in teams:
        t_assigns = assign_by_team.get(t["team"], [])
        if t_assigns:
            done = sum(1 for a in t_assigns if a["status"] in ("완료", "승인"))
            t["assignment_total"] = len(t_assigns)
            t["assignment_done"] = done
            t["assignment_rate"] = round(done / len(t_assigns) * 100)
        else:
            t["assignment_total"] = 0
            t["assignment_done"] = 0
            t["assignment_rate"] = None

    return {
        "week": {"start": ws, "end": we,
                 "label": f"{week_start.isocalendar().year}년 W{week_start.isocalendar().week:02d}",
                 "range": f"{week_start.strftime('%m/%d')}–{week_end.strftime('%m/%d')}"},
        "summary": {"total_reports": len([r for r in wk if r["source"] in WORK_SRC]),
                    "avg_completion": avg_comp, "active_people": len(by_person),
                    "open_decisions": total_decisions},
        "teams": teams, "persons": persons,
        "assignments": assignments,
        "unmatched_names": unmatched,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def slice_team_data(data: dict, team: str) -> dict:
    """전체 대시보드 데이터를 팀 스코프로 슬라이스(LLM 재호출 0 — 이미 계산된 결과 필터)."""
    d = copy.deepcopy(data)
    d["team"] = team
    d["teams"] = [t for t in data["teams"] if t["team"] == team]
    d["persons"] = [p for p in data["persons"] if p["team"] == team]
    d["assignments"] = [a for a in data.get("assignments", []) if a.get("team") == team]
    d["unmatched_names"] = []  # 팀 스코프 — 미매칭 경고 생략
    persons = d["persons"]
    team_obj = d["teams"][0] if d["teams"] else None
    d["summary"] = {
        "total_reports": sum(p["task_count"] for p in persons),
        "avg_completion": team_obj["completion_rate"] if team_obj else None,
        "active_people": len(persons),
        "open_decisions": sum(len(p["open_decisions"]) for p in persons),
    }
    return d


def team_leads() -> dict:
    return EMP.get("team_leads", {})


# ─── HTML 렌더 ───
def _esc(s) -> str:
    return html.escape(str(s or ""))


def _donut(cats: dict, size: int = 92) -> str:
    """카테고리 분포 inline-SVG 도넛."""
    total = sum(cats.values())
    if not total:
        return f'<div class="donut-empty" style="width:{size}px;height:{size}px">—</div>'
    r, cx, cy, sw = size / 2 - 8, size / 2, size / 2, 12
    circ = 2 * 3.14159 * r
    off = 0.0
    segs = []
    for i, (cat, n) in enumerate(cats.items()):
        frac = n / total
        dash = frac * circ
        col = PALETTE[i % len(PALETTE)]
        segs.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{col}" '
            f'stroke-width="{sw}" stroke-dasharray="{dash:.1f} {circ - dash:.1f}" '
            f'stroke-dashoffset="{-off:.1f}" transform="rotate(-90 {cx} {cy})"/>')
        off += dash
    leg = " ".join(
        f'<span class="lg"><i style="background:{PALETTE[i % len(PALETTE)]}"></i>{_esc(c)} {n}</span>'
        for i, (c, n) in enumerate(cats.items()))
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{"".join(segs)}'
            f'<text x="{cx}" y="{cy+5}" text-anchor="middle" class="donut-c">{total}</text></svg>'
            f'<div class="legend">{leg}</div>')


def _comp_bar(pct) -> str:
    if pct is None:
        return '<div class="bar"><span class="bar-na">측정안함(N/A)</span></div>'
    col = "var(--green)" if pct >= 70 else ("var(--amber)" if pct >= 40 else "var(--red)")
    return (f'<div class="bar"><div class="bar-fill" style="width:{pct}%;background:{col}"></div>'
            f'<span class="bar-lbl">{pct}%</span></div>')


def _growth_gauges(g: dict) -> str:
    labels = {"clarity": "명확성", "evidence": "근거", "structure": "구조",
              "output_quality": "산출물", "outcome_quality": "의미", "decision_thinking": "의사결정"}
    cells = []
    for k, lab in labels.items():
        v = g["metrics"].get(k)
        if v is None:
            cells.append(f'<div class="gz gz-na"><b>—</b><small>{lab}</small></div>')
        else:
            cells.append(f'<div class="gz"><b>{v}</b><small>{lab}</small></div>')
    if g.get("status") == "scored":
        res = g.get("resolution", 0)
        col = "var(--green)" if res >= 60 else ("var(--amber)" if res >= 35 else "var(--red)")
        head = (f'ARISA 사고 해상도 '
                f'<span class="reso" style="color:{col}">{res}%</span>'
                f'<span class="reso-sub">커버리지 {g.get("coverage",0)}% · 깊이 {g.get("depth_avg",0)}/3</span>')
    else:
        head = 'ARISA 성장지표 <span class="collecting">수집 중</span>'
    return f'<div class="growth"><div class="growth-h">{head}</div><div class="gauges">{"".join(cells)}</div></div>'


def _chips(items, cls="chip") -> str:
    return "".join(f'<span class="{cls}">{_esc(i)}</span>' for i in items) or '<span class="muted">—</span>'


def render_html(data: dict) -> str:
    w = data["week"]; s = data["summary"]
    # 대표 전체 주간 vs 팀 리더 주간 분기 (data["team"] 유무)
    team = data.get("team")
    is_team = bool(team)
    TITLE = f"{team} 팀 주간 · {w['label']}" if is_team else f"주간 업무 대시보드 · {w['label']}"
    H1 = f"{_esc(team)} 팀 주간 대시보드" if is_team else "주간 업무 대시보드"
    GATE_H2 = f"{_esc(team)} 팀 주간" if is_team else "주간 업무 대시보드"
    GATE_SUB = f'{_esc(w["label"])} · {_esc(team)} 팀 리더' if is_team else f'{_esc(w["label"])} · 로그인'
    SESS_KEY = "team_weekly_sess" if is_team else "weekly_sess"
    TEAM_JS = json.dumps(team or "", ensure_ascii=False)
    if is_team:
        JS_CAN = "(d.admin || (d.lead_teams||[]).indexOf(TEAM)>=0)"
        JS_SESS_CAN = "(sess.admin || (sess.lead_teams||[]).indexOf(TEAM)>=0)"
        JS_GROWTH = "(s.admin || (s.lead_teams||[]).indexOf(TEAM)>=0)"
        JS_DENY = "이 팀 리더 전용 화면입니다"
    else:
        JS_CAN = "d.ok"
        JS_SESS_CAN = "sess.name"
        JS_GROWTH = "s.admin"
        JS_DENY = "로그인 실패"
    # 파트 카드
    team_cards = []
    for t in data["teams"]:
        comp = "N/A" if t["completion_rate"] is None else f'{t["completion_rate"]}%'
        cb = "".join(f'<span class="badge badge-amber">{_esc(v)} ·{n}명</span>'
                     for v, n in t["common_blockers"]) or '<span class="muted">공통 블로커 없음</span>'
        # 분장 달성률 게이지
        assign_row = ""
        if t.get("assignment_total", 0) > 0:
            ar = t["assignment_rate"]
            assign_row = f'<div class="row"><span class="k">분장 달성</span>{_comp_bar(ar)}<span class="muted" style="margin-left:8px">{t["assignment_done"]}/{t["assignment_total"]}</span></div>'
        team_cards.append(f'''
        <div class="card team-card">
          <div class="card-h"><h3>{_esc(t["team"])}</h3><span class="muted">{len(t["active_members"])}명 활성 · {t["task_count"]}건 (인당 {t["per_capita"]})</span></div>
          <div class="donut-wrap">{_donut(t["categories"])}</div>
          {assign_row}
          <div class="row"><span class="k">완료율</span>{_comp_bar(t["completion_rate"])}</div>
          <div class="row"><span class="k">공통 블로커</span><div class="vals">{cb}</div></div>
          <div class="row"><span class="k">도구</span><div class="vals">{_chips(t["tools"])}</div></div>
        </div>''')

    # 개인 카드
    person_cards = []
    for p in data["persons"]:
        dec = "".join(f'<li>{_esc(d)}</li>' for d in p["open_decisions"]) or '<li class="muted">없음</li>'
        blk = "".join(f'<span class="badge badge-amber">{_esc(b)}</span>' for b in p["blockers"]) or '<span class="muted">—</span>'
        person_cards.append(f'''
        <div class="card person-card">
          <div class="card-h"><h3>{_esc(p["name"])} <span class="team-tag">{_esc(p["team"])}</span></h3><span class="muted">{p["task_count"]}건</span></div>
          <div class="donut-wrap">{_donut(p["categories"])}</div>
          <div class="row"><span class="k">완료율</span>{_comp_bar(p["completion_rate"])}</div>
          <div class="row"><span class="k">도구</span><div class="vals">{_chips(p["tools"])}</div></div>
          <div class="row"><span class="k">반복 블로커</span><div class="vals">{blk}</div></div>
          <div class="row"><span class="k">미해결 의사결정</span><ul class="dec">{dec}</ul></div>
          {_growth_gauges(p["growth"])}
        </div>''')

    unmatched = ""
    if data["unmatched_names"]:
        unmatched = f'<div class="warn">⚠️ 명부 미매칭 이름: {_esc(", ".join(data["unmatched_names"]))} (집계엔 포함됨 — 명부 등록 권장)</div>'

    avg = "N/A" if s["avg_completion"] is None else f'{s["avg_completion"]}%'
    return f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(TITLE)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>
:root{{--bg:#1A1A1A;--bg-2:#202020;--bg-3:#262626;--fg:#F5F0EB;--muted:#8A857E;--line:#333;
--accent:#6C5CE7;--green:#8FA37E;--amber:#D9A34B;--red:#E17055}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--fg);font-family:'Pretendard Variable',sans-serif;
font-weight:300;line-height:1.5;padding:32px 20px 64px}}
.wrap{{max-width:1100px;margin:0 auto}}
header{{margin-bottom:24px}}
header h1{{font-weight:600;font-size:26px;letter-spacing:-.02em}}
header .sub{{color:var(--muted);margin-top:4px;font-size:14px}}
.statbar{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0 32px}}
.stat{{background:var(--bg-2);border:1px solid var(--line);border-radius:10px;padding:16px}}
.stat b{{font-size:28px;font-weight:600;color:var(--accent)}}
.stat small{{display:block;color:var(--muted);font-size:12px;margin-top:4px}}
h2.sec{{font-size:14px;font-weight:600;color:var(--muted);text-transform:uppercase;
letter-spacing:.08em;margin:32px 0 14px;border-bottom:1px solid var(--line);padding-bottom:8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:14px}}
.card{{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:18px}}
.card-h{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:12px}}
.card-h h3{{font-size:16px;font-weight:600}}
.team-tag{{font-size:11px;color:var(--accent);font-weight:400;margin-left:4px}}
.muted{{color:var(--muted);font-size:12px}}
.donut-wrap{{display:flex;align-items:center;gap:14px;margin-bottom:12px}}
.donut-c{{fill:var(--fg);font-size:18px;font-weight:600}}
.donut-empty{{display:flex;align-items:center;justify-content:center;color:var(--muted);border:2px dashed var(--line);border-radius:50%}}
.legend{{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:11px;color:var(--muted)}}
.lg i{{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:4px;vertical-align:middle}}
.row{{display:flex;gap:10px;margin:8px 0;font-size:13px;align-items:flex-start}}
.row .k{{color:var(--muted);min-width:80px;flex-shrink:0;font-size:12px;padding-top:2px}}
.vals{{display:flex;flex-wrap:wrap;gap:4px}}
.bar{{flex:1;background:var(--bg-3);border-radius:6px;height:18px;position:relative;overflow:hidden}}
.bar-fill{{height:100%;border-radius:6px}}
.bar-lbl{{position:absolute;right:8px;top:0;font-size:11px;line-height:18px}}
.bar-na{{font-size:11px;color:var(--muted);line-height:18px;padding-left:8px}}
.chip{{background:var(--bg-3);border:1px solid var(--line);border-radius:6px;padding:2px 8px;font-size:12px}}
.badge{{border-radius:6px;padding:2px 8px;font-size:12px}}
.badge-amber{{background:rgba(217,163,75,.15);color:var(--amber);border:1px solid rgba(217,163,75,.3)}}
.dec{{list-style:none;flex:1}}
.dec li{{font-size:12px;padding:3px 0;border-bottom:1px solid var(--line)}}
.dec li:last-child{{border:0}}
.growth{{margin-top:14px;padding-top:12px;border-top:1px solid var(--line)}}
.growth-h{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px}}
.collecting{{color:var(--accent);background:rgba(108,92,231,.12);border-radius:4px;padding:1px 6px;font-size:10px}}
.reso{{font-weight:600;font-size:15px;margin-left:6px}}
.reso-sub{{display:block;font-size:10px;color:var(--muted);margin-top:3px;letter-spacing:0}}
.gauges{{display:grid;grid-template-columns:repeat(6,1fr);gap:6px}}
.gz{{background:var(--bg-3);border-radius:8px;padding:8px 4px;text-align:center}}
.gz b{{font-size:16px;font-weight:600;color:var(--accent)}}
.gz small{{display:block;font-size:9px;color:var(--muted);margin-top:2px}}
.gz-na b{{color:var(--line)}}
.warn{{background:rgba(217,163,75,.1);border:1px solid rgba(217,163,75,.3);color:var(--amber);
border-radius:8px;padding:10px 14px;font-size:13px;margin:16px 0}}
footer{{margin-top:40px;color:var(--muted);font-size:11px;text-align:center;border-top:1px solid var(--line);padding-top:16px}}
/* 성장지표는 대표(admin)만 — 직원 로그인 시 숨김(측정설계 v2) */
.growth{{display:none}}
body.is-admin .growth{{display:block}}
/* 로그인 게이트 */
#login-gate{{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:100}}
#login-box{{background:var(--bg-2);border:1px solid var(--line);border-radius:14px;padding:38px 40px;width:330px;text-align:center}}
#login-box h2{{font-size:19px;font-weight:600;margin-bottom:6px}}
#login-box .lg-sub{{color:var(--muted);font-size:13px;margin-bottom:22px}}
#login-box input{{width:100%;background:var(--bg-3);border:1px solid var(--line);border-radius:8px;padding:12px 14px;color:var(--fg);font-size:14px;margin-bottom:10px;font-family:inherit}}
#login-box button{{width:100%;background:var(--accent);color:#fff;border:0;border-radius:8px;padding:12px;font-size:14px;font-weight:600;cursor:pointer;margin-top:6px}}
#login-err{{color:var(--red);font-size:12px;margin-top:12px;min-height:16px}}
#whoami{{position:fixed;top:14px;right:18px;font-size:12px;color:var(--muted);z-index:50}}
#whoami a{{color:var(--accent);cursor:pointer;margin-left:8px}}
</style></head>
<body>
<div id="login-gate">
  <div id="login-box">
    <h2>{GATE_H2}</h2>
    <div class="lg-sub">{GATE_SUB}</div>
    <input id="lg-id" placeholder="이름 (예: 최원석)" autocomplete="username">
    <input id="lg-pin" type="password" placeholder="PIN" autocomplete="current-password">
    <button id="lg-btn">로그인</button>
    <div id="login-err"></div>
  </div>
</div>
<div id="whoami" style="display:none"></div>
<div id="content" style="display:none"><div class="wrap">
<header><h1>{H1}</h1><div class="sub">{_esc(w["label"])} · {_esc(w["range"])}</div></header>
{unmatched}
<div class="statbar">
  <div class="stat"><b>{s["total_reports"]}</b><small>총 보고 건수</small></div>
  <div class="stat"><b>{avg}</b><small>평균 완료율</small></div>
  <div class="stat"><b>{s["active_people"]}</b><small>활성 인원</small></div>
  <div class="stat"><b>{s["open_decisions"]}</b><small>미해결 의사결정</small></div>
</div>
<h2 class="sec">파트별</h2><div class="grid">{"".join(team_cards)}</div>
<h2 class="sec">개인별</h2><div class="grid">{"".join(person_cards)}</div>
<footer>Generated by weekly-report-aggregate.py · {_esc(data["generated_at"])} · by Project Rent</footer>
</div></div>
<script>
(function(){{
  var TEAM={TEAM_JS};
  var gate=document.getElementById('login-gate'), content=document.getElementById('content'), who=document.getElementById('whoami');
  function enter(s){{
    gate.style.display='none'; content.style.display='block';
    who.style.display='block';
    var growth=({JS_GROWTH});
    who.innerHTML = s.name+' ('+(s.role||'')+')'+(growth?' · 성장지표 ON':'')+' <a id="lg-out">로그아웃</a>';
    if(growth) document.body.classList.add('is-admin');
    document.getElementById('lg-out').onclick=function(){{ localStorage.removeItem('{SESS_KEY}'); location.reload(); }};
  }}
  var sess=null; try{{ sess=JSON.parse(localStorage.getItem('{SESS_KEY}')||'null'); }}catch(e){{}}
  if(sess && {JS_SESS_CAN}) enter(sess);
  function doLogin(){{
    var id=document.getElementById('lg-id').value.trim(), pin=document.getElementById('lg-pin').value.trim();
    var err=document.getElementById('login-err'); err.textContent='';
    fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{id:id,pin:pin}})}})
      .then(function(r){{return r.json();}})
      .then(function(d){{
        if(d.ok && {JS_CAN}){{ localStorage.setItem('{SESS_KEY}',JSON.stringify(d)); enter(d); }}
        else if(d.ok){{ err.textContent='{JS_DENY}'; }}
        else {{ err.textContent=d.error||'로그인 실패'; }}
      }})
      .catch(function(){{ err.textContent='서버 연결 실패 (대시보드 서버 경유로 열어주세요)'; }});
  }}
  document.getElementById('lg-btn').onclick=doLogin;
  document.getElementById('lg-pin').addEventListener('keydown',function(e){{ if(e.key==='Enter') doLogin(); }});
}})();
</script>
</body></html>'''


# ─── 저장/알림 ───
def save_and_notify(data: dict, do_open: bool, no_telegram: bool) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    w = data["week"]
    yw = f'{datetime.strptime(w["start"], "%Y-%m-%d").isocalendar().year}-W{datetime.strptime(w["start"], "%Y-%m-%d").isocalendar().week:02d}'
    html_path = OUT_DIR / f"weekly-report-{yw}.html"
    json_path = OUT_DIR / f"weekly-data-{yw}.json"
    html_path.write_text(render_html(data), encoding="utf-8")
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ HTML: {html_path}")
    print(f"✅ JSON: {json_path}")
    if do_open:
        subprocess.run(["open", str(html_path)], check=False)
    if not no_telegram and MANAGER_BOT_TOKEN and MANAGER_CHAT_ID:
        _telegram_summary(data, html_path)
    return html_path


def _telegram_summary(data: dict, html_path: Path):
    s = data["summary"]; w = data["week"]
    top_blockers = []
    for t in data["teams"]:
        for v, n in t["common_blockers"]:
            top_blockers.append(f"{t['team']}: {v}")
    avg = "N/A" if s["avg_completion"] is None else f'{s["avg_completion"]}%'
    msg = (f"📊 주간 업무 대시보드 {w['label']} ({w['range']})\n\n"
           f"• 총 보고 {s['total_reports']}건 · 평균 완료율 {avg}\n"
           f"• 활성 {s['active_people']}명 · 미해결 의사결정 {s['open_decisions']}건\n")
    if top_blockers:
        msg += "\n🔔 공통 블로커\n" + "\n".join(f"– {b}" for b in top_blockers[:3])
    # 폰에서 열리는 원격 URL — 고정 URL은 .env DASHBOARD_BASE_URL로 관리
    msg += f"\n\n📄 {DASHBOARD_BASE_URL}/dashboard"
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{MANAGER_BOT_TOKEN}/sendMessage"
        body = json.dumps({"chat_id": MANAGER_CHAT_ID, "text": msg}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20)
        print("✅ 텔레그램 요약 전송")
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 실패: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", default="last", help="'last' 또는 YYYY-MM-DD(그 주)")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--no-telegram", action="store_true")
    args = ap.parse_args()
    ws, we = week_range(args.week)
    print(f"주간 범위: {ws} ~ {we}")

    # 가드: 시트 접근 사전 프로브 — gws 인증 장애 시 '빈 주간리포트'를 조용히 발송하는 것 방지
    # (메타 A1은 헤더라 항상 존재. []면 읽기 실패로 간주 — 07-03 invalid_rapt 사고 참조)
    if not _gws.values_get(DAILY_SHEET, "메타!A1:A1", retries=2):
        alert = ("⚠️ 주간리포트 생성 중단\n"
                 "구글시트 읽기 실패(gws 인증 장애 의심) — 빈 리포트 발송을 막았습니다.\n"
                 "→ 서버에서 `gws auth login --services drive,sheets,gmail,calendar,docs,slides,tasks` 재인증 후 수동 재실행: "
                 "python weekly-report-aggregate.py --week last")
        print(alert)
        if not args.no_telegram and MANAGER_BOT_TOKEN and MANAGER_CHAT_ID:
            try:
                import urllib.request
                _req = urllib.request.Request(
                    f"https://api.telegram.org/bot{MANAGER_BOT_TOKEN}/sendMessage",
                    data=json.dumps({"chat_id": MANAGER_CHAT_ID, "text": alert}).encode(),
                    headers={"Content-Type": "application/json"})
                urllib.request.urlopen(_req, timeout=20)
            except Exception as e:  # noqa: BLE001
                print(f"⚠️ 알림 발송 실패: {e}")
        sys.exit(1)

    data = build_dashboard_data(ws, we)
    print(f"집계: {data['summary']['total_reports']}건 · {data['summary']['active_people']}명 "
          f"· 미매칭 {len(data['unmatched_names'])}")
    save_and_notify(data, args.open, args.no_telegram)

    # ─── 팀별 주간(리더용) — slice_team_data로 LLM 재호출 0 ───
    w = data["week"]
    _dt = datetime.strptime(w["start"], "%Y-%m-%d")
    yw = f'{_dt.isocalendar().year}-W{_dt.isocalendar().week:02d}'
    for team in team_leads():
        tdata = slice_team_data(data, team)
        tpath = OUT_DIR / f"weekly-report-{yw}-{team}.html"
        tpath.write_text(render_html(tdata), encoding="utf-8")
        print(f"✅ [{team}] {tpath.name} (인원 {tdata['summary']['active_people']}, 보고 {tdata['summary']['total_reports']})")


if __name__ == "__main__":
    main()
