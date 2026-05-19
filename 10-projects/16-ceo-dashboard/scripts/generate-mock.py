#!/usr/bin/env python3
"""CEO Dashboard 개발용 샘플 데이터 생성"""

import json
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

now = datetime.now()
today = now.strftime("%Y-%m-%d")


def write_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {filename}")


# === 1. email-actions.json ===
email_actions = {
    "generated_at": now.isoformat(),
    "recent_emails": [
        {"id": "msg001", "from": "김대리 <kim@partner.co.kr>", "subject": "3월 정산 확인 요청", "date": (now - timedelta(hours=6)).isoformat(), "hours_ago": 6, "replied": False, "gmail_link": "https://mail.google.com/mail/u/0/#inbox/msg001"},
        {"id": "msg002", "from": "서울디자인재단 <info@sdf.or.kr>", "subject": "2026 상반기 입주 신청 안내", "date": (now - timedelta(hours=18)).isoformat(), "hours_ago": 18, "replied": False, "gmail_link": "https://mail.google.com/mail/u/0/#inbox/msg002"},
        {"id": "msg003", "from": "이과장 <lee@vendor.com>", "subject": "매장 인테리어 견적서 송부", "date": (now - timedelta(hours=30)).isoformat(), "hours_ago": 30, "replied": False, "gmail_link": "https://mail.google.com/mail/u/0/#inbox/msg003"},
        {"id": "msg004", "from": "박팀장 <park@building.co.kr>", "subject": "4월 임대차 계약 갱신 관련", "date": (now - timedelta(hours=52)).isoformat(), "hours_ago": 52, "replied": False, "gmail_link": "https://mail.google.com/mail/u/0/#inbox/msg004"},
        {"id": "msg005", "from": "정세무사 <jung@tax.kr>", "subject": "1분기 부가세 신고 자료 요청", "date": (now - timedelta(hours=55)).isoformat(), "hours_ago": 55, "replied": False, "gmail_link": "https://mail.google.com/mail/u/0/#inbox/msg005"},
        {"id": "msg006", "from": "최디자이너 <choi@design.co>", "subject": "브랜딩 시안 3종 전달", "date": (now - timedelta(hours=10)).isoformat(), "hours_ago": 10, "replied": True, "gmail_link": "https://mail.google.com/mail/u/0/#inbox/msg006"},
        {"id": "msg007", "from": "한매니저 <han@store.com>", "subject": "성수점 3월 실적 보고", "date": (now - timedelta(hours=26)).isoformat(), "hours_ago": 26, "replied": True, "gmail_link": "https://mail.google.com/mail/u/0/#inbox/msg007"},
        {"id": "msg008", "from": "GS리테일 <gs@retail.co.kr>", "subject": "입점 제안서 검토 요청", "date": (now - timedelta(hours=4)).isoformat(), "hours_ago": 4, "replied": False, "gmail_link": "https://mail.google.com/mail/u/0/#inbox/msg008"},
    ],
    "unreplied_summary": {"total": 6, "urgent": 2, "warning": 1, "normal": 3}
}
write_json("email-actions.json", email_actions)


# === 2. regular-tasks.json ===
regular_tasks = {
    "generated_at": now.isoformat(),
    "tasks": [
        {"name": "임대료 송금 (성수점)", "cycle": "매월", "day": 25, "amount": 3500000, "next_date": f"{now.strftime('%Y-%m')}-25", "note": "우리은행 자동이체 확인"},
        {"name": "임대료 송금 (북촌점)", "cycle": "매월", "day": 25, "amount": 4200000, "next_date": f"{now.strftime('%Y-%m')}-25", "note": "신한은행 수동 송금"},
        {"name": "부가세 예정신고", "cycle": "매분기", "day": 25, "amount": None, "next_date": "2026-04-25", "note": "정세무사 사무실 연락"},
        {"name": "직원 급여 이체", "cycle": "매월", "day": 10, "amount": None, "next_date": f"{now.strftime('%Y-%m')}-10", "note": ""},
        {"name": "4대보험료 납부", "cycle": "매월", "day": 10, "amount": None, "next_date": f"{now.strftime('%Y-%m')}-10", "note": "자동이체"},
        {"name": "매장 소방점검", "cycle": "매분기", "day": 15, "amount": 150000, "next_date": "2026-06-15", "note": "성수점+북촌점 동시"},
    ]
}
write_json("regular-tasks.json", regular_tasks)


# === 3. calendar-today.json ===
calendar_today = {
    "generated_at": now.isoformat(),
    "date": today,
    "events": [
        {"id": "evt1", "title": "주간회의", "start": "10:00", "end": "11:00", "location": "사무실", "description": "프로젝트 진행상황 공유", "calendar_link": "https://calendar.google.com/"},
        {"id": "evt2", "title": "성수점 매니저 미팅", "start": "14:00", "end": "15:00", "location": "성수점", "description": "3월 실적 리뷰 + 4월 프로모션 논의", "calendar_link": "https://calendar.google.com/"},
        {"id": "evt3", "title": "디자인 시안 리뷰", "start": "16:00", "end": "16:30", "location": "Zoom", "description": "브랜딩 시안 3종 최종 선정", "calendar_link": "https://calendar.google.com/"},
    ]
}
write_json("calendar-today.json", calendar_today)


# === 4. calendar-week.json ===
def future_date(days):
    return (now + timedelta(days=days)).strftime("%Y-%m-%d")

calendar_week = {
    "generated_at": now.isoformat(),
    "week_range": f"{today} ~ {future_date(6)}",
    "events": [
        {"title": "주간회의", "date": today, "start": "10:00", "is_deadline": False},
        {"title": "성수점 매니저 미팅", "date": today, "start": "14:00", "is_deadline": False},
        {"title": "디자인 시안 리뷰", "date": today, "start": "16:00", "is_deadline": False},
        {"title": "북촌점 현장 점검", "date": future_date(1), "start": "11:00", "is_deadline": False},
        {"title": "GS리테일 입점 미팅", "date": future_date(2), "start": "15:00", "is_deadline": False},
        {"title": "마감: 제안서 제출", "date": future_date(2), "start": None, "is_deadline": True},
        {"title": "세무사 상담", "date": future_date(3), "start": "10:00", "is_deadline": False},
        {"title": "마감: 4월 프로모션 확정", "date": future_date(5), "start": None, "is_deadline": True},
    ]
}
write_json("calendar-week.json", calendar_week)


# === 5. pos-sales.json ===
pos_sales = {
    "generated_at": now.isoformat(),
    "source_file": "pos-daily-20260411.xlsx",
    "stores": [
        {
            "name": "성수점",
            "yesterday": 2450000,
            "same_day_last_week": 2100000,
            "same_day_last_month": 2300000,
            "change_vs_last_week": 16.7,
            "change_vs_last_month": 6.5,
            "customers": 82,
            "avg_per_customer": 29878,
            "monthly_target": 70000000,
            "monthly_actual": 38500000,
            "daily_trend": [2100000, 2350000, 1980000, 2450000, 2200000, 2550000, 2450000],
            "voc_count": 2,
            "voc_unresolved": 1,
            "inventory_alerts": ["오리지널 커피포 10T — 재고 2일분"],
            "issues": "해외결제 POS 오류 1건",
            "work_requests": [
                {"content": "에어컨 필터 교체 요청", "urgency": "중", "status": "대기", "date": "2026-04-11"},
                {"content": "간판 조명 점멸 수리", "urgency": "상", "status": "진행", "date": "2026-04-10"}
            ]
        },
        {
            "name": "북촌점",
            "yesterday": 1750000,
            "same_day_last_week": 2200000,
            "same_day_last_month": 1900000,
            "change_vs_last_week": -20.5,
            "change_vs_last_month": -7.9,
            "customers": 58,
            "avg_per_customer": 30172,
            "monthly_target": 60000000,
            "monthly_actual": 29500000,
            "daily_trend": [2200000, 1900000, 2050000, 1800000, 1750000, 2100000, 1750000],
            "voc_count": 0,
            "voc_unresolved": 0,
            "inventory_alerts": [],
            "issues": "",
            "work_requests": [
                {"content": "화장실 수전 교체", "urgency": "하", "status": "완료", "date": "2026-04-08"}
            ]
        }
    ],
    "total": {
        "yesterday": 4200000,
        "monthly_target": 130000000,
        "monthly_actual": 68000000,
        "achievement_rate": 52.3
    }
}
write_json("pos-sales.json", pos_sales)

# === 6. projects.json ===
projects = {
    "generated_at": now.isoformat(),
    "source_file": "주간회의자료-20260411.xlsx",
    "projects": [
        {
            "name": "성수점 리뉴얼",
            "progress": 65,
            "total_budget": 120000000,
            "spent": 58000000,
            "spend_rate": 48.3,
            "next_milestone": "인테리어 시공 착수",
            "milestone_date": "2026-04-20",
            "today_topics": "시공업체 최종 선정, 임시 영업 일정 조율",
        },
        {
            "name": "북촌점 브랜딩",
            "progress": 30,
            "total_budget": 25000000,
            "spent": 12000000,
            "spend_rate": 48.0,
            "next_milestone": "디자인 시안 확정",
            "milestone_date": "2026-04-15",
            "today_topics": "시안 3종 최종 리뷰",
        },
        {
            "name": "GS리테일 입점",
            "progress": 15,
            "total_budget": 50000000,
            "spent": 18000000,
            "spend_rate": 36.0,
            "next_milestone": "제안서 제출",
            "milestone_date": "2026-04-14",
            "today_topics": "",
        },
        {
            "name": "온라인 스토어 구축",
            "progress": 80,
            "total_budget": 30000000,
            "spent": 32000000,
            "spend_rate": 106.7,
            "next_milestone": "베타 테스트",
            "milestone_date": "2026-04-25",
            "today_topics": "결제 모듈 테스트 결과 공유",
        },
    ]
}
write_json("projects.json", projects)


# === 7. attendance.json ===
attendance = {
    "generated_at": now.isoformat(),
    "source_file": "근태현황-202604.xlsx",
    "month": "2026-04",
    "budget": {"overtime_budget": 3000000, "used": 2150000, "usage_rate": 71.7},
    "employees": [
        {"name": "한매니저", "store": "성수점", "overtime_hours": 12, "night_hours": 4, "holiday_hours": 8, "total_extra_hours": 24, "estimated_pay": 480000, "total_leave": 15, "used_leave": 8, "remaining_leave": 7},
        {"name": "김부점장", "store": "성수점", "overtime_hours": 8, "night_hours": 6, "holiday_hours": 4, "total_extra_hours": 18, "estimated_pay": 360000, "total_leave": 15, "used_leave": 12, "remaining_leave": 3},
        {"name": "박매니저", "store": "북촌점", "overtime_hours": 15, "night_hours": 8, "holiday_hours": 6, "total_extra_hours": 29, "estimated_pay": 580000, "total_leave": 15, "used_leave": 5, "remaining_leave": 10},
        {"name": "이스태프", "store": "북촌점", "overtime_hours": 6, "night_hours": 2, "holiday_hours": 0, "total_extra_hours": 8, "estimated_pay": 160000, "total_leave": 11, "used_leave": 4, "remaining_leave": 7},
        {"name": "최인턴", "store": "사무실", "overtime_hours": 20, "night_hours": 10, "holiday_hours": 4, "total_extra_hours": 34, "estimated_pay": 570000, "total_leave": 11, "used_leave": 9, "remaining_leave": 2},
    ],
    "store_labor_ratio": [
        {"store": "성수점", "monthly_sales": 38500000, "labor_cost": 840000, "ratio": 2.2},
        {"store": "북촌점", "monthly_sales": 29500000, "labor_cost": 740000, "ratio": 2.5},
    ]
}
write_json("attendance.json", attendance)


print(f"\n모든 샘플 데이터 생성 완료 → {DATA_DIR}")
