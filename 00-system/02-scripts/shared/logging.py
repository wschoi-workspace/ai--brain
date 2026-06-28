"""공유 로깅 — 텔레그램 봇 토큰 마스킹.

httpx가 요청 URL(`.../bot<TOKEN>/getUpdates`)을 INFO 로그에 평문 노출하는 것을 막는다.
daily-report-bot·second-brain bot이 글자까지 동일하게 복제하던 필터의 단일 출처.
"""
from __future__ import annotations

import logging
import re


class TokenRedactingFilter(logging.Filter):
    """로그 메시지에서 텔레그램 봇 토큰 자리만 <REDACTED>로 치환."""

    _TOKEN_RE = re.compile(r"\d{8,10}:[A-Za-z0-9_-]{35}")

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        if self._TOKEN_RE.search(msg):
            record.msg = self._TOKEN_RE.sub("<REDACTED>", msg)
            record.args = ()
        return True


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """기본 포맷 + 모든 핸들러에 토큰 마스킹 필터 부착. 루트 로거 반환."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=level,
    )
    for h in logging.getLogger().handlers:
        h.addFilter(TokenRedactingFilter())
    return logging.getLogger()
