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
SRC_DIRECT = "대표지시"     # 대표가 직접 분장 (N열 = 경로: 셸·텔레그램)
SRC_RELAY = "리더분장"      # 리더가 팀원에게 분장·이관
SRC_SELF = "본인등록"       # 담당자 자발 등록
SOURCES = (SRC_MEETING, SRC_DAILY, SRC_PLAN, SRC_DIRECT, SRC_RELAY, SRC_SELF)

# 출처 미상(빈값) = 이 체계 도입(2026-07-26) 이전 행. 집계에서 별도 표기한다.
SRC_UNKNOWN_LABEL = "출처 미상"

_TS_RE = re.compile(r"\d{8}-\d{6}")
# 회의 액션 ID (A1·S12 등) — 자유 텍스트가 출처ID로 흘러드는 것을 막는 좁은 형식 (WS1)
_ACTION_ID_RE = re.compile(r"[A-Z]\d{1,3}")


def meeting_ref(pid: str, ts: str, action_id: str = "") -> str:
    """(프로젝트ID, 문서 ts[, 액션 ID]) → 출처ID 문자열. 형식 위반이면 빈 문자열.

    WS1(2026-07-27): 3번째 세그먼트로 회의 액션 ID를 옵션 추가한다. 의존성 본문은
    문서함 JSON(doc["result"])에 이미 있으므로 시트에 복제하지 않고, 액션 단위로
    조인할 키만 얹는다 — 업무명으로 조인하면 /api/assign-edit의 업무명 편집에 조용히 깨진다.
    """
    pid = (pid or "").strip()
    ts = (ts or "").strip()
    if not pid or not _TS_RE.fullmatch(ts):
        return ""
    aid = (action_id or "").strip()
    if aid and _ACTION_ID_RE.fullmatch(aid):
        return f"{pid}|{ts}|{aid}"
    return f"{pid}|{ts}"


def parse_meeting_ref(ref):
    """출처ID → (pid, ts). 회의 참조가 아니면 (None, None).

    3세그먼트 형식도 받는다(액션 ID는 버림) — 기존 소비처의 시그니처를 바꾸지 않기 위해.
    """
    pid, ts, _ = parse_meeting_ref3(ref)
    return pid, ts


def parse_meeting_ref3(ref):
    """출처ID → (pid, ts, action_id). 회의 참조가 아니면 (None, None, "").

    레거시 2세그먼트("<pid>|<ts>")는 action_id를 ""로 돌려준다 — 왕복 보존.
    """
    parts = (ref or "").strip().split("|", 2)
    if len(parts) < 2:
        return None, None, ""
    pid, ts = parts[0].strip(), parts[1].strip()
    if not (pid and _TS_RE.fullmatch(ts)):
        return None, None, ""
    aid = parts[2].strip() if len(parts) > 2 else ""
    if aid and not _ACTION_ID_RE.fullmatch(aid):
        aid = ""      # 알 수 없는 3번째 세그먼트는 무시(참조 자체는 유효하게 둔다)
    return pid, ts, aid


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


def normalize_source(raw) -> str:
    """시트 M열 원문 → 알려진 출처 값. 모르는 값·빈값은 "" (미상)."""
    s = (raw or "").strip()
    return s if s in SOURCES else ""


def assign_source(is_admin_user: bool) -> str:
    """대표·리더의 직접 분장 출처. 누가 넣었는지(L열 by)와 별개로 '지시 경로'를 남긴다."""
    return SRC_DIRECT if is_admin_user else SRC_RELAY


def source_mix(assigns, status_mod=None) -> list:
    """업무 유입 출처 분포 → [{"source", "label", "count"}] (많은 순, 미상은 항상 끝).

    '업무가 어디서 생기는가'를 보는 집계 — 회의에서만 쏟아지는지, 대표 지시가 대부분인지.
    status_mod를 주면 삭제·종료 5종을 분모에서 뺀다(실제로 살아 있는 업무 기준).
    """
    rows = assigns or []
    if status_mod is not None:
        rows = [a for a in rows
                if (a.get("status") or "") not in status_mod.ASSIGN_DROPPED_STATES]
    cnt = {}
    for a in rows:
        cnt[normalize_source(a.get("source"))] = cnt.get(normalize_source(a.get("source")), 0) + 1
    known = sorted(((s, n) for s, n in cnt.items() if s), key=lambda x: (-x[1], x[0]))
    out = [{"source": s, "label": s, "count": n} for s, n in known]
    if cnt.get(""):
        out.append({"source": "", "label": SRC_UNKNOWN_LABEL, "count": cnt[""]})
    return out


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
