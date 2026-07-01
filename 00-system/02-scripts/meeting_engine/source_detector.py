"""소스 타입 자동 감지 — AI 디스커션 vs 사람 미팅 분류."""

from __future__ import annotations

import re

AI_KEYWORDS = [
    "chatgpt", "gpt", "아리사", "arisa", "claude",
    "ai와", "ai가", "ai는", "ai의",
    "ChatGPT의 말:", "나의 말:",
]

MTG_INDICATORS = [
    "참석자:",
    "회의실",
    "전화 회의",
    "zoom", "teams", "meet",
]


def detect_source_type(text: str) -> str:
    """회의 텍스트에서 소스 타입을 감지한다.

    Returns:
        'ai' — GPT/아리사와의 디스커션
        'mtg' — 사람 간 미팅 전사록
    """
    text_lower = text.lower()

    # AI 디스커션 신호
    ai_score = 0
    for kw in AI_KEYWORDS:
        if kw.lower() in text_lower:
            ai_score += 1

    # 참석자 필드에서 AI 이름 확인
    participants_match = re.search(r"참석자[:\s]*(.+?)(\n|$)", text)
    if participants_match:
        participants = participants_match.group(1).lower()
        for ai_name in ["chatgpt", "gpt", "아리사", "arisa", "claude"]:
            if ai_name in participants:
                ai_score += 3  # 참석자에 명시되면 강한 신호

    # MTG 신호
    mtg_score = 0
    for kw in MTG_INDICATORS:
        if kw.lower() in text_lower:
            mtg_score += 1

    # 참석자 수 확인 (3명 이상이면 mtg 가능성 높음)
    if participants_match:
        names = [n.strip() for n in participants_match.group(1).split(",")]
        if len(names) >= 3:
            mtg_score += 2

    if ai_score >= 2:
        return "ai"
    elif mtg_score >= 2:
        return "mtg"
    elif ai_score > mtg_score:
        return "ai"
    else:
        return "mtg"


SOURCE_LABELS = {
    "ai": "🤖 AI 디스커션",
    "mtg": "👥 팀 미팅",
}
