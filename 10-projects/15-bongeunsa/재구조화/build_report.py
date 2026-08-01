#!/usr/bin/env python3
"""
섹션 조각(sections/*.html) → 봉은사-7단계-재구조화-리포트.html 조립
- CSS는 기존 `봉은문화회관-공간활용-통합제언-보고서.html`의 <style> 블록을 그대로 재사용
- 추가 CSS(인쇄 페이지 분할, 근거 칩, 선택지 카드 등)를 덧붙임
- 좌측 네비게이션은 섹션 파일의 <section id=... data-nav=...>에서 자동 생성
usage:
  python3 build_report.py                    # 현행본(sections/) → 봉은문화센터-master-strategy-report.html
  python3 build_report.py --v1               # 리라이팅 전 원본(sections/_v1-backup/) → _구버전-50아젠다-분석문체.html
  python3 build_report.py <srcdir> <outfile> # 임의 지정
"""
import os, re, glob, json, sys

BASE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(BASE)
os.chdir(BASE)

SRC_CSS = os.path.join(PROJ, "봉은문화회관-공간활용-통합제언-보고서.html")

# ---- 0. 빌드 대상 결정 ----
if len(sys.argv) >= 3:
    SRCDIR, OUT = sys.argv[1], sys.argv[2]
elif len(sys.argv) == 2 and sys.argv[1] == "--v1":
    SRCDIR = "sections/_v1-backup"
    OUT = "_구버전-50아젠다-분석문체.html"
else:
    SRCDIR = "sections"
    OUT = "봉은문화센터-master-strategy-report.html"

# ---- 1. 기존 CSS 추출 ----
src = open(SRC_CSS, encoding="utf-8").read()
m = re.search(r"<style>(.*?)</style>", src, re.S)
if not m:
    raise SystemExit("원본에서 <style> 블록을 찾지 못했습니다.")
base_css = m.group(1)

# ---- 2. 추가 CSS ----
extra_css = """
/* ===== 재구조화 리포트 추가 스타일 ===== */

/* 아젠다 = 인쇄 1페이지 */
.agenda{padding:72px 120px 84px;max-width:1440px;margin:0 auto;border-bottom:1px solid var(--line-2)}
.agenda:last-of-type{border-bottom:none}
.agenda-head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:26px}
.agenda-head .no{font-size:10px;letter-spacing:.25em;color:var(--fg-3)}
.agenda-head .eyebrow{font-size:10px;letter-spacing:.3em;color:var(--accent);text-transform:uppercase}
.agenda h3{font-size:30px;font-weight:300;letter-spacing:-0.025em;line-height:1.2;margin:10px 0 0;max-width:1000px}
.agenda h3 em{font-style:normal;color:var(--accent-light)}
.agenda .lead{font-size:15px;color:var(--fg-2);line-height:1.75;max-width:900px;margin:22px 0 8px}
.agenda p{font-size:14px;color:var(--fg-2);line-height:1.8;max-width:960px;margin:14px 0}
.agenda h4{font-size:14px;font-weight:500;color:var(--fg);margin:28px 0 10px;letter-spacing:-0.01em}
.agenda ul,.agenda ol{margin:12px 0 12px 20px}
.agenda li{font-size:14px;color:var(--fg-2);line-height:1.8;margin:6px 0}
.agenda li strong{color:var(--fg)}

/* 근거 칩 — 요소 ID 참조 */
.ev{display:inline-block;font-size:9px;letter-spacing:.08em;color:var(--fg-3);border:1px solid var(--line);padding:1px 5px;margin-left:5px;vertical-align:middle;white-space:nowrap}
.ev.a{color:var(--accent-light);border-color:rgba(108,92,231,.3)}
.ev.b{color:var(--blue);border-color:rgba(111,138,163,.3)}
.ev.c{color:var(--fg-3);border-style:dashed}

/* 선택지 카드 (S3) */
.choice{display:grid;gap:14px;margin:24px 0}
.choice-2{grid-template-columns:repeat(2,1fr)}
.choice-3{grid-template-columns:repeat(3,1fr)}
.choice-card{border:1px solid var(--line-2);background:var(--bg-3);padding:24px;position:relative}
.choice-card .ct{font-size:10px;letter-spacing:.25em;text-transform:uppercase;color:var(--accent);margin-bottom:10px}
.choice-card h5{font-size:17px;font-weight:400;color:var(--fg);margin-bottom:12px;letter-spacing:-0.015em}
.choice-card p{font-size:13px;color:var(--fg-2);line-height:1.7;margin:0 0 10px}
.choice-card .pro,.choice-card .con{font-size:12px;line-height:1.65;padding-left:16px;position:relative;margin:5px 0;color:var(--fg-2)}
.choice-card .pro::before{content:"+";position:absolute;left:0;color:var(--green)}
.choice-card .con::before{content:"−";position:absolute;left:0;color:var(--red)}
.choice-card.rec{border-color:rgba(108,92,231,.45);background:rgba(108,92,231,.045)}
.choice-card.rec::after{content:"권고";position:absolute;top:-1px;right:-1px;background:var(--accent);color:#fff;font-size:9px;letter-spacing:.2em;padding:3px 9px}

/* 관점 블록 (S2) */
.lens{border-left:3px solid var(--accent);background:var(--bg-2);padding:22px 26px;margin:22px 0}
.lens .lt{font-size:10px;letter-spacing:.25em;text-transform:uppercase;color:var(--accent);margin-bottom:8px}
.lens h5{font-size:16px;font-weight:400;color:var(--fg);margin-bottom:10px}
.lens p{font-size:13px;color:var(--fg-2);line-height:1.75;margin:6px 0}

/* 대비 2열 */
.split{display:grid;grid-template-columns:1fr 1fr;gap:0;margin:24px 0;border:1px solid var(--line-2)}
.split>div{padding:24px 26px}
.split>div:first-child{border-right:1px solid var(--line-2)}
.split .sh{font-size:10px;letter-spacing:.25em;text-transform:uppercase;margin-bottom:12px}
.split .sh.pos{color:var(--green)}
.split .sh.neg{color:var(--red)}
.split p{font-size:13px;color:var(--fg-2);line-height:1.7;margin:6px 0}

/* 인용 */
blockquote{border-left:2px solid var(--accent);padding:6px 0 6px 20px;margin:20px 0;font-size:15px;color:var(--fg);font-weight:300;line-height:1.7;max-width:900px;letter-spacing:-0.015em}
blockquote cite{display:block;font-size:11px;color:var(--fg-3);font-style:normal;letter-spacing:.1em;margin-top:10px}

/* 매트릭스 표 강조 */
.matrix td.hit{background:rgba(108,92,231,.07);color:var(--fg)}
.matrix td.mid{background:rgba(217,163,75,.07)}
.matrix td.out{background:rgba(225,112,85,.05);color:var(--fg-3)}

/* placeholder (S7) */
.placeholder{border:1px dashed var(--line);background:var(--bg-2);padding:48px 40px;text-align:center;margin:24px 0}
.placeholder .pt{font-size:11px;letter-spacing:.3em;color:var(--fg-3);text-transform:uppercase;margin-bottom:14px}
.placeholder h4{font-size:20px;font-weight:300;color:var(--fg-2);margin:0 0 12px}
.placeholder p{font-size:13px;color:var(--fg-3);max-width:640px;margin:0 auto;line-height:1.7}

/* 내부 전용 표식 */
.internal{display:inline-block;font-size:9px;letter-spacing:.2em;background:rgba(225,112,85,.12);color:var(--red);padding:3px 9px;text-transform:uppercase;margin-left:10px;vertical-align:middle}

/* 인쇄 — 아젠다당 A4 1장 */
@media print{
  @page{size:A4 portrait;margin:14mm 12mm}
  html,body{background:#fff!important;color:#111!important}
  .nav,.brand-mark,.toc{display:none!important}
  .sec,.agenda{opacity:1!important;transform:none!important;padding:0!important;margin:0 0 8mm!important;max-width:none!important;border-bottom:none!important}
  .agenda{page-break-after:always;break-after:page}
  .agenda:last-of-type{page-break-after:auto}
  .sec{page-break-after:always;break-after:page}
  .card,.case-study,.choice-card,.kpi,.lens,.callout,.split,table{page-break-inside:avoid;break-inside:avoid}
  .agenda h3{font-size:20pt}
  .agenda p,.agenda li{font-size:9.5pt;color:#333!important}
  .ev{display:none}
}

@media (max-width:1100px){
  .sec,.agenda{padding-left:32px;padding-right:32px}
  .nav{display:none}
  .choice-2,.choice-3,.split,.card-grid,.card-grid-4,.card-grid-5,.kpi-grid{grid-template-columns:1fr}
  .cover-title{font-size:48px}
  .cover-meta{grid-template-columns:repeat(2,1fr)}
}
"""

# ---- 3. 섹션 조립 ----
files = sorted(glob.glob(f"{SRCDIR}/*.html"))
if not files:
    raise SystemExit("sections/*.html 이 없습니다. 섹션 조각을 먼저 작성하세요.")
body_parts, nav_items = [], []
for f in files:
    html = open(f, encoding="utf-8").read().strip()
    body_parts.append(html)
    for sid, label in re.findall(r'<section[^>]*id="([^"]+)"[^>]*data-nav="([^"]+)"', html):
        nav_items.append((sid, label))

nav_html = "\n".join(f'<a href="#{i}">{l}</a>' for i, l in nav_items)

meta = {}
if os.path.exists("elements.json"):
    els = json.load(open("elements.json", encoding="utf-8"))
    meta["n"] = len(els)

doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>봉은문화센터 Master Strategy Report | PROJECT RENT</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
<style>{base_css}{extra_css}</style>
</head>
<body>
<div class="brand-mark">PROJECT RENT</div>
<nav class="nav">
{nav_html}
</nav>

{chr(10).join(body_parts)}

<footer>
  <div class="logo">PROJECT RENT</div>
  <div class="meta">봉은문화센터 활용전략 · 7단계 재구조화 · 내부 문서 · 요소 {meta.get('n','—')}개</div>
</footer>

<script>
// 스크롤 인 애니메이션
const io = new IntersectionObserver((es) => {{
  es.forEach(e => {{ if (e.isIntersecting) e.target.classList.add('visible'); }});
}}, {{ threshold: 0.06 }});
document.querySelectorAll('.sec').forEach(s => io.observe(s));

// 네비 활성 표시
const navLinks = [...document.querySelectorAll('.nav a')];
const targets = navLinks.map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
const spy = new IntersectionObserver((es) => {{
  es.forEach(e => {{
    if (!e.isIntersecting) return;
    navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + e.target.id));
  }});
}}, {{ rootMargin: '-45% 0px -50% 0px' }});
targets.forEach(t => spy.observe(t));
</script>
</body>
</html>
"""

open(OUT, "w", encoding="utf-8").write(doc)
n_ag = doc.count('class="agenda"')
print(f"→ {OUT}")
print(f"   섹션 파일 {len(files)}개 / 네비 {len(nav_items)}개 / 아젠다 {n_ag}개 / {len(doc):,} bytes")
for f in files:
    print(f"   - {f}")
