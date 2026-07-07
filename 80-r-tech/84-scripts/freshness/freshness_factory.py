"""
Freshness Factory — 언어별 Freshness Index 분기

사용법:
    from freshness.freshness_factory import calculate_freshness, apply_freshness_delta

    result = calculate_freshness(text, lang='en')
    delta  = apply_freshness_delta(result['freshness_index'], text, lang='en')
"""

from typing import Optional

from .freshness_ko import calculate_freshness_ko, apply_delta_ko
from .freshness_en import calculate_freshness_en


def calculate_freshness(
    full_text: str,
    lang: str = 'ko',
    config: Optional[dict] = None,
) -> dict:
    """언어에 따라 적절한 Freshness 산출 로직을 호출한다.

    Args:
        full_text: 분석 대상 텍스트
        lang: 'ko' | 'en'
        config: 영어 모드 시 커스텀 사전 오버라이드
    """
    if lang == 'en':
        return calculate_freshness_en(full_text, config=config, apply_delta=True)
    else:
        return calculate_freshness_ko(full_text)


def apply_freshness_delta(
    freshness_index: float,
    full_text: str,
    lang: str = 'ko',
) -> dict:
    """언어별 보정 규칙 적용.

    한국어: 시간근접 표지 +5
    영어: calculate_freshness_en에 이미 내장 (별도 호출 불필요하나 호환성 유지)
    """
    if lang == 'en':
        # 영어는 calculate_freshness_en에서 이미 delta 적용됨
        # 별도 호출 시에는 delta만 재산출
        from .freshness_en import _calculate_delta
        return _calculate_delta(full_text)
    else:
        return apply_delta_ko(freshness_index, full_text)
