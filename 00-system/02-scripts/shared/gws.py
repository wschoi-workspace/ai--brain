"""공유 Google Workspace(gws CLI) 래퍼.

배치의 _gws_values_get(읽기)와 봇의 save_to_sheet/append_sheet(쓰기)를 단일 출처로.
기존 구현과 동일한 명령·재시도·타임아웃을 보존한다.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import time

logger = logging.getLogger(__name__)


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
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"[gws err {attempt+1}] {rng}: {e}\n")
        if attempt < retries - 1:
            time.sleep(2)
    return []


def append_to_sheet(sheet_id: str, range_str: str, row: list,
                    value_input_option: str = "RAW", timeout: int = 15) -> bool:
    """시트 1행 append. (봇 save_to_sheet / append_sheet / append_progress / log_todo 단일 출처)"""
    if not sheet_id:
        logger.warning("append_to_sheet: sheet_id 미설정 — 건너뜀")
        return False
    try:
        r = subprocess.run([
            "gws", "sheets", "spreadsheets", "values", "append",
            "--params", json.dumps({
                "spreadsheetId": sheet_id, "range": range_str,
                "valueInputOption": value_input_option, "insertDataOption": "INSERT_ROWS",
            }),
            "--json", json.dumps({"values": [row]}),
        ], capture_output=True, timeout=timeout, text=True)
        if r.returncode != 0:
            logger.error(f"sheet append fail: {r.stderr[:300]}")
            return False
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"sheet append error: {e}")
        return False


def values_update(sheet_id: str, rng: str, values: list[list],
                  value_input_option: str = "RAW", timeout: int = 15) -> bool:
    """시트 특정 범위 덮어쓰기 (분장 상태 업데이트 등)."""
    if not sheet_id:
        logger.warning("values_update: sheet_id 미설정 — 건너뜀")
        return False
    try:
        r = subprocess.run([
            "gws", "sheets", "spreadsheets", "values", "update",
            "--params", json.dumps({
                "spreadsheetId": sheet_id, "range": rng,
                "valueInputOption": value_input_option,
            }),
            "--json", json.dumps({"values": values}),
        ], capture_output=True, timeout=timeout, text=True)
        if r.returncode != 0:
            logger.error(f"sheet update fail: {r.stderr[:300]}")
            return False
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"sheet update error: {e}")
        return False
