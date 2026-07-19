"""프로젝트 네이밍 규칙 SSOT — Team Ops Guide v1 2부-① (2026-07-18 대표 확정).

P2 (팀 방법론 스터디): 프로젝트명은 한글·영문·숫자·공백·-·&·×·· 만 허용
(괄호·슬래시·언더스코어 등 특수문자 금지), 2~40자. 등록명이 유일한 공식 명칭.
위반 문자는 공백으로 자동 정리(clean)한 뒤 검증한다 — 입력 마찰 최소화(원리 8).

규칙을 바꾸려면 이 파일만 수정한다. 소비처:
dashboard-server(/api/project/save·assign-commit·assign-project-check),
daily-report-bot(/assign 시트 저장).
"""
from __future__ import annotations

import re

NAME_MIN = 2
NAME_MAX = 40

# 허용 문자 밖 = 공백 치환 대상 (괄호·슬래시·백슬래시·언더스코어·따옴표 등)
_FORBIDDEN = re.compile(r"[^가-힣A-Za-z0-9 &×·.\-]")


def clean_project_name(name) -> str:
    """위반 문자를 공백으로 치환하고 공백을 정돈한 프로젝트명. 빈 입력은 ''."""
    s = _FORBIDDEN.sub(" ", str(name or ""))
    return re.sub(r"\s+", " ", s).strip()


def _bigrams(s: str) -> set:
    """정규화(영숫자·한글만, 소문자) 후 문자 bigram 집합."""
    n = re.sub(r"[^a-z0-9가-힣]", "", str(s or "").lower())
    if len(n) < 2:
        return {n} if n else set()
    return {n[i:i + 2] for i in range(len(n) - 1)}


def name_similarity(a, b) -> float:
    """프로젝트명 n-gram(문자 bigram) Dice 유사도 0.0~1.0.

    토큰 매칭이 못 잡는 붙임 표기('중기 팝업스토어' vs '중기제품팝업스토')를 감지한다.
    귀속(pid 확정)에는 쓰지 말 것 — 중복 경고·유사 후보 등 사람이 확인하는 지점 전용.
    """
    ba, bb = _bigrams(a), _bigrams(b)
    if not ba or not bb:
        return 0.0
    return 2 * len(ba & bb) / (len(ba) + len(bb))


# 중복 경고 임계값 — 실데이터 캘리브레이션(2026-07-18): 중기 쌍 0.62, 무관 쌍 < 0.4
SIMILARITY_DUP = 0.55


def validate_project_name(name) -> tuple[bool, str]:
    """정리(clean) 후의 이름을 검증. (ok, 오류 메시지) 반환 — ok면 메시지 ''."""
    s = clean_project_name(name)
    if not s:
        return False, "프로젝트명이 비어 있습니다"
    if len(s) < NAME_MIN:
        return False, f"프로젝트명이 너무 짧습니다 ({NAME_MIN}자 이상)"
    if len(s) > NAME_MAX:
        return False, f"프로젝트명이 너무 깁니다 ({NAME_MAX}자 이하)"
    if not re.search(r"[가-힣A-Za-z]", s):
        return False, "프로젝트명에 한글 또는 영문이 필요합니다"
    return True, ""
