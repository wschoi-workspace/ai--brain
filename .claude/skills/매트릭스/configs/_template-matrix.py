# -*- coding: utf-8 -*-
"""전략 매트릭스 config 템플릿 — 이 파일을 복사해서 새 매트릭스를 만든다.

  cp _template-matrix.py <프로젝트>-matrix.py
  python3 ../scripts/matrix_gen.py <프로젝트>-matrix.py

이 템플릿은 그대로 실행된다(아래 데모 원자 6건). 먼저 돌려서 화면을 보고,
load()와 축 정의를 실제 데이터로 갈아끼우는 순서를 권한다.
OUT을 바꾸기 전까지 산출물(template-matrix.html·-graph.json)은 이 폴더에 떨어진다 — 데모 확인용이다.

── 이 구조가 답하는 질문 ──────────────────────────────────────
  "왼쪽에서 오른쪽으로 갈 때, 무엇이 무엇으로 이어지고 어디서 잘리는가"
  각 열은 '축(axis)' 하나이고, 원자(개별 항목)마다 축 값을 매긴다.
  링크는 IR에 박지 않는다 — 렌더러가 필터마다 다시 센다.

── 설계 규칙 5개 (실측으로 얻은 것. references/flow-grammar.md가 SSOT) ──
  1. 라벨에 건수를 박지 않는다 — 필터를 걸면 거짓이 된다. 배지는 렌더러가 붙인다
  2. 다중 태깅을 전부 이으면 밀도 80% 완전 이분 그래프가 된다 → pick 규칙으로 좁힌다
  3. 상세 열(atomic)은 (상위 × 항목) 조합으로 쪼갠다 — 안 그러면 계층이 안 생긴다
  4. 흐름이 아니라 '조건'인 열은 filter_only — 선을 지우고 필터로만 남긴다
  5. 판정 재료는 라벨이 아니라 원문 문장이다. 키워드를 문장에 그대로 돌리면 오탐이 크다
"""
import os

NAME = 'template-matrix'
OUT = os.path.dirname(os.path.abspath(__file__))     # ← 실제 프로젝트 폴더로 바꾼다
SRC = '(출처 파일 경로)'


# ── 1. 원자 원본 ───────────────────────────────────────────────
# 실제로는 json.load(...)로 읽는다. 원자 = 이 매트릭스에서 세는 최소 단위.
def load():
    return [
        dict(id='E-01', label='전통다원 · 오픈형', group='G1', tier='t1', concept='C-A',
             text='예약 없이 들어와 차를 마시는 상시 개방형. 객단가는 낮고 회전이 빠르다.'),
        dict(id='E-02', label='티 클럽 멤버십', group='G1', tier='t1', concept='C-B',
             text='연회비를 내면 시즌 차를 정기 수령한다. 1회 소비를 연간 관계로 바꾼다.'),
        dict(id='E-03', label='유료 기획전', group='G2', tier='t1', concept='C-A',
             text='회기제 유료 기획전. 입장료를 직접 수익원으로 삼는다.'),
        dict(id='E-04', label='뮤지엄숍', group='G2', tier='t1', concept='C-B',
             text='관람 동선 끝에 붙는 상품 매장. 입장료만으론 자립이 안 되는 구조를 보완한다.'),
        dict(id='E-05', label='기업 연수', group='G3', tier='t2', concept='C-B',
             text='표준 커리큘럼으로 70~100명을 받는다. 수용력을 그대로 매출로 바꾼다.'),
        dict(id='E-06', label='일반 웨딩홀 [배제]', group='G3', tier='t3', concept='',
             text='종교적 맥락 없는 예식 영업은 현행법으로 닫혀 있다.'),
    ]


# ── 2. 원자에서 무엇을 뽑을 것인가 ──────────────────────────────
ATOM = dict(
    id=lambda x: x['id'],
    label=lambda x: x['label'],
    summary=lambda x: x['text'],
    blocked=lambda x: '[배제]' in x['label'],
    evidence=lambda x: [dict(quote=x['text'], src=SRC)],
)

_lab = lambda s: s['label'].replace(' [배제]', '')      # 배제 꼬리표를 뗀 이름 = 판정 키


# ── 3. 축 A · 그룹 (배타) ─────────────────────────────────────
GROUPS = [('G1', 'F&B'), ('G2', '전시·리테일'), ('G3', '대관·B2B')]
GROUP_NODES = [dict(id=g, label=f'{g} · {nm}', kind='group',
                    match=(lambda gg: (lambda s: s['group'] == gg))(g))
               for g, nm in GROUPS]


# ── 4. 축 B · 모델 (주력 1개 + 연계 n개) ───────────────────────
# ⚠️ 그룹당 상위 하나로 고정하면 실제로 있는 교차가 화면에서 통째로 사라진다.
#    주력은 PRIMARY_OF, 연계는 두 층으로 선언한다:
#      ALSO_GROUP — 그룹 전체가 걸리는 것
#      ALSO_ITEM  — 같은 그룹 안에서도 아이템마다 다른 것 (이게 없으면 큰 그룹이 통째로 틀린다)
#    연계는 근거를 주석에 남긴다. 다 이으면 밀도 80% 함정으로 되돌아간다.
MODELS = [('m1', '체험·프로그램형'), ('m2', '리테일·상품형'), ('m3', '공간임대형')]
PRIMARY_OF = {'G1': 'm1', 'G2': 'm2', 'G3': 'm3'}
ALSO_GROUP = {
    'G2': ['m1'],                 # 전시는 체험 프로그램과 동선을 공유한다
}
ALSO_ITEM = {
    '티 클럽 멤버십': ['m2'],       # "시즌 차를 정기 수령" — 상품 정기배송이기도 하다
}

def models_of(s):
    """이 원자가 걸리는 모델 — 주력 1개 + 연계."""
    out = [PRIMARY_OF.get(s['group'])] if PRIMARY_OF.get(s['group']) else []
    for m in ALSO_GROUP.get(s['group'], []) + ALSO_ITEM.get(_lab(s), []):
        if m not in out:
            out.append(m)
    return out

MODEL_NODES = [dict(id=m, label=nm, kind='group',
                    match=(lambda mm: (lambda s: mm in models_of(s)))(m))
               for m, nm in MODELS]


# ── 5. 축 C · 상세 열 (atomic) ────────────────────────────────
# 상위와 M:N인 축은 **(상위 × 항목) 조합으로 쪼개야** 계층이 된다.
# 판정 재료는 라벨이 아니라 원문 문장이다 — 라벨만 보면 '지역 상인 입점'이
# 무수익으로 잘못 앉는다(실제 문장은 "임대 수익을 걸러내는"이라고 말한다).
ITEM_INFO = {
    'r-fee':   ('참가·수강료',  '회당·과정 단위로 받는다'),
    'r-goods': ('상품 판매',    '객단가 × 구매 전환'),
    'r-sub':   ('멤버십·구독',  '1회 소비를 연간 관계로 바꾼다'),
    'r-rent':  ('대관·임대료',  '시간·면적 단위 사용료'),
    'r-x':     ('✕ 배제',      '현행 법으로 닫혀 있다'),
}
# ①라벨 1차 판정
ITEM_RULES = [
    ('r-sub',   lambda s, l: any(k in l for k in ('멤버십', '구독', '회원'))),
    ('r-goods', lambda s, l: any(k in l for k in ('숍', '굿즈', '상품'))),
    ('r-rent',  lambda s, l: any(k in l for k in ('대관', '임대', '연수'))),
    ('r-fee',   lambda s, l: True),
]
# ②문장을 읽고 고치는 예외 (주 항목 교정)
ITEM_EXCEPT = {}
# ③한 원자가 두 항목을 말할 때의 부수익
ITEM_ALSO = {
    '티 클럽 멤버십': ['r-goods'],    # "시즌 차를 정기 수령" — 상품 매출이 함께 난다
}

def items_of(s):
    if ATOM['blocked'](s):
        return ['r-x']                       # 배제는 매출이 성립하지 않는다
    key, l = _lab(s), s['label']
    main = ITEM_EXCEPT.get(key)
    if not main:
        for rid, fn in ITEM_RULES:
            if fn(s, l):
                main = rid
                break
    return [main] + [r for r in ITEM_ALSO.get(key, []) if r != main]

# 이 모델이 가질 수 있는 항목 — 목록의 대부분은 원자에서 나온다.
# 리서치로 '원자 없이' 세우는 칸은 **없으면 그 모델이 성립하지 않는 것만** 남긴다.
# 0건으로 남는 칸이 곧 "가능한데 아직 안 하는 것"이다. 남발하면 경고로 안 읽힌다.
MODEL_ITEMS = {
    'm1': ['r-fee', 'r-sub'],
    'm2': ['r-goods', 'r-sub'],
    'm3': ['r-rent', 'r-fee'],
}

def _item_nodes(_atoms):
    out = []
    for m, _nm in MODELS:
        by = {}
        for s in load():
            if m in models_of(s):            # 연계로 걸린 것도 그 모델의 항목이 된다
                for rid in items_of(s):
                    by.setdefault(rid, []).append(s)
        ids = list(MODEL_ITEMS.get(m, []))
        for rid in by:                       # 선언에서 빠졌어도 실측이 있으면 살린다
            if rid not in ids:
                ids.append(rid)
        for rid in ids:
            nm, note = ITEM_INFO[rid]
            hit = by.get(rid, [])
            out.append(dict(
                id=f'{m}-{rid}', label=nm, category=m,          # category = 상위 노드 id (짝 정렬의 열쇠)
                summary=note + '\n' + (' / '.join(x['label'] for x in hit[:4]) if hit
                                       else '⚠ 이 모델이면 가능한데 지금 항목이 없다'),
                match=(lambda mm, rr: (lambda s: mm in models_of(s)
                                       and rr in items_of(s)))(m, rid),
                evidence=[dict(quote=(f'{nm} — {len(hit)}건' if hit else f'{nm} — 가능하지만 미가동'),
                               src=SRC)]))
    return out


# ── 6. 축 D · 관문 (filter_only) ──────────────────────────────
# 흐름의 한 칸이 아니라 조건인 열. 선을 안 그리고 앞뒤를 직접 잇는다.
TIER_NODES = [dict(id=t, label=nm, kind='group',
                   match=(lambda tt: (lambda s: s['tier'] == tt))(t))
              for t, nm in [('t1', 'Tier 1 · 즉시'), ('t2', 'Tier 2 · 해석 필요'),
                            ('t3', 'Tier 3 · 불가')]]


# ── 7. 결론 열 ────────────────────────────────────────────────
CONCEPT_NODES = [dict(id=c, label=nm, kind='card', caption=cap,
                      match=(lambda cc: (lambda s: s['concept'] == cc))(c))
                 for c, nm, cap in [('C-A', 'Concept A', '진입 우선'),
                                    ('C-B', 'Concept B', '관계 우선')]]


# ── 8. 열 배치 ────────────────────────────────────────────────
# 마지막 열은 반드시 role='conclusion'. 열이 8개를 넘으면 화면에서 안 읽힌다.
STAGES = [
    dict(id='s1', label='A · 그룹', order=0, role='origin', axis='group',
         nodes=GROUP_NODES, kind='group', pick='first',
         note='배타 축 — 원자 하나가 한 곳에만 걸린다'),
    dict(id='s2', label='B · 모델', order=1, role='structure', axis='model',
         nodes=MODEL_NODES, kind='group',
         note='주력 + 연계 — 한 그룹이 한 모델에만 쓰이지 않는다'),
    dict(id='s2b', label='B-1 · 수익 항목', order=2, role='synthesis', axis='item',
         atomic=True, nodes_fn=_item_nodes,
         note='돈이 실제로 어디서 들어오는가 · 0건 칸 = 가능한데 아직 안 하는 것'),
    dict(id='s3', label='C · 관문', order=3, role='synthesis', axis='tier',
         filter_only=True, nodes=TIER_NODES, kind='group',
         note='흐름이 아니라 조건 — 선 대신 필터로 남긴다'),
    dict(id='s4', label='Concept', order=4, role='conclusion', axis='concept',
         nodes=CONCEPT_NODES, kind='card', note='결론 열'),
]

# 자료가 없어 비워둔 칸 — 원자가 없으므로 필터와 무관하게 늘 보인다
SLOTS = [
    dict(id='slot-price', stage='s2b', label='◻︎ 항목별 객단가',
         why='매출 산식이 없어 금액을 붙이지 못했다', need='항목별 객단가·회전율'),
]

META = dict(
    title='(제목)',
    subtitle='(부제 — 무엇을 몇 건 다뤘는지)',
    source=SRC,
    axis='topic',             # topic | time — 검증기 필수
    mode='structure',         # structure | generate(빈틈 탐지) — 검증기 필수
)

# CONCLUSIONS = [dict(node_id='C-A', text='...', support=['E-01', 'E-03'])]
# WHITESPACE  = [dict(where=['m3'], question='...')]
