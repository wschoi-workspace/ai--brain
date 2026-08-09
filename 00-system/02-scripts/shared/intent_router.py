"""ARISA Intent Router — "어떤 봇을 써야 하지?"를 없애는 층.

## 왜 만드는가 (현장 근거)
`20-operations/23-arisa/inquiries/inbox.jsonl`에 남은 미처리 입력 2건이 **둘 다 라우팅 실패**였다.
- 2026-07-29 김가은: 완성된 업무보고 전문을 자유 입력으로 보냈으나
  "⚠️ 저장되지 않았습니다. /report 를 먼저 누른 후 다시 입력해주세요"로 반려됨.
  봇은 `looks_like_report: true`로 **의도를 이미 알아본 뒤에 거절했다.**
- 2026-07-30 정예은: 슬래시 없는 `report` 입력 → 문의로 접수.

즉 문제는 인식이 아니라 **처리**다. 인식하고도 사용자에게 "다시 하라"고 되돌린다.
그래서 이 라우터의 제1원칙은:

    **의도를 알아봤으면 실행하거나 확인을 묻는다. 되돌리지 않는다.**

## 구조
규칙 1차 → (모호하면) LLM 2차 → (그래도 모호하면) 확인 질문.
규칙이 앞인 이유: 결정론적이고 공짜이며, 오분류를 재현·수정할 수 있다.
LLM은 규칙이 못 가른 것만 본다.

## Role 매핑
인텐트는 Role(내부 에이전트)로 접힌다. 봇은 하나, Role은 여럿 — 사용자에게는 Role이 보이지 않는다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Role (내부 에이전트) ────────────────────────────────────
ROLE_REPORT = "daily_report"    # 일일 업무보고
ROLE_TASK = "task"              # 내 업무·할 일
ROLE_PROJECT = "project"        # 프로젝트 조회
ROLE_MEETING = "meeting"        # 회의록·회의 요약
ROLE_BRIEF = "brief"            # 브리프
ROLE_MEMO = "memo"              # 개인 메모(Second Brain)
ROLE_POLICY = "policy"          # 사내 규정·사규 (원문 인용 기반)
ROLE_CONVERSATION = "conversation"  # 일반 대화

# ── Intent ────────────────────────────────────────────────
I_REPORT = "report_submit"
I_MY_WORK = "my_work"
I_PROJECT = "project_query"
I_MEETING_DOC = "meeting_doc"
I_MEETING_SUM = "meeting_summarize"
I_BRIEF = "brief"
I_MEMO = "memo"
I_POLICY = "policy_question"
I_LEAVE_BALANCE = "leave_balance"
I_CHAT = "chat"
I_UNKNOWN = "unknown"

INTENT_ROLE = {
    I_REPORT: ROLE_REPORT, I_MY_WORK: ROLE_TASK, I_PROJECT: ROLE_PROJECT,
    I_MEETING_DOC: ROLE_MEETING, I_MEETING_SUM: ROLE_MEETING, I_BRIEF: ROLE_BRIEF,
    I_MEMO: ROLE_MEMO, I_POLICY: ROLE_POLICY, I_LEAVE_BALANCE: ROLE_POLICY,
    I_CHAT: ROLE_CONVERSATION, I_UNKNOWN: ROLE_CONVERSATION,
}

# 확신 임계값 — 이 아래는 실행하지 않고 확인을 묻는다(거절하지 않는다).
CONFIRM_BELOW = 0.75

# ── 봇 분할 (2026-08-09) ──────────────────────────────────
# 인텐트를 어느 봇이 담당하는가. **여기가 단일 출처다.**
# 각 봇이 자기 목록을 따로 들고 있으면 새 인텐트가 늘 때 한쪽만 고쳐져 조용히 새는 곳이 생긴다.
#
# 경계 = "대화 상태를 쓰는가":
#   아리사   — 분장→보고→완료 환류. 여러 턴을 주고받는 흐름이라 상태가 필요하다
#   알군(R)  — 물으면 답하고 끝. ConversationHandler를 아예 만들지 않는다
BOT_ARISA = "arisa"      # 분장·보고
BOT_SUPPORT = "support"  # 조회·질의

# 사용자에게 보이는 이름. 텔레그램 표시 이름과 일치시킨다 —
# 안내문의 이름과 텔레그램 표시 이름이 다르면 직원이 어느 창을 열지 못 찾는다.
BOT_LABEL = {BOT_ARISA: "아리사", BOT_SUPPORT: "알군"}

INTENT_BOT = {
    I_REPORT: BOT_ARISA,
    I_MY_WORK: BOT_ARISA,        # 분장의 소비 측 — "내 할 일 → 그중 하나 보고"가 한 창에서 이어져야
    I_MEMO: BOT_ARISA,           # 개인 메모는 별도 봇(@wonseok_brain_bot) 소관이나 접수는 여기서
    I_PROJECT: BOT_SUPPORT,
    I_MEETING_DOC: BOT_SUPPORT,
    I_MEETING_SUM: BOT_SUPPORT,
    I_BRIEF: BOT_SUPPORT,
    I_POLICY: BOT_SUPPORT,
    I_LEAVE_BALANCE: BOT_SUPPORT,
    # I_CHAT·I_UNKNOWN은 담당을 두지 않는다 — 받은 쪽이 그대로 처리한다(핑퐁 방지)
}


def owner_of(intent_name: str) -> str | None:
    """이 인텐트를 담당하는 봇. 담당이 없으면 None(받은 쪽이 처리)."""
    return INTENT_BOT.get(intent_name)


def handoff_message(intent_name: str, target_bot: str, target_username: str) -> str:
    """다른 봇 소관일 때 안내문. **막지 않고 링크 한 번으로 건너가게 한다.**

    창구를 나눈 순간 "어떤 봇을 써야 하지?"가 다시 생긴다. 잘못 들어온 사람을
    돌려세우는 게 아니라 문을 열어주는 것이 이 함수의 목적이다.
    """
    what = {
        I_POLICY: "사내 규정",
        I_LEAVE_BALANCE: "연차",
        I_PROJECT: "프로젝트 현황",
        I_MEETING_DOC: "회의록",
        I_MEETING_SUM: "회의 정리",
        I_BRIEF: "브리프",
        I_REPORT: "업무보고",
        I_MY_WORK: "내 할 일",
    }.get(intent_name, "그 요청")
    label = BOT_LABEL.get(target_bot, "다른 봇")
    # 받침 유무로 조사를 고른다 — "업무보고은"처럼 어색하면 봇이 대충 만든 티가 난다.
    # 봇 이름 뒤에는 조사를 붙이지 않는다("R가"/"R이" 같은 알파벳 조사 문제를 아예 피한다).
    last = what[-1]
    josa = "은" if (ord(last) - 0xAC00) % 28 else "는"
    return (f"{what}{josa} {label} 담당입니다 👉 https://t.me/{target_username}\n\n"
            "보내주신 내용을 그대로 복사해 붙여넣으시면 됩니다.")


@dataclass
class Intent:
    name: str
    confidence: float
    role: str = ""
    slots: dict = field(default_factory=dict)
    reason: str = ""
    source: str = "rule"     # rule | llm | command

    def __post_init__(self):
        if not self.role:
            self.role = INTENT_ROLE.get(self.name, ROLE_CONVERSATION)

    @property
    def needs_confirm(self) -> bool:
        return self.confidence < CONFIRM_BELOW


# ── 규칙 사전 ──────────────────────────────────────────────
# 슬래시 유무·오타를 흡수한다. 정예은의 `report`가 문의로 빠진 사고의 직접 대응.
_COMMANDS = {
    "report": I_REPORT, "리포트": I_REPORT, "보고": I_REPORT, "업무보고": I_REPORT,
    "todo": I_MY_WORK, "할일": I_MY_WORK, "내할일": I_MY_WORK, "myrwork": I_MY_WORK,
    "project": I_PROJECT, "프로젝트": I_PROJECT,
    "brief": I_BRIEF, "브리프": I_BRIEF,
    "meeting": I_MEETING_DOC, "회의록": I_MEETING_DOC,
    "memo": I_MEMO, "메모": I_MEMO,
}

# 업무보고 어휘 — 기존 daily-report-bot의 _REPORT_INTENT_RE를 계승(현장 검증된 사전)
# 2026-08-09: 야근·출장·외근·납품·촬영·답사 추가. "오늘 야근했습니다"가 어휘 0으로
# unknown에 빠지던 구멍. 규정 인텐트는 **질문 신호를 함께 요구**하므로 겹치지 않는다.
_REPORT_WORDS = re.compile(
    r"업무|보고|진행|완료|발송|처리|수정|확인|준비|미팅|회의|매출|발주|정리|견적|세미나|팝업|오픈|마감"
    r"|야근|출장|외근|납품|촬영|답사|입고|시공|계약|제안")
# 보고서 형태의 구조 신호 — 소제목 줄. 콜론이 있든(오늘: …) 단독 줄이든(목표\n…) 잡는다.
# 2026-07-29 김가은 반려 건이 정확히 후자였다: "목표 / 진행 과정 / 결과물 / 사용 도구"가
# 콜론 없이 각각 한 줄로 서 있었고, 콜론을 요구하는 규칙은 이걸 서식으로 보지 못한다.
_REPORT_SHAPE = re.compile(
    r"^\s*(목표|오늘|금일|진행\s*과정|진행\s*상황|결과물|산출물|완료|이슈|내일|특이사항|사용\s*도구)"
    r"\s*(?:[:：\-].*)?$", re.M)

# 조사를 흡수한다 — 2026-08-03 실사용에서 "내가할일 알려줘"가 규칙을 빠져나가 LLM 2차로 넘어갔다.
# (`(내|나)\s*할일`은 '내'와 '할일' 사이의 '가'를 못 넘는다). 규칙이 잡으면 공짜에 즉시다.
# 보고 서술 어미 — 질문이 아니라 "한 일을 말하는" 문장의 끝맺음.
# 어휘가 하나뿐인 짧은 보고("오늘 야근했습니다")를 건지는 보조 신호다.
_REPORT_ENDING_RE = re.compile(
    r"(했|였|왔|갔|봤|줬|냈|었)(습니다|어요|음|다)\s*[.!]?\s*$"
    r"|(완료|종료|마무리|끝)\s*[.!]?\s*$"
    r"|(합니다|했네요|했음|중입니다|예정입니다)\s*[.!]?\s*$", re.M)

_MY_WORK_RE = re.compile(
    r"(내|나)(가|는|의|한테|에게)?\s*(할\s*일|업무|일감|태스크|일정)"
    r"|오늘\s*(뭐|무엇|할)|남은\s*(일|업무)|뭐\s*하[지면]|미완|밀린\s*(일|업무)")
_PROJECT_RE = re.compile(r"프로젝트|어떻게\s*(돼|되|가)|진행\s*상황|현황|어디까지")
_MEETING_RE = re.compile(r"회의록|회의\s*(내용|정리|요약)|미팅\s*(내용|정리)|녹취|전사")
_BRIEF_RE = re.compile(r"브리프|브리핑|어제\s*(보고|요약)|오늘\s*아침")
_MEMO_RE = re.compile(r"^\s*(메모|기록|노트|저장|적어)\s*[:：]?\s*")

# ── 사내 규정 (2026-08-09) ────────────────────────────────
# 규정 어휘만으로는 부족하다. "오늘 야근했습니다"는 보고이지 질문이 아니다.
# 그래서 **주제어 + 질문 신호**를 모두 요구한다.
_POLICY_TOPIC_RE = re.compile(
    r"규정|사규|취업규칙|규칙|방침|수당|야근|초과근무|연장근로|고정OT"
    r"|연차|휴가|반차|병가|경조|육아|출산|휴직"
    r"|퇴직금|퇴직급여|급여|임금|월급|상여|정산"
    r"|수습|채용|근로계약|징계|해고|정년|복무|겸업|재택|유연근무"
    r"|개인정보|괴롭힘|성희롱|시프트|대타")
_POLICY_ASK_RE = re.compile(
    r"\?|？|되나|되나요|인가요|입니까|하나요|가능한|가능해|가능하|얼마|며칠|몇\s*(일|시간|퍼센트|%)"
    r"|어떻게|어떤|무엇|뭐[야지]|알려줘|알려주|규정상|기준|어디|언제|누가|왜")

# "내 연차 며칠 남았어?"는 규정이 아니라 **내 데이터**다. 규정 문서로는 답이 안 나온다.
# 이걸 규정으로 보내면 "규정에서 못 찾았습니다"라는 엉뚱한 답이 나간다 → 따로 가른다.
_LEAVE_BALANCE_RE = re.compile(
    r"(연차|휴가|월차|반차).{0,10}(남았|남은|잔여|얼마나\s*(있|남)|몇\s*개|몇\s*일\s*(남|있))"
    r"|(잔여|남은)\s*(연차|휴가)"
    r"|내\s*연차|연차\s*현황|휴가\s*현황")

# 회의 전사 특유의 신호 — 화자 표기·타임스탬프가 반복되면 요약 대상이다
_TRANSCRIPT_HINT = re.compile(r"^\s*(\[?\d{1,2}:\d{2}\]?|[가-힣]{2,4}\s*[:：])", re.M)
_TRANSCRIPT_MIN_CHARS = 800


def _norm_cmd(text: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", (text or "").strip().lower())


def route(text: str, *, has_attachment: bool = False, in_session: bool = False) -> Intent:
    """규칙 1차 라우팅. 확신이 낮으면 낮은 confidence로 돌려준다(거절하지 않는다).

    in_session=True면 진행 중인 대화 흐름(ConversationHandler 등)이 있다는 뜻 —
    호출측이 이 값을 보고 흐름 유지/이탈을 정한다. 라우터는 판단만 하고 강제하지 않는다.
    """
    raw = (text or "").strip()
    if not raw:
        return Intent(I_UNKNOWN, 0.0, reason="빈 입력")

    # 1) 명시적 커맨드 — 슬래시가 있든 없든 같게 취급
    cmd = _norm_cmd(raw.lstrip("/"))
    if raw.startswith("/") or (len(raw) <= 12 and cmd in _COMMANDS):
        if cmd in _COMMANDS:
            return Intent(_COMMANDS[cmd], 0.99, source="command",
                          reason=f"커맨드 '{cmd}'" + ("" if raw.startswith("/") else " (슬래시 없음 — 동일 처리)"))
        return Intent(I_UNKNOWN, 0.2, source="command", reason=f"모르는 커맨드 '{cmd}'")

    # 2) 메모 접두어 — 명시적이므로 우선
    if _MEMO_RE.match(raw):
        return Intent(I_MEMO, 0.95, slots={"text": _MEMO_RE.sub("", raw, count=1).strip()},
                      reason="메모 접두어")

    # 3) 긴 전사 붙여넣기 → 회의 요약
    if len(raw) >= _TRANSCRIPT_MIN_CHARS and len(_TRANSCRIPT_HINT.findall(raw)) >= 3:
        return Intent(I_MEETING_SUM, 0.9, slots={"text": raw},
                      reason=f"전사 형태 장문({len(raw)}자, 화자·시각 표기 반복)")

    lines = [ln for ln in raw.splitlines() if ln.strip()]
    words = len(_REPORT_WORDS.findall(raw))

    # 4) 업무보고 — 인식했으면 **실행 또는 확인**. 되돌리지 않는다.
    #    (구 동작: looks_like_report=True인데도 "/report 먼저 누르세요"로 반려 → 현장 실패 2건의 원인)
    shaped = bool(_REPORT_SHAPE.search(raw))
    if shaped and words >= 1:
        return Intent(I_REPORT, 0.92, slots={"text": raw},
                      reason=f"보고 서식({len(lines)}줄, 어휘 {words})")
    if words >= 2 and len(lines) >= 3:
        return Intent(I_REPORT, 0.8, slots={"text": raw},
                      reason=f"보고 어휘 {words}개 · {len(lines)}줄")

    q = raw.endswith("?") or "?" in raw

    # 4.5) 내 연차 잔여 — 규정이 아니라 **내 데이터**다.
    #      규정 문서로 보내면 "규정에서 못 찾았습니다"라는 엉뚱한 답이 나가므로 먼저 가른다.
    if _LEAVE_BALANCE_RE.search(raw):
        return Intent(I_LEAVE_BALANCE, 0.9 if q else 0.8, reason="연차 잔여 조회 어휘")

    # 4.6) 사내 규정 — 주제어 + 질문 신호를 **둘 다** 요구한다.
    #      "오늘 야근했습니다"는 보고이지 질문이 아니다. 어휘만 보면 그걸 규정으로 잡는다.
    if _POLICY_TOPIC_RE.search(raw) and _POLICY_ASK_RE.search(raw):
        return Intent(I_POLICY, 0.88 if q else 0.78, slots={"question": raw},
                      reason="규정 주제어 + 질문형" + ("" if q else " (물음표 없음)"))

    # 5) 조회 인텐트 — 질문형이면 확신을 올린다
    for rx, name in ((_MY_WORK_RE, I_MY_WORK), (_MEETING_RE, I_MEETING_DOC),
                     (_BRIEF_RE, I_BRIEF), (_PROJECT_RE, I_PROJECT)):
        if rx.search(raw):
            return Intent(name, 0.85 if q else 0.7, reason=f"{name} 어휘 매치" + (" + 질문형" if q else ""))

    # 6) 짧은 보고형 — 어휘는 있는데 구조가 약하다. 확인을 묻는 구간.
    #    어휘가 1개뿐이어도 **서술 어미**로 끝나면 보고로 본다("오늘 야근했습니다").
    #    질문이 아니라 사실 진술이라는 신호다. 확신은 낮게 줘서 확인을 거친다.
    if words >= 1 and not q and _REPORT_ENDING_RE.search(raw):
        return Intent(I_REPORT, 0.6, slots={"text": raw},
                      reason=f"보고 어휘 {words}개 + 서술 어미 — 확인 필요")
    if words >= 2:
        return Intent(I_REPORT, 0.55, slots={"text": raw},
                      reason=f"보고 어휘 {words}개지만 구조 약함 — 확인 필요")

    if q:
        return Intent(I_CHAT, 0.7, reason="질문형")
    return Intent(I_UNKNOWN, 0.3, reason="규칙으로 판별 불가 — LLM 2차 또는 확인 질문")


# ── LLM 2차 ────────────────────────────────────────────────
CLASSIFY_PROMPT = """너는 회사 업무 어시스턴트의 의도 분류기다. 사용자 메시지를 아래 중 하나로 분류한다.

- report_submit: 오늘 한 일을 보고하는 내용 (완료·진행·이슈 서술)
- my_work: 본인의 할 일·남은 업무를 묻는 것
- project_query: 특정 프로젝트나 전체 프로젝트 현황을 묻는 것
- meeting_doc: 과거 회의록 내용을 찾는 것
- meeting_summarize: 회의 전사·긴 원문을 정리해달라는 것
- brief: 일일 브리프를 달라는 것
- memo: 개인적으로 남겨두려는 생각·아이디어
- policy_question: 사내 규정·사규를 묻는 것 (연차 신청 절차, 야근수당 계산, 수습기간, 징계 등)
- leave_balance: **본인의** 연차 잔여 일수를 묻는 것 (규정이 아니라 내 데이터)
- chat: 위 어디에도 안 맞는 일반 질문·대화

JSON만 출력한다: {"intent": "...", "confidence": 0.0~1.0, "reason": "한 문장"}
확신이 없으면 confidence를 낮게 준다. 억지로 고르지 마라."""


def route_with_llm(text: str, llm_call, *, threshold: float = CONFIRM_BELOW, **kw) -> Intent:
    """규칙 → 부족하면 LLM. llm_call(system, user) -> str(JSON) 을 주입받는다.

    LLM을 주입으로 받는 이유: 라우터를 API 키 없이 테스트할 수 있어야 하기 때문이다.
    """
    it = route(text, **kw)
    if it.confidence >= threshold or it.source == "command" or not llm_call:
        return it
    try:
        import json
        raw = llm_call(CLASSIFY_PROMPT, (text or "")[:4000]) or ""
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            return it
        d = json.loads(m.group(0))
        name = d.get("intent")
        if name not in INTENT_ROLE:
            return it
        conf = float(d.get("confidence") or 0)
        if conf <= it.confidence:
            return it   # LLM이 규칙보다 확신이 낮으면 규칙을 유지한다
        return Intent(name, conf, slots=dict(it.slots), source="llm",
                      reason=f"LLM: {d.get('reason') or ''} (규칙 1차: {it.name} {it.confidence:.2f})")
    except Exception:
        return it


def confirm_question(it: Intent) -> str:
    """확신이 낮을 때 사용자에게 던질 확인 문장.

    **여기서 '다시 입력해주세요'라고 말하지 않는다.** 사용자가 이미 쓴 내용은 보존하고,
    예/아니오만 받는다. 재입력을 요구하는 순간 김가은 사례가 반복된다.
    """
    return {
        I_REPORT: "업무보고로 보입니다. 이 내용 그대로 등록할까요?",
        I_MY_WORK: "지금 남은 업무를 정리해서 보여드릴까요?",
        I_PROJECT: "프로젝트 현황을 찾아볼까요?",
        I_MEETING_DOC: "회의록을 찾아볼까요?",
        I_MEETING_SUM: "이 내용을 회의록으로 정리할까요?",
        I_BRIEF: "브리프를 가져올까요?",
        I_MEMO: "메모로 저장할까요?",
        I_POLICY: "사내 규정에서 찾아볼까요?",
        I_LEAVE_BALANCE: "연차 잔여 일수를 확인해 드릴까요?",
    }.get(it.name, "무엇을 도와드릴까요? (업무보고 · 내 할 일 · 프로젝트 · 회의록 · 브리프)")
