#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
elements.json → 봉은사-요소-마인드맵.html (인터랙티브 마인드맵, 단일 HTML)

usage: python3 build_mindmap.py

- 뼈대 = 슬롯 트리 : L1 STEP(S1~S10) / L2 리프 슬롯 / (S6만 L3 그룹) / 요소
- 한 요소가 n개 슬롯에 걸리면 트리에 n번 나타난다(다대다). 같은 id끼리 ★고스트 링크로 연결.
- 외부 JS 라이브러리 없음. 순수 JS + SVG. 데이터는 인라인 임베드(file:// 로 열려야 함).

⚠️ HTML을 직접 편집하지 말 것. elements.json 을 고치고 이 스크립트를 다시 돌린다.
"""
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "elements.json")
OUT = os.path.join(BASE, "봉은사-요소-마인드맵.html")

# ---------------------------------------------------------------- 슬롯 체계
# 00-슬롯체계.md §1 + 00-슬롯체계-v2.md 의 STEP↔슬롯 매핑 (v2 우선)
STEPS = [
    {"id": "S1", "name": "프로젝트 정의", "en": "Project Define", "slots": [
        ("S1-A", "고려요소·주의사항·제약·리스크", 0),
        ("S1-B", "클라이언트 요구사항·산출물 정의", 0),
        ("S1-C", "우리의 합의·프로젝트 목적", 0),
        ("S1-K", "성공 기준(KPI)", 0),
    ]},
    {"id": "S2", "name": "프로젝트 재정의", "en": "Project Redefine", "slots": [
        ("S2-b1", "불교 전체 — 한국불교의 위치·봉은사의 역할", 0),
        ("S2-b2", "불교 전체 — 문화와 종교, MZ·외국인 접점", 0),
        ("S2-b3", "불교 전체 — 브랜드 가치·지속가능성·공익성", 0),
        ("S2-a1", "봉은사 — 상징성", 0),
        ("S2-a2", "봉은사 — 강남 입지·브랜드 강화", 0),
        ("S2-a3", "봉은사 — 중창불사·전국 사찰·지역 문화공간", 0),
        ("S2-c1", "운영 — 지속가능성(안정적 수익)", 0),
        ("S2-c2", "운영 — 수익성(최대화)", 0),
        ("S2-c3", "운영 — 공공성·사회적 가치", 0),
    ]},
    {"id": "S3", "name": "전략적 선택", "en": "Strategic Decision", "slots": [
        ("S3-C1", "프리미엄 vs 대중화", 0),
        ("S3-C2", "종교시설 vs 문화시설", 0),
        ("S3-C3", "합법 운영 vs 제도 개선", 0),
        ("S3-C4", "중창불사 독립 vs 연계", 0),
        ("S3-C5", "지역 중심 vs 글로벌", 0),
        ("S3-C6", "브랜드 강화 vs 산업화", 0),
        ("S3-X", "선택의 종속관계·파급(매트릭스)", 0),
    ]},
    {"id": "S4", "name": "기회", "en": "Opportunity", "slots": [
        ("S4-O1", "Market — 종교·웰니스·관광·문화 시장", 0),
        ("S4-O2a", "Target — 외국인", 0),
        ("S4-O2b", "Target — 강남 지역주민", 0),
        ("S4-O2c", "Target — MZ", 0),
        ("S4-O2d", "Target — 전국 불교 신자", 0),
        ("S4-O2e", "Target — 기업", 0),
        ("S4-O2f", "Target — VIP", 0),
        ("S4-O3", "시장 공백", 0),
        ("S4-O4", "Location — 입지·코엑스·상징성·스케일", 0),
        ("S4-O5", "Timing — 왜 지금인가", 0),
    ]},
    {"id": "S5", "name": "벤치마크", "en": "Benchmark", "slots": [
        ("S5-BM1", "국내 종교시설", 0),
        ("S5-BM2", "해외 종교시설", 0),
        ("S5-BM3", "문화시설 × 지역연계", 0),
        ("S5-BM4", "웰니스 시설·멤버십", 0),
        ("S5-BM5", "관광시설", 0),
        ("S5-BMX", "결론 — 매스/로컬/프리미엄 (v1, → S7 이관 대상)", 1),
    ]},
    {"id": "S6", "name": "서비스 라이브러리", "en": "Service Library", "slots": [
        ("S6-RAW", "서비스·콘텐츠 전량 (그룹 G1~G10)", 0),
    ]},
    {"id": "S7", "name": "전략 매트릭스", "en": "Strategy Matrix", "slots": [
        ("S7-MTX", "시장→타겟→서비스→BM→법률→운영→브랜드→확장성", 0),
    ]},
    {"id": "S8", "name": "미래 시나리오", "en": "Future Scenario", "slots": [
        ("S8-A", "A안 · Buddhist Cultural Destination (도달)", 0),
        ("S8-B", "B안 · Buddhist Wellness & Lifestyle (깊이·단가)", 0),
        ("S8-C", "C안 · Buddhist Business Innovation Lab (파급)", 0),
        ("S8-P1", "글로벌 불교문화 허브 (v1)", 1),
        ("S8-P2", "강남 로컬 웰니스 (v1)", 1),
        ("S8-P3", "정신문화 거점 (v1 · A안에 병합)", 1),
        ("S8-P4", "BM 중심 (v1)", 1),
        ("S8-FINAL", "최종 3안 × 3-Track (v1 · → S10 개칭)", 1),
    ]},
    {"id": "S9", "name": "시나리오 평가", "en": "Scenario Evaluation", "slots": [
        ("S9-EVAL", "A·B·C 동일 10축 평가", 0),
    ]},
    {"id": "S10", "name": "최종 제언", "en": "Final Recommendation", "slots": [
        ("S10-REC", "Core / Support / Roadmap", 0),
    ]},
]

STEP_DESC = {
    "S1": "계약·과업이 정의한 경계",
    "S2": "누구의 입장에서 다시 묻는가",
    "S3": "무엇을 고르면 무엇이 따라오는가",
    "S4": "시장·타겟·자산·타이밍",
    "S5": "누가 무엇을 해서 성공했나",
    "S6": "이 공간에 무엇이 존재할 수 있나",
    "S7": "모든 축을 하나로 연결",
    "S8": "각각 독립 완결된 세 컨셉",
    "S9": "동일 기준 평가",
    "S10": "우선할 전략축 제안",
}


def build():
    with open(SRC, encoding="utf-8") as f:
        els = json.load(f)

    ids = [e["id"] for e in els]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        raise SystemExit(f"중복 id: {dup}")

    known = {s[0] for st in STEPS for s in st["slots"]}
    used = Counter()
    for e in els:
        for s in e.get("slots", []):
            used[s] += 1
    unknown = sorted(set(used) - known)
    if unknown:
        # 체계에 없는 슬롯은 '기타' STEP으로 흡수 (조용히 버리지 않는다)
        STEPS.append({"id": "SX", "name": "체계 외 슬롯", "en": "Unmapped",
                      "slots": [(s, "⚠ 슬롯체계 문서에 없음", 1) for s in unknown]})
        STEP_DESC["SX"] = "00-슬롯체계-v2.md 에 정의되지 않은 슬롯"

    idset = set(ids)
    dangling = sorted({x["to"] for e in els for x in (e.get("edges") or []) if x.get("to") not in idset}
                      | {d for e in els for d in (e.get("derived_from") or []) if d not in idset})

    occurrences = sum(used.values())
    empty_slots = sorted(known - set(used))

    steps_js = json.dumps([
        {"id": st["id"], "name": st["name"], "en": st["en"], "desc": STEP_DESC.get(st["id"], ""),
         "slots": [{"id": s[0], "name": s[1], "legacy": bool(s[2])} for s in st["slots"]]}
        for st in STEPS], ensure_ascii=False, separators=(",", ":"))

    data_js = json.dumps(els, ensure_ascii=False, separators=(",", ":"))
    # </script> 방어
    data_js = data_js.replace("<", "\\u003c")
    steps_js = steps_js.replace("<", "\\u003c")

    html = TEMPLATE
    html = html.replace("__STEPS__", steps_js)
    html = html.replace("__DATA__", data_js)
    html = html.replace("__GEN__", datetime.now().strftime("%Y-%m-%d %H:%M"))
    html = html.replace("__NEL__", str(len(els)))
    html = html.replace("__NOCC__", str(occurrences))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ {os.path.relpath(OUT, BASE)}  ({os.path.getsize(OUT)/1024:.0f} KB)")
    print(f"   요소 {len(els)} · 슬롯 출현(=요소 노드) {occurrences} · 사용 슬롯 {len(used)} / 정의 슬롯 {len(known)}")
    print(f"   confidence {dict(Counter(e.get('confidence') for e in els))}")
    print(f"   ownership  {dict(Counter(e.get('ownership') for e in els))}")
    ed = Counter(x.get("rel") for e in els for x in (e.get("edges") or []))
    print(f"   edges {sum(ed.values())} {dict(ed)} · derived_from {sum(len(e.get('derived_from') or []) for e in els)}")
    print(f"   빈 슬롯 {len(empty_slots)}: {' '.join(empty_slots) if empty_slots else '-'}")
    if dangling:
        print(f"   ⚠ 참조 깨진 id {len(dangling)}: {' '.join(dangling[:12])}")
    # 트리 노드 총계(전개 시): root + step + slot + S6그룹 + 요소출현
    groups = {e.get("group") or "기타" for e in els if "S6-RAW" in e.get("slots", [])}
    total_nodes = 1 + len(STEPS) + len(known) + len(groups) + occurrences
    print(f"   트리 전개 시 총 노드 {total_nodes} (root 1 + step {len(STEPS)} + slot {len(known)} + S6그룹 {len(groups)} + 요소노드 {occurrences})")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>봉은사 재구조화 — 요소 마인드맵</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>
:root{
  --bg:#1A1A1A; --fg:#F5F0EB; --accent:#6C5CE7; --fg-3:#7A7570; --line:#333;
  --panel:#202020; --panel-2:#252525;
  --cA:#6C5CE7; --cB:#6F8AA3; --cC:#6B6560;
  --warn:#E05252; --ok:#5CB88A;
}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{
  background:var(--bg); color:var(--fg);
  font-family:'Pretendard Variable',Pretendard,-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
  font-size:13px; overflow:hidden;
}
button,input,select{font-family:inherit}

/* ---------- header ---------- */
header{
  position:relative; z-index:5;
  padding:10px 16px 8px; border-bottom:1px solid var(--line); background:#151515;
  display:flex; flex-wrap:wrap; gap:10px 18px; align-items:center;
}
h1{font-size:14px;margin:0;font-weight:700;letter-spacing:-.02em;white-space:nowrap}
h1 small{display:block;font-size:10px;color:var(--fg-3);font-weight:400;letter-spacing:0}
.counters{display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.ct{font-size:11px;color:var(--fg-3);white-space:nowrap}
.ct b{color:var(--fg);font-size:14px;font-weight:700;margin-right:3px}
.chip{display:inline-flex;align-items:center;gap:4px;font-size:11px;color:var(--fg-3)}
.dot{width:8px;height:8px;border-radius:2px;display:inline-block}
.spacer{flex:1}
.search{
  background:#101010;border:1px solid var(--line);color:var(--fg);
  border-radius:6px;padding:6px 10px;width:230px;outline:none;font-size:12px;
}
.search:focus{border-color:var(--accent)}
.btn{
  background:#101010;border:1px solid var(--line);color:var(--fg-3);
  border-radius:6px;padding:6px 9px;cursor:pointer;font-size:11px;white-space:nowrap;
}
.btn:hover{border-color:#555;color:var(--fg)}
.btn.on{background:rgba(108,92,231,.18);border-color:var(--accent);color:var(--fg)}

/* ---------- filter bar ---------- */
#filters{
  border-bottom:1px solid var(--line);background:#131313;padding:7px 16px;
  display:none; gap:18px; flex-wrap:wrap; align-items:flex-start; font-size:11px;
}
#filters.open{display:flex}
.fg{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.fg > span.lbl{color:var(--fg-3);margin-right:2px;min-width:64px}
.tog{
  border:1px solid var(--line);border-radius:20px;padding:3px 9px;cursor:pointer;
  color:var(--fg-3);background:#101010;user-select:none;
}
.tog.on{color:var(--fg);border-color:#5b5b5b;background:#1e1e1e}
.tog.on[data-k="conf"][data-v="A"]{border-color:var(--cA);color:#c3b9ff}
.tog.on[data-k="conf"][data-v="B"]{border-color:var(--cB);color:#bcd2df}
.tog.on[data-k="conf"][data-v="C"]{border-color:#8a8378;color:#c9c2b8}

/* ---------- layout ---------- */
#main{position:absolute;top:0;left:0;right:0;bottom:0;display:flex;padding-top:0}
#stage{flex:1;position:relative;overflow:hidden;cursor:grab}
#stage.drag{cursor:grabbing}
svg{width:100%;height:100%;display:block;user-select:none}
#hint{
  position:absolute;left:14px;bottom:12px;font-size:10.5px;color:var(--fg-3);
  background:rgba(20,20,20,.82);border:1px solid var(--line);border-radius:6px;padding:6px 10px;
  line-height:1.7;pointer-events:none;
}
#hint b{color:#a99ff0}
#status{
  position:absolute;right:14px;bottom:12px;font-size:10.5px;color:var(--fg-3);
  background:rgba(20,20,20,.82);border:1px solid var(--line);border-radius:6px;padding:6px 10px;
}

/* ---------- svg nodes ---------- */
.link{fill:none;stroke:#2E2E2E;stroke-width:1}
.link.hl{stroke:#5b4fbf;stroke-width:1.4}
.ghost{fill:none;stroke:var(--accent);stroke-width:1.4;stroke-dasharray:4 4;opacity:.85}
.ghost.dim{opacity:.28;stroke-width:1}
.edge{fill:none;stroke-width:1.3;opacity:.8}
.edge.supports{stroke:#5CB88A}
.edge.enables{stroke:#4FA3C7}
.edge.precedent_for{stroke:#B08CD9}
.edge.blocks{stroke:#D98C4F;stroke-dasharray:5 3}
.edge.contradicts{stroke:var(--warn);stroke-width:2.2;stroke-dasharray:none}
.nd{cursor:pointer}
.nd text{font-size:12px;fill:var(--fg);dominant-baseline:middle}
.nd .sub{fill:var(--fg-3);font-size:10.5px}
.nd.step text{font-size:14.5px;font-weight:700;letter-spacing:-.01em}
.nd.slot text{font-size:12.5px;font-weight:600}
.nd.group text{font-size:12px;font-weight:600;fill:#cfc8c0}
.nd.el text{font-size:11.5px}
.nd.el.dimmed{opacity:.22}
.nd.hit{fill:transparent}
.mk{stroke-width:1.2}
.nd.el.own .mk{stroke-width:2.6}
.nd.el.confC .mk{stroke-dasharray:2.2 2}
.nd.sel > .halo{fill:rgba(108,92,231,.22);stroke:var(--accent);stroke-width:1}
.nd.occ > .halo{fill:rgba(108,92,231,.13);stroke:rgba(108,92,231,.55);stroke-width:1;stroke-dasharray:3 3}
.nd.match > .halo{fill:rgba(230,180,60,.16);stroke:#E0B23C;stroke-width:1}
.nd.sel text,.nd.match text{fill:#fff;font-weight:700}
.caret{fill:var(--fg-3)}
.nd.step .caret{fill:#9a938c}
.badge{font-size:9.5px;fill:var(--fg-3)}

/* ---------- panel ---------- */
#panel{
  width:392px;min-width:392px;border-left:1px solid var(--line);background:var(--panel);
  overflow-y:auto;padding:16px 18px 60px;
}
#panel.empty{display:flex;align-items:center;justify-content:center;color:var(--fg-3);text-align:center;padding:30px}
#panel h2{font-size:15px;margin:0 0 2px;letter-spacing:-.02em;line-height:1.35}
.pid{font-size:10.5px;color:var(--fg-3);font-family:ui-monospace,Menlo,monospace;letter-spacing:.02em}
.stm{font-size:13px;line-height:1.72;margin:12px 0 14px;color:#EDE7E0}
.meta{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0 4px}
.tag{font-size:10.5px;padding:2.5px 7px;border-radius:4px;background:#2b2b2b;color:#cfc8c0;border:1px solid #363636}
.tag.A{background:rgba(108,92,231,.2);border-color:var(--cA);color:#c3b9ff}
.tag.B{background:rgba(111,138,163,.18);border-color:var(--cB);color:#bcd2df}
.tag.C{background:#262626;border-color:#5a544c;color:#a49d95;border-style:dashed}
.tag.own{border-color:#8a7fe0;color:#c3b9ff}
.sec{margin:16px 0 0;border-top:1px solid #2b2b2b;padding-top:12px}
.sec > h3{font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--fg-3);margin:0 0 7px;font-weight:600}
.angle{
  background:var(--panel-2);border-left:2px solid var(--accent);padding:9px 11px;
  border-radius:0 5px 5px 0;font-size:12px;line-height:1.65;color:#DCD6CF;margin-bottom:7px;
}
.angle .sl{display:block;font-size:10px;color:#9b93ea;margin-bottom:3px;font-weight:600;letter-spacing:.02em}
.angle.here{border-left-color:#E0B23C;background:#2a2620}
.angle.here .sl{color:#E0B23C}
.row{display:flex;gap:8px;font-size:11.5px;line-height:1.6;padding:4px 0;border-bottom:1px solid #262626}
.row:last-child{border-bottom:0}
.row .k{color:var(--fg-3);min-width:66px;flex-shrink:0}
.row .v{color:#DCD6CF;word-break:break-word}
.num{background:var(--panel-2);border-radius:5px;padding:7px 9px;margin-bottom:5px;font-size:11.5px;line-height:1.55}
.num b{color:#c3b9ff;font-size:13px}
.lnk{color:#9b93ea;cursor:pointer;text-decoration:none;border-bottom:1px dotted #6C5CE7}
.lnk:hover{color:#c3b9ff}
.occ{
  display:flex;gap:7px;align-items:baseline;padding:6px 8px;border-radius:5px;cursor:pointer;
  font-size:11.5px;line-height:1.5;margin-bottom:3px;background:var(--panel-2);border:1px solid transparent;
}
.occ:hover{border-color:var(--accent)}
.occ.cur{border-color:#E0B23C;background:#2a2620}
.occ code{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;color:#9b93ea;flex-shrink:0}
.rel{display:flex;gap:7px;align-items:baseline;padding:5px 0;font-size:11.5px;line-height:1.5}
.rel .r{font-size:9.5px;padding:1.5px 5px;border-radius:3px;flex-shrink:0;border:1px solid}
.r.supports{color:#5CB88A;border-color:#2f6b4d}
.r.contradicts{color:#fff;background:var(--warn);border-color:var(--warn);font-weight:700}
.r.enables{color:#4FA3C7;border-color:#2e5f74}
.r.blocks{color:#D98C4F;border-color:#7a4f28}
.r.precedent_for{color:#B08CD9;border-color:#5d4577}
.r.derived{color:#9b93ea;border-color:#4a428f}
.src{font-size:10.5px;color:var(--fg-3);line-height:1.6;margin-bottom:4px;word-break:break-all}
.evgrid{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;text-align:center}
.ev{background:var(--panel-2);border-radius:5px;padding:6px 2px}
.ev .l{font-size:9px;color:var(--fg-3);display:block;margin-bottom:3px}
.ev .v{font-size:13px;font-weight:700}
.ev .v.H{color:#5CB88A}.ev .v.M{color:#E0B23C}.ev .v.L{color:#9b8f85}
.ev .v.Tier1{color:#5CB88A;font-size:11px}.ev .v.Tier2{color:#E0B23C;font-size:11px}.ev .v.Tier3{color:var(--warn);font-size:11px}
::-webkit-scrollbar{width:9px;height:9px}
::-webkit-scrollbar-thumb{background:#3a3a3a;border-radius:5px}
::-webkit-scrollbar-track{background:transparent}
</style>
</head>
<body>

<div id="main">
  <div style="flex:1;display:flex;flex-direction:column;min-width:0">
    <header>
      <h1>봉은사 재구조화 · 요소 마인드맵<small>슬롯 트리 × 다대다 요소 배치 · elements.json 자동 생성 __GEN__</small></h1>
      <div class="counters">
        <span class="ct"><b id="cEl">__NEL__</b>요소</span>
        <span class="ct"><b id="cOcc">__NOCC__</b>슬롯 출현</span>
        <span class="ct"><b id="cSlot">0</b>슬롯</span>
        <span class="ct"><b id="cMulti">0</b>중복배치 요소</span>
        <span class="chip"><i class="dot" style="background:var(--cA)"></i>A <b id="cA" style="color:var(--fg)">0</b></span>
        <span class="chip"><i class="dot" style="background:var(--cB)"></i>B <b id="cB" style="color:var(--fg)">0</b></span>
        <span class="chip"><i class="dot" style="background:transparent;border:1px dashed #8a8378"></i>C <b id="cC" style="color:var(--fg)">0</b></span>
      </div>
      <span class="spacer"></span>
      <input id="q" class="search" placeholder="검색 — 라벨·문장·ID·슬롯 (Enter로 다음)">
      <button class="btn" id="bFilter">필터</button>
      <button class="btn" id="bEdges">관계선</button>
      <button class="btn" id="bGhostAll">고스트 전체</button>
      <button class="btn" id="bExpand">전체 펼침</button>
      <button class="btn" id="bCollapse">L2로 접기</button>
      <button class="btn" id="bFit">화면 맞춤</button>
    </header>
    <div id="filters"></div>
    <div id="stage">
      <svg id="svg"><g id="scene">
        <g id="gLinks"></g><g id="gEdges"></g><g id="gGhost"></g><g id="gNodes"></g>
      </g></svg>
      <div id="hint">
        <b>클릭</b> 노드 펼침/접기 · 요소 클릭 = 선택 &amp; <b>모든 출현 위치 동시 하이라이트</b><br>
        <b>휠</b> 확대/축소 · <b>드래그</b> 이동 · <b>Esc</b> 선택 해제
      </div>
      <div id="status"></div>
    </div>
  </div>
  <div id="panel" class="empty"><div>요소 노드를 클릭하면<br>상세와 모든 출현 위치가 여기에 표시된다.</div></div>
</div>

<script>
const STEPS = __STEPS__;
const DATA  = __DATA__;
</script>
<script>
(function(){
"use strict";
const SVGNS="http://www.w3.org/2000/svg";
const $=s=>document.querySelector(s);
const gLinks=$("#gLinks"),gEdges=$("#gEdges"),gGhost=$("#gGhost"),gNodes=$("#gNodes"),scene=$("#scene"),svg=$("#svg");

/* ============================ 데이터 색인 ============================ */
const byId={}; DATA.forEach(e=>byId[e.id]=e);
const occByEl={};                        // id -> [node]
const KINDS=[...new Set(DATA.map(e=>e.kind))].sort();
const OWNS=["own","reference","context","constraint"];
const CONFS=["A","B","C"];
const SCEN=["A","B","C","미지정"];
const CONF_COLOR={A:"#6C5CE7",B:"#6F8AA3",C:"#6B6560"};
const KIND_KO={fact:"사실",constraint:"제약",case:"사례",insight:"통찰",option:"선택지",
  service:"서비스",risk:"리스크",requirement:"요구사항",asset:"자산",actor:"주체"};
const OWN_KO={own:"봉은사 보유",reference:"남의 사례",context:"시장·환경",constraint:"법·계약 제약"};
const POL_KO={pro:"지지",con:"반대",neutral:"중립"};
const REL_KO={supports:"지지",contradicts:"모순",enables:"가능케함",blocks:"차단",precedent_for:"선례"};

const slotMeta={}; STEPS.forEach(st=>st.slots.forEach(s=>slotMeta[s.id]={...s,step:st.id}));

/* ============================ 트리 구축 ============================ */
let KEY=0;
function N(o){o.key="n"+(KEY++);o.children=o.children||[];return o;}
const root=N({type:"root",label:"봉은문화센터",sub:"미래의 불교와 사회를 연결하는 어떤 플랫폼이 되어야 하는가",expanded:true});

const bySlot={}; DATA.forEach(e=>(e.slots||[]).forEach(s=>(bySlot[s]=bySlot[s]||[]).push(e)));

function elNode(e,slot,parent){
  const n=N({type:"el",elId:e.id,slot:slot,label:e.label,el:e,parent:parent,expanded:false});
  (occByEl[e.id]=occByEl[e.id]||[]).push(n);
  return n;
}
STEPS.forEach(st=>{
  const sn=N({type:"step",label:st.id+". "+st.name,sub:st.desc,en:st.en,parent:root,expanded:true});
  st.slots.forEach(s=>{
    const items=(bySlot[s.id]||[]);
    const sl=N({type:"slot",slotId:s.id,label:s.id,sub:s.name,legacy:s.legacy,parent:sn,expanded:false});
    if(s.id==="S6-RAW"){
      const gm={};
      items.forEach(e=>{const g=e.group||"⚠ 미그루핑"; (gm[g]=gm[g]||[]).push(e);});
      const gnum=g=>{const m=/^G(\d+)/.exec(g);return m?+m[1]:999;};
      Object.keys(gm).sort((a,b)=>gnum(a)-gnum(b)||a.localeCompare(b)).forEach(g=>{
        const gn=N({type:"group",label:g,parent:sl,expanded:false});
        gm[g].forEach(e=>gn.children.push(elNode(e,s.id,gn)));
        sl.children.push(gn);
      });
    }else{
      items.forEach(e=>sl.children.push(elNode(e,s.id,sl)));
    }
    sn.children.push(sl);
  });
  root.children.push(sn);
});

const allNodes=[]; (function w(n){allNodes.push(n);n.children.forEach(w);})(root);
const nodeByKey={}; allNodes.forEach(n=>nodeByKey[n.key]=n);
const TOTAL_EL_NODES=allNodes.filter(n=>n.type==="el").length;

/* 헤더 카운터 */
$("#cSlot").textContent=Object.keys(bySlot).length;
$("#cMulti").textContent=DATA.filter(e=>(e.slots||[]).length>1).length;
$("#cOcc").textContent=TOTAL_EL_NODES;
CONFS.forEach(c=>$("#c"+c).textContent=DATA.filter(e=>e.confidence===c).length);

/* ============================ 필터 ============================ */
const F={conf:new Set(CONFS),own:new Set(OWNS),kind:new Set(KINDS),scen:new Set(SCEN)};
(function buildFilters(){
  const box=$("#filters");
  const mk=(label,k,vals,fmt)=>{
    const d=document.createElement("div");d.className="fg";
    d.innerHTML='<span class="lbl">'+label+'</span>'+vals.map(v=>
      '<span class="tog on" data-k="'+k+'" data-v="'+v+'">'+(fmt?fmt(v):v)+'</span>').join("")
      +'<span class="tog" data-k="'+k+'" data-v="__all">전체</span>';
    box.appendChild(d);
  };
  mk("confidence","conf",CONFS,v=>v+" ("+DATA.filter(e=>e.confidence===v).length+")");
  mk("ownership","own",OWNS,v=>OWN_KO[v]+" ("+DATA.filter(e=>e.ownership===v).length+")");
  mk("kind","kind",KINDS,v=>(KIND_KO[v]||v)+" ("+DATA.filter(e=>e.kind===v).length+")");
  mk("scenario","scen",SCEN,v=>v+" ("+DATA.filter(e=>scenOf(e).includes(v)).length+")");
  box.addEventListener("click",ev=>{
    const t=ev.target.closest(".tog"); if(!t)return;
    const k=t.dataset.k,v=t.dataset.v;
    if(v==="__all"){ const all={conf:CONFS,own:OWNS,kind:KINDS,scen:SCEN}[k]; F[k]=new Set(all); }
    else { F[k].has(v)?F[k].delete(v):F[k].add(v); }
    box.querySelectorAll('.tog[data-k="'+k+'"]').forEach(x=>{
      if(x.dataset.v!=="__all") x.classList.toggle("on",F[k].has(x.dataset.v));
    });
    render();
  });
})();
function scenOf(e){ const s=e.scenario; return (s&&s.length)?s:["미지정"]; }
function pass(e){
  if(!F.conf.has(e.confidence))return false;
  if(!F.own.has(e.ownership))return false;
  if(!F.kind.has(e.kind))return false;
  if(!scenOf(e).some(s=>F.scen.has(s)))return false;
  return true;
}
function kids(n){ return n.type==="el"?[]:n.children.filter(c=>c.type!=="el"?visCount(c)>0||c.type==="slot"||c.type==="step":pass(c.el)); }
const _vc=new Map();
function visCount(n){
  if(n.type==="el")return pass(n.el)?1:0;
  if(_vc.has(n))return _vc.get(n);
  let s=0; n.children.forEach(c=>s+=visCount(c)); _vc.set(n,s); return s;
}

/* ============================ 레이아웃 ============================ */
const ROW=19, COLX=[0,26,250,560,860,1130];
let laid=[],links=[];
function layout(){
  _vc.clear(); laid=[];links=[]; let y=0;
  (function walk(n,depth){
    n.depth=depth; n.x=COLX[Math.min(depth,COLX.length-1)];
    const ch=kids(n);
    n._n=ch.length;
    if(n.expanded&&ch.length){
      ch.forEach(c=>{walk(c,depth+1);links.push([n,c]);});
      n.y=(ch[0].y+ch[ch.length-1].y)/2;
    }else{ n.y=y; y+=ROW; }
    laid.push(n);
  })(root,0);
}

/* ============================ 렌더 ============================ */
let sel=null, selKey=null, matches=new Set(), showEdges=false, showGhostAll=false;
const esc=s=>String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
function tw(s,fs){ // 대략적 텍스트 폭
  let w=0; for(const ch of String(s)) w+= (ch.charCodeAt(0)>0x2000?1.0:0.55);
  return w*fs;
}
function curve(x1,y1,x2,y2){const mx=(x1+x2)/2;return "M"+x1+","+y1+"C"+mx+","+y1+" "+mx+","+y2+" "+x2+","+y2;}

function render(){
  layout();
  const hlKeys=new Set();
  if(sel){ (occByEl[sel]||[]).forEach(n=>{ let p=n; while(p){hlKeys.add(p.key);p=p.parent;} }); }

  // links
  let s="";
  for(const [a,b] of links){
    s+='<path class="link'+(hlKeys.has(b.key)?" hl":"")+'" d="'+curve(a.x+7,a.y,b.x-4,b.y)+'"/>';
  }
  gLinks.innerHTML=s;

  // nodes
  const buf=[];
  for(const n of laid){
    const cls=["nd",n.type];
    let mk="",txt="",sub="",fs=12,tx=14;
    if(n.type==="el"){
      const e=n.el, c=CONF_COLOR[e.confidence]||"#666";
      cls.push("conf"+e.confidence);
      if(e.ownership==="own")cls.push("own");
      if(sel&&e.id===sel)cls.push(selKey===n.key?"sel":"occ");
      if(matches.has(n.key))cls.push("match");
      if(sel&&e.id!==sel&&hlKeys.size)cls.push("dimmed");
      const fill=e.confidence==="C"?"none":c;
      mk='<rect class="mk" x="-5" y="-5" width="10" height="10" rx="2" fill="'+fill+'" stroke="'+c+'"/>';
      fs=11.5;tx=12;
      txt=esc(e.label);
      const nslot=(e.slots||[]).length;
      sub=(nslot>1?" ★"+nslot:"")+((e.edges||[]).some(x=>x.rel==="contradicts")?" ⚡":"");
    }else{
      const open=n.expanded&&n._n>0;
      if(n.type==="root"){fs=16;tx=16;mk='<circle class="mk" r="7" fill="#6C5CE7" stroke="#b9b0ff"/>';}
      else{
        mk='<path class="caret" d="'+(open?"M-5,-3L5,-3L0,4Z":"M-3,-5L4,0L-3,5Z")+'"/>';
        if(n.type==="step"){fs=14.5;tx=14;}
        else if(n.type==="slot"){fs=12.5;tx=12;}
        else {fs=12;tx=12;}
      }
      txt=esc(n.label);
      if(n.type==="slot"){ sub="  "+esc(n.sub)+"  ("+visCount(n)+")"; if(n.legacy)sub+=" ·v1"; }
      else if(n.type==="group"){ sub="  ("+visCount(n)+")"; }
      else if(n.type==="step"){ sub="  "+esc(n.sub||"")+"  ["+visCount(n)+"]"; }
      else if(n.type==="root"){ sub="  "+visCount(n)+"개 요소 배치"; }
      if(matches.has(n.key))cls.push("match");
      if(hlKeys.has(n.key))cls.push("onpath");
    }
    const w=tw(txt,fs)+tw(sub,10.5)+tx+14;
    const halo=(cls.includes("sel")||cls.includes("occ")||cls.includes("match"))
      ? '<rect class="halo" x="'+(tx-5)+'" y="-9" width="'+(w-tx+6)+'" height="18" rx="4"/>':"";
    buf.push('<g class="'+cls.join(" ")+'" data-k="'+n.key+'" transform="translate('+n.x+','+n.y+')">'
      +'<rect class="hit" x="-8" y="-9" width="'+(w+8)+'" height="18"/>'
      +halo+mk
      +'<text x="'+tx+'" style="font-size:'+fs+'px">'+txt
      +(sub?'<tspan class="sub">'+sub+'</tspan>':"")+'</text></g>');
  }
  gNodes.innerHTML=buf.join("");

  drawGhost(); drawEdges();
  $("#status").textContent="노드 "+laid.length+" / 요소노드 "+laid.filter(n=>n.type==="el").length
    +" (전체 "+TOTAL_EL_NODES+")"+(sel?" · 선택 "+sel:"");
}

/* ---- 고스트 링크 : 같은 id의 모든 출현을 잇는다 ---- */
function ghostPath(a,b){
  const rx=Math.max(a.x,b.x)+70+Math.min(180,Math.abs(a.y-b.y)*0.25);
  return "M"+(a.x+9)+","+a.y+"C"+rx+","+a.y+" "+rx+","+b.y+" "+(b.x+9)+","+b.y;
}
function drawGhost(){
  const vis=new Set(laid.map(n=>n.key)); let s="";
  const draw=(id,dim)=>{
    const ns=(occByEl[id]||[]).filter(n=>vis.has(n.key));
    if(ns.length<2)return;
    const a=ns[0];
    for(let i=1;i<ns.length;i++) s+='<path class="ghost'+(dim?" dim":"")+'" d="'+ghostPath(a,ns[i])+'"/>';
  };
  if(showGhostAll){
    const seen=new Set();
    laid.forEach(n=>{if(n.type==="el"&&!seen.has(n.elId)){seen.add(n.elId);if(n.elId!==sel)draw(n.elId,true);}});
  }
  if(sel)draw(sel,false);
  gGhost.innerHTML=s;
}

/* ---- 관계선(edges) ---- */
function firstVis(id){ const vis=new Set(laid.map(n=>n.key)); return (occByEl[id]||[]).find(n=>vis.has(n.key)); }
function drawEdges(){
  let s="";
  const vis=new Set(laid.map(n=>n.key));
  const seen=new Set();
  const put=(from,to,rel)=>{
    const k=from.key+">"+to.key+rel; if(seen.has(k))return; seen.add(k);
    s+='<path class="edge '+rel+'" d="'+ghostPath(from,to)+'"/>';
  };
  const pairs=[];
  if(showEdges){
    DATA.forEach(e=>(e.edges||[]).forEach(x=>pairs.push([e.id,x.to,x.rel])));
  }else if(sel){
    (byId[sel].edges||[]).forEach(x=>pairs.push([sel,x.to,x.rel]));
    DATA.forEach(e=>(e.edges||[]).forEach(x=>{if(x.to===sel)pairs.push([e.id,sel,x.rel]);}));
  }
  pairs.forEach(([a,b,rel])=>{
    const na=(occByEl[a]||[]).find(n=>vis.has(n.key)), nb=(occByEl[b]||[]).find(n=>vis.has(n.key));
    if(na&&nb&&na!==nb)put(na,nb,rel);
  });
  gEdges.innerHTML=s;
}

/* ============================ 상호작용 ============================ */
function expandTo(n){ let p=n.parent; while(p){p.expanded=true;p=p.parent;} }
function selectEl(id,node){
  sel=id; selKey=node?node.key:null;
  (occByEl[id]||[]).forEach(expandTo);
  const e=byId[id];
  (e.edges||[]).forEach(x=>{const t=(occByEl[x.to]||[])[0]; if(t)expandTo(t);});
  (e.derived_from||[]).forEach(d=>{const t=(occByEl[d]||[])[0]; if(t)expandTo(t);});
  panel(id,node);
  render();
}
gNodes.addEventListener("click",ev=>{
  const g=ev.target.closest(".nd"); if(!g)return;
  const n=nodeByKey[g.dataset.k];
  if(n.type==="el"){ selectEl(n.elId,n); }
  else { n.expanded=!n.expanded; render(); }
});

/* ---- zoom / pan ---- */
let tx=60,ty=40,k=1;
function apply(){scene.setAttribute("transform","translate("+tx+","+ty+") scale("+k+")");}
apply();
const stage=$("#stage");
stage.addEventListener("wheel",ev=>{
  ev.preventDefault();
  const r=svg.getBoundingClientRect(), mx=ev.clientX-r.left, my=ev.clientY-r.top;
  const f=Math.exp(-ev.deltaY*0.0016), nk=Math.min(3,Math.max(0.08,k*f)), rf=nk/k;
  tx=mx-(mx-tx)*rf; ty=my-(my-ty)*rf; k=nk; apply();
},{passive:false});
let dr=null;
stage.addEventListener("mousedown",ev=>{ if(ev.button!==0)return; dr={x:ev.clientX,y:ev.clientY,tx:tx,ty:ty}; stage.classList.add("drag"); });
window.addEventListener("mousemove",ev=>{ if(!dr)return; tx=dr.tx+(ev.clientX-dr.x); ty=dr.ty+(ev.clientY-dr.y); apply(); });
window.addEventListener("mouseup",()=>{dr=null;stage.classList.remove("drag");});
function centerOn(n){
  const r=svg.getBoundingClientRect();
  tx=r.width*0.34-n.x*k; ty=r.height/2-n.y*k; apply();
}
function fit(){
  if(!laid.length)return;
  const b=gNodes.getBBox(), r=svg.getBoundingClientRect(), pad=26;
  if(!b.width||!b.height)return;
  k=Math.min(1.15,Math.max(0.04,Math.min((r.width-pad*2)/b.width,(r.height-pad*2)/b.height)));
  tx=pad-b.x*k; ty=Math.max(pad,(r.height-b.height*k)/2)-b.y*k; apply();
}
window.addEventListener("resize",()=>{clearTimeout(window.__rz);window.__rz=setTimeout(fit,180);});

/* ---- 검색 ---- */
let hits=[],hitI=-1;
function search(q){
  matches=new Set(); hits=[];
  q=q.trim().toLowerCase();
  if(!q){render();return;}
  const els=DATA.filter(e=>
    e.id.toLowerCase().includes(q)||
    (e.label||"").toLowerCase().includes(q)||
    (e.statement||"").toLowerCase().includes(q)||
    (e.group||"").toLowerCase().includes(q)
  );
  els.slice(0,400).forEach(e=>(occByEl[e.id]||[]).forEach(n=>{
    if(!pass(e))return; matches.add(n.key); expandTo(n); hits.push(n);
  }));
  laid.forEach(()=>{});
  allNodes.forEach(n=>{
    if(n.type==="slot"&&((n.slotId||"").toLowerCase().includes(q)||(n.sub||"").toLowerCase().includes(q))){
      matches.add(n.key); expandTo(n); hits.push(n);
    }
    if(n.type==="step"&&(n.label||"").toLowerCase().includes(q)){matches.add(n.key);expandTo(n);hits.push(n);}
  });
  hitI=-1; render();
  $("#status").textContent="검색 “"+q+"” — "+els.length+"개 요소 / "+hits.length+"개 노드 매칭";
}
let dbt; $("#q").addEventListener("input",e=>{clearTimeout(dbt);dbt=setTimeout(()=>search(e.target.value),160);});
$("#q").addEventListener("keydown",e=>{
  if(e.key!=="Enter"||!hits.length)return;
  hitI=(hitI+1)%hits.length; const n=hits[hitI];
  if(n.type==="el"){selectEl(n.elId,n);} else render();
  centerOn(n);
});

/* ---- 버튼 ---- */
$("#bFilter").onclick=e=>{$("#filters").classList.toggle("open");e.target.classList.toggle("on");};
$("#bEdges").onclick=e=>{showEdges=!showEdges;e.target.classList.toggle("on",showEdges);render();};
$("#bGhostAll").onclick=e=>{showGhostAll=!showGhostAll;e.target.classList.toggle("on",showGhostAll);render();};
$("#bExpand").onclick=()=>{allNodes.forEach(n=>{if(n.type!=="el")n.expanded=true;});render();fit();};
$("#bCollapse").onclick=()=>{allNodes.forEach(n=>{n.expanded=(n.type==="root"||n.type==="step");});sel=null;selKey=null;matches=new Set();panelClear();render();fit();};
$("#bFit").onclick=()=>{render();fit();};
window.addEventListener("keydown",e=>{
  if(e.key==="Escape"){sel=null;selKey=null;matches=new Set();$("#q").value="";panelClear();render();}
});

/* ============================ 우측 패널 ============================ */
function panelClear(){
  const p=$("#panel"); p.className="empty";
  p.innerHTML='<div>요소 노드를 클릭하면<br>상세와 모든 출현 위치가 여기에 표시된다.</div>';
}
function slotLabel(id){ const m=slotMeta[id]; return m?(id+" · "+m.name):id; }
function panel(id,node){
  const e=byId[id],p=$("#panel");p.className="";
  const curSlot=node?node.slot:null;
  const H=[];
  H.push('<div class="pid">'+esc(e.id)+" · "+(e.slots||[]).length+"개 슬롯에 배치"+(curSlot?" · 현재 "+esc(curSlot):"")+'</div>');
  H.push("<h2>"+esc(e.label)+"</h2>");
  H.push('<div class="meta">'
    +'<span class="tag '+e.confidence+'">confidence '+e.confidence+'</span>'
    +'<span class="tag'+(e.ownership==="own"?" own":"")+'">'+esc(OWN_KO[e.ownership]||e.ownership)+'</span>'
    +'<span class="tag">'+esc(KIND_KO[e.kind]||e.kind)+'</span>'
    +'<span class="tag">'+esc(POL_KO[e.polarity]||e.polarity)+'</span>'
    +(e.group?'<span class="tag">'+esc(e.group)+'</span>':"")
    +(e.variant?'<span class="tag">변주: '+esc(e.variant)+'</span>':"")
    +(e.scenario&&e.scenario.length?'<span class="tag">시나리오 '+esc(e.scenario.join("·"))+'</span>':"")
    +'</div>');
  H.push('<div class="stm">'+esc(e.statement)+'</div>');

  H.push('<div class="sec"><h3>슬롯별 각도 · '+(e.renderings||[]).length+'</h3>');
  (e.renderings||[]).forEach(r=>{
    H.push('<div class="angle'+(r.slot===curSlot?" here":"")+'"><span class="sl">'
      +esc(slotLabel(r.slot))+(r.slot===curSlot?" ← 지금 이 자리":"")+'</span>'+esc(r.angle)+'</div>');
  });
  H.push("</div>");

  H.push('<div class="sec"><h3>★ 모든 출현 위치 ('+(e.slots||[]).length+')</h3>');
  (e.slots||[]).forEach(s=>{
    const n=(occByEl[id]||[]).find(x=>x.slot===s);
    H.push('<div class="occ'+(s===curSlot?" cur":"")+'" data-jump="'+(n?n.key:"")+'">'
      +'<code>'+esc(s)+'</code><span>'+esc((slotMeta[s]||{}).name||"")+'</span></div>');
  });
  H.push("</div>");

  if(e.stance&&Object.keys(e.stance).length){
    H.push('<div class="sec"><h3>stance</h3>');
    Object.entries(e.stance).forEach(([kk,v])=>H.push('<div class="row"><span class="k">'+esc(kk)+'</span><span class="v">'+esc(v)+'</span></div>'));
    H.push("</div>");
  }
  if(e.eval){
    H.push('<div class="sec"><h3>5축 평가</h3><div class="evgrid">');
    [["revenue","수익성"],["brand","브랜드"],["difficulty","난이도"],["legal","법률"],["sustainability","지속성"]]
      .forEach(([kk,ko])=>{const v=e.eval[kk]||"-";
        H.push('<div class="ev"><span class="l">'+ko+'</span><span class="v '+esc(v)+'">'+esc(v)+'</span></div>');});
    H.push("</div></div>");
  }
  if(e.viability&&Object.keys(e.viability).length){
    H.push('<div class="sec"><h3>viability — 어느 선택 아래 살아남는가</h3>');
    Object.entries(e.viability).forEach(([kk,v])=>H.push('<div class="row"><span class="k">'+esc(kk)+'</span><span class="v">'+esc([].concat(v).join(" · "))+'</span></div>'));
    H.push("</div>");
  }
  if(e.numbers&&e.numbers.length){
    H.push('<div class="sec"><h3>수치 '+e.numbers.length+'</h3>');
    e.numbers.forEach(n=>H.push('<div class="num"><b>'+esc(n.value)+'</b> '+esc(n.unit||"")
      +(n.year?' <span style="color:var(--fg-3)">['+esc(n.year)+']</span>':"")
      +(n.context?'<br><span style="color:var(--fg-3)">'+esc(n.context)+'</span>':"")+'</div>'));
    H.push("</div>");
  }
  const inb=DATA.filter(x=>(x.edges||[]).some(y=>y.to===id));
  if((e.edges&&e.edges.length)||(e.derived_from&&e.derived_from.length)||inb.length){
    H.push('<div class="sec"><h3>관계</h3>');
    (e.edges||[]).forEach(x=>H.push('<div class="rel"><span class="r '+x.rel+'">'+(REL_KO[x.rel]||x.rel)
      +'</span><span class="lnk" data-go="'+x.to+'">'+esc(x.to+" · "+((byId[x.to]||{}).label||"?"))+'</span></div>'));
    inb.forEach(x=>{const r=(x.edges.find(y=>y.to===id)||{}).rel;
      H.push('<div class="rel"><span class="r '+r+'">← '+(REL_KO[r]||r)+'</span><span class="lnk" data-go="'+x.id+'">'+esc(x.id+" · "+x.label)+'</span></div>');});
    (e.derived_from||[]).forEach(d=>H.push('<div class="rel"><span class="r derived">파생원</span><span class="lnk" data-go="'+d+'">'+esc(d+" · "+((byId[d]||{}).label||"?"))+'</span></div>'));
    H.push("</div>");
  }
  if(e.legal_note)H.push('<div class="sec"><h3>법률 메모</h3><div style="font-size:11.5px;line-height:1.7;color:#DCD6CF">'+esc(e.legal_note)+'</div></div>');
  H.push('<div class="sec"><h3>출처 '+((e.source||[]).length)+'</h3>');
  (e.source||[]).forEach(s=>H.push('<div class="src">'+esc(s.file)+(s.loc?" <span style=\"color:#6C5CE7\">"+esc(s.loc)+"</span>":"")+'</div>'));
  H.push("</div>");
  p.innerHTML=H.join("");
}
$("#panel").addEventListener("click",ev=>{
  const j=ev.target.closest("[data-jump]");
  if(j&&j.dataset.jump){const n=nodeByKey[j.dataset.jump];if(n){selectEl(n.elId,n);centerOn(n);}return;}
  const g=ev.target.closest("[data-go]");
  if(g){const id=g.dataset.go;const n=(occByEl[id]||[])[0];selectEl(id,n);if(n){render();centerOn(n);}}
});

/* ============================ 시작 ============================ */
render(); fit();

window.__MM={
  elements:DATA.length,
  elementNodes:TOTAL_EL_NODES,
  totalNodes:allNodes.length,
  slotsUsed:Object.keys(bySlot).length,
  slotsDefined:Object.keys(slotMeta).length,
  edges:DATA.reduce((a,e)=>a+((e.edges||[]).length),0),
  ghostable:DATA.filter(e=>(e.slots||[]).length>1).length,
  visible:()=>laid.length,
  select:id=>{const n=(occByEl[id]||[])[0];selectEl(id,n);return (occByEl[id]||[]).length;},
  expandAll:()=>{$("#bExpand").click();return laid.length;},
  collapse:()=>{$("#bCollapse").click();return laid.length;},
  search:q=>{$("#q").value=q;search(q);return {hits:hits.length,matched:matches.size};},
  ghostCount:()=>gGhost.childElementCount,
  edgeCount:()=>gEdges.childElementCount,
  toggleEdges:()=>{$("#bEdges").click();return gEdges.childElementCount;},
  state:()=>({sel:sel,visible:laid.length,ghost:gGhost.childElementCount,edge:gEdges.childElementCount})
};
console.log("[mindmap] 요소 "+DATA.length+" · 요소노드(슬롯 출현) "+TOTAL_EL_NODES
  +" · 트리 총노드 "+allNodes.length+" · 사용 슬롯 "+Object.keys(bySlot).length
  +" · edges "+window.__MM.edges+" · 다중배치 요소 "+window.__MM.ghostable);
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
