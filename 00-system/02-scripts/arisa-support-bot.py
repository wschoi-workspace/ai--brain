#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""알군(R) — 조회·질의 전담 봇 (2026-08-09).

## 왜 분리했나

아리사(분장·보고)는 8단계 대화 상태를 쓴다. 상태가 열려 있는 동안 그 사람의 모든
텍스트를 그 단계가 가져간다. 그래서 8/3에 `report` 직후 "봉은사 어떻게 돼가?"가
업무 내용으로 저장됐고, 그 세션이 6일간 갇혀 있었다. 라우터에 도달조차 못 했다.

경계는 곧 상태의 유무다:
  아리사   — 분장 → 보고 → 완료 환류. 여러 턴을 주고받는 흐름 (상태 필요)
  알군(R)  — 물으면 답하고 끝                                (상태 불필요)

## 이 파일의 계약

    **ConversationHandler를 만들지 않는다.**

여기에 상태를 들이는 순간 분리한 이유가 사라진다. 여러 턴이 필요한 기능이 생기면
그건 아리사 소관이거나, 버튼(콜백)으로 풀어야 한다.

## 재사용

새로 짓는 로직은 없다. `shared/policy_docs.py`(규정 QA)와
`shared/assistant_tools.py`(대시보드 API)를 그대로 쓴다.
mem0는 **쓰지 않는다** — 맥미니 전역 lock 충돌로 기존 봇들의 기억 기능이 죽은 전례가 있다.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (Application, ApplicationBuilder, CommandHandler,
                          ContextTypes, MessageHandler, filters)

WS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

for _envp in (WS / ".env", Path.home() / "arisa-project-memory" / ".env"):
    if _envp.exists():
        load_dotenv(_envp)

from shared.logging import TokenRedactingFilter  # noqa: E402
from shared import intent_router as _IR  # noqa: E402
from shared import policy_docs as _policy  # noqa: E402
from shared.assistant_tools import AssistantTools, ToolError  # noqa: E402
from shared.employee import EmployeeRegistry  # noqa: E402

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger().addFilter(TokenRedactingFilter())
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("ARISA_SUPPORT_BOT_TOKEN", "")
ARISA_USERNAME = os.environ.get("ARISA_BOT_USERNAME", "Dailywork_report_bot")
API_BASE = os.environ.get("ARISA_API_BASE") or "http://127.0.0.1:8780"

_EMP = EmployeeRegistry()

# 퇴사자 차단 — 아리사와 **같은 파일·같은 구조**를 본다.
# 스키마: {이름: {date, telegram_ids: [...], ...}}  (/퇴사처리 offboard-employee.py가 기록)
# ⚠️ 판정 로직을 여기 복제한 것은 daily-report-bot의 것이 모듈이 아니라 봇 내부 함수이기 때문이다.
#    구조가 바뀌면 양쪽을 같이 고쳐야 한다 — 나중에 shared/offboard.py로 빼는 게 맞다.
_OFFBOARD_PATH = Path(__file__).resolve().parent / "offboarded.json"
_OFFBOARDED_MSG = "퇴사 처리된 계정입니다. 문의가 필요하면 회사 대표 연락처로 연락해주세요."


def _is_offboarded(uid) -> bool:
    try:
        import json
        ob = json.loads(_OFFBOARD_PATH.read_text(encoding="utf-8"))
    except Exception:
        return False  # 파일이 없으면 차단하지 않는다(아리사와 동일)
    s = str(uid)
    return any(s in [str(x) for x in (v.get("telegram_ids") or [])]
               for v in ob.values() if isinstance(v, dict))


def _who(update: Update) -> tuple[int, str]:
    """텔레그램 ID → (uid, 직원명). 명부에 없으면 표시 이름."""
    uid = update.effective_user.id
    e = _EMP.by_telegram_id(uid)
    return uid, (e["name"] if e else (update.effective_user.full_name or str(uid)))


def _tools(uid, name) -> AssistantTools:
    return AssistantTools(uid, name=name, base_url=API_BASE)


# ── 포매터 (아리사에서 이관) ────────────────────────────────
def _fmt_projects(d: dict) -> str:
    ps = [p for p in (d.get("projects") or []) if not p.get("archived")]
    lines = [f"🗂 볼 수 있는 프로젝트 {len(ps)}개"]
    for p in ps[:15]:
        r = p.get("rollup") or {}
        pct = r.get("percent")
        lines.append(f"· {p.get('name','')}"
                     + (f" — {pct}% ({r.get('done',0)}/{r.get('total',0)})" if r.get("total") else "")
                     + (f" / PM {p['pm']}" if p.get("pm") else ""))
    if len(ps) > 15:
        lines.append(f"… 외 {len(ps)-15}개")
    return "\n".join(lines)


def _fmt_brief(d: dict) -> str:
    b = d.get("brief") or {}
    body = b.get("headline") or b.get("summary") or ""
    if not body:
        import json
        body = json.dumps(b, ensure_ascii=False)[:1200]
    return f"📨 {d.get('date','')} 브리프\n\n{body}"


def _fmt_meeting_summary(r: dict) -> str:
    if not r:
        return "요약 결과를 받지 못했습니다."
    md = r.get("metadata") or {}
    out = [f"📝 {r.get('title_guess') or md.get('meeting_name') or '회의 요약'}"
           + (f"  [{md.get('type_label')}]" if md.get("type_label") else "")]
    if md.get("date"):
        out.append(f"일시: {md['date']}")
    para = (r.get("block_2_summary") or {}).get("paragraph")
    if para:
        out.append(f"\n{para}")
    if r.get("block_4_decisions"):
        out.append("\n✅ 결정")
        out += [f"· {d.get('decision','')}" for d in r["block_4_decisions"][:8]]
    ours = ((r.get("block_5_todos") or {}).get("ours")) or []
    if ours:
        out.append("\n📌 우리 할 일")
        out += [f"· {t.get('task','')}"
                + (f" — {t['assignee']}" if t.get("assignee") else "")
                + (f" (~{t['due']})" if t.get("due") else "") for t in ours[:12]]
    if r.get("quality_note"):
        out.append(f"\n⚠️ {r['quality_note']}")
    out.append(f"\n— 저장은 안 됐습니다. 등록은 아리사에서 → https://t.me/{ARISA_USERNAME}")
    return "\n".join(out)[:3800]


# ── 실행 ──────────────────────────────────────────────────
async def _run(update: Update, it) -> bool:
    """인텐트 실행. 처리했으면 True. **상태를 남기지 않는다.**"""
    uid, name = _who(update)
    try:
        if it.name == _IR.I_POLICY:
            await update.message.reply_text("📕 사내 규정에서 찾아볼게요…")
            q = it.slots.get("question") or (update.message.text or "")
            await update.message.reply_text(await asyncio.to_thread(_policy.ask, q))
        elif it.name == _IR.I_LEAVE_BALANCE:
            await update.message.reply_text(_policy.LEAVE_BALANCE_NOTICE)
        elif it.name == _IR.I_PROJECT:
            t = _tools(uid, name)
            await update.message.reply_text(
                _fmt_projects(await asyncio.to_thread(t.project_list)))
        elif it.name == _IR.I_BRIEF:
            t = _tools(uid, name)
            await update.message.reply_text(
                _fmt_brief(await asyncio.to_thread(t.daily_brief)))
        elif it.name == _IR.I_MEETING_SUM:
            await update.message.reply_text("📝 회의 내용으로 보입니다. 정리 중이에요… (30~60초)")
            t = _tools(uid, name)
            r = await asyncio.to_thread(t.meeting_summarize, it.slots.get("text", ""))
            await update.message.reply_text(_fmt_meeting_summary(r.get("result") or {}))
        elif it.name == _IR.I_MEETING_DOC:
            await update.message.reply_text(
                "🗂 어느 프로젝트의 회의록인지 알려주세요.\n"
                "예) \"봉은사 지난주 회의록\"\n\n"
                "프로젝트 목록은 /project 로 보실 수 있습니다.")
        else:
            return False
        return True
    except ToolError as e:
        await update.message.reply_text(f"⚠️ {e.user_message}")
        return True


HELP = (
    "안녕하세요, 알군입니다. 회사에 대해 궁금한 걸 물어보세요.\n\n"
    "그냥 물어보세요.\n"
    "· \"연차는 며칠 전에 신청해?\" → 사내 규정 원문에서 찾아 답변\n"
    "· \"봉은사 어떻게 돼가?\" → 프로젝트 현황\n"
    "· 회의 녹취를 붙여넣으면 → 회의록으로 정리\n"
    "· \"어제 브리프\" → 일일 브리프\n\n"
    f"업무보고·분장은 아리사에서 👉 https://t.me/{ARISA_USERNAME}"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if _is_offboarded(update.effective_user.id):
        await update.message.reply_text(_OFFBOARDED_MSG)
        return
    _, name = _who(update)
    await update.message.reply_text(f"{name}님, 반갑습니다.\n\n{HELP}")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP)


async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ask [질문] — 사내 규정 질의."""
    if _is_offboarded(update.effective_user.id):
        await update.message.reply_text(_OFFBOARDED_MSG)
        return
    q = " ".join(context.args or []).strip()
    if not q:
        await update.message.reply_text(
            "📕 사내 규정에 대해 물어보세요.\n\n"
            "예)\n· 연차는 며칠 전에 신청해야 하나요?\n· 야근수당은 어떻게 계산되나요?\n"
            "· 수습기간은 얼마인가요?\n· 경조휴가는 며칠 나오나요?\n\n"
            "`/ask` 없이 그냥 질문하셔도 됩니다.")
        return
    await update.message.reply_text("📕 사내 규정에서 찾아볼게요…")
    await update.message.reply_text(await asyncio.to_thread(_policy.ask, q))


async def cmd_project(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if _is_offboarded(update.effective_user.id):
        await update.message.reply_text(_OFFBOARDED_MSG)
        return
    uid, name = _who(update)
    try:
        await update.message.reply_text(
            _fmt_projects(await asyncio.to_thread(_tools(uid, name).project_list)))
    except ToolError as e:
        await update.message.reply_text(f"⚠️ {e.user_message}")


async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if _is_offboarded(update.effective_user.id):
        await update.message.reply_text(_OFFBOARDED_MSG)
        return
    uid, name = _who(update)
    try:
        await update.message.reply_text(
            _fmt_brief(await asyncio.to_thread(_tools(uid, name).daily_brief)))
    except ToolError as e:
        await update.message.reply_text(f"⚠️ {e.user_message}")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """자유 텍스트 단일 진입점. 상태가 없으므로 언제 무엇을 물어도 같게 동작한다."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not text:
        return
    if _is_offboarded(update.effective_user.id):
        await update.message.reply_text(_OFFBOARDED_MSG)
        return

    _, name = _who(update)
    it = _IR.route(text)
    logger.info(f"[router] {name}: {it.name} conf={it.confidence:.2f} src={it.source} — {it.reason}")

    # 1) 다른 봇 소관이면 링크로 넘긴다 — 막지 않고 문을 연다
    owner = _IR.owner_of(it.name)
    if owner == _IR.BOT_ARISA:
        await update.message.reply_text(
            _IR.handoff_message(it.name, owner, ARISA_USERNAME))
        return

    # 2) 내 몫 — 확신이 낮으면 되묻는다(거절하지 않는다)
    if it.needs_confirm and it.name not in (_IR.I_CHAT, _IR.I_UNKNOWN):
        await update.message.reply_text(
            f"{_IR.confirm_question(it)}\n\n맞으면 다시 한 번 구체적으로 말씀해주세요.")
        return
    if await _run(update, it):
        return

    # 3) 판별 실패 — 규정 질의를 기본값으로 두지 않는다.
    #    엉뚱한 질문에 "규정에서 못 찾음"이 나가면 봇이 고장난 것처럼 보인다.
    await update.message.reply_text(
        "무엇을 찾아드릴까요?\n\n" + HELP)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Handler exception: {context.error}")


def main() -> None:
    if not BOT_TOKEN:
        logger.error("ARISA_SUPPORT_BOT_TOKEN 이 없습니다 (.env 확인)")
        sys.exit(1)

    app: Application = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("project", cmd_project))
    app.add_handler(CommandHandler("brief", cmd_brief))
    # ⚠️ ConversationHandler를 만들지 않는다 — 이 봇의 계약이다.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)

    logger.info("알군(R) support bot started — stateless, no ConversationHandler")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
