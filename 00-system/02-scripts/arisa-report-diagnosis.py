#!/usr/bin/env python3
"""ARISA 보고 품질 진단 — 지난 2주(기본 2026-06-22~07-05) 일일보고를 14요소로 채점.

weekly-report-aggregate.py의 자산(GROWTH_PROMPT·DAILY 기대셋·normalize·gws·명부)을
그대로 재사용하되, compute_growth가 버리는 **14요소 el(filled/depth)을 보존**해
개인×요소 히트맵·전체 결핍 순위를 낼 수 있게 한다. (compute_growth는 요약만 반환)

산출: diagnosis-scored-2026-2wk.json (summary/teams/persons + 14요소 raw + 오염 통계)
재실행: python3 arisa-report-diagnosis.py [--start 2026-06-22 --end 2026-07-05]
fidelity: 근거 없으면 depth 0. 추측 채점은 GROWTH_PROMPT가 금지. raw 없으면 collecting.
"""
from __future__ import annotations

import sys
import json
import argparse
import importlib.util
from pathlib import Path
from collections import defaultdict, Counter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# weekly-report-aggregate.py를 모듈로 로드(하이픈 파일명 → importlib)
_spec = importlib.util.spec_from_file_location("wagg", HERE / "weekly-report-aggregate.py")
w = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(w)

ALL14 = ["status", "why", "problem", "approach", "output", "outcome", "timeline",
         "risk", "support", "decision", "budget", "impact", "next", "reflection"]
ELEM_KR = {"status": "현황", "why": "목적", "problem": "문제", "approach": "해결방향",
           "output": "산출물", "outcome": "의미", "timeline": "일정", "risk": "리스크",
           "support": "요청", "decision": "의사결정", "budget": "예산", "impact": "기대효과",
           "next": "실행계획", "reflection": "회고"}
EXPECTED = w.DAILY_REQUIRED + w.DAILY_OPTIONAL   # daily 기대셋 8요소(필수4+선택4)
OUT_PATH = HERE.parents[1] / "20-operations" / "23-arisa" / "diagnosis-scored-2026-2wk.json"


def _filled(el, k):
    return bool((el.get(k) or {}).get("filled"))


def _depth(el, k):
    v = el.get(k) or {}
    return int(v.get("depth", 0)) if v.get("filled") else 0


def score_elements(raws: list[str]) -> dict | None:
    """개인 raw 묶음 → 14요소 el(filled/depth). compute_growth와 동일 프롬프트·모델."""
    text = "\n\n---\n\n".join(raws)[:6000]
    client = w._get_growth_client()
    if client is None:
        return None
    resp = client.chat.completions.create(
        model="gpt-4o-mini", temperature=0.1,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": w.GROWTH_PROMPT},
                  {"role": "user", "content": f"[직원 주간 보고 원문]\n{text}"}],
    )
    return json.loads(resp.choices[0].message.content or "{}").get("elements", {})


def resolution_from(el: dict) -> dict:
    """compute_growth 산식 복제 — coverage×(depth_avg/3)×100."""
    cov_n = sum(1 for k in EXPECTED if _filled(el, k))
    coverage = cov_n / len(EXPECTED)
    filled_all = [k for k in ALL14 if _filled(el, k)]
    depth_avg = (sum(_depth(el, k) for k in filled_all) / len(filled_all)) if filled_all else 0.0
    return {
        "resolution": round(coverage * (depth_avg / 3) * 100),
        "coverage": round(coverage * 100),
        "depth_avg": round(depth_avg, 1),
        "req_filled": [k for k in w.DAILY_REQUIRED if _filled(el, k)],
        "req_missing": [k for k in w.DAILY_REQUIRED if not _filled(el, k)],
        "elements": {k: {"filled": _filled(el, k), "depth": _depth(el, k)} for k in ALL14},
    }


def detect_pollution(raw_meta_rows: list[list], start: str, end: str) -> dict:
    """정규화에서 조용히 누락되는 오염행 집계(findings). 원시 메타행 기준."""
    total, dropped, samples = 0, 0, []
    reasons = Counter()
    for r in raw_meta_rows:
        r = r + [""] * (12 - len(r))
        raw_date, raw_name = (r[0] or "").strip(), (r[1] or "").strip()
        d = w.normalize_date(raw_date)
        nm = w.normalize_name(raw_name)
        # 창 필터(날짜 파싱된 것만): 창 밖은 집계 대상 아님
        if d and not (start <= d <= end):
            continue
        total += 1
        ok_date = bool(d)
        ok_name = bool(nm) and nm in w.BY_NAME
        if ok_date and ok_name:
            continue
        dropped += 1
        if not ok_date:
            reasons["날짜 파싱 실패"] += 1
        if not ok_name:
            reasons["이름 미매칭/오염"] += 1
        if len(samples) < 5:
            samples.append({"date": raw_date[:20], "name": raw_name[:40],
                            "name_len": len(raw_name), "has_newline": "\n" in raw_name})
    return {"meta_rows_in_window": total, "dropped": dropped,
            "reasons": dict(reasons), "samples": samples}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-06-22")
    ap.add_argument("--end", default="2026-07-05")
    args = ap.parse_args()
    S, E = args.start, args.end

    daily = w.fetch_daily()
    recs = w.normalize_daily(daily)
    wk = [r for r in recs if r["date"] and S <= r["date"] <= E]

    pollution = detect_pollution(daily["meta"], S, E)

    by_person = defaultdict(list)
    by_team = defaultdict(list)
    for r in wk:
        by_person[r["name"]].append(r)
        by_team[r["team"]].append(r)

    persons = []
    for nm, rs in by_person.items():
        vol, comp = w._completion(rs)
        meta_raws = [r["raw"] for r in rs if r["source"] == "daily-meta" and (r["raw"] or "").strip()]
        p = {
            "name": nm, "team": w.team_of(nm),
            "report_days": len({r["date"] for r in rs if r["source"] == "daily-meta"}),
            "task_count": vol, "completion_rate": comp,
            "categories": w._categories(rs), "blockers": w._blockers(rs),
            "tools": w._tools(rs), "open_decisions": w._open_decisions(rs),
            "raw_chars": sum(len(x) for x in meta_raws),
        }
        if meta_raws:
            el = score_elements(meta_raws)
            p["growth"] = resolution_from(el) if el is not None else {"status": "collecting"}
            p["growth"]["status"] = "scored"
            # 대표 원문 발췌(가장 긴 것 = 대표성) — 왜곡 방지 위해 원문 그대로
            longest = max(meta_raws, key=len)
            p["raw_excerpt"] = longest[:600]
        else:
            p["growth"] = {"status": "collecting"}
        persons.append(p)

    # 정렬: 팀 순서 → 보고건수
    persons.sort(key=lambda p: (w.TEAM_ORDER.index(p["team"]) if p["team"] in w.TEAM_ORDER else 99,
                                -p["task_count"]))

    # 팀 집계
    teams = []
    for tm, rs in by_team.items():
        members = sorted({r["name"] for r in rs})
        scored = [p for p in persons if p["team"] == tm and p["growth"].get("status") == "scored"]
        avg_res = round(sum(p["growth"]["resolution"] for p in scored) / len(scored)) if scored else None
        avg_cov = round(sum(p["growth"]["coverage"] for p in scored) / len(scored)) if scored else None
        teams.append({"team": tm, "members": members, "scored_members": len(scored),
                      "avg_resolution": avg_res, "avg_coverage": avg_cov,
                      "categories": w._categories(rs)})
    teams.sort(key=lambda t: w.TEAM_ORDER.index(t["team"]) if t["team"] in w.TEAM_ORDER else 99)

    # 전체 요소 결핍: 채점된 사람 기준 요소별 filled 비율·평균깊이
    scored_p = [p for p in persons if p["growth"].get("status") == "scored"]
    elem_stat = {}
    for k in ALL14:
        fills = [p["growth"]["elements"][k]["filled"] for p in scored_p]
        depths = [p["growth"]["elements"][k]["depth"] for p in scored_p if p["growth"]["elements"][k]["filled"]]
        elem_stat[k] = {
            "kr": ELEM_KR[k],
            "fill_rate": round(sum(fills) / len(fills) * 100) if fills else 0,
            "avg_depth": round(sum(depths) / len(depths), 1) if depths else 0.0,
            "expected": "req" if k in w.DAILY_REQUIRED else ("opt" if k in w.DAILY_OPTIONAL else "—"),
        }

    # 5대 결함 발생률(채점자 기준)
    n = len(scored_p) or 1
    defects = {
        "output_missing": round(sum(1 for p in scored_p if not p["growth"]["elements"]["output"]["filled"]) / n * 100),
        "outcome_missing": round(sum(1 for p in scored_p if not p["growth"]["elements"]["outcome"]["filled"]) / n * 100),
        "decision_missing": round(sum(1 for p in scored_p if not p["growth"]["elements"]["decision"]["filled"]) / n * 100),
        "problem_missing": round(sum(1 for p in scored_p if not p["growth"]["elements"]["problem"]["filled"]) / n * 100),
    }

    avg_res = round(sum(p["growth"]["resolution"] for p in scored_p) / len(scored_p)) if scored_p else None
    avg_cov = round(sum(p["growth"]["coverage"] for p in scored_p) / len(scored_p)) if scored_p else None
    open_dec = sum(len(p["open_decisions"]) for p in persons)

    summary = {
        "window": {"start": S, "end": E},
        "reporters": len(persons),
        "scored": len(scored_p),
        "meta_reports": sum(p["report_days"] for p in persons),
        "avg_resolution": avg_res, "avg_coverage": avg_cov,
        "pollution": pollution,
        "open_decisions": open_dec,
        "elem_stat": elem_stat,
        "defects": defects,
        "worst_elements": sorted(
            [(k, v["fill_rate"]) for k, v in elem_stat.items() if v["expected"] in ("req", "opt")],
            key=lambda x: x[1])[:3],
    }

    out = {"summary": summary, "teams": teams, "persons": persons}
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {OUT_PATH}")
    print(f"  보고자 {summary['reporters']}명 / 채점 {summary['scored']}명 / 메타보고 {summary['meta_reports']}건")
    print(f"  평균 해상도 {avg_res} · 커버리지 {avg_cov}%")
    print(f"  오염행 {pollution['dropped']}건 (사유 {pollution['reasons']})")
    print(f"  최약 요소 TOP3: {summary['worst_elements']}")


if __name__ == "__main__":
    main()
