"""공유 상태·우선순위 표준 — 분장 시트(한글)·프로젝트 tasks(영문)·brief 상태의 단일 정의.

G2 (2026-07-18 노션 PM 갭 분석): dashboard-server / daily-brief-aggregate /
weekly-report-aggregate에 흩어져 있던 판정 튜플·매핑·뱃지 클래스의 단일 출처.
값 자체는 기존 운영값과 동일하게 보존한다(무마이그레이션 — 시트·JSON 데이터 불변).

상태 어휘를 바꾸려면(예: '보류' 추가, P0/P1/P2 도입) 이 파일만 수정한다.
"""
from __future__ import annotations

# ── 분장 상태 (주간분장 시트 H열, SSOT) — 한글 canonical ──────────────
# R4 개편 1차(2026-07-25): 검토 흐름 3종(검토중·승인대기·보류) + 종료 5종 추가.
# 기존 5값(미착수/진행중/완료/승인/삭제)은 값·의미 불변 — 시트 데이터 무마이그레이션.
ASSIGN_STATES = ("미착수", "진행중", "검토중", "승인대기", "보류",
                 "완료", "승인", "패스", "취소", "미실행종료", "일정경과종료",
                 "다른업무로통합", "삭제")
ASSIGN_DEFAULT = "미착수"
# 종료 상태 — 완료 없이 닫힘. 전이 시 사유(reason) 필수 (API 레이어에서 강제)
ASSIGN_TERMINAL_STATES = ("패스", "취소", "미실행종료", "일정경과종료", "다른업무로통합")
# 목록·집계에서 완전 제외 (status_log 이력에만 남음) — 종전 '삭제' 단독 필터의 일반화
ASSIGN_DROPPED_STATES = ("삭제",) + ASSIGN_TERMINAL_STATES
ASSIGN_DONE_STATES = ("완료", "승인")      # 완료 판정 (승인 포함)
ASSIGN_HIDDEN_STATES = ("승인",) + ASSIGN_DROPPED_STATES  # 내 업무·팀 목록에서 숨김
ASSIGN_OPEN_STATES = ("미착수", "진행중", "검토중", "승인대기", "보류")  # 미완(진행 대상)
ASSIGN_CLOSED_STATES = ASSIGN_DONE_STATES + ASSIGN_DROPPED_STATES  # 브리프 '이번주 할일'에서 제외
# 승인 대기 큐 판정 — 담당자 완료 보고(완료) + PM 검토 통과(승인대기, 2차 승인 체인)
ASSIGN_AWAITING_APPROVAL_STATES = ("완료", "승인대기")
# PM 클리어 선택지 (2차 /api/pm-clear에서 소비 — 어휘만 선정의)
PM_CLEAR_CHOICES = ("정상완료", "수정필요", "지연", "패스",
                    "대표보고필요", "대표결정필요", "대표지원필요")

# ── 우선순위 (주간분장 시트 J열) ──────────────────────────────────────
PRIORITIES = ("일반", "긴급")
PRIORITY_DEFAULT = "일반"

# ── 프로젝트 tasks 상태 (프로젝트 JSON SSOT) — 영문 canonical ─────────
TASK_STATES = ("Not Started", "In Progress", "Done")
TASK_DEFAULT = "Not Started"
# 과거 데이터에 한글 '완료'가 섞여 있어 판정은 양쪽 허용 (기존 동작 보존)
TASK_DONE_STATES = ("Done", "완료")

# ── 프로젝트 brief 상태 (LLM 산출 허용값) ─────────────────────────────
BRIEF_STATES = ("Not Started", "In Progress", "On Track", "At Risk", "Hold", "Done")

# ── 매핑: 분장(한글) → 태스크(영문) / 진행률 ─────────────────────────
# 종료 5종은 매핑하지 않음 — 소비처가 ASSIGN_DROPPED_STATES로 먼저 걸러낸다(삭제와 동일 취급)
ASSIGN_TO_TASK = {"미착수": "Not Started", "진행중": "In Progress",
                  "검토중": "In Progress", "승인대기": "In Progress", "보류": "In Progress",
                  "완료": "Done", "승인": "Done"}
ASSIGN_TO_PROGRESS = {"미착수": 0, "진행중": 50, "검토중": 70, "승인대기": 90, "보류": 30,
                      "완료": 100, "승인": 100}

# ── 표시: 분장 상태 → 뱃지 CSS 클래스 (daily-brief·weekly 공통) ───────
ASSIGN_BADGE_CLASS = {"완료": "as-done", "승인": "as-done", "진행중": "as-doing",
                      "검토중": "as-doing", "승인대기": "as-doing"}
ASSIGN_BADGE_DEFAULT = "as-todo"


def norm_assign_status(raw) -> str:
    """시트 원문 → 분장 상태 (빈값은 미착수)."""
    return (raw or "").strip() or ASSIGN_DEFAULT


def norm_priority(raw) -> str:
    """시트 원문 → 우선순위 (빈값은 일반)."""
    return (raw or "").strip() or PRIORITY_DEFAULT


def is_assign_done(st) -> bool:
    return (st or "") in ASSIGN_DONE_STATES


def is_task_done(st) -> bool:
    return (st or "") in TASK_DONE_STATES


def assign_to_task(st) -> str:
    return ASSIGN_TO_TASK.get(st or "", TASK_DEFAULT)


def assign_to_progress(st) -> int:
    return ASSIGN_TO_PROGRESS.get(st or "", 0)


def badge_class(st) -> str:
    return ASSIGN_BADGE_CLASS.get(st or "", ASSIGN_BADGE_DEFAULT)


def overdue_days(deadline, today=None) -> int:
    """마감 경과일 — 마감(YYYY-MM-DD)이 지났으면 경과일(≥1), 아니면 0.

    filament 반영(2026-07-20): '지연 N일' 배지·오늘 섹션·모닝 발송이 모두
    이 함수를 쓴다. 형식이 아니면(빈값·자유텍스트) 0 — 지연 아님으로 안전 처리.
    """
    import datetime as _dt
    dl = (deadline or "").strip()[:10]
    try:
        dld = _dt.date.fromisoformat(dl)
    except ValueError:
        return 0
    today = today or _dt.date.today()
    return max(0, (today - dld).days)


def is_overdue(deadline, status, today=None) -> bool:
    """지연 판정 — 열린 분장(완료·승인·삭제 제외)이고 마감이 지났는가."""
    if (status or "") in ASSIGN_CLOSED_STATES:
        return False
    return overdue_days(deadline, today) > 0


def task_rollup(tasks) -> dict:
    """프로젝트 진행률 자동 롤업 (G3 — 노션 'Task completion percent' 방식).

    저장하지 않고 tasks에서 파생 계산한다. percent 산식은 포트폴리오 상세 화면의
    기존 클라이언트 롤업과 동일: Done=100, 그 외는 task.progress(없으면 0)의 평균.
    반환: {"total": 전체 수, "done": 완료 수, "percent": 0~100}
    """
    tasks = tasks or []
    total = len(tasks)
    if not total:
        return {"total": 0, "done": 0, "percent": 0}
    done, acc = 0, 0
    for t in tasks:
        if is_task_done(t.get("status")):
            done += 1
            acc += 100
        else:
            try:
                acc += max(0, min(100, int(t.get("progress") or 0)))
            except (TypeError, ValueError):
                pass
    return {"total": total, "done": done, "percent": round(acc / total)}
