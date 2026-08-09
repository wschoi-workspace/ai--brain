"""공유 직원명부 — arisa-employees.json 단일 로더 + 조회 레지스트리.

봇 3종이 각자 load_employees / _emp_by_tid / get_people 를 복제하던 것을 통합.
배치는 load_employees()만, 봇은 EmployeeRegistry를 쓰면 된다.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# shared/ 의 상위(02-scripts)에 위치한 명부
DEFAULT_EMP_PATH = Path(__file__).resolve().parents[1] / "arisa-employees.json"


def load_employees(path: Path | str = DEFAULT_EMP_PATH) -> dict:
    """인사마스터 스냅샷 명부 로드. 실패 시 빈 구조."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        logger.error(f"employees load error: {e}")
        return {"by_name": {}, "by_telegram_id": {}}


def _norm(s: str) -> str:
    return (s or "").replace(" ", "").strip()


# ── 느슨한 이름 해석 (2026-08-09) ──────────────────────────
# 사람은 명부에 적힌 대로 부르지 않는다. "@지혜님"·"지혜씨"·"전제훈 팀장"처럼 쓴다.
# 정확 매칭만 하면 담당자가 빈 채로 등록되고, 그 업무는 **아무도 안 보는 행**이 된다.
# (실측: `/assign 기획팀 CJ 시안 수정 @지혜님 ~수요일` → "지혜" → 미매칭)
#
# 원칙: 느슨하게 찾되 **애매하면 고르지 않는다.** 후보가 둘이면 호출측이 되묻게 한다.
# 엉뚱한 사람에게 업무가 붙는 것이 못 찾는 것보다 나쁘다.
_HONORIFICS = ("선생님", "팀장님", "매니저님", "대표님", "실장님", "부장님", "과장님", "차장님",
               "님", "씨", "쌤", "팀장", "매니저", "대표", "실장", "부장", "과장", "차장")


def strip_honorific(s: str) -> str:
    """앞의 @·공백과 뒤의 존칭·직함을 걷어낸다. 긴 것부터 지운다(팀장님 > 님)."""
    n = (s or "").strip().lstrip("@").strip()
    changed = True
    while changed:
        changed = False
        for h in _HONORIFICS:
            if len(n) > len(h) and n.endswith(h):
                n = n[: -len(h)].strip()
                changed = True
                break
    return n


def resolve_name(query: str, names) -> tuple[str | None, list[str]]:
    """이름 후보 해석. 반환 (확정 이름 | None, 후보 목록).

    단계: ①정확 ②존칭 제거 후 정확 ③이름이 query로 **끝남**(지혜 → 양지혜)
    후보가 1명이면 확정, 2명 이상이면 (None, 후보들) — 호출측이 되묻는다.
    """
    names = list(names or [])
    q = _norm(query)
    if not q:
        return None, []

    exact = [n for n in names if _norm(n) == q]
    if len(exact) == 1:
        return exact[0], exact

    q2 = _norm(strip_honorific(query))
    if not q2:
        return None, []
    exact2 = [n for n in names if _norm(n) == q2]
    if len(exact2) == 1:
        return exact2[0], exact2
    if len(exact2) > 1:
        return None, exact2

    # 성을 빼고 부른 경우 — 2글자 이상일 때만. 1글자 접미는 오탐이 너무 많다.
    if len(q2) >= 2:
        suffix = [n for n in names if _norm(n).endswith(q2) and _norm(n) != q2]
        if len(suffix) == 1:
            return suffix[0], suffix
        if len(suffix) > 1:
            return None, suffix
    return None, []


class EmployeeRegistry:
    """봇용 직원명부 조회/학습. 매 호출 파일을 읽어 최신 상태 반영(기존 봇 동작과 동일)."""

    def __init__(self, path: Path | str = DEFAULT_EMP_PATH):
        self.path = Path(path)

    def load(self) -> dict:
        return load_employees(self.path)

    def save(self, data: dict) -> None:
        try:
            self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            logger.error(f"employees save error: {e}")

    def names(self) -> list[str]:
        return list(self.load().get("by_name", {}).keys())

    def match_by_name(self, name: str) -> dict | None:
        emp = self.load().get("by_name", {})
        n = _norm(name)
        for k, v in emp.items():
            if _norm(k) == n:
                return {"name": k, **v}
        return None

    def by_telegram_id(self, uid) -> dict | None:
        d = self.load()
        nm = d.get("by_telegram_id", {}).get(str(uid))
        if nm:
            e = d.get("by_name", {}).get(nm)
            if e:
                return {"name": nm, **e}
        return None

    def register_telegram_id(self, uid, name: str) -> None:
        d = self.load()
        d.setdefault("by_telegram_id", {})[str(uid)] = name
        self.save(d)
