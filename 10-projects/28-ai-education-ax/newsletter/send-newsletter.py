#!/usr/bin/env python3
"""
AX 직원교육 뉴스레터 — 순차 발송 스크립트

매주 1회 launchd가 호출. delivery-status.json의 회차 카운터를 보고
다음 회차 ep-0N.md를 수신자에게 텔레그램 발송한다.

발송 패턴은 00-system/02-scripts/daily-report-bot.py(send_to_manager)를 재사용.

■ 수신 대상(audience)
  me        : 매니저봇 → 본인(테스트/미리보기용). 기본값.
  employees : 일일업무보고봇(DAILY_REPORT_BOT_TOKEN) → 직원 명부.
              직원들이 이미 쓰는 그 봇으로 뉴스레터가 간다(전용 봇 불필요).
              수신자 = recipients.json(있으면 우선) 또는 arisa-employees.json의 by_telegram_id.

사용법:
  python send-newsletter.py --audience employees           # 다음 회차 직원 발송 + 상태 갱신
  python send-newsletter.py --episode 0                     # 특정 회차(상태 미갱신). 0=온보딩
  python send-newsletter.py --episode 1 --audience employees
  python send-newsletter.py --test                          # 다음 회차를 본인에게만(상태 미갱신)
  python send-newsletter.py --dry-run --audience employees  # 발송 없이 대상/내용 출력
  python send-newsletter.py --status                        # 진행 상태만 출력
  python send-newsletter.py --list-recipients               # 직원 수신자 목록(마스킹) 확인
"""
import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

# ── 경로 ──
BASE = Path(__file__).resolve().parent          # .../newsletter/
EPISODES = BASE / "episodes"
STATUS_FILE = BASE / "delivery-status.json"
RECIPIENTS_FILE = BASE / "recipients.json"
EMP_PATH = Path.home() / "do-better-workspace" / "00-system" / "02-scripts" / "arisa-employees.json"
SENT_LOG = BASE / "sent-log.json"               # 발송 message_id 기록(30일 후 삭제용)
PLAYBOOK_LOCKED = BASE / "job-playbook-locked.html"  # 예제집 보안본(첨부)

# ── 보안 정책 ──
SECURITY_TTL_DAYS = 30   # 발송 후 N일 뒤 텔레그램 메시지 자동삭제

# ── env (워크스페이스 .env 재사용) ──
load_dotenv(Path.home() / "do-better-workspace" / ".env")

MANAGER_BOT_TOKEN = os.getenv("DAILY_REPORT_MANAGER_BOT_TOKEN")
MANAGER_CHAT_ID = os.getenv("DAILY_REPORT_MANAGER_CHAT_ID")
# 직원 발송: 전용 봇이 있으면 우선, 없으면 일일업무보고봇(직원이 이미 아는 봇)
EMPLOYEE_BOT_TOKEN = os.getenv("AX_NEWSLETTER_BOT_TOKEN") or os.getenv("DAILY_REPORT_BOT_TOKEN")

KST = timezone(timedelta(hours=9))


def log(msg: str):
    print(f"[{datetime.now(KST):%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def episode_path(ep: int) -> Path:
    if ep == 0:
        return EPISODES / "ep-00-onboarding.md"
    return EPISODES / f"ep-{ep:02d}.md"


def load_status() -> dict:
    if STATUS_FILE.exists():
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    return {"last_sent_episode": 0, "last_sent_at": None, "total_episodes": 7,
            "send_weekday": "mon", "send_hour": 9}


def save_status(status: dict):
    STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def employee_chat_ids() -> list:
    """arisa-employees.json의 by_telegram_id 키(=개인채팅 chat_id) 목록."""
    if not EMP_PATH.exists():
        return []
    try:
        d = json.loads(EMP_PATH.read_text(encoding="utf-8"))
        return [str(k) for k in d.get("by_telegram_id", {}).keys()]
    except Exception as e:
        log(f"employees 로드 실패: {e}")
        return []


# ── 직무별 케이스북 ──
CASEBOOK_DIR = BASE / "casebook"
JOB_CASEBOOK = {
    "design":    CASEBOOK_DIR / "case-design-locked.html",
    "planning":  CASEBOOK_DIR / "case-planning-locked.html",
    "ops":       CASEBOOK_DIR / "case-ops-locked.html",
    "marketing": CASEBOOK_DIR / "case-marketing-locked.html",
}
JOB_LABEL = {"design": "디자인", "planning": "기획·PM", "ops": "매장운영", "marketing": "마케팅"}


def job_of(emp: dict) -> str:
    """직원 team/role → 직무 카테고리. team 우선, 없으면 role 키워드, 기본 planning."""
    team = emp.get("team", "") or ""
    if "공간" in team:
        return "design"
    if "운영" in team:
        return "ops"
    if "기획" in team:  # 기획팀·사업기획
        return "planning"
    blob = team + (emp.get("role", "") or "") + (emp.get("duty", "") or "") + (emp.get("position", "") or "")
    if "마케팅" in blob or "마케터" in blob:
        return "marketing"
    if "디자인" in blob or "Design" in blob or "Space" in blob:
        return "design"
    if "매장" in blob:
        return "ops"
    return "planning"


def employee_job_map() -> dict:
    """{chat_id: job} — 직원명부 by_telegram_id → by_name → team/role."""
    if not EMP_PATH.exists():
        return {}
    d = json.loads(EMP_PATH.read_text(encoding="utf-8"))
    by_name = d.get("by_name", {})
    out = {}
    for tid, name in d.get("by_telegram_id", {}).items():
        out[str(tid)] = job_of(by_name.get(name, {}))
    return out


STEPS_DIR = BASE / "steps"


def send_steps(token: str, recipients: list, wk: int, dry_run: bool = False,
               force_job: str = None, also_marketing: bool = False) -> bool:
    """주차 wk의 직무매칭 스텝(보안본) 첨부 발송. 마케팅 스텝은 전 직무 공통 동봉."""
    jobmap = employee_job_map()
    ok_all = True
    for cid in recipients:
        job = force_job or jobmap.get(str(cid), "planning")
        jobs = [job]  # 주 1개 원칙 — 직무 스텝 1개만
        if also_marketing and "marketing" not in jobs:
            jobs.append("marketing")
        for j in jobs:
            f = STEPS_DIR / f"wk{wk}-{j}-locked.html"
            if not f.exists():
                if j == "marketing" and job != "marketing":
                    continue  # 마케팅 공통 동봉인데 해당 주차 미존재(예: WK8) → 조용히 skip
                log(f"  ❌ chat={str(cid)[:4]}**** WK{wk}-{j} 파일 없음"); ok_all = False; continue
            if dry_run:
                log(f"  [dry] chat={str(cid)[:4]}**** WK{wk} → {f.name}"); continue
            tag = "마케팅(공통)" if j == "marketing" and job != "marketing" else JOB_LABEL.get(j, j)
            mid = tg_send_document(token, cid, f,
                                   caption=f"📕 *WK{wk} 심화 — {tag}* (다운받아 브라우저로 열기 · 비번 필요 · 30일 후 만료)")
            record_sent(token, cid, mid, wk, f"step:wk{wk}:{j}")
            log(f"  {'✅' if mid else '❌'} chat={str(cid)[:4]}**** WK{wk}-{j} msg={mid}")
            ok_all = ok_all and (mid is not None)
            time.sleep(0.4)
    return ok_all


def send_casebook(token: str, recipients: list, dry_run: bool = False,
                  force_job: str = None, also_marketing: bool = False) -> bool:
    """각 수신자에게 직무 매칭 케이스북(보안본) 첨부 발송. 매핑 불명은 planning."""
    jobmap = employee_job_map()
    ok_all = True
    for cid in recipients:
        job = force_job or jobmap.get(str(cid), "planning")
        targets = [job]
        if also_marketing and job != "marketing":
            targets.append("marketing")  # 마케팅 케이스북 동봉 옵션
        for j in targets:
            f = JOB_CASEBOOK.get(j)
            if not f or not f.exists():
                log(f"  ❌ chat={str(cid)[:4]}**** 직무={j} 케이스북 파일 없음")
                ok_all = False
                continue
            if dry_run:
                log(f"  [dry] chat={str(cid)[:4]}**** 직무={j} → {f.name}")
                continue
            mid = tg_send_document(token, cid, f,
                                   caption=f"📕 *내 직무 케이스북 — {JOB_LABEL.get(j, j)}* (다운받아 브라우저로 열기 · 비번 필요 · 30일 후 만료)")
            record_sent(token, cid, mid, -1, f"casebook:{j}")
            log(f"  {'✅' if mid else '❌'} chat={str(cid)[:4]}**** 직무={j} msg={mid}")
            ok_all = ok_all and (mid is not None)
            time.sleep(0.4)
    return ok_all


def resolve_audience(audience: str):
    """(bot_token, [chat_id,...], label) 반환."""
    if audience == "me":
        if not MANAGER_BOT_TOKEN or not MANAGER_CHAT_ID:
            log("❌ 매니저 봇/챗ID 없음 (.env DAILY_REPORT_MANAGER_*)")
            return None, [], "me"
        return MANAGER_BOT_TOKEN, [str(MANAGER_CHAT_ID)], "me"

    # employees
    if not EMPLOYEE_BOT_TOKEN:
        log("❌ 직원 봇 토큰 없음 (.env AX_NEWSLETTER_BOT_TOKEN 또는 DAILY_REPORT_BOT_TOKEN)")
        return None, [], "employees"
    # 자동구독(recipients.json) ∪ 직원명부(by_telegram_id) 합집합, 중복 제거
    ids = set()
    if RECIPIENTS_FILE.exists():
        data = json.loads(RECIPIENTS_FILE.read_text(encoding="utf-8"))
        ids |= {str(r["chat_id"]) for r in data.get("recipients", []) if r.get("chat_id")}
    ids |= set(employee_chat_ids())
    ids = sorted(ids)
    log(f"ℹ️ 수신자 {len(ids)}명 (자동구독 recipients.json ∪ 직원명부 by_telegram_id)")
    return EMPLOYEE_BOT_TOKEN, ids, "employees"


def _post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def tg_send(token: str, chat_id: str, text: str):
    """텔레그램 sendMessage. 성공 시 message_id(int), 실패 시 None.
    Markdown 파싱 실패 시 plain으로 1회 재시도."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for parse_mode in ("Markdown", None):
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        try:
            res = _post_json(url, payload)
            if res.get("ok"):
                return res["result"]["message_id"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            log(f"  HTTP {e.code} ({parse_mode}): {body[:160]}")
            if parse_mode == "Markdown" and "can't parse" in body.lower():
                continue
            return None
        except Exception as e:
            log(f"  발송 예외: {e}")
            return None
    return None


def tg_send_document(token: str, chat_id: str, filepath: Path, caption: str = ""):
    """텔레그램 sendDocument(파일 첨부). 성공 시 message_id, 실패 시 None."""
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    boundary = "----AXNewsletterBoundary7MA4YWxk"
    fp = Path(filepath)
    def field(name, value):
        return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode("utf-8")
    body = field("chat_id", str(chat_id))
    if caption:
        body += field("caption", caption) + field("parse_mode", "Markdown")
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="document"; '
             f'filename="{fp.name}"\r\nContent-Type: text/html\r\n\r\n').encode("utf-8")
    body += fp.read_bytes() + b"\r\n" + f"--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("ok"):
                return res["result"]["message_id"]
    except urllib.error.HTTPError as e:
        log(f"  sendDocument HTTP {e.code}: {e.read().decode('utf-8','ignore')[:160]}")
    except Exception as e:
        log(f"  sendDocument 예외: {e}")
    return None


def tg_delete(token: str, chat_id: str, message_id: int) -> bool:
    """deleteMessage. 봇이 보낸 메시지는 시간제한 없이 삭제 가능."""
    url = f"https://api.telegram.org/bot{token}/deleteMessage"
    try:
        return bool(_post_json(url, {"chat_id": chat_id, "message_id": message_id}).get("ok"))
    except urllib.error.HTTPError as e:
        log(f"  delete {message_id}: HTTP {e.code} {e.read().decode('utf-8','ignore')[:120]}")
        return True  # 이미 삭제/만료 → 로그에서 제거 처리
    except Exception as e:
        log(f"  delete {message_id} 예외: {e}")
        return False


def load_sent_log() -> list:
    if SENT_LOG.exists():
        try:
            return json.loads(SENT_LOG.read_text(encoding="utf-8")).get("sent", [])
        except Exception:
            return []
    return []


def save_sent_log(items: list):
    SENT_LOG.write_text(json.dumps({"sent": items}, ensure_ascii=False, indent=2), encoding="utf-8")


def record_sent(token, chat_id, message_id, episode, kind):
    """발송 메시지를 30일 삭제 대상으로 기록."""
    if message_id is None:
        return
    items = load_sent_log()
    items.append({"token_full": token, "chat_id": str(chat_id), "message_id": message_id,
                  "episode": episode, "kind": kind, "sent_at": datetime.now(KST).isoformat()})
    save_sent_log(items)


def purge_expired():
    """SECURITY_TTL_DAYS 경과한 발송 메시지를 deleteMessage로 회수."""
    items = load_sent_log()
    if not items:
        log("purge: 삭제 대상 없음(발송 이력 비어있음)"); return
    cutoff = datetime.now(KST) - timedelta(days=SECURITY_TTL_DAYS)
    keep, deleted = [], 0
    for it in items:
        try:
            sent = datetime.fromisoformat(it["sent_at"])
        except Exception:
            keep.append(it); continue
        if sent <= cutoff:
            ok = tg_delete(it["token_full"], it["chat_id"], it["message_id"])
            if ok:
                deleted += 1
            else:
                keep.append(it)  # 실패 → 다음 회차에 재시도
            time.sleep(0.3)
        else:
            keep.append(it)
    save_sent_log(keep)
    log(f"purge 완료: {deleted}건 삭제, {len(keep)}건 유지(TTL {SECURITY_TTL_DAYS}일)")


def send_episode(ep: int, token: str, recipients: list, dry_run: bool = False, attach: bool = False) -> bool:
    path = episode_path(ep)
    if not path.exists():
        log(f"❌ 회차 파일 없음: {path.name}")
        return False
    text = path.read_text(encoding="utf-8")
    log(f"📤 EP{ep:02d} ({path.name}) → 수신자 {len(recipients)}명" + (" +예제집첨부" if attach else ""))
    if dry_run:
        print("─" * 40)
        print(text)
        print("─" * 40)
        if attach:
            print(f"[첨부 예정] {PLAYBOOK_LOCKED.name} ({'있음' if PLAYBOOK_LOCKED.exists() else '❌ 없음'})")
        return True
    ok_all = True
    for cid in recipients:
        mid = tg_send(token, cid, text)
        ok = mid is not None
        record_sent(token, cid, mid, ep, "text")
        log(f"  {'✅' if ok else '❌'} chat_id={str(cid)[:4]}**** msg={mid}")
        # 예제집 보안본 첨부(있을 때만)
        if attach and PLAYBOOK_LOCKED.exists():
            dmid = tg_send_document(token, cid, PLAYBOOK_LOCKED,
                                    caption="📎 *직무별 예제집* (비번 필요 · 30일 후 만료)")
            record_sent(token, cid, dmid, ep, "playbook")
            log(f"     📎 예제집 첨부 {'✅' if dmid else '❌'} msg={dmid}")
        ok_all = ok_all and ok
        time.sleep(0.4)
    return ok_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audience", choices=["me", "employees"], default="me",
                    help="me=본인(기본) / employees=직원명부")
    ap.add_argument("--episode", type=int, help="특정 회차 발송(상태 미갱신). 0=온보딩")
    ap.add_argument("--test", action="store_true", help="다음 회차를 본인에게만(상태 미갱신)")
    ap.add_argument("--dry-run", action="store_true", help="발송 없이 내용 출력")
    ap.add_argument("--status", action="store_true", help="진행 상태만 출력")
    ap.add_argument("--list-recipients", action="store_true", help="직원 수신자(마스킹) 목록")
    ap.add_argument("--purge", action="store_true", help=f"{SECURITY_TTL_DAYS}일 경과 메시지 삭제(보안)")
    ap.add_argument("--attach", action="store_true", help="회차와 함께 예제집 보안본 첨부")
    ap.add_argument("--casebook", action="store_true", help="직무매칭 케이스북(보안본) 첨부 발송")
    ap.add_argument("--steps", action="store_true", help="주차별 직무 스텝 첨부 발송(마케팅 공통 동봉)")
    ap.add_argument("--wk", type=int, help="스텝 주차 지정(기본: 현재 회차)")
    ap.add_argument("--force-job", choices=["design", "planning", "ops", "marketing"],
                    help="직무 강제(테스트용)")
    ap.add_argument("--to", help="특정 chat_id 1명에게만 발송(직원봇)")
    ap.add_argument("--also-marketing", action="store_true", help="케이스북 발송 시 마케팅본 동봉")
    args = ap.parse_args()

    status = load_status()
    total = status.get("total_episodes", 7)

    if args.status:
        log(f"진행: {status['last_sent_episode']}/{total} 발송됨, 마지막={status.get('last_sent_at')}")
        log(f"보안 로그: {len(load_sent_log())}건 추적 중(TTL {SECURITY_TTL_DAYS}일)")
        return

    if args.purge:
        purge_expired()
        return

    if args.list_recipients:
        ids = employee_chat_ids()
        log(f"직원명부 발송가능(by_telegram_id) {len(ids)}명: {[str(i)[:4]+'****' for i in ids]}")
        return

    # --test 는 항상 본인(me)
    audience = "me" if args.test else args.audience
    token, recipients, label = resolve_audience(audience)
    if not token:
        sys.exit(1)
    # --to: 특정 1명에게만(직원봇 토큰 사용)
    if args.to:
        if not EMPLOYEE_BOT_TOKEN:
            log("❌ 직원봇 토큰 없음(.env)"); sys.exit(1)
        token = EMPLOYEE_BOT_TOKEN
        recipients = [str(args.to)]
        label = f"단일:{str(args.to)[:4]}****"
        log(f"📍 단일 수신자 모드 → {label}")

    # --casebook: 직무매칭 케이스북 첨부 발송(회차와 독립)
    if args.casebook:
        if not recipients:
            log("❌ 수신자 없음"); sys.exit(1)
        log(f"📕 케이스북 발송 — 대상 {label} ({len(recipients)}명)"
            + (f" · 직무강제={args.force_job}" if args.force_job else ""))
        send_casebook(token, recipients, dry_run=args.dry_run,
                      force_job=args.force_job, also_marketing=args.also_marketing)
        return

    # --steps: 주차별 직무 스텝 첨부 발송
    if args.steps:
        if not recipients:
            log("❌ 수신자 없음"); sys.exit(1)
        wk = args.wk or max(1, status["last_sent_episode"])
        log(f"📕 WK{wk} 스텝 발송 — 대상 {label} ({len(recipients)}명)"
            + (f" · 직무강제={args.force_job}" if args.force_job else ""))
        send_steps(token, recipients, wk, dry_run=args.dry_run,
                   force_job=args.force_job, also_marketing=args.also_marketing)
        return

    # --episode N: 특정 회차 강제(상태 미갱신)
    if args.episode is not None:
        if not recipients:
            log("❌ 수신자 없음"); sys.exit(1)
        send_episode(args.episode, token, recipients, dry_run=args.dry_run, attach=args.attach)
        return

    # --test: 다음 회차를 본인에게만
    if args.test:
        next_ep = status["last_sent_episode"] + 1
        if next_ep > total:
            log("모든 회차 발송 완료 상태 — 테스트할 다음 회차 없음"); return
        send_episode(next_ep, token, recipients, dry_run=args.dry_run, attach=args.attach)
        log("(테스트 모드 — 상태 미갱신)")
        return

    # 기본: 다음 회차 자동 발송 + 상태 갱신
    next_ep = status["last_sent_episode"] + 1
    if next_ep > total:
        log(f"🎉 전 회차({total}) 발송 완료 — 더 보낼 회차 없음")
        if MANAGER_BOT_TOKEN and MANAGER_CHAT_ID and not status.get("completed_notified"):
            tg_send(MANAGER_BOT_TOKEN, str(MANAGER_CHAT_ID),
                    f"🎉 AX 뉴스레터 전 {total}회차 발송이 모두 끝났습니다. by Project Rent")
            status["completed_notified"] = True
            save_status(status)
        return

    if not recipients:
        log(f"❌ 수신자 없음 (audience={label}) — recipients.json 또는 직원명부 필요")
        sys.exit(1)

    log(f"대상: {label} ({len(recipients)}명)")
    ok = send_episode(next_ep, token, recipients, dry_run=args.dry_run, attach=args.attach)
    if args.dry_run:
        return
    if ok:
        status["last_sent_episode"] = next_ep
        status["last_sent_at"] = datetime.now(KST).isoformat()
        save_status(status)
        log(f"✅ EP{next_ep:02d} 발송 완료 → 상태 갱신({next_ep}/{total})")
    else:
        log(f"⚠️ EP{next_ep:02d} 일부/전체 실패 — 상태 미갱신(다음 실행 재시도)")
        sys.exit(1)


if __name__ == "__main__":
    main()
