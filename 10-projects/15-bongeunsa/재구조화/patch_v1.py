#!/usr/bin/env python3
"""
보정 v1 — shard 원본에 적용 (merge_validate.py 재실행에도 살아남게)
1) stance.C4 부여 (실제 입장이 있는 3건만. 미확정 사실·리스크는 stance 없이 두는 것이 정직)
2) label 20자 초과 4건 축약
3) confidence 재조정 — 우리가 작성·제출한 공식 문서는 C가 아니라 B
   ※ 슬롯체계 §3의 C 규칙은 '출처 불명 외부 자료'를 겨냥한 것이지 자사 산출물을 겨냥한 것이 아님
멱등(idempotent) — 여러 번 실행해도 결과 동일
"""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

STANCE_C4 = {
    "E-0421": "상호보완",  # 1898 지하 전략 — 지상 성당 경관 보존하며 지하에 신기능
    "E-0464": "상호보완",  # 삼쓰데라 — 본당 보존 + 상층부 호텔 임대
    "E-0550": "상호보완",  # 중창불사 2단계에서 문화회관을 신도 기도공간으로 편입
}
LABEL = {
    "E-0225": "Sacred Core+Gateway",
    "E-0237": "McMindfulness 붕괴",
    "E-0255": "L4 본원·센터 분업",
    "E-0256": "L5 sacred boundary",
}
OWN_DOCS = (
    "봉은문화회관-착수계획서.html",
    "bongeunsa-project-timeline.html",
    "봉은문화회관-프레임워크분석.html",
)

n_s = n_l = n_c = 0
for p in sorted(glob.glob("shards/*.json")):
    d = json.load(open(p, encoding="utf-8"))
    changed = False
    for e in d:
        eid = e.get("id")
        if eid in STANCE_C4 and (e.get("stance") or {}).get("C4") != STANCE_C4[eid]:
            e.setdefault("stance", {})["C4"] = STANCE_C4[eid]
            n_s += 1
            changed = True
        if eid in LABEL and e.get("label") != LABEL[eid]:
            e["label"] = LABEL[eid]
            n_l += 1
            changed = True
        if e.get("confidence") == "C":
            files = [s.get("file", "") for s in (e.get("source") or [])]
            if files and all(any(f.endswith(o) for o in OWN_DOCS) for f in files):
                e["confidence"] = "B"
                n_c += 1
                changed = True
    if changed:
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  patched {p}")

print(f"stance.C4 {n_s}건 / label {n_l}건 / confidence C→B {n_c}건")
