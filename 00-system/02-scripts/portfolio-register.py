#!/usr/bin/env python3
"""프로젝트 포트폴리오 등록 — 브리프 JSON → ARISA 포트폴리오 프로젝트 파일 생성·병합·배포.

/프로젝트등록 스킬의 결정론적 실행부. 파싱(자연어→JSON)은 스킬(LLM)이 담당하고,
검증·병합·저장·배포는 전부 이 스크립트가 처리한다.

  python3 portfolio-register.py --input brief.json            # 등록(병합) + 맥미니 배포
  python3 portfolio-register.py --input brief.json --dry-run  # 검증만, 파일 안 씀
  python3 portfolio-register.py --input brief.json --no-deploy
  python3 portfolio-register.py --input brief.json --replace-tasks
  cat brief.json | python3 portfolio-register.py --input -

진행 상황 갱신(등록 없이 상태만 바꿀 때):
  python3 portfolio-register.py --id <프로젝트id> \
      --task "견적서 재발행=Done" --issue "용역기간이 '21.04.01=Closed"
  # 좌변은 task/issue 문구의 일부(부분일치, 공백·유니코드 정규화). 여러 번 반복 가능.
  # 한 항목만 매칭돼야 하며, 0건·2건 이상이면 중단한다.

외부 파트너(사내 명부 밖 협업자) 등록:
  python3 portfolio-register.py --id <프로젝트id> \
      --partner "진실=jinsil@example.com=유럽 AHQ(파리)=현지 컨트롤"
  # 형식은 "이름=이메일[=소속[=역할]]". 이름과 이메일은 필수 —
  # 둘 중 하나라도 없거나 이메일 형식이 아니면 등록을 중단한다(경고 아님).
  # 연락처 없는 '이름만 파트너'는 인수인계 시 추적이 불가능해지므로 원천 차단한다.
  # --input 브리프 JSON 에서는 최상위 "partners": [{name,email,org,role}] 로 준다.
  # partners 에 이름이 있으면 그 사람을 tasks.owner 로 지정해도 명부 경고가 나지 않는다.

병합 규칙(기본):
  - brief    : 입력에 있는 키만 덮어쓰기, 없는 키는 기존 값 보존
  - tasks    : akey(start|task|owner) 기준 중복 skip → 추가만
  - issues   : issue 텍스트 정규화 기준 중복 skip → 추가만
  - members  : 합집합 (사내 직원 전용 — 대시보드 열람 권한과 연결된다)
  - partners : 이메일(소문자) 기준 병합, 같은 이메일이면 최신 값으로 갱신
  --replace-tasks 를 주면 tasks를 통째로 교체한다(이슈·파트너는 항상 병합).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # 00-system
PROJ_DIR = ROOT / "01-templates" / "_data" / "projects"
EMPLOYEES = ROOT / "02-scripts" / "arisa-employees.json"

REMOTE_HOST = "macmini-ts"
REMOTE_DIR = "~/do-better-workspace/00-system/01-templates/_data/projects/"

TASK_STATUS = {"Not Started", "In Progress", "Done"}
ISSUE_STATUS = {"Open", "In Progress", "Closed"}
BRIEF_FIELDS = [
    "name", "code", "client", "type", "location", "pm", "status",
    "start", "end", "dday", "opPeriod",
    "summary", "req", "goal", "kpi", "critical", "deliverables", "risk",
]
# 외부 파트너(명부 밖 협업자) — name·email 필수, org·role은 선택
PARTNER_REQUIRED = ("name", "email")
PARTNER_FIELDS = ("name", "email", "org", "role")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EMAIL_RE = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[A-Za-z]{2,}$")


def is_date(v) -> bool:
    """형식 + 실재하는 날짜인지까지 확인 (2026-13-01·2026-02-30 차단)."""
    if not DATE_RE.match(str(v or "")):
        return False
    try:
        datetime.strptime(str(v), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def safe_id(pid: str) -> str:
    """dashboard-server._safe 와 동일 규칙 — 파일명·URL 안전."""
    return re.sub(r"[^A-Za-z0-9가-힣_\-]", "_", str(pid))[:80] or "proj"


def norm(s: str) -> str:
    """중복 판정용 정규화 — 유니코드 정규화 + 공백 축약."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(s or ""))).strip()


def akey(t: dict) -> str:
    return f"{t.get('start','')}|{norm(t.get('task'))}|{norm(t.get('owner'))}"


def load_employees() -> set[str]:
    try:
        d = json.loads(EMPLOYEES.read_text(encoding="utf-8"))
        return set(d.get("by_name", {}).keys())
    except Exception:
        return set()


def fail(msg: str) -> None:
    print(f"✖ {msg}", file=sys.stderr)
    sys.exit(1)


def partner_names(src: dict) -> set[str]:
    """외부 파트너 이름 집합 — 태스크 담당자 검증에서 명부 대신 인정하는 근거."""
    return {norm(p.get("name")) for p in (src.get("partners") or [])
            if isinstance(p, dict) and norm(p.get("name"))}


def merge_partners(existing: list | None, incoming: list | None) -> list[dict]:
    """이메일(소문자) 기준 병합 — 같은 사람이면 최신 값으로 갱신. 이메일 없는 항목은 버린다."""
    partners: list[dict] = []
    pidx: dict[str, int] = {}
    for p in [*(existing or []), *(incoming or [])]:
        if not isinstance(p, dict) or not norm(p.get("email")):
            continue
        rec = {k: norm(p.get(k)) for k in PARTNER_FIELDS if norm(p.get(k))}
        key = rec["email"].lower()
        if key in pidx:
            partners[pidx[key]].update(rec)
        else:
            pidx[key] = len(partners)
            partners.append(rec)
    return partners


def parse_partner_specs(specs: list[str]) -> list[dict]:
    """'이름=이메일[=소속[=역할]]' → partners 레코드. 이름·이메일 중 하나라도 없으면 중단."""
    out: list[dict] = []
    for spec in specs:
        parts = [s.strip() for s in str(spec).split("=")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            fail(f'--partner 형식 오류: {spec!r} — "이름=이메일[=소속[=역할]]" 형태로 '
                 f"이름과 이메일을 모두 지정해야 합니다.")
        if len(parts) > 4:
            fail(f"--partner 항목 과다: {spec!r} (이름=이메일=소속=역할 까지만)")
        rec = {"name": norm(parts[0]), "email": norm(parts[1])}
        for key, i in (("org", 2), ("role", 3)):
            if len(parts) > i and parts[i]:
                rec[key] = norm(parts[i])
        out.append(rec)
    return out


def validate_partners(src: dict, known: set[str]) -> list[str]:
    """외부 파트너 검증 — 이름과 이메일은 강제. 하나라도 없으면 등록 중단.

    연락처 없는 '이름만 파트너'가 카드에 쌓이면 인수인계 시점에 누구인지
    추적이 불가능해진다. 그래서 경고가 아니라 fail 로 막는다."""
    ps = src.get("partners")
    if ps is None:
        return []
    if not isinstance(ps, list):
        fail('partners 는 배열이어야 합니다. 예: '
             '[{"name":"홍길동","email":"hong@x.com","org":"OO스튜디오","role":"현지 코디"}]')

    warn: list[str] = []
    seen: dict[str, int] = {}
    for i, p in enumerate(ps, 1):
        if not isinstance(p, dict):
            fail(f"partners[{i}] 는 객체여야 합니다 — name·email 필수.")
        for f in PARTNER_REQUIRED:
            if not norm(p.get(f)):
                fail(f"partners[{i}].{f} 가 비어 있습니다 — "
                     f"외부 파트너는 이름과 이메일을 모두 입력해야 합니다.")
        email = norm(p["email"])
        if not EMAIL_RE.match(email):
            fail(f"partners[{i}].email 형식 오류: {p['email']!r} (예: name@company.com)")
        key = email.lower()
        if key in seen:
            fail(f"partners[{i}] 이메일 중복: {email} — partners[{seen[key]}] 와 동일합니다.")
        seen[key] = i
        if known and norm(p["name"]) in known:
            warn.append(f"partners[{i}] {p['name']} 은 사내 명부에 있는 인원입니다 "
                        f"— 외부 파트너가 아니라면 members 로 옮기세요")
        for k in p:
            if k not in PARTNER_FIELDS:
                warn.append(f"partners[{i}] 미지정 필드(저장은 되나 화면 미표시 가능): {k}")
    return warn


def validate(src: dict, known: set[str]) -> list[str]:
    """치명적 오류는 fail(), 되돌릴 수 있는 문제는 경고로 반환."""
    warn: list[str] = validate_partners(src, known)
    pnames = partner_names(src)

    if not norm(src.get("name")):
        fail("name 이 비어 있습니다.")
    if not norm(src.get("pm")):
        fail("pm 이 비어 있습니다.")

    for f in ("start", "end", "dday"):
        v = src.get(f)
        if v and not is_date(v):
            fail(f"{f} 날짜 오류: {v!r} (YYYY-MM-DD, 실재하는 날짜)")
    if src.get("start") and src.get("end") and src["start"] > src["end"]:
        fail(f"start({src['start']}) 가 end({src['end']}) 보다 늦습니다.")

    members = src.get("members") or []
    if known:
        for m in [src["pm"], *members]:
            if norm(m) not in known:
                warn.append(f"명부에 없는 인원: {m} — 사외 협업자라면 members 가 아니라 "
                            f"partners 로(이름·이메일 필수) 등록하세요")

    for i, t in enumerate(src.get("tasks") or [], 1):
        for f in ("task", "owner", "start", "end"):
            if not norm(t.get(f)):
                fail(f"tasks[{i}] 의 {f} 가 비어 있습니다.")
        for f in ("start", "end"):
            if not is_date(t[f]):
                fail(f"tasks[{i}].{f} 날짜 오류: {t[f]!r} (YYYY-MM-DD, 실재하는 날짜)")
        if t["start"] > t["end"]:
            fail(f"tasks[{i}] 기간 역전: {t['start']} > {t['end']}")
        if t.get("status") and t["status"] not in TASK_STATUS:
            fail(f"tasks[{i}].status 허용값 아님: {t['status']!r} ({'/'.join(sorted(TASK_STATUS))})")
        own = norm(t["owner"])
        if known and own not in known and own not in {"팀", "전팀"} and own not in pnames:
            warn.append(f"tasks[{i}] 담당자 명부 미등록: {t['owner']} "
                        f"— 사외 인력이면 partners 에 이름·이메일을 등록하세요")
        if (own not in [norm(m) for m in members] and own != norm(src["pm"])
                and own not in pnames):
            warn.append(f"tasks[{i}] 담당자가 members·partners 어디에도 없음: {t['owner']}")

    for i, s in enumerate(src.get("issues") or [], 1):
        if not norm(s.get("issue")):
            fail(f"issues[{i}].issue 가 비어 있습니다.")
        if s.get("status") and s["status"] not in ISSUE_STATUS:
            fail(f"issues[{i}].status 허용값 아님: {s['status']!r}")

    brief = src.get("brief") or {}
    for k in brief:
        if k not in BRIEF_FIELDS:
            warn.append(f"brief 미지정 필드(무시되지 않지만 화면 미표시 가능): {k}")
    if not norm(brief.get("summary")):
        warn.append("brief.summary 없음 — 포트폴리오 카드에 프로젝트 정의가 비어 보입니다.")
    if not norm(brief.get("goal")):
        warn.append("brief.goal 없음 — 올해 목표가 비어 보입니다.")

    return warn


def build(src: dict, cur: dict | None, replace_tasks: bool) -> tuple[dict, dict]:
    """기존 프로젝트(cur)와 병합한 최종 dict + 변경 통계 반환."""
    today = datetime.now().strftime("%Y%m%d")
    pid = safe_id(src.get("id") or cur and cur.get("id") or f"{norm(src['name'])}-{today}")

    d = dict(cur) if cur else {}
    d["id"] = pid
    d["name"] = norm(src.get("name") or d.get("name"))
    d["pm"] = norm(src.get("pm") or d.get("pm"))
    if src.get("desc"):
        d["desc"] = src["desc"]
    d.setdefault("desc", [])
    for f in ("start", "end", "dday"):
        if src.get(f):
            d[f] = src[f]
        d.setdefault(f, "")

    seen, members = set(), []
    for m in [*(d.get("members") or []), *(src.get("members") or [])]:
        if norm(m) and norm(m) not in seen:
            seen.add(norm(m))
            members.append(norm(m))
    d["members"] = members

    partners = merge_partners(d.get("partners"), src.get("partners"))
    if partners:
        d["partners"] = partners

    # 별칭 — 합집합. 보고·분장의 표기 변형이 이 프로젝트로 매칭되는 근거라
    # 유실·재등록 시 함께 복원되어야 한다(정식명과 같은 값은 의미 없으므로 제외).
    seen_a, aliases = set(), []
    for a in [*(d.get("aliases") or []), *(src.get("aliases") or [])]:
        na = norm(a)
        if na and na not in seen_a and na != d["name"]:
            seen_a.add(na)
            aliases.append(na)
    if aliases:
        d["aliases"] = aliases

    brief = dict(d.get("brief") or {})
    brief.update({k: v for k, v in (src.get("brief") or {}).items() if v not in (None, "")})
    brief.setdefault("name", d["name"])
    brief.setdefault("pm", d["pm"])
    brief.setdefault("status", "In Progress")
    for f in ("start", "end", "dday"):
        brief.setdefault(f, d.get(f, ""))
    d["brief"] = brief

    old_tasks = [] if replace_tasks else list(d.get("tasks") or [])
    have = {akey(t) for t in old_tasks}
    added, skipped = 0, 0
    for t in src.get("tasks") or []:
        nt = {
            "division": norm(t.get("division")) or "기타",
            "task": norm(t["task"]),
            "owner": norm(t["owner"]),
            "start": t["start"],
            "end": t["end"],
            "status": t.get("status") or "Not Started",
            "progress": t.get("progress", 0),
        }
        for opt in ("category", "priority"):
            if t.get(opt):
                nt[opt] = t[opt]
        nt["akey"] = akey(nt)
        if nt["akey"] in have:
            skipped += 1
            continue
        have.add(nt["akey"])
        old_tasks.append(nt)
        added += 1
    d["tasks"] = old_tasks

    old_issues = list(d.get("issues") or [])
    have_i = {norm(s.get("issue")) for s in old_issues}
    i_added, i_skipped = 0, 0
    for s in src.get("issues") or []:
        key = norm(s["issue"])
        if key in have_i:
            i_skipped += 1
            continue
        have_i.add(key)
        old_issues.append({
            "issue": key,
            "division": norm(s.get("division")) or "기타",
            "status": s.get("status") or "Open",
        })
        i_added += 1
    d["issues"] = old_issues

    stamp = datetime.now().strftime("%Y-%m-%d")
    origin = d.get("origin") or ""
    mark = f"프로젝트등록({stamp})"
    d["origin"] = origin if mark in origin else (f"{origin} + {mark}" if origin else mark)

    return d, {
        "tasks_added": added, "tasks_skipped": skipped, "tasks_total": len(d["tasks"]),
        "issues_added": i_added, "issues_skipped": i_skipped, "issues_total": len(d["issues"]),
        "partners_total": len(d.get("partners") or []),
        "created": cur is None,
    }


def apply_status(d: dict, specs: list[str], kind: str) -> list[str]:
    """'문구일부=상태' 목록을 적용. 유일 매칭이 아니면 fail. 변경 로그 반환."""
    field, allowed = ("task", TASK_STATUS) if kind == "task" else ("issue", ISSUE_STATUS)
    items = d.get("tasks" if kind == "task" else "issues") or []
    logs: list[str] = []

    for spec in specs:
        if "=" not in spec:
            fail(f"--{kind} 형식 오류: {spec!r} (예: \"견적서 재발행=Done\")")
        needle, status = spec.rsplit("=", 1)
        needle, status = norm(needle), status.strip()
        if status not in allowed:
            fail(f"--{kind} 상태 허용값 아님: {status!r} ({'/'.join(sorted(allowed))})")

        hits = [it for it in items if needle in norm(it.get(field))]
        if not hits:
            fail(f"--{kind} 매칭 없음: {needle!r}")
        if len(hits) > 1:
            preview = "\n    ".join(norm(h.get(field))[:70] for h in hits)
            fail(f"--{kind} 매칭 {len(hits)}건 — 더 구체적으로 지정하세요:\n    {preview}")

        it = hits[0]
        before = it.get("status") or "-"
        it["status"] = status
        if kind == "task":
            if status == "Done":
                it["progress"] = 100
            elif status == "Not Started":
                it["progress"] = 0
        logs.append(f"  {kind:5s} : {norm(it.get(field))[:56]} … {before} → {status}")

    return logs


# 맥미니 dashboard-server가 직접 쓰는 키 — 로컬은 이 값들을 모른다(divergence의 근원).
# scp 통짜 덮어쓰기가 이걸 지워서 회의 문서함 링크가 실제로 유실됐다(2026-08-02 실측:
# 로컬·맥미니 md5 불일치, docs/pendingBrief가 맥미니에만 존재). 배포 전 원격을 읽어 병합한다.
SERVER_OWNED_KEYS = ("docs", "pendingBrief", "archived")


def _fetch_remote_json(name: str):
    """원격 프로젝트 JSON. 반환: (상태, dict|None) — 상태 ∈ ok|absent|error.

    'absent'(신규 프로젝트)와 'error'(네트워크·파싱 실패)를 구분하는 것이 요점이다.
    error인데 그냥 scp하면 지금까지의 통짜 덮어쓰기와 똑같아진다 — error면 배포를 멈춘다.
    """
    remote_path = REMOTE_DIR.rstrip("/") + "/" + name
    # 주의: shlex.quote를 쓰면 안 된다 — '~'가 작은따옴표에 갇혀 원격 홈 확장이 안 되고,
    # 기존 파일도 전부 absent로 오판해 결국 통짜 덮어쓰기로 돌아간다.
    if remote_path.startswith("~/"):
        remote_path = "$HOME/" + remote_path[2:]
    p = '"' + remote_path.replace('"', '\\"') + '"'
    probe = "test -f {p} && cat {p} || echo __ABSENT__".format(p=p)
    try:
        r = subprocess.run(["ssh", "-o", "ConnectTimeout=15", REMOTE_HOST, probe],
                           capture_output=True, timeout=60)
    except Exception as e:  # noqa: BLE001
        print(f"✖ 원격 확인 실패: {e}", file=sys.stderr)
        return ("error", None)
    out = r.stdout.decode("utf-8", errors="replace").strip()
    if r.returncode != 0:
        print(f"✖ 원격 확인 실패: {r.stderr.decode(errors='replace').strip()[:120]}", file=sys.stderr)
        return ("error", None)
    if out == "__ABSENT__":
        return ("absent", None)
    try:
        return ("ok", json.loads(out))
    except ValueError as e:
        print(f"✖ 원격 JSON 파싱 실패: {e}", file=sys.stderr)
        return ("error", None)


def _merge_for_deploy(local: dict, remote: dict) -> dict:
    """배포 페이로드 = 로컬(등록 결과) + 서버 소유 키(원격) + tasks/issues 원격 우선 합집합.

    tasks를 원격 우선으로 두는 이유: 원격 tasks에는 회의 액션 append·시트 동기
    진행률·완료 근거가 실려 있다. 로컬이 아는 것은 등록 시점의 계획뿐이다 —
    "프로젝트 JSON에 시트에서 복원 불가능한 값을 로컬이 덮지 않는다"의 배포판.
    """
    out = dict(local)
    for k in SERVER_OWNED_KEYS:
        if k in remote:
            out[k] = remote[k]
    r_tasks = list(remote.get("tasks") or [])
    seen = {t.get("akey") for t in r_tasks if t.get("akey")}
    for t in (local.get("tasks") or []):
        if not t.get("akey") or t.get("akey") not in seen:
            r_tasks.append(t)
    out["tasks"] = r_tasks

    def _norm_issue(it):
        return re.sub(r"\s+", "", str((it or {}).get("issue") or ""))
    r_issues = list(remote.get("issues") or [])
    seen_i = {_norm_issue(it) for it in r_issues}
    for it in (local.get("issues") or []):
        if _norm_issue(it) not in seen_i:
            r_issues.append(it)
    out["issues"] = r_issues
    return out


def deploy(path: Path) -> bool:
    # 1) 원격 병합 — 신규(absent)면 그대로, 실패(error)면 덮어쓰기 대신 중단
    state, remote = _fetch_remote_json(path.name)
    if state == "error":
        print("✖ 배포 중단 — 원격 상태를 모르는 채 덮어쓰지 않는다. "
              "네트워크 복구 후 재실행하거나 --no-deploy로 로컬만 저장.", file=sys.stderr)
        return False
    send_path = path
    if state == "ok" and remote:
        merged = _merge_for_deploy(json.loads(path.read_text(encoding="utf-8")), remote)
        send_path = path.parent / (path.name + ".deploy-tmp")
        send_path.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
        kept = [k for k in SERVER_OWNED_KEYS if k in remote]
        if kept:
            print(f"  원격 병합: {'/'.join(kept)} 보존 · tasks {len(merged.get('tasks') or [])}건")
    try:
        subprocess.run(
            ["scp", "-o", "ConnectTimeout=15", str(send_path), f"{REMOTE_HOST}:{REMOTE_DIR}{path.name}"],
            check=True, capture_output=True, timeout=90,
        )
    except subprocess.CalledProcessError as e:
        print(f"✖ 배포 실패: {e.stderr.decode(errors='replace').strip()}", file=sys.stderr)
        return False
    except Exception as e:  # noqa: BLE001
        print(f"✖ 배포 실패: {e}", file=sys.stderr)
        return False
    finally:
        if send_path is not path:
            try:
                send_path.unlink()
            except OSError:
                pass

    check = (
        'python3 -c "import json,sys;'
        f"d=json.load(open(sys.argv[1]));"
        'print(d[\'id\'],d[\'start\'],d[\'end\'],len(d[\'tasks\']),len(d[\'issues\']))" '
        f"{REMOTE_DIR}{path.name}"
    )
    try:
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=15", REMOTE_HOST, check],
            capture_output=True, timeout=60,
        )
        out = r.stdout.decode(errors="replace").strip()
        if out:
            print(f"  맥미니 검증: {out}")
            return True
        print(f"⚠ 맥미니 검증 실패: {r.stderr.decode(errors='replace').strip()}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"⚠ 맥미니 검증 생략: {e}", file=sys.stderr)
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="브리프 JSON 파일 경로 (- 는 stdin)")
    ap.add_argument("--id", help="상태 갱신 모드 — 대상 프로젝트 id")
    ap.add_argument("--task", action="append", default=[], metavar="문구일부=상태",
                    help="태스크 상태 갱신 (Not Started/In Progress/Done)")
    ap.add_argument("--issue", action="append", default=[], metavar="문구일부=상태",
                    help="이슈 상태 갱신 (Open/In Progress/Closed)")
    ap.add_argument("--partner", action="append", default=[], metavar="이름=이메일[=소속[=역할]]",
                    help="외부 파트너 추가·갱신 — 이름과 이메일은 필수")
    ap.add_argument("--dry-run", action="store_true", help="검증만 수행, 파일 미기록")
    ap.add_argument("--no-deploy", action="store_true", help="로컬만 저장, 맥미니 배포 생략")
    ap.add_argument("--replace-tasks", action="store_true", help="tasks 병합 대신 통째 교체")
    a = ap.parse_args()

    # ── 상태 갱신 · 파트너 등록 모드 ────────────────────────────
    if a.task or a.issue or a.partner:
        if not a.id:
            fail("--task/--issue/--partner 는 --id 와 함께 씁니다.")
        target = PROJ_DIR / f"{safe_id(a.id)}.json"
        if not target.exists():
            fail(f"프로젝트를 찾을 수 없습니다: {target.name}")
        d = json.loads(target.read_text(encoding="utf-8"))

        logs = apply_status(d, a.task, "task") + apply_status(d, a.issue, "issue")
        if a.partner:
            incoming = parse_partner_specs(a.partner)
            before = {norm(p.get("email")).lower() for p in (d.get("partners") or [])}
            merged = merge_partners(d.get("partners"), incoming)
            # 병합 결과를 그대로 검증 — 이름·이메일 누락이나 형식 오류면 여기서 중단
            for w in validate_partners({"partners": merged}, load_employees()):
                print(f"⚠ {w}", file=sys.stderr)
            d["partners"] = merged
            for p in incoming:
                verb = "갱신" if p["email"].lower() in before else "추가"
                tail = " · ".join(x for x in (p.get("org"), p.get("role")) if x)
                logs.append(f"  파트너: {p['name']} <{p['email']}>"
                            + (f" — {tail}" if tail else "") + f" … {verb}")

        print(f"\n[{'DRY-RUN' if a.dry_run else '상태 갱신'}] {d['id']}")
        print("\n".join(logs))
        done = sum(1 for t in d.get("tasks", []) if t.get("status") == "Done")
        openi = sum(1 for s in d.get("issues", []) if s.get("status") == "Open")
        print(f"  현황  : 태스크 {done}/{len(d.get('tasks', []))} 완료 · 이슈 Open {openi}/{len(d.get('issues', []))}")

        if a.dry_run:
            print("\n※ dry-run — 파일을 쓰지 않았습니다.")
            return
        bak = target.with_suffix(f".json.bak-{datetime.now():%Y%m%d-%H%M}")
        shutil.copy(target, bak)
        target.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  백업  : {bak.name}")
        if a.no_deploy:
            print("\n※ --no-deploy — 맥미니 배포 생략.")
            return
        ok = deploy(target)
        print("\n✔ 완료 — 통합 대시보드 즉시 반영" if ok else "\n⚠ 로컬 저장됨, 맥미니 반영 미확인")
        return
    # ───────────────────────────────────────────────────────────

    if not a.input:
        fail("--input(등록) 또는 --id + --task/--issue(상태 갱신) 중 하나가 필요합니다.")

    raw = sys.stdin.read() if a.input == "-" else Path(a.input).read_text(encoding="utf-8")
    try:
        src = json.loads(raw)
    except json.JSONDecodeError as e:
        fail(f"입력 JSON 파싱 실패: {e}")

    warns = validate(src, load_employees())

    pid = safe_id(src.get("id") or f"{norm(src.get('name'))}-{datetime.now():%Y%m%d}")
    target = PROJ_DIR / f"{pid}.json"
    cur = None
    if target.exists():
        try:
            cur = json.loads(target.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            fail(f"기존 파일 읽기 실패({target.name}): {e}")

    final, st = build(src, cur, a.replace_tasks)
    target = PROJ_DIR / f"{final['id']}.json"

    for w in warns:
        print(f"⚠ {w}", file=sys.stderr)

    mode = "신규 생성" if st["created"] else ("교체(tasks)" if a.replace_tasks else "병합")
    print(f"\n[{'DRY-RUN' if a.dry_run else mode}] {final['id']}")
    print(f"  기간   : {final['start']} ~ {final['end']} (D-Day {final['dday']})")
    print(f"  PM/멤버: {final['pm']} / {', '.join(final['members']) or '-'}")
    if final.get("partners"):
        for p in final["partners"]:
            tail = " · ".join(x for x in (p.get("org"), p.get("role")) if x)
            print(f"  파트너 : {p['name']} <{p['email']}>" + (f" — {tail}" if tail else ""))
    if final.get("aliases"):
        print(f"  별칭   : {', '.join(final['aliases'])}")
    print(f"  브리프 : {sum(1 for k in BRIEF_FIELDS if norm(final['brief'].get(k)))}/{len(BRIEF_FIELDS)} 필드")
    print(f"  태스크 : +{st['tasks_added']} (중복 skip {st['tasks_skipped']}) → 총 {st['tasks_total']}")
    print(f"  이슈   : +{st['issues_added']} (중복 skip {st['issues_skipped']}) → 총 {st['issues_total']}")

    if a.dry_run:
        print("\n※ dry-run — 파일을 쓰지 않았습니다.")
        return

    PROJ_DIR.mkdir(parents=True, exist_ok=True)
    if target.exists():
        bak = target.with_suffix(f".json.bak-{datetime.now():%Y%m%d-%H%M}")
        shutil.copy(target, bak)
        print(f"  백업   : {bak.name}")
    target.write_text(json.dumps(final, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  저장   : {target}")

    if a.no_deploy:
        print("\n※ --no-deploy — 맥미니 배포 생략. 반영하려면 재실행하거나 scp 하세요.")
        return
    print("  배포   : 맥미니(macmini-ts) …")
    ok = deploy(target)
    print("\n✔ 완료 — 통합 대시보드(8780) 즉시 반영 (서버가 요청마다 파일을 읽음)"
          if ok else "\n⚠ 로컬 저장은 됐으나 맥미니 반영은 확인되지 않았습니다.")


if __name__ == "__main__":
    main()
