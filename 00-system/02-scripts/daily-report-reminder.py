#!/usr/bin/env python3
"""일일 업무보고 미완료자 자동 리마인더 — 매일 20:00 / 22:00.

정책(2026-07-01, 대표 지시):
  - '완료' 기준 = 데일리 업무보고(인사이트 시트 메타/핵심업무). 매출보고(바스켓)는 제외.
    → 매장스텝(운영팀)이 매출만 올린 경우도 '미완료'로 보고 업무보고를 요청한다.
  - 대상 = arisa-employees.json by_telegram_id (대표·퇴사자 제외, 명부가 단일 출처).
  - 미완료자에게 daily-report-bot으로 개별 DM.
런타임: .venv311 (gws subprocess + stdlib). 사용: python daily-report-reminder.py [--dry]
"""
import os, sys, json, subprocess, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
WS = SCRIPTS.parent.parent
for envp in (WS / ".env", Path.home() / "arisa-project-memory" / ".env"):
    if envp.exists():
        for line in envp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

DAILY = os.environ.get("DAILY_REPORT_SHEET_ID", "")
BOT_TOKEN = os.environ.get("DAILY_REPORT_BOT_TOKEN", "")
MGR_TOKEN = os.environ.get("DAILY_REPORT_MANAGER_BOT_TOKEN", "")
MGR_CHAT = os.environ.get("DAILY_REPORT_MANAGER_CHAT_ID", "")
EMP = json.loads((SCRIPTS / "arisa-employees.json").read_text(encoding="utf-8"))
BY_NAME = EMP.get("by_name", {})
BY_TID = EMP.get("by_telegram_id", {})
NAME2TID = {n: t for t, n in BY_TID.items()}
TARGETS = [nm for tid, nm in BY_TID.items() if nm != "최원석"]  # 대표·퇴사자(명부에서 이미 제거) 제외
sys.path.insert(0, str(SCRIPTS))
from shared.normalize import normalize_name  # noqa: E402  이름 정규화 단일출처(별칭·오염제거)


def gws_get(sid, rng, retries=3, timeout=40):
    if not sid:
        return []
    params = json.dumps({"spreadsheetId": sid, "range": rng})
    for _ in range(retries):
        try:
            r = subprocess.run(["gws", "sheets", "spreadsheets", "values", "get", "--params", params],
                               capture_output=True, text=True, timeout=timeout)
            if r.returncode == 0:
                return json.loads(r.stdout or "{}").get("values", [])
        except Exception as e:
            sys.stderr.write(f"[gws] {rng}: {e}\n")
    return None  # 읽기 실패(인증/네트워크) — 정상 빈 결과([])와 구분해 상위에서 발송 중단


def norm(s):
    return normalize_name(s, BY_NAME)


def send_dm(tid, text):
    data = urllib.parse.urlencode({"chat_id": tid, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data)
    try:
        urllib.request.urlopen(req, timeout=20)
        return True, ""
    except Exception as e:
        detail = ""
        if hasattr(e, "read"):
            try:
                detail = e.read().decode()[:150]
            except Exception:
                pass
        return False, f"{e} {detail}"


def main():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour = now.hour
    # 데일리 업무보고 완료자(메타 + 핵심업무). 바스켓 매출은 제외.
    meta_rows = gws_get(DAILY, "메타!A:B")
    core_rows = gws_get(DAILY, "핵심업무!A:B")
    # 가드: 시트 읽기 실패(gws 인증/네트워크 장애) 시 전원을 '미완료'로 오판해 허위 리마인드가 나가는 것을 차단
    if meta_rows is None or core_rows is None:
        alert = (f"⚠️ 일일보고 리마인더 중단 · {today} {hour}시\n"
                 f"구글시트 읽기 실패(gws 인증 장애 의심)로 미보고자 DM을 보내지 않았습니다.\n"
                 f"→ 서버에서 `gws auth login --services drive,sheets,gmail,calendar,docs,slides,tasks` 재인증이 필요합니다.")
        print(alert)
        if "--dry" not in sys.argv and MGR_TOKEN and MGR_CHAT:
            try:
                body = urllib.parse.urlencode({"chat_id": MGR_CHAT, "text": alert}).encode()
                urllib.request.urlopen(urllib.request.Request(
                    f"https://api.telegram.org/bot{MGR_TOKEN}/sendMessage", data=body), timeout=20)
                print("✅ 장애 알림 발송(대표)")
            except Exception as e:
                print(f"⚠️ 알림 발송 실패: {e}")
        return
    reported = set()
    for r in meta_rows:
        if len(r) >= 2 and str(r[0]).startswith(today):
            reported.add(norm(r[1]))
    for r in core_rows:
        if len(r) >= 2 and str(r[0]).startswith(today):
            reported.add(norm(r[1]))

    todo = [n for n in TARGETS if n not in reported]
    done = [n for n in TARGETS if n in reported]
    print(f"[{now:%Y-%m-%d %H:%M}] 업무보고 {len(done)}/{len(TARGETS)} 완료 · 미완료 {len(todo)}: {', '.join(todo) or '없음'}")

    if "--dry" in sys.argv:
        print("(--dry: 미발송)")
        return
    if not (BOT_TOKEN and todo):
        return
    for n in todo:
        tid = NAME2TID.get(n)
        if not tid:
            print(f"  ⚠️ {n}: telegram_id 없음 — 건너뜀")
            continue
        msg = (f"안녕하세요 {n}님 🙏\n"
               f"오늘({today}) 일일 업무보고가 아직 등록되지 않았습니다. 현재 {hour}시입니다.\n"
               f"오늘 진행하신 업무 내용을 이 봇으로 보내주시면 완료 처리됩니다. 감사합니다!")
        ok, err = send_dm(tid, msg)
        print(f"  {'✅' if ok else '❌'} {n} ({tid})" + ("" if ok else f" — {err}"))


if __name__ == "__main__":
    main()
