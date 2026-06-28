"""공유 LLM 클라이언트 — OpenAI 호출 + JSON 파싱 + 재시도.

봇이 각자 call_gpt / gpt_structure / classify 내부에 복제하던 OpenAI 호출·파싱을 통합.
프롬프트는 절대 여기 두지 않는다(도메인 차별성). 여기는 호출 배관만.

기존 동작 보존:
- call_json(use_response_format=False) = daily-report의 call_gpt (마크다운 펜스 제거)
- call_json(use_response_format=True)  = basket/second-brain (response_format=json_object)
- 재시도는 JSON 파싱 실패에만 적용(중복 호출 부작용 최소화).
"""
from __future__ import annotations

import json
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def call_json(self, system: str, user_msg: str, *, temperature: float = 0.3,
                  max_tokens: int = 2000, model: str | None = None,
                  use_response_format: bool = False, retries: int = 2) -> dict | None:
        """JSON 응답 → dict. 실패 시 None. 마크다운 코드펜스 자동 제거."""
        last_err = None
        for attempt in range(retries):
            try:
                kwargs = dict(
                    model=model or self.model,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user_msg}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if use_response_format:
                    kwargs["response_format"] = {"type": "json_object"}
                resp = self.client.chat.completions.create(**kwargs)
                text = (resp.choices[0].message.content or "").strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return json.loads(text)
            except json.JSONDecodeError as e:
                last_err = e
                logger.warning(f"LLM JSON parse retry {attempt+1}: {e}")
                continue
            except Exception as e:  # noqa: BLE001
                logger.error(f"LLM call error: {e}")
                return None
        logger.error(f"LLM JSON parse final error: {last_err}")
        return None

    def call_text(self, system: str, user_msg: str, *, temperature: float = 0.5,
                  max_tokens: int = 500, model: str | None = None) -> str:
        """텍스트 응답 → str. 실패 시 ""."""
        try:
            resp = self.client.chat.completions.create(
                model=model or self.model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user_msg}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            logger.error(f"LLM text error: {e}")
            return ""
