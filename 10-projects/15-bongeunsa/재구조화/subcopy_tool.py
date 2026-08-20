#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""서브카피 관리 — 위치 키 → 청크 본문 해시 키 전환·점검 (2026-08-19)

배경. 종전 `deck-subcopy.json`은 `{아젠다}/{순번}` 위치 키였다.
재패킹으로 청크 경계가 밀리면 서브카피가 **그럴듯하지만 다른 슬라이드를 설명하는**
상태가 되는데, 이건 읽어봐도 티가 안 나서 사실상 못 찾는다.
2026-08-19 S8/S9 재작성 때 실제로 30건이 통째로 어긋났다.

해시 키는 본문이 바뀌면 **자동으로 분리되어 빈칸**이 될 뿐 절대 오배치되지 않는다.
빈칸은 보이고 오배치는 안 보인다 — 그 비대칭이 이 설계의 이유다.

usage:
  python3 subcopy_tool.py --migrate   # 위치 키 파일 → hash-v1 형식으로 변환(백업 생성)
  python3 subcopy_tool.py --check     # 현재 청크 대비 매칭/미매칭 점검
  python3 subcopy_tool.py --missing   # 서브카피가 비어 있는 청크의 본문을 집필용으로 출력

전제: `deck-chunks.json`이 최신이어야 한다(= build_deck.py를 한 번 돌린 뒤 실행).
"""
import json, os, re, sys, shutil, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
SUB = 'deck-subcopy.json'
CH = 'deck-chunks.json'


def chunk_hash(text):
    """build_deck.py의 동명 함수와 동일해야 한다 — 바꾸려면 양쪽을 같이 바꾼다."""
    norm = re.sub(r'\s+', ' ', text or '').strip()
    return hashlib.sha1(norm.encode('utf-8')).hexdigest()[:12]


def load():
    chunks = json.load(open(CH, encoding='utf-8'))
    raw = json.load(open(SUB, encoding='utf-8')) if os.path.exists(SUB) else {}
    fmt = 'hash-v1' if isinstance(raw, dict) and raw.get('_format') == 'hash-v1' else 'legacy'
    return chunks, raw, fmt


def subs_of(raw, fmt):
    return {k: v['sub'] for k, v in raw.get('entries', {}).items()} if fmt == 'hash-v1' else raw


def migrate():
    chunks, raw, fmt = load()
    if fmt == 'hash-v1':
        print('이미 hash-v1 형식입니다. --check 를 쓰십시오.')
        return
    shutil.copy(SUB, '_old/deck-subcopy.json.bak-poskey')
    entries, carried, dropped = {}, 0, []
    for key, c in chunks.items():
        sub = raw.get(key)
        if not sub:
            dropped.append(key); continue
        h = c.get('hash') or chunk_hash(c['text'])
        entries[h] = {'agenda': key.split('/')[0], 'part': c.get('part', ''),
                      'title': c.get('title', '')[:70], 'sub': sub}
        carried += 1
    orphan = [k for k in raw if k not in chunks]
    out = {
        '_format': 'hash-v1',
        '_note': ('키 = 청크 본문 SHA1[:12]. 본문이 바뀌면 자동 분리되어 빈칸이 될 뿐 '
                  '다른 슬라이드에 잘못 붙지 않는다. 재빌드 후 `subcopy_tool.py --missing` 으로 '
                  '빈칸을 확인하고 집필한다. 해시 계산은 build_deck.chunk_hash 와 동일.'),
        '_migrated': '2026-08-19 · 위치 키에서 전환',
        'entries': entries,
    }
    json.dump(out, open(SUB, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'→ {SUB} hash-v1 전환 · 이관 {carried}건')
    if dropped:
        print(f'   서브카피 없던 청크 {len(dropped)}건: ' + ', '.join(dropped[:10]))
    if orphan:
        print(f'   현재 청크에 없어 버려진 구 키 {len(orphan)}건: ' + ', '.join(orphan[:10]))


def check(show_missing=False):
    chunks, raw, fmt = load()
    subs = subs_of(raw, fmt)
    hit, miss = [], []
    for key, c in chunks.items():
        h = c.get('hash') or chunk_hash(c['text'])
        (hit if subs.get(h) else miss).append((key, h, c))
    print(f'형식 {fmt} · 청크 {len(chunks)} · 매칭 {len(hit)} · 미매칭 {len(miss)}')
    if miss and not show_missing:
        print('  미매칭:', ', '.join(k for k, _, _ in miss[:20]))
        print('  본문을 보려면 --missing')
    if show_missing:
        for key, h, c in miss:
            print(f'\n── [{key}] hash={h} · {c.get("title","")[:50]}')
            print('   ' + c['text'][:400])
    dead = [h for h in subs if h not in {c.get('hash') or chunk_hash(c['text']) for c in chunks.values()}]
    if dead:
        print(f'\n  더 이상 쓰이지 않는 서브카피 {len(dead)}건 (본문이 바뀌었거나 청크가 사라짐)')
    return len(miss)


if __name__ == '__main__':
    if '--migrate' in sys.argv:
        migrate()
    elif '--missing' in sys.argv:
        check(show_missing=True)
    else:
        sys.exit(1 if check() else 0)
