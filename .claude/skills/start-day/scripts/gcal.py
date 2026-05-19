#!/usr/bin/env python3
"""
Google Calendar 이벤트 관리 스크립트

사용법:
    # 이벤트 추가
    python3 gcal.py add --title "회의" --date 2026-04-08 --start 15:00 --end 16:00 --description "메모"

    # 이벤트 조회 (오늘)
    python3 gcal.py list

    # 이벤트 조회 (특정 날짜)
    python3 gcal.py list --date 2026-04-08

    # 이벤트 조회 (기간)
    python3 gcal.py list --from 2026-04-01 --to 2026-04-07

인증:
    - ~/.config/gmail-claude/credentials.json 필요
    - 최초 실행 시 브라우저 인증 → gcal_token.json 자동 생성
"""

import argparse
import json
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

SCOPES = ["https://www.googleapis.com/auth/calendar"]

CONFIG_DIR = Path.home() / ".config" / "gmail-claude"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"
TOKEN_PATH = CONFIG_DIR / "gcal_token.json"


def get_calendar_service():
    """Google Calendar API 서비스 객체를 반환합니다."""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

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
                    "message": f"credentials.json이 없습니다. {CREDENTIALS_PATH}에 파일을 저장하세요."
                }))
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def add_event(service, title, date, start_time, end_time=None, description=None, location=None):
    """캘린더에 이벤트를 추가합니다."""
    if not end_time:
        # 기본 1시간
        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(hours=1)
        end_time = end_dt.strftime("%H:%M")

    event = {
        "summary": title,
        "start": {
            "dateTime": f"{date}T{start_time}:00",
            "timeZone": "Asia/Seoul",
        },
        "end": {
            "dateTime": f"{date}T{end_time}:00",
            "timeZone": "Asia/Seoul",
        },
    }

    if description:
        event["description"] = description
    if location:
        event["location"] = location

    result = service.events().insert(calendarId="primary", body=event).execute()
    print(json.dumps({
        "status": "created",
        "id": result.get("id"),
        "title": title,
        "date": date,
        "start": start_time,
        "end": end_time,
        "link": result.get("htmlLink")
    }, ensure_ascii=False, indent=2))


def delete_event(service, event_id):
    """캘린더 이벤트를 삭제합니다."""
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    print(json.dumps({"status": "deleted", "id": event_id}, ensure_ascii=False, indent=2))


def list_events(service, date_from, date_to=None):
    """캘린더 이벤트를 조회합니다."""
    if not date_to:
        date_to = date_from

    time_min = f"{date_from}T00:00:00+09:00"
    time_max = f"{date_to}T23:59:59+09:00"

    results = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        maxResults=50
    ).execute()

    events = results.get("items", [])
    output = []

    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        output.append({
            "id": event.get("id"),
            "title": event.get("summary", "(제목 없음)"),
            "start": start,
            "end": end,
            "location": event.get("location", ""),
            "description": event.get("description", ""),
        })

    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Google Calendar 관리")
    subparsers = parser.add_subparsers(dest="command")

    # add 명령
    add_parser = subparsers.add_parser("add", help="이벤트 추가")
    add_parser.add_argument("--title", required=True, help="이벤트 제목")
    add_parser.add_argument("--date", required=True, help="날짜 (YYYY-MM-DD)")
    add_parser.add_argument("--start", required=True, help="시작 시간 (HH:MM)")
    add_parser.add_argument("--end", help="종료 시간 (HH:MM, 기본: 시작+1시간)")
    add_parser.add_argument("--description", help="설명")
    add_parser.add_argument("--location", help="장소")

    # delete 명령
    del_parser = subparsers.add_parser("delete", help="이벤트 삭제")
    del_parser.add_argument("--id", required=True, help="이벤트 ID")

    # list 명령
    list_parser = subparsers.add_parser("list", help="이벤트 조회")
    list_parser.add_argument("--date", help="조회 날짜 (YYYY-MM-DD, 기본: 오늘)")
    list_parser.add_argument("--from", dest="date_from", help="시작 날짜")
    list_parser.add_argument("--to", dest="date_to", help="종료 날짜")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        service = get_calendar_service()

        if args.command == "add":
            add_event(service, args.title, args.date, args.start, args.end, args.description, args.location)
        elif args.command == "delete":
            delete_event(service, args.id)
        elif args.command == "list":
            if args.date_from:
                list_events(service, args.date_from, args.date_to)
            else:
                date = args.date or datetime.now().strftime("%Y-%m-%d")
                list_events(service, date)

    except Exception as e:
        print(json.dumps({"error": "runtime_error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
