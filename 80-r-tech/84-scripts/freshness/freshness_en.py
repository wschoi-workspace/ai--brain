"""
Freshness Index — 영어 (English)
CLT 기반 7-피처 가중 합산 모델

피처 7종 (각 0~1 정규화 → 가중 합산 → 0~100 스케일):
  1. Discovery verbs      (×25) — "just found", "noticed", "turns out"
  2. Temporal proximity    (×20) — "just", "today", "suddenly", "recently"
  3. Progressive aspect    (×15) — be + -ing (진행상, 사건 내부 스캔)
  4. Proximal demonstratives (×15) — this/(this+that) 비율
  5. Present perfect+just  (×10) — "have just", "has been" vs "years ago"
  6. Exclamatory markers   (×10) — "!!", "wow", "can't believe"
  7. Sensory concreteness  (× 5) — 감각어 밀도

Phase 1: Pure Regex (spaCy 의존성 없음)
"""

import re
from typing import Optional


# ── 기본 사전 ──

DEFAULT_DISCOVERY_VERBS = [
    r'\bjust found\b', r'\bjust discovered\b', r'\bjust noticed\b',
    r'\bnoticed\b', r'\brealized\b', r'\bdiscovered\b',
    r'\bturns out\b', r'\bturned out\b',
    r'\bcame across\b', r'\bstumbled upon\b', r'\bstumbled on\b',
    r'\bfound out\b', r'\bjust learned\b',
    r'\bjust tried\b', r'\bjust got\b', r'\bjust had\b',
]

DEFAULT_TEMPORAL_PROXIMITY = [
    r'\bjust\b', r'\bright now\b', r'\btoday\b',
    r'\bsuddenly\b', r'\brecently\b',
    r'\bthis morning\b', r'\blast night\b', r'\byesterday\b',
    r'\bjust now\b', r'\bmoments ago\b',
    r'\ba few minutes ago\b', r'\bearlier today\b',
]

DEFAULT_SENSORY_VOCAB = {
    'taste': [r'\btast(?:e[ds]?|y|ing)\b', r'\bflavor(?:ful|s)?\b', r'\bdelicious\b',
              r'\bsweet\b', r'\bbitter\b', r'\bsour\b', r'\bsalty\b', r'\bsavory\b',
              r'\bumami\b', r'\bbland\b', r'\brich\b'],
    'smell': [r'\bsmell(?:s|ed|ing)?\b', r'\bscent(?:ed|s)?\b', r'\baroma(?:tic|s)?\b',
              r'\bfragran(?:t|ce)\b', r'\bstink(?:s|ing)?\b', r'\bodor\b'],
    'touch': [r'\bsmooth\b', r'\brough\b', r'\bsoft\b', r'\bhard\b',
              r'\bsticky\b', r'\bcrispy\b', r'\bcrunchy\b', r'\btender\b',
              r'\bsilky\b', r'\bvelvety\b', r'\btexture[ds]?\b'],
    'sight': [r'\bbright\b', r'\bcolorful\b', r'\bshiny\b', r'\bsparkling\b',
              r'\bgolden\b', r'\bvibrant\b', r'\bglowing\b', r'\bgleaming\b'],
    'sound': [r'\bloud\b', r'\bquiet\b', r'\bbuzzing\b', r'\bcrunching\b',
              r'\bsizzling\b', r'\bnoisy\b'],
}

# 보정 규칙용 사전
EXTREME_RECENCY = [
    r'\bright now\b', r'\bjust now\b',
    r'\bas I type\b', r'\bas I write\b', r'\bas we speak\b',
]

DISTANT_MARKERS = [
    r'\bfor years\b', r'\bfor months\b', r'\bsince 20\d{2}\b',
    r'\bback in\b', r'\bused to\b', r'\balways been\b',
    r'\bfor decades\b', r'\bover the years\b',
]

NARRATIVE_PRESENT = [
    r'\bso I walk\b', r'\bso I go\b', r'\bso I try\b',
    r'\band it goes\b', r'\band I go\b', r'\band she goes\b',
    r'\band he goes\b', r'\bthen I go\b',
]


# ── 피처 스코어링 함수 (각 0~1 반환) ──

def _score_discovery(text: str, patterns: Optional[list] = None) -> tuple[float, list]:
    """Discovery verbs: 이/가 "초점" 기능의 가장 직접적 등가물."""
    pats = patterns or DEFAULT_DISCOVERY_VERBS
    matches = []
    for p in pats:
        found = re.findall(p, text, re.IGNORECASE)
        matches.extend(found)
    word_count = max(len(text.split()), 1)
    density = len(matches) / word_count
    # 정규화: 1% 이상이면 1.0
    score = min(density / 0.01, 1.0)
    return score, matches


def _score_temporal(text: str, patterns: Optional[list] = None) -> tuple[float, list]:
    """Temporal proximity: CLT 시간적 거리 차원."""
    pats = patterns or DEFAULT_TEMPORAL_PROXIMITY
    matches = []
    for p in pats:
        found = re.findall(p, text, re.IGNORECASE)
        matches.extend(found)
    word_count = max(len(text.split()), 1)
    density = len(matches) / word_count
    score = min(density / 0.015, 1.0)
    return score, matches


def _score_progressive(text: str) -> tuple[float, list]:
    """Progressive aspect: be + -ing (Langacker 인지문법 — 사건 내부 시점).

    Phase 1 regex 한계: 동명사(gerund) 오분류 가능.
    """
    prog_pattern = r"\b(?:i'?m|he'?s|she'?s|it'?s|we'?re|they'?re|i am|he is|she is|it is|we are|they are|was|were|is|are)\s+\w+ing\b"
    matches = re.findall(prog_pattern, text, re.IGNORECASE)
    # 제외: being, having (보조동사), nothing, something, anything, everything
    exclude = re.compile(r'\b(?:no|some|any|every)thing\b', re.IGNORECASE)
    matches = [m for m in matches if not exclude.search(m)]
    sentence_count = max(len(re.split(r'[.!?]+', text)), 1)
    density = len(matches) / sentence_count
    score = min(density / 0.3, 1.0)
    return score, matches


def _score_proximal(text: str) -> tuple[float, int, int]:
    """Proximal demonstratives: this/(this+that) 비율 — 이/가 ratio와 구조적 동형.

    Diessel: this = 근접(Low Construal), that = 원거리(High Construal).
    """
    this_count = len(re.findall(r'\bthis\b', text, re.IGNORECASE))
    that_count = len(re.findall(r'\bthat\b', text, re.IGNORECASE))
    total = this_count + that_count
    if total == 0:
        return 0.5, this_count, that_count  # 중립
    score = this_count / total
    return score, this_count, that_count


def _score_perfective(text: str) -> tuple[float, list]:
    """Present perfect + just: 과거→현재 관련성 표시.

    have/has + just + pp vs past tense + "years ago" 등.
    """
    pf_patterns = [
        r"\b(?:have|has)\s+just\s+\w+",
        r"\b(?:have|has)\s+(?:never|already|recently)\s+\w+",
        r"\b(?:i've|we've|they've)\s+just\s+\w+",
        r"\b(?:i've|we've|they've)\s+(?:never|already|recently)\s+\w+",
    ]
    matches = []
    for p in pf_patterns:
        found = re.findall(p, text, re.IGNORECASE)
        matches.extend(found)
    sentence_count = max(len(re.split(r'[.!?]+', text)), 1)
    density = len(matches) / sentence_count
    score = min(density / 0.15, 1.0)
    return score, matches


def _score_affect(text: str) -> tuple[float, dict]:
    """Exclamatory markers: Trope & Liberman — 감정 반응 = Low Construal 부산물."""
    excl_count = text.count('!')
    double_excl = len(re.findall(r'!!+', text))
    caps_words = len(re.findall(r'\b[A-Z]{3,}\b', text))  # 3글자 이상 ALL CAPS
    affect_phrases = [
        r'\bwow\b', r'\bomg\b', r'\boh my god\b', r'\boh my\b',
        r"\bcan'?t believe\b", r'\bblew my mind\b', r'\bamazing\b',
        r'\bunbelievable\b', r'\bincredible\b', r'\binsane\b',
        r'\bmind[- ]?blow(?:n|ing)\b', r'\bgame[- ]?changer\b',
    ]
    phrase_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in affect_phrases)

    sentence_count = max(len(re.split(r'[.!?]+', text)), 1)
    raw = (excl_count * 0.3 + double_excl * 0.5 + caps_words * 0.2 + phrase_count * 1.0) / sentence_count
    score = min(raw / 0.8, 1.0)

    return score, {
        'exclamation_marks': excl_count,
        'double_exclamations': double_excl,
        'caps_words': caps_words,
        'affect_phrases': phrase_count,
    }


def _score_sensory(text: str, vocab: Optional[dict] = None) -> tuple[float, dict]:
    """Sensory concreteness: Semin & Fiedler LCM — 구체 행위동사 = Low Construal.

    가중치 최소(5): LAI와 이중계상 최소화.
    """
    v = vocab or DEFAULT_SENSORY_VOCAB
    category_counts = {}
    total_matches = 0
    for category, patterns in v.items():
        count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in patterns)
        category_counts[category] = count
        total_matches += count

    word_count = max(len(text.split()), 1)
    density = total_matches / word_count
    score = min(density / 0.02, 1.0)

    return score, category_counts


# ── 보정 규칙 (Delta) ──

def _calculate_delta(text: str) -> dict:
    """보정 규칙 적용: 극단적 근접/원거리/내러티브 현재."""
    delta = 0
    matched = {}

    # +5: 극단적 근접 신호
    extreme = [m for p in EXTREME_RECENCY for m in re.findall(p, text, re.IGNORECASE)]
    if extreme:
        delta += 5
        matched['extreme_recency'] = extreme

    # -5: 원거리 시간 표지 2개 이상
    distant = [m for p in DISTANT_MARKERS for m in re.findall(p, text, re.IGNORECASE)]
    if len(distant) >= 2:
        delta -= 5
        matched['distant_markers'] = distant

    # +3: 내러티브 현재
    narrative = [m for p in NARRATIVE_PRESENT for m in re.findall(p, text, re.IGNORECASE)]
    if narrative:
        delta += 3
        matched['narrative_present'] = narrative

    return {
        'freshness_delta': delta,
        'matched_markers': matched,
    }


# ── 메인 함수 ──

WEIGHTS = {
    'discovery':    25,
    'temporal':     20,
    'progressive':  15,
    'proximal':     15,
    'perfective':   10,
    'affect':       10,
    'sensory':       5,
}


def calculate_freshness_en(
    full_text: str,
    config: Optional[dict] = None,
    apply_delta: bool = True,
) -> dict:
    """영어 텍스트의 Freshness Index를 산출한다 (7-피처 가중 합산).

    Args:
        full_text: 분석 대상 영어 텍스트
        config: 커스텀 사전 오버라이드 (discovery_verbs, temporal_proximity, sensory_vocabulary)
        apply_delta: 보정 규칙 적용 여부

    Returns:
        dict with keys: freshness_index (0-100), features, delta, details
    """
    cfg = config or {}

    # 커스텀 패턴 변환 (config.json의 단순 문자열 → regex word boundary)
    disc_patterns = None
    if 'discovery_verbs' in cfg:
        disc_patterns = [rf'\b{re.escape(v)}\b' for v in cfg['discovery_verbs']]

    temp_patterns = None
    if 'temporal_proximity' in cfg:
        temp_patterns = [rf'\b{re.escape(v)}\b' for v in cfg['temporal_proximity']]

    sensory_vocab = cfg.get('sensory_vocabulary', None)

    # 7 피처 산출
    disc_score, disc_matches = _score_discovery(full_text, disc_patterns)
    temp_score, temp_matches = _score_temporal(full_text, temp_patterns)
    prog_score, prog_matches = _score_progressive(full_text)
    prox_score, this_n, that_n = _score_proximal(full_text)
    perf_score, perf_matches = _score_perfective(full_text)
    aff_score, aff_detail = _score_affect(full_text)
    sens_score, sens_detail = _score_sensory(full_text, sensory_vocab)

    features = {
        'discovery':   {'score': round(disc_score, 4), 'weight': WEIGHTS['discovery'],   'matches': disc_matches},
        'temporal':    {'score': round(temp_score, 4), 'weight': WEIGHTS['temporal'],    'matches': temp_matches},
        'progressive': {'score': round(prog_score, 4), 'weight': WEIGHTS['progressive'], 'matches': prog_matches},
        'proximal':    {'score': round(prox_score, 4), 'weight': WEIGHTS['proximal'],    'this': this_n, 'that': that_n},
        'perfective':  {'score': round(perf_score, 4), 'weight': WEIGHTS['perfective'],  'matches': perf_matches},
        'affect':      {'score': round(aff_score, 4),  'weight': WEIGHTS['affect'],      'detail': aff_detail},
        'sensory':     {'score': round(sens_score, 4), 'weight': WEIGHTS['sensory'],     'detail': sens_detail},
    }

    # 가중 합산 (0~100)
    raw_score = sum(
        features[k]['score'] * WEIGHTS[k]
        for k in WEIGHTS
    )

    # 보정
    delta_info = _calculate_delta(full_text) if apply_delta else {'freshness_delta': 0, 'matched_markers': {}}
    final_score = max(0, min(100, round(raw_score + delta_info['freshness_delta'], 1)))

    return {
        'freshness_index': final_score,
        'raw_score': round(raw_score, 1),
        'features': features,
        'delta': delta_info,
        'details': {
            'method': '7_feature_weighted',
            'language': 'en',
            'weights': WEIGHTS,
            'word_count': len(full_text.split()),
        }
    }
