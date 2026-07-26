"""업무 출처(provenance) 표준 — 분장이 '무엇에서' 나왔는지의 단일 정의.

노션 PM 갭 분석 2차(2026-07-26, 갭 A): 노션 템플릿은 회의↔할 일↔프로젝트를 양방향
relation으로 묶어 "이 회의에서 나온 액션이 실제로 완료됐는가"를 바로 본다. ARISA는
회의분석(R4·직원용)이 to-do를 5~12개 뽑아내고도 화면 산출물로 끝나 분장과 끊겨 있었다.

주간분장 시트 M열(출처)·N열(출처ID)의 어휘·조립·해석을 여기 모은다.
회의 ID는 새로 만들지 않고 **프로젝트 문서함의 (pid, ts)** 를 그대로 식별자로 쓴다
(dashboard-server `/api/simulator/submit-doc`이 생성 — DOC_DIR/<pid>/<ts>.json|.md).

원칙: 순수함수만 둔다(시트·파일 I/O는 호출측 책임).
"""
from __future__ import annotations

import re

# ── 출처 타입 (M열) — 빈값은 '미상'(구 데이터 전부) ────────────────────
SRC_MEETING = "회의"        # 회의분석 결과 → 액션 등록 (N열 = "<pid>|<ts>")
SRC_DAILY = "일일보고"      # 어제 보고에서 도출된 제안 수락 (N열 = 보고 날짜)
SRC_PLAN = "주간계획"       # 주간업무계획.xlsx 파싱 (N열 = 파일명)
SRC_DIRECT = "대표지시"     # 대표·리더의 직접 분장
SRC_SELF = "본인등록"       # 담당자 자발 등록
SOURCES = (SRC_MEETING, SRC_DAILY, SRC_PLAN, SRC_DIRECT, SRC_SELF)

_TS_RE = re.compile(r"\d{8}-\d{6}")


def meeting_ref(pid: str, ts: str) -> str:
    """(프로젝트ID, 문서 ts) → 출처ID 문자열. 형식 위반이면 빈 문자열."""
    pid = (pid or "").strip()
    ts = (ts or "").strip()
    if not pid or not _TS_RE.fullmatch(ts):
        return ""
    return f"{pid}|{ts}"


def parse_meeting_ref(ref):
    """출처ID → (pid, ts). 회의 참조가 아니면 (None, None)."""
    pid, sep, ts = (ref or "").strip().partition("|")
    if not (sep and pid and _TS_RE.fullmatch(ts)):
        return None, None
    return pid, ts


def is_meeting_action(a) -> bool:
    """분장 dict가 회의에서 파생된 것인가."""
    a = a or {}
    return (a.get("source") or "") == SRC_MEETING and bool(a.get("source_ref"))


def norm_due(raw) -> str:
    """회의 to-do의 기한 표기 → 시트 일정 문자열.

    LLM은 '미정'·'확인 필요'·'ASAP' 같은 값을 그대로 내보낸다. 마감으로 쓸 수 없는
    값은 빈 문자열로 떨어뜨린다 — status.is_overdue가 비ISO를 지연 아님으로 처리하므로
    '확인 필요'를 그대로 두면 영원히 지연 판정되지 않는 조용한 구멍이 된다.
    'M/D'·'M월 D일' 표기는 올해 기준 ISO로 정규화한다(연도 추정은 하지 않음).
    """
    s = (raw or "").strip()
    if not s or s in ("미정", "확인 필요", "확인필요", "TBD", "tbd", "-", "없음", "ASAP", "asap"):
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    m = re.fullmatch(r"(\d{1,2})\s*[/.\-월]\s*(\d{1,2})\s*일?", s)
    if m:
        import datetime as _dt
        mo, dy = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12 and 1 <= dy <= 31:
            try:
                return _dt.date(_dt.date.today().year, mo, dy).isoformat()
            except ValueError:
                return ""
    return ""  # 자유 텍스트(예: '오픈 전까지')는 마감으로 승격하지 않는다


def action_rollup(assigns, status_mod) -> dict:
    """회의 파생 분장 목록 → 실행률. (status 모듈을 주입받아 판정 SSOT 유지)

    반환: {"total", "done", "open", "overdue", "percent"}
    percent = 완료(완료·승인) / 전체. 종료 5종·삭제는 분모에서 제외한다 —
    '패스·취소'된 액션까지 미완으로 세면 회의 실행률이 부당하게 낮아진다.
    """
    live = [a for a in (assigns or [])
            if (a.get("status") or "") not in status_mod.ASSIGN_DROPPED_STATES]
    total = len(live)
    done = sum(1 for a in live if status_mod.is_assign_done(a.get("status")))
    overdue = sum(1 for a in live
                  if status_mod.is_overdue(a.get("deadline"), a.get("status")))
    return {"total": total, "done": done, "open": total - done, "overdue": overdue,
            "percent": round(done * 100 / total) if total else 0}
