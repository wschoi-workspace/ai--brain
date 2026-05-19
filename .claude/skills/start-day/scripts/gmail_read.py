#!/usr/bin/env python3
"""
Gmail 메일 읽기/검색 스크립트 (멀티 계정 지원)

사용법:
    # 메일 검색 (전체 계정)
    python3 gmail_read.py search "서울디자인재단"

    # 특정 계정만 검색
    python3 gmail_read.py search "키워드" --account codexzero999

    # 메일 검색 (최근 N일)
    python3 gmail_read.py search "키워드" --days 7

    # 특정 메일 본문 읽기 (message ID)
    python3 gmail_read.py read --id MESSAGE_ID --account project-rent

인증: gmail_unreplied.py와 동일 (~/.config/gmail-claude/token_<account>.json)
"""

import argparse
import base64
import json
import re
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

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
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
    if account_name:
        if account_name not in ACCOUNTS:
            print(json.dumps({"error": "unknown_account", "accounts": list(ACCOUNTS.keys())}))
            sys.exit(1)
        token_path = ACCOUNTS[account_name]["token"]
    else:
        # 기본값: project-rent
        token_path = ACCOUNTS["project-rent"]["token"]

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
                print(json.dumps({"error": "credentials_missing"}))
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def extract_body(payload):
    """메일 본문을 추출합니다 (text/plain 우선, 없으면 text/html에서 텍스트 추출)."""
    body_text = ""

    if payload.get("body", {}).get("data"):
        mime = payload.get("mimeType", "")
        data = payload["body"]["data"]
        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        if "plain" in mime:
            return decoded
        elif "html" in mime:
            body_text = decoded

    for part in payload.get("parts", []):
        result = extract_body(part)
        if result:
            # plain text 우선
            if part.get("mimeType") == "text/plain":
                return result
            if not body_text:
                body_text = result

    # HTML에서 태그 제거
    if body_text and "<" in body_text:
        body_text = re.sub(r"<style[^>]*>.*?</style>", "", body_text, flags=re.DOTALL)
        body_text = re.sub(r"<script[^>]*>.*?</script>", "", body_text, flags=re.DOTALL)
        body_text = re.sub(r"<[^>]+>", " ", body_text)
        body_text = re.sub(r"\s+", " ", body_text).strip()
        # &nbsp; 등 HTML 엔티티 처리
        body_text = body_text.replace("&nbsp;", " ").replace("&amp;", "&")
        body_text = body_text.replace("&lt;", "<").replace("&gt;", ">")

    return body_text


def search_mail(service, query, days=7, max_results=10):
    """메일을 검색하고 제목/발신자/ID를 반환합니다."""
    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    full_query = f"after:{after_date} {query}"

    results = service.users().messages().list(
        userId="me", q=full_query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        print(json.dumps([], ensure_ascii=False))
        return

    output = []
    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

        from_raw = headers.get("From", "")
        if "<" in from_raw:
            from_name = from_raw.split("<")[0].strip().strip('"')
            from_email = from_raw.split("<")[1].rstrip(">") if "<" in from_raw else from_raw
        else:
            from_name = from_raw
            from_email = from_raw

        output.append({
            "id": msg_ref["id"],
            "from_name": from_name,
            "from_email": from_email,
            "subject": headers.get("Subject", "(제목 없음)"),
            "date": headers.get("Date", ""),
        })

    print(json.dumps(output, ensure_ascii=False, indent=2))


def read_mail(service, message_id):
    """특정 메일의 전체 내용을 읽습니다."""
    msg = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    body = extract_body(msg.get("payload", {}))

    from_raw = headers.get("From", "")
    if "<" in from_raw:
        from_name = from_raw.split("<")[0].strip().strip('"')
        from_email = from_raw.split("<")[1].rstrip(">")
    else:
        from_name = from_raw
        from_email = from_raw

    output = {
        "id": message_id,
        "from_name": from_name,
        "from_email": from_email,
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", "(제목 없음)"),
        "date": headers.get("Date", ""),
        "body": body[:5000] if body else "(본문 없음)",
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Gmail 메일 읽기/검색 (멀티 계정)")
    parser.add_argument("--account", choices=list(ACCOUNTS.keys()), default=None,
                        help="계정 선택 (미지정 시 project-rent)")
    subparsers = parser.add_subparsers(dest="command")

    # search
    search_parser = subparsers.add_parser("search", help="메일 검색")
    search_parser.add_argument("query", help="검색어")
    search_parser.add_argument("--days", type=int, default=7, help="최근 N일 (기본: 7)")
    search_parser.add_argument("--max", type=int, default=10, help="최대 결과 수 (기본: 10)")

    # read
    read_parser = subparsers.add_parser("read", help="메일 본문 읽기")
    read_parser.add_argument("--id", required=True, help="메시지 ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    account = args.account or "project-rent"

    try:
        service = get_gmail_service(account)
        if args.command == "search":
            search_mail(service, args.query, args.days, args.max)
        elif args.command == "read":
            read_mail(service, args.id)
    except Exception as e:
        print(json.dumps({"error": "runtime_error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
