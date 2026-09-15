#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_sankey.py — sankey-graph.json 검증 + 빈틈 탐지 + HTML 생성

  python3 build_sankey.py graph.json [-o report.html] [--absorb] [--strict]

역할 분담:
  매핑 판단(어느 필드가 어느 단계인가, 결론 문장) = LLM
  산술·검증·탐지                                  = 이 스크립트 (결정론적)

규칙 SSOT: ../references/flow-grammar.md, ../references/whitespace.md
FAIL이 하나라도 있으면 HTML을 만들지 않고 종료 코드 1로 멈춘다.
"""
import argparse, json, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TPL = os.path.join(HERE, '..', 'templates', 'sankey-report.html')
MAP_TPL = os.path.join(HERE, '..', 'templates', 'concept-map.html')
DEC_TPL = os.path.join(HERE, '..', 'templates', 'decision-map.html')
MARK_A = '<script id="graph-data" type="application/json">'
MARK_B = '</' + 'script>'
HUB_RATIO = 2.5      # 같은 단계 평균의 몇 배부터 hub로 볼 것인가
MIN_SPLIT = 0.25     # collision — 2위 결론 도달 비중이 이보다 작으면 "갈렸다"고 보지 않는다
MAX_PER_TYPE = 8     # 유형별 상한. 넘으면 잘라내되 반드시 로그로 알린다(조용한 절삭 금지)

def josa(word, pair='이/가'):
    """받침에 맞는 조사를 붙인다. pair는 '받침있음/받침없음' 순서."""
    a, b = pair.split('/')
    w = str(word).rstrip()
    if not w:
        return w
    ch = w[-1]
    if '가' <= ch <= '힣':
        has = (ord(ch) - 0xAC00) % 28 != 0
    elif ch.isdigit():
        has = ch in '0136780'          # 영·일·삼·육·칠·팔·십
    else:
        has = True                      # 영문·기호는 받침 있는 쪽으로 (안전)
    return w + (a if has else b)


fails, warns, notes = [], [], []
def FAIL(m): fails.append(m)
def WARN(m): warns.append(m)
def NOTE(m): notes.append(m)


def validate(g):
    """flow-grammar.md R1~R5. 반환: 파생 색인"""
    meta = g.get('meta') or {}
    for k in ('title', 'source', 'axis', 'mode', 'value_basis'):
        if not meta.get(k):
            FAIL(f'meta.{k} 누락')
    if meta.get('value_basis') not in ('count', 'evidence', 'equal'):
        FAIL(f"meta.value_basis는 count|evidence|equal 중 하나여야 함 (현재: {meta.get('value_basis')})")
    if meta.get('axis') not in ('topic', 'time'):
        FAIL(f"meta.axis는 topic|time (현재: {meta.get('axis')})")
    if meta.get('mode') not in ('structure', 'generate'):
        FAIL(f"meta.mode는 structure|generate (현재: {meta.get('mode')})")
    render = meta.get('render', 'sankey')
    if render not in ('sankey', 'map', 'decision'):
        FAIL(f"meta.render는 sankey|map|decision (현재: {render})")
    if render == 'map' and meta.get('value_basis') != 'equal':
        WARN("render=map은 선 굵기를 쓰지 않는다 — value_basis를 equal로 두는 게 정확하다")

    stages = sorted(g.get('stages') or [], key=lambda s: s['order'])
    if not stages:
        FAIL('stages 비어 있음'); return None
    if render != 'decision' and stages[0].get('role') != 'origin':
        FAIL(f"첫 단계 role은 origin이어야 함 (현재: {stages[0].get('role')})")
    # R1 — 마지막은 반드시 conclusion (decision 모드 제외: 열이 흐름이 아니라 선택 축이다)
    if render != 'decision' and stages[-1].get('role') != 'conclusion':
        FAIL(f"마지막 단계 role은 conclusion이어야 함 (현재: {stages[-1].get('role')}) — 결론 없는 흐름도는 산출물이 아님")
    if len(stages) > 6:
        WARN(f'단계 {len(stages)}개 — 6개를 넘으면 화면에서 읽히지 않음')
    if len(stages) < 3:
        WARN(f'단계 {len(stages)}개 — 3단계 미만은 흐름이 드러나지 않음')

    sorder = {s['id']: i for i, s in enumerate(stages)}
    slabel = {s['id']: s.get('label', s['id']) for s in stages}

    nodes = g.get('nodes') or []
    nmap = {}
    last_id = stages[-1]['id']
    for n in nodes:
        if n['id'] in nmap:
            FAIL(f"노드 id 중복: {n['id']}")
        nmap[n['id']] = n
        if n.get('stage') not in sorder:          # R5
            FAIL(f"노드 {n['id']}의 stage '{n.get('stage')}'가 stages에 없음")
        if render == 'map':                        # map 전용 필드 검사
            kind = n.get('kind', 'item')
            if kind not in ('item', 'group', 'card'):
                FAIL(f"노드 {n['id']}의 kind는 item|group|card (현재: {kind})")
            elif kind == 'card' and n.get('stage') != last_id:
                WARN(f"노드 {n['id']}가 kind=card인데 결론 단계가 아니다 — 카드는 결론 열에만 둔다")
            elif kind == 'item' and n.get('members'):
                WARN(f"노드 {n['id']}는 kind=item인데 members가 있다 — group/card로 바꾸지 않으면 화면에 안 보인다")

    # R3/R4/R5 — 링크
    links, seen = [], set()
    for i, l in enumerate(g.get('links') or []):
        lid = l.get('id') or f"l{i}-{l.get('source')}>{l.get('target')}"
        l['id'] = lid
        if lid in seen:
            FAIL(f'링크 id 중복: {lid}')
        seen.add(lid)
        s, t = l.get('source'), l.get('target')
        if s not in nmap or t not in nmap:
            FAIL(f'링크 {lid}: 미해결 노드 참조 ({s} → {t})'); continue
        try:
            v = float(l.get('value'))
        except (TypeError, ValueError):
            FAIL(f'링크 {lid}: value가 숫자가 아님'); continue
        if v <= 0:
            FAIL(f'링크 {lid}: value는 0보다 커야 함 (현재 {v})'); continue
        so, to = sorder[nmap[s]['stage']], sorder[nmap[t]['stage']]
        if render == 'decision':
            links.append(l); continue              # decision은 양방향 탐색이라 순서를 강제하지 않는다
        if so >= to:                               # R3-1 역방향/동일단계 금지 → DAG 보장
            FAIL(f'링크 {lid}: 역방향 또는 동일 단계 연결 ({slabel[nmap[s]["stage"]]} → {slabel[nmap[t]["stage"]]}) — d3-sankey가 무한루프에 빠짐')
            continue
        if to - so > 1:                            # R3-2 건너뛰기는 경고
            WARN(f'링크 {lid}: 단계 건너뜀 ({slabel[nmap[s]["stage"]]} → {slabel[nmap[t]["stage"]]}) — 화면에 점선으로 표시됨')
        links.append(l)

    if fails:
        return None

    ins, outs = defaultdict(list), defaultdict(list)
    for l in links:
        outs[l['source']].append(l)
        ins[l['target']].append(l)

    # R4 — 값 정합(중간 유실). map 모드는 선이 '관계'라 유량 개념이 없으므로 검사하지 않는다.
    last_stage = stages[-1]['id']
    loss = []
    for n in (nodes if render == 'sankey' else []):
        if n['stage'] in (stages[0]['id'], last_stage):
            continue
        i, o = sum(x['value'] for x in ins[n['id']]), sum(x['value'] for x in outs[n['id']])
        if i - o > 1e-6:
            loss.append((n, i - o))

    # ── 원자 레이어 (atoms + axis_map) — 있으면 링크는 렌더러가 매번 집계한다
    atoms = g.get('atoms') or []
    axis_map = g.get('axis_map') or {}
    aids = {a.get('id') for a in atoms}
    if atoms:
        if not axis_map:
            FAIL('atoms가 있는데 axis_map이 없다 — 어느 stage가 어느 축인지 알 수 없다')
        for sid in axis_map:
            if sid not in sorder:
                FAIL(f"axis_map의 stage '{sid}'가 stages에 없음")
        bad_ref, hit = [], set()
        for a in atoms:
            for ax_stage, ax_name in axis_map.items():
                v = (a.get('axes') or {}).get(ax_name)
                for x in ([] if v is None else (v if isinstance(v, list) else [v])):
                    if x not in nmap:
                        bad_ref.append(f"{a.get('id')}.{ax_name}={x}")
                    else:
                        hit.add(x)
        if bad_ref:
            FAIL(f'원자 축이 없는 노드를 가리킴 {len(bad_ref)}건: ' + ', '.join(bad_ref[:5]) +
                 (' …' if len(bad_ref) > 5 else ''))
        idle = [n['id'] for n in nodes
                if axis_map.get(n['stage']) and n['id'] not in hit]
        if idle:
            WARN(f'어떤 원자도 안 걸린 노드 {len(idle)}건: ' + ', '.join(idle[:6]) +
                 (' …' if len(idle) > 6 else ''))

    # R5 — 결론 무결성
    concls = g.get('conclusions') or []
    lids = {l['id'] for l in links} | aids   # atoms가 있으면 링크는 동적이라 원자 id를 근거로 쓴다
    for c in concls:
        nid = c.get('node_id')
        if nid not in nmap:
            FAIL(f"결론의 node_id '{nid}'가 노드에 없음"); continue
        if nmap[nid]['stage'] != last_stage:
            FAIL(f"결론 '{nid}'는 conclusion 단계 노드가 아님")
        sup = c.get('support') or []
        if not sup:
            FAIL(f"결론 '{c.get('statement','')[:30]}...'에 support가 없음 — 근거 없는 결론은 만들지 않는다")
        bad = [x for x in sup if x not in lids]
        if bad:
            FAIL(f"결론 '{nid}'의 support에 없는 링크: {bad}")
    if not concls and render != 'decision':
        WARN('conclusions가 비어 있음 — 결론 카테고리를 만들지 않았다면 이 도구를 반만 쓴 것')
    return dict(stages=stages, sorder=sorder, slabel=slabel, nmap=nmap,
                nodes=nodes, links=links, ins=ins, outs=outs,
                last_stage=last_stage, loss=loss, meta=meta, render=render,
                atoms=atoms, axis_map=axis_map)

def set_flags(ctx):
    """orphan / dead_end / hub 자동 부여"""
    if ctx.get('render') == 'decision' or ctx.get('atoms'):
        return          # 관계를 노드 필드·원자로 표현하는 모드는 링크 기반 플래그가 의미 없다
    ins, outs, last = ctx['ins'], ctx['outs'], ctx['last_stage']
    counts = defaultdict(list)
    for n in ctx['nodes']:
        n.setdefault('flags', [])
        n['flags'] = [f for f in n['flags'] if f not in ('orphan', 'dead_end', 'hub')]
        i, o = len(ins[n['id']]), len(outs[n['id']])
        if i == 0 and o == 0:
            n['flags'].append('orphan')
        elif i > 0 and o == 0 and n['stage'] != last:
            n['flags'].append('dead_end')
        flow = max(sum(x['value'] for x in ins[n['id']]),
                   sum(x['value'] for x in outs[n['id']]))
        n['__flow'] = flow
        counts[n['stage']].append(flow)
    for n in ctx['nodes']:
        if n['stage'] == last:      # 결론 노드는 몰리는 게 정상이다 — hub로 보지 않는다
            continue
        peers = counts[n['stage']]
        avg = sum(peers) / len(peers) if peers else 0
        if avg > 0 and n['__flow'] >= HUB_RATIO * avg and len(peers) > 2:
            n['flags'].append('hub')


def detect_whitespace(ctx, g):
    """whitespace.md 7종. 기존 항목은 유지하고 새로 찾은 것만 병합."""
    nmap, ins, outs = ctx['nmap'], ctx['ins'], ctx['outs']
    sorder, stages, last = ctx['sorder'], ctx['stages'], ctx['last_stage']
    lab = lambda i: nmap[i].get('label', i)
    found = []
    linkset = {(l['source'], l['target']) for l in ctx['links']}

    by_stage = defaultdict(list)
    for n in ctx['nodes']:
        by_stage[n['stage']].append(n)

    # 1. empty_cell — 양쪽 다 활발한데 이 조합만 비어 있음
    #    결론 단계는 제외한다. 결론 매핑은 대개 배타적이라 "안 간 것"이 당연하고, 그걸 빈틈이라 부르면 노이즈가 된다.
    for a_st, b_st in zip(stages, stages[1:]):
        if b_st.get('role') == 'conclusion':
            continue
        for a in by_stage[a_st['id']]:
            if len(outs[a['id']]) < 2:
                continue
            for b in by_stage[b_st['id']]:
                if len(ins[b['id']]) < 2 or (a['id'], b['id']) in linkset:
                    continue
                found.append(dict(type='empty_cell', where=[a['id'], b['id']],
                    question=f"{lab(a['id'])}에서 {josa(lab(b['id']), '으로/로')} 가는 경로가 왜 없는가 — 불가능한가, 안 해본 것인가?",
                    idea=f"{lab(a['id'])} × {lab(b['id'])} 조합 — 경쟁자가 없는 구간"))

    # 2. orphan  3. hub  7. dead_end
    for n in ctx['nodes']:
        f = n.get('flags', [])
        if 'orphan' in f:
            found.append(dict(type='orphan', where=[n['id']],
                question=f"{josa(lab(n['id']))} 어떤 흐름에도 안 걸린 이유는? 분류 축이 이걸 못 담는 건 아닌가?",
                idea=f"{josa(lab(n['id']), '을/를')} 담으려면 어떤 관점/단계가 새로 필요한가"))
        if 'hub' in f:
            found.append(dict(type='hub', where=[n['id']],
                question=f"{lab(n['id'])}에 흐름이 몰리는데 하류가 {len(outs[n['id']])}갈래뿐인 이유는?",
                idea=f"{josa(lab(n['id']), '을/를')} 여러 갈래로 쪼개면 각각 무엇이 되는가"))
        if 'dead_end' in f:
            found.append(dict(type='dead_end', where=[n['id']],
                question=f"{josa(lab(n['id']), '은/는')} 여기서 왜 끊겼는가 — 결론이 안 난 것인가, 기록이 빠진 것인가?",
                idea=f"{josa(lab(n['id']), '을/를')} 결론까지 밀면 어떤 판단이 필요한가"))

    # 4. triad — 같은 뿌리에서 갈라진 둘이 끝까지 안 만남
    for a in ctx['nodes']:
        kids = [l['target'] for l in outs[a['id']]]
        for i in range(len(kids)):
            for j in range(i + 1, len(kids)):
                b, c = kids[i], kids[j]
                if nmap[b]['stage'] != nmap[c]['stage']:
                    continue
                db = {l['target'] for l in outs[b]}
                dc = {l['target'] for l in outs[c]}
                if db and dc and not (db & dc):
                    found.append(dict(type='triad', where=[a['id'], b, c],
                        question=f"{josa(lab(b), '과/와')} {josa(lab(c), '은/는')} 같은 {lab(a['id'])}에서 나왔는데 왜 끝까지 안 만나는가?",
                        idea=f"{lab(b)} + {lab(c)}를 하나로 묶는 결론이 성립하는가"))

    # 5. collision — 같은 원인이 서로 다른 결론으로 "의미 있게" 갈림
    #    결론까지의 도달 유량을 비율로 계산하고, 2위 결론이 MIN_SPLIT 이상일 때만 잡는다.
    #    소수가 새는 것(부정 감성 2%가 리스크로 흐르는 식)까지 잡으면 전부 collision이 되어 쓸모가 없다.
    memo = {}
    def reach_ratio(nid):
        if nid in memo:
            return memo[nid]
        if nmap[nid]['stage'] == last:
            memo[nid] = {nid: 1.0}; return memo[nid]
        tot = sum(l['value'] for l in outs[nid])
        acc = {}
        if tot:
            for l in outs[nid]:
                w = l['value'] / tot
                for k, v in reach_ratio(l['target']).items():
                    acc[k] = acc.get(k, 0.0) + v * w
        memo[nid] = acc
        return acc

    for n in ctx['nodes']:
        if n['stage'] == last or len(outs[n['id']]) < 2:
            continue
        r = sorted(reach_ratio(n['id']).items(), key=lambda kv: -kv[1])
        if len(r) >= 2 and r[1][1] >= MIN_SPLIT:
            names = ' / '.join(f'{lab(k)} {v:.0%}' for k, v in r[:3])
            found.append(dict(type='collision', where=[n['id']],
                question=f"{josa(lab(n['id']))} {names}로 갈렸다 — 무엇이 방향을 갈랐는가?",
                idea="그 갈림 조건 자체를 새 단계로 세우면 무엇이 보이는가"))

    # 6. thin_path — 근거가 얇은 결론
    for c in (g.get('conclusions') or []):
        sup = c.get('support') or []
        nid = c.get('node_id')
        lowratio = 0.0
        if nid in ins and ins[nid]:
            low = sum(1 for l in ins[nid] if l.get('confidence') == 'low')
            lowratio = low / len(ins[nid])
        if len(sup) <= 1 or lowratio > 0.5:
            why = f"근거가 {len(sup)}건뿐" if len(sup) <= 1 else f"유입 링크의 {lowratio:.0%}가 low 신뢰도"
            found.append(dict(type='thin_path', where=[nid],
                question=f"'{c.get('statement','')}'를 뒷받침하는 {why}이다 — 더 있는가, 아니면 취소할 것인가?",
                idea="이 결론을 확인하려면 어떤 데이터를 더 봐야 하는가"))

    existing = {(w.get('type'), tuple(w.get('where') or [])) for w in (g.get('whitespace') or [])}
    merged = list(g.get('whitespace') or [])
    for w in found:
        if (w['type'], tuple(w['where'])) not in existing:
            merged.append(w); existing.add((w['type'], tuple(w['where'])))
    order = dict(thin_path=0, collision=1, dead_end=2, empty_cell=3, hub=4, triad=5, orphan=6)
    merged.sort(key=lambda w: order.get(w.get('type'), 9))

    # 유형별 상한 — 절삭했으면 반드시 알린다
    kept, seen_n = [], defaultdict(int)
    for w in merged:
        t = w.get('type')
        seen_n[t] += 1
        if seen_n[t] <= MAX_PER_TYPE:
            kept.append(w)
    for t, c in seen_n.items():
        if c > MAX_PER_TYPE:
            NOTE(f'빈틈 {t}: {c}건 중 상위 {MAX_PER_TYPE}건만 표시 (나머지 {c - MAX_PER_TYPE}건 생략)')
    return kept

def absorb_loss(ctx, g):
    """중간 유실을 결론 단계의 '미분류' 노드로 흡수 — 흐름 보존을 지킨다"""
    if not ctx['loss']:
        return 0
    nid = '__unclassified'
    if nid not in ctx['nmap']:
        node = dict(id=nid, stage=ctx['last_stage'], label='미분류 · 추적 실패',
                    category='unclassified',
                    summary='상류에서 들어왔으나 하류로 이어지지 않은 유량. 흐름 보존을 위해 흡수한 값이다.',
                    evidence=[], flags=[])
        g['nodes'].append(node); ctx['nmap'][nid] = node
    for n, amt in ctx['loss']:
        g['links'].append(dict(id=f"__loss-{n['id']}", source=n['id'], target=nid,
                               value=round(amt, 4), confidence='low',
                               note='값 정합 보정 — 하류로 추적되지 않은 유량'))
    return len(ctx['loss'])


def report(ctx, g):
    m, st = ctx['meta'], ctx['stages']
    roles = defaultdict(int)
    for s in st:
        roles[s.get('role')] += 1
    fl = defaultdict(int)
    for n in ctx['nodes']:
        for f in n.get('flags', []):
            fl[f] += 1
    print('[검증] sankey-graph.json')
    print(f"  스테이지     {len(st)}개 ({', '.join(f'{k} {v}' for k, v in roles.items())})")
    print(f"  노드         {len(ctx['nodes'])}개" +
          (f" (orphan {fl['orphan']}, dead_end {fl['dead_end']}, hub {fl['hub']})" if fl else ''))
    print(f"  링크         {len(ctx['links'])}개" +
          ('  (원자에서 렌더러가 매번 집계)' if ctx.get('atoms') else ''))
    if ctx.get('atoms'):
        print(f"  원자         {len(ctx['atoms'])}건 · 축 {len(ctx['axis_map'])}개 · 미해결 참조 0")
    print(f"  DAG          역방향 0건 (단계 순서로 순환 원천 차단)")
    # 총량 대조 — 시작 유량이 결론까지 얼마나 보존되는가 (map 모드는 유량이 없어 건너뛴다)
    first = st[0]['id']
    if ctx.get('render') in ('map', 'decision'):
        print(f"  렌더         {ctx['render']}" +
              (' (선은 관계만 표시 — 유량 검사 없음)' if ctx['render'] == 'map'
               else ' (양방향 의사결정 — 흐름·유량 검사 없음)'))
    else:
        src_tot = sum(l['value'] for l in ctx['links'] if ctx['nmap'][l['source']]['stage'] == first)
        dst_tot = sum(l['value'] for l in ctx['links'] if ctx['nmap'][l['target']]['stage'] == ctx['last_stage'])
        if src_tot > 0:
            drift = abs(dst_tot - src_tot) / src_tot
            mark = 'OK' if drift <= 0.005 else 'WARN'
            print(f"  총량 보존     시작 {src_tot:,.1f} → 결론 {dst_tot:,.1f} (오차 {drift:.2%})  {mark}")
            if drift > 0.005:
                WARN(f'시작 유량과 결론 유량이 {drift:.1%} 어긋남 — 안분 반올림이 누적됐거나 매핑이 빠졌다')
    print(f"  결론         {len(g.get('conclusions') or [])}개, support 링크 전부 유효")
    print(f"  value_basis  {m.get('value_basis')}" + (f" ({m['value_note']})" if m.get('value_note') else ''))
    if m.get('value_basis') == 'equal':
        print('               ※ 두께에 의미 없음 — 화면에 경고 배지 표시됨')
    if g.get('whitespace'):
        wc = defaultdict(int)
        for w in g['whitespace']:
            wc[w['type']] += 1
        print(f"  빈틈         {len(g['whitespace'])}건 ({', '.join(f'{k} {v}' for k, v in wc.items())})")
    for w in warns:
        print(f'  WARN  {w}')
    for n in notes:
        print(f'  NOTE  {n}')


def build_html(g, tpl_path, out_path):
    with open(tpl_path, encoding='utf-8') as f:
        tpl = f.read()
    a = tpl.index(MARK_A) + len(MARK_A)
    b = tpl.index(MARK_B, a)
    payload = json.dumps(g, ensure_ascii=False, indent=1)
    if MARK_B.lower() in payload.lower():
        raise SystemExit('데이터에 script 종료 태그가 포함되어 있어 주입할 수 없습니다')
    html = tpl[:a] + '\n' + payload + '\n' + tpl[b:]
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('graph')
    ap.add_argument('-o', '--out', help='출력 HTML 경로 (기본: graph.json과 같은 폴더의 sankey-report.html)')
    ap.add_argument('-t', '--template', default=None,
                    help='기본은 meta.render에 따라 자동 선택 (sankey→sankey-report.html, map→concept-map.html)')
    ap.add_argument('--absorb', action='store_true', help="중간 유실을 '미분류' 노드로 흡수")
    ap.add_argument('--strict', action='store_true', help='WARN도 실패로 취급')
    ap.add_argument('--check-only', action='store_true', help='검증만 하고 HTML은 만들지 않음')
    ap.add_argument('--render', choices=('sankey', 'map', 'decision'), default=None,
                    help='meta.render를 덮어쓴다 — IR 하나로 다른 화면을 뽑을 때 (예: 매트릭스 IR → decision)')
    a = ap.parse_args()

    with open(a.graph, encoding='utf-8') as f:
        g = json.load(f)

    if a.render:                      # 같은 IR에서 다른 화면 — 원본 파일은 건드리지 않는다
        g = json.loads(json.dumps(g))
        g['meta'] = dict(g.get('meta') or {}, render=a.render)

    ctx = validate(g)
    if fails:
        print('[검증 실패] HTML을 만들지 않고 멈춥니다', file=sys.stderr)
        for x in fails:
            print(f'  FAIL  {x}', file=sys.stderr)
        sys.exit(1)

    set_flags(ctx)
    if a.absorb:
        k = absorb_loss(ctx, g)
        if k:
            NOTE(f"중간 유실 {k}건을 '미분류' 노드로 흡수함")
            ctx = validate(g)          # 흡수 후 재검증
            if fails:
                print('[재검증 실패]', *[f'  FAIL  {x}' for x in fails], sep='\n', file=sys.stderr)
                sys.exit(1)
            set_flags(ctx)
    elif ctx['loss']:
        WARN(f"중간 유실 {len(ctx['loss'])}건 (합 {sum(v for _, v in ctx['loss']):.1f}) — "
             f"--absorb로 '미분류' 노드에 흡수하거나 원인을 밝힐 것")

    if ctx['meta'].get('mode') == 'generate' and ctx.get('render') != 'decision':
        g['whitespace'] = detect_whitespace(ctx, g)

    for n in ctx['nodes']:
        n.pop('__flow', None)

    report(ctx, g)
    if a.strict and warns:
        print('[strict] WARN이 있어 중단합니다', file=sys.stderr); sys.exit(1)
    if a.check_only:
        return

    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.graph)), 'sankey-report.html')
    tpl = a.template or {'map': MAP_TPL, 'decision': DEC_TPL}.get(ctx.get('render'), DEFAULT_TPL)
    build_html(g, tpl, out)
    print(f'\n  → {out}')
    if a.render:       # 화면만 바꿔 뽑은 것 — 원본 IR을 render 값으로 덮으면 안 된다
        print(f'  · {a.graph}는 그대로 둠 (render={a.render}로 화면만 바꿔 뽑음)')
    else:
        with open(a.graph, 'w', encoding='utf-8') as f:
            json.dump(g, f, ensure_ascii=False, indent=2)
        print(f'  → {a.graph} (flags·whitespace 반영본으로 갱신)')


if __name__ == '__main__':
    main()
