# -*- coding: utf-8 -*-
"""봉은문화센터 전략 매트릭스 — 축 정의

  python3 ../scripts/matrix_gen.py bongeunsa-matrix.py

Target → Direction → 서비스·컨텐츠 → [C-1 상세] → 수익모델 → [D-1 수익항목] → 법 관문 → Concept

⚠️ 확장 예정 (2026-07-31 사용자 확인)
  1. Target 해석 — 지금은 서비스 속성(viability)에서 역산한 것이다.
     리서치 자료가 들어오면 ▼TARGET_NODES▼ 의 match를 그 자료 기준으로 갈아끼운다.
     S4-O2a~f(외국인 28·강남 15·MZ 23·불교신자 22·기업 0·VIP 0) + S4-O4 Location 66건이 재료.
  2. 컨셉 해석 구조 — 옵션 열로 추가 예정. ▼여기에 STAGE 하나를 더 끼우면 된다▼
     자리는 Concept 직전(order 7)이 자연스럽다. atomic=True로 두면 상세 열이 된다.
  3. D-1 수익 항목 — C·C-1의 서비스 문장(statement)이 말하는 수익 방식을 재해석한 것이다.
     라벨 키워드 1차 판정(▼REVENUE▼) + 문장을 읽고 고친 예외(▼_REV_EXCEPT▼)
     + 한 서비스가 두 수익원을 말할 때의 부수익(▼SECONDARY▼).
     매출 산식(객단가·회전)이 들어오면 항목마다 금액을 붙일 수 있다.
"""
import json, os
from collections import Counter

WS = '/Users/choi_ai/do-better-workspace'
SRC = '10-projects/15-bongeunsa/재구조화/elements.json'
RPT = '10-projects/15-bongeunsa/재구조화/봉은문화센터-master-strategy-report.html'
PROG = '10-projects/15-bongeunsa/15-progress.md'

NAME = 'strategy-matrix'
OUT = os.path.join(WS, '10-projects/15-bongeunsa/sankey')
# 같은 IR로 Decision Map까지 뽑는다 (열 쓰임은 STAGES의 dec 힌트가 정한다)
DECISION = 'decision-map.html'

# ── 원본 ──────────────────────────────────────────────────────────
_EL = json.load(open(os.path.join(WS, SRC), encoding='utf-8'))
_SV = [x for x in _EL if x.get('kind') == 'service']

vb = lambda s, ax: (s.get('viability') or {}).get(ax, [])
tier = lambda s: (s.get('eval') or {}).get('legal')
gid = lambda s: s.get('group', '')[:3].strip()

def load():
    return _SV

ATOM = dict(
    id=lambda x: x['id'],
    label=lambda x: x['label'].replace(' [배제]', ''),
    summary=lambda x: x.get('statement', ''),
    blocked=lambda x: x.get('variant') == '배제',
    evidence=lambda x: [dict(quote=x.get('statement', ''), src=f"{SRC} #{x['id']}")] +
                       ([dict(quote=x['legal_note'], src='법률 주석')] if x.get('legal_note') else []),
)

# ── ▼TARGET_NODES▼ ────────────────────────────────────────────────
# ⚠️ 이 열은 "타겟"을 판정하지 않는다.
#    match의 입력이 서비스의 viability(조건부 생존성)이므로, 판정하는 것은
#    "이 서비스는 어떤 전략 선택 아래에서 살아남는가"이지 "누가 이걸 사는가"가 아니다.
#
#    2026-08-02 검토 결과 — 실측(RXR 4,330건·서울관광조사 원자료)으로 이 match를
#    갈아끼우는 것은 불가능하다. 서비스 116건 중 타겟 슬롯(S4-O2*)이 붙은 것이 2건뿐이라
#    실측이 닿을 필드가 없다. 실측 기반 타겟은 별도 수요 매트릭스에 있다
#    (bongeunsa-demand-matrix.py — 원자가 수요 54건이라 층위 충돌이 없다).
#    match를 실제로 바꾸려면 서비스 116건에 demand_target을 사람이 다시 태깅해야 한다.
#
#    ⚠️ match를 건드리면 rarity가 전역 상수라 다른 노드 건수가 연쇄로 재배치된다.
#       (t-intl을 8건으로 좁히면 t-biz +13·t-mz +17·t-local +18로 움직인다)
TARGET_NODES = [
    dict(id='t-mz',    label='MZ · 이슈화',            match=lambda s: '대중화' in vb(s, 'C1'),
         summary='판정 기준 — viability.C1 = 대중화\n(서비스마다 희소한 순으로 최대 2개만 연결)'),
    dict(id='t-local', label='기타 · 미분류',           match=lambda s: '지역' in vb(s, 'C5'),
         summary='판정 기준 — viability.C5 = 지역\n'
                 '⚠️ C5(지역↔글로벌)는 master-strategy-report에서 판별력 없음(ARI 0.014)으로 '
                 '기각되어 실행 변수로 강등된 축이다.\n'
                 '실제 내용 — raw 108건 중 78건이 pick 규칙에 탈락하고 남은 30건. '
                 '다른 노드에 걸리지 않은 잔여다. "강남 주민 수요"가 아니다.'),
    dict(id='t-bud',   label='불교 신자',              match=lambda s: '종교' in vb(s, 'C2'),
         summary='판정 기준 — viability.C2 = 종교\n'
                 '(전량 통과하는 이유는 판정이 강해서가 아니라 rarity 랭킹 1위여서다)'),
    dict(id='t-intl',  label='해외 확장 가능',          match=lambda s: '글로벌' in vb(s, 'C5'),
         summary='판정 기준 — viability.C5 = 글로벌\n'
                 '⚠️ C5는 판별력 없음(ARI 0.014)으로 기각된 축이다.\n'
                 '이 노드는 "외국인이 소비하는 서비스"가 아니라 "해외 확장을 택했을 때 '
                 '살아남는 서비스"다. 56건 중 외국인·다국어가 명시된 것은 4건이고, '
                 'G10 상품화·공급(굿즈 위탁제조·리테일 라이선싱·전시 패키지 턴키)이 13건이다.\n'
                 '외국인 실수요는 수요 매트릭스 tg-intl을 볼 것.'),
    dict(id='t-biz',   label='비즈니스 이해관계자 · B2B',
         match=lambda s: '특화' in vb(s, 'C1') or s.get('variant') in ('B2B', '멤버십', '프리미엄'),
         summary='판정 기준 — viability.C1 = 특화 · variant = B2B/멤버십/프리미엄'),
]

# ── Direction — C2(종교↔문화) × C6(브랜드↔산업화). 배타적으로 하나만 ──
def _dir_rev(s):  return '산업화' in vb(s, 'C6')
def _dir_prac(s): return not _dir_rev(s) and '종교' in vb(s, 'C2') and gid(s) in ('G4', 'G6')
def _dir_rel(s):  return not _dir_rev(s) and '종교' in vb(s, 'C2') and gid(s) not in ('G4', 'G6')
def _dir_cul(s):  return not _dir_rev(s) and '종교' not in vb(s, 'C2')

DIRECTION_NODES = [
    dict(id='d-rev',  label='수익시설',  kind='group',
         summary='수익 확장성 중심\n판정 기준 — C6=산업화'),
    dict(id='d-prac', label='수행 중심',  kind='group',
         summary='종교 관점\n판정 기준 — C2=종교 ∩ 명상·웰니스/체류·리트리트'),
    dict(id='d-rel',  label='종교시설',  kind='group',
         summary='불교 브랜딩 관점\n판정 기준 — C2=종교'),
    dict(id='d-cul',  label='문화시설',  kind='group',
         summary='일반인 복합문화공간\n판정 기준 — C2=문화'),
]
for _n, _f in zip(DIRECTION_NODES, [_dir_rev, _dir_prac, _dir_rel, _dir_cul]):
    _n['match'] = _f

# ── 서비스 그룹 (G1~G10) ──────────────────────────────────────────
_GROUPS = sorted({s.get('group') for s in _SV if s.get('group')},
                 key=lambda g: int(g.split('·')[0].strip()[1:]))

def _cat_nodes(_atoms):
    out = []
    for g in _GROUPS:
        mine = [s for s in _SV if s.get('group') == g]
        short = g.split('·', 1)[1].strip()
        t = Counter(tier(s) for s in mine)
        out.append(dict(id=gid(mine[0]), label=f'{gid(mine[0])} · {short}', kind='group',
                        category='서비스·컨텐츠',
                        summary=' / '.join(f'{k} {v}' for k, v in sorted(t.items())),
                        match=(lambda gg: (lambda s: s.get('group') == gg))(g),
                        evidence=[dict(quote=f"{s['label']} — {s['statement'][:96]}",
                                       src=f"{SRC} #{s['id']}") for s in mine]))
    return out

# ── C-1 · 서비스 상세 (원자 1:1) ──────────────────────────────────
def _svc_nodes(_atoms):
    return [dict(id='sv-' + s['id'], label=s['label'].replace(' [배제]', ''),
                 category=gid(s), summary=s.get('statement', ''),
                 match=(lambda sid: (lambda x: x['id'] == sid))(s['id']),
                 evidence=[dict(quote=s.get('statement', ''), src=f"{SRC} #{s['id']}")])
            for s in _SV]

# ── 수익모델 10유형 (master-strategy-report STEP 5) ───────────────
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

# 그룹만 보면 BM 정의에 있는 연계 수익원이 끊긴다 — 서비스 단위로 되돌린다
_BM_EXCEPT = {
    '뮤지엄숍': 'bm5',                 # BM-5 정의: 입장료 + 기념품숍 연계
    '리미티드 공예 에디션': 'bm5',       # 장인×현대 디자이너 협업 — 전시 연계 고가 에디션
    '전시 연계 굿즈 개발': 'bm5',
    '수집형 스탬프·부적': 'bm5',        # 관람 동선 안에서 팔린다
}

# 한 서비스군이 한 모델에만 쓰이지 않는다. 그룹당 BM 하나로 묶으면
# 실제로 있는 교차(대관=MICE=전시, 멤버십=커뮤니티)가 화면에서 아예 사라진다.
# 주력은 BM_OF 그대로 두고, 여기에 '연계'를 더한다.
BM_ALSO = {
    'G9': ['bm4'],   # 멤버십·후원·디지털 = 커뮤니티 관계 설계 그 자체 (2026-07-31 지적)
    'G7': ['bm5'],   # 대관 = 컨벤션·MICE — 전시 오프닝·포럼이 같은 공간을 쓴다 (지적)
    'G4': ['bm4'],   # 웰니스 상시 프로그램 = 지역 주민 대상 커뮤니티 허브 (지적)
    'G5': ['bm4'],   # 시민 강좌·청소년 교실은 공익 커뮤니티 기능
    'G1': ['bm2'],   # 사찰음식·다도는 체험 프로그램과 한 몸
    'G2': ['ax2'],   # 미디어아트 순회·전시 패키지 공급이 확산 모델의 재료
    'G3': ['bm5'],   # 리테일의 기본형이 뮤지엄숍 — 관람 동선의 끝
    'G8': ['ax2'],   # 지역 상인 입점·상생기금 판매는 리테일 형태를 빌린다
}

# 그룹 단위로는 안 맞는 것 — 한 그룹 안에서 아이템마다 붙는 모델이 다르다.
# G10(상품화·공급·확산) 26건이 그 경우다: 전시 패키지는 박물관형에, 프로그램 확산은 체험형에,
# 기업 콜라보는 F&B에 붙고, 순수 도매·굿즈 13건은 축②에만 남는다. (2026-07-31 지적)
SV_ALSO = {
    # ── 전시형으로 — 전시가 소재이거나 전시 자체를 옮긴다
    '전시 패키지 공급 · 턴키':  ['bm5'],   # 작품·연출·설치를 묶어 공급
    '전시 패키지 · 시즌 순회':  ['bm5'],   # 같은 전시 세트를 순회
    '해외 전시연계 상품공급':    ['bm5'],   # 해외 박물관 한국 전시 연계
    '사찰 미디어아트 상설':     ['bm5'],   # "유료 관람 상품으로 운영"
    '종단 채널 연계 상품화':    ['bm5'],   # 서울국제불교박람회 = 전시 채널
    # ── 체험형으로 — 파는 것이 상품이 아니라 프로그램이다
    '사찰운영자 아카데미':      ['bm2'],   # 표준 커리큘럼 교육·수료 인증
    '운영 매뉴얼 패키지 판매':   ['bm2'],   # 프로그램 설계·인력 배치를 판다
    '불교 콘텐츠 IP 라이선싱':  ['bm2', 'bm5'],  # "프로그램·공간연출·브랜드를 IP로"
    '통합 예약·유통 채널':     ['bm2'],   # 전국 사찰 프로그램의 예약을 묶는다
    '프로그램 인증·평가':      ['bm2'],
    '강남 테스트베드 검증':     ['bm2'],   # "상품·프로그램을 먼저 팔아보고"
    # ── F&B로
    '기업 콜라보 라이선싱':     ['ax1'],   # "F&B·뷰티·리빙 기업에 라이선스"
    '오리지널 식품 브랜드':     ['ax1'],   # 된장·간장·차 — 조리 인프라를 공유한다
    '웰니스 소비재 라인':      ['ax1'],   # 차·사찰음식 가공품
}

def bms_of(s):
    """이 서비스가 걸리는 수익모델 — 주력 1개 + 연계(그룹 단위 + 아이템 단위)."""
    key = s['label'].replace(' [배제]', '')
    main = _BM_EXCEPT.get(key, BM_OF.get(gid(s)))
    out = [main] if main else []
    for b in BM_ALSO.get(gid(s), []) + SV_ALSO.get(key, []):
        if b not in out:
            out.append(b)
    return out

def bm_of(s):                      # 주력 1개
    v = bms_of(s)
    return v[0] if v else None
MARK = {'핵심': '★', '가능': '○', '최근접': '◎', '진입점': '▲',
        '조건부': '△', '보조': '·', '최대규모': '◇', '부분': '▽', '배제': '✕'}

# 묶음(category)은 하나로 둔다 — 판정별로 나누면 묶음마다 한 개씩이라
# 정렬이 고정돼 앞 열과 어긋난다(실측 교차 1,282 → 631). 판정은 라벨 앞 기호로 읽힌다.
BM_NODES = [dict(id=b[0], label=f'{MARK[b[2]]} {b[1]}', kind='group', category='수익모델',
                 summary=f'{b[2]} — {b[4]}',
                 match=(lambda bid: (lambda s: bid in bms_of(s)))(b[0]),
                 evidence=[dict(quote=f'{b[2]} — {b[4]}',
                                src=f'{RPT} #STEP 5 수익모델 7유형 + 축①②③')])
            for b in BMS]

# ── D-1 · 수익 항목 — C·C-1이 말하는 수익 방식의 재해석 ──────────
# variant(매스·프리미엄)는 '판매 등급'이지 수익 항목이 아니다.
# 재료는 서비스 116건의 statement다 — 문장이 이미 수익 방식을 말하고 있다
# ("연회비를 내면", "객단가를 올리는", "정부 지원을 받으며 유료 운영", "임대 수익을 걸러내는").
# 라벨만 보면 놓치므로 문장을 읽어 ①오분류를 고치고 ②한 서비스의 두 번째 수익원을 살린다.
# 리서치(shards/05-bm.json · STEP 5)는 '서비스가 아직 없는 칸'을 세우는 데만 쓴다 — 근거 있는 것만.
_has = lambda l, *k: any(x in l for x in k)

REV_INFO = {                     # id: (이름, 설명)
    'rv-adm':   ('입장 · 관람료',        '전시·뮤지엄 입장 단가 — 단독 자립은 어렵다(BM-5)'),
    'rv-fee':   ('체험 · 참가비',        '회당 참가비 — 워크인·단발 체험'),
    'rv-edu':   ('교육 · 수강료',        '클래스·과정 수강료'),
    'rv-dine':  ('F&B · 다이닝',         '코스·정식 객단가 — 발우공양 3코스 36,000~70,000원'),
    'rv-tea':   ('F&B · 차 · 다과',      '전통다원 객단가 — 시행령이 이름을 적어둔 유일한 F&B'),
    'rv-stay':  ('체류 · 숙박',          '템플스테이 체험형 10만 / 휴식형 5~8만 / 당일형 3~5만'),
    'rv-goods': ('상품 · 굿즈 판매',     '기념품숍 — BM-5의 수익 보완 핵심'),
    'rv-art':   ('작품 · 에디션 판매',   '장인×현대 디자이너 협업 고가 에디션 — 객단가 상한을 올린다'),
    'rv-expo':  ('전시 유치 · 박람회',   '외부 전시 유치·박람회 출품 — 서울국제불교박람회 25만명(2026)'),
    'rv-pub':   ('출판 · 도록 · 미디어', '도록·출판·영상 콘텐츠 — 전시 자산의 2차 활용'),
    'rv-loan':  ('소장품 대여 · 이미지', '성보 대여·이미지 사용료 — 불교중앙박물관이 34개 성보박물관을 지원'),
    'rv-sub':   ('멤버십 · 구독',        '연회비·월정액 — 1회 소비를 관계로 바꾼다'),
    'rv-don':   ('후원 · 헌금',          '헌금·정기후원 — BM-4는 교단 재정 의존도 90%+'),
    'rv-grant': ('보조금 · 기금',        '정부·교단 재정 — 템플스테이는 관광진흥개발기금 약 230억(2017)의 이중 재원'),
    'rv-rent':  ('대관료 · 행사',        '시간·행사 단위 공간 사용료'),
    'rv-lease': ('임대료 · 입점',        '테넌트 임대 — 1898 명동성당 20개 매장. 오피스·업무는 불가(제9조)'),
    'rv-comm':  ('매출 연동 수수료',     '입점사 매출 비례 수수료 — 임대료 대신 쓰는 구조'),
    'rv-b2b':   ('B2B · 기업 프로그램',  '기업 연수·워크숍·협찬 — 묶음 단위 계약'),
    'rv-whole': ('도매 · 공급',          '제조·납품 — 좌석 수 한계를 넘는다'),
    'rv-ip':    ('IP · 라이선스',        '캐릭터·브랜드 사용권 — 자본 없이 거점이 는다'),
    'rv-cha':   ('봉안 · 추모',          '분양 1기 300만~1억 — 일본 사원 BM의 다수'),
    'rv-mgmt':  ('관리비 · 영대공양',    '연간 관리비·영구 공양료 — 봉안의 반복 수익부'),
    'rv-free':  ('무수익 · 공익/기반',   '수익이 아니라 성립 조건이거나 공익 지표'),
    'rv-x':     ('✕ 배제',              '현행 법으로 닫혀 있다 — 매출이 성립하지 않는다'),
}

# 서비스 → 수익 항목 판정 (위에서부터 먼저 걸리는 것)
REVENUE = [
    ('rv-x',     lambda s, l: s.get('variant') == '배제'),
    ('rv-free',  lambda s, l: s.get('variant') in ('공익', '인프라')
     or _has(l, '무료', '개방', '자원봉사', '커뮤니티 매칭', '종교 간', 'CRM', 'SNS', 'DX', '검증', '비파괴')),
    ('rv-cha',   lambda s, l: _has(l, '봉안', '수목장', '영대공양', '라이프엔딩', '추모')),
    ('rv-b2b',   lambda s, l: _has(l, '기업', '임원', '협찬', 'B2B')),
    ('rv-rent',  lambda s, l: _has(l, '대관', '로케이션', '의전', '법요', '혼례', '의례')),
    ('rv-lease', lambda s, l: _has(l, '입점', '임대')),
    ('rv-expo',  lambda s, l: _has(l, '유치', '박람회', '공모', '종단 채널')),
    ('rv-ip',    lambda s, l: _has(l, '라이선', 'IP', '캐릭터', '사용권')),
    ('rv-whole', lambda s, l: _has(l, '도매', '공급', '제조', '대행', '매뉴얼',
                                   '턴키', '순회', '케이터링', '채널', '유통망', '패키지')),
    ('rv-sub',   lambda s, l: _has(l, '멤버십', '구독', '회원')),
    ('rv-don',   lambda s, l: _has(l, '후원', '헌금', '기부')),
    ('rv-stay',  lambda s, l: _has(l, '템플스테이', '리트리트', '스테이', '숙박', '워케이션')),
    ('rv-dine',  lambda s, l: _has(l, '다이닝', '정식당', '조식', '공양식당', '셰프')),
    ('rv-tea',   lambda s, l: _has(l, '다원', '티 ', '한과')),
    ('rv-adm',   lambda s, l: _has(l, '전시', '뮤지엄', '상설', '기획전', '아카이브',
                                   '라이트업', '프로젝션', '역사관', '미디어아트')
     and not _has(l, '숍', '굿즈', '상품')),
    ('rv-art',   lambda s, l: _has(l, '에디션', '공예', '작가', '아트')),
    ('rv-goods', lambda s, l: _has(l, '숍', '굿즈', '상품', '서점', '브랜드몰',
                                   '스탬프', '부적', '소비재', '판매', '브랜드')),
    ('rv-edu',   lambda s, l: _has(l, '클래스', '강좌', '과정', '교실', '아카데미', '양성', '해설')),
    ('rv-fee',   lambda s, l: True),
]

# 라벨 판정이 문장과 어긋나는 것 — statement를 읽고 주 수익원을 바로잡는다
_REV_EXCEPT = {
    '청소년·어린이 문화교실': 'rv-edu',    # "지역 문화공간 역할을 수강료 구조 위에서"
    '측정 기반 명상 DX': 'rv-b2b',        # "기업 웰빙 예산의 집행 근거를 만들어주는"
    '기업 콜라보 라이선싱': 'rv-ip',       # "라이선스해 … 로열티를 받는"
    '지역 상인·공정무역 입점': 'rv-lease',  # "임대 수익을 사회적 가치 기준으로 걸러내는"
    '상생 기금 적립 판매': 'rv-goods',      # "판매 품목마다 일정액을 적립" — 판매가 전제
    '통합 예약·유통 채널': 'rv-comm',       # "유통·결제·데이터를 집중시키는"
}

# 한 서비스가 두 수익원을 말하는 경우 — 문장에 근거가 있는 것만
SECONDARY = {
    '도심형 템플스테이':   ['rv-grant'],   # "정부 지원을 받으며 유료 운영되는 제도"
    '1일 선(禪) 리트리트': ['rv-dine'],    # "좌선·사경·공양·차를 하나로 묶은"
    '웰니스 월정액 멤버십': ['rv-edu'],     # "명상·요가·다도 클래스를 무제한 이용"
    '리트리트 연간 멤버십': ['rv-stay'],    # "분기별 리트리트 참가권"
    '기업 연간 웰니스 계약': ['rv-sub'],    # "예측 가능한 고정 수입으로"
    '기업 연수 · 멤버십형': ['rv-sub'],     # "수주 영업을 반복 매출로"
    '티 클럽 멤버십':      ['rv-tea'],     # "시즌 차를 정기 수령"
    '다이닝 멤버십':       ['rv-dine'],    # "시즌 코스 우선 예약과 비공개 회기"
    '전시 프리뷰 멤버십':   ['rv-adm'],     # "기획전 프리뷰·도슨트·아카이브 열람"
    '봉은사 역사관·아카이브': ['rv-pub'],    # "역사와 성보 기록을 정리해" — 도록·출판의 재료
    '공연장 대관':         ['rv-lease'],   # "정기 슬롯을 주면 … 임대 수익을 동시에"
    '촬영·미디어 로케이션':  ['rv-loan'],    # "사찰 이미지 사용에 대한 심사가 전제"
    '영대공양 추모 서비스':  ['rv-mgmt'],    # "평생 단위 … 장기 관계와 반복 수익"
    '신도·후원 회원 등급제': ['rv-don'],     # "기부 규모에 따라 예우와 참여 권한"
    '온라인 브랜드몰':      ['rv-sub'],     # "오리지널 상품과 구독 박스를 파는"
    '상품 정기구독 박스':    ['rv-goods'],   # "계절 차·장류·향을 정기 배송"
    '나이트마켓·야간 프로그램': ['rv-lease'], # "상업 매대의 성격에 따라"
    '사찰 미디어아트 상설':  ['rv-whole'],   # "같은 작품 세트를 전국 사찰로 순회·이식"
    '기업 콜라보 라이선싱':  ['rv-b2b'],     # "기업에 라이선스해 기업 유통망에서 판매"
    '기업 협찬 전시':       ['rv-adm'],     # 협찬으로 제작비를 대고 전시는 관람 상품으로 남는다
    # '독점 프라이빗 스테이' 의 "경내 독점 입장"은 무료 개방 경내라 별도 입장 매출이 아니다
}

def _revenues_of(s):
    """이 서비스가 만드는 수익 항목 — 주 1개 + 문장 근거가 있는 부수익."""
    l = s['label']
    key = l.replace(' [배제]', '')
    main = _REV_EXCEPT.get(key)
    if not main:
        for rid, fn in REVENUE:
            if fn(s, l):
                main = rid
                break
    main = main or 'rv-fee'
    if s.get('variant') == '배제':        # 배제는 매출이 성립하지 않는다 — 부수익도 없다
        return ['rv-x']
    out = [main] + [r for r in SECONDARY.get(key, []) if r != main]
    return out

def _revenue_of(s):                       # 주 수익원 1개 (하위호환)
    rid = _revenues_of(s)[0]
    return rid, REV_INFO[rid][0], REV_INFO[rid][1]

# ── 각 BM이 가질 수 있는 수익원 ───────────────────────────────────
# 목록의 대부분은 C-1 서비스에서 나온다. 리서치로 '서비스 없이' 세우는 칸은
# 그 BM의 정의상 없으면 모델이 성립하지 않는 것만 남겼다 — 그래야 0건이 경고로 읽힌다.
BM_REVENUE = {
    # 체험 참가비가 정의. 템플스테이는 참가비 + 관광진흥개발기금의 이중 재원(E-0426)
    'bm2': ['rv-fee', 'rv-stay', 'rv-edu', 'rv-b2b', 'rv-sub', 'rv-grant', 'rv-dine'],
    # 입장료만으론 자립 불가 — 기념품숍·레스토랑 연계가 수익 보완의 핵심(E-0404)
    'bm5': ['rv-adm', 'rv-expo', 'rv-goods', 'rv-art', 'rv-pub', 'rv-sub', 'rv-b2b', 'rv-dine'],
    # 상품·도매·IP 3층. 유통 채널을 쥐면 수수료가 붙는다(E-0414)
    'ax2': ['rv-goods', 'rv-whole', 'rv-ip', 'rv-expo', 'rv-adm', 'rv-edu',
            'rv-comm', 'rv-b2b', 'rv-sub'],
    # 카페 → 레스토랑 → 복합 순으로 투자비가 오른다(E-0410)
    'ax1': ['rv-tea', 'rv-dine', 'rv-whole', 'rv-sub'],
    # 임대료 — 앵커 효과로 마케팅비 없이 캐시플로우(E-0402). 1898은 20개 매장(E-0416)
    'bm3': ['rv-rent', 'rv-b2b', 'rv-lease', 'rv-comm'],
    # 부동산 임대 + 납골당·영대공양이 일본 사원 BM의 다수(E-0415)
    'ax3': ['rv-cha', 'rv-mgmt', 'rv-sub', 'rv-don', 'rv-goods'],
    # 독립 수익 모델이 약해 헌금·교단 재정 의존 90%+(E-0403)
    'bm4': ['rv-free', 'rv-fee', 'rv-lease', 'rv-goods', 'rv-don'],
    'bm1': [],      # 입장료 단일 엔진 90%+ — 봉은사는 그 엔진을 닫았다(E-0400)
    'bm6': [],      # 종교 주체가 빠지는 구조 — 전제가 다르다
    'bm7': [],      # 정부 재정 전액 — 재현 불가
}

def _var_nodes(_atoms):
    out = []
    for b in [x[0] for x in BMS]:
        items_by = {}
        for x in _SV:
            if b in bms_of(x):          # 연계로 걸린 것도 그 모델의 수익원이 된다
                for rid in _revenues_of(x):
                    items_by.setdefault(rid, []).append(x)
        # 선언된 가능 수익원 + 실제로 서비스가 걸린 것(선언에서 빠졌어도 살린다)
        ids = list(BM_REVENUE.get(b, []))
        for rid in items_by:
            if rid not in ids:
                ids.append(rid)
        for rid in ids:
            name, note = REV_INFO[rid]
            items = items_by.get(rid, [])
            out.append(dict(
                id=f'{b}-{rid}', label=name, category=b,
                summary=note + '\n' + (' / '.join(y['label'][:22] for y in items[:4]) if items
                                        else '⚠ 이 모델이면 가능한데 지금 서비스가 없다'),
                match=(lambda bb, rr: (lambda s: bb in bms_of(s)
                                       and rr in _revenues_of(s)))(b, rid),
                evidence=[dict(quote=(f'{name} — {len(items)}건 · ' +
                                      ', '.join(y['label'][:18] for y in items)) if items
                                     else f'{name} — 가능하지만 미가동. {note}',
                               src=f'{RPT} #STEP 5 · shards/05-bm.json')]))
    return out

# ── Segment E · 비즈니스 모델 유형 ────────────────────────────────
# variant(매스·프리미엄·멤버십…)는 수익 항목이 아니라 '파는 방식'이다 — D-1과 축이 다르다.
# 9개 값을 그대로 세우면 열이 산만해지므로, 돈을 버는 구조가 같은 것끼리 4유형으로 묶는다.
# 건수는 라벨에 박지 않는다 — 렌더러가 필터마다 다시 센다(설명줄에는 구성만 적는다).
BIZ = [
    ('bz-mass', '대중 유입형',  '회전과 접근성으로 트래픽을 받는다',
     ['매스', '기본'],       '단가는 낮고 수용력이 매출을 만든다 — 진입 장벽이 가장 낮다'),
    ('bz-prem', '고단가 관계형', '객단가와 재방문을 관계로 묶는다',
     ['프리미엄', '멤버십'],  '1회 소비를 연간 관계로 바꾸는 층 — 같은 인프라 위에서 단가를 올린다'),
    ('bz-b2b',  '도매 · 기업형', '좌석 수 한계를 넘어 밖으로 판다',
     ['공급', 'B2B'],       '경내 수용력과 무관하게 확장된다 — 계약 단위가 크고 영업이 필요하다'),
    ('bz-base', '기반 · 공익형', '수익이 아니라 성립 조건과 공익 지표',
     ['인프라', '공익'],     '이것 없이는 위 세 유형이 작동하지 않는다 — 비용으로 읽되 빼면 안 된다'),
    ('bz-x',    '✕ 배제',      '현행 법으로 닫혀 있다',
     ['배제'],              '영업행위 금지·용도 불일치로 매출이 성립하지 않는다'),
]
BIZ_OF = {v: b[0] for b in BIZ for v in b[3]}
BIZ_NODES = [dict(id=b[0], label=b[1], kind='group', category='비즈니스 모델',
                  summary=f'{b[2]}\n{" · ".join(b[3])}',
                  match=(lambda bid: (lambda s: BIZ_OF.get(s.get('variant')) == bid))(b[0]),
                  evidence=[dict(quote=f'{b[1]} — {b[4]}', src=f'{RPT} #STEP 5')])
             for b in BIZ]

# ── 법 관문 ───────────────────────────────────────────────────────
_HI = lambda x: (x.get('eval') or {}).get('revenue') == 'H'
_TIERS = [
    ('t1', 'Tier 1 · 해석 없이 가능', 'Tier1',
     '시행령 제7조 문언에 그대로 걸리는 것 — 유권해석을 기다리지 않는다'),
    ('t2', 'Tier 2 · 유권해석 전제', 'Tier2', '선례는 있으나 문체부 종무실 확인이 필요한 영역'),
    ('t3', 'Tier 3 · 공론화·제도 개선 시', 'Tier3',
     '현행 법으로는 닫혀 있다 — 7건 전부 배제 판정(프랜차이즈 카페·주류·일반숙박·웨딩홀 등)'),
]
LEGAL_NODES = []
for _tid, _lab, _tv, _note in _TIERS:
    _m = [s for s in _SV if tier(s) == _tv]
    _h = [s for s in _m if _HI(s)]
    LEGAL_NODES.append(dict(
        id=_tid, label=_lab, kind='group', category='법적 관문',
        summary=f'{_note}\n고수익(H) {len(_h)}건 / {len(_m)}건 = {len(_h)/max(1,len(_m)):.0%}',
        match=(lambda tv: (lambda s: tier(s) == tv))(_tv),
        evidence=[dict(quote=f"{len(_m)}건 중 고수익 {len(_h)}건 — " +
                             ', '.join(x['label'][:20] for x in (_h or _m)[:4]),
                       src=f'{SRC} #service[*].eval.legal = {_tv}'),
                  dict(quote='지금 그대로 되는 44개 중 돈이 되는 것은 5개(11%)인데, 해석을 받아야 하는 '
                             '65개 중에는 19개(29%)다 — 돈은 회색지대 쪽에 몰려 있다. '
                             '유권해석이 수익 천장을 정한다.', src=f'{RPT} #STEP 7.1')]))

# ── Concept (2026-07-29 대표 확정) ────────────────────────────────
_CONCEPTS = [
    ('C-A', 'Concept A', 'Cultural Destination',
     '한국 불교를 가장 먼저 떠올리게 하는 상징적 문화 목적지',
     ['엔진 · Attract (밖→안)', '상징성 · 대중성 · 관광',
      '외국인 · MZ · 일반 방문객', '방문 · 체험 · 관광 · 굿즈 · F&B']),
    ('C-B', 'Concept B', 'Premium Wellness Center',
     '불교 문화와 프리미엄 웰니스를 결합한 강남형 멤버십 플랫폼',
     ['엔진 · Engage (안에서 더 깊이)', '프리미엄 · 멤버십 · 수익성',
      '강남 고소득층 · 기업 · VIP', '멤버십 · 프리미엄 프로그램 · 기업 서비스']),
    ('C-C', 'Concept C', 'Content & Business Lab',
     '불교 콘텐츠를 상품화해 전국 사찰로 확산하는 생산·공급 플랫폼',
     ['엔진 · Produce & Scale (안→밖)', '상품화 · 산업화 · 확산성',
      '전국 사찰 · 기관 · 문화 소비자', '제조 · 공급 · 유통 · 라이선스 · IP']),
]
CONCEPT_NODES = [dict(id=c[0], label=c[1], kind='card', caption=c[2], category=c[0],
                      summary=c[3], members=c[4],
                      match=(lambda cid: (lambda s: cid[2:] in (s.get('scenario') or [])))(c[0]),
                      evidence=[dict(quote=c[3],
                                     src=f'{PROG} #3대 컨셉 확정 정의 (대표 확정, 2026-07-29)')])
                 for c in _CONCEPTS]

# ══════════════════════════════════════════════════════════════════
# dec = 이 열을 Decision Map에서 어떻게 쓰는가 (매트릭스 화면에는 영향 없다)
#   tab=상단 탭 · col=중앙 열 · detail=원자 열 · filter=좌측 체크 · skip=안 씀
# 같은 IR로 두 화면을 뽑기 위한 힌트다 — build_sankey.py --render decision
STAGES = [
    dict(id='s1', label='Segment A · 조건부 생존군', order=0, role='origin', axis='target',
         note='어떤 전략 선택 아래에서 살아남는가 — 전략 선택축(C1·C2·C5·C6)에서 역산한 값이며 '
              '방문객 속성이 아니다. 실측 기반 타겟은 수요 매트릭스(demand-matrix)를 볼 것',
         nodes=TARGET_NODES, pick=('rare', 2), dec='filter'),
    dict(id='s2', label='Segment B · Direction', order=1, role='structure', axis='dir',
         note='어떤 시설로 규정하는가', nodes=DIRECTION_NODES, pick='first', kind='group',
         dec='col'),
    dict(id='s3', label='Segment C · 서비스·컨텐츠', order=2, role='structure', axis='cat',
         note='116건을 10개 군으로 그룹핑', nodes_fn=_cat_nodes, kind='group', dec='col'),
    dict(id='s3b', label='C-1 · 서비스 상세', order=3, role='structure', axis='svc',
         atomic=True, note='그룹을 누르면 그 안의 것만 남는다', nodes_fn=_svc_nodes,
         dec='detail', dec_group='s3'),
    dict(id='s4', label='Segment D · 수익모델', order=4, role='synthesis', axis='bm',
         note='종교시설이 먹고사는 10가지 — 쓸 수 있는 칸과 못 쓰는 칸',
         nodes=BM_NODES, kind='group', dec='col'),
    # 77항목은 Decision Map의 4열 배치에 안 들어간다 — 매트릭스에서 본다
    dict(id='s4b', label='D-1 · 수익 항목', order=5, role='synthesis', axis='revenue',
         atomic=True, note='이 모델에서 돈이 실제로 어디서 들어오는가', nodes_fn=_var_nodes,
         dec='skip'),
    dict(id='s4c', label='Segment E · 비즈니스 모델', order=6, role='synthesis', axis='biz',
         note='같은 수익 항목도 파는 방식이 다르다 — 돈 버는 구조로 묶는다',
         nodes=BIZ_NODES, kind='group', pick='first', dec='col'),
    # 법 관문은 흐름의 한 칸이 아니라 조건이다 — 선을 지우고 옵션 필터로 남긴다.
    # D-1에서 여기로 내려꽂히던 51개 선이 평균 1,251px·최대 3,065px여서 화면을 덮었다.
    dict(id='s5', label='법 관문', order=7, role='synthesis', axis='legal',
         filter_only=True, note='여기서 수익의 윗부분이 잘린다 — 유권해석이 천장을 정한다',
         nodes=LEGAL_NODES, kind='group', dec='filter+col'),
    # ▼ 컨셉 해석 구조를 옵션 열로 넣는다면 여기(order 8)가 자리다. atomic=True면 상세 열.
    dict(id='s6', label='Concept', order=8, role='conclusion', axis='concept',
         note='2026-07-29 대표 확정', nodes=CONCEPT_NODES, kind='card', dec='tab'),
]

META = dict(
    title='봉은문화센터 — 전략 매트릭스',
    subtitle=f'서비스·컨텐츠 {len(_SV)}건 → 수익모델 10유형 → 법 관문 → 3대 컨셉 · '
             f'법이 자르는 지점이 보이도록 배제 7건도 태웠다 · ◻︎ 표시는 자료가 없어 비워둔 슬롯',
    source=f'{SRC} · BM 10유형은 {RPT} · 3대 컨셉은 {PROG}',
    generated_at='2026-07-31', axis='topic', mode='structure',
    value_note='관계 표시 — 선 굵기에 양의 뜻 없음')

CONCLUSIONS = [
    dict(node_id='C-A',
         statement='A는 밖에서 안으로 끌어오는 엔진이다 — 상징성·대중성·관광으로 성립한다',
         so_what='문화시설 방향과 대중 유입형 BM을 중심에 두고, Tier1 서비스로 먼저 연다',
         support=[s['id'] for s in _SV if 'A' in (s.get('scenario') or [])][:6]),
    dict(node_id='C-B',
         statement='B는 안에서 더 깊이 들어가는 엔진이다 — 프리미엄·멤버십·수익성으로 성립한다',
         so_what='고단가 관계형 BM이 핵심이고, 유권해석(Tier2)이 천장을 결정한다',
         support=[s['id'] for s in _SV if 'B' in (s.get('scenario') or [])][:6]),
    dict(node_id='C-C',
         statement='C는 안에서 밖으로 내보내는 엔진이다 — 상품화·산업화·확산성으로 성립한다',
         so_what='수익시설 방향과 도매·기업형 BM이 축이며, 상품화·공급군(G10) 26건이 재료다',
         support=[s['id'] for s in _SV if 'C' in (s.get('scenario') or [])][:6]),
]

# ── 아직 자료가 없어 비워둔 칸 ────────────────────────────────────
SLOTS = [
    dict(id='slot-o2e', stage='s1', label='◻︎ 기업 · VIP (세분 필요)',
         why='S4-O2e(기업)·S4-O2f(VIP) 슬롯이 0건이다. 지금은 "비즈니스 이해관계자·B2B" 하나로 '
             '뭉쳐 있어 강남 법인 수요와 개인 VIP 수요가 구분되지 않는다.',
         need='기업 워크숍·리트리트 수요 조사 / 강남 법인 복지예산 규모 / VIP 멤버십 지불의향'),
    dict(id='slot-c1', stage='s2', label='◻︎ 프리미엄 ↔ 대중화 축 (S3-C1)',
         why='지금 Direction은 C2(종교↔문화)×C6(브랜드↔산업화)만 쓴다. '
             '리포트 3.1에 5축 분석과 권고(프리미엄)까지 있으나 서비스 태깅이 없어 방향 축으로 못 세웠다.',
         need='C1 판정을 서비스 단위로 태깅 — 어느 방향이 어느 서비스군을 살리는가'),
    dict(id='slot-c5', stage='s2', label='◻︎ 지역 ↔ 글로벌 (판정 완료 · 갈림길 아님)',
         why='master-strategy-report STEP 3이 "C5는 갈림길이 아니라 실행 방법"으로 판정했다. '
             '지금은 Target 판정에만 쓰이고 있어 그 판정 근거가 이 지도에 안 보인다.',
         need='3.5 말미의 판정 근거를 Target 노드 근거로 편입 — 방향 축으로는 세우지 않는다'),
    dict(id='slot-c4', stage='s2', label='◻︎ 중창불사 관계 축 (S3-C4)',
         why='5대 갈림길 중 C4(본원 공사와 독립이냐 연계냐)만 서비스 태깅이 없어 흐름에 못 붙었다.',
         need='중창불사 3단계 일정 × 개관 시점 간섭 검토 — 독립/상호보완/백업전제 중 무엇인가'),
    dict(id='slot-loc', stage='s2', label='◻︎ 입지 · 상권 반영 (S4-O4)',
         why='Location 슬롯 66건(코엑스 도보 3분·강남 생활인구·GBC 2031)이 이 매트릭스에 '
             '들어오지 못했다. 입지는 방향을 가르는 조건인데 지금은 어디에도 없다.',
         need='상권 데이터를 Direction 판정 기준에 편입 — 어느 방향이 이 입지에서만 가능한가'),
    dict(id='slot-bmnum', stage='s4', label='◻︎ 유형별 매출 산식',
         why='BM 10유형과 서비스 그룹은 이었지만, 유형마다 얼마가 도는지는 아직 없다. '
             '리포트도 "수익 추정 신규 산출 필요"로 남겨두었다.',
         need='유형별 객단가·회전·좌석/면적 기준 매출 산식 — 특히 C안(축②)은 기존에 없던 모델이라 전부 신규'),
]

WHITESPACE = [
    dict(type='배제', where=['t3'],
         question='Tier 3 · 7건은 현행 법으로 닫혀 있다 — 공론화로 열 가치가 있는가?',
         idea='프랜차이즈 카페·주류·일반숙박·웨딩홀 — 열리면 수익 구조가 바뀌지만 정체성 비용이 크다'),
    dict(type='집중', where=['G10'],
         question='G10 상품화·공급이 26건으로 최대군인데 전부 C안에 몰려 있다 — A·B와 접점이 없는가?',
         idea='상품화 라인 일부를 A의 굿즈·B의 멤버십 상품으로 끌어오면 세 컨셉이 재료를 공유한다'),
]
