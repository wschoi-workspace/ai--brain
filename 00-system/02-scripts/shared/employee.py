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
