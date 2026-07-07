"""
Freshness Index — 한국어 (Korean)
CLT 기반: 이/가(Low Construal, 즉시적 발견) vs 은/는(High Construal, 추상적 설명) 비율
원본: xylitol_crawl.py L388-392 + xylitol_pipeline.py L347-351
"""

import re


def calculate_freshness_ko(full_text: str) -> dict:
    """한국어 텍스트의 Freshness Index를 산출한다.

    Returns:
        dict with keys: freshness_index (0-100), iga_count, eunneun_count, details
    """
    iga_count = len(re.findall(r'[가-힣]이\s|[가-힣]가\s', full_text))
    eunneun_count = len(re.findall(r'[가-힣]은\s|[가-힣]는\s', full_text))
    total_particles = iga_count + eunneun_count
    freshness = round(iga_count / max(total_particles, 1) * 100, 1)

    return {
        'freshness_index': freshness,
        'iga_count': iga_count,
        'eunneun_count': eunneun_count,
        'total_particles': total_particles,
        'details': {
            'method': 'particle_ratio',
            'language': 'ko',
        }
    }


def apply_delta_ko(freshness_index: float, full_text: str) -> dict:
    """시간근접 표지 보정 (pipeline 단계).

    Returns:
        dict with keys: freshness_delta, matched_markers
    """
    temporal_markers = ['오늘', '아까', '방금', '지금', '어제']
    matched = [m for m in temporal_markers if m in full_text]
    delta = 5 if matched else 0

    return {
        'freshness_delta': delta,
        'matched_markers': matched,
    }
