#!/usr/bin/env python3
"""일일 업무보고 텔레그램 봇 v2

직원이 텔레그램에서 대화하면 GPT가 업무를 구조화 → 관리자에게 자동 전송 + 구글시트 저장.
v2: GPT 기반 의도 판단 — 질문/수정/답변을 구분하여 자연스러운 대화 지원.

사용법:
  python 00-system/02-scripts/daily-report-bot.py

직원 흐름:
  /start → /report → 업무 나열 → GPT가 정리 → 관리자에게 자동 전송
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# .env 로드
load_dotenv(Path.home() / "do-better-workspace" / ".env")
load_dotenv(Path.home() / "arisa-project-memory" / ".env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# === 설정 ===
BOT_TOKEN = "8892729948:AAFp6SCohuo_4CsDoDl3mE3x-lX94IcpDbg"
MANAGER_BOT_TOKEN = "8708336649:AAH1iYv8PujNZqBcG4Fo7iXeHAhAZnpyH80"
MANAGER_CHAT_ID = "8123576679"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SHEET_ID = "1izuwjWPiJfbaJZ-Ib-U_NO0_Ln1_5yRr1SIRAum-hi4"
# 결과물(첨부파일) 저장용 구글드라이브 폴더
DRIVE_FOLDER_ID = "18JLhq98zVbJps1B-AXQ0xgxWqscIBYbe"  # "일일업무보고" 폴더
# 텔레그램에서 받은 파일을 잠시 내려받을 임시 폴더
ATTACH_TMP_DIR = Path("/tmp/daily-report-attachments")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# 대화 상태
WAITING_INFO, WAITING_TASKS, WAITING_CONFIRM, WAITING_DRILLDOWN, WAITING_ISSUES, WAITING_TOMORROW = range(6)

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

DRILLDOWN_PROMPT = """직원이 핵심 업무에 대해 상세 설명했다. 아래 정보를 추출해서 JSON으로만 응답해:

{
  "process": "시작 → 중간 → 결과 형태로 프로세스 정리",
  "tools": "사용한 도구/프로그램 (없으면 빈 문자열)",
  "output": "산출물/결과물 (없으면 빈 문자열)",
  "issues": "이슈/블로커 (없으면 빈 문자열)"
}"""

# 단계별 질문 설명 (의도 판단용)
STEP_QUESTIONS = {
    WAITING_CONFIRM: "업무 목록이 맞는지 확인하거나 수정",
    WAITING_DRILLDOWN: "핵심 업무에 대해 상세하게 설명 (프로세스, 도구, 산출물)",
    WAITING_ISSUES: "오늘 막힌 부분이나 시간 많이 든 부분",
    WAITING_TOMORROW: "내일 이어갈 일이나 우선순위",
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


def send_to_manager(message: str) -> bool:
    """관리자 텔레그램으로 전송."""
    import urllib.request
    url = f"https://api.telegram.org/bot{MANAGER_BOT_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": MANAGER_CHAT_ID, "text": message}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req)
        return True
    except Exception as e:
        logger.error(f"Manager send error: {e}")
        return False


def save_to_sheet(report_data: dict) -> bool:
    """구글시트에 저장 (GWS CLI)."""
    try:
        d = report_data
        for ct in d.get("core_tasks", []):
            row = [d["date"], d["name"], d["team"], d["role"],
                   ct.get("category", ""), ct.get("task", ""), ct.get("status", ""),
                   ct.get("process", ""), ct.get("tools", ""), ct.get("output", ""), ct.get("issues", "")]
            subprocess.run([
                "gws", "sheets", "spreadsheets", "values", "append",
                "--params", json.dumps({"spreadsheetId": SHEET_ID, "range": "핵심업무!A1", "valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}),
                "--json", json.dumps({"values": [row]})
            ], capture_output=True, timeout=15)

        for st in d.get("sub_tasks", []):
            row = [d["date"], d["name"], d["team"], st.get("category", ""), st.get("task", ""), st.get("status", "")]
            subprocess.run([
                "gws", "sheets", "spreadsheets", "values", "append",
                "--params", json.dumps({"spreadsheetId": SHEET_ID, "range": "서브업무!A1", "valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}),
                "--json", json.dumps({"values": [row]})
            ], capture_output=True, timeout=15)

        attach_cell = "\n".join(
            f"{a['name']}: {a['link']}" for a in d.get("attachments", [])
        )
        row = [d["date"], d["name"], d["team"], d.get("tomorrow", ""), d.get("improvement", ""), d.get("blockers", ""), attach_cell]
        subprocess.run([
            "gws", "sheets", "spreadsheets", "values", "append",
            "--params", json.dumps({"spreadsheetId": SHEET_ID, "range": "메타!A1", "valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"}),
            "--json", json.dumps({"values": [row]})
        ], capture_output=True, timeout=15)

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


def format_report_for_manager(d: dict) -> str:
    """관리자용 정리된 보고서 생성."""
    lines = [f"📋 일일 업무보고 — {d['name']} ({d['team']})", f"📅 {d['date']}", ""]

    lines.append("■ 핵심 업무")
    for i, ct in enumerate(d.get("core_tasks", []), 1):
        lines.append(f"{i}. [{ct['category']}] {ct['task']} — {ct['status']}")
        if ct.get("process"):
            lines.append(f"   → {ct['process']}")
        if ct.get("output"):
            lines.append(f"   산출물: {ct['output']}")
        if ct.get("issues"):
            lines.append(f"   이슈: {ct['issues']}")

    if d.get("sub_tasks"):
        lines.append("")
        lines.append("■ 서브 업무")
        for st in d["sub_tasks"]:
            lines.append(f"- [{st['category']}] {st['task']} ({st['status']})")

    if d.get("blockers"):
        lines.append(f"\n■ 블로커: {d['blockers']}")
    if d.get("tomorrow"):
        lines.append(f"■ 내일: {d['tomorrow']}")
    if d.get("improvement"):
        lines.append(f"■ 개선: {d['improvement']}")

    if d.get("attachments"):
        lines.append("\n■ 첨부 산출물")
        for i, a in enumerate(d["attachments"], 1):
            lines.append(f"{i}. {a['name']}\n   {a['link']}")

    return "\n".join(lines)


# === 핸들러 ===

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "안녕하세요! 업무보고 도우미입니다 📋\n\n"
        "오늘 하신 일을 편하게 얘기해주시면\n"
        "깔끔하게 정리해서 팀장님께 보내드릴게요.\n\n"
        "/report — 업무 보고 시작\n"
        "/cancel — 취소"
    )


async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["chat_history"] = []
    await update.message.reply_text(
        "업무 보고를 시작할게요!\n\n"
        "먼저, 이름 / 팀(소속) / 역할을 알려주세요.\n"
        "예) 양지혜 / 마케팅팀 / 시니어 마케터"
    )
    return WAITING_INFO


async def receive_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    parts = [p.strip() for p in text.replace(",", "/").split("/")]

    if len(parts) < 2:
        await update.message.reply_text(
            "이름과 팀은 꼭 필요해요!\n"
            "예) 양지혜 / 마케팅팀 / 시니어 마케터"
        )
        return WAITING_INFO

    context.user_data["name"] = parts[0]
    context.user_data["team"] = parts[1] if len(parts) > 1 else ""
    context.user_data["role"] = parts[2] if len(parts) > 2 else ""
    context.user_data["date"] = datetime.now().strftime("%Y-%m-%d")

    await update.message.reply_text(
        f"{parts[0]}님, 반갑습니다!\n\n"
        "오늘 하신 일을 생각나는 대로 쭉 나열해주세요.\n"
        "크든 작든 다 괜찮아요. 순서 상관없어요! 😊"
    )
    return WAITING_TASKS


async def receive_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
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

    await update.message.reply_text("보고서 정리하고 전송할게요... ⏳")

    # 최종 데이터 조립
    all_tasks = context.user_data.get("all_tasks", [])
    core_details = context.user_data.get("core_details", [])
    core_indices = set(context.user_data.get("core_indices", []))

    report = {
        "date": context.user_data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "name": context.user_data.get("name", ""),
        "team": context.user_data.get("team", ""),
        "role": context.user_data.get("role", ""),
        "core_tasks": [],
        "sub_tasks": [],
        "blockers": context.user_data.get("blockers", ""),
        "tomorrow": context.user_data.get("tomorrow", ""),
        "improvement": "",
        "attachments": context.user_data.get("attachments", []),
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
                "issues": detail.get("issues", ""),
            })
        else:
            report["sub_tasks"].append({
                "task": t["task"],
                "category": t["category"],
                "status": t["status"],
            })

    manager_msg = format_report_for_manager(report)
    sent = send_to_manager(manager_msg)
    saved = save_to_sheet(report)

    status_lines = ["✅ 업무보고 완료!\n"]
    status_lines.append(f"📊 핵심 업무 {len(report['core_tasks'])}건 + 서브 {len(report['sub_tasks'])}건 정리됨")
    if report["attachments"]:
        status_lines.append(f"📎 첨부 산출물 {len(report['attachments'])}건 함께 전송됨")
    if sent:
        status_lines.append("📨 팀장님께 전송 완료!")
    else:
        status_lines.append("⚠️ 팀장님 전송 실패 (나중에 재시도)")
    if saved:
        status_lines.append("💾 구글시트 저장 완료!")
    else:
        status_lines.append("⚠️ 시트 저장 실패")

    status_lines.append("\n수고하셨어요! 내일도 화이팅 💪")

    await update.message.reply_text("\n".join(status_lines))
    return ConversationHandler.END


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

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY가 설정되지 않았습니다.")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()

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
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(conv)

    logger.info("Daily Report Bot v2 started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
