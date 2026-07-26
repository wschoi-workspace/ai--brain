"""주간분장 시트 접근 — 컬럼 정의·파싱·상태 갱신의 단일 출처.

노션 가이드 대조(2026-07-26): '보고 → 상태 환류'를 봇에도 붙이려면 봇이 분장을 읽어야
하는데, 파싱 로직이 dashboard-server 안에만 있었다. 세 번째 사본을 만들지 않기 위해
컬럼 정의를 여기로 올린다(dashboard-server._assign_read가 이 모듈을 호출).

시트 헤더(A~N): 날짜·프로젝트명·팀구분·담당자·업무내용·일정(완료예상)·결과물·상태·
                이해관계자·우선순위·프로젝트ID(K)·등록자(L)·출처(M)·출처ID(N)

원칙: gws 핸들은 주입받는다(호출측이 shared.gws를 넘긴다). 이 모듈은 I/O를 소유하지 않는다.
"""
from __future__ import annotations

TAB = "주간분장"
READ_RANGE = f"{TAB}!A2:N5000"
COLS = 14
STATUS_COL = "H"   # 상태 — 전이 시 갱신 대상


def parse_row(r, sheet_row: int, status_mod) -> dict:
    """시트 1행 → 분장 dict. 짧은 구행(12칸 이하)도 안전하게 채운다."""
    r = list(r) + [""] * (COLS - len(r))
    a = {"row": sheet_row,
         "date": (r[0] or "").strip(), "project": (r[1] or "").strip(),
         "team": (r[2] or "").strip(), "assignee": (r[3] or "").strip(),
         "task": (r[4] or "").strip(), "deadline": (r[5] or "").strip(),
         "result": (r[6] or "").strip(), "status": status_mod.norm_assign_status(r[7]),
         "stakeholder": (r[8] or "").strip(), "priority": status_mod.norm_priority(r[9]),
         "pid": (r[10] or "").strip(), "by": (r[11] or "").strip(),
         "source": (r[12] or "").strip(), "source_ref": (r[13] or "").strip()}
    a["days_overdue"] = (status_mod.overdue_days(a["deadline"])
                         if status_mod.is_overdue(a["deadline"], a["status"]) else 0)
    return a


def parse_all(rows, status_mod) -> list:
    """values_get 결과(A2부터) → 분장 dict 리스트."""
    return [parse_row(r, i + 2, status_mod) for i, r in enumerate(rows or [])]


def read(gws, sheet_id, status_mod, retries: int = 2, timeout: int = 20) -> list:
    """주간분장 전체 읽기. 시트 미설정·실패 시 [] (호출측 화면이 죽지 않게)."""
    if not (gws and sheet_id):
        return []
    try:
        rows = gws.values_get(sheet_id, READ_RANGE, retries=retries, timeout=timeout)
    except Exception:
        return []
    return parse_all(rows, status_mod)


def open_for(assigns, name, status_mod) -> list:
    """그 사람의 '열린' 분장(미착수·진행중·검토중·승인대기·보류)."""
    return [a for a in (assigns or [])
            if a.get("assignee") == name and a.get("status") in status_mod.ASSIGN_OPEN_STATES]


def set_status(gws, sheet_id, row, status, timeout: int = 20) -> bool:
    """H열 상태 갱신. row는 시트 실제 행 번호."""
    if not (gws and sheet_id and row):
        return False
    try:
        return bool(gws.values_update(sheet_id, f"{TAB}!{STATUS_COL}{int(row)}",
                                      [[status]], timeout=timeout))
    except Exception:
        return False


# 노션 가이드 §4.1 '⚠️입력누락' — 이게 비면 업무가 아니라 메모다.
# 담당자는 '미지정 큐'(A2)가 이미 잡으므로 여기서는 마감·프로젝트만 본다.
REQUIRED_FIELDS = (("deadline", "마감일"), ("project", "프로젝트"))


def missing_fields(a) -> list:
    """이 분장에서 비어 있는 필수 항목 이름 목록. 완결이면 []."""
    a = a or {}
    return [label for key, label in REQUIRED_FIELDS if not (a.get(key) or "").strip()]


def incomplete(assigns, status_mod, assignee=None) -> list:
    """열린 분장 중 필수 항목이 빈 것 → [분장 + missing]. 마감 없는 것을 앞에 둔다.

    마감이 없으면 지연 판정이 아예 작동하지 않는다(is_overdue가 비ISO를 지연 아님으로
    처리) — 화면에서 영원히 늦지 않는 업무가 되므로 프로젝트 누락보다 먼저 보여준다.
    """
    out = []
    for a in (assigns or []):
        if a.get("status") not in status_mod.ASSIGN_OPEN_STATES:
            continue
        if assignee and a.get("assignee") != assignee:
            continue
        miss = missing_fields(a)
        if miss:
            out.append({**a, "missing": miss})
    out.sort(key=lambda x: (0 if "마감일" in x["missing"] else 1,
                            x.get("assignee") or "", x.get("row") or 0))
    return out


def task_sig(task) -> str:
    """업무명 지문 6자 — 텔레그램 callback_data(64B 제한)에 업무 동일성을 실어 보내기 위한 것."""
    import hashlib
    return hashlib.sha1(((task or "").strip()[:40]).encode("utf-8")).hexdigest()[:6]


def verify_row(gws, sheet_id, row, expect_assignee, status_mod,
               expect_task=None, expect_sig=None, timeout: int = 20):
    """행이 아직 그 사람의 그 업무인지 확인 후 dict 반환, 아니면 None.

    시트는 행이 밀릴 수 있다(삽입·삭제). 상태를 바꾸기 전에 반드시 대조한다 —
    엉뚱한 사람의 업무를 완료 처리하는 사고를 막는 지점.
    업무 동일성은 원문(expect_task) 또는 지문(expect_sig) 중 주어진 쪽으로 확인한다.
    """
    if not (gws and sheet_id and row):
        return None
    try:
        cur = gws.values_get(sheet_id, f"{TAB}!A{int(row)}:N{int(row)}",
                             retries=2, timeout=timeout)
    except Exception:
        return None
    if not cur:
        return None
    a = parse_row(cur[0], int(row), status_mod)
    if expect_task is not None and (a["task"] or "")[:40] != (expect_task or "")[:40]:
        return None
    if expect_sig and task_sig(a["task"]) != expect_sig:
        return None
    if expect_assignee and a["assignee"] != expect_assignee:
        return None
    return a
