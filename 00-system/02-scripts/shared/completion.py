"""완료 5요소 — '완료'의 근거가 남게 하는 단일 출처 (vNext Phase 1).

대표 요구(2026-08): 완료는 체크가 아니다. 완료일·완료자·최종 산출물·보고 대상·
보고 완료 여부가 남아야 한다.

## 왜 status.py가 아니라 별도 파일인가
status.py는 '상태 전이' 축이고 이미 18.6KB다. 완료 근거는 그와 직교하는 축이라
섞으면 두 개념이 한 파일에서 얽힌다. approval.py·project_match.py와 같은 원칙 —
순수 함수만 두고 I/O·권한은 호출측 책임.

## 사람에게 묻지 않는 것이 설계의 요점
5요소 중 4개는 시스템이 이미 아는 사실이다.
  · 완료일   = 오늘 (09시 이전 제출은 전날 — 봇 finalize_and_send의 귀속 규칙 그대로)
  · 완료자   = 버튼을 누른 사람
  · 보고 대상 = approval.next_step()이 산출
  · 보고 완료 = _notify_approvers()가 텔레그램을 쏜 그 시각
사람에게 물으면 입력 부담만 늘고 정확도는 떨어진다. grace에서 실제로 묻는 것은
**산출물이 아무 데도 없을 때 1문항**뿐이고, strict가 막는 것도 산출물 하나다.

## 모드
report_score.current_mode()·status.transition_mode()와 동형이다. 같은 운영 패턴을
세 번 배우지 않게 한다. GRACE_END는 그 둘과 **다른 주**에 둔다 — 같은 주에 세 규칙이
동시에 조여지면 조직이 무엇 때문에 막혔는지 구분하지 못한다.
  report_score.GRACE_END = 2026-10-20 / status.ENFORCE_FROM = 2026-08-17
"""
from __future__ import annotations

from datetime import date as _date, datetime as _dt

GRACE_END = _date(2026, 11, 30)
ENV_MODE_KEY = "ARISA_COMPLETION_MODE"   # grace|strict|shadow|off — plist env 1줄로 롤백

# 완료 근거 5요소 — (분장 dict 키, 사람이 읽는 라벨)
FIELDS = (("done_at", "완료일"), ("done_by", "완료자"), ("deliverable", "최종 산출물"),
          ("report_to", "보고 대상"), ("reported_at", "보고 완료"))

# strict에서 실제로 차단하는 항목. 나머지 4개는 strict에서도 자동 충전이 유효하다
# (값의 출처가 사람의 기억이 아니라 시스템 사실이므로 물어볼 이유가 없다).
REQUIRED_IN_STRICT = ("deliverable",)

# 09시 이전 제출은 전날 업무로 귀속 (대표 지시 2026-07-20, 봇과 동일 규칙)
DAY_ROLLOVER_HOUR = 9


def current_mode(today=None) -> str:
    """grace | strict | shadow | off. 환경변수가 날짜보다 우선."""
    import os
    env = (os.environ.get(ENV_MODE_KEY) or "").strip().lower()
    if env in ("grace", "strict", "shadow", "off"):
        return env
    return "strict" if (today or _date.today()) > GRACE_END else "grace"


def is_link(s) -> bool:
    """산출물이 링크 형태인가. strict에서도 강제가 아니라 권고 — 오프라인 산출물이 존재한다."""
    t = (s or "").strip().lower()
    return t.startswith("http://") or t.startswith("https://")


def done_date(now=None) -> str:
    """완료일 자동값 — 09시 이전이면 전날. 봇 finalize_and_send의 귀속 규칙과 동일."""
    import datetime as _d
    n = now or _dt.now()
    d = n.date()
    if n.hour < DAY_ROLLOVER_HOUR:
        d = d - _d.timedelta(days=1)
    return d.isoformat()


def _has(a, key) -> bool:
    """그 요소가 채워져 있는가. 산출물만 G열(result) 폴백을 인정한다."""
    a = a or {}
    if (a.get(key) or "").strip():
        return True
    if key == "deliverable":
        # G열(결과물)은 set_result()가 자유서술로 이미 쓰고 있는 살아 있는 컬럼이다.
        # 여기에 URL을 강제하면 기존 동작이 깨지므로 `U or G`로 판정한다.
        return bool((a.get("result") or "").strip())
    return False


def missing(a) -> list:
    """비어 있는 완료 요소의 라벨 목록. 모드와 무관한 순수 판정."""
    return [label for key, label in FIELDS if not _has(a, key)]


def missing_required(a) -> list:
    """strict가 실제로 차단하는 항목만."""
    labels = dict(FIELDS)
    return [labels[k] for k in REQUIRED_IN_STRICT if not _has(a, k)]


def autofill(a, *, actor="", now=None, report_output="", report_to="") -> dict:
    """grace에서 자동으로 채울 값 → set_completion(**결과)에 그대로 넘긴다.

    이미 값이 있는 요소는 건드리지 않는다(사람이 고친 것을 배치가 덮지 않게).
    산출물 폴백 순서: U(기존) → G열 결과물 → 일일보고 core_tasks[].output
    """
    a = a or {}
    out = {}
    if not _has(a, "done_at"):
        out["done_at"] = done_date(now)
    if not _has(a, "done_by"):
        out["done_by"] = (actor or a.get("assignee") or "").strip()
    if not (a.get("deliverable") or "").strip():
        cand = (a.get("result") or "").strip() or (report_output or "").strip()
        if cand:
            out["deliverable"] = cand
    if not _has(a, "report_to") and (report_to or "").strip():
        out["report_to"] = report_to.strip()
    return out


def check(a, today=None) -> tuple:
    """(완료 처리를 진행해도 되는가, 빈 항목 라벨들).

    status.check_transition()과 같은 시그니처 형태다 — 호출측 분기 코드가 동일해서
    두 게이트를 한 번에 배우면 된다. shadow/grace는 통과시키고 사유만 채운다.
    """
    miss = missing_required(a)
    if not miss:
        return (True, [])
    mode = current_mode(today)
    if mode in ("off", "grace", "shadow"):
        return (True, miss)
    return (False, miss)


def completion_note(miss, mode=None) -> str:
    """빈 항목 → status_log note 접두. 집계 grep 대상이라 태그를 고정한다."""
    if not miss:
        return ""
    m = mode or current_mode()
    tag = "completion-blocked" if m == "strict" else "completion-%s" % m
    return "[%s] %s 없음" % (tag, "·".join(miss))
