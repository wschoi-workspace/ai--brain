#!/usr/bin/env python3
"""
basket-weekly-insight.py — Basket 주간 매장 인사이트 자동생성 + 대표 결재큐 텔레그램 push

흐름:
  일일보고 시트(최근 7일) 읽기
   → 정량 KPI(매출 합계·일별·보고건수·빈제출) 계산
   → OpenAI(gpt-4o-mini)로 결재·의사결정 큐 / 반복 테마 / 데이터품질 추출(JSON)
   → R 다크테마 HTML 인사이트 1장 생성(insights/weekly-insight-YYMMDD.html)
   → 대표(BASKET_MANAGER_CHAT_ID)에게 결재큐 요약 텔레그램 push

기존 basket-ops-bot.py의 .env 로딩·gws 읽기·OpenAI 패턴 재사용.
실행: python3 basket-weekly-insight.py [--dry-run]   (--dry-run = 생성만, 텔레그램 미발송)
launchd 주간 가동: com.basket.weekly-insight.plist (매주 월 09:00, 직전 7일 리뷰)
"""
from __future__ import annotations
import json, os, sys, subprocess, urllib.request, urllib.parse, html as _html
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared import gws as _gws  # noqa: E402
from openai import OpenAI

WORKSPACE = Path(__file__).resolve().parents[2]
ENV_PATH = WORKSPACE / ".env"
WK = ["월", "화", "수", "목", "금", "토", "일"]

def load_env():
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
load_env()

SHEET_ID   = os.environ.get("BASKET_REPORT_SHEET_ID", "")
SHEET_TAB  = os.environ.get("BASKET_REPORT_SHEET_TAB", "일일보고")
BOT_TOKEN  = os.environ.get("BASKET_BOT_TOKEN", "")
MANAGER_ID = os.environ.get("BASKET_MANAGER_CHAT_ID", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL      = os.environ.get("BASKET_BOT_MODEL", "gpt-4o-mini")
OUT_DIR    = WORKSPACE / "10-projects" / "30-basket-report-webapp" / "insights"
SECTIONS = [("approval","③송금·승인"),("notes","④특이"),("equipment","⑤장비"),
            ("worklog","⑥업무"),("rental","⑦대관"),("staff","⑧스태프"),
            ("purchase","⑨구매"),("tenant","⑩입점"),("reflection","⑪복기")]

def read_sheet():
    """일일보고 시트 읽기(shared.gws = 재시도+auth분류 단일출처).
    실패 시 []; 헤더행은 항상 있으므로 빈 결과는 main()에서 인증장애로 처리."""
    return _gws.values_get(SHEET_ID, f"{SHEET_TAB}!A1:P200", timeout=40)

def parse_won(s):
    s = "".join(ch for ch in str(s) if ch.isdigit())
    return int(s) if s else 0

def collect(rows, days=7):
    """최근 days일 보고 수집. 행: [store,날짜,작성자,매출,지출,③~⑪,업로드시각]"""
    today = datetime.now().date()
    start = today - timedelta(days=days-1)
    body = rows[1:] if rows else []
    reports, sales_by_day = [], {}
    empty = 0
    for r in body:
        r = r + [""]*(15-len(r))
        ymd = r[1].strip()
        try:
            d = datetime.strptime(ymd, "%y%m%d").date()
        except ValueError:
            continue
        if not (start <= d <= today):
            continue
        secs = {k: r[i+5].strip() for i,(k,_) in enumerate(SECTIONS)}
        sales = parse_won(r[3])
        expense = parse_won(r[4])
        substantive = bool(sales) or bool(expense) or any(secs.values())
        if not substantive:
            empty += 1
            continue
        if sales:
            sales_by_day[ymd] = sales_by_day.get(ymd, 0) + sales
        reports.append({"date": ymd, "wd": WK[d.weekday()], "author": r[2].strip(),
                        "sales": sales, "expense": expense, "time": r[14].strip(), "secs": secs})
    return reports, sales_by_day, empty, start, today

LLM_SYS = """너는 Basket 매장(카페+편의점+대관 복합공간, GS타워 직장인 상권)의 주간 운영 분석가다.
한 주치 일일보고를 읽고 대표 의사결정에 필요한 것만 뽑아 JSON으로 반환한다. 지어내지 말고 보고 내용만 쓴다.
스키마:
{
 "headline": "이번 주 한 줄 요약(매출보다 매장이 실제로 무엇으로 작동했는지)",
 "decision_queue": [{"item":"대표 판단·결재·승인이 필요한 건(금액 있으면 포함)","status":"미결|진행중|회신함"}],
 "themes": ["반복·부상하는 운영 테마(이벤트/납품/장비 등)"],
 "pipeline": [{"item":"입점·대관·납품 파이프라인 건","status":"검토|진행|대기|완료"}],
 "data_quality": ["데이터 품질·운영 리스크 관찰(빈 제출, 정량 미기입 등)"]
}
decision_queue·themes·pipeline은 각각 최대 6개. 한국어."""

def llm_extract(reports):
    if not OPENAI_KEY or not reports:
        return {"headline":"", "decision_queue":[], "themes":[], "pipeline":[], "data_quality":[]}
    lines = []
    for r in reports:
        lines.append(f"[{r['date']} {r['wd']} {r['author']} {r['time']}] 매출={r['sales']} 지출={r.get('expense',0)}")
        for k, lab in SECTIONS:
            if r["secs"].get(k):
                lines.append(f"  {lab}: {r['secs'][k]}")
    client = OpenAI(api_key=OPENAI_KEY)
    resp = client.chat.completions.create(
        model=MODEL, temperature=0.2, response_format={"type":"json_object"},
        messages=[{"role":"system","content":LLM_SYS},
                  {"role":"user","content":"\n".join(lines)[:8000]}])
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"headline":"", "decision_queue":[], "themes":[], "pipeline":[], "data_quality":[]}

# ---------- HTML ----------
def esc(s): return _html.escape(str(s))
STATUS_CLS = {"미결":"m-open","검토":"m-open","진행중":"m-prog","대기":"m-prog",
              "진행":"m-done","회신함":"m-done","완료":"m-done"}

def build_html(kpi, ins, sales_by_day, start, today):
    days = sorted(sales_by_day.items())
    mx = max([v for _,v in days], default=1) or 1
    bars = ""
    for ymd, v in days:
        d = datetime.strptime(ymd,"%y%m%d").date()
        h = int(v/mx*100)
        bars += (f'<div class="bar"><div class="val" style="color:var(--acc2)">{v:,}</div>'
                 f'<div class="col" style="height:{h}%"></div>'
                 f'<div class="lab">{d.month}/{d.day} ({WK[d.weekday()]})</div></div>')
    if not bars:
        bars = '<div style="color:var(--mut);font-size:13px;padding:20px">정량 매출 기입 없음</div>'
    def li_items(items, cls):
        if not items: return f'<li style="color:var(--mut)">해당 없음</li>'
        out = ""
        for it in items:
            if isinstance(it, dict):
                st = it.get("status",""); cl = STATUS_CLS.get(st,"m-prog")
                tag = f'<span class="tagm {cl}">{esc(st)}</span>' if st else ""
                out += f'<li>{esc(it.get("item",""))} {tag}</li>'
            else:
                out += f'<li>{esc(it)}</li>'
        return out
    period = f"{start.month}/{start.day}~{today.month}/{today.day}"
    return TEMPLATE.format(
        period=period, gen=today.strftime("%Y-%m-%d"),
        headline=esc(ins.get("headline","")) or "이번 주 운영 인사이트",
        n_real=kpi["n_real"], n_total=kpi["n_total"], empty=kpi["empty"],
        sales_sum=f'{kpi["sales_sum"]:,}', n_decision=len(ins.get("decision_queue",[])),
        n_pipe=len(ins.get("pipeline",[])), bars=bars,
        decision=li_items(ins.get("decision_queue",[]),"q"),
        themes=li_items(ins.get("themes",[]),"theme"),
        pipeline=li_items(ins.get("pipeline",[]),"pipe"),
        dataq=li_items(ins.get("data_quality",[]),"q"))

def telegram_text(kpi, ins, start, today):
    # parse_mode 미사용(아래 send_telegram) — LLM/사용자 텍스트의 * _ 로 인한 Telegram 400 방지
    t = [f"🧺 Basket 주간 인사이트 ({start.month}/{start.day}~{today.month}/{today.day})",
         f"💰 매출 {kpi['sales_sum']:,}원 · 지출 {kpi.get('expense_sum',0):,}원 · 보고 {kpi['n_real']}/{kpi['n_total']}건"]
    if ins.get("headline"): t.append(f"📌 {ins['headline']}")
    dq = ins.get("decision_queue",[])
    if dq:
        t.append("\n▶ 대표 결재·의사결정 큐")
        for it in dq[:6]:
            st = f" ({it.get('status')})" if isinstance(it,dict) and it.get('status') else ""
            t.append(f"• {it.get('item') if isinstance(it,dict) else it}{st}")
    if ins.get("data_quality"):
        t.append("\n⚠️ " + " / ".join(ins["data_quality"][:2]))
    return "\n".join(t)

def send_telegram(text):
    if not (BOT_TOKEN and MANAGER_ID): return False, "no token/chat"
    data = urllib.parse.urlencode({"chat_id":MANAGER_ID,"text":text}).encode()
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data, timeout=20) as r:
            return json.loads(r.read()).get("ok",False), "sent"
    except Exception as e:
        return False, str(e)

def main():
    dry = "--dry-run" in sys.argv
    rows = read_sheet()
    # 헤더행은 항상 존재 → 빈 결과는 시트 읽기 실패(gws 인증/네트워크 장애)로 간주.
    # (과거엔 read_sheet의 json.loads가 크래시나면서 주간잡이 알림 없이 조용히 죽었음)
    if not rows:
        alert = ("⚠️ Basket 주간 인사이트 생성 실패\n"
                 "일일보고 시트 읽기 실패(gws 인증 장애 의심) — 이번 주 인사이트를 만들지 못했습니다.\n"
                 "→ 서버에서 `gws auth login --services drive,sheets,gmail,calendar,docs,slides,tasks` 재인증 필요.")
        print(alert)
        if not dry:
            ok, msg = send_telegram(alert)
            print(f"[telegram alert] ok={ok} {msg}")
        return
    reports, sbd, empty, start, today = collect(rows, days=7)
    kpi = {"n_real":len(reports), "n_total":len(reports)+empty, "empty":empty,
           "sales_sum":sum(r["sales"] for r in reports),
           "expense_sum":sum(r.get("expense",0) for r in reports)}
    ins = llm_extract(reports)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"weekly-insight-{today.strftime('%y%m%d')}.html"
    out.write_text(build_html(kpi, ins, sbd, start, today), encoding="utf-8")
    print(f"[insight] {out}  (보고 {kpi['n_real']}/{kpi['n_total']}, 매출 {kpi['sales_sum']:,})")
    tx = telegram_text(kpi, ins, start, today)
    if dry:
        print("--- DRY-RUN 텔레그램 미발송 ---\n" + tx)
    else:
        ok, msg = send_telegram(tx)
        print(f"[telegram] ok={ok} {msg}")

TEMPLATE = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Basket 주간 매장 인사이트 — {period}</title>
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" rel="stylesheet">
<style>
:root{{--bg:#0E0B1A;--panel:#171327;--panel2:#1F1A33;--line:#2C2542;--txt:#EDEBF5;--sub:#B4B0C6;--mut:#6F6A86;--acc:#6C5CE7;--acc2:#8B7BFF;--acc-soft:rgba(108,92,231,.12);--green:#27C093;--amber:#F2B53C;--rose:#FF6B9D;--am:#4DA3FF}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--txt);font-family:'Pretendard',-apple-system,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased;padding:0 0 90px;font-size:15px}}
.wrap{{max-width:1040px;margin:0 auto;padding:0 24px}}
header.hero{{padding:48px 0 26px;border-bottom:1px solid var(--line);background:radial-gradient(1000px 320px at 16% -10%,var(--acc-soft),transparent)}}
.eyebrow{{color:var(--acc2);font-weight:700;font-size:12.5px;letter-spacing:.12em;text-transform:uppercase}}
h1{{font-size:28px;font-weight:800;line-height:1.3;margin:11px 0;letter-spacing:-.02em}}
h1 .hl{{color:var(--acc2)}}
.lede{{color:var(--sub);font-size:14.5px;max-width:760px}}
.meta{{margin-top:15px;display:flex;gap:8px;flex-wrap:wrap}}
.chip{{background:var(--panel2);border:1px solid var(--line);color:var(--sub);font-size:11.5px;padding:5px 11px;border-radius:999px}}
section{{margin:34px 0}}
h2{{font-size:19px;font-weight:800;margin:6px 0;display:flex;align-items:center;gap:10px}}
h2 .num{{color:var(--acc2);font-size:13px;font-weight:700;background:var(--acc-soft);border:1px solid var(--acc);min-width:26px;height:26px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center}}
.sub{{color:var(--mut);font-size:12.5px;margin-bottom:14px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}}
@media(max-width:760px){{.kpis{{grid-template-columns:repeat(2,1fr)}}}}
.kpi{{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:16px}}
.kpi .v{{font-size:25px;font-weight:800;letter-spacing:-.02em}}
.kpi .l{{font-size:11.5px;color:var(--mut);margin-top:3px}}
.kpi.acc .v{{color:var(--acc2)}}.kpi.green .v{{color:var(--green)}}.kpi.rose .v{{color:var(--rose)}}.kpi.amber .v{{color:var(--amber)}}
.bars{{display:flex;gap:18px;align-items:flex-end;height:140px;padding:12px 6px 0;border-bottom:1px solid var(--line)}}
.bar{{flex:0 0 60px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}}
.bar .col{{width:42px;background:linear-gradient(180deg,var(--acc2),var(--acc));border-radius:7px 7px 0 0;min-height:3px}}
.bar .val{{font-size:12px;font-weight:700;margin-bottom:6px}}
.bar .lab{{font-size:11px;color:var(--mut);margin-top:8px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:760px){{.grid2{{grid-template-columns:1fr}}}}
.box{{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:16px 18px}}
.box h3{{font-size:14.5px;font-weight:800;margin-bottom:10px}}
ul.li{{list-style:none}}ul.li li{{position:relative;padding:7px 0 7px 18px;border-bottom:1px solid var(--line);font-size:13.2px;color:var(--sub)}}
ul.li li:last-child{{border-bottom:none}}ul.li li::before{{content:"";position:absolute;left:0;top:13px;width:6px;height:6px;border-radius:50%;background:var(--acc2)}}
ul.li li b{{color:var(--txt)}}
.q li::before{{background:var(--rose)}}.theme li::before{{background:var(--green)}}.pipe li::before{{background:var(--am)}}
.tagm{{display:inline-block;font-size:10px;font-weight:700;padding:1px 6px;border-radius:5px;margin-left:5px}}
.m-done{{background:rgba(39,192,147,.13);color:var(--green)}}.m-open{{background:rgba(255,107,157,.12);color:var(--rose)}}.m-prog{{background:rgba(242,181,60,.12);color:var(--amber)}}
.note{{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:12px 16px;color:var(--sub);font-size:12.6px;margin:14px 0}}
.note b{{color:var(--rose)}}
footer{{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);color:var(--mut);font-size:12px;text-align:center}}
</style></head><body>
<header class="hero"><div class="wrap">
<div class="eyebrow">Project Rent · Basket · 주간 매장 인사이트 (자동생성)</div>
<h1><span class="hl">{headline}</span></h1>
<p class="lede">일일보고 시트(최근 7일)를 자동 분석한 인사이트. 매출·결재 큐·반복 테마·파이프라인·데이터 품질을 한 장으로.</p>
<div class="meta"><span class="chip">기간 {period}</span><span class="chip">시트→CSV→자동요약</span><span class="chip">by Project Rent</span></div>
</div></header>
<div class="wrap">
<section><div class="kpis">
<div class="kpi acc"><div class="v">{n_real}<span style="font-size:15px;color:var(--mut)"> / {n_total}</span></div><div class="l">실질 보고 / 전체 (빈 {empty})</div></div>
<div class="kpi green"><div class="v">{sales_sum}</div><div class="l">매출 합계 (원, 7일)</div></div>
<div class="kpi rose"><div class="v">{n_decision}</div><div class="l">대표 결재·의사결정 대기</div></div>
<div class="kpi amber"><div class="v">{n_pipe}</div><div class="l">입점·이벤트 파이프라인</div></div>
</div></section>
<section><h2><span class="num">1</span>매출 추이</h2><p class="sub">정량 매출 기입 보고만 집계. 정량 입력이 늘수록 추세가 의미를 가진다.</p>
<div class="bars">{bars}</div></section>
<section><h2><span class="num">2</span>대표 결재·의사결정 큐</h2><p class="sub">보고에서 대표 판단이 필요한 건만 추출.</p>
<div class="box"><ul class="li q">{decision}</ul></div></section>
<section><h2><span class="num">3</span>반복 테마 · 파이프라인</h2>
<div class="grid2">
<div class="box"><h3>🟢 반복·부상 테마</h3><ul class="li theme">{themes}</ul></div>
<div class="box"><h3>🔵 입점·이벤트 파이프라인</h3><ul class="li pipe">{pipeline}</ul></div>
</div></section>
<section><h2><span class="num">4</span>데이터 품질 · 리스크</h2>
<div class="box"><ul class="li q">{dataq}</ul></div></section>
<footer>Basket 주간 매장 인사이트 (자동생성) · {period} · 시트→자동요약 · {gen} · by Project Rent</footer>
</div></body></html>'''

if __name__ == "__main__":
    main()
