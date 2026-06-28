"""공유 정규화 — 직원명/팀/날짜. daily-brief·weekly-report가 복제하던 로직의 단일 출처.

순수 함수: 레지스트리(by_name)·별칭(aliases)을 인자로 주입한다(전역 의존 제거).
행동은 기존 배치 구현과 동일하게 보존한다.
"""
from __future__ import annotations

from datetime import datetime

# 과거 데이터 영문/변형 이름 → 명부 정규명 (daily-brief / weekly-report 공통이던 값)
DEFAULT_NAME_ALIASES = {
    "yang eun jung": "양은정", "yangeunjung": "양은정", "eun jung": "양은정",
    "준호 김": "김준호", "김 준호": "김준호", "bro callme": "최원석",
}


def normalize_name(s: str, by_name: dict, aliases: dict | None = None) -> str:
    """시트 이름 → 명부 정규명. 영문/변형은 별칭으로 흡수. 미매칭은 원문 유지.

    오염 데이터(이름칸에 보고문 — 줄바꿈/과길이)는 ""로 제외한다.
    """
    aliases = DEFAULT_NAME_ALIASES if aliases is None else aliases
    s = (s or "").strip()
    if not s:
        return ""
    key = s.replace(" ", "").lower()
    for name in by_name:
        if name.replace(" ", "").lower() == key:
            return name
    if s.lower() in aliases:
        return aliases[s.lower()]
    for k, v in aliases.items():
        if k.replace(" ", "") == key:
            return v
    if "\n" in s or len(s) > 12:
        return ""
    return s


def team_of(name: str, by_name: dict) -> str:
    e = by_name.get(name)
    if e:
        return e.get("team") or e.get("company", "") or "미지정"
    return "미지정"


def normalize_date(s: str) -> str | None:
    """YYYY-MM-DD 그대로 / YYMMDD → YYYY-MM-DD / ISO timestamp → 앞 10자. 실패 시 None."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        if len(s) == 10 and s[4] == "-":
            datetime.strptime(s, "%Y-%m-%d")
            return s
        if len(s) == 6 and s.isdigit():
            return datetime.strptime(s, "%y%m%d").strftime("%Y-%m-%d")
        if len(s) >= 10:
            return s[:10]
    except Exception:
        return None
    return None
