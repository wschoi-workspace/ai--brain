#!/usr/bin/env python3
"""
봉은사 재구조화 — shard 병합 + 스키마 검증
usage: python3 merge_validate.py
출력: elements.json (병합본), 콘솔에 검증 리포트
"""
import json, os, sys, glob
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
SHARD_DIR = os.path.join(BASE, "shards")
OUT = os.path.join(BASE, "elements.json")

VALID_SLOTS = {
    "S1-A","S1-B","S1-C","S1-K",
    "S2-a1","S2-a2","S2-a3","S2-b1","S2-b2","S2-b3","S2-c1","S2-c2","S2-c3",
    "S3-C1","S3-C2","S3-C3","S3-C4","S3-C5","S3-C6","S3-X",
    "S4-O1","S4-O2a","S4-O2b","S4-O2c","S4-O2d","S4-O2e","S4-O2f","S4-O3","S4-O4","S4-O5",
    "S5-BM1","S5-BM2","S5-BM3","S5-BM4","S5-BM5","S5-BMX",
    "S6-RAW",
    "S7-RESERVED","S7-MTX",
    "S8-FINAL",  # v1 잔존 태그 — STEP 10 집필이 이 슬롯 브리프로 이미 이뤄져 유효하게 남긴다
    "S8-A","S8-B","S8-C",
    "S9-EVAL","S10-REC",
}
VALID_KIND = {"fact","constraint","case","insight","option","service","risk","requirement","asset","actor"}
VALID_OWN  = {"own","reference","context","constraint"}
VALID_POL  = {"pro","con","neutral"}
VALID_CONF = {"A","B","C"}
VALID_REL  = {"supports","contradicts","enables","blocks","precedent_for"}
STANCE_VALS = {
    "C1": {"특화","대중화","양립"},
    "C2": {"종교","문화","양립"},
    "C3": {"합법화","미확정영역","합법범위내"},
    "C4": {"독립","상호보완","백업전제"},
    "C5": {"지역","글로벌","양립"},
    "C6": {"브랜드","산업화","양립"},
}
REQUIRED = ["id","label","statement","kind","ownership","slots","renderings","polarity","numbers","confidence","source"]

def main():
    shards = sorted(glob.glob(os.path.join(SHARD_DIR, "*.json")))
    if not shards:
        sys.exit("shard 파일이 없습니다.")

    all_els, errors, warns = [], [], []
    per_shard = {}

    for path in shards:
        name = os.path.basename(path)
        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception as e:
            errors.append(f"[{name}] JSON 파싱 실패: {e}")
            continue
        if not isinstance(data, list):
            errors.append(f"[{name}] 최상위가 배열이 아님")
            continue
        per_shard[name] = len(data)
        for el in data:
            el["_shard"] = name
            all_els.append(el)

    # --- ID 중복 ---
    ids = [e.get("id") for e in all_els]
    dup = [i for i, c in Counter(ids).items() if c > 1]
    for d in dup:
        errors.append(f"ID 중복: {d}")
    idset = set(ids)

    # --- 요소별 검증 ---
    for el in all_els:
        eid = el.get("id", "?")
        tag = f"[{el.get('_shard')}] {eid}"

        for f in REQUIRED:
            if f not in el:
                errors.append(f"{tag} 필수필드 누락: {f}")

        if el.get("kind") not in VALID_KIND:
            errors.append(f"{tag} kind 부정: {el.get('kind')}")
        if el.get("ownership") not in VALID_OWN:
            errors.append(f"{tag} ownership 부정: {el.get('ownership')}")
        if el.get("polarity") not in VALID_POL:
            errors.append(f"{tag} polarity 부정: {el.get('polarity')}")
        if el.get("confidence") not in VALID_CONF:
            errors.append(f"{tag} confidence 부정: {el.get('confidence')}")

        slots = el.get("slots") or []
        if not slots:
            errors.append(f"{tag} slots 비어 있음")
        for s in slots:
            if s not in VALID_SLOTS:
                errors.append(f"{tag} 미정의 슬롯: {s}")
        if "S7-RESERVED" in slots:
            warns.append(f"{tag} S7은 예약 슬롯 — 지금은 비어 있어야 함")

        rends = el.get("renderings") or []
        if len(rends) != len(slots):
            errors.append(f"{tag} renderings {len(rends)}개 ≠ slots {len(slots)}개")
        else:
            rslots = [r.get("slot") for r in rends]
            if set(rslots) != set(slots):
                errors.append(f"{tag} renderings 슬롯 불일치: {rslots} vs {slots}")
            for r in rends:
                if not (r.get("angle") or "").strip():
                    errors.append(f"{tag} angle 비어 있음 ({r.get('slot')})")

        # stance
        st = el.get("stance") or {}
        s3 = [s for s in slots if s.startswith("S3-C")]
        # 미확정 사실·리스크·요구사항은 어느 갈래도 지지하지 않으므로 stance 면제
        stance_exempt = el.get("kind") in {"risk", "fact", "requirement"}
        for s in s3:
            key = s.split("-")[1]
            if key not in st and not stance_exempt:
                warns.append(f"{tag} {s} 보유하나 stance.{key} 없음")
        for k, v in st.items():
            if k not in STANCE_VALS:
                errors.append(f"{tag} stance 키 부정: {k}")
            elif v not in STANCE_VALS[k]:
                errors.append(f"{tag} stance.{k} 값 부정: {v}")

        # service 규칙
        if el.get("kind") == "service" and not el.get("viability"):
            warns.append(f"{tag} kind=service 인데 viability 없음")

        # edges
        for e in (el.get("edges") or []):
            if e.get("to") not in idset:
                errors.append(f"{tag} edge 대상 미존재: {e.get('to')}")
            if e.get("rel") not in VALID_REL:
                errors.append(f"{tag} edge rel 부정: {e.get('rel')}")
        for d in (el.get("derived_from") or []):
            if d not in idset:
                errors.append(f"{tag} derived_from 미존재: {d}")

        if len(el.get("label", "")) > 20:
            warns.append(f"{tag} label 20자 초과: {el.get('label')}")

    # --- 통계 ---
    slot_cnt = Counter()
    for el in all_els:
        for s in el.get("slots", []):
            slot_cnt[s] += 1
    kind_cnt = Counter(e.get("kind") for e in all_els)
    own_cnt  = Counter(e.get("ownership") for e in all_els)
    conf_cnt = Counter(e.get("confidence") for e in all_els)

    src_cnt = Counter()
    for el in all_els:
        for s in (el.get("source") or []):
            src_cnt[s.get("file")] += 1

    empty_slots = sorted(VALID_SLOTS - set(slot_cnt) - {"S7-RESERVED"})

    # --- 리포트 ---
    print("=" * 60)
    print(f"shard {len(per_shard)}개 / 총 요소 {len(all_els)}개")
    for k, v in per_shard.items():
        print(f"  {k:22s} {v:4d}")
    print("=" * 60)
    print("\n[슬롯 분포]")
    for s in sorted(VALID_SLOTS):
        print(f"  {s:12s} {slot_cnt.get(s,0):4d}")
    if empty_slots:
        print(f"\n  ⚠️ 요소 0개인 슬롯: {', '.join(empty_slots)}")
    print(f"\n[kind]       {dict(kind_cnt)}")
    print(f"[ownership]  {dict(own_cnt)}")
    print(f"[confidence] {dict(conf_cnt)}")

    print(f"\n[소스 파일 커버리지] {len(src_cnt)}개 파일")
    for f, c in src_cnt.most_common():
        print(f"  {c:4d}  {f}")

    print("\n" + "=" * 60)
    if errors:
        print(f"❌ 오류 {len(errors)}건")
        for e in errors[:60]:
            print("  " + e)
        if len(errors) > 60:
            print(f"  ... 외 {len(errors)-60}건")
    else:
        print("✅ 오류 0건")
    if warns:
        print(f"\n⚠️  경고 {len(warns)}건")
        for w in warns[:40]:
            print("  " + w)
        if len(warns) > 40:
            print(f"  ... 외 {len(warns)-40}건")

    # --- 저장 ---
    for el in all_els:
        el.pop("_shard", None)
    all_els.sort(key=lambda x: x.get("id", ""))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(all_els, f, ensure_ascii=False, indent=1)
    print(f"\n→ {OUT} ({len(all_els)}개)")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
