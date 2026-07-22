#!/usr/bin/env python3
"""ARISA 2.0 — 일일 업무보고 봇 (Cognitive Operations System, MVP1)

ARISA는 업무보고 자동화 봇이 아니다. 직원의 사고를 번역·구조화해 스스로 자신의
사고를 보게 만드는 사고의 거울(Cognitive Reflection)이다. 보고는 인터페이스다.
처리 순서: Report → Interpretation → Reflection (코칭은 후속 MVP).

v2: GPT 기반 의도 판단 — 질문/수정/답변을 구분하여 자연스러운 대화 지원.
2.0-MVP1:
  - Engine B (Report Completion): Output/Outcome/Decision이 약하면 부드럽게 최대 3개만 질문
  - Engine C (Report Structuring): 7섹션(Task/Output/Outcome/Decision/Support/Next/Reflection)
  - 직원 본인에게도 정리본 + Reflection 회신(거울 학습 루프)

사용법:
  python 00-system/02-scripts/daily-report-bot.py

직원 흐름:
  /start → /report → 업무 나열 → GPT 정리 → (부족하면 질문) → 7섹션 정리본을
           직원 본인 + 관리자에게 전송 + 구글시트 저장
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
    PicklePersistence,
)

# ARISA 직원 메모리 레이어(mem0) — 보조. import 실패해도 봇은 정상 동작.
try:
    import arisa_memory_emp as _emem
except Exception:  # noqa: BLE001
    _emem = None

# ARISA Meeting Engine (1.0 통합) — 회의록 6종 리포트 생성. import 실패해도 /report는 정상.
try:
    from meeting_engine import engine as meeting_engine
    from meeting_engine import client as meeting_client
    from meeting_engine.source_detector import detect_source_type, SOURCE_LABELS
    _MEETING_AVAILABLE = True
except Exception:  # noqa: BLE001
    _MEETING_AVAILABLE = False

# .env 로드
load_dotenv(Path.home() / "do-better-workspace" / ".env")
load_dotenv(Path.home() / "arisa-project-memory" / ".env")

# ARISA 공유 코어 (Phase 1) — 봇 간 복붙되던 기능 배관 단일 출처
sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared.logging import TokenRedactingFilter  # noqa: E402
from shared import gws as _gws  # noqa: E402
from shared import report_queue as _rq  # noqa: E402
from shared.employee import load_employees as _load_emp  # noqa: E402
from shared.decision import save_decision_log as _save_decision_log  # noqa: E402
from shared import report_score as _report_score  # noqa: E402  (채점 SSOT — 2026-07-20)
from shared.naming import clean_project_name as _nm_clean  # noqa: E402  (P2 네이밍 규칙)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# 모든 핸들러에 토큰 마스킹 필터 부착 (httpx 등 전파된 로그까지 커버)
for _h in logging.getLogger().handlers:
    _h.addFilter(TokenRedactingFilter())

logger = logging.getLogger(__name__)

# === 설정 (.env에서 로드 — do-better-workspace/.env) ===
BOT_TOKEN = os.getenv("DAILY_REPORT_BOT_TOKEN")
MANAGER_BOT_TOKEN = os.getenv("DAILY_REPORT_MANAGER_BOT_TOKEN")
MANAGER_CHAT_ID = os.getenv("DAILY_REPORT_MANAGER_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHEET_ID = os.getenv("DAILY_REPORT_SHEET_ID")
# 결과물(첨부파일) 저장용 구글드라이브 폴더 ("일일업무보고" 폴더)
DRIVE_FOLDER_ID = os.getenv("DAILY_REPORT_DRIVE_FOLDER_ID")
# 직원명부 (인사기록카드_마스터 스냅샷) — 이름→소속/직책/직무 자동 보정 + 텔레그램ID 학습
EMP_PATH = Path(__file__).resolve().parent / "arisa-employees.json"

# AX 뉴스레터 구독자 자동등록 대상 파일
NEWSLETTER_RECIPIENTS = (Path.home() / "do-better-workspace" / "10-projects"
                         / "28-ai-education-ax" / "newsletter" / "recipients.json")


def _locked_update_json(path: Path, mutate):
    """path의 JSON을 flock 하에 읽고 mutate(data)->data 적용 후 원자적으로 재작성.
    mutate가 None 반환 시 '변경 없음'으로 보고 쓰지 않는다. 반환=실제 변경 여부.
    동시 /start·/report의 read-modify-write 경쟁으로 인한 갱신 유실·파일 손상을 방지."""
    import fcntl
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(path.suffix + ".lock")
    with open(lock, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            new = mutate(data)
            if new is None:
                return False
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, path)
            return True
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def register_subscriber(chat_id) -> bool:
    """봇에 /start 한 사용자를 AX 뉴스레터 구독자(recipients.json)로 자동 등록. 신규면 True."""
    def _mut(data):
        data = data or {"recipients": []}
        ids = {str(r.get("chat_id")) for r in data.get("recipients", []) if r.get("chat_id")}
        if str(chat_id) in ids:
            return None  # 이미 구독 중 — 변경 없음
        data.setdefault("recipients", []).append({"chat_id": int(chat_id)})
        return data
    try:
        return _locked_update_json(NEWSLETTER_RECIPIENTS, _mut)
    except Exception as e:
        logger.error(f"newsletter subscriber register error: {e}")
        return False
# 텔레그램에서 받은 파일을 잠시 내려받을 임시 폴더
ATTACH_TMP_DIR = Path("/tmp/daily-report-attachments")

# 대화 상태 영속화 — 진행 중 보고가 봇 재시작/크래시에도 살아남게(휘발 방지)
PERSIST_FILE = Path(__file__).resolve().parent / ".bot-state" / "daily-report-persistence.pkl"
PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)

openai_client = OpenAI(api_key=OPENAI_API_KEY)


# === 직원명부 (규칙5: 입력 식별 정합) ===

def load_employees() -> dict:
    """인사마스터 스냅샷 명부 로드 (shared 코어 위임)."""
    return _load_emp(EMP_PATH)


def save_employees(data: dict) -> None:
    try:
        tmp = EMP_PATH.with_suffix(EMP_PATH.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, EMP_PATH)  # 원자적 교체 — 부분쓰기(파일손상) 방지
    except Exception as e:
        logger.error(f"employees save error: {e}")


def _norm_name(s: str) -> str:
    return (s or "").replace(" ", "").strip()


def match_employee(name: str) -> dict | None:
    """이름으로 명부 조회 (소속/직책/직무 반환)."""
    emp = load_employees().get("by_name", {})
    n = _norm_name(name)
    for k, v in emp.items():
        if _norm_name(k) == n:
            return {"name": k, **v}
    return None


def employee_by_tid(uid) -> dict | None:
    """텔레그램 user_id로 직원 식별 (학습된 경우)."""
    d = load_employees()
    nm = d.get("by_telegram_id", {}).get(str(uid))
    if nm:
        e = d.get("by_name", {}).get(nm)
        if e:
            return {"name": nm, **e}
    return None


def register_telegram_id(uid, name: str) -> None:
    """user_id ↔ 이름 매핑 학습 저장 (flock으로 동시쓰기 경쟁·손상 방지)."""
    def _mut(data):
        data = data or {}
        data.setdefault("by_telegram_id", {})[str(uid)] = name
        return data
    try:
        _locked_update_json(EMP_PATH, _mut)
    except Exception as e:
        logger.error(f"register_telegram_id error: {e}")


# 대화 상태
(
    WAITING_INFO,
    WAITING_TASKS,
    WAITING_CONFIRM,
    WAITING_DRILLDOWN,
    WAITING_ISSUES,
    WAITING_TOMORROW,
    WAITING_COMPLETION,  # 2.0-MVP1: 보고 보완 질문 답변 대기
    WAITING_QUESTION,    # 3.0: 직원 '오늘의 질문' 1개 수집 (질문보고 전환)
) = range(8)

# /meeting 대화 상태 (기존 /report와 충돌 방지)
(
    MTG_SELECT_PROJECT,
    MTG_INPUT,
    MTG_CONFIRM,
) = range(100, 103)

# /assign 대화 상태
(
    ASSIGN_TEAM,
    ASSIGN_CONTENT,
    ASSIGN_CONFIRM,
) = range(200, 203)

# 회의 프로젝트 경로
_MEETING_PROJECTS_DIR = Path(__file__).resolve().parents[2] / "20-operations" / "23-arisa" / "meeting-projects"
_MEETING_TEMPLATE_DIR = _MEETING_PROJECTS_DIR / "_template"
# 대표 전용 (최원석) — .env DAILY_REPORT_ADMIN_IDS(쉼표구분)로 오버라이드 가능
_MEETING_ALLOWED = {int(x) for x in os.environ.get("DAILY_REPORT_ADMIN_IDS", "8123576679").split(",") if x.strip()}

# === GPT 프롬프트 ===

INTENT_PROMPT = """너는 업무보고 봇의 의도 분류기다.
사용자의 메시지가 아래 3가지 중 무엇인지 판단해.

1. "answer" — 봇의 질문에 대한 답변 (업무 내용, 확인, 정보 제공 등)
2. "question" — 사용자가 봇에게 질문하는 것 (뭔가를 물어봄, 되물음, 확인 요청)
3. "correction" — 이전 내용을 수정/추가하려는 것

반드시 아래 JSON만 출력해:
{"intent": "answer|question|correction", "detail": "판단 근거 한 줄"}"""

ANSWER_QUESTION_PROMPT = """너는 친절한 업무보고 도우미 봇이다.
사용자가 업무 보고 도중에 질문을 했다. 자연스럽고 캐주얼하게 답변해줘.
- 봇이 정리한 업무 목록에 대한 질문이면, 맥락을 참고해서 설명해줘
- 모르는 건 솔직하게 "그건 제가 판단하기 어려워요" 라고 해
- 답변 후 마지막에 자연스럽게 현재 단계의 질문으로 돌아가줘

현재 대화 맥락:
{context}

현재 단계: {step}
이 단계에서 봇이 물어보고 있는 것: {step_question}"""

CATEGORIZE_PROMPT = """너는 직원의 업무 보고를 정리하는 봇이다.
직원이 나열한 업무를 아래 7개 카테고리로 자동 분류하고 구조화해.

카테고리: 기획 | 실행 | 커뮤니케이션 | 관리 | 리서치 | 교육 | 기타

응답은 반드시 아래 JSON 형식으로만 출력해. 다른 텍스트 없이 JSON만:

{
  "tasks": [
    {"task": "업무 내용", "category": "카테고리", "status": "완료/진행중/시작"}
  ],
  "suggested_core": [0, 1]
}

suggested_core는 가장 복잡하거나 시간이 많이 걸렸을 것 같은 업무의 인덱스(0부터) 1~2개를 추천해."""

DRILLDOWN_PROMPT = """직원이 핵심 업무에 대해 상세 설명했다.
**직원이 실제로 말한 내용에서만** 추출하라. 말하지 않은 것은 절대 지어내거나 형식적으로 채우지 마라.

JSON으로만 응답:
{
  "goal": "직원이 말한 이 업무의 목표·왜 하는지·완료 기준. 직접 말했을 때만 적는다 (말하지 않았으면 \\"\\")",
  "process": "직원이 설명한 실제 진행 단계. 구체적 단계를 말했을 때만 적는다. 단계를 말하지 않았으면 반드시 빈 문자열 \\"\\" — 'A → B → C' 같은 형식적·내용없는 채움(특히 '시작 → 중간 → 결과')은 절대 금지",
  "tools": "직원이 언급한 도구/프로그램 (언급 없으면 \\"\\")",
  "output": "구체적 산출물/결과물. 업무명을 그대로 반복하지 말고 실제로 만들어진 것을 적는다 (없거나 업무명과 같으면 \\"\\")",
  "issues": "이슈/블로커 (없으면 \\"\\")"
}"""

# === 2.0-MVP1: Engine B (Report Completion) ===
# 직원의 사고를 비추는 거울. 평가하지 않고, 보고에서 빠진 핵심만 짚어 '단 하나'만 질문(질문 폭탄 금지).
COMPLETION_CHECK_PROMPT = """너는 ARISA, 직원의 사고를 비추는 거울이다. 평가하거나 코칭하지 않는다.
좋은 보고는 7요소를 갖춘다:
  Task(한 일) / Output(생산한 결과물) / Outcome(그래서 무엇이 달라졌나·의미) /
  Decision Needed(대표·팀장이 결정해줄 것) / Support Needed(필요한 지원) /
  Blocker(막힌 것) / Next(다음 액션)

아래 보고에서 다음 '부실 신호'가 있는 부분만 골라, 직원이 스스로 채우도록 부드럽게 질문해라:
- **공란**: Output(산출물)·Outcome(의미)·Decision 같은 핵심이 비어 있음
- **더미**: 프로세스가 '시작→중간→결과'처럼 내용 없는 형식적 문구
- **동어반복**: Output(산출물)이 업무명과 사실상 같음 (예: 업무 "판매페이지 세팅" / 산출물 "판매페이지")
- **추상어만**: '정리함/검토함/진행함'처럼 무엇을·어떻게가 없는 서술
- **모호어**: '진행 중/확인 중/거의 완료/~것 같다/이야기했다'처럼 날짜·수치·주체·결과가 없음
- **사실·해석 혼재**: 타인의 의사를 단정하는데("클라이언트가 원한다") 직접 발언인지 해석인지 알 수 없음

판정 기준 한 줄: **"제3자가 이 보고만 보고 다음 액션이나 의사결정을 할 수 있는가?"**
가능하면 통과(질문 0개), 불가능하게 만드는 부실 슬롯만 질문.

규칙:
- 질문은 **최대 1개**. 부실 슬롯이 여럿이어도 "제3자가 다음 의사결정을 가장 못 하게
  만드는 단 하나"만 고른다. 충분하면 빈 배열 [] (피로 최소화).
- 우선순위: 중요·고난도 업무의 핵심(Output·Outcome·Decision) 누락 > 사소한 업무.
- 평가·코칭·지적 금지. 사고를 비추는 질문만.
- **질문에는 반드시 해당 프로젝트·업무명을 명시** — '그 업무/그 조사' 같은 지시어만 쓰지 마라.
  예) "'매장 A 리뉴얼' 조사로 무엇을 발견했나요?" / "'판매페이지 세팅'의 구체적 산출물은 무엇인가요?" /
      "'여수 프로젝트' 건은 대표가 무엇을 결정해주면 되나요?"
- 짧고 담담하게. 한 질문에 한 가지만.

반드시 JSON만 출력(원소 1개 이하): {"questions": ["..."]}"""

# === 2.0-MVP1: Engine C (Report Structuring) ===
# 원본 보고 + 보완답변 → Outcome/Decision/Support/Reflection 채우기. 없는 건 지어내지 않는다.
STRUCTURE_PROMPT = """너는 ARISA, 직원의 보고를 구조화하는 거울이다. 너의 역할은 '구조화'이지 '창작'이 아니다.
아래 '원본 보고(JSON)'와 '보완 답변'에 **실제로 있는 내용만** 정리하라.
**보강·추측·미화 절대 금지** — 원본/답변에 없으면 그럴듯하게 지어내지 말고 반드시 빈 문자열로 둬라.
(직원이 '핫플이 됐다'고만 했으면 '디자인 업계에서 입소문' 같은 구체는 만들지 마라.)

- outcomes: 원본 보고의 core_tasks 순서대로, 각 업무의 Outcome(그 산출물이 만든 변화·의미)
  한 줄씩. 같은 길이의 배열. **직원이 의미를 말하지 않았으면 "" (지어내기 금지).**
- projects: core_tasks 순서대로, 각 업무가 속한 프로젝트를 아래 '프로젝트 목록'에서 골라
  **정확히 그 이름 그대로** 적어라. 같은 길이의 배열.
  목록에 없는 이름을 만들지 말 것. 어느 프로젝트인지 불확실하면 "" (추측 금지).
- decision_needed: 대표·팀장이 결정해야 할 것 (없으면 "")
- decision: decision_needed가 있을 때만 그것을 구조화(Engine D). decision_needed가 ""이면 모두 "".
    project        = 어느 프로젝트/업무에 대한 결정인가 (core_tasks의 category/task에서. 불명확하면 "")
    decision_type  = 결정의 성격 한 단어 (positioning/budget/priority/direction/hiring/approval/scope 등)
    urgency        = high / medium / low (셋 중 하나)
    related_output = 이 결정과 연결된 산출물 (core_tasks의 output에서. 없으면 "")
    options        = 직원이 말한 선택지들 (예: "A안: ~ / B안: ~". 말하지 않았으면 "")
    recommendation = 직원의 추천안 + 이유 (말하지 않았으면 "")
    deadline       = 결정이 필요한 기한 (말하지 않았으면 "")
    delay_impact   = 결정이 늦어질 경우의 영향 (말하지 않았으면 "")
  **추측 금지** — 원본에 근거가 없으면 각 필드를 "" 로 둬라.
- support_needed: 직원이 필요로 하는 지원 (블로커와 구분. 없으면 "")
- reflection: 보고 품질에 대한 '관찰'(평가가 아니라 거울).
    good   = 오늘 보고에서 잘 설명된 점
    missing= 다음에 더하면 좋을 점(부드럽게)
    next   = 다음 보고 때 보완하면 좋을 포인트 한 가지
  따뜻하고 담담한 어조. 지적하지 말 것.
  **어느 프로젝트·업무 이야기인지 업무명을 명시**해라 ('그 업무'처럼 지시어만 쓰지 말 것).
  예) missing="'에너넷 미팅'은 확정된 시간·장소가 빠져 있어요"

반드시 JSON만 출력:
{"outcomes": ["", ""], "projects": ["", ""], "decision_needed": "",
 "decision": {"project": "", "decision_type": "", "urgency": "", "related_output": "",
              "options": "", "recommendation": "", "deadline": "", "delay_impact": ""},
 "support_needed": "",
 "reflection": {"good": "", "missing": "", "next": ""}}"""

# === Reporting OS v2: Report Score 루브릭 — 공유 코어 SSOT (shared/report_score.py) ===
# 채점은 목적이 아니라 수단 — 부족 항목을 질문으로 마저 채우게 유도하는 것이 핵심.
# 2026-07-20: 유형별(A/B/C) 이원 루브릭 + grace/strict 2모드. 시뮬레이터와 동일 기준.
_SCORE_OUTPUT_RULES = """

## 질문(gaps) 규칙
- gaps: **최대 3개**, 유형별 우선순위로 골라라(점수 손실 크기보다 이 순서가 우선) —
  Type A: ①사실·의견 혼재(evidence) ②결과·목표 누락(context/objective) ③다음 액션 불명확(priority)
  Type B: ①리스크 누락·조건부 재질문(risk — 영향·원인·대응 중 빠진 것) ②지원(support) ③사실·의견 혼재(evidence)
  Type C: ①결정 요청 구체화(decision — 옵션·추천안·결정 기한·늦어질 경우의 영향 중 빠진 것)
         ②리스크(risk) ③사실·의견 혼재(evidence)
  각 항목마다 직원이 스스로 채울 수 있는 질문 1개. **보고에 이미 답이 있는 항목은
  절대 gaps에 넣지 마라** (예: '목표 대비 80%'가 이미 있으면 objective를 다시 묻지 않는다).
  평가·코칭·지적 금지, 사고를 비추는 질문만. 짧고 담담하게.
  **질문에는 반드시 근거가 된 프로젝트·업무명을 명시해라** — 직원이 여러 업무를 보고하므로
  '그 업무/그 결정/그 지연'처럼 지시어만 쓰면 무엇을 묻는지 알 수 없다.
  예) "'여수 프로젝트' 계약 결정 — 관리자가 A/B 중 고르면 되도록 옵션을 붙여줄 수 있나요?" /
      "'세스크멘슬 전략레포트'는 목표까지 몇 % 왔는지 숫자로 말해줄 수 있나요?"
  Type A는 목표·결과·다음 액션이 이미 충분하면 gaps를 비워라(경량 통과).
- well_done: 가장 잘 채워진 항목을 보고의 실제 내용을 들어 한 줄로
  (따뜻하고 담담하게). 잘 채워진 항목이 하나도 없으면 빈 문자열 "".

반드시 JSON만 출력. scores에는 분류된 유형의 항목만 넣어라 (아래는 형식 예시일 뿐, 값을 복사하지 마라):
{"report_type": "A",
 "scores": {"context": 0, "objective": 0, "evidence": 0, "priority": 0, "risk": 0},
 "total": 0,
 "gaps": [{"item": "evidence", "reason": "...", "question": "..."}],
 "well_done": ""}"""


def _score_prompt() -> str:
    """공유 코어(grace/strict 모드 자동) + 봇 출력 형식 — 채점 시점마다 조립."""
    return _report_score.build_prompt() + _SCORE_OUTPUT_RULES


# 단계별 질문 설명 (의도 판단용)
STEP_QUESTIONS = {
    WAITING_CONFIRM: "업무 목록이 맞는지 확인하거나 수정",
    WAITING_DRILLDOWN: "핵심 업무에 대해 상세하게 설명 (프로세스, 도구, 산출물)",
    WAITING_ISSUES: "오늘 막힌 부분이나 시간 많이 든 부분",
    WAITING_TOMORROW: "내일 이어갈 일이나 우선순위",
    WAITING_COMPLETION: "보고에서 보완할 부분(발견·의미·필요한 결정)에 대한 답변",
    WAITING_QUESTION: "오늘 가장 중요하게 떠오른 질문 하나",
}


# === 유틸리티 ===

def call_gpt(system: str, user_msg: str) -> dict | None:
    """GPT API 호출 → JSON 파싱."""
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        text = resp.choices[0].message.content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"GPT error: {e}")
        return None


def call_gpt_text(system: str, user_msg: str) -> str:
    """GPT API 호출 → 텍스트 응답."""
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.5,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"GPT text error: {e}")
        return "죄송해요, 잠시 오류가 있었어요. 다시 말씀해주세요!"


def detect_intent(text: str) -> str:
    """사용자 메시지의 의도를 판단: answer / question / correction"""
    result = call_gpt(INTENT_PROMPT, text)
    if result and "intent" in result:
        return result["intent"]
    return "answer"  # 판단 실패 시 기본값


def build_context_summary(user_data: dict) -> str:
    """현재까지의 대화 맥락 요약."""
    parts = []
    if user_data.get("name"):
        parts.append(f"보고자: {user_data['name']} ({user_data.get('team', '')})")
    if user_data.get("all_tasks"):
        task_list = "\n".join([f"- {t['task']} [{t['category']}]" for t in user_data["all_tasks"]])
        parts.append(f"정리된 업무 목록:\n{task_list}")
    if user_data.get("core_details"):
        for d in user_data["core_details"]:
            parts.append(f"핵심 업무 상세: {d}")
    return "\n".join(parts) if parts else "아직 수집된 정보 없음"


async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE, step: int) -> int:
    """질문을 GPT로 답변하고 현재 단계 유지."""
    text = update.message.text.strip()
    ctx_summary = build_context_summary(context.user_data)
    step_q = STEP_QUESTIONS.get(step, "업무 보고 진행 중")

    prompt = ANSWER_QUESTION_PROMPT.format(
        context=ctx_summary,
        step=step,
        step_question=step_q,
    )
    answer = await asyncio.to_thread(call_gpt_text, prompt, text)
    await update.message.reply_text(answer)
    return step  # 현재 단계 유지!


def _tg_send(token: str, chat_id, message: str) -> bool:
    """임의의 봇 토큰·chat_id로 텔레그램 메시지 전송 (raw API)."""
    import urllib.request
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": message}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        return True
    except Exception as e:
        logger.error(f"tg send error (chat={chat_id}): {e}")
        return False


# ── 문의·건의 접수 (2026-07-22, 아리사 OS 전직원 오픈) ──────────────────
# 대화(보고/회의/분장) 밖 자유 텍스트 = 문의/건의로 접수 → 기록 + 대표 전달 + 접수 확인 회신.
_INQUIRY_LOG = Path(__file__).resolve().parents[2] / "20-operations" / "23-arisa" / "inquiries" / "inbox.jsonl"


async def receive_inquiry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not text:
        return
    uid = update.effective_user.id
    emp = employee_by_tid(uid)
    name = emp["name"] if emp else (update.effective_user.full_name or str(uid))
    try:
        _INQUIRY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with _INQUIRY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                "name": name, "tg_id": uid, "text": text},
                               ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"inquiry log error: {e}")
    sent = await asyncio.to_thread(send_to_manager, f"💬 문의/건의 접수 — {name}\n\n{text}")
    if not sent:
        logger.error(f"inquiry forward failed: {name}")
    await update.message.reply_text(
        "💬 접수했습니다 — 확인 후 회신드리겠습니다.\n"
        "· 일일보고를 하시려면 /report\n"
        "· 아리사 OS 접속: https://arisa-os.com (가이드: https://arisa-os.com/guide-os)")


def send_to_manager(message: str) -> bool:
    """관리자(대표) 텔레그램으로 전송 (관리자봇)."""
    return _tg_send(MANAGER_BOT_TOKEN, MANAGER_CHAT_ID, message)


def team_leader_chat_ids(team: str, reporter_name: str) -> list:
    """해당 팀 리더의 telegram_id 목록 (보고자 본인·미연결 리더 제외).

    명부 team_leads(팀→리더이름) → by_telegram_id 역조회로 리더 chat_id 확보.
    리더가 봇에 미연결이면 빈 목록(자동 skip). 리더가 곧 보고자면 중복 방지로 제외.
    """
    d = load_employees()
    leader_name = d.get("team_leads", {}).get((team or "").strip())
    if not leader_name or leader_name == reporter_name:
        return []
    return [tid for tid, nm in d.get("by_telegram_id", {}).items() if nm == leader_name]


def share_to_team_leader(report: dict, manager_msg: str) -> int:
    """팀원 일일보고 정리본을 해당 팀 리더에게 직원봇으로 공유. 전송 성공 건수 반환.

    성공·스킵·실패를 모두 로그에 남긴다 — '공유가 안 왔다' 제보 시 추적 가능하게 (2026-07-06).
    """
    team = report.get("team", "")
    reporter = report.get("name", "")
    leader_ids = team_leader_chat_ids(team, reporter)
    if not leader_ids:
        logger.info(f"leader-share skip: team={team!r} reporter={reporter} (리더 없음/미연결/본인이 리더)")
        return 0
    sent = 0
    for lid in leader_ids:
        share = f"👥 [팀원 일일보고 공유 · {team}]\n\n{manager_msg}"
        # 리더는 직원봇(BOT_TOKEN)에 연결돼 있으므로 직원봇으로 발신
        if _tg_send(BOT_TOKEN, lid, share):
            sent += 1
            logger.info(f"leader-share ok: {reporter}({team}) → 리더 chat={lid}")
        else:
            logger.error(f"leader-share FAIL: {reporter}({team}) → 리더 chat={lid} — 리더가 직원봇 /start 안 했거나 차단 가능성")
    return sent


# 백필 dedup용: 탭별 중복 판정 컬럼(날짜·이름·내용·제출식별자). 마지막 인덱스 = submitted_at 컬럼.
_DEDUP_COLS = {"핵심업무!A1": [0, 1, 5, 12], "서브업무!A1": [0, 1, 4, 6], "메타!A1": [0, 1, 12]}


def _build_sheet_rows(d: dict) -> list[tuple[str, list]]:
    """보고 데이터 → append할 (탭, 행) 목록. 저장과 큐잉이 같은 조립을 공유.

    각 행 마지막 컬럼 = submitted_at(제출 식별자). 같은날 재제출을 백필 dedup이 서로 다른 건으로
    구분해, 2차 보고가 1차의 '중복'으로 오판돼 유실되던 문제를 방지한다(같은 제출의 재시도는 sid가
    같아 여전히 dedup됨). 기존 행은 이 컬럼이 비어 있어도 무방(후행 추가 컬럼).
    """
    rows: list[tuple[str, list]] = []
    _sid = d.get("submitted_at") or datetime.now().isoformat(timespec="seconds")
    d["submitted_at"] = _sid  # 재조립 시에도 동일 sid 유지(라이브 저장/큐 백필 일관)
    for ct in d.get("core_tasks", []):
        # outcome은 기존 11컬럼 뒤(12번째)에 추가 — 기존 데이터 정합 유지. sid=13번째(M열).
        # G1b: project(N)·pid(O) 후행 컬럼 — 보고↔프로젝트 ID Relation 축적 (기존 행은 빈값 무방)
        rows.append(("핵심업무!A1", [d["date"], d["name"], d["team"], d["role"],
                     ct.get("category", ""), ct.get("task", ""), ct.get("status", ""),
                     ct.get("process", ""), ct.get("tools", ""), ct.get("output", ""),
                     ct.get("issues", ""), ct.get("outcome", ""), _sid,
                     ct.get("project", ""), ct.get("pid", "")]))
    for st in d.get("sub_tasks", []):
        rows.append(("서브업무!A1", [d["date"], d["name"], d["team"],
                     st.get("category", ""), st.get("task", ""), st.get("status", ""), _sid]))
    attach_cell = "\n".join(
        f"{a['name']}: {a['link']}" for a in d.get("attachments", [])
    )
    refl = d.get("reflection") or {}
    reflection_cell = "\n".join(
        f"{k}: {refl[k]}" for k in ("good", "missing", "next") if refl.get(k)
    )
    rows.append(("메타!A1", [d["date"], d["name"], d["team"], d.get("tomorrow", ""), d.get("improvement", ""),
                 d.get("blockers", ""), attach_cell,
                 d.get("decision_needed", ""), d.get("support_needed", ""), reflection_cell,
                 d.get("raw", ""),  # fidelity: 직원 원문 보존(K열)
                 d.get("key_question", ""), _sid,  # L=오늘의 질문, M=submitted_at
                 d.get("report_score", ""),  # Reporting OS v1.1: Report Score 총점(N열)
                 d.get("score_detail", "")]))  # Reporting OS v1.1: 항목별 점수+질문수 JSON(O열)
    return rows


def save_to_sheet(report_data: dict) -> dict:
    """구글시트에 저장 (GWS CLI).

    반환 {"total": N, "failed": [(tab, row)...], "err": ""|"auth"|"transient"}.
    실패 행은 로컬 큐(failed-reports/queue.jsonl)에 보관 → 백필 배치가 자동 재시도.
    (2026-07-03 gws 인증 장애로 5명 보고가 소리 없이 유실된 사고의 재발 방지.)
    """
    d = report_data
    try:
        rows = _build_sheet_rows(d)
    except Exception as e:
        logger.error(f"Sheet save error (row build): {e}")
        # 무성공-ack 방지: 행조립 실패도 유실이므로 원문을 복구용으로 로그에 덤프하고
        # err='build'로 구분 반환 → 호출부가 '저장 완료'로 오안내하지 않게 함.
        logger.error(f"LOST-REPORT(build-fail) {json.dumps(d, ensure_ascii=False, default=str)}")
        return {"total": 0, "failed": [], "err": "build"}

    failed, err = [], ""
    for tab, row in rows:
        if err == "auth":
            # 인증 장애면 나머지도 실패 확정 — 시도 낭비 없이 전부 큐로
            failed.append((tab, row))
            continue
        ok, kind = _gws.append_to_sheet_ex(SHEET_ID, tab, row, value_input_option="RAW", timeout=15)
        if not ok:
            failed.append((tab, row))
            err = kind or err or "transient"

    if failed:
        report_key = f"{d.get('date','')}|{d.get('name','')}"
        _rq.enqueue([
            _rq.make_entry("daily-report", SHEET_ID, tab, row, report_key,
                           _DEDUP_COLS.get(tab, [0, 1]), vio="RAW", last_error=err)
            for tab, row in failed
        ])
    return {"total": len(rows), "failed": failed, "err": err}


def upload_to_drive(local_path: Path, display_name: str) -> str | None:
    """텔레그램에서 받은 파일을 구글드라이브에 업로드 → 공유 링크 반환."""
    import time as _time
    _auth_pat = ("invalid_rapt", "invalid_grant", "reauth", "unauthorized_client")
    try:
        result = None
        for attempt in range(3):  # 시트 저장과 동일하게 재시도 + 인증장애 즉시중단
            result = subprocess.run(
                ["gws", "drive", "+upload", str(local_path),
                 "--parent", DRIVE_FOLDER_ID, "--name", display_name],
                capture_output=True, timeout=60, text=True,
            )
            if result.returncode == 0:
                break
            if any(p in (result.stderr or "").lower() for p in _auth_pat):
                logger.error(f"Drive upload auth fail (재시도 무의미): {result.stderr[:200]}")
                return None
            logger.error(f"Drive upload fail try {attempt+1}/3: {result.stderr[:200]}")
            if attempt < 2:
                _time.sleep(2 * (attempt + 1))
        if result is None or result.returncode != 0:
            return None
        # 응답 JSON에서 파일 ID 추출 (헬퍼가 키링 안내 등 비-JSON 라인을 섞어 출력할 수 있음)
        out = result.stdout.strip()
        start = out.find("{")
        if start == -1:
            logger.error(f"Drive upload: no JSON in output: {out[:200]}")
            return None
        info = json.loads(out[start:])
        file_id = info.get("id")
        if not file_id:
            logger.error(f"Drive upload: no id in response: {info}")
            return None
        return f"https://drive.google.com/file/d/{file_id}/view"
    except Exception as e:
        logger.error(f"Drive upload error: {e}")
        return None


# === 2.0-MVP1: 보고 조립 · Completion · Structuring · 전송 ===

def assemble_report(user_data: dict) -> dict:
    """수집된 user_data를 보고 dict로 조립한다 (Outcome/Decision/Support/Reflection 자리 포함)."""
    all_tasks = user_data.get("all_tasks", [])
    core_details = user_data.get("core_details", [])
    core_indices = set(user_data.get("core_indices", []))

    report = {
        "date": user_data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "name": user_data.get("name", ""),
        "team": user_data.get("team", ""),
        "role": user_data.get("role", ""),
        "core_tasks": [],
        "sub_tasks": [],
        "blockers": user_data.get("blockers", ""),
        "tomorrow": user_data.get("tomorrow", ""),
        "improvement": "",
        # 2.0-MVP1 신규 필드
        "decision_needed": "",
        "support_needed": "",
        "reflection": {},
        # 3.0 질문보고: 직원이 스스로 던진 오늘의 질문 (측정 ④ 입력)
        "key_question": user_data.get("key_question", ""),
        # fidelity: 직원의 원문 입력 보존 (정리본 왜곡 시 대조용)
        "raw": "\n".join(user_data.get("raw_log", [])),
        "attachments": user_data.get("attachments", []),
    }

    for i, t in enumerate(all_tasks):
        if i in core_indices:
            detail = next((d for d in core_details if d.get("task_idx") == i), {})
            report["core_tasks"].append({
                "task": t["task"],
                "category": t["category"],
                "status": t["status"],
                "goal": detail.get("goal", ""),  # Wave 2 (Step2): 업무 목표(왜)
                "process": detail.get("process", ""),
                "tools": detail.get("tools", ""),
                "output": detail.get("output", ""),
                "outcome": "",  # Engine C에서 채움
                "issues": detail.get("issues", ""),
            })
        else:
            report["sub_tasks"].append({
                "task": t["task"],
                "category": t["category"],
                "status": t["status"],
            })

    return report


def _report_digest(report: dict) -> str:
    """GPT에 넘길 보고 요약 텍스트."""
    parts = [f"보고자: {report['name']} ({report['team']})"]
    parts.append("핵심 업무:")
    for ct in report.get("core_tasks", []):
        parts.append(
            f"- {ct['task']} [{ct['category']}/{ct['status']}]"
            f" | 목표: {ct.get('goal','')}"
            f" | 프로세스: {ct.get('process','')}"
            f" | 산출물(Output): {ct.get('output','')}"
            f" | 이슈: {ct.get('issues','')}"
        )
    if report.get("sub_tasks"):
        parts.append("서브 업무: " + ", ".join(t["task"] for t in report["sub_tasks"]))
    if report.get("blockers"):
        parts.append(f"블로커: {report['blockers']}")
    if report.get("tomorrow"):
        parts.append(f"내일/Next: {report['tomorrow']}")
    return "\n".join(parts)


def _norm(s: str) -> str:
    """공백 제거 정규화 (동어반복·더미 비교용)."""
    return re.sub(r"\s+", "", s or "")


_DUMMY_PROCESS = {"시작→중간→결과", "시작->중간->결과", "시작중간결과", "시작→진행→완료"}

# Wave 1 (2.0 원칙4): 그대로 통과시키지 않는 모호 표현 — 진행상태형만 규칙으로 잡고,
# 문맥 의존적인 '~것 같다'(사실/해석 혼재)는 LLM(SCORE_PROMPT)이 판단한다.
_VAGUE_RE = re.compile(
    r"(진행\s*중|확인\s*중|검토\s*중|거의\s*(다\s*)?(완료|끝)|늦어질\s*(듯|것\s*같))"
)
# Wave 1 (2.0 Step11): 다음 액션에 기한이 있는지 — 날짜/시간/요일/마감 단서
_DEADLINE_RE = re.compile(
    r"(\d{1,2}\s*[월일시]|\d{1,2}\s*[:/.]\s*\d{1,2}|까지|오전|오후|내일|모레|"
    r"이번\s*주|다음\s*주|주말|[월화수목금토일]요일|마감|오늘\s*중|퇴근\s*전)"
)
# 기한 없이도 통과 불가한 추상 액션 (정규화 비교)
_ABSTRACT_NEXT = {"계속진행", "계속", "추가확인", "이어서진행", "마무리", "진행", "확인"}

# Reporting OS v1.1: Daily 질문 상한 (ARISA 2.0 정의서와 일치 — 질문 폭탄 금지)
MAX_COMPLETION_QUESTIONS = 3

# 루브릭 배점 — 유형별 가중치는 shared/report_score.TYPE_WEIGHTS가 SSOT (2026-07-20)
_SCORE_LABELS = {"context": "맥락", "objective": "목표 명확성", "evidence": "근거(사실/의견 구분)",
                 "priority": "우선순위", "risk": "리스크", "decision": "결정 요청", "support": "지원 요청"}


def _rule_based_gaps(report: dict) -> list[str]:
    """규칙 기반 부실 슬롯 탐지 (LLM이 놓치는 확실한 더미/동어반복/모호표현 안전망)."""
    gaps = []
    for ct in report.get("core_tasks", []):
        task = ct.get("task", "")
        proc, out = ct.get("process", ""), ct.get("output", "")
        np, nt, no = _norm(proc), _norm(task), _norm(out)
        # 더미 프로세스 or 공란
        if not np or np in _DUMMY_PROCESS:
            gaps.append(f"'{task}' — 구체적으로 어떤 순서로 진행하셨어요?")
        # 산출물 공란 or 업무명 동어반복
        if not no or (nt and (no in nt or nt in no)):
            gaps.append(f"'{task}'의 구체적인 산출물(결과물)은 무엇인가요?")
        # Wave 1 (원칙4): '진행 중/확인 중' 같은 모호 표현은 그대로 통과시키지 않는다
        elif _VAGUE_RE.search(out) or _VAGUE_RE.search(ct.get("issues", "")):
            gaps.append(
                f"'{task}'가 '진행 중'이라면 — 오늘 기준 어디까지 됐고, 언제까지 완료 예정인가요?")

    # Wave 1 (원칙4): 블로커의 모호 표현 — 주체·회신 시점 구체화
    blockers = report.get("blockers", "")
    if blockers and _VAGUE_RE.search(blockers):
        gaps.append("막힌 부분이 '확인 중'이라면 — 누구에게 무엇을 확인 중이고, 언제 답을 받나요?")

    # Wave 1 (Step11): 다음 액션은 행동 단위 + 기한 — '계속 진행'류는 통과 금지
    tomorrow = report.get("tomorrow", "")
    if tomorrow:
        if _norm(tomorrow) in _ABSTRACT_NEXT or not _DEADLINE_RE.search(tomorrow):
            gaps.append("내일 할 일을 '무엇을 언제까지'가 보이게 한 줄로 적어줄 수 있나요?")

    # Wave 3 (품질진단 2wk 대응): Outcome 한 줄 강제 — 산출물은 있는데 의미가 없는 경우
    has_output_no_outcome = any(
        ct.get("output") and not ct.get("outcome")
        for ct in report.get("core_tasks", [])
    )
    if has_output_no_outcome:
        # 가장 중요한 업무(첫 번째 core_task) 기준으로 질문
        first_with_output = next(
            (ct for ct in report.get("core_tasks", []) if ct.get("output") and not ct.get("outcome")),
            None,
        )
        if first_with_output:
            task_name = first_with_output.get("task", "업무")
            gaps.append(f"'{task_name}'의 산출물로 그래서 무엇이 달라졌나요? (의미·변화 한 줄)")

    # Wave 3: 의사결정 유도 — 전원 0% 공란 개선
    # strict 전환(GRACE_END 이후) 강화 규칙(2026-07-20 사용자 지시): 보고 본문에
    # 결정 단서어("결정이 필요"·컨펌·승인 등)가 보이면 존재 질문 대신 구체화 질문.
    if not report.get("decision_needed"):
        if (_report_score.current_mode() == "strict"
                and _report_score.has_decision_cue(
                    json.dumps(report, ensure_ascii=False))):
            gaps.append("보고에 결정이 필요한 사안이 보여요 — 무엇을 결정해야 하는지 "
                        "옵션과 기한을 함께 알려줄 수 있나요?")
        else:
            gaps.append("오늘 업무 중 대표나 팀장이 정해줘야 할 것이 있나요? (없으면 '없음')")

    return gaps


def _score_digest(report: dict) -> str:
    """루브릭 채점용 digest — 기본 digest에 Outcome/Decision/Support/오늘의 질문 포함."""
    parts = [_report_digest(report)]
    outs = [ct.get("outcome", "") for ct in report.get("core_tasks", []) if ct.get("outcome")]
    if outs:
        parts.append("의미(Outcome): " + " / ".join(outs))
    if report.get("decision_needed"):
        parts.append(f"필요한 의사결정: {report['decision_needed']}")
    if report.get("support_needed"):
        parts.append(f"필요한 지원: {report['support_needed']}")
    if report.get("key_question"):
        parts.append(f"오늘의 질문: {report['key_question']}")
    return "\n".join(parts)


def rubric_evaluate(report: dict) -> dict | None:
    """Reporting OS v2: 유형별(A/B/C) 루브릭 채점 (LLM 1회). 실패 시 None — 보고 흐름을 막지 않는다.

    유형 검증·가중치 클램프·total 재계산·mode 스탬프는 공유 코어 validate_scores가 담당."""
    result = call_gpt(_score_prompt(), _score_digest(report))
    if not result or not isinstance(result.get("scores"), dict):
        return None
    return _report_score.validate_scores(result)


def _rule_based_score(report: dict) -> dict:
    """LLM 실패 시 폴백 — 필드 존재 기반 부분 채점. 유형(A/B/C)은 규칙으로 추정."""
    _none_words = {_norm(w) for w in ("없음", "없어", "없습니다", "없다")}
    blockers = _norm(report.get("blockers", ""))
    issues = any(ct.get("issues") for ct in report.get("core_tasks", []))
    has_real_blocker = bool(blockers) and blockers not in _none_words
    decision = _norm(report.get("decision_needed", ""))
    if decision and decision not in _none_words:
        rtype = "C"
    elif issues or has_real_blocker:
        rtype = "B"
    else:
        rtype = "A"
    weights = _report_score.TYPE_WEIGHTS[rtype]
    scores = {k: 0 for k in weights}
    if report.get("core_tasks"):
        scores["context"] = weights["context"] // 2  # 업무는 있으나 '왜'는 판단 불가 → 부분
    if report.get("tomorrow"):
        scores["priority"] = weights["priority"]
    if issues or blockers:  # 이슈 기재 또는 "없음" 명시(판단한 결과) 모두 득점
        scores["risk"] = weights["risk"]
    if "decision" in weights and report.get("decision_needed"):
        scores["decision"] = weights["decision"]
    if "support" in weights and report.get("support_needed"):
        scores["support"] = weights["support"]
    return {"scores": scores, "total": sum(scores.values()), "gaps": [],
            "well_done": "", "report_type": rtype, "fallback": True,
            "mode": _report_score.current_mode(),
            "weights_version": _report_score.WEIGHTS_VERSION}


def completion_evaluate(report: dict) -> tuple[dict | None, list[str]]:
    """Engine B 확장(Reporting OS v1.1): 루브릭 채점 + 부족 항목 질문 큐(최대 3개).

    규칙 기반 안전망(_rule_based_gaps)은 유지 — LLM 실패에도 최소한의 질문은 나간다.
    """
    rule_qs = _rule_based_gaps(report)

    score = rubric_evaluate(report)
    llm_qs = []
    if score:
        llm_qs = [g.get("question", "").strip() for g in score.get("gaps", [])
                  if isinstance(g, dict) and g.get("question", "").strip()]
    else:
        # 루브릭 실패 시 기존 Engine B 프롬프트로 폴백 (질문 최대 1개)
        result = call_gpt(COMPLETION_CHECK_PROMPT, _report_digest(report))
        if result and "questions" in result:
            llm_qs = [q for q in result["questions"] if isinstance(q, str) and q.strip()][:1]

    # 병합 + 중복 제거(정규화 기준), 규칙 질문 우선
    merged, seen = [], set()
    for q in rule_qs + llm_qs:
        key = _norm(q)
        if key and key not in seen:
            seen.add(key)
            merged.append(q)

    # Wave 2 (§5): 유형별 질문 상한 — Type A(일반)는 1개(경량), B(이슈)/C(결정)는 3개
    cap = 1 if (score or {}).get("report_type") == "A" else MAX_COMPLETION_QUESTIONS
    return score, merged[:cap]


# === G1b: 보고 ↔ 프로젝트 ID Relation (노션 갭 분석 2026-07-18) ===
# 원칙: 화면보다 데이터 먼저 — 구조화 시점에 프로젝트 귀속을 ID로 확정해 시트에 축적.
_PROJECTS_DATA_DIR = Path(__file__).resolve().parents[2] / "00-system" / "01-templates" / "_data" / "projects"


def _load_project_registry() -> list[dict]:
    """프로젝트 JSON SSOT → [{id, name, aliases}]. 실패 시 [] (보고 본흐름 무영향)."""
    out = []
    try:
        for f in _PROJECTS_DATA_DIR.glob("*.json"):
            try:
                p = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if p.get("id") and p.get("name"):
                out.append({"id": p["id"], "name": p["name"],
                            "aliases": [a for a in (p.get("aliases") or []) if a]})
    except Exception:
        return []
    return out


def _norm_proj_name(s: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]", "", (s or "").lower())


def _project_pid(name: str, registry: list[dict]) -> str:
    """프로젝트명(LLM이 목록에서 고른 값) → ID. 정규화 정확 일치(이름+별칭)만 — 추측 매칭 금지."""
    key = _norm_proj_name(name)
    if not key:
        return ""
    for p in registry:
        if _norm_proj_name(p["name"]) == key or any(_norm_proj_name(a) == key for a in p["aliases"]):
            return p["id"]
    return ""


def structure_report(report: dict, completion_answers: str = "") -> None:
    """Engine C: Outcome/Decision/Support/Reflection을 채워 report를 in-place 보강."""
    registry = _load_project_registry()
    plist = "\n".join(
        f"- {p['name']}" + (f" (별칭: {', '.join(p['aliases'])})" if p["aliases"] else "")
        for p in registry
    )
    user_msg = (
        f"원본 보고(JSON):\n{json.dumps(report, ensure_ascii=False)}\n\n"
        f"보완 답변:\n{completion_answers or '(없음)'}\n\n"
        f"프로젝트 목록(projects는 반드시 여기서만 선택):\n{plist or '(없음)'}"
    )
    structured = call_gpt(STRUCTURE_PROMPT, user_msg)
    if not structured:
        return

    outcomes = structured.get("outcomes", [])
    for i, oc in enumerate(outcomes):
        if i < len(report["core_tasks"]) and isinstance(oc, str):
            report["core_tasks"][i]["outcome"] = oc.strip()

    # G1b: 업무별 프로젝트 귀속 — 이름은 목록에서, ID는 정확 매칭으로 확정 (실패 시 "")
    for i, pn in enumerate(structured.get("projects") or []):
        if i < len(report["core_tasks"]) and isinstance(pn, str):
            pn = pn.strip()
            report["core_tasks"][i]["project"] = pn
            report["core_tasks"][i]["pid"] = _project_pid(pn, registry)

    report["decision_needed"] = (structured.get("decision_needed") or "").strip()
    dec = structured.get("decision")
    if isinstance(dec, dict):
        report["decision"] = dec  # Engine D: 구조화 메타(project/type/urgency/related_output)
    report["support_needed"] = (structured.get("support_needed") or "").strip()
    refl = structured.get("reflection")
    if isinstance(refl, dict):
        report["reflection"] = refl


_TYPE_BADGE = {"A": "🟢 일반 진행", "B": "🟠 이슈·리스크", "C": "🔴 의사결정 요청"}


def format_report_for_manager(d: dict) -> str:
    """대표·관리자용 7섹션 보고서 (의사결정 중심)."""
    lines = [f"📋 일일 업무보고 — {d['name']} ({d['team']})", f"📅 {d['date']}"]
    # Wave 2 (§5): 보고 유형 — 읽기 전에 성격을 안다 (C=결정 필요, B=이슈)
    if d.get("report_type") in _TYPE_BADGE:
        lines.append(f"🏷 유형: {_TYPE_BADGE[d['report_type']]}")
    # Reporting OS: 읽기 전에 품질을 안다 (폴백 채점은 '간이' 표기 — 5/7 항목만 측정)
    if d.get("report_score") not in ("", None):
        suffix = " (간이)" if (d.get("_score_meta") or {}).get("fallback") else ""
        lines.append(f"📊 Report Score: {d['report_score']}/100{suffix}")
    lines.append("")

    lines.append("■ 핵심 업무 (Task → Output → Outcome)")
    for i, ct in enumerate(d.get("core_tasks", []), 1):
        ptag = f" 〔{ct['project']}〕" if ct.get("project") else ""  # G1b: 프로젝트 귀속 표기
        lines.append(f"{i}. [{ct['category']}] {ct['task']} — {ct['status']}{ptag}")
        if ct.get("goal"):
            lines.append(f"   목표: {ct['goal']}")
        if ct.get("process"):
            lines.append(f"   → {ct['process']}")
        if ct.get("output"):
            lines.append(f"   산출물(Output): {ct['output']}")
        if ct.get("outcome"):
            lines.append(f"   의미(Outcome): {ct['outcome']}")
        if ct.get("issues"):
            lines.append(f"   이슈: {ct['issues']}")

    if d.get("sub_tasks"):
        lines.append("")
        lines.append("■ 서브 업무")
        for st in d["sub_tasks"]:
            lines.append(f"- [{st['category']}] {st['task']} ({st['status']})")

    if d.get("decision_needed"):
        lines.append(f"\n🟥 필요한 의사결정 (Decision Needed)\n   {d['decision_needed']}")
        # Wave 2 (Step9): 결정 요청 구조 — 옵션/추천/기한/지연영향 (있는 것만)
        dec = d.get("decision") or {}
        for key, label in (("options", "옵션"), ("recommendation", "추천안"),
                           ("deadline", "결정 기한"), ("delay_impact", "지연 시 영향")):
            if (dec.get(key) or "").strip():
                lines.append(f"   · {label}: {dec[key].strip()}")
    if d.get("support_needed"):
        lines.append(f"\n🟦 필요한 지원 (Support Needed)\n   {d['support_needed']}")

    if d.get("blockers"):
        lines.append(f"\n■ 블로커: {d['blockers']}")
    if d.get("tomorrow"):
        lines.append(f"■ 내일(Next): {d['tomorrow']}")

    if d.get("attachments"):
        lines.append("\n■ 첨부 산출물")
        for i, a in enumerate(d["attachments"], 1):
            lines.append(f"{i}. {a['name']}\n   {a['link']}")

    return "\n".join(lines)


def format_report_for_employee(d: dict) -> str:
    """직원 본인용 7섹션 정리본 + ARISA Reflection (거울 학습 루프).

    직원이 '내가 한 말이 이렇게 정리되는구나'를 보며 좋은 보고를 체득한다.
    """
    lines = [f"🪞 ARISA가 정리한 오늘의 보고 — {d['name']}", f"📅 {d['date']}", ""]

    # 1. Task / 2. Output / 3. Outcome
    lines.append("【 1. 오늘 한 일 · 생산물 · 의미 】")
    for i, ct in enumerate(d.get("core_tasks", []), 1):
        lines.append(f"{i}. {ct['task']} ({ct['status']})")
        if ct.get("goal"):
            lines.append(f"   · 목표: {ct['goal']}")
        if ct.get("output"):
            lines.append(f"   · 생산물: {ct['output']}")
        if ct.get("outcome"):
            lines.append(f"   · 의미: {ct['outcome']}")
    if d.get("sub_tasks"):
        lines.append("   그 외: " + ", ".join(t["task"] for t in d["sub_tasks"]))

    # 4. Decision / 5. Support
    if d.get("decision_needed"):
        lines.append(f"\n【 2. 필요한 의사결정 】\n{d['decision_needed']}")
    if d.get("support_needed"):
        lines.append(f"\n【 3. 필요한 지원 】\n{d['support_needed']}")

    # 6. Next
    if d.get("tomorrow"):
        lines.append(f"\n【 4. 다음 액션 】\n{d['tomorrow']}")
    if d.get("blockers"):
        lines.append(f"\n【 5. 막힌 부분 】\n{d['blockers']}")

    # 3.0 질문보고: 직원이 던진 오늘의 질문을 되비춘다 (자기 사고를 마주보게)
    if d.get("key_question"):
        lines.append(f"\n💭 오늘의 질문: {d['key_question']}")

    # 7. Reflection
    refl = d.get("reflection") or {}
    if refl.get("good") or refl.get("missing") or refl.get("next"):
        lines.append("\n— ARISA Reflection —")
        if refl.get("good"):
            lines.append(f"👍 잘 설명된 점: {refl['good']}")
        if refl.get("missing"):
            lines.append(f"🔎 더하면 좋을 점: {refl['missing']}")
        if refl.get("next"):
            lines.append(f"➡️ 다음 보고 보완 포인트: {refl['next']}")

    # Reporting OS v1.1: Report Score (거울 톤 — 점수는 결과, 목적은 다음 보고의 한 줄)
    sm = d.get("_score_meta")
    if sm and d.get("report_score") not in ("", None) and not sm.get("fallback"):
        lines.append(f"\n📊 오늘 보고 Report Score: {d['report_score']}/100")
        if sm.get("well_done"):
            lines.append(f"👍 {sm['well_done']}")
        gaps = [g for g in sm.get("gaps", []) if isinstance(g, dict) and g.get("item")]
        if gaps:
            lab = _SCORE_LABELS.get(gaps[0]["item"], gaps[0]["item"])
            lines.append(f"➡️ 다음 보고에서 '{lab}' 한 줄을 더하면 점수가 올라가요.")

    return "\n".join(lines)


async def _employee_memory(update: Update, report: dict) -> None:
    """ARISA 직원 거울(MVP2): 그 직원의 과거 사고를 재부상해 본인에게 되비추고(A),
    오늘 핵심 업무를 mem0에 누적한다. 원문은 구글시트에 보존됨 — mem0는 재부상 보조.
    보조 레이어라 실패해도 보고 완료 흐름은 영향 없음."""
    if not _emem or not getattr(_emem, "ENABLED", False):
        return
    try:
        uid = str(update.effective_user.id)
        name = report.get("name", "")
        date = report.get("date", "") or datetime.now().strftime("%Y-%m-%d")
        core = report.get("core_tasks", [])
        today = " / ".join(
            f"{c.get('task','')} {c.get('outcome','')}".strip() for c in core
        ).strip()
        if not today:
            return
        # 재부상은 add 전에(오늘 보고는 아직 없음 → 자기 자신 제외)
        recalled = await asyncio.to_thread(_emem.recall, today, uid, 3)
        for c in core:
            t = f"{c.get('task','')}. {c.get('outcome','')}".strip(". ")
            if t:
                await asyncio.to_thread(
                    _emem.add, t, uid,
                    {"name": name, "date": date, "category": c.get("category", "")},
                )
        if recalled:
            lines = "\n".join(
                f"· {h['memory']}" + (f"  ({h['date']})" if h.get("date") else "")
                for h in recalled
            )
            await update.message.reply_text(
                "🪞 돌아보면, 전에 이런 일도 하셨어요\n" + lines +
                "\n\n(평가가 아니라, 스스로의 흐름을 보시라고 띄워드려요)"
            )
    except Exception:
        logger.exception("employee memory failed")  # 보고 본흐름은 영향 없음


async def finalize_and_send(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    report: dict,
    completion_answers: str = "",
) -> int:
    """Engine C 실행 → 최종 채점(Reporting OS) → 직원 회신(거울) + 관리자 전송 + 시트 저장."""
    # 핫픽스(2026-07-12): 보고 날짜 = 제출일. PicklePersistence로 부활한 과거 세션(/report 없이
    # 이어짐)이 시작일 날짜로 저장되면 브리프 집계(직전 영업일 소스)에서 영구 누락된다.
    # 정책(2026-07-20, 대표 지시): 아침 9시 이전 제출은 전날 업무 보고로 귀속 —
    # 자정 넘긴 늦은 보고가 다음날로 밀려 브리프에서 하루 늦게 잡히는 것 방지.
    now = datetime.now()
    if now.hour < 9:
        today = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        today = now.strftime("%Y-%m-%d")
    if report.get("date") != today:
        logger.info(f"report date fix: {report.get('date')} → {today} "
                    f"({report.get('name','?')}, 제출 {now.strftime('%H:%M')})")
        report["date"] = today

    # 블로킹 호출(LLM·subprocess·urllib)은 to_thread로 오프로딩해 이벤트루프 정지를 막는다.
    await asyncio.to_thread(structure_report, report, completion_answers)

    # Reporting OS v1.1: 보완 답변이 반영된 최종본 기준 채점. 실패해도 보고 흐름은 막지 않는다.
    final_score = await asyncio.to_thread(rubric_evaluate, report) or _rule_based_score(report)
    asked = len(context.user_data.get("completion_queue", []) or [])
    report["report_score"] = final_score.get("total", "")
    # Wave 2 (§5): 보고 유형 A(일반)/B(이슈)/C(의사결정) — 시트 스키마 불변, score_detail JSON에 포함
    report["report_type"] = final_score.get("report_type", "")
    report["score_detail"] = json.dumps(
        {"scores": final_score.get("scores", {}), "asked": asked,
         "type": report["report_type"],
         "mode": final_score.get("mode", ""),           # grace/strict (2026-07-20 이원화)
         "weights": final_score.get("weights_version", ""),
         "fallback": bool(final_score.get("fallback"))},
        ensure_ascii=False,
    )
    report["_score_meta"] = final_score  # 회신 포맷용 (시트에는 report_score/score_detail만)
    logger.info(f"report-score: {report.get('name','')} {report.get('date','')} = "
                f"{report['report_score']}/100 (asked={asked}, fallback={bool(final_score.get('fallback'))})")

    employee_msg = format_report_for_employee(report)
    manager_msg = format_report_for_manager(report)

    # 1) 직원 본인에게 정리본 + Reflection 회신 (거울 학습 루프 — MVP1 핵심)
    await update.message.reply_text(employee_msg)

    # 2) 관리자(대표) 전송 + 팀 리더 공유 + 시트 저장 (모두 블로킹 → to_thread)
    sent = await asyncio.to_thread(send_to_manager, manager_msg)
    leader_sent = await asyncio.to_thread(share_to_team_leader, report, manager_msg)
    sv = await asyncio.to_thread(save_to_sheet, report)
    _save_decision_log(report)  # Engine D: 결정 있으면 decisions.jsonl 축적(없으면 no-op)

    status_lines = ["\n✅ 업무보고 완료!"]
    status_lines.append(
        f"📊 핵심 {len(report['core_tasks'])}건 + 서브 {len(report['sub_tasks'])}건 정리됨"
    )
    if report.get("attachments"):
        status_lines.append(f"📎 첨부 산출물 {len(report['attachments'])}건 함께 전송됨")
    status_lines.append("📨 팀장님께 전송 완료!" if sent else "⚠️ 팀장님 전송 실패 (나중에 재시도)")
    if leader_sent:
        status_lines.append(f"👥 팀 리더께도 공유됨 ({leader_sent}명)")
    # '저장 완료'는 실제로 1행 이상 저장됐고 실패가 없을 때만. total==0(행조립 실패 등)은 완료 아님.
    if sv["total"] > 0 and not sv["failed"]:
        status_lines.append("💾 구글시트 저장 완료!")
    else:
        # 정직한 안내: 유실 아님(로컬 큐 보관·자동 백필, 조립실패는 복구로그) — 직원이 재전송할 필요 없음
        status_lines.append(
            "💾 시트 저장이 지연되고 있어요 — 보고 내용은 안전하게 보관했고 자동으로 재시도됩니다.\n"
            "   (다시 보내실 필요 없어요!)")
        if sv["err"] == "auth":
            cause = ("gws 인증 장애 — 서버에서 "
                     "`gws auth login --services drive,sheets,gmail,calendar,docs,slides,tasks` 재인증 필요"
                     " (--full은 RAPT 재발로 금지)")
        elif sv["err"] == "build":
            cause = "보고 구조 조립 오류(형식 이상) — 원문은 봇 로그에 보존됨, 수동 확인 필요"
        else:
            cause = "일시 오류"
        scope = "행 조립 실패" if sv["err"] == "build" else f"{len(sv['failed'])}/{sv['total']}행"
        send_to_manager(
            f"🚨 시트 저장 실패 · {report.get('name','?')} ({scope})\n"
            f"원인: {cause}\n"
            f"→ 로컬 큐/로그 보관됨, 백필 배치가 자동 재시도합니다.")
    status_lines.append("\n수고하셨어요! 내일도 화이팅 💪")

    await update.message.reply_text("\n".join(status_lines))
    await _employee_memory(update, report)  # ARISA 직원 거울: 재부상 + 누적
    context.user_data.pop("pending_report", None)
    return ConversationHandler.END


# === 핸들러 ===

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # AX 뉴스레터 자동 구독 (링크 클릭 → [시작]만으로 등록)
    is_new = register_subscriber(update.effective_chat.id)
    nl_line = ("✅ AX 교육 뉴스레터 수신 신청이 완료됐어요! 매주 한 통씩 보내드릴게요.\n\n"
               if is_new else "✅ 이미 AX 뉴스레터를 받고 계세요!\n\n")
    await update.message.reply_text(
        "안녕하세요! 업무보고 도우미입니다 📋\n\n"
        + nl_line +
        "오늘 하신 일을 편하게 얘기해주시면\n"
        "깔끔하게 정리해서 팀장님께 보내드릴게요.\n\n"
        "/report — 업무 보고 시작\n"
        "/assign — 업무분장 추가 (대표 전용)\n"
        "/cancel — 취소"
    )


async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["chat_history"] = []
    context.user_data["raw_log"] = []  # fidelity: 직원 원문 입력 보존

    # 텔레그램 ID로 직원 자동 인식 (학습된 경우 → 이름 입력 생략)
    emp = employee_by_tid(update.effective_user.id)
    if emp:
        team = emp.get("team") or emp.get("company", "")
        context.user_data["name"] = emp["name"]
        context.user_data["team"] = team
        context.user_data["role"] = emp.get("role", "")
        context.user_data["date"] = datetime.now().strftime("%Y-%m-%d")
        await update.message.reply_text(
            f"{emp['name']}님, 안녕하세요! ({team} · {emp.get('role','')})\n\n"
            "오늘 하신 일을 생각나는 대로 쭉 말씀해주세요. 순서 상관없어요 😊"
        )
        return WAITING_TASKS

    await update.message.reply_text(
        "업무 보고를 시작할게요!\n\n"
        "먼저 이름을 알려주세요. (명부에 있으면 소속·역할은 자동으로 채워져요)\n"
        "명부에 없으면 '이름 / 팀 / 역할' 형식으로 알려주세요.\n"
        "예) 양지혜   또는   홍길동 / 마케팅팀 / 마케터"
    )
    return WAITING_INFO


async def receive_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    # 이름칸 오염 방지: 보고문(ChatGPT 정리본 등)을 이름 자리에 붙여넣으면 시트 컬럼이 밀린다.
    # 여러 줄이거나 과하게 길면 이름이 아니라 업무 내용 → 되묻기.
    if "\n" in text or len(text) > 40:
        await update.message.reply_text(
            "앗, 여기는 성함만 짧게 보내주세요 🙏 (명부에 있으면 이름만, 없으면 '이름 / 팀 / 역할')\n"
            "업무 내용은 다음 단계에서 받을게요!"
        )
        return WAITING_INFO
    parts = [p.strip() for p in text.replace(",", "/").split("/")]
    name = parts[0]
    if not name or len(name) > 15:
        await update.message.reply_text("성함만 입력해주세요 🙏 (예: 홍길동)")
        return WAITING_INFO

    # 규칙5: 명부 매칭 → 소속/직책/직무 자동 보정 (직원이 잘못 입력해도 정답으로 정정)
    emp = match_employee(name)
    if emp:
        team = emp.get("team") or emp.get("company", "")
        context.user_data["name"] = emp["name"]
        context.user_data["team"] = team
        context.user_data["role"] = emp.get("role", "")
        register_telegram_id(update.effective_user.id, emp["name"])  # 다음부터 자동 인식
        greet = f"{emp['name']}님 확인했어요! ({team} · {emp.get('role','')})"
    else:
        if len(parts) < 2:
            await update.message.reply_text(
                "이름이 명부에 없네요. '이름 / 팀 / 역할' 형식으로 알려주세요!\n"
                "예) 홍길동 / 마케팅팀 / 마케터"
            )
            return WAITING_INFO
        context.user_data["name"] = parts[0]
        context.user_data["team"] = parts[1] if len(parts) > 1 else ""
        context.user_data["role"] = parts[2] if len(parts) > 2 else ""
        greet = f"{parts[0]}님, 반갑습니다!"

    context.user_data["date"] = datetime.now().strftime("%Y-%m-%d")
    await update.message.reply_text(
        f"{greet}\n\n"
        "오늘 하신 일을 생각나는 대로 쭉 나열해주세요.\n"
        "크든 작든 다 괜찮아요. 순서 상관없어요! 😊"
    )
    return WAITING_TASKS


async def receive_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data.setdefault("raw_log", []).append(f"[업무 나열] {text}")
    await update.message.reply_text("정리하고 있어요... ⏳")

    result = await asyncio.to_thread(call_gpt, CATEGORIZE_PROMPT, text)
    if not result or "tasks" not in result:
        await update.message.reply_text(
            "죄송해요, 정리가 잘 안 됐어요 😅\n다시 한번 업무를 나열해주세요!"
        )
        return WAITING_TASKS

    context.user_data["all_tasks"] = result["tasks"]
    context.user_data["suggested_core"] = result.get("suggested_core", [0])

    lines = ["오케이, 정리하면 이런 느낌이네요:\n"]
    for i, t in enumerate(result["tasks"]):
        lines.append(f"{i+1}. {t['task']} [{t['category']}] — {t['status']}")

    suggested = result.get("suggested_core", [0])
    suggested_names = [result["tasks"][i]["task"] for i in suggested if i < len(result["tasks"])]
    lines.append(f"\n💡 핵심 업무 추천: {', '.join(suggested_names)}")
    lines.append("\n빠진 거 있으면 말씀해주시고,\n맞으면 '맞아' 또는 '확인' 이라고 해주세요!")

    await update.message.reply_text("\n".join(lines))
    return WAITING_CONFIRM


async def receive_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    low = text.lower()
    confirm_kw = ("맞아", "확인", "네", "ㅇㅇ", "응", "ok", "ㅇ", "맞음", "넵")

    # 확인 키워드면 GPT 의도판단 생략(비용·지연↓). 아니면 to_thread로 판단(질문이면 답변).
    if low not in confirm_kw and await asyncio.to_thread(detect_intent, text) == "question":
        return await handle_question(update, context, WAITING_CONFIRM)

    if low in confirm_kw:
        suggested = context.user_data.get("suggested_core", [0])
        all_tasks = context.user_data.get("all_tasks", [])
        if suggested and all_tasks:
            core_idx = suggested[0]
            core_task = all_tasks[core_idx]["task"] if core_idx < len(all_tasks) else all_tasks[0]["task"]
            context.user_data["current_core_idx"] = 0
            context.user_data["core_indices"] = suggested
            context.user_data["core_details"] = []

            await update.message.reply_text(
                f"좋아요! 그러면 '{core_task}'에 대해서만 자세히 들을게요.\n\n"
                "이 업무가 원래 무엇을 위한 것이었는지(목표),\n"
                "어떻게 시작됐고, 어떤 순서로 진행했고,\n"
                "결과물이 뭔지, 사용한 도구가 있는지\n"
                "편하게 말씀해주세요!"
            )
            return WAITING_DRILLDOWN
        # 확인했지만 정리된 업무가 비어 있음 → 무응답으로 갇히지 않게 다시 나열 요청
        await update.message.reply_text(
            "앗, 정리된 업무가 없네요 😅 오늘 하신 일을 다시 한번 나열해주시겠어요?")
        return WAITING_TASKS
    else:
        # 수정/추가 처리
        original = "\n".join([t["task"] for t in context.user_data.get("all_tasks", [])])
        result = await asyncio.to_thread(call_gpt, CATEGORIZE_PROMPT, f"기존 업무:\n{original}\n\n수정/추가 사항:\n{text}")
        if result and "tasks" in result:
            context.user_data["all_tasks"] = result["tasks"]
            context.user_data["suggested_core"] = result.get("suggested_core", [0])

            lines = ["수정했어요:\n"]
            for i, t in enumerate(result["tasks"]):
                lines.append(f"{i+1}. {t['task']} [{t['category']}] — {t['status']}")
            lines.append("\n이제 맞나요? '맞아' 라고 해주세요!")
            await update.message.reply_text("\n".join(lines))
        else:
            await update.message.reply_text("수정 반영이 어려워요 😅 '맞아'로 진행하거나 다시 나열해주세요!")
        return WAITING_CONFIRM


async def receive_drilldown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()

    # 의도 판단(블로킹 GPT는 to_thread로 오프로딩)
    intent = await asyncio.to_thread(detect_intent, text)

    if intent == "question":
        return await handle_question(update, context, WAITING_DRILLDOWN)

    core_indices = context.user_data.get("core_indices", [0])
    current_idx = context.user_data.get("current_core_idx", 0)
    all_tasks = context.user_data.get("all_tasks", [])

    task_name = all_tasks[core_indices[current_idx]]["task"] if core_indices[current_idx] < len(all_tasks) else ""
    context.user_data.setdefault("raw_log", []).append(f"[상세: {task_name}] {text}")
    detail = await asyncio.to_thread(call_gpt, DRILLDOWN_PROMPT, f"업무: {task_name}\n상세 설명: {text}")

    if detail:
        context.user_data.setdefault("core_details", []).append({
            "task_idx": core_indices[current_idx],
            **detail
        })

    next_idx = current_idx + 1
    if next_idx < len(core_indices) and next_idx < 2:
        context.user_data["current_core_idx"] = next_idx
        next_task = all_tasks[core_indices[next_idx]]["task"] if core_indices[next_idx] < len(all_tasks) else ""
        await update.message.reply_text(
            f"고마워요! 다음으로 '{next_task}'도 간단히 알려주세요."
        )
        return WAITING_DRILLDOWN

    await update.message.reply_text(
        "좋아요! 거의 다 됐어요 👍\n\n"
        "오늘 일하면서 막힌 부분이나\n"
        "시간이 예상보다 많이 든 부분이 있었어요?\n\n"
        "없으면 '없어' 라고 해주세요!"
    )
    return WAITING_ISSUES


async def receive_issues(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    low = text.lower()

    if low in ("없어", "없음", "없었어", "없었어요", "ㄴㄴ", "노", "no"):
        context.user_data["blockers"] = ""  # 키워드 답변 → GPT 생략
    else:
        # 키워드가 아니면 의도판단(질문이면 답하고 단계 유지)
        if await asyncio.to_thread(detect_intent, text) == "question":
            return await handle_question(update, context, WAITING_ISSUES)
        context.user_data["blockers"] = text

    await update.message.reply_text(
        "마지막! 내일 이어갈 일이나 우선순위가 있으면 알려주세요.\n"
        "없으면 '없어' 라고 해주세요!"
    )
    return WAITING_TOMORROW


async def receive_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    low = text.lower()

    if low in ("없어", "없음", "없었어", "ㄴㄴ"):
        context.user_data["tomorrow"] = ""  # 키워드 답변 → GPT 생략
    else:
        if await asyncio.to_thread(detect_intent, text) == "question":
            return await handle_question(update, context, WAITING_TOMORROW)
        context.user_data["tomorrow"] = text

    # 3.0 질문보고: 직원이 스스로 던지는 '오늘의 질문' 하나
    # (봇이 캐묻는 게 아니라, 직원이 자기 사고를 꺼내도록 자리만 연다 — 답→질문 전환의 첫걸음)
    await update.message.reply_text(
        "💭 마지막으로, 오늘 일하면서 가장 중요하게 떠오른 '질문' 하나가 있다면 적어주세요.\n"
        "   (답이 아니라 질문이어도 좋아요. 없으면 '없어')"
    )
    return WAITING_QUESTION


async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """3.0 질문보고: 직원의 '오늘의 질문' 1개 수집 → Engine B(최대 1개 보완질문) → 정리."""
    text = update.message.text.strip()

    low = text.lower()
    kw = ("없어", "없음", "없었어", "ㄴㄴ", "패스", "스킵", "pass", "skip")

    # 키워드가 아닐 때만 의도판단(질문이면 답하고 단계 유지) — 키워드면 GPT 생략
    if low not in kw and await asyncio.to_thread(detect_intent, text) == "question":
        return await handle_question(update, context, WAITING_QUESTION)

    if low in kw:
        context.user_data["key_question"] = ""
    else:
        context.user_data["key_question"] = text
        # fidelity: 직원의 질문 원문도 보존 (assemble_report가 raw_log → raw로 합침)
        context.user_data.setdefault("raw_log", []).append(f"[오늘의 질문] {text}")

    # 보고 조립
    report = assemble_report(context.user_data)

    # Engine B 확장(Reporting OS v1.1): 루브릭으로 비춰보고, 부족 항목을 질문으로 마저 채운다
    await update.message.reply_text("오늘 보고를 정리하고 있어요... ⏳")
    _, questions = await asyncio.to_thread(completion_evaluate, report)

    if not questions:
        # 충분 → 바로 마무리 (피로 최소화)
        return await finalize_and_send(update, context, report, "")

    # 부족 → 배점 큰 항목부터 한 번에 하나씩, 최대 3라운드 (질문 폭탄 금지)
    context.user_data["pending_report"] = report
    context.user_data["completion_queue"] = questions
    context.user_data["completion_idx"] = 0
    context.user_data["completion_answers"] = ""
    total_q = len(questions)
    intro = (f"{total_q}가지만 더 여쭤볼게요 🙂" if total_q > 1 else "딱 하나만 더 여쭤볼게요 🙂")
    await update.message.reply_text(
        f"거의 다 됐어요! {intro}\n\n"
        f"(1/{total_q}) {questions[0]}\n\n"
        "편하게 답해주세요. 해당 없으면 '없음', 넘어가려면 '패스'라고 해도 돼요."
    )
    return WAITING_COMPLETION


async def receive_completion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Engine B 보완 질문 루프 — 답변을 누적하고 큐가 남았으면 재질문, 소진되면 Engine C로.

    '없음'은 판단한 결과이므로 답변으로 기록(루브릭 만점 규칙), '패스'만 건너뛴다.
    """
    text = update.message.text.strip()

    low = text.lower()
    kw = ("패스", "스킵", "없어", "없음", "pass", "skip")

    # 키워드가 아닐 때만 의도판단(질문이면 답하고 단계 유지)
    if low not in kw and await asyncio.to_thread(detect_intent, text) == "question":
        return await handle_question(update, context, WAITING_COMPLETION)

    report = context.user_data.get("pending_report")
    if not report:
        # 안전장치: 세션이 유실되면 재조립
        report = assemble_report(context.user_data)
        context.user_data["pending_report"] = report

    queue = context.user_data.get("completion_queue", [])
    idx = context.user_data.get("completion_idx", 0)
    current_q = queue[idx] if idx < len(queue) else ""

    answer = "" if text.lower() in ("패스", "스킵", "pass", "skip") else text
    if answer:  # fidelity: 보완 답변도 원문 보존 (질문 맥락 포함)
        entry = f"Q: {current_q}\nA: {answer}" if current_q else answer
        prev = context.user_data.get("completion_answers", "")
        context.user_data["completion_answers"] = f"{prev}\n\n{entry}".strip()
        report["raw"] = (report.get("raw", "") + f"\n[보완답변] {answer}").strip()

    # 다음 질문이 남아 있으면 이어서 (최대 3라운드 — completion_evaluate에서 상한 적용)
    idx += 1
    context.user_data["completion_idx"] = idx
    if idx < len(queue):
        await update.message.reply_text(
            f"고마워요! ({idx + 1}/{len(queue)}) {queue[idx]}\n\n"
            "해당 없으면 '없음', 넘어가려면 '패스'라고 해도 돼요."
        )
        return WAITING_COMPLETION

    await update.message.reply_text("반영해서 정리할게요... ⏳")
    return await finalize_and_send(
        update, context, report, context.user_data.get("completion_answers", "")
    )


async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """보고 도중 언제든 파일(사진/문서)을 받으면 드라이브에 업로드하고 누적.

    state를 반환하지 않으므로(None) 현재 대화 단계는 그대로 유지된다.
    """
    msg = update.message
    name = context.user_data.get("name", "미상")
    date = context.user_data.get("date", datetime.now().strftime("%Y-%m-%d"))

    # 1) 텔레그램 파일 객체 + 원본 파일명 결정
    if msg.document:
        tg_file_id = msg.document.file_id
        orig_name = msg.document.file_name or f"file_{msg.document.file_unique_id}"
    elif msg.photo:
        photo = msg.photo[-1]  # 가장 큰 해상도
        tg_file_id = photo.file_id
        orig_name = f"photo_{photo.file_unique_id}.jpg"
    else:
        return  # 처리 대상 아님

    await msg.reply_text("📎 파일 받는 중... ⏳")

    # 2) 임시 폴더로 다운로드
    ATTACH_TMP_DIR.mkdir(parents=True, exist_ok=True)
    display_name = f"{date}_{name}_{orig_name}"
    local_path = ATTACH_TMP_DIR / display_name
    try:
        tg_file = await context.bot.get_file(tg_file_id)
        await tg_file.download_to_drive(custom_path=str(local_path))
    except Exception as e:
        logger.error(f"Telegram download error: {e}")
        await msg.reply_text("⚠️ 파일을 받지 못했어요. 다시 보내주세요!")
        return

    # 3) 구글드라이브 업로드 (실패 시 임시파일을 지우지 않고 보존 — 유실 방지)
    link = await asyncio.to_thread(upload_to_drive, local_path, display_name)
    if not link:
        logger.error(f"LOST-ATTACHMENT keep={local_path}")  # 수동 복구용 경로 로그 보존
        await msg.reply_text("⚠️ 파일 저장에 실패했어요. 잠시 후 다시 보내주세요! (받은 파일은 서버에 임시 보관돼 있어요)")
        return
    local_path.unlink(missing_ok=True)  # 업로드 성공 시에만 임시파일 정리

    context.user_data.setdefault("attachments", []).append(
        {"name": orig_name, "link": link}
    )
    count = len(context.user_data["attachments"])
    await msg.reply_text(
        f"✅ 받았어요! ({orig_name})\n"
        f"지금까지 첨부 {count}개. 계속 보고 진행하셔도 돼요!"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("업무 보고를 취소했어요. 다시 하려면 /report!")
    return ConversationHandler.END


# === /meeting 핸들러 (ARISA 1.0 회의록 통합) ===

def _get_meeting_projects() -> list[str]:
    """meeting-projects/ 안의 프로젝트 목록 (디렉토리, _template 제외)."""
    if not _MEETING_PROJECTS_DIR.exists():
        return []
    return sorted([
        d.name for d in _MEETING_PROJECTS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
    ])


async def cmd_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """회의록 처리 시작 — 프로젝트 선택."""
    if not _MEETING_AVAILABLE:
        await update.message.reply_text("Meeting Engine을 로드하지 못했습니다.")
        return ConversationHandler.END

    uid = update.effective_user.id
    if uid not in _MEETING_ALLOWED:
        await update.message.reply_text("회의록 기능은 대표 전용입니다.")
        return ConversationHandler.END

    context.user_data["mtg"] = {}
    projects = _get_meeting_projects()

    if projects:
        lines = ["어떤 프로젝트 회의인가요?\n"]
        for i, p in enumerate(projects, 1):
            lines.append(f"{i}. {p}")
        lines.append(f"\n번호 또는 이름을 입력하세요.")
        lines.append("새 프로젝트를 만들려면 '새로 [이름]' (예: 새로 봉은사리뉴얼)")
    else:
        lines = ["등록된 프로젝트가 없습니다.\n'새로 [이름]'으로 새 프로젝트를 만드세요."]

    await update.message.reply_text("\n".join(lines))
    return MTG_SELECT_PROJECT


async def mtg_select_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """프로젝트 선택 또는 신규 생성."""
    text = update.message.text.strip()
    projects = _get_meeting_projects()

    # 신규 생성
    if text.startswith("새로 ") or text.startswith("새로\n"):
        name = text[3:].strip().replace(" ", "-").lower()
        if not name:
            await update.message.reply_text("프로젝트 이름을 입력해주세요. (예: 새로 브랜딩전략)")
            return MTG_SELECT_PROJECT
        import shutil
        project_dir = _MEETING_PROJECTS_DIR / name
        if project_dir.exists():
            await update.message.reply_text(f"'{name}' 프로젝트가 이미 있습니다. 그대로 사용합니다.")
        else:
            shutil.copytree(_MEETING_TEMPLATE_DIR, project_dir)
            await update.message.reply_text(f"'{name}' 프로젝트를 생성했습니다.")
        context.user_data["mtg"]["project"] = name
        await update.message.reply_text(
            "회의 내용을 보내주세요.\n"
            "- 텍스트 붙여넣기 (50자 이상)\n"
            "- .txt / .md 파일 첨부\n"
            "둘 다 가능합니다."
        )
        return MTG_INPUT

    # 번호 선택
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(projects):
            context.user_data["mtg"]["project"] = projects[idx]
            await update.message.reply_text(
                f"'{projects[idx]}' 프로젝트 선택.\n\n"
                "회의 내용을 보내주세요. (텍스트 또는 .txt/.md 파일)"
            )
            return MTG_INPUT

    # 이름 매칭
    matched = [p for p in projects if text.lower() in p.lower()]
    if len(matched) == 1:
        context.user_data["mtg"]["project"] = matched[0]
        await update.message.reply_text(
            f"'{matched[0]}' 프로젝트 선택.\n\n"
            "회의 내용을 보내주세요. (텍스트 또는 .txt/.md 파일)"
        )
        return MTG_INPUT

    await update.message.reply_text(
        "프로젝트를 찾지 못했습니다. 번호 또는 정확한 이름을 입력해주세요.\n"
        "새 프로젝트: '새로 [이름]'"
    )
    return MTG_SELECT_PROJECT


async def mtg_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """회의 텍스트 수신 -> 소스타입 감지 -> 확인."""
    text = update.message.text.strip()
    if len(text) < 50:
        await update.message.reply_text("회의 내용이 너무 짧습니다. 50자 이상 입력해주세요.")
        return MTG_INPUT

    context.user_data["mtg"]["text"] = text
    context.user_data["mtg"]["source_name"] = "telegram-text"

    src = detect_source_type(text)
    label = SOURCE_LABELS.get(src, src)
    context.user_data["mtg"]["source_type"] = src

    await update.message.reply_text(
        f"소스 타입: {label}\n\n"
        "맞으면 '확인', 변경하려면 'ai' 또는 'mtg'를 입력해주세요."
    )
    return MTG_CONFIRM


async def mtg_receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """회의 파일(.txt/.md) 수신."""
    document = update.message.document
    if not document:
        await update.message.reply_text("텍스트 또는 .txt/.md 파일을 보내주세요.")
        return MTG_INPUT

    file_name = document.file_name or "unknown"
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext not in ("txt", "md", "markdown"):
        await update.message.reply_text(f"'{file_name}' — .txt 또는 .md 파일만 지원합니다.")
        return MTG_INPUT

    await update.message.reply_text(f"'{file_name}' 다운로드 중...")

    tg_file = await document.get_file()
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    await tg_file.download_to_drive(str(tmp_path))

    content = None
    for encoding in ("utf-8", "utf-16", "cp949", "euc-kr"):
        try:
            content = tmp_path.read_text(encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    tmp_path.unlink(missing_ok=True)

    if not content or len(content.strip()) < 50:
        await update.message.reply_text("파일 내용이 없거나 너무 짧습니다 (50자 이상).")
        return MTG_INPUT

    context.user_data["mtg"]["text"] = content
    context.user_data["mtg"]["source_name"] = file_name

    src = detect_source_type(content)
    label = SOURCE_LABELS.get(src, src)
    context.user_data["mtg"]["source_type"] = src

    await update.message.reply_text(
        f"'{file_name}' ({len(content):,}자) 수신 완료.\n"
        f"소스 타입: {label}\n\n"
        "맞으면 '확인', 변경하려면 'ai' 또는 'mtg'를 입력해주세요."
    )
    return MTG_CONFIRM


async def mtg_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """소스타입 확인 -> 6종 리포트 생성."""
    text = update.message.text.strip().lower()
    mtg_data = context.user_data.get("mtg", {})

    if text in ("ai",):
        mtg_data["source_type"] = "ai"
        await update.message.reply_text("AI 디스커션으로 변경. '확인'을 눌러주세요.")
        return MTG_CONFIRM
    elif text in ("mtg", "팀", "미팅"):
        mtg_data["source_type"] = "mtg"
        await update.message.reply_text("팀 미팅으로 변경. '확인'을 눌러주세요.")
        return MTG_CONFIRM
    elif text not in ("확인", "맞아", "네", "ㅇㅇ", "응", "ok", "ㅇ"):
        await update.message.reply_text("'확인', 'ai', 또는 'mtg'를 입력해주세요.")
        return MTG_CONFIRM

    project_name = mtg_data.get("project", "")
    project_dir = _MEETING_PROJECTS_DIR / project_name
    meeting_text = mtg_data.get("text", "")
    source_name = mtg_data.get("source_name", "telegram")

    if not meeting_text:
        await update.message.reply_text("회의 내용이 없습니다. /meeting 으로 다시 시작해주세요.")
        return ConversationHandler.END

    await update.message.reply_text(
        f"'{project_name}' 프로젝트 — 6종 리포트 생성 중...\n"
        "(GPT 6회 호출, 1~3분 소요)"
    )

    try:
        result = await asyncio.to_thread(
            meeting_engine.process_all_reports,
            meeting_text, project_dir, source_name,
        )
    except Exception as e:
        logger.exception(f"Meeting engine error: {e}")
        await update.message.reply_text(f"리포트 생성 실패: {e}")
        return ConversationHandler.END

    # 텔레그램 요약 전송
    summary = meeting_engine.format_meeting_summary(result)
    await update.message.reply_text(summary)

    # 시트에 메타 기록
    _save_meeting_meta(result)

    # 결정사항이 있으면 관리자에게도 전송
    reports = result.get("reports", {})
    dec = reports.get("decisions", {})
    new_decs = dec.get("new_decisions", [])
    if new_decs:
        dec_lines = [f"[Meeting] {project_name} — 신규 결정 {len(new_decs)}건"]
        for d in new_decs:
            dec_lines.append(f"  {d.get('decision', '')}")
        send_to_manager("\n".join(dec_lines))

    context.user_data.pop("mtg", None)
    return ConversationHandler.END


def _save_meeting_meta(result: dict) -> bool:
    """회의록 메타를 구글시트 '회의록' 탭에 기록."""
    try:
        reports = result.get("reports", {})
        dec = reports.get("decisions", {})
        td = reports.get("todo", {})
        pr = reports.get("progress", {})

        n_decisions = len(dec.get("new_decisions", []))
        n_todos = len(td.get("todos", []))
        health = pr.get("project_health", "")

        row = [
            result.get("today", ""),
            result.get("project", ""),
            result.get("source_label", ""),
            n_decisions,
            n_todos,
            health,
        ]
        # shared.gws 경유(재시도+인증분류) — raw subprocess는 returncode를 안 봐서 실패를 삼켰음
        return _gws.append_to_sheet(SHEET_ID, "회의록!A1", row, value_input_option="RAW", timeout=15)
    except Exception as e:
        logger.error(f"Meeting meta save error: {e}")
        return False


async def cancel_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("mtg", None)
    await update.message.reply_text("회의록 처리를 취소했습니다.")
    return ConversationHandler.END


# === /assign 핸들러 (주간 업무분장 간편 추가) ===

_ASSIGN_TEAMS = ["기획팀", "공간팀", "사업기획", "운영팀", "경영"]

ASSIGN_PARSE_PROMPT = """주간 업무분장 항목을 파싱해라. 입력에서 프로젝트/팀/업무내용/담당자/마감을 추출.
담당자는 이름만(님 제거). 마감은 요일이면 이번 주 날짜(YYYY-MM-DD)로 변환.
project: 프로젝트·브랜드명이 언급되면 그 이름(없으면 빈문자열. 지어내지 말 것).
우선순위: "최우선"/"긴급"/"!!" → "긴급", 나머지 → "일반".

오늘 날짜: {today}

반드시 JSON만 출력:
{{"project": "프로젝트명 또는 빈문자열", "team": "팀명", "task": "업무내용", "assignee": "담당자이름 또는 빈문자열", "deadline": "YYYY-MM-DD 또는 빈문자열", "priority": "긴급|일반"}}"""


def _week_label() -> str:
    """현재 ISO 주차 라벨 (W27 등)."""
    now = datetime.now()
    return f"W{now.isocalendar().week:02d}"


def save_assignment_to_sheet(team: str, task: str, assignee: str,
                              deadline: str, priority: str, project: str = "") -> bool:
    """주간분장 탭에 1행 등록 — 신스키마(셸 분장과 동일):
    날짜|프로젝트명|팀|담당자|업무내용|일정|결과물|상태|이해관계자|우선순위|프로젝트ID(G1).
    (구스키마 W라벨 행을 잘못된 칸에 append하던 버그 수정 — 2026-07-18)"""
    pr = "긴급" if priority in ("긴급", "최우선") else "일반"
    registry = _load_project_registry()
    project = _nm_clean(project)  # P2 — 네이밍 규칙 자동 정리 (Team Ops Guide 2부-①)
    row = [
        datetime.now().strftime("%Y-%m-%d"), project or "", team,
        assignee or "팀", task, deadline, "", "미착수", "", pr,
        _project_pid(project, registry),
    ]
    return _gws.append_to_sheet(
        SHEET_ID, "주간분장!A1", row,
        value_input_option="RAW", timeout=15,
    )


async def cmd_assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """업무분장 간편 추가 — 대표 전용."""
    uid = update.effective_user.id
    if uid not in _MEETING_ALLOWED:
        await update.message.reply_text("업무분장 등록은 대표 전용입니다.")
        return ConversationHandler.END

    text = (update.message.text or "").strip()
    # 원라인 모드: /assign 기획팀 CJ 시안 수정 @지혜님 ~수요일
    args = text.split(None, 1)
    if len(args) > 1 and args[1].strip():
        oneline = args[1].strip()
        context.user_data["assign"] = {"raw": oneline}
        await update.message.reply_text("파싱 중... ⏳")
        parsed = await asyncio.to_thread(
            call_gpt,
            ASSIGN_PARSE_PROMPT.format(today=datetime.now().strftime("%Y-%m-%d")),
            oneline,
        )
        if parsed and parsed.get("task"):
            context.user_data["assign"]["parsed"] = parsed
            # P2 — 프로젝트명 네이밍 규칙 자동 정리 (괄호·특수문자 → 공백)
            pj_raw = parsed.get("project") or ""
            parsed["project"] = _nm_clean(pj_raw)
            team = parsed.get("team", "")
            assignee = parsed.get("assignee", "")
            deadline = parsed.get("deadline", "")
            priority = parsed.get("priority", "일반")
            # 담당자 명부 매칭
            if assignee:
                emp = match_employee(assignee)
                if emp:
                    assignee = emp["name"]
                    if not team:
                        team = emp.get("team", "")
            context.user_data["assign"]["parsed"]["team"] = team
            context.user_data["assign"]["parsed"]["assignee"] = assignee
            _pj_note = " (규칙 자동정리)" if parsed.get("project") != pj_raw and pj_raw else ""
            await update.message.reply_text(
                f"✅ 파싱 결과:\n"
                f"  프로젝트: {(parsed.get('project') or '—') + _pj_note}\n"
                f"  팀: {team}\n"
                f"  업무: {parsed['task']}\n"
                f"  담당: {assignee or '팀'}\n"
                f"  마감: {deadline or '미정'}\n"
                f"  우선순위: {priority}\n\n"
                f"맞으면 '확인', 수정하려면 내용을 다시 입력하세요."
            )
            return ASSIGN_CONFIRM

    # 대화형 모드
    context.user_data["assign"] = {}
    lines = ["어떤 팀에 배정하시겠어요?\n"]
    for i, t in enumerate(_ASSIGN_TEAMS, 1):
        lines.append(f"{i}. {t}")
    await update.message.reply_text("\n".join(lines))
    return ASSIGN_TEAM


async def assign_team(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """팀 선택."""
    text = update.message.text.strip()
    team = None
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(_ASSIGN_TEAMS):
            team = _ASSIGN_TEAMS[idx]
    else:
        for t in _ASSIGN_TEAMS:
            if text in t or t in text:
                team = t
                break
    if not team:
        await update.message.reply_text("팀을 다시 선택해주세요. (번호 또는 팀명)")
        return ASSIGN_TEAM

    context.user_data["assign"]["team"] = team
    await update.message.reply_text(
        f"'{team}' 선택.\n\n"
        "업무 내용을 입력해주세요.\n"
        "예) CJ 시안 수정 @양지혜 ~수요일 (최우선)"
    )
    return ASSIGN_CONTENT


async def assign_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """업무 내용 파싱."""
    text = update.message.text.strip()
    team = context.user_data["assign"].get("team", "")
    context.user_data["assign"]["raw"] = text

    parsed = await asyncio.to_thread(
        call_gpt,
        ASSIGN_PARSE_PROMPT.format(today=datetime.now().strftime("%Y-%m-%d")),
        f"팀: {team}\n내용: {text}",
    )
    if not parsed or not parsed.get("task"):
        parsed = {"team": team, "task": text, "assignee": "", "deadline": "", "priority": "일반"}

    parsed["team"] = parsed.get("team") or team
    # 담당자 명부 매칭
    assignee = parsed.get("assignee", "")
    if assignee:
        emp = match_employee(assignee)
        if emp:
            parsed["assignee"] = emp["name"]

    context.user_data["assign"]["parsed"] = parsed
    await update.message.reply_text(
        f"✅ 파싱 결과:\n"
        f"  프로젝트: {parsed.get('project') or '—'}\n"
        f"  팀: {parsed['team']}\n"
        f"  업무: {parsed['task']}\n"
        f"  담당: {parsed.get('assignee') or '팀'}\n"
        f"  마감: {parsed.get('deadline') or '미정'}\n"
        f"  우선순위: {parsed.get('priority', '일반')}\n\n"
        f"맞으면 '확인', 수정하려면 내용을 다시 입력하세요."
    )
    return ASSIGN_CONFIRM


async def assign_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """확인 → 시트 등록."""
    text = update.message.text.strip()

    if text.lower() not in ("확인", "맞아", "네", "ㅇㅇ", "응", "ok", "ㅇ", "맞음"):
        # 재파싱
        context.user_data["assign"]["raw"] = text
        team = context.user_data["assign"].get("team", "")
        parsed = await asyncio.to_thread(
            call_gpt,
            ASSIGN_PARSE_PROMPT.format(today=datetime.now().strftime("%Y-%m-%d")),
            f"팀: {team}\n내용: {text}",
        )
        if parsed and parsed.get("task"):
            parsed["team"] = parsed.get("team") or team
            assignee = parsed.get("assignee", "")
            if assignee:
                emp = match_employee(assignee)
                if emp:
                    parsed["assignee"] = emp["name"]
            context.user_data["assign"]["parsed"] = parsed
            await update.message.reply_text(
                f"수정 파싱:\n"
                f"  팀: {parsed['team']} | 업무: {parsed['task']}\n"
                f"  담당: {parsed.get('assignee') or '팀'} | 마감: {parsed.get('deadline') or '미정'}\n"
                f"맞으면 '확인'"
            )
            return ASSIGN_CONFIRM
        await update.message.reply_text("파싱 실패. 다시 입력해주세요.")
        return ASSIGN_CONFIRM

    p = context.user_data["assign"].get("parsed", {})
    ok = save_assignment_to_sheet(
        p.get("team", ""), p.get("task", ""),
        p.get("assignee", ""), p.get("deadline", ""),
        p.get("priority", "일반"), p.get("project", ""),
    )
    if ok:
        await update.message.reply_text(
            f"✅ 등록 완료!\n"
            f"  [{p.get('team','')}] {p.get('task','')} — {p.get('assignee','') or '팀'}\n\n"
            f"추가 등록: /assign\n전체 분장: /주간분장 (Claude)"
        )
    else:
        await update.message.reply_text("⚠️ 시트 등록 실패. 잠시 후 다시 시도해주세요.")
    context.user_data.pop("assign", None)
    return ConversationHandler.END


async def cancel_assign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("assign", None)
    await update.message.reply_text("업무분장 등록을 취소했습니다.")
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """핸들러 내부에서 발생한 모든 예외를 잡아 로깅하고, 가능하면 사용자에게 안내한다.

    에러 핸들러가 없으면(No error handlers are registered) 일시적 네트워크 끊김에도
    직원의 보고가 재시도/안내 없이 통째로 유실된다. 이 핸들러가 마지막 안전망이다.
    """
    err = context.error
    logger.error("Handler exception: %s", err, exc_info=err)

    # 사용자가 보고 중이었다면, 유실로 끝나지 않도록 안내해 재시도를 유도한다.
    msg = getattr(update, "message", None) if isinstance(update, Update) else None
    if msg is None:
        return
    try:
        if isinstance(err, (NetworkError, TimedOut)):
            await msg.reply_text(
                "⚠️ 잠시 네트워크가 불안정했어요. 방금 보내신 내용을 한 번만 다시 보내주시겠어요?\n"
                "(보고는 이어서 진행됩니다 — 처음부터 다시 하실 필요 없어요)"
            )
        else:
            await msg.reply_text(
                "⚠️ 처리 중 문제가 생겼어요. 잠시 후 같은 내용을 다시 보내주세요.\n"
                "계속 안 되면 /report 로 다시 시작해주세요."
            )
    except Exception as e:
        # 안내 전송마저 실패(네트워크 지속 끊김) — 로깅만 하고 조용히 넘어간다.
        logger.error("error_handler reply failed: %s", e)


def main() -> None:
    # PID lock — 중복 실행 방지
    pid_file = Path("/tmp/daily-report-bot.pid")
    if pid_file.exists():
        old_pid = pid_file.read_text().strip()
        try:
            os.kill(int(old_pid), 0)  # 프로세스 존재 확인
            print(f"ERROR: 봇이 이미 실행 중입니다 (PID {old_pid}). 종료 후 재시작하세요.")
            print(f"  kill {old_pid} && python3 {__file__}")
            sys.exit(1)
        except (ProcessLookupError, ValueError):
            pass  # 이전 프로세스 없음, 정상 진행
    pid_file.write_text(str(os.getpid()))

    import atexit
    atexit.register(lambda: pid_file.unlink(missing_ok=True))

    # 필수 설정 검증 (.env 누락 시 즉시 명확하게 실패)
    required = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "DAILY_REPORT_BOT_TOKEN": BOT_TOKEN,
        "DAILY_REPORT_MANAGER_BOT_TOKEN": MANAGER_BOT_TOKEN,
        "DAILY_REPORT_MANAGER_CHAT_ID": MANAGER_CHAT_ID,
        "DAILY_REPORT_SHEET_ID": SHEET_ID,
        "DAILY_REPORT_DRIVE_FOLDER_ID": DRIVE_FOLDER_ID,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"ERROR: .env에 다음 값이 없습니다: {', '.join(missing)}")
        sys.exit(1)

    # 네트워크 타임아웃을 넉넉히 둬 일시적 지연·슬립복귀에 강하게 만든다.
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .concurrent_updates(True)  # 사용자별 업데이트 동시 처리 — 한 명의 지연이 전체를 막지 않게
        .persistence(PicklePersistence(filepath=str(PERSIST_FILE)))  # 대화상태 디스크 영속화
        .build()
    )

    # 보고 도중 언제든 파일이 오면 받아서 누적 (모든 단계 공통)
    file_handler = MessageHandler(filters.PHOTO | filters.Document.ALL, receive_file)

    conv = ConversationHandler(
        entry_points=[CommandHandler("report", start_report)],
        states={
            WAITING_INFO: [file_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, receive_info)],
            WAITING_TASKS: [file_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tasks)],
            WAITING_CONFIRM: [file_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, receive_confirm)],
            WAITING_DRILLDOWN: [file_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, receive_drilldown)],
            WAITING_ISSUES: [file_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, receive_issues)],
            WAITING_TOMORROW: [file_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tomorrow)],
            WAITING_QUESTION: [file_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)],
            WAITING_COMPLETION: [file_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, receive_completion)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            # 핫픽스(2026-07-15): 미완료 세션(pickle 부활 포함)이 살아있으면 /report가
            # 어떤 핸들러에도 안 걸려 무반응이 되는 함정 — 진행 중에도 /report = 새로 시작.
            CommandHandler("report", start_report),
        ],
        name="report_conv",
        persistent=True,  # 진행 중 보고 상태를 재시작에도 보존
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(conv)

    # /meeting — 회의록 6종 리포트 (ARISA 1.0 통합)
    if _MEETING_AVAILABLE:
        meeting_client.init(openai_client, model="gpt-4o")
        mtg_conv = ConversationHandler(
            entry_points=[CommandHandler("meeting", cmd_meeting)],
            states={
                MTG_SELECT_PROJECT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, mtg_select_project),
                ],
                MTG_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, mtg_receive_text),
                    MessageHandler(filters.Document.ALL, mtg_receive_file),
                ],
                MTG_CONFIRM: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, mtg_confirm),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel_meeting)],
        )
        app.add_handler(mtg_conv)
        logger.info("Meeting Engine loaded (6-report)")
    else:
        logger.warning("Meeting Engine not available — /meeting disabled")

    # /assign — 주간 업무분장 간편 추가 (대표 전용)
    assign_conv = ConversationHandler(
        entry_points=[CommandHandler("assign", cmd_assign)],
        states={
            ASSIGN_TEAM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, assign_team),
            ],
            ASSIGN_CONTENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, assign_content),
            ],
            ASSIGN_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, assign_confirm),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_assign)],
    )
    app.add_handler(assign_conv)
    logger.info("/assign handler registered (weekly assignment)")

    # 문의·건의 접수 폴백 (2026-07-22, 아리사 OS 전직원 오픈) — 반드시 모든 ConversationHandler 뒤에 등록.
    # 같은 group(0)에서 앞선 대화 핸들러가 매칭되지 않을 때만 실행 → 보고/회의/분장 플로우와 충돌 없음.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_inquiry))
    logger.info("inquiry fallback registered")

    app.add_error_handler(error_handler)  # 핸들러 예외 안전망 (보고 유실 방지)

    logger.info("Daily Report Bot v2 started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
