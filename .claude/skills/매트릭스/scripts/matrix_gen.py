#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
matrix_gen.py — 축 정의(config) → 전략 매트릭스 IR 생성기

  python3 matrix_gen.py <config.py> [-o out.html]

config가 "무엇을 어느 축으로 나눌 것인가"만 선언하면,
이 엔진이 원자마다 축 값을 채우고 노드·IR을 만든다. 링크는 렌더러가 매번 집계한다.

config가 정의할 것 (자세한 예: ../configs/bongeunsa-matrix.py)
  META      dict          제목·출처 등
  load()    -> list       원자 원본 목록 (dict 아무 형태)
  ATOM      dict          id/label/summary/evidence 를 원본에서 뽑는 함수들
  STAGES    list[dict]    열 정의. 각 열은 axis(축 이름)와 nodes(판정 목록)를 갖는다
  CONCLUSIONS list        선택
  SLOTS     list          선택 — 아직 자료가 없어 비워둔 칸

STAGES 한 항목:
  { 'id':'s1', 'label':'Segment A · Target', 'axis':'target', 'role':'origin',
    'note':'...', 'atomic':False, 'kind':'item'|'group'|'card',
    'nodes': [ {'id':'t-mz', 'label':'MZ · 이슈화', 'match': lambda a: ...,
                'summary':'...', 'evidence':[...], 'caption':'', 'members':[]} ],
    'nodes_fn': lambda atoms: [...]        # nodes 대신 원자에서 동적 생성할 때
    'pick': 'all'|'first'|('rare', k)      # 여러 개 매치될 때 무엇을 남길지
  }
"""
import argparse, importlib.util, json, os, subprocess, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config(path):
    spec = importlib.util.spec_from_file_location('mxcfg', path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['mxcfg'] = mod
    spec.loader.exec_module(mod)
    return mod


def resolve_nodes(stage, atoms):
    """nodes를 그대로 쓰거나, nodes_fn으로 원자에서 만들어낸다."""
    if stage.get('nodes_fn'):
        return stage['nodes_fn'](atoms)
    return stage.get('nodes') or []


def match_axis(stage, nodes, atom, rarity):
    """이 원자가 이 열에서 어느 노드에 걸리는가. pick 규칙으로 좁힌다.

    다중 태깅을 전부 이으면 밀도가 80%를 넘는 완전 이분 그래프가 되어 경로가 사라진다.
    그래서 축마다 '무엇을 주된 것으로 볼지'를 선언하게 했다.
    """
    hit = [n['id'] for n in nodes if n.get('match') and n['match'](atom)]
    if not hit:
        return []
    pick = stage.get('pick', 'all')
    if pick == 'all':
        return hit
    if pick == 'first':
        return hit[:1]
    if isinstance(pick, tuple) and pick[0] == 'rare':
        # 희소한 것일수록 그 원자를 특징짓는다 — 흔한 값보다 변별력이 크다
        return sorted(hit, key=lambda x: rarity.get(x, 0))[:pick[1]]
    return hit


def build(cfg):
    raw = cfg.load()
    A = cfg.ATOM
    atoms_meta = [dict(id=A['id'](x), label=A['label'](x), raw=x) for x in raw]

    stages, nodes, axis_map = [], [], {}
    stage_nodes = {}
    for st in cfg.STAGES:
        stages.append({k: v for k, v in st.items()
                       if k in ('id', 'label', 'order', 'role', 'note', 'atomic', 'filter_only',
                                'dec', 'dec_group')})
        ns = resolve_nodes(st, atoms_meta)
        stage_nodes[st['id']] = ns
        if st.get('axis'):
            axis_map[st['id']] = st['axis']

    # 축별 희소도 — pick='rare'에 쓴다
    rarity = {}
    for st in cfg.STAGES:
        for n in stage_nodes[st['id']]:
            if n.get('match'):
                rarity[n['id']] = sum(1 for a in atoms_meta if n['match'](a['raw']))

    # 원자마다 축 값을 채운다
    atoms = []
    for a in atoms_meta:
        axes = {}
        for st in cfg.STAGES:
            ax = st.get('axis')
            if not ax:
                continue
            hit = match_axis(st, stage_nodes[st['id']], a['raw'], rarity)
            axes[ax] = hit if st.get('multi', True) else (hit[0] if hit else None)
        atoms.append(dict(
            id=a['id'], label=a['label'], axes=axes,
            blocked=bool(A.get('blocked', lambda x: False)(a['raw'])),
            summary=A.get('summary', lambda x: '')(a['raw']),
            evidence=A.get('evidence', lambda x: [])(a['raw'])))

    # 노드 생성 — 라벨에 건수를 박지 않는다(필터를 걸면 거짓이 된다)
    for st in cfg.STAGES:
        for n in stage_nodes[st['id']]:
            node = dict(id=n['id'], stage=st['id'],
                        kind=n.get('kind', st.get('kind', 'item')),
                        label=n['label'], category=n.get('category', st.get('label')),
                        summary=n.get('summary', ''), evidence=n.get('evidence', []))
            for k in ('caption', 'members', 'blocked'):
                if n.get(k) is not None:
                    node[k] = n[k]
            nodes.append(node)

    # 비어 있는 슬롯 — 원자가 없으니 필터와 무관하게 늘 보인다
    for sl in getattr(cfg, 'SLOTS', []):
        nodes.append(dict(id=sl['id'], stage=sl['stage'], kind='item', slot=True,
                          label=sl['label'], category='리서치 필요',
                          summary=sl.get('why', '') + ('\n\n필요한 것 — ' + sl['need']
                                                       if sl.get('need') else ''),
                          evidence=[dict(quote=sl.get('need', ''), src=sl.get('src', '추가 리서치 요청'))]))

    g = dict(meta=dict(cfg.META, render='map', value_basis='equal',
                       link_rule=dict(strong=.60, weak=.35)),
             stages=stages, nodes=nodes, links=[],
             atoms=atoms, axis_map=axis_map,
             conclusions=getattr(cfg, 'CONCLUSIONS', []),
             whitespace=getattr(cfg, 'WHITESPACE', []))
    return g, atoms, stage_nodes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config')
    ap.add_argument('-o', '--out', help='출력 HTML (기본: config의 OUT/<name>.html)')
    ap.add_argument('--json-only', action='store_true')
    a = ap.parse_args()

    cfg = load_config(a.config)
    g, atoms, stage_nodes = build(cfg)

    out_dir = getattr(cfg, 'OUT', os.path.dirname(os.path.abspath(a.config)))
    os.makedirs(out_dir, exist_ok=True)
    name = getattr(cfg, 'NAME', os.path.splitext(os.path.basename(a.config))[0])
    jpath = os.path.join(out_dir, f'{name}-graph.json')
    json.dump(g, open(jpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print(f'원자 {len(atoms)}건 · 축 {len(g["axis_map"])}개 · 단계 {len(g["stages"])}')
    for st in g['stages']:
        n = sum(1 for x in g['nodes'] if x['stage'] == st['id'])
        ax = g['axis_map'].get(st['id'])
        if ax:
            cov = sum(1 for a_ in atoms if a_['axes'].get(ax))
            miss = len(atoms) - cov
            tail = f' · 원자 커버 {cov}/{len(atoms)}' + (f'  ← {miss}건 미분류' if miss else '')
        else:
            tail = ' · 축 없음(슬롯 전용)'
        print(f"  {st['label']:26} {n:>4}개{tail}{'  ← 상세' if st.get('atomic') else ''}")
    print(f'→ {jpath}')

    if a.json_only:
        return
    hpath = a.out or os.path.join(out_dir, f'{name}.html')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'build_sankey.py'), jpath, '-o', hpath])
    if r.returncode:
        sys.exit(r.returncode)

    # 같은 IR로 Decision Map도 뽑는다 — config가 DECISION에 파일명을 적어두면 자동이다.
    # 판정을 한 번 고치면 두 화면이 같이 갱신되게 하는 것이 요점이다.
    dec = getattr(cfg, 'DECISION', None)
    if dec:
        dpath = dec if os.path.isabs(dec) else os.path.join(out_dir, dec)
        r2 = subprocess.run([sys.executable, os.path.join(HERE, 'build_sankey.py'),
                             jpath, '--render', 'decision', '-o', dpath])
        sys.exit(r2.returncode)


if __name__ == '__main__':
    main()
