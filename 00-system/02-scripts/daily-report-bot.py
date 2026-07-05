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

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
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
from shared.employee import load_employees as _load_emp  # noqa: E402
from shared.decision import save_decision_log as _save_decision_log  # noqa: E402

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


def register_subscriber(chat_id) -> bool:
    """봇에 /start 한 사용자를 AX 뉴스레터 구독자(recipients.json)로 자동 등록. 신규면 True."""
    try:
        if NEWSLETTER_RECIPIENTS.exists():
            data = json.loads(NEWSLETTER_RECIPIENTS.read_text(encoding="utf-8"))
        else:
            data = {"recipients": []}
        ids = {str(r.get("chat_id")) for r in data.get("recipients", []) if r.get("chat_id")}
        if str(chat_id) in ids:
            return False
        data.setdefault("recipients", []).append({"chat_id": int(chat_id)})
        NEWSLETTER_RECIPIENTS.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"newsletter subscriber register error: {e}")
        return False
# 텔레그램에서 받은 파일을 잠시 내려받을 임시 폴더
ATTACH_TMP_DIR = Path("/tmp/daily-report-attachments")

openai_client = OpenAI(api_key=OPENAI_API_KEY)


# === 직원명부 (규칙5: 입력 식별 정합) ===

def load_employees() -> dict:
    """인사마스터 스냅샷 명부 로드 (shared 코어 위임)."""
    return _load_emp(EMP_PATH)


def save_employees(data: dict) -> None:
    try:
        EMP_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
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
    """user_id ↔ 이름 매핑 학습 저장."""
    d = load_employees()
    d.setdefault("by_telegram_id", {})[str(uid)] = name
    save_employees(d)


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
# 대표 전용 (최원석)
_MEETING_ALLOWED = {8123576679}

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

판정 기준 한 줄: **"제3자가 이 보고만 보고 다음 액션이나 의사결정을 할 수 있는가?"**
가능하면 통과(질문 0개), 불가능하게 만드는 부실 슬롯만 질문.

규칙:
- 질문은 **최대 1개**. 부실 슬롯이 여럿이어도 "제3자가 다음 의사결정을 가장 못 하게
  만드는 단 하나"만 고른다. 충분하면 빈 배열 [] (피로 최소화).
- 우선순위: 중요·고난도 업무의 핵심(Output·Outcome·Decision) 누락 > 사소한 업무.
- 평가·코칭·지적 금지. 사고를 비추는 질문만.
  예) "그 조사로 무엇을 발견했나요?" / "그게 이 프로젝트에 어떤 의미인가요?" /
      "그 업무의 구체적 산출물은 무엇인가요?" / "대표가 무엇을 결정해주면 되나요?"
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
- decision_needed: 대표·팀장이 결정해야 할 것 (없으면 "")
- decision: decision_needed가 있을 때만 그것을 구조화(Engine D). decision_needed가 ""이면 모두 "".
    project        = 어느 프로젝트/업무에 대한 결정인가 (core_tasks의 category/task에서. 불명확하면 "")
    decision_type  = 결정의 성격 한 단어 (positioning/budget/priority/direction/hiring/approval/scope 등)
    urgency        = high / medium / low (셋 중 하나)
    related_output = 이 결정과 연결된 산출물 (core_tasks의 output에서. 없으면 "")
  **추측 금지** — 원본에 근거가 없으면 각 필드를 "" 로 둬라.
- support_needed: 직원이 필요로 하는 지원 (블로커와 구분. 없으면 "")
- reflection: 보고 품질에 대한 '관찰'(평가가 아니라 거울).
    good   = 오늘 보고에서 잘 설명된 점
    missing= 다음에 더하면 좋을 점(부드럽게)
    next   = 다음 보고 때 보완하면 좋을 포인트 한 가지
  따뜻하고 담담한 어조. 지적하지 말 것.

반드시 JSON만 출력:
{"outcomes": ["", ""], "decision_needed": "",
 "decision": {"project": "", "decision_type": "", "urgency": "", "related_output": ""},
 "support_needed": "",
 "reflection": {"good": "", "missing": "", "next": ""}}"""

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
    answer = call_gpt_text(prompt, text)
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
    """팀원 일일보고 정리본을 해당 팀 리더에게 직원봇으로 공유. 전송 성공 건수 반환."""
    team = report.get("team", "")
    leader_ids = team_leader_chat_ids(team, report.get("name", ""))
    sent = 0
    for lid in leader_ids:
        share = f"👥 [팀원 일일보고 공유 · {team}]\n\n{manager_msg}"
        # 리더는 직원봇(BOT_TOKEN)에 연결돼 있으므로 직원봇으로 발신
        if _tg_send(BOT_TOKEN, lid, share):
            sent += 1
    return sent


def save_to_sheet(report_data: dict) -> bool:
    """구글시트에 저장 (GWS CLI)."""
    try:
        d = report_data
        for ct in d.get("core_tasks", []):
            # outcome은 기존 11컬럼 뒤(12번째)에 추가 — 기존 데이터 정합 유지
            row = [d["date"], d["name"], d["team"], d["role"],
                   ct.get("category", ""), ct.get("task", ""), ct.get("status", ""),
                   ct.get("process", ""), ct.get("tools", ""), ct.get("output", ""),
                   ct.get("issues", ""), ct.get("outcome", "")]
            _gws.append_to_sheet(SHEET_ID, "핵심업무!A1", row, value_input_option="RAW", timeout=15)

        for st in d.get("sub_tasks", []):
            row = [d["date"], d["name"], d["team"], st.get("category", ""), st.get("task", ""), st.get("status", "")]
            _gws.append_to_sheet(SHEET_ID, "서브업무!A1", row, value_input_option="RAW", timeout=15)

        attach_cell = "\n".join(
            f"{a['name']}: {a['link']}" for a in d.get("attachments", [])
        )
        refl = d.get("reflection") or {}
        reflection_cell = "\n".join(
            f"{k}: {refl[k]}" for k in ("good", "missing", "next") if refl.get(k)
        )
        row = [d["date"], d["name"], d["team"], d.get("tomorrow", ""), d.get("improvement", ""),
               d.get("blockers", ""), attach_cell,
               d.get("decision_needed", ""), d.get("support_needed", ""), reflection_cell,
               d.get("raw", ""),  # fidelity: 직원 원문 보존(K열)
               d.get("key_question", "")]  # 3.0 질문보고: 오늘의 질문(L열)
        _gws.append_to_sheet(SHEET_ID, "메타!A1", row, value_input_option="RAW", timeout=15)

        return True
    except Exception as e:
        logger.error(f"Sheet save error: {e}")
        return False


def upload_to_drive(local_path: Path, display_name: str) -> str | None:
    """텔레그램에서 받은 파일을 구글드라이브에 업로드 → 공유 링크 반환."""
    try:
        result = subprocess.run(
            ["gws", "drive", "+upload", str(local_path),
             "--parent", DRIVE_FOLDER_ID, "--name", display_name],
            capture_output=True, timeout=60, text=True,
        )
        if result.returncode != 0:
            logger.error(f"Drive upload failed: {result.stderr}")
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
    import re
    return re.sub(r"\s+", "", s or "")


_DUMMY_PROCESS = {"시작→중간→결과", "시작->중간->결과", "시작중간결과", "시작→진행→완료"}


def _rule_based_gaps(report: dict) -> list[str]:
    """규칙 기반 부실 슬롯 탐지 (LLM이 놓치는 확실한 더미/동어반복 안전망)."""
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
    return gaps


def completion_check(report: dict) -> list[str]:
    """Engine B: 부실 슬롯을 짚어 '단 하나'의 질문만 반환 (규칙 + LLM 혼합, 없으면 빈 리스트)."""
    # 규칙 기반(확실한 더미/동어반복)을 우선 — LLM 실패에도 작동하는 안전망
    rule_qs = _rule_based_gaps(report)

    llm_qs = []
    result = call_gpt(COMPLETION_CHECK_PROMPT, _report_digest(report))
    if result and "questions" in result:
        llm_qs = [q for q in result["questions"] if isinstance(q, str) and q.strip()]

    # 병합 + 중복 제거(정규화 기준), 규칙 질문 우선
    merged, seen = [], set()
    for q in rule_qs + llm_qs:
        key = _norm(q)
        if key and key not in seen:
            seen.add(key)
            merged.append(q)
    return merged[:1]  # 질문 폭탄 금지 — 한 번에 하나만(가장 우선되는 슬롯)


def structure_report(report: dict, completion_answers: str = "") -> None:
    """Engine C: Outcome/Decision/Support/Reflection을 채워 report를 in-place 보강."""
    user_msg = (
        f"원본 보고(JSON):\n{json.dumps(report, ensure_ascii=False)}\n\n"
        f"보완 답변:\n{completion_answers or '(없음)'}"
    )
    structured = call_gpt(STRUCTURE_PROMPT, user_msg)
    if not structured:
        return

    outcomes = structured.get("outcomes", [])
    for i, oc in enumerate(outcomes):
        if i < len(report["core_tasks"]) and isinstance(oc, str):
            report["core_tasks"][i]["outcome"] = oc.strip()

    report["decision_needed"] = (structured.get("decision_needed") or "").strip()
    dec = structured.get("decision")
    if isinstance(dec, dict):
        report["decision"] = dec  # Engine D: 구조화 메타(project/type/urgency/related_output)
    report["support_needed"] = (structured.get("support_needed") or "").strip()
    refl = structured.get("reflection")
    if isinstance(refl, dict):
        report["reflection"] = refl


def format_report_for_manager(d: dict) -> str:
    """대표·관리자용 7섹션 보고서 (의사결정 중심)."""
    lines = [f"📋 일일 업무보고 — {d['name']} ({d['team']})", f"📅 {d['date']}", ""]

    lines.append("■ 핵심 업무 (Task → Output → Outcome)")
    for i, ct in enumerate(d.get("core_tasks", []), 1):
        lines.append(f"{i}. [{ct['category']}] {ct['task']} — {ct['status']}")
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
    """Engine C 실행 → 직원 회신(거울) + 관리자 전송 + 시트 저장."""
    structure_report(report, completion_answers)

    employee_msg = format_report_for_employee(report)
    manager_msg = format_report_for_manager(report)

    # 1) 직원 본인에게 정리본 + Reflection 회신 (거울 학습 루프 — MVP1 핵심)
    await update.message.reply_text(employee_msg)

    # 2) 관리자(대표) 전송 + 팀 리더 공유 + 시트 저장
    sent = send_to_manager(manager_msg)
    leader_sent = share_to_team_leader(report, manager_msg)
    saved = save_to_sheet(report)
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
    status_lines.append("💾 구글시트 저장 완료!" if saved else "⚠️ 시트 저장 실패")
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

    result = call_gpt(CATEGORIZE_PROMPT, text)
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

    # 의도 판단
    intent = detect_intent(text)

    if intent == "question":
        return await handle_question(update, context, WAITING_CONFIRM)

    if text.lower() in ("맞아", "확인", "네", "ㅇㅇ", "응", "ok", "ㅇ", "맞음", "넵"):
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
                "어떻게 시작됐고, 어떤 순서로 진행했고,\n"
                "결과물이 뭔지, 사용한 도구가 있는지\n"
                "편하게 말씀해주세요!"
            )
            return WAITING_DRILLDOWN
    else:
        # 수정/추가 처리
        original = "\n".join([t["task"] for t in context.user_data.get("all_tasks", [])])
        result = call_gpt(CATEGORIZE_PROMPT, f"기존 업무:\n{original}\n\n수정/추가 사항:\n{text}")
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

    # 의도 판단
    intent = detect_intent(text)

    if intent == "question":
        return await handle_question(update, context, WAITING_DRILLDOWN)

    core_indices = context.user_data.get("core_indices", [0])
    current_idx = context.user_data.get("current_core_idx", 0)
    all_tasks = context.user_data.get("all_tasks", [])

    task_name = all_tasks[core_indices[current_idx]]["task"] if core_indices[current_idx] < len(all_tasks) else ""
    context.user_data.setdefault("raw_log", []).append(f"[상세: {task_name}] {text}")
    detail = call_gpt(DRILLDOWN_PROMPT, f"업무: {task_name}\n상세 설명: {text}")

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

    # 의도 판단
    intent = detect_intent(text)

    if intent == "question":
        return await handle_question(update, context, WAITING_ISSUES)

    if text.lower() in ("없어", "없음", "없었어", "없었어요", "ㄴㄴ", "노", "no"):
        context.user_data["blockers"] = ""
    else:
        context.user_data["blockers"] = text

    await update.message.reply_text(
        "마지막! 내일 이어갈 일이나 우선순위가 있으면 알려주세요.\n"
        "없으면 '없어' 라고 해주세요!"
    )
    return WAITING_TOMORROW


async def receive_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()

    # 의도 판단
    intent = detect_intent(text)

    if intent == "question":
        return await handle_question(update, context, WAITING_TOMORROW)

    if text.lower() in ("없어", "없음", "없었어", "ㄴㄴ"):
        context.user_data["tomorrow"] = ""
    else:
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

    # 보고 도중 되묻는 질문이면 답해주고 같은 단계 유지
    if detect_intent(text) == "question":
        return await handle_question(update, context, WAITING_QUESTION)

    if text.lower() in ("없어", "없음", "없었어", "ㄴㄴ", "패스", "스킵", "pass", "skip"):
        context.user_data["key_question"] = ""
    else:
        context.user_data["key_question"] = text
        # fidelity: 직원의 질문 원문도 보존 (assemble_report가 raw_log → raw로 합침)
        context.user_data.setdefault("raw_log", []).append(f"[오늘의 질문] {text}")

    # 보고 조립
    report = assemble_report(context.user_data)

    # Engine B: 보고가 충분한지 거울로 비춰보고, 부족하면 '가장 중요한 단 하나'만 질문
    await update.message.reply_text("오늘 보고를 정리하고 있어요... ⏳")
    questions = completion_check(report)

    if not questions:
        # 충분 → 바로 마무리 (피로 최소화)
        return await finalize_and_send(update, context, report, "")

    # 부족 → 질문 폭탄 금지: 딱 하나만 묻고 답변 대기
    context.user_data["pending_report"] = report
    await update.message.reply_text(
        "거의 다 됐어요! 딱 하나만 더 여쭤볼게요 🙂\n\n"
        f"{questions[0]}\n\n"
        "편하게 답해주세요. (생각 안 나면 '패스'라고 해도 돼요)"
    )
    return WAITING_COMPLETION


async def receive_completion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Engine B 보완 질문에 대한 답변 → Engine C로 최종 정리 후 전송."""
    text = update.message.text.strip()

    # 보고 도중 되묻는 질문이면 답해주고 같은 단계 유지
    if detect_intent(text) == "question":
        return await handle_question(update, context, WAITING_COMPLETION)

    report = context.user_data.get("pending_report")
    if not report:
        # 안전장치: 세션이 유실되면 재조립
        report = assemble_report(context.user_data)

    answers = "" if text.lower() in ("패스", "스킵", "없어", "없음", "pass", "skip") else text
    if answers:  # fidelity: 보완 답변도 원문 보존
        report["raw"] = (report.get("raw", "") + f"\n[보완답변] {answers}").strip()
    await update.message.reply_text("반영해서 정리할게요... ⏳")
    return await finalize_and_send(update, context, report, answers)


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

    # 3) 구글드라이브 업로드
    link = upload_to_drive(local_path, display_name)
    local_path.unlink(missing_ok=True)  # 임시파일 정리

    if not link:
        await msg.reply_text("⚠️ 파일 저장에 실패했어요. 잠시 후 다시 보내주세요!")
        return

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

    import asyncio
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
        subprocess.run([
            "gws", "sheets", "spreadsheets", "values", "append",
            "--params", json.dumps({
                "spreadsheetId": SHEET_ID,
                "range": "회의록!A1",
                "valueInputOption": "RAW",
                "insertDataOption": "INSERT_ROWS",
            }),
            "--json", json.dumps({"values": [row]}),
        ], capture_output=True, timeout=15)
        return True
    except Exception as e:
        logger.error(f"Meeting meta save error: {e}")
        return False


async def cancel_meeting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("mtg", None)
    await update.message.reply_text("회의록 처리를 취소했습니다.")
    return ConversationHandler.END


# === /assign 핸들러 (주간 업무분장 간편 추가) ===

_ASSIGN_TEAMS = ["기획팀", "공간팀", "사업기획", "운영팀", "경영"]

ASSIGN_PARSE_PROMPT = """주간 업무분장 항목을 파싱해라. 입력에서 팀/업무내용/담당자/마감을 추출.
담당자는 이름만(님 제거). 마감은 요일이면 이번 주 날짜(YYYY-MM-DD)로 변환.
우선순위: "최우선"/"긴급"/"!!" → "최우선", "참고"/"FYI" → "참고", 나머지 → "일반".

오늘 날짜: {today}

반드시 JSON만 출력:
{{"team": "팀명", "task": "업무내용", "assignee": "담당자이름 또는 빈문자열", "deadline": "YYYY-MM-DD 또는 빈문자열", "priority": "최우선|일반|참고"}}"""


def _week_label() -> str:
    """현재 ISO 주차 라벨 (W27 등)."""
    now = datetime.now()
    return f"W{now.isocalendar().week:02d}"


def save_assignment_to_sheet(team: str, task: str, assignee: str,
                              deadline: str, priority: str) -> bool:
    """주간분장 탭에 1행 등록."""
    row = [
        _week_label(), team, "", task, assignee or "팀",
        deadline, priority, "미착수",
        datetime.now().strftime("%Y-%m-%d"), "bot",
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
        parsed = call_gpt(
            ASSIGN_PARSE_PROMPT.format(today=datetime.now().strftime("%Y-%m-%d")),
            oneline,
        )
        if parsed and parsed.get("task"):
            context.user_data["assign"]["parsed"] = parsed
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
            await update.message.reply_text(
                f"✅ 파싱 결과:\n"
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

    parsed = call_gpt(
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
        parsed = call_gpt(
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
        p.get("priority", "일반"),
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
        fallbacks=[CommandHandler("cancel", cancel)],
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

    app.add_error_handler(error_handler)  # 핸들러 예외 안전망 (보고 유실 방지)

    logger.info("Daily Report Bot v2 started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
