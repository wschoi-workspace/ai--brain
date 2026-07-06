#!/usr/bin/env python3
"""
build-steps.py — 주차별 직무 스텝 HTML 28개 생성.

step-content.py의 STEPS[(wk, job)] 데이터 + 공통 템플릿 → steps/wk{N}-{job}.html.
각 스텝: 이번 주 심화 워크스루 + 성과 한 줄 + 차주 주간 공유 발표 가이드(발표자료 AI 제작 포함).

사용법:
  python build-steps.py            # 데이터에 있는 모든 (wk,job) 생성
  python build-steps.py --wk 1 2   # 특정 주차만
"""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from step_content import STEPS

BASE = Path(__file__).resolve().parent
OUT = BASE / "steps"

JOB_META = {
    "design":    ("🎨", "공간/브랜드 디자인"),
    "planning":  ("📋", "기획·AE·PM"),
    "ops":       ("🏪", "매장운영"),
    "marketing": ("📣", "마케팅"),
}
EP_META = {
    1: "왜 까만 화면인가 — 에이전트 첫 실행",
    2: "말하듯 시키고 \"확인해줘\"",
    3: "한 번에 다 시키지 마라 — Plan·/clear",
    4: "CLAUDE.md — 내 AI 업무 매뉴얼",
    5: "첫 스킬 만들기",
    6: "HTML로 비주얼 산출물",
    7: "깎아 쓰기 + 1년 후의 풍경",
    8: "프로젝트 일정 구체화 (특별편)",
}

HEAD = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__PAGETITLE__</title>
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
  :root{--bg:#0f0e17;--card:#1a1925;--card2:#211f30;--line:#2e2c40;--text:#e7e5f0;--muted:#9b97b3;
    --accent:#6C5CE7;--accent-soft:#8b7df0;--good:#16A34A;--warn:#E0A93B;--code:#0a0913;}
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:var(--bg);color:var(--text);font-family:'Pretendard',-apple-system,sans-serif;line-height:1.7;-webkit-font-smoothing:antialiased}
  .wrap{max-width:760px;margin:0 auto;padding:50px 22px 90px}
  .crumb{font-size:13px;font-weight:700;letter-spacing:.04em;color:var(--accent-soft);background:rgba(108,92,231,.12);display:inline-block;padding:6px 14px;border-radius:999px;margin-bottom:16px}
  h1{font-size:29px;font-weight:800;letter-spacing:-.02em;line-height:1.28}
  .concept{font-size:15px;color:var(--muted);margin:12px 0 4px}
  .concept b{color:#e7e5f0}
  .divider{height:1px;background:var(--line);margin:34px 0}
  .sec-label{font-size:14px;font-weight:800;color:#fff;margin-bottom:14px;display:flex;align-items:center;gap:8px}
  .before{font-size:14.5px;color:#cdcae0;background:var(--card2);border-left:3px solid var(--warn);border-radius:0 10px 10px 0;padding:13px 16px;margin:0 0 12px}
  .before b{color:var(--warn)}
  .why{font-size:13.5px;color:#cdcae0;background:rgba(108,92,231,.08);border:1px solid rgba(108,92,231,.22);border-radius:10px;padding:12px 15px;margin:0 0 14px;line-height:1.65}
  .why b{color:var(--accent-soft)}
  .tip{font-size:13px;color:var(--muted);margin-top:8px;padding-left:2px;line-height:1.6}
  .tip b{color:#bdb9d4}
  .step{display:grid;grid-template-columns:32px 1fr;gap:13px;margin:16px 0}
  .step-n{width:28px;height:28px;border-radius:50%;background:var(--accent);color:#fff;font-weight:800;font-size:13px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .step-b{min-width:0}
  .step-t{font-size:13.5px;font-weight:700;color:var(--accent-soft);margin-bottom:6px}
  .io{font-size:13.5px;color:#bdb9d4;background:var(--card2);border:1px solid var(--line);border-radius:10px;padding:11px 14px;font-style:italic}
  .code{background:var(--code);border:1px solid var(--line);border-radius:10px;padding:13px 15px;font-family:'SF Mono',Consolas,monospace;font-size:12.5px;line-height:1.6;color:#c9c4e8;white-space:pre-wrap;word-break:break-word}
  .result{border:1px solid rgba(22,163,74,.4);border-radius:12px;overflow:hidden;margin-top:2px}
  .result .rh{background:rgba(22,163,74,.12);color:#5fd38a;font-size:12.5px;font-weight:700;padding:8px 14px}
  .result .rb{padding:12px 15px;font-size:13.5px;color:#d6d3e4}
  .result .rb .k{color:var(--accent-soft);font-weight:700}
  table{width:100%;border-collapse:collapse;font-size:12.5px}
  th,td{text-align:left;padding:8px 11px;border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--accent-soft);font-weight:700;background:rgba(108,92,231,.06)}
  td{color:#cdcae0}td:first-child{color:var(--muted);font-weight:600;white-space:nowrap}
  .chk{font-size:13.5px;color:#cdcae0;margin-top:10px;display:flex;gap:8px}
  .chk .ic{color:var(--warn);font-weight:700;flex-shrink:0}
  .mstone{display:flex;flex-direction:column;border:1px solid rgba(224,169,59,.3);border-radius:12px;overflow:hidden}
  .mrow{display:grid;grid-template-columns:92px 1fr;gap:0;align-items:center;border-bottom:1px solid var(--line)}
  .mrow:last-child{border-bottom:none}
  .mrow .dday{font-weight:800;color:var(--warn);font-size:13.5px;background:rgba(224,169,59,.1);padding:11px 8px;text-align:center;align-self:stretch;display:flex;align-items:center;justify-content:center}
  .mrow .mlabel{font-size:13.5px;color:#d6d3e4;padding:10px 14px}
  .mrow .mlabel b{color:#fff}
  .perf{background:linear-gradient(135deg,rgba(108,92,231,.12),rgba(108,92,231,.03));border:1px solid rgba(108,92,231,.28);border-radius:14px;padding:16px 18px;margin-top:4px}
  .perf .big{font-size:17px;font-weight:800;color:#fff;margin-bottom:4px}
  .perf .big span{color:var(--accent-soft)}
  .perf .src{font-size:11.5px;color:var(--muted);margin-top:6px}
  .present{background:var(--card);border:1px solid rgba(224,169,59,.35);border-radius:16px;padding:22px 22px;margin-top:4px}
  .present h3{font-size:17px;font-weight:800;color:var(--warn);margin-bottom:4px}
  .present .psub{font-size:13.5px;color:var(--muted);margin-bottom:14px}
  .talk{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px}
  .talk .t{background:var(--card2);border:1px solid var(--line);border-radius:9px;padding:10px 12px;font-size:13px;color:#cdcae0}
  .talk .t b{color:#fff;display:block;font-size:13.5px;margin-bottom:2px}
  .present .pp{font-size:13px;color:var(--accent-soft);font-weight:700;margin:4px 0 6px}
  .peer{font-size:13px;color:var(--muted);margin-top:12px;border-top:1px dashed var(--line);padding-top:11px}
  .peer b{color:#cdcae0}
  footer{margin-top:34px;text-align:center;color:var(--muted);font-size:13px}
  @media(max-width:560px){.wrap{padding:38px 15px 60px}h1{font-size:24px}.talk{grid-template-columns:1fr}table{font-size:11.5px}th,td{padding:6px 8px}}
</style>
</head>
<body>
<div class="wrap">
"""

FOOT = """  <footer>🤖 AX 케이스북 · by Project Rent</footer>
</div>
</body>
</html>
"""


def esc(s):
    return s  # 데이터는 신뢰된 내부 콘텐츠


def render_step(wk, job, d):
    icon, jlabel = JOB_META[job]
    ep = EP_META[wk]
    parts = []
    parts.append(f'<span class="crumb">WEEK {wk} · {icon} {jlabel}</span>')
    parts.append(f'<h1>{d["title"]}</h1>')
    parts.append(f'<p class="concept">이번 주 개념 — <b>{ep}</b></p>')
    parts.append('<div class="divider"></div>')

    # 🎯 이번 주 심화
    parts.append('<div class="sec-label">🎯 이번 주 심화 — 직접 해보기</div>')
    if d.get("before"):
        parts.append(f'<div class="before"><b>Before</b> — {d["before"]}</div>')
    if d.get("why"):
        parts.append(f'<div class="why"><b>왜 이걸 하나</b> — {d["why"]}</div>')
    n = 1
    if d.get("input"):
        parts.append(f'<div class="step"><div class="step-n">{n}</div><div class="step-b">'
                     f'<div class="step-t">입력 — 내가 가진 것</div>'
                     f'<div class="io">{d["input"]}</div></div></div>'); n += 1
    if d.get("stages"):
        # 순차 워크스루 — 각 단계를 번호 step으로(①정의 ②현황 ③일정 …)
        for st in d["stages"]:
            inner = f'<div class="code">{st["prompt"]}</div>'
            if st.get("tip"):
                inner += f'<div class="tip">💬 <b>팁</b> — {st["tip"]}</div>'
            if st.get("result_mock"):
                inner += st["result_mock"]
            parts.append(f'<div class="step"><div class="step-n">{n}</div><div class="step-b">'
                         f'<div class="step-t">{st["title"]}</div>{inner}</div></div>'); n += 1
    if d.get("prompt") and not d.get("stages"):
        tip = f'<div class="tip">💬 <b>팁</b> — {d["tip"]}</div>' if d.get("tip") else ""
        parts.append(f'<div class="step"><div class="step-n">{n}</div><div class="step-b">'
                     f'<div class="step-t">프롬프트 — 이렇게 시킨다</div>'
                     f'<div class="code">{d["prompt"]}</div>{tip}</div></div>'); n += 1
    if d.get("result_mock") and not d.get("stages"):
        parts.append(f'<div class="step"><div class="step-n">{n}</div><div class="step-b">'
                     f'<div class="step-t">결과 — 이렇게 나온다 (예시)</div>'
                     f'{d["result_mock"]}</div></div>'); n += 1
    if d.get("verify"):
        parts.append(f'<div class="step"><div class="step-n">{n}</div><div class="step-b">'
                     f'<div class="step-t">검증 — 한 마디 더</div>'
                     f'<div class="chk"><span class="ic">✓</span><span>{d["verify"]}</span></div></div></div>'); n += 1
    if d.get("next"):
        nx = d["next"]
        inner = f'<div class="code">{nx["prompt"]}</div>'
        if nx.get("result_mock"):
            inner += nx["result_mock"]
        parts.append(f'<div class="step"><div class="step-n">{n}</div><div class="step-b">'
                     f'<div class="step-t">이어서 — {nx["title"]}</div>{inner}</div></div>')

    # 🚩 핵심 마일스톤 (있을 때만)
    if d.get("milestones"):
        parts.append('<div class="divider"></div>')
        parts.append('<div class="sec-label">🚩 핵심 마일스톤 — 놓치면 안 되는 데드라인</div>')
        rows = "".join(
            f'<div class="mrow"><div class="dday">{m["dday"]}</div>'
            f'<div class="mlabel">{m["label"]}</div></div>' for m in d["milestones"])
        parts.append(f'<div class="mstone">{rows}</div>')

    # 📊 성과
    if d.get("perf"):
        parts.append('<div class="divider"></div>')
        parts.append('<div class="sec-label">📊 이게 쌓이면</div>')
        parts.append(f'<div class="perf"><div class="big">{d["perf"]["big"]}</div>'
                     f'<div class="src">{d["perf"]["src"]}</div></div>')

    # 🎤 발표
    parts.append('<div class="divider"></div>')
    parts.append('<div class="sec-label">🎤 차주 주간 공유 — 5분 발표</div>')
    present_prompt = d.get("present",
        "이번 주 내가 한 실습으로 발표 슬라이드 3장 만들어줘.\n"
        "1장: 뭘 했나 / 2장: 결과(스크린샷 자리) / 3장: 배운 점·다음 시도.\n"
        "16:9 다크 톤, Pretendard. 완성되면 스크린샷으로.")
    parts.append(
        '<div class="present">'
        '<h3>이번 주 실습한 걸 다음 주 <b>주간 공유</b> 때 5분으로 나눕니다</h3>'
        '<p class="psub">잘한 것보다 "해보니 어땠는지"가 중요해요. 막힌 것도 자산입니다.</p>'
        '<div class="talk">'
        '<div class="t"><b>① 뭘 했나 (1분)</b>어떤 실습을 골랐는지</div>'
        '<div class="t"><b>② 결과 (2분)</b>나온 결과물 보여주기</div>'
        '<div class="t"><b>③ 배운 점 (1분)</b>새로 알게 된 것</div>'
        '<div class="t"><b>④ 막힌 점·질문 (1분)</b>안 된 것·궁금한 것</div>'
        '</div>'
        '<div class="pp">📑 발표 슬라이드도 AI로 — 그대로 복사해서 쓰세요</div>'
        f'<div class="code">{present_prompt}</div>'
        '<div class="peer">👥 <b>동료에게</b> — 발표 들은 뒤 한 줄씩: '
        '"가장 인상적인 점 1개" + "나도 써볼 것 1개"</div>'
        '</div>')

    return HEAD.replace("__PAGETITLE__", f'AX 스텝 WK{wk} · {jlabel}') + "\n".join(parts) + "\n" + FOOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wk", nargs="*", type=int, help="특정 주차만")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    made = 0
    for (wk, job), d in sorted(STEPS.items()):
        if args.wk and wk not in args.wk:
            continue
        html = render_step(wk, job, d)
        f = OUT / f"wk{wk}-{job}.html"
        f.write_text(html, encoding="utf-8")
        made += 1
        print(f"  ✅ {f.name}")
    print(f"총 {made}개 생성 → {OUT}/")


if __name__ == "__main__":
    main()
