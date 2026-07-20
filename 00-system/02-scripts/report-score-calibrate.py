#!/usr/bin/env python3
"""보고 채점 캘리브레이션 — 봇(텔레그램 digest) vs 시뮬레이터(폼) 점수 편차 측정.

같은 내용의 보고를 두 채널 프롬프트로 각각 채점해 갭을 잰다 (2026-07-20 갭 해소 검증).
합격 기준: 동일 내용 양 채널 점수 차 ±10점 이내 + 유형 분류 일치.

사용: OPENAI_API_KEY가 환경(또는 워크스페이스 .env)에 있어야 한다.
  python3 report-score-calibrate.py [--runs 3]
"""
import argparse
import json
import os
import re
import statistics
import sys
import urllib.request
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from shared import report_score as rs  # noqa: E402

# .env 보충 (dashboard-server와 동일 방식)
_WS = _HERE.parent.parent
for _envp in (_WS / ".env",):
    if _envp.exists():
        for line in _envp.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")


def _extract_block(path: Path, var: str) -> str:
    """소스에서 출력 블록 문자열 추출 — SSOT 유지 (복붙 사본 방지)."""
    src = path.read_text(encoding="utf-8")
    m = re.search(rf'{var} = """(.*?)"""', src, re.S)
    if not m:
        raise SystemExit(f"{path.name}에서 {var}를 찾지 못함")
    return m.group(1)


BOT_OUTPUT = _extract_block(_HERE / "daily-report-bot.py", "_SCORE_OUTPUT_RULES")
SIM_OUTPUT = _extract_block(_HERE / "dashboard-server.py", "_SIM_DAILY_OUTPUT")


def call_llm(system: str, user: str) -> dict:
    payload = json.dumps({
        "model": "gpt-4o-mini", "temperature": 0.3,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=payload,
        headers={"Authorization": "Bearer " + OPENAI_KEY,
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read())
    text = d["choices"][0]["message"]["content"]
    m = re.search(r"```json\s*([\s\S]*?)```", text)
    return json.loads(m.group(1) if m else text)


# ===== 샘플 6종 — 유형 A/B/C × 우수/미흡, 텔레그램 digest ↔ 폼 필드 동일 내용 =====

SAMPLES = [
    {
        "name": "A-우수", "expect_type": "A",
        "telegram": (
            "이름: 김샘플 / 날짜: 2026-07-20\n"
            "업무: [세스크멘슬] 전략레포트 v2 작성 — 경쟁사 3곳 벤치마킹 비교표 12건 완성, 목표 대비 80%.\n"
            "왜: 8월 클라이언트 PT의 근거 자료.\n"
            "산출물: 비교표 12건 (드라이브 업로드 완료 — 직접 확인한 공개 가격 기준, 내 해석은 별도 표기)\n"
            "오늘 최중요: 벤치마킹 비교표 완성. 내일 최우선: 남은 20%(요약 슬라이드 3장)를 내일 오후 3시까지 완성.\n"
            "리스크: 없음 (검토함)\n"
        ),
        "fields": {
            "project": "[세스크멘슬] 전략레포트 v2 — 8월 클라이언트 PT 근거 자료",
            "objective": "목표 대비 80% (비교표 12건 완성)",
            "output": "경쟁사 3곳 벤치마킹 비교표 12건, 드라이브 업로드 완료",
            "evidence": "공개 가격은 직접 확인한 사실, 전략 방향은 내 해석으로 별도 표기",
            "priority": "오늘: 비교표 완성 / 내일: 요약 슬라이드 3장, 내일 오후 3시까지",
            "risk": "없음 (검토함)",
        },
    },
    {
        "name": "A-미흡", "expect_type": "A",
        "telegram": (
            "이름: 김샘플 / 날짜: 2026-07-20\n"
            "업무: 레포트 작업 진행 중.\n"
            "내일: 계속 진행.\n"
        ),
        "fields": {
            "project": "레포트 작업",
            "output": "진행 중",
            "priority": "계속 진행",
        },
    },
    {
        "name": "B-우수", "expect_type": "B",
        "telegram": (
            "이름: 김샘플 / 날짜: 2026-07-20\n"
            "업무: [둔촌주공] 시공 발주 준비 — 발주서 초안 완료(목표 대비 70%). 이유: 8/1 착공 일정 확보.\n"
            "이슈: 자재 업체가 '단가 인상 예정'이라고 직접 통화로 말함(사실). 인상 폭은 아직 미확정(추정 5~8%).\n"
            "영향: 예산 300만원 초과 가능. 대응: 대체 업체 2곳에 내일 오전 견적 요청 예정.\n"
            "오늘 최중요: 발주서 초안. 내일 최우선: 대체 견적 2건 확보(내일 18시까지).\n"
            "필요한 지원: 구매팀 견적 비교 검토 30분, 수요일까지 — 단가 협상 근거 마련 위해.\n"
        ),
        "fields": {
            "project": "[둔촌주공] 시공 발주 준비 — 8/1 착공 일정 확보",
            "objective": "발주서 초안 완료, 목표 대비 70%",
            "evidence": "업체 단가 인상 발언은 직접 통화로 확인한 사실, 인상 폭 5~8%는 추정",
            "priority": "오늘: 발주서 초안 / 내일: 대체 견적 2건, 내일 18시까지",
            "risk": "자재 단가 인상 → 예산 300만원 초과 가능. 대응: 대체 업체 2곳 견적 요청",
            "support": "구매팀 견적 비교 검토 30분, 수요일까지 (단가 협상 근거)",
        },
    },
    {
        "name": "B-미흡", "expect_type": "B",
        "telegram": (
            "이름: 김샘플 / 날짜: 2026-07-20\n"
            "업무: 발주 관련 업무. 업체가 어려워하는 것 같음.\n"
            "이슈: 단가 문제 확인 중.\n"
        ),
        "fields": {
            "project": "발주 관련",
            "evidence": "업체가 어려워하는 것 같음",
            "risk": "단가 문제 확인 중",
        },
    },
    {
        "name": "C-우수", "expect_type": "C",
        "telegram": (
            "이름: 김샘플 / 날짜: 2026-07-20\n"
            "업무: [여수 프로젝트] 계약 조건 협상 — 상대측 최종안 수령(목표 대비 90%). 이유: 7월 내 계약 체결 목표.\n"
            "사실: 상대측이 '보증금 20% 인하 시 즉시 서명'이라고 서면으로 회신함. 내 판단: 수용해도 수익성 유지 가능(마진 시뮬레이션 첨부).\n"
            "필요한 의사결정: A안 보증금 20% 인하 수용(즉시 체결·마진 -1.2%p) vs B안 10% 인하 역제안(체결 1~2주 지연 리스크).\n"
            "추천: A안 — 8월 오픈 일정이 더 큰 가치. 결정 기한: 7/23(수). 늦어지면 상대측 타 후보와 협상 개시 가능성.\n"
            "오늘 최중요: 최종안 분석. 내일 최우선: 결정 즉시 계약서 검토 의뢰(법무, 내일 중).\n"
            "지원: 없음\n"
        ),
        "fields": {
            "project": "[여수 프로젝트] 계약 조건 협상 — 7월 내 체결 목표",
            "objective": "상대측 최종안 수령, 목표 대비 90%",
            "evidence": "'보증금 20% 인하 시 즉시 서명'은 서면 회신(사실), 수익성 유지는 내 시뮬레이션 판단",
            "priority": "오늘: 최종안 분석 / 내일: 결정 즉시 법무 검토 의뢰(내일 중)",
            "risk": "결정 지연 시 상대측 타 후보와 협상 개시 가능성",
            "decision": "A안 20% 인하 수용(즉시 체결·마진 -1.2%p) vs B안 10% 역제안(1~2주 지연). 추천 A안. 기한 7/23",
            "support": "없음",
        },
    },
    {
        "name": "C-미흡", "expect_type": "C",
        "telegram": (
            "이름: 김샘플 / 날짜: 2026-07-20\n"
            "업무: 여수 계약 관련 진행.\n"
            "필요한 의사결정: 계약 조건 컨펌 필요.\n"
        ),
        "fields": {
            "project": "여수 계약",
            "decision": "계약 조건 컨펌 필요",
        },
    },
]


def form_to_text(fields: dict) -> str:
    labels = {"project": "프로젝트/맥락", "objective": "목표 대비 진행",
              "output": "산출물", "evidence": "근거(사실/의견)",
              "priority": "우선순위(오늘/내일)", "risk": "리스크",
              "decision": "필요한 의사결정", "support": "필요한 지원"}
    return "\n".join(f"[{labels.get(k, k)}] {v}" for k, v in fields.items() if v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()
    if not OPENAI_KEY:
        raise SystemExit("OPENAI_API_KEY 없음 — 워크스페이스 .env 확인")

    core = rs.build_prompt()
    bot_prompt = core + BOT_OUTPUT
    sim_prompt = core + SIM_OUTPUT
    print(f"모드: {rs.current_mode()} / 가중치: {rs.WEIGHTS_VERSION} / 반복: {args.runs}회\n")

    all_pass = True
    for s in SAMPLES:
        bot_scores, sim_scores, types = [], [], []
        for _ in range(args.runs):
            b = rs.validate_scores(call_llm(bot_prompt, s["telegram"]))
            f = rs.validate_scores(call_llm(sim_prompt, form_to_text(s["fields"])))
            bot_scores.append(b["total"])
            sim_scores.append(f["total"])
            types.extend([b["report_type"], f["report_type"]])
        bm, fm = statistics.mean(bot_scores), statistics.mean(sim_scores)
        gap = abs(bm - fm)
        type_ok = all(t == s["expect_type"] for t in types)
        ok = gap <= 10 and type_ok
        all_pass &= ok
        print(f"{'✅' if ok else '❌'} {s['name']:8s} 봇 {bm:5.1f} (표본 {bot_scores}) | "
              f"폼 {fm:5.1f} (표본 {sim_scores}) | 갭 {gap:4.1f} | "
              f"유형 {'일치' if type_ok else '불일치 ' + str(types)}")

    print("\n결과:", "전체 합격 (갭 ≤10점·유형 일치)" if all_pass else "기준 미달 항목 있음 — 프롬프트 수위 조정 필요")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
