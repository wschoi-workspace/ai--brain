#!/usr/bin/env python3
"""ARISA 산출물 파수꾼 — 브리프·주간 리포트가 사라지거나 낡으면 즉시 알린다.

배경(2026-07-27 사고):
  07:31 배치가 daily-brief-2026-07-27 정상 생성
  09:47 git reset --hard → 미커밋 산출물 삭제
  12:32 git pull → 7/09 브리프로 복원
  → 대시보드가 18일 전 브리프를 18일간(주간은 3주간) 서빙했는데 아무도 몰랐다.

.gitignore로 git 경로는 막았지만 배치 실패·권한·디스크 등 다른 원인은 남는다.
이 스크립트는 **원인과 무관하게 결과만 본다** — 오늘 것이 없으면 알린다.

점검 3종:
  1) 오늘자 daily-brief 존재
  2) 최신 weekly가 지난주(직전 완료 주차) 것인지
  3) 산출물이 다시 git 추적 대상이 되지 않았는지 (재발 방지 장치 자체를 감시)

실행: python3 arisa-artifact-guard.py   (launchd 매일 10:00)
"""
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta

WS = os.environ.get("ARISA_WS", "/Users/server-mini/do-better-workspace")
BRIEF = os.path.join(WS, "20-operations/23-arisa/brief")
WEEKLY = os.path.join(WS, "20-operations/23-arisa/weekly")
EMP = os.path.join(WS, "00-system/02-scripts/arisa-employees.json")


def tg_token():
    try:
        for line in open(os.path.join(WS, ".env"), encoding="utf-8"):
            line = line.strip()
            if line.startswith("DAILY_REPORT_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def owner_chat():
    try:
        d = json.load(open(EMP, encoding="utf-8"))
        for tid, info in d.get("by_telegram_id", {}).items():
            nm = info.get("name") if isinstance(info, dict) else info
            if nm == "최원석":
                return str(tid)
    except Exception:
        pass
    return ""


def notify(text):
    import urllib.request
    tok, cid = tg_token(), owner_chat()
    if not (tok and cid):
        print("[guard] 텔레그램 설정 없음 — 알림 생략", flush=True)
        return False
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendMessage",
        data=json.dumps({"chat_id": cid, "text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r).get("ok", False)
    except Exception as e:
        print(f"[guard] 발송 실패: {e!r}", flush=True)
        return False


def last_week_tag(today):
    """직전 완료 주차 태그 (배치가 --week last 로 만드는 것과 같은 기준)."""
    prev = today - timedelta(days=7)
    y, w, _ = prev.isocalendar()
    return f"{y}-W{w:02d}"


def git_tracked(rel):
    try:
        r = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                           cwd=WS, capture_output=True, timeout=20)
        return r.returncode == 0
    except Exception:
        return False


def main():
    today = date.today()
    issues = []

    # 1) 오늘자 브리프
    bf = os.path.join(BRIEF, f"daily-brief-{today.isoformat()}.html")
    if not os.path.exists(bf):
        issues.append(f"오늘자 브리프 없음 — daily-brief-{today.isoformat()}.html")
    else:
        newest = max((f for f in os.listdir(BRIEF)
                      if f.startswith("daily-brief-") and f.endswith(".html")
                      and len(f) == len("daily-brief-2026-01-01.html")), default="")
        if newest and newest < f"daily-brief-{today.isoformat()}.html":
            issues.append(f"최신 브리프가 과거 날짜 — {newest}")

    # 2) 주간 리포트
    tag = last_week_tag(today)
    wf = os.path.join(WEEKLY, f"weekly-report-{tag}.html")
    if not os.path.exists(wf):
        have = sorted(f for f in os.listdir(WEEKLY)
                      if f.startswith("weekly-report-") and f.endswith(".html")
                      and "-" not in f[len("weekly-report-2026-W00"):])
        issues.append(f"지난주 리포트 없음 — {tag} (최신 보유: {have[-1] if have else '없음'})")

    # 3) 재발 방지 장치 감시 — 산출물이 다시 추적되면 경고
    for rel in (f"20-operations/23-arisa/brief/daily-brief-{today.isoformat()}.html",
                f"20-operations/23-arisa/weekly/weekly-report-{tag}.html"):
        if os.path.exists(os.path.join(WS, rel)) and git_tracked(rel):
            issues.append(f"⚠️ 산출물이 다시 git 추적됨 — {rel}"
                          " (.gitignore 무력화, 배포 시 또 소실됨)")

    ts = datetime.now().strftime("%m/%d %H:%M")
    if not issues:
        print(f"[guard] {ts} 정상 — 오늘 브리프·{tag} 주간 모두 존재", flush=True)
        return 0

    msg = ("🚨 ARISA 산출물 이상\n\n"
           + "\n".join("• " + i for i in issues)
           + "\n\n대시보드가 낡은 자료를 보여주고 있을 수 있습니다.\n"
             "https://arisa-os.com")
    notify(msg)
    print(f"[guard] {ts} 이상 {len(issues)}건\n{msg}", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
