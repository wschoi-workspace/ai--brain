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
