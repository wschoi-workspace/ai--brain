#!/usr/bin/env python3
"""ARISA OS 사용 가이드 링크 리더 3인 발송 (대표 직접 실행용).
실행: python3 20-operations/23-arisa/send-guide-notice.py
"""
import json
import urllib.request
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
token = ""
for line in (WS / ".env").read_text(encoding="utf-8").splitlines():
    if line.startswith("DAILY_REPORT_BOT_TOKEN="):
        token = line.split("=", 1)[1].strip()
assert token, ".env에서 DAILY_REPORT_BOT_TOKEN을 찾지 못했습니다"

MSG = """📖 ARISA OS 사용 가이드가 준비됐습니다

🔗 https://arisa-os.com/guide-os

담긴 내용:
· 로그인·PIN 변경 방법
· 역할별 화면 안내 (팀 홈 / 오늘 Brief / 이번 주)
· 업무분장 사용법 — 자유 텍스트 AI 정리 + 주간업무계획 엑셀 업로드 (템플릿 다운로드 포함)
· 받은 업무 → 팀원에게 상세 분장하는 법
· 일일보고가 브리프에 자동 반영되는 구조
· FAQ

대시보드 우상단 '가이드' 링크로도 언제든 열 수 있습니다.
팀원들에게도 이 링크를 공유해 주세요."""

for name, cid in [("전제훈", 8714627048), ("배성원", 921741497), ("윤혜정", 8452510149)]:
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": cid, "text": MSG}).encode(),
        headers={"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=20).read())
    print(name, "→", "✅ 발송" if d.get("ok") else f"❌ 실패: {d}")
