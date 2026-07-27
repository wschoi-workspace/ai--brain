#!/usr/bin/env python3
"""Team Ops Guide 규칙 ⑥ 임계값 ↔ approval-rules.json 정합 (WS4a, 2026-07-27).

실행: python3 00-system/02-scripts/tests/test_ops_guide_thresholds.py

임계값의 SSOT는 approval-rules.json이고 가이드 표는 그 반영이다. 규칙이 바뀌었는데
문서가 안 따라오면 직원은 문서를 믿고 잘못된 대상에게 보고한다 — 그 표류를 잡는다.
읽기 전용.
"""
import json
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3]
RULES = WORKSPACE / "00-system" / "01-templates" / "_data" / "approval-rules.json"
GUIDE = WORKSPACE / "20-operations" / "27-team-ops-guide" / "team-ops-guide-v1.html"

FAIL = []
N = 0


def ck(cond, label):
    global N
    N += 1
    if not cond:
        FAIL.append(label)
        print(f"  ✗ {label}")
    else:
        print(f"  ✓ {label}")


rules = json.loads(RULES.read_text(encoding="utf-8"))
html = GUIDE.read_text(encoding="utf-8")

print("§1 규칙 ⑥ 존재")
ck("⑥ 나쁜 소식 전달" in html, "규칙 ⑥ 제목")
ck("여섯 규칙" in html, "Part 2 lead가 '여섯 규칙'")
for item in ("① 무슨 일", "② 영향 범위", "③ 실행 중 조치", "④ 필요한 것", "⑤ 타임라인"):
    ck(item in html, f"5항목 구조 — {item}")

print("\n§2 금액 임계값 ↔ approval-rules.json")
amounts = [r["amountOver"] for r in rules["rules"] if r.get("amountOver") is not None]
ck(len(amounts) == 1, f"결재 규칙의 amountOver 규칙이 1개 (실제 {len(amounts)}개)")
if amounts:
    won = int(amounts[0])
    man = won // 10000
    ck(f"{man}만원 초과" in html,
       f"가이드 표에 '{man}만원 초과' 표기 (amountOver={won})")
    ck(f"amountOver: {won}" in html, f"근거 값 {won} 명시")
    lv = [r["minLevel"] for r in rules["rules"] if r.get("amountOver") == won][0]
    ck(lv == "대표", f"고액 결재 minLevel이 대표 (실제 {lv})")

print("\n§3 유형별 대상 ↔ approval-rules.json")
by_level = {}
for r in rules["rules"]:
    if r.get("type"):
        by_level.setdefault(r["minLevel"], []).append(r["type"])
for lv, types in sorted(by_level.items()):
    for t in types:
        # '완료확인'은 승인 흐름 항목이라 나쁜 소식 표의 대상이 아니다
        if t == "완료확인":
            continue
        ck(t in html, f"{lv} 항목 '{t}'가 가이드 표에 있다")

print("\n§4 채점기와 같은 완충어를 쓰는가")
sys.path.insert(0, str(WORKSPACE / "00-system" / "02-scripts"))
import shared.report_score as RS  # noqa: E402
strict = RS.RUBRIC_RULES_STRICT
for word in ("진행 중", "확인 중", "거의 완료", "조금 늦어질 듯", "것 같다"):
    ck(word in strict and word in html,
       f"'{word}' — 루브릭·가이드 양쪽에 존재")

print("\n§5 SSOT 표기")
ck("approval-rules.json" in html, "가이드가 SSOT 파일 경로를 명시")
ck("SSOT는 그 파일이며 이 표가 아니다" in html, "SSOT가 문서가 아님을 명시")

print(f"\n{'─' * 52}")
if FAIL:
    print(f"실패 {len(FAIL)}/{N}")
    for f in FAIL:
        print(f"  · {f}")
    sys.exit(1)
print(f"전체 통과 {N}/{N}")
