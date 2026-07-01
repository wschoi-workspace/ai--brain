#!/usr/bin/env python3
"""
canva_autofill.py — Canva Connect API (Enterprise) Autofill 헬퍼.

SNS 카드뉴스 자동화 파이프라인의 D 모듈.
지정 브랜드 템플릿에 정리된 콘텐츠(text 필드)를 자동 채워 카드뉴스 초안(디자인)을 만든다.

의존성: 표준 라이브러리만 사용 (urllib) — pip 설치 불필요.

OAuth(PKCE) 흐름:
  1) 최초 1회   : `python3 canva_autofill.py auth`  → 브라우저 인가 → refresh_token을 .env에 저장
  2) 필드 확인  : `python3 canva_autofill.py dataset`  → 브랜드 템플릿의 데이터 필드 키/타입 출력
  3) 디자인 생성: `python3 canva_autofill.py autofill --data payload.json [--title "..."]`
                  → 디자인 생성(async) → job 폴링 → edit_url / view_url 출력(JSON)

스코프: brandtemplate:content:read design:content:write
필요 .env: CANVA_CLIENT_ID, CANVA_CLIENT_SECRET, CANVA_REFRESH_TOKEN, CANVA_BRAND_TEMPLATE_ID
참고: https://www.canva.dev/docs/connect/
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

# --- 설정 ---------------------------------------------------------------
WORKSPACE = Path(__file__).resolve().parents[2]  # do-better-workspace/
ENV_PATH = WORKSPACE / ".env"

AUTHORIZE_URL = "https://www.canva.com/api/oauth/authorize"
TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"
API_BASE = "https://api.canva.com/rest/v1"
SCOPES = "brandtemplate:content:read design:content:write"

# 로컬 리다이렉트 (Canva Developer Portal의 "Redirect URLs"에 동일하게 등록할 것)
REDIRECT_HOST = "127.0.0.1"
REDIRECT_PORT = 8910
REDIRECT_URI = f"http://{REDIRECT_HOST}:{REDIRECT_PORT}/callback"

POLL_INTERVAL_SEC = 2
POLL_TIMEOUT_SEC = 120


# --- .env 헬퍼 ----------------------------------------------------------
def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    # 실제 환경변수가 있으면 우선
    for k in ("CANVA_CLIENT_ID", "CANVA_CLIENT_SECRET", "CANVA_REFRESH_TOKEN",
              "CANVA_BRAND_TEMPLATE_ID"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def upsert_env(key: str, value: str) -> None:
    """.env에서 key 라인을 갱신하거나 없으면 추가."""
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- HTTP 헬퍼 ----------------------------------------------------------
def _req(method: str, url: str, *, headers: dict | None = None,
         data: bytes | None = None) -> dict:
    req = urllib.request.Request(url, method=method, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise SystemExit(f"[Canva API 오류 {e.code}] {method} {url}\n{detail}")


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(raw).decode()


# --- OAuth --------------------------------------------------------------
def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    return verifier, challenge


def cmd_auth(env: dict) -> None:
    """최초 1회 인가 → refresh_token을 .env에 저장."""
    client_id = env.get("CANVA_CLIENT_ID")
    client_secret = env.get("CANVA_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("CANVA_CLIENT_ID / CANVA_CLIENT_SECRET 를 .env에 먼저 넣어주세요.")

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    params = {
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    }
    auth_url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)

    code_holder: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            qs = urllib.parse.urlparse(self.path).query
            q = urllib.parse.parse_qs(qs)
            if q.get("state", [""])[0] != state:
                self.send_response(400); self.end_headers()
                self.wfile.write(b"state mismatch"); return
            code_holder["code"] = q.get("code", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>인증 완료 — 터미널로 돌아가세요.</h2>".encode())

        def log_message(self, *a):  # 조용히
            pass

    server = http.server.HTTPServer((REDIRECT_HOST, REDIRECT_PORT), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    print(f"\n브라우저에서 Canva 인가를 진행하세요. 안 열리면 아래 URL을 직접 여세요:\n{auth_url}\n")
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    # 콜백 대기
    for _ in range(120):
        if code_holder.get("code"):
            break
        time.sleep(1)
    if not code_holder.get("code"):
        raise SystemExit("인가 코드 수신 실패 (타임아웃).")

    # code → token 교환
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code_holder["code"],
        "code_verifier": verifier,
        "redirect_uri": REDIRECT_URI,
    }).encode()
    tok = _req("POST", TOKEN_URL, headers={
        "Authorization": _basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }, data=data)

    refresh = tok.get("refresh_token")
    if not refresh:
        raise SystemExit(f"refresh_token 없음: {tok}")
    upsert_env("CANVA_REFRESH_TOKEN", refresh)
    print("✅ refresh_token을 .env에 저장했습니다. 이제 dataset / autofill 명령을 쓸 수 있습니다.")


def get_access_token(env: dict) -> str:
    """refresh_token으로 access_token 발급 (회전된 refresh_token은 .env에 갱신 저장)."""
    client_id = env.get("CANVA_CLIENT_ID")
    client_secret = env.get("CANVA_CLIENT_SECRET")
    refresh = env.get("CANVA_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh):
        raise SystemExit("CANVA_CLIENT_ID/SECRET/REFRESH_TOKEN 가 필요합니다. 먼저 `auth` 를 실행하세요.")

    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh,
    }).encode()
    tok = _req("POST", TOKEN_URL, headers={
        "Authorization": _basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }, data=data)

    if tok.get("refresh_token") and tok["refresh_token"] != refresh:
        upsert_env("CANVA_REFRESH_TOKEN", tok["refresh_token"])
    access = tok.get("access_token")
    if not access:
        raise SystemExit(f"access_token 없음: {tok}")
    return access


# --- API 호출 -----------------------------------------------------------
def get_dataset(access: str, template_id: str) -> dict:
    return _req("GET", f"{API_BASE}/brand-templates/{template_id}/dataset",
                headers={"Authorization": f"Bearer {access}"})


def create_autofill(access: str, template_id: str, data_fields: dict,
                    title: str | None = None) -> str:
    payload = {
        "brand_template_id": template_id,
        "data": data_fields,
    }
    if title:
        payload["title"] = title[:255]
    res = _req("POST", f"{API_BASE}/autofills",
               headers={"Authorization": f"Bearer {access}",
                        "Content-Type": "application/json"},
               data=json.dumps(payload).encode())
    job = res.get("job", {})
    job_id = job.get("id")
    if not job_id:
        raise SystemExit(f"autofill job id 없음: {res}")
    return job_id


def poll_job(access: str, job_id: str) -> dict:
    deadline = time.time() + POLL_TIMEOUT_SEC
    while time.time() < deadline:
        res = _req("GET", f"{API_BASE}/autofills/{job_id}",
                   headers={"Authorization": f"Bearer {access}"})
        job = res.get("job", {})
        status = job.get("status")
        if status == "success":
            return job.get("result", {})
        if status == "failed":
            raise SystemExit(f"autofill 실패: {job.get('error', job)}")
        time.sleep(POLL_INTERVAL_SEC)
    raise SystemExit("autofill 폴링 타임아웃.")


def to_text_fields(flat: dict) -> dict:
    """{key: "값"} 평면 딕셔너리를 Canva text 필드 구조로 변환."""
    return {k: {"type": "text", "text": str(v)} for k, v in flat.items() if v is not None}


# --- CLI ----------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="Canva Autofill 헬퍼")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth", help="최초 1회 OAuth 인가 → refresh_token 저장")
    d = sub.add_parser("dataset", help="브랜드 템플릿 데이터 필드 조회")
    d.add_argument("--template", help="브랜드 템플릿 ID (없으면 .env)")
    a = sub.add_parser("autofill", help="디자인 자동 생성")
    a.add_argument("--data", required=True, help="필드 데이터 JSON 파일 경로")
    a.add_argument("--template", help="브랜드 템플릿 ID (없으면 .env)")
    a.add_argument("--title", help="디자인 제목")
    a.add_argument("--raw", action="store_true",
                   help="data JSON이 이미 Canva 필드 구조(type/text)면 변환 생략")
    args = p.parse_args()

    env = load_env()

    if args.cmd == "auth":
        cmd_auth(env)
        return

    access = get_access_token(env)

    if args.cmd == "dataset":
        tid = args.template or env.get("CANVA_BRAND_TEMPLATE_ID")
        if not tid:
            raise SystemExit("--template 또는 .env의 CANVA_BRAND_TEMPLATE_ID 필요")
        print(json.dumps(get_dataset(access, tid), ensure_ascii=False, indent=2))
        return

    if args.cmd == "autofill":
        tid = args.template or env.get("CANVA_BRAND_TEMPLATE_ID")
        if not tid:
            raise SystemExit("--template 또는 .env의 CANVA_BRAND_TEMPLATE_ID 필요")
        flat = json.loads(Path(args.data).read_text(encoding="utf-8"))
        fields = flat if args.raw else to_text_fields(flat)
        job_id = create_autofill(access, tid, fields, args.title)
        result = poll_job(access, job_id)
        design = result.get("design", {})
        out = {
            "design_id": design.get("id"),
            "title": design.get("title"),
            "edit_url": design.get("urls", {}).get("edit_url"),
            "view_url": design.get("urls", {}).get("view_url"),
            "thumbnail": design.get("thumbnail", {}).get("url"),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
