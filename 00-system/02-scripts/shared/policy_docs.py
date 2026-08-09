"""사내 규정 질의응답 — 원문 인용 기반 (2026-08-09).

## 설계 원칙: 지어내지 않는다

인사규칙 답변은 틀리면 인사 분쟁이 된다. 그래서 이 모듈의 계약은 하나다.

    **원문을 인용하지 못하면 답하지 않는다.**

요약·의역보다 인용이 우선이고, 규정에 없는 것은 "없다"고 말한다. `answer()`는
근거를 못 찾으면 `found=False`를 돌려주고, 호출측은 그걸 담당자 연결로 바꾼다.

## 왜 임베딩·벡터DB를 쓰지 않는가

규정은 **6개 문서, 각 4~5천 토큰**(실측: 취업규칙 9,347자)이다. 전부 합쳐도 3만 토큰.
청크로 자르면 "제15조 단서" 같은 맥락이 끊겨 규정 답변에서 가장 위험한 오류가 난다.
질문에 맞는 문서 1~2개를 **통째로** 넣는 편이 더 정확하고 인프라도 안 늘어난다.
(참고: `~/hr-workspace/10-projects/24-hr-telegram-bot`이 langchain+chromadb로 같은 일을
하려 했으나 미배포 상태다. 이 규모에 8개 패키지는 과잉이다.)

## 원본 위치

Drive 폴더 `03-policy_규정규칙` (ID는 POLICY_FOLDER_ID). `.docx` 6종.
⚠️ `90-archive/labor-cost-deploy/work-rules-2026-v2.html`을 근거로 쓰지 말 것 —
   본문에 "참고용 템플릿, 노무사 검토 권장" 경고가 있는 초안이다. 정식본은 Drive의 `_FINAL.docx`.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

from . import gws as _gws

logger = logging.getLogger(__name__)

POLICY_FOLDER_ID = os.environ.get(
    "ARISA_POLICY_FOLDER_ID", "1887EEbIWqEqBMxK5rUePxZY8qN544LkL")

_WS = Path(__file__).resolve().parents[2]
CACHE_DIR = Path(os.environ.get("ARISA_POLICY_CACHE")
                 or (_WS / "01-templates" / "_data" / "policy-cache"))

# ── 매니페스트 ────────────────────────────────────────────
# 파일명 접두 번호로 문서를 식별한다. fileId를 박아두지 않는 이유: 문서를 재업로드하면
# ID가 바뀐다. 번호+이름은 유지된다. 폴더는 화이트리스트 1개뿐이라 검색 비용도 무시할 만하다.
#
# topics = 이 문서가 답할 수 있는 질문의 어휘. pick()의 1차 라우팅에 쓴다.
MANIFEST = {
    "임금퇴직급여": {
        "prefix": "01_",
        "title": "임금·퇴직급여 운영규정",
        "topics": ["임금", "급여", "월급", "퇴직금", "퇴직급여", "정산", "지급일", "상여",
                   "수당", "통상임금", "평균임금", "공제", "감액", "연봉"],
    },
    "취업규칙": {
        "prefix": "03_",
        "title": "취업규칙",
        "topics": ["취업규칙", "복무", "채용", "수습", "근로계약", "징계", "해고", "퇴직",
                   "정년", "괴롭힘", "성희롱", "겸업", "비밀유지", "재택", "유연근무",
                   "근로시간", "휴게", "출근", "지각", "결근", "표창"],
    },
    "휴가": {
        "prefix": "04_",
        "title": "휴가 운영규정",
        "topics": ["휴가", "연차", "반차", "월차", "병가", "경조", "출산", "육아", "휴직",
                   "신청", "승인", "잔여", "소멸", "촉진", "대체공휴일", "여름휴가"],
    },
    "야근": {
        "prefix": "05_",
        "title": "야근 운영·고정OT 규정",
        "topics": ["야근", "연장", "초과근무", "고정OT", "OT", "야간", "휴일근로", "가산",
                   "식대", "교통비", "택시", "사전승인", "포괄임금"],
    },
    "개인정보": {
        "prefix": "06_",
        "title": "개인정보 처리방침",
        "topics": ["개인정보", "정보보호", "수집", "이용", "제3자", "파기", "열람", "동의",
                   "cctv", "주민등록번호"],
    },
    "매장운영직": {
        "prefix": "07_",
        "title": "매장 운영직 근무 운영 부속규정",
        "topics": ["매장", "운영직", "스태프", "시프트", "교대", "단시간", "알바",
                   "파트타임", "대타", "마감", "오픈"],
    },
}


# ── 동기화 ────────────────────────────────────────────────
def _meta_path() -> Path:
    return CACHE_DIR / "_meta.json"


def _load_meta() -> dict:
    try:
        return json.loads(_meta_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_meta(m: dict) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _meta_path().write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        logger.error(f"policy meta save 실패: {e}")


def sync(force: bool = False) -> dict:
    """Drive → 로컬 캐시. modifiedTime이 같으면 건너뛴다. 반환 {key: 'updated'|'cached'|'missing'}."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    files = _gws.drive_search(POLICY_FOLDER_ID, limit=50)
    if not files:
        logger.error("policy sync: Drive에서 규정 폴더를 읽지 못했습니다")
        return {k: "missing" for k in MANIFEST}

    meta = _load_meta()
    result: dict[str, str] = {}
    for key, spec in MANIFEST.items():
        f = next((x for x in files if x["name"].startswith(spec["prefix"])), None)
        if not f:
            result[key] = "missing"
            logger.warning(f"policy sync: {spec['prefix']}* 문서를 폴더에서 못 찾음")
            continue
        txt_path = CACHE_DIR / f"{key}.txt"
        prev = (meta.get(key) or {}).get("modifiedTime")
        if not force and prev == f["modifiedTime"] and txt_path.exists():
            result[key] = "cached"
            continue

        tmp = CACHE_DIR / f"_{key}.docx"
        if not _gws.drive_download(f["id"], tmp):
            result[key] = "missing"
            continue
        text = _gws.docx_to_text(tmp)
        try:
            tmp.unlink()
        except OSError:
            pass
        if not text.strip():
            result[key] = "missing"
            continue
        txt_path.write_text(text, encoding="utf-8")
        meta[key] = {"fileId": f["id"], "name": f["name"],
                     "modifiedTime": f["modifiedTime"], "chars": len(text)}
        result[key] = "updated"

    _save_meta(meta)
    return result


def load(key: str) -> str:
    """캐시된 규정 원문. 없으면 빈 문자열."""
    try:
        return (CACHE_DIR / f"{key}.txt").read_text(encoding="utf-8")
    except Exception:
        return ""


def available() -> list[str]:
    return [k for k in MANIFEST if (CACHE_DIR / f"{k}.txt").exists()]


# ── 문서 선택 ──────────────────────────────────────────────
def pick(question: str, limit: int = 2) -> list[str]:
    """질문 → 관련 규정 키 목록. 어휘 매칭 1차. 못 고르면 빈 리스트."""
    q = (question or "").lower()
    if not q:
        return []
    scored: list[tuple[int, str]] = []
    for key, spec in MANIFEST.items():
        if not (CACHE_DIR / f"{key}.txt").exists():
            continue
        hits = sum(1 for t in spec["topics"] if t.lower() in q)
        # 문서 제목이 직접 언급되면 강한 신호
        if spec["title"].split()[0] in question:
            hits += 3
        if hits:
            scored.append((hits, key))
    scored.sort(reverse=True)
    return [k for _, k in scored[:limit]]


# ── 답변 ──────────────────────────────────────────────────
ANSWER_PROMPT = """너는 회사 사내 규정을 안내하는 어시스턴트다. 아래 규정 원문만을 근거로 답한다.

## 절대 규칙
1. **원문에 없는 내용은 절대 만들지 않는다.** 일반적인 근로기준법 지식으로 보충하지 마라.
2. 답변에는 반드시 **근거 조항의 원문을 그대로 인용**한다.
3. 원문에서 근거를 찾지 못하면 found를 false로 하고 answer를 비운다. 추측하지 마라.
4. 규정에 여러 경우가 있으면 모두 적는다. 하나만 골라 단정하지 마라.
5. 금액·일수·비율은 원문 그대로 옮긴다. 계산해서 바꾸지 마라.

## 출력 (유효한 JSON만)
{
  "found": true/false,
  "answer": "질문에 대한 답. 2~5문장. 한국어. 존댓말.",
  "citations": [{"doc": "규정 이름", "clause": "제N조 (제목)", "text": "인용한 원문 그대로"}],
  "caveat": "주의할 예외나 단서가 있으면 한 문장, 없으면 빈 문자열"
}"""


def answer(question: str, llm_call, keys: list[str] | None = None,
           max_chars: int = 60000) -> dict:
    """규정 기반 답변. llm_call(system, user) -> str(JSON) 주입.

    반환 {found, answer, citations, caveat, docs}. 근거를 못 찾으면 found=False.
    llm_call을 주입받는 이유: API 키 없이 테스트할 수 있어야 하고, 모델 선택을 호출측이 정한다.
    """
    keys = keys or pick(question)
    if not keys:
        return {"found": False, "answer": "", "citations": [], "caveat": "",
                "docs": [], "reason": "관련 규정을 특정하지 못했습니다"}

    parts, used = [], []
    for k in keys:
        body = load(k)
        if not body:
            continue
        used.append(k)
        parts.append(f"===== [{MANIFEST[k]['title']}] =====\n{body}")
    if not parts:
        return {"found": False, "answer": "", "citations": [], "caveat": "",
                "docs": [], "reason": "규정 캐시가 비어 있습니다 (sync 필요)"}

    corpus = "\n\n".join(parts)[:max_chars]
    user = f"[규정 원문]\n{corpus}\n\n[질문]\n{question}"
    try:
        raw = llm_call(ANSWER_PROMPT, user) or ""
    except Exception as e:  # noqa: BLE001
        logger.error(f"policy answer LLM 실패: {e}")
        return {"found": False, "answer": "", "citations": [], "caveat": "",
                "docs": used, "reason": "일시적인 오류"}

    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {"found": False, "answer": "", "citations": [], "caveat": "",
                "docs": used, "reason": "응답 파싱 실패"}
    try:
        d = json.loads(m.group(0))
    except Exception:
        return {"found": False, "answer": "", "citations": [], "caveat": "",
                "docs": used, "reason": "응답 파싱 실패"}

    d.setdefault("citations", [])
    d.setdefault("caveat", "")
    d["docs"] = used

    # 🔴 인용 검증 — LLM이 found=true라고 해도 인용문이 원문에 실제로 없으면 기각한다.
    #    이게 "지어내지 않는다"를 코드로 강제하는 유일한 지점이다.
    if d.get("found"):
        verified = [c for c in d["citations"] if _quote_in(corpus, c.get("text", ""))]
        dropped = len(d["citations"]) - len(verified)
        if dropped:
            logger.warning(f"policy answer: 원문에 없는 인용 {dropped}건 제거")
        d["citations"] = verified
        if not verified:
            d["found"] = False
            d["answer"] = ""
            d["reason"] = "인용이 원문과 일치하지 않아 기각했습니다"
    return d


_SEP_RE = re.compile(r"[\s|/·・、,]+")


def _norm_quote(s: str) -> str:
    """대조용 정규화 — 공백과 **구분자**를 없앤다.

    표를 인용할 때 LLM은 원문의 ' | '를 ' / '나 ', '로 바꿔 적는다(실측). 그건 서식 차이지
    내용 왜곡이 아니므로 허용한다. 반대로 **글자·숫자가 다르면 기각**된다 — 그게 요점이다.
    """
    return _SEP_RE.sub("", s or "")


def _quote_in(corpus: str, quote: str) -> bool:
    """인용문이 원문에 실제로 있는가.

    너무 짧은 인용(15자 미만)은 우연히 맞을 수 있어 기각한다.
    """
    q = _norm_quote(quote)
    if len(q) < 15:
        return False
    return q in _norm_quote(corpus)


def format_reply(res: dict) -> str:
    """답변 dict → 텔레그램 메시지."""
    if not res.get("found"):
        return ("📕 사내 규정에서 근거를 찾지 못했습니다.\n"
                "제가 지어내서 답하지 않도록 되어 있어서요.\n\n"
                "인사 담당자에게 확인해 보시겠어요? 규정 원문은 아리사 OS에서도 보실 수 있습니다.")
    out = [f"📕 {res['answer']}"]
    if res.get("caveat"):
        out.append(f"\n⚠️ {res['caveat']}")
    if res.get("citations"):
        out.append("\n─── 근거 ───")
        for c in res["citations"][:3]:
            head = " · ".join(x for x in (c.get("doc"), c.get("clause")) if x)
            body = (c.get("text") or "").strip()
            out.append(f"[{head}]\n{body[:400]}")
    return "\n".join(out)[:3800]
