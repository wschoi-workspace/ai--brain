"""매장 마감보고 공용 로직 — basket-ops-bot·daily-report-bot 공유(SSOT).

정책(2026-07-29 대표 지시): 마감보고는 매장 담당자가 일일업무보고와 **별도로** 제출한다.
- 어느 봇으로 보내든 '매장마감' 탭에 매장 단위로 기록한다(개인 일일보고와 병합 금지 —
  과거엔 제출자의 일일보고 '업무보고' 칸에 우겨넣어져 매출이 매출 칸에 안 잡혔다).
- 마감보고는 일일업무보고 완료로 인정하지 않는다(체크인/리마인더 동일 기준).
"""
from __future__ import annotations
import os
from datetime import datetime

from . import gws as _gws
from . import report_queue as _rq

TAB = os.environ.get("BASKET_CLOSING_SHEET_TAB", "매장마감")


def sheet_id() -> str:
    """호출 시점에 읽는다 — 봇마다 .env 로딩과 import 순서가 달라 import 시점 고정은 위험."""
    return os.environ.get("BASKET_REPORT_SHEET_ID", "")

# 매장마감 탭 11열: 매장·날짜·담당자·제출자·방문객체감·일매출·음료·디저트·특이·원문·시각
FIELDS = [("store", "매장"), ("date", "영업일"), ("manager", "담당자"), ("visitors", "방문객 체감"),
          ("sales", "일 매출"), ("drinks", "음료"), ("desserts", "디저트"), ("notes", "특이사항")]

PROMPT = """너는 매장 일일 마감보고 정리 비서다.
운영자가 전달한 매장 마감보고(담당자·일 매출·판매 상세 포함)를 아래 JSON 스키마로 구조화한다.
규칙: 보고에 적힌 내용만 담는다(지어내지 않음). 없으면 빈 문자열. 원문 표현을 최대한 보존한다.
'clarify'에는 꼭 되물어야 할 핵심 질문만 0~2개 담는다. 매장명이 보고에 없으면 반드시
"어느 매장 마감보고인가요? (리진/바스켓/아랑재 등)"을 clarify에 넣는다.

스키마:
{
 "store": "매장명(리진/바스켓/아랑재/올드타운/여수 등, 명시 없으면 빈 문자열)",
 "date": "보고에 적힌 영업일(YYMMDD 6자리, 없으면 빈 문자열)",
 "manager": "담당자 이름",
 "visitors": "방문객 체감 수준",
 "sales": "일 매출(숫자+원)",
 "drinks": "음료 판매(잔수·품목별 상세)",
 "desserts": "디저트 판매(개수·품목별 상세)",
 "notes": "특이사항",
 "clarify": ["되물을 질문1", "되물을 질문2"]
}
JSON만 출력."""


def is_closing_report(text: str) -> bool:
    """매장 마감보고 감지 — 담당자+일 매출 패턴 또는 '마감보고' 명시."""
    t = (text or "").replace(" ", "")
    return ("마감보고" in t) or ("담당자" in t and "일매출" in t)


def build_row(d: dict, submitter: str) -> list:
    """구조화 결과 → 매장마감 탭 1행. date가 YYMMDD가 아니면 오늘 날짜."""
    now = datetime.now()
    date_ = (d.get("date") or "").strip()
    if not (len(date_) == 6 and date_.isdigit()):
        date_ = now.strftime("%y%m%d")
    return [
        d.get("store", ""), date_, d.get("manager", ""), submitter,
        d.get("visitors", ""), d.get("sales", ""), d.get("drinks", ""), d.get("desserts", ""),
        d.get("notes", ""), (d.get("_raw") or d.get("raw") or "").strip(), now.strftime("%H:%M"),
    ]


def append_row(row: list) -> bool:
    """매장마감 탭 append + 실패 시 로컬 큐 보관(백필 배치가 자동 재시도). 유실 방지 단일 경로."""
    sid = sheet_id()
    ok, kind = _gws.append_to_sheet_ex(sid, f"{TAB}!A1", row,
                                       value_input_option="USER_ENTERED", timeout=20)
    if not ok:
        key = f"{datetime.now().strftime('%Y-%m-%d')}|closing|{row[0]}|{row[2]}"
        _rq.enqueue([_rq.make_entry("basket", sid, f"{TAB}!A1", row, key,
                                    [1, 2, 10], vio="USER_ENTERED", last_error=kind)])
    return ok


def push_lines(d: dict, submitter: str) -> list[str]:
    """대표 푸시용 요약 라인(플레인 텍스트 — 발신 봇이 포맷을 입힌다)."""
    store = (d.get("store") or "매장?").strip() or "매장?"
    head = f"🏪 {store} 마감보고 {(d.get('date') or datetime.now().strftime('%y%m%d'))}"
    if (d.get("manager") or "").strip():
        head += f" · 담당 {d['manager'].strip()}"
    L = [head]
    if (d.get("sales") or "").strip():
        L.append("💰 일매출 " + d["sales"].strip())
    if (d.get("visitors") or "").strip():
        L.append("👥 방문객 " + d["visitors"].strip())
    if (d.get("drinks") or "").strip():
        L.append("☕ " + d["drinks"].strip()[:200])
    if (d.get("desserts") or "").strip():
        L.append("🍰 " + d["desserts"].strip()[:200])
    if (d.get("notes") or "").strip():
        L.append("📍 " + d["notes"].strip()[:180])
    L.append(f"(제출: {submitter})")
    return L
