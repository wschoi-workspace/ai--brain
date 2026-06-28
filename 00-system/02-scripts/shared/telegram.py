"""공유 텔레그램 plumbing — 타임아웃 앱 빌더 + 네트워크 에러 핸들러.

daily-report-bot·second-brain bot이 동일하게 쓰던 30초 타임아웃 빌더를 단일 출처로.
basket-ops-bot은 타임아웃이 없었으나 이 빌더로 통일하면 안정성↑.

⚠️ 봇 채택 시: 각 봇의 기존 error 핸들러 안내 문구를 먼저 대조하고 적용할 것.
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import Application, ApplicationBuilder, ContextTypes

logger = logging.getLogger(__name__)


def create_telegram_app(token: str, timeout: float = 30.0) -> Application:
    """네트워크 안정성 높은 Application 빌더(connect/read/write/pool/getUpdates 타임아웃)."""
    return (
        ApplicationBuilder()
        .token(token)
        .connect_timeout(timeout)
        .read_timeout(timeout)
        .write_timeout(timeout)
        .pool_timeout(timeout)
        .get_updates_connect_timeout(timeout)
        .get_updates_read_timeout(timeout)
        .build()
    )


async def safe_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """네트워크/타임아웃 등 미처리 예외 안전망. 사용자에게 1회 재전송 안내."""
    err = context.error
    logger.error("Handler exception: %s", err, exc_info=err)
    msg = getattr(update, "message", None) if isinstance(update, Update) else None
    if msg is None:
        return
    try:
        if isinstance(err, (NetworkError, TimedOut)):
            await msg.reply_text(
                "⚠️ 잠시 네트워크가 불안정했어요. 방금 보내신 내용을 한 번만 다시 보내주시겠어요?"
            )
        else:
            await msg.reply_text("⚠️ 처리 중 문제가 생겼어요. 잠시 후 다시 보내주세요.")
    except Exception as e:  # noqa: BLE001
        logger.error("error_handler reply failed: %s", e)
