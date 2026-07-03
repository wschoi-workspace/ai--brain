#!/usr/bin/env python3
"""일일보고 정착 점검 — 매일 밤 22:00, 오늘 보고 현황(N/10·미보고자)을 대표 텔레그램 발송.

가이드 정착 추적용: 누가 보고했고 누가 빠졌는지 매일 밤 대표에게 1줄 요약.
완료 판정 = 데일리 업무보고(메타 + 핵심업무)만. 바스켓 매출보고는 완료에서 제외하고 별도 줄로 표시
(reminder와 동일 기준; 매출만 올린 매장스텝도 '미완료'로 집계).
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
# 요약 CC: 대표 외 추가 수신자(예: 기획팀 리더 윤혜정). 직원과 같은 daily-report-bot으로 발송
# (윤혜정은 manager-bot엔 chat 없음 — daily-report-bot으로만 도달 가능).
BOT_TOKEN = os.environ.get("DAILY_REPORT_BOT_TOKEN", "")
SUMMARY_CC = [x.strip() for x in os.environ.get("DAILY_REPORT_SUMMARY_CC", "").split(",") if x.strip()]
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
    return None  # 읽기 실패(인증/네트워크) — 정상 빈 결과([])와 구분해 상위에서 발송 중단


def norm(s):
    s = (s or "").strip()
    for n in BY_NAME:
        if n.replace(" ", "").lower() == s.replace(" ", "").lower():
            return n
    return ALIAS.get(s.lower(), s)


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    today_yy = datetime.now().strftime("%y%m%d")
    # 완료 판정 = 데일리 업무보고(메타 + 핵심업무)만. 바스켓 매출보고는 별도 집계(완료에 미포함).
    meta_rows = gws_get(DAILY, "메타!A:B")
    core_rows = gws_get(DAILY, "핵심업무!A:B")
    # 가드: 시트 읽기 실패(gws 인증/네트워크 장애) 시 '전원 미보고' 허위 요약을 막고 대표에게 장애만 알림
    if meta_rows is None or core_rows is None:
        alert = (f"⚠️ 일일보고 점검 실패 · {today}\n"
                 f"구글시트 읽기 실패(gws 인증 장애 의심). 오늘 현황을 집계하지 못했습니다.\n"
                 f"→ 서버에서 `gws auth login --full` 재인증이 필요합니다.")
        print(alert)
        if "--dry" not in sys.argv and MGR_TOKEN and MGR_CHAT:
            try:
                body = json.dumps({"chat_id": MGR_CHAT, "text": alert}).encode()
                urllib.request.urlopen(urllib.request.Request(
                    f"https://api.telegram.org/bot{MGR_TOKEN}/sendMessage",
                    data=body, headers={"Content-Type": "application/json"}), timeout=20)
                print("✅ 장애 알림 발송")
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
    # 바스켓 매출보고(참고용, 완료 판정에는 미포함). 읽기 실패는 참고정보라 무시(None→[])
    basket = set()
    for r in (gws_get(BASKET, "일일보고!A:C") or []):
        if len(r) >= 3 and str(r[1]).strip() == today_yy:
            basket.add(norm(r[2]))

    done = [n for n in TARGETS if n in reported]
    todo = [n for n in TARGETS if n not in reported]
    basket_only = [n for n in TARGETS if n in basket and n not in reported]
    msg = f"🌙 일일보고 점검 · {today}\n\n업무보고 {len(done)}/{len(TARGETS)}명 완료"
    if todo:
        msg += "\n⬜ 미보고: " + ", ".join(todo)
    else:
        msg += "\n✅ 전원 완료! 🎉"
    if basket_only:
        msg += "\n🧺 매출보고만(업무보고 미완): " + ", ".join(basket_only)
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
            print("✅ 대표 발송")
        except Exception as e:
            print(f"⚠️ 대표 발송 실패: {e}")
    # 요약 CC(기획팀 리더 등) — daily-report-bot으로 동일 요약 공유
    for cc in SUMMARY_CC:
        if not BOT_TOKEN:
            break
        try:
            b = json.dumps({"chat_id": cc, "text": msg}).encode()
            urllib.request.urlopen(urllib.request.Request(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data=b, headers={"Content-Type": "application/json"}), timeout=20)
            print(f"✅ 요약 공유 발송 → {cc}")
        except Exception as e:
            print(f"⚠️ 요약 공유 실패({cc}): {e}")


if __name__ == "__main__":
    main()
