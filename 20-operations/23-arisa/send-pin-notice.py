#!/usr/bin/env python3
"""아리사 OS 로그인 PIN 개별 안내 — 각 직원의 본인 텔레그램 채팅으로만 발송 (직원봇).

주의: PIN은 반드시 본인 chat_id로만 발송. 대표(최원석)는 기본 제외.
실행(맥미니 권장 — users.json SSOT):
  python3 20-operations/23-arisa/send-pin-notice.py --test        # 최원석에게 본인 PIN 형식 확인
  python3 20-operations/23-arisa/send-pin-notice.py               # 전 직원(대표 제외)
  python3 20-operations/23-arisa/send-pin-notice.py --to 김가은    # 특정 인원만
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

MSG_TMPL = """🔑 아리사 OS 로그인 PIN 재안내 ({name}님 전용)

어제 시스템 오류 복구로 PIN이 처음 안내드린 값으로
돌아가 있습니다. 아래 PIN이 현재 유효한 PIN입니다.

🔗 https://arisa-os.com
· 아이디: {name}  (본인 이름 그대로)
· PIN: {pin}

⚠️ 대소문자를 구분합니다 — 이 메시지에서 PIN을
길게 눌러 복사해 붙여넣으시는 걸 권장합니다.
(끝에 공백이 딸려오면 지워주세요)

로그인 후 우측 상단 [PIN변경]에서
본인만 아는 번호(4자 이상)로 꼭 변경해주세요.

이 메시지는 본인에게만 발송되었습니다.
로그인이 안 되면 이 채팅에 남겨주세요 — 확인 후 회신드립니다."""


def load_pins():
    # PIN SSOT는 맥미니(~/dev/arisa2/data/users.json) — 로컬 파일은 테스트 사본이라 구버전 PIN 발송 사고 위험(2026-07-24 결함 수정).
    import subprocess
    try:
        out = subprocess.run(["ssh", "macmini-ts", "cat", "dev/arisa2/data/users.json"],
                             check=True, capture_output=True, text=True, timeout=15)
        u = json.loads(out.stdout)
        src = "맥미니 SSOT"
    except Exception:
        u = json.loads((WS / "00-system" / "01-templates" / "_data" / "users.json").read_text(encoding="utf-8"))
        src = "⚠ 로컬 폴백(사본 — PIN 불일치 위험)"
    print(f"PIN 소스: {src}")
    users = u.get("users", u)
    if isinstance(users, list):
        return {x["name"]: str(x.get("pin") or "") for x in users if x.get("name")}
    return {k: str(v.get("pin") or "") for k, v in users.items()}


def send(chat_id, text):
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("ok")


def main():
    test = "--test" in sys.argv
    only = sys.argv[sys.argv.index("--to") + 1] if "--to" in sys.argv else None
    pins = load_pins()
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
        if not pins.get(name):
            print(f"  ⚠ {name}: PIN 미설정 — 건너뜀")
            continue
        targets.append((name, tg_id))
    print(f"발송 대상 {len(targets)}명: {', '.join(n for n, _ in targets)}")
    ok = fail = 0
    for name, tg_id in targets:
        try:
            if send(tg_id, MSG_TMPL.format(name=name, pin=pins[name])):
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
