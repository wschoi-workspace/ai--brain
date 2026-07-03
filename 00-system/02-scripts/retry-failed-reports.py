#!/usr/bin/env python3
"""유실 방지 큐 백필 배치 — 15분 주기(launchd com.arisa.report-backfill).

시트 저장에 실패해 로컬 큐(failed-reports/queue.jsonl)에 보관된 보고 행을 시트로 백필한다.
gws 인증 장애(invalid_rapt 등)가 복구되면 사람 개입 없이 자동으로 큐가 비워진다.

로직: 큐 비면 즉시 종료 → 인증 프로브(메타!A1:A1 읽기; auth 실패면 attempts 오염 없이
종료 + 대표 알림[2시간 스로틀]) → 엔트리별 dedup 검사(이미 저장된 행 재-append 방지)
→ append → 큐 원자 재작성 → 백필 >0건이면 대표 알림.
런타임: .venv311. 사용: python retry-failed-reports.py [--dry]
"""
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from shared import gws as _gws  # noqa: E402
from shared import report_queue as _rq  # noqa: E402

WS = SCRIPTS.parent.parent
import os  # noqa: E402
for envp in (WS / ".env", Path.home() / "arisa-project-memory" / ".env"):
    if envp.exists():
        for line in envp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

DAILY = os.environ.get("DAILY_REPORT_SHEET_ID", "")
MGR_TOKEN = os.environ.get("DAILY_REPORT_MANAGER_BOT_TOKEN", "")
MGR_CHAT = os.environ.get("DAILY_REPORT_MANAGER_CHAT_ID", "")
LAST_ALERT = _rq.QUEUE_DIR / ".last-alert"
ALERT_INTERVAL = 2 * 3600  # 인증 장애 대표 알림 스로틀(초)
MAX_ATTEMPTS_WARN = 8      # 이 이상 실패한 엔트리는 수동 확인 경고
DRY = "--dry" in sys.argv


def notify(text: str) -> None:
    print(text)
    if DRY or not (MGR_TOKEN and MGR_CHAT):
        return
    try:
        body = json.dumps({"chat_id": MGR_CHAT, "text": text}).encode()
        urllib.request.urlopen(urllib.request.Request(
            f"https://api.telegram.org/bot{MGR_TOKEN}/sendMessage",
            data=body, headers={"Content-Type": "application/json"}), timeout=20)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ 알림 발송 실패: {e}")


def alert_throttled(text: str) -> None:
    """인증 장애 알림 — 2시간에 1회만(15분 주기라 매번 울리면 스팸)."""
    now = time.time()
    try:
        if LAST_ALERT.exists() and now - float(LAST_ALERT.read_text().strip()) < ALERT_INTERVAL:
            print("(인증 장애 알림 스로틀 — 발송 생략)")
            return
    except Exception:  # noqa: BLE001
        pass
    notify(text)
    if not DRY:
        LAST_ALERT.write_text(str(now))


def is_dup(entry: dict, tab_cache: dict) -> bool:
    """dedup_cols 값이 일치하는 기존 행이 시트에 있으면 True.

    append는 성공했는데 timeout으로 실패 보고된 케이스 방어. 탭 데이터는 1회만 읽어 캐시.
    """
    key = (entry["sheet_id"], entry["tab"])
    if key not in tab_cache:
        tab_name = entry["tab"].split("!")[0]
        tab_cache[key] = _gws.values_get(entry["sheet_id"], f"{tab_name}!A:Z", timeout=40)
    rows = tab_cache[key]
    cols = entry.get("dedup_cols") or [0, 1]
    target = [str(entry["row"][c]) if c < len(entry["row"]) else "" for c in cols]
    for r in rows:
        if [str(r[c]) if c < len(r) else "" for c in cols] == target:
            return True
    return False


def main():
    pending = _rq.load_pending()
    if not pending:
        return  # 큐 비어있음 — 로그도 남기지 않고 조용히 종료(15분 주기 부담 제로)

    print(f"[{datetime.now():%Y-%m-%d %H:%M}] 백필 시작 · 대기 {len(pending)}건" + (" (--dry)" if DRY else ""))

    # 인증 프로브 — 장애 중이면 attempts 오염 없이 종료
    probe = _gws.values_get(DAILY or pending[0]["sheet_id"], "메타!A1:A1", retries=1, timeout=30)
    if probe == [] and DAILY:
        # 빈 시트일 수도 있으니 auth 여부를 append 1회로 단정하지 않고, 프로브 실패 시 보수적으로 대기
        # (values_get은 실패·빈값 모두 [] — 여기선 메타 헤더가 항상 있으므로 []는 장애로 간주)
        alert_throttled(
            f"⚠️ 보고 백필 대기 중 · 큐 {len(pending)}건\n"
            f"구글시트 접근 실패(gws 인증 장애 의심) — 복구되면 자동 백필됩니다.\n"
            f"→ 서버에서 `gws auth login --full` 재인증 필요할 수 있습니다.")
        return

    tab_cache: dict = {}
    remaining, done, backfilled, deduped = [], [], 0, 0
    for e in pending:
        try:
            if is_dup(e, tab_cache):
                e["last_error"] = "dup(이미 저장됨)"
                done.append(e)
                deduped += 1
                print(f"  ⏭️ dedup: {e['report_key']} {e['tab']}")
                continue
            if DRY:
                print(f"  [dry] append 예정: {e['report_key']} {e['tab']}")
                remaining.append(e)
                continue
            ok, kind = _gws.append_to_sheet_ex(e["sheet_id"], e["tab"], e["row"],
                                               value_input_option=e.get("vio", "RAW"), timeout=20)
            if ok:
                done.append(e)
                backfilled += 1
                # 같은 탭 캐시에 방금 넣은 행 반영(같은 실행 내 중복 append 방지)
                tab_cache.setdefault((e["sheet_id"], e["tab"]), []).append([str(x) for x in e["row"]])
                print(f"  ✅ 백필: {e['report_key']} {e['tab']}")
            else:
                e["attempts"] = int(e.get("attempts", 0)) + 1
                e["last_error"] = kind
                remaining.append(e)
                print(f"  ❌ 실패({kind}): {e['report_key']} {e['tab']} (attempts={e['attempts']})")
                if kind == "auth":
                    # 인증 장애 — 나머지도 실패 확정, attempts 더 안 올리고 보존
                    idx = pending.index(e)
                    remaining.extend(pending[idx + 1:])
                    break
        except Exception as ex:  # noqa: BLE001
            e["attempts"] = int(e.get("attempts", 0)) + 1
            e["last_error"] = f"error: {ex}"
            remaining.append(e)
            print(f"  ❌ 예외: {e['report_key']}: {ex}")

    if not DRY:
        _rq.rewrite(remaining, done)

    if backfilled or deduped:
        msg = f"✅ 유실보고 백필 {backfilled}건 완료"
        if deduped:
            msg += f" (중복확인 {deduped}건)"
        if remaining:
            msg += f" · 잔여 {len(remaining)}건"
        notify(msg)
    stuck = [e for e in remaining if int(e.get("attempts", 0)) >= MAX_ATTEMPTS_WARN]
    if stuck:
        notify(f"⚠️ 백필 {MAX_ATTEMPTS_WARN}회 이상 실패 {len(stuck)}건 — 수동 확인 필요\n"
               + "\n".join(f"  · {e['report_key']} {e['tab']} ({e['last_error']})" for e in stuck[:5]))


if __name__ == "__main__":
    main()
