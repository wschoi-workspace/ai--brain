#!/usr/bin/env python3
"""
basket-monthly-insight.py — Basket 매장 월간 인사이트 자동생성 + 대표 월간 리뷰 텔레그램 push

주간(basket-weekly-insight.py)의 월간 확장판. 한 달 일일보고를 읽고:
  → 정량 KPI(월 매출·지출 합·주차별 추이·보고일수·빈제출)
  → OpenAI(gpt-4o-mini) 월간 추출: 반복이슈(카테고리화) / 파이프라인 진행률 /
     월말 미결 결재큐 / 복기 기반 다음달 액션 / 데이터품질
  → R 다크테마 HTML 1장(insights/monthly-insight-YYMM.html)
  → 대표에게 월간 요약 텔레그램 push

실행: python3 basket-monthly-insight.py [--month YYYY-MM] [--dry-run]
  --month 미지정 시 = 직전 달(매월 1일 실행 기준). --dry-run = 생성만, 텔레그램 미발송.
launchd 월간 가동: com.basket.monthly-insight.plist (매월 1일 09:30, 직전 달 리뷰)
"""
from __future__ import annotations
import json, os, sys, calendar, urllib.request, urllib.parse, html as _html
from datetime import datetime, date
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

def target_month(spec: str) -> tuple[int, int]:
    """--month YYYY-MM 또는 미지정(=직전 달). (year, month) 반환."""
    if spec:
        y, m = spec.split("-")[:2]
        return int(y), int(m)
    t = datetime.now().date()
    # 직전 달
    y, m = (t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)
    return y, m

def read_sheet():
    """일일보고 시트 읽기(shared.gws = 재시도+auth분류 단일출처). 월간이라 넉넉히 A1:P600."""
    return _gws.values_get(SHEET_ID, f"{SHEET_TAB}!A1:P600", timeout=40)

def parse_won(s):
    digits = "".join(ch for ch in str(s) if ch.isdigit())
    if not digits:
        return 0
    val = int(digits)
    # 방어: 매장 일 매출은 억 단위 이하. 10자리(10억)↑는 계좌·전화 등 오입력 → 0 처리.
    return 0 if val >= 1_000_000_000 else val

def week_of_month(d: date) -> int:
    """월 내 주차(1~5): 1~7일=W1, 8~14=W2 ..."""
    return (d.day - 1) // 7 + 1

def collect(rows, year, month):
    """대상 (year, month) 한 달 보고 수집. 행: [store,날짜(yymmdd),작성자,매출,지출,③~⑪,시각]"""
    last = calendar.monthrange(year, month)[1]
    start, end = date(year, month, 1), date(year, month, last)
    body = rows[1:] if rows else []
    reports, sales_by_week = [], {}
    report_days, empty = set(), 0
    for r in body:
        r = r + [""]*(15-len(r))
        ymd = r[1].strip()
        try:
            d = datetime.strptime(ymd, "%y%m%d").date()
        except ValueError:
            continue
        if not (start <= d <= end):
            continue
        secs = {k: r[i+5].strip() for i,(k,_) in enumerate(SECTIONS)}
        sales = parse_won(r[3]); expense = parse_won(r[4])
        substantive = bool(sales) or bool(expense) or any(secs.values())
        if not substantive:
            empty += 1
            continue
        wom = week_of_month(d)
        if sales:
            sales_by_week[wom] = sales_by_week.get(wom, 0) + sales
        report_days.add(ymd)
        reports.append({"date": ymd, "wd": WK[d.weekday()], "wom": wom, "author": r[2].strip(),
                        "sales": sales, "expense": expense, "time": r[14].strip(), "secs": secs})
    return reports, sales_by_week, report_days, empty, start, end

LLM_SYS = """너는 Basket 매장(카페+편의점+대관 복합공간, GS타워 직장인 상권)의 월간 운영 분석가다.
한 달치 일일보고를 읽고 대표의 월간 리뷰·다음달 계획에 필요한 것만 뽑아 JSON으로 반환한다.
지어내지 말고 보고에 실제 있는 내용만 쓴다.
스키마:
{
 "headline": "이번 달 매장이 실제로 무엇으로 작동했는지 한 줄(매출 너머의 운영 성격)",
 "recurring_issues": [{"category":"장비|스태프|특이|구매|대관|운영 중 하나","issue":"한 달간 반복된 이슈 요약","freq":"몇 회/며칠 언급된 정도"}],
 "pipeline_progress": [{"item":"입점·대관·납품 파이프라인 건","status":"검토|진행|대기|완료","note":"한 달간 어디까지 진행됐나"}],
 "decision_queue": [{"item":"월말 기준 아직 미결이거나 대표 판단이 필요한 건(금액 있으면 포함)","status":"미결|진행중|회신함"}],
 "next_month_actions": ["복기(⑪)·반복이슈·데이터에 근거한 다음 달 실행 액션"],
 "data_quality": ["데이터 품질·운영 리스크 관찰(빈 제출, 매출·지출 정량 미기입 등)"]
}
recurring_issues·pipeline_progress·decision_queue·next_month_actions는 각각 최대 6개. 한국어."""

def llm_extract(reports):
    empty = {"headline":"", "recurring_issues":[], "pipeline_progress":[],
             "decision_queue":[], "next_month_actions":[], "data_quality":[]}
    if not OPENAI_KEY or not reports:
        return empty
    lines = []
    for r in reports:
        lines.append(f"[{r['date']} {r['wd']} W{r['wom']} {r['author']}] 매출={r['sales']} 지출={r.get('expense',0)}")
        for k, lab in SECTIONS:
            if r["secs"].get(k):
                lines.append(f"  {lab}: {r['secs'][k]}")
    client = OpenAI(api_key=OPENAI_KEY)
    resp = client.chat.completions.create(
        model=MODEL, temperature=0.2, response_format={"type":"json_object"},
        messages=[{"role":"system","content":LLM_SYS},
                  {"role":"user","content":"\n".join(lines)[:14000]}])
    try:
        d = json.loads(resp.choices[0].message.content)
        for k in empty:
            d.setdefault(k, empty[k])
        return d
    except Exception:
        return empty

# ---------- HTML ----------
def esc(s): return _html.escape(str(s))
STATUS_CLS = {"미결":"m-open","검토":"m-open","대기":"m-open","진행중":"m-prog","진행":"m-prog",
              "회신함":"m-done","완료":"m-done"}
CAT_CLS = {"장비":"c-eq","스태프":"c-st","특이":"c-no","구매":"c-pu","대관":"c-re","운영":"c-op"}

def build_html(kpi, ins, sales_by_week, start, end):
    weeks = sorted(sales_by_week.items())
    mx = max([v for _,v in weeks], default=1) or 1
    bars = ""
    for wom, v in weeks:
        h = int(v/mx*100)
        bars += (f'<div class="bar"><div class="val">{v:,}</div>'
                 f'<div class="col" style="height:{h}%"></div>'
                 f'<div class="lab">{wom}주차</div></div>')
    if not bars:
        bars = '<div style="color:var(--mut);font-size:13px;padding:20px">정량 매출 기입 없음</div>'

    def li_plain(items, cls):
        if not items: return '<li style="color:var(--mut)">해당 없음</li>'
        out = ""
        for it in items:
            if isinstance(it, dict):
                st = it.get("status",""); cl = STATUS_CLS.get(st,"m-prog")
                note = it.get("note","")
                tag = f'<span class="tagm {cl}">{esc(st)}</span>' if st else ""
                nt = f'<span class="note-i">{esc(note)}</span>' if note else ""
                out += f'<li>{esc(it.get("item",""))} {tag}{nt}</li>'
            else:
                out += f'<li>{esc(it)}</li>'
        return out

    def li_issues(items):
        if not items: return '<li style="color:var(--mut)">해당 없음</li>'
        out = ""
        for it in items:
            cat = it.get("category","운영") if isinstance(it, dict) else "운영"
            cl = CAT_CLS.get(cat, "c-op")
            issue = it.get("issue","") if isinstance(it, dict) else str(it)
            freq = it.get("freq","") if isinstance(it, dict) else ""
            fr = f'<span class="freq">{esc(freq)}</span>' if freq else ""
            out += f'<li><span class="cat {cl}">{esc(cat)}</span>{esc(issue)} {fr}</li>'
        return out

    period = f"{start.year}.{start.month:02d} ({start.month}/1~{end.month}/{end.day})"
    return TEMPLATE.format(
        period=period, gen=datetime.now().strftime("%Y-%m-%d"),
        headline=esc(ins.get("headline","")) or "이번 달 운영 인사이트",
        report_days=kpi["report_days"], empty=kpi["empty"],
        sales_sum=f'{kpi["sales_sum"]:,}', expense_sum=f'{kpi["expense_sum"]:,}',
        n_decision=len(ins.get("decision_queue",[])), n_pipe=len(ins.get("pipeline_progress",[])),
        bars=bars,
        issues=li_issues(ins.get("recurring_issues",[])),
        pipeline=li_plain(ins.get("pipeline_progress",[]),"pipe"),
        decision=li_plain(ins.get("decision_queue",[]),"q"),
        actions=li_plain(ins.get("next_month_actions",[]),"act"),
        dataq=li_plain(ins.get("data_quality",[]),"q"))

def telegram_text(kpi, ins, start):
    t = [f"🧺 Basket 월간 인사이트 ({start.year}.{start.month:02d})",
         f"💰 매출 {kpi['sales_sum']:,}원 · 지출 {kpi['expense_sum']:,}원 · 보고 {kpi['report_days']}일",
         ]
    if ins.get("headline"): t.append(f"📌 {ins['headline']}")
    dq = ins.get("decision_queue",[])
    if dq:
        t.append("\n▶ 월말 결재·의사결정")
        for it in dq[:5]:
            st = f" ({it.get('status')})" if isinstance(it,dict) and it.get('status') else ""
            t.append(f"• {it.get('item') if isinstance(it,dict) else it}{st}")
    na = ins.get("next_month_actions",[])
    if na:
        t.append("\n▶ 다음 달 액션")
        for a in na[:4]:
            t.append(f"• {a}")
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
    spec = ""
    if "--month" in sys.argv:
        i = sys.argv.index("--month")
        if i+1 < len(sys.argv): spec = sys.argv[i+1]
    year, month = target_month(spec)
    rows = read_sheet()
    if not rows:
        alert = ("⚠️ Basket 월간 인사이트 생성 실패\n"
                 "일일보고 시트 읽기 실패(gws 인증 장애 의심) — 이번 달 인사이트를 만들지 못했습니다.\n"
                 "→ 서버에서 `gws auth login --services drive,sheets,gmail,calendar,docs,slides,tasks` 재인증 필요.")
        print(alert)
        if not dry:
            ok, msg = send_telegram(alert); print(f"[telegram alert] ok={ok} {msg}")
        return
    reports, sbw, rdays, empty, start, end = collect(rows, year, month)
    kpi = {"report_days":len(rdays), "empty":empty,
           "sales_sum":sum(r["sales"] for r in reports),
           "expense_sum":sum(r.get("expense",0) for r in reports)}
    ins = llm_extract(reports)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"monthly-insight-{year%100:02d}{month:02d}.html"
    out.write_text(build_html(kpi, ins, sbw, start, end), encoding="utf-8")
    print(f"[insight] {out}  (보고 {kpi['report_days']}일, 매출 {kpi['sales_sum']:,}, 지출 {kpi['expense_sum']:,})")
    tx = telegram_text(kpi, ins, start)
    if dry:
        print("--- DRY-RUN 텔레그램 미발송 ---\n" + tx)
    else:
        ok, msg = send_telegram(tx); print(f"[telegram] ok={ok} {msg}")

TEMPLATE = '''<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Basket 월간 매장 인사이트 — {period}</title>
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
.subt{{color:var(--mut);font-size:12.5px;margin-bottom:14px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}}
@media(max-width:760px){{.kpis{{grid-template-columns:repeat(2,1fr)}}}}
.kpi{{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:16px}}
.kpi .v{{font-size:25px;font-weight:800;letter-spacing:-.02em}}
.kpi .l{{font-size:11.5px;color:var(--mut);margin-top:3px}}
.kpi.acc .v{{color:var(--acc2)}}.kpi.green .v{{color:var(--green)}}.kpi.rose .v{{color:var(--rose)}}.kpi.amber .v{{color:var(--amber)}}
.bars{{display:flex;gap:26px;align-items:flex-end;height:150px;padding:12px 6px 0;border-bottom:1px solid var(--line)}}
.bar{{flex:1;max-width:110px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%}}
.bar .col{{width:56px;background:linear-gradient(180deg,var(--acc2),var(--acc));border-radius:7px 7px 0 0;min-height:3px}}
.bar .val{{font-size:12px;font-weight:700;margin-bottom:6px;color:var(--acc2)}}
.bar .lab{{font-size:11.5px;color:var(--mut);margin-top:8px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:760px){{.grid2{{grid-template-columns:1fr}}}}
.box{{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:16px 18px}}
.box h3{{font-size:14.5px;font-weight:800;margin-bottom:10px}}
ul.li{{list-style:none}}ul.li li{{position:relative;padding:8px 0 8px 18px;border-bottom:1px solid var(--line);font-size:13.2px;color:var(--sub)}}
ul.li li:last-child{{border-bottom:none}}ul.li li::before{{content:"";position:absolute;left:0;top:14px;width:6px;height:6px;border-radius:50%;background:var(--acc2)}}
ul.li li b{{color:var(--txt)}}
.q li::before{{background:var(--rose)}}.pipe li::before{{background:var(--am)}}.act li::before{{background:var(--green)}}
.issues li::before{{display:none}}.issues li{{padding-left:0}}
.tagm{{display:inline-block;font-size:10px;font-weight:700;padding:1px 6px;border-radius:5px;margin-left:5px}}
.m-done{{background:rgba(39,192,147,.13);color:var(--green)}}.m-open{{background:rgba(255,107,157,.12);color:var(--rose)}}.m-prog{{background:rgba(242,181,60,.12);color:var(--amber)}}
.note-i{{display:block;font-size:11.5px;color:var(--mut);margin-top:2px}}
.cat{{display:inline-block;font-size:10.5px;font-weight:700;padding:1px 7px;border-radius:5px;margin-right:7px}}
.c-eq{{background:rgba(77,163,255,.14);color:var(--am)}}.c-st{{background:rgba(242,181,60,.14);color:var(--amber)}}
.c-no{{background:rgba(255,107,157,.13);color:var(--rose)}}.c-pu{{background:rgba(139,123,255,.16);color:var(--acc2)}}
.c-re{{background:rgba(39,192,147,.14);color:var(--green)}}.c-op{{background:var(--panel2);color:var(--sub)}}
.freq{{font-size:11px;color:var(--mut);margin-left:6px}}
footer{{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);color:var(--mut);font-size:12px;text-align:center}}
</style></head><body>
<header class="hero"><div class="wrap">
<div class="eyebrow">Project Rent · Basket · 월간 매장 인사이트 (자동생성)</div>
<h1><span class="hl">{headline}</span></h1>
<p class="lede">한 달 일일보고를 자동 분석한 월간 인사이트. 매출 추이·반복 이슈·파이프라인 진행·월말 결재·다음 달 액션을 한 장으로.</p>
<div class="meta"><span class="chip">기간 {period}</span><span class="chip">시트→자동요약</span><span class="chip">by Project Rent</span></div>
</div></header>
<div class="wrap">
<section><div class="kpis">
<div class="kpi green"><div class="v">{sales_sum}</div><div class="l">월 매출 합계 (원)</div></div>
<div class="kpi amber"><div class="v">{expense_sum}</div><div class="l">월 지출 합계 (원)</div></div>
<div class="kpi acc"><div class="v">{report_days}<span style="font-size:15px;color:var(--mut)">일</span></div><div class="l">보고일수 (빈 {empty})</div></div>
<div class="kpi rose"><div class="v">{n_decision}</div><div class="l">월말 미결 결재</div></div>
</div></section>
<section><h2><span class="num">1</span>주차별 매출 추이</h2><p class="subt">정량 매출 기입 보고만 집계. 주차별 흐름으로 성수·비수 패턴을 본다.</p>
<div class="bars">{bars}</div></section>
<section><h2><span class="num">2</span>반복·부상 이슈</h2><p class="subt">한 달간 되풀이된 운영 이슈를 카테고리로. 다음 달 개선의 1순위 후보.</p>
<div class="box"><ul class="li issues">{issues}</ul></div></section>
<section><h2><span class="num">3</span>파이프라인 진행 · 월말 결재</h2>
<div class="grid2">
<div class="box"><h3>🔵 입점·대관·납품 파이프라인</h3><ul class="li pipe">{pipeline}</ul></div>
<div class="box"><h3>🔴 월말 결재·의사결정</h3><ul class="li q">{decision}</ul></div>
</div></section>
<section><h2><span class="num">4</span>다음 달 액션</h2><p class="subt">복기(⑪)·반복이슈·데이터에 근거한 실행 항목.</p>
<div class="box"><ul class="li act">{actions}</ul></div></section>
<section><h2><span class="num">5</span>데이터 품질 · 리스크</h2>
<div class="box"><ul class="li q">{dataq}</ul></div></section>
<footer>Basket 월간 매장 인사이트 (자동생성) · {period} · 시트→자동요약 · {gen} · by Project Rent</footer>
</div></body></html>'''

if __name__ == "__main__":
    main()
