"""프로젝트명 매칭 — 표기 변형·별칭 허용 매칭의 단일 출처 (R4 개편 1차, 2026-07-25).

dashboard-server.py에 있던 _proj_tokens/_match_project/_match_project_p를 이관.
목적: daily-brief·weekly·arisa-memory classifier가 동일 매칭을 쓰도록 공유화 —
같은 프로젝트가 별칭·표기 차이로 서로 다른 프로젝트로 인식되는 문제의 방지 지점.

원칙: 순수함수만 둔다(파일 I/O·프로젝트 로드는 호출측 책임).
"""
from __future__ import annotations

import re

# 매칭에서 제외할 일반어 — 이 단어만 겹쳐서는 동일 프로젝트로 보지 않는다
PROJ_STOP = {"프로젝트", "행사", "팝업", "기획", "관련", "운영", "브랜드", "상세"}


def proj_tokens(s) -> set:
    """프로젝트명 → 매칭용 토큰 집합 (영숫자·한글 단어, 일반어 제외)."""
    toks = set()
    for t in re.findall(r"[A-Za-z0-9]+|[가-힣]+", (s or "").lower()):
        if len(t) >= 2 and t not in PROJ_STOP:
            toks.add(t)
    return toks


def match_project(ap, pname) -> bool:
    """분장 프로젝트명(ap) vs 포트폴리오명(pname) — 표기 변형 허용 매칭.
    ① 정규화 상호 포함 ② 유의 토큰 교집합 (영문 3자+/한글 2자+, 일반어 제외)."""
    na = re.sub(r"[^a-z0-9가-힣]", "", (ap or "").lower())
    nb = re.sub(r"[^a-z0-9가-힣]", "", (pname or "").lower())
    if na and nb and (na in nb or nb in na):
        return True
    common = proj_tokens(ap) & proj_tokens(pname)
    return any(len(t) >= 3 or re.fullmatch(r"[가-힣]{2,}", t) for t in common)


def match_project_p(ap, p) -> bool:
    """분장 프로젝트명(ap) vs 프로젝트 dict — 정식 명칭 + aliases(별칭·구표기)까지 매칭."""
    if match_project(ap, (p or {}).get("name") or ""):
        return True
    return any(match_project(ap, al) for al in ((p or {}).get("aliases") or []))
