#!/usr/bin/env python3
"""
elements.json → 집필용 슬롯별 브리프 + 요소 원장
usage: python3 query.py
출력: briefs/S1.md ... briefs/S8.md, 00-요소원장.md
"""
import json, os
from collections import defaultdict, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
els = json.load(open("elements.json", encoding="utf-8"))
idx = {e["id"]: e for e in els}

SECTIONS = {
    "S1": ("프로젝트 정의", ["S1-A", "S1-B", "S1-C"]),
    "S2": ("프로젝트 재정의", ["S2-a1","S2-a2","S2-a3","S2-b1","S2-b2","S2-b3","S2-c1","S2-c2","S2-c3"]),
    "S3": ("핵심 선택 요소", ["S3-C1","S3-C2","S3-C3","S3-C4","S3-C5","S3-C6","S3-X"]),
    "S4": ("기회", ["S4-O1","S4-O2a","S4-O2b","S4-O2c","S4-O2d","S4-O3","S4-O4","S4-O5"]),
    "S5": ("비즈니스 모델", ["S5-BM1","S5-BM2","S5-BM3","S5-BM4","S5-BM5","S5-BMX"]),
    "S6": ("서비스·콘텐츠", ["S6-RAW"]),
    "S8": ("최종 수렴", ["S8-A","S8-B","S8-C","S8-FINAL"]),
}
SLOT_NAME = {
    "S1-A":"고려요소·주의사항","S1-B":"요구사항·산출물 정의","S1-C":"합의·목적",
    "S2-a1":"봉은사 — 수익성","S2-a2":"봉은사 — 브랜드 강화","S2-a3":"봉은사 — 지역 문화공간",
    "S2-b1":"불교 전체 — 봉은사의 역할","S2-b2":"불교 전체 — 신자·지역에 대한 역할","S2-b3":"불교 전체 — 지속가능성·공익성",
    "S2-c1":"운영 — 안정적 수익 확보","S2-c2":"운영 — 수익 최대화","S2-c3":"운영 — 공공성·사회적 가치",
    "S3-C1":"특화 vs 대중화","S3-C2":"종교시설 vs 문화시설","S3-C3":"합법성 전략","S3-C4":"중창불사와의 관계",
    "S3-C5":"지역 vs 글로벌(기각·실행변수로 강등)","S3-C6":"브랜드 강화 vs 산업화","S3-X":"선택별 BM 변화",
    "S4-O1":"시장성","S4-O2a":"타겟 — 외국인","S4-O2b":"타겟 — 강남 주민","S4-O2c":"타겟 — MZ","S4-O2d":"타겟 — 전국 불자",
    "S4-O3":"시장 공백","S4-O4":"입지·상징·스케일 자산","S4-O5":"Timing — 왜 지금인가",
    "S5-BM1":"국내 종교시설","S5-BM2":"해외 종교시설","S5-BM3":"문화시설 × 지역연계","S5-BM4":"프리미엄 웰니스·멤버십",
    "S5-BM5":"관광시설","S5-BMX":"결론 — 매스/로컬/프리미엄",
    "S6-RAW":"서비스·콘텐츠 나열",
    "S8-A":"A · 불교 문화 목적지","S8-B":"B · 웰니스·라이프스타일","S8-C":"C · 비즈니스 이노베이션 랩","S8-FINAL":"최종 3안 × 3-Track",
}
CONF_MARK = {"A": "🟣A", "B": "🔵B", "C": "⚪C"}

by_slot = defaultdict(list)
for e in els:
    for s in e.get("slots", []):
        by_slot[s].append(e)


def angle_of(e, slot):
    for r in e.get("renderings", []):
        if r.get("slot") == slot:
            return r.get("angle", "")
    return ""


def fmt(e, slot):
    L = []
    head = f"### {e['id']} · {e['label']}  {CONF_MARK.get(e.get('confidence'),'')}"
    meta = f"`{e['kind']}` `{e['ownership']}` `{e['polarity']}`"
    if e.get("stance"):
        meta += "  stance: " + ", ".join(f"{k}={v}" for k, v in e["stance"].items())
    if e.get("viability"):
        meta += "  viability: " + json.dumps(e["viability"], ensure_ascii=False)
    L.append(head)
    L.append(meta)
    L.append(f"**{e['statement']}**")
    a = angle_of(e, slot)
    if a:
        L.append(f"> 이 자리에서의 각도: {a}")
    if e.get("numbers"):
        nums = "; ".join(
            f"{n.get('value')}{' '+str(n.get('unit')) if n.get('unit') else ''}"
            f"{' ('+str(n.get('context'))+')' if n.get('context') else ''}"
            f"{' ['+str(n.get('year'))+']' if n.get('year') else ''}"
            for n in e["numbers"]
        )
        L.append(f"- 수치: {nums}")
    if e.get("edges"):
        L.append("- 연결: " + ", ".join(
            f"{x['rel']}→{x['to']}({idx[x['to']]['label'] if x['to'] in idx else '?'})"
            for x in e["edges"]))
    if e.get("derived_from"):
        L.append("- 파생원: " + ", ".join(e["derived_from"]))
    other = [s for s in e["slots"] if s != slot]
    if other:
        L.append("- 다른 자리: " + ", ".join(other))
    src = "; ".join(f"{s.get('file')} {s.get('loc','')}".strip() for s in (e.get("source") or []))
    L.append(f"- 출처: {src}")
    return "\n".join(L)


os.makedirs("briefs", exist_ok=True)
for sec, (title, slots) in SECTIONS.items():
    out = [f"# {sec} — {title}", "",
           "> 집필용 브리프. elements.json에서 자동 생성됨 (직접 편집하지 말 것).",
           "> 🟣A=원출처 확인 / 🔵B=2차 인용, \"○○ 리서치 기준\" 표기 / ⚪C=본문 수치 인용 금지", ""]
    for s in slots:
        items = by_slot.get(s, [])
        out.append(f"\n---\n\n## {s} · {SLOT_NAME.get(s,s)}  ({len(items)}개)\n")
        if not items:
            out.append("_(요소 없음)_\n")
            continue
        conf = Counter(x.get("confidence") for x in items)
        own = Counter(x.get("ownership") for x in items)
        out.append(f"_confidence {dict(conf)} · ownership {dict(own)}_\n")
        for e in sorted(items, key=lambda x: (x.get("confidence", "Z"), x["id"])):
            out.append(fmt(e, s))
            out.append("")
    open(f"briefs/{sec}.md", "w", encoding="utf-8").write("\n".join(out))
    print(f"briefs/{sec}.md  ({sum(len(by_slot.get(s,[])) for s in slots)} 배정)")

# --- 요소 원장 ---
led = ["# 요소 원장 — 봉은사 재구조화", "",
       f"총 {len(els)}개 요소. `elements.json`에서 자동 생성 (직접 편집하지 말 것).", "",
       "| ID | label | kind | own | conf | 슬롯 |", "|---|---|---|---|---|---|"]
for e in els:
    led.append(f"| {e['id']} | {e['label']} | {e['kind']} | {e['ownership']} | {e['confidence']} | {' '.join(e['slots'])} |")
open("00-요소원장.md", "w", encoding="utf-8").write("\n".join(led))
print(f"00-요소원장.md ({len(els)}행)")
