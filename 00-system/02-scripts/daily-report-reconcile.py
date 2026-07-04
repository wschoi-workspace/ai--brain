#!/usr/bin/env python3
"""일일보고 아침 재확인(1회성) — gws 인증장애로 유실됐던 보고가 재전송·저장됐는지 대조.

2026-07-03 밤 gws invalid_rapt 장애로 5명 보고가 유실 → 재전송 요청함. 다음날 아침 이 스크립트가
해당 날짜의 시트 최종 현황을 읽어 (1) N/10 완료·미보고자, (2) 재전송 요청 5명이 실제 재제출됐는지,
(3) gws 토큰 정상 여부를 대표 텔레그램으로 1회 보고한다. --oneshot이면 실행 후 자기 launchd를 제거.
런타임: .venv311 (gws subprocess + stdlib). 사용: python daily-report-reconcile.py [--date YYYY-MM-DD] [--oneshot] [--dry]
"""
import os, sys, json, subprocess, urllib.request
from datetime import datetime, timedelta
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
MGR_TOKEN = os.environ.get("DAILY_REPORT_MANAGER_BOT_TOKEN", "")
MGR_CHAT = os.environ.get("DAILY_REPORT_MANAGER_CHAT_ID", "")
EMP = json.loads((SCRIPTS / "arisa-employees.json").read_text(encoding="utf-8"))
BY_NAME = EMP.get("by_name", {})
TARGETS = [nm for tid, nm in EMP.get("by_telegram_id", {}).items() if nm != "최원석"]
ALIAS = {"yang eun jung": "양은정", "준호 김": "김준호", "bro callme": "최원석"}
RESEND5 = ["김예진", "배성원", "김도영", "김가은", "윤혜정"]  # 07-03 유실→재전송 요청 대상


def gws_get(sid, rng):
    if not sid:
        return None
    try:
        r = subprocess.run(["gws", "sheets", "spreadsheets", "values", "get", "--params",
                            json.dumps({"spreadsheetId": sid, "range": rng})],
                           capture_output=True, text=True, timeout=40)
        if r.returncode == 0:
            return json.loads(r.stdout or "{}").get("values", [])
    except Exception as e:
        sys.stderr.write(f"[gws] {rng}: {e}\n")
    return None


def norm(s):
    s = (s or "").strip()
    for n in BY_NAME:
        if n.replace(" ", "").lower() == s.replace(" ", "").lower():
            return n
    return ALIAS.get(s.lower(), s)


def arg(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def self_remove():
    label = "com.arisa.daily-report-reconcile"
    plist = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
    try:
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{label}"],
                       capture_output=True, text=True, timeout=15)
    except Exception as e:
        sys.stderr.write(f"[bootout] {e}\n")
    try:
        if plist.exists():
            plist.unlink()
        print("🧹 1회성 launchd 제거 완료")
    except Exception as e:
        sys.stderr.write(f"[unlink] {e}\n")


def main():
    date = arg("--date") or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    meta = gws_get(DAILY, "메타!A:B")
    core = gws_get(DAILY, "핵심업무!A:B")
    gws_ok = meta is not None and core is not None

    if gws_ok:
        reported = set()
        for rows in (meta, core):
            for r in rows:
                if len(r) >= 2 and str(r[0]).startswith(date):
                    reported.add(norm(r[1]))
        done = [n for n in TARGETS if n in reported]
        todo = [n for n in TARGETS if n not in reported]
        resend_done = [n for n in RESEND5 if n in reported]
        resend_wait = [n for n in RESEND5 if n not in reported]
        msg = (f"🔎 일일보고 아침 재확인 · {date}\n\n"
               f"업무보고 {len(done)}/{len(TARGETS)}명 완료\n")
        msg += ("✅ 전원 완료! 🎉\n" if not todo else f"⬜ 미보고: {', '.join(todo)}\n")
        msg += (f"\n📌 어제 유실→재전송 요청 5명:\n"
                f"  • 재제출 완료: {', '.join(resend_done) or '없음'}\n"
                f"  • 아직 대기: {', '.join(resend_wait) or '없음'}")
        if resend_wait:
            msg += "\n(대기자는 아직 재전송 전 — 필요 시 개별 확인 권장)"
    else:
        msg = (f"⚠️ 일일보고 아침 재확인 실패 · {date}\n"
               f"구글시트 읽기 실패(gws 인증 장애 재발 의심).\n"
               f"→ 서버에서 `gws auth login --services drive,sheets,gmail,calendar,docs,slides,tasks` 재인증이 필요합니다.")

    print(msg)

    if "--dry" not in sys.argv and MGR_TOKEN and MGR_CHAT:
        try:
            body = json.dumps({"chat_id": MGR_CHAT, "text": msg}).encode()
            urllib.request.urlopen(urllib.request.Request(
                f"https://api.telegram.org/bot{MGR_TOKEN}/sendMessage",
                data=body, headers={"Content-Type": "application/json"}), timeout=20)
            print("✅ 텔레그램 발송")
        except Exception as e:
            print(f"⚠️ 발송 실패: {e}")

    if "--oneshot" in sys.argv:
        self_remove()


if __name__ == "__main__":
    main()
