#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[폐기 · 2026-07-31] 봉은문화센터 Decision Map — 구 생성 경로

⚠️ 이 파일은 더 이상 쓰지 않는다. Decision Map은 이제 매트릭스와 **같은 IR**에서 나온다:

    python3 ../scripts/matrix_gen.py bongeunsa-matrix.py    # → 매트릭스 + Decision Map 둘 다

판정 로직이 이 파일과 bongeunsa-matrix.py로 갈라져 있던 탓에 실제로 한쪽이 낡았다 —
C→D 연계 22개·수익 항목 77개·비즈니스 모델 5유형이 이 파일에는 없다.
축 판정의 SSOT는 bongeunsa-matrix.py다. 이 파일은 통합 전후를 대조하려고 남겨둔 것뿐이다.

구 경로(대조용):
  python3 bongeunsa-decision.py && python3 ../scripts/build_sankey.py <out>/decision-map-graph.json -o <out>/decision-map.html

좌→우 흐름도가 아니라 양방향 필터다. 어느 열을 눌러도 나머지가 그 조건으로 좁혀진다.
매트릭스(bongeunsa-matrix.py)와 같은 원본을 쓰되, 서비스 116건을 낱개로 훑는 용도다.

⚠️ 이 파일의 TARGETS(99~135행)는 bongeunsa-matrix.py의 TARGET_NODES를 복제한 것이고
   pick도 다르다([:3] vs ('rare',2)). SSOT를 고쳐도 여기는 따라오지 않는다.
   대조 목적으로만 읽고, 새로 실행하지 마라.

❌ 확장 예정 1번은 취소됐다 (2026-08-02 검토)
  ~~1. Target 해석 — TARGETS의 판정을 리서치 자료 기준으로 교체 (S4-O2a~f)~~
  → **불가능하다.** match의 입력은 서비스의 viability(조건부 생존성)이고 실측은 방문객
    속성이라 층위가 다르다. 서비스 116건 중 타겟 슬롯(S4-O2*)이 붙은 것은 2건뿐이라
    실측이 닿을 필드가 없다. "외국인 방문률 5.26%"를 어디에 넣어도 '리테일 모델
    라이선싱'은 외국인 노드에 계속 붙는다.
    실측 기반 타겟은 bongeunsa-demand-matrix.py에 별도로 있다(원자가 수요 54건).
    이 판정을 실제로 바꾸려면 서비스 116건에 demand_target을 사람이 다시 태깅해야 한다.

⚠️ 남은 확장 예정
  2. Research 레이어 — RS에 슬롯을 추가하면 우측 패널에 붙는다
  3. 컨셉 해석 구조 — stages에 열을 추가하고 role을 정하면 된다
"""
import json, os
from collections import Counter, defaultdict

WS = '/Users/choi_ai/do-better-workspace'
SRC = '10-projects/15-bongeunsa/재구조화/elements.json'
RPT = '10-projects/15-bongeunsa/재구조화/봉은문화센터-master-strategy-report.html'
PROG = '10-projects/15-bongeunsa/15-progress.md'
OUT = os.path.join(WS, '10-projects/15-bongeunsa/sankey')
os.makedirs(OUT, exist_ok=True)

EL = json.load(open(os.path.join(WS, SRC), encoding='utf-8'))
SV = [x for x in EL if x.get('kind') == 'service']
vb = lambda s, ax: (s.get('viability') or {}).get(ax, [])
tier = lambda s: (s.get('eval') or {}).get('legal')
gid = lambda s: s.get('group', '')[:3].strip()

N = []
add = lambda **k: N.append(dict(evidence=k.pop('ev', []), **k))

# ── Concept (시작점) ─────────────────────────────────────────────
CONCEPTS = [
    ('C-A', 'Concept A', 'Cultural Destination',
     '한국 불교를 가장 먼저 떠올리게 하는 상징적 문화 목적지\n'
     '엔진 Attract (밖→안) · 상징성·대중성·관광 · 외국인/MZ/일반 방문객'),
    ('C-B', 'Concept B', 'Premium Wellness Center',
     '불교 문화와 프리미엄 웰니스를 결합한 강남형 멤버십 플랫폼\n'
     '엔진 Engage (안에서 더 깊이) · 프리미엄·멤버십·수익성 · 강남 고소득층/기업/VIP'),
    ('C-C', 'Concept C', 'Content & Business Lab',
     '불교 콘텐츠를 상품화해 전국 사찰로 확산하는 생산·공급 플랫폼\n'
     '엔진 Produce & Scale (안→밖) · 상품화·산업화·확산성 · 전국 사찰/기관/문화 소비자'),
]
for cid, label, cap, desc in CONCEPTS:
    add(id=cid, stage='concept', label=label, caption=cap, summary=desc,
        ev=[dict(quote=desc.split('\n')[0], src=f'{PROG} #3대 컨셉 확정 정의 (대표 확정, 2026-07-29)')])

# ── Business Model 10유형 (STEP 5) ───────────────────────────────
BMS = [
    ('bm2', 'BM-2 체험경제형', '핵심', ['G4', 'G5', 'G6'],
     '체험 참가비 + F&B · 템플스테이·츠키지혼간지·닌나지 — 봉은사가 이미 일부 보유'),
    ('ax2', '축② 라이프스타일 리브랜딩형', '최근접', ['G3', 'G10'],
     "'오픈 복합문화공간'으로의 재명명 자체가 엔진 — 봉은문화회관에 가장 직접 대응"),
    ('bm5', 'BM-5 박물관전시형', '가능', ['G2'],
     '입장료 + 기념품숍 연계 · 전시장·박물관은 3법을 모두 통과하는 용도'),
    ('ax1', '축① F&B 특화형', '진입점', ['G1'],
     '진입 장벽 최저·폐점 리스크 최고 · 건물 용도상 조리가 원천 불가해 막혀 있다'),
    ('bm3', 'BM-3 복합임대형', '조건부', ['G7'],
     '임대료 — 종교시설이 앵커 · 오피스 임대는 불가, 전통사찰법 제9조 허가 필요'),
    ('ax3', '축③ 부동산·장묘형', '최대규모', ['G9'],
     '정기차지권 임대 + 납골당·영대공양 · 일본 도시형 사원 BM의 다수 — 재검증 필요'),
    ('bm4', 'BM-4 커뮤니티허브형', '보조', ['G8'],
     '수익 엔진 없음(헌금 의존 90%+) · 공익성 최고, 자립 불가'),
    ('bm1', 'BM-1 관광수익형', '부분', [],
     '입장료 단일 엔진(사그라다 파밀리아 97%) — 입장료 엔진 배제, 무료 개방형만 열림'),
    ('bm6', 'BM-6 적응적재사용형', '배제', [],
     '민간이 인수해 상업시설로 전환 — 종교 주체가 빠지는 구조라 전제가 다르다'),
    ('bm7', 'BM-7 국가프로젝트형', '배제', [],
     '정부 재정 전액 · 목적이 수익이 아니라 국가 브랜딩 — 재정 구조 재현 불가'),
]
BM_OF = {g: b[0] for b in BMS for g in b[3]}
for bid, label, verdict, cats, note in BMS:
    mine = [s for s in SV if BM_OF.get(gid(s)) == bid]
    add(id=bid, stage='bm', label=label, verdict=verdict, summary=note,
        ev=[dict(quote=f'{verdict} — {note}', src=f'{RPT} #STEP 5 수익모델 7유형 + 축①②③')])

# ── Service Category (Level 1) ───────────────────────────────────
GROUPS = sorted({s.get('group') for s in SV if s.get('group')},
                key=lambda g: int(g.split('·')[0].strip()[1:]))
for g in GROUPS:
    mine = [s for s in SV if s.get('group') == g]
    short = g.split('·', 1)[1].strip()
    t = Counter(tier(s) for s in mine)
    add(id=gid(mine[0]), stage='cat', label=short,
        summary=f'{len(mine)}건 · ' + ' / '.join(f'{k} {v}' for k, v in sorted(t.items())),
        ev=[dict(quote=f'{g} — {len(mine)}건', src=f'{SRC} #service[*].group')])

# ── Target (직교 필터) ───────────────────────────────────────────
TARGETS = [
    ('t-mz',    'MZ · 이슈화',      lambda s: '대중화' in vb(s, 'C1')),
    ('t-local', '지역주민 · 강남',   lambda s: '지역'   in vb(s, 'C5')),
    ('t-bud',   '불교 신자',        lambda s: '종교'   in vb(s, 'C2')),
    ('t-intl',  '외국인 관광객',     lambda s: '글로벌' in vb(s, 'C5')),
    ('t-biz',   '기업 · VIP · B2B', lambda s: '특화' in vb(s, 'C1')
                or s.get('variant') in ('B2B', '멤버십', '프리미엄')),
]
RARITY = {t[0]: sum(1 for x in SV if t[2](x)) for t in TARGETS}
for tid, label, fn in TARGETS:
    add(id=tid, stage='target', label=label,
        ev=[dict(quote=f'{sum(1 for s in SV if fn(s))}건이 이 타깃에서 성립',
                 src=f'{SRC} #service[*].viability')])

# ── Legal Check (필터 겸 관문) ───────────────────────────────────
HI = lambda x: (x.get('eval') or {}).get('revenue') == 'H'
TIERS = [
    ('Tier1', 'Tier 1 · 해석 없이 가능', False,
     '시행령 제7조 문언에 그대로 걸린다 — 유권해석을 기다리지 않는다'),
    ('Tier2', 'Tier 2 · 유권해석 전제', False,
     '선례는 있으나 문체부 종무실 확인이 필요하다'),
    ('Tier3', 'Tier 3 · 현행 불가', True,
     '공론화·제도 개선이 있어야 열린다 — 지금은 전부 배제 판정'),
]
for tid, label, blocked, note in TIERS:
    mine = [s for s in SV if tier(s) == tid]
    hi = [s for s in mine if HI(s)]
    add(id=tid, stage='legal', label=label, blocked=blocked,
        summary=f'{note}\n{len(mine)}건 중 고수익 {len(hi)}건 ({len(hi)/max(1,len(mine)):.0%})',
        ev=[dict(quote='지금 그대로 되는 44개 중 돈이 되는 것은 5개(11%)인데, 해석을 받아야 하는 '
                       '65개 중에는 19개(29%)다 — 돈은 회색지대 쪽에 몰려 있다. '
                       '유권해석이 수익 천장을 정한다.', src=f'{RPT} #STEP 7.1')])

# ── Service Contents (Level 2) ───────────────────────────────────
for s in SV:
    tg = sorted([t[0] for t in TARGETS if t[2](s)], key=lambda x: RARITY[x])[:3]
    add(id=s['id'], stage='svc', label=s['label'].replace(' [배제]', ''),
        parent=gid(s), bm=BM_OF.get(gid(s)), legal=tier(s),
        blocked=(s.get('variant') == '배제'),
        concepts=['C-' + c for c in (s.get('scenario') or [])],
        targets=tg, summary=s.get('statement', ''),
        ev=[dict(quote=s.get('statement', ''), src=f"{SRC} #{s['id']}")] +
           ([dict(quote=s['legal_note'], src='법률 주석')] if s.get('legal_note') else []))

# ── Research 레이어 ──────────────────────────────────────────────
RS = [('S4-O4', 'Location — 입지·상권'), ('S4-O2a', 'Target — 외국인'),
      ('S4-O2b', 'Target — 강남'), ('S4-O2c', 'Target — MZ'),
      ('S4-O2d', 'Target — 불교 신자'), ('S4-O3', '시장 공백')]
for slot, label in RS:
    items = [x['label'] for x in EL if slot in (x.get('slots') or [])]
    if items:
        add(id='rs-' + slot, stage='research', label=label, items=items,
            ev=[dict(quote=' / '.join(items[:8]), src=f'{SRC} #slots={slot}')])

# ── 빈 슬롯 ──────────────────────────────────────────────────────
SLOTS = [
    ('◻︎ 기업 · VIP 수요 데이터', 'S4-O2e(기업)·S4-O2f(VIP) 슬롯이 0건이다. '
     '지금 "기업·VIP·B2B" 타깃은 서비스 속성에서 역산한 것이지 수요 조사가 아니다. '
     '필요 — 기업 워크숍·리트리트 수요, 강남 법인 복지예산, VIP 멤버십 지불의향'),
    ('◻︎ 유형별 매출 산식', 'BM 10유형과 서비스는 이었지만 유형마다 얼마가 도는지가 없다. '
     '필요 — 객단가·회전·면적 기준 매출 산식. 특히 C안(축②)은 기존에 없던 모델이라 전부 신규'),
    ('◻︎ 프리미엄 ↔ 대중화 축 (S3-C1)', '리포트 3.1에 5축 분석과 권고(프리미엄)까지 있으나 '
     '서비스 태깅이 없어 이 지도에 못 들어왔다. 필요 — C1 판정을 서비스 단위로 태깅'),
    ('◻︎ 중창불사 관계 축 (S3-C4)', '5대 갈림길 중 C4만 서비스 태깅이 없다. '
     '필요 — 중창불사 3단계 일정 × 개관 시점 간섭 검토'),
]
for i, (label, why) in enumerate(SLOTS):
    add(id=f'slot{i}', stage='research', slot=True, label=label, summary=why, items=[])

G = dict(
    meta=dict(
        title='봉은문화센터 — Decision Map',
        subtitle=f'Concept → Business Model → Service Category → Service Contents → Legal '
                 f'(+ Target·Research 레이어) · 서비스 {len(SV)}건 · '
                 f'어느 열을 눌러도 나머지가 그 조건으로 좁혀진다',
        source=f'{SRC} · BM 10유형은 {RPT} · 3대 컨셉은 {PROG}',
        generated_at='2026-07-30', axis='topic', mode='structure', render='decision',
        value_basis='equal', value_note='관계·가능 여부만 표시'),
    stages=[
        dict(id='concept',  label='Concept',          order=0, role='entry'),
        dict(id='bm',       label='Business Model',   order=1, role='structure'),
        dict(id='cat',      label='Service Category', order=2, role='structure'),
        dict(id='svc',      label='Service Contents', order=3, role='structure'),
        dict(id='legal',    label='Legal Check',      order=4, role='gate'),
        dict(id='target',   label='Target',           order=5, role='filter'),
        dict(id='research', label='Research',         order=6, role='data'),
    ],
    nodes=N, links=[], conclusions=[], whitespace=[])

path = os.path.join(OUT, 'decision-map-graph.json')
json.dump(G, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'Concept {len(CONCEPTS)} · BM {len(BMS)} · Category {len(GROUPS)} · Service {len(SV)}')
print(f'Target {len(TARGETS)} · Legal {len(TIERS)} · Research {len(RS)} · 빈 슬롯 {len(SLOTS)}')
print(f'노드 {len(N)}')
print('→', path)
