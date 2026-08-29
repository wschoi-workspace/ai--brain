"""공유 Google Workspace(gws CLI) 래퍼.

배치의 _gws_values_get(읽기)와 봇의 save_to_sheet/append_sheet(쓰기)를 단일 출처로.
기존 구현과 동일한 명령·재시도·타임아웃을 보존한다.

2026-07-04: 쓰기(append/update)에 재시도 + 인증장애 분류 추가.
  - 인증 장애(invalid_rapt 등)는 재시도해도 소용없으므로(수 시간~수일 지속) 즉시 실패 처리
  - append_to_sheet_ex()는 (성공여부, 실패종류 ''|'auth'|'transient')를 반환 — 호출부가
    실패를 로컬 큐(report_queue)로 보낼 수 있게 함. 기존 bool 시그니처는 그대로 유지.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import time

logger = logging.getLogger(__name__)

# gws stderr에서 재인증이 필요한(재시도 무의미) 장애를 식별하는 패턴
_AUTH_PATTERNS = ("invalid_rapt", "invalid_grant", "reauth", "unauthorized_client")


def _classify(stderr: str) -> str:
    """gws stderr → 'auth'(재인증 필요, 재시도 무의미) | 'transient'(일시 오류)."""
    s = (stderr or "").lower()
    return "auth" if any(p in s for p in _AUTH_PATTERNS) else "transient"


def _run_with_retry(cmd: list[str], label: str, retries: int = 3,
                    timeout: int = 15) -> tuple[bool, str]:
    """gws 쓰기 명령 실행 + 재시도(백오프 2s,4s). auth 장애는 즉시 중단.
    반환 (성공여부, 실패종류 ''|'auth'|'transient')."""
    kind = "transient"
    for attempt in range(retries):
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
            if r.returncode == 0:
                return True, ""
            kind = _classify(r.stderr)
            logger.error(f"{label} fail ({kind}, try {attempt+1}/{retries}): {r.stderr[:300]}")
            if kind == "auth":
                return False, "auth"  # 재인증 전엔 몇 번을 해도 실패 — 즉시 반환
        except Exception as e:  # noqa: BLE001
            logger.error(f"{label} error (try {attempt+1}/{retries}): {e}")
            kind = "transient"
        if attempt < retries - 1:
            time.sleep(2 * (attempt + 1))  # 2s, 4s
    return False, kind


def values_get(sheet_id: str, rng: str, retries: int = 3, timeout: int = 40) -> list[list]:
    """시트 범위 읽기 → 2차원 리스트. (배치 _gws_values_get 단일 출처)"""
    if not sheet_id:
        return []
    params = json.dumps({"spreadsheetId": sheet_id, "range": rng})
    for attempt in range(retries):
        try:
            r = subprocess.run(
                ["gws", "sheets", "spreadsheets", "values", "get", "--params", params],
                capture_output=True, text=True, timeout=timeout,
            )
            if r.returncode == 0:
                return json.loads(r.stdout or "{}").get("values", [])
            sys.stderr.write(f"[gws retry {attempt+1}] {rng}: {r.stderr[:120]}\n")
            if _classify(r.stderr) == "auth":
                break  # 인증 장애 — 재시도 무의미
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"[gws err {attempt+1}] {rng}: {e}\n")
        if attempt < retries - 1:
            time.sleep(2)
    return []


def append_to_sheet_ex(sheet_id: str, range_str: str, row: list,
                       value_input_option: str = "RAW", timeout: int = 15,
                       retries: int = 3) -> tuple[bool, str]:
    """시트 1행 append + 재시도. 반환 (성공여부, 실패종류 ''|'auth'|'transient')."""
    if not sheet_id:
        logger.warning("append_to_sheet: sheet_id 미설정 — 건너뜀")
        return False, "transient"
    cmd = [
        "gws", "sheets", "spreadsheets", "values", "append",
        "--params", json.dumps({
            "spreadsheetId": sheet_id, "range": range_str,
            "valueInputOption": value_input_option, "insertDataOption": "INSERT_ROWS",
        }),
        "--json", json.dumps({"values": [row]}),
    ]
    return _run_with_retry(cmd, f"sheet append({range_str})", retries=retries, timeout=timeout)


def append_to_sheet(sheet_id: str, range_str: str, row: list,
                    value_input_option: str = "RAW", timeout: int = 15) -> bool:
    """시트 1행 append. (봇 save_to_sheet / append_sheet / append_progress / log_todo 단일 출처)"""
    return append_to_sheet_ex(sheet_id, range_str, row, value_input_option, timeout)[0]


def values_update(sheet_id: str, rng: str, values: list[list],
                  value_input_option: str = "RAW", timeout: int = 15) -> bool:
    """시트 특정 범위 덮어쓰기 (분장 상태 업데이트 등)."""
    if not sheet_id:
        logger.warning("values_update: sheet_id 미설정 — 건너뜀")
        return False
    cmd = [
        "gws", "sheets", "spreadsheets", "values", "update",
        "--params", json.dumps({
            "spreadsheetId": sheet_id, "range": rng,
            "valueInputOption": value_input_option,
        }),
        "--json", json.dumps({"values": values}),
    ]
    return _run_with_retry(cmd, f"sheet update({rng})", timeout=timeout)[0]


# ── 캘린더 읽기 (2026-08-30, 대시보드 팀 일정표) ────────────────────────
# 레이아웃 원안(레이아웃1.pptx)이 전 화면 좌측에 '구글 팀일정표'를 두는데 연동이 없었다.
# 읽기 전용 — 일정 생성(events insert)은 권한 경계가 별건이라 여기 넣지 않는다.


def calendar_events(calendar_id: str, time_min: str, time_max: str,
                    limit: int = 50, retries: int = 2, timeout: int = 25) -> list[dict]:
    """캘린더 1개의 기간 내 일정 → items 리스트. 실패 시 [] (화면이 죽지 않게).

    time_min/time_max는 RFC3339(예: 2026-08-30T00:00:00+09:00).
    singleEvents=true로 반복 일정을 개별 인스턴스로 펼치고 시작시각 순 정렬한다.
    """
    if not calendar_id:
        return []
    params = json.dumps({
        "calendarId": calendar_id, "timeMin": time_min, "timeMax": time_max,
        "maxResults": max(1, min(int(limit), 250)),
        "singleEvents": True, "orderBy": "startTime",
    })
    for attempt in range(retries):
        try:
            r = subprocess.run(
                ["gws", "calendar", "events", "list", "--params", params],
                capture_output=True, text=True, timeout=timeout,
            )
            if r.returncode == 0:
                items = json.loads(r.stdout or "{}").get("items", [])
                return items if isinstance(items, list) else []
            sys.stderr.write(f"[gws cal retry {attempt+1}] {calendar_id}: {r.stderr[:120]}\n")
            if _classify(r.stderr) == "auth":
                break  # 인증 장애 — 재시도 무의미
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"[gws cal err {attempt+1}] {calendar_id}: {e}\n")
        if attempt < retries - 1:
            time.sleep(2)
    return []


# ── 드라이브 읽기 (2026-08-09, 사내 규정 질의응답) ──────────────────────
# 이 래퍼는 지금까지 시트만 다뤘다. 사내 규정 원본이 드라이브 .docx로 있어서 읽기가 필요해졌다.
#
# ⚠️ **폴더 화이트리스트를 인자로 강제한다.** 드라이브에는 `렌트_로그인/법인카드 정보`,
#    정산 시트, 인사기록 마스터가 함께 있다. "드라이브 전체 검색"을 가능하게 만들면
#    LLM이 그쪽으로 질의를 확장하는 순간 사고가 난다. folder_id 없이는 검색이 안 되게 둔다.
#
# ⚠️ .docx는 Drive `export`가 지원되지 않는다(Google Docs 네이티브만 가능).
#    다운로드 후 직접 파싱해야 한다 — 아래 docx_to_text 참조.


def drive_search(folder_id: str, name_contains: str = "", full_text: str = "",
                 limit: int = 20, timeout: int = 40) -> list[dict]:
    """지정 폴더 **안에서만** 파일 검색. folder_id가 없으면 아무것도 하지 않는다.

    반환: [{id, name, mimeType, modifiedTime}, ...]
    """
    if not folder_id:
        logger.error("drive_search: folder_id 필수 — 전체 드라이브 검색은 허용하지 않는다")
        return []
    clauses = [f'"{folder_id}" in parents', "trashed=false"]
    if name_contains:
        clauses.append(f"name contains '{_q(name_contains)}'")
    if full_text:
        clauses.append(f"fullText contains '{_q(full_text)}'")
    params = json.dumps({
        "q": " and ".join(clauses),
        "pageSize": max(1, min(int(limit), 100)),
        "fields": "files(id,name,mimeType,modifiedTime)",
        "orderBy": "name",
    })
    try:
        r = subprocess.run(["gws", "drive", "files", "list", "--params", params,
                            "--format", "json"],
                           capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            logger.error(f"drive_search fail ({_classify(r.stderr)}): {r.stderr[:200]}")
            return []
        return json.loads(_json_head(r.stdout)).get("files", [])
    except Exception as e:  # noqa: BLE001
        logger.error(f"drive_search error: {e}")
        return []


def drive_download(file_id: str, dst_path, timeout: int = 90) -> bool:
    """드라이브 파일을 그대로 내려받는다(.docx 등 바이너리).

    실측으로 확인한 제약 2개 (2026-08-09):
    1. gws는 `--output`이 **현재 작업 디렉터리 밖**을 가리키면 거부한다
       (`resolves to ... which is outside the current directory`) → 목적지 폴더를 cwd로 잡는다
    2. `drive files download`는 `error[api]: Internal error encountered.`로 실패한다.
       **`files get` + `alt=media`가 동작하는 경로**다 (45KB .docx 정상 수신 확인)
    """
    if not file_id:
        return False
    import os as _os
    dst = _os.path.abspath(str(dst_path))
    parent = _os.path.dirname(dst) or "."
    _os.makedirs(parent, exist_ok=True)
    cmd = ["gws", "drive", "files", "get",
           "--params", json.dumps({"fileId": file_id, "alt": "media"}),
           "--output", _os.path.basename(dst)]
    label = f"drive download({file_id[:12]})"
    for attempt in range(2):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout, cwd=parent)
            if r.returncode == 0 and _os.path.exists(dst) and _os.path.getsize(dst) > 0:
                return True
            logger.error(f"{label} fail (try {attempt+1}/2): {r.stderr[:200]}")
            if _classify(r.stderr) == "auth":
                return False
        except Exception as e:  # noqa: BLE001
            logger.error(f"{label} error (try {attempt+1}/2): {e}")
        if attempt == 0:
            time.sleep(2)
    return False


def _q(s: str) -> str:
    """Drive q 문자열 이스케이프 — 작은따옴표·백슬래시가 쿼리를 깨거나 조건을 탈출시킨다."""
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


def _json_head(out: str) -> str:
    """gws가 stdout 앞에 붙이는 'Using keyring backend: file' 같은 잡음을 걷어낸다."""
    i = out.find("{")
    return out[i:] if i >= 0 else "{}"


def docx_to_text(path) -> str:
    """.docx → 평문. python-docx 없이 zip+XML만으로 뽑는다(의존성 0).

    ⚠️ **표는 행 단위로 묶어야 한다.** 사내 규정은 핵심 수치를 표로 적는다:

        휴가 종류        | 사전 신청 시한
        연차 (1일 이하)  | 전일 18:00 이전
        연차 (2~5일)     | 3일 전

    셀을 그냥 순서대로 뽑으면 한 줄에 하나씩 나열되어 **어느 값이 어느 항목의 것인지
    사라진다.** 그 상태로 LLM에 넘기면 "연차 1일 이하는 3일 전"처럼 짝을 잘못 맺는다.
    규정 답변에서 가장 위험한 오류가 여기서 난다. 그래서 행을 ' | '로 묶어 한 줄로 만든다.
    """
    import re as _re
    import zipfile
    from xml.etree import ElementTree as ET

    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    try:
        with zipfile.ZipFile(str(path)) as z:
            xml = z.read("word/document.xml")
    except Exception as e:  # noqa: BLE001
        logger.error(f"docx_to_text: {path} 열기 실패 — {e}")
        return ""
    try:
        root = ET.fromstring(xml)
    except Exception as e:  # noqa: BLE001
        logger.error(f"docx_to_text: XML 파싱 실패 — {e}")
        return ""

    def para_text(p) -> str:
        # w:t 조각을 이어붙인다. 한 문장이 서식 때문에 여러 run으로 쪼개져 있다.
        return "".join(t.text or "" for t in p.iter(f"{W}t")).strip()

    def walk(node, lines: list[str]) -> None:
        """본문을 문서 순서대로 훑되, 표를 만나면 행 단위로 접는다."""
        for child in node:
            tag = child.tag
            if tag == f"{W}p":
                s = para_text(child)
                if s:
                    lines.append(s)
            elif tag == f"{W}tbl":
                for tr in child.findall(f"{W}tr"):
                    cells = []
                    for tc in tr.findall(f"{W}tc"):
                        # 셀 안에도 표가 중첩될 수 있다 — 재귀로 처리하고 한 셀로 합친다
                        sub: list[str] = []
                        walk(tc, sub)
                        cells.append(" ".join(sub).strip())
                    row = " | ".join(c for c in cells)
                    if row.strip(" |"):
                        lines.append(row)
            else:
                # sdt(콘텐츠 컨트롤) 등 컨테이너 안에 본문이 들어있는 경우
                if len(child):
                    walk(child, lines)

    body = root.find(f"{W}body")
    lines: list[str] = []
    walk(body if body is not None else root, lines)
    text = "\n".join(lines)
    return _re.sub(r"\n{3,}", "\n\n", text).strip()
