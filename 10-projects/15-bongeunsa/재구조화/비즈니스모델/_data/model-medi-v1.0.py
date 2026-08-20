# -*- coding: utf-8 -*-
"""RL-06 명상 프로그램(B2C) 단독 모델 v1.0
질문: 숙박(RL-09)에 흡수되지 않고 명상 라인이 혼자 설 수 있는가.
방법: 면적 원가를 명상이 직접 지는 구조로 바꿔 3개 구조 × 3개 시나리오를 돌린다.
     구조 A 전용 풀세트 / 구조 B 경량(선잠 제외) / 구조 C 기생형(시간대만 임차)
비교군: model-stay-v1.0.py — 같은 상품 구성을 숙박층에 흡수시킨 모델(명상 전용면적 0㎡)
"""
def eok(v): return v/1e8
CASE = ["보수", "기준", "낙관"]
STRUCT = ["A 전용", "B 경량", "C 기생"]

BENCH = """
[법적 프레임]
◆ E-0140(A) 명상·웰니스는 건축법상 용도변경 불요 · 단 '유료 정기 프로그램이 신도 편의시설인가'는 해석 여지
◆ E-0134(A) 요가·필라테스는 Tier3 불가 — 웰니스 확장 경로가 법으로 막혀 있다
◆ E-1049(A) 봉은사 현행 타이치명상·선명상 수강료 0원 · 강남구청 2012년 '교인 외 이용 가능' 기준 5억 추징
             → 무료를 유료로 바꾸는 순간이 과세 판정 시점

[수요 실측]
◆ E-1021(A) 도보 10~15분권 종사자 112,349명 (삼성1·2동). '타겟 75~80만'은 과대 표현
◆ E-1017(B) 점심 1시간 · 자유시간 10~20분 · 성공 프로그램은 예외 없이 30~50분
◆ E-1018(B) 삼성동 점심값 15,000원(전국 1.58배·12권역 1위)
             → 유료 서비스는 ①점심값을 대체하거나 ②3,000~5,000원 이하 회차권
◆ E-1016(A) 선릉·정릉 점심 관람권 3,000원 / 3개월 10회 = 회당 300원 (국가기관 검증)
◆ E-1015(B) 사내 복지 희망 1위 수면공간 51.3% · 눕는 데 눈치 25.6%
             → 사찰은 같은 행위를 '명상'으로 정당화해 주는 유일한 공급자
◆ E-1019(C) 봉은사·선정릉 둘 다 옥외 · 실내 대안은 유료·소수·만석 (수면카페 8,900원/40분+음료)
◆ E-1020(B) 서울시 집계 점심 문화 프로그램 6종 전부 중구·종로 · 강남권 0개
◆ E-1014(B) 점심에 원하는 것은 식사가 아니라 관계로부터의 이탈 (혼밥 26.9%·감정노동 피로 65.1%)
◆ E-1058(A) 점심 회차권 과금구조가 116개 서비스 목록에 0건 — 서비스 정의부터가 신규

[단가 앵커]
◆ E-1042(B) 차 명상 기업 프로그램 3~7만원 · 봉은사 정통성 감안 5~10만 무리 없음
◆ E-0639(B) 몽크챗 — 통역으로 소실되는 깊이를 사람으로 복구하는 저비용 콘텐츠
◆ E-0631(A) 드롭인 30~60분 · 무예약 = 가장 낮은 진입장벽
◆ E-0632(B) 점심 30분 명상 — 통근 반경 안에서만 성립
◆ E-0633(C) 1일 선 리트리트 — 숙박 없이 리트리트 완결감을 만드는 중간 단가
"""

# ═══════════════════════════════════════════════════════════════
# ① 면적 — 명상이 직접 지는 전용면적
# ═══════════════════════════════════════════════════════════════
A_SEON   = 450    # 선방·명상홀 (드롭인·리트리트·점심 선 공용)
A_LOUNGE = 350    # 다경실·서고 라운지
A_NAP    = 300    # 선잠존 — 베드 32 × 7㎡ + 공용 샤워·탈의
A_BACK   = 150    # 리셉션·로커·사무·창고
NAP_BEDS_N = [24, 32, 36]

def area(struct):
    if struct == 0: return A_SEON + A_LOUNGE + A_NAP + A_BACK   # 1,250㎡ = 378평
    if struct == 1: return A_SEON + A_LOUNGE + A_BACK           #   950㎡ = 287평
    return 0                                                     # 기생형 — 전용면적 없음

# ═══════════════════════════════════════════════════════════════
# ② 상품 5종 — 매출
# ═══════════════════════════════════════════════════════════════
WALK_POOL = 112_349          # E-1021(A)

# ②-1 점심 선(禪) — 30분 완결·무예약·무인 운영
#     단가는 E-1018 상한 5,000원을 넘지 않는다 (stay 모델의 5/7/9천은 근거 초과였음)
LUNCH_PEN  = [0.010, 0.025, 0.045]    # 브리프 R-07 침투 1~4.5% 범위
LUNCH_FREQ = [10, 18, 25]             # 브리프 R-07 연 10~25회
LUNCH_FEE  = [3_000, 4_000, 5_000]    # E-1018 회차권 상한
def lunch_users(i): return WALK_POOL*LUNCH_PEN[i]
def rev_lunch(i):   return lunch_users(i)*LUNCH_FREQ[i]*LUNCH_FEE[i]

# ②-2 선잠(禪眠) 데이유즈 — E-1015 명분 + E-1019 실내 공백
#     단가는 E-1018의 ①'점심값 대체' 경로로 정당화 (회차권 경로로는 상한 초과)
NAP_DAYS   = [240, 250, 260]
NAP_TURN   = [0.8, 1.4, 2.0]          # 베드당 일 회전 (40~50분 슬롯)
NAP_FEE    = [9_000, 12_000, 15_000]  # 수면카페 8,900원 앵커
def rev_nap(i, struct):
    if struct == 1: return 0          # 경량구조는 선잠 미시행
    return NAP_BEDS_N[i]*NAP_DAYS[i]*NAP_TURN[i]*NAP_FEE[i]

# ②-3 드롭인 명상 클래스 — 저녁 60분 (E-0631)
DROP_SESS  = [300, 500, 700]
DROP_SEATS = [12, 18, 24]
DROP_FEE   = [20_000, 25_000, 30_000]
def rev_drop(i): return DROP_SESS[i]*DROP_SEATS[i]*DROP_FEE[i]

# ②-4 1일 선 리트리트 — 주말 (E-0633 · E-1042 5~10만)
RET_DAYS  = [40, 60, 80]
RET_SEATS = [12, 18, 25]
RET_FEE   = [70_000, 90_000, 120_000]
def rev_retreat(i): return RET_DAYS[i]*RET_SEATS[i]*RET_FEE[i]

# ②-5 스님과의 대화 — 외국인 (E-0639)
MONK_SESS  = [150, 250, 350]
MONK_SEATS = [8, 12, 16]
MONK_FEE   = [25_000, 35_000, 45_000]
def rev_monk(i): return MONK_SESS[i]*MONK_SEATS[i]*MONK_FEE[i]

def revenue(i, struct):
    return (rev_lunch(i) + rev_nap(i, struct) + rev_drop(i)
            + rev_retreat(i) + rev_monk(i))

# ═══════════════════════════════════════════════════════════════
# ③ 시간대 점유 — 전용면적을 잡으면 나머지 시간은 무엇을 파는가
# ═══════════════════════════════════════════════════════════════
# 주당 선방·라운지 점유시간 (연간 회차 ÷ 50주)
def hours_week(i):
    lunch = 10                                   # 평일 11:30~13:30 = 2h × 5일
    drop  = DROP_SESS[i]/50 * 1.0                # 60분 클래스
    ret   = RET_DAYS[i]/50 * 6.0                 # 종일 리트리트
    monk  = MONK_SESS[i]/50 * 0.75               # 45분
    return lunch + drop + ret + monk
OPEN_HOURS_WEEK = 72        # 주 6일 × 12시간 영업 가정

# ═══════════════════════════════════════════════════════════════
# ④ CAPEX
# ═══════════════════════════════════════════════════════════════
C_SEON, C_LOUNGE, C_NAP, C_BACK = 1_300_000, 1_500_000, 1_400_000, 1_100_000   # 원/㎡
FF_E = [0.12, 0.15, 0.18]

def capex(i, struct):
    if struct == 2: return 0                     # 기생형 — 면적 투자를 타 라인이 진다
    hard = A_SEON*C_SEON + A_LOUNGE*C_LOUNGE + A_BACK*C_BACK
    if struct == 0: hard += A_NAP*C_NAP
    return hard*(1+FF_E[i])

DEPR_YEARS = 12
def depr(i, struct): return capex(i, struct)/DEPR_YEARS

# ═══════════════════════════════════════════════════════════════
# ⑤ OPEX — 무인 상품과 유인 상품을 갈라서 잡는다
# ═══════════════════════════════════════════════════════════════
STAFF_COST = 46_000_000
STAFF_N = {0: [4, 5, 6], 1: [3, 4, 5], 2: [1, 2, 2]}   # 구조별 상주 인력
UTIL_SQM = 65_000        # 원/㎡·년 (숙박과 달리 24시간 아님)

# 회차형 변동비 — 지도법사·강사 인건은 고정급이 아니라 회당으로 잡는다
FEE_DROP_TEACHER = 100_000      # 드롭인 회당
FEE_RET_TEACHER  = 400_000      # 리트리트 일당(종일)
FEE_MONK         = 80_000       # 몽크챗 회당 보시금
LINEN_PER_TURN   = 1_500        # 선잠 회전당 린넨
TEA_PER_SEAT     = 2_000        # 리트리트·몽크챗 다과 1인
MKT    = [0.06, 0.07, 0.08]
REPAIR = [0.03, 0.035, 0.04]

def var_cost(i, struct):
    v  = DROP_SESS[i]*FEE_DROP_TEACHER
    v += RET_DAYS[i]*FEE_RET_TEACHER + RET_DAYS[i]*RET_SEATS[i]*TEA_PER_SEAT
    v += MONK_SESS[i]*FEE_MONK + MONK_SESS[i]*MONK_SEATS[i]*TEA_PER_SEAT
    if struct != 1:
        v += NAP_BEDS_N[i]*NAP_DAYS[i]*NAP_TURN[i]*LINEN_PER_TURN
    return v

RENT_SQM = 183_900       # 기생형이 타 라인에 물어야 할 시간대 임차 원가 (RL-08 대관 ㎡당 연매출)
def opex(i, struct):
    labor = STAFF_N[struct][i]*STAFF_COST
    util  = area(struct)*UTIL_SQM
    rev   = revenue(i, struct)
    o = labor + util + var_cost(i, struct) + rev*(MKT[i]+REPAIR[i])
    if struct == 2:
        # 기생형은 면적을 공짜로 쓰는 게 아니다 — 점유시간 비율만큼 기회비용을 문다
        o += (A_SEON+A_LOUNGE)*RENT_SQM*min(1.0, hours_week(i)/OPEN_HOURS_WEEK)
    return o

def gop(i, struct):  return revenue(i, struct)-opex(i, struct)
def ebit(i, struct): return gop(i, struct)-depr(i, struct)

# ═══════════════════════════════════════════════════════════════
# ⑥ 손익분기 침투율 — 점심 선이 고정비를 얼마나 덮어야 하는가
# ═══════════════════════════════════════════════════════════════
def fixed_cost(i, struct):
    f = STAFF_N[struct][i]*STAFF_COST + area(struct)*UTIL_SQM + depr(i, struct)
    if struct == 2:
        f += (A_SEON+A_LOUNGE)*RENT_SQM*min(1.0, hours_week(i)/OPEN_HOURS_WEEK)
    return f

def bep_pen(i, struct):
    """다른 4개 상품의 공헌이익을 뺀 잔여 고정비를 점심 선만으로 덮으려면 침투율 몇 %"""
    cm_other = (rev_nap(i, struct) + rev_drop(i) + rev_retreat(i) + rev_monk(i)) \
               - var_cost(i, struct) \
               - (rev_nap(i, struct)+rev_drop(i)+rev_retreat(i)+rev_monk(i))*(MKT[i]+REPAIR[i])
    resid = fixed_cost(i, struct) - cm_other
    unit_cm = LUNCH_FEE[i]*LUNCH_FREQ[i]*(1-MKT[i]-REPAIR[i])   # 1인 연 공헌이익
    if unit_cm <= 0: return None
    return resid/unit_cm/WALK_POOL

if __name__ == "__main__":
    print("="*100)
    print("RL-06 명상 프로그램(B2C) 단독 모델 v1.0 — 숙박 없이 혼자 서는가")
    print("="*100)
    print()
    print("[매출 구성] 구조 A·C 공통 (구조 B는 선잠 0)")
    print(f"{'':24}{'보수':>13}{'기준':>14}{'낙관':>14}")
    print("-"*100)
    rows = [("점심 선(禪)", lambda i: rev_lunch(i)),
            ("선잠 데이유즈", lambda i: rev_nap(i, 0)),
            ("드롭인 클래스", lambda i: rev_drop(i)),
            ("1일 리트리트", lambda i: rev_retreat(i)),
            ("스님과의 대화", lambda i: rev_monk(i)),
            ("★ 매출 합계", lambda i: revenue(i, 0))]
    for name, fn in rows:
        print(f"{name:24}" + "".join(f"{eok(fn(i)):>13.2f}억" for i in range(3)))
    print()
    print(f"{'점심 선 이용자':24}" + "".join(f"{lunch_users(i):>12,.0f}명" for i in range(3)))
    print(f"{'  = 도보권 침투율':24}" + "".join(f"{LUNCH_PEN[i]*100:>13.1f}%" for i in range(3)))
    print(f"{'  회차권 단가':24}" + "".join(f"{LUNCH_FEE[i]:>11,}원" for i in range(3)))
    print()

    for s in range(3):
        print("="*100)
        print(f"구조 {STRUCT[s]} — 전용면적 {area(s):,}㎡ ({area(s)/3.3058:,.0f}평)")
        print("="*100)
        print(f"{'':24}{'보수':>13}{'기준':>14}{'낙관':>14}")
        print("-"*100)
        for name, fn in [("매출", revenue), ("OPEX", opex), ("GOP(상각전)", gop),
                         ("감가상각", depr), ("영업이익", ebit), ("CAPEX", capex)]:
            print(f"{name:24}" + "".join(f"{eok(fn(i, s)):>13.2f}억" for i in range(3)))
        print(f"{'영업이익률':24}" + "".join(f"{ebit(i,s)/revenue(i,s)*100:>13.1f}%" for i in range(3)))
        if s < 2:
            print(f"{'㎡당 매출':24}" + "".join(f"{revenue(i,s)/area(s):>11,.0f}원" for i in range(3)))
            print(f"{'회수기간(GOP)':24}" + "".join(
                f"{capex(i,s)/gop(i,s):>12.1f}년" if gop(i,s) > 0 else f"{'불가':>13}" for i in range(3)))
        print(f"{'BEP 침투율':24}" + "".join(
            f"{bep_pen(i,s)*100:>13.2f}%" if bep_pen(i,s) is not None else f"{'—':>14}" for i in range(3)))
        print()

    print("="*100)
    print("시간대 점유 — 전용면적을 잡으면 선방은 주 몇 시간 팔리는가")
    print("="*100)
    for i in range(3):
        h = hours_week(i)
        print(f"{CASE[i]:4} 주 {h:>5.1f}시간 점유 / 영업 {OPEN_HOURS_WEEK}시간 = {h/OPEN_HOURS_WEEK*100:>5.1f}% "
              f"· 168시간 기준 {h/168*100:>4.1f}%")
    print()
    print("  내역(기준안): 점심 선 10.0h · 드롭인 10.0h · 리트리트 7.2h · 몽크챗 3.8h")
    print()

    print("="*100)
    print("구조 비교 — 기준 시나리오")
    print("="*100)
    print(f"{'':16}{'매출':>12}{'영업이익':>12}{'이익률':>10}{'CAPEX':>12}{'전용면적':>11}")
    print("-"*100)
    for s in range(3):
        print(f"{STRUCT[s]:16}{eok(revenue(1,s)):>11.2f}억{eok(ebit(1,s)):>11.2f}억"
              f"{ebit(1,s)/revenue(1,s)*100:>9.1f}%{eok(capex(1,s)):>11.2f}억{area(s):>9,}㎡")
    print()
    print("="*100)
    print("대조 — model-stay-v1.0(숙박 흡수형)에서의 같은 라인")
    print("="*100)
    print("  숙박 흡수형 RL-06 기준 매출 9.2억 · 명상 전용면적 0㎡ · 명상 귀속 CAPEX 0억")
    print("  ※ 단가 차이: stay 모델은 점심 선 5/7/9천원 — E-1018 상한(5,000원) 초과분을 본 모델에서 정정")
    print(f"  본 모델 구조A 기준 매출 {eok(revenue(1,0)):.2f}억 · 전용면적 {area(0):,}㎡ · CAPEX {eok(capex(1,0)):.1f}억")
