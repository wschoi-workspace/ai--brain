#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sections/*.html → 봉은문화센터-master-strategy-deck-출력본.html
가로 16:9(1280×720) 슬라이드 덱 · 화이트 출력 테마 · 내용 무손실(아젠다 54개 전량)

usage: python3 build_deck.py

- 표지 2장(커버 + 원칙·세 안) + STEP 표지 10장 + 아젠다 분할 슬라이드
- 아젠다 1개를 h4 그룹 경계 우선으로 여러 장에 패킹. 블록(표·kpi·callout·card)은 쪼개지 않음
- 오버플로는 로드 시 JS auto-fit(transform:scale, 하한 0.62)이 흡수하고 data-scaled로 기록
- 근거칩(E-xxxx) 전량 유지. build_report.py와 같은 sections/ 를 읽는 자매 빌더
"""
import os, re, glob
from lxml import html as LH
from lxml import etree

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
OUT = '봉은문화센터-master-strategy-deck-출력본.html'
BUDGET = 450       # 슬라이드 본문 가용 높이(px) 예산 — 720 - 헤더·푸터·패딩
SOLO = 540         # 추정 높이가 이를 넘는 단일 블록은 단독 슬라이드(data-big)
TBL_SPLIT = 500    # 실측 높이가 이를 넘는 표·그리드·스텝은 분할(헤더 복제·열수 유지)
                   # ⚠️460으로 낮춰봤으나 역효과 — .choice-3처럼 가로 N열 그리드는 항목을 쪼개도
                   #   행 높이가 그대로라 슬라이드만 늘어난다(2026-08-19 실측). 500 유지.

# ── 유틸 ──────────────────────────────────────────────────────────

def outer(el):
    return etree.tostring(el, encoding='unicode', method='html')

def inner(el):
    parts = [el.text or '']
    for c in el:
        parts.append(outer(c))
    return ''.join(parts)

def cls(el):
    return el.get('class') or ''

def txlen(el):
    return len(re.sub(r'\s+', '', el.text_content()))

def _ceil(a, b):
    return -(-a // b)

def table_px(el):
    rows = el.findall('.//tr')
    if not rows:
        return 40
    first = rows[0]
    ncols = max(1, len(first.findall('./th')) + len(first.findall('./td')))
    colchars = max(10, int(100 / ncols))
    h = 14
    for r in rows:
        cells = r.findall('./th') + r.findall('./td')
        ml = max((_ceil(txlen(cd), colchars) for cd in cells), default=1)
        h += max(20, ml * 15 + 8)
    return h

def est_px(el):
    """블록의 렌더 높이(px) 추정 — 폰트 크기·열 폭 기반"""
    t, c = el.tag, cls(el)
    n = txlen(el)
    if t == 'h4':
        return 32
    if t == 'table':
        return table_px(el)
    if 'kpi-grid' in c:
        tiles = len(el.findall('./div'))
        return _ceil(tiles, 3) * 102 + 10
    if 'card-grid' in c or c.startswith('choice'):
        cols = 4 if '4' in c else 5 if '5' in c else 2 if '-2' in c or 'choice-2' in c else 3
        cards = el.findall('./div')
        if not cards:
            return 70
        colchars = max(14, int(96 / cols))
        per = [40 + _ceil(txlen(d), colchars) * 16 for d in cards]
        return _ceil(len(cards), cols) * max(per) + 10
    if 'split' in c:
        cols = el.findall('./div')
        return (max((28 + _ceil(txlen(d), 44) * 17) for d in cols) if cols else 60) + 10
    if 'callout' in c:
        return 26 + _ceil(n, 92) * 19
    if t == 'blockquote':
        return 16 + _ceil(n, 78) * 21
    if 'steps' in c:
        return sum(30 + _ceil(txlen(d), 88) * 16 for d in el.findall('./div')) + 10
    if 'interpretation' in c:
        return 60 + _ceil(n, 90) * 18
    if 'lens' in c:
        return 32 + _ceil(n, 90) * 18
    if 'placeholder' in c:
        return 130
    if 'lead' in c:
        return 16 + _ceil(n, 88) * 22
    if t in ('ul', 'ol'):
        return 10 + sum(6 + _ceil(txlen(li), 90) * 19 for li in el.findall('./li'))
    return 12 + _ceil(n, 90) * 20

# 실측 피드백: measure_deck.py가 만든 measured.json이 있으면 추정 대신 실측 px 사용
import json as _json
MEASURED = {}
if os.path.exists('deck-measured.json'):
    MEASURED = _json.load(open('deck-measured.json', encoding='utf-8'))
    print(f'   (실측 {len(MEASURED)}블록 반영)')

# ── 서브카피 — 청크 본문 해시 기반 (2026-08-19 전환) ──────────────────────
# 왜 바꿨나: 종전 키는 위치 기반 f'{no}/{i+1}'이었다. 재패킹으로 청크 경계가 밀리면
#   서브카피가 "그럴듯하지만 다른 슬라이드를 설명하는" 상태가 되고, 이건 눈으로 못 찾는다.
#   실제로 2026-08-19 S8/S9 재작성 때 30건이 통째로 어긋났다.
# 해시 키는 본문이 바뀌면 자동으로 분리(빈칸)될 뿐 절대 오배치되지 않는다 —
#   빈칸은 보이고 오배치는 안 보인다. 그 비대칭이 이 설계의 전부다.
import hashlib as _hl

def chunk_hash(text):
    """청크 본문 정규화 후 SHA1 앞 12자. build/migrate가 같은 함수를 쓴다."""
    norm = re.sub(r'\s+', ' ', text or '').strip()
    return _hl.sha1(norm.encode('utf-8')).hexdigest()[:12]

SUBCOPY, SUBCOPY_MODE = {}, 'none'
if os.path.exists('deck-subcopy.json'):
    _raw = _json.load(open('deck-subcopy.json', encoding='utf-8'))
    if isinstance(_raw, dict) and _raw.get('_format') == 'hash-v1':
        SUBCOPY = {k: v['sub'] for k, v in _raw.get('entries', {}).items()}
        SUBCOPY_MODE = 'hash'
    else:                                   # 구 위치 기반 파일도 그대로 읽는다(하위호환)
        SUBCOPY = _raw
        SUBCOPY_MODE = 'legacy'
    print(f'   (서브카피 {len(SUBCOPY)}건 · {SUBCOPY_MODE} 키)')
SUB_HIT, SUB_MISS = [], []                  # 빌드 후 리포트용
CHUNKS = {}   # 서브카피 생성용 슬라이드별 본문 덤프 → deck-chunks.json

def weight(el):
    k = el.get('data-blk')
    if k and k in MEASURED:
        return MEASURED[k] + 8          # 블록 간 마진
    if el.get('data-h'):
        return int(el.get('data-h')) + 8  # 분할 청크의 보정 추정치
    return est_px(el) + 8

def split_table(el, ratio=1.0):
    """초대형 표 → 행 청크 표 여러 개 (thead·헤더행 복제, 내용 무손실)
    ratio = 실측높이/추정높이 — 청크 목표 크기를 실측 기준으로 보정"""
    thead = el.find('./thead')
    tbody = el.find('./tbody')
    rows = (tbody.findall('./tr') if tbody is not None else el.findall('./tr'))
    head_html = outer(thead) if thead is not None else ''
    if not head_html:
        # 첫 th 전용 행만 헤더로 승격 — 나머지 th 행(중간 제목행)은 데이터로 보존
        hr = next((r for r in rows if r.find('./td') is None and r.find('./th') is not None), None)
        if hr is not None:
            head_html = f'<thead>{outer(hr)}</thead>'
            rows = [r for r in rows if r is not hr]
    if len(rows) < 4:
        return [el]
    chunks, cur, h = [], [], 60
    for r in rows:
        cells = r.findall('./th') + r.findall('./td')
        ncols = max(1, len(cells))
        rh = max(20, max((_ceil(txlen(cd), max(10, int(100 / ncols))) for cd in cells), default=1) * 15 + 8)
        if cur and (h + rh) * ratio > BUDGET - 60:
            chunks.append((cur, h))
            cur, h = [], 60
        cur.append(r)
        h += rh
    if cur:
        chunks.append((cur, h))
    klass = cls(el)
    out = []
    for ch, ch_h in chunks:
        html = (f'<table class="{klass}" data-h="{int(ch_h * ratio)}">{head_html}<tbody>'
                + ''.join(outer(r) for r in ch) + '</tbody></table>')
        out.append(LH.fragment_fromstring(html))
    return out

def split_grid(el, ratio=1.0):
    """초대형 카드·kpi 그리드 → 자식 묶음 분할 (열수·클래스 유지, 내용 무손실)"""
    kids = [c for c in el if isinstance(c.tag, str)]
    total_h = est_px(el) * ratio
    parts = max(2, _ceil(int(total_h), BUDGET - 60))
    if len(kids) < 2:
        return [el]
    per = _ceil(len(kids), parts)
    klass = cls(el)
    out = []
    for i in range(0, len(kids), per):
        sub = kids[i:i + per]
        html = f'<div class="{klass}">' + ''.join(outer(d) for d in sub) + '</div>'
        frag = LH.fragment_fromstring(html)
        frag.set('data-h', str(int(est_px(frag) * ratio)))
        out.append(frag)
    return out

# ── 청킹: h4 그룹 → 예산 패킹 ─────────────────────────────────────

def groups_of(blocks):
    gs, cur = [], []
    for b in blocks:
        if b.tag == 'h4' and cur:
            gs.append(cur)
            cur = [b]
        else:
            cur.append(b)
    if cur:
        gs.append(cur)
    return gs

def pack(blocks):
    slides, cur, w = [], [], 0

    def flush():
        nonlocal cur, w
        if cur:
            slides.append(cur)
            cur, w = [], 0

    for g in groups_of(blocks):
        gw = sum(weight(b) for b in g)
        if gw <= BUDGET:
            if w and w + gw > BUDGET:
                flush()
            cur += g
            w += gw
            continue
        # 그룹 자체가 예산 초과 → 블록 단위 분할 (h4는 다음 블록과 동행)
        for b in g:
            bw = weight(b)
            h4only = bool(cur) and all(x.tag == 'h4' for x in cur)
            if bw >= SOLO:
                if h4only:                      # h4 꼬리는 대형 블록과 같은 장으로
                    cur.append(b)
                    flush()
                else:
                    flush()
                    slides.append([b])
            elif w and w + bw > BUDGET and not h4only:
                flush()
                cur, w = [b], bw
            else:
                cur.append(b)
                w += bw
        flush()
    flush()
    return slides

# ── 소스 파싱 ─────────────────────────────────────────────────────

def parse_file(path):
    raw = open(path, encoding='utf-8').read()
    root = LH.fromstring('<div id="R">' + raw + '</div>')
    return [c for c in root if isinstance(c.tag, str)]

def divider_slide(sec):
    ey = sec.find('.//div[@class="eyebrow"]')
    eyebrow = inner(ey) if ey is not None else ''
    noel = sec.find('.//div[@class="no"]')
    no = noel.text_content().strip() if noel is not None else ''
    h2 = sec.find('.//h2')
    descs = ''.join(f'<p class="dv-desc">{inner(d)}</p>'
                    for d in sec.findall('.//p[@class="sec-desc"]'))
    return (f'<div class="slide divider">'
            f'<div class="dv-no">{no}</div>'
            f'<div class="dv-eyebrow">{eyebrow}</div>'
            f'<h1>{inner(h2) if h2 is not None else ""}</h1>'
            f'{descs}'
            f'{FOOT}</div>')

def agenda_slides(ag):
    kids = [c for c in ag if isinstance(c.tag, str)]
    eyebrow, no = '', ''
    h3_html, blocks = '', []
    for k in kids:
        c = cls(k)
        if 'agenda-head' in c:
            ey = k.find('.//div[@class="eyebrow"]')
            eyebrow = inner(ey).strip() if ey is not None else ''
            noel = k.find('.//div[@class="no"]')
            no = noel.text_content().strip() if noel is not None else ''
        elif k.tag == 'h3' and not h3_html:
            h3_html = inner(k)
        else:
            blocks.append(k)          # p.lead 포함 — 항상 첫 장에 실림
    return render_slides(no, eyebrow, h3_html, blocks)

def render_slides(no, eyebrow, title_html, blocks):
    """블록 목록 → 분할·패킹된 슬라이드 HTML 목록 (아젠다·표지 부속 공용)"""
    for j, b in enumerate(blocks):
        if not b.get('data-blk'):
            b.set('data-blk', f'{no}#{j}')       # 실측 조인 키(원본 자식 순번)
    expanded = []
    for b in blocks:
        est = est_px(b)
        h = MEASURED.get(b.get('data-blk'), est)
        c = cls(b)
        if b.tag == 'table' and h > TBL_SPLIT:
            expanded += split_table(b, ratio=h / max(1, table_px(b)))
        elif h > TBL_SPLIT and ('card-grid' in c or 'kpi-grid' in c or c.startswith('choice') or 'steps' in c):
            expanded += split_grid(b, ratio=h / max(1, est))
        else:
            expanded.append(b)
    chunks = pack(expanded) or [[]]
    total = len(chunks)
    out = []
    for i, chunk in enumerate(chunks):
        key = f'{no}/{i + 1}'
        _txt = re.sub(r'\s+', ' ', ' '.join(b.text_content() for b in chunk))[:900]
        _h = chunk_hash(_txt)
        CHUNKS[key] = {
            'title': re.sub(r'<[^>]+>', '', title_html).strip(),
            'part': f'{i + 1}/{total}',
            'hash': _h,
            'text': _txt}
        sub = SUBCOPY.get(_h) or (SUBCOPY.get(key, '') if SUBCOPY_MODE == 'legacy' else '')
        (SUB_HIT if sub else SUB_MISS).append((key, _h))
        chunk_out = list(chunk)
        if not sub and i == 0:
            lead = next((b for b in chunk_out if 'lead' in cls(b)), None)
            if lead is not None:
                sub = re.sub(r'\s+', ' ', lead.text_content()).strip()
                chunk_out.remove(lead)          # 서브카피로 승격 — 본문 중복 방지
        sub_html = f'<p class="hsub">{sub}</p>' if sub else ''
        cont = (f'<span class="cont">· 계속 {i + 1}/{total}</span>'
                if total > 1 and i > 0 else '')
        big = ' data-big="1"' if len(chunk) == 1 and weight(chunk[0]) >= SOLO else ''
        body = ''.join(outer(b) for b in chunk_out)
        out.append(
            f'<div class="slide" data-agenda="{no}" data-key="{key}"{big}>'
            f'<div class="slide-head">'
            f'<div class="eyebrow"><span class="num">{no}</span> {eyebrow} {cont}</div>'
            f'<h1>{title_html}</h1>{sub_html}</div>'
            f'<div class="slide-body"><div class="fit">{body}</div></div>'
            f'{FOOT}</div>')
    return out

def cover_slides():
    kids = parse_file('sections/00-cover.html')
    sec = kids[0]
    title = sec.find('.//h1[@class="cover-title"]')
    sub = sec.find('.//p[@class="cover-sub"]')
    quote = sec.find('.//blockquote')
    meta = sec.find('.//dl[@class="cover-meta"]')
    toc = sec.find('.//div[@class="toc"]')
    cards = [d for d in sec.iter('div') if cls(d) == 'card-grid']
    callouts = [d for d in sec.iter('div') if cls(d) == 'callout']
    s1 = (f'<div class="slide cover">'
          f'<div class="cv-line">Project Rent · Internal Working Document · 출력용 슬라이드판</div>'
          f'<h1 class="cv-title">{inner(title)}</h1>'
          f'<p class="cv-sub">{inner(sub)}</p>'
          f'<div class="cv-cols"><div>{outer(quote)}{outer(meta)}</div>'
          f'<div>{outer(toc)}</div></div>'
          f'{FOOT}</div>')
    s2 = (f'<div class="slide" data-agenda="0.2">'
          f'<div class="slide-head"><div class="eyebrow"><span class="num">00</span> Principles</div>'
          f'<h1>세 개의 안과 이 보고서의 원칙</h1>'f'<p class="hsub">세 안은 단계로 이어지는 순서가 아니라 서로 다른 것을 최대로 키우는 별개의 안이며, 최종 선택은 무엇을 중심에 두고 나머지를 어디까지 섞을지의 판단입니다.</p></div>'
          f'<div class="slide-body"><div class="fit">'
          + ''.join(outer(c) for c in cards)
          + ''.join(outer(c) for c in callouts)
          + f'</div></div>{FOOT}</div>')
    return [s1, s2]

FOOT = ('<div class="foot"><span>봉은문화센터 Master Strategy Report</span>'
        '<span class="r">by <b>Project Rent</b> · <span class="pg"></span></span></div>')

# ── 조립 ─────────────────────────────────────────────────────────

slides = cover_slides()
per_agenda = {}
for f in sorted(glob.glob('sections/[0-9]*.html')):
    if f.endswith('00-cover.html'):
        continue
    for el in parse_file(f):
        if el.tag == 'section':
            slides.append(divider_slide(el))
            extra = [c for c in el if isinstance(c.tag, str)
                     and 'sec-head' not in cls(c)
                     and not (c.tag == 'p' and 'sec-desc' in cls(c))]
            if extra:
                noel = el.find('.//div[@class="no"]')
                sno = (noel.text_content().strip() if noel is not None else '')
                ey = el.find('.//div[@class="eyebrow"]')
                h2 = el.find('.//h2')
                ss = render_slides(f'{sno}.0', inner(ey).strip() if ey is not None else '',
                                   inner(h2) if h2 is not None else '', extra)
                per_agenda[f'{sno}.0'] = len(ss)
                slides += ss
        elif 'agenda' in cls(el):
            ss = agenda_slides(el)
            no = re.search(r'data-agenda="([^"]+)"', ss[0]).group(1)
            per_agenda[no] = len(ss)
            slides += ss

CSS = """
/* ── R 디자인 가이드 적용(화이트 출력 테마) — 12col grid·8px scale·아래정렬 ── */
:root{--bg:#FFFFFF;--bg-2:#F6F4F1;--bg-3:#EFECE7;--fg:#1A1A1A;--fg-2:#3D3A36;--fg-3:#8A857D;
--line:#D8D4CD;--line-2:#E5E2DC;--accent:#6C5CE7;--accent-light:#5848C8;
--green:#1E7D4E;--red:#C2472F;--amber:#A8720E;--blue:#3E6B8F;--warm:#8A6D3B;
--rust:#A34D28;--stone:#8A8175;--accent-subtle:rgba(108,92,231,.07);--accent-dark:#5848C8}
*{margin:0;padding:0;box-sizing:border-box;print-color-adjust:exact;-webkit-print-color-adjust:exact}
svg{max-width:100%;height:auto;min-width:0!important}
html{background:#E9E7E2}
body{font-family:'Pretendard Variable',Pretendard,-apple-system,sans-serif;font-weight:400;color:var(--fg);
background:#E9E7E2;letter-spacing:-0.01em}
h1,h2,h3,h4{text-wrap:balance}
.slide{width:1280px;height:720px;background:var(--bg);display:none;flex-direction:column;
padding:40px 56px 24px;position:relative;overflow:hidden;margin:0 auto}
@media screen{body{padding:24px 0}.slide{box-shadow:0 2px 18px rgba(0,0,0,.12)}
.slide.active{display:flex}}
/* 헤더: 상단 고정 (가이드 §4 슬라이드 규칙) */
.slide-head{flex-shrink:0;border-bottom:1px solid var(--line-2);padding-bottom:16px}
.eyebrow{font-size:11px;letter-spacing:.25em;text-transform:uppercase;color:var(--fg-3);margin-bottom:8px}
.eyebrow .num{display:inline-block;background:var(--accent);color:#fff;font-weight:600;
padding:2px 8px;margin-right:8px;letter-spacing:.08em}
.eyebrow .cont{color:var(--fg-3);letter-spacing:.1em;margin-left:6px}
.slide-head h1{font-size:35px;font-weight:500;line-height:1.28;letter-spacing:-0.025em;max-width:1168px}
.hsub{font-size:12.5px;color:var(--fg-2);line-height:1.6;margin-top:10px;max-width:1100px}
.slide-head h1 em{font-style:normal;color:var(--accent-light)}
/* 본문: 아래정렬 (justify-content:flex-end) */
.slide-body{flex:1;display:flex;flex-direction:column;justify-content:flex-end;overflow:hidden;position:relative;min-height:0}
.fit{width:100%}
.foot{flex-shrink:0;display:flex;justify-content:space-between;font-size:10px;letter-spacing:.2em;
text-transform:uppercase;color:var(--fg-3);border-top:1px solid var(--line-2);padding-top:14px;margin-top:16px}
.foot b{color:var(--accent-light);font-weight:600}
/* ── 본문 타이포 — 8px 리듬 ── */
.fit p{font-size:12.5px;line-height:1.6;color:var(--fg-2);margin:8px 0;max-width:1168px}
.fit p.lead{font-size:14px;color:var(--fg);border-left:3px solid var(--accent);padding-left:14px;margin:8px 0 16px}
.fit h4{font-size:13px;font-weight:600;color:var(--fg);margin:16px 0 8px}
.fit h4::before{content:'';display:inline-block;width:3px;height:12px;background:var(--accent);margin-right:8px;vertical-align:-1px}
.fit ul,.fit ol{margin:8px 0 8px 18px}
.fit li{font-size:12px;line-height:1.6;color:var(--fg-2);margin:4px 0}
.fit strong,.fit li strong{color:var(--fg);font-weight:600}
/* ── 표 ── */
.fit table{width:100%;border-collapse:collapse;font-size:11px;margin:8px 0}
.fit th{background:var(--bg-3);color:var(--fg);font-weight:600;text-align:left;padding:6px 8px;
border:1px solid var(--line);font-size:10px;letter-spacing:.04em}
.fit td{padding:6px 8px;border:1px solid var(--line-2);color:var(--fg-2);line-height:1.5;vertical-align:top}
.fit td small{font-size:10px;color:var(--fg-3)}
.matrix td.hit{background:rgba(108,92,231,.10);color:var(--fg)}
.matrix td.mid{background:rgba(168,114,14,.10)}
.matrix td.out{background:rgba(194,71,47,.08);color:var(--fg-3)}
/* ── 12-column grid (gap 14px · 개수→스팬 규칙) ── */
.kpi-grid,.kpi-grid-3,.card-grid,.card-grid-2,.card-grid-4,.card-grid-5,
.choice,.interpretation{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;margin:16px 0}
.kpi-grid>*{grid-column:span 3}
.kpi-grid-3>*,.card-grid>*,.card-grid-5>*,.choice-3>*,.interpretation>*{grid-column:span 4}
.card-grid-2>*,.choice-2>*{grid-column:span 6}
.card-grid-4>*{grid-column:span 3}
.split{display:grid;grid-template-columns:repeat(12,1fr);gap:0;margin:16px 0;border:1px solid var(--line-2)}
.split>div{grid-column:span 6;padding:16px}
.split>div:first-child{border-right:1px solid var(--line-2)}
.split .sh{font-size:10px;letter-spacing:.2em;text-transform:uppercase;margin-bottom:8px}
.split .sh.pos{color:var(--green)}
.split .sh.neg{color:var(--red)}
.split p{font-size:11px;margin:4px 0}
/* ── 컴포넌트 (내부 패딩 16px 통일) ── */
.callout,.callout-danger,.callout-success{border:1px solid var(--line);border-left:3px solid var(--accent);
background:var(--bg-2);padding:16px;margin:16px 0;font-size:12px}
.callout-danger{border-left-color:var(--red);background:rgba(194,71,47,.05)}
.callout-success{border-left-color:var(--green);background:rgba(30,125,78,.05)}
.callout p,.callout-danger p,.callout-success p{margin:4px 0;font-size:12px}
.kpi{background:var(--bg-2);border:1px solid var(--line-2);padding:16px;text-align:center}
.kpi-label{font-size:10px;letter-spacing:.2em;color:var(--fg-3);text-transform:uppercase;margin-bottom:8px}
.kpi-value{font-size:26px;font-weight:600;color:var(--accent-light);line-height:1.1;letter-spacing:-0.02em}
.kpi-unit{font-size:13px;font-weight:500;margin-left:2px}
.kpi-sub{font-size:10px;color:var(--fg-3);margin-top:8px;line-height:1.45}
.card{border:1px solid var(--line-2);background:var(--bg-2);padding:16px}
.card h4{margin:0 0 8px;font-size:12px;font-weight:600}
.card h4::before{content:none}
.card p{font-size:11px;margin:4px 0;line-height:1.55}
.card .tag,.tag{display:inline-block;font-size:9px;letter-spacing:.12em;color:var(--accent-light);
border:1px solid var(--line);padding:2px 8px;margin-top:8px}
.choice-card{border:1px solid var(--line);background:var(--bg-2);padding:16px;position:relative}
.choice-card .ct{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent-light);margin-bottom:8px}
.choice-card h5{font-size:13px;font-weight:600;margin-bottom:8px}
.choice-card p{font-size:11px;margin:0 0 8px}
.choice-card .pro,.choice-card .con{font-size:10.5px;line-height:1.5;padding-left:14px;position:relative;margin:4px 0;color:var(--fg-2)}
.choice-card .pro::before{content:"+";position:absolute;left:0;color:var(--green);font-weight:600}
.choice-card .con::before{content:"−";position:absolute;left:0;color:var(--red);font-weight:600}
.choice-card.rec{border-color:var(--accent)}
.choice-card.rec::after{content:"권고";position:absolute;top:-1px;right:-1px;background:var(--accent);
color:#fff;font-size:9px;letter-spacing:.15em;padding:2px 8px}
.lens{border-left:3px solid var(--accent);background:var(--bg-2);padding:16px;margin:16px 0}
.lens .lt{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent-light);margin-bottom:8px}
.lens h5{font-size:12.5px;font-weight:600;margin-bottom:8px}
.lens p{font-size:11px;margin:4px 0}
blockquote{border-left:2px solid var(--accent);padding:8px 0 8px 16px;margin:16px 0;font-size:13px;
color:var(--fg);line-height:1.55;max-width:1000px}
blockquote cite{display:block;font-size:10px;color:var(--fg-3);font-style:normal;letter-spacing:.08em;margin-top:8px}
.steps{margin:16px 0}
.step{border:1px solid var(--line-2);padding:12px 16px;font-size:11px;background:var(--bg-2);margin:8px 0}
.step-num{color:var(--accent-light);font-weight:700;margin-right:8px}
.badge,.badge-yes,.badge-no,.badge-warn,.badge-info{display:inline-block;font-size:9px;letter-spacing:.1em;
padding:2px 8px;border:1px solid var(--line);color:var(--fg-3);vertical-align:middle;white-space:nowrap}
.badge-yes{color:var(--green);border-color:var(--green);background:rgba(30,125,78,.07)}
.badge-no{color:var(--red);border-color:var(--red);background:rgba(194,71,47,.07)}
.badge-warn{color:var(--amber);border-color:var(--amber);background:rgba(168,114,14,.07)}
.badge-info{color:var(--blue);border-color:var(--blue);background:rgba(62,107,143,.07)}
.ev{display:inline-block;font-size:8px;letter-spacing:.05em;color:var(--fg-3);border:1px solid var(--line-2);
padding:0 4px;margin-left:3px;vertical-align:middle;white-space:nowrap}
.ev.a{color:var(--accent-light);border-color:rgba(88,72,200,.4)}
.ev.b{color:var(--blue);border-color:rgba(62,107,143,.4)}
.internal{display:inline-block;font-size:8px;letter-spacing:.15em;background:rgba(194,71,47,.1);
color:var(--red);padding:2px 8px;text-transform:uppercase;margin-left:8px;vertical-align:middle}
.hero-number{font-size:48px;font-weight:300;color:var(--accent-light);letter-spacing:-0.03em}
.interp-card{border:1px solid var(--line-2);background:var(--bg-2);padding:16px;font-size:11px}
.placeholder{border:1px dashed var(--line);background:var(--bg-2);padding:24px;text-align:center;margin:16px 0}
.placeholder .pt{font-size:9px;letter-spacing:.25em;color:var(--fg-3);text-transform:uppercase;margin-bottom:8px}
.placeholder h4{font-size:14px;color:var(--fg-2);margin:0 0 8px}
.placeholder h4::before{content:none}
.placeholder p{font-size:11px;color:var(--fg-3);max-width:560px;margin:0 auto}
.compare-table th{font-size:10px}
/* ── 표지 (중앙 정렬 예외 — 가이드 슬라이드 타입 규칙) ── */
.slide.cover{justify-content:flex-start;padding-top:64px}
.cv-line{font-size:11px;letter-spacing:.3em;color:var(--fg-3);text-transform:uppercase;margin-bottom:24px}
.cv-title{font-size:60px;font-weight:300;line-height:1.05;letter-spacing:-0.04em;margin-bottom:16px}
.cv-title em{font-style:normal;color:var(--accent-light)}
.cv-sub{font-size:14px;color:var(--fg-2);line-height:1.6;max-width:760px;margin-bottom:24px}
.cv-cols{display:grid;grid-template-columns:repeat(12,1fr);gap:14px;flex:1;min-height:0}
.cv-cols>div:first-child{grid-column:span 7}
.cv-cols>div:last-child{grid-column:span 5}
.cv-cols blockquote{font-size:15px}
.cover-meta{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 24px;margin-top:16px}
.cover-meta dt{font-size:10px;letter-spacing:.2em;color:var(--fg-3);text-transform:uppercase;margin-bottom:2px}
.cover-meta dd{font-size:12px;color:var(--fg);margin:0}
.toc h3{font-size:11px;letter-spacing:.25em;color:var(--accent-light);text-transform:uppercase;margin-bottom:8px}
.toc ol{margin-left:18px}
.toc li{font-size:11.5px;line-height:1.75;color:var(--fg-2)}
.toc a{color:inherit;text-decoration:none}
/* ── STEP 표지(간지 — 중앙 정렬 예외) ── */
.slide.divider{justify-content:center;background:var(--bg-2)}
.dv-no{font-size:104px;font-weight:700;color:rgba(108,92,231,.14);line-height:1;position:absolute;top:48px;right:56px}
.dv-eyebrow{font-size:11px;letter-spacing:.3em;color:var(--fg-3);text-transform:uppercase;margin-bottom:16px}
.slide.divider h1{font-size:40px;font-weight:500;line-height:1.25;letter-spacing:-0.025em;max-width:1040px;margin-bottom:24px}
.slide.divider h1 em{font-style:normal;color:var(--accent-light)}
.dv-desc{font-size:14px;color:var(--fg-2);line-height:1.7;max-width:920px;margin-bottom:8px}
.dv-desc strong{color:var(--fg)}
/* ── 네비 ── */
.prog{position:fixed;top:0;left:0;height:3px;background:var(--accent);z-index:50;transition:width .18s}
.nav{position:fixed;bottom:16px;right:20px;display:flex;gap:8px;z-index:50;align-items:center}
.nav button{border:1px solid var(--line);background:#fff;color:var(--fg-2);font-size:11px;
padding:6px 14px;cursor:pointer;font-family:inherit;letter-spacing:.1em}
.nav button:hover{border-color:var(--accent);color:var(--accent-light)}
.nav .cnt{font-size:11px;color:var(--fg-3);letter-spacing:.08em;padding:0 4px}
.measuring{display:flex!important;visibility:hidden;position:absolute!important;top:0;left:0}
/* SVG 다이어그램은 슬라이드 본문 높이를 넘지 않게 — 넘치면 fitAll 0.62 하한에 걸려 잘린다.
   인라인 min-width/width를 !important로 무력화하고 종횡비를 유지한 채 높이로 맞춘다. (2026-08-19) */
.fit svg{width:auto!important;min-width:0!important;max-width:100%!important;
  height:auto!important;max-height:450px;display:block;margin:0 auto}
@media print{
  html,body{background:#fff;padding:0;margin:0}
  .nav,.prog{display:none!important}
  .slide{display:flex!important;page-break-after:always;break-after:page;box-shadow:none;margin:0}
  .slide:last-child{page-break-after:auto}
  @page{size:1280px 720px;margin:0}
}
"""

JS = """
const S=[...document.querySelectorAll('.slide')];let cur=0;
function show(i){cur=Math.max(0,Math.min(S.length-1,i));
S.forEach((s,j)=>s.classList.toggle('active',j===cur));
document.querySelector('.prog').style.width=((cur+1)/S.length*100)+'%';
document.querySelector('.nav .cnt').textContent=(cur+1)+' / '+S.length;}
document.addEventListener('keydown',e=>{
if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();show(cur+1)}
if(['ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();show(cur-1)}
if(e.key==='Home')show(0); if(e.key==='End')show(S.length-1);});
S.forEach((s,i)=>{const pg=s.querySelector('.pg');if(pg)pg.textContent=String(i+1).padStart(2,'0')+' / '+S.length;});
function fitAll(){
S.forEach(s=>{const body=s.querySelector('.slide-body'),f=s.querySelector('.fit');
if(!body||!f)return;
s.classList.add('measuring');
f.style.transform='';f.style.width='100%';
let avail=body.clientHeight;
for(let k=0;k<3;k++){
  const h=f.scrollHeight;
  if(h<=avail+2)break;
  const sc=Math.max(0.62,avail/h*(f._sc||1));
  f._sc=sc;f.style.transform='scale('+sc+')';f.style.transformOrigin='bottom left';
  f.style.width=(100/sc)+'%';
  s.dataset.scaled=sc.toFixed(3);
}
s.classList.remove('measuring');});
window._fitDone=true;}
document.fonts.ready.then(()=>requestAnimationFrame(fitAll));
window.addEventListener('load',()=>setTimeout(()=>{if(!window._fitDone)fitAll();},400));
show(0);
"""

doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1280">
<title>봉은문화센터 Master Strategy — 슬라이드 출력본 | PROJECT RENT</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<style>{CSS}</style>
</head>
<body>
<div class="prog"></div>
{chr(10).join(slides)}
<div class="nav"><button onclick="show(cur-1)">‹ 이전</button><span class="cnt"></span><button onclick="show(cur+1)">다음 ›</button></div>
<script>{JS}</script>
</body>
</html>
"""

open(OUT, 'w', encoding='utf-8').write(doc)
_json.dump(CHUNKS, open('deck-chunks.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
n = len(slides)
multi = {k: v for k, v in per_agenda.items() if v > 1}
print(f'→ {OUT}')
print(f'   서브카피 정합: {len(SUB_HIT)}/{len(SUB_HIT)+len(SUB_MISS)} 매칭' + (f"  ⚠️ 미매칭 {len(SUB_MISS)}건: " + ', '.join(k for k, _ in SUB_MISS[:8]) if SUB_MISS else '  ✓'))
print(f'   슬라이드 {n}장 = 표지 2 + STEP 표지 {n - 2 - sum(per_agenda.values())} + 아젠다 {sum(per_agenda.values())}')
print(f'   아젠다 54개 → 분할 분포: 1장 {sum(1 for v in per_agenda.values() if v == 1)}개 · '
      f'2장 {sum(1 for v in per_agenda.values() if v == 2)}개 · '
      f'3장 {sum(1 for v in per_agenda.values() if v == 3)}개 · '
      f'4장+ {sum(1 for v in per_agenda.values() if v >= 4)}개')
big = sorted(((k, v) for k, v in per_agenda.items() if v >= 4), key=lambda x: -x[1])
if big:
    print('   최다 분할:', ' · '.join(f'{k}({v}장)' for k, v in big[:8]))
