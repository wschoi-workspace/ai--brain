"""주간분장 시트 접근 — 컬럼 정의·파싱·상태 갱신의 단일 출처.

노션 가이드 대조(2026-07-26): '보고 → 상태 환류'를 봇에도 붙이려면 봇이 분장을 읽어야
하는데, 파싱 로직이 dashboard-server 안에만 있었다. 세 번째 사본을 만들지 않기 위해
컬럼 정의를 여기로 올린다(dashboard-server._assign_read가 이 모듈을 호출).

시트 헤더(A~O): 날짜·프로젝트명·팀구분·담당자·업무내용·일정(완료예상)·결과물·상태·
                이해관계자·우선순위·프로젝트ID(K)·등록자(L)·출처(M)·출처ID(N)·유형(O)
시트 헤더(P~W): 진행률(P)·완료예상일ETA(Q)·진행률갱신시각(R)·
                완료일(S)·완료자(T)·산출물링크(U)·보고대상(V)·보고완료시각(W)

원칙: gws 핸들은 주입받는다(호출측이 shared.gws를 넘긴다). 이 모듈은 I/O를 소유하지 않는다.
"""
from __future__ import annotations

TAB = "주간분장"
READ_RANGE = f"{TAB}!A2:W5000"
COLS = 23
STATUS_COL = "H"   # 상태 — 전이 시 갱신 대상

# ── P~W 확장 (vNext Phase 1, 2026-08) ────────────────────────────────
# A~O는 한 칸도 건드리지 않는다. parse_row가 짧은 행을 빈 문자열로 패딩하므로
# 기존 15칸 행은 P~W가 전부 ""로 안전하게 읽힌다 — 시트 마이그레이션 0.
#
# 왜 기존 컬럼을 재사용하지 않는가:
#  · Q(ETA) ≠ F(일정/완료예상) — follow-up 답변을 F에 쓰면 is_overdue()가 매번
#    리셋돼 지연 통계가 세탁된다. F=원래 약속, Q=지금 예측, 격차가 곧 지연 신호다.
#  · U(산출물 링크) ≠ G(결과물) — G는 set_result()가 자유서술로 이미 쓰고 있다.
#    여기에 URL을 강제하면 살아 있는 동작이 깨진다. 완료 판정은 `G or U`.
#
# 블록 배치인 이유: gws.py에 batchUpdate가 없고 매 호출이 subprocess 1회다.
# 연속 범위로 두면 8칸을 P:R + S:W = 2회 write로 끝낸다(개별이면 8회).
PROGRESS_RANGE = ("P", "R")     # 진행 블록 — progress, eta, progress_at
COMPLETION_RANGE = ("S", "W")   # 완료 블록 — done_at, done_by, deliverable, report_to, reported_at

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
         "type": norm_type(r[14]),
         # P~W — 구행(15칸)은 전부 "" 로 채워진다
         "progress": (r[15] or "").strip(), "eta": (r[16] or "").strip(),
         "progress_at": (r[17] or "").strip(),
         "done_at": (r[18] or "").strip(), "done_by": (r[19] or "").strip(),
         "deliverable": (r[20] or "").strip(), "report_to": (r[21] or "").strip(),
         "reported_at": (r[22] or "").strip()}
    a["days_overdue"] = (status_mod.overdue_days(a["deadline"])
                         if status_mod.is_overdue(a["deadline"], a["status"]) else 0)
    a["progress_pct"] = status_mod.effective_progress(a)
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


def _now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def set_progress(gws, sheet_id, row, pct, eta="", status_mod=None,
                 ts=None, timeout: int = 20) -> bool:
    """P:R(진행률·ETA·갱신시각) 1회 write.

    ETA를 F열(마감)에 쓰지 않는 것이 이 함수의 존재 이유다 — 모듈 상단 주석 참조.
    pct가 형식 오류면 P는 빈칸으로 두고 ETA만 기록한다(부분 입력 허용).
    """
    if not (gws and sheet_id and row):
        return False
    p = ""
    if status_mod is not None:
        n = status_mod.norm_progress(pct)
        p = "" if n is None else str(n)
    elif pct not in (None, ""):
        p = str(pct)
    eta = (eta or "").strip()[:10]
    if not (p or eta):
        return False
    lo, hi = PROGRESS_RANGE
    try:
        return bool(gws.values_update(sheet_id, f"{TAB}!{lo}{int(row)}:{hi}{int(row)}",
                                      [[p, eta, ts or _now_iso()]], timeout=timeout))
    except Exception:
        return False


def set_completion(gws, sheet_id, row, *, done_at="", done_by="", deliverable="",
                   report_to="", reported_at="", timeout: int = 20) -> bool:
    """S:W(완료 5요소) 1회 write.

    호출측은 이걸 **상태(H열) 갱신보다 먼저** 부른다. 반대 순서면 S:W 실패 시
    '완료인데 5요소 공란'인 유령 행이 남는다(되돌릴 주체가 없다).
    """
    if not (gws and sheet_id and row):
        return False
    vals = [(done_at or "").strip()[:10], (done_by or "").strip()[:40],
            (deliverable or "").strip()[:300], (report_to or "").strip()[:100],
            (reported_at or "").strip()[:19]]
    if not any(vals):
        return False
    lo, hi = COMPLETION_RANGE
    try:
        return bool(gws.values_update(sheet_id, f"{TAB}!{lo}{int(row)}:{hi}{int(row)}",
                                      [vals], timeout=timeout))
    except Exception:
        return False


def completion_missing_rows(assigns, status_mod, completion_mod, assignee=None) -> list:
    """완료·승인인데 완료 근거가 빈 행 → [분장 + missing]. 대시보드 '완료 정보 누락' 큐.

    incomplete()와 같은 모양이다(호출측 렌더 재사용). 쓰기 실패로 남은 유령 행도
    여기로 떠오르므로 사람이 복구할 수 있다.
    """
    out = []
    for a in (assigns or []):
        if a.get("status") not in status_mod.ASSIGN_DONE_STATES:
            continue
        if assignee and a.get("assignee") != assignee:
            continue
        miss = completion_mod.missing(a)
        if miss:
            out.append({**a, "missing": miss})
    out.sort(key=lambda x: (x.get("assignee") or "", x.get("row") or 0))
    return out


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
        cur = gws.values_get(sheet_id, f"{TAB}!A{int(row)}:W{int(row)}",
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
