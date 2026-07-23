#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""퇴사자 아리사 접근 즉시 차단 — /퇴사처리 스킬의 실행부.

python3 offboard-employee.py 이름 [--dry-run] [--no-deploy]

동작:
  ① 로컬 users.json에서 제거          → 아리사 OS 웹 세션·PIN·재로그인 즉시 차단
                                        (dashboard가 매 요청 load_users() 재검증 — 재시작 불필요)
  ② arisa-employees.json에서 제거     → 팀 판정·봇 자동 인식 차단 (by_name, by_telegram_id, _team_note 주석)
  ③ offboarded.json에 기록            → 봇이 이름 자유 입력·문의까지 거부하는 근거 목록
  ④ 맥미니 동기화(scp 3파일) + daily-report-bot 재시작
  ⑤ arisa-os.com 로그인 차단 검증 (브라우저 UA — Cloudflare가 urllib 기본 UA를 403 처리)

복구: _data/offboard-backups/{ts}-{이름}/ 의 파일을 원위치로 되돌린 뒤 재배포.
"""
import argparse
import datetime
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent                     # 00-system/02-scripts
DATA = HERE.parent / "01-templates" / "_data"
USERS = DATA / "users.json"
EMP = HERE / "arisa-employees.json"
OFFBOARDED = HERE / "offboarded.json"
BACKUP_ROOT = DATA / "offboard-backups"

MACMINI = "macmini-ts"
MAC_DATA = "do-better-workspace/00-system/01-templates/_data"
MAC_SCRIPTS = "do-better-workspace/00-system/02-scripts"
BOT_SERVICE = "com.arisa.daily-report-bot"
PROD = "https://arisa-os.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def save(p, obj):
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def _users_has(users, name):
    """users.json에서 이름 존재 여부 — dict(users)·list(arisa2 SSOT)·구식 list 모두 지원."""
    if isinstance(users, dict):
        inner = users.get("users")
        if isinstance(inner, dict):
            return name in inner
        if isinstance(inner, list):
            return any(x.get("name") == name for x in inner)
        return False
    return any(x.get("name") == name for x in users)


def inspect(name):
    """제거 대상 수집 — 실행 전 dry-run 표시용. users.json 판정은 맥미니 SSOT 기준."""
    emp = load(EMP)
    try:
        out = subprocess.run(["ssh", MACMINI, f"cat {MAC_DATA}/users.json"],
                             check=True, capture_output=True, text=True, timeout=15)
        remote = _users_has(json.loads(out.stdout), name)
    except Exception:
        remote = None  # 원격 확인 불가 — 로컬 기준 폴백
    local = _users_has(load(USERS), name)
    e = (emp.get("by_name") or {}).get(name)
    tids = [t for t, n in (emp.get("by_telegram_id") or {}).items() if n == name]
    lead_of = [team for team, ldr in (emp.get("team_leads") or {}).items() if ldr == name]
    return {"users_entry": remote if remote is not None else local, "users_local": local,
            "users_remote": remote, "emp_entry": e, "telegram_ids": tids, "lead_of": lead_of}


def apply_local(name, info):
    today = datetime.date.today().isoformat()
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    bdir = BACKUP_ROOT / f"{ts}-{name}"
    bdir.mkdir(parents=True, exist_ok=True)
    for f in (USERS, EMP) + ((OFFBOARDED,) if OFFBOARDED.exists() else ()):
        shutil.copy2(f, bdir / f.name)
    # ① users.json
    users = load(USERS)
    if isinstance(users, dict):
        (users.get("users") or {}).pop(name, None)
        if isinstance(users.get("_employees"), list) and name in users["_employees"]:
            users["_employees"].remove(name)
    else:  # 구식 list 스키마
        users = [x for x in users if x.get("name") != name]
    save(USERS, users)
    # ② arisa-employees.json
    emp = load(EMP)
    (emp.get("by_name") or {}).pop(name, None)
    for t in info["telegram_ids"]:
        (emp.get("by_telegram_id") or {}).pop(t, None)
    note = f"{name} 퇴사 제외({today})"
    emp["_team_note"] = (emp.get("_team_note", "").rstrip("; ") + "; " + note).lstrip("; ")
    save(EMP, emp)
    # ③ offboarded.json — 봇 거부 근거 목록
    ob = load(OFFBOARDED) if OFFBOARDED.exists() else {}
    ob[name] = {"date": today, "telegram_ids": info["telegram_ids"],
                "was_lead_of": info["lead_of"], "ts": ts}
    save(OFFBOARDED, ob)
    return bdir


# ⚠️ 사고 교훈(2026-07-23): 맥미니 users.json은 arisa2 SSOT(~/dev/arisa2/data/users.json 심링크,
# 리스트 스키마·실PIN)다. 로컬 users.json을 scp로 밀면 전 직원 PIN·계정이 구버전으로 덮인다(실제 발생).
# → users.json은 절대 push하지 않고, 맥미니 파일에서 해당 이름만 원격 제거한다.
_REMOTE_REMOVE = """
import json, pathlib, shutil, datetime, sys
name = sys.argv[1]
p = pathlib.Path.home() / "do-better-workspace/00-system/01-templates/_data/users.json"
p = p.resolve()  # 심링크면 원본(arisa2 SSOT)을 따라감
shutil.copy2(p, p.with_name(f"users.json.bak-offboard-{datetime.datetime.now():%Y%m%d-%H%M}"))
u = json.loads(p.read_text(encoding="utf-8"))
if isinstance(u.get("users"), list):
    u["users"] = [x for x in u["users"] if x.get("name") != name]
elif isinstance(u.get("users"), dict):
    u["users"].pop(name, None)
elif isinstance(u, list):
    u = [x for x in u if x.get("name") != name]
if isinstance(u, dict) and isinstance(u.get("_employees"), list) and name in u["_employees"]:
    u["_employees"].remove(name)
tmp = p.with_suffix(".json.tmp")
tmp.write_text(json.dumps(u, ensure_ascii=False, indent=2), encoding="utf-8")
tmp.replace(p)
print("removed:", name)
"""


def deploy(name):
    # users.json: 맥미니 SSOT에서 해당 이름만 원격 제거 (백업 자동)
    subprocess.run(["ssh", MACMINI, "python3", "-", name],
                   input=_REMOTE_REMOVE, text=True, check=True, capture_output=True)
    # 명부·퇴사자 목록: 로컬이 SSOT — 복사 안전
    for src, dst in ((EMP, f"{MACMINI}:{MAC_SCRIPTS}/arisa-employees.json"),
                     (OFFBOARDED, f"{MACMINI}:{MAC_SCRIPTS}/offboarded.json")):
        subprocess.run(["scp", str(src), dst], check=True, capture_output=True)
    subprocess.run(["ssh", MACMINI,
                    f"launchctl kickstart -k gui/$(id -u)/{BOT_SERVICE}"],
                   check=True, capture_output=True)


def verify_blocked(name):
    """프로덕션 로그인 시도 → 401 '등록되지 않은 이름'이면 차단 성공."""
    req = urllib.request.Request(PROD + "/api/login", method="POST",
                                 data=json.dumps({"id": name, "pin": "0000"}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": UA})
    try:
        urllib.request.urlopen(req, timeout=15)
        return False, "로그인이 성공함(차단 실패!)"
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if e.code == 401 and "등록되지 않은" in body:
            return True, "401 등록되지 않은 이름"
        return e.code == 401, f"{e.code} {body[:80]}"
    except Exception as e:
        return None, f"검증 불가(네트워크): {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-deploy", action="store_true", help="로컬만 수정(테스트용)")
    a = ap.parse_args()
    info = inspect(a.name)
    if not info["users_entry"] and not info["emp_entry"] and not info["telegram_ids"]:
        print(f"'{a.name}' — users.json·arisa-employees.json 어디에도 없습니다. 이미 처리됐거나 이름 오타.")
        sys.exit(1)
    print(f"[{a.name}] 제거 대상:")
    _r = info.get("users_remote")
    print(f"  users.json(맥미니 SSOT): {'확인 불가 — 로컬 기준 ' + ('있음' if info['users_local'] else '없음') if _r is None else ('있음 → 제거(웹 즉시 차단)' if _r else '없음')}")
    print(f"  by_name         : {'있음 → 제거' if info['emp_entry'] else '없음'}")
    print(f"  by_telegram_id  : {info['telegram_ids'] or '없음'}")
    if info["lead_of"]:
        print(f"  ⚠️ 팀 리더({', '.join(info['lead_of'])}) — team_leads 승계 지정 필요(수동)")
    if a.dry_run:
        print("\n--dry-run: 변경 없음.")
        return
    bdir = apply_local(a.name, info)
    print(f"\n로컬 반영 완료 (백업: {bdir})")
    if a.no_deploy:
        print("--no-deploy: 맥미니 미반영(테스트 모드).")
        return
    deploy(a.name)
    print("맥미니 동기화 + 일일보고 봇 재시작 완료")
    ok, detail = verify_blocked(a.name)
    print(f"차단 검증: {'✅ 차단됨' if ok else '❌ 확인 필요'} — {detail}")


if __name__ == "__main__":
    main()
