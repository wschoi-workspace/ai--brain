#!/usr/bin/env python3
"""ARISA 2.0 MVP3 — 대표 Daily Executive Brief.

직원들의 '오늘' 보고 전체를 Engine D(Decision Engine, LLM)로 읽어, 대표가 한 화면에서
"오늘 봐야 할 것 TOP 5"(Decision/Intervention/Project/Growth/Risk)를 보게 한다.
대표 본질: "보고를 보고 싶은 게 아니라 조직을 보고 싶다."

fidelity: 보고 원문(raw)·이슈·블로커·outcome·basket결재에 실제 근거가 있는 것만 추출.
추측 금지(근거 없으면 항목 안 만듦). decision_needed 필드가 비어도 raw에서 추출.

런타임: .venv311 (gws subprocess). 사용:
  python daily-brief-aggregate.py [--date YYYY-MM-DD] [--open] [--no-telegram]
"""
from __future__ import annotations

import os
import re
import sys
import json
import html
import argparse
import subprocess
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

# ─── 경로/설정 (weekly-report-aggregate.py와 동일 패턴) ───
SCRIPTS = Path(__file__).resolve().parent
WORKSPACE = SCRIPTS.parent.parent
EMP_PATH = SCRIPTS / "arisa-employees.json"
OUT_DIR = WORKSPACE / "20-operations" / "23-arisa" / "brief"
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
# 팀 리더 알림은 직원봇으로 발신(리더는 직원봇에 연결됨 — 관리자봇 미접속).
LEADER_BOT_TOKEN = os.environ.get("DAILY_REPORT_BOT_TOKEN", "")
# 링크 URL은 .env의 DASHBOARD_BASE_URL이 우선. 기본값은 tailnet(대표 기기 전용) —
# 리더는 tailnet 밖이라 named tunnel 고정 도메인 완성 시 .env 한 줄로 교체(cloudflare-migration-checklist.md).
# (구 trycloudflare quick tunnel URL은 2026-07-08 사망 확인 — 링크 미작동 장애 원인)
DASHBOARD_BASE_URL = os.environ.get("DASHBOARD_BASE_URL", "https://server-mini-macmini.tail7739de.ts.net")

TEAM_ORDER = ["경영", "사업기획", "공간팀", "기획팀", "운영팀", "감사"]
NAME_ALIASES = {
    "yang eun jung": "양은정", "yangeunjung": "양은정", "eun jung": "양은정",
    "준호 김": "김준호", "김 준호": "김준호", "bro callme": "최원석",
}
# basket 항목 컬럼(D~N) → 라벨 (결재성 항목이 Decision 후보)
BASKET_FIELDS = [
    (3, "매출"), (4, "지출"), (5, "송금·승인"), (6, "특이사항"), (7, "장비"),
    (8, "업무보고"), (9, "대관"), (10, "스태프"), (11, "구매"), (12, "입점제안"), (13, "복기"),
]
BASKET_DECISION = {"송금·승인", "장비", "입점제안"}  # 결재성 → Decision 1급 후보

# 범주 메타: (라벨, 색) — Daily Report 2.0 §9 대표 브리프 체계
# (진척=project / 지연·리스크=risk / 결정=decision / 지원=support / 이상신호=anomaly
#  + 기존 intervention(개입)·growth(성장신호) 유지)
CAT_META = {
    "decision":     ("Decision · 결정",   "var(--accent)"),
    "intervention": ("Intervention · 개입", "var(--amber)"),
    "risk":         ("Risk · 리스크",     "var(--red)"),
    "support":      ("Support · 지원 요청", "#C08BC9"),
    "project":      ("Project · 진행",    "var(--blue)"),
    "growth":       ("Growth · 성장신호",  "var(--green)"),
    "anomaly":      ("Signal · 이상 신호", "var(--muted)"),
}
CAT_ORDER = ["decision", "intervention", "risk", "support", "project", "growth", "anomaly"]
URG_RANK = {"high": 0, "mid": 1, "low": 2}


# ─── 명부·정규화·gws (shared 코어 위임 — Phase 1) ───
sys.path.insert(0, str(SCRIPTS))
from shared.employee import load_employees as _load_emp
from shared import normalize as _N, gws as _gws
from shared.decision import load_open_decisions as _load_open_decisions


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


# ─── 오늘 데이터 수집 (직원별 보고 블록) ───
def prev_bizday_range(date_str: str) -> list[str]:
    """브리프 날짜의 소스 보고일 = 직전 영업일~어제 전부.
    직원은 당일 저녁(20~22시 리마인드)에 보고하므로, 아침 브리프는 전날 보고를 읽어야 한다.
    화~토 브리프 → 어제 하루. 월 브리프 → 금+토+일 (주말 보고 포함)."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    out, prev = [], d - timedelta(days=1)
    while True:
        out.append(prev.strftime("%Y-%m-%d"))
        if prev.weekday() < 5:  # 평일(직전 영업일)을 만나면 중단
            break
        prev -= timedelta(days=1)
    return out


def fetch_day(target: str | list[str]) -> dict:
    """target(YYYY-MM-DD 또는 날짜 리스트)에 해당하는 직원별 보고 블록을 모은다.
    반환: {name: {team, raw, core:[{output,issue,outcome,task,blocker}], meta:{decision,support,blocker,question}, basket:[(label,val)]}}"""
    targets = {target} if isinstance(target, str) else set(target)
    core = _gws_values_get(DAILY_SHEET, "핵심업무!A2:L5000")
    meta = _gws_values_get(DAILY_SHEET, "메타!A2:O5000")  # N=Report Score, O=score_detail(type 포함)
    basket = _gws_values_get(BASKET_SHEET, "일일보고!A2:O5000")
    by = defaultdict(lambda: {"team": "", "raw": "", "core": [], "meta": {}, "basket": []})

    for r in core:
        r = r + [""] * (12 - len(r))
        if normalize_date(r[0]) not in targets:
            continue
        nm = normalize_name(r[1])
        if not nm:
            continue
        by[nm]["team"] = team_of(nm)
        by[nm]["core"].append({"task": r[5], "output": r[9], "issue": r[10], "outcome": r[11]})

    for r in meta:
        r = r + [""] * (15 - len(r))
        if normalize_date(r[0]) not in targets:
            continue
        nm = normalize_name(r[1])
        if not nm:
            continue
        by[nm]["team"] = team_of(nm)
        by[nm]["raw"] = r[10]
        by[nm]["meta"] = {"blocker": r[5], "decision": r[7], "support": r[8],
                          "reflection": r[9], "question": r[11]}
        # 2.0 Wave 2: Report Score(N) + score_detail(O)의 type — 브리프 개인카드 표기용
        by[nm]["score"] = (r[13] or "").strip()
        try:
            by[nm]["rtype"] = (json.loads(r[14]).get("type") or "").strip() if (r[14] or "").strip() else ""
        except Exception:
            by[nm]["rtype"] = ""

    for r in basket:
        r = r + [""] * (15 - len(r))
        if normalize_date(r[1]) not in targets:
            continue
        nm = normalize_name(r[2])
        if not nm:
            continue
        if not BY_NAME.get(nm):
            by[nm]["team"] = "운영팀"
        else:
            by[nm]["team"] = team_of(nm)
        for idx, label in BASKET_FIELDS:
            v = (r[idx] or "").strip()
            if v:
                by[nm]["basket"].append((label, v))
    return dict(by)


def _emp_block(name: str, d: dict) -> str:
    """한 직원의 오늘 보고를 LLM 입력용 텍스트 블록으로."""
    lines = [f"[{name} · {d['team']}]"]
    if d["raw"].strip():
        lines.append(f"보고원문(raw): {d['raw'][:1500]}")
    for c in d["core"]:
        seg = []
        if c["task"].strip(): seg.append(f"업무={c['task']}")
        if c["output"].strip(): seg.append(f"산출물={c['output']}")
        if c["issue"].strip(): seg.append(f"이슈={c['issue']}")
        if c["outcome"].strip(): seg.append(f"의미={c['outcome']}")
        if seg:
            lines.append("  핵심업무: " + " / ".join(seg))
    m = d["meta"]
    if m.get("blocker", "").strip(): lines.append(f"  블로커: {m['blocker']}")
    if m.get("decision", "").strip(): lines.append(f"  명시적 의사결정요청: {m['decision']}")
    if m.get("support", "").strip(): lines.append(f"  지원요청: {m['support']}")
    if m.get("question", "").strip(): lines.append(f"  오늘의질문: {m['question']}")
    # 봇이 채점한 보고유형·점수 — anomaly(활동만 나열·낮은 품질) 판단 보조 신호
    if (d.get("rtype") or d.get("score")):
        lines.append(f"  보고유형: {d.get('rtype') or '?'} · ReportScore: {d.get('score') or '?'}")
    for label, v in d["basket"]:
        tag = "[결재]" if label in BASKET_DECISION else ""
        lines.append(f"  basket {tag}{label}: {v[:200]}")
    return "\n".join(lines)


# ─── Engine D — Decision Engine (LLM) ───
BRIEF_PROMPT = """너는 ARISA Engine D — Decision Engine이다. 대표(최원석)가 "오늘 봐야 할 것"만
보도록, 직원들의 오늘 보고 전체에서 의사결정·개입·리스크·프로젝트상태·성장신호를 추출·분류·정렬한다.
대표의 본질: "보고를 보고 싶은 게 아니라 조직을 보고 싶다."

[엄격 규칙 — fidelity (최우선)]
- 보고 원문(raw)·이슈·블로커·outcome·basket결재에 실제 근거가 있는 것만 추출.
- 추측·창작 금지. 근거 없으면 항목을 만들지 않는다(빈 배열 허용).
- 직원이 의사결정요청을 비워뒀어도, 원문에 "결정이 필요한 갈림길/막힌 지점/승인 대기"가
  보이면 추출한다. 단 원문 표현을 넘는 단정 금지.
- source_employee·project는 반드시 근거 보고에서 귀속. 모르면 project=null.

[7범주]
- decision : 대표/팀장이 선택·승인해야 할 갈림길. basket의 [결재]송금·승인/장비/입점은 결재 의사결정.
- intervention : 대표가 개입(코칭/방향제시/조율)해야 할 지점. 직원이 헤매거나 방향이 어긋난 신호.
- risk : 놓치면 손실·지연·관계훼손이 되는 위험. 외부·금전·기한 결부된 블로커.
- support : 직원이 명시적으로 요청한 지원(정보 확인/외부 커뮤니케이션/일정 조정/인력/예산/전문 검토).
  intervention(대표의 판단·코칭 필요)과 구분 — support는 직원이 무엇이 필요한지 아는 상태.
- project : 프로젝트 진행상태 변화(완료/지연/전환). outcome 기반.
- growth : 직원 사고가 또렷해진/약했던 신호(좋은 질문, 의미연결, 반복 약점). 오늘의질문 활용.
- anomaly : 이상 신호 — ①결과 없이 활동만 나열된 보고 ②서로 다른 보고 간 내용 충돌
  ③특정 담당자에게 업무 과다 집중 ④리스크·결정 항목이 있어 보이는데 "없음"으로만 채워진 보고.
  오늘 보고 범위에서 보이는 것만. 근거 없이 만들지 마라.

[urgency] high=오늘 안 보면 손실/기한 / mid=이번 주 / low=인지만

[decision 항목 구조 (§9-3)] decision 항목에는 보고에 근거가 있을 때만 다음을 채워라(없으면 ""):
  recommendation=담당자의 추천안, deadline=결정이 필요한 기한, delay_impact=미결정 시 영향

반드시 아래 JSON만 출력:
{"headline":"오늘 이 조직/팀이 가장 주목해야 할 핵심을 한 문장으로(의사결정·리스크 우선). 근거 없으면 빈 문자열.",
 "items":[{"category":"decision|intervention|risk|support|project|growth|anomaly",
  "title":"대표가 30초에 읽는 한 줄 요약",
  "detail":"무엇을 결정/개입/주시해야 하나 (구체)",
  "urgency":"high|mid|low",
  "source_employee":"근거 보고 직원명",
  "project":"프로젝트명 또는 null",
  "related":"근거가 된 산출물/이슈 한 줄",
  "recommendation":"", "deadline":"", "delay_impact":""}]}"""


def engine_d(blocks: list[str]) -> dict:
    """LLM 5범주 추출 + 오늘 핵심 한줄(headline). 반환 {"items":[...], "headline":str}."""
    empty = {"items": [], "headline": ""}
    if not blocks:
        return empty
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return empty
    text = "\n\n".join(blocks)[:12000]
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini", temperature=0.1,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": BRIEF_PROMPT},
                      {"role": "user", "content": f"[오늘 직원 보고 전체]\n{text}"}],
        )
        result = json.loads(resp.choices[0].message.content or "{}")
        headline = (result.get("headline") or "").strip()
        # 정규화·검증
        out = []
        for it in result.get("items", []):
            cat = (it.get("category") or "").strip()
            if cat not in CAT_META:
                continue
            out.append({
                "category": cat,
                "title": (it.get("title") or "").strip(),
                "detail": (it.get("detail") or "").strip(),
                "urgency": it.get("urgency") if it.get("urgency") in URG_RANK else "mid",
                "source_employee": (it.get("source_employee") or "").strip(),
                "project": (it.get("project") or "").strip() or None,
                "related": (it.get("related") or "").strip(),
                # §9-3: 결정 요청 구조 (근거 있을 때만 LLM이 채움)
                "recommendation": (it.get("recommendation") or "").strip(),
                "deadline": (it.get("deadline") or "").strip(),
                "delay_impact": (it.get("delay_impact") or "").strip(),
            })
        return {"items": out, "headline": headline}
    except Exception as e:
        sys.stderr.write(f"[engine_d err] {e}\n")
        return empty


def _decision_summary(items: list[dict]) -> list[dict]:
    """상단 요약존용 — decision·intervention 항목을 urgency순으로 정렬."""
    ds = [it for it in items if it["category"] in ("decision", "intervention")]
    return sorted(ds, key=lambda x: URG_RANK.get(x["urgency"], 1))


def pick_top5(items: list[dict]) -> list[dict]:
    """5범주에서 각 1순위(urgency 높은 것) 우선 채우고, 빈 범주는 남은 high로 메움."""
    by_cat = defaultdict(list)
    for it in items:
        by_cat[it["category"]].append(it)
    for c in by_cat:
        by_cat[c].sort(key=lambda x: URG_RANK.get(x["urgency"], 1))
    top, used = [], set()
    for c in CAT_ORDER:
        if by_cat[c]:
            top.append(by_cat[c][0]); used.add(id(by_cat[c][0]))
    if len(top) < 5:
        rest = sorted([it for it in items if id(it) not in used],
                      key=lambda x: URG_RANK.get(x["urgency"], 1))
        top += rest[:5 - len(top)]
    return top[:5]


def _carried_decision_items(target: str) -> list[dict]:
    """어제 이전의 미해결(open) 결정을 브리프 item으로 이월.

    오늘자(age 0) 결정은 engine_d가 시트에서 이미 뽑으므로 제외 → 중복 매칭 불필요.
    age≥1(어제 이전에 올라왔는데 아직 안 정해진 것)만 이월해 "어제 결정이 오늘 사라짐"을 막는다.
    urgency는 봇 축적(high/medium/low)을 브리프 체계(high/mid/low)로 매핑.
    """
    urg_map = {"high": "high", "medium": "mid", "low": "low"}
    carried = []
    for e in _load_open_decisions(today=target):
        age = e.get("age_days", 0)
        if age < 1:
            continue  # 오늘 결정은 engine_d(시트) 담당
        rel = (e.get("related_output") or "").strip()
        opts = (e.get("options") or "").strip()
        carried.append({
            "category": "decision",
            "title": (e.get("decision_needed") or "").strip(),
            "detail": f"{age}일째 미결" + (f" · {rel}" if rel else "") + (f" · 옵션: {opts}" if opts else ""),
            "urgency": urg_map.get(e.get("urgency"), "mid"),
            "source_employee": (e.get("source_employee") or "").strip(),
            "project": (e.get("project") or "").strip() or None,
            "related": rel,
            # §9-3: 봇 Wave 2가 축적한 결정 구조(decisions.jsonl) 표면화
            "recommendation": (e.get("recommendation") or "").strip(),
            "deadline": (e.get("deadline") or "").strip(),
            "delay_impact": (e.get("delay_impact") or "").strip(),
            "carried": True,
            "age_days": age,
        })
    return carried


def _weekday_kr(target: str) -> str:
    return ["월", "화", "수", "목", "금", "토", "일"][datetime.strptime(target, "%Y-%m-%d").weekday()]


def fetch_assignments(target: str) -> list[dict]:
    """주간분장 탭에서 브리프 날짜가 속한 주(월~일)의 분장 항목 fetch.
    실스키마(셸 '내 업무' AI 분장): 날짜(0)|프로젝트명(1)|팀구분(2)|담당자(3)|업무내용(4)|
    일정완료예상(5)|결과물(6)|상태(7)|이해관계자(8)|우선순위(9)"""
    try:
        rows = _gws_values_get(DAILY_SHEET, "주간분장!A2:J5000")
    except Exception:
        return []
    d = datetime.strptime(target, "%Y-%m-%d").date()
    week_start = d - timedelta(days=d.weekday())
    week_end = week_start + timedelta(days=6)
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
        if (r[7] or "").strip() == "삭제":
            continue
        items.append({
            "date": nd, "project": (r[1] or "").strip(), "team": (r[2] or "").strip(),
            "assignee": normalize_name(r[3]), "task": (r[4] or "").strip(),
            "deadline": (r[5] or "").strip(), "status": (r[7] or "미착수").strip(),
            "priority": (r[9] or "일반").strip(),
        })
    return items


def _raw_details(raw: str) -> dict:
    """보고 원문의 '[상세: 업무명] 내용' 블록을 {업무명: 상세} dict로 파싱."""
    out = {}
    for m in re.finditer(r"\[상세:\s*([^\]]+)\]\s*([^\[]+)", raw or ""):
        out[m.group(1).strip()] = " ".join(m.group(2).split())
    return out


def _people_summary(day: dict, assignments: list[dict] | None = None) -> list[dict]:
    """활성 보고자만, TEAM_ORDER→이름 순 정렬한 개인별 원문 정리(브리프 하단 써머리용).
    LLM 미경유 — 시트 원문 그대로 구조화(fidelity). 핵심업무 상세는 raw의 [상세:] 블록에서 보강.
    assignments가 있으면 담당자 매칭으로 이번주 분장 항목을 개인별로 붙인다."""
    assignments = assignments or []
    out = []
    for nm, d in day.items():
        if not (d["raw"] or d["core"] or d["basket"]):
            continue
        details = _raw_details(d["raw"])
        core = []
        for c in d["core"]:
            if not any((v or "").strip() for v in c.values()):
                continue
            c = dict(c)
            task = (c.get("task") or "").strip()
            det = details.get(task) or next(
                (v for k, v in details.items() if task and (task in k or k in task)), "")
            if det:
                c["detail"] = det
            core.append(c)
        out.append({
            "name": nm,
            "team": d["team"] or team_of(nm),
            "core": core,
            "meta": {k: v for k, v in d["meta"].items()
                     if (v or "").strip() and k != "reflection"},
            "basket": d["basket"][:6],
            "assignments": [a for a in assignments if a["assignee"] == nm],
            "score": d.get("score", ""),   # 2.0 Wave 2: Report Score
            "rtype": d.get("rtype", ""),   # 2.0 Wave 2: 보고 유형 A/B/C
        })
    out.sort(key=lambda p: (TEAM_ORDER.index(p["team"]) if p["team"] in TEAM_ORDER else 99, p["name"]))
    return out


def build_brief_data(target: str, day: dict | None = None,
                     team_datas: dict | None = None,
                     assignments: list[dict] | None = None) -> dict:
    """대표 전체 Brief. day(fetch_day 결과)를 받으면 gws 재호출을 피한다.
    team_datas({팀: build_team_brief_data 결과})를 받으면 팀별 오늘 브리프 섹션(teams)을 병합한다."""
    if day is None:
        day = fetch_day(prev_bizday_range(target))
    blocks = [_emp_block(nm, d) for nm, d in day.items()]
    res = engine_d(blocks)
    items = res["items"]
    items += _carried_decision_items(target)  # 과거 미결(open) 결정 이월 — 정해질 때까지 노출
    unmatched = sorted({nm for nm in day if nm not in BY_NAME})
    counts = {c: sum(1 for it in items if it["category"] == c) for c in CAT_META}
    people = _people_summary(day, assignments)
    # 팀별 병합 블록 — TEAM_ORDER 순, team_leads 외 팀(경영 등) 보고자는 '기타'로
    teams = []
    if team_datas:
        covered = set(team_datas)
        reporters = {p["name"] for p in people}

        def _unreported(scope_teams):
            """분장은 있는데 오늘 보고가 없는 사람 — {이름: 건수}"""
            miss = {}
            for a in (assignments or []):
                nm = a["assignee"]
                if nm and nm not in reporters and team_of(nm) in scope_teams:
                    miss[nm] = miss.get(nm, 0) + 1
            return [{"name": k, "count": v} for k, v in miss.items()]

        for t in TEAM_ORDER:
            if t in team_datas:
                td = team_datas[t]
                teams.append({"team": t, "headline": td["headline"], "top": td["top5"][:3],
                              "active_people": td["active_people"], "people": td["people"],
                              "unreported": _unreported({t})})
        etc = [p for p in people if p["team"] not in covered]
        etc_unrep = _unreported({t for t in set(team_of(a["assignee"]) for a in (assignments or []))
                                 if t not in covered})
        if etc or etc_unrep:
            teams.append({"team": "기타", "headline": "", "top": [],
                          "active_people": len(etc), "people": etc, "unreported": etc_unrep})
    return {
        "date": target,
        "weekday": _weekday_kr(target),
        "active_people": len([nm for nm, d in day.items() if (d["raw"] or d["core"] or d["basket"])]),
        "headline": res["headline"],
        "decision_summary": _decision_summary(items),
        "items": items,
        "top5": pick_top5(items),
        "counts": counts,
        "unmatched": unmatched,
        "people": people,
        "teams": teams,
        "assignments": assignments or [],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def build_team_brief_data(target: str, team: str, day: dict,
                          assignments: list[dict] | None = None) -> dict:
    """팀 스코프 Brief — 그 팀 직원 보고만 Engine D로. 보고 0건이면 LLM 호출 skip."""
    tday = {nm: d for nm, d in day.items() if d.get("team") == team}
    blocks = [_emp_block(nm, d) for nm, d in tday.items()]
    res = engine_d(blocks) if blocks else {"items": [], "headline": ""}
    items = res["items"]
    counts = {c: sum(1 for it in items if it["category"] == c) for c in CAT_META}
    return {
        "date": target,
        "team": team,
        "weekday": _weekday_kr(target),
        "active_people": len([nm for nm, d in tday.items() if (d["raw"] or d["core"] or d["basket"])]),
        "headline": res["headline"],
        "decision_summary": _decision_summary(items),
        "items": items,
        "top5": pick_top5(items),
        "counts": counts,
        "unmatched": [],  # 팀 brief는 팀 필터라 매칭된 직원만 — 미매칭 경고 불필요
        "people": _people_summary(tday, assignments),
        "assignments": [a for a in (assignments or [])
                        if a.get("team") == team or team_of(a.get("assignee", "")) == team],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def team_leads() -> dict:
    """team_leads 매핑(팀→리더이름). 팀 Brief 생성·알림의 대상 출처."""
    return EMP.get("team_leads", {})


def leader_chat_ids(team: str) -> list:
    """해당 팀 리더의 텔레그램 chat_id(직원봇). 미연결이면 빈 목록."""
    leader = team_leads().get(team)
    if not leader:
        return []
    return [tid for tid, nm in EMP.get("by_telegram_id", {}).items() if nm == leader]


# ─── HTML 렌더 ───
def _esc(s) -> str:
    return html.escape(str(s or ""))


def _urg_badge(u: str) -> str:
    lab = {"high": "긴급", "mid": "이번주", "low": "참고"}.get(u, u)
    return f'<span class="urg urg-{u}">{lab}</span>'


def _item_card(it: dict) -> str:
    src = _esc(it["source_employee"])
    proj = f' · {_esc(it["project"])}' if it["project"] else ""
    rel = f'<div class="rel">{_esc(it["related"])}</div>' if it["related"] else ""
    # §9-3: 결정 요청 구조 — 추천안/기한/미결정 영향 (있는 것만)
    dec_bits = []
    for key, lab in (("recommendation", "추천안"), ("deadline", "결정 기한"),
                     ("delay_impact", "지연 시 영향")):
        v = (it.get(key) or "").strip()
        if v:
            dec_bits.append(f'<div class="rel">· {lab}: {_esc(v)}</div>')
    dec_html = "".join(dec_bits)
    return f'''<div class="card">
      <div class="ic-h"><b>{_esc(it["title"])}</b>{_urg_badge(it["urgency"])}</div>
      <div class="ic-d">{_esc(it["detail"])}</div>
      <div class="ic-m">{src}{proj}</div>{dec_html}{rel}
    </div>'''


_META_LABELS = [  # (key, 라벨, CSS 클래스)
    ("blocker", "🚧 블로커", "pm-amber"),
    ("decision", "🔴 의사결정요청", "pm-red"),
    ("support", "🙋 지원요청", ""),
    ("question", "❓ 오늘의질문", ""),
]


def _person_card(p: dict) -> str:
    """개인별 업무 써머리 카드 — 시트 원문(핵심업무/메타/매장보고) 그대로."""
    rows = []
    for i, c in enumerate(p["core"]):
        num = chr(0x2460 + i) if i < 10 else f"{i+1}."
        detail = (c.get("detail") or "").strip()
        det_line = f'<span class="pt-detail">{_esc(detail[:400])}</span>' if detail else ""
        # output/outcome 중복 제거 + 상세와 겹치면 생략
        out_bits, seen = [], set()
        for b in (c.get("output", "").strip(), c.get("outcome", "").strip()):
            if b and b not in seen and b not in detail:
                out_bits.append(b)
                seen.add(b)
        out_line = f'<span class="pt-out">→ {_esc(" · ".join(out_bits))}</span>' if out_bits else ""
        issue = f'<div class="pp-issue">⚠ {_esc(c["issue"].strip())}</div>' if c.get("issue", "").strip() else ""
        rows.append(f'<div class="pp-task">{num} {_esc(c.get("task", "").strip() or "(업무명 미기재)")}{det_line}{out_line}{issue}</div>')
    for label, v in p.get("basket", []):
        rows.append(f'<div class="pp-task"><span class="pt-out">{_esc(label)}: {_esc(v[:120])}</span></div>')
    metas = []
    for key, label, cls in _META_LABELS:
        v = (p["meta"].get(key) or "").strip()
        if v:
            metas.append(f'<div class="{cls}">{label} · {_esc(v[:200])}</div>')
    meta_html = f'<div class="pp-meta">{"".join(metas)}</div>' if metas else ""
    # 이번주 분장 — 담당 항목 + 상태 뱃지
    asg_html = ""
    if p.get("assignments"):
        st_cls = {"완료": "as-done", "승인": "as-done", "진행중": "as-doing"}
        lines = []
        for a in p["assignments"]:
            dl = f' <span class="as-dl">~{_esc(a["deadline"][5:] if len(a.get("deadline",""))>=10 else a.get("deadline",""))}</span>' if a.get("deadline") else ""
            tk = (f'[{a["project"]}] ' if a.get("project") else "") + a["task"]
            lines.append(f'<div class="as-item"><span class="as-st {st_cls.get(a["status"], "as-todo")}">{_esc(a["status"])}</span>'
                         f'<span class="as-task">{_esc(tk[:90])}</span>{dl}</div>')
        asg_html = f'<div class="pp-asg"><div class="as-label">📋 이번주 분장 {len(p["assignments"])}건</div>{"".join(lines)}</div>'
    # 2.0 Wave 2: 보고 유형 배지 + Report Score (있을 때만)
    qual_bits = []
    tb = {"A": "🟢 일반", "B": "🟠 이슈", "C": "🔴 결정"}.get((p.get("rtype") or "").strip(), "")
    if tb:
        qual_bits.append(tb)
    if (p.get("score") or "").strip():
        qual_bits.append(f'{p["score"]}점')
    qual = f'<span class="pp-team">{_esc(" · ".join(qual_bits))}</span>' if qual_bits else ""
    return f'''<div class="card">
      <div class="pp-head"><span class="pp-name">{_esc(p["name"])}</span><span class="pp-team">{_esc(p["team"])}</span>{qual}</div>
      {"".join(rows) or '<div class="muted">보고 내용 없음</div>'}{meta_html}{asg_html}
    </div>'''


# ─── 최상단 우선 파악존 (대표 브리프) — 프로젝트/팀 전환 뷰 ───
_PAY_KW = ("승인", "결재", "송금", "결제", "계약")
_COST_KW = ("비용", "지출", "예산", "견적", "단가", "금액", "발주")


def _prio_rank(it: dict) -> int:
    """의사결정(0) > 결재·승인(1) > 비용(2) > 리스크(3) > 개입(4) > 보고·기타(5)"""
    txt = f'{it.get("title", "")} {it.get("detail", "")}'
    if it.get("category") == "decision":
        return 0
    if any(k in txt for k in _PAY_KW):
        return 1
    if any(k in txt for k in _COST_KW):
        return 2
    if it.get("category") == "risk":
        return 3
    if it.get("category") == "intervention":
        return 4
    return 5


def _norm_proj(p) -> str:
    p = (str(p or "")).strip()
    return "" if p.lower() in ("", "null", "none") else p


def _vz_item_row(it: dict) -> str:
    lab, col = CAT_META.get(it.get("category"), ("기타", "var(--muted)"))
    return (f'<div class="vz-item"><span style="color:{col};flex-shrink:0">●</span>'
            f'{_urg_badge(it.get("urgency", "low"))}<span class="vz-t">{_esc(it.get("title", ""))}</span>'
            f'<span class="vz-src">{_esc(it.get("source_employee") or "")}</span></div>')


def _vz_asg_row(a: dict) -> str:
    st = a.get("status") or "미착수"
    cls = {"완료": "as-done", "승인": "as-done", "진행중": "as-doing"}.get(st, "as-todo")
    dl = a.get("deadline") or ""
    dls = f' <span class="as-dl">~{_esc(dl[5:] if len(dl) >= 10 else dl)}</span>' if dl else ""
    return (f'<div class="as-item"><span class="as-st {cls}">{_esc(st)}</span>'
            f'<span class="as-task">{_esc(a.get("task", ""))}</span>'
            f'<span class="vz-src">{_esc(a.get("assignee", ""))}</span>{dls}</div>')


def _view_zone(data: dict, single: bool = False) -> str:
    """브리프 최상단 우선 파악존 — 대표: [프로젝트 단위 | 팀별 단위] 전환,
    팀 브리프(single=True): 프로젝트 단위만(토글 없음).
    진행상황·할일을 의사결정→결재·승인→비용→리스크→보고 순으로 우선 노출."""
    items = data.get("items") or []
    assignments = data.get("assignments") or []
    teams = data.get("teams") or []
    if not (items or assignments or teams):
        return ""
    headline = f'<div class="sz-hl">{_esc(data["headline"])}</div>' if data.get("headline") else ""

    # ── 프로젝트 단위 ──
    proj: dict = {}
    for it in items:
        p = _norm_proj(it.get("project")) or "프로젝트 미지정"
        proj.setdefault(p, {"items": [], "asg": []})["items"].append(it)
    _seen = set()
    for a in assignments:
        key = (a.get("project"), a.get("task"), a.get("assignee"), a.get("deadline"), a.get("status"))
        if key in _seen:  # 이중 등록 표시 중복 제거 (시트 무변경)
            continue
        _seen.add(key)
        p = _norm_proj(a.get("project")) or "프로젝트 미지정"
        proj.setdefault(p, {"items": [], "asg": []})["asg"].append(a)

    def _proj_rank(p):
        best = min((_prio_rank(i) for i in proj[p]["items"]), default=6)
        return (best, 1 if p == "프로젝트 미지정" else 0, p)

    pblocks = []
    for p in sorted(proj, key=_proj_rank):
        g = proj[p]
        rows = "".join(_vz_item_row(i) for i in sorted(g["items"], key=_prio_rank))
        asg = "".join(_vz_asg_row(a) for a in g["asg"])
        if asg:
            asg = f'<div class="vz-sub">할 일 · 이번주 분장</div>{asg}'
        if rows or asg:
            pblocks.append(f'<div class="vz-block"><div class="vz-head">📁 {_esc(p)}</div>{rows}{asg}</div>')
    pview = "".join(pblocks) or '<div class="muted">오늘 항목이 없습니다.</div>'

    if single:  # 팀 브리프 — 프로젝트 단위 뷰만 (토글·스크립트 없음)
        return (f'<div class="view-zone">{headline}'
                f'<div class="vz-tabs"><span class="vz-tab on" style="cursor:default">프로젝트 단위 · 진행상황과 할 일</span>'
                f'<span class="vz-note">우선순위: 의사결정 → 결재·승인 → 비용 → 리스크 → 보고</span></div>'
                f'{pview}</div>')

    # ── 팀별 단위 (컴팩트: headline + 우선 항목 + 미보고 경고) ──
    tblocks = []
    for tb in teams:
        rows = "".join(_vz_item_row(i) for i in sorted(tb.get("top") or [], key=_prio_rank))
        hl = f'<div class="tb-hl">{_esc(tb["headline"])}</div>' if tb.get("headline") else ""
        unrep = ""
        if tb.get("unreported"):
            u = " · ".join(f'{_esc(x["name"])} {x["count"]}건' for x in tb["unreported"])
            unrep = f'<div class="tb-unrep">📋 분장 등록·보고 없음: {u}</div>'
        tblocks.append(f'<div class="vz-block"><div class="vz-head">👥 {_esc(tb["team"])}'
                       f'<span class="cnt">보고 {tb.get("active_people", 0)}명</span></div>{hl}{rows}{unrep}</div>')
    tview = "".join(tblocks) or '<div class="muted">팀 데이터가 없습니다.</div>'

    return f'''<div class="view-zone">
{headline}
<div class="vz-tabs"><button class="vz-tab on" data-v="proj">프로젝트 단위</button><button class="vz-tab" data-v="team">팀별 단위</button>
<span class="vz-note">우선순위: 의사결정 → 결재·승인 → 비용 → 리스크 → 보고</span></div>
<div id="vz-proj" class="vz-view on">{pview}</div>
<div id="vz-team" class="vz-view">{tview}</div>
</div>
<script>
(function(){{
  var tabs=document.querySelectorAll('.vz-tab');
  function show(v){{
    tabs.forEach(function(b){{ b.classList.toggle('on', b.getAttribute('data-v')===v); }});
    document.getElementById('vz-proj').classList.toggle('on', v==='proj');
    document.getElementById('vz-team').classList.toggle('on', v==='team');
    try{{ localStorage.setItem('vz_view', v); }}catch(e){{}}
  }}
  tabs.forEach(function(b){{ b.onclick=function(){{ show(b.getAttribute('data-v')); }}; }});
  var saved=null; try{{ saved=localStorage.getItem('vz_view'); }}catch(e){{}}
  if(saved==='team') show('team');
}})();
</script>'''


def _people_section(data: dict) -> str:
    """브리프 하단 — 대표는 '팀별 오늘 브리프'(팀 headline+핵심+개인카드 병합),
    팀 브리프는 '개인별 업무 써머리'(카드 나열)."""
    teams = data.get("teams") or []
    if teams:
        blocks = []
        for tb in teams:
            hl = f'<div class="tb-hl">{_esc(tb["headline"])}</div>' if tb.get("headline") else ""
            chips = ""
            if tb.get("top"):
                cs = []
                for it in tb["top"]:
                    lab, col = CAT_META[it["category"]]
                    cs.append(f'<span class="tb-chip" style="border-left:3px solid {col}">'
                              f'{_urg_badge(it["urgency"])}{_esc(it["title"])}</span>')
                chips = f'<div class="tb-chips">{"".join(cs)}</div>'
            cards = (f'<div class="pp-grid">{"".join(_person_card(p) for p in tb["people"])}</div>'
                     if tb.get("people") else '<div class="muted">오늘 보고 없음</div>')
            unrep = ""
            if tb.get("unreported"):
                u = " · ".join(f'{_esc(x["name"])} {x["count"]}건' for x in tb["unreported"])
                unrep = f'<div class="tb-unrep">📋 분장 등록·보고 없음: {u}</div>'
            blocks.append(f'<div class="tb-block"><div class="tb-head">{_esc(tb["team"])}'
                          f'<span class="cnt">보고 {tb["active_people"]}명</span></div>{hl}{chips}{cards}{unrep}</div>')
        n = sum(tb["active_people"] for tb in teams)
        return (f'<h2 class="sec" style="border-color:var(--accent)"><span style="color:var(--accent)">●</span>'
                f' 팀별 오늘 브리프 <span class="cnt">보고 {n}명</span></h2>{"".join(blocks)}')

    people = data.get("people") or []
    body = ""
    if not people:
        body = '<div class="muted">오늘 보고한 인원이 없습니다.</div>'
    elif data.get("team"):
        body = f'<div class="pp-grid">{"".join(_person_card(p) for p in people)}</div>'
    else:
        chunks, cur = [], None
        for p in people:
            if p["team"] != cur:
                if cur is not None:
                    chunks.append("</div>")
                chunks.append(f'<div class="pp-team-head">{_esc(p["team"])}</div><div class="pp-grid">')
                cur = p["team"]
            chunks.append(_person_card(p))
        chunks.append("</div>")
        body = "".join(chunks)
    return (f'<h2 class="sec" style="border-color:var(--accent)"><span style="color:var(--accent)">●</span>'
            f' 개인별 업무 써머리 <span class="cnt">{len(people)}명</span></h2>{body}')


def render_brief_html(data: dict) -> str:
    # 대표 전체 Brief vs 팀 리더 Brief 분기 (data["team"] 유무)
    team = data.get("team")
    is_team = bool(team)
    TITLE = f"{team} 팀 Brief · {data['date']}" if is_team else f"대표 Daily Brief · {data['date']}"
    GATE_H2 = f"{_esc(team)} 팀 Brief" if is_team else "대표 Daily Brief"
    GATE_SUB = f'{_esc(data["date"])} · {_esc(team)} 팀 리더' if is_team else f'{_esc(data["date"])} · 대표 전용'
    H1 = f"{_esc(team)} 팀이 오늘 봐야 할 것" if is_team else "오늘 대표가 봐야 할 것"
    SESS_KEY = "team_brief_sess" if is_team else "brief_sess"
    TEAM_JS = json.dumps(team or "", ensure_ascii=False)
    if is_team:
        JS_CAN = "(d.admin || (d.lead_teams||[]).indexOf(TEAM)>=0)"
        JS_SESS_CAN = "(sess.admin || (sess.lead_teams||[]).indexOf(TEAM)>=0)"
        JS_DENY = "이 팀 리더 전용 화면입니다"
    else:
        JS_CAN = "d.admin"
        JS_SESS_CAN = "sess.admin"
        JS_DENY = "대표 전용 화면입니다"
    # TOP5 히어로
    hero = []
    for it in data["top5"]:
        lab, col = CAT_META[it["category"]]
        hero.append(f'''<div class="hero-card" style="border-top:3px solid {col}">
          <div class="hc-cat" style="color:{col}">{_esc(lab)}</div>
          <div class="hc-title">{_esc(it["title"])}</div>
          <div class="hc-foot">{_urg_badge(it["urgency"])}<span class="muted">{_esc(it["source_employee"])}</span></div>
        </div>''')
    hero_html = "".join(hero) or '<div class="muted">오늘 들어온 보고가 없습니다.</div>'

    # 5범주 섹션
    secs = []
    for c in CAT_ORDER:
        lab, col = CAT_META[c]
        cards = [_item_card(it) for it in data["items"] if it["category"] == c]
        body = "".join(cards) or '<div class="muted">오늘 해당 없음</div>'
        secs.append(f'<h2 class="sec" style="border-color:{col}"><span style="color:{col}">●</span> {_esc(lab)}'
                    f' <span class="cnt">{data["counts"][c]}</span></h2><div class="grid">{body}</div>')
    secs_html = "".join(secs)

    # 상단 요약존 — 팀/파트 한줄 써머리 + 오늘 의사결정·개입
    headline = _esc(data.get("headline") or "")
    dsum = data.get("decision_summary") or []
    summary_zone = ""
    if headline or dsum:
        hl = f'<div class="sz-hl">{headline}</div>' if headline else ''
        if dsum:
            dz_cards = "".join(
                f'<div class="dz-card">{_urg_badge(it["urgency"])}<b>{_esc(it["title"])}</b>'
                f'<span class="dz-src">{_esc(it["source_employee"])}'
                f'{" · " + _esc(it["project"]) if it["project"] else ""}'
                f'{" · ⏰ " + _esc(it["deadline"]) if (it.get("deadline") or "").strip() else ""}</span></div>'
                for it in dsum)
            dz = f'<div class="sz-label">오늘 의사결정 · 개입</div><div class="dz-grid">{dz_cards}</div>'
        else:
            dz = '<div class="sz-label">오늘 의사결정 · 개입</div><div class="muted">오늘 결정·개입 필요사항 없음</div>'
        summary_zone = f'<div class="summary-zone">{hl}{dz}</div>'

    cnt = data["counts"]
    unmatched = ""
    if data["unmatched"]:
        unmatched = f'<div class="warn">⚠️ 명부 미매칭: {_esc(", ".join(data["unmatched"]))}</div>'

    # 최상단 우선 파악존 — 대표=프로젝트/팀 토글, 팀 브리프=프로젝트 단위 단일 뷰.
    # headline·결정 카드를 포함하므로 기존 요약존 대체
    view_zone = _view_zone(data, single=is_team)
    if view_zone:
        summary_zone = ""

    return f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(TITLE)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>
:root{{--bg:#1A1A1A;--bg-2:#202020;--bg-3:#262626;--fg:#F5F0EB;--muted:#8A857E;--line:#333;
--accent:#6C5CE7;--green:#8FA37E;--amber:#D9A34B;--red:#E17055;--blue:#6F8AA3}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--fg);font-family:'Pretendard Variable',sans-serif;font-weight:300;line-height:1.5;padding:32px 20px 64px}}
.wrap{{max-width:1100px;margin:0 auto}}
header h1{{font-weight:600;font-size:26px;letter-spacing:-.02em}}
header .sub{{color:var(--muted);margin-top:4px;font-size:14px}}
.statbar{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:20px 0 28px}}
.stat{{background:var(--bg-2);border:1px solid var(--line);border-radius:10px;padding:14px}}
.stat b{{font-size:24px;font-weight:600;color:var(--accent)}}
.stat small{{display:block;color:var(--muted);font-size:11px;margin-top:3px}}
.hero{{display:grid;grid-template-columns:repeat(auto-fit,minmax(195px,1fr));gap:12px;margin-bottom:8px}}
.hero-card{{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:16px}}
.hc-cat{{font-size:11px;font-weight:600;letter-spacing:.04em;margin-bottom:8px}}
.hc-title{{font-size:14px;font-weight:500;line-height:1.45;min-height:40px}}
.hc-foot{{display:flex;align-items:center;gap:8px;margin-top:10px}}
h2.sec{{font-size:14px;font-weight:600;margin:34px 0 14px;border-bottom:1px solid var(--line);padding-bottom:8px;display:flex;align-items:center;gap:8px}}
h2.sec .cnt{{margin-left:auto;color:var(--muted);font-size:12px;font-weight:400}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}}
.card{{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:16px}}
.ic-h{{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:8px}}
.ic-h b{{font-size:15px;font-weight:600;line-height:1.4}}
.ic-d{{font-size:13px;color:var(--fg);line-height:1.6;margin-bottom:8px}}
.ic-m{{font-size:12px;color:var(--accent)}}
.rel{{font-size:11px;color:var(--muted);margin-top:4px;border-top:1px solid var(--line);padding-top:6px}}
.urg{{font-size:11px;border-radius:5px;padding:2px 8px;white-space:nowrap;flex-shrink:0}}
.urg-high{{background:rgba(225,112,85,.16);color:var(--red);border:1px solid rgba(225,112,85,.4)}}
.urg-mid{{background:rgba(217,163,75,.14);color:var(--amber);border:1px solid rgba(217,163,75,.35)}}
.urg-low{{background:var(--bg-3);color:var(--muted);border:1px solid var(--line)}}
.muted{{color:var(--muted);font-size:12px}}
.summary-zone{{background:var(--bg-3);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:18px 20px;margin:18px 0 24px}}
.sz-hl{{font-size:16px;font-weight:500;color:var(--fg);line-height:1.55;margin-bottom:16px}}
.sz-label{{font-size:11px;font-weight:600;color:var(--accent);letter-spacing:.05em;text-transform:uppercase;margin-bottom:10px}}
.dz-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}}
.dz-card{{background:var(--bg-2);border:1px solid var(--line);border-radius:9px;padding:11px 13px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.dz-card b{{font-size:13px;font-weight:500;flex:1;min-width:130px;line-height:1.4}}
.dz-src{{font-size:11px;color:var(--muted);width:100%}}
.warn{{background:rgba(217,163,75,.1);border:1px solid rgba(217,163,75,.3);color:var(--amber);border-radius:8px;padding:10px 14px;font-size:13px;margin:16px 0}}
.pp-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px;margin-bottom:6px}}
.pp-team-head{{font-size:12px;font-weight:600;color:var(--muted);letter-spacing:.04em;margin:16px 0 10px}}
.pp-head{{display:flex;align-items:center;gap:8px;margin-bottom:10px}}
.pp-name{{font-size:15px;font-weight:600}}
.pp-team{{font-size:11px;color:var(--accent);background:rgba(108,92,231,.12);border:1px solid rgba(108,92,231,.35);border-radius:5px;padding:1px 7px}}
.pp-task{{font-size:13px;line-height:1.5;margin-bottom:8px}}
.pp-task .pt-out{{display:block;font-size:12px;color:var(--muted);margin-top:2px;padding-left:18px}}
.pp-task .pt-detail{{display:block;font-size:12px;color:var(--fg);opacity:.85;line-height:1.6;margin-top:3px;padding-left:18px}}
.pp-issue{{font-size:12px;color:var(--amber);margin-top:2px;padding-left:18px}}
.pp-meta{{border-top:1px solid var(--line);margin-top:10px;padding-top:8px;font-size:12px;line-height:1.7}}
.pp-meta .pm-red{{color:var(--red)}}
.pp-meta .pm-amber{{color:var(--amber)}}
.pp-asg{{border-top:1px solid var(--line);margin-top:10px;padding-top:8px}}
.as-label{{font-size:11px;font-weight:600;color:var(--accent);margin-bottom:6px}}
.as-item{{display:flex;align-items:baseline;gap:7px;font-size:12px;line-height:1.55;margin-bottom:4px}}
.as-st{{font-size:10px;border-radius:4px;padding:1px 6px;white-space:nowrap;flex-shrink:0}}
.as-todo{{background:rgba(225,112,85,.14);color:var(--red);border:1px solid rgba(225,112,85,.35)}}
.as-doing{{background:rgba(217,163,75,.14);color:var(--amber);border:1px solid rgba(217,163,75,.35)}}
.as-done{{background:var(--bg-3);color:var(--muted);border:1px solid var(--line)}}
.as-done + .as-task{{text-decoration:line-through;color:var(--muted)}}
.as-task{{flex:1;min-width:0}}
.as-dl{{font-size:11px;color:var(--muted);white-space:nowrap}}
.tb-block{{background:var(--bg-2);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:16px}}
.tb-head{{font-size:15px;font-weight:600;display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.tb-head .cnt{{margin-left:auto;color:var(--muted);font-size:12px;font-weight:400}}
.tb-hl{{font-size:13px;color:var(--muted);line-height:1.55;margin-bottom:10px}}
.tb-chips{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}}
.tb-chip{{background:var(--bg-3);border:1px solid var(--line);border-radius:8px;padding:6px 10px;font-size:12px;display:inline-flex;align-items:center;gap:7px;line-height:1.4}}
.tb-block .pp-grid{{margin-bottom:0}}
.tb-block .card{{background:var(--bg-3)}}
.tb-unrep{{font-size:12px;color:var(--amber);margin-top:12px;border-top:1px solid var(--line);padding-top:8px}}
.view-zone{{background:var(--bg-3);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:18px 20px;margin:18px 0 24px}}
.vz-tabs{{display:flex;gap:8px;align-items:center;margin:4px 0 14px;flex-wrap:wrap}}
.vz-tab{{background:var(--bg-2);border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:7px 16px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}}
.vz-tab.on{{background:var(--accent);color:#fff;border-color:var(--accent)}}
.vz-note{{font-size:11px;color:var(--muted);margin-left:auto}}
.vz-view{{display:none}}
.vz-view.on{{display:block}}
.vz-block{{background:var(--bg-2);border:1px solid var(--line);border-radius:10px;padding:13px 15px;margin-bottom:10px}}
.vz-head{{font-size:14px;font-weight:600;margin-bottom:8px;display:flex;align-items:center;gap:8px}}
.vz-head .cnt{{margin-left:auto;color:var(--muted);font-size:12px;font-weight:400}}
.vz-item{{display:flex;align-items:baseline;gap:8px;font-size:13px;line-height:1.55;margin-bottom:5px}}
.vz-t{{flex:1;min-width:0}}
.vz-src{{font-size:11px;color:var(--muted);white-space:nowrap}}
.vz-sub{{font-size:11px;font-weight:600;color:var(--accent);margin:9px 0 5px;border-top:1px solid var(--line);padding-top:8px}}
footer{{margin-top:44px;color:var(--muted);font-size:11px;text-align:center;border-top:1px solid var(--line);padding-top:16px}}
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
<div id="login-gate"><div id="login-box">
  <h2>{GATE_H2}</h2>
  <div class="lg-sub">{GATE_SUB}</div>
  <input id="lg-id" placeholder="이름" autocomplete="username">
  <input id="lg-pin" type="password" placeholder="PIN" autocomplete="current-password">
  <button id="lg-btn">로그인</button>
  <div id="login-err"></div>
</div></div>
<div id="whoami" style="display:none"></div>
<div id="content" style="display:none"><div class="wrap">
<header><h1>{H1}</h1><div class="sub">{_esc(data["date"])} ({_esc(data["weekday"])}) · 생성 {_esc(data["generated_at"])}</div></header>
{unmatched}
{view_zone}
{summary_zone}
<div class="statbar">
  <div class="stat"><b>{cnt["decision"]}</b><small>결정</small></div>
  <div class="stat"><b>{cnt["intervention"]}</b><small>개입</small></div>
  <div class="stat"><b>{cnt["risk"]}</b><small>리스크</small></div>
  <div class="stat"><b>{cnt["support"]}</b><small>지원요청</small></div>
  <div class="stat"><b>{cnt["project"]}</b><small>프로젝트</small></div>
  <div class="stat"><b>{cnt["growth"]}</b><small>성장신호</small></div>
  <div class="stat"><b>{cnt["anomaly"]}</b><small>이상신호</small></div>
  <div class="stat"><b>{data["active_people"]}</b><small>보고 인원</small></div>
</div>
<div class="hero">{hero_html}</div>
{secs_html}
{_people_section(data)}
<footer>ARISA Engine D · Daily Executive Brief · {_esc(data["generated_at"])} · by Project Rent</footer>
</div></div>
<script>
(function(){{
  var TEAM={TEAM_JS};
  var gate=document.getElementById('login-gate'), content=document.getElementById('content'), who=document.getElementById('whoami');
  function enter(s){{
    gate.style.display='none'; content.style.display='block'; who.style.display='block';
    who.innerHTML = s.name+' ('+(s.role||'')+') <a id="lg-out">로그아웃</a>';
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
    html_path = OUT_DIR / f"daily-brief-{data['date']}.html"
    json_path = OUT_DIR / f"daily-brief-{data['date']}.json"
    html_path.write_text(render_brief_html(data), encoding="utf-8")
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ HTML: {html_path}")
    print(f"✅ JSON: {json_path}")
    if do_open:
        subprocess.run(["open", str(html_path)], check=False)
    if not no_telegram and MANAGER_BOT_TOKEN and MANAGER_CHAT_ID:
        _telegram_brief(data)
    return html_path


def _telegram_brief(data: dict):
    c = data["counts"]
    msg = (f"🗂 대표 Daily Brief {data['date']}({data['weekday']})\n"
           f"결정 {c['decision']} · 개입 {c['intervention']} · 리스크 {c['risk']} "
           f"· 지원 {c['support']} · 프로젝트 {c['project']} · 성장 {c['growth']}"
           + (f" · ⚡이상신호 {c['anomaly']}" if c.get("anomaly") else "") + "\n")
    if data["top5"]:
        msg += "\n오늘 봐야 할 것:\n"
        for it in data["top5"]:
            lab = CAT_META[it["category"]][0].split(" ")[0]
            msg += f"• [{lab}] {it['title']}\n"
    else:
        msg += "\n오늘 들어온 보고 없음\n"
    msg += f"\n📄 {DASHBOARD_BASE_URL}/dashboard"
    try:
        import urllib.request
        url = f"https://api.telegram.org/bot{MANAGER_BOT_TOKEN}/sendMessage"
        body = json.dumps({"chat_id": MANAGER_CHAT_ID, "text": msg}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20)
        print("✅ 텔레그램 브리프 전송")
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 실패: {e}")


def _telegram_team_brief(data: dict, chat_ids: list):
    """팀 리더에게 자기 팀 Brief 요약 + 팀 대시보드 링크 발송(직원봇)."""
    if not (LEADER_BOT_TOKEN and chat_ids):
        return
    import urllib.parse, urllib.request
    team = data["team"]
    c = data["counts"]
    msg = (f"👥 {team} 팀 Brief {data['date']}({data['weekday']})\n"
           f"결정 {c['decision']} · 개입 {c['intervention']} · 리스크 {c['risk']} "
           f"· 지원 {c['support']} · 프로젝트 {c['project']} · 성장 {c['growth']}"
           + (f" · ⚡이상신호 {c['anomaly']}" if c.get("anomaly") else "") + "\n")
    if data["top5"]:
        msg += "\n오늘 봐야 할 것:\n"
        for it in data["top5"]:
            lab = CAT_META[it["category"]][0].split(" ")[0]
            msg += f"• [{lab}] {it['title']}\n"
    else:
        msg += "\n오늘 들어온 팀 보고 없음\n"
    link = f"{DASHBOARD_BASE_URL}/team?team=" + urllib.parse.quote(team)
    msg += f"\n📄 {link}"
    for cid in chat_ids:
        try:
            url = f"https://api.telegram.org/bot{LEADER_BOT_TOKEN}/sendMessage"
            body = json.dumps({"chat_id": cid, "text": msg}).encode()
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=20)
            print(f"✅ [{team}] 리더 텔레그램 전송 (chat={cid})")
        except Exception as e:
            print(f"⚠️ [{team}] 리더 전송 실패: {e}")


def save_team_brief(data: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    team = data["team"]
    html_path = OUT_DIR / f"daily-brief-{data['date']}-{team}.html"
    json_path = OUT_DIR / f"daily-brief-{data['date']}-{team}.json"
    html_path.write_text(render_brief_html(data), encoding="utf-8")
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ [{team}] {html_path.name} (항목 {len(data['items'])}, TOP5 {len(data['top5'])}, 보고 {data['active_people']})")
    return html_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="YYYY-MM-DD (기본 오늘)")
    ap.add_argument("--source", default="", help="소스 보고일(쉼표 구분) — 기본: 직전 영업일~어제 (저녁 보고 습관 반영)")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--no-telegram", action="store_true")
    args = ap.parse_args()
    sources = [s.strip() for s in args.source.split(",") if s.strip()] or prev_bizday_range(args.date)
    print(f"브리프 날짜: {args.date} · 소스 보고일: {', '.join(sources)}")
    day = fetch_day(sources)  # 1회 수집 → 대표·팀 brief 공용(gws 재호출 0)
    assignments = fetch_assignments(args.date)  # 브리프 날짜가 속한 주의 분장 → 개인카드 연동
    print(f"주간분장: 이번주 {len(assignments)}건")

    # ─── 팀 Brief 먼저 생성 (대표 브리프에 팀별 섹션으로 병합) ───
    tdatas = {team: build_team_brief_data(args.date, team, day, assignments)
              for team in team_leads()}

    data = build_brief_data(args.date, day, team_datas=tdatas, assignments=assignments)
    print(f"추출 항목: {len(data['items'])}건 (TOP5 {len(data['top5'])}) · 보고인원 {data['active_people']} · 미매칭 {len(data['unmatched'])}")
    save_and_notify(data, args.open, args.no_telegram)

    # ─── 팀 리더 Brief 저장·알림 (team_leads 각 팀) ───
    for team, tdata in tdatas.items():
        save_team_brief(tdata)
        if not args.no_telegram:
            _telegram_team_brief(tdata, leader_chat_ids(team))


if __name__ == "__main__":
    main()
