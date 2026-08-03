"""매장 명부(SSOT) — 매장관리 봇·마감보고·인제스트가 공유.

배경(2026-07-30): 시트·웹앱은 처음부터 store_id로 매장을 구분하는 구조였는데
봇이 store_id를 'basket' 하나로 고정해 넣고 있어서 매장이 늘어도 구분되지 않았다.
이 모듈이 매장 목록의 단일 출처이고, 신규 매장은 add()(봇 /매장추가) 또는
stores.json 직접 편집으로 늘린다.

용어: id = 시트 store_id 컬럼용 안정 슬러그, name = 사람이 보는 매장명(마감보고 '매장' 컬럼).
"""
from __future__ import annotations
import json
import re
import threading
from datetime import date
from pathlib import Path

REGISTRY = Path(__file__).resolve().parent.parent / "stores.json"
COMMON = ""          # 특정 매장에 안 붙는 본사·공통 업무
COMMON_LABEL = "공통"
_LOCK = threading.Lock()


def load() -> dict:
    try:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        return {"stores": []}


def all_stores() -> list[dict]:
    return [s for s in load().get("stores", []) if s.get("id")]


def active_stores() -> list[dict]:
    """운영·준비 중인 매장(폐점 제외)."""
    return [s for s in all_stores() if s.get("status") != "폐점"]


def by_id(store_id: str) -> dict | None:
    for s in all_stores():
        if s["id"] == (store_id or "").strip():
            return s
    return None


def display(store_id: str) -> str:
    """store_id → 매장명. 미등록이면 받은 값 그대로(기록 유실 방지)."""
    s = by_id(store_id)
    return s["name"] if s else (store_id or COMMON_LABEL)


def _terms(store: dict) -> list[str]:
    out = [store.get("name", ""), store.get("id", "")] + list(store.get("aliases") or [])
    return [t.strip() for t in out if t and t.strip()]


def find(text: str) -> list[dict]:
    """텍스트에 언급된 매장 목록(등장 순서, 중복 제거)."""
    t = text or ""
    low = t.lower()
    hits: list[tuple[int, dict]] = []
    for s in active_stores():
        pos = min((low.find(term.lower()) for term in _terms(s) if term.lower() in low),
                  default=-1)
        if pos >= 0:
            hits.append((pos, s))
    hits.sort(key=lambda x: x[0])
    return [s for _, s in hits]


def resolve(text: str) -> str:
    """매장명 문자열 → store_id. 못 찾으면 '' (공통)."""
    hits = find(text)
    return hits[0]["id"] if hits else COMMON


def attribute(text: str) -> str:
    """보고 본문 → 귀속 매장 id. 정확히 한 곳만 언급됐을 때만 귀속(여러 곳이면 공통).

    여러 매장을 한 보고에 섞어 쓰는 일이 잦아, 억지 귀속보다 '공통'이 안전하다.
    """
    hits = find(text)
    return hits[0]["id"] if len(hits) == 1 else COMMON


def slugify(name: str) -> str:
    """매장명 → ascii 슬러그. 한글 등 비ascii면 store{n}로 대체(시트 조인 키라 ascii 유지)."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (name or "").strip().lower()).strip("-")
    if re.search(r"[a-z]", s):  # 숫자·기호만 남은 건 슬러그로 못 씀('올드타운 2호점'→'2')
        return s
    used = {x["id"] for x in all_stores()}
    n = len(used) + 1
    while f"store{n}" in used:
        n += 1
    return f"store{n}"


def add(name: str, aliases: list[str] | None = None, store_id: str = "",
        status: str = "준비", managers: list[str] | None = None) -> tuple[bool, str]:
    """신규 매장 등록. 반환 (성공, 메시지). 이름·id 중복이면 실패."""
    name = (name or "").strip()
    if not name:
        return False, "매장명이 비어 있습니다."
    with _LOCK:
        data = load()
        stores = data.setdefault("stores", [])
        sid = (store_id or "").strip() or slugify(name)
        for s in stores:
            if s["id"] == sid or s.get("name") == name:
                return False, f"이미 등록된 매장입니다 — {s.get('name')} ({s['id']})"
        stores.append({
            "id": sid, "name": name,
            "aliases": sorted({a.strip() for a in (aliases or []) if a.strip()} | {name}),
            "status": status, "managers": managers or [],
        })
        data["updated"] = date.today().isoformat()
        tmp = REGISTRY.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(REGISTRY)  # 원자적 교체 — 봇이 읽는 중 깨진 JSON을 보지 않게
    return True, f"{name} ({sid}) 등록 완료"


def summary_lines() -> list[str]:
    """매장 목록 표시용 라인."""
    out = []
    for s in active_stores():
        mgr = ", ".join(s.get("managers") or []) or "담당 미지정"
        out.append(f"• {s['name']} [{s['id']}] · {s.get('status', '운영')} · {mgr}")
    return out or ["등록된 매장이 없습니다."]
