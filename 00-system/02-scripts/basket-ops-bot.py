#!/usr/bin/env python3
"""
basket-ops-bot.py — Basket 운영팀 일일업무 보고 봇 (전용)

흐름(혼합 입력):
  운영자가 텔레그램에 자유롭게 보고 입력
   → OpenAI가 11섹션으로 구조화 + 부족/모호한 핵심만 되물음(최대 2개)
   → 운영자 보완 → 요약 확인
   → 구글 시트(일일보고 리스트)에 1행 append
   → 승인·결재 필요 건(③송금·승인 / ⑤장비 견적·AS / ⑩입점)은 매니저에게 별도 강조 전송

기존 daily-report-bot.py 패턴 재사용: python-telegram-bot · OpenAI · gws CLI Sheets append.
구글 시트 컬럼 순서 = basket-업무보고-양식.xlsx '일일보고(리스트)'와 동일(15열: store_id·날짜·작성자·매출·지출·③~⑪·업로드시각).

필요 .env:
  BASKET_BOT_TOKEN            전용 텔레그램 봇 토큰(@BotFather)
  BASKET_MANAGER_CHAT_ID      승인 알림 받을 매니저/대표 chat_id
  BASKET_REPORT_SHEET_ID      구글 시트 ID(드라이브에서 xlsx→구글시트 변환 후)
  BASKET_REPORT_SHEET_TAB     탭 이름(기본: 일일보고)
  OPENAI_API_KEY              기존 사용
실행: python3 basket-ops-bot.py  (launchd 상시가동 권장 — *.plist 참조)
"""
from __future__ import annotations
import json, logging, os, subprocess, sys, atexit
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Application, ApplicationHandlerStop, CommandHandler, MessageHandler,
                          ConversationHandler, ContextTypes, TypeHandler, filters)

# ---- 설정 ----
WORKSPACE = Path(__file__).resolve().parents[2]
ENV_PATH = WORKSPACE / ".env"

def load_env():
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
load_env()

BOT_TOKEN   = os.environ.get("BASKET_BOT_TOKEN", "")
MANAGER_ID  = os.environ.get("BASKET_MANAGER_CHAT_ID", "")
SHEET_ID    = os.environ.get("BASKET_REPORT_SHEET_ID", "")
SHEET_TAB   = os.environ.get("BASKET_REPORT_SHEET_TAB", "일일보고")
TODO_TAB    = os.environ.get("BASKET_TODO_SHEET_TAB", "TODO이행")
PROGRESS_TAB= os.environ.get("BASKET_PROGRESS_SHEET_TAB", "진행로그")
STORE_ID    = os.environ.get("BASKET_STORE_ID", "basket")
OPENAI_KEY  = os.environ.get("OPENAI_API_KEY", "")
MODEL       = os.environ.get("BASKET_BOT_MODEL", "gpt-4o-mini")
CHECKLIST_PATH = WORKSPACE / "20-operations" / "25-basket-ops-manual" / "basket-todo-checklist.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
# ARISA 공유 코어 (Phase 1) — 토큰 마스킹·gws·명부 배관 단일 출처
sys.path.insert(0, "/Users/server-mini/do-better-workspace/00-system/02-scripts")
from shared.logging import TokenRedactingFilter  # noqa: E402
from shared import gws as _gws  # noqa: E402
from shared import report_queue as _rq  # noqa: E402
from shared.employee import load_employees as _load_emp  # noqa: E402
for _h in logging.getLogger().handlers:
    _h.addFilter(TokenRedactingFilter())  # 기존엔 필터 없어 토큰 평문 노출 — 보안 개선
logger = logging.getLogger("basket-ops-bot")
client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

# 직원 명부 연동 — 텔레그램 표시이름(양은정/Yang Eun Jung 혼재)이 아니라 명부 이름으로 통일.
EMP_PATH = Path(__file__).resolve().parent / "arisa-employees.json"

def _emp_by_tid(uid) -> str:
    """텔레그램 ID로 명부 이름 조회(daily-report-bot이 학습한 by_telegram_id 공유). 없으면 ''."""
    return _load_emp(EMP_PATH).get("by_telegram_id", {}).get(str(uid), "") or ""

def _author(update) -> str:
    """보고자 이름: 명부 우선 → 텔레그램 표시이름 → '운영자'. 이름 혼재 방지."""
    u = update.effective_user
    if not u:
        return "운영자"
    return _emp_by_tid(u.id) or u.full_name or "운영자"

# 퇴사자 차단 — /퇴사처리(offboard-employee.py)가 기록하는 목록. daily-report-bot과 공유.
OFFBOARDED_PATH = Path(__file__).resolve().parent / "offboarded.json"

def _is_offboarded_tid(uid) -> bool:
    try:
        ob = json.loads(OFFBOARDED_PATH.read_text(encoding="utf-8"))
    except Exception:
        return False
    s = str(uid)
    return any(s in (v.get("telegram_ids") or []) for v in ob.values())

# 11섹션 (시트 컬럼 순서와 매핑)
SECTIONS = [
    ("sales",      "매출"),
    ("jichul",     "③ 지출 총합"),
    ("approval",   "③ 송금·승인 급한 건"),
    ("notes",      "④ 특이사항"),
    ("equipment",  "⑤ 장비"),
    ("worklog",    "⑥ 업무 보고(완료/진행/예정)"),
    ("rental",     "⑦ 대관"),
    ("staff",      "⑧ 스태프"),
    ("purchase",   "⑨ 구매"),
    ("tenant",     "⑩ 입점 제안"),
    ("reflection", "⑪ 복기(선택)"),
]
APPROVAL_KEYS = {"approval": "③ 송금·승인", "equipment": "⑤ 장비(견적·AS)", "tenant": "⑩ 입점 제안"}

WAITING_REPORT, WAITING_CLARIFY, WAITING_CONFIRM, TODO_COLLECT = range(4)

# 요일 (datetime.weekday(): 월=0 … 일=6)
WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]

def load_checklist() -> dict:
    try:
        return json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"checklist load error: {e}")
        return {}

def todo_for_day(ko: str) -> dict | None:
    """요일(ko)의 오픈/미들/마감 항목 리스트 반환. 휴무일이면 None."""
    cl = load_checklist()
    if not cl or ko not in cl.get("by_day", {}):
        return None
    com = cl["common"]; d = cl["by_day"][ko]
    return {
        "staff": d.get("staff", ""),
        "open":  com["open"]  + d.get("open_add", []),
        "mid":   com["mid"]   + d.get("mid_add", []),
        "close": com["close"] + d.get("close_add", []),
    }

def todo_text(ko: str, t: dict) -> str:
    def block(title, items): return f"*{title}*\n" + "\n".join(f"☐ {it}" for it in items)
    return (f"🗓️ *{ko}요일 TO-DO* · 근무 {t['staff']}\n\n"
            + block("■ 오픈(AM)", t["open"]) + "\n\n"
            + block("■ 미들(영업 중)", t["mid"]) + "\n\n"
            + block("■ 마감(PM)", t["close"]))

STRUCT_PROMPT = """너는 Basket 매장 운영팀의 일일보고 정리 비서다.
운영자가 자유롭게 쓴 보고를 아래 JSON 스키마로 구조화한다.
규칙: 운영자가 말한 내용만 담는다(지어내지 않음). 없으면 빈 문자열. 원문 표현을 최대한 보존한다.
'clarify'에는 보고에서 빠졌거나 모호해서 꼭 되물어야 할 핵심 질문을 0~2개만(중요한 것만) 담는다.

스키마:
{
 "sales": "매출(숫자+원, 없으면 빈 문자열)",
 "jichul": "지출 총합(숫자+원, 없으면 빈 문자열)",
 "approval": "송금·승인 등 결재 급한 건(1차 승인자 피드백 필요 건)",
 "notes": "특이사항",
 "equipment": "장비(고장·수리·설치·견적·AS)",
 "worklog": "업무 보고(완료/진행/예정)",
 "rental": "대관(문의·일정·인원·금액·회신)",
 "staff": "스태프(근태·계약·추가근무·면접)",
 "purchase": "구매(비품·상품, 고위드/법인카드 상태)",
 "tenant": "입점 제안(테스트·일정·대표 피드백)",
 "reflection": "복기(오늘 손님이 멈춘 곳/반복한 말/내일 바꿀 것 — 있으면)",
 "clarify": ["되물을 질문1", "되물을 질문2"]
}
JSON만 출력."""

def gpt_structure(text: str, prev: dict | None = None) -> dict:
    if not client:
        return {"notes": text, "clarify": []}
    user = text if not prev else f"[1차 보고]\n{prev.get('_raw','')}\n\n[보완 답변]\n{text}"
    try:
        resp = client.chat.completions.create(
            model=MODEL, temperature=0.2,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": STRUCT_PROMPT},
                      {"role": "user", "content": user}],
        )
        data = json.loads(resp.choices[0].message.content)
        data["_raw"] = (prev.get("_raw", "") + "\n" + text) if prev else text
        return data
    except Exception as e:
        logger.error(f"GPT structure error: {e}")
        return (prev or {}) | {"notes": text, "clarify": []}

def _basket_append(tab: str, row: list, dedup_cols: list, author: str = "") -> bool:
    """append + 실패 시 로컬 큐 보관(백필 배치가 자동 재시도). 유실 방지 단일 경로."""
    ok, kind = _gws.append_to_sheet_ex(SHEET_ID, f"{tab}!A1", row,
                                       value_input_option="USER_ENTERED", timeout=20)
    if not ok:
        key = f"{datetime.now().strftime('%Y-%m-%d')}|{author or STORE_ID}"
        _rq.enqueue([_rq.make_entry("basket", SHEET_ID, f"{tab}!A1", row, key,
                                    dedup_cols, vio="USER_ENTERED", last_error=kind)])
    return ok

def append_sheet(row: list) -> bool:
    return _basket_append(SHEET_TAB, row, [1, 2, 14], author=str(row[2]) if len(row) > 2 else "")

def build_row(d: dict, author: str) -> list:
    now = datetime.now()
    return [
        STORE_ID, now.strftime("%y%m%d"), author, d.get("sales",""), d.get("jichul",""), d.get("approval",""),
        d.get("notes",""), d.get("equipment",""), d.get("worklog",""), d.get("rental",""),
        d.get("staff",""), d.get("purchase",""), d.get("tenant",""), d.get("reflection",""),
        now.strftime("%H:%M"),
    ]

def _md(s) -> str:
    """레거시 Markdown 안전 이스케이프(동적 텍스트용) — 사용자/LLM 내용의 _ * ` [ 로 인한
    Telegram 400(파싱 실패→메시지 조용히 유실)을 방지. 정적 볼드 라벨은 이스케이프하지 않는다."""
    s = str(s or "")
    for ch in ("\\", "_", "*", "`", "["):
        s = s.replace(ch, "\\" + ch)
    return s


def summary_text(d: dict, author: str) -> str:
    lines = [f"📋 *{datetime.now():%y%m%d} 일일보고* — {_md(author)}", ""]
    for key, label in SECTIONS:
        v = (d.get(key) or "").strip()
        if v:
            lines.append(f"*{label}*\n{_md(v)}")
    return "\n".join(lines) if len(lines) > 2 else "내용이 비어 있습니다."

def _trunc(s: str, n: int) -> str:
    s = (s or "").strip()
    return s[:n] + "…" if len(s) > n else s

def daily_summary(d: dict, author: str) -> str:
    """제출 완료 → 대표 푸시용 일일보고 요약 (매출·결재필요·업무·특이)."""
    L = [f"🧺 *Basket 일일보고* {datetime.now():%y%m%d} · {_md(author)}", ""]
    if (d.get("sales") or "").strip():
        sales = d["sales"].strip()
        L.append("💰 매출 " + _md(sales) + ("원" if sales[-1:].isdigit() else ""))
    appr = [f"• {label}: {_md(d.get(key).strip())}" for key, label in APPROVAL_KEYS.items() if (d.get(key) or "").strip()]
    if appr:
        L += ["", "🔔 *결재 필요*"] + appr
    if (d.get("worklog") or "").strip():
        L += ["", "📌 *업무*\n" + _md(_trunc(d["worklog"], 240))]
    if (d.get("notes") or "").strip():
        L.append("📍 *특이*\n" + _md(_trunc(d["notes"], 180)))
    return "\n".join(L)


# ---- 텔레그램 핸들러 ----
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧺 Basket 운영 봇입니다.\n"
        "• 오늘 업무를 편하게 쭉 적으면 → 일일보고로 정리·기록합니다.\n"
        "• /jot 내용 — 낮에 짬짬이 진행상황을 빠르게 기록(웹앱이 모아 보고로 구성).\n"
        "• /todo — 오늘 요일의 TO-DO 체크리스트를 띄웁니다.\n"
        "(지출·장비·대관·스태프·구매·입점·특이사항 등 생각나는 대로 적어 주세요)")
    return WAITING_REPORT

async def recv_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text("정리 중…")
    d = gpt_structure(text)
    ctx.user_data["d"] = d
    clarify = [q for q in (d.get("clarify") or []) if q][:2]
    if clarify:
        ctx.user_data["clarify"] = clarify
        msg = "몇 가지만 확인할게요:\n" + "\n".join(f"– {q}" for q in clarify) + "\n\n한 번에 답해 주세요. (없으면 '없음')"
        await update.message.reply_text(msg)
        return WAITING_CLARIFY
    return await show_confirm(update, ctx)

async def recv_clarify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ans = update.message.text.strip()
    if ans and ans not in ("없음", "없어요", "-"):
        ctx.user_data["d"] = gpt_structure(ans, prev=ctx.user_data.get("d"))
    return await show_confirm(update, ctx)

async def show_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = ctx.user_data["d"]
    author = _author(update)
    ctx.user_data["author"] = author
    kb = ReplyKeyboardMarkup([["✅ 등록", "✏️ 다시"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(summary_text(d, author), parse_mode="Markdown", reply_markup=kb)
    return WAITING_CONFIRM

async def recv_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if "다시" in choice:
        await update.message.reply_text("다시 적어 주세요.", reply_markup=ReplyKeyboardRemove())
        return WAITING_REPORT
    # 확인 버튼("✅ 등록")이 아닌 자유 텍스트는 '수정 의도'로 보고 새 내용으로 재구조화(옛 구조 저장 방지)
    if not ("등록" in choice or "✅" in choice or choice.lower() in ("ok", "확인", "저장", "네", "넵", "응")):
        return await recv_report(update, ctx)
    d = ctx.user_data["d"]; author = ctx.user_data.get("author", "운영자")
    # 빈 행 가드: 실제 보고 섹션이 전부 비거나(빈 입력·GPT 구조화 실패) 무의미 토큰뿐이면 저장하지 않는다.
    _TRIVIAL = {"기록완료", "완료", "끝", "기록", "없음", "없습니다", "done", "ok", "오케이", "넵", "네"}
    if not any((d.get(k) or "").strip() and (d.get(k) or "").strip() not in _TRIVIAL for k, _ in SECTIONS):
        await update.message.reply_text(
            "보고 내용이 비어 있어 저장하지 않았어요 🙏 오늘 한 일을 적어 다시 보내주세요.",
            reply_markup=ReplyKeyboardRemove())
        ctx.user_data.clear()
        return ConversationHandler.END
    ok = append_sheet(build_row(d, author))
    # 대표에게 일일보고 요약 푸시
    if MANAGER_ID:
        try:
            summary = daily_summary(d, author)
            if not ok:
                summary += "\n⚠️ 시트 저장 실패 → 로컬 큐 보관, 자동 재시도 예정"
            await ctx.bot.send_message(chat_id=MANAGER_ID, text=summary, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"manager summary fail: {e}")
    msg = "✅ 일일보고 등록 완료." + ("" if ok else " (⚠️ 시트 저장 지연 — 자동 재시도 예정, 다시 보내실 필요 없어요)")
    if MANAGER_ID:
        msg += "\n📤 요약을 대표에게 전달했습니다."
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    ctx.user_data.clear()
    return ConversationHandler.END

# ---- /jot (낮 동안 짬짬이 진행로그) ----
def append_progress(author: str, text: str) -> bool:
    now = datetime.now()
    row = [STORE_ID, now.strftime("%y%m%d"), now.strftime("%H:%M"), author, text]
    return _basket_append(PROGRESS_TAB, row, [1, 2, 3], author=author)

async def cmd_jot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").partition(" ")[2].strip()
    if not text:
        await update.message.reply_text("사용법: /jot 다음에 진행상황을 적어주세요.\n예) /jot 오전 발주 완료, 사진전 대관 회신대기")
        return
    author = _author(update)
    ok = append_progress(author, text)
    await update.message.reply_text("📝 진행 기록됨" + ("" if ok else " (⚠️ 시트 저장 지연 — 자동 재시도 예정)"))


# ---- /todo (요일별 체크리스트) ----
def log_todo(ko: str, author: str, incomplete: str) -> bool:
    now = datetime.now()
    row = [now.strftime("%y%m%d"), ko, author, incomplete, now.strftime("%H:%M")]
    return _basket_append(TODO_TAB, row, [0, 2, 4], author=author)

async def cmd_todo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ko = WEEKDAY_KO[datetime.now().weekday()]
    t = todo_for_day(ko)
    if t is None:
        await update.message.reply_text(f"오늘({ko}요일)은 휴무일입니다. (운영: 월~토)")
        return ConversationHandler.END
    ctx.user_data["todo_ko"] = ko
    await update.message.reply_text(todo_text(ko, t), parse_mode="Markdown")
    await update.message.reply_text(
        "위 체크리스트대로 진행해 주세요.\n완료했으면 *완료*, 못 한 항목·이슈가 있으면 적어 주세요.",
        parse_mode="Markdown")
    return TODO_COLLECT

async def recv_todo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ans = update.message.text.strip()
    ko = ctx.user_data.get("todo_ko", WEEKDAY_KO[datetime.now().weekday()])
    author = _author(update)
    incomplete = "" if ans in ("완료", "끝", "다 했어요", "완료요") else ans
    ok = log_todo(ko, author, incomplete)
    msg = "✅ 체크 완료 기록." if not incomplete else "✅ 기록 완료 — 미완료/이슈 접수했습니다."
    if not ok:
        msg += " (⚠️ 시트 저장 지연 — 자동 재시도 예정)"
    # 미완료에 이슈가 있으면 매니저에 알림
    if incomplete and MANAGER_ID:
        try:
            await ctx.bot.send_message(chat_id=MANAGER_ID,
                text=f"📌 *{ko}요일 TO-DO 미완료/이슈* ({author})\n{incomplete}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"todo alert fail: {e}")
    await update.message.reply_text(msg)
    ctx.user_data.clear()
    return ConversationHandler.END

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("취소했습니다.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def on_error(update, ctx):
    logger.error(f"update error: {ctx.error}")

# 모든 메시지의 chat_id 등록(향후 DM 발송용). 다른 핸들러 비차단(group=-1).
CHAT_REG = Path(__file__).resolve().parent / ".basket-chats.json"
async def log_chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # group=-1 선행 핸들러 — 퇴사자면 여기서 전체 파이프라인 중단 (단일 차단 지점)
    u0 = update.effective_user
    if u0 and _is_offboarded_tid(u0.id):
        if update.message:
            await update.message.reply_text("퇴사 처리된 계정입니다.")
        raise ApplicationHandlerStop
    try:
        c = update.effective_chat; u = update.effective_user
        if not c or c.type != "private":
            return
        reg = json.loads(CHAT_REG.read_text(encoding="utf-8")) if CHAT_REG.exists() else {}
        reg[str(c.id)] = (u.full_name if u else "") or ""
        CHAT_REG.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as e:
        logger.error(f"chat reg error: {e}")


def main():
    if not BOT_TOKEN:
        sys.exit("BASKET_BOT_TOKEN 미설정 — .env에 전용 봇 토큰을 넣어주세요.")
    # 중복 실행 방지
    lock = Path("/tmp/basket-ops-bot.pid")
    if lock.exists():
        try:
            os.kill(int(lock.read_text()), 0); sys.exit("이미 실행 중")
        except (OSError, ValueError):
            pass
    lock.write_text(str(os.getpid())); atexit.register(lambda: lock.exists() and lock.unlink())

    app = Application.builder().token(BOT_TOKEN).build()
    todo_conv = ConversationHandler(
        entry_points=[CommandHandler("todo", cmd_todo)],
        states={TODO_COLLECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_todo)]},
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )
    app.add_handler(TypeHandler(Update, log_chat), group=-1)
    app.add_handler(todo_conv)
    app.add_handler(CommandHandler("jot", cmd_jot))
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start),
                      CommandHandler("report", cmd_start),
                      MessageHandler(filters.TEXT & ~filters.COMMAND, recv_report)],
        states={
            WAITING_REPORT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_report)],
            WAITING_CLARIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_clarify)],
            WAITING_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )
    app.add_handler(conv)
    app.add_error_handler(on_error)
    logger.info("Basket 운영 일일보고 봇 시작")
    # drop_pending_updates=False: 슬립/재시작 동안 쌓인 보고·명령을 깨어난 뒤 빠짐없이 처리.
    # (Telegram이 미확정 update를 최대 24h 보관 → 마지막 offset부터 재수신)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=False)


if __name__ == "__main__":
    main()
