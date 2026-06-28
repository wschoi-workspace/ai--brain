#!/usr/bin/env python3
"""최원석 Second Brain — Telegram 캡처 봇 (Phase 1).

모든 입력(텔레그램 앱 / 아이폰 단축어→Telegram API)이 이 봇으로 수렴한다.
1) 받은 생각을 00_inbox/*.md 에 즉시 저장하고 "저장됨" 응답  (입력 마찰 0)
2) 백그라운드로 자동분류 → frontmatter 7필드 채움 + "정리됨" 알림

거울/대화형 없음. 저장은 동기, 분류는 비동기. 개발 가이드: 00_dev-guide.md
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ARISA 메모리 레이어(mem0) — 보조. import 실패해도 봇은 정상 동작.
try:
    import arisa_memory as _mem
except Exception:  # noqa: BLE001
    _mem = None

# ─── 경로 ───
BASE = Path("/Users/choi_ai/do-better-workspace/20-operations/24-second-brain")
INBOX = BASE / "00_inbox"
PROJECTS_DIR = Path("/Users/choi_ai/do-better-workspace/10-projects")
EMP_PATH = Path("/Users/choi_ai/do-better-workspace/00-system/02-scripts/arisa-employees.json")

# ─── 설정 (launchd EnvironmentVariables로 주입) ───
TOKEN = os.getenv("SECOND_BRAIN_BOT_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
ALLOWED = {8123576679}  # 최원석 본인만

TYPES = "idea | memo | task | project_issue | decision | reminder | question | reference | lecture_seed"

# ARISA 공유 코어 (Phase 1) — 봇 간 복붙되던 기능 배관 단일 출처
import sys  # noqa: E402
sys.path.insert(0, "/Users/choi_ai/do-better-workspace/00-system/02-scripts")
from shared.logging import TokenRedactingFilter  # noqa: E402

# 포맷은 second-brain 기존 그대로 유지, 토큰 마스킹 필터만 공유 클래스로 교체
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
for _h in logging.getLogger().handlers:
    _h.addFilter(TokenRedactingFilter())
logger = logging.getLogger("second-brain")

_client = None


def get_client() -> OpenAI:
    """OpenAI 클라이언트 lazy 생성 — 키 없이 import만 하는 도구(report.py)가 죽지 않도록."""
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


# ─── 사전(엔티티 정규화 소스) ───
def get_projects() -> list[str]:
    """10-projects 폴더명(디렉토리만). canonical 프로젝트 사전."""
    if not PROJECTS_DIR.exists():
        return []
    return [
        d.name for d in sorted(PROJECTS_DIR.iterdir())
        if d.is_dir() and not d.name.startswith(".")
    ]


def get_people() -> list[str]:
    try:
        return list(json.loads(EMP_PATH.read_text(encoding="utf-8")).get("by_name", {}).keys())
    except Exception:
        return []


def load_registry() -> dict:
    try:
        return json.loads((BASE / "registry.json").read_text(encoding="utf-8"))
    except Exception:
        return {"projects": []}


def project_dict_text() -> str:
    """registry.json의 프로젝트(별칭·설명) + registry에 없는 폴더 fallback을 사전 텍스트로."""
    reg = load_registry()
    lines, keys = [], set()
    for p in reg.get("projects", []):
        key = p.get("key", "")
        if not key:
            continue
        keys.add(key)
        al = ", ".join(p.get("aliases", []))
        desc = p.get("desc", "")
        lines.append(f"- {key} (별칭: {al}) — {desc}")
    for f in get_projects():
        if f not in keys:
            lines.append(f"- {f}")
    return "\n".join(lines) or "- (없음)"


# ─── frontmatter writer (의존성 없는 안전 YAML) ───
def _yv(v) -> str:
    if isinstance(v, list):
        return "[" + ", ".join(_yv(x) for x in v) + "]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return f'"{s}"'


def build_md(meta: dict, body: str) -> str:
    lines = ["---"]
    for k, v in meta.items():
        lines.append(f"{k}: {_yv(v)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body.strip() + "\n"


def _slug(text: str) -> str:
    words = re.findall(r"[0-9A-Za-z가-힣]+", text)[:4]
    s = "-".join(words)[:40]
    return s or "memo"


# ─── frontmatter reader (build_md 역직렬화) ───
def _unq(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return s


def _parse_val(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_unq(x) for x in inner.split(",")] if inner else []
    return _unq(v)


def read_thought(path: Path) -> tuple[dict, str]:
    txt = path.read_text(encoding="utf-8")
    if not txt.startswith("---"):
        return {}, txt.strip()
    try:
        _, fm, body = txt.split("---", 2)
    except ValueError:
        return {}, txt.strip()
    meta = {}
    for line in fm.strip().splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        meta[k.strip()] = _parse_val(v)
    return meta, body.strip()


def find_thoughts(query: str) -> list[tuple[dict, str]]:
    """query가 related_projects/tags/related_topics/summary/본문 어디든 매칭되는 생각."""
    q = query.lower().replace(" ", "")
    hits = []
    for p in sorted(INBOX.glob("*.md")):
        meta, body = read_thought(p)
        parts = []
        for key in ("related_projects", "tags", "related_topics"):
            val = meta.get(key, [])
            if isinstance(val, list):
                parts.extend(val)
        parts.append(str(meta.get("summary", "")))
        parts.append(body)
        hay = " ".join(parts).lower().replace(" ", "")
        if q in hay:
            hits.append((meta, body))
    return hits


def make_brief(query: str, hits: list[tuple[dict, str]]) -> str:
    lines = []
    for meta, body in hits:
        s = meta.get("summary") or body[:60]
        lines.append(f"- ({meta.get('type', '')}) {s}")
    system = (
        "너는 최원석의 Second Brain 브리프 생성기다. 주어진 생각 목록을 3~5줄로 압축한다. "
        "핵심 방향 / 결정 필요 / 다음 액션을 간결히. 군더더기·인사말 없이 바로 본론."
    )
    user = f"주제: {query}\n\n수집된 생각({len(hits)}건):\n" + "\n".join(lines)
    resp = get_client().chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return (resp.choices[0].message.content or "").strip()


_TYPE_ICON = {
    "idea": "💡", "question": "❓", "decision": "⚖️", "task": "✅",
    "project_issue": "⚠️", "reference": "📚", "lecture_seed": "🎓",
    "memo": "📝", "reminder": "⏰",
}


def connect_view(query: str, hits: list[tuple[dict, str]]) -> str:
    """연결 구조를 LLM 없이 즉시 표시 — type별 묶음 + 연관 주제·프로젝트 집계."""
    by_type: dict[str, list[str]] = defaultdict(list)
    topics: Counter = Counter()
    projects: Counter = Counter()
    for m, b in hits:
        by_type[m.get("type", "memo")].append(m.get("summary") or b[:50])
        for t in (m.get("related_topics") or []):
            if t:
                topics[t] += 1
        for p in (m.get("related_projects") or []):
            if p:
                projects[p] += 1
    out = [f"🔗 '{query}' 연결 ({len(hits)}건)"]
    for typ, items in by_type.items():
        out.append(f"\n{_TYPE_ICON.get(typ, '•')} {typ} ({len(items)})")
        for s in items[:5]:
            out.append(f"   · {s}")
        if len(items) > 5:
            out.append(f"   … 외 {len(items) - 5}건")
    if topics:
        out.append("\n🏷 연관 주제: " + ", ".join(
            (f"{t}×{c}" if c > 1 else t) for t, c in topics.most_common(8)))
    if projects:
        out.append("🔀 연결 프로젝트: " + ", ".join(
            f"{p}×{c}" for p, c in projects.most_common(6)))
    return "\n".join(out)


def transcribe(path: Path) -> str:
    """텔레그램 음성(ogg/opus) → 한국어 텍스트 (OpenAI Whisper)."""
    with open(path, "rb") as f:
        r = get_client().audio.transcriptions.create(model="whisper-1", file=f, language="ko")
    return (r.text or "").strip()


# ─── 인텐트 라우터 (규칙 기반: 빠르고 예측가능) ───
CAPTURE_PREFIXES = ("메모", "기록", "노트", "저장")


def route_intent(text: str) -> tuple[str, str]:
    """반환 (intent, payload). 규칙:
    - '메모/기록/노트/저장'으로 시작 → capture (접두어 제거)
    - 물음표(? 또는 ？) 포함 → chat
    - 그 외 → capture (기본, 생각 유실 방지)
    """
    t = (text or "").strip()
    for p in CAPTURE_PREFIXES:
        if t.startswith(p):
            rest = t[len(p):].lstrip(" :：,-야은는임 ")
            return "capture", (rest or t)
    if "?" in t or "？" in t:
        return "chat", t
    return "capture", t


def all_thoughts_context(limit: int = 50) -> str:
    """최근 생각들의 요약 목록 — 대화 컨텍스트로 주입."""
    files = sorted(INBOX.glob("*.md"), reverse=True)[:limit]
    lines = []
    for p in files:
        m, b = read_thought(p)
        rp = m.get("related_projects", [])
        rp = ",".join(rp) if isinstance(rp, list) else str(rp)
        lines.append(f"- [{m.get('type','')}/{rp}] {m.get('summary') or b[:50]}")
    return "\n".join(lines) or "(저장된 생각 없음)"


CHAT_SYSTEM = (
    "너는 최원석의 'Second Brain' — 최원석과 1:1로 편하게 대화하는 똑똑한 사고 파트너야. "
    "사람처럼 자연스럽게 말해. 딱딱한 비서체('~입니다', '~하십시오')나 "
    "'[내 생각]에 따르면', '컨텍스트에 따르면' 같은 기계적인 표현은 절대 쓰지 마. "
    "친한 동료가 말하듯 편하고 또렷하게, 핵심부터 말해. 가볍게 존대하되 과한 격식은 빼고, "
    "필요하면 되묻거나 네 의견도 살짝 보태. 너무 길게 늘어놓지 말고 대화하듯 자연스럽게. "
    "아래 노트는 최원석이 저장해둔 생각들이야 — 답의 근거로만 참고하고, 없는 내용은 "
    "솔직히 모른다고 해(절대 지어내지 마)."
)


def chat_reply(text: str, history: list, recalled: list | None = None) -> str:
    ctx = ""
    if recalled:
        rel = "\n".join(f"- {h['memory']}" for h in recalled)
        ctx += "# 이 질문과 의미적으로 관련된 과거 생각 (mem0 재부상 — 우선 참고)\n" + rel + "\n\n"
    ctx += "# 최원석의 저장된 생각(최근)\n" + all_thoughts_context()
    msgs = [{"role": "system", "content": CHAT_SYSTEM + "\n\n" + ctx}]
    msgs += history[-8:]
    msgs.append({"role": "user", "content": text})
    r = get_client().chat.completions.create(model=OPENAI_MODEL, messages=msgs, temperature=0.8)
    return (r.choices[0].message.content or "").strip()


# ─── 저장 ───
def save_raw(text: str, source: str, input_type: str,
             type_hint: str = "", project_hint: str = "") -> tuple[str, Path]:
    """raw 상태로 즉시 저장. 분류 전. (id, path) 반환."""
    INBOX.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    tid = now.strftime("%Y-%m-%d-%H%M%S")
    path = INBOX / f"{tid}-{_slug(text)}.md"
    meta = {
        "id": tid,
        "created": now.isoformat(timespec="seconds"),
        "source": source,
        "input_type": input_type,
        "status": "raw",
        "type": type_hint,
        "tags": [],
        "related_topics": [],
        "related_projects": [project_hint] if project_hint else [],
        "possible_use": [],
        "summary": "",
        "next_action": "",
        "confidence": 0.0,
    }
    path.write_text(build_md(meta, text), encoding="utf-8")
    return tid, path


# ─── 분류 (동기, to_thread로 호출) ───
def classify(text: str, people: list[str]) -> dict:
    system = f"""너는 최원석(대표) 본인의 Second Brain 분류기다. 화자는 항상 최원석 1인칭이다.
짧은 생각을 받아 아래 7필드를 생성한다. 받아쓰기(STT) 오류가 섞일 수 있으니
'고유명사 사전'을 참고해 프로젝트명·사람명을 정식 표기로 정규화하라(사전에 없으면 원문 존중).

[프로젝트 사전] (related_projects에는 매칭되는 항목의 key 값을 넣는다. 별칭·설명으로 판단)
{project_dict_text()}

[사람 사전]
{', '.join(people) or '(없음)'}

type은 정확히 다음 중 하나: {TYPES}

반드시 아래 JSON만 출력:
{{
  "type": "{TYPES.split(' | ')[0]}",
  "tags": ["키워드", "..."],
  "related_topics": ["연관 주제", "..."],
  "related_projects": ["프로젝트 폴더명 또는 비움"],
  "possible_use": ["강의소재|제안서|프로젝트방향|의사결정 등"],
  "summary": "생각을 또렷하게 1문장으로 재진술(지어내지 말 것)",
  "next_action": "있으면 다음 행동, 없으면 빈 문자열",
  "confidence": 0.0
}}"""
    resp = get_client().chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"생각:\n{text}"},
        ],
    )
    return json.loads(resp.choices[0].message.content or "{}")


def update_frontmatter(path: Path, text: str, result: dict,
                       source: str, input_type: str, project_hint: str = "") -> dict:
    """분류 결과로 frontmatter 재작성(status=classified). 본문(원문) 보존."""
    tid = path.stem.split("-")[:6]
    rp = result.get("related_projects") or ([project_hint] if project_hint else [])
    meta = {
        "id": path.stem,
        "created": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "input_type": input_type,
        "status": "classified",
        "type": result.get("type", "memo"),
        "tags": result.get("tags", []),
        "related_topics": result.get("related_topics", []),
        "related_projects": rp,
        "possible_use": result.get("possible_use", []),
        "summary": result.get("summary", ""),
        "next_action": result.get("next_action", ""),
        "confidence": result.get("confidence", 0.0),
    }
    path.write_text(build_md(meta, text), encoding="utf-8")
    return meta


# ─── 텔레그램 핸들러 ───
def _allowed(update: Update) -> bool:
    return bool(update.effective_user and update.effective_user.id in ALLOWED)


async def _capture(update: Update, text: str, type_hint: str = "", project_hint: str = "",
                   source: str = "telegram", input_type: str = "text", resurface: bool = True):
    """저장 + 백그라운드 분류. resurface=False면 재부상(💭)은 생략하고 mem0 적재만
    한다(질문형 경로에서 _chat이 이미 재부상을 보여주므로 중복 방지)."""
    text = (text or "").strip()
    if not text:
        await update.message.reply_text("빈 내용이에요. 생각을 적어주세요.")
        return
    tid, path = save_raw(text, source, input_type, type_hint, project_hint)
    await update.message.reply_text("🟢 저장됨")
    asyncio.create_task(_classify_task(update, path, text, source, input_type, project_hint, resurface))


async def _chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE, text: str):
    hist = ctx.chat_data.setdefault("hist", [])
    # mem0 재부상: 질문과 의미적으로 관련된 과거 생각을 끌어와 답변 근거로 + 💭 표시
    recalled = []
    if _mem and getattr(_mem, "ENABLED", False):
        try:
            recalled = await asyncio.to_thread(_mem.recall, text, "wonseok", 4, None, 0.3)
        except Exception:
            logger.exception("chat recall failed")  # 재부상 실패해도 대화는 계속
    try:
        reply = await asyncio.to_thread(chat_reply, text, list(hist), recalled)
    except Exception as e:
        logger.exception("chat failed")
        await update.message.reply_text(f"⚠️ 대화 실패: {e}")
        return
    hist.append({"role": "user", "content": text})
    hist.append({"role": "assistant", "content": reply})
    del hist[:-16]  # 최근 8턴만 유지
    await update.message.reply_text(f"💬 {reply}")
    if recalled:
        lines = "\n".join(f"· {h['memory']}" for h in recalled[:3])
        await update.message.reply_text("💭 관련해서 전에 이런 생각도 했어요\n" + lines)


async def _classify_task(update, path, text, source, input_type, project_hint, resurface=True):
    try:
        result = await asyncio.to_thread(classify, text, get_people())
        meta = update_frontmatter(path, text, result, source, input_type, project_hint)
        proj = ", ".join(meta["related_projects"]) or "미분류"
        await update.message.reply_text(f"🧠 {meta['type']} · {proj}\n{meta['summary']}")
        await _memory_task(update, path, text, meta, resurface)
    except Exception as e:
        logger.exception("classify failed")
        await update.message.reply_text(f"⚠️ 저장은 됐는데 분류 실패: {e}")


async def _memory_task(update, path, text, meta, resurface=True):
    """mem0 적재(항상) + 재부상(resurface=True일 때만). 원문은 이미 inbox .md에 보존됨 —
    mem0는 시맨틱 재부상 보조용. 실패해도 봇은 계속."""
    if not _mem or not getattr(_mem, "ENABLED", False):
        return
    try:
        recalled = []
        if resurface:
            query = meta.get("summary") or text
            recalled = await asyncio.to_thread(_mem.recall, query, "wonseok", 4, path.name)
        md = {
            "source_file": path.name,
            "project": ",".join(meta.get("related_projects") or []),
            "type": meta.get("type", ""),
            "date": str(meta.get("created", ""))[:10],
        }
        await asyncio.to_thread(_mem.add, text, md)
        if recalled:
            lines = "\n".join(f"· {h['memory']}" for h in recalled[:3])
            await update.message.reply_text("💭 관련해서 전에 이런 생각도 했어요\n" + lines)
    except Exception:
        logger.exception("memory task failed")  # 봇 본흐름은 영향 없음


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    await update.message.reply_text(
        "🧠 Second Brain\n"
        "• 생각을 보내면 → 저장 + 자동분류\n"
        "• ? 로 물으면 → 내 생각 기반으로 대화\n"
        "• '메모…'로 시작하면 → 무조건 저장\n"
        "• 생각을 저장하면 → 관련된 과거 생각을 자동 재부상 💭\n\n"
        "/ask 질문 · /save 생각 · /brief 주제 · /recall 의미검색 · /connect 연결 · /idea 내용 · /project 이름 내용"
    )


async def cmd_idea(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    await _capture(update, " ".join(ctx.args), type_hint="idea")


async def cmd_project(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    if not ctx.args:
        await update.message.reply_text("사용법: /project <프로젝트명> <내용>")
        return
    await _capture(update, " ".join(ctx.args[1:]), project_hint=ctx.args[0])


async def cmd_brief(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    if not ctx.args:
        await update.message.reply_text("사용법: /brief <프로젝트|키워드>")
        return
    query = " ".join(ctx.args)
    hits = await asyncio.to_thread(find_thoughts, query)
    if not hits:
        await update.message.reply_text(f"'{query}' 관련 생각이 아직 없어요.")
        return
    await update.message.reply_text(f"🔎 '{query}' {len(hits)}건 정리 중…")
    try:
        text = await asyncio.to_thread(make_brief, query, hits)
        await update.message.reply_text(f"📋 {query} 브리프 ({len(hits)}건)\n\n{text}")
    except Exception as e:
        logger.exception("brief failed")
        await update.message.reply_text(f"⚠️ 브리프 생성 실패: {e}")


async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    q = " ".join(ctx.args)
    if not q:
        await update.message.reply_text("사용법: /ask <질문>")
        return
    await _chat(update, ctx, q)


async def cmd_save(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    t = " ".join(ctx.args)
    if not t:
        await update.message.reply_text("사용법: /save <생각>")
        return
    await _capture(update, t)


async def cmd_connect(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    if not ctx.args:
        await update.message.reply_text("사용법: /connect <키워드>")
        return
    query = " ".join(ctx.args)
    hits = await asyncio.to_thread(find_thoughts, query)
    if not hits:
        await update.message.reply_text(f"'{query}' 연결된 생각이 아직 없어요.")
        return
    await update.message.reply_text(connect_view(query, hits))


async def cmd_recall(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """mem0 시맨틱 재부상 — 키워드가 정확히 안 겹쳐도 의미로 과거 생각을 찾는다(/connect의 보완)."""
    if not _allowed(update):
        return
    if not _mem or not getattr(_mem, "ENABLED", False):
        await update.message.reply_text("메모리 레이어가 아직 비활성이에요.")
        return
    query = " ".join(ctx.args)
    if not query:
        await update.message.reply_text("사용법: /recall <질의>")
        return
    hits = await asyncio.to_thread(_mem.recall, query, "wonseok", 6, None, 0.3)
    if not hits:
        await update.message.reply_text(f"'{query}' 재부상되는 생각이 없어요.")
        return
    lines = "\n".join(f"[{h['score']}] {h['memory']}" for h in hits)
    await update.message.reply_text(f"🧠 '{query}' 재부상 ({len(hits)}건)\n{lines}")


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    intent, payload = route_intent(update.message.text)
    if intent == "chat":
        # 질문형도 생각으로 저장(유실 방지) + 대화 답변. 재부상은 _chat이 1회만 담당.
        await _capture(update, payload, resurface=False)
        await _chat(update, ctx, payload)
    else:
        await _capture(update, payload)


async def on_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    media = update.message.voice or update.message.audio
    if not media:
        return
    await update.message.reply_text("🎙 듣는 중…")
    tmp = Path("/tmp") / f"sb_voice_{media.file_unique_id}.oga"
    try:
        tg_file = await ctx.bot.get_file(media.file_id)
        await tg_file.download_to_drive(str(tmp))
        text = await asyncio.to_thread(transcribe, tmp)
    except Exception as e:
        logger.exception("transcribe failed")
        await update.message.reply_text(f"⚠️ 전사 실패: {e}")
        return
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
    if not text:
        await update.message.reply_text("음성을 못 알아들었어요. 다시 말해줄래요?")
        return
    await update.message.reply_text(f"📝 {text}")
    intent, payload = route_intent(text)
    if intent == "chat":
        await _capture(update, payload, source="telegram", input_type="voice", resurface=False)
        await _chat(update, ctx, payload)
    else:
        await _capture(update, payload, source="telegram", input_type="voice")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """핸들러 내부 예외의 마지막 안전망. 없으면 일시적 네트워크 끊김에도 생각이
    재시도/안내 없이 유실된다(daily-report-bot 2026-06-16 교훈과 동일)."""
    err = context.error
    logger.error("Handler exception: %s", err, exc_info=err)
    msg = getattr(update, "message", None) if isinstance(update, Update) else None
    if msg is None:
        return
    try:
        if isinstance(err, (NetworkError, TimedOut)):
            await msg.reply_text("⚠️ 잠시 네트워크가 불안정했어요. 방금 내용을 한 번만 다시 보내주실래요?")
        else:
            await msg.reply_text("⚠️ 처리 중 문제가 생겼어요. 잠시 후 다시 보내주세요.")
    except Exception as e:
        logger.error("error_handler reply failed: %s", e)


def main():
    if not TOKEN:
        raise SystemExit("SECOND_BRAIN_BOT_TOKEN 미설정")
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .build()
    )
    app.add_error_handler(error_handler)  # 핸들러 예외 안전망 (생각 유실 방지)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("idea", cmd_idea))
    app.add_handler(CommandHandler("project", cmd_project))
    app.add_handler(CommandHandler("brief", cmd_brief))
    app.add_handler(CommandHandler("connect", cmd_connect))
    app.add_handler(CommandHandler("recall", cmd_recall))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("save", cmd_save))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    logger.info("Second Brain bot starting (polling)…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
