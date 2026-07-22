#!/usr/bin/env python3
"""Gmail/Calendar raw JSON → 대시보드 스키마 변환

Usage:
    python3 transform-api-data.py <data_dir>

_raw_unreplied.json + _raw_recent.json → email-actions.json
_raw_cal_today.json + _raw_cal_week.json → calendar-today.json + calendar-week.json
"""

import json
import os
import sys
from datetime import datetime, timedelta

DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)

now = datetime.now()
today_str = now.strftime("%Y-%m-%d")


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {filename}")


# ===== Email Transform =====
def transform_emails():
    """gmail_unreplied.py 출력 + gmail_read.py 출력 → email-actions.json"""
    unreplied_raw = load_json("_raw_unreplied.json")
    recent_raw = load_json("_raw_recent.json")

    if not unreplied_raw and not recent_raw:
        print("  ⚠ 메일 raw 데이터 없음 — 스킵")
        return

    # unreplied_raw: [{"from": "...", "subject": "...", "date": "YYYY-MM-DD", "days_ago": N}, ...]
    # recent_raw: 동일 형식 또는 유사

    recent_emails = []
    seen_subjects = set()

    # 미회신 메일 (unreplied) — replied=False
    if isinstance(unreplied_raw, list):
        for e in unreplied_raw:
            hours_ago = e.get("days_ago", 0) * 24
            email_date = e.get("date", "")
            # 더 정확한 hours_ago 계산
            try:
                d = datetime.strptime(email_date, "%Y-%m-%d")
                hours_ago = int((now - d).total_seconds() / 3600)
            except (ValueError, TypeError):
                pass

            key = f"{e.get('from', '')}|{e.get('subject', '')}"
            seen_subjects.add(key)
            recent_emails.append({
                "id": key[:16],
                "from": e.get("from", "알 수 없음"),
                "subject": e.get("subject", "(제목 없음)"),
                "date": email_date,
                "hours_ago": hours_ago,
                "replied": False,
                "gmail_link": f"https://mail.google.com/mail/u/0/#search/{e.get('subject', '')[:20]}",
            })

    # 최근 메일 (recent) — unreplied에 없으면 replied=True로 추가
    if isinstance(recent_raw, list):
        for e in recent_raw:
            key = f"{e.get('from', '')}|{e.get('subject', '')}"
            if key in seen_subjects:
                continue
            hours_ago = e.get("days_ago", 0) * 24
            try:
                email_date = e.get("date", "")
                d = datetime.strptime(email_date, "%Y-%m-%d")
                hours_ago = int((now - d).total_seconds() / 3600)
            except (ValueError, TypeError):
                email_date = ""

            recent_emails.append({
                "id": key[:16],
                "from": e.get("from", "알 수 없음"),
                "subject": e.get("subject", "(제목 없음)"),
                "date": email_date,
                "hours_ago": hours_ago,
                "replied": True,
                "gmail_link": f"https://mail.google.com/mail/u/0/#search/{e.get('subject', '')[:20]}",
            })

    # 우선순위 계산
    unreplied = [e for e in recent_emails if not e["replied"]]
    urgent = sum(1 for e in unreplied if e["hours_ago"] >= 48)
    warning = sum(1 for e in unreplied if 24 <= e["hours_ago"] < 48)
    normal = len(unreplied) - urgent - warning

    result = {
        "generated_at": now.isoformat(),
        "recent_emails": sorted(recent_emails, key=lambda x: x["hours_ago"]),
        "unreplied_summary": {
            "total": len(unreplied),
            "urgent": urgent,
            "warning": warning,
            "normal": normal,
        },
    }
    save_json("email-actions.json", result)


# ===== Calendar Transform =====
def transform_calendar():
    """gcal.py list 출력 → calendar-today.json + calendar-week.json"""
    cal_today_raw = load_json("_raw_cal_today.json")
    cal_week_raw = load_json("_raw_cal_week.json")

    if not cal_today_raw and not cal_week_raw:
        print("  ⚠ 캘린더 raw 데이터 없음 — 스킵")
        return

    # gcal.py 출력: [{"id": "...", "title": "...", "start": "ISO datetime", "end": "...", "location": "", "description": ""}, ...]

    # Today
    if isinstance(cal_today_raw, list):
        events = []
        for e in cal_today_raw:
            start_raw = e.get("start", "")
            end_raw = e.get("end", "")
            # ISO datetime → HH:MM 추출
            start_time = start_raw[11:16] if len(start_raw) > 16 else start_raw
            end_time = end_raw[11:16] if len(end_raw) > 16 else end_raw

            events.append({
                "id": e.get("id", ""),
                "title": e.get("title", "(제목 없음)"),
                "start": start_time,
                "end": end_time,
                "location": e.get("location", ""),
                "description": e.get("description", ""),
                "calendar_link": "https://calendar.google.com/",
            })

        events.sort(key=lambda x: x["start"])
        save_json("calendar-today.json", {
            "generated_at": now.isoformat(),
            "date": today_str,
            "events": events,
        })

    # Week
    all_week = cal_week_raw if isinstance(cal_week_raw, list) else []
    if isinstance(cal_today_raw, list):
        all_week = cal_today_raw + [e for e in all_week if e.get("start", "")[:10] != today_str]

    week_events = []
    for e in all_week:
        start_raw = e.get("start", "")
        event_date = start_raw[:10] if len(start_raw) >= 10 else ""
        start_time = start_raw[11:16] if len(start_raw) > 16 else None

        is_deadline = "마감" in e.get("title", "") or "deadline" in e.get("title", "").lower()

        week_events.append({
            "title": e.get("title", "(제목 없음)"),
            "date": event_date,
            "start": start_time,
            "is_deadline": is_deadline,
        })

    week_events.sort(key=lambda x: (x["date"], x["start"] or "99:99"))

    end_of_week = (now + timedelta(days=6)).strftime("%Y-%m-%d")
    save_json("calendar-week.json", {
        "generated_at": now.isoformat(),
        "week_range": f"{today_str} ~ {end_of_week}",
        "events": week_events,
    })


# ===== Main =====
if __name__ == "__main__":
    print(f"데이터 디렉토리: {DATA_DIR}")
    transform_emails()
    transform_calendar()
    print("  변환 완료")
