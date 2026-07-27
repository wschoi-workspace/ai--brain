#!/usr/bin/env python3
"""ARISA PIN 정책 준수 점검 — 1회성 예약 확인 (2026-07-30).

SSO 통합(plan: partitioned-beaming-turing)으로 PIN 하나가 HR 본인 인사·급여 정보까지
열게 되어 정책을 강화했다. 기존 PIN은 강제 무효화하지 않았으므로(락아웃 방지)
미충족자가 실제로 바꿨는지 사후 확인이 필요하다.

동작: 미충족자가 있으면 본인에게 리마인드 + 대표에게 보고 / 전원 충족이면 대표에게 완료 보고.
실행 후 자기 자신(launchd 잡)을 해제한다.
"""
import json, os, subprocess, sys, urllib.request

WS = "/Users/server-mini/do-better-workspace"
USERS = "/Users/server-mini/dev/arisa2/data/users.json"
EMP = os.path.join(WS, "00-system/02-scripts/arisa-employees.json")
PLIST = os.path.expanduser("~/Library/LaunchAgents/com.arisa.pin-policy-check.plist")
LABEL = "com.arisa.pin-policy-check"

PIN_MIN_LEN = 8


def policy_error(pin):
    v = str(pin or "")
    if len(v) < PIN_MIN_LEN:
        return f"{PIN_MIN_LEN}자 미만"
    if v.isdigit():
        return "숫자로만 구성"
    if len(set(v)) < 4:
        return "같은 문자 반복"
    return None


def token():
    for line in open(os.path.join(WS, ".env"), encoding="utf-8"):
        line = line.strip()
        if line.startswith("DAILY_REPORT_BOT_TOKEN="):
            return line.split("=", 1)[1].strip()
    return ""


def chat_ids():
    d = json.load(open(EMP, encoding="utf-8"))
    out = {}
    for tid, info in d.get("by_telegram_id", {}).items():
        nm = info.get("name") if isinstance(info, dict) else info
        if nm:
            out[nm] = str(tid)
    return out


def send(tok, cid, text):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendMessage",
        data=json.dumps({"chat_id": cid, "text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r).get("ok", False)
    except Exception as e:
        print(f"[pin-check] 발송 실패 {cid}: {e}", flush=True)
        return False


def main():
    users = json.load(open(USERS, encoding="utf-8"))["users"]
    bad = [(u["name"], policy_error(u.get("pin"))) for u in users if policy_error(u.get("pin"))]
    tok, cids = token(), chat_ids()
    if not tok:
        print("[pin-check] 봇 토큰 없음", flush=True); return

    if bad:
        for nm, why in bad:
            cid = cids.get(nm)
            if cid:
                send(tok, cid, (
                    f"🔐 아리사 PIN 변경 리마인드 ({nm}님)\n\n"
                    f"지난 안내드린 PIN 변경이 아직 안 되어 있습니다. (사유: {why})\n\n"
                    "HR 포털이 아리사 로그인으로 통합되어, PIN 하나로 본인 인사·급여 정보까지 열립니다.\n"
                    "잠깐이면 되니 오늘 중으로 바꿔주세요.\n\n"
                    "【변경 방법】\n"
                    "1. arisa-os.com 로그인\n"
                    "2. 우측 상단 이름 옆 'PIN변경'\n"
                    "3. 현재 PIN → 새 PIN (8자 이상, 숫자만은 불가)"))
        body = "\n".join(f"• {nm} — {why}" for nm, why in bad)
        msg = (f"🔐 ARISA PIN 정책 점검 (7/30)\n\n"
               f"미충족 {len(bad)}명 / 전체 {len(users)}명\n\n{body}\n\n"
               "→ 해당 인원에게 리마인드 발송했습니다.")
    else:
        msg = (f"🔐 ARISA PIN 정책 점검 (7/30)\n\n"
               f"✅ 전원 충족 ({len(users)}/{len(users)}명)\n\n"
               "SSO 통합에 따른 PIN 강화 조치가 완료됐습니다.")

    if cids.get("최원석"):
        send(tok, cids["최원석"], msg)
    print("[pin-check]", msg.replace("\n", " | "), flush=True)

    # 1회성 — 실행 후 자기 자신 해제
    try:
        subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}/{LABEL}"],
                       capture_output=True)
        if os.path.exists(PLIST):
            os.rename(PLIST, PLIST + ".done")
        print("[pin-check] 예약 작업 자체 해제 완료", flush=True)
    except Exception as e:
        print(f"[pin-check] 자체 해제 실패(무해): {e}", flush=True)


if __name__ == "__main__":
    main()
