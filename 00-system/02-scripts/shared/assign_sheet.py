"""주간분장 시트 접근 — 컬럼 정의·파싱·상태 갱신의 단일 출처.

노션 가이드 대조(2026-07-26): '보고 → 상태 환류'를 봇에도 붙이려면 봇이 분장을 읽어야
하는데, 파싱 로직이 dashboard-server 안에만 있었다. 세 번째 사본을 만들지 않기 위해
컬럼 정의를 여기로 올린다(dashboard-server._assign_read가 이 모듈을 호출).

시트 헤더(A~O): 날짜·프로젝트명·팀구분·담당자·업무내용·일정(완료예상)·결과물·상태·
                이해관계자·우선순위·프로젝트ID(K)·등록자(L)·출처(M)·출처ID(N)·유형(O)

원칙: gws 핸들은 주입받는다(호출측이 shared.gws를 넘긴다). 이 모듈은 I/O를 소유하지 않는다.
"""
from __future__ import annotations

TAB = "주간분장"
READ_RANGE = f"{TAB}!A2:O5000"
COLS = 15
STATUS_COL = "H"   # 상태 — 전이 시 갱신 대상

# 업무 유형(O열) — "우리 팀 시간이 어디로 가는가"를 보기 위한 축 (노션 가이드 §2.1 '유형').
# 등록 시 LLM이 추정하고 사람이 편집으로 고친다(입력 부담 0이 목표).
# 어휘를 바꾸려면 이 튜플만 고친다.
TASK_TYPES = ("기획", "제작", "운영", "영업", "행정")


def norm_type(raw) -> str:
    """시트 원문 → 업무 유형. 목록 밖·빈값은 "" (미분류)."""
    t = (raw or "").strip()
    return t if t in TASK_TYPES else ""


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
         "source": (r[12] or "").strip(), "source_ref": (r[13] or "").strip(),
         "type": norm_type(r[14])}
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


def set_status_guarded(gws, sheet_id, row, status, *, from_status, source,
                       status_mod, admin: bool = False, timeout: int = 20) -> tuple:
    """전이 게이트를 통과한 뒤 H열 갱신 (WS2). 반환 (시트 갱신됨?, 위반사유).

    반환값 구분:
      (True,  "")     정상 전이
      (True,  사유)   shadow 모드 위반 — 시트는 갱신됨, 호출측이 note에 사유를 남긴다
      (False, 사유)   enforce 차단 — 시트 불변
      (False, "")     게이트는 통과했으나 시트 쓰기 실패(네트워크·권한)

    로깅은 호출측 책임이다 — 경로마다 남길 필드(reason·approved_by·pid·note)가 다르고,
    여기서 로그까지 쓰면 기존 _log_st와 이중 기록이 된다. 위반사유가 비어 있지 않으면
    호출측은 status_mod.transition_note(사유)를 log_status_change의 note에 실어야 한다.
    """
    ok, why = status_mod.check_transition(from_status, status, source, admin)
    if not ok:
        return (False, why)
    return (set_status(gws, sheet_id, row, status, timeout=timeout), why)


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


def type_mix(assigns, status_mod) -> list:
    """업무 유형 분포 → [{"type","count"}] (많은 순, 미분류는 끝). 삭제·종료 5종 제외."""
    rows = [a for a in (assigns or [])
            if (a.get("status") or "") not in status_mod.ASSIGN_DROPPED_STATES]
    cnt = {}
    for a in rows:
        k = norm_type(a.get("type"))
        cnt[k] = cnt.get(k, 0) + 1
    out = [{"type": t, "count": n}
           for t, n in sorted(((t, n) for t, n in cnt.items() if t), key=lambda x: (-x[1], x[0]))]
    if cnt.get(""):
        out.append({"type": "미분류", "count": cnt[""]})
    return out


def set_type(gws, sheet_id, row, task_type, timeout: int = 20) -> bool:
    """O열(유형) 기록. 목록 밖 값은 쓰지 않는다."""
    t = norm_type(task_type)
    if not (gws and sheet_id and row and t):
        return False
    try:
        return bool(gws.values_update(sheet_id, f"{TAB}!O{int(row)}", [[t]], timeout=timeout))
    except Exception:
        return False


def set_result(gws, sheet_id, row, text, timeout: int = 20) -> bool:
    """G열(결과물) 기록 — 완료 시 '무엇을 남겼나'.

    실측(2026-07-26) 유효 분장 94건 전부 공란인 죽은 컬럼이었다. 사람에게 또 물어보는 대신
    일일보고에 이미 적힌 산출물(core_tasks[].output)을 완료 확정 시점에 옮겨 적는다.
    """
    text = (text or "").strip()[:300]
    if not (gws and sheet_id and row and text):
        return False
    try:
        return bool(gws.values_update(sheet_id, f"{TAB}!G{int(row)}", [[text]], timeout=timeout))
    except Exception:
        return False


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
        cur = gws.values_get(sheet_id, f"{TAB}!A{int(row)}:O{int(row)}",
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
