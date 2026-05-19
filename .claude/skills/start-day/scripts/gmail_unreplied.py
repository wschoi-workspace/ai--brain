#!/usr/bin/env python3
"""
Gmail 미회신 업무 메일 조회 스크립트 (멀티 계정 지원)

최근 3일간 수신 메일 중 미회신 메일을 필터링하여 JSON으로 출력합니다.

사용법:
    python3 gmail_unreplied.py                        # 전체 계정
    python3 gmail_unreplied.py --account project-rent  # 특정 계정
    python3 gmail_unreplied.py --account codexzero999  # 특정 계정

출력 형식:
    [{"account": "계정", "from": "발신자", "subject": "제목", "date": "2026-03-29", "days_ago": 0}, ...]

인증:
    - ~/.config/gmail-claude/credentials.json 필요 (Google Cloud에서 다운로드)
    - 최초 실행 시 브라우저 인증 → token_<account>.json 자동 생성
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print(json.dumps({"error": "dependencies_missing", "message": "pip install google-auth-oauthlib google-api-python-client"}))
    sys.exit(1)

# Gmail API 스코프 (읽기 전용)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# 인증 파일 경로
CONFIG_DIR = Path.home() / ".config" / "gmail-claude"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"

# 등록된 계정 목록
ACCOUNTS = {
    "project-rent": {
        "email": "ws.choi@project-rent.com",
        "token": CONFIG_DIR / "token_project-rent.json",
    },
    "codexzero999": {
        "email": "codexzero999@gmail.com",
        "token": CONFIG_DIR / "token_codexzero999.json",
    },
}


def get_gmail_service(account_name=None):
    """Gmail API 서비스 객체를 반환합니다."""
    if account_name:
        if account_name not in ACCOUNTS:
            print(json.dumps({"error": "unknown_account", "accounts": list(ACCOUNTS.keys())}))
            sys.exit(1)
        token_path = ACCOUNTS[account_name]["token"]
    else:
        token_path = CONFIG_DIR / "token.json"

    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not CREDENTIALS_PATH.exists():
                print(json.dumps({
                    "error": "credentials_missing",
                    "message": f"credentials.json이 없습니다. {CREDENTIALS_PATH}에 파일을 저장하세요.",
                    "setup_guide": "SETUP-GMAIL.md 참조"
                }))
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_my_email(service):
    """내 이메일 주소를 가져옵니다."""
    profile = service.users().getProfile(userId="me").execute()
    return profile["emailAddress"]


def get_unreplied_messages(service, days=3, account_label=""):
    """최근 N일간 미회신 메일을 조회합니다."""
    my_email = get_my_email(service)
    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    today = datetime.now()

    # 최근 N일 수신 메일 조회 (보낸 메일 제외)
    query = f"after:{after_date} in:inbox -from:me"
    results = service.users().messages().list(
        userId="me", q=query, maxResults=100
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    unreplied = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        thread_id = msg.get("threadId")

        # 스레드 내 메시지 확인 → 내가 답장했는지 체크
        thread = service.users().threads().get(
            userId="me", id=thread_id, format="metadata",
            metadataHeaders=["From"]
        ).execute()

        replied = False
        for thread_msg in thread.get("messages", []):
            thread_headers = {h["name"]: h["value"] for h in thread_msg.get("payload", {}).get("headers", [])}
            from_header = thread_headers.get("From", "")
            # 내 이메일이 From에 포함되어 있으면 답장한 것
            if my_email.lower() in from_header.lower():
                replied = True
                break

        if not replied:
            # 날짜 파싱
            date_str = headers.get("Date", "")
            try:
                # 다양한 날짜 형식 처리
                from email.utils import parsedate_to_datetime
                msg_date = parsedate_to_datetime(date_str)
                days_ago = (today - msg_date.replace(tzinfo=None)).days
                date_formatted = msg_date.strftime("%Y-%m-%d")
            except Exception:
                days_ago = 0
                date_formatted = date_str[:10] if len(date_str) >= 10 else date_str

            # 발신자 정리
            from_raw = headers.get("From", "알 수 없음")
            # "이름 <email>" 형식에서 이름 추출
            if "<" in from_raw:
                from_name = from_raw.split("<")[0].strip().strip('"')
                if not from_name:
                    from_name = from_raw
            else:
                from_name = from_raw

            unreplied.append({
                "account": account_label,
                "from": from_name,
                "subject": headers.get("Subject", "(제목 없음)"),
                "date": date_formatted,
                "days_ago": days_ago
            })

    # 날짜 역순 정렬 (최신순)
    unreplied.sort(key=lambda x: x["date"], reverse=True)
    return unreplied


def main():
    parser = argparse.ArgumentParser(description="Gmail 미회신 메일 조회 (멀티 계정)")
    parser.add_argument("--account", choices=list(ACCOUNTS.keys()), default=None,
                        help="특정 계정만 조회 (미지정 시 전체 계정)")
    parser.add_argument("--days", type=int, default=3, help="최근 N일 (기본: 3)")
    args = parser.parse_args()

    try:
        if args.account:
            # 특정 계정만
            accounts_to_check = {args.account: ACCOUNTS[args.account]}
        else:
            # 전체 계정
            accounts_to_check = ACCOUNTS

        all_unreplied = []
        for name, info in accounts_to_check.items():
            try:
                service = get_gmail_service(name)
                unreplied = get_unreplied_messages(service, days=args.days, account_label=name)
                all_unreplied.extend(unreplied)
            except Exception as e:
                all_unreplied.append({
                    "account": name,
                    "error": str(e)
                })

        # 날짜 역순 정렬
        all_unreplied.sort(key=lambda x: x.get("date", ""), reverse=True)
        print(json.dumps(all_unreplied, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({
            "error": "runtime_error",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
