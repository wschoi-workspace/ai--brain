#!/usr/bin/env python3
"""일일보고 정착 점검 — 매일 밤 22:00, 오늘 보고 현황(N/10·미보고자)을 대표 텔레그램 발송.

가이드 정착 추적용: 누가 보고했고 누가 빠졌는지 매일 밤 대표에게 1줄 요약.
런타임: .venv311 (gws subprocess + stdlib). 사용: python daily-report-checkin.py [--dry]
"""
import os, sys, json, subprocess, urllib.request
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
BASKET = os.environ.get("BASKET_REPORT_SHEET_ID", "")
MGR_TOKEN = os.environ.get("DAILY_REPORT_MANAGER_BOT_TOKEN", "")
MGR_CHAT = os.environ.get("DAILY_REPORT_MANAGER_CHAT_ID", "")
EMP = json.loads((SCRIPTS / "arisa-employees.json").read_text(encoding="utf-8"))
BY_NAME = EMP.get("by_name", {})
TARGETS = [nm for tid, nm in EMP.get("by_telegram_id", {}).items() if nm != "최원석"]  # 보고 대상(대표 제외)
ALIAS = {"yang eun jung": "양은정", "준호 김": "김준호", "bro callme": "최원석"}


def gws_get(sid, rng):
    if not sid:
        return []
    try:
        r = subprocess.run(["gws", "sheets", "spreadsheets", "values", "get", "--params",
                            json.dumps({"spreadsheetId": sid, "range": rng})],
                           capture_output=True, text=True, timeout=40)
        if r.returncode == 0:
            return json.loads(r.stdout or "{}").get("values", [])
    except Exception as e:
        sys.stderr.write(f"[gws] {rng}: {e}\n")
    return []


def norm(s):
    s = (s or "").strip()
    for n in BY_NAME:
        if n.replace(" ", "").lower() == s.replace(" ", "").lower():
            return n
    return ALIAS.get(s.lower(), s)


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    today_yy = datetime.now().strftime("%y%m%d")
    reported = set()
    for r in gws_get(DAILY, "메타!A:B"):
        if len(r) >= 2 and r[0].startswith(today):
            reported.add(norm(r[1]))
    for r in gws_get(BASKET, "일일보고!A:C"):
        if len(r) >= 3 and r[1].strip() == today_yy:
            reported.add(norm(r[2]))

    done = [n for n in TARGETS if n in reported]
    todo = [n for n in TARGETS if n not in reported]
    msg = f"🌙 일일보고 점검 · {today}\n\n오늘 {len(done)}/{len(TARGETS)}명 보고 완료"
    if todo:
        msg += "\n⬜ 미보고: " + ", ".join(todo)
    else:
        msg += "\n✅ 전원 완료! 🎉"
    print(msg)

    if "--dry" in sys.argv:
        print("\n(--dry: 텔레그램 미발송)")
        return
    if MGR_TOKEN and MGR_CHAT:
        body = json.dumps({"chat_id": MGR_CHAT, "text": msg}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{MGR_TOKEN}/sendMessage",
                                     data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=20)
            print("✅ 텔레그램 발송")
        except Exception as e:
            print(f"⚠️ 발송 실패: {e}")


if __name__ == "__main__":
    main()
