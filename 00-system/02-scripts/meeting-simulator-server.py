#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 Meeting OS — 회의록 시뮬레이터 (Phase 1 Conversation Prototype).

회의 전사 → 타입 분류(12종) → 구조화 회의록 → 누락 탐지 → 후속 질문 루프
→ 실행 패키지(Action/Output/Support Map/Readiness)까지 검증하는 단일 파일 서버.
표준 라이브러리만 사용(dashboard-server.py 패턴). 세션은 r4-data/sessions/*.json.

실행:   python3 meeting-simulator-server.py [port]     (기본 8781, 127.0.0.1)
테스트: python3 meeting-simulator-server.py --test 전사파일.txt
"""
import json, os, re, sys, threading, datetime, secrets, time, shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen, Request
from pathlib import Path

# .env 로드 (do-better-workspace/.env — dashboard-server.py와 동일 부트스트랩)
_WS = Path(__file__).resolve().parent.parent.parent
for _envp in (_WS / ".env",):
    if _envp.exists():
        for _l in _envp.read_text(encoding="utf-8").splitlines():
            _l = _l.strip()
            if _l and not _l.startswith("#") and "=" in _l:
                _k, _, _v = _l.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

HOST = os.environ.get("R4_HOST", "127.0.0.1")
PORT = int(os.environ.get("R4_PORT", "8781"))
DATA_DIR = Path(os.environ.get("R4_DATA") or (Path(__file__).resolve().parent / "r4-data"))
SESS_DIR = DATA_DIR / "sessions"
TRASH_DIR = SESS_DIR / "trash"
MAX_TRANSCRIPT_CHARS = 100_000
MAX_QUESTION_ROUNDS = 3

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("R4_MODEL", "claude-sonnet-4-6")

_lock = threading.Lock()


# ── LLM 호출 ──────────────────────────────────────────────────────────────

def _parse_json_text(text):
    m = re.search(r"```json\s*([\s\S]*?)```", text)
    return json.loads(m.group(1) if m else text)


def _call_llm_json(system_prompt, user_msg, max_tokens=3000, timeout=90, retry=1):
    """Anthropic 우선 → OpenAI fallback. JSON 파싱 실패 시 retry회 재요청. 실패 시 None."""
    def _anthropic(msg):
        payload = json.dumps({
            "model": ANTHROPIC_MODEL,
            "max_tokens": max_tokens, "temperature": 0.3,
            "system": system_prompt,
            "messages": [{"role": "user", "content": msg}]
        }).encode("utf-8")
        req = Request("https://api.anthropic.com/v1/messages", data=payload, headers={
            "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read())
        if d.get("stop_reason") == "max_tokens":
            raise RuntimeError("output_truncated")
        return d["content"][0]["text"]

    def _openai(msg):
        payload = json.dumps({
            "model": "gpt-4o", "temperature": 0.3, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": msg}]
        }).encode("utf-8")
        req = Request("https://api.openai.com/v1/chat/completions", data=payload,
                      headers={"Authorization": "Bearer " + OPENAI_KEY,
                               "Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read())
        return d["choices"][0]["message"]["content"]

    last_err = None
    for backend in ([_anthropic] if ANTHROPIC_KEY else []) + ([_openai] if OPENAI_KEY else []):
        msg = user_msg
        for attempt in range(retry + 1):
            try:
                return _parse_json_text(backend(msg))
            except json.JSONDecodeError as e:
                last_err = e
                msg = user_msg + "\n\n(이전 응답이 JSON 파싱에 실패했다. 설명 없이 유효한 JSON만 출력하라.)"
            except Exception as e:
                last_err = e
                break  # API 에러는 재시도 없이 다음 backend로
    sys.stderr.write(f"[llm] 실패: {last_err}\n")
    return None


# ── 회의 타입 · 필수 정보 모델 · Enum ────────────────────────────────────

MEETING_TYPES = {
    "INFO_SHARE":        "정보 공유 미팅",
    "CONDITION_CHECK":   "컨디션 체크 미팅",
    "FIRST_MEETING":     "1차 미팅",
    "PROJECT_KICKOFF":   "프로젝트 킥오프",
    "PLANNING":          "기획 및 방향성 협의",
    "WORKING_SESSION":   "실무 협의",
    "DESIGN_REVIEW":     "디자인·산출물 리뷰",
    "EXECUTION_PREP":    "실행 준비 미팅",
    "OPERATION":         "운영 미팅",
    "ISSUE_DECISION":    "이슈 해결 및 의사결정 미팅",
    "CLOSING_RETRO":     "프로젝트 종료 및 회고",
    "FOLLOW_UP":         "후속 제안 및 팔로업 미팅",
}

TYPE_TO_MODEL = {
    "INFO_SHARE": "info_share", "CONDITION_CHECK": "info_share",
    "FIRST_MEETING": "first_meeting",
    "PROJECT_KICKOFF": "kickoff",
    "PLANNING": "planning",
    "WORKING_SESSION": "working", "OPERATION": "working", "ISSUE_DECISION": "working",
    "DESIGN_REVIEW": "design_review",
    "EXECUTION_PREP": "execution_prep",
    "CLOSING_RETRO": "closing", "FOLLOW_UP": "closing",
}

REQUIRED_INFO_MODELS = {
    "info_share": [
        ("purpose", "공유 목적"), ("current_state", "현재 상황"),
        ("new_facts", "새롭게 확인된 사실"), ("notables", "특이사항"),
        ("risks", "리스크"), ("to_verify", "추가 확인 필요사항"),
        ("share_targets", "후속 공유 대상")],
    "first_meeting": [
        ("client_needs", "상대방의 요청/니즈"), ("background", "프로젝트 배경"),
        ("problem", "현재 문제"), ("expected_result", "기대하는 결과"),
        ("scope_estimate", "예상 범위"), ("stakeholders", "주요 이해관계자"),
        ("budget", "예산 정보"), ("schedule", "일정 정보"),
        ("next_steps", "다음 단계"), ("to_verify", "제안/추가 확인 필요사항")],
    "kickoff": [
        ("purpose", "프로젝트 목적"), ("problem", "해결해야 할 문제"),
        ("success_criteria", "성공 기준"), ("scope", "프로젝트 범위"),
        ("out_of_scope", "제외 범위"), ("stakeholders", "주요 이해관계자"),
        ("decision_maker", "의사결정자"), ("roles", "역할 및 책임"),
        ("key_outputs", "핵심 산출물"), ("schedule", "주요 일정"),
        ("budget", "예산"), ("constraints", "제약조건"),
        ("risks", "리스크"), ("communication", "커뮤니케이션 방식"),
        ("next_milestone", "다음 마일스톤")],
    "planning": [
        ("current_direction", "기존 방향"), ("proposed_direction", "제안된 방향"),
        ("alternatives", "선택 가능한 대안"), ("pros_cons", "각 대안의 장단점"),
        ("criteria", "핵심 판단 기준"), ("decisions", "결정사항"),
        ("undecided", "미결정사항"), ("to_verify", "추가 조사/검증사항"),
        ("execution_impact", "방향 변경이 실행에 미치는 영향")],
    "working": [
        ("prev_decisions", "이전 회의 결정사항"), ("progress", "현재 진행 상황"),
        ("changes", "이전 대비 변경사항"), ("change_reason", "변경 이유"),
        ("affected_tasks", "변경으로 영향받는 업무"), ("problems", "현재 문제"),
        ("required_actions", "필요한 조치"), ("owners", "담당자"),
        ("deadlines", "마감일"), ("before_next", "다음 회의 전 완료사항")],
    "design_review": [
        ("review_target", "리뷰 대상 산출물"), ("version", "현재 버전"),
        ("review_purpose", "검토 목적"), ("keep", "유지할 내용"),
        ("revise", "수정할 내용"), ("revise_reason", "수정 이유"),
        ("references", "참고자료"), ("revise_owner", "수정 책임자"),
        ("review_owner", "리뷰 책임자"), ("next_version_due", "다음 버전 제출일"),
        ("approval_criteria", "최종 승인 기준")],
    "execution_prep": [
        ("final_outputs", "최종 산출물"), ("part_tasks", "파트별 업무"),
        ("divisions", "담당 부서"), ("owners", "담당자"),
        ("done_criteria", "완료 기준"), ("deadlines", "마감일"),
        ("dependencies", "선행 업무"), ("budget", "예산"),
        ("contracts", "발주/계약"), ("partners", "외부 협력사"),
        ("permits", "인허가"), ("ops_ready", "운영 준비"),
        ("risks", "주요 리스크"), ("feasibility", "실행 가능 여부"),
        ("next_milestone", "다음 마일스톤")],
    "closing": [
        ("results", "프로젝트 결과"), ("completed_outputs", "완료된 산출물"),
        ("incomplete", "미완료 업무"), ("achievements", "성과"),
        ("problems_causes", "문제 및 원인"), ("handover", "인수인계"),
        ("maintenance", "유지관리"), ("settlement", "정산"),
        ("follow_up_schedule", "후속 일정"), ("proposals", "추가 제안"),
        ("next_project", "다음 프로젝트 가능성"), ("learnings", "학습/재사용 정보")],
}

DIVISIONS = ["PLANNING", "BX_DESIGN", "GRAPHIC_DESIGN", "SPACE_DESIGN", "CONSTRUCTION",
             "OPERATION", "MARKETING", "CONTENT", "FNB", "FINANCE", "LEGAL",
             "ADMINISTRATION", "LOGISTICS", "DEVELOPMENT", "MANAGEMENT", "EXTERNAL"]

DIVISION_KO = {
    "PLANNING": "기획", "BX_DESIGN": "BX디자인", "GRAPHIC_DESIGN": "그래픽",
    "SPACE_DESIGN": "공간디자인", "CONSTRUCTION": "시공", "OPERATION": "운영",
    "MARKETING": "마케팅", "CONTENT": "콘텐츠", "FNB": "F&B", "FINANCE": "재무",
    "LEGAL": "법무", "ADMINISTRATION": "총무", "LOGISTICS": "물류",
    "DEVELOPMENT": "개발", "MANAGEMENT": "경영", "EXTERNAL": "외부"}

READINESS_AREAS = [
    ("purpose_clarity", "목적 명확성"), ("scope_clarity", "범위 명확성"),
    ("output_definition", "산출물 정의"), ("owner_assignment", "담당자 지정"),
    ("schedule_confirmed", "일정 확정"), ("budget_confirmed", "예산 확정"),
    ("inputs_secured", "필요 입력자료 확보"), ("external_conditions", "외부 협력 조건"),
    ("decisions_complete", "의사결정 완료"), ("risk_response", "리스크 대응"),
    ("approval_process", "승인 프로세스"), ("next_milestone", "다음 마일스톤")]

INFO_STATUS = ["CONFIRMED", "INFERRED", "PARTIAL", "MISSING", "CONFLICTED", "NOT_REQUIRED"]


def _clamp(value, allowed, default):
    return value if value in allowed else default


# ── 프롬프트 ──────────────────────────────────────────────────────────────
# v1.0 2026-07-21 — 튜닝 기록은 10-projects/39-r4-meeting-os/README.md

PROMPT_COMMON_RULES = """당신은 회의 내용을 단순히 요약하는 비서가 아니다.
당신의 역할은 회의에서 확인된 사실·요청·의견·제안·결정·변경·리스크·업무·산출물·이해관계자 지원 요청을 구분하고,
회의 결과를 실행 가능한 프로젝트 구조로 전환하는 것이다.

다음 원칙을 반드시 따른다.
1. 사실과 의견을 구분한다.
2. 제안과 결정사항을 구분한다. 확실히 결정된 것만 CONFIRMED, 애매하면 PROPOSED로 표시한다.
3. 발언에 없는 내용을 확정된 사실처럼 만들지 않는다.
4. 추정한 정보는 추정(INFERRED)이라고 표시한다.
5. 담당자와 일정이 불명확하면 임의로 확정하지 않는다. 담당자는 추천(suggested)만 한다.
6. 업무(해야 할 일)와 산출물(만들어지는 결과물)을 구분한다.
7. 모든 핵심 업무에는 완료 기준(completionCriteria)을 만든다.
8. 실행에 필요한 외부·내부 지원을 함께 분석한다.
9. 단순 정보 공유 미팅에는 불필요한 업무를 억지로 만들지 않는다. 액션이 없는 회의도 있다.
10. 모든 주요 결과에는 전사 근거(quote+speaker)를 연결한다. 근거 인용문은 전사 원문 그대로 짧게 발췌한다.
11. 출력은 반드시 유효한 JSON만. 설명 문장·마크다운 금지.
"""

PROMPT_CLASSIFY = PROMPT_COMMON_RULES + """
[작업] 회의 전사를 읽고 (1) 회의 타입을 분류하고 (2) 메타정보를 추정하라. 전사를 재작성하지 마라.

회의 타입 12종:
""" + "\n".join(f"- {k}: {v}" for k, v in MEETING_TYPES.items()) + """

한 회의가 여러 성격을 가질 수 있다. 가장 지배적인 성격을 primaryType으로, 부차적 성격을 secondaryTypes로.
confidence는 0~1. 판단 근거(evidence)는 전사에서 짧게 발췌한 인용문 2~4개.

분류 구분 기준 (킥오프 편향 주의):
- PROJECT_KICKOFF는 프로젝트를 "처음 착수"하며 목적·범위·역할·일정을 세팅하는 회의에만 쓴다.
- 이미 진행 중인 프로젝트에서 방향·대안(A안/B안 등)을 비교·결정하면 PLANNING이다.
- 이전 결정을 전제로 진행 상황·변경·실행 항목을 다루면 WORKING_SESSION이다.
- 일방적 공유·보고가 중심이고 논의·결정이 거의 없으면 INFO_SHARE다. 요약·보고서 형식 텍스트라도 형식이 아니라 내용으로 판단하라.

출력 JSON:
{
  "classification": {
    "primaryType": "PROJECT_KICKOFF",
    "secondaryTypes": ["PLANNING"],
    "confidence": 0.85,
    "reason": ["분류 이유 1", "분류 이유 2"],
    "evidence": ["전사 인용문", "..."]
  },
  "meta": {
    "title": "회의명(추정)", "dateGuess": "YYYY-MM-DD 또는 빈문자열",
    "participants": [{"name": "이름", "roleGuess": "역할 추정"}],
    "projectGuess": "프로젝트명 추정", "clientGuess": "고객사/외부기관 추정"
  },
  "warnings": ["전사 품질 경고(화자 구분 없음 등), 없으면 빈 배열"]
}"""

_EXTRACT_SHARED = """
전수 추출 원칙 (가장 중요):
- 회의에서 합의되거나 지시된 항목을 하나도 빠뜨리지 말고 추출한다. 요약·압축 금지.
- 대화 중 짧게 지나간 합의("~하시죠", "~할게요", "~해주세요", "~보내드릴게요")도 각각 별도 항목으로 만든다.
- STT 품질이 낮아 문장이 깨져 있어도, 문맥상 명확한 합의·업무는 추출하되 confidence를 낮게(0.5~0.7) 표시한다. 완전히 불명확한 것만 제외한다.

출력 압축 규칙 (출력 잘림 방지):
- JSON은 들여쓰기·줄바꿈 없이 압축해서 출력한다.
- evidence는 항목당 최대 1개, quote는 60자 이내로 발췌한다.
- 설명 필드는 1~2문장으로 간결하게.
"""

PROMPT_EXTRACT_MINUTES = PROMPT_COMMON_RULES + _EXTRACT_SHARED + """
[작업] 회의 전사에서 구조화 회의록(minutes)만 추출하라. 결정·액션·산출물·지원요청 목록은 별도 단계에서 처리하므로 여기서는 만들지 마라.
- D_topics는 논의된 주제를 모두 나열한다 (보통 3~8개).
- evidence는 {"quote": "전사 원문 발췌", "speaker": "화자"} 형식. 화자 불명이면 "".
- 발언 충돌: 참석자들이 같은 사안(일정·예산·범위 등)을 서로 다르게 알고 있으면 반드시 G_open_issues에 "충돌: ..." 형태로 기록한다.

출력 JSON:
{
  "minutes": {
    "A_overview": {"purpose": "회의 목적"},
    "B_summary": {"core_results": ["핵심 결과 1~3개"], "key_decisions": ["핵심 결정"], "key_changes": ["중요 변경"], "biggest_risk": "가장 큰 리스크(없으면 빈문자열)", "next_steps": ["다음 단계"]},
    "C_status": {"before": "회의 전 상황", "after": "현재 상황", "delta": "회의로 달라진 점"},
    "D_topics": [{"topic": "주제", "background": "논의 배경", "discussion": "주요 논의", "conclusion": "결론", "rationale": "결정 근거", "execution_impact": "실행 영향", "open_points": "미해결 사항", "evidence": [{"quote": "", "speaker": ""}]}],
    "F_changes": [{"what": "무엇이", "before": "기존", "after": "변경", "impact": ["영향 1"], "evidence": [{"quote": "", "speaker": ""}]}],
    "G_open_issues": [{"issue": "사안", "needed_decision": "필요한 결정", "decider": "누가 결정", "deadline": ""}],
    "H_risks": [{"risk": "리스크", "severity": "HIGH|MEDIUM|LOW", "response": "대응 방안(논의됐다면)"}],
    "L_next_schedule": [{"item": "항목", "when": "시점"}]
  }
}"""

PROMPT_EXTRACT_ITEMS = PROMPT_COMMON_RULES + _EXTRACT_SHARED + """
[작업] 회의 전사에서 실행 항목만 완전히 추출하라: 결정(decisions) + 실행업무(actions) + 산출물(outputs) + 지원요청(supportRequests).
- 1시간 이상 실무 회의라면 결정 3~8개, 액션 5~15개가 정상이다. 항목이 1~2개뿐이면 놓친 것이 없는지 전사를 다시 훑어라.

담당 부서(division)는 반드시 다음 enum 중 하나: """ + ", ".join(DIVISIONS) + """
- id 규칙: decisions=D1,D2.. / actions=A1,A2.. / outputs=O1,O2.. / supportRequests=S1,S2..
- 정보공유/컨디션체크 성격 회의라면 actions·outputs를 억지로 만들지 마라 (빈 배열 허용).
- evidence는 {"quote": "전사 원문 발췌", "speaker": "화자"} 형식. 화자 불명이면 "".
- status 값: 날짜·담당자 등 개별 필드에는 "CONFIRMED"(회의에서 확정) 또는 "INFERRED"(AI 추정)를 붙인다.
- 날짜 규칙: 상대 표현("금요일까지", "다음 주")은 회의 일시가 주어진 경우에만 실제 날짜로 환산한다. 회의 일시를 모르면 연도·날짜를 지어내지 말고 상대 표현 그대로 적고 deadlineStatus=INFERRED로 둔다. 전사에 없는 연도를 절대 만들지 마라.
- 지원요청: 외부 기관·고객사·타 부서로부터 받아야 할 자료·확인·승인(도면, 견적, 계약서, 일정 확정 등)은 빠짐없이 supportRequests로 추출한다. "OO에서 받아야 해요" 류 발언이 단서다.

출력 JSON:
{
  "decisions": [{"id": "D1", "title": "결정 제목", "description": "내용", "rationale": "근거", "rejectedAlternatives": ["제외한 대안"], "status": "CONFIRMED|PROPOSED", "decidedBy": ["결정자"], "confidence": 0.9, "evidence": [{"quote": "", "speaker": ""}]}],
  "actions": [{"id": "A1", "title": "업무명", "description": "설명", "purpose": "목적", "division": "SPACE_DESIGN", "suggestedOwner": "추천 담당자(없으면 빈문자열)", "ownerReason": "추천 이유", "deadline": "YYYY-MM-DD 또는 빈문자열", "deadlineStatus": "CONFIRMED|INFERRED|MISSING", "priority": "CRITICAL|HIGH|MEDIUM|LOW", "completionCriteria": "완료 기준(결과물+조건+검토자)", "dependencies": ["선행 업무 id"], "outputId": "연결 산출물 id 또는 빈문자열", "confidence": 0.8, "evidence": [{"quote": "", "speaker": ""}]}],
  "outputs": [{"id": "O1", "name": "산출물명", "outputType": "문서|디자인|공간|보고서|기타", "purpose": "목적", "format": "PDF v2 등", "ownerDivision": "SPACE_DESIGN", "suggestedOwner": "", "dueDate": "", "dueDateStatus": "CONFIRMED|INFERRED|MISSING", "acceptanceCriteria": ["승인 기준"], "requiredInputs": ["필요한 입력자료"], "relatedActions": ["A1"], "confidence": 0.8}],
  "supportRequests": [{"id": "S1", "actionId": "A1", "stakeholderName": "대상", "stakeholderType": "CLIENT|DECISION_MAKER|APPROVER|INTERNAL_OWNER|INTERNAL_SUPPORT|EXTERNAL_PARTNER|VENDOR|CONSULTANT|PUBLIC_AGENCY|LEGAL_ADVISOR|FINANCIAL_ADVISOR|OTHER", "requestTitle": "요청 제목", "requestedInformation": "요청 정보/산출물", "requestReason": "왜 필요한지", "requestDueDate": "", "blockingLevel": "BLOCKING|IMPORTANT|REFERENCE", "blockedWithout": "못 받으면 멈추는 업무", "confidence": 0.8}]
}"""

PROMPT_DETECT = PROMPT_COMMON_RULES + """
[작업] 아래 회의 분석 JSON을 회의 타입별 필수 정보 모델과 대조해 (1) 항목별 충족 상태를 판정하고 (2) 후속 질문을 생성하라.

항목 상태: CONFIRMED(명확히 확인) / INFERRED(문맥상 추정) / PARTIAL(일부만) / MISSING(없음) / CONFLICTED(발언 충돌) / NOT_REQUIRED(이 회의에선 불필요)
중요도: CRITICAL(없으면 실행/의사결정 불가) / IMPORTANT(품질·효율에 큰 영향) / OPTIONAL(기록하면 유용)

질문 원칙:
- 실행을 막는 정보(CRITICAL)부터. tier별로 정렬하되 전체 질문은 CRITICAL 최대 3개 + IMPORTANT 최대 3개 + OPTIONAL 최대 2개.
- 질문은 구체적으로. 가능하면 선택지(choices)를 2~5개 제시 (마지막은 "직접 입력" 없이 — UI가 처리).
- AI가 추정 가능한 값이 있으면 aiGuess에 근거와 함께 제시.
- 이미 CONFIRMED인 항목은 질문하지 마라.

출력 JSON:
{
  "infoStatus": [{"field": "success_criteria", "label": "성공 기준", "status": "MISSING", "importance": "CRITICAL", "currentValue": "현재 파악된 값(없으면 빈문자열)", "note": "판정 이유 한 줄"}],
  "questions": [{"id": "Q1", "tier": "CRITICAL", "field": "success_criteria", "question": "이번 프로젝트에서 반드시 달성해야 할 성공 기준은 무엇입니까?", "why": "이 정보가 왜 실행에 필요한지", "aiGuess": "AI 추정값(근거 포함, 없으면 빈문자열)", "choices": ["선택지1", "선택지2"], "targetPath": "값을 반영할 위치 설명"}]
}"""

PROMPT_REVISE = PROMPT_COMMON_RULES + """
[작업] 사용자가 후속 질문에 답변했다. 답변을 분석 JSON에 반영할 patch를 생성하라. 전체 JSON을 재출력하지 마라.

patch path 규칙:
- 리스트 항목: "actions.A1.deadline", "outputs.O2.dueDate", "decisions.D1.status", "supportRequests.S1.requestDueDate"
- minutes: "minutes.B_summary.biggest_risk" 같은 dict 경로
- meta: "meta.title" 등
- 새 항목 추가는 addItems에 (기존 id와 겹치지 않는 새 id 부여).
- 답변 action이 defer(추후확인)/not_applicable(해당없음)이면 infoStatusUpdates만 갱신 (defer→PARTIAL+note, not_applicable→NOT_REQUIRED).
- use_ai_guess면 aiGuess 값을 반영하고 source는 "AI_INFERRED_ACCEPTED". (currentValue·newValue에 소스 라벨 문자열을 넣지 말 것 — 실제 내용 값만)
- ask_owner면 해당 질문을 supportRequests 항목으로 addItems에 추가.
- 사용자가 직접 답변한 값의 source는 "USER_CONFIRMED".
- 남은 CRITICAL/IMPORTANT 누락이 있으면 newQuestions로 다음 라운드 질문(최대 3개) 생성. 더 물을 게 없으면 questioningComplete=true.
- newQuestions의 각 질문은 반드시 아래 스키마(id/tier/field/question/why/aiGuess/choices/targetPath)를 모두 갖춘다. id는 기존과 겹치지 않게(Q4, Q5...).

출력 JSON:
{
  "patches": [{"path": "actions.A1.deadline", "newValue": "2026-08-01", "source": "USER_CONFIRMED"}],
  "addItems": [{"collection": "supportRequests", "item": {"id": "S9", "...": "..."}}],
  "infoStatusUpdates": [{"field": "budget", "status": "CONFIRMED", "currentValue": "3천만원", "note": "사용자 확인"}],
  "newQuestions": [{"id": "Q4", "tier": "CRITICAL", "field": "budget", "question": "...", "why": "...", "aiGuess": "", "choices": [], "targetPath": ""}],
  "questioningComplete": false,
  "summary": "이번 답변으로 무엇이 반영됐는지 1~2문장"
}"""

PROMPT_FINALIZE = PROMPT_COMMON_RULES + """
[작업] 최종 분석 JSON을 평가해 (1) 실행 준비도와 (2) Executive Summary를 생성하라.

준비도 12개 영역 (key: 한글명):
""" + "\n".join(f"- {k}: {v}" for k, v in READINESS_AREAS) + """

각 영역 상태: READY / PARTIAL / NOT_READY / NOT_REQUIRED. 점수는 참고용 — 확정적 진척률로 표현하지 않는다.
infoStatus에서 CONFIRMED인 항목(currentValue 포함)은 이미 확보된 정보다 — 분석 JSON 본문에 없어도 반드시 평가에 반영하라 (예: budget이 CONFIRMED면 budget_confirmed는 NOT_READY가 아니다).
overall(%)은 NOT_REQUIRED를 제외한 영역의 READY=100/PARTIAL=50/NOT_READY=0 평균.

출력 JSON:
{
  "readiness": {
    "overall": 68,
    "areas": [{"area": "purpose_clarity", "status": "READY", "rationale": "판정 근거 한 줄"}]
  },
  "executiveSummary": {
    "oneLiner": "회의 결과 한 줄 (공유용)",
    "purpose": "회의 목적",
    "keyResults": ["핵심 결과 1~3개"],
    "keyDecisions": ["결정사항"],
    "keyChanges": ["중요 변경사항"],
    "ceoDecisionsNeeded": ["대표 의사결정 필요사항"],
    "biggestRisk": "가장 큰 리스크",
    "nextMilestone": "다음 마일스톤",
    "criticalGaps": ["실행을 막는 미확인 정보"]
  }
}"""


# ── 세션 저장소 ────────────────────────────────────────────────────────────

def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sess_path(sid):
    if not re.fullmatch(r"[0-9]{8}-[0-9]{4,6}-[0-9a-f]{4}", sid):
        raise ValueError("bad session id")
    return SESS_DIR / f"{sid}.json"


def new_session(transcript, meta):
    sid = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)
    sess = {
        "id": sid, "createdAt": _now(), "updatedAt": _now(), "status": "DRAFT",
        "meta": {k: (meta.get(k) or "") for k in
                 ("title", "date", "participants", "project", "author", "client")},
        "transcript": transcript,
        "classification": None, "typeConfirmed": False,
        "analysis": None, "infoStatus": [], "questions": [],
        "answerLog": [], "questionRound": 0,
        "readiness": None, "executiveSummary": None,
        "llmLog": [], "error": None,
    }
    save_session(sess)
    return sess


def save_session(sess):
    sess["updatedAt"] = _now()
    SESS_DIR.mkdir(parents=True, exist_ok=True)
    path = _sess_path(sess["id"])
    tmp = path.with_suffix(".tmp")
    with _lock:
        tmp.write_text(json.dumps(sess, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)


def load_session(sid):
    path = _sess_path(sid)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_sessions():
    if not SESS_DIR.exists():
        return []
    out = []
    for p in SESS_DIR.glob("*.json"):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
            cls = s.get("classification") or {}
            out.append({
                "id": s["id"], "status": s["status"], "updatedAt": s["updatedAt"],
                "title": (s.get("meta") or {}).get("title") or "(제목 없음)",
                "project": (s.get("meta") or {}).get("project") or "",
                "primaryType": (cls.get("classification") or cls).get("primaryType", "") if cls else "",
                "readiness": (s.get("readiness") or {}).get("overall"),
            })
        except Exception:
            continue
    out.sort(key=lambda x: x["updatedAt"], reverse=True)
    return out


def _log_llm(sess, call, t0, ok, note=""):
    sess["llmLog"].append({"call": call, "durationSec": round(time.time() - t0, 1),
                           "ok": bool(ok), "note": note, "ts": _now()})


# ── 파이프라인 ────────────────────────────────────────────────────────────

def _normalize_questions(qs):
    """LLM이 id/tier를 빠뜨리거나 questionId로 반환해도 UI·revise가 깨지지 않게 정규화."""
    out = []
    for i, q in enumerate(qs or [], 1):
        if not isinstance(q, dict) or not q.get("question"):
            continue
        q.setdefault("id", q.pop("questionId", None) or f"Q{i}x")
        q["tier"] = _clamp(q.get("tier"), ["CRITICAL", "IMPORTANT", "OPTIONAL"], "IMPORTANT")
        for k, default in (("field", ""), ("why", ""), ("aiGuess", ""), ("choices", []), ("targetPath", "")):
            q.setdefault(k, default)
        out.append(q)
    return out


def _user_msg_meta(sess):
    m = sess["meta"]
    lines = [f"{k}: {v}" for k, v in (("회의명", m["title"]), ("일시", m["date"]),
             ("참석자", m["participants"]), ("프로젝트", m["project"]),
             ("작성자", m["author"]), ("고객사/외부기관", m["client"])) if v]
    return ("[사용자 입력 메타정보]\n" + "\n".join(lines) + "\n\n") if lines else ""


def run_classify(sess):
    sess["status"] = "CLASSIFYING"
    save_session(sess)
    t0 = time.time()
    user_msg = _user_msg_meta(sess) + "[회의 전사]\n" + sess["transcript"]
    result = _call_llm_json(PROMPT_CLASSIFY, user_msg, max_tokens=2000, timeout=90)
    _log_llm(sess, "classify", t0, result)
    if not result:
        sess["status"] = "ERROR"
        sess["error"] = "회의 타입 분류(LLM 호출)에 실패했습니다. 재시도해 주세요."
        save_session(sess)
        return sess
    cls = result.get("classification") or {}
    cls["primaryType"] = _clamp(cls.get("primaryType"), MEETING_TYPES, "INFO_SHARE")
    cls["secondaryTypes"] = [t for t in (cls.get("secondaryTypes") or []) if t in MEETING_TYPES]
    sess["classification"] = {"classification": cls,
                              "metaGuess": result.get("meta") or {},
                              "warnings": result.get("warnings") or []}
    # 사용자 미입력 메타는 추정값으로 보충 (추정 표시는 UI에서)
    mg = result.get("meta") or {}
    if not sess["meta"]["title"]:
        sess["meta"]["title"] = mg.get("title") or ""
    if not sess["meta"]["date"]:
        sess["meta"]["date"] = mg.get("dateGuess") or ""
    if not sess["meta"]["project"]:
        sess["meta"]["project"] = mg.get("projectGuess") or ""
    sess["status"] = "TYPE_CONFIRM"
    sess["error"] = None
    save_session(sess)
    return sess


def _validate_analysis(a):
    """extract 결과의 enum·id 클램핑."""
    for act in a.get("actions") or []:
        act["division"] = _clamp(act.get("division"), DIVISIONS, "PLANNING")
        act["priority"] = _clamp(act.get("priority"), ["CRITICAL", "HIGH", "MEDIUM", "LOW"], "MEDIUM")
        act["deadlineStatus"] = _clamp(act.get("deadlineStatus"), ["CONFIRMED", "INFERRED", "MISSING"], "MISSING")
        act.setdefault("userConfirmed", {})
    for o in a.get("outputs") or []:
        o["ownerDivision"] = _clamp(o.get("ownerDivision"), DIVISIONS, "PLANNING")
        o["dueDateStatus"] = _clamp(o.get("dueDateStatus"), ["CONFIRMED", "INFERRED", "MISSING"], "MISSING")
        o.setdefault("userConfirmed", {})
    for d in a.get("decisions") or []:
        d["status"] = _clamp(d.get("status"), ["CONFIRMED", "PROPOSED"], "PROPOSED")
    for s in a.get("supportRequests") or []:
        s["blockingLevel"] = _clamp(s.get("blockingLevel"), ["BLOCKING", "IMPORTANT", "REFERENCE"], "IMPORTANT")
    for key in ("minutes", "decisions", "actions", "outputs", "supportRequests"):
        a.setdefault(key, {} if key == "minutes" else [])
    return a


def _required_model_text(ptype):
    model_key = TYPE_TO_MODEL.get(ptype, "info_share")
    items = REQUIRED_INFO_MODELS[model_key]
    return (f"[회의 타입] {ptype} ({MEETING_TYPES.get(ptype, '')})\n[필수 정보 모델: {model_key}]\n"
            + "\n".join(f"- {k}: {label}" for k, label in items))


def run_extract_detect(sess):
    """Call ②+③ 연속 실행 — 백그라운드 스레드용."""
    try:
        sess["status"] = "ANALYZING"
        save_session(sess)
        ptype = sess["classification"]["classification"]["primaryType"]
        user_msg = (_user_msg_meta(sess) + _required_model_text(ptype)
                    + "\n\n[회의 전사]\n" + sess["transcript"])
        # ②a extract-minutes (출력 잘림 방지를 위해 minutes와 실행항목을 분리 호출)
        t0 = time.time()
        r_min = _call_llm_json(PROMPT_EXTRACT_MINUTES, user_msg, max_tokens=8000, timeout=300)
        _log_llm(sess, "extract-minutes", t0, r_min)
        if not r_min:
            sess["status"] = "ERROR"
            sess["error"] = "회의록 추출(LLM 호출)에 실패했습니다. 재시도해 주세요."
            save_session(sess)
            return
        # ②b extract-items
        t0 = time.time()
        r_items = _call_llm_json(PROMPT_EXTRACT_ITEMS, user_msg, max_tokens=10000, timeout=300)
        _log_llm(sess, "extract-items", t0, r_items)
        if not r_items:
            sess["status"] = "ERROR"
            sess["error"] = "실행 항목 추출(LLM 호출)에 실패했습니다. 재시도해 주세요."
            save_session(sess)
            return
        sess["analysis"] = _validate_analysis({"minutes": r_min.get("minutes") or {}, **{
            k: r_items.get(k) or [] for k in ("decisions", "actions", "outputs", "supportRequests")}})
        save_session(sess)
        # ③ detect
        t0 = time.time()
        user_msg2 = (_required_model_text(ptype) + "\n\n[회의 분석 JSON]\n"
                     + json.dumps(sess["analysis"], ensure_ascii=False))
        result2 = _call_llm_json(PROMPT_DETECT, user_msg2, max_tokens=3000, timeout=90)
        _log_llm(sess, "detect", t0, result2)
        if not result2:
            sess["status"] = "ERROR"
            sess["error"] = "누락 정보 탐지에 실패했습니다. 재시도해 주세요."
            save_session(sess)
            return
        for st in result2.get("infoStatus") or []:
            st["status"] = _clamp(st.get("status"), INFO_STATUS, "PARTIAL")
            st["importance"] = _clamp(st.get("importance"), ["CRITICAL", "IMPORTANT", "OPTIONAL"], "OPTIONAL")
        sess["infoStatus"] = result2.get("infoStatus") or []
        sess["questions"] = _normalize_questions(result2.get("questions"))
        sess["questionRound"] = 1
        sess["status"] = "QUESTIONING" if sess["questions"] else "USER_REVIEW"
        sess["error"] = None
        save_session(sess)
    except Exception as e:
        sess["status"] = "ERROR"
        sess["error"] = f"분석 중 오류: {e}"
        save_session(sess)


def _apply_patch(sess, patch):
    """path 규칙: collection.id.field | minutes.X.Y | meta.X"""
    path = patch.get("path") or ""
    val = patch.get("newValue")
    src = patch.get("source") or "USER_CONFIRMED"
    parts = path.split(".")
    a = sess.get("analysis") or {}
    try:
        if parts[0] in ("actions", "outputs", "decisions", "supportRequests") and len(parts) >= 3:
            for item in a.get(parts[0]) or []:
                if item.get("id") == parts[1]:
                    item[parts[2]] = val
                    item.setdefault("userConfirmed", {})[parts[2]] = src
                    # 확정 상태 동기화
                    if parts[2] == "deadline" and "deadlineStatus" in item:
                        item["deadlineStatus"] = "CONFIRMED"
                    if parts[2] == "dueDate" and "dueDateStatus" in item:
                        item["dueDateStatus"] = "CONFIRMED"
                    return True
            return False
        if parts[0] == "minutes":
            node = a.get("minutes") or {}
            for p in parts[1:-1]:
                node = node.setdefault(p, {}) if isinstance(node, dict) else None
                if node is None:
                    return False
            if isinstance(node, dict):
                node[parts[-1]] = val
                return True
            return False
        if parts[0] == "meta" and len(parts) == 2:
            sess["meta"][parts[1]] = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
            return True
    except Exception:
        return False
    return False


def run_revise(sess, answers):
    """Call ④ — 답변 배치 반영."""
    sess["status"] = "REVISING"
    save_session(sess)
    t0 = time.time()
    qmap = {q.get("id"): q for q in sess.get("questions") or [] if q.get("id")}
    answer_block = []
    for ans in answers:
        q = qmap.get(ans.get("questionId")) or {}
        answer_block.append({"questionId": ans.get("questionId"), "question": q.get("question", ""),
                             "field": q.get("field", ""), "targetPath": q.get("targetPath", ""),
                             "aiGuess": q.get("aiGuess", ""),
                             "action": ans.get("action", "answer"), "text": ans.get("text", "")})
        sess["answerLog"].append({**answer_block[-1], "round": sess["questionRound"], "ts": _now()})
    user_msg = ("[현재 분석 JSON]\n" + json.dumps(sess["analysis"], ensure_ascii=False)
                + "\n\n[현재 infoStatus]\n" + json.dumps(sess["infoStatus"], ensure_ascii=False)
                + "\n\n[이번 라운드 답변]\n" + json.dumps(answer_block, ensure_ascii=False)
                + f"\n\n[라운드] {sess['questionRound']}/{MAX_QUESTION_ROUNDS}"
                + (" — 마지막 라운드이므로 newQuestions는 비우고 questioningComplete=true로."
                   if sess["questionRound"] >= MAX_QUESTION_ROUNDS else ""))
    result = _call_llm_json(PROMPT_REVISE, user_msg, max_tokens=3000, timeout=90)
    _log_llm(sess, "revise", t0, result)
    if not result:
        sess["status"] = "QUESTIONING"
        sess["error"] = "답변 반영에 실패했습니다. 다시 시도해 주세요."
        save_session(sess)
        return sess
    applied, failed = 0, 0
    for p in result.get("patches") or []:
        if _apply_patch(sess, p):
            applied += 1
        else:
            failed += 1
    for add in result.get("addItems") or []:
        coll = add.get("collection")
        if coll in ("actions", "outputs", "decisions", "supportRequests") and isinstance(add.get("item"), dict):
            sess["analysis"].setdefault(coll, []).append(add["item"])
            applied += 1
    _validate_analysis(sess["analysis"])
    stmap = {s["field"]: s for s in sess["infoStatus"]}
    for up in result.get("infoStatusUpdates") or []:
        s = stmap.get(up.get("field"))
        if s:
            s["status"] = _clamp(up.get("status"), INFO_STATUS, s["status"])
            if up.get("currentValue"):
                s["currentValue"] = up["currentValue"]
            if up.get("note"):
                s["note"] = up["note"]
    # 결정론적 반영 — LLM이 infoStatusUpdates를 빠뜨려도 답변 자체는 반드시 상태에 남긴다
    for ab in answer_block:
        s = stmap.get(ab.get("field"))
        if not s:
            continue
        act = ab["action"]
        if act == "answer" and ab["text"].strip():
            s["status"] = "CONFIRMED"
            s["currentValue"] = ab["text"].strip()
            s["note"] = "사용자 답변"
        elif act == "use_ai_guess" and ab.get("aiGuess"):
            s["status"] = "CONFIRMED"
            s["currentValue"] = ab["aiGuess"]
            s["note"] = "AI 추정값 수용"
        elif act == "not_applicable":
            s["status"] = "NOT_REQUIRED"
            s["note"] = "사용자: 해당 없음"
        elif act == "defer":
            s["status"] = "PARTIAL" if s["status"] != "CONFIRMED" else s["status"]
            s["note"] = "추후 확인"
        elif act == "ask_owner":
            s["note"] = "담당자에게 질문 전달됨"
    sess["reviseSummary"] = result.get("summary") or ""
    new_qs = _normalize_questions(result.get("newQuestions"))
    done = bool(result.get("questioningComplete")) or sess["questionRound"] >= MAX_QUESTION_ROUNDS or not new_qs
    if done:
        sess["questions"] = []
        sess["status"] = "USER_REVIEW"
    else:
        sess["questions"] = new_qs[:3]
        sess["questionRound"] += 1
        sess["status"] = "QUESTIONING"
    sess["error"] = None
    save_session(sess)
    return sess


def run_finalize(sess):
    """Call ⑤ — readiness + exec summary."""
    sess["status"] = "FINALIZING"
    save_session(sess)
    t0 = time.time()
    user_msg = ("[최종 분석 JSON]\n" + json.dumps(sess["analysis"], ensure_ascii=False)
                + "\n\n[infoStatus]\n" + json.dumps(sess["infoStatus"], ensure_ascii=False))
    result = _call_llm_json(PROMPT_FINALIZE, user_msg, max_tokens=4000, timeout=120)
    _log_llm(sess, "finalize", t0, result)
    if not result:
        sess["status"] = "USER_REVIEW"
        sess["error"] = "준비도 평가에 실패했습니다. 재시도해 주세요."
        save_session(sess)
        return sess
    rd = result.get("readiness") or {}
    area_keys = [k for k, _ in READINESS_AREAS]
    areas = []
    for ar in rd.get("areas") or []:
        if ar.get("area") in area_keys:
            ar["status"] = _clamp(ar.get("status"), ["READY", "PARTIAL", "NOT_READY", "NOT_REQUIRED"], "PARTIAL")
            areas.append(ar)
    scored = [a for a in areas if a["status"] != "NOT_REQUIRED"]
    if scored:
        pts = {"READY": 100, "PARTIAL": 50, "NOT_READY": 0}
        rd["overall"] = round(sum(pts[a["status"]] for a in scored) / len(scored))
    rd["areas"] = areas
    sess["readiness"] = rd
    sess["executiveSummary"] = result.get("executiveSummary") or {}
    sess["status"] = "FINALIZED"
    sess["error"] = None
    save_session(sess)
    return sess


def run_retry(sess):
    """ERROR 상태에서 직전 단계 재실행."""
    if sess.get("classification") is None:
        return run_classify(sess)
    if sess.get("analysis") is None or not sess.get("infoStatus"):
        threading.Thread(target=run_extract_detect, args=(sess,), daemon=True).start()
        return sess
    if sess.get("readiness") is None and sess["status"] in ("ERROR", "USER_REVIEW", "FINALIZING"):
        return run_finalize(sess)
    sess["status"] = "USER_REVIEW"
    save_session(sess)
    return sess


# ── 마크다운 내보내기 (회의록정리 9섹션 호환) ─────────────────────────────

def _md_esc(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ")


def _ai_mark(item, field):
    """AI추정/확정 접미사."""
    uc = (item.get("userConfirmed") or {}).get(field)
    if uc == "USER_CONFIRMED":
        return " ✅"
    if uc == "AI_INFERRED_ACCEPTED":
        return " (AI추정·수용)"
    return ""


def build_markdown(sess):
    a = sess.get("analysis") or {}
    m = sess.get("meta") or {}
    mins = a.get("minutes") or {}
    es = sess.get("executiveSummary") or {}
    cls = ((sess.get("classification") or {}).get("classification") or {})
    ptype = cls.get("primaryType", "")
    L = []
    title = m.get("title") or "회의록"
    date = m.get("date") or datetime.date.today().isoformat()
    L.append(f"# 📝 {title} — {date}\n")
    # 메타데이터
    L.append("## 📋 회의 메타데이터\n")
    L.append("| 항목 | 내용 |\n|------|------|")
    for k, label in (("date", "일시"), ("project", "프로젝트"), ("participants", "참석자"),
                     ("author", "작성자"), ("client", "고객사/외부기관")):
        if m.get(k):
            L.append(f"| {label} | {_md_esc(m[k])} |")
    L.append(f"| 회의 타입 | {MEETING_TYPES.get(ptype, ptype)} (신뢰도 {round((cls.get('confidence') or 0)*100)}%) |\n")
    # 핵심 요약
    summ = es.get("oneLiner") or " / ".join((mins.get("B_summary") or {}).get("core_results") or [])
    if summ:
        L.append(f"## 📌 회의 핵심 요약\n\n> {summ}\n")
    # 결정사항
    decs = a.get("decisions") or []
    if decs:
        L.append("## ✅ 결정사항\n")
        L.append("| # | 결정 | 근거/맥락 | 상태 |\n|---|------|-----------|------|")
        for i, d in enumerate(decs, 1):
            extra = f" (제외 대안: {', '.join(d.get('rejectedAlternatives') or [])})" if d.get("rejectedAlternatives") else ""
            st = "확정" if d.get("status") == "CONFIRMED" else "⚠️ 결정 여부 확인 필요"
            L.append(f"| {i} | {_md_esc(d.get('title'))} | {_md_esc((d.get('rationale') or '') + extra)} | {st} |")
        L.append("")
    # To do list
    acts = a.get("actions") or []
    if acts:
        L.append("## 🎯 To do list\n")
        L.append("| 액션 | 담당 | 기한 | 완료 기준 |\n|------|------|------|-----------|")
        for act in acts:
            owner = act.get("ownerName") or (f"제안: {act['suggestedOwner']}" if act.get("suggestedOwner") else "⚠️ 미지정")
            owner += _ai_mark(act, "ownerName")
            dl = act.get("deadline") or "⚠️ 확인 필요"
            if act.get("deadlineStatus") == "INFERRED":
                dl += " (AI추정)"
            dl += _ai_mark(act, "deadline")
            div = DIVISION_KO.get(act.get("division"), act.get("division", ""))
            L.append(f"| [{div}] {_md_esc(act.get('title'))} | {_md_esc(owner)} | {_md_esc(dl)} | {_md_esc(act.get('completionCriteria'))} |")
        L.append("")
    # 의사결정 필요사항
    issues = mins.get("G_open_issues") or []
    if issues:
        L.append("## ❓ 의사결정 필요사항\n")
        L.append("| 사안 | 필요한 결정 | 누가 결정 | 데드라인 |\n|------|------------|----------|----------|")
        for it in issues:
            L.append(f"| {_md_esc(it.get('issue'))} | {_md_esc(it.get('needed_decision'))} | {_md_esc(it.get('decider') or '⚠️ 확인 필요')} | {_md_esc(it.get('deadline') or '-')} |")
        L.append("")
    # 이슈/리스크
    risks = mins.get("H_risks") or []
    if risks:
        L.append("## ⚠️ 이슈/리스크\n")
        icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        for r in risks:
            L.append(f"- {icon.get(r.get('severity'), '🟡')} {r.get('risk')}" +
                     (f" → 대응: {r['response']}" if r.get("response") else ""))
        L.append("")
    # 이후 대응
    nexts = mins.get("L_next_schedule") or []
    if nexts:
        L.append("## 🔜 이후 대응/다음 회의\n")
        L.append("| 항목 | 시점 |\n|------|------|")
        for n in nexts:
            L.append(f"| {_md_esc(n.get('item'))} | {_md_esc(n.get('when') or '-')} |")
        L.append("")
    # 한 줄 공유
    if es.get("oneLiner"):
        L.append(f"## 📤 한 줄 공유용 메시지\n\n{es['oneLiner']}\n")
    # ── R4 확장 섹션 ──
    L.append("---\n\n# R4 실행 패키지 (Meeting OS)\n")
    topics = mins.get("D_topics") or []
    if topics:
        L.append("## 주제별 논의\n")
        for t in topics:
            L.append(f"### {t.get('topic')}\n")
            for k, label in (("background", "논의 배경"), ("discussion", "주요 논의"),
                             ("conclusion", "결론"), ("rationale", "결정 근거"),
                             ("execution_impact", "실행 영향"), ("open_points", "미해결 사항")):
                if t.get(k):
                    L.append(f"- **{label}**: {t[k]}")
            L.append("")
    changes = mins.get("F_changes") or []
    if changes:
        L.append("## 변경사항\n")
        for c in changes:
            L.append(f"- **{c.get('what')}**: {c.get('before')} → {c.get('after')}")
            for imp in c.get("impact") or []:
                L.append(f"  - 영향: {imp}")
        L.append("")
    outs = a.get("outputs") or []
    if outs:
        L.append("## 산출물\n")
        L.append("| 산출물 | 목적 | 포맷 | 담당 | 제출일 | 승인 기준 |\n|--------|------|------|------|--------|-----------|")
        for o in outs:
            owner = o.get("ownerName") or (f"제안: {o['suggestedOwner']}" if o.get("suggestedOwner") else "⚠️ 미지정")
            due = (o.get("dueDate") or "⚠️ 확인 필요") + (" (AI추정)" if o.get("dueDateStatus") == "INFERRED" else "")
            L.append(f"| {_md_esc(o.get('name'))} | {_md_esc(o.get('purpose'))} | {_md_esc(o.get('format'))} | {_md_esc(owner)} | {_md_esc(due)} | {_md_esc('; '.join(o.get('acceptanceCriteria') or []))} |")
        L.append("")
    sups = a.get("supportRequests") or []
    if sups:
        L.append("## Support Map (이해관계자 지원 요청)\n")
        L.append("| 대상 | 요청 | 이유 | 기한 | 차단 수준 | 미수신 시 영향 |\n|------|------|------|------|-----------|----------------|")
        for s in sups:
            L.append(f"| {_md_esc(s.get('stakeholderName'))} | {_md_esc(s.get('requestTitle'))} | {_md_esc(s.get('requestReason'))} | {_md_esc(s.get('requestDueDate') or '-')} | {s.get('blockingLevel')} | {_md_esc(s.get('blockedWithout') or '-')} |")
        L.append("")
    rd = sess.get("readiness") or {}
    if rd:
        L.append(f"## 실행 준비도: {rd.get('overall', '-')}%\n")
        icon = {"READY": "🟢", "PARTIAL": "🟡", "NOT_READY": "🔴", "NOT_REQUIRED": "⚪"}
        label = dict(READINESS_AREAS)
        for ar in rd.get("areas") or []:
            L.append(f"- {icon.get(ar['status'], '🟡')} **{label.get(ar['area'], ar['area'])}** — {ar.get('rationale', '')}")
        L.append("")
    gaps = [s for s in sess.get("infoStatus") or [] if s.get("status") in ("MISSING", "CONFLICTED")
            and s.get("importance") in ("CRITICAL", "IMPORTANT")]
    if gaps:
        L.append("## ⚠️ 미확인 정보\n")
        for g in gaps:
            L.append(f"- [{g.get('importance')}] {g.get('label')}: {g.get('note', '')}")
        L.append("")
    L.append(f"\n---\n*R4 Meeting OS Simulator · 세션 {sess['id']} · 생성 {_now()}*\n")
    return "\n".join(L)


# ── 인쇄용 리포트 HTML (PDF 저장·워드 문서 겸용) ─────────────────────────

def _h(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build_report_html(sess, for_doc=False):
    """밝은 테마 인쇄 최적화 리포트. for_doc=True면 인쇄 버튼 생략(.doc용)."""
    a = sess.get("analysis") or {}
    m = sess.get("meta") or {}
    mins = a.get("minutes") or {}
    es = sess.get("executiveSummary") or {}
    rd = sess.get("readiness") or {}
    cls = ((sess.get("classification") or {}).get("classification") or {})
    title = m.get("title") or "회의 결과 리포트"
    date = m.get("date") or ""

    def sec(t):
        return f'<h2>{_h(t)}</h2>'

    def table(headers, rows):
        if not rows:
            return ""
        h = "<table><tr>" + "".join(f"<th>{_h(x)}</th>" for x in headers) + "</tr>"
        for r in rows:
            h += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
        return h + "</table>"

    body = []
    body.append(f"<h1>{_h(title)}</h1>")
    meta_bits = [x for x in (date, m.get("project"), m.get("participants"),
                             MEETING_TYPES.get(cls.get("primaryType"), "")) if x]
    body.append(f'<p class="meta">{_h(" · ".join(meta_bits))}</p>')
    if es.get("oneLiner"):
        body.append(f'<blockquote>{_h(es["oneLiner"])}</blockquote>')
    # 써머리
    body.append(sec("Executive Summary"))
    items = [("핵심 결과", es.get("keyResults")), ("핵심 결정", es.get("keyDecisions")),
             ("중요 변경", es.get("keyChanges")), ("대표 의사결정 필요", es.get("ceoDecisionsNeeded")),
             ("실행을 막는 미확인 정보", es.get("criticalGaps"))]
    for label, vals in items:
        if vals:
            body.append(f"<h3>{_h(label)}</h3><ul>" +
                        "".join(f"<li>{_h(v)}</li>" for v in vals) + "</ul>")
    for label, v in (("가장 큰 리스크", es.get("biggestRisk")), ("다음 마일스톤", es.get("nextMilestone"))):
        if v:
            body.append(f"<p><b>{_h(label)}:</b> {_h(v)}</p>")
    # 결정사항
    decs = a.get("decisions") or []
    if decs:
        body.append(sec("결정사항"))
        body.append(table(["#", "결정", "근거/맥락", "상태"],
            [[str(i), f"<b>{_h(d.get('title'))}</b><br>{_h(d.get('description') or '')}",
              _h(d.get("rationale") or ""),
              "확정" if d.get("status") == "CONFIRMED" else "확인 필요"]
             for i, d in enumerate(decs, 1)]))
    # To do
    acts = a.get("actions") or []
    if acts:
        body.append(sec("실행 업무 (To do)"))
        body.append(table(["우선순위", "업무", "부서", "담당", "기한", "완료 기준"],
            [[_h(t.get("priority")),
              f"<b>{_h(t.get('title'))}</b><br>{_h(t.get('description') or '')}",
              _h(DIVISION_KO.get(t.get("division"), t.get("division", ""))),
              _h(t.get("ownerName") or (("제안: " + t["suggestedOwner"]) if t.get("suggestedOwner") else "미지정")),
              _h(t.get("deadline") or "확인 필요") + (" (AI추정)" if t.get("deadlineStatus") == "INFERRED" else ""),
              _h(t.get("completionCriteria") or "")] for t in acts]))
    # 산출물
    outs = a.get("outputs") or []
    if outs:
        body.append(sec("산출물"))
        body.append(table(["산출물", "목적", "포맷", "담당", "제출일", "승인 기준"],
            [[f"<b>{_h(o.get('name'))}</b>", _h(o.get("purpose") or ""), _h(o.get("format") or ""),
              _h(o.get("ownerName") or o.get("suggestedOwner") or DIVISION_KO.get(o.get("ownerDivision"), "")),
              _h(o.get("dueDate") or "확인 필요"),
              _h("; ".join(o.get("acceptanceCriteria") or []))] for o in outs]))
    # Support Map
    sups = a.get("supportRequests") or []
    if sups:
        body.append(sec("이해관계자 지원 요청 (Support Map)"))
        body.append(table(["대상", "요청", "이유", "기한", "차단 수준"],
            [[f"<b>{_h(s.get('stakeholderName'))}</b>", _h(s.get("requestTitle") or ""),
              _h(s.get("requestReason") or ""), _h(s.get("requestDueDate") or "-"),
              _h(s.get("blockingLevel") or "")] for s in sups]))
    # 리스크·미해결
    rk = mins.get("H_risks") or []
    if rk:
        body.append(sec("리스크"))
        body.append("<ul>" + "".join(
            f"<li><b>[{_h(r.get('severity'))}]</b> {_h(r.get('risk'))}" +
            (f" — 대응: {_h(r['response'])}" if r.get("response") else "") + "</li>" for r in rk) + "</ul>")
    oi = mins.get("G_open_issues") or []
    if oi:
        body.append(sec("미해결 이슈"))
        body.append(table(["사안", "필요한 결정", "결정자", "기한"],
            [[_h(i.get("issue")), _h(i.get("needed_decision")), _h(i.get("decider") or "확인 필요"),
              _h(i.get("deadline") or "-")] for i in oi]))
    # 준비도
    if rd.get("areas"):
        body.append(sec(f"실행 준비도 — {rd.get('overall', '-')}%"))
        label = dict(READINESS_AREAS)
        body.append(table(["영역", "상태", "근거"],
            [[_h(label.get(ar["area"], ar["area"])), _h(ar["status"]), _h(ar.get("rationale") or "")]
             for ar in rd["areas"]]))
    body.append(f'<p class="foot">by Project Rent · R4 Meeting OS · 세션 {_h(sess["id"])} · {_h(_now())}</p>')

    print_btn = "" if for_doc else (
        '<div class="noprint toolbar"><button onclick="window.print()">🖨 인쇄 / PDF로 저장</button>'
        '<span>브라우저 인쇄 대화상자에서 "PDF로 저장"을 선택하세요.</span></div>')
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_h(title)}</title>
<style>
body{{font-family:'Pretendard Variable','Apple SD Gothic Neo','Malgun Gothic',sans-serif;color:#1a1a1a;background:#fff;max-width:820px;margin:0 auto;padding:40px 32px;line-height:1.6;font-size:13px}}
h1{{font-size:24px;margin:0 0 4px;border-bottom:3px solid #6C5CE7;padding-bottom:10px}}
h2{{font-size:16px;margin:28px 0 10px;color:#3b3470;border-left:4px solid #6C5CE7;padding-left:10px}}
h3{{font-size:13px;margin:14px 0 6px}}
.meta{{color:#777;font-size:12px;margin:6px 0 14px}}
blockquote{{margin:14px 0;padding:12px 16px;background:#f4f2ff;border-left:4px solid #6C5CE7;font-size:14px}}
table{{width:100%;border-collapse:collapse;font-size:12px;margin:8px 0}}
th{{background:#f0eefc;text-align:left;padding:7px 9px;border:1px solid #ddd;font-weight:600}}
td{{padding:7px 9px;border:1px solid #ddd;vertical-align:top}}
ul{{margin:4px 0 10px 20px}}
li{{margin-bottom:4px}}
.foot{{margin-top:36px;color:#999;font-size:11px;border-top:1px solid #eee;padding-top:10px}}
.toolbar{{position:sticky;top:0;background:#fff;padding:10px 0;border-bottom:1px solid #eee;margin-bottom:14px;display:flex;gap:12px;align-items:center}}
.toolbar button{{background:#6C5CE7;color:#fff;border:0;border-radius:8px;padding:10px 20px;font-size:13px;font-weight:700;cursor:pointer;font-family:inherit}}
.toolbar span{{color:#999;font-size:11px}}
@media print{{.noprint{{display:none!important}} body{{padding:0}} h2{{break-after:avoid}} table{{break-inside:auto}} tr{{break-inside:avoid}}}}
</style></head><body>
{print_btn}
{"".join(body)}
</body></html>"""


# ── HTML (UI는 PAGE_HTML 상수 — 별도 섹션) ───────────────────────────────

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>R4 Meeting OS — Simulator</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>
:root{--bg:#1A1A1A;--bg2:#202020;--bg3:#262626;--fg:#F5F0EB;--fg2:#C4BEB7;--muted:#8A857E;--line:#333;--accent:#6C5CE7;--red:#E17055;--green:#00b894;--amber:#FDCB6E}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:'Pretendard Variable',sans-serif;font-weight:300;min-height:100vh}
.wrap{max-width:1280px;margin:0 auto;padding:24px 20px}
h1{font-size:21px;font-weight:700}
.sub{color:var(--muted);font-size:13px;margin:4px 0 22px}
h1 .r4{color:var(--accent)}
section{display:none}section.on{display:block}
.panel{background:var(--bg2);border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:16px}
.panel h2{font-size:16px;font-weight:600;margin-bottom:14px}
.btn{background:var(--accent);color:#fff;border:0;border-radius:10px;padding:12px 26px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit}
.btn:disabled{opacity:.45;cursor:default}
.btn2{background:var(--bg3);color:var(--fg2);border:1px solid var(--line);border-radius:10px;padding:11px 20px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}
.btn2:hover{border-color:var(--accent);color:var(--fg)}
.btn-sm{padding:6px 14px;font-size:12px;border-radius:8px}
textarea,input[type=text]{width:100%;background:var(--bg3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:10px 12px;font-size:13px;font-family:inherit;line-height:1.6}
textarea:focus,input:focus{border-color:var(--accent);outline:none}
label{display:block;font-size:12px;font-weight:500;color:var(--fg2);margin:12px 0 5px}
.badge{display:inline-block;font-size:10px;padding:2px 8px;border-radius:4px;font-weight:700;vertical-align:middle}
.b-ai{background:rgba(108,92,231,.16);color:var(--accent);border:1px dashed var(--accent)}
.b-ok{background:rgba(0,184,148,.15);color:var(--green)}
.b-crit{background:rgba(225,112,85,.15);color:var(--red)}
.b-imp{background:rgba(253,203,110,.15);color:var(--amber)}
.b-opt{background:var(--bg3);color:var(--muted)}
.b-warn{background:rgba(225,112,85,.15);color:var(--red)}
.list-item{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin-bottom:10px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:12px}
.list-item:hover{border-color:var(--accent)}
.list-item .t{font-size:14px;font-weight:600}
.list-item .m{font-size:11px;color:var(--muted);margin-top:3px}
.st-chip{font-size:10px;padding:3px 9px;border-radius:10px;font-weight:700;white-space:nowrap}
table{width:100%;border-collapse:collapse;font-size:12px}
th{color:var(--muted);font-weight:600;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:9px 10px;border-bottom:1px solid #2a2a2a;vertical-align:top;line-height:1.55;color:var(--fg2)}
td b,td strong{color:var(--fg)}
.steps{display:flex;flex-direction:column;gap:14px;padding:10px 0}
.step{display:flex;align-items:center;gap:12px;font-size:14px;color:var(--muted)}
.step.on{color:var(--fg)}.step.done{color:var(--green)}
.dot{width:10px;height:10px;border-radius:50%;background:var(--bg3);flex-shrink:0}
.step.on .dot{background:var(--accent);animation:pulse 1.2s infinite}
.step.done .dot{background:var(--green)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
.type-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;margin-top:12px}
.type-cell{background:var(--bg3);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:12px;cursor:pointer;color:var(--fg2)}
.type-cell:hover{border-color:var(--accent)}
.type-cell.sel{border-color:var(--accent);background:rgba(108,92,231,.12);color:var(--fg)}
.conf-bar{height:6px;background:var(--bg3);border-radius:3px;overflow:hidden;margin:8px 0}
.conf-fill{height:100%;background:var(--accent);border-radius:3px}
.quote{border-left:2px solid var(--accent);padding:4px 0 4px 12px;font-size:12px;color:var(--fg2);margin:6px 0;line-height:1.5}
.qcard{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:12px}
.qcard .qt{font-size:14px;font-weight:600;line-height:1.5;margin:6px 0 4px}
.qwhy{font-size:12px;color:var(--muted);margin:4px 0 8px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.chip{background:var(--bg3);border:1px solid var(--line);border-radius:14px;padding:5px 12px;font-size:12px;cursor:pointer;color:var(--fg2)}
.chip:hover,.chip.sel{border-color:var(--accent);color:var(--fg)}
.qactions{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.qact{background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:6px 12px;font-size:11px;cursor:pointer;font-family:inherit}
.qact.sel{border-color:var(--accent);color:var(--accent);background:rgba(108,92,231,.1)}
.aiguess{background:rgba(108,92,231,.07);border:1px dashed rgba(108,92,231,.4);border-radius:8px;padding:8px 12px;font-size:12px;color:var(--fg2);margin:8px 0}
.tabs{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:16px;border-bottom:1px solid var(--line);padding-bottom:0}
.tab{background:transparent;border:0;color:var(--muted);padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;border-bottom:2px solid transparent}
.tab.on{color:var(--fg);border-bottom-color:var(--accent)}
.rgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;margin-top:12px}
.rcell{border-radius:8px;padding:10px 12px;font-size:12px;border:1px solid var(--line);background:var(--bg3)}
.rcell .rn{font-weight:600;font-size:12px}
.rcell .rr{color:var(--muted);font-size:11px;margin-top:3px;line-height:1.45}
.rcell.READY{border-color:rgba(0,184,148,.4)}.rcell.READY .rn{color:var(--green)}
.rcell.PARTIAL{border-color:rgba(253,203,110,.4)}.rcell.PARTIAL .rn{color:var(--amber)}
.rcell.NOT_READY{border-color:rgba(225,112,85,.4)}.rcell.NOT_READY .rn{color:var(--red)}
.rcell.NOT_REQUIRED{opacity:.5}
.score-circle{width:130px;height:130px;position:relative;flex-shrink:0}
.score-circle svg{transform:rotate(-90deg)}
.score-circle .val{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.score-circle .num{font-size:32px;font-weight:800}
.score-circle .lb{font-size:11px;color:var(--muted)}
.exec-top{display:flex;gap:24px;align-items:center;flex-wrap:wrap}
.kv{margin-bottom:12px}
.kv .k{font-size:11px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.kv .v{font-size:13px;color:var(--fg2);line-height:1.6}
.kv ul{margin-left:16px}
pre.raw{white-space:pre-wrap;font-size:12px;line-height:1.7;color:var(--fg2);background:var(--bg3);border-radius:10px;padding:16px;max-height:600px;overflow:auto;font-family:inherit}
.topbar{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}
.err{background:rgba(225,112,85,.1);border:1px solid rgba(225,112,85,.4);border-radius:10px;padding:12px 16px;font-size:13px;color:var(--red);margin-bottom:14px}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid var(--line);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;vertical-align:-2px;margin-right:8px}
@keyframes spin{to{transform:rotate(360deg)}}
.count{font-size:11px;color:var(--muted);text-align:right;margin-top:4px}
.meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
@media(max-width:800px){.meta-grid{grid-template-columns:1fr}}
.mini-status{font-size:12px;color:var(--fg2);line-height:1.8}
h3.sec{font-size:14px;font-weight:600;margin:18px 0 8px;color:var(--fg)}
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:center;justify-content:center;z-index:50}
.overlay.on{display:flex}
.overlay .box{background:var(--bg2);border:1px solid var(--line);border-radius:14px;padding:28px 36px;font-size:14px}
</style></head><body>
<div class="wrap">
<h1><span class="r4">R4</span> Meeting OS <span style="font-weight:300;color:var(--muted)">Simulator</span></h1>
<p class="sub">회의 전사 → 타입 분류 → 구조화 → 누락 질문 → 실행 패키지. AI가 회의를 실행 가능한 데이터로 전환합니다.</p>
<div id="err-box"></div>

<section id="scr-home" class="on">
  <div class="topbar"><h2 style="font-size:16px;font-weight:600">회의 세션</h2>
    <button class="btn" onclick="goInput()">+ 새 회의 분석</button></div>
  <div id="sess-list" style="margin-top:14px"></div>
</section>

<section id="scr-input">
  <div class="panel">
    <h2>회의 전사 입력</h2>
    <label>전사 텍스트 *</label>
    <textarea id="in-transcript" rows="14" placeholder="회의 전사·메모·정리본을 붙여넣으세요. (.txt/.md 내용 그대로)"></textarea>
    <div class="count"><span id="char-count">0</span> / 100,000자</div>
    <div class="meta-grid">
      <div><label>회의명 (선택 — 비우면 AI 추정)</label><input type="text" id="in-title"></div>
      <div><label>회의 일시 (선택)</label><input type="text" id="in-date" placeholder="2026-07-21"></div>
      <div><label>참석자 (선택)</label><input type="text" id="in-participants" placeholder="최원석, 김OO, ..."></div>
      <div><label>프로젝트명 (선택)</label><input type="text" id="in-project"></div>
      <div><label>작성자 (선택)</label><input type="text" id="in-author"></div>
      <div><label>고객사/외부기관 (선택)</label><input type="text" id="in-client"></div>
    </div>
    <div style="margin-top:18px;display:flex;gap:10px;align-items:center">
      <button class="btn" id="btn-analyze" onclick="submitMeeting()">AI 분석 시작</button>
      <button class="btn2" onclick="show('scr-home');loadList()">취소</button>
      <span id="in-msg" style="font-size:12px;color:var(--muted)"></span>
    </div>
  </div>
</section>

<section id="scr-progress">
  <div class="panel">
    <h2>분석 중...</h2>
    <div class="steps">
      <div class="step" id="stp-1"><span class="dot"></span>① 회의 타입 분류</div>
      <div class="step" id="stp-2"><span class="dot"></span>② 구조화 추출 (회의록·결정·업무·산출물·지원요청)</div>
      <div class="step" id="stp-3"><span class="dot"></span>③ 누락 정보 탐지 + 질문 생성</div>
    </div>
    <p style="font-size:12px;color:var(--muted)">경과 <span id="elapsed">0</span>초 — 회의 길이에 따라 1~4분 걸립니다.</p>
  </div>
</section>

<section id="scr-type">
  <div class="panel" id="type-card"></div>
</section>

<section id="scr-question">
  <div style="display:grid;grid-template-columns:1fr 300px;gap:16px" id="q-layout">
    <div>
      <div class="panel" style="margin-bottom:12px">
        <h2>AI 후속 질문 <span style="font-size:12px;color:var(--muted)">라운드 <span id="q-round"></span>/3</span></h2>
        <p style="font-size:12px;color:var(--muted);margin-bottom:4px">실행을 막는 정보부터 확인합니다. 각 질문에 답변하거나 처리 방식을 선택하세요.</p>
      </div>
      <div id="q-cards"></div>
      <div style="display:flex;gap:10px;margin-top:6px">
        <button class="btn" id="btn-answer" onclick="submitAnswers()">답변 제출</button>
        <button class="btn2" onclick="skipQuestions()">질문 건너뛰고 결과 보기</button>
      </div>
    </div>
    <div class="panel" style="align-self:start">
      <h2 style="font-size:13px">정보 충족 현황</h2>
      <div id="q-status" class="mini-status"></div>
    </div>
  </div>
</section>

<section id="scr-result">
  <div class="topbar" style="margin-bottom:14px">
    <div><h2 style="font-size:17px;font-weight:700" id="res-title"></h2>
      <div style="font-size:12px;color:var(--muted);margin-top:3px" id="res-sub"></div></div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <button class="btn btn-sm" onclick="window.open(API+'/api/meeting/'+S.id+'/report.html','_blank')">리포트 · PDF</button>
      <button class="btn2 btn-sm" onclick="location.href=API+'/api/meeting/'+S.id+'/export.doc'">Word(.doc)</button>
      <button class="btn2 btn-sm" onclick="location.href=API+'/api/meeting/'+S.id+'/export.md'">MD</button>
      <button class="btn2 btn-sm" onclick="location.href=API+'/api/meeting/'+S.id+'/export.json'">JSON</button>
      <button class="btn2 btn-sm" id="btn-requestion" onclick="show('scr-question');renderQuestions()" style="display:none">질문 이어하기</button>
      <button class="btn2 btn-sm" onclick="show('scr-home');loadList()">목록으로</button>
    </div>
  </div>
  <div class="tabs" id="res-tabs"></div>
  <div id="res-body"></div>
</section>

<div class="overlay" id="overlay"><div class="box"><span class="spinner"></span><span id="overlay-msg">처리 중...</span></div></div>
</div>
<script>
(function(){
var API='';
window.S = null;
var pollTimer=null, elapsedTimer=null, elapsed=0;
var esc=function(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');};
var TYPES={"INFO_SHARE":"정보 공유","CONDITION_CHECK":"컨디션 체크","FIRST_MEETING":"1차 미팅","PROJECT_KICKOFF":"프로젝트 킥오프","PLANNING":"기획·방향성 협의","WORKING_SESSION":"실무 협의","DESIGN_REVIEW":"디자인·산출물 리뷰","EXECUTION_PREP":"실행 준비","OPERATION":"운영 미팅","ISSUE_DECISION":"이슈 해결·의사결정","CLOSING_RETRO":"종료·회고","FOLLOW_UP":"팔로업"};
var DIV_KO={"PLANNING":"기획","BX_DESIGN":"BX디자인","GRAPHIC_DESIGN":"그래픽","SPACE_DESIGN":"공간디자인","CONSTRUCTION":"시공","OPERATION":"운영","MARKETING":"마케팅","CONTENT":"콘텐츠","FNB":"F&B","FINANCE":"재무","LEGAL":"법무","ADMINISTRATION":"총무","LOGISTICS":"물류","DEVELOPMENT":"개발","MANAGEMENT":"경영","EXTERNAL":"외부"};
var AREA_KO={"purpose_clarity":"목적 명확성","scope_clarity":"범위 명확성","output_definition":"산출물 정의","owner_assignment":"담당자 지정","schedule_confirmed":"일정 확정","budget_confirmed":"예산 확정","inputs_secured":"입력자료 확보","external_conditions":"외부 협력 조건","decisions_complete":"의사결정 완료","risk_response":"리스크 대응","approval_process":"승인 프로세스","next_milestone":"다음 마일스톤"};
var ST_KO={"DRAFT":"초안","CLASSIFYING":"분류 중","TYPE_CONFIRM":"타입 확인","ANALYZING":"분석 중","QUESTIONING":"질문 중","REVISING":"반영 중","USER_REVIEW":"검토","FINALIZING":"마무리 중","FINALIZED":"완료","ERROR":"오류"};
var ST_COLOR={"FINALIZED":"var(--green)","ERROR":"var(--red)","QUESTIONING":"var(--amber)","ANALYZING":"var(--accent)"};

function show(id){document.querySelectorAll('section').forEach(function(s){s.classList.remove('on')});document.getElementById(id).classList.add('on');window.scrollTo(0,0);}
window.show=show;
function overlay(on,msg){var o=document.getElementById('overlay');o.classList.toggle('on',!!on);if(msg)document.getElementById('overlay-msg').textContent=msg;}
function showErr(msg){document.getElementById('err-box').innerHTML=msg?'<div class="err">'+esc(msg)+' <button class="btn2 btn-sm" style="margin-left:10px" onclick="retrySession()">재시도</button></div>':'';}
window.retrySession=function(){if(!S)return;overlay(true,'재시도 중...');api('POST','/api/meeting/'+S.id+'/retry',{}).then(function(d){overlay(false);if(d.ok){S=d.session;route();}});};
function api(method,url,body){return fetch(API+url,{method:method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined}).then(function(r){return r.json();}).catch(function(e){overlay(false);showErr('네트워크 오류: '+e);return {ok:false};});}

// ── 목록 ──
function loadList(){api('GET','/api/meetings').then(function(d){
  var el=document.getElementById('sess-list');
  if(!d.ok||!d.sessions.length){el.innerHTML='<p style="color:var(--muted);font-size:13px;padding:30px 0;text-align:center">아직 분석한 회의가 없습니다. 새 회의를 시작하세요.</p>';return;}
  el.innerHTML=d.sessions.map(function(s){
    var c=ST_COLOR[s.status]||'var(--muted)';
    return '<div class="list-item" onclick="openSession(\''+s.id+'\')"><div><div class="t">'+esc(s.title)+'</div>'+
    '<div class="m">'+esc(s.project||'')+(s.primaryType?' · '+(TYPES[s.primaryType]||s.primaryType):'')+' · '+esc(s.updatedAt)+(s.readiness!=null?' · 준비도 '+s.readiness+'%':'')+'</div></div>'+
    '<div style="display:flex;gap:8px;align-items:center"><span class="st-chip" style="background:rgba(0,0,0,.25);color:'+c+';border:1px solid '+c+'">'+(ST_KO[s.status]||s.status)+'</span>'+
    '<button class="qact" onclick="event.stopPropagation();delSession(\''+s.id+'\')">삭제</button></div></div>';}).join('');
});}
window.loadList=loadList;
window.delSession=function(id){if(!confirm('이 세션을 삭제할까요?'))return;api('POST','/api/meeting/'+id+'/delete',{}).then(loadList);};
window.openSession=function(id){overlay(true,'세션 로드 중...');api('GET','/api/meeting/'+id).then(function(d){overlay(false);if(d.ok){S=d.session;route();}});};

// ── 라우팅: 세션 status → 화면 ──
function route(){
  showErr(S&&S.error);
  if(!S)return show('scr-home');
  var st=S.status;
  if(st==='TYPE_CONFIRM')return renderType();
  if(st==='ANALYZING'||st==='CLASSIFYING'){show('scr-progress');startPoll();return;}
  if(st==='QUESTIONING'){show('scr-question');renderQuestions();return;}
  if(st==='REVISING'){show('scr-progress');startPoll();return;}
  if(st==='USER_REVIEW'){autoFinalize();return;}
  if(st==='FINALIZING'){overlay(true,'실행 준비도 평가 중...');startPoll();return;}
  if(st==='FINALIZED'){renderResult();return;}
  if(st==='ERROR'){ // 마지막 도달 화면 추정
    if(!S.classification)show('scr-input');
    else if(!S.analysis){show('scr-progress');stopPoll();}
    else renderResult();
    return;}
  show('scr-home');loadList();
}

// ── 입력 ──
window.goInput=function(){show('scr-input');};
document.getElementById('in-transcript').addEventListener('input',function(){document.getElementById('char-count').textContent=this.value.length.toLocaleString();});
window.submitMeeting=function(){
  var t=document.getElementById('in-transcript').value.trim();
  if(!t){document.getElementById('in-msg').textContent='전사 텍스트를 입력하세요.';return;}
  if(t.length>100000){document.getElementById('in-msg').textContent='10만 자를 초과했습니다. 나눠서 입력하세요.';return;}
  var meta={title:val('in-title'),date:val('in-date'),participants:val('in-participants'),project:val('in-project'),author:val('in-author'),client:val('in-client')};
  var btn=document.getElementById('btn-analyze');btn.disabled=true;
  document.getElementById('in-msg').innerHTML='<span class="spinner"></span>회의 타입 분류 중 (~30초)...';
  api('POST','/api/meeting',{transcript:t,meta:meta}).then(function(d){
    btn.disabled=false;document.getElementById('in-msg').textContent='';
    if(!d.ok){document.getElementById('in-msg').textContent=d.error||'실패';return;}
    S=d.session;route();
  });
};
function val(id){return document.getElementById(id).value.trim();}

// ── 타입 확인 ──
var selType=null;
function renderType(){
  var cls=S.classification.classification;
  selType=cls.primaryType;
  var conf=Math.round((cls.confidence||0)*100);
  var low=conf<70;
  var h='<h2>회의 타입 판별 결과</h2>';
  h+='<div style="font-size:22px;font-weight:800;margin:10px 0 2px">'+(TYPES[cls.primaryType]||cls.primaryType)+'</div>';
  if(cls.secondaryTypes&&cls.secondaryTypes.length)h+='<div style="margin:4px 0">'+cls.secondaryTypes.map(function(t){return '<span class="badge b-opt" style="margin-right:4px">'+(TYPES[t]||t)+'</span>';}).join('')+'</div>';
  h+='<div class="conf-bar" style="max-width:300px"><div class="conf-fill" style="width:'+conf+'%"></div></div>';
  h+='<div style="font-size:12px;color:'+(low?'var(--amber)':'var(--muted)')+'">신뢰도 '+conf+'%'+(low?' — 낮습니다. 타입을 직접 확인해 주세요.':'')+'</div>';
  (cls.reason||[]).forEach(function(r){h+='<div style="font-size:12px;color:var(--fg2);margin-top:6px">· '+esc(r)+'</div>';});
  (cls.evidence||[]).slice(0,3).forEach(function(q){h+='<div class="quote">"'+esc(q)+'"</div>';});
  var warns=S.classification.warnings||[];
  warns.forEach(function(w){h+='<div style="font-size:12px;color:var(--amber);margin-top:6px">⚠ '+esc(w)+'</div>';});
  h+='<h3 class="sec">'+(low?'타입을 선택하세요':'다른 타입이라면 선택을 바꾸세요')+'</h3><div class="type-grid" id="tgrid">';
  Object.keys(TYPES).forEach(function(k){h+='<div class="type-cell'+(k===selType?' sel':'')+'" data-t="'+k+'" onclick="pickType(\''+k+'\')">'+TYPES[k]+'</div>';});
  h+='</div><div style="margin-top:18px;display:flex;gap:10px"><button class="btn" onclick="confirmType()">이 타입으로 분석 계속</button></div>';
  document.getElementById('type-card').innerHTML=h;
  show('scr-type');
}
window.pickType=function(t){selType=t;document.querySelectorAll('#tgrid .type-cell').forEach(function(c){c.classList.toggle('sel',c.dataset.t===t);});};
window.confirmType=function(){
  overlay(true,'구조화 분석 시작...');
  api('POST','/api/meeting/'+S.id+'/confirm-type',{primaryType:selType}).then(function(d){
    overlay(false);
    if(d.ok){S.status='ANALYZING';show('scr-progress');setStep(2);startPoll();}
  });
};

// ── 폴링 ──
function setStep(n){[1,2,3].forEach(function(i){var el=document.getElementById('stp-'+i);el.className='step'+(i<n?' done':i===n?' on':'');});}
function startPoll(){
  stopPoll();elapsed=0;
  document.getElementById('elapsed').textContent='0';
  elapsedTimer=setInterval(function(){elapsed+=1;document.getElementById('elapsed').textContent=elapsed;},1000);
  if(S.status==='ANALYZING')setStep(S.analysis?3:2);
  pollTimer=setInterval(function(){
    api('GET','/api/meeting/'+S.id).then(function(d){
      if(!d.ok)return;
      S=d.session;
      if(S.status==='ANALYZING'){setStep(S.analysis?3:2);return;}
      stopPoll();overlay(false);route();
    });
  },3000);
}
function stopPoll(){if(pollTimer){clearInterval(pollTimer);pollTimer=null;}if(elapsedTimer){clearInterval(elapsedTimer);elapsedTimer=null;}}

// ── 질문 루프 ──
var qState={};
function visibleQuestions(){
  var order={CRITICAL:0,IMPORTANT:1,OPTIONAL:2};
  var qs=(S.questions||[]).slice().sort(function(a,b){return (order[a.tier]||9)-(order[b.tier]||9);});
  return qs.slice(0,3);
}
function renderQuestions(){
  document.getElementById('q-round').textContent=S.questionRound||1;
  qState={};
  var qs=visibleQuestions();
  if(!qs.length){autoFinalize();return;}
  var tierBadge={CRITICAL:'b-crit',IMPORTANT:'b-imp',OPTIONAL:'b-opt'};
  document.getElementById('q-cards').innerHTML=qs.map(function(q){
    qState[q.id]={action:'answer',text:''};
    var h='<div class="qcard" id="qc-'+q.id+'">';
    h+='<span class="badge '+(tierBadge[q.tier]||'b-opt')+'">'+q.tier+'</span>';
    h+='<div class="qt">'+esc(q.question)+'</div>';
    if(q.why)h+='<div class="qwhy">왜 필요한가: '+esc(q.why)+'</div>';
    if(q.aiGuess)h+='<div class="aiguess"><span class="badge b-ai">AI 추정</span> '+esc(q.aiGuess)+'</div>';
    if(q.choices&&q.choices.length)h+='<div class="chips">'+q.choices.map(function(c,i){return '<span class="chip" onclick="pickChoice(\''+q.id+'\','+i+',this)">'+esc(c)+'</span>';}).join('')+'</div>';
    h+='<textarea rows="2" placeholder="답변 입력 (선택지를 누르면 자동 입력)" oninput="qState[\''+q.id+'\'].text=this.value" id="qi-'+q.id+'"></textarea>';
    h+='<div class="qactions">';
    [['answer','답변하기'],['defer','추후 확인'],['not_applicable','해당 없음'],['use_ai_guess','AI 추정값 사용'],['ask_owner','담당자에게 질문 전환']].forEach(function(a){
      h+='<button class="qact'+(a[0]==='answer'?' sel':'')+'" onclick="pickAction(\''+q.id+'\',\''+a[0]+'\',this)">'+a[1]+'</button>';});
    h+='</div></div>';
    return h;
  }).join('');
  renderQStatus();
  show('scr-question');
}
window.qState=qState;
window.pickChoice=function(qid,idx,el){
  var q=(S.questions||[]).find(function(x){return x.id===qid;});
  document.getElementById('qi-'+qid).value=q.choices[idx];
  qState[qid].text=q.choices[idx];
  el.parentNode.querySelectorAll('.chip').forEach(function(c){c.classList.remove('sel');});
  el.classList.add('sel');
};
window.pickAction=function(qid,action,el){
  qState[qid].action=action;
  el.parentNode.querySelectorAll('.qact').forEach(function(b){b.classList.remove('sel');});
  el.classList.add('sel');
};
function renderQStatus(){
  var st=S.infoStatus||[];
  var icon={CONFIRMED:'🟢',INFERRED:'🟣',PARTIAL:'🟡',MISSING:'🔴',CONFLICTED:'⚠️',NOT_REQUIRED:'⚪'};
  var crit=st.filter(function(s){return s.importance==='CRITICAL';});
  var ok=crit.filter(function(s){return s.status==='CONFIRMED'||s.status==='NOT_REQUIRED';}).length;
  var h='<div style="margin-bottom:8px;font-weight:600">CRITICAL 충족 '+ok+'/'+crit.length+'</div>';
  h+=st.map(function(s){return icon[s.status]+' '+esc(s.label)+' <span style="color:var(--muted);font-size:10px">'+s.status+'</span>';}).join('<br>');
  document.getElementById('q-status').innerHTML=h;
}
window.submitAnswers=function(){
  var answers=[];
  Object.keys(qState).forEach(function(qid){
    var a=qState[qid];
    a.text=(document.getElementById('qi-'+qid)||{value:a.text}).value;
    if(a.action==='answer'&&!a.text.trim())a.action='defer'; // 빈 답변은 추후확인 처리
    answers.push({questionId:qid,action:a.action,text:a.text});
  });
  overlay(true,'답변 반영 중 (~1분)...');
  document.getElementById('btn-answer').disabled=true;
  api('POST','/api/meeting/'+S.id+'/answer',{answers:answers}).then(function(d){
    overlay(false);document.getElementById('btn-answer').disabled=false;
    if(!d.ok){showErr(d.error||'답변 반영 실패');return;}
    S=d.session;route();
  });
};
window.skipQuestions=function(){
  overlay(true,'결과 생성 중...');
  api('POST','/api/meeting/'+S.id+'/skip-questions',{}).then(function(d){
    if(d.ok){S=d.session;autoFinalize();}else overlay(false);
  });
};

// ── finalize ──
function autoFinalize(){
  if(S.readiness&&S.status==='FINALIZED'){renderResult();return;}
  overlay(true,'실행 준비도 평가 + Executive Summary 생성 중...');
  api('POST','/api/meeting/'+S.id+'/finalize',{}).then(function(d){
    overlay(false);
    if(d.ok){S=d.session;}
    renderResult();
  });
}

// ── 결과 7탭 ──
var curTab='exec';
function renderResult(){
  showErr(S.error);
  document.getElementById('res-title').textContent=S.meta.title||'회의 결과';
  var cls=(S.classification||{}).classification||{};
  document.getElementById('res-sub').textContent=(TYPES[cls.primaryType]||'')+' · '+(S.meta.date||'')+(S.meta.project?' · '+S.meta.project:'')+' · 세션 '+S.id;
  document.getElementById('btn-requestion').style.display=(S.questions&&S.questions.length)?'':'none';
  var tabs=[['exec','Executive Summary'],['minutes','회의록'],['actions','실행 업무'],['outputs','산출물'],['support','Support Map'],['review','AI Review'],['raw','원문']];
  document.getElementById('res-tabs').innerHTML=tabs.map(function(t){return '<button class="tab'+(t[0]===curTab?' on':'')+'" onclick="setTab(\''+t[0]+'\')">'+t[1]+'</button>';}).join('');
  renderTab();
  show('scr-result');
}
window.setTab=function(t){curTab=t;renderResult();};
function badge(status,userConfirmed){
  if(userConfirmed==='USER_CONFIRMED')return ' <span class="badge b-ok">확인됨</span>';
  if(userConfirmed==='AI_INFERRED_ACCEPTED')return ' <span class="badge b-ai">AI추정 수용</span>';
  if(status==='INFERRED')return ' <span class="badge b-ai">AI추정</span>';
  if(status==='MISSING')return ' <span class="badge b-warn">확인 필요</span>';
  return '';
}
function kv(k,v){if(!v||(Array.isArray(v)&&!v.length))return '';
  var body=Array.isArray(v)?'<ul>'+v.map(function(x){return '<li>'+esc(x)+'</li>';}).join('')+'</ul>':esc(v);
  return '<div class="kv"><div class="k">'+k+'</div><div class="v">'+body+'</div></div>';}
function renderTab(){
  var a=S.analysis||{},mins=a.minutes||{},el=document.getElementById('res-body'),h='';
  if(curTab==='exec'){
    var es=S.executiveSummary||{},rd=S.readiness||{};
    var pct=rd.overall!=null?rd.overall:0;
    var circ=2*Math.PI*56, off=circ*(1-pct/100);
    h='<div class="panel"><div class="exec-top">';
    h+='<div class="score-circle"><svg width="130" height="130"><circle cx="65" cy="65" r="56" fill="none" stroke="#2a2a2a" stroke-width="10"/><circle cx="65" cy="65" r="56" fill="none" stroke="'+(pct>=70?'var(--green)':pct>=40?'var(--amber)':'var(--red)')+'" stroke-width="10" stroke-linecap="round" stroke-dasharray="'+circ+'" stroke-dashoffset="'+off+'"/></svg><div class="val"><div class="num">'+(rd.overall!=null?pct+'%':'—')+'</div><div class="lb">실행 준비도</div></div></div>';
    h+='<div style="flex:1;min-width:260px">'+kv('한 줄 요약',es.oneLiner)+kv('회의 목적',es.purpose)+kv('다음 마일스톤',es.nextMilestone)+'</div></div>';
    var rareas=rd.areas||[];
    if(rareas.length){h+='<div class="rgrid">'+rareas.map(function(ar){return '<div class="rcell '+ar.status+'"><div class="rn">'+(AREA_KO[ar.area]||ar.area)+' · '+ar.status+'</div><div class="rr">'+esc(ar.rationale||'')+'</div></div>';}).join('')+'</div>';}
    h+='</div><div class="panel">'+kv('핵심 결과',es.keyResults)+kv('결정사항',es.keyDecisions)+kv('중요 변경',es.keyChanges)+kv('대표 의사결정 필요',es.ceoDecisionsNeeded)+kv('가장 큰 리스크',es.biggestRisk)+kv('실행을 막는 미확인 정보',es.criticalGaps)+'</div>';
  }
  else if(curTab==='minutes'){
    var B=mins.B_summary||{},C=mins.C_status||{};
    h='<div class="panel"><h2>대표 요약</h2>'+kv('핵심 결과',B.core_results)+kv('핵심 결정',B.key_decisions)+kv('중요 변경',B.key_changes)+kv('가장 큰 리스크',B.biggest_risk)+kv('다음 단계',B.next_steps)+'</div>';
    h+='<div class="panel"><h2>프로젝트 현황</h2>'+kv('회의 전',C.before)+kv('현재',C.after)+kv('달라진 점',C.delta)+'</div>';
    var tps=mins.D_topics||[];
    if(tps.length){h+='<div class="panel"><h2>주제별 논의</h2>'+tps.map(function(t){
      var s='<h3 class="sec">'+esc(t.topic)+'</h3>'+kv('배경',t.background)+kv('주요 논의',t.discussion)+kv('결론',t.conclusion)+kv('결정 근거',t.rationale)+kv('실행 영향',t.execution_impact)+kv('미해결',t.open_points);
      (t.evidence||[]).slice(0,2).forEach(function(e){s+='<div class="quote">"'+esc(e.quote)+'"'+(e.speaker?' — '+esc(e.speaker):'')+'</div>';});
      return s;}).join('')+'</div>';}
    var decs=a.decisions||[];
    if(decs.length){h+='<div class="panel"><h2>결정사항</h2><table><tr><th>결정</th><th>근거</th><th>제외 대안</th><th>결정자</th><th>상태</th></tr>'+decs.map(function(d){
      return '<tr><td><b>'+esc(d.title)+'</b><br>'+esc(d.description||'')+'</td><td>'+esc(d.rationale||'')+'</td><td>'+esc((d.rejectedAlternatives||[]).join(', '))+'</td><td>'+esc((d.decidedBy||[]).join(', '))+'</td><td>'+(d.status==='CONFIRMED'?'<span class="badge b-ok">확정</span>':'<span class="badge b-warn">결정 여부 확인 필요</span>')+'</td></tr>';}).join('')+'</table></div>';}
    var chg=mins.F_changes||[];
    if(chg.length){h+='<div class="panel"><h2>변경사항</h2><table><tr><th>항목</th><th>기존</th><th>변경</th><th>영향</th></tr>'+chg.map(function(c){return '<tr><td><b>'+esc(c.what)+'</b></td><td>'+esc(c.before)+'</td><td>'+esc(c.after)+'</td><td>'+esc((c.impact||[]).join('; '))+'</td></tr>';}).join('')+'</table></div>';}
    var oi=mins.G_open_issues||[];
    if(oi.length){h+='<div class="panel"><h2>미해결 이슈</h2><table><tr><th>사안</th><th>필요한 결정</th><th>결정자</th><th>기한</th></tr>'+oi.map(function(i){return '<tr><td>'+esc(i.issue)+'</td><td>'+esc(i.needed_decision)+'</td><td>'+esc(i.decider||'⚠️')+'</td><td>'+esc(i.deadline||'-')+'</td></tr>';}).join('')+'</table></div>';}
    var rk=mins.H_risks||[];
    if(rk.length){var ic={HIGH:'🔴',MEDIUM:'🟡',LOW:'🟢'};h+='<div class="panel"><h2>리스크</h2>'+rk.map(function(r){return '<div style="font-size:13px;color:var(--fg2);margin-bottom:8px">'+(ic[r.severity]||'🟡')+' '+esc(r.risk)+(r.response?' <span style="color:var(--muted)">→ '+esc(r.response)+'</span>':'')+'</div>';}).join('')+'</div>';}
  }
  else if(curTab==='actions'){
    var acts=a.actions||[];
    if(!acts.length)h='<div class="panel"><p style="color:var(--muted);font-size:13px">이 회의에서 도출된 실행 업무가 없습니다. (정보 공유 성격의 회의일 수 있습니다)</p></div>';
    else{var pOrder={CRITICAL:0,HIGH:1,MEDIUM:2,LOW:3};
    h='<div class="panel"><table><tr><th>우선순위</th><th>업무</th><th>부서</th><th>담당자</th><th>기한</th><th>완료 기준</th><th>선행/지원</th></tr>'+
    acts.slice().sort(function(x,y){return (pOrder[x.priority]||9)-(pOrder[y.priority]||9);}).map(function(t){
      var uc=t.userConfirmed||{};
      var owner=t.ownerName?esc(t.ownerName)+badge('',uc.ownerName||'USER_CONFIRMED'):(t.suggestedOwner?'제안: '+esc(t.suggestedOwner)+' <span class="badge b-ai">AI추천</span>':'<span class="badge b-warn">미지정</span>');
      var dl=t.deadline?esc(t.deadline)+badge(t.deadlineStatus,uc.deadline):'<span class="badge b-warn">확인 필요</span>';
      var pb={CRITICAL:'b-crit',HIGH:'b-imp',MEDIUM:'b-opt',LOW:'b-opt'};
      var dep=(t.dependencies||[]).join(', ');var sup=(a.supportRequests||[]).filter(function(s){return s.actionId===t.id;}).map(function(s){return s.stakeholderName;}).join(', ');
      return '<tr><td><span class="badge '+(pb[t.priority]||'b-opt')+'">'+t.priority+'</span></td><td><b>'+esc(t.title)+'</b><br>'+esc(t.description||'')+(t.ownerReason?'<br><span style="color:var(--muted);font-size:11px">추천 이유: '+esc(t.ownerReason)+'</span>':'')+'</td><td>'+(DIV_KO[t.division]||t.division)+'</td><td>'+owner+'</td><td>'+dl+'</td><td>'+esc(t.completionCriteria||'')+'</td><td>'+esc(dep)+(sup?'<br>지원: '+esc(sup):'')+'</td></tr>';}).join('')+'</table></div>';}
  }
  else if(curTab==='outputs'){
    var outs=a.outputs||[];
    if(!outs.length)h='<div class="panel"><p style="color:var(--muted);font-size:13px">정의된 산출물이 없습니다.</p></div>';
    else h='<div class="panel"><table><tr><th>산출물</th><th>목적</th><th>포맷</th><th>부서/담당</th><th>제출일</th><th>승인 기준</th><th>필요 입력</th></tr>'+outs.map(function(o){
      var uc=o.userConfirmed||{};
      var owner=(DIV_KO[o.ownerDivision]||o.ownerDivision||'')+(o.suggestedOwner?' · 제안: '+esc(o.suggestedOwner)+' <span class="badge b-ai">AI추천</span>':'');
      var due=o.dueDate?esc(o.dueDate)+badge(o.dueDateStatus,uc.dueDate):'<span class="badge b-warn">확인 필요</span>';
      return '<tr><td><b>'+esc(o.name)+'</b><br><span style="color:var(--muted)">'+esc(o.outputType||'')+'</span></td><td>'+esc(o.purpose||'')+'</td><td>'+esc(o.format||'')+'</td><td>'+owner+'</td><td>'+due+'</td><td>'+esc((o.acceptanceCriteria||[]).join('; '))+'</td><td>'+esc((o.requiredInputs||[]).join('; '))+'</td></tr>';}).join('')+'</table></div>';
  }
  else if(curTab==='support'){
    var sups=a.supportRequests||[];
    if(!sups.length)h='<div class="panel"><p style="color:var(--muted);font-size:13px">이해관계자 지원 요청이 없습니다.</p></div>';
    else h='<div class="panel"><table><tr><th>차단 수준</th><th>대상</th><th>요청</th><th>이유</th><th>기한</th><th>미수신 시</th></tr>'+sups.map(function(s){
      var bl={BLOCKING:'b-crit',IMPORTANT:'b-imp',REFERENCE:'b-opt'};
      return '<tr><td><span class="badge '+(bl[s.blockingLevel]||'b-opt')+'">'+s.blockingLevel+'</span></td><td><b>'+esc(s.stakeholderName)+'</b><br><span style="color:var(--muted)">'+esc(s.stakeholderType||'')+'</span></td><td><b>'+esc(s.requestTitle)+'</b><br>'+esc(s.requestedInformation||'')+'</td><td>'+esc(s.requestReason||'')+'</td><td>'+esc(s.requestDueDate||'-')+'</td><td>'+esc(s.blockedWithout||'-')+'</td></tr>';}).join('')+'</table></div>';
  }
  else if(curTab==='review'){
    var st=S.infoStatus||[];
    var sb={CONFIRMED:'b-ok',INFERRED:'b-ai',PARTIAL:'b-imp',MISSING:'b-crit',CONFLICTED:'b-crit',NOT_REQUIRED:'b-opt'};
    h='<div class="panel"><h2>정보 충족 상태</h2><table><tr><th>항목</th><th>중요도</th><th>상태</th><th>현재 값</th><th>비고</th></tr>'+st.map(function(s){
      return '<tr><td><b>'+esc(s.label)+'</b></td><td>'+esc(s.importance)+'</td><td><span class="badge '+(sb[s.status]||'b-opt')+'">'+s.status+'</span></td><td>'+esc(s.currentValue||'')+'</td><td>'+esc(s.note||'')+'</td></tr>';}).join('')+'</table></div>';
    if(S.questions&&S.questions.length)h+='<div class="panel"><h2>미해결 질문</h2>'+S.questions.map(function(q){return '<div class="qwhy">· ['+q.tier+'] '+esc(q.question)+'</div>';}).join('')+'</div>';
    if(S.answerLog&&S.answerLog.length)h+='<div class="panel"><h2>답변 이력</h2><table><tr><th>라운드</th><th>질문</th><th>처리</th><th>답변</th></tr>'+S.answerLog.map(function(l){
      var am={answer:'답변',defer:'추후확인',not_applicable:'해당없음',use_ai_guess:'AI추정수용',ask_owner:'담당자질문'};
      return '<tr><td>'+l.round+'</td><td>'+esc(l.question)+'</td><td>'+(am[l.action]||l.action)+'</td><td>'+esc(l.text||'')+'</td></tr>';}).join('')+'</table></div>';
    h+='<div class="panel"><h2>LLM 호출 로그</h2><table><tr><th>호출</th><th>소요</th><th>성공</th><th>시각</th></tr>'+(S.llmLog||[]).map(function(l){
      return '<tr><td>'+l.call+'</td><td>'+l.durationSec+'s</td><td>'+(l.ok?'✅':'❌')+'</td><td>'+l.ts+'</td></tr>';}).join('')+'</table></div>';
  }
  else if(curTab==='raw'){
    h='<div class="panel"><h2>원본 전사</h2><pre class="raw">'+esc(S.transcript)+'</pre></div>';
  }
  el.innerHTML=h;
}

loadList();
})();
</script></body></html>"""


# ── HTTP 핸들러 ───────────────────────────────────────────────────────────

class H(BaseHTTPRequestHandler):
    server_version = "R4Meeting/0.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", headers=None):
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception:
            return {}

    def _sess_or_404(self, sid):
        try:
            sess = load_session(sid)
        except ValueError:
            sess = None
        if not sess:
            self._send(404, {"ok": False, "error": "세션 없음"})
        return sess

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path
        if path in ("/", "/index.html"):
            return self._send(200, PAGE_HTML.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/api/health":
            return self._send(200, {"ok": True, "service": "r4-meeting-simulator"})
        if path == "/api/meetings":
            return self._send(200, {"ok": True, "sessions": list_sessions()})
        m = re.fullmatch(r"/api/meeting/([^/]+)", path)
        if m:
            sess = self._sess_or_404(m.group(1))
            if sess:
                self._send(200, {"ok": True, "session": sess})
            return
        m = re.fullmatch(r"/api/meeting/([^/]+)/export\.md", path)
        if m:
            sess = self._sess_or_404(m.group(1))
            if sess:
                md = build_markdown(sess)
                fname = f"meeting-{sess['id']}.md"
                self._send(200, md.encode("utf-8"), "text/markdown; charset=utf-8",
                           {"Content-Disposition": f'attachment; filename="{fname}"'})
            return
        m = re.fullmatch(r"/api/meeting/([^/]+)/export\.json", path)
        if m:
            sess = self._sess_or_404(m.group(1))
            if sess:
                fname = f"meeting-{sess['id']}.json"
                self._send(200, json.dumps(sess, ensure_ascii=False, indent=1).encode("utf-8"),
                           "application/json; charset=utf-8",
                           {"Content-Disposition": f'attachment; filename="{fname}"'})
            return
        m = re.fullmatch(r"/api/meeting/([^/]+)/report\.html", path)
        if m:
            sess = self._sess_or_404(m.group(1))
            if sess:
                self._send(200, build_report_html(sess).encode("utf-8"), "text/html; charset=utf-8")
            return
        m = re.fullmatch(r"/api/meeting/([^/]+)/export\.doc", path)
        if m:
            sess = self._sess_or_404(m.group(1))
            if sess:
                fname = f"meeting-{sess['id']}.doc"
                self._send(200, build_report_html(sess, for_doc=True).encode("utf-8"),
                           "application/msword; charset=utf-8",
                           {"Content-Disposition": f'attachment; filename="{fname}"'})
            return
        self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        try:
            self._do_POST()
        except Exception as e:
            # 처리 중 예외 시 세션 상태가 *ING에 고착되지 않게 복구
            sys.stderr.write(f"[handler] POST {self.path} 예외: {e}\n")
            m = re.fullmatch(r"/api/meeting/([^/]+)/[a-z-]+", urlparse(self.path).path)
            if m:
                try:
                    sess = load_session(m.group(1))
                    if sess and sess["status"] in ("CLASSIFYING", "ANALYZING", "REVISING", "FINALIZING"):
                        sess["status"] = "QUESTIONING" if sess.get("questions") else \
                                         ("USER_REVIEW" if sess.get("analysis") else "ERROR")
                        sess["error"] = f"처리 중 오류가 발생했습니다: {e}"
                        save_session(sess)
                except Exception:
                    pass
            try:
                self._send(500, {"ok": False, "error": f"서버 오류: {e}"})
            except Exception:
                pass

    def _do_POST(self):
        u = urlparse(self.path)
        path = u.path
        b = self._body()
        if path == "/api/meeting":
            transcript = (b.get("transcript") or "").strip()
            if not transcript:
                return self._send(400, {"ok": False, "error": "전사 텍스트가 비어 있습니다."})
            if len(transcript) > MAX_TRANSCRIPT_CHARS:
                return self._send(400, {"ok": False, "error":
                                        f"전사가 {MAX_TRANSCRIPT_CHARS:,}자를 초과합니다. 나눠서 입력해 주세요."})
            sess = new_session(transcript, b.get("meta") or {})
            sess = run_classify(sess)  # 동기 (~1분 내)
            return self._send(200, {"ok": True, "session": sess})
        m = re.fullmatch(r"/api/meeting/([^/]+)/([a-z-]+)", path)
        if not m:
            return self._send(404, {"ok": False, "error": "not found"})
        sid, action = m.group(1), m.group(2)
        sess = self._sess_or_404(sid)
        if not sess:
            return
        if action == "confirm-type":
            cls = sess["classification"]["classification"]
            if b.get("primaryType") in MEETING_TYPES:
                cls["primaryType"] = b["primaryType"]
            if isinstance(b.get("secondaryTypes"), list):
                cls["secondaryTypes"] = [t for t in b["secondaryTypes"] if t in MEETING_TYPES]
            sess["typeConfirmed"] = True
            sess["status"] = "ANALYZING"
            save_session(sess)
            threading.Thread(target=run_extract_detect, args=(sess,), daemon=True).start()
            return self._send(200, {"ok": True, "session": {"id": sess["id"], "status": "ANALYZING"}})
        if action == "answer":
            answers = b.get("answers") or []
            if not answers:
                return self._send(400, {"ok": False, "error": "답변이 없습니다."})
            sess = run_revise(sess, answers)
            return self._send(200, {"ok": True, "session": sess})
        if action == "skip-questions":
            sess["questions"] = []
            sess["status"] = "USER_REVIEW"
            save_session(sess)
            return self._send(200, {"ok": True, "session": sess})
        if action == "finalize":
            sess = run_finalize(sess)
            return self._send(200, {"ok": True, "session": sess})
        if action == "retry":
            sess["error"] = None
            sess = run_retry(sess)
            return self._send(200, {"ok": True, "session": sess})
        if action == "delete":
            TRASH_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(_sess_path(sid)), str(TRASH_DIR / f"{sid}.json"))
            return self._send(200, {"ok": True})
        self._send(404, {"ok": False, "error": "unknown action"})


# ── 서버 기동 시 미완 세션 복구 ───────────────────────────────────────────

def _mark_interrupted():
    for meta in list_sessions():
        if meta["status"] in ("CLASSIFYING", "ANALYZING", "REVISING", "FINALIZING"):
            sess = load_session(meta["id"])
            if sess:
                sess["status"] = "ERROR"
                sess["error"] = "서버 재시작으로 분석이 중단되었습니다. 재시도해 주세요."
                save_session(sess)


# ── CLI 테스트 모드 ───────────────────────────────────────────────────────

def _cli_test(transcript_path):
    text = Path(transcript_path).read_text(encoding="utf-8")
    print(f"▶ 전사 {len(text):,}자 로드 — 파이프라인 테스트 시작")
    sess = new_session(text, {})
    sess = run_classify(sess)
    if sess["status"] == "ERROR":
        print("✖ classify 실패:", sess["error"])
        return
    cls = sess["classification"]["classification"]
    print(f"① classify OK ({sess['llmLog'][-1]['durationSec']}s) — "
          f"{cls['primaryType']} {round(cls['confidence']*100)}% / 2차: {cls['secondaryTypes']}")
    run_extract_detect(sess)
    sess = load_session(sess["id"])
    if sess["status"] == "ERROR":
        print("✖ extract/detect 실패:", sess["error"])
        return
    a = sess["analysis"]
    print(f"② extract OK ({sess['llmLog'][-2]['durationSec']}s) — "
          f"결정 {len(a['decisions'])} / 액션 {len(a['actions'])} / 산출물 {len(a['outputs'])} / 지원요청 {len(a['supportRequests'])}")
    crit = [s for s in sess['infoStatus'] if s['importance'] == 'CRITICAL']
    print(f"③ detect OK ({sess['llmLog'][-1]['durationSec']}s) — "
          f"infoStatus {len(sess['infoStatus'])}개 (CRITICAL {len(crit)}) / 질문 {len(sess['questions'])}개")
    for q in sess["questions"]:
        print(f"   [Q·{q['tier']}] {q['question']}")
    sess = run_finalize(sess)
    if sess.get("readiness"):
        print(f"⑤ finalize OK — 준비도 {sess['readiness'].get('overall')}%")
    md = build_markdown(sess)
    out = SESS_DIR / f"{sess['id']}-test.md"
    out.write_text(md, encoding="utf-8")
    print(f"✔ 세션 {sess['id']} 저장 / 마크다운: {out}")


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--test":
        return _cli_test(sys.argv[2])
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else PORT
    SESS_DIR.mkdir(parents=True, exist_ok=True)
    _mark_interrupted()
    try:
        srv = ThreadingHTTPServer((HOST, port), H)
    except OSError as e:
        sys.stderr.write(f"✖ {HOST}:{port} 바인드 실패({e}) — R4_PORT 환경변수로 포트를 바꿔 재시도하세요.\n")
        sys.exit(1)
    print(f"R4 Meeting Simulator → http://{HOST}:{port}  (모델: {ANTHROPIC_MODEL})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
