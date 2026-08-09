#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""아리사 봇 프로필 설정 — 이름·설명·커맨드 메뉴 (2026-08-09).

## 왜 필요한가
직원 봇의 표시 이름이 "업무보고 도우미"였다. 이름이 곧 역할 선언이라, 그 이름으로는
"물어봐도 되는 곳"이 되지 않는다. 아리사는 보고를 받기만 하는 창구가 아니다.

그리고 **커맨드 메뉴가 비어 있었다**(`getMyCommands` → []). 텔레그램은 등록된 커맨드를
입력창 옆 메뉴로 보여주는데, 비어 있으면 직원은 `/report`가 있는지도 모른다.
기능을 만들어도 발견되지 않으면 없는 것과 같다.

## 바꾸는 것 / 안 바꾸는 것
- 바꾼다: 표시 이름(`setMyName`), 설명 2종, 커맨드 메뉴
- **안 바꾼다: @username.** BotFather에서만 가능하고, 바꾸면 기존 공유 링크·QR이 깨진다.
  표시 이름만 바꿔도 직원 대화창에는 "아리사"로 보인다.

사용: python3 arisa-bot-profile.py [--dry] [--show]
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

WS = Path(__file__).resolve().parents[2]

# .env 로드 (다른 스크립트와 같은 방식 — 환경변수가 이미 있으면 덮지 않는다)
for envp in (WS / ".env", Path.home() / "arisa-project-memory" / ".env"):
    if envp.exists():
        for line in envp.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

TOKEN = os.environ.get("DAILY_REPORT_BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"

# ── 프로필 ────────────────────────────────────────────────
NAME = "아리사"

# 짧은 설명 — 프로필 카드와 검색 결과에 뜬다 (120자 제한)
SHORT_DESC = "프로젝트 렌트 업무 어시스턴트. 업무보고·내 할 일·프로젝트 현황·사내 규정을 도와드립니다."

# 긴 설명 — 대화를 처음 열었을 때 빈 화면에 뜬다 (512자 제한)
# 여기가 사실상 유일한 사용법 안내다. "무엇을 물어도 되는지"를 예시로 보여준다.
# ⚠️ **지금 실제로 되는 것만 적는다.** 안내문은 약속이다 — 못 지키면 신뢰가 먼저 깎인다.
#    규정 질의(policy_lookup)가 붙으면 그때 한 줄 추가한다.
DESCRIPTION = (
    "안녕하세요, 아리사입니다.\n\n"
    "그냥 말씀하시면 알아듣습니다.\n"
    "· 오늘 한 일을 쭉 적어주시면 → 업무보고로 정리해 드려요\n"
    "· \"내 할 일 알려줘\" → 남은 업무와 마감\n"
    "· \"봉은사 어떻게 돼가?\" → 프로젝트 현황\n"
    "· 회의 녹취를 붙여넣으면 → 회의록으로 정리\n"
    "· \"연차는 며칠 전에 신청해?\" → 사내 규정에서 원문 찾아 답변\n\n"
    "명령어를 외우지 않으셔도 됩니다."
)

# 커맨드 메뉴 — 입력창 옆 [/] 버튼에 뜬다
# ⚠️ **핸들러가 실제로 있는 것만 넣는다.** 메뉴에 있는데 눌러도 무반응인 것이
#    아예 없는 것보다 나쁘다. 봇의 핸들러는 `~filters.COMMAND`로 필터링되므로,
#    CommandHandler가 등록되지 않은 커맨드는 조용히 무시된다(오류 메시지조차 없다).
# ⚠️ /meeting 제외 — 현재 "Meeting Engine not available"로 비활성.
# 2026-08-09: /ask·/todo 핸들러 등록 완료(daily-report-bot.py cmd_ask·cmd_todo) → 메뉴 추가.
COMMANDS = [
    {"command": "report", "description": "업무보고 시작"},
    {"command": "todo", "description": "내 할 일·마감 보기"},
    {"command": "ask", "description": "사내 규정 물어보기"},
    {"command": "cancel", "description": "진행 중인 대화 취소"},
]


def call(method: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(f"{API}/{method}", data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"ok": False, "description": f"HTTP {e.code}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "description": str(e)}


def show() -> None:
    me = (call("getMe").get("result") or {})
    print(f"  이름      : {me.get('first_name')}")
    print(f"  주소      : @{me.get('username')}")
    print(f"  설명      : {(call('getMyDescription').get('result') or {}).get('description') or '(비어있음)'}")
    print(f"  짧은설명  : {(call('getMyShortDescription').get('result') or {}).get('short_description') or '(비어있음)'}")
    cmds = call("getMyCommands").get("result") or []
    print(f"  커맨드    : {len(cmds)}개" + ("" if cmds else "  ← 직원에게 메뉴가 안 보인다"))
    for c in cmds:
        print(f"              /{c['command']:<8} {c['description']}")


def main() -> int:
    if not TOKEN:
        print("DAILY_REPORT_BOT_TOKEN 이 없습니다 (.env 확인)", file=sys.stderr)
        return 1

    print("── 변경 전 ──")
    show()

    if "--show" in sys.argv:
        return 0

    if "--dry" in sys.argv:
        print(f"\n[dry] 이름 → {NAME}")
        print(f"[dry] 커맨드 {len(COMMANDS)}종 등록")
        print(f"[dry] 설명·짧은설명 설정")
        return 0

    print("\n── 적용 ──")
    steps = [
        ("setMyName", {"name": NAME}),
        ("setMyShortDescription", {"short_description": SHORT_DESC}),
        ("setMyDescription", {"description": DESCRIPTION}),
        ("setMyCommands", {"commands": COMMANDS}),
    ]
    failed = 0
    for method, payload in steps:
        r = call(method, payload)
        ok = r.get("ok")
        failed += (not ok)
        print(f"  {'✅' if ok else '❌'} {method}" + ("" if ok else f"  → {r.get('description')}"))

    print("\n── 변경 후 ──")
    show()
    if failed:
        print(f"\n⚠️ {failed}건 실패")
        return 1
    print("\n⚠️ 텔레그램 앱에서 실제로 렌더되는지 눈으로 확인할 것 (API 200 ≠ 화면 반영)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
