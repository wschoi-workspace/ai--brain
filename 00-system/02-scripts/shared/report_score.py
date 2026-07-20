"""ARISA 보고 채점 공유 코어 (SSOT).

봇(daily-report-bot)과 시뮬레이터(dashboard-server)가 동일 기준으로 채점하도록
루브릭·유형별 가중치·모드(순화/엄격)를 한곳에서 관리한다.

배경(2026-07-20): 같은 보고가 시뮬레이터 100점 vs 텔레그램 60점.
원인 = 프롬프트 엄격도·모델·입력구조 3중 갭. 해소 설계:
  1) 보고 유형별(A 진행공유 / B 이슈 / C 의사결정) 루브릭 이원화 —
     진행공유 보고는 decision·support를 애초에 채점하지 않아
     채널(폼 vs 대화) 간 구조적 감점이 사라진다.
  2) 유예기간(GRACE_END까지) 순화(grace) 채점 → 이후 엄격(strict) 자동 전환.
  3) 채점 모델 통일: gpt-4o-mini, temperature 0.3 (호출부 책임).

기준 문서: 20-operations/26-reporting-os/reporting-os-보고체계-정의-v1.md
"""
from datetime import date

# ===== 운영 파라미터 =====

# 유예 종료일 — 이날까지 grace(순화) 채점, 다음날부터 strict 자동 전환.
# 조정은 이 한 줄만 바꾸면 봇·시뮬레이터가 함께 바뀐다.
GRACE_END = date(2026, 10, 20)

WEIGHTS_VERSION = "type-v1-20260720"

# 유형별 가중치 — 각 유형의 합은 항상 100.
TYPE_WEIGHTS = {
    "A": {"context": 25, "objective": 15, "evidence": 20, "priority": 25,
          "risk": 15},
    "B": {"context": 20, "objective": 10, "evidence": 15, "priority": 15,
          "risk": 25, "support": 15},
    "C": {"context": 15, "objective": 10, "evidence": 15, "priority": 10,
          "risk": 10, "decision": 30, "support": 10},
}

TYPE_LABELS = {"A": "진행 공유", "B": "이슈·리스크", "C": "의사결정"}

ITEM_LABELS = {
    "context": "맥락", "objective": "목표 명확성", "evidence": "근거",
    "priority": "우선순위", "risk": "리스크", "decision": "결정 요청",
    "support": "지원 요청",
}


def current_mode(today=None) -> str:
    """오늘 날짜 기준 채점 모드 — 'grace'(순화) 또는 'strict'(엄격)."""
    d = today or date.today()
    return "grace" if d <= GRACE_END else "strict"


# ===== 프롬프트 블록 =====

CLASSIFY_RULES = """## 1단계 — 보고 유형(report_type) 분류
내용을 보고 셋 중 하나로 분류하라:
- "C" (의사결정 보고): 대표·리더가 결정해줘야 할 사안이 있음 (decision 단서 존재)
- "B" (이슈·리스크 보고): 일정 지연·예산·품질·외부 이슈나 리스크가 있음 (C에 해당 없을 때)
- "A" (진행 공유 보고): 특별한 리스크·결정 사안 없음"""


def _weights_block() -> str:
    lines = ["## 2단계 — 분류된 유형의 루브릭으로만 채점 (유형별 합계 100점)",
             "유형에 없는 항목은 채점하지 말고 결과에서 생략하라(감점 아님 — 그 유형에선 요구되지 않는 항목이다).",
             ""]
    for t in ("A", "B", "C"):
        w = TYPE_WEIGHTS[t]
        parts = [f"{k}({ITEM_LABELS[k]}) {v}" for k, v in w.items()]
        lines.append(f"- Type {t} ({TYPE_LABELS[t]}): " + " / ".join(parts))
    lines.append("")
    lines.append("""항목별 만점 기준:
  context — 어떤 프로젝트의 일인지 + 왜 하는지가 담겨 있다
  objective — 목표 대비 진행(% 또는 성공 기준)이 숫자·상태로 있다
  evidence — 판단 문장에서 사실과 의견이 구분된다
  priority — 오늘 가장 중요했던 업무와 내일 최우선이 드러난다
  risk — 발생한 문제/예상 위험 + 대응이 있다
  decision — 관리자가 결정할 것이 옵션·추천·기한과 함께 있다 (Type C만)
  support — 무엇이·언제까지·왜 필요한지 있다 (Type B·C만)""")
    return "\n".join(lines)


_RULES_COMMON = """- risk/decision/support는 직원이 "없음"이라고 **명시적으로 판단**했으면 만점.
  아예 언급이 없으면(공란) 0점. 공란(생각 안 함)과 "없음"(판단한 결과)은 다르다.
- **0점은 그 항목의 단서가 전혀 없을 때만.** 부분 충족은 부분 점수를 줘라 —
  업무명·산출물이 있으면 context는 최소 부분 점수, 내일 계획이 있으면 priority 부분 점수,
  이슈가 기재돼 있으면 risk 부분 점수."""

RUBRIC_RULES_STRICT = _RULES_COMMON + """
- **risk 예외(조건부 재질문)**: "없음"이라고 답했어도 보고 안에
  ①마감 임박(3일 이내) ②외부 회신 대기 ③승인·견적 미확정 ④일정 변경 발생
  ⑤예산 초과 가능성 단서가 보이면 risk 만점 금지 — 그 단서를 근거로
  영향과 대응을 물어라.
- **사실·해석 분리(evidence)**: 타인의 의사·감정·의도를 단정한 문장
  ("클라이언트가 원한다", "업체가 어려워하는 것 같다")이 직접 확인된 발언인지
  담당자의 해석인지 구분되지 않으면 evidence를 감점하라.
- **모호 표현은 충족으로 치지 마라**: "진행 중/확인 중/거의 완료/조금 늦어질 듯/
  ~것 같다/업체와 이야기했다"처럼 날짜·수치·주체·결과가 없는 표현은 해당 항목을
  부분 점수로 낮춰라.
- **다음 액션은 행동 단위 + 기한**이 있어야 priority 만점.
  "계속 진행", "추가 확인"처럼 기한·행동이 없으면 부분 점수."""

RUBRIC_RULES_GRACE = _RULES_COMMON + """
- (순화 기간 채점 — 감점은 하되 폭을 줄인다)
- **risk 예외(조건부 재질문)**: "없음"이라고 답했어도 보고 안에
  ①마감 임박(3일 이내) ②외부 회신 대기 ③승인·견적 미확정 ④일정 변경 발생
  ⑤예산 초과 가능성 단서가 보이면 risk 만점은 주지 마라 — 단 배점의 80% 이상은
  부여하고, 그 단서를 근거로 영향과 대응을 물어라.
- **사실·해석 분리(evidence)**: 타인의 의사·감정을 단정한 문장이 직접 발언인지
  해석인지 구분되지 않으면 소폭 감점하되 배점의 80% 이상은 유지하고, 분리 질문을 던져라.
- **모호 표현**: "진행 중/확인 중/~것 같다"처럼 날짜·수치·주체·결과가 없는 표현은
  해당 항목을 만점 대신 배점의 60% 이상 부분 점수로 낮추고, 구체화 질문을 던져라.
- **다음 액션**: 행동 단위 + 기한이 있어야 priority 만점. 없으면 배점의 60% 이상
  부분 점수 + 구체화 질문."""


def build_prompt(mode=None) -> str:
    """공용 채점 지시문 (분류 → 유형별 루브릭 → 감점 규칙).

    출력 형식(JSON 스키마)은 포함하지 않는다 — 봇/시뮬레이터가 각자 형식 블록을
    이어붙인다. mode 미지정 시 오늘 날짜로 자동 결정.
    """
    m = mode or current_mode()
    rules = RUBRIC_RULES_GRACE if m == "grace" else RUBRIC_RULES_STRICT
    head = ("너는 ARISA, 직원의 보고 품질을 비추는 거울이다. 평가·질책이 아니라\n"
            "'이 보고가 관리자의 의사결정을 가능하게 하는가'를 잰다.\n")
    mode_note = ("\n(현재 순화 기준 기간 — 감점 폭을 줄여 채점한다)\n"
                 if m == "grace" else "\n")
    return (head + mode_note + "\n" + CLASSIFY_RULES + "\n\n" + _weights_block()
            + "\n\n## 채점 규칙\n" + rules)


def validate_scores(result: dict) -> dict:
    """LLM 채점 결과 검증 — 유형별 가중치로 클램프하고 total 재계산.

    result에는 report_type과 scores(dict)가 있어야 한다. scores 값은
    int 또는 {"score": int, ...} 형태 모두 허용 (시뮬레이터는 후자).
    유형에 없는 항목은 제거한다. 반환은 같은 result (in-place 수정).
    """
    rtype = result.get("report_type")
    if rtype not in TYPE_WEIGHTS:
        rtype = "A"
        result["report_type"] = rtype
    weights = TYPE_WEIGHTS[rtype]
    raw = result.get("scores") or {}
    clamped, total = {}, 0
    for k, w in weights.items():
        v = raw.get(k)
        if isinstance(v, dict):
            try:
                s = max(0, min(int(v.get("score") or 0), w))
            except (TypeError, ValueError):
                s = 0
            v = dict(v)
            v["score"], v["max"] = s, w
            clamped[k] = v
        else:
            try:
                s = max(0, min(int(v or 0), w))
            except (TypeError, ValueError):
                s = 0
            clamped[k] = s
        total += s
    result["scores"] = clamped
    result["total"] = total
    result["mode"] = current_mode()
    result["weights_version"] = WEIGHTS_VERSION
    return result
