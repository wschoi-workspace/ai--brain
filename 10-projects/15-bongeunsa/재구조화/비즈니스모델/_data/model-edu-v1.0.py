# -*- coding: utf-8 -*-
"""RL-05 교육·체험 클래스 비즈니스 모델 v1.0

핵심 1: 마스터의 단일 공식(회차단가×정원×가동률×연회차)은 클래스에만 맞다.
        9개 서비스 중 즉석체험은 정원 개념이 없고, 과정형은 회차가 아니라 기수다.
핵심 2: 이 라인의 병목은 공간도 수요도 아니라 '진행 인력'이다.
        RL-06 명상이 이미 810회로 지도 인력 한계를 선언했고, 여기에 RL-05가 더 얹힌다.
핵심 3: RL-01 전시가 해설·도슨트 4.3억 + 심화 프로그램 0.7억을 이미 계상했다.
        RL-05의 해설·프라이빗 계열과 같은 상품이다 — 한쪽에서 빼야 한다.
"""
def eok(v): return v/1e8
CASE = ["보수", "기준", "낙관"]

BENCH = """
[단가 근거]
◆ E-1042 (B)  티 테이스팅·차 명상은 기업 프로그램 시장에 1인 3~7만원으로 존재하며,
              봉은사 다도·차담은 최상위 정통성 — 1인 5~10만원 책정에 무리 없음
◆ E-1007 (A)  오행 인요가 나이트 ₩80,000 · 금 19~21시 · 정원 16명이
              Viator 봉은사 19건 중 판매 1위. 나머지 18건은 전부 경유형
              → 60분 규격을 깬 상품이 이미 최고 실적을 냈다
◆ E-0581 (A)  K-Temple 체험 8~15만원 (자체 제언)
◆ E-0311 (A)  예약 없이 방문한 외국인이 할 수 있는 참여 활동이 사실상 없어 체류가 30분~1시간에 그친다
              — 태국은 3천~5천원 공양 세트로 5~10분 즉석 참여가 가능하다
  → 즉석 체험의 단가 앵커는 클래스가 아니라 '3~5천원 공양 세트'다

[선례 — 사찰음식 교육은 이미 조계종이 하고 있다]
◆ E-0435 (A)  조계종은 사찰음식을 한국사찰음식문화체험관(문화체험)·향적세계(교육)·
              발우공양(다이닝) 3기관 체계로 분업 운영하고 있다
◆ E-0431 (A)  사찰음식 명장 1호 선재 스님이 법룡사 1층에서 선재사찰음식문화센터를 운영하며
              매주 수요 강좌와 체험 클래스 수강료를 수익 모델로 삼는다
  → 봉은사가 사찰음식 교육을 신설하면 종단 내부 기관과 중복된다.
    이는 리스크이면서 동시에 해법이다 — 커리큘럼과 강사를 가져오는 경로가 이미 있다.
◆ E-0481 (A)  왓포는 사원 안에 '발상지' 브랜드를 건 정규 교육기관을 두고
              4단계 15개 코스를 강사:학생 1:6으로 운영하며, 수료증이 태국 전역의 자격으로 인정된다
  → 지도자 양성 과정이 강사 공급을 스스로 재생산하는 구조 (E-0644가 지목한 바로 그것)

[수요 — 이 라인의 강점]
◆ E-1036 (B)  '사찰이 아니라 기업 같다'는 반발은 유료 공양간·판매대·연등 접수에서 나오고
              해설·강좌·워크숍에는 나타나지 않는다 — 배움이 유료화 저항이 가장 낮은 상품군
◆ E-0343 (A)  삼성동에는 상시 운영 체험형 공방·원데이클래스 공간이 거의 없고
              워크숍 공간도 대관형에 그쳐, 성수동식 생태계 자체가 없다
◆ E-0336 (A)  경전·의례가 한문 중심이라 불교 용어의 난해함이 MZ 접근 장벽으로 작동한다
◆ E-0313 (A)  통역이 있어도 스님 말의 뉘앙스와 깊이가 전달되지 않아
              외국인이 체험의 의미층에 도달하지 못한다

[제약]
◆ E-0041 (A)  문화집회시설 용도로 음식 조리 원천 불가 → 9개 서비스 중 2건이 이 게이트 뒤에 있다
◆ E-0532 (A)  면적 배분 — '외국인 체험 500㎡'는 있으나 클래스·공방 전용 강의실 항목은 없다
              (전시·체험 2,000㎡ 안에 뭉쳐 있음)
◆ RL-06 명상 검토 v1.0  유인 상품 진행 회차 810회/년 · "지도 인력이 이 라인의 한계"
              + '스님과의 대화'(주 5회)의 경합 라인으로 RL-05를 직접 지목
◆ RL-01 전시 검토 v1.2  권고안에 해설·도슨트 4.3억 + 심화 프로그램(인경 체험) 0.7억 계상
"""

# ══════════════════════════════════════════════════════════════════
# 모수
# ══════════════════════════════════════════════════════════════════
CV = [110_000, 255_000, 525_634]        # 문화센터 연간 방문객 (마스터 v0.2)

# ══════════════════════════════════════════════════════════════════
# 트랙 A · 즉석 체험 — 클래스가 아니다. 정원도 가동률도 없다.
# ══════════════════════════════════════════════════════════════════
# E-0645 외국인 즉석 체험 (헌등·공양·필사, 5~10분, 무예약)
# 마스터는 이것을 '회차단가 × 정원 × 가동률 × 연회차'로 계산했지만
# 실제 구조는 리테일(RL-04)과 같은 'CV × 전환율 × 객단가'다.
INST_CONV = [0.03, 0.08, 0.12]          # 방문객 중 즉석 체험 참여율
INST_PP   = [3_000, 5_000, 8_000]       # 객단가 — E-0311 태국 공양세트 3~5천원 앵커
def rev_instant(i): return CV[i] * INST_CONV[i] * INST_PP[i]

# ══════════════════════════════════════════════════════════════════
# 트랙 B · 클래스형 — 마스터의 원래 공식이 맞는 유일한 영역
# ══════════════════════════════════════════════════════════════════
# (단가, 정원, 가동률, 연회차, 조리게이트 여부, 라벨, 근거)
CLASSES = [
    ([50_000,  70_000, 100_000], [16,16,20], [0.50,0.65,0.75], [120,250,340], False,
     "다도·차담·필사 클래스", "E-1042 5~10만 · E-1007 정원 16"),
    ([40_000,  60_000,  80_000], [12,16,16], [0.45,0.60,0.70], [ 80,150,220], False,
     "공방·메이커 클래스",   "E-0343 삼성동 공백"),
    ([20_000,  30_000,  40_000], [16,20,20], [0.50,0.65,0.75], [ 60,100,140], False,
     "청소년·어린이 문화교실", "E-0647 공익 · rev L"),
    ([70_000, 100_000, 150_000], [12,16,16], [0.50,0.65,0.75], [ 60,120,180], True,
     "원데이 사찰음식 클래스", "E-0641 · 조리 게이트"),
]
def rev_class(i, only=None):
    t = 0
    for fee, cap, occ, n, cook, *_ in CLASSES:
        if only is not None and cook != only: continue
        t += fee[i]*cap[i]*occ[i]*n[i]
    return t
def n_class(i, only=None):
    return sum(n[i] for fee,cap,occ,n,cook,*_ in CLASSES if only is None or cook==only)

# ══════════════════════════════════════════════════════════════════
# 트랙 C · 과정형 — 회차가 아니라 기수다
# ══════════════════════════════════════════════════════════════════
# (과정단가, 정원, 연 기수, 기당 회차, 조리게이트, 라벨, 근거)
COURSES = [
    ([ 300_000,  450_000,  600_000], [16,20,24], [2,3,4], 12, False,
     "불교 아카데미 정규강좌", "E-0643 · Tier2 중 리스크 최저"),
    ([1_000_000,1_500_000,2_500_000], [12,16,20], [1,2,2], 15, False,
     "지도자 양성 과정",       "E-0644 · E-0481 왓포 1:6 · 4단계 15코스"),
    ([  800_000,1_200_000,1_800_000], [12,16,16], [1,2,3], 10, True,
     "사찰음식 전문가 과정",   "E-0642 · 조리 게이트"),
]
def rev_course(i, only=None):
    t = 0
    for fee, cap, gi, sess, cook, *_ in COURSES:
        if only is not None and cook != only: continue
        t += fee[i]*cap[i]*gi[i]
    return t
def n_course(i, only=None):
    return sum(gi[i]*sess for fee,cap,gi,sess,cook,*_ in COURSES if only is None or cook==only)

# ══════════════════════════════════════════════════════════════════
# 트랙 D · 해설·프라이빗 — RL-01이 이미 계상했다
# ══════════════════════════════════════════════════════════════════
# E-0649 현대어 교리 해설 / E-0646 외국인 프라이빗 투어
# RL-01 전시 검토 권고안: 해설·도슨트 4.3억 + 심화 프로그램 0.7억 = 5.0억(기준)
# 같은 상품을 양쪽에서 세지 않기 위해 본 검토는 0원으로 두고 경고만 남긴다.
RL01_NARRATION = [0.8e8, 5.0e8, 17.8e8]   # 참고값 (RL-01 권고안 해설 0.6/4.3/16.0 + 심화 0.2/0.7/1.8)
def rev_narration(i): return 0

def rev_all(i, cook_gate_open=True):
    r = rev_instant(i) + rev_course(i, only=False) + rev_class(i, only=False) + rev_narration(i)
    if cook_gate_open:
        r += rev_class(i, only=True) + rev_course(i, only=True)
    return r

# ══════════════════════════════════════════════════════════════════
# ★ 진행 인력 검산 — 이 라인의 진짜 병목
# ══════════════════════════════════════════════════════════════════
HOURS_PER_SESSION = 2.5      # 진행 시간
PREP_RATIO        = 0.6      # 준비·정리 (진행시간 대비)
FTE_HOURS         = 1_800    # 연간 1인 가동시간
RL06_SESSIONS     = 810      # RL-06 명상 유인 상품 진행 회차 (검토 v1.0 실측 전제)
RL07_T2_SESSIONS  = 12       # RL-07 B2B 프리미엄 리트리트 (검토 v1.0 기준안)
# 분야가 갈린다 — 한 사람이 사찰음식·불교학·다도·공방·외국어를 다 하지 못한다
DOMAINS = ["다도·차담", "불교학", "사찰음식", "공방·메이커", "어린이", "외국어 해설"]

def edu_sessions(i, cook_gate_open=True):
    n = n_class(i, only=False) + n_course(i, only=False)
    if cook_gate_open: n += n_class(i, only=True) + n_course(i, only=True)
    return n
def fte(sessions): return sessions * HOURS_PER_SESSION * (1+PREP_RATIO) / FTE_HOURS

# ══════════════════════════════════════════════════════════════════
# 원가 — RL-06 검토의 강사료 단가를 준용해 라인 간 정합을 맞춘다
# ══════════════════════════════════════════════════════════════════
FEE_CLASS  = 100_000        # 클래스 회당 강사료 (RL-06 드롭인 10만원 준용)
FEE_COURSE = 150_000        # 과정 회당 강사료 (전문성 가산)
MAT_CLASS  = [0.25, 0.20, 0.16]   # 클래스 재료비율 (공방·사찰음식 재료 포함)
MAT_COURSE = [0.15, 0.12, 0.10]
MAT_INST   = [0.35, 0.30, 0.25]   # 즉석 체험 — 헌등·공양물 원가율이 높다
STAFF      = [2, 3, 4]; WAGE = 3.5e7      # 프로그램 기획·운영 상주
MKT        = [0.10, 0.08, 0.06]
CAPEX      = [8.0e8, 11.0e8, 14.0e8]      # 강의실·공방 설비 (조리대 제외)
DEP_YEARS  = 10

def cost_of(i, cook_gate_open=True):
    ncl = n_class(i, only=False) + (n_class(i, only=True) if cook_gate_open else 0)
    nco = n_course(i, only=False) + (n_course(i, only=True) if cook_gate_open else 0)
    teach = ncl*FEE_CLASS + nco*FEE_COURSE
    rc = rev_class(i, only=False) + (rev_class(i, only=True) if cook_gate_open else 0)
    rk = rev_course(i, only=False) + (rev_course(i, only=True) if cook_gate_open else 0)
    mat = rc*MAT_CLASS[i] + rk*MAT_COURSE[i] + rev_instant(i)*MAT_INST[i]
    return teach, mat

def op(i, cook_gate_open=True):
    rev = rev_all(i, cook_gate_open)
    teach, mat = cost_of(i, cook_gate_open)
    return rev - teach - mat - STAFF[i]*WAGE - rev*MKT[i] - CAPEX[i]/DEP_YEARS

# ── 출력 ──────────────────────────────────────────────────────────
print(BENCH)
W = 112
print("="*W)
print("RL-05 교육·체험 — 마스터의 단일 공식이 4개 다른 상품군을 하나로 묶었다")
print("="*W)
print("  마스터 v0.2: 회차단가 5/7/10만 × 정원 16/16/20 × 가동 50/65/75% × 연회차 300/600/800")
print("  → 이 공식은 '트랙 B 클래스형'에만 맞는다. 즉석체험은 정원이 없고, 과정형은 기수제다.")
print()
print(f"{'':<32}{'보수':>16}{'기준':>16}{'낙관':>16}")
print("-"*W)
print("[트랙 A] 즉석 체험 — CV × 전환율 × 객단가 (정원·가동률 개념 없음)")
print(f"{'  참여율':<32}"+"".join(f"{INST_CONV[i]:>15.0%}" for i in range(3)))
print(f"{'  객단가':<32}"+"".join(f"{INST_PP[i]:>14,}원" for i in range(3)))
print(f"{'  매출':<32}"+"".join(f"{eok(rev_instant(i)):>15.2f}억" for i in range(3)))
print()
print("[트랙 B] 클래스형 — 회차단가 × 정원 × 가동률 × 연회차")
for fee,cap,occ,n,cook,lab,src in CLASSES:
    mark = " ※조리" if cook else ""
    print(f"  {lab+mark:<30}"+"".join(f"{eok(fee[i]*cap[i]*occ[i]*n[i]):>15.2f}억" for i in range(3)))
    print(f"{'     단가×정원×가동×회차':<32}"+"".join(
        f"{f'{fee[i]//10000}만×{cap[i]}×{occ[i]:.0%}×{n[i]}':>16}" for i in range(3)))
print(f"{'  소계':<32}"+"".join(f"{eok(rev_class(i)):>15.2f}억" for i in range(3)))
print()
print("[트랙 C] 과정형 — 과정단가 × 정원 × 연 기수 (회차 모델 아님)")
for fee,cap,gi,sess,cook,lab,src in COURSES:
    mark = " ※조리" if cook else ""
    print(f"  {lab+mark:<30}"+"".join(f"{eok(fee[i]*cap[i]*gi[i]):>15.2f}억" for i in range(3)))
    print(f"{'     단가×정원×기수':<32}"+"".join(
        f"{f'{fee[i]//10000}만×{cap[i]}×{gi[i]}기':>16}" for i in range(3)))
print(f"{'  소계':<32}"+"".join(f"{eok(rev_course(i)):>15.2f}억" for i in range(3)))
print()
print("[트랙 D] 해설·프라이빗 — RL-01 전시가 이미 계상했다")
print(f"{'  본 검토 계상':<32}"+"".join(f"{0.0:>15.2f}억" for i in range(3)))
print(f"{'  (RL-01 권고안 해설+심화)':<32}"+"".join(f"{eok(RL01_NARRATION[i]):>15.2f}억" for i in range(3)))
print("-"*W)
print(f"{'합계 (조리 게이트 열림)':<32}"+"".join(f"{eok(rev_all(i,True)):>15.2f}억" for i in range(3)))
print(f"{'합계 (조리 게이트 닫힘)':<32}"+"".join(f"{eok(rev_all(i,False)):>15.2f}억" for i in range(3)))
print(f"{'  조리 종속분':<32}"+"".join(
    f"{eok(rev_all(i,True)-rev_all(i,False)):>15.2f}억" for i in range(3)))
print(f"{'  조리 종속 비중':<32}"+"".join(
    f"{(rev_all(i,True)-rev_all(i,False))/rev_all(i,True):>15.0%}" for i in range(3)))
print(f"{'(마스터 v0.2 RL-05)':<32}"+"".join(f"{v:>16}" for v in ["1.20억","4.40억","12.00억"]))
print()

print("="*W)
print("★ 진행 인력 검산 — 공간도 수요도 아니라 사람이 병목이다")
print("="*W)
print(f"  전제: 회당 진행 {HOURS_PER_SESSION}h + 준비·정리 {PREP_RATIO:.0%} · FTE {FTE_HOURS:,}h/년")
print(f"  RL-06 명상 검토가 이미 유인 상품 {RL06_SESSIONS}회/년에서 '지도 인력이 이 라인의 한계'라고 선언했다.")
print()
print(f"{'':<32}{'보수':>16}{'기준':>16}{'낙관':>16}")
print("-"*W)
print(f"{'RL-05 연 진행 회차':<32}"+"".join(f"{edu_sessions(i):>15,}회" for i in range(3)))
print(f"{'  + RL-06 명상 유인':<32}"+"".join(f"{RL06_SESSIONS:>15,}회" for i in range(3)))
print(f"{'  + RL-07 B2B 프리미엄':<32}"+"".join(f"{RL07_T2_SESSIONS:>15,}회" for i in range(3)))
tot_sess = [edu_sessions(i)+RL06_SESSIONS+RL07_T2_SESSIONS for i in range(3)]
print(f"{'  = 3개 라인 합계':<32}"+"".join(f"{tot_sess[i]:>15,}회" for i in range(3)))
print(f"{'필요 FTE (단순 시간환산)':<32}"+"".join(f"{fte(tot_sess[i]):>15.1f}명" for i in range(3)))
print(f"{'  영업 300일 기준 일 평균':<32}"+"".join(f"{tot_sess[i]/300:>15.1f}회" for i in range(3)))
print("-"*W)
print(f"  그런데 단순 FTE 환산이 답이 아니다 — 분야가 갈린다.")
print(f"  필요 분야 {len(DOMAINS)}종: {' · '.join(DOMAINS)}")
print(f"  한 사람이 사찰음식과 불교학과 공방과 외국어 해설을 동시에 하지 못한다.")
print(f"  분야별로 쪼개면 기준안에서 1인당 연 {tot_sess[1]/len(DOMAINS):.0f}회 = 주 {tot_sess[1]/len(DOMAINS)/48:.1f}회.")
print(f"  → 상근이 성립하지 않는 파트타임 {len(DOMAINS)}명을 상시 확보·유지해야 한다는 뜻이다.")
print()

print("="*W)
print("★ 그래서 지도자 양성 과정이 매출 라인이 아니라 공급 엔진이다")
print("="*W)
i = 1
lead = [f for f in COURSES if f[5] == "지도자 양성 과정"][0]
grad = lead[1][i] * lead[2][i]
RETURN_RATE = [0.15, 0.30, 0.45]   # 졸업생 중 진행자로 복귀하는 비율 — 실측 없음, 가정
SESS_PER_GRAD = 50                 # 복귀자 1인당 연 진행 회차
print(f"  지도자 양성 과정 기준안: 정원 {lead[1][i]}명 × 연 {lead[2][i]}기 = 연 {grad}명 배출")
print(f"  매출 기여는 {eok(lead[0][i]*lead[1][i]*lead[2][i]):.2f}억으로 이 라인의 {lead[0][i]*lead[1][i]*lead[2][i]/rev_all(i,True):.0%}에 그친다.")
print(f"  값어치는 매출이 아니라 진행 능력이다 — 졸업생 일부가 진행자로 복귀한다.")
print()
print(f"{'복귀율':<20}{'복귀 인원':>14}{'확보 회차':>14}{'3개 라인 대비':>16}")
print("-"*W)
for r in RETURN_RATE:
    n_ret = grad*r
    print(f"{r:<20.0%}{n_ret:>13.1f}명{n_ret*SESS_PER_GRAD:>13,.0f}회{n_ret*SESS_PER_GRAD/tot_sess[i]:>15.0%}"
          + ("  ←기준 가정" if abs(r-0.30) < 0.01 else ""))
print("-"*W)
print(f"  E-0481 왓포는 이 구조를 이미 증명했다 — 4단계 15개 코스, 강사:학생 1:6, 수료증이 전국 자격.")
print(f"  🔴 복귀율은 실측이 아니라 가정이다. 국내에 대조할 사례가 없다.")
print(f"  🔴 1기 배출까지 최소 1년 — 개관 1년차에는 이 엔진이 아직 돌지 않는다.")
print(f"     즉 1년차 진행 인력은 전량 외부 조달이고, 그 확보 여부가 매출의 전제다.")
print()

print("="*W)
print("★ 중복 경고 — RL-01이 같은 상품을 이미 계상했다")
print("="*W)
print(f"  RL-01 전시 권고안   해설·도슨트 {0.6:.1f}/{4.3:.1f}/{16.0:.1f}억 + 심화 프로그램 {0.2:.1f}/{0.7:.1f}/{1.8:.1f}억")
print(f"  RL-05 트랙 D        E-0649 현대어 교리 해설 · E-0646 외국인 프라이빗 투어")
print(f"  → 같은 상품이다. RL-01은 '전시를 팔지 말고 해설을 팔아야 한다'는 결론의 근거로 이 매출을 썼다.")
print(f"    본 검토는 RL-05에서 0원으로 두고 RL-01에 남긴다. 반대로 옮기려면 RL-01 권고안이 무너진다.")
print(f"    ※ RL-01 기준안 해설 4.3억은 RL-05 전체({eok(rev_all(1,True)):.2f}억)의 {5.0/eok(rev_all(1,True)):.0%}에 해당하는 규모다.")
print()
print(f"  RL-07 B2B T2 프리미엄  정원 16명 · 연 12회 — E-1007 같은 규격, 같은 방, 같은 진행자")
print(f"  RL-06 '스님과의 대화'  주 5회 — RL-06 검토가 경합 라인으로 RL-05를 직접 지목")
print()

print("="*W)
print("★ 조리 게이트 — 9개 서비스 중 2건이 R-03 뒤에 있다")
print("="*W)
print(f"{'':<32}{'보수':>16}{'기준':>16}{'낙관':>16}")
print("-"*W)
print(f"{'게이트 열림 (조리 가능)':<32}"+"".join(f"{eok(rev_all(i,True)):>15.2f}억" for i in range(3)))
print(f"{'  영업이익':<32}"+"".join(f"{eok(op(i,True)):>+15.2f}억" for i in range(3)))
print(f"{'게이트 닫힘 (조리 불가)':<32}"+"".join(f"{eok(rev_all(i,False)):>15.2f}억" for i in range(3)))
print(f"{'  영업이익':<32}"+"".join(f"{eok(op(i,False)):>+15.2f}억" for i in range(3)))
print(f"{'매출 감소분':<32}"+"".join(
    f"{eok(rev_all(i,False)-rev_all(i,True)):>+15.2f}억" for i in range(3)))
print("-"*W)
print("  ※ 다이닝(RL-02·03 코어의 47%)에 비하면 조리 게이트의 타격이 작다.")
print("     E-0435가 말하듯 사찰음식 교육은 이미 조계종 3기관 체계가 하고 있어,")
print("     게이트가 닫히면 '우리가 안 하고 향적세계와 연계한다'는 대안이 열려 있다.")
print()

print("="*W)
print("손익 (조리 게이트 열림 기준)")
print("="*W)
print(f"{'':<32}{'보수':>16}{'기준':>16}{'낙관':>16}")
print("-"*W)
print(f"{'매출':<32}"+"".join(f"{eok(rev_all(i)):>15.2f}억" for i in range(3)))
for lab, f in [("  트랙 A 즉석 체험", rev_instant), ("  트랙 B 클래스", rev_class), ("  트랙 C 과정", rev_course)]:
    print(f"{lab:<32}"+"".join(f"{eok(f(i)):>15.2f}억" for i in range(3)))
print()
print(f"{'강사료 (회당 10/15만)':<32}"+"".join(f"{eok(cost_of(i)[0]):>15.2f}억" for i in range(3)))
print(f"{'재료비':<32}"+"".join(f"{eok(cost_of(i)[1]):>15.2f}억" for i in range(3)))
print(f"{'상주 인건비':<32}"+"".join(f"{eok(STAFF[i]*WAGE):>15.2f}억" for i in range(3)))
print(f"{'마케팅':<32}"+"".join(f"{eok(rev_all(i)*MKT[i]):>15.2f}억" for i in range(3)))
print(f"{'감가상각 (CAPEX/10년)':<32}"+"".join(f"{eok(CAPEX[i]/DEP_YEARS):>15.2f}억" for i in range(3)))
print(f"{'영업이익':<32}"+"".join(f"{eok(op(i)):>+15.2f}억" for i in range(3)))
print(f"{'영업이익률':<32}"+"".join(f"{op(i)/rev_all(i):>15.0%}" for i in range(3)))
print(f"{'CAPEX':<32}"+"".join(f"{eok(CAPEX[i]):>15.2f}억" for i in range(3)))
print(f"{'회수기간':<32}"+"".join(
    f"{CAPEX[i]/op(i):>14.1f}년" if op(i) > 0 else f"{'불가':>16}" for i in range(3)))
print("-"*W)
print("  ※ 마스터 배정 500㎡는 E-0532의 '외국인 체험 500㎡'다 — 트랙 A의 몫이다.")
print("     클래스·공방 강의실은 배분 목록에 별도 항목이 없고 '전시·체험 2,000㎡'에 뭉쳐 있다.")
print("     RL-01 권고안이 전시를 2,000→1,450㎡로 줄였으므로 550㎡가 풀린다 — 그 자리가 강의실이다.")
print()
print(f"{'면적 기준':<34}{'보수':>16}{'기준':>16}{'낙관':>16}")
print("-"*W)
for lab, a in [("마스터 배정 500㎡ (즉석체험만)", 500), ("실소요 1,050㎡ (+RL-01 반납 550㎡)", 1050)]:
    print(f"{lab:<34}" + "".join(f"{op(i)/a/10000:>14,.0f}만원" for i in range(3)))
print("-"*W)
print("  대조 — 다이닝 5축 206만 · 대관 32~39만 · 숙박 29만 · 전시 13만")
print("  → 500㎡ 기준이면 대관과 동급이지만, 실소요 1,050㎡로 보면 전시보다 조금 나은 수준이다.")
print("     면적 재배치가 선행되어야 위 손익이 성립하고, 그 면적을 반영하면 효율은 절반이 된다.")
