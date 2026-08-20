#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sections/*.html 블록 실측 → deck-measured.json

build_deck.py 주석이 참조하던 스크립트인데 실물이 없어 신규 작성(2026-08-19).
build_deck.py는 blocks 열거 시 data-blk = f'{no}#{j}' 키를 붙이고,
MEASURED[key]가 있으면 추정 대신 실측 px를 써서 패킹·분할을 결정한다.
실측이 없거나 낡으면 과밀 패킹 → 런타임 fitAll()이 0.62까지 축소하고,
그래도 안 되면 내용이 잘린다.

usage: python3 measure_deck.py            # 측정 후 deck-measured.json 갱신
       python3 measure_deck.py --dry      # 파일 쓰지 않고 비교만

열거 규칙은 build_deck.py와 동일해야 한다:
  <section>          → divider + extra(children 중 sec-head/p.sec-desc 제외) → 키 '{sno}.0#{j}'
  .agenda            → children 중 agenda-head·첫 h3 제외 → 키 '{no}#{j}'
측정 컨텍스트도 동일해야 한다: .slide(1280w, padding 40/56/24) > .slide-body > .fit > block
"""
import os, re, glob, json, sys, asyncio
from lxml import html as LH
from lxml import etree

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
OUT = 'deck-measured.json'
DRY = '--dry' in sys.argv


def outer(el): return etree.tostring(el, encoding='unicode', method='html')
def inner(el):
    return (el.text or '') + ''.join(outer(c) for c in el)
def cls(el): return el.get('class') or ''


def parse_file(path):
    raw = open(path, encoding='utf-8').read()
    root = LH.fromstring('<div id="R">' + raw + '</div>')
    return [c for c in root if isinstance(c.tag, str)]


def collect():
    """[(key, block_html)] — build_deck.py의 blocks 열거를 그대로 재현"""
    items = []
    for f in sorted(glob.glob('sections/[0-9]*.html')):
        if f.endswith('00-cover.html'):
            continue
        for el in parse_file(f):
            if el.tag == 'section':
                extra = [c for c in el if isinstance(c.tag, str)
                         and 'sec-head' not in cls(c)
                         and not (c.tag == 'p' and 'sec-desc' in cls(c))]
                if extra:
                    noel = el.find('.//div[@class="no"]')
                    sno = noel.text_content().strip() if noel is not None else ''
                    for j, b in enumerate(extra):
                        items.append((f'{sno}.0#{j}', outer(b)))
            elif 'agenda' in cls(el):
                kids = [c for c in el if isinstance(c.tag, str)]
                no, h3_seen, blocks = '', False, []
                for k in kids:
                    c = cls(k)
                    if 'agenda-head' in c:
                        noel = k.find('.//div[@class="no"]')
                        no = noel.text_content().strip() if noel is not None else ''
                    elif k.tag == 'h3' and not h3_seen:
                        h3_seen = True
                    else:
                        blocks.append(k)
                for j, b in enumerate(blocks):
                    items.append((f'{no}#{j}', outer(b)))
    return items


def deck_css():
    """build_deck.py의 CSS 상수를 그대로 읽어온다 (빌드본과 동일 조건 보장)"""
    src = open('build_deck.py', encoding='utf-8').read()
    m = re.search(r'^CSS = """(.*?)"""', src, re.S | re.M)
    if not m:
        raise SystemExit('build_deck.py에서 CSS 상수를 찾지 못했습니다')
    return m.group(1)


def build_page(items, css):
    cells = ''.join(
        f'<div class="slide meas" data-mk="{k}"><div class="slide-body"><div class="fit">{h}</div></div></div>'
        for k, h in items)
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<style>{css}
/* 측정 전용 오버라이드 — 폭은 슬라이드와 동일하게 두고 높이만 풀어준다 */
.slide.meas{{display:block!important;height:auto!important;overflow:visible!important;
  margin:0 0 24px;box-shadow:none}}
.slide.meas .slide-body{{display:block!important;height:auto!important;overflow:visible!important;flex:none}}
.slide.meas .fit{{transform:none!important;width:100%!important}}
</style></head><body>{cells}</body></html>"""


async def measure(page_html):
    from playwright.async_api import async_playwright
    tmp = os.path.join(BASE, '_measure-tmp.html')
    open(tmp, 'w', encoding='utf-8').write(page_html)
    try:
        async with async_playwright() as p:
            br = await p.chromium.launch()
            pg = await br.new_page(viewport={'width': 1400, 'height': 1000})
            await pg.goto('file://' + tmp)
            await pg.evaluate('document.fonts.ready')
            await pg.wait_for_timeout(1200)
            res = await pg.evaluate("""() => {
              const out = {};
              document.querySelectorAll('.slide.meas').forEach(s => {
                const f = s.querySelector('.fit');
                const b = f && f.firstElementChild;
                if (b) out[s.dataset.mk] = Math.round(b.getBoundingClientRect().height);
              });
              return out;
            }""")
            await br.close()
            return res
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


if __name__ == '__main__':
    items = collect()
    print(f'블록 {len(items)}개 열거')
    css = deck_css()
    new = asyncio.run(measure(build_page(items, css)))
    print(f'실측 {len(new)}개')

    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else {}
    added = [k for k in new if k not in old]
    gone = [k for k in old if k not in new]
    diff = [(k, old[k], new[k]) for k in new if k in old and abs(new[k] - old[k]) >= 8]
    diff.sort(key=lambda x: -abs(x[2] - x[1]))
    print(f'  신규 {len(added)} · 소멸 {len(gone)} · 8px 이상 변동 {len(diff)}')
    for k, o, n in diff[:15]:
        print(f'    {k:<12}{o:>6} → {n:>6}  ({n-o:+})')
    if added[:10]:
        print('  신규 키:', ', '.join(added[:10]))

    if DRY:
        print('--dry — 파일 쓰지 않음')
    else:
        json.dump(new, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(f'→ {OUT} 갱신 ({len(new)}블록)')
