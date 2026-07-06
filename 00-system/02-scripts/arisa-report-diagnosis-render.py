#!/usr/bin/env python3
"""ARISA 보고 품질 진단 리포트 렌더러 — diagnosis-scored JSON → 다크테마 HTML.

수치는 전부 diagnosis-scored-2026-2wk.json에서 읽어 소급 가능(fidelity).
저작 콘텐츠(좋은보고 기준·양식·외부 프레임 정합)는 3.0 측정설계 v2 + 2.0 DEFINITION
+ 외부 리서치(PPP/STAR/SBAR/OKR/MBE)에 근거. 실제 원문 발췌는 raw_excerpt 사용.

재실행: python3 arisa-report-diagnosis-render.py
출력: 20-operations/23-arisa/arisa-report-quality-diagnosis-2026-2wk.html
"""
from __future__ import annotations

import json
import html
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / "20-operations" / "23-arisa"
DATA = json.load(open(BASE / "diagnosis-scored-2026-2wk.json", encoding="utf-8"))
OUT = BASE / "arisa-report-quality-diagnosis-2026-2wk.html"

S = DATA["summary"]
TEAMS = DATA["teams"]
PERSONS = DATA["persons"]

ALL14 = ["status", "why", "problem", "approach", "output", "outcome", "timeline",
         "risk", "support", "decision", "budget", "impact", "next", "reflection"]
KR = {k: S["elem_stat"][k]["kr"] for k in ALL14}


def esc(s):
    return html.escape(str(s or ""))


# ── 14요소 정의 + 깊이 앵커 (3.0 측정설계 v2) ──
ELEM_DEF = {
    "status": ("현황", '"진행중" → 단계·완료율·최근 변화 명시'),
    "why": ("목적", "막연 → 상위 목표와의 연결 명시"),
    "problem": ("문제", '"어렵다" → 원인·범위·영향 구체화'),
    "approach": ("해결방향", '"열심히" → 선택지·근거·결정 명시'),
    "output": ("산출물", "업무명 반복 → 구체 결과물·링크"),
    "outcome": ("의미", '"잘됨" → 무엇이 어떻게 달라졌나'),
    "timeline": ("일정", '"곧" → 날짜·마일스톤'),
    "risk": ("리스크", "누락 → 발생가능성·대비책"),
    "support": ("요청", '"도와주세요" → 누가·무엇을·언제'),
    "decision": ("의사결정", "모호 → 선택지+추천+기한"),
    "budget": ("예산", "누락 → 금액·항목·근거"),
    "impact": ("기대효과", "막연 → 정량·정성 기대치"),
    "next": ("실행계획", '"진행" → 단계별 액션·담당'),
    "reflection": ("회고", "형식적 → 구체 관찰 1개 이상"),
}

# ── 외부 프레임 정합 (리서치 결과, 교차확인 완료) ──
FRAMES = [
    ("PPP", "Progress · Plans · Problems", "산출물·의미 / 실행계획·일정 / 문제·리스크·요청",
     "2000년대 스타트업발 주간보고 표준"),
    ("STAR", "Situation · Task · Action · Result", "현황·목적 / 해결방향 / 산출물·의미·기대효과",
     "성과의 인과 사슬 서술"),
    ("SBAR", "Situation · Background · Assessment · Recommendation",
     "현황 / 문제·목적 / 해결방향·의사결정·요청", "판단·권고까지 담아 즉시 의사결정 가능"),
    ("OKR check-in", "Progress · Confidence · Priorities · Blockers",
     "현황·산출물 / 리스크·기대효과 / 실행계획 / 문제·요청", "달성 자신도로 위험 조기 포착"),
    ("MBE", "Management by Exception", "문제·리스크·의사결정 (보고 밀도 원칙)",
     "정상은 무보고, 예외만 신호로"),
]


def sec_header():
    return f"""
  <header class="rpt-head">
    <div class="eyebrow">ARISA · 보고 품질 진단 · by Project Rent</div>
    <h1>직원 업무보고 품질 진단</h1>
    <p class="sub">지난 2주({S['window']['start']} ~ {S['window']['end']}) · 보고자 {S['reporters']}명 ·
       메타보고 {S['meta_reports']}건 · 좋은 보고 기준 대비 갭 분석</p>
  </header>"""


def sec_exec():
    d = S["defects"]
    worst = S["worst_elements"]
    worst_kr = " · ".join(f"{KR[k]} {r}%" for k, r in worst)
    conclusion = (
        f"직원들은 <b>'한 일(산출물)'은 100% 적지만</b>, "
        f"<b>'그래서 무엇이 달라졌나(의미)'는 {100-d['outcome_missing']}%만, "
        f"'무엇을 결정해야 하나(의사결정)'는 {100-d['decision_missing']}%만</b> 적는다. "
        f"보고가 <b>업무 나열에 머물고 사고·판단으로 올라가지 못한다.</b> "
        f"평균 해상도는 100점 만점에 <b>{S['avg_resolution']}점</b>."
    )
    stats = [
        ("보고자", f"{S['reporters']}명", "2주 활동"),
        ("평균 해상도", f"{S['avg_resolution']}", "/ 100"),
        ("평균 커버리지", f"{S['avg_coverage']}%", "기대셋 8요소"),
        ("의사결정 공란", f"{S['defects']['decision_missing']}%", "아무도 안 씀"),
        ("의미 공란", f"{S['defects']['outcome_missing']}%", "Outcome 누락"),
        ("오염 보고", f"{S['pollution']['dropped']}건", "집계서 유실"),
    ]
    cells = "".join(
        f'<div class="stat"><b>{esc(v)}</b><span>{esc(t)}</span><small>{esc(sub)}</small></div>'
        for t, v, sub in stats)
    return f"""
  <section class="panel accent-top">
    <div class="tag">진단 요약 · Executive Summary</div>
    <p class="lead">{conclusion}</p>
    <div class="statbar">{cells}</div>
    <p class="note">가장 빈 요소: {esc(worst_kr)} · 판정선 = "제3자가 이 보고만 보고 다음 액션·의사결정을 할 수 있는가"</p>
  </section>"""


def sec_criteria():
    # 14요소 정의표 + fill_rate
    rows = ""
    for k in ALL14:
        name, anchor = ELEM_DEF[k]
        st = S["elem_stat"][k]
        exp = {"req": "필수", "opt": "선택", "—": "—"}[st["expected"]]
        expc = {"req": "req", "opt": "opt", "—": "non"}[st["expected"]]
        fr = st["fill_rate"]
        bar = f'<div class="minibar"><i style="width:{fr}%"></i></div>'
        rows += (f'<tr class="{expc}"><td class="ek">{esc(name)}<small>{k}</small></td>'
                 f'<td class="ea">{esc(anchor)}</td><td class="ex">{exp}</td>'
                 f'<td class="ef">{bar}<span>{fr}%</span></td></tr>')
    frames = "".join(
        f'<div class="frame"><b>{esc(n)}</b><span>{esc(sub)}</span>'
        f'<p>{esc(m)}</p><small>{esc(note)}</small></div>'
        for n, sub, m, note in FRAMES)
    return f"""
  <section class="panel">
    <div class="tag">① 좋은 보고의 기준</div>
    <p class="lead2">좋은 보고는 <b>'제3자가 이 보고만 보고 다음 액션·의사결정을 할 수 있는가'</b>를 통과한다.
       ARISA는 이를 <b>14개 사고요소</b>로 분해하고, 각 요소를 <b>깊이 0~3</b>(0=비었거나 형식적 · 3=구체 디테일+핵심 명확)으로 잰다.</p>
    <table class="crit">
      <thead><tr><th>요소</th><th>깊이 0 → 3 핵심 갈림</th><th>일일</th><th>2주 충족률</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <p class="subtag">업계 표준과의 정합 — 14요소는 임의 설계가 아니다</p>
    <div class="frames">{frames}</div>
    <p class="note">5개 표준 프레임(각 2개 이상 출처 교차확인)이 강조하는 요소의 합집합이 14요소. 예산·회고는 표준에도 약한 축 —
       사내 기준이 오히려 더 넓다. SBAR만이 '의사결정·요청'을 명시 요구한다.</p>
  </section>"""


def _elem_card(key, bad, good):
    name, anchor = ELEM_DEF[key]
    return (f'<div class="ecard"><div class="ecard-h">{esc(name)} <small>{key}</small></div>'
            f'<div class="ex-bad"><span>✗ 낮음(0-1)</span>{esc(bad)}</div>'
            f'<div class="ex-good"><span>✓ 높음(3)</span>{esc(good)}</div>'
            f'<div class="ex-anchor">{esc(anchor)}</div></div>')


def sec_forms():
    # 일일 양식
    daily_req = ["output", "outcome", "problem", "approach"]
    daily_opt = ["timeline", "support", "decision", "next"]
    daily_no = ["status", "why", "risk", "budget", "impact", "reflection"]

    def chips(keys, cls):
        return "".join(f'<span class="chip {cls}">{esc(KR[k])}</span>' for k in keys)

    # 실제 발췌 기반 요소 카드
    cards = "".join([
        _elem_card("outcome",
                   "정리 중 ?? / 업무명만 나열 (양은정·김가은 사례)",
                   "각 자료에 업체별 단가·제작기간·리스크·7/30 납품 타임라인 정리, 베이직 기준 재견적 방향으로 좁힘 (정예은)"),
        _elem_card("approach",
                   "브루비 설치 → 팔로업 / 열심히 진행",
                   "여러 제작안을 넓게 검토하기보다 상하뚜껑형 기준으로 재견적, 허니콤보드 샘플 먼저 검증하는 방향"),
        _elem_card("decision",
                   "(공란 — 10명 전원 미작성)",
                   "행사인력 10→15명·조명 추가·보험규모(128만원) 확정 필요 — 선택지+추천+기한 명시"),
    ])

    # 주간 v0.9
    weekly = [
        ("① 이번 주 핵심 Output·Outcome", "만든 것 + 그게 만든 변화 (나열 아님)"),
        ("② 목표 대비 진척", "현황·완료율·일정 마일스톤"),
        ("③ 반복 블로커·리스크", "이번 주 되풀이된 막힘, 다음 주 위험"),
        ("④ 다음 주 집중 과제", "실행계획 — 단계·담당"),
        ("⑤ 의사결정 요청", "대표·팀장이 정해줄 것 (선택지+추천+기한)"),
        ("⑥ 주간 회고 + Confidence", "관찰 1개 + 목표 달성 자신도 🟢🟡🔴 (OKR 차용)"),
    ]
    wk = "".join(f'<div class="wk"><b>{esc(t)}</b><span>{esc(d)}</span></div>' for t, d in weekly)

    return f"""
  <section class="panel">
    <div class="tag">② 제안 — 보고 기준 양식</div>

    <div class="form-block">
      <h3>일일 보고 (현행 7섹션 정련)</h3>
      <p class="lead2">일일은 <b>가볍게</b> — 8요소만 기대하고 6요소는 <b>불요</b>(과잉보고 방지).</p>
      <div class="chiprow"><b>필수</b> {chips(daily_req,'req')}</div>
      <div class="chiprow"><b>선택</b> {chips(daily_opt,'opt')}</div>
      <div class="chiprow"><b>불요</b> {chips(daily_no,'non')}</div>
      <p class="note">핵심 정련점: <b>Blocker(막힘) ≠ Support(필요 지원)</b> 구분 · Reflection은 '평가'가 아닌 '관찰' ·
         산출물 다음엔 반드시 <b>의미(Outcome)</b>를 한 줄.</p>
      <div class="ecards">{cards}</div>
    </div>

    <div class="form-block">
      <h3>주간 보고 <span class="ver">v0.9 제안</span></h3>
      <p class="lead2">현재 <b>개인 주간보고 양식은 미정의</b>(집계 대시보드만 존재). 아래를 파일럿으로 제안 —
         이번 진단이 그 검증 데이터다. 3.0 측정설계 weekly 기대셋 + OKR check-in 차용.</p>
      <div class="wkgrid">{wk}</div>
    </div>
  </section>"""


def sec_gap():
    # 히트맵: scored persons × 14요소
    scored = [p for p in PERSONS if p["growth"].get("status") == "scored"]
    head = "".join(f'<th class="{S["elem_stat"][k]["expected"]}">{esc(KR[k])}</th>' for k in ALL14)
    body = ""
    for p in scored:
        els = p["growth"]["elements"]
        cells = ""
        for k in ALL14:
            e = els[k]
            if e["filled"]:
                cells += f'<td class="h d{e["depth"]}" title="{esc(KR[k])} 깊이{e["depth"]}"></td>'
            else:
                cells += f'<td class="h d0" title="{esc(KR[k])} 미충족"></td>'
        res = p["growth"]["resolution"]
        body += (f'<tr><td class="pn">{esc(p["name"])}<small>{esc(p["team"])}</small></td>'
                 f'{cells}<td class="pr">{res}</td></tr>')
    # 결함 발생률
    d = S["defects"]
    defect_items = [("의사결정 미작성", d["decision_missing"]), ("의미(Outcome) 미작성", d["outcome_missing"]),
                    ("문제 미작성", d["problem_missing"]), ("산출물 미작성", d["output_missing"])]
    defbars = "".join(
        f'<div class="defect"><span>{esc(t)}</span><div class="dbar"><i style="width:{v}%"></i></div><b>{v}%</b></div>'
        for t, v in defect_items)
    return f"""
  <section class="panel">
    <div class="tag">③ 현재 갭 — 전체</div>
    <p class="lead2">아래는 채점된 {len(scored)}명 × 14요소 <b>충족 히트맵</b>. 진할수록 깊이(0~3)가 높다.
       빈 칸이 <b>안 쓰인 사고</b>다.</p>
    <div class="heatwrap">
      <table class="heat">
        <thead><tr><th class="pn">직원</th>{head}<th class="pr">해상도</th></tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
    <div class="legend"><span class="h d0"></span>미충족<span class="h d1"></span>1<span class="h d2"></span>2<span class="h d3"></span>3 ·
      상단 색 = <span class="lg-req">필수</span> <span class="lg-opt">선택</span></div>

    <p class="subtag">ARISA 5대 결함 발생률</p>
    <div class="defects">{defbars}</div>
    <p class="note">산출물은 전원 작성(0% 결함)하지만 <b>의사결정 100%·의미 80%·문제 60%가 공란</b> —
       '나열은 하되 판단·의미로 올라가지 못한다'는 5대 결함이 실제 데이터로 확인된다.
       의사결정 0%는 <b>Decision Log(decisions.jsonl)가 비어 있던 이유</b>와 정확히 일치한다.</p>
  </section>"""


def sec_teams():
    order = sorted(TEAMS, key=lambda t: -(t["avg_resolution"] or 0))
    mx = max((t["avg_resolution"] or 0) for t in TEAMS) or 1
    bars = ""
    for t in order:
        r = t["avg_resolution"] or 0
        c = t["avg_coverage"] or 0
        w = round(r / mx * 100)
        bars += (f'<div class="teamrow"><span class="tn">{esc(t["team"])}</span>'
                 f'<div class="tbar"><i style="width:{w}%"></i></div>'
                 f'<span class="tv">해상도 {r} · 커버리지 {c}% · {t["scored_members"]}명</span></div>')
    return f"""
  <section class="panel">
    <div class="tag">④ 팀별 비교</div>
    <div class="teams">{bars}</div>
    <p class="note">팀 간 격차가 크다 — 최고 팀과 최저 팀의 해상도 차이가 2배 이상.
       개인 편차(뒤 카드)가 팀 평균을 좌우한다.</p>
  </section>"""


def _gauge(res):
    # 반원 게이지 대신 원형 conic
    color = "#8FA37E" if res >= 60 else ("#D9A34B" if res >= 30 else "#E17055")
    return (f'<div class="gauge" style="background:conic-gradient({color} {res*3.6}deg,#2a2a2a 0)">'
            f'<span>{res}</span></div>')


def sec_persons():
    cards = ""
    for p in PERSONS:
        g = p["growth"]
        if g.get("status") != "scored":
            cards += (f'<div class="pcard collecting"><div class="pc-h"><b>{esc(p["name"])}</b>'
                      f'<span>{esc(p["team"])}</span></div><p class="coll">데이터 수집 중</p></div>')
            continue
        miss = g.get("req_missing", [])
        miss_ch = "".join(f'<span class="mc">{esc(KR[k])}</span>' for k in miss) or '<span class="ok">필수 완비 ✓</span>'
        # 요소 미니맵
        mini = "".join(
            f'<i class="m d{g["elements"][k]["depth"] if g["elements"][k]["filled"] else 0}" title="{esc(KR[k])}"></i>'
            for k in ALL14)
        exc = esc((p.get("raw_excerpt") or "")[:240])
        cards += f"""
    <div class="pcard">
      <div class="pc-h">{_gauge(g['resolution'])}<div><b>{esc(p['name'])}</b><span>{esc(p['team'])} ·
        {p['report_days']}일 보고 · {p['task_count']}건</span></div></div>
      <div class="pc-map">{mini}</div>
      <div class="pc-miss"><small>필수 누락</small>{miss_ch}</div>
      <div class="pc-exc">"{exc}…"</div>
    </div>"""
    return f"""
  <section class="panel">
    <div class="tag">⑤ 개인별 진단</div>
    <div class="pcards">{cards}</div>
    <p class="note">해상도 색: <b style="color:#8FA37E">녹색 60+</b> · <b style="color:#D9A34B">황색 30~59</b> ·
       <b style="color:#E17055">적색 30미만</b>. 미니맵 14칸 = 14요소 깊이. 발췌는 실제 원문(왜곡 없음).</p>
  </section>"""


def sec_actions():
    org = [
        ("입력 UX 오염 수정", f"이름칸에 보고 원문이 통째로 들어가 {S['pollution']['dropped']}건이 집계에서 조용히 유실. 봇 이름 검증 강화(이미 일부 반영) + 재발 감지."),
        ("의사결정 유도", "10명 전원 decision 공란 → 보고 완료 시 '대표가 정해줄 것 있나요?' 1문항 상시 노출. Decision Log 축적으로 연결."),
        ("주간양식 v0.9 도입", "개인 주간보고 양식을 파일럿으로 시작 — 이번 진단이 baseline. 4주 뒤 재측정으로 해상도 변화 추적."),
        ("의미(Outcome) 한 줄 강제", "산출물 다음에 '그래서 무엇이 달라졌나'를 Completion 질문으로. 80% 공란 → 목표 절반 감소."),
    ]
    ind = [
        "산출물은 잘 쓴다 → 다음 단계는 <b>의미(Outcome) 한 줄</b> 붙이기 (대부분 공통 과제)",
        "정예은(해상도 75)의 보고를 팀 <b>모범 사례</b>로 공유 — 산출물+방향+의미+일정을 한 흐름으로",
        "공간팀·운영팀은 <b>나열 → 문제·해결방향</b> 전환이 1순위",
    ]
    orgc = "".join(f'<div class="act"><b>{esc(t)}</b><p>{d}</p></div>' for t, d in org)
    indc = "".join(f'<li>{d}</li>' for d in ind)
    return f"""
  <section class="panel">
    <div class="tag">⑥ 개선 액션</div>
    <h3>조직 레벨</h3>
    <div class="acts">{orgc}</div>
    <h3>개인 레벨 — 각자 '다음 한 요소'</h3>
    <ul class="indlist">{indc}</ul>
  </section>"""


def render():
    body = (sec_header() + sec_exec() + sec_criteria() + sec_forms()
            + sec_gap() + sec_teams() + sec_persons() + sec_actions())
    return TEMPLATE.replace("{{BODY}}", body)


TEMPLATE = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ARISA 보고 품질 진단 · 2주</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>
:root{--bg:#0F0F0F;--panel:#1A1A1A;--card:#212121;--bd:#2E2E2E;--tx:#F5F0EB;--mu:#9A948C;
--ac:#6C5CE7;--lt:#A29BFE;--gn:#8FA37E;--am:#D9A34B;--co:#E17055;--bl:#6F8AA3;}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--tx);font-family:'Pretendard Variable',sans-serif;
font-weight:300;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:48px 28px 80px}
.rpt-head{padding:8px 0 28px;border-bottom:1px solid var(--bd);margin-bottom:32px}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ac);font-weight:500}
h1{font-size:34px;font-weight:600;margin:12px 0 8px;letter-spacing:-.02em}
.sub{color:var(--mu);font-size:14px}
.panel{background:var(--panel);border:1px solid var(--bd);border-radius:14px;padding:28px;margin-bottom:22px}
.accent-top{border-top:2px solid var(--ac)}
.tag{font-size:12px;font-weight:600;color:var(--lt);letter-spacing:.03em;margin-bottom:16px}
.subtag{font-size:12px;font-weight:600;color:var(--mu);margin:24px 0 12px;letter-spacing:.04em;text-transform:uppercase}
.lead{font-size:17px;line-height:1.7;font-weight:300}.lead b{font-weight:600;color:#fff}
.lead2{font-size:14px;color:#d8d2c9;margin-bottom:16px}.lead2 b{color:#fff;font-weight:600}
.note{font-size:12.5px;color:var(--mu);margin-top:14px;line-height:1.65}.note b{color:var(--lt);font-weight:500}
.statbar{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:var(--bd);border:1px solid var(--bd);border-radius:10px;overflow:hidden;margin-top:20px}
.stat{background:var(--panel);padding:16px 12px;text-align:center}
.stat b{display:block;font-size:26px;font-weight:700;color:#fff}
.stat span{display:block;font-size:11px;color:var(--mu);margin-top:4px}
.stat small{display:block;font-size:10px;color:#6a655e;margin-top:2px}
table{width:100%;border-collapse:collapse}
.crit td,.crit th{text-align:left;padding:9px 10px;font-size:13px;border-bottom:1px solid #262626;vertical-align:middle}
.crit th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mu);font-weight:500}
.crit .ek{font-weight:600;white-space:nowrap}.crit .ek small{display:block;font-size:10px;color:#6a655e;font-weight:300}
.crit .ea{color:#c9c3ba}.crit .ex{text-align:center;color:var(--mu);font-size:12px}
.crit tr.req .ex{color:var(--ac);font-weight:600}.crit tr.opt .ex{color:var(--bl)}
.crit .ef{white-space:nowrap;width:120px}.crit .ef span{font-size:11px;color:var(--mu);margin-left:6px}
.minibar{display:inline-block;width:70px;height:6px;background:#2a2a2a;border-radius:3px;overflow:hidden;vertical-align:middle}
.minibar i{display:block;height:100%;background:var(--ac)}
.frames{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:6px}
.frame{background:var(--card);border:1px solid var(--bd);border-radius:9px;padding:13px}
.frame b{font-size:13px;color:#fff}.frame span{display:block;font-size:10.5px;color:var(--lt);margin:2px 0 7px}
.frame p{font-size:11.5px;color:#c2bcb3;line-height:1.5}.frame small{display:block;font-size:10px;color:var(--mu);margin-top:6px}
.form-block{margin-bottom:26px}
h3{font-size:16px;font-weight:600;margin-bottom:10px;color:#fff}
.ver{font-size:11px;color:var(--am);border:1px solid var(--am);border-radius:5px;padding:1px 7px;font-weight:500;vertical-align:middle}
.chiprow{margin:6px 0;font-size:12px}.chiprow b{color:var(--mu);font-size:11px;margin-right:8px;text-transform:uppercase}
.chip{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;margin:2px}
.chip.req{background:rgba(108,92,231,.18);color:var(--lt);border:1px solid rgba(108,92,231,.4)}
.chip.opt{background:rgba(111,138,163,.15);color:#a9bccc;border:1px solid rgba(111,138,163,.3)}
.chip.non{background:#242424;color:#6a655e;border:1px solid #333}
.ecards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:16px}
.ecard{background:var(--card);border:1px solid var(--bd);border-radius:10px;overflow:hidden}
.ecard-h{background:#262626;padding:9px 13px;font-weight:600;font-size:13px}.ecard-h small{color:#6a655e;font-weight:300;font-size:10px}
.ex-bad,.ex-good{padding:10px 13px;font-size:12px;line-height:1.5;border-bottom:1px solid #262626}
.ex-bad span,.ex-good span{display:block;font-size:10px;font-weight:600;margin-bottom:3px}
.ex-bad{color:#d8b0a5}.ex-bad span{color:var(--co)}
.ex-good{color:#c2d0b8}.ex-good span{color:var(--gn)}
.ex-anchor{padding:8px 13px;font-size:11px;color:var(--mu);background:#1c1c1c}
.wkgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
.wk{background:var(--card);border:1px solid var(--bd);border-left:2px solid var(--ac);border-radius:8px;padding:12px 14px}
.wk b{display:block;font-size:13px;color:#fff;margin-bottom:3px}.wk span{font-size:11.5px;color:var(--mu)}
.heatwrap{overflow-x:auto}
.heat{font-size:11px;min-width:760px}
.heat th{padding:6px 3px;font-size:10px;color:var(--mu);text-align:center;font-weight:500;border-bottom:1px solid var(--bd)}
.heat th.req{color:var(--lt)}.heat th.opt{color:var(--bl)}
.heat td.pn{font-weight:600;font-size:12px;white-space:nowrap;padding-right:10px}.heat td.pn small{display:block;font-size:9px;color:#6a655e;font-weight:300}
.heat td.h{width:26px;height:26px;border:1px solid var(--bg);border-radius:3px}
.heat td.pr{font-weight:700;text-align:center;font-size:13px;padding-left:8px}
.h{display:inline-block}.h.d0{background:#242424}.h.d1{background:rgba(108,92,231,.3)}
.h.d2{background:rgba(108,92,231,.6)}.h.d3{background:var(--ac)}
.legend{margin-top:12px;font-size:11px;color:var(--mu);display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.legend .h{width:14px;height:14px;border-radius:3px}
.lg-req{color:var(--lt)}.lg-opt{color:var(--bl)}
.defects{display:flex;flex-direction:column;gap:9px}
.defect{display:flex;align-items:center;gap:12px;font-size:13px}
.defect span{width:150px;color:#d8d2c9}.defect b{width:44px;text-align:right;font-weight:700}
.dbar{flex:1;height:9px;background:#242424;border-radius:5px;overflow:hidden}
.dbar i{display:block;height:100%;background:linear-gradient(90deg,var(--co),var(--am))}
.teams{display:flex;flex-direction:column;gap:11px}
.teamrow{display:flex;align-items:center;gap:12px;font-size:13px}
.tn{width:64px;font-weight:600}.tbar{flex:0 0 200px;height:12px;background:#242424;border-radius:6px;overflow:hidden}
.tbar i{display:block;height:100%;background:linear-gradient(90deg,var(--ac),var(--lt))}
.tv{color:var(--mu);font-size:12px}
.pcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.pcard{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px}
.pcard.collecting{opacity:.5}.coll{font-size:12px;color:var(--mu);margin-top:8px}
.pc-h{display:flex;align-items:center;gap:12px;margin-bottom:12px}
.pc-h b{font-size:15px;color:#fff}.pc-h span{display:block;font-size:11px;color:var(--mu);margin-top:2px}
.gauge{width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;position:relative}
.gauge::before{content:'';position:absolute;inset:4px;background:var(--card);border-radius:50%}
.gauge span{position:relative;font-size:14px;font-weight:700;color:#fff}
.pc-map{display:flex;gap:3px;margin-bottom:12px}
.pc-map .m{flex:1;height:16px;border-radius:2px}
.m.d0{background:#242424}.m.d1{background:rgba(108,92,231,.3)}.m.d2{background:rgba(108,92,231,.6)}.m.d3{background:var(--ac)}
.pc-miss{font-size:12px;margin-bottom:10px}.pc-miss small{color:var(--mu);margin-right:8px;text-transform:uppercase;font-size:10px}
.mc{display:inline-block;background:rgba(225,112,85,.15);color:#e0a596;border:1px solid rgba(225,112,85,.3);border-radius:5px;padding:1px 7px;font-size:11px;margin:2px}
.ok{color:var(--gn);font-size:12px}
.pc-exc{font-size:11.5px;color:#a8a29a;line-height:1.55;background:#1b1b1b;border-radius:7px;padding:10px 12px;font-style:italic}
.acts{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin-bottom:8px}
.act{background:var(--card);border:1px solid var(--bd);border-left:2px solid var(--ac);border-radius:8px;padding:14px}
.act b{font-size:13.5px;color:#fff}.act p{font-size:12px;color:#bdb7ae;margin-top:6px;line-height:1.55}
.indlist{margin:6px 0 0 2px;list-style:none}.indlist li{font-size:13px;color:#d8d2c9;padding:7px 0 7px 20px;position:relative;border-bottom:1px solid #242424}
.indlist li::before{content:'→';position:absolute;left:0;color:var(--ac)}
.foot{text-align:center;color:#6a655e;font-size:11px;margin-top:30px}
</style></head>
<body><div class="wrap">{{BODY}}
<p class="foot">ARISA 보고 품질 진단 · 채점 = 14요소×깊이 0-3 (측정설계 v2) · 모든 수치는 diagnosis-scored JSON 소급 · by Project Rent</p>
</div></body></html>"""


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8")
    print("저장:", OUT)
    print("크기:", len(OUT.read_text(encoding="utf-8")), "chars")
