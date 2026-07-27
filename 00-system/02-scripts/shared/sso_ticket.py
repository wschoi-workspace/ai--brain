"""ARISA → 외부 서비스 SSO 티켓 서명기.

ARISA 대시보드가 로그인한 사용자의 신원을 외부 서비스(현재는 HR 포털)에
넘길 때 쓰는 단발성 HS256 티켓을 만든다. 검증은 수신 측이 한다.

설계 원칙
  - **신원만 전달한다.** 권한(role)은 수신 측이 자기 데이터로 결정한다.
    티켓의 arisa_role은 참고·로그용이며 권한 부여에 쓰면 안 된다.
  - TTL 90초 + jti 1회용 — URL 쿼리로 노출되는 값이므로 수명을 짧게 잡는다.
  - ensure_ascii=True — 한글 sub를 \\uXXXX로 이스케이프해 페이로드를 순수 ASCII로
    만든다. 맥미니(발급)와 컨테이너(검증) 간 인코딩 변수를 없앤다.
  - stdlib만 사용(hmac/hashlib/base64) — 신규 의존성 0.

수신 측 구현: hr-workspace/20-operations/21-hr/portal/sso/token.py
플랜: partitioned-beaming-turing (2026-07-27)
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

ISS = "arisa-os"
DEFAULT_TTL = 90          # 수신 측 MAX_TTL(300초)보다 짧게 유지할 것


def _b64(raw: bytes) -> bytes:
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def issue(name: str, arisa_role: str, secret: str, *,
          audience: str, purpose: str, ttl: int = DEFAULT_TTL) -> str:
    """단발성 티켓 발급. secret이 비어 있으면 ValueError(fail-closed)."""
    if not secret:
        raise ValueError("SSO 시크릿 미설정 — 티켓 발급 거부")
    if not (name or "").strip():
        raise ValueError("사용자 이름 없음 — 티켓 발급 거부")

    now = int(time.time())
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"},
                             separators=(",", ":")).encode())
    payload = _b64(json.dumps({
        "iss": ISS,
        "aud": audience,
        "purpose": purpose,
        "sub": name.strip(),
        "arisa_role": arisa_role or "",
        "jti": secrets.token_hex(16),
        "iat": now,
        "exp": now + int(ttl),
    }, separators=(",", ":"), ensure_ascii=True).encode())

    msg = header + b"." + payload
    sig = _b64(hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest())
    return (msg + b"." + sig).decode("ascii")


def issue_hr(name: str, arisa_role: str, secret: str, ttl: int = DEFAULT_TTL) -> str:
    """HR 포털(rent-hr-portal)용 티켓."""
    return issue(name, arisa_role, secret,
                 audience="rent-hr-portal", purpose="arisa_sso", ttl=ttl)
