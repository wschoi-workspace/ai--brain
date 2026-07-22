"""
텔레그램 인박스 수집 봇
텔레그램에서 보낸 링크, 메모, 파일을 자동으로 inbox.jsonl에 저장.
Claude Code에서 "인박스 정리해줘"로 정리/분류/메모리 저장.
"""

import os
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_IDS = os.getenv("ALLOWED_USER_IDS", "")

# 인박스 파일 경로
INBOX_FILE = Path(__file__).parent / "inbox.jsonl"

# 허용된 사용자 ID 파싱
allowed_ids: set[int] = set()
if ALLOWED_USER_IDS.strip():
    for uid in ALLOWED_USER_IDS.split(","):
        uid = uid.strip()
        if uid.isdigit():
            allowed_ids.add(int(uid))

# URL 패턴
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')


def is_allowed(user_id: int) -> bool:
    if not allowed_ids:
        return True
    return user_id in allowed_ids


def classify_content(text: str) -> str:
    """메시지 내용을 자동 분류."""
    urls = URL_PATTERN.findall(text)
    if urls:
        for url in urls:
            if "youtube.com" in url or "youtu.be" in url:
                return "youtube"
            if "instagram.com" in url:
                return "instagram"
            if "twitter.com" in url or "x.com" in url:
                return "twitter"
            if "github.com" in url:
                return "github"
            if "news" in url or "article" in url:
                return "article"
        return "link"
    if len(text) > 200:
        return "note"
    return "memo"


def save_to_inbox(entry: dict) -> int:
    """인박스에 항목 저장. 저장된 총 항목 수 반환."""
    with open(INBOX_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # 총 항목 수 카운트
    count = sum(1 for _ in open(INBOX_FILE, encoding="utf-8"))
    return count


def get_inbox_count() -> int:
    if not INBOX_FILE.exists():
        return 0
    return sum(1 for _ in open(INBOX_FILE, encoding="utf-8"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("허용된 사용자만 이용할 수 있습니다.")
        logger.warning(f"Unauthorized: user_id={user_id}")
        return

    count = get_inbox_count()
    await update.message.reply_text(
        "📥 인박스 봇입니다!\n\n"
        "링크, 메모, 아이디어 — 아무거나 보내주세요.\n"
        "자동으로 저장해두고, 나중에 Claude Code에서 정리해드립니다.\n\n"
        f"현재 인박스: {count}개 항목\n\n"
        "명령어:\n"
        "/count - 인박스 항목 수 확인\n"
        "/recent - 최근 5개 항목 보기\n"
        "/myid - 내 텔레그램 ID 확인"
    )


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return
    n = get_inbox_count()
    await update.message.reply_text(f"📥 인박스: {n}개 항목")


async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_allowed(update.effective_user.id):
        return

    if not INBOX_FILE.exists():
        await update.message.reply_text("인박스가 비어있습니다.")
        return

    lines = open(INBOX_FILE, encoding="utf-8").readlines()
    last_5 = lines[-5:]

    text = "📋 최근 항목:\n\n"
    for line in last_5:
        entry = json.loads(line)
        time_str = entry["timestamp"][:16].replace("T", " ")
        content = entry["content"][:80]
        tag = entry.get("type", "?")
        text += f"[{tag}] {time_str}\n{content}\n\n"

    await update.message.reply_text(text)


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(f"텔레그램 ID: `{user_id}`", parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("허용된 사용자만 이용할 수 있습니다.")
        return

    text = update.message.text
    if not text:
        return

    urls = URL_PATTERN.findall(text)
    content_type = classify_content(text)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": content_type,
        "content": text,
        "urls": urls,
        "user_id": user_id,
    }

    total = save_to_inbox(entry)
    emoji = {"youtube": "🎬", "link": "🔗", "memo": "📝", "note": "📄",
             "article": "📰", "github": "💻", "instagram": "📸", "twitter": "🐦"}.get(content_type, "📥")

    await update.message.reply_text(f"{emoji} 저장! [{content_type}] (인박스 {total}개)")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return

    document = update.message.document
    caption = update.message.caption or ""
    file_name = document.file_name or "unknown"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "file",
        "content": f"[파일: {file_name}] {caption}".strip(),
        "urls": [],
        "file_name": file_name,
        "file_id": document.file_id,
        "user_id": user_id,
    }

    total = save_to_inbox(entry)
    await update.message.reply_text(f"📎 파일 저장! [{file_name}] (인박스 {total}개)")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        return

    caption = update.message.caption or ""
    photo = update.message.photo[-1]  # 가장 큰 사이즈

    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "photo",
        "content": f"[사진] {caption}".strip(),
        "urls": URL_PATTERN.findall(caption),
        "file_id": photo.file_id,
        "user_id": user_id,
    }

    total = save_to_inbox(entry)
    await update.message.reply_text(f"📷 사진 저장! (인박스 {total}개)")


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")

    if allowed_ids:
        logger.info(f"Allowed user IDs: {allowed_ids}")
    else:
        logger.warning("ALLOWED_USER_IDS not set - bot is open to all users!")

    logger.info(f"Inbox file: {INBOX_FILE}")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("count", count))
    app.add_handler(CommandHandler("recent", recent))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Inbox bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
