"""ARISA Assistant 툴 레이어 — 봇이 조직 데이터에 닿는 유일한 경로.

툴 카탈로그 v1(`20-operations/23-arisa/assistant-tool-catalog-v1.md`)의 실행부.

## 왜 이 파일이 필요한가
봇이 시트·JSON을 직접 읽고 쓰면 권한 필터(can_view)·상태 전이 게이트(check_transition)·
이력(status_log)·낙관적 잠금이 전부 우회된다. 그러면 화면과 봇에 서로 다른 진실이 생긴다.
**모든 접근은 dashboard-server HTTP API를 지난다.** 이 파일은 그 규칙을 코드로 강제한다.

## 신원
`X-Arisa-On-Behalf-Tg`에 **텔레그램 user_id**를 넣는다(이름이 아니다).
서버가 arisa-employees.json:by_telegram_id로 이름을 도출하고, 그 이름의 권한을 적용한다.
LLM이 만든 문자열이 신원이 되는 경로를 아예 만들지 않기 위한 설계다.

## Phase 1 범위 (2026-08-03)
읽기 5종 + 조직 상태를 바꾸지 않는 AI 보조 1종. 쓰기는 라우터 오분류율을 본 뒤 개방한다.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

DEFAULT_BASE = os.environ.get("ARISA_API_BASE") or "http://127.0.0.1:8780"
_TIMEOUT = 20


class ToolError(Exception):
    """툴 호출 실패. status는 HTTP 코드(연결 실패 시 0)."""

    def __init__(self, message: str, status: int = 0, payload: dict | None = None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}

    @property
    def user_message(self) -> str:
        """사용자에게 그대로 보여줄 수 있는 문장."""
        if self.status == 403:
            return str(self) or "권한이 없습니다."
        if self.status == 404:
            return str(self) or "찾을 수 없습니다."
        if self.status == 409:
            # 낙관적 잠금 — 재시도하면 남의 변경을 덮는다. 반드시 사람에게 되묻는다.
            return "그 사이 다른 분이 내용을 바꿨습니다. 다시 확인하고 알려주세요."
        if self.status == 401:
            return "아리사 계정을 찾지 못했습니다. 관리자에게 문의해주세요."
        return str(self) or "요청을 처리하지 못했습니다."


class AssistantTools:
    """한 사용자(텔레그램 ID) 기준의 툴 호출기.

    사용자마다 인스턴스를 만든다 — 신원이 인스턴스에 묶여 있어야 다른 사람의 요청에
    섞이지 않는다. 전역 싱글턴으로 쓰고 매번 신원을 인자로 넘기는 구조는 금지.
    """

    def __init__(self, telegram_id, name: str = "", base_url: str = "", secret: str = ""):
        self.telegram_id = str(telegram_id)
        self.name = name or ""
        self.base = (base_url or DEFAULT_BASE).rstrip("/")
        self.secret = secret or (os.environ.get("ARISA_ASSISTANT_SECRET") or "").strip()

    # ── 하부 ──────────────────────────────────────────────
    @property
    def enabled(self) -> bool:
        return bool(self.secret)

    def _headers(self) -> dict:
        return {"X-Arisa-Service": self.secret,
                "X-Arisa-On-Behalf-Tg": self.telegram_id,
                "Content-Type": "application/json"}

    def _call(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        if not self.enabled:
            raise ToolError("Assistant 서비스 토큰이 설정되지 않았습니다(.env ARISA_ASSISTANT_SECRET).")
        url = self.base + path
        if params:
            clean = {k: v for k, v in params.items() if v not in (None, "")}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
                return json.loads(r.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode("utf-8") or "{}")
            except Exception:
                payload = {}
            msg = payload.get("error") or f"HTTP {e.code}"
            logger.warning("tool %s %s → %s %s", method, path, e.code, msg)
            raise ToolError(msg, e.code, payload) from None
        except Exception as e:
            logger.error("tool %s %s 연결 실패: %s", method, path, e)
            raise ToolError("아리사 서버에 연결하지 못했습니다.", 0) from None

    def _get(self, path, **params):
        # ?user= 는 서버의 신원 강제(스푸핑 방지)를 통과해야 하므로 항상 본인 이름을 넣는다
        params.setdefault("user", self.name)
        return self._call("GET", path, params=params)

    # ── R1: 내 일 ─────────────────────────────────────────
    def my_work(self) -> dict:
        """내 미완 분장 + 프로젝트 태스크 + 승인·결정 큐 + 오늘 계획 + 개인 브리프."""
        return self._get("/api/my-work")

    # ── R2/R3: 프로젝트 ───────────────────────────────────
    def project_list(self) -> dict:
        """열람 가능한 프로젝트 목록 + 진행률 롤업."""
        return self._get("/api/projects")

    def project_detail(self, pid: str) -> dict:
        """프로젝트 전문 + 연결 분장 + 회의별 실행률."""
        if not pid:
            raise ToolError("프로젝트를 지정해주세요.", 400)
        return self._get("/api/project", id=pid)

    # ── R4: 회의록 ────────────────────────────────────────
    def meeting_doc(self, pid: str, ts: str) -> dict:
        """회의록 원문. ts는 YYYYMMDD-HHMMSS."""
        if not pid or not ts:
            raise ToolError("프로젝트와 회의 시각이 필요합니다.", 400)
        return self._get("/api/project/doc", id=pid, ts=ts)

    # ── R12: 브리프 (2026-08-03 신설 API) ─────────────────
    def daily_brief(self, scope: str = "person", date: str = "", team: str = "") -> dict:
        """브리프 본문. scope=exec(대표)|team(팀)|person(개인). 기본은 본인 것."""
        if scope not in ("exec", "team", "person"):
            raise ToolError("scope는 exec·team·person 중 하나입니다.", 400)
        return self._get("/api/brief", scope=scope, date=date, team=team)

    # ── AI 보조: 조직 상태를 바꾸지 않는 유일한 생성 툴 ──────
    def meeting_summarize(self, text: str, title: str = "", date: str = "") -> dict:
        """전사 텍스트 → 5블록 미팅록. 아무것도 저장하지 않는다(R4 엔진 재사용).

        ⚠️ 서버 파라미터명은 `transcript`다(`text`가 아니다). 응답은 {"ok", "result": {...5블록}}.
        """
        text = (text or "").strip()
        if not text:
            raise ToolError("요약할 내용이 없습니다.", 400)
        if len(text) > 60000:
            raise ToolError("내용이 너무 깁니다(6만자 초과). 나눠서 보내주세요.", 400)
        return self._call("POST", "/api/simulator/meeting-summary",
                          body={"transcript": text, "title": title, "date": date})


# ── LLM 함수호출용 스펙 ────────────────────────────────────
# 라우터가 규칙으로 못 가르면 이 스펙을 LLM에 넘겨 툴을 고르게 한다.
# **쓰기 툴은 여기 없다** — Phase 1은 읽기 전용이다.
TOOL_SPECS = [
    {"name": "my_work",
     "description": "요청자 본인의 할 일·미완 업무·오늘 계획·승인 대기를 가져온다. "
                    "'오늘 뭐 하지', '내 할 일', '나 뭐 남았어' 같은 질문.",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "project_list",
     "description": "볼 수 있는 프로젝트 목록과 진행률. '무슨 프로젝트 돌아가?', '프로젝트 현황'.",
     "parameters": {"type": "object", "properties": {}}},
    {"name": "project_detail",
     "description": "특정 프로젝트의 상세(담당·진행률·연결 업무·회의 실행률). 프로젝트 이름이 나오면 이것.",
     "parameters": {"type": "object",
                    "properties": {"pid": {"type": "string", "description": "프로젝트 ID 또는 이름"}},
                    "required": ["pid"]}},
    {"name": "meeting_doc",
     "description": "특정 회의의 회의록 원문.",
     "parameters": {"type": "object",
                    "properties": {"pid": {"type": "string"},
                                   "ts": {"type": "string", "description": "YYYYMMDD-HHMMSS"}},
                    "required": ["pid", "ts"]}},
    {"name": "daily_brief",
     "description": "일일 브리프 본문. 본인 것이 기본, 리더는 팀, 대표는 전사.",
     "parameters": {"type": "object",
                    "properties": {"scope": {"type": "string", "enum": ["exec", "team", "person"]},
                                   "date": {"type": "string", "description": "YYYY-MM-DD, 생략 시 최신"},
                                   "team": {"type": "string"}}}},
    {"name": "meeting_summarize",
     "description": "붙여넣은 회의 전사·긴 텍스트를 회의 요약으로 정리한다. 저장하지 않는다.",
     "parameters": {"type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"]}},
]

TOOL_NAMES = {s["name"] for s in TOOL_SPECS}


def call_tool(tools: AssistantTools, name: str, args: dict | None = None):
    """이름 + 인자로 툴 실행. 스펙에 없는 이름은 거부한다(LLM 환각 차단)."""
    if name not in TOOL_NAMES:
        raise ToolError(f"알 수 없는 기능입니다: {name}", 400)
    fn = getattr(tools, name, None)
    if not callable(fn):
        raise ToolError(f"구현되지 않은 기능입니다: {name}", 500)
    return fn(**(args or {}))
