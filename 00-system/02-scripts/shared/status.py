"""공유 상태·우선순위 표준 — 분장 시트(한글)·프로젝트 tasks(영문)·brief 상태의 단일 정의.

G2 (2026-07-18 노션 PM 갭 분석): dashboard-server / daily-brief-aggregate /
weekly-report-aggregate에 흩어져 있던 판정 튜플·매핑·뱃지 클래스의 단일 출처.
값 자체는 기존 운영값과 동일하게 보존한다(무마이그레이션 — 시트·JSON 데이터 불변).

상태 어휘를 바꾸려면(예: '보류' 추가, P0/P1/P2 도입) 이 파일만 수정한다.
"""
from __future__ import annotations

from datetime import date as _date

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

# ── 상태 전이 그래프 (WS2, 2026-07-27) — 허용 from→to 의 SSOT ─────────
# 도입 배경: 어휘(ASSIGN_STATES)만 있고 전이 규칙이 없어서, 자동 배치가 사람의 판단을
# 덮어쓰고 있었다. weekly-report-aggregate.update_assignment_status_in_sheet는 예외가
# '미착수' 하나뿐이어서 매주 월 08:30에 검토중·승인대기·보류 카드를 진행중으로
# 되돌렸다. daily-brief의 자동 완료도 want_from이 없어 승인대기→완료로 역행했다.
# kanban-skill(Apache-2.0) 차용: 게이트를 코드 분기가 아니라 데이터 규칙으로 둔다.
#
# 어휘를 추가하면 이 두 테이블도 함께 고친다. 빠뜨리면 그 상태는 '나갈 수 없는 상태'가 된다.
_T5 = ASSIGN_TERMINAL_STATES  # 패스·취소·미실행종료·일정경과종료·다른업무로통합

# 사람(대시보드 버튼·리더 검토·PM 클리어·봇 ✓완료) 기준.
# '삭제'는 테이블에 넣지 않는다 — 모든 from에서 무조건 허용(아래 can_transition 특례).
# 일괄삭제(최대 200건)·프로젝트 삭제가 게이트에 걸리면 운영이 마비된다.
TRANSITIONS = {
    # 완료 직행 허용 — 짧은 업무를 미착수에서 바로 닫는 실제 동작 보존
    "미착수":   ("진행중", "검토중", "보류", "완료") + _T5,
    "진행중":   ("검토중", "완료", "보류", "미착수") + _T5,   # 미착수 복귀 = 오조작 정정
    # 진행중=반려(/api/assign-review action=return), 승인=PM 부재 시 리더 전결
    "검토중":   ("진행중", "승인대기", "승인", "완료", "보류") + _T5,
    # 진행중=PM_CLEAR_EFFECTS['수정필요'], 패스=['패스'], 승인=['정상완료']
    "승인대기": ("승인", "진행중", "보류", "패스") + _T5,
    "보류":     ("진행중", "미착수", "검토중", "완료") + _T5,
    # 담당자 완료 보고 상태 — 리더 검토가 여기서 출발한다(approval.next_step)
    "완료":     ("승인대기", "승인", "진행중", "검토중", "보류") + _T5,
    "승인":     (),          # 종결. 되살리기는 ADMIN_ONLY
    "삭제":     ("미착수", "진행중"),   # 오삭제 복구
}
# 종료 5종 → 되살리기 (리더·PM·대표가 종료를 취소하는 경우)
for _t in _T5:
    TRANSITIONS[_t] = ("진행중", "미착수")
del _t

# 자동 소스(보고 문장·키워드 매칭) — 사람 테이블의 좁은 부분집합.
# 사람이 세운 판단(검토중·승인대기·보류)을 배치가 건드리지 못하게 하는 것이 이 테이블의 전부다.
AUTO_TRANSITIONS = {
    "미착수": ("진행중", "완료"),
    "진행중": ("완료",),
}

# 대표만 가능한 예외 전이 — 승인된 업무 재개
ADMIN_ONLY = (("승인", "진행중"), ("승인", "완료"), ("승인", "검토중"))

# status_log의 source 값 기준 분류 (log_status_change docstring과 동일 어휘)
AUTO_SOURCES = ("daily-brief-auto", "weekly-auto")
# 사람이 버튼을 눌렀고 verify_row로 본인·업무 동일성까지 재확인한 전이 → 사람 취급
# report-followup(봇 진행률 되묻기 응답)도 verify_row를 두 번 통과한 뒤에만 쓴다 — 사람 취급.
CONFIRMED_SOURCES = ("report-sync", "report-followup")

ENFORCE_FROM = _date(2026, 8, 17)   # 3주 shadow 후 전환 (report_score.GRACE_END와 겹치지 않게)
ENV_MODE_KEY = "ARISA_TRANSITION_MODE"   # shadow|enforce|off — plist env 1줄로 즉시 롤백

# ── 우선순위 (주간분장 시트 J열) ──────────────────────────────────────
PRIORITIES = ("일반", "긴급")
PRIORITY_DEFAULT = "일반"

# ── 프로젝트 tasks 상태 (프로젝트 JSON SSOT) — 영문 canonical ─────────
TASK_STATES = ("Not Started", "In Progress", "Done")
TASK_DEFAULT = "Not Started"
# 과거 데이터에 한글 '완료'가 섞여 있어 판정은 양쪽 허용 (기존 동작 보존)
TASK_DONE_STATES = ("Done", "완료")

# ── 프로젝트 brief 상태 (LLM 산출 허용값) ─────────────────────────────
# Hold = 보류(재개 전제) / Dropped = 중단·무산(재개 없이 종료) — 아카이브 시 구분해 기록한다
BRIEF_STATES = ("Not Started", "In Progress", "On Track", "At Risk", "Hold", "Done", "Dropped")

# 프로젝트 중단 사유 귀속 — 책임 소재를 남겨야 회고가 학습으로 이어진다
DROP_CAUSES = {
    "client": "클라이언트 사유",      # 예산 철회·방향 전환·발주 취소
    "internal": "우리 측 사유",       # 역량·일정·리소스·관리 미흡
    "external": "외부·시장 요인",     # 수요 부족·규제·환경 변화
}

# ── 매핑: 분장(한글) → 태스크(영문) / 진행률 ─────────────────────────
# 종료 5종은 매핑하지 않음 — 소비처가 ASSIGN_DROPPED_STATES로 먼저 걸러낸다(삭제와 동일 취급)
ASSIGN_TO_TASK = {"미착수": "Not Started", "진행중": "In Progress",
                  "검토중": "In Progress", "승인대기": "In Progress", "보류": "In Progress",
                  "완료": "Done", "승인": "Done"}
ASSIGN_TO_PROGRESS = {"미착수": 0, "진행중": 50, "검토중": 70, "승인대기": 90, "보류": 30,
                      "완료": 100, "승인": 100}

# ── 진행률 밴드 (vNext Phase 1) — 상태가 아니라 '표시 라벨'이다 ────────
# 대표 원안의 5단계(Not Started 0 / Planning 20 / In Progress 50 / Review 80 / Done 100)를
# ASSIGN_STATES에 새 상태로 추가하지 않는다. 어휘 13종·TRANSITIONS는 불변이 계약이다.
# 대신 진행률을 독립 축으로 두면 "상태는 미착수인데 20% 입력된 행"이 Planning을 자연히
# 흡수한다 — 없던 상태를 만들지 않고 원안의 의도를 만족시키는 유일한 방법.
PROGRESS_BANDS = ((100, "Done"), (80, "Review"), (50, "In Progress"),
                  (1, "Planning"), (0, "Not Started"))
# 진행률이 이 일수만큼 안 움직인 '진행중' 분장 = follow-up 우선 대상 (coach·followup 공용)
PROGRESS_STALE_DAYS = 5

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


def norm_progress(raw):
    """시트 P열 원문 → 0~100 정수, 미입력·형식오류는 None.

    None과 0을 구분하는 것이 이 함수의 전부다. 0으로 뭉개면 '아직 안 적었다'와
    '적었는데 0%다'가 같아져서 effective_progress가 실입력을 무시하게 된다.
    """
    s = str(raw if raw is not None else "").strip().rstrip("%").strip()
    if not s:
        return None
    try:
        n = int(float(s))
    except (TypeError, ValueError):
        return None
    return max(0, min(100, n))


def effective_progress(a) -> int:
    """분장 1건의 진행률 — 사람이 적은 값(P열)이 상태 파생 사다리보다 우선.

    P열이 비면 ASSIGN_TO_PROGRESS를 그대로 반환하므로 기존 동작이 보존된다
    (무마이그레이션). 완료·승인은 실입력이 무엇이든 100 — 닫힌 업무가 70%로
    남아 롤업을 갉아먹는 것을 막는다.
    """
    a = a or {}
    st = a.get("status") or ""
    if st in ASSIGN_DONE_STATES:
        return 100
    p = norm_progress(a.get("progress"))
    return p if p is not None else ASSIGN_TO_PROGRESS.get(st, 0)


def progress_band(pct) -> str:
    """0~100 → 대표 어휘 라벨. 표시 전용이며 데이터에 쓰지 않는다."""
    n = norm_progress(pct)
    if n is None:
        return "Not Started"
    for floor, label in PROGRESS_BANDS:
        if n >= floor:
            return label
    return "Not Started"


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


# ── 상태 전이 게이트 (WS2) ────────────────────────────────────────────
def source_class(source) -> str:
    """status_log의 source → "human" | "auto".

    report-sync(봇 ✓완료 버튼)는 auto가 아니다 — verify_row로 본인·업무를 재확인한
    뒤에만 쓰므로 사람이 확인한 전이다. 계층을 대시보드/봇/배치 3단으로 늘리지 않는다
    (테이블이 3배가 되는데 12명 규모에서 얻는 게 없다).
    """
    return "auto" if (source or "").strip() in AUTO_SOURCES else "human"


def transition_mode(today=None) -> str:
    """shadow | enforce | off. 환경변수가 날짜보다 우선.

    report_score.current_mode()와 동형 — 같은 운영 패턴을 두 번 배우지 않게 한다.
    """
    import os
    env = (os.environ.get(ENV_MODE_KEY) or "").strip().lower()
    if env in ("shadow", "enforce", "off"):
        return env
    return "enforce" if (today or _date.today()) >= ENFORCE_FROM else "shadow"


def can_transition(from_status, to_status, source="dashboard", admin=False) -> tuple:
    """전이 허용 여부 판정 — 모드 무관 순수 함수. (허용?, 위반사유).

    fail-open: 어휘 밖 상태값(빈값·구 데이터·오타)은 항상 통과시킨다. 알 수 없는
    과거값 때문에 운영이 멈추는 사고를 원칙적으로 배제한다 — norm_assign_status는
    화이트리스트 검증을 하지 않으므로 시트에 어휘 밖 값이 있을 수 있다.
    """
    frm = (from_status or "").strip()
    to = (to_status or "").strip()
    if frm == to:
        return (True, "")                      # no-op
    if frm not in ASSIGN_STATES or to not in ASSIGN_STATES:
        return (True, "")                      # fail-open
    if to == "삭제":
        return (True, "")                      # 일괄삭제·프로젝트 삭제 보호
    cls = source_class(source)
    table = AUTO_TRANSITIONS if cls == "auto" else TRANSITIONS
    if to in table.get(frm, ()):
        return (True, "")
    if cls == "human" and admin and (frm, to) in ADMIN_ONLY:
        return (True, "")
    why = f"{frm} → {to} 불가"
    if cls == "auto":
        why += f" (자동 갱신 {source})"
    elif (frm, to) in ADMIN_ONLY:
        why += " (대표만 가능)"
    return (False, why)


def check_transition(from_status, to_status, source="dashboard", admin=False,
                     today=None) -> tuple:
    """(쓰기를 진행해도 되는가, 위반사유).

    shadow 모드면 위반이어도 True를 주고 사유 문자열만 채운다. 호출측 분기가 ok
    하나뿐이므로 enforce 플립에 코드 변경이 없다 — 사유가 있으면 note에 실어
    log_status_change 하면 3주 뒤 위반 실측이 그대로 쌓인다.
    """
    ok, why = can_transition(from_status, to_status, source, admin)
    if ok:
        return (True, "")
    mode = transition_mode(today)
    if mode == "off":
        return (True, "")
    return (mode == "shadow", why)


def transition_note(why, mode=None) -> str:
    """위반 사유 → status_log note 접두. 집계 grep 대상이므로 태그 문자열을 고정한다."""
    if not why:
        return ""
    m = mode or transition_mode()
    tag = "transition-shadow" if m == "shadow" else "transition-blocked"
    return f"[{tag}] {why}"


# ── 프로젝트 신호등 (WS3a) ────────────────────────────────────────────
# senior-pm(alirezarezvani/claude-skills)의 5차원 가중 헬스에서 차용. 프레임은 정의로
# 보존하고 코드는 실제로 데이터가 있는 축만 쓴다 — 실측(2026-07-27): budget+actual 1/21,
# brief.risk 3/21, status_log 1줄. Budget·Quality를 계산하면 20/21이 N/A인데 5차원처럼
# 보이는 거짓 정밀도가 된다. 데이터가 채워지면 차원을 켠다(확장 슬롯).
HEALTH_WEIGHTS = {"timeline": 25, "budget": 25, "scope": 20, "quality": 20, "risk": 10}
HEALTH_ACTIVE_DIMS = ("delivery",)   # 현재 코드가 실제로 쓰는 축 (분장 이행)
GRADES = ("green", "amber", "red", "gray")

# 신호등 임계 — 분장 이행 기준
SIGNAL_RED_OVERDUE = 3       # 지연 분장 건수
SIGNAL_RED_DAYS = 14         # 최장 경과일
SIGNAL_AMBER_DAYS = 7
SIGNAL_AMBER_ISSUES = 5      # 미해결 이슈가 이만큼 쌓이면 초록으로 두지 않는다


def project_signal(p, assigns=None, today=None) -> dict:
    """프로젝트 상태 신호등 — 분장 이행(지연 건수·최장 경과일)으로 판정.

    입력을 분장으로 잡은 이유(실측 2026-07-27): 프로젝트 JSON의 end/dday는 21개 중 20개가
    등록 주(7/16~22) 기준의 짧은 창이라 프로젝트 종료일로 쓸 수 없고, tasks.progress는
    자동 생성 골격이라 대부분 0%다. 이 둘로 판정하면 20/21이 빨강이 되어 정보가 0이 된다.
    사람이 매일 실제로 갱신하는 것은 주간분장(마감 F열·상태 H열)이며, 그것만이 지금
    신뢰할 수 있는 진척 신호다.

    일정 축(timeline)은 확장 슬롯으로 남긴다 — brief.end가 실제 종료일로 관리되기
    시작하면 켠다. HEALTH_WEIGHTS는 senior-pm 5차원 프레임의 정의로 보존한다.

    반환 {"grade": green|amber|red|gray, "score": 0~100|None, "why": 1줄, "na": bool}
    grade=gray는 '판정 보류'다 — 색을 칠하지 않는다(모르는 것을 초록으로 보이게 하지 않는다).
    score는 전주 대비 추세 화살표용이며 grade 판정에는 쓰지 않는다(규칙이 더 읽기 쉽다).
    """
    p = p or {}
    open_assigns = [a for a in (assigns or [])
                    if (a.get("status") or "") in ASSIGN_OPEN_STATES]
    issues = sum(1 for i in (p.get("issues") or [])
                 if not is_task_done((i or {}).get("status")))

    if not open_assigns:
        # 열린 분장이 없으면 진척을 말할 근거가 없다 — 완료됐는지 방치인지 여기서 알 수 없다
        return {"grade": "gray", "score": None, "na": True,
                "why": "열린 분장 없음 — 판정 보류"}

    ov = [overdue_days(a.get("deadline"), today) for a in open_assigns
          if is_overdue(a.get("deadline"), a.get("status"), today)]
    overdue = len(ov)
    worst = max(ov) if ov else 0
    total = len(open_assigns)
    on_time = total - overdue
    score = max(0, min(100, round(on_time * 100 / total) - 5 * issues))

    reds = []
    if overdue >= SIGNAL_RED_OVERDUE:
        reds.append(f"지연 {overdue}/{total}건")
    if worst >= SIGNAL_RED_DAYS:
        reds.append(f"최장 {worst}일 경과")
    if reds:
        return {"grade": "red", "score": score, "na": False, "why": " · ".join(reds)}

    ambers = []
    if overdue:
        ambers.append(f"지연 {overdue}/{total}건")
    if worst >= SIGNAL_AMBER_DAYS:
        ambers.append(f"최장 {worst}일 경과")
    if issues >= SIGNAL_AMBER_ISSUES:
        # 분장은 제때 가고 있어도 이슈가 쌓인 프로젝트를 초록으로 두면 오해가 생긴다
        ambers.append(f"미해결 이슈 {issues}건")
    if ambers:
        return {"grade": "amber", "score": score, "na": False, "why": " · ".join(ambers)}

    why = f"열린 {total}건 · 지연 없음"
    if issues:
        why += f" · 이슈 {issues}건"
    return {"grade": "green", "score": score, "na": False, "why": why}


def signal_missing(p) -> list:
    """신호등이 아직 쓰지 못하는 축 → 회색 라벨 목록.

    "데이터를 채우면 켜진다"는 신호가 곧 입력 유인이다 — 비어 있음을 숨기지 않는다.
    """
    p = p or {}
    b = p.get("brief") or {}
    out = []
    if not (str(b.get("budget") or "").strip() and str(b.get("actual") or "").strip()):
        out.append("예산 미기재")
    if not (p.get("tasks") or []):
        out.append("태스크 없음")
    if not ((p.get("end") or "").strip() or (p.get("dday") or "").strip()):
        out.append("종료일 미기재")
    return out
