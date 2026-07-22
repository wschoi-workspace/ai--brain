#!/usr/bin/env python3
"""ARISA OS 전직원 오픈 공지 — 텔레그램 연결된 전 직원에게 발송 (직원봇).

실행:
  python3 20-operations/23-arisa/send-os-launch-notice.py --test        # 최원석에게만 테스트 발송
  python3 20-operations/23-arisa/send-os-launch-notice.py --to 배성원    # 특정 인원만 발송
  python3 20-operations/23-arisa/send-os-launch-notice.py               # 전 직원 발송
"""
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
token = ""
for line in (WS / ".env").read_text(encoding="utf-8").splitlines():
    if line.startswith("DAILY_REPORT_BOT_TOKEN="):
        token = line.split("=", 1)[1].strip()
assert token, ".env에서 DAILY_REPORT_BOT_TOKEN을 찾지 못했습니다"

MSG = """🎉 아리사 OS가 오늘부터 전 직원에게 오픈됩니다

■ 아리사 OS가 뭔가요?
프로젝트 렌트의 업무 운영 시스템입니다.
우리 회사의 업무분장·일일보고·프로젝트 일정이 한곳에 모이고,
각자의 보고가 다음날 아침 브리프와 프로젝트 현황에 자동으로 반영됩니다.

■ 왜 함께 써야 하나요?
지시와 보고가 카톡·구두로 흩어지면 놓치는 일이 생깁니다.
아리사 OS에서는
· 내가 맡은 업무와 마감이 항상 한 화면에 정리되고
· 내 보고가 리더·대표에게 자동으로 전달·집계되며
· 같은 내용을 두 번 보고하거나 다시 물어볼 일이 줄어듭니다.
전원이 함께 써야 전체 그림이 돌아가는 시스템입니다.

🔗 https://arisa-os.com
로그인: 본인 이름(한글) + PIN (이미 안내받은 번호 그대로 / 분실 시 대표에게 재발급 요청)

📌 역할별로 보이는 화면이 다릅니다
· 대표 — 전사 전체 (브리프·주간·결재/지연 집계)
· 파트 리더 — 담당 파트 전체 (팀 홈·팀 브리프·팀 주간)
· 팀원 — 내 담당 업무와 일정 (내 업무·내 브리프)

🆕 문서 시뮬레이터 — 전 직원 사용 가능
· 일일보고 / 기획안: 쓰기 전에 AI 리뷰(100점 채점 + 개선 팁)
· 회의분석: 회의 전사나 회의록 파일(.txt·.docx·.html)을 올리면
  AI가 실행 중심 회의록(써머리·결정·할 일)으로 정리 → PDF·워드로 바로 저장

📖 사용 가이드: https://arisa-os.com/guide-os
(로그인 후 우측 상단 '가이드'로도 열 수 있습니다)

💬 궁금한 점, 건의, 업무 요청사항은
지금 이 채팅(일일업무 보고봇)에 바로 남겨주세요.
자동 접수되어 확인 후 회신드립니다."""


def send(chat_id, text):
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("ok")


def main():
    test = "--test" in sys.argv
    only = sys.argv[sys.argv.index("--to") + 1] if "--to" in sys.argv else None
    skip = set((sys.argv[sys.argv.index("--skip") + 1] if "--skip" in sys.argv else "").split(",")) - {""}
    emp = json.loads((WS / "00-system" / "02-scripts" / "arisa-employees.json").read_text(encoding="utf-8"))
    targets = []
    for tg_id, info in emp.get("by_telegram_id", {}).items():
        name = info.get("name") if isinstance(info, dict) else str(info)
        if test and name != "최원석":
            continue
        if only and name != only:
            continue
        if name in skip:
            continue
        targets.append((name, tg_id))
    print(f"발송 대상 {len(targets)}명: {', '.join(n for n, _ in targets)}")
    ok = fail = 0
    for name, tg_id in targets:
        try:
            if send(tg_id, MSG):
                ok += 1
                print(f"  ✓ {name}")
            else:
                fail += 1
                print(f"  ✗ {name} (API 거절)")
        except Exception as e:
            fail += 1
            print(f"  ✗ {name} ({e})")
        time.sleep(0.5)
    print(f"완료 — 성공 {ok} / 실패 {fail}")


if __name__ == "__main__":
    main()
