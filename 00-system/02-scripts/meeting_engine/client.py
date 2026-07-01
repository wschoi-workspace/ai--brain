"""Meeting Engine OpenAI client - 외부에서 주입받은 클라이언트 사용."""
from __future__ import annotations

import json
import logging
import time

logger = logging.getLogger(__name__)

_openai_client = None
_model = "gpt-4o"


def init(client, model: str = "gpt-4o"):
    """daily-report-bot의 OpenAI 클라이언트를 주입받는다."""
    global _openai_client, _model
    _openai_client = client
    _model = model


def call_openai(
    system_prompt: str,
    user_prompt: str,
    response_format: str = "json_object",
    max_retries: int = 3,
) -> dict:
    """OpenAI API 호출 -> JSON dict 반환. 지수 백오프 재시도."""
    if _openai_client is None:
        raise RuntimeError("meeting_engine.client.init()을 먼저 호출하세요")

    kwargs = {
        "model": _model,
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if response_format == "json_object":
        kwargs["response_format"] = {"type": "json_object"}

    for attempt in range(max_retries):
        try:
            response = _openai_client.chat.completions.create(**kwargs)
            usage = response.usage
            if usage:
                logger.info(
                    f"[meeting] tokens in={usage.prompt_tokens} "
                    f"out={usage.completion_tokens} total={usage.total_tokens}"
                )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw": content}
        except Exception as e:
            wait = 2 ** (attempt + 1)
            logger.warning(f"[meeting] retry {attempt+1}/{max_retries}: {e} - {wait}s")
            time.sleep(wait)

    logger.error("[meeting] OpenAI API failed after max retries")
    return {}
