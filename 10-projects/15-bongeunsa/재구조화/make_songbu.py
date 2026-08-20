#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""출력본(내부용) → 송부본(대외 배포용) redaction

🔴 이 스크립트가 없으면 출력본을 이름만 바꿔 보내게 되고, 계약 협상 내부 정보가 발주처로 나간다.
   2026-08-19 이전에는 이 편집 패스가 손으로만 이뤄졌고 문서에도 없었다 — 그래서 스크립트로 고정한다.

usage: python3 make_songbu.py [--check]
  --check : 파일을 쓰지 않고 무엇이 제거되는지만 출력

redaction 규칙 (기존 송부본을 역설계해 확정)
  1) <h4>…<span class="internal">내부 전용</span></h4>  → h4 통째로 제거 (본문은 유지)
  2) <p><strong>내부 전용 …</strong>… </p>              → p 통째로 제거
  3) 그 외 <span class="internal">내부 전용</span>       → span만 제거 (문단은 유지)
  4) 「내부 전용」이 아닌 internal 라벨(예: '2026-08-14 갱신', '과업 범위 밖 · 제언 형태')은 그대로 둔다
  5) 표지 문구 : Internal Working Document · 출력용 슬라이드판 → Final Report · 최종 송부본
  6) <title>    : 슬라이드 출력본 → 최종 송부본
  7) '이 문서의 위치' 콜아웃 제거 (내부 문서 위치 설명)
  8) .fit p.lead 스타일 1줄 추가 (대외판 전용 리드 문단 서식)
"""
import os, re, sys
from lxml import html as LH
from lxml import etree

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
SRC = '봉은문화센터-master-strategy-deck-출력본.html'
DST = '봉은문화센터-master-strategy-deck-송부본.html'
CHECK = '--check' in sys.argv

LEAD_CSS = ('.fit p.lead{font-size:14px;color:var(--fg);border-left:3px solid var(--accent);'
            'padding-left:14px;margin:8px 0 16px}')


def drop(el):
    p = el.getparent()
    if p is None:
        return
    tail = el.tail or ''
    prev = el.getprevious()
    if prev is not None:
        prev.tail = (prev.tail or '') + tail
    else:
        p.text = (p.text or '') + tail
    p.remove(el)


def redact(src_html):
    doc = LH.document_fromstring(src_html)
    removed = []

    for span in list(doc.xpath('//span[@class="internal"]')):
        label = (span.text_content() or '').strip()
        if not label.startswith('내부 전용'):
            continue                      # 규칙 4 — 다른 라벨은 유지
        host = span.getparent()
        if host is None:
            continue
        if host.tag == 'h4':              # 규칙 1
            removed.append(('h4', re.sub(r'\s+', ' ', host.text_content()).strip()[:50]))
            drop(host)
        elif host.tag == 'p' and re.sub(r'\s+', ' ', host.text_content()).strip().startswith('내부 전용'):
            removed.append(('p', re.sub(r'\s+', ' ', host.text_content()).strip()[:50]))
            drop(host)                    # 규칙 2
        else:
            removed.append(('span', re.sub(r'\s+', ' ', host.text_content()).strip()[:50]))
            drop(span)                    # 규칙 3

    # 규칙 7 — '이 문서의 위치' 콜아웃
    for d in list(doc.xpath('//div[@class="callout"]')):
        if '이 문서의 위치' in d.text_content():
            removed.append(('callout', '이 문서의 위치'))
            drop(d)

    out = etree.tostring(doc, encoding='unicode', method='html', doctype='<!doctype html>')

    # 규칙 5·6 — 문자열 치환
    subs = [
        ('Project Rent · Internal Working Document · 출력용 슬라이드판',
         'Project Rent · Final Report · 최종 송부본'),
        ('봉은문화센터 Master Strategy — 슬라이드 출력본 | PROJECT RENT',
         '봉은문화센터 Master Strategy — 최종 송부본 | PROJECT RENT'),
    ]
    for a, b in subs:
        if a not in out:
            print(f'   ⚠️ 치환 대상 미발견: {a[:46]}')
        out = out.replace(a, b)

    # 규칙 8 — 리드 문단 스타일
    if LEAD_CSS not in out:
        anchor = '.measuring{'
        i = out.find(anchor)
        if i > 0:
            out = out[:i] + LEAD_CSS + '\n' + out[i:]
        else:
            print('   ⚠️ CSS 앵커 미발견 — .fit p.lead 미삽입')
    return out, removed


if __name__ == '__main__':
    src = open(SRC, encoding='utf-8').read()
    out, removed = redact(src)
    print(f'제거 {len(removed)}건')
    for kind, txt in removed:
        print(f'   [{kind:<7}] {txt}')

    leak = re.findall(r'내부 전용', out)
    print(f'\n잔존 "내부 전용": {len(leak)}건  {"✓" if not leak else "✗ 유출 위험"}')
    for s in ('추가합의서가 바꾼 네 가지', '수정요구를 어디까지 받는가', '회색지대를 회색지대라고',
              'Internal Working Document'):
        print(f'   {s[:30]:<32}{"✗ 잔존" if s in out else "✓ 제거"}')

    if CHECK:
        print('\n--check — 파일 쓰지 않음')
    else:
        open(DST, 'w', encoding='utf-8').write(out)
        print(f'\n→ {DST}  ({len(out)/1024:.0f}KB)')
