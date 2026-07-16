#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""프로젝트 포트폴리오 대시보드 — 공유 서버 (표준 라이브러리만).
화면(포트폴리오_대시보드.html)과 JSON API를 한 서버에서 서빙한다.
PM이 수정하면 서버에 저장되어 대표·팀원 모두 같은 데이터를 본다.

데이터: 00-system/01-templates/_data/  (users.json + projects/{id}.json)
권한:   대표=전체 열람·수정·생성·삭제 / PM=본인 프로젝트 수정 / 직원=배정 프로젝트 열람
실행:   python3 dashboard-server.py [port]   (기본 8770, 127.0.0.1 — Tailscale serve로 노출)
"""
import json, os, re, threading, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from pathlib import Path

# .env 로드(WEEKLY_KEY 등 — 환경 미설정 시 do-better-workspace/.env에서 보충)
_WS = Path(__file__).resolve().parent.parent.parent
for _envp in (_WS / ".env",):
    if _envp.exists():
        for _l in _envp.read_text(encoding="utf-8").splitlines():
            _l = _l.strip()
            if _l and not _l.startswith("#") and "=" in _l:
                _k, _, _v = _l.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

# 이관 가능: 경로는 스크립트 기준(상대) + 환경변수로 덮어쓰기 가능
BASE = Path(os.environ.get("DASHBOARD_BASE") or (Path(__file__).resolve().parent.parent / "01-templates"))
HTML = BASE / "포트폴리오_대시보드.html"
DATA = Path(os.environ.get("DASHBOARD_DATA") or (BASE / "_data"))
PROJ_DIR = DATA / "projects"
HOST = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("DASHBOARD_PORT", "8770"))
# ARISA 주간 대시보드 서빙 — /weekly. 성장지표는 대표 토큰(?key=WEEKLY_KEY)일 때만 노출.
WEEKLY_DIR = Path(os.environ.get("WEEKLY_DIR") or (_WS / "20-operations" / "23-arisa" / "weekly"))
WEEKLY_KEY = os.environ.get("WEEKLY_KEY", "")
# ARISA 대표 Daily Brief — /brief. HTML 내장 로그인이 대표(admin)만 입장시킴.
BRIEF_DIR = Path(os.environ.get("BRIEF_DIR") or (_WS / "20-operations" / "23-arisa" / "brief"))
# 팀 리더 판정 출처 — arisa-employees.json의 team_leads(팀→리더이름) 역매핑.
EMP_PATH = Path(__file__).resolve().parent / "arisa-employees.json"
# ARISA 2.0 리버스 프록시 — /arisa2/* → localhost:ARISA2_PORT
ARISA2_PORT = int(os.environ.get("ARISA2_PORT", "8787"))
ARISA2_UPSTREAM = f"http://127.0.0.1:{ARISA2_PORT}"
_lock = threading.Lock()

# ── 주간분장 시트 연동 (개인 대시보드 — 업무분장 입력/조회) ──
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from shared import gws as _asgws
except Exception:
    _asgws = None
try:
    from shared.decision import load_open_decisions as _load_open_decisions
except Exception:
    _load_open_decisions = None
DAILY_SHEET = os.environ.get("DAILY_REPORT_SHEET_ID", "")
ASSIGN_TAB = "주간분장"


def _week_label(d=None):
    d = d or datetime.date.today()
    return f"W{d.isocalendar().week:02d}"


def _assign_read():
    """주간분장 탭 → dict 리스트. 탭 없거나 gws 실패 시 [] (안전 — 개인탭이 죽지 않게)."""
    if not (_asgws and DAILY_SHEET):
        return []
    try:
        rows = _asgws.values_get(DAILY_SHEET, f"{ASSIGN_TAB}!A2:J5000", retries=2, timeout=20)
    except Exception:
        return []
    out = []
    for i, r in enumerate(rows):
        r = list(r) + [""] * (10 - len(r))
        # 시트 헤더: 날짜·프로젝트명·팀구분·담당자·업무내용·일정(완료예상)·결과물·상태·이해관계자·우선순위
        out.append({"row": i + 2,  # 시트 실제 행 번호 (A2부터) — 상태 업데이트용
                    "date": (r[0] or "").strip(), "project": (r[1] or "").strip(),
                    "team": (r[2] or "").strip(), "assignee": (r[3] or "").strip(),
                    "task": (r[4] or "").strip(), "deadline": (r[5] or "").strip(),
                    "result": (r[6] or "").strip(), "status": (r[7] or "미착수").strip(),
                    "stakeholder": (r[8] or "").strip(), "priority": (r[9] or "일반").strip()})
    return out


def _assign_append(assignee, task, deadline, priority, by, project="", result="", stakeholder=""):
    """주간분장 append. 사용자 헤더 순서: 날짜·프로젝트명·팀·담당자·업무내용·일정·결과물·상태·이해관계자·우선순위."""
    if not (_asgws and DAILY_SHEET):
        return False, "시트 미설정"
    team = emp_team(assignee) or ""
    row = [datetime.date.today().isoformat(), project, team, assignee, task, deadline,
           result, "미착수", stakeholder, priority]
    try:
        ok = _asgws.append_to_sheet(DAILY_SHEET, f"{ASSIGN_TAB}!A1", row, timeout=20)
        return bool(ok), "" if ok else "주간분장 탭 없음/append 실패"
    except Exception as e:
        return False, str(e)[:80]


OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def _call_llm_json(system_prompt, user_msg):
    """LLM API 호출 → JSON 파싱. Anthropic 우선, OpenAI fallback. 실패 시 None."""
    def _parse_json(text):
        m = re.search(r"```json\s*([\s\S]*?)```", text)
        return json.loads(m.group(1) if m else text)
    # 1) Anthropic
    if ANTHROPIC_KEY:
        try:
            payload = json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 2000, "temperature": 0.3,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_msg}]
            }).encode("utf-8")
            req = Request("https://api.anthropic.com/v1/messages", data=payload, headers={
                "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }, method="POST")
            with urlopen(req, timeout=60) as r:
                d = json.loads(r.read())
            return _parse_json(d["content"][0]["text"])
        except Exception:
            pass  # fallback to OpenAI
    # 2) OpenAI fallback
    if OPENAI_KEY:
        try:
            payload = json.dumps({
                "model": "gpt-4o", "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ]
            }).encode("utf-8")
            req = Request("https://api.openai.com/v1/chat/completions", data=payload,
                          headers={"Authorization": "Bearer " + OPENAI_KEY,
                                   "Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=60) as r:
                d = json.loads(r.read())
            return _parse_json(d["choices"][0]["message"]["content"])
        except Exception:
            pass
    return None


# 하위 호환: 기존 _call_claude 호출부 유지
_call_claude = _call_llm_json


# 주간업무계획.xlsx 파싱 폴백용 파이썬 (시스템 3.9에 openpyxl 없을 때 subprocess)
_XLSX_PY_CANDIDATES = [
    str(_WS / "20-operations" / "24-second-brain" / ".venv311" / "bin" / "python"),
    "/usr/bin/python3",
]

_PLAN_PARSE_SNIPPET = r'''
import json, sys
import openpyxl
rows = []
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
for ws in wb.worksheets:
    hdr = None
    last_proj = ""
    for r in ws.iter_rows(values_only=True):
        cells = ["" if c is None else str(c).strip() for c in r]
        if hdr is None:
            if any("프로젝트명" in c for c in cells):
                hdr = {}
                for i, c in enumerate(cells):
                    if "프로젝트명" in c: hdr["project"] = i
                    elif "금주" in c: hdr["this"] = i
                    elif "차주" in c: hdr["next"] = i
                    elif "계약상황" in c: hdr["status"] = i
                    elif "due" in c.lower() or "런칭" in c: hdr["due"] = i
            continue
        def g(k):
            i = hdr.get(k)
            return cells[i] if i is not None and i < len(cells) else ""
        proj = g("project") or last_proj
        if g("project"):
            last_proj = g("project")
        tw, nw = g("this"), g("next")
        if not (tw or nw):
            continue
        rows.append({"project": proj, "this": tw, "next": nw, "status": g("status"), "due": g("due")})
print(json.dumps(rows, ensure_ascii=False))
'''


def _parse_weekly_plan(path):
    """주간업무계획.xlsx → [{project, this, next, status, due}] — 헤더('프로젝트명') 탐지,
    프로젝트명 빈 행은 직전 상속, 금주·차주 모두 빈 행 skip.
    인프로세스 openpyxl 우선, 없으면 venv 파이썬 subprocess 폴백."""
    try:
        import openpyxl  # noqa: F401
        rows = []
        wb = openpyxl.load_workbook(path, data_only=True)
        for ws in wb.worksheets:
            hdr = None
            last_proj = ""
            for r in ws.iter_rows(values_only=True):
                cells = ["" if c is None else str(c).strip() for c in r]
                if hdr is None:
                    if any("프로젝트명" in c for c in cells):
                        hdr = {}
                        for i, c in enumerate(cells):
                            if "프로젝트명" in c: hdr["project"] = i
                            elif "금주" in c: hdr["this"] = i
                            elif "차주" in c: hdr["next"] = i
                            elif "계약상황" in c: hdr["status"] = i
                            elif "due" in c.lower() or "런칭" in c: hdr["due"] = i
                    continue
                def g(k):
                    i = hdr.get(k)
                    return cells[i] if i is not None and i < len(cells) else ""
                proj = g("project") or last_proj
                if g("project"):
                    last_proj = g("project")
                tw, nw = g("this"), g("next")
                if not (tw or nw):
                    continue
                rows.append({"project": proj, "this": tw, "next": nw,
                             "status": g("status"), "due": g("due")})
        return rows
    except ImportError:
        pass
    import subprocess, tempfile
    for py in _XLSX_PY_CANDIDATES:
        if not Path(py).exists():
            continue
        try:
            r = subprocess.run([py, "-c", _PLAN_PARSE_SNIPPET, str(path)],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout)
        except Exception:
            continue
    return []


def _llm_todo(text, max_items=12):
    """자유 텍스트 업무지시 → 실행가능 to-do 항목 리스트. OpenAI(urllib, stdlib). 실패 시 []."""
    text = (text or "").strip()
    if not (OPENAI_KEY and text):
        return []
    _today = datetime.date.today().isoformat()
    sys_p = (f"오늘은 {_today}(YYYY-MM-DD)이다. 다음 업무 지시 텍스트를 담당자가 바로 실행할 수 있는 "
             f"개별 to-do 항목으로 분해한다. 각 항목은 구체적 한 문장. 지시에 없는 내용을 지어내지 말 것. 항목 최대 {max_items}개. "
             "**프로젝트 귀속 필수**: 항목이 특정 프로젝트에 속하면 project에 상위 프로젝트명을 넣는다. "
             "예) '봉은사 프로젝트 … (상세항목 _ BM 세부 리서치 및 아이데이션)' → 봉은사의 하위 상세항목이므로 "
             "그 항목의 project는 '봉은사'. 상위 프로젝트가 명시된 문장의 하위 항목들은 모두 같은 project를 상속한다. 불명확하면 빈칸. "
             "마감(deadline)은 텍스트에 명시적 날짜·요일이 있을 때만 오늘 기준 YYYY-MM-DD로 계산하고, 없거나 불명확하면 반드시 빈칸. "
             "임의 날짜 생성 절대 금지. priority는 '긴급' 근거 없으면 '일반'. "
             '반드시 JSON만 출력: {"items":[{"task":"...","project":"","deadline":"","priority":"일반"}]}')
    payload = json.dumps({"model": "gpt-4o-mini", "temperature": 0.2,
                          "response_format": {"type": "json_object"},
                          "messages": [{"role": "system", "content": sys_p},
                                       {"role": "user", "content": text[:4000]}]}).encode("utf-8")
    req = Request("https://api.openai.com/v1/chat/completions", data=payload,
                  headers={"Authorization": "Bearer " + OPENAI_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        items = json.loads(d["choices"][0]["message"]["content"]).get("items", [])
    except Exception:
        return []
    out = []
    for it in items:
        t = (it.get("task") or "").strip()
        if t:
            out.append({"task": t, "project": (it.get("project") or "").strip(),
                        "deadline": (it.get("deadline") or "").strip(),
                        "priority": (it.get("priority") or "일반").strip()})
    return out

# ── 보고 시뮬레이터 AI 프롬프트 ──

SIMULATOR_DAILY_PROMPT = """너는 ARISA 보고 품질 시뮬레이터다. 직원의 일일보고를 6-Layer 프레임워크로 리뷰하고 ReportScore 100점을 채점한다.

## 6-Layer 프레임워크
| Layer | 핵심 질문 |
|-------|----------|
| Context | 이 프로젝트가 무엇인가? 왜 하는가? |
| Progress | 현재 어디까지 왔는가? Output/Outcome |
| Thinking | 왜 그렇게 판단했는가? 사실 vs 의견 구분 |
| Priority | 무엇이 가장 중요한가? 오늘/내일 최중요 |
| Risk | 문제·막힌 것·예상 위험 |
| Decision | 대표가 결정해야 할 것, 승인·지원 요청 |

## ReportScore 채점 루브릭 (100점)
| 항목 | 배점 | 만점 기준 |
|------|------|----------|
| context | 20 | 프로젝트명 + 왜 하는지(목적/배경) |
| objective | 10 | 목표 대비 % 또는 성공 기준이 숫자·상태로 있음 |
| evidence | 15 | 판단마다 사실/의견이 구분됨 |
| priority | 15 | 오늘 최중요 1~2개 + 내일 최중요 1개 표시 |
| risk | 10 | 발생 문제 + 예상 위험 + 대응 ("없음" 명시 = 만점, 빈칸 = 0) |
| decision | 20 | 옵션 + 추천안 + 기한 ("없음" 명시 = 만점, 빈칸 = 0) |
| support | 10 | 무엇이·언제까지·왜 필요한지 ("없음" 명시 = 만점, 빈칸 = 0) |

## 안티패턴 감지 (7종)
1. output_copy: Output 텍스트가 Outcome에 그대로 복사
2. vague_decision: "컨펌 필요"만 — 옵션/기한 없음
3. empty_risk: Risk 빈칸 ("없음" 명시가 아닌 진짜 빈칸)
4. no_why: 중요 업무에 "왜" 설명 없음
5. abstract_tomorrow: "계속 진행", "추가 확인" 등 구체성 없는 내일 계획
6. fact_opinion_mix: 사실/의견 미분리 ("클라이언트가 원하는 것 같다" 등)
7. no_numbers: Output/Outcome에 수치(건수, %, 금액 등) 전무

## ThinkingCost
대표가 이 보고를 읽고 추가로 물어야 할 질문 수를 예측하라.
- 0개 = ★★★★★ (5), 1개 = ★★★★☆ (4), 2개 = ★★★☆☆ (3), 3개 = ★★☆☆☆ (2), 4개 = ★☆☆☆☆ (1), 5개+ = ☆☆☆☆☆ (0)

## Before/After 참고
Bad: "도면 작업 중" → Good: "[세스크멘슬] 주방 도면 v3 — 설비팀 피드백 반영 중. 환기닥트 위치 변경으로 레이아웃 수정. 내일 오전 최종본 공유 예정"
Bad: "컨펌 필요" → Good: "결정 요청: 자재 A안(2,000만원·내구성↑) vs B안(1,500만원·납기↑). 추천: A안 (유지보수비 절감). 기한: 7/15까지"
Bad: "리서치 진행함" → Good: "경쟁사 3곳 벤치마킹 완료 — 가격대/메뉴구성/타깃 비교표 작성(12건). 공유 드라이브에 업로드"

## 출력 형식 (반드시 이 JSON만 출력)
```json
{
  "scores": {
    "context": {"score": 0, "max": 20, "pass": false, "feedback": "..."},
    "objective": {"score": 0, "max": 10, "pass": false, "feedback": "..."},
    "evidence": {"score": 0, "max": 15, "pass": false, "feedback": "..."},
    "priority": {"score": 0, "max": 15, "pass": false, "feedback": "..."},
    "risk": {"score": 0, "max": 10, "pass": false, "feedback": "..."},
    "decision": {"score": 0, "max": 20, "pass": false, "feedback": "..."},
    "support": {"score": 0, "max": 10, "pass": false, "feedback": "..."}
  },
  "total": 0,
  "grade": "D",
  "patterns_detected": [
    {"type": "패턴명", "field": "해당필드", "detail": "구체 설명"}
  ],
  "thinking_cost": {"predicted_questions": 0, "stars": 5, "detail": "예측 근거"},
  "summary": "전체 코멘트 (2~3문장)",
  "improvement_tips": ["개선 팁1", "개선 팁2", "개선 팁3"]
}
```
등급: S(90~100), A(75~89), B(60~74), C(40~59), D(0~39)"""

SIMULATOR_BRIEF_PROMPT = """너는 ARISA 기획안(1P-Brief) 품질 시뮬레이터다. 직원의 기획안보고를 리뷰하고 100점을 채점한다.

## 1P-Brief 7항목 루브릭 (100점)
| 항목 | 배점 | 만점 기준 |
|------|------|----------|
| title | 15 | "[대상]을 위한 [내용]" 형식. 한 문장으로 무엇인지 알 수 있음 |
| summary | 20 | 대상/문제/방식/결과 4문장. 대표가 이것만 읽고 판단 가능 |
| stakeholder | 10 | P1/P2/P3 이해관계자 + 각각 원하는 것 명시 |
| client_value | 10 | 클라이언트가 얻는 구체적 이익(수치/상태) |
| core_idea | 20 | 형식이 아닌 해결방식(How). "팝업을 한다"는 형식, "유휴공간을 활용한 체험형 쇼룸"이 아이디어 |
| success_criteria | 15 | 측정 가능한 상태/숫자 (KPI). "성공적으로 마친다"는 0점 |
| support_needed | 10 | 예산/인력/파트너/의사결정. "없음" 명시 = 만점, 빈칸 = 0 |

## 기획안 안티패턴
1. abstract_title: "[OO] 프로젝트" 같은 추상적 제목 — 대상·내용 불명
2. no_summary: Summary 없음 또는 1문장 미만
3. format_as_idea: "팝업을 한다", "전시를 한다"처럼 형식만 적고 해결방식(How) 없음
4. unmeasurable_success: "성공적으로", "효과적으로" 등 측정 불가 기준
5. missing_stakeholder: 이해관계자 미식별 또는 "우리 회사"만
6. vague_budget: "추후 협의" 등 구체성 없는 예산/지원
7. no_problem: 왜 이 기획이 필요한지(문제 정의) 빠짐

## ThinkingCost
대표가 "이거 진행해도 되나?"를 판단하기 위해 추가로 물어야 할 질문 수 예측.
별점: 0개=5★, 1개=4★, 2개=3★, 3개=2★, 4개=1★, 5+개=0★

## 출력 형식 (반드시 이 JSON만 출력)
```json
{
  "scores": {
    "title": {"score": 0, "max": 15, "pass": false, "feedback": "..."},
    "summary": {"score": 0, "max": 20, "pass": false, "feedback": "..."},
    "stakeholder": {"score": 0, "max": 10, "pass": false, "feedback": "..."},
    "client_value": {"score": 0, "max": 10, "pass": false, "feedback": "..."},
    "core_idea": {"score": 0, "max": 20, "pass": false, "feedback": "..."},
    "success_criteria": {"score": 0, "max": 15, "pass": false, "feedback": "..."},
    "support_needed": {"score": 0, "max": 10, "pass": false, "feedback": "..."}
  },
  "total": 0,
  "grade": "D",
  "patterns_detected": [
    {"type": "패턴명", "field": "해당필드", "detail": "구체 설명"}
  ],
  "thinking_cost": {"predicted_questions": 0, "stars": 5, "detail": "예측 근거"},
  "summary": "전체 코멘트 (2~3문장)",
  "improvement_tips": ["개선 팁1", "개선 팁2", "개선 팁3"]
}
```
등급: S(90~100), A(75~89), B(60~74), C(40~59), D(0~39)"""

SIMULATOR_DRAFT_PROMPT = """너는 업무 보고 구조화 도우미다. 사용자가 자유롭게 서술한 업무 텍스트를 받아, 지정된 필드 구조에 맞게 정보를 추출·배분한다.

## 규칙
1. 텍스트에 실제로 언급된 정보만 추출한다. 없는 정보를 지어내지 않는다.
2. 빈 필드는 빈 문자열 ""로 반환한다.
3. 구체적 수치·이름·날짜가 있으면 반드시 포함한다.
4. 리뷰/채점/평가를 하지 않는다. 정보 추출·구조화만 수행한다.
5. 반드시 JSON만 출력한다.

## daily 모드 (일일보고 8필드)
```json
{"context":"","output":"","outcome":"","risk":"","tomorrow":"","decision":"","support":"","evidence":""}
```
- context: 프로젝트명 + 왜 중요한지
- output: 오늘 한 일의 구체적 산출물
- outcome: 목표 대비 진행 상황
- risk: 문제·리스크 (없으면 "없음")
- tomorrow: 내일 할 일
- decision: 대표에게 필요한 결정 (없으면 "없음")
- support: 필요한 지원 (없으면 "없음")
- evidence: 사실 vs 의견 구분

## brief 모드 (기획안 7필드)
```json
{"title":"","summary":"","stakeholder":"","client_value":"","core_idea":"","success_criteria":"","support_needed":""}
```
- title: [대상]을 위한 [내용] 형식 제목
- summary: 대상/문제/방식/결과 4문장
- stakeholder: P1/P2/P3 이해관계자
- client_value: 클라이언트가 얻는 이익
- core_idea: 해결방식(How)
- success_criteria: 측정 가능한 KPI
- support_needed: 예산/인력/파트너 (없으면 "없음")

사용자 메시지 첫 줄에 [MODE:daily] 또는 [MODE:brief]가 명시된다."""

_DAILY_FIELDS = [
    ("context", "오늘 가장 중요한 업무 (프로젝트명 + 왜)"),
    ("output", "오늘 얻은 결과 (Output)"),
    ("outcome", "목표 대비 현재 위치 (Outcome)"),
    ("risk", "발견한 문제 / 리스크"),
    ("tomorrow", "내일 가장 중요한 일"),
    ("decision", "대표에게 필요한 결정"),
    ("support", "필요한 지원"),
    ("evidence", "사실·의견 구분 메모"),
]
_BRIEF_FIELDS = [
    ("title", "프로젝트 제목"),
    ("summary", "Executive Summary"),
    ("stakeholder", "Primary Stakeholder (P1/P2/P3)"),
    ("client_value", "Client Value"),
    ("core_idea", "핵심 아이디어 (How)"),
    ("success_criteria", "성공 기준 (KPI)"),
    ("support_needed", "필요한 지원"),
]


def _build_simulator_input(mode, fields):
    """사용자 입력 필드를 LLM 유저 메시지로 조합."""
    items = _BRIEF_FIELDS if mode == "brief" else _DAILY_FIELDS
    lines = []
    for key, label in items:
        val = (fields.get(key) or "").strip()
        lines.append(f"[{label}]\n{val if val else '(빈칸)'}")
    return "\n\n".join(lines)


SIMULATOR_HTML = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>보고 시뮬레이터 — ARISA</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>
:root{--bg:#1A1A1A;--bg2:#202020;--bg3:#262626;--fg:#F5F0EB;--fg2:#C4BEB7;--muted:#8A857E;--line:#333;--accent:#6C5CE7;--red:#E17055;--green:#00b894;--amber:#FDCB6E;--coral:#E17055}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:'Pretendard Variable',sans-serif;font-weight:300;min-height:100vh}
.wrap{max-width:1400px;margin:0 auto;padding:24px 20px}
h1{font-size:22px;font-weight:700;margin-bottom:4px}
.sub{color:var(--muted);font-size:13px;margin-bottom:20px}
.modes{display:flex;gap:8px;margin-bottom:20px}
.mode-btn{background:var(--bg3);border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit}
.mode-btn.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.main{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:1200px){.main{grid-template-columns:1fr}}
.panel{background:var(--bg2);border:1px solid var(--line);border-radius:14px;padding:20px}
.panel h2{font-size:16px;font-weight:600;margin-bottom:14px}
.field{margin-bottom:14px}
.field label{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;margin-bottom:6px}
.field .tag{font-size:10px;padding:2px 7px;border-radius:4px;font-weight:600}
.tag-ctx{background:rgba(108,92,231,.15);color:var(--accent)}
.tag-prg{background:rgba(0,184,148,.15);color:var(--green)}
.tag-thk{background:rgba(253,203,110,.15);color:var(--amber)}
.tag-pri{background:rgba(253,203,110,.15);color:var(--amber)}
.tag-rsk{background:rgba(225,112,85,.15);color:var(--coral)}
.tag-dec{background:rgba(225,112,85,.15);color:var(--coral)}
.field textarea{width:100%;background:var(--bg3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:10px 12px;font-size:13px;font-family:inherit;resize:vertical;line-height:1.6;min-height:64px}
.field textarea:focus{border-color:var(--accent);outline:none}
.guide-toggle{font-size:11px;color:var(--accent);cursor:pointer;margin-left:auto;user-select:none}
.guide-box{display:none;margin:6px 0 0;background:var(--bg);border-radius:8px;padding:10px 12px;font-size:12px;line-height:1.6}
.guide-box.open{display:block}
.g-bad{color:var(--coral)}
.g-good{color:var(--green)}
.submit-row{margin-top:16px;display:flex;gap:10px;align-items:center}
.submit-btn{background:var(--accent);color:#fff;border:0;border-radius:10px;padding:14px 32px;font-size:15px;font-weight:700;cursor:pointer;font-family:inherit}
.submit-btn:disabled{opacity:.5;cursor:default}
.submit-msg{font-size:12px;color:var(--muted)}
.draft-section{background:var(--bg3);border:1px solid var(--line);border-radius:10px;margin-bottom:16px;overflow:hidden}
.draft-header{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;cursor:pointer;user-select:none}
.draft-header h3{font-size:13px;font-weight:600;color:var(--accent)}
.draft-header .arrow{font-size:12px;color:var(--muted);transition:transform .2s}
.draft-header .arrow.open{transform:rotate(180deg)}
.draft-body{display:none;padding:0 14px 14px}
.draft-body.open{display:block}
.draft-body textarea{width:100%;min-height:80px;background:var(--bg);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:10px 12px;font-size:13px;font-family:inherit;resize:vertical;line-height:1.6}
.draft-body textarea:focus{border-color:var(--accent);outline:none}
.draft-actions{display:flex;gap:8px;margin-top:10px;align-items:center}
.draft-btn{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:10px 18px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}
.draft-btn:disabled{opacity:.5;cursor:default}
.draft-msg{font-size:12px;color:var(--muted)}
.draft-hint{font-size:11px;color:var(--muted);margin-bottom:8px;line-height:1.5}
.ai-compare{margin-top:6px;background:rgba(108,92,231,.06);border:1px solid rgba(108,92,231,.2);border-radius:8px;padding:8px 10px;display:none}
.ai-compare.show{display:block}
.ai-compare-label{font-size:10px;color:var(--accent);font-weight:600;margin-bottom:4px}
.ai-compare-text{font-size:12px;color:var(--fg2);line-height:1.5}
.ai-replace-btn{background:transparent;border:1px solid var(--accent);color:var(--accent);border-radius:6px;padding:3px 10px;font-size:11px;cursor:pointer;margin-top:6px;font-family:inherit}
.ai-replace-btn:hover{background:var(--accent);color:#fff}
.result-empty{color:var(--muted);font-size:14px;text-align:center;padding:60px 0}
.score-circle{width:140px;height:140px;margin:0 auto 12px;position:relative}
.score-circle svg{transform:rotate(-90deg)}
.score-circle .val{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.score-circle .num{font-size:36px;font-weight:800}
.score-circle .grade{font-size:18px;font-weight:700;margin-top:2px}
.tc-row{text-align:center;margin-bottom:16px}
.tc-stars{font-size:22px;letter-spacing:2px}
.tc-detail{font-size:12px;color:var(--muted);margin-top:4px}
.item-card{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:8px}
.item-head{display:flex;justify-content:space-between;align-items:center}
.item-name{font-size:13px;font-weight:600}
.item-score{font-size:13px;font-weight:700}
.item-bar{height:4px;background:var(--bg3);border-radius:2px;margin:8px 0 6px;overflow:hidden}
.item-bar-fill{height:100%;border-radius:2px;transition:width .4s}
.item-fb{font-size:12px;color:var(--fg2);line-height:1.5}
.pat-card{background:rgba(225,112,85,.08);border:1px solid rgba(225,112,85,.25);border-radius:10px;padding:10px 14px;margin-bottom:8px}
.pat-type{font-size:12px;font-weight:700;color:var(--coral)}
.pat-detail{font-size:12px;color:var(--fg2);margin-top:4px}
.tips{margin-top:14px}
.tips h3{font-size:13px;font-weight:600;margin-bottom:8px}
.tip-item{font-size:12px;color:var(--fg2);padding:4px 0 4px 14px;border-left:2px solid var(--accent);margin-bottom:6px;line-height:1.5}
.summary-box{background:var(--bg);border-radius:10px;padding:14px;margin-bottom:14px;font-size:13px;line-height:1.7}
</style></head><body>
<div class="wrap">
<h1>보고 시뮬레이터</h1>
<p class="sub">Reporting OS v2 — 보고를 쓰고 AI 리뷰를 받아보세요. ReportScore 100점 채점 + ThinkingCost 예측</p>
<div class="modes">
  <button class="mode-btn on" data-m="daily">일일보고</button>
  <button class="mode-btn" data-m="brief">기획안 (1P-Brief)</button>
</div>
<div class="main">
  <div class="panel" id="input-panel">
    <h2 id="input-title">일일보고 입력</h2>
    <div class="draft-section" id="draft-section">
      <div class="draft-header" id="draft-toggle">
        <h3>AI 비교 보기</h3>
        <span class="arrow" id="draft-arrow">▼</span>
      </div>
      <div class="draft-body" id="draft-body">
        <div class="draft-hint">먼저 아래 폼을 직접 작성한 뒤, 같은 내용을 자유 텍스트로 입력하면 AI 드래프트와 비교할 수 있습니다.<br>내 보고와 AI 드래프트의 차이를 보며 빠진 항목을 발견하세요.</div>
        <textarea id="draft-text" placeholder="업무를 자유롭게 설명하세요...&#10;예) 오늘 세스크멘슬 주방 도면 v3 작업했고, 설비팀 피드백 반영 중. 환기닥트 위치가 바뀌어서 레이아웃 수정해야 함. 내일 오전까지 최종본 보내야 하는데, 자재 A안 B안 중에 대표님 결정이 필요함."></textarea>
        <div class="draft-actions">
          <button class="draft-btn" id="draft-btn" disabled>AI 드래프트와 비교</button>
          <span class="draft-msg" id="draft-msg"></span>
        </div>
      </div>
    </div>
    <div id="fields"></div>
    <div class="submit-row">
      <button class="submit-btn" id="submit-btn">AI 리뷰 받기</button>
      <span class="submit-msg" id="submit-msg"></span>
    </div>
  </div>
  <div class="panel" id="result-panel">
    <h2>AI 리뷰 결과</h2>
    <div id="result"><div class="result-empty">왼쪽 폼을 작성하고 "AI 리뷰 받기"를 눌러보세요.</div></div>
  </div>
</div>
</div>
<script>
(function(){
var mode='daily';
var DAILY=[
  {key:'context',label:'오늘 가장 중요한 업무',tag:'Context',tagC:'ctx',ph:'프로젝트명 + 왜 중요한지\\n예) [세스크멘슬] 주방 도면 v3 최종화 — 설비팀 피드백 반영 기한이 오늘',
   bad:'도면 작업 중',good:'[세스크멘슬] 주방 도면 v3 — 설비팀 피드백(환기닥트 위치 변경) 반영. 내일 오전 최종본 공유 예정'},
  {key:'output',label:'오늘 얻은 결과 (Output)',tag:'Progress',tagC:'prg',ph:'구체적 산출물 + 수량\\n예) 경쟁사 3곳 벤치마킹 비교표 작성(12건), 드라이브 업로드 완료',
   bad:'리서치 진행함',good:'경쟁사 3곳 벤치마킹 완료 — 가격대/메뉴구성/타깃 비교표(12건). 드라이브에 업로드'},
  {key:'outcome',label:'목표 대비 현재 위치 (Outcome)',tag:'Thinking',tagC:'thk',ph:'Output이 목표에 어떤 의미인지\\n예) 전체 진행률 70% — 남은 건 자재 발주(A/B안 확정 대기)',
   bad:'(Output을 그대로 복사)',good:'도면 검토 3/5건 완료(60%). 남은 2건은 구조 변경 영향 확인 후 내일 반영 예정'},
  {key:'risk',label:'발견한 문제 / 리스크',tag:'Risk',tagC:'rsk',ph:'문제 + 영향 + 대응\\n없으면 "없음"이라고 명시 (빈칸은 0점)',
   bad:'(빈칸)',good:'자재 납기 1주 지연 통보 — 오픈일 영향 가능. 대안업체 2곳 견적 요청 완료, 내일 비교'},
  {key:'tomorrow',label:'내일 가장 중요한 일',tag:'Priority',tagC:'pri',ph:'★ 최중요 1개 + 기타\\n예) ★ 자재 A/B안 비교표 대표 보고 → 나머지: 도면 잔여 2건 마무리',
   bad:'계속 진행',good:'★ 자재 A/B안 비교표 작성 → 오전 중 대표 보고. 도면 잔여 2건 오후 마무리'},
  {key:'decision',label:'대표에게 필요한 결정',tag:'Decision',tagC:'dec',ph:'옵션 + 추천안 + 기한\\n없으면 "없음"이라고 명시',
   bad:'컨펌 필요',good:'결정 요청: 자재 A안(2,000만·내구성↑) vs B안(1,500만·납기↑). 추천: A안. 기한: 7/15'},
  {key:'support',label:'필요한 지원',tag:'Decision',tagC:'dec',ph:'무엇이·언제까지·왜 필요한지\\n없으면 "없음"이라고 명시',
   bad:'(빈칸)',good:'설비업체 미팅 동석 요청 — 7/16(수) 오후. 환기 설계 변경 최종 확인 필요'},
  {key:'evidence',label:'사실·의견 구분 메모',tag:'Thinking',tagC:'thk',ph:'판단 근거가 직접 확인인지, 추정인지\\n예) 사실: 업체가 메일로 납기지연 통보 / 의견: 대안업체가 더 빠를 것으로 예상',
   bad:'클라이언트가 원하는 것 같다',good:'사실: 7/10 미팅에서 면적 확대 요청 직접 발언. 의견: 예산 내 가능할 것으로 판단(견적 대기 중)'}
];
var BRIEF=[
  {key:'title',label:'프로젝트 제목',tag:'Context',tagC:'ctx',ph:'"[대상]을 위한 [내용]" 형식\\n예) 봉은사 방문객을 위한 도심 명상 체험 프로그램',
   bad:'봉은사 프로젝트',good:'봉은사 방문객을 위한 도심 명상 체험 프로그램'},
  {key:'summary',label:'Executive Summary',tag:'Context',tagC:'ctx',ph:'4문장: 대상 / 문제 / 방식 / 결과',
   bad:'봉은사에서 프로그램을 진행합니다.',good:'대상: 25~45세 도시 직장인. 문제: 봉은사 방문자 90%가 산책만 하고 떠남(체류 20분). 방식: 점심시간 런치명상(30분) 정기 프로그램. 결과: 재방문율 40%↑, 체류시간 2배'},
  {key:'stakeholder',label:'Primary Stakeholder',tag:'Context',tagC:'ctx',ph:'P1/P2/P3 + 각각 원하는 것',
   bad:'우리 회사',good:'P1: 봉은사 주지스님 — 현대적 포교 확대. P2: 직장인 참가자 — 접근성 높은 명상. P3: 기업 HR — 직원 복지 콘텐츠'},
  {key:'client_value',label:'Client Value',tag:'Context',tagC:'ctx',ph:'클라이언트가 얻는 구체적 이익',
   bad:'좋은 프로그램을 제공합니다',good:'봉은사: 25~45세 신규 방문자 월 500명↑, 정기후원 전환 5%. 기업 HR: 직원 스트레스 지수 15% 감소(3개월 측정)'},
  {key:'core_idea',label:'핵심 아이디어 (How)',tag:'Thinking',tagC:'thk',ph:'형식(팝업/전시)이 아닌 해결방식',
   bad:'명상 프로그램을 합니다',good:'출퇴근 동선에 30분 명상을 끼워넣는 "런치명상" — 앱 예약+현장 안내+사후 가이드 3단계 여정 설계'},
  {key:'success_criteria',label:'성공 기준 (KPI)',tag:'Priority',tagC:'pri',ph:'측정 가능한 숫자/상태',
   bad:'성공적으로 마친다',good:'3개월 내 정기참가자 200명, 만족도 4.5/5.0, 재참가율 60%, 후원전환 5%'},
  {key:'support_needed',label:'필요한 지원',tag:'Decision',tagC:'dec',ph:'예산/인력/파트너/의사결정\\n없으면 "없음"',
   bad:'추후 협의',good:'초기 예산 1,500만원 승인(공간조성 800+운영 700). 봉은사 담당 스님 소개 연결. 기한: 8월 초'}
];
var esc=function(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');};
function renderFields(){
  var items=mode==='brief'?BRIEF:DAILY, h='';
  document.getElementById('input-title').textContent=mode==='brief'?'기획안 (1P-Brief) 입력':'일일보고 입력';
  items.forEach(function(f){
    h+='<div class="field"><label>'+esc(f.label)+' <span class="tag tag-'+f.tagC+'">'+esc(f.tag)+'</span>'
      +'<span class="guide-toggle" data-k="'+f.key+'">가이드 ▼</span></label>'
      +'<textarea id="f-'+f.key+'" placeholder="'+esc(f.ph)+'"></textarea>'
      +'<div class="guide-box" id="g-'+f.key+'">'
      +'<div class="g-bad">Bad: '+esc(f.bad)+'</div>'
      +'<div class="g-good">Good: '+esc(f.good)+'</div></div></div>';
  });
  document.getElementById('fields').innerHTML=h;
  document.querySelectorAll('.guide-toggle').forEach(function(el){
    el.onclick=function(){
      var g=document.getElementById('g-'+el.dataset.k);
      g.classList.toggle('open');
      el.textContent=g.classList.contains('open')?'가이드 ▲':'가이드 ▼';
    };
  });
}
function gradeColor(g){
  if(g==='S') return 'var(--green)';
  if(g==='A') return 'var(--accent)';
  if(g==='B') return 'var(--amber)';
  return 'var(--coral)';
}
var ITEM_LABELS={context:'Context (맥락)',objective:'Objective (목표)',evidence:'Evidence (근거)',
  priority:'Priority (우선순위)',risk:'Risk (리스크)',decision:'Decision (결정)',support:'Support (지원)',
  title:'제목',summary:'Executive Summary',stakeholder:'Stakeholder',client_value:'Client Value',
  core_idea:'핵심 아이디어',success_criteria:'성공 기준',support_needed:'필요한 지원'};
function renderResult(d){
  var box=document.getElementById('result');
  if(!d||!d.scores){box.innerHTML='<div class="result-empty">리뷰 결과를 가져오지 못했습니다. 다시 시도해주세요.</div>';return;}
  var pct=d.total, gc=gradeColor(d.grade);
  var r=Math.round(pct/100*251.2); // circumference=2*PI*40
  var h='<div class="score-circle"><svg width="140" height="140"><circle cx="70" cy="70" r="40" fill="none" stroke="var(--bg3)" stroke-width="8"/>'
    +'<circle cx="70" cy="70" r="40" fill="none" stroke="'+gc+'" stroke-width="8" stroke-dasharray="'+r+' 251.2" stroke-linecap="round"/></svg>'
    +'<div class="val"><div class="num" style="color:'+gc+'">'+d.total+'</div><div class="grade" style="color:'+gc+'">'+esc(d.grade)+'</div></div></div>';
  // ThinkingCost
  var tc=d.thinking_cost||{};
  var stars='';for(var i=0;i<5;i++) stars+=(i<(tc.stars||0))?'★':'☆';
  h+='<div class="tc-row"><div style="font-size:12px;color:var(--muted);margin-bottom:4px">ThinkingCost</div>'
    +'<div class="tc-stars" style="color:'+gc+'">'+stars+'</div>'
    +'<div class="tc-detail">예상 추가질문 '+(tc.predicted_questions||0)+'개'+(tc.detail?(' — '+esc(tc.detail)):'')+'</div></div>';
  // Summary
  if(d.summary) h+='<div class="summary-box">'+esc(d.summary)+'</div>';
  // Item cards
  var scores=d.scores;
  for(var k in scores){
    var s=scores[k], barPct=Math.round(s.score/s.max*100);
    var barC=s.pass?'var(--green)':'var(--coral)';
    h+='<div class="item-card"><div class="item-head"><span class="item-name">'+(s.pass?'✓':'✗')+' '+(ITEM_LABELS[k]||k)+'</span>'
      +'<span class="item-score" style="color:'+barC+'">'+s.score+'/'+s.max+'</span></div>'
      +'<div class="item-bar"><div class="item-bar-fill" style="width:'+barPct+'%;background:'+barC+'"></div></div>'
      +'<div class="item-fb">'+esc(s.feedback||'')+'</div></div>';
  }
  // Patterns
  var pats=d.patterns_detected||[];
  if(pats.length){
    h+='<h3 style="font-size:13px;font-weight:600;margin:14px 0 8px">감지된 안티패턴</h3>';
    pats.forEach(function(p){
      h+='<div class="pat-card"><div class="pat-type">⚠ '+esc(p.type)+(p.field?(' · '+esc(p.field)):'')+'</div>'
        +'<div class="pat-detail">'+esc(p.detail||'')+'</div></div>';
    });
  }
  // Tips
  var tips=d.improvement_tips||[];
  if(tips.length){
    h+='<div class="tips"><h3>개선 팁</h3>';
    tips.forEach(function(t){ h+='<div class="tip-item">'+esc(t)+'</div>'; });
    h+='</div>';
  }
  box.innerHTML=h;
}
document.querySelectorAll('.mode-btn').forEach(function(b){
  b.onclick=function(){
    mode=b.dataset.m;
    document.querySelectorAll('.mode-btn').forEach(function(x){x.classList.toggle('on',x.dataset.m===mode);});
    renderFields();
    document.getElementById('result').innerHTML='<div class="result-empty">왼쪽 폼을 작성하고 "AI 리뷰 받기"를 눌러보세요.</div>';
  };
});
document.getElementById('submit-btn').onclick=function(){
  var btn=this, msg=document.getElementById('submit-msg');
  var items=mode==='brief'?BRIEF:DAILY, fields={}, empty=0;
  items.forEach(function(f){
    var v=(document.getElementById('f-'+f.key)||{}).value||'';
    fields[f.key]=v;
    if(!v.trim()) empty++;
  });
  if(empty===items.length){msg.textContent='최소 1개 항목을 입력해주세요.';return;}
  btn.disabled=true; msg.textContent='AI가 리뷰 중… (10~20초 소요)';
  document.getElementById('result').innerHTML='<div class="result-empty">분석 중…</div>';
  fetch('/api/simulator/review',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({mode:mode,fields:fields})})
    .then(function(r){return r.json();})
    .then(function(d){
      btn.disabled=false; msg.textContent='';
      if(d.ok) renderResult(d.result);
      else{document.getElementById('result').innerHTML='<div class="result-empty">'+(d.error||'리뷰 실패')+'</div>';}
    })
    .catch(function(){btn.disabled=false;msg.textContent='서버 연결 실패';});
};
renderFields();
// --- AI 비교 보기 ---
var draftOpen=false, aiDraft=null;
document.getElementById('draft-toggle').onclick=function(){
  draftOpen=!draftOpen;
  document.getElementById('draft-body').classList.toggle('open',draftOpen);
  document.getElementById('draft-arrow').classList.toggle('open',draftOpen);
};
// draft-btn 활성화: 폼에 1개 이상 입력 + 자유텍스트 입력 시
function checkDraftReady(){
  var items=mode==='brief'?BRIEF:DAILY, hasField=false;
  items.forEach(function(f){if((document.getElementById('f-'+f.key)||{}).value&&(document.getElementById('f-'+f.key)||{}).value.trim()) hasField=true;});
  var hasText=((document.getElementById('draft-text')||{}).value||'').trim().length>0;
  document.getElementById('draft-btn').disabled=!(hasField&&hasText);
}
document.getElementById('draft-text').addEventListener('input',checkDraftReady);
// 폼 필드에도 리스너 (renderFields 후 재부착)
var origRender=renderFields;
renderFields=function(){
  origRender();
  aiDraft=null; clearCompare();
  var items=mode==='brief'?BRIEF:DAILY;
  items.forEach(function(f){
    var el=document.getElementById('f-'+f.key);
    if(el) el.addEventListener('input',checkDraftReady);
  });
  checkDraftReady();
};
renderFields();
function clearCompare(){
  document.querySelectorAll('.ai-compare').forEach(function(el){el.classList.remove('show');el.innerHTML='';});
}
function showCompare(draft){
  var items=mode==='brief'?BRIEF:DAILY;
  items.forEach(function(f){
    var cmp=document.getElementById('cmp-'+f.key);
    if(!cmp) return;
    var val=(draft[f.key]||'').trim();
    if(!val){cmp.classList.remove('show');cmp.innerHTML='';return;}
    cmp.classList.add('show');
    cmp.innerHTML='<div class="ai-compare-label">AI 드래프트</div>'
      +'<div class="ai-compare-text">'+esc(val)+'</div>'
      +'<button class="ai-replace-btn" data-k="'+f.key+'">이 값으로 교체</button>';
    cmp.querySelector('.ai-replace-btn').onclick=function(){
      var ta=document.getElementById('f-'+this.dataset.k);
      if(ta){ta.value=draft[this.dataset.k]||'';ta.style.borderColor='var(--accent)';setTimeout(function(){ta.style.borderColor='';},1500);}
    };
  });
}
// renderFields에서 compare div 삽입
var origRender2=renderFields;
renderFields=function(){
  origRender2();
  // 각 필드 아래에 비교 영역 추가
  var items=mode==='brief'?BRIEF:DAILY;
  items.forEach(function(f){
    var fieldDiv=document.getElementById('f-'+f.key);
    if(!fieldDiv) return;
    var cmpDiv=document.createElement('div');
    cmpDiv.className='ai-compare';cmpDiv.id='cmp-'+f.key;
    fieldDiv.parentNode.appendChild(cmpDiv);
  });
};
renderFields();
document.getElementById('draft-btn').onclick=function(){
  var btn=this, msg=document.getElementById('draft-msg');
  var text=(document.getElementById('draft-text').value||'').trim();
  if(!text){msg.textContent='텍스트를 입력해주세요.';return;}
  btn.disabled=true; msg.textContent='AI가 구조화 중... (5~10초)';
  clearCompare();
  fetch('/api/simulator/draft',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({mode:mode,text:text})})
    .then(function(r){return r.json();})
    .then(function(d){
      btn.disabled=false; msg.textContent='';
      if(d.ok&&d.fields){aiDraft=d.fields;showCompare(d.fields);msg.textContent='비교 결과가 각 필드 아래에 표시됩니다.';}
      else{msg.textContent=d.error||'드래프트 생성 실패';}
      checkDraftReady();
    })
    .catch(function(){btn.disabled=false;msg.textContent='서버 연결 실패';checkDraftReady();});
};
})();
</script></body></html>"""

# / — 역할 인식 통합 셸: 로그인 1회 후 역할별 탭을 iframe으로 전환.
#   대표   = [프로젝트 | 오늘 Brief | 이번 주 | Decision Window] + 팀 스코프 드롭다운
#   리더   = [프로젝트 | 오늘 Brief(팀) | 이번 주(팀)] (2팀 리더는 드롭다운)
#   직원   = [프로젝트]
# iframe 격리라 CSS 충돌 없음. 통합 로그인이 pm_sess(포트폴리오)+brief_sess 등 세션키를 미리
# 세팅해 각 iframe(/projects·/brief·/weekly·/team-*·/arisa2/)이 게이트를 자동 통과.
UNIFIED_SHELL = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project Rent 대시보드</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>
:root{--bg:#1A1A1A;--bg-2:#202020;--bg-3:#262626;--fg:#F5F0EB;--muted:#8A857E;--line:#333;--accent:#6C5CE7;--red:#E17055}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:var(--bg);color:var(--fg);font-family:'Pretendard Variable',sans-serif;font-weight:300}
#login-gate{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:100}
#login-box{background:var(--bg-2);border:1px solid var(--line);border-radius:14px;padding:38px 40px;width:330px;text-align:center}
#login-box h2{font-size:19px;font-weight:600;margin-bottom:6px}
#login-box .lg-sub{color:var(--muted);font-size:13px;margin-bottom:22px}
#login-box input{width:100%;background:var(--bg-3);border:1px solid var(--line);border-radius:8px;padding:12px 14px;color:var(--fg);font-size:14px;margin-bottom:10px;font-family:inherit}
#login-box button{width:100%;background:var(--accent);color:#fff;border:0;border-radius:8px;padding:12px;font-size:14px;font-weight:600;cursor:pointer;margin-top:6px}
#login-err{color:var(--red);font-size:12px;margin-top:12px;min-height:16px}
#shell{display:none;flex-direction:column;height:100vh}
#tabs{display:flex;gap:6px;padding:10px 16px;border-bottom:1px solid var(--line);background:var(--bg-2);align-items:center;flex-shrink:0}
.tab{background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:8px;padding:8px 18px;font-size:14px;cursor:pointer;font-family:inherit;font-weight:500}
.tab.on{background:var(--accent);color:#fff;border-color:var(--accent)}
#scope-sel{background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:8px 12px;font-size:13px;font-family:inherit}
#tabs .who{margin-left:auto;font-size:12px;color:var(--muted)}
#tabs .who a{color:var(--accent);cursor:pointer;margin-left:8px}
.frame{flex:1;border:0;width:100%;display:none;background:var(--bg)}
.frame.on{display:block}
#f-mywork{overflow:auto;padding:24px}
.mw-wrap{max-width:1000px;margin:0 auto}
.mw-h{font-size:15px;font-weight:600;margin:22px 0 12px}
.mw-form{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:14px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:6px}
.mw-form select,.mw-form input{background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:9px 12px;font-size:13px;font-family:inherit}
.mw-form button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:9px 18px;font-size:13px;font-weight:600;cursor:pointer}
.mw-assign{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:8px}
.mw-assign textarea{width:100%;min-height:76px;background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:11px 13px;font-size:13px;font-family:inherit;resize:vertical;line-height:1.5}
.td-actions{display:flex;gap:8px;margin-top:10px;align-items:center}
.td-actions button,.mw-assign button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:9px 18px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}
.td-actions button:disabled{opacity:.5}
button.btn-sec{background:var(--bg-3);color:var(--fg);border:1px solid var(--line)}
.td-row{display:flex;gap:6px;align-items:center;margin-top:7px}
.tg-box{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-top:10px}
.tg-head{display:flex;gap:8px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:10px}
.tg-label{font-size:11px;color:var(--muted);flex-shrink:0}
.tg-proj{flex:1;min-width:150px;background:var(--bg-3);border:1px solid var(--accent);color:var(--fg);border-radius:8px;padding:9px 12px;font-size:13px;font-weight:500;font-family:inherit}
.tg-as{background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:9px 10px;font-size:12px;font-family:inherit}
.tg-add{background:transparent;border:1px dashed var(--line);color:var(--muted);border-radius:8px;padding:7px 12px;font-size:12px;cursor:pointer;margin-top:8px;font-family:inherit}
.mw-plan{display:flex;gap:10px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
.mw-file{background:rgba(108,92,231,.12);border:1px solid rgba(108,92,231,.4);color:var(--accent);border-radius:8px;padding:8px 14px;font-size:12.5px;font-weight:600;cursor:pointer}
.mw-file:hover{background:var(--accent);color:#fff}
.pg-head{font-size:13px;font-weight:600;color:var(--accent);margin:16px 0 6px;display:flex;align-items:center;gap:8px}
.pg-cnt{font-size:11px;color:var(--muted);font-weight:400}
.pg-item{margin-left:10px;border-left:2px solid var(--line)}
.td-row .td-proj{width:120px;flex-shrink:0;background:var(--bg-3);border:1px solid var(--accent);color:var(--fg);border-radius:8px;padding:9px 10px;font-size:12px;font-family:inherit}
.td-row .td-task{flex:1;min-width:140px;background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:9px 12px;font-size:13px;font-family:inherit}
.td-row select,.td-row input[type=date]{background:var(--bg-3);border:1px solid var(--line);color:var(--fg);border-radius:8px;padding:9px 10px;font-size:12px;font-family:inherit}
.td-row .td-del{background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:8px;width:32px;height:34px;cursor:pointer;font-size:16px;flex-shrink:0}
.mw-card{background:var(--bg-2);border:1px solid var(--line);border-radius:10px;padding:12px 15px;margin-bottom:7px}
.mw-card .t{font-size:14px;font-weight:500}
.mw-card .m{font-size:12px;color:var(--muted);margin-top:4px}
.mw-badge{font-size:11px;border-radius:5px;padding:1px 7px;margin-left:8px}
.st-act{cursor:pointer;font-size:11px;border:1px solid var(--line);border-radius:6px;padding:2px 9px;margin-left:6px;color:var(--muted);white-space:nowrap}
.st-act:hover{border-color:var(--accent);color:var(--accent)}
.st-wait{font-size:11px;border-radius:5px;padding:1px 7px;margin-left:8px;background:rgba(244,196,48,.14);color:#f4c430}
.st-chk{accent-color:var(--red);width:14px;height:14px;cursor:pointer;margin-left:8px;vertical-align:middle}
#mw-bulkbar{display:none;position:fixed;bottom:26px;left:50%;transform:translateX(-50%);background:var(--bg-2);
  border:1px solid var(--red);border-radius:12px;padding:10px 16px;gap:12px;align-items:center;z-index:60;
  box-shadow:0 6px 24px rgba(0,0,0,.5);font-size:13px}
#mw-bulkbar button{border:0;border-radius:8px;padding:7px 14px;cursor:pointer;font-family:inherit;font-size:13px}
#mw-bulkbar .bb-del{background:var(--red);color:#fff;font-weight:600}
#mw-bulkbar .bb-clear{background:transparent;border:1px solid var(--line);color:var(--muted)}
.mw-urgent{background:rgba(225,112,85,.16);color:var(--red)}
.mw-proj{border-left:2px solid var(--accent);padding-left:14px;margin-bottom:16px}
.mw-proj-name{font-size:14px;font-weight:600;margin-bottom:8px}
.mw-empty{color:var(--muted);font-size:13px;padding:8px 0}
#arisa2-status{font-size:11px;color:var(--muted);margin-left:6px}
#arisa2-status.ok{color:#00b894}
#arisa2-status.err{color:var(--red)}
</style></head>
<body>
<div id="login-gate"><div id="login-box">
  <h2>Project Rent 대시보드</h2>
  <div class="lg-sub">이름 + PIN (첫 로그인 시 PIN 설정)</div>
  <input id="lg-id" placeholder="이름" autocomplete="username">
  <input id="lg-pin" type="password" placeholder="PIN" autocomplete="current-password">
  <button id="lg-btn">로그인</button>
  <div id="login-err"></div>
</div></div>
<div id="shell">
  <div id="tabs">
    <button class="tab on" data-t="mywork">내 업무</button>
    <button class="tab" data-t="projects">프로젝트</button>
    <button class="tab" data-t="simulator">보고 시뮬레이터</button>
    <button class="tab" data-t="brief" style="display:none">오늘 Brief</button>
    <button class="tab" data-t="weekly" style="display:none">이번 주</button>
    <select id="scope-sel" style="display:none"></select>
    <span class="who" id="who"></span>
  </div>
  <div class="frame on" id="f-mywork"></div>
  <iframe class="frame" id="f-projects"></iframe>
  <iframe class="frame" id="f-brief"></iframe>
  <iframe class="frame" id="f-weekly"></iframe>
  <iframe class="frame" id="f-simulator"></iframe>
</div>
<script>
(function(){
  var gate=document.getElementById('login-gate'), shell=document.getElementById('shell'), who=document.getElementById('who');
  var sel=document.getElementById('scope-sel');
  var frames={mywork:document.getElementById('f-mywork'),projects:document.getElementById('f-projects'),
              brief:document.getElementById('f-brief'),weekly:document.getElementById('f-weekly'),
              simulator:document.getElementById('f-simulator')};
  var SESS=null, curTab='mywork', curScope='', loaded={projects:false,brief:false,weekly:false,simulator:false};
  var MW_ASSIGNEES=[];
  var SESS_KEYS=['pm_sess','brief_sess','weekly_sess','team_brief_sess','team_weekly_sess'];
  var CLEAR_KEYS=SESS_KEYS.concat(['arisa_sess','arisa_token']);
  function tabBtn(t){ return document.querySelector('.tab[data-t="'+t+'"]'); }
  function srcFor(t){
    if(t==='projects') return '/projects';
    if(t==='simulator') return '/simulator';
    if(t==='decision') return '/arisa2/';
    var lt=SESS.lead_teams||[];
    if(t==='brief'){
      if(SESS.admin) return curScope==='' ? '/brief' : '/team-brief?team='+encodeURIComponent(curScope);
      if(lt.length) return curScope==='' ? '/lead-brief?teams='+encodeURIComponent(lt.join(',')) : '/team-brief?team='+encodeURIComponent(curScope);
      return '/my-brief?name='+encodeURIComponent(SESS.name);  // 직원 — 내 카드 + 팀 헤드라인
    }
    if(SESS.admin && curScope==='') return '/weekly';
    return '/team-weekly?team='+encodeURIComponent(curScope||lt[0]||'');
  }
  function showTab(t){
    curTab=t;
    document.querySelectorAll('.tab').forEach(function(b){ b.classList.toggle('on', b.dataset.t===t); });
    Object.keys(frames).forEach(function(k){ frames[k].classList.toggle('on', k===t); });
    if(t==='mywork'){ renderMyWork(); return; }  // div 직접 렌더(iframe 아님) — 매번 최신
    if(!loaded[t]){ frames[t].src=srcFor(t); loaded[t]=true; }
  }
  function loadScope(scope){
    curScope=scope; loaded.brief=false; loaded.weekly=false;
    frames.brief.src='about:blank'; frames.weekly.src='about:blank';
    if(curTab==='brief'||curTab==='weekly'){ frames[curTab].src=srcFor(curTab); loaded[curTab]=true; }
  }
  function arisa2Login(s){
    // PIN 단일화(users.json symlink)로 같은 자격 재사용 → ARISA 2.0 토큰 발급. Promise<bool> 반환(showTab이 await).
    return fetch('/arisa2/api/login?name='+encodeURIComponent(s.name)+'&pin='+encodeURIComponent(s.pin||''),{method:'POST'})
      .then(function(r){ if(!r.ok) throw new Error('login '+r.status); return r.json(); })
      .then(function(d){
        if(!(d && d.ok)) throw new Error('bad response');
        localStorage.setItem('arisa_sess',JSON.stringify(d.user));
        localStorage.setItem('arisa_token',d.token);
        if(loaded.decision){ frames.decision.src=srcFor('decision'); } // 이미 열려 있었으면 재로드
        return true;
      }).catch(function(e){ console.warn('[arisa2Login]', e && e.message); return false; });
  }
  function checkArisa2(){
    fetch('/arisa2/api/health',{method:'GET'}).then(function(r){
      var ok=r.status<500; // 401 등 4xx = 서버 살아있음(인증 게이트)
      a2s.textContent=ok?'ARISA 2.0 ON':'ARISA 2.0 OFF';
      a2s.className=ok?'ok':'err';
    }).catch(function(){ a2s.textContent='ARISA 2.0 OFF'; a2s.className='err'; });
  }
  function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function mwAssignHtml(lv){
    return '<div class="mw-h">업무 분장 <span class="sub2">— 자유롭게 적으면 AI가 항목화 → 편집 후 '+lv+'에게 배분 → 승인'+(lv==='팀원'?' (대표가 배분한 내 업무를 참고해도 됩니다)':'')+'</span></div>'
      +'<div class="mw-assign">'
      +'<div class="mw-plan"><label class="mw-file" for="mw-xlsx">📄 주간업무계획 업로드 (.xlsx)</label>'
      +'<input type="file" id="mw-xlsx" accept=".xlsx" style="display:none">'
      +'<a href="/guide/template.xlsx" style="color:var(--accent);font-size:12px;text-decoration:none">📥 템플릿 받기</a>'
      +'<span class="sub2">— 금주·차주 업무를 프로젝트별 검토 초안으로 자동 변환</span></div>'
      +'<textarea id="mw-text" placeholder="이번주 팀 업무를 자유롭게 적으세요.&#10;예) 봉은사 마스터플랜 검토·정리본 공유, 세스크멘슬 주방도면 정리, KBO 굿즈 발주 최종확인"></textarea>'
      +'<div class="td-actions"><button id="mw-parse">AI로 항목 정리</button></div>'
      +'<div id="mw-todos"></div><div id="mw-msg" class="sub2"></div></div>';
  }
  function mwBindParse(){
    var fx=document.getElementById('mw-xlsx');
    if(fx){ fx.onchange=function(){
      var f=fx.files&&fx.files[0], msg=document.getElementById('mw-msg');
      if(!f) return;
      msg.textContent='📄 '+f.name+' — 주간업무계획을 검토 초안으로 변환 중…';
      var rd=new FileReader();
      rd.onload=function(){
        fetch('/api/assign-from-plan',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({user:SESS.name,pin:SESS.pin,b64:rd.result})})
          .then(function(r){return r.json();}).then(function(d){
            fx.value='';
            if(d.ok && d.items && d.items.length){
              msg.textContent='검토 초안 '+d.items.length+'건 생성 ('+ (d.rows||0) +'개 행) — 담당자 지정 후 등록하세요.';
              mwRenderTodos(d.items);
            } else { msg.textContent=d.error||'항목을 뽑지 못했습니다.'; }
          }).catch(function(){ fx.value=''; msg.textContent='서버 오류'; });
      };
      rd.readAsDataURL(f);
    };}
    var pb=document.getElementById('mw-parse');
    if(!pb) return;
    pb.onclick=function(){
      var txt=document.getElementById('mw-text').value.trim(), msg=document.getElementById('mw-msg');
      if(!txt){ msg.textContent='업무 내용을 입력하세요'; return; }
      msg.textContent='AI가 항목으로 정리 중…'; pb.disabled=true;
      fetch('/api/assign-parse',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({user:SESS.name,pin:SESS.pin,text:txt})})
        .then(function(r){return r.json();}).then(function(d){
          pb.disabled=false;
          if(d.ok && d.items && d.items.length){ msg.textContent='검토 후 각 항목에 담당자를 지정하고 승인하세요.'; mwRenderTodos(d.items); }
          else { msg.textContent='항목을 뽑지 못했습니다. 더 구체적으로 적어보세요.'; }
        }).catch(function(){ pb.disabled=false; msg.textContent='서버 오류'; });
    };
  }
  function renderLeadHome(){
    // 리더 홈 — 팀 Todo(대표·리더 분장) + 분장 생성 + 진행중 프로젝트 + 팀원 오늘 보고
    var box=frames.mywork;
    box.innerHTML='<div class="mw-wrap"><div class="mw-empty">불러오는 중…</div></div>';
    var u=encodeURIComponent(SESS.name);
    Promise.all([
      fetch('/api/lead-home?user='+u).then(function(r){return r.json();}),
      fetch('/api/assignees?user='+u).then(function(r){return r.json();})
    ]).then(function(res){
      var lh=res[0]||{}, ac=res[1]||{}, h='<div class="mw-wrap">';
      MW_ASSIGNEES = ac.assignees || [];
      var A=lh.assignments||[];
      // 위계 분리: 받은 업무(대표→리더 본인) vs 팀 Todo(리더→팀원 배분분)
      var _rcSeen={};
      var received=A.filter(function(a){
        if(a.assignee!==SESS.name) return false;
        var k=[a.project,a.task,a.deadline,a.status].join('|');
        if(_rcSeen[k]) return false; _rcSeen[k]=1; return true;
      });
      var teamTodo=A.filter(function(a){ return a.assignee!==SESS.name; });
      h+=mwApprovalsHtml(lh.approvals||[]);
      if(received.length){
        h+='<div class="mw-h">📥 받은 업무 <span class="sub2">— 대표 지시 · [상세 분장]으로 팀원에게 쪼개서 배분하세요</span></div>';
        received.forEach(function(a,i){
          var st=a.status||'미착수';
          var badge='<span class="lh-st '+(st==='완료'?'lh-done':(st==='진행중'?'lh-doing':'lh-todo'))+'">'+esc(st)+'</span>';
          var urg=(a.priority==='긴급')?'<span class="mw-badge mw-urgent">긴급</span>':'';
          var pj=a.project?(esc(a.project)+' · '):'';
          var dl=a.deadline?(' · 마감 '+esc(a.deadline)):'';
          var act='';
          if(a.row){
            if(st==='완료'){ act='<span class="st-wait">⏳ 승인 대기</span>'; }
            else{ act=mwStBtn(a,'완료','✓ 완료'); }
          }
          h+='<div class="mw-card rc-card"><div class="t">'+badge+' '+esc(a.task)+urg+act
            +'<button class="rc-btn" data-i="'+i+'">→ 팀원에게 상세 분장</button></div>'
            +'<div class="m">'+pj+'대표 지시'+dl+'</div></div>';
        });
      }
      h+='<div class="mw-h">팀 Todo · 이번주 분장 <span class="sub2">'+esc((lh.teams||[]).join(' · '))+'</span></div>';
      if(teamTodo.length){ h+=mwAssignListHtml(teamTodo, true); }
      else { h+='<div class="mw-empty">팀원에게 배분된 분장이 아직 없습니다. 아래에서 바로 만들 수 있습니다.</div>'; }
      if(ac.canAssign){ h+=mwAssignHtml(ac.level||'팀원'); }
      h+='<div class="mw-h">진행중인 프로젝트 <span class="sub2">'+(lh.projects||[]).length+'건 — 클릭하면 프로젝트 탭</span></div>';
      var P=lh.projects||[];
      if(P.length){ P.forEach(function(p){
        var pr=(p.task_total?(' · 업무 '+p.task_done+'/'+p.task_total):'');
        h+='<div class="lh-proj" data-open="projects"><div class="t">'+esc(p.name)+'</div><div class="m">PM '+esc(p.pm||'-')+(p.dday?(' · D-day '+esc(p.dday)):'')+pr+'</div></div>';
      }); } else { h+='<div class="mw-empty">진행중인 팀 프로젝트가 없습니다.</div>'; }
      h+='<div class="mw-h">팀원 오늘 보고 <span class="sub2">'+esc(lh.brief_date||'')+'</span></div>';
      h+=(lh.brief_html||'<div class="mw-empty">보고가 아직 없습니다.</div>');
      h+='</div>'; box.innerHTML=h;
      mwBindParse();
      mwBindStatus(box);
      mwBindBulk(box);
      box.querySelectorAll('.lh-proj').forEach(function(el){ el.onclick=function(){ showTab('projects'); }; });
      box.querySelectorAll('.rc-btn').forEach(function(b){
        b.onclick=function(){
          var a=received[parseInt(b.getAttribute('data-i'),10)]; if(!a) return;
          var ta=document.getElementById('mw-text'); if(!ta) return;
          ta.value=(a.project?('['+a.project+'] '):'')+a.task+' — 이를 실행하기 위한 상세 업무:\\n- ';
          ta.focus(); ta.scrollIntoView({behavior:'smooth',block:'center'});
        };
      });
    }).catch(function(){ box.innerHTML='<div class="mw-wrap"><div class="mw-empty">불러오기 실패</div></div>'; });
  }
  function renderMyWork(){
    var lt=SESS.lead_teams||[];
    if(!SESS.admin && lt.length){ renderLeadHome(); return; }  // 리더 → 팀 홈
    var box=frames.mywork;
    box.innerHTML='<div class="mw-wrap"><div class="mw-empty">불러오는 중…</div></div>';
    var u=encodeURIComponent(SESS.name);
    Promise.all([
      fetch('/api/my-work?user='+u).then(function(r){return r.json();}),
      fetch('/api/assignees?user='+u).then(function(r){return r.json();}),
      SESS.admin ? fetch('/api/exec-attn?user='+u).then(function(r){return r.json();}) : Promise.resolve(null)
    ]).then(function(res){
      var mw=res[0]||{}, ac=res[1]||{}, ex=res[2], h='<div class="mw-wrap">';
      MW_ASSIGNEES = ac.assignees || [];
      if(ex && ex.ok){
        var D=ex.decisions||[], O=ex.overdue||[];
        if(D.length){
          h+='<div class="mw-h">🧾 결재·확인 필요 <span class="sub2">'+D.length+'건 — 미해결 결정·승인 요청</span></div>';
          D.forEach(function(d){
            var age=d.age>0?(' · '+d.age+'일 경과'):'';
            var pj=d.project?(' · '+esc(d.project)):'';
            h+='<div class="mw-card ex-red"><div class="t">'+esc(d.title)+'</div><div class="m">'+esc(d.who||'')+pj+age+'</div></div>';
          });
        }
        if(O.length){
          h+='<div class="mw-h">⏰ 지연 업무 <span class="sub2">'+O.length+'건 — 마감 경과·미완료 분장</span></div>';
          O.forEach(function(a){
            var pj=a.project?(esc(a.project)+' · '):'';
            h+='<div class="mw-card ex-amber"><div class="t">'+esc(a.task)+' <span class="mw-badge mw-urgent">D+'+a.days_overdue+'</span>'
              +(a.row?(mwStBtn(a,'삭제','🗑')+mwChk(a)):'')+'</div>'
              +'<div class="m">'+pj+esc(a.assignee||'미지정')+' · 마감 '+esc(a.deadline||'')+' · '+esc(a.status||'미착수')+'</div></div>';
          });
        }
        h+=mwApprovalsHtml(ex.approvals||[]);
        if(!D.length && !O.length && !(ex.approvals||[]).length){ h+='<div class="mw-h">✅ 지연·결재·승인 대기 없음</div>'; }
      }
      if(ac.canAssign){ h+=mwAssignHtml(ac.level||'담당자'); }
      h+='<div class="mw-h">오늘 할일 · 내 분장</div>';
      var A=mw.assignments||[];
      if(A.length){ h+=mwAssignListHtml(A, false); }
      else { h+='<div class="mw-empty">배정된 분장이 없습니다.</div>'; }
      h+='<div class="mw-h">내 프로젝트 일정</div>';
      var P=mw.projects||[];
      if(P.length){ P.forEach(function(p){
        h+='<div class="mw-proj"><div class="mw-proj-name">'+esc(p.name)+(p.dday?(' <span style="color:var(--muted);font-weight:400;font-size:12px">D-day '+esc(p.dday)+'</span>'):'')+'</div>';
        (p.tasks||[]).forEach(function(t){
          var per=(t.start||'')+(t.end?('~'+t.end):'');
          h+='<div class="mw-card"><div class="t">'+esc(t.task||'')+'</div><div class="m">'+esc(t.status||'')+' · '+esc(t.division||'')+(per?(' · '+esc(per)):'')+'</div></div>';
        });
        h+='</div>';
      }); } else { h+='<div class="mw-empty">배정된 프로젝트 업무가 없습니다.</div>'; }
      h+='</div>'; box.innerHTML=h;
      mwBindParse();
      mwBindStatus(box);
      mwBindBulk(box);
    }).catch(function(){ box.innerHTML='<div class="mw-wrap"><div class="mw-empty">불러오기 실패</div></div>'; });
  }
  function mwAsOpts(sel){ return MW_ASSIGNEES.map(function(a){return '<option value="'+esc(a.name)+'"'+(a.name===sel?' selected':'')+'>'+esc(a.name)+' ('+esc(a.team||'')+')</option>';}).join(''); }
  function mwTodoRow(it){
    it=it||{};
    return '<div class="td-row"><input class="td-task" value="'+esc(it.task||'')+'" placeholder="업무 내용">'
      +'<select class="td-as"><option value="">담당자</option>'+mwAsOpts(it.assignee||'')+'</select>'
      +'<input class="td-dl" type="date" value="'+esc(it.deadline||'')+'" title="마감">'
      +'<select class="td-pr"><option'+(it.priority==='긴급'?'':' selected')+'>일반</option><option'+(it.priority==='긴급'?' selected':'')+'>긴급</option></select>'
      +'<button class="td-del" title="삭제">×</button></div>';
  }
  function mwBindRow(row){ row.querySelector('.td-del').onclick=function(){ row.remove(); }; }
  function mwGroupBox(project, items){
    // 프로젝트 그룹 에디터 — 프로젝트명은 그룹당 1개 입력, 담당자는 항목별 개별 지정
    return '<div class="tg-box"><div class="tg-head">'
      +'<span class="tg-label">프로젝트</span><input class="tg-proj" value="'+esc(project)+'" placeholder="(비우면 기타)">'
      +'<span class="tg-label">일괄 담당자</span><select class="tg-as"><option value="">선택 시 빈 담당자 채움</option>'+mwAsOpts('')+'</select>'
      +'</div><div class="tg-rows">'+items.map(mwTodoRow).join('')+'</div>'
      +'<button class="tg-add">+ 이 프로젝트에 항목 추가</button></div>';
  }
  function mwBindGroup(g){
    g.querySelectorAll('.td-row').forEach(mwBindRow);
    g.querySelector('.tg-add').onclick=function(){
      var d=document.createElement('div'); d.innerHTML=mwTodoRow({}); var row=d.firstChild;
      mwBindRow(row); g.querySelector('.tg-rows').appendChild(row);
    };
    g.querySelector('.tg-as').onchange=function(){
      var v=this.value; if(!v) return;
      g.querySelectorAll('.td-as').forEach(function(s){ if(!s.value) s.value=v; });
      this.selectedIndex=0;
    };
  }
  function mwRenderTodos(items){
    var box=document.getElementById('mw-todos');
    var groups={}, order=[];
    (items||[]).forEach(function(it){
      var p=(it.project||'').trim();
      if(!(p in groups)){ groups[p]=[]; order.push(p); }
      groups[p].push(it);
    });
    if(!order.length) order.push('');
    box.innerHTML=order.map(function(p){ return mwGroupBox(p, groups[p]||[{}]); }).join('')
      +'<div class="td-actions"><button id="mw-addgrp" class="btn-sec">+ 새 프로젝트 그룹</button>'
      +'<button id="mw-commit">최종 승인 · 등록</button></div>';
    box.querySelectorAll('.tg-box').forEach(mwBindGroup);
    document.getElementById('mw-addgrp').onclick=function(){
      var d=document.createElement('div'); d.innerHTML=mwGroupBox('', [{}]); var g=d.firstChild;
      mwBindGroup(g); box.insertBefore(g, box.querySelector('.td-actions'));
    };
    document.getElementById('mw-commit').onclick=mwCommit;
  }
  function mwCommit(){
    var items=[], msg=document.getElementById('mw-msg');
    document.querySelectorAll('#mw-todos .tg-box').forEach(function(g){
      if(g.id==='mw-projconf') return;
      var proj=g.querySelector('.tg-proj'); if(!proj) return;
      var pv=proj.value.trim();
      g.querySelectorAll('.td-row').forEach(function(r){
        var task=r.querySelector('.td-task').value.trim();
        if(task) items.push({assignee:r.querySelector('.td-as').value, task:task, project:pv,
          deadline:r.querySelector('.td-dl').value, priority:r.querySelector('.td-pr').value});
      });
    });
    if(!items.length){ msg.textContent='등록할 항목이 없습니다'; return; }
    if(items.some(function(i){return !i.assignee;})){ msg.textContent='모든 항목에 담당자를 지정하세요'; return; }
    var names=[]; items.forEach(function(i){ var p=(i.project||'').trim(); if(p && names.indexOf(p)<0) names.push(p); });
    if(!names.length){ mwSend(items, []); return; }
    msg.textContent='프로젝트 확인 중…';
    fetch('/api/assign-project-check',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({user:SESS.name,pin:SESS.pin,names:names})})
      .then(function(r){return r.json();}).then(function(d){
        if(!d.ok){ msg.textContent=d.error||'프로젝트 확인 실패'; return; }
        var news=(d.results||[]).filter(function(x){return x.isNew;});
        if(!news.length){ mwSend(items, []); return; }
        mwRenderProjConfirm(items, news, d.all||[], d.results||[]);
      }).catch(function(){ msg.textContent='서버 오류'; });
  }
  function pcPmOpts(){
    var names=MW_ASSIGNEES.map(function(a){return a.name;});
    if(names.indexOf(SESS.name)<0) names.unshift(SESS.name);
    return names.map(function(n){return '<option'+(n===SESS.name?' selected':'')+'>'+esc(n)+'</option>';}).join('');
  }
  function mwRenderProjConfirm(items, news, all, results){
    // 신규 프로젝트 확인 패널 — 그룹별 [신규 생성(PM·일정)] 또는 [기존에 합치기] 선택 후 확정
    var msg=document.getElementById('mw-msg'); msg.textContent='';
    var old=document.getElementById('mw-projconf'); if(old) old.remove();
    var today=new Date().toISOString().slice(0,10);
    var box=document.createElement('div'); box.id='mw-projconf'; box.className='tg-box';
    var h='<div class="tg-head"><span class="tg-label">🆕 신규 프로젝트 확인</span>'
      +'<span class="sub2">포트폴리오에 없는 이름입니다 — 신규 생성 또는 기존 프로젝트에 합치세요</span></div>';
    var matchedInfo=(results||[]).filter(function(x){return x.matched && x.name!==x.matched.name;})
      .map(function(x){ return '“'+esc(x.name)+'” → 기존 “'+esc(x.matched.name)+'”에 반영됩니다'; });
    if(matchedInfo.length){ h+='<div class="sub2" style="padding:4px 2px">'+matchedInfo.join(' · ')+'</div>'; }
    news.forEach(function(n,i){
      var opts='<option value="">— 기존 프로젝트 선택 —</option>', candIds={};
      (n.candidates||[]).forEach(function(c){ candIds[c.id]=1; opts+='<option value="'+esc(c.id)+'">'+esc(c.name)+' (유사)</option>'; });
      (all||[]).forEach(function(c){ if(!candIds[c.id]) opts+='<option value="'+esc(c.id)+'">'+esc(c.name)+'</option>'; });
      var dls=items.filter(function(it){return (it.project||'').trim()===n.name && it.deadline;})
        .map(function(it){return it.deadline;}).sort();
      var endDef=dls.length?dls[dls.length-1]:'';
      h+='<div class="pc-row" data-name="'+esc(n.name)+'" style="padding:10px 2px;border-top:1px solid rgba(255,255,255,.08)">'
        +'<div style="font-weight:600;margin-bottom:6px">🆕 '+esc(n.name)+'</div>'
        +'<label><input type="radio" name="pc-act-'+i+'" value="create" checked> 신규 생성</label>'
        +'<label style="margin-left:12px"><input type="radio" name="pc-act-'+i+'" value="merge"> 기존에 합치기</label>'
        +'<div class="pc-create" style="margin-top:6px">'
          +'<span class="tg-label">PM(리드)</span><select class="pc-pm">'+pcPmOpts()+'</select> '
          +'<span class="tg-label">시작</span><input type="date" class="pc-start" value="'+today+'"> '
          +'<span class="tg-label">종료</span><input type="date" class="pc-end" value="'+esc(endDef)+'">'
        +'</div>'
        +'<div class="pc-merge" style="margin-top:6px;display:none"><select class="pc-target">'+opts+'</select></div>'
        +'</div>';
    });
    h+='<div class="td-actions" style="margin-top:8px"><button id="pc-ok">확정 등록</button>'
      +'<button id="pc-cancel" class="btn-sec">취소</button></div>';
    box.innerHTML=h;
    var todos=document.getElementById('mw-todos'); todos.parentNode.insertBefore(box, todos.nextSibling);
    box.querySelectorAll('.pc-row').forEach(function(row){
      row.querySelectorAll('input[type=radio]').forEach(function(rb){ rb.onchange=function(){
        var m=this.value==='merge';
        row.querySelector('.pc-create').style.display=m?'none':'';
        row.querySelector('.pc-merge').style.display=m?'':'none';
      };});
    });
    document.getElementById('pc-cancel').onclick=function(){ box.remove(); };
    document.getElementById('pc-ok').onclick=function(){
      var acts=[], bad=null;
      box.querySelectorAll('.pc-row').forEach(function(row){
        var name=row.getAttribute('data-name');
        var act=row.querySelector('input[type=radio]:checked').value;
        if(act==='merge'){
          var t=row.querySelector('.pc-target').value;
          if(!t){ bad='“'+name+'”: 합칠 기존 프로젝트를 선택하세요'; return; }
          acts.push({name:name, action:'merge', mergeId:t});
        } else {
          acts.push({name:name, action:'create', pm:row.querySelector('.pc-pm').value||SESS.name,
            start:row.querySelector('.pc-start').value, end:row.querySelector('.pc-end').value});
        }
      });
      if(bad){ msg.textContent=bad; return; }
      box.remove();
      mwSend(items, acts);
    };
  }
  function mwSend(items, projectActions){
    var msg=document.getElementById('mw-msg');
    msg.textContent='등록 중…';
    fetch('/api/assign-commit',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({user:SESS.name,pin:SESS.pin,items:items,projectActions:projectActions||[]})})
      .then(function(r){return r.json();}).then(function(d){
        if(d.added){
          var extra=[];
          if(d.created&&d.created.length) extra.push('신규 프로젝트 생성: '+d.created.join(', '));
          if(d.merged&&d.merged.length) extra.push('기존 프로젝트에 합침: '+d.merged.join(', '));
          if(extra.length) alert('등록 완료 ('+d.added+'건) — '+extra.join(' / '));
          renderMyWork();
        } else { msg.textContent=(d.errors&&d.errors.join(', '))||'등록 실패(주간분장 탭 확인)'; }
      }).catch(function(){ msg.textContent='서버 오류'; });
  }
  function mwStBtn(a, st, label){
    return '<a class="st-act" data-row="'+a.row+'" data-task="'+esc(a.task)+'" data-assignee="'+esc(a.assignee||'')+'" data-st="'+st+'">'+label+'</a>';
  }
  function mwChk(a){
    return '<input type="checkbox" class="st-chk" title="일괄 삭제 선택" data-row="'+a.row+'" data-task="'+esc(a.task)+'" data-assignee="'+esc(a.assignee||'')+'">';
  }
  function mwBindBulk(scope){
    var chks=scope.querySelectorAll('.st-chk');
    var bar=document.getElementById('mw-bulkbar');
    if(!bar){ bar=document.createElement('div'); bar.id='mw-bulkbar'; document.body.appendChild(bar); }
    bar.style.display='none';
    if(!chks.length) return;
    function upd(){
      var sel=scope.querySelectorAll('.st-chk:checked');
      if(!sel.length){ bar.style.display='none'; return; }
      bar.style.display='flex';
      bar.innerHTML='<span>🗑 <b>'+sel.length+'건</b> 선택됨</span>'
        +'<button class="bb-del">선택 삭제</button><button class="bb-clear">선택 해제</button>';
      bar.querySelector('.bb-clear').onclick=function(){
        [].forEach.call(sel,function(c){ c.checked=false; }); upd();
      };
      bar.querySelector('.bb-del').onclick=function(){
        if(!confirm('선택한 '+sel.length+'건 분장을 삭제할까요? 목록·집계·포트폴리오에서 제외됩니다. (시트 행은 삭제 표시로 보존)')) return;
        var items=[].map.call(sel,function(c){ return {row:+c.getAttribute('data-row'),
          task:c.getAttribute('data-task'), assignee:c.getAttribute('data-assignee')}; });
        this.disabled=true; this.textContent='삭제 중…';
        fetch('/api/assign-bulk-delete',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({user:SESS.name,pin:SESS.pin,items:items})})
        .then(function(r){return r.json();}).then(function(d){
          if(d.errors&&d.errors.length) alert((d.deleted||0)+'건 삭제, 일부 실패: '+d.errors.join(' / '));
          bar.style.display='none'; renderMyWork();
        }).catch(function(){ alert('서버 오류'); renderMyWork(); });
      };
    }
    [].forEach.call(chks,function(c){ c.onchange=upd; });
  }
  function mwBindStatus(scope){
    scope.querySelectorAll('.st-act').forEach(function(el){
      el.onclick=function(){
        var st=el.getAttribute('data-st');
        if(st==='승인' && !confirm('승인하면 내 업무에서 정리되고 프로젝트 포트폴리오에 완료로 기록됩니다.')) return;
        if(st==='삭제' && !confirm('이 분장을 삭제할까요? 목록·집계에서 제외되고 포트폴리오 기록도 제거됩니다. (시트 행은 삭제 표시로 보존)')) return;
        el.textContent='…';
        fetch('/api/assign-status',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({user:SESS.name,pin:SESS.pin,row:+el.getAttribute('data-row'),
            task:el.getAttribute('data-task'),assignee:el.getAttribute('data-assignee'),status:st})})
        .then(function(r){return r.json();}).then(function(d){
          if(!d.ok) alert(d.error||'상태 변경 실패');
          renderMyWork();
        }).catch(function(){ alert('서버 오류'); renderMyWork(); });
      };
    });
  }
  function mwApprovalsHtml(AP){
    if(!AP||!AP.length) return '';
    var h='<div class="mw-h">✅ 완료 승인 대기 <span class="sub2">'+AP.length+'건 — 승인 시 프로젝트 포트폴리오에 완료 기록</span></div>';
    AP.forEach(function(a){
      var pj=a.project?(esc(a.project)+' · '):'';
      var dl=a.deadline?(' · 마감 '+esc(a.deadline)):'';
      h+='<div class="mw-card"><div class="t">'+esc(a.task)
        +mwStBtn(a,'승인','✓ 승인')+mwStBtn(a,'진행중','↩ 반려')+mwStBtn(a,'삭제','🗑')+mwChk(a)
        +'</div><div class="m">'+pj+esc(a.assignee||'미지정')+dl+'</div></div>';
    });
    return h;
  }
  function mwAssignListHtml(A, withAssignee){
    // 분장 완료 리스트 — 프로젝트 단위 그룹 + 완전 동일 행 표시 중복 제거(시트 무변경)
    var seen={}, groups={}, order=[];
    (A||[]).forEach(function(a){
      var key=[(a.project||''),(a.task||''),(a.assignee||''),(a.deadline||''),(a.status||'')].join('|');
      if(seen[key]) return; seen[key]=1;
      var p=(a.project||'').trim()||'기타';
      if(!(p in groups)){ groups[p]=[]; order.push(p); }
      groups[p].push(a);
    });
    order.sort(function(a,b){ if(a==='기타') return 1; if(b==='기타') return -1; return a.localeCompare(b,'ko'); });
    var h='';
    order.forEach(function(p){
      var items=groups[p];
      h+='<div class="pg-head">📁 '+esc(p)+' <span class="pg-cnt">'+items.length+'건</span></div>';
      items.forEach(function(a){
        var st=a.status||'미착수';
        var badge='<span class="lh-st '+(st==='완료'?'lh-done':(st==='진행중'?'lh-doing':'lh-todo'))+'">'+esc(st)+'</span>';
        var urg=(a.priority==='긴급')?'<span class="mw-badge mw-urgent">긴급</span>':'';
        var dl=a.deadline?(' · 마감 '+esc(a.deadline)):'';
        var who=withAssignee?esc(a.assignee||'미지정'):'';
        var act='';
        var canDel = SESS.admin || (SESS.lead_teams||[]).length;
        if(!withAssignee && a.row){
          if(st==='완료'){ act='<span class="st-wait">⏳ 승인 대기</span>'; }
          else{
            if(st==='미착수') act+=mwStBtn(a,'진행중','▶ 진행');
            act+=mwStBtn(a,'완료','✓ 완료');
          }
          if(canDel) act+=mwStBtn(a,'삭제','🗑')+mwChk(a);
        }
        if(withAssignee && a.row && canDel){ act+=mwStBtn(a,'삭제','🗑')+mwChk(a); }
        h+='<div class="mw-card pg-item"><div class="t">'+badge+' '+esc(a.task)+urg+act+'</div><div class="m">'+who+dl+'</div></div>';
      });
    });
    return h;
  }
  function changePin(){
    var cur=prompt('현재 PIN을 입력하세요'); if(!cur) return;
    var nw=prompt('새 PIN (4자 이상)'); if(!nw) return;
    fetch('/api/set-pin',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:SESS.name,pin:cur,new_pin:nw})})
      .then(function(r){return r.json();}).then(function(d){
        if(d.ok){ SESS.pin=nw; var j=JSON.stringify(SESS); SESS_KEYS.forEach(function(k){localStorage.setItem(k,j);}); alert('PIN이 변경되었습니다'); }
        else alert(d.error||'변경 실패');
      });
  }
  function enter(s){
    SESS=s; var j=JSON.stringify(s);
    SESS_KEYS.forEach(function(k){ localStorage.setItem(k,j); });
    gate.style.display='none'; shell.style.display='flex';
    who.innerHTML = s.name+' ('+(s.role||'')+') <a id="lg-guide">가이드</a> <a id="lg-pin-c">PIN변경</a> <a id="lg-out">로그아웃</a>';
    document.getElementById('lg-out').onclick=function(){ CLEAR_KEYS.forEach(function(k){localStorage.removeItem(k);}); location.reload(); };
    document.getElementById('lg-pin-c').onclick=changePin;
    document.getElementById('lg-guide').onclick=function(){ window.open('/guide-os','_blank'); };
    var lt=s.lead_teams||[];
    if(s.admin){
      tabBtn('brief').style.display=''; tabBtn('weekly').style.display='';
      // Decision Window(ARISA 2.0)는 데이터 취합 백단 창구 — 대시보드 전면 노출 안 함(탭 숨김)
      sel.style.display='inline-block'; sel.innerHTML='<option value="">전체</option>';
      lt.forEach(function(t){ var o=document.createElement('option'); o.value=t; o.textContent=t; sel.appendChild(o); });
      sel.onchange=function(){ loadScope(sel.value); };
      curScope='';
    } else if(lt.length){
      tabBtn('mywork').textContent='팀 홈';  // 리더 — 팀 Todo·분장·프로젝트·팀원 보고 통합
      tabBtn('brief').style.display=''; tabBtn('weekly').style.display='';
      if(lt.length>1){
        // 겸임 리더 — 기본 '담당팀 전체'(병합 한 페이지), 개별 팀은 집중 보기
        curScope='';
        sel.style.display='inline-block'; sel.innerHTML='<option value="">담당팀 전체</option>';
        lt.forEach(function(t){ var o=document.createElement('option'); o.value=t; o.textContent=t; sel.appendChild(o); });
        sel.onchange=function(){ loadScope(sel.value); };
      } else { curScope=lt[0]; sel.style.display='none'; }
    } else {
      tabBtn('brief').style.display='';  // 직원 — 내 브리프(본인 카드+팀 헤드라인)
      sel.style.display='none';
    }
    showTab('mywork');
  }
  document.querySelectorAll('.tab').forEach(function(b){ b.onclick=function(){ showTab(b.dataset.t); }; });
  var sess=null; try{ sess=JSON.parse(localStorage.getItem('pm_sess')||'null'); }catch(e){}
  if(sess && sess.name) enter(sess);
  function doLogin(){
    var id=document.getElementById('lg-id').value.trim(), pin=document.getElementById('lg-pin').value.trim();
    var err=document.getElementById('login-err'); err.textContent='';
    fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id,pin:pin})})
      .then(function(r){return r.json();})
      .then(function(d){
        if(d.ok){ var s=Object.assign({},d,{id:id,pin:pin}); enter(s); if(d.pin_set) alert('PIN이 설정되었습니다'); }
        else { err.textContent=d.error||'로그인 실패'; }
      })
      .catch(function(){ err.textContent='서버 연결 실패'; });
  }
  document.getElementById('lg-btn').onclick=doLogin;
  document.getElementById('lg-pin').addEventListener('keydown',function(e){ if(e.key==='Enter') doLogin(); });
})();
</script>
</body></html>"""

def load_users():
    """users.json 로드 — dict 스키마(대시보드)와 list 스키마(ARISA 2.0, symlink 단일화)를 모두 지원."""
    try:
        u = json.loads((DATA/"users.json").read_text(encoding="utf-8")).get("users", {})
    except Exception:
        return {}
    if isinstance(u, list):  # ARISA 2.0 스키마: [{name, role(admin/leader/member), team, pin}]
        return {x["name"]: {"pin": x.get("pin", ""),
                            "role": "대표" if x.get("role") == "admin" else (x.get("role") or "직원")}
                for x in u if x.get("name")}
    return u

def load_projects():
    out = []
    if PROJ_DIR.exists():
        for f in sorted(PROJ_DIR.glob("*.json")):
            try: out.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception: pass
    return out

def get_project(pid):
    f = PROJ_DIR / f"{_safe(pid)}.json"
    if f.exists():
        try: return json.loads(f.read_text(encoding="utf-8"))
        except Exception: return None
    return None

def save_project(p):
    PROJ_DIR.mkdir(parents=True, exist_ok=True)
    pid = _safe(p["id"])
    with _lock:
        (PROJ_DIR / f"{pid}.json").write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")

def _safe(pid):
    return re.sub(r"[^A-Za-z0-9가-힣_\-]", "_", str(pid))[:80] or "proj"

def auth(uid, pin):
    u = load_users().get(uid)
    if u and str(u.get("pin")) == str(pin): return u
    return None

def is_admin(uid):
    u = load_users().get(uid)
    return bool(u) and u.get("role") in ("대표", "admin")

def load_emp():
    try: return json.loads(EMP_PATH.read_text(encoding="utf-8"))
    except Exception: return {}

def lead_teams_of(uid):
    """이 사람이 리더인 팀 목록(team_leads 역매핑). 대표(admin)는 전체 팀."""
    tl = load_emp().get("team_leads", {})
    if is_admin(uid):
        return sorted(set(tl.keys()))
    return sorted([team for team, leader in tl.items() if leader == uid])

def set_pin(uid, new_pin):
    """users.json에 PIN 저장(첫 설정/변경) — dict/list 스키마 모두 지원. 성공 True."""
    p = DATA / "users.json"
    with _lock:
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return False
        users = doc.get("users")
        if isinstance(users, list):  # ARISA 2.0 스키마
            for x in users:
                if x.get("name") == uid:
                    x["pin"] = str(new_pin)
                    break
            else:
                return False
        else:
            if uid not in (users or {}):
                return False
            users[uid]["pin"] = str(new_pin)
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return True

def emp_team(name):
    """직원의 소속 팀(arisa-employees.json by_name[…].team)."""
    return (load_emp().get("by_name", {}).get(name, {}) or {}).get("team")

def is_leader(uid):
    """팀 리더 여부(대표 제외한 순수 리더도 True, 대표도 True)."""
    return bool(lead_teams_of(uid))


_PROJ_STOP = {"프로젝트", "행사", "팝업", "기획", "관련", "운영", "브랜드", "상세"}


def _proj_tokens(s):
    """프로젝트명 → 매칭용 토큰 집합 (영숫자·한글 단어, 일반어 제외)."""
    toks = set()
    for t in re.findall(r"[A-Za-z0-9]+|[가-힣]+", (s or "").lower()):
        if len(t) >= 2 and t not in _PROJ_STOP:
            toks.add(t)
    return toks


def _match_project(ap, pname):
    """분장 프로젝트명(ap) vs 포트폴리오명(pname) — 표기 변형 허용 매칭.
    ① 정규화 상호 포함 ② 유의 토큰 교집합 (영문 3자+/한글 2자+, 일반어 제외)."""
    na = re.sub(r"[^a-z0-9가-힣]", "", (ap or "").lower())
    nb = re.sub(r"[^a-z0-9가-힣]", "", (pname or "").lower())
    if na and nb and (na in nb or nb in na):
        return True
    common = _proj_tokens(ap) & _proj_tokens(pname)
    return any(len(t) >= 3 or re.fullmatch(r"[가-힣]{2,}", t) for t in common)


def _match_project_p(ap, p):
    """분장 프로젝트명(ap) vs 프로젝트 dict — 정식 명칭 + aliases(별칭·구표기)까지 매칭."""
    if _match_project(ap, p.get("name") or ""):
        return True
    return any(_match_project(ap, al) for al in (p.get("aliases") or []))


def _project_assignments(pname, aliases=None):
    """최근 2주 주간분장 중 프로젝트명이 매칭되는 항목 — 프로젝트 상세 '분장 업무' 섹션용.
    (엄격한 '이번주' 필터는 주가 바뀌면 미완료 할일이 사라져 2주 윈도우 사용.)
    완전 동일 행은 표시 중복 제거. aliases(별칭)도 매칭 대상."""
    pname = (pname or "").strip()
    if not pname:
        return []
    names = [pname] + list(aliases or [])
    today = datetime.date.today()
    ws = today - datetime.timedelta(days=today.weekday() + 7)  # 지난주 월요일부터
    we = today
    out, seen = [], set()
    for a in _assign_read():
        ds = (a.get("date") or "").strip()[:10]
        try:
            d = datetime.date.fromisoformat(ds)
        except ValueError:
            continue
        if not (ws <= d <= we):
            continue
        if (a.get("status") or "") == "삭제":
            continue
        ap = (a.get("project") or "").strip()
        if not ap or not any(_match_project(ap, n) for n in names):
            continue
        key = (ap, a.get("task"), a.get("assignee"), a.get("deadline"), a.get("status"))
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    out.sort(key=lambda a: (a.get("status") == "완료", a.get("deadline") or "9999"))
    return out


# ── 분장 ↔ 프로젝트 포트폴리오 연동 ──────────────────────────
_ASSIGN_ST_MAP = {"미착수": "Not Started", "진행중": "In Progress", "완료": "Done", "승인": "Done"}
_ASSIGN_PROG_MAP = {"미착수": 0, "진행중": 50, "완료": 100, "승인": 100}
_ASSIGN_DONE_STATES = ("완료", "승인")   # 분장 완료 판정
_ASSIGN_HIDDEN_STATES = ("승인", "삭제")  # 내 업무·팀 목록에서 숨김
_TASK_DONE_STATES = ("Done", "완료")     # 프로젝트 tasks 완료 판정 (영문/국문 혼재)


def _remove_done_task(assign):
    """삭제된 분장을 프로젝트 tasks에서 제거 (akey 매칭)."""
    pn = (assign.get("project") or "").strip()
    if not pn:
        return False
    tp = next((p for p in load_projects() if _match_project_p(pn, p)), None)
    if not tp:
        return False
    k = _akey(assign.get("date"), assign.get("task"), assign.get("assignee"))
    before = len(tp.get("tasks") or [])
    tp["tasks"] = [t for t in (tp.get("tasks") or []) if t.get("akey") != k]
    if len(tp["tasks"]) < before:
        save_project(tp)
        return True
    return False


def _can_approve(uid, assignee):
    """완료 승인 권한 — 대표 전체, 리더는 자기 팀원."""
    if is_admin(uid):
        return True
    return is_leader(uid) and emp_team(assignee) in set(lead_teams_of(uid))


def _record_done_task(assign, approver):
    """승인된 분장을 프로젝트 포트폴리오 tasks에 Done으로 영구 기록."""
    pn = (assign.get("project") or "").strip()
    if not pn:
        return False
    tp = next((p for p in load_projects() if _match_project_p(pn, p)), None)
    if not tp:
        return False
    k = _akey(assign.get("date"), assign.get("task"), assign.get("assignee"))
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    hit = next((t for t in (tp.get("tasks") or []) if t.get("akey") == k), None)
    if hit:
        hit.update({"status": "Done", "progress": 100, "approved_by": approver, "approved_at": now})
    else:
        tp.setdefault("tasks", []).append({
            "division": emp_team(assign.get("assignee")) or "", "task": assign.get("task") or "",
            "owner": assign.get("assignee") or "", "start": (assign.get("date") or "")[:10],
            "end": (assign.get("deadline") or "").strip(), "status": "Done", "progress": 100,
            "akey": k, "approved_by": approver, "approved_at": now})
    save_project(tp)
    return True


def _akey(date, task, assignee):
    """분장 행 식별키(등록일|업무|담당자) — 프로젝트 tasks 중복 방지·상태 동기화용."""
    return "|".join([(date or "").strip()[:10], (task or "").strip(), (assignee or "").strip()])


def _similar_projects(name, projects, limit=3):
    """유사 프로젝트 후보 — 이름 토큰 교집합 많은 순 최대 limit개."""
    toks = _proj_tokens(name)
    scored = []
    for p in projects:
        common = toks & _proj_tokens(p.get("name") or "")
        if common:
            scored.append((len(common), p))
    scored.sort(key=lambda x: -x[0])
    return [{"id": p.get("id"), "name": p.get("name") or p.get("id")} for _, p in scored[:limit]]


def _append_assign_tasks(p, items):
    """분장 항목을 프로젝트 tasks에 영구 반영 (akey 동일 항목 skip). 추가 건수 반환."""
    tasks = p.setdefault("tasks", [])
    seen = {t.get("akey") for t in tasks if t.get("akey")}
    today = datetime.date.today().isoformat()
    added = 0
    for it in items:
        k = _akey(today, it.get("task"), it.get("assignee"))
        if k in seen:
            continue
        seen.add(k)
        tasks.append({"division": emp_team(it.get("assignee")) or "", "task": (it.get("task") or "").strip(),
                      "owner": (it.get("assignee") or "").strip(), "start": today,
                      "end": (it.get("deadline") or "").strip(), "status": "Not Started",
                      "progress": 0, "akey": k})
        added += 1
    return added


def _sync_assign_status(p):
    """akey 있는 프로젝트 tasks 상태를 주간분장 시트(SSOT) 최신 상태로 갱신. 변경 여부 반환."""
    keyed = [t for t in (p.get("tasks") or []) if t.get("akey")]
    if not keyed:
        return False
    sheet = {}
    for a in _assign_read():
        sheet[_akey(a.get("date"), a.get("task"), a.get("assignee"))] = a.get("status") or "미착수"
    changed = False
    removed = []
    for t in keyed:
        st = sheet.get(t["akey"])
        if not st:
            continue
        if st == "삭제":
            removed.append(t["akey"])
            continue
        new_st = _ASSIGN_ST_MAP.get(st, "Not Started")
        if t.get("status") != new_st:
            t["status"] = new_st
            t["progress"] = _ASSIGN_PROG_MAP.get(st, 0)
            changed = True
    if removed:
        p["tasks"] = [t for t in (p.get("tasks") or []) if t.get("akey") not in removed]
        changed = True
    return changed


# ── 브리프 코멘트 (대표·리더 → 보고자 피드백 + 텔레그램 회신) ──
CMT_DIR = BRIEF_DIR / "comments"


def _load_comments(date_str):
    f = CMT_DIR / f"{date_str}.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_comments(date_str, arr):
    CMT_DIR.mkdir(parents=True, exist_ok=True)
    with _lock:
        (CMT_DIR / f"{date_str}.json").write_text(json.dumps(arr, ensure_ascii=False, indent=1), encoding="utf-8")


def _tg_chat_id(name):
    """직원명 → 텔레그램 chat_id (arisa-employees.json by_telegram_id 역매핑)."""
    for cid, nm in (load_emp().get("by_telegram_id", {}) or {}).items():
        if nm == name:
            return cid
    return None


def _brief_item_detail(date_str, item, src):
    """브리프 JSON에서 항목(title)+보고자 매칭 → 보고 원문(detail). 대표 브리프 → 팀 브리프 순."""
    def _cands(doc):
        out = list(doc.get("items") or []) + list(doc.get("decision_summary") or []) + list(doc.get("top5") or [])
        for t in (doc.get("teams") or []):
            out += list(t.get("top") or [])
        return out
    files = [BRIEF_DIR / f"daily-brief-{date_str}.json"] + sorted(BRIEF_DIR.glob(f"daily-brief-{date_str}-*.json"))
    for f in files:
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for c in _cands(doc):
            if not isinstance(c, dict):
                continue
            title = (c.get("title") or "").strip()
            if not title:
                continue
            if title != item and title not in item and item not in title:
                continue
            if src and (c.get("source_employee") or "").strip() not in ("", src):
                continue
            return (c.get("detail") or "").strip()
    return ""


def _report_raw_lookup(date_str, item, src):
    """일일보고 시트(SSOT)에서 담당자 보고 원문을 그대로 조회 — 축약 없음.
    메타 탭(요청한 결정 H·지원 요청 I·블로커 F·질문 L) 필드와 핵심업무 행 중
    항목과 토큰이 가장 겹치는 것을 반환. 겹침 2토큰 미만이면 '' (오매칭 방지)."""
    if not (_asgws and DAILY_SHEET and src):
        return ""
    try:
        from shared.normalize import normalize_date as _nd
    except Exception:
        _nd = lambda s: (s or "").strip()[:10]
    # 브리프는 전날 저녁 제출 보고로 만들어짐 — 브리프 날짜 + 직전 3영업일까지 조회
    dates = {date_str}
    try:
        d = datetime.date.fromisoformat(date_str)
        while len(dates) < 4:
            d -= datetime.timedelta(days=1)
            if d.weekday() < 5:
                dates.add(d.isoformat())
    except ValueError:
        pass
    toks = _proj_tokens(item)
    def _score(t):
        return len(toks & _proj_tokens(t))
    def _mine(r, width):
        r = list(r) + [""] * (width - len(r))
        return r if ((_nd(r[0]) or "") in dates and (r[1] or "").strip() == src) else None
    best_txt, best = "", 0
    try:
        meta = _asgws.values_get(DAILY_SHEET, "메타!A2:O5000", retries=2, timeout=20)
    except Exception:
        meta = []
    for r in meta:
        r = _mine(r, 15)
        if not r:
            continue
        for lab, txt in (("요청한 결정", r[7]), ("지원 요청", r[8]), ("블로커", r[5]), ("질문", r[11])):
            txt = (txt or "").strip()
            if txt and _score(txt) > best:
                best, best_txt = _score(txt), f"{lab}: {txt}"
    try:
        core = _asgws.values_get(DAILY_SHEET, "핵심업무!A2:L5000", retries=2, timeout=20)
    except Exception:
        core = []
    for r in core:
        r = _mine(r, 12)
        if not r:
            continue
        blob = " ".join([(r[5] or ""), (r[9] or ""), (r[10] or ""), (r[11] or "")])
        s = _score(blob)
        if s > best:
            parts = []
            if (r[5] or "").strip():
                parts.append(f"[업무] {r[5].strip()}")
            for lab, v in (("성과", r[11]), ("이슈", r[10]), ("산출물", r[9])):
                if (v or "").strip():
                    parts.append(f"{lab}: {v.strip()}")
            if parts:
                best, best_txt = s, "\n".join(parts)
    # 메타 raw(K열 — 보고 원문 전체)에서 블록 매칭: '['헤더/빈 줄로 블록 분리 후 최다 겹침 블록
    for r in meta:
        r = _mine(r, 15)
        if not r or not (r[10] or "").strip():
            continue
        block, blocks = [], []
        for ln in (r[10] or "").splitlines():
            if (ln.strip().startswith("[") or not ln.strip()) and block:
                blocks.append("\n".join(block)); block = []
            if ln.strip():
                block.append(ln.rstrip())
        if block:
            blocks.append("\n".join(block))
        for blk in blocks:
            s = _score(blk)
            if s > best:
                best, best_txt = s, blk.strip()
    # Basket 매장보고 시트 (송금·승인/구매 등 결재성 요청은 여기 기록됨)
    bsid = os.environ.get("BASKET_REPORT_SHEET_ID", "")
    if bsid:
        try:
            brows = _asgws.values_get(bsid, "일일보고!A2:O5000", retries=2, timeout=20)
        except Exception:
            brows = []
        blabs = {3: "매출", 4: "지출", 5: "송금·승인", 6: "특이사항", 7: "장비",
                 8: "업무보고", 9: "대관", 10: "스태프", 11: "구매", 12: "입점제안", 13: "복기"}
        for r in brows:
            r = list(r) + [""] * (15 - len(r))
            if (_nd(r[1]) or "") not in dates or (r[2] or "").strip() != src:
                continue
            for idx, lab in blabs.items():
                txt = (r[idx] or "").strip()
                if txt and _score(txt) > best:
                    best, best_txt = _score(txt), f"[매장보고 · {lab}] {txt}"
    return best_txt if best >= 2 else ""


def _brief_item_source(date_str, item, src):
    """담당자가 보고한 원문 — ① 일일보고 시트 원문 → ② 브리프 JSON people.core →
    ③ AI 요약 detail 순 폴백. 원문은 축약 없이 그대로."""
    raw = _report_raw_lookup(date_str, item, src)
    if raw:
        return raw
    toks_item = _proj_tokens(item)
    best, best_score, n_cands = None, 0, 0
    files = [BRIEF_DIR / f"daily-brief-{date_str}.json"] + sorted(BRIEF_DIR.glob(f"daily-brief-{date_str}-*.json"))
    for f in files:
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for p in (doc.get("people") or []):
            if src and (p.get("name") or "").strip() != src:
                continue
            for e in (p.get("core") or []):
                if not isinstance(e, dict):
                    continue
                n_cands += 1
                blob = " ".join(str(e.get(k) or "") for k in ("task", "issue", "detail", "outcome", "output"))
                score = len(toks_item & _proj_tokens(blob))
                if score > best_score:
                    best, best_score = e, score
    # 겹침 2토큰↑ 신뢰, 보고 행이 1건뿐이면 1토큰도 허용 (오매칭 방지)
    if best and (best_score >= 2 or (best_score >= 1 and n_cands == 1)):
        parts = []
        if (best.get("task") or "").strip():
            parts.append(f"[업무] {best['task'].strip()}")
        for lab, k in (("성과", "outcome"), ("이슈", "issue"), ("상세", "detail"), ("산출물", "output")):
            if (best.get(k) or "").strip():
                parts.append(f"{lab}: {best[k].strip()}")
        if parts:
            return "\n".join(parts)
    return _brief_item_detail(date_str, item, src)


def _tg_send(chat_id, text):
    """일일보고 봇으로 메시지 발송 — 실패해도 예외 없이 False (코멘트 저장은 유지)."""
    tok = os.environ.get("DAILY_REPORT_BOT_TOKEN", "")
    if not (tok and chat_id):
        return False
    import urllib.request
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{tok}/sendMessage",
            data=json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return bool(json.loads(r.read().decode()).get("ok"))
    except Exception:
        return False


# 브리프 페이지 주입용 코멘트 위젯 — .vz-item(제목+보고자) 단위로 코멘트 표시·입력.
# __DATE__ 는 서빙 시 해당 브리프 날짜로 치환. 세션은 셸이 심어둔 localStorage 키 재사용.
BRIEF_CMT_JS = """<script>(function(){
var DS='__DATE__', sess=null;
['brief_sess','team_brief_sess','pm_sess'].some(function(k){
  try{var s=JSON.parse(localStorage.getItem(k)||'null'); if(s&&s.name&&s.pin){sess=s;return true;}}catch(e){}
  return false;});
if(!sess) return;
function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function cline(c){return '<div style="color:var(--muted,#8A857E);padding:3px 0">💬 <b style="color:var(--fg,#eee)">'
  +esc(c.author)+'</b> '+esc(c.text)+' <span style="opacity:.6">'+esc(c.ts)+(c.tg_sent?' · TG✓':'')+'</span></div>';}
fetch('/api/brief-comments?user='+encodeURIComponent(sess.name)+'&date='+DS)
.then(function(r){return r.json();}).then(function(d){
  if(!d.ok) return;
  var by={};(d.comments||[]).forEach(function(c){var k=c.item+'|'+(c.src||'');(by[k]=by[k]||[]).push(c);});
  [].slice.call(document.querySelectorAll('.vz-item, .tb-chip')).forEach(function(el){
    var t=el.querySelector('.vz-t'), s=el.querySelector('.vz-src');
    if(!t) return;
    var item=t.textContent.trim(), src=s?s.textContent.trim():'';
    var wrap=document.createElement('div'); wrap.style.cssText='margin:2px 0 8px 22px;font-size:12px';
    var list=document.createElement('div'); wrap.appendChild(list);
    (by[item+'|'+src]||[]).forEach(function(c){ list.innerHTML+=cline(c); });
    var btn=document.createElement('a'); btn.textContent='💬 코멘트';
    btn.style.cssText='cursor:pointer;color:var(--accent,#6C5CE7);font-size:11px';
    btn.onclick=function(){
      if(wrap.querySelector('.bc-in')) return;
      var box=document.createElement('div'); box.className='bc-in'; box.style.cssText='display:flex;gap:6px;margin-top:4px';
      box.innerHTML='<input style="flex:1;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);'
        +'border-radius:6px;padding:6px 8px;color:inherit;font:inherit;font-size:12px" placeholder="코멘트 입력 — 등록 시 '
        +esc(src||'보고자')+' 텔레그램으로 회신">'
        +'<button style="background:var(--accent,#6C5CE7);border:0;border-radius:6px;color:#fff;padding:6px 12px;'
        +'font-size:12px;cursor:pointer">등록</button>';
      var inp=box.querySelector('input'), sb=box.querySelector('button');
      function go(){
        var v=inp.value.trim(); if(!v) return; sb.disabled=true;
        fetch('/api/brief-comment',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({user:sess.name,pin:sess.pin,date:DS,item:item,src:src,text:v})})
        .then(function(r){return r.json();}).then(function(d2){
          if(d2.ok){ box.remove(); list.innerHTML+=cline(d2.comment); }
          else{ sb.disabled=false; alert(d2.error||'등록 실패'); }
        }).catch(function(){ sb.disabled=false; alert('서버 오류'); });
      }
      sb.onclick=go; inp.onkeydown=function(e){ if(e.key==='Enter') go(); };
      wrap.appendChild(box); inp.focus();
    };
    wrap.appendChild(btn);
    el.parentNode.insertBefore(wrap, el.nextSibling);
  });
});
})();</script>"""


# ── 계정별 브리프 뷰 (/my-brief 직원 · /lead-brief 겸임리더) — 브리프 JSON 서버렌더 ──
_DBA = None

def _dba():
    """daily-brief-aggregate.py 모듈(하이픈 파일명) — 개인카드 렌더러 재사용."""
    global _DBA
    if _DBA is None:
        import importlib.util
        p = Path(__file__).resolve().parent / "daily-brief-aggregate.py"
        spec = importlib.util.spec_from_file_location("dba_mod", str(p))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _DBA = m
    return _DBA


# 브리프 카드 스타일 (daily-brief-aggregate.py 렌더와 동일 팔레트 — pp-*/as-*/tb-* 발췌)
# 셸(리더 홈)에도 주입되므로 페이지 골격(BRIEF_PAGE_CSS)과 분리.
BRIEF_CARD_CSS = """
.muted{color:var(--muted);font-size:12px}
.urg{font-size:11px;border-radius:5px;padding:2px 8px;white-space:nowrap;flex-shrink:0}
.urg-high{background:rgba(225,112,85,.16);color:var(--red);border:1px solid rgba(225,112,85,.4)}
.urg-mid{background:rgba(217,163,75,.14);color:var(--amber);border:1px solid rgba(217,163,75,.35)}
.urg-low{background:var(--bg-3);color:var(--muted);border:1px solid var(--line)}
.card{background:var(--bg-3);border:1px solid var(--line);border-radius:12px;padding:16px}
.pp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}
.pp-head{display:flex;align-items:center;gap:8px;margin-bottom:10px}
.pp-name{font-size:15px;font-weight:600}
.pp-team{font-size:11px;color:var(--accent);background:rgba(108,92,231,.12);border:1px solid rgba(108,92,231,.35);border-radius:5px;padding:1px 7px}
.pp-task{font-size:13px;line-height:1.5;margin-bottom:8px}
.pp-task .pt-out{display:block;font-size:12px;color:var(--muted);margin-top:2px;padding-left:18px}
.pp-task .pt-detail{display:block;font-size:12px;color:var(--fg);opacity:.85;line-height:1.6;margin-top:3px;padding-left:18px}
.pp-issue{font-size:12px;color:var(--amber);margin-top:2px;padding-left:18px}
.pp-meta{border-top:1px solid var(--line);margin-top:10px;padding-top:8px;font-size:12px;line-height:1.7}
.pp-meta .pm-red{color:var(--red)}
.pp-meta .pm-amber{color:var(--amber)}
.pp-asg{border-top:1px solid var(--line);margin-top:10px;padding-top:8px}
.as-label{font-size:11px;font-weight:600;color:var(--accent);margin-bottom:6px}
.as-item{display:flex;align-items:baseline;gap:7px;font-size:12px;line-height:1.55;margin-bottom:4px}
.as-st{font-size:10px;border-radius:4px;padding:1px 6px;white-space:nowrap;flex-shrink:0}
.as-todo{background:rgba(225,112,85,.14);color:var(--red);border:1px solid rgba(225,112,85,.35)}
.as-doing{background:rgba(217,163,75,.14);color:var(--amber);border:1px solid rgba(217,163,75,.35)}
.as-done{background:var(--bg-3);color:var(--muted);border:1px solid var(--line)}
.as-done + .as-task{text-decoration:line-through;color:var(--muted)}
.as-task{flex:1;min-width:0}
.as-dl{font-size:11px;color:var(--muted);white-space:nowrap}
.tb-block{background:var(--bg-2);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:16px}
.tb-head{font-size:15px;font-weight:600;display:flex;align-items:center;gap:10px;margin-bottom:8px}
.tb-head .cnt{margin-left:auto;color:var(--muted);font-size:12px;font-weight:400}
.tb-hl{font-size:13px;color:var(--muted);line-height:1.55;margin-bottom:10px}
.tb-chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.tb-chip{background:var(--bg-3);border:1px solid var(--line);border-radius:8px;padding:6px 10px;font-size:12px;display:inline-flex;align-items:center;gap:7px;line-height:1.4}
.lh-st{font-size:10px;border-radius:4px;padding:1px 6px;white-space:nowrap;margin-right:4px}
.lh-todo{background:rgba(225,112,85,.14);color:var(--red);border:1px solid rgba(225,112,85,.35)}
.lh-doing{background:rgba(217,163,75,.14);color:var(--amber);border:1px solid rgba(217,163,75,.35)}
.lh-done{background:var(--bg-3);color:var(--muted);border:1px solid var(--line)}
.lh-proj{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:13px 15px;margin-bottom:8px;cursor:pointer}
.lh-proj:hover{border-color:var(--accent)}
.lh-proj .t{font-size:14px;font-weight:500}
.lh-proj .m{font-size:12px;color:var(--muted);margin-top:3px}
.rc-card{border-left:3px solid var(--accent)}
.ex-red{border-left:3px solid var(--red, #E17055)}
.ex-amber{border-left:3px solid var(--amber, #D9A34B)}
.rc-btn{float:right;background:rgba(108,92,231,.12);border:1px solid rgba(108,92,231,.4);color:var(--accent);border-radius:7px;padding:4px 11px;font-size:11px;font-weight:600;cursor:pointer;font-family:inherit;margin-left:10px}
.rc-btn:hover{background:var(--accent);color:#fff}
"""

BRIEF_PAGE_CSS = """
:root{--bg:#1A1A1A;--bg-2:#202020;--bg-3:#262626;--fg:#F5F0EB;--muted:#8A857E;--line:#333;
--accent:#6C5CE7;--green:#8FA37E;--amber:#D9A34B;--red:#E17055;--blue:#6F8AA3}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:'Pretendard Variable',sans-serif;font-weight:300;line-height:1.5;padding:32px 20px 64px}
.wrap{max-width:1100px;margin:0 auto}
header h1{font-weight:600;font-size:24px;letter-spacing:-.02em}
header .sub{color:var(--muted);margin-top:4px;font-size:13px}
#bv-gate{position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:100}
#bv-box{background:var(--bg-2);border:1px solid var(--line);border-radius:14px;padding:38px 40px;width:330px;text-align:center}
#bv-box h2{font-size:19px;font-weight:600;margin-bottom:6px}
#bv-box .lg-sub{color:var(--muted);font-size:13px;margin-bottom:22px}
#bv-box input{width:100%;background:var(--bg-3);border:1px solid var(--line);border-radius:8px;padding:12px 14px;color:var(--fg);font-size:14px;margin-bottom:10px;font-family:inherit}
#bv-box button{width:100%;background:var(--accent);color:#fff;border:0;border-radius:8px;padding:12px;font-size:14px;font-weight:600;cursor:pointer;margin-top:6px}
#bv-err{color:var(--red);font-size:12px;margin-top:12px;min-height:16px}
"""


def _brief_json(date_str, team):
    """daily-brief-{date}-{team}.json 로드 (없으면 None)."""
    p = BRIEF_DIR / f"daily-brief-{date_str}-{team}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _brief_biz_dates(team):
    """해당 팀 브리프 JSON이 존재하는 영업일 목록(오름차순)."""
    pat = re.compile(r"daily-brief-(\d{4}-\d{2}-\d{2})-" + re.escape(team) + r"$")
    out = []
    for f in sorted(BRIEF_DIR.glob(f"daily-brief-2*-{team}.json")):
        m = pat.fullmatch(f.stem)
        if not m:
            continue
        try:
            if datetime.datetime.strptime(m.group(1), "%Y-%m-%d").weekday() < 5:
                out.append(m.group(1))
        except ValueError:
            pass
    return out


def _brief_nav(base_url, dates, sel):
    """최근 7영업일 날짜 버튼 nav — 기존 /brief 패턴과 동일 스타일."""
    wk = ["월", "화", "수", "목", "금", "토", "일"]
    btns = []
    for ds in dates[-7:]:
        d = datetime.datetime.strptime(ds, "%Y-%m-%d")
        lab = f"{wk[d.weekday()]} {d.strftime('%m/%d')}"
        on = "background:var(--accent);color:#fff;border-color:var(--accent)" if ds == sel else "color:var(--muted)"
        btns.append(f'<a href="{base_url}&date={ds}" style="text-decoration:none;border:1px solid var(--line);'
                    f'border-radius:7px;padding:5px 12px;font-size:12px;{on}">{lab}</a>')
    return ('<div style="display:flex;gap:6px;margin:0 0 18px;align-items:center;flex-wrap:wrap">'
            '<span style="color:var(--muted);font-size:11px;margin-right:4px">최근 영업일</span>'
            + "".join(btns) + '</div>')


def _team_block_html(dba, td, only_person=None, chips_max=3):
    """팀 브리프 JSON → 팀 블록 HTML. only_person 지정 시 그 사람 카드만(직원 뷰)."""
    esc = dba._esc
    hl = f'<div class="tb-hl">{esc(td.get("headline") or "")}</div>' if td.get("headline") else ""
    chips = ""
    tops = (td.get("top5") or [])[:chips_max]
    if tops:
        cs = []
        for it in tops:
            col = dba.CAT_META.get(it.get("category"), ("", "var(--accent)"))[1]
            src = esc(it.get("source_employee") or "")
            cs.append(f'<span class="tb-chip" style="border-left:3px solid {col}">'
                      f'{dba._urg_badge(it.get("urgency", "low"))}<span class="vz-t">{esc(it.get("title", ""))}</span>'
                      + (f' <span class="vz-src" style="color:var(--muted);font-size:11px">{src}</span>' if src else "")
                      + '</span>')
        chips = f'<div class="tb-chips">{"".join(cs)}</div>'
    people = td.get("people") or []
    if only_person is not None:
        people = [p for p in people if p.get("name") == only_person]
    cards = (f'<div class="pp-grid">{"".join(dba._person_card(p) for p in people)}</div>'
             if people else "")
    return hl, chips, cards


def _brief_view_page(title, h1, sub, body, allow_js, deny_msg):
    """계정별 브리프 뷰 공통 페이지 — 셸 프리셋 세션(pm_sess) 게이트 + 자체 로그인 폴백.
    allow_js: 세션 객체 s를 받아 허용 여부를 리턴하는 JS 표현식 (예: "s.name===NAME||s.admin")"""
    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>{BRIEF_PAGE_CSS}{BRIEF_CARD_CSS}</style></head>
<body>
<div id="bv-gate"><div id="bv-box">
  <h2>{h1}</h2><div class="lg-sub">{sub}</div>
  <input id="bv-id" placeholder="이름" autocomplete="username">
  <input id="bv-pin" type="password" placeholder="PIN" autocomplete="current-password">
  <button id="bv-btn">로그인</button><div id="bv-err"></div>
</div></div>
<div id="content" style="display:none"><div class="wrap">
<header><h1>{h1}</h1><div class="sub">{sub}</div></header>
{body}
</div></div>
<script>
(function(){{
  var gate=document.getElementById('bv-gate'), content=document.getElementById('content');
  function allowed(s){{ return !!(s && ({allow_js})); }}
  function enter(){{ gate.style.display='none'; content.style.display='block'; }}
  var s=null;
  ['pm_sess','brief_sess','team_brief_sess'].some(function(k){{
    try{{ var v=JSON.parse(localStorage.getItem(k)||'null'); if(v&&v.name){{ s=v; return true; }} }}catch(e){{}} return false;
  }});
  if(allowed(s)){{ enter(); return; }}
  if(s){{ document.getElementById('bv-err').textContent={deny_msg!r}; }}
  function doLogin(){{
    var id=document.getElementById('bv-id').value.trim(), pin=document.getElementById('bv-pin').value.trim();
    var err=document.getElementById('bv-err'); err.textContent='';
    fetch('/api/login',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{id:id,pin:pin}})}})
      .then(function(r){{return r.json();}})
      .then(function(d){{
        if(d.ok && allowed(d)){{ localStorage.setItem('pm_sess',JSON.stringify(Object.assign({{}},d,{{id:id,pin:pin}}))); enter(); }}
        else if(d.ok){{ err.textContent={deny_msg!r}; }}
        else {{ err.textContent=d.error||'로그인 실패'; }}
      }}).catch(function(){{ err.textContent='서버 연결 실패'; }});
  }}
  document.getElementById('bv-btn').onclick=doLogin;
  document.getElementById('bv-pin').addEventListener('keydown',function(e){{ if(e.key==='Enter') doLogin(); }});
}})();
</script>
</body></html>"""

def project_teams(p):
    """프로젝트에 걸린 팀 집합 = PM + 멤버들의 소속 팀."""
    people = list(p.get("members") or [])
    if p.get("pm"): people.append(p["pm"])
    return {t for t in (emp_team(x) for x in people) if t}

def can_manage(uid, p):
    """멤버 배정 권한: 대표 / 담당 PM / (본인 리더팀이 이 프로젝트에 걸린) 팀 리더."""
    if is_admin(uid) or uid == p.get("pm"):
        return True
    return bool(set(lead_teams_of(uid)) & project_teams(p))

def can_view(uid, p):
    # 리더는 '본인 팀이 걸린' 프로젝트를 멤버가 아니어도 열람(멤버 배정 위해)
    return is_admin(uid) or uid == p.get("pm") or uid in (p.get("members") or []) or can_manage(uid, p)

def can_edit(uid, p):
    # 내용(업무·이슈·브리프) 편집은 기존대로 담당 PM·대표만 — 리더는 멤버 배정만
    return is_admin(uid) or uid == p.get("pm")

class H(BaseHTTPRequestHandler):
    server_version = "PRDashboard/1.0"
    def log_message(self, *a): pass

    def _proxy_arisa2(self, method="GET"):
        """리버스 프록시: /arisa2/* → ARISA2_UPSTREAM (stdlib only)."""
        # /arisa2/foo → /foo 로 변환 (/arisa2 자체는 / 로)
        upstream_path = self.path[len("/arisa2"):] or "/"
        url = ARISA2_UPSTREAM + upstream_path
        body = None
        if method in ("POST", "PUT", "PATCH"):
            n = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(n) if n else b""
        headers = {}
        for h in ("Content-Type", "Authorization"):  # Bearer 토큰 전달(ARISA 2.0 인증)
            v = self.headers.get(h)
            if v:
                headers[h] = v
        try:
            req = Request(url, data=body, headers=headers, method=method)
            with urlopen(req, timeout=30) as resp:
                resp_body = resp.read()
                ctype = resp.headers.get("Content-Type", "application/octet-stream")
                if "text/html" in ctype:
                    # SPA의 API 베이스를 프록시 프리픽스로 재작성 → /arisa2/api/* 로 호출
                    resp_body = resp_body.replace(b"var API='';", b"var API='/arisa2';")
                self.send_response(resp.status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(resp_body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(resp_body)
        except HTTPError as e:
            # upstream이 4xx/5xx를 반환해도 상태·본문 그대로 전달(401 인증게이트 = 서버 살아있음)
            resp_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json; charset=utf-8"))
            self.send_header("Content-Length", str(len(resp_body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(resp_body)
        except URLError:
            err = b'{"ok":false,"error":"ARISA 2.0 unavailable"}'
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n: return {}
        try: return json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception: return {}

    def do_GET(self):
        u = urlparse(self.path); path = u.path; q = parse_qs(u.query)
        if path.startswith("/arisa2"):
            return self._proxy_arisa2("GET")
        if path in ("/", "/index.html"):
            # 통합 셸 — 로그인 1회, 역할별 탭(프로젝트/Brief/Weekly/Decision)
            # 리더 홈(팀 Todo·팀원 보고 카드)이 브리프 카드 스타일을 쓰므로 CARD_CSS 주입
            html = UNIFIED_SHELL.replace("</style>", BRIEF_CARD_CSS + "</style>", 1)
            return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/projects":
            # 포트폴리오 HTML (구 / 핸들러) — 셸 iframe 또는 직접 접속(자체 로그인)
            try:
                html = HTML.read_text(encoding="utf-8")
            except Exception:
                return self._send(500, "<h1>대시보드 파일이 없습니다. generate-portfolio.py 실행 필요</h1>".encode("utf-8"), "text/html; charset=utf-8")
            inject = "<script>window.SERVED=true;window.API_BASE='/api';</script>\n</head>"
            html = html.replace("</head>", inject, 1)
            return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        if path in ("/dashboard", "/team"):
            # 구 대표/리더 셸 → 통합 셸로 (기존 알림 링크 호환)
            self.send_response(301)
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if path == "/weekly":
            # 로그인은 HTML 내장 JS가 /api/login으로 처리. 성장지표(.growth)는 admin(대표)만
            # CSS로 노출(직원 로그인 시 숨김 — 측정설계 v2). 서버는 최신 HTML만 서빙.
            # 날짜 형식만 매칭(팀 suffix 파일 `…-W26-공간팀.html` 격리)
            files = sorted(f for f in WEEKLY_DIR.glob("weekly-report-2*.html")
                           if re.fullmatch(r"weekly-report-\d{4}-W\d{2}", f.stem))
            if not files:
                return self._send(404, "<h1>주간 대시보드가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            return self._send(200, files[-1].read_text(encoding="utf-8").encode("utf-8"), "text/html; charset=utf-8")
        if path == "/brief":
            # 대표 Daily Brief — 로그인은 HTML 내장 JS가 /api/login으로 처리(대표 admin만 입장).
            # 날짜 네비: 업무 맥락 위해 오늘 + 직전 3영업일(주말 제외)을 버튼으로 주입. ?date=로 전환.
            # 날짜 형식만 매칭(팀 suffix 파일 `…-06-30-공간팀.html` 격리)
            files = sorted(f for f in BRIEF_DIR.glob("daily-brief-2*.html")
                           if re.fullmatch(r"daily-brief-\d{4}-\d{2}-\d{2}", f.stem))
            if not files:
                return self._send(404, "<h1>오늘 브리프가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            biz = []  # 영업일 brief 날짜(월~금)
            for f in files:
                ds = f.stem.replace("daily-brief-", "")
                try:
                    if datetime.datetime.strptime(ds, "%Y-%m-%d").weekday() < 5:
                        biz.append(ds)
                except ValueError:
                    pass
            recent = biz[-7:]  # 오늘 + 직전 6영업일 (최근 일주일 이력)
            sel = (q.get("date") or [""])[0]
            target = BRIEF_DIR / f"daily-brief-{sel}.html"
            if not (sel and target.exists()):
                target = files[-1]
                sel = files[-1].stem.replace("daily-brief-", "")
            wk = ["월", "화", "수", "목", "금", "토", "일"]
            btns = []
            for ds in recent:
                d = datetime.datetime.strptime(ds, "%Y-%m-%d")
                lab = f"{wk[d.weekday()]} {d.strftime('%m/%d')}"
                on = "background:var(--accent);color:#fff;border-color:var(--accent)" if ds == sel else "color:var(--muted)"
                btns.append(f'<a href="/brief?date={ds}" style="text-decoration:none;border:1px solid var(--line);'
                            f'border-radius:7px;padding:5px 12px;font-size:12px;{on}">{lab}</a>')
            nav = ('<div style="display:flex;gap:6px;margin:0 0 18px;align-items:center">'
                   '<span style="color:var(--muted);font-size:11px;margin-right:4px">최근 영업일</span>'
                   + "".join(btns) + '</div>')
            html = target.read_text(encoding="utf-8").replace("</header>", "</header>" + nav, 1)
            html = html.replace("</body>", BRIEF_CMT_JS.replace("__DATE__", sel) + "</body>", 1)
            return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/team-brief":
            # 팀 Brief — 로그인은 셸이 처리(team_brief_sess). team별 파일 + 날짜네비.
            team = (q.get("team") or [""])[0]
            if not team:
                return self._send(400, "<h1>team 파라미터가 필요합니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            pre = "daily-brief-"
            pat = re.compile(r"daily-brief-\d{4}-\d{2}-\d{2}-" + re.escape(team) + r"$")
            files = sorted(f for f in BRIEF_DIR.glob(f"daily-brief-2*-{team}.html") if pat.fullmatch(f.stem))
            if not files:
                return self._send(404, f"<h1>{team} 팀 브리프가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            def _ds(f):  # stem에서 날짜부분(YYYY-MM-DD) 추출
                return f.stem[len(pre):-(len(team) + 1)]
            biz = []
            for f in files:
                ds = _ds(f)
                try:
                    if datetime.datetime.strptime(ds, "%Y-%m-%d").weekday() < 5:
                        biz.append(ds)
                except ValueError:
                    pass
            recent = biz[-7:]  # 최근 일주일 이력 (팀)
            sel = (q.get("date") or [""])[0]
            target = BRIEF_DIR / f"daily-brief-{sel}-{team}.html"
            if not (sel and target.exists()):
                target = files[-1]
                sel = _ds(files[-1])
            wk = ["월", "화", "수", "목", "금", "토", "일"]
            btns = []
            for ds in recent:
                d = datetime.datetime.strptime(ds, "%Y-%m-%d")
                lab = f"{wk[d.weekday()]} {d.strftime('%m/%d')}"
                on = "background:var(--accent);color:#fff;border-color:var(--accent)" if ds == sel else "color:var(--muted)"
                btns.append(f'<a href="/team-brief?team={quote(team)}&date={ds}" style="text-decoration:none;border:1px solid var(--line);'
                            f'border-radius:7px;padding:5px 12px;font-size:12px;{on}">{lab}</a>')
            nav = ('<div style="display:flex;gap:6px;margin:0 0 18px;align-items:center">'
                   '<span style="color:var(--muted);font-size:11px;margin-right:4px">최근 영업일</span>'
                   + "".join(btns) + '</div>')
            html_str = target.read_text(encoding="utf-8").replace("</header>", "</header>" + nav, 1)
            html_str = html_str.replace("</body>", BRIEF_CMT_JS.replace("__DATE__", sel) + "</body>", 1)
            return self._send(200, html_str.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/my-brief":
            # 직원용 개인 브리프 — 내 카드(상세+분장) + 팀 헤드라인·핵심칩만 (동료 카드 비공개).
            name = (q.get("name") or [""])[0]
            if not name:
                return self._send(400, "<h1>name 파라미터가 필요합니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            team = emp_team(name) or ""
            try:
                dba = _dba()
            except Exception as e:
                return self._send(500, f"<h1>브리프 렌더러 로드 실패: {e}</h1>".encode("utf-8"), "text/html; charset=utf-8")
            dates = _brief_biz_dates(team) if team else []
            if not dates:
                body = '<div class="muted">아직 생성된 팀 브리프가 없습니다.</div>'
                page = _brief_view_page(f"내 브리프 · {name}", "내 오늘 브리프",
                                        f"{name} · {team or '팀 미배정'}", body,
                                        f"s.name==={json.dumps(name, ensure_ascii=False)}||s.admin",
                                        "본인 전용 화면입니다")
                return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            sel = (q.get("date") or [""])[0]
            if sel not in dates:
                sel = dates[-1]
            td = _brief_json(sel, team) or {}
            hl, chips, cards = _team_block_html(dba, td, only_person=name)
            if not cards:
                cards = ('<div class="card"><div class="muted">이 날짜에 제출한 보고가 없습니다. '
                         '저녁 20:00·22:00 리마인드에 맞춰 보고하면 다음날 아침 브리프에 반영됩니다.</div></div>')
            nav = _brief_nav(f"/my-brief?name={quote(name)}", dates, sel)
            body = (nav + f'<div class="tb-block"><div class="tb-head">{dba._esc(team)}'
                    f'<span class="cnt">{dba._esc(sel)}</span></div>{hl}{chips}{cards}</div>')
            page = _brief_view_page(f"내 브리프 · {name}", "내 오늘 브리프",
                                    f"{name} · {team}", body,
                                    f"s.name==={json.dumps(name, ensure_ascii=False)}||s.admin",
                                    "본인 전용 화면입니다")
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/lead-brief":
            # 겸임 리더용 — 담당팀들을 한 페이지로 병합 (팀 headline+핵심칩+개인카드 전체).
            teams_p = (q.get("teams") or [""])[0]
            teams = [t.strip() for t in teams_p.split(",") if t.strip()]
            if not teams:
                return self._send(400, "<h1>teams 파라미터가 필요합니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            try:
                dba = _dba()
            except Exception as e:
                return self._send(500, f"<h1>브리프 렌더러 로드 실패: {e}</h1>".encode("utf-8"), "text/html; charset=utf-8")
            all_dates = sorted(set().union(*[set(_brief_biz_dates(t)) for t in teams]))
            if not all_dates:
                return self._send(404, "<h1>팀 브리프가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            sel = (q.get("date") or [""])[0]
            if sel not in all_dates:
                sel = all_dates[-1]
            blocks = []
            for t in teams:
                td = _brief_json(sel, t)
                if not td:
                    blocks.append(f'<div class="tb-block"><div class="tb-head">{_dba()._esc(t)}</div>'
                                  '<div class="muted">이 날짜 브리프 없음</div></div>')
                    continue
                hl, chips, cards = _team_block_html(dba, td)
                if not cards:
                    cards = '<div class="muted">오늘 보고 없음</div>'
                blocks.append(f'<div class="tb-block"><div class="tb-head">{dba._esc(t)}'
                              f'<span class="cnt">보고 {td.get("active_people", 0)}명</span></div>{hl}{chips}{cards}</div>')
            nav = _brief_nav(f"/lead-brief?teams={quote(teams_p)}", all_dates, sel)
            teams_js = json.dumps(teams, ensure_ascii=False)
            allow = f"(s.admin || {teams_js}.every(function(t){{return (s.lead_teams||[]).indexOf(t)>=0;}}))"
            page = _brief_view_page(f"팀 Brief · {' · '.join(teams)}", f"{' · '.join(teams)} 오늘 브리프",
                                    f"{sel} · 팀 리더", nav + "".join(blocks), allow,
                                    "담당 팀 리더 전용 화면입니다")
            page = page.replace("</body>", BRIEF_CMT_JS.replace("__DATE__", sel) + "</body>", 1)
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/team-weekly":
            # 팀 주간 — 로그인은 셸이 처리(team_weekly_sess). team별 최신 파일.
            team = (q.get("team") or [""])[0]
            if not team:
                return self._send(400, "<h1>team 파라미터가 필요합니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            pat = re.compile(r"weekly-report-\d{4}-W\d{2}-" + re.escape(team) + r"$")
            files = sorted(f for f in WEEKLY_DIR.glob(f"weekly-report-2*-{team}.html") if pat.fullmatch(f.stem))
            if not files:
                return self._send(404, f"<h1>{team} 팀 주간이 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            return self._send(200, files[-1].read_text(encoding="utf-8").encode("utf-8"), "text/html; charset=utf-8")
        if path == "/simulator":
            return self._send(200, SIMULATOR_HTML.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/guide":
            # 일일업무보고 가이드 — 직원 열람용(무인증, 공개).
            gp = _WS / "20-operations" / "23-arisa" / "guide" / "daily-report-guide.html"
            if not gp.exists():
                return self._send(404, "<h1>가이드가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            return self._send(200, gp.read_text(encoding="utf-8").encode("utf-8"), "text/html; charset=utf-8")
        if path == "/guide-os":
            # ARISA OS 통합 사용 가이드 (무인증, 공개)
            gp = _WS / "20-operations" / "23-arisa" / "guide" / "arisa-os-guide.html"
            if not gp.exists():
                return self._send(404, "<h1>가이드가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            return self._send(200, gp.read_text(encoding="utf-8").encode("utf-8"), "text/html; charset=utf-8")
        if path == "/guide-flow":
            # 업무분장 플로우 구조도 (무인증, 공개)
            gp = _WS / "20-operations" / "23-arisa" / "assignment-flow-구조도.html"
            if not gp.exists():
                return self._send(404, "<h1>구조도가 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            return self._send(200, gp.read_text(encoding="utf-8").encode("utf-8"), "text/html; charset=utf-8")
        if path == "/guide/template.xlsx":
            # 주간업무계획 템플릿 다운로드
            gp = _WS / "20-operations" / "23-arisa" / "guide" / "주간업무계획_템플릿.xlsx"
            if not gp.exists():
                return self._send(404, "<h1>템플릿이 아직 없습니다.</h1>".encode("utf-8"), "text/html; charset=utf-8")
            data = gp.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", "attachment; filename*=UTF-8''%EC%A3%BC%EA%B0%84%EC%97%85%EB%AC%B4%EA%B3%84%ED%9A%8D_%ED%85%9C%ED%94%8C%EB%A6%BF.xlsx")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/health":
            return self._send(200, {"ok": True})
        if path == "/api/assignees":
            # 계층적 분장 후보 — 대표=리더급에게만, 리더=자기 팀원에게만
            uid = (q.get("user") or [""])[0]
            emp = load_emp().get("by_name", {})
            tl = load_emp().get("team_leads", {})
            if is_admin(uid):
                lead_team = {}
                for team, ldr in tl.items():
                    lead_team.setdefault(ldr, []).append(team)
                data = [{"name": n, "team": "·".join(lead_team[n])} for n in sorted(lead_team.keys())]
                if uid not in lead_team:  # 대표 본인도 담당자 후보(직접 챙기는 업무)
                    data.insert(0, {"name": uid, "team": emp_team(uid) or "경영"})
                level = "리더"
            else:
                my = set(lead_teams_of(uid))
                data = [{"name": n, "team": (v or {}).get("team", "")} for n, v in sorted(emp.items())
                        if (v or {}).get("team") in my]
                level = "팀원"
            return self._send(200, {"ok": True, "canAssign": is_admin(uid) or is_leader(uid),
                                    "level": level, "assignees": data})
        if path == "/api/my-work":
            # 개인 대시보드 — 내 분장(미완) + 내 프로젝트 일정(owner)
            uid = (q.get("user") or [""])[0]
            mine = [a for a in _assign_read() if a["assignee"] == uid and a["status"] not in _ASSIGN_HIDDEN_STATES]
            mine.sort(key=lambda a: (a["status"] == "완료", a["status"] != "진행중", a.get("deadline") or "9999"))
            projs = []
            for p in load_projects():
                ts = [t for t in (p.get("tasks") or []) if t.get("owner") == uid
                      and (t.get("status") or "") not in _TASK_DONE_STATES]
                if ts:
                    projs.append({"id": p.get("id"), "name": p.get("name"), "dday": p.get("dday"),
                                  "tasks": [{"task": t.get("task"), "start": t.get("start"), "end": t.get("end"),
                                             "status": t.get("status"), "priority": t.get("priority"),
                                             "division": t.get("division")} for t in ts]})
            return self._send(200, {"ok": True, "user": uid, "assignments": mine, "projects": projs})
        if path == "/api/exec-attn":
            # 대표창 — 지연 업무(마감 경과·미완료 분장) + 결재·확인 필요(미해결 결정)
            uid = (q.get("user") or [""])[0]
            if not is_admin(uid):
                return self._send(403, {"ok": False, "error": "대표 전용"})
            today = datetime.date.today()
            reg_cut = today - datetime.timedelta(days=30)
            overdue, seen = [], set()
            approvals = []
            for a in _assign_read():
                st = (a.get("status") or "미착수")
                if st == "완료":
                    approvals.append(a)   # 승인 대기 큐 (대표 승인용)
                if st in _ASSIGN_DONE_STATES or st == "삭제":
                    continue
                dl = (a.get("deadline") or "").strip()[:10]
                try:
                    dld = datetime.date.fromisoformat(dl)
                except ValueError:
                    continue
                if dld >= today:
                    continue
                ds = (a.get("date") or "").strip()[:10]
                try:
                    if datetime.date.fromisoformat(ds) < reg_cut:
                        continue
                except ValueError:
                    pass
                key = (a.get("project"), a.get("task"), a.get("assignee"), dl)
                if key in seen:
                    continue
                seen.add(key)
                a = dict(a)
                a["days_overdue"] = (today - dld).days
                overdue.append(a)
            overdue.sort(key=lambda x: -x["days_overdue"])
            # 결재·확인 필요 — 미해결 결정 이월 로그 + 최신 브리프 decision_summary 병합
            decisions, titles = [], set()
            if _load_open_decisions:
                try:
                    for d in _load_open_decisions(14):
                        t = (d.get("decision_needed") or "").strip()
                        if t and t not in titles:
                            titles.add(t)
                            decisions.append({"title": t, "who": d.get("source_employee") or "",
                                              "project": d.get("project") or "",
                                              "age": d.get("age_days", 0)})
                except Exception:
                    pass
            try:
                bfiles = sorted(f for f in BRIEF_DIR.glob("daily-brief-2*.json")
                                if re.fullmatch(r"daily-brief-\d{4}-\d{2}-\d{2}", f.stem))
                if bfiles:
                    bd = json.loads(bfiles[-1].read_text(encoding="utf-8"))
                    for it in bd.get("decision_summary") or []:
                        t = (it.get("title") or "").strip()
                        if t and t not in titles:
                            titles.add(t)
                            proj = (it.get("project") or "")
                            proj = "" if str(proj).lower() in ("none", "null") else proj
                            decisions.append({"title": t, "who": it.get("source_employee") or "",
                                              "project": proj, "age": 0})
            except Exception:
                pass
            return self._send(200, {"ok": True, "overdue": overdue, "decisions": decisions,
                                    "approvals": approvals})
        if path == "/api/lead-home":
            # 리더 홈 — 팀 Todo(이번주 분장) + 진행중 프로젝트 + 팀원 오늘 보고 카드(HTML fragment)
            uid = (q.get("user") or [""])[0]
            if not load_users().get(uid):
                return self._send(401, {"ok": False, "error": "unknown user"})
            teams = lead_teams_of(uid)
            if not teams:
                return self._send(403, {"ok": False, "error": "리더 전용"})
            today = datetime.date.today()
            # 2주 윈도우(지난주 월~이번주 일) — 주 바뀐 직후 미완료 분장이 사라지는 문제 방지
            ws = today - datetime.timedelta(days=today.weekday() + 7)
            we = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=6)
            assigns = []
            approvals = []
            for a in _assign_read():
                # 승인 대기(완료)는 날짜 무관 전체 — 리더 승인 큐
                if (a.get("status") or "") == "완료" and (a.get("team") in teams or emp_team(a.get("assignee")) in teams):
                    approvals.append(a)
                ds = (a.get("date") or "").strip()[:10]
                try:
                    d = datetime.date.fromisoformat(ds)
                except ValueError:
                    continue
                if not (ws <= d <= we):
                    continue
                if a.get("status") in _ASSIGN_HIDDEN_STATES:
                    continue
                if a.get("team") in teams or emp_team(a.get("assignee")) in teams:
                    assigns.append(a)
            assigns.sort(key=lambda a: (a["status"] == "완료", a["status"] != "진행중",
                                        a.get("deadline") or "9999", a.get("assignee") or ""))
            projs = []
            for p in load_projects():
                if not (project_teams(p) & set(teams)):
                    continue
                tasks = p.get("tasks") or []
                done = sum(1 for t in tasks if (t.get("status") or "") in _TASK_DONE_STATES)
                end = (p.get("end") or p.get("dday") or "").strip()
                if end and end < today.isoformat():
                    continue  # 종료된 프로젝트 제외
                projs.append({"id": p.get("id"), "name": p.get("name"), "pm": p.get("pm"),
                              "dday": p.get("dday"), "task_done": done, "task_total": len(tasks)})
            projs.sort(key=lambda p: p.get("dday") or "9999")
            brief_html, brief_date = "", ""
            try:
                dba = _dba()
                for t in teams:
                    ds = _brief_biz_dates(t)
                    if ds and ds[-1] > brief_date:
                        brief_date = ds[-1]
                blocks = []
                for t in teams:
                    td = _brief_json(brief_date, t) if brief_date else None
                    if not td:
                        continue
                    hl, chips, cards = _team_block_html(dba, td)
                    if not cards:
                        cards = '<div class="muted">이 날짜 팀 보고 없음</div>'
                    blocks.append(f'<div class="tb-block"><div class="tb-head">{dba._esc(t)}'
                                  f'<span class="cnt">보고 {td.get("active_people", 0)}명</span></div>{hl}{chips}{cards}</div>')
                brief_html = "".join(blocks)
            except Exception as e:
                brief_html = f'<div class="muted">보고 로드 실패: {e}</div>'
            return self._send(200, {"ok": True, "teams": teams, "assignments": assigns,
                                    "projects": projs, "approvals": approvals,
                                    "brief_html": brief_html, "brief_date": brief_date})
        if path == "/api/projects":
            uid = (q.get("user") or [""])[0]
            if not load_users().get(uid): return self._send(401, {"ok": False, "error": "unknown user"})
            vis = []
            for p in load_projects():
                if can_view(uid, p):
                    q = dict(p); q["canManage"] = can_manage(uid, p); q["canEdit"] = can_edit(uid, p)
                    vis.append(q)
            return self._send(200, {"ok": True, "projects": vis, "admin": is_admin(uid),
                                    "canCreate": is_admin(uid) or is_leader(uid)})
        if path == "/api/project":
            uid = (q.get("user") or [""])[0]; pid = (q.get("id") or [""])[0]
            p = get_project(pid)
            if not p: return self._send(404, {"ok": False, "error": "not found"})
            if not can_view(uid, p): return self._send(403, {"ok": False, "error": "forbidden"})
            if _sync_assign_status(p): save_project(p)  # 분장 시트(SSOT) 상태 lazy 반영
            return self._send(200, {"ok": True, "project": p, "canEdit": can_edit(uid, p), "canManage": can_manage(uid, p),
                                    "assignments": _project_assignments(p.get("name") or "", p.get("aliases"))})
        if path == "/api/brief-comments":
            uid = (q.get("user") or [""])[0]
            if not load_users().get(uid): return self._send(401, {"ok": False, "error": "unknown user"})
            ds = (q.get("date") or [""])[0]
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", ds): return self._send(400, {"ok": False, "error": "date 형식"})
            return self._send(200, {"ok": True, "comments": _load_comments(ds)})
        return self._send(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path.startswith("/arisa2"):
            return self._proxy_arisa2("POST")
        b = self._body()
        if path == "/api/login":
            uid = b.get("id", ""); pin = b.get("pin", "")
            users = load_users()
            u = users.get(uid)
            if not u: return self._send(401, {"ok": False, "error": "등록되지 않은 이름입니다."})
            cur = str(u.get("pin") or "")
            pin_set = False
            if cur == "":
                # PIN 미설정 → 첫 로그인 시 본인이 설정
                if len(str(pin)) < 4:
                    return self._send(400, {"ok": False, "error": "첫 로그인입니다. PIN을 4자 이상으로 설정해주세요."})
                set_pin(uid, pin); pin_set = True
            elif cur != str(pin):
                return self._send(401, {"ok": False, "error": "ID 또는 PIN이 올바르지 않습니다."})
            return self._send(200, {"ok": True, "name": uid, "role": u.get("role", "직원"),
                                    "admin": is_admin(uid), "lead_teams": lead_teams_of(uid), "pin_set": pin_set})
        if path == "/api/set-pin":
            # PIN 변경(자가설정) — 현재 PIN 검증 후 새 PIN 저장
            uid = b.get("id", ""); cur = b.get("pin", ""); new = b.get("new_pin", "")
            if not auth(uid, cur): return self._send(401, {"ok": False, "error": "현재 PIN이 올바르지 않습니다."})
            if len(str(new)) < 4: return self._send(400, {"ok": False, "error": "새 PIN은 4자 이상이어야 합니다."})
            set_pin(uid, new)
            return self._send(200, {"ok": True})
        if path == "/api/simulator/review":
            sim_mode = b.get("mode", "daily")
            fields = b.get("fields") or {}
            if not any((fields.get(k) or "").strip() for k in fields):
                return self._send(400, {"ok": False, "error": "최소 1개 항목을 입력해주세요."})
            prompt = SIMULATOR_BRIEF_PROMPT if sim_mode == "brief" else SIMULATOR_DAILY_PROMPT
            user_msg = _build_simulator_input(sim_mode, fields)
            result = _call_claude(prompt, user_msg)
            if not result:
                return self._send(500, {"ok": False, "error": "AI 리뷰에 실패했습니다. API 키를 확인하세요."})
            return self._send(200, {"ok": True, "result": result})
        if path == "/api/simulator/draft":
            sim_mode = b.get("mode", "daily")
            text = (b.get("text") or "").strip()
            if not text:
                return self._send(400, {"ok": False, "error": "텍스트를 입력해주세요."})
            user_msg = f"[MODE:{sim_mode}]\n{text}"
            result = _call_claude(SIMULATOR_DRAFT_PROMPT, user_msg)
            if not result:
                return self._send(500, {"ok": False, "error": "AI 드래프트 생성에 실패했습니다."})
            return self._send(200, {"ok": True, "fields": result})
        # 이하 쓰기: user+pin 검증
        uid = b.get("user", ""); pin = b.get("pin", "")
        if not auth(uid, pin): return self._send(401, {"ok": False, "error": "인증 실패"})
        if path == "/api/assign-parse":
            # 자유 텍스트 → AI to-do 항목화 (담당자 미지정 — 리더가 이후 지정)
            if not (is_admin(uid) or is_leader(uid)):
                return self._send(403, {"ok": False, "error": "분장 권한 없음"})
            items = _llm_todo(b.get("text") or "")
            return self._send(200, {"ok": True, "items": items})
        if path == "/api/assign-from-plan":
            # 주간업무계획.xlsx(base64) → 파싱 → AI 항목화 → 분장 검토 초안 (대표·리더 전용)
            if not (is_admin(uid) or is_leader(uid)):
                return self._send(403, {"ok": False, "error": "분장 권한 없음"})
            import base64, tempfile
            try:
                raw = base64.b64decode((b.get("b64") or "").split(",")[-1])
            except Exception:
                return self._send(400, {"ok": False, "error": "파일 디코드 실패"})
            if not raw or len(raw) > 10 * 1024 * 1024:
                return self._send(400, {"ok": False, "error": "빈 파일 또는 10MB 초과"})
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
                tf.write(raw)
                tmp = tf.name
            try:
                rows = _parse_weekly_plan(tmp)
            finally:
                try: os.unlink(tmp)
                except OSError: pass
            if not rows:
                return self._send(200, {"ok": False, "error": "표를 읽지 못했습니다 — '프로젝트명/금주/차주' 헤더가 있는 주간업무계획 형식인지 확인하세요"})
            lines = []
            for r in rows:
                seg = f"[{r['project']}]" if r.get("project") else "[프로젝트 미지정]"
                if r.get("status"): seg += f" (상황: {r['status']})"
                if r.get("this"): seg += f" 금주: {r['this']}"
                if r.get("next"): seg += f" / 차주: {r['next']}"
                if r.get("due"): seg += f" / 예상 런칭: {r['due']}"
                lines.append(seg)
            items = _llm_todo("\n".join(lines), max_items=30)
            return self._send(200, {"ok": True, "items": items, "rows": len(rows)})
        if path == "/api/brief-comment":
            # 브리프 항목 코멘트 — 대표·리더. 저장(시스템 피드백) + 보고자 텔레그램 회신
            if not (is_admin(uid) or is_leader(uid)):
                return self._send(403, {"ok": False, "error": "코멘트 권한 없음(대표·리더)"})
            ds = (b.get("date") or "").strip()
            item = (b.get("item") or "").strip()
            src = (b.get("src") or "").strip()
            text = (b.get("text") or "").strip()
            if not (re.fullmatch(r"\d{4}-\d{2}-\d{2}", ds) and item and text):
                return self._send(400, {"ok": False, "error": "date·item·text 필수"})
            if len(text) > 1000:
                return self._send(400, {"ok": False, "error": "코멘트는 1000자 이내"})
            tg = False
            if src and src != uid:
                cid = _tg_chat_id(src)
                if cid:
                    detail = _brief_item_source(ds, item, src)
                    quoted = f"▸ {item}" + (f"\n{detail}" if detail else "")
                    tg = _tg_send(cid, f"💬 {uid} 님의 코멘트 ({ds} 브리프)\n\n"
                                       f"📌 보고하신 내용\n{quoted}\n\n"
                                       f"💬 코멘트\n{text}\n\n"
                                       f"— 아리사 OS 브리프에서 확인할 수 있어요")
            cmt = {"date": ds, "item": item, "src": src, "author": uid, "text": text,
                   "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "tg_sent": tg}
            arr = _load_comments(ds)
            arr.append(cmt)
            _save_comments(ds, arr)
            return self._send(200, {"ok": True, "comment": cmt, "tg_sent": tg})
        if path == "/api/assign-project-check":
            # 분장 그룹 프로젝트명 → 기존 매칭/신규 판별 + 유사 후보 (대표·리더 전용)
            if not (is_admin(uid) or is_leader(uid)):
                return self._send(403, {"ok": False, "error": "분장 권한 없음"})
            projs = load_projects()
            res = []
            for name in (b.get("names") or []):
                name = (name or "").strip()
                if not name: continue
                hit = next((p for p in projs if _match_project_p(name, p)), None)
                if hit:
                    res.append({"name": name, "matched": {"id": hit.get("id"), "name": hit.get("name")}})
                else:
                    res.append({"name": name, "isNew": True, "candidates": _similar_projects(name, projs)})
            return self._send(200, {"ok": True, "results": res,
                                    "all": [{"id": p.get("id"), "name": p.get("name") or p.get("id")} for p in projs]})
        if path == "/api/assign-commit":
            # 편집·담당자 지정 완료된 항목 일괄 등록
            # + 프로젝트 연동: projectActions(create=포트폴리오 카드 자동 생성 / merge=기존 정식 명칭으로 치환)
            #   등록 성공 항목은 대상 프로젝트 tasks에 영구 반영(akey 중복 방지)
            items = b.get("items") or []
            actions = {}
            for a in (b.get("projectActions") or []):
                n = (a.get("name") or "").strip()
                if n: actions[n] = a
            projs = load_projects()
            users_known = set(load_users().keys())
            created, merged, proj_errs = [], [], []
            name_map = {}   # 그룹명 → 정식 프로젝트명
            target = {}     # 정식 프로젝트명 → 프로젝트 dict
            for n, a in actions.items():
                if a.get("action") == "merge":
                    tp = get_project(a.get("mergeId") or "")
                    if not tp:
                        proj_errs.append(f"{n}: 합칠 프로젝트를 찾지 못함"); continue
                    name_map[n] = tp.get("name") or n
                    target[name_map[n]] = tp
                    merged.append(tp.get("name"))
                elif a.get("action") == "create":
                    if not (is_admin(uid) or is_leader(uid)):
                        proj_errs.append(f"{n}: 생성은 대표·팀 리더만"); continue
                    pm = (a.get("pm") or uid).strip()
                    if pm not in users_known:
                        proj_errs.append(f"{n}: PM({pm}) 계정 없음"); continue
                    today = datetime.date.today()
                    grp = [it for it in items if (it.get("project") or "").strip() == n]
                    dls = sorted(d for d in ((it.get("deadline") or "").strip() for it in grp) if d)
                    start = (a.get("start") or "").strip() or today.isoformat()
                    end = (a.get("end") or "").strip() or (dls[-1] if dls else "")
                    mem = [pm] + [m for m in sorted({(it.get("assignee") or "").strip() for it in grp})
                                  if m in users_known and m != pm]
                    pid = _safe(n) + "-" + today.strftime("%Y%m%d")
                    np = get_project(pid)  # 같은 날 재커밋 시 재사용
                    if not np:
                        np = {"id": pid, "name": n, "desc": [], "pm": pm,
                              "start": start, "end": end, "dday": end, "members": mem,
                              "brief": {"name": n, "pm": pm, "status": "In Progress",
                                        "start": start, "end": end, "dday": end,
                                        "summary": "업무분장 등록에서 자동 생성"},
                              "tasks": [], "issues": [], "origin": "assign"}
                        save_project(np)
                        created.append(n)
                    name_map[n] = np.get("name") or n
                    target[name_map[n]] = np
            added, errs, ok_items = 0, list(proj_errs), []
            for it in items:
                assignee = (it.get("assignee") or "").strip()
                task = (it.get("task") or "").strip()
                if not (assignee and task):
                    errs.append(f"'{task[:16] or '항목'}': 담당자·업무 누락"); continue
                if is_admin(uid):
                    if assignee not in (set(load_emp().get("team_leads", {}).values()) | {uid}):
                        errs.append(f"{assignee}: 대표는 리더·본인에게만 배분"); continue
                elif emp_team(assignee) not in set(lead_teams_of(uid)):
                    errs.append(f"{assignee}: 자기 팀원만 분장 가능"); continue
                pn = (it.get("project") or "").strip()
                pn = name_map.get(pn, pn)
                ok, msg = _assign_append(assignee, task, (it.get("deadline") or "").strip(),
                                         (it.get("priority") or "일반").strip(), uid,
                                         project=pn)
                if ok:
                    added += 1
                    it2 = dict(it); it2["project"] = pn
                    ok_items.append(it2)
                else: errs.append(msg or "append 실패")
            # tasks 영구 반영 — 생성/합치기 대상 + 기존 매칭 프로젝트
            tasks_synced = 0
            by_proj = {}
            for it in ok_items:
                pn = (it.get("project") or "").strip()
                if pn: by_proj.setdefault(pn, []).append(it)
            for pn, its in by_proj.items():
                tp = target.get(pn) or next((p for p in projs if _match_project_p(pn, p)), None)
                if not tp: continue
                n_add = _append_assign_tasks(tp, its)
                if n_add:
                    save_project(tp); tasks_synced += n_add
            return self._send(200, {"ok": added > 0, "added": added, "errors": errs,
                                    "created": created, "merged": merged, "tasks_synced": tasks_synced})
        if path == "/api/assign":
            # (단건 — 하위호환) 업무분장 입력. 대표=전 직원, 리더=자기 팀원에게만
            assignee = (b.get("assignee") or "").strip()
            task = (b.get("task") or "").strip()
            if not (assignee and task): return self._send(400, {"ok": False, "error": "담당자·업무 필수"})
            if is_admin(uid):
                if assignee not in (set(load_emp().get("team_leads", {}).values()) | {uid}):
                    return self._send(403, {"ok": False, "error": "대표는 리더·본인에게만 배분할 수 있습니다"})
            elif emp_team(assignee) not in set(lead_teams_of(uid)):
                return self._send(403, {"ok": False, "error": "자기 팀원에게만 분장할 수 있습니다"})
            ok, msg = _assign_append(assignee, task, (b.get("deadline") or "").strip(),
                                     (b.get("priority") or "일반").strip(), uid)
            return self._send(200 if ok else 500, {"ok": ok, "error": msg})
        if path == "/api/assign-status":
            # 분장 상태 변경 — 완료(본인 체크)·진행중(진행 표시/반려 복귀)·승인(리더·대표)
            if not (_asgws and DAILY_SHEET):
                return self._send(500, {"ok": False, "error": "시트 미설정"})
            try:
                row = int(b.get("row") or 0)
            except (TypeError, ValueError):
                row = 0
            new_st = (b.get("status") or "").strip()
            if row < 2 or new_st not in ("미착수", "진행중", "완료", "승인", "삭제"):
                return self._send(400, {"ok": False, "error": "row·status 확인"})
            # 행 재조회 — 수동 행 삭제 등으로 어긋났으면 거부
            try:
                cur = _asgws.values_get(DAILY_SHEET, f"{ASSIGN_TAB}!A{row}:J{row}", retries=2, timeout=20)
            except Exception:
                cur = []
            r = (list(cur[0]) + [""] * 10)[:10] if cur else [""] * 10
            assignee = (r[3] or "").strip()
            task = (r[4] or "").strip()
            if not task or task != (b.get("task") or "").strip() or assignee != (b.get("assignee") or "").strip():
                return self._send(409, {"ok": False, "error": "행 내용이 달라졌습니다 — 새로고침 후 다시 시도"})
            if new_st in ("승인", "삭제"):
                if not _can_approve(uid, assignee):
                    return self._send(403, {"ok": False, "error": f"{new_st} 권한 없음(대표·해당 팀 리더)"})
            elif not (assignee == uid or _can_approve(uid, assignee)):
                return self._send(403, {"ok": False, "error": "본인 분장만 변경할 수 있습니다"})
            try:
                ok = _asgws.values_update(DAILY_SHEET, f"{ASSIGN_TAB}!H{row}", [[new_st]], timeout=20)
            except Exception as e:
                return self._send(500, {"ok": False, "error": str(e)[:80]})
            if not ok:
                return self._send(500, {"ok": False, "error": "시트 업데이트 실패"})
            recorded = False
            assign = {"date": (r[0] or "").strip(), "project": (r[1] or "").strip(),
                      "assignee": assignee, "task": task, "deadline": (r[5] or "").strip()}
            if new_st == "승인":
                recorded = _record_done_task(assign, uid)
            elif new_st == "삭제":
                _remove_done_task(assign)  # 포트폴리오에 반영돼 있었으면 함께 제거
            return self._send(200, {"ok": True, "status": new_st, "portfolio_recorded": recorded})
        if path == "/api/assign-bulk-delete":
            # 체크리스트 일괄 삭제 — 스냅샷 1회 검증 후 행별 '삭제' 마킹 (+포트폴리오 제거)
            items = b.get("items") or []
            if not items or len(items) > 200:
                return self._send(400, {"ok": False, "error": "items 확인(1~200건)"})
            if not (_asgws and DAILY_SHEET):
                return self._send(500, {"ok": False, "error": "시트 미설정"})
            snap = {a["row"]: a for a in _assign_read()}
            deleted, errs = 0, []
            for it in items:
                try:
                    row = int(it.get("row") or 0)
                except (TypeError, ValueError):
                    row = 0
                a = snap.get(row)
                label = ((it.get("task") or "")[:16]) or f"행{row}"
                if not a or a.get("task") != (it.get("task") or "").strip() \
                        or a.get("assignee") != (it.get("assignee") or "").strip():
                    errs.append(f"{label}: 행 불일치 — 새로고침 필요"); continue
                if not _can_approve(uid, a.get("assignee")):
                    errs.append(f"{label}: 권한 없음"); continue
                try:
                    ok = _asgws.values_update(DAILY_SHEET, f"{ASSIGN_TAB}!H{row}", [["삭제"]], timeout=20)
                except Exception:
                    ok = False
                if not ok:
                    errs.append(f"{label}: 시트 업데이트 실패"); continue
                _remove_done_task(a)
                deleted += 1
            return self._send(200, {"ok": deleted > 0 or not errs, "deleted": deleted, "errors": errs})
        if path == "/api/project/save":
            p = b.get("project") or {}
            if not p.get("id"): return self._send(400, {"ok": False, "error": "id 없음"})
            existing = get_project(p["id"])
            if existing and not can_edit(uid, existing):
                return self._send(403, {"ok": False, "error": "수정 권한 없음(담당 PM·대표만)"})
            if not existing and not (is_admin(uid) or is_leader(uid)):
                return self._send(403, {"ok": False, "error": "생성은 대표·팀 리더만"})
            save_project(p)
            return self._send(200, {"ok": True})
        if path == "/api/project/members":
            # 멤버(열람 직원) 배정 전용 — 내용은 안 건드림. 대표·PM·해당 팀 리더만.
            pid = b.get("id", ""); members = b.get("members")
            p = get_project(pid)
            if not p: return self._send(404, {"ok": False, "error": "not found"})
            if not can_manage(uid, p):
                return self._send(403, {"ok": False, "error": "멤버 배정 권한 없음(대표·PM·해당 팀 리더만)"})
            if not isinstance(members, list):
                return self._send(400, {"ok": False, "error": "members 배열이 필요합니다"})
            known = set(load_users().keys())
            clean = [m for m in members if m in known]
            if p.get("pm") and p["pm"] not in clean: clean.append(p["pm"])  # PM은 항상 유지
            p["members"] = clean
            save_project(p)
            return self._send(200, {"ok": True, "members": clean})
        if path == "/api/project/delete":
            # 프로젝트 통째 삭제 — 카드(JSON) + 이 프로젝트로 등록된 분장(미착수/진행중/완료)도 '삭제' 마킹.
            # 승인된 분장(완료 이력)은 보존.
            pid = b.get("id", "")
            p = get_project(pid)
            if not (is_admin(uid) or (p and (p.get("pm") or "") == uid)):
                return self._send(403, {"ok": False, "error": "삭제는 대표·담당 PM만"})
            assigns_deleted = 0
            if p and _asgws and DAILY_SHEET:
                for a in _assign_read():
                    if (a.get("status") or "") in ("삭제", "승인"):
                        continue
                    ap = (a.get("project") or "").strip()
                    if not ap or not _match_project_p(ap, p):
                        continue
                    try:
                        if _asgws.values_update(DAILY_SHEET, f"{ASSIGN_TAB}!H{a['row']}", [["삭제"]], timeout=20):
                            assigns_deleted += 1
                    except Exception:
                        pass
            f = PROJ_DIR / f"{_safe(pid)}.json"
            if f.exists(): f.unlink()
            return self._send(200, {"ok": True, "assigns_deleted": assigns_deleted})
        return self._send(404, {"ok": False, "error": "not found"})

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1: PORT = int(sys.argv[1])
    PROJ_DIR.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer((HOST, PORT), H)
    print(f"▶ 대시보드 서버 http://{HOST}:{PORT}  (데이터: {DATA})")
    print(f"  프로젝트 {len(load_projects())}개 · 사용자 {len(load_users())}명")
    try: srv.serve_forever()
    except KeyboardInterrupt: srv.shutdown()
