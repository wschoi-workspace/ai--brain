#!/usr/bin/env python3
"""아리사 OS 오전 로그인 오류 안내 (2026-07-23) — 직원 개별 텔레그램 발송 (직원봇).

  python3 20-operations/23-arisa/send-login-fix-notice.py --test   # 최원석에게 형식 확인
  python3 20-operations/23-arisa/send-login-fix-notice.py          # 전 직원(대표 제외)
  python3 20-operations/23-arisa/send-login-fix-notice.py --to 배성원
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
token = ""
for line in (WS / ".env").read_text(encoding="utf-8").splitlines():
    if line.startswith("DAILY_REPORT_BOT_TOKEN="):
        token = line.split("=", 1)[1].strip()
assert token, ".env에서 DAILY_REPORT_BOT_TOKEN을 찾지 못했습니다"

MSG = """📢 아리사 OS 로그인 안내 ({name}님)

오늘 오전(08시~12시) 시스템 계정 파일 문제로
아리사 OS(arisa-os.com) 로그인이 안 되는 오류가 있었습니다.
지금은 정상 복구되었습니다. 🙏

✅ 로그인 방법
· 아이디: 본인 이름
· PIN: 7/22에 개별 안내드린 PIN 그대로

⚠️ 어제 PIN을 직접 변경하셨던 분은
변경 전(처음 안내받은) PIN으로 다시 로그인해주세요.
— 오류 복구 과정에서 변경분이 초기화되었습니다.

로그인이 계속 안 되면 이 채팅에 남겨주세요.
확인 후 바로 회신드립니다."""


def send(chat_id, text):
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("ok")


def main():
    test = "--test" in sys.argv
    only = sys.argv[sys.argv.index("--to") + 1] if "--to" in sys.argv else None
    emp = json.loads((WS / "00-system" / "02-scripts" / "arisa-employees.json").read_text(encoding="utf-8"))
    targets = []
    for tg_id, info in emp.get("by_telegram_id", {}).items():
        name = info.get("name") if isinstance(info, dict) else str(info)
        if test:
            if name != "최원석":
                continue
        elif only:
            if name != only:
                continue
        elif name == "최원석":  # 대표는 기본 제외
            continue
        targets.append((name, tg_id))
    print(f"발송 대상 {len(targets)}명: {', '.join(n for n, _ in targets)}")
    ok = fail = 0
    for name, tg_id in targets:
        try:
            if send(tg_id, MSG.format(name=name)):
                ok += 1
                print(f"  ✓ {name}")
            else:
                fail += 1
                print(f"  ✗ {name} (API 거절)")
        except Exception as e:
            fail += 1
            print(f"  ✗ {name} ({e})")
        time.sleep(0.5)
    print(f"완료 — 성공 {ok} / 실패 {fail}")


if __name__ == "__main__":
    main()
