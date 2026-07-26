"""'오늘 하기로 한 일' 선언 — 담당자 본인이 고르는 하루 계획의 단일 출처.

노션 PM 갭 분석 2차(2026-07-26, 갭C): 노션 템플릿의 '오늘 할 일' 체크박스가 하는 역할.
ARISA의 '오늘'은 전부 시스템이 산출한 것이었다 — 마감·지연 기반 자동 추출(A1)과 대표창
today_focus(LLM). 담당자가 스스로 "오늘은 이 3개를 한다"고 선언하는 층이 없어서
**계획 대비 실행률**(선언 3건 중 2건 완료)을 아무도 볼 수 없었다.

저장: <DATA>/today-plan/<YYYY-MM-DD>.json = {"이름": ["<row>|<task앞부분>", ...]}
  · 날짜별 파일이라 과거 기록이 자연히 남는다(하루 단위 스냅샷, 이력 로그는 두지 않음)
  · 키에 시트 row를 쓰되 task 앞부분을 함께 넣어, 행이 밀렸을 때 엉뚱한 업무가
    선언 상태를 물려받지 않게 한다(둘 다 맞아야 같은 항목)

원칙: 파일 I/O만 담당하고 권한 검증은 호출측(서버) 책임.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DIR_NAME = "today-plan"
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def make_key(row, task) -> str:
    """분장 1건의 선언 키 — 시트 행 + 업무명 앞부분."""
    try:
        r = int(row)
    except (TypeError, ValueError):
        return ""
    t = (task or "").strip()[:40]
    return f"{r}|{t}" if t else ""


def _path(data_dir, date_str) -> Path:
    return Path(data_dir) / DIR_NAME / f"{date_str}.json"


def load_day(data_dir, date_str) -> dict:
    """그 날짜의 전체 선언 {이름: [키…]}. 파일이 없으면 빈 dict."""
    if not _DATE_RE.fullmatch(date_str or ""):
        return {}
    try:
        d = json.loads(_path(data_dir, date_str).read_text(encoding="utf-8"))
    except Exception:
        return {}
    return d if isinstance(d, dict) else {}


def load_person(data_dir, date_str, name) -> list:
    """그 날짜의 내 선언 키 목록."""
    v = load_day(data_dir, date_str).get(name or "")
    return list(v) if isinstance(v, list) else []


def toggle(data_dir, date_str, name, key, on: bool) -> list:
    """선언 추가/해제 후 그 사람의 최신 키 목록 반환. 키가 비면 변경 없이 현재 목록."""
    if not (key and name and _DATE_RE.fullmatch(date_str or "")):
        return load_person(data_dir, date_str, name)
    day = load_day(data_dir, date_str)
    keys = [k for k in (day.get(name) or []) if isinstance(k, str)]
    if on and key not in keys:
        keys.append(key)
    elif not on:
        keys = [k for k in keys if k != key]
    day[name] = keys
    p = _path(data_dir, date_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(day, ensure_ascii=False, indent=2), encoding="utf-8")
    return keys


def summarize(keys, assigns, status_mod) -> dict:
    """선언한 항목의 진행 요약 — {"planned", "done", "percent", "stale"}.

    stale = 선언했지만 현재 분장 목록에서 사라진 항목 수(삭제·행 이동). 분모에서 뺀다.
    """
    keyset = set(keys or [])
    if not keyset:
        return {"planned": 0, "done": 0, "percent": 0, "stale": 0}
    live = {}
    for a in (assigns or []):
        k = make_key(a.get("row"), a.get("task"))
        if k in keyset:
            live[k] = a
    done = sum(1 for a in live.values() if status_mod.is_assign_done(a.get("status")))
    planned = len(live)
    return {"planned": planned, "done": done,
            "percent": round(done * 100 / planned) if planned else 0,
            "stale": len(keyset) - planned}
