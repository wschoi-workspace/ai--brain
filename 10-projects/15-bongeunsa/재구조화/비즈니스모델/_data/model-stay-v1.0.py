# -*- coding: utf-8 -*-
"""RL-06 명상 + RL-09 숙박 통합 모델 v1.0
구조: 800평(2,645㎡) 한 개 층을 낮(명상)과 밤(숙박)이 시간대로 나눠 쓰는 24시간 이중가동
전제: 1개층 800평 배정 확정 (2026-08-17 발주 판단)
"""
def eok(v): return v/1e8
CASE = ["보수", "기준", "낙관"]
JPY = 9.39   # 100엔 = 939원 (2026.08 평균 전망 9.390원/엔)

BENCH = """
[법적 프레임 — 이 모델의 경계]
◆ E-0131(A) 일반 숙박시설 불가 — 호텔·게스트하우스는 영업행위 금지(Tier3).
  → Book and Bed의 '호스텔 업태'는 이식 불가. 이식하는 것은 업태가 아니라 공간 구조다.
◆ E-0145(A)/E-0426(A) 템플스테이는 국고지원을 받으며 유료 운영되는 제도가 이미 정착
◆ E-0152(A) 3일·7일 프리미엄 명상 리트리트는 시행령 제7조 '신도 편의시설' → Tier1
◆ E-0140(A) 명상·웰니스는 건축법상 용도변경조차 불요 · 단 '유료 정기 프로그램' 해석 여지
◆ E-0134(A) 요가·필라테스는 불가 — 명상과 같은 공간에 두되 라벨을 섞으면 안 됨
◆ E-0873(A) 템플스테이 등록요건 20인 이상 동시수용·예산 1억+·예비운영 1년
◆ E-0874(A) 운영표준 1박2일 월 2회+·연 500명+
◆ E-0876(A) 시설보조금 2억+ 수령 시 7년 반납의무 락인
  → 프리미엄 유료화를 하려면 시설비 국고보조를 받지 않는 편이 자유롭다
◆ E-1049(A) 봉은사 현행 타이치명상·선명상 수강료 0원 · 강남구청 2012년 종교시설 과세 추징 5억
  → 무료를 유료로 바꾸는 순간이 과세 판정 시점

[숙박 단가 벤치마크 — 실측]
◆ 봉은사 현행     9~12만원   외국인 영어 템플스테이 (E-0428 A)
◆ 템플스테이 정가 체험형 10만 / 휴식형 5~8만 / 당일형 3~5만 (E-0426 A)
◆ 서울 4성급 ADR  16.7만원   2024년 (2022년 12.8만 대비 +30.5%)
◆ 서울 5성급 ADR  26.8만원   2024년 (3년간 +1.1% 정체)
◆ 고야산 슈쿠보   ¥23,000~30,000+ = 21.6~28.2만원  117개 사찰 중 51개가 숙방 운영
◆ Zenbo Seinei    ¥48,000 = 45.1만원 (1인 1박·식사포함) · 반 시게루 설계 젠 웰니스
                  데이트립 ¥23,000 = 21.6만원 · 3박 ¥110,000 / 4박 ¥165,000
◆ 닌나지 쇼린안    ¥1,000,000 = 939만원 (1파티 5명 한정·폐장 후 독점) (E-0450 C)
◆ Book and Bed Tokyo 신주쿠 — 이식 대상은 가격이 아니라 구조
                  싱글 ¥5,000(4.7만) / 컴포트 ¥5,500 / 더블 ¥11,000 / 슈페리어 ¥15,000(14.1만)
                  ★ 데이유즈: 라운지 ¥700/1H + 1오더, 라운지+침대 ¥960/1H(9,000원)
                  ★ 4,000권 서가 사이에 침대를 끼워넣음 — '책방인데 잘 수 있는 곳'
                  ★ 침대 규격 205×85cm(컴팩트) / 205×129cm(스탠다드) — 캡슐급 원단위

[명상 단가 벤치마크]
◆ 선릉·정릉 점심 관람권 3,000원 · 10회권 3개월 · 11:30~13:30 (E-1016 A)
◆ 차 명상 시장가 3~7만원 · 봉은사 권고 5~10만원 (E-1042 B)
◆ K-Temple 외국인 체험 8~15만원 (E-0581 A)
◆ MNDFL(뉴욕) 드롭인 $15 · 월 무제한 $150 · 첫 클래스 $10
◆ Unplug(LA) 5클래스 $39/주 패키지
◆ 수면카페 40분+음료 8,900원 — 삼성동 유료 대안의 하한 (E-1019 C)

[수요 실측 — 낮 시간이 비어 있다]
◆ E-1021(A) 도보 10~15분권 종사자 112,349명 (삼성1동 63,427 + 삼성2동)
◆ E-1017(B) 점심 1시간 81.8% · 식사 후 잔여 자유시간 10~20분 → 30분 완결·무예약이 절대 제약
◆ E-1015(B) 사내 복지 희망 휴게공간 1위 = 수면공간 51.3% · 바라는 공간 1위 = 수면실 49.6%
            한국인 실수면 5시간 25분(표본 37만명)
◆ E-1019(C) 삼성동 점심 실내 무료 휴식 공간 0곳
◆ E-1020(B) 강남권 점심시간 문화 프로그램 0개 (서울시 집계 6종 전부 중구·종로)
◆ E-1018(B) 삼성동 평균 점심값 15,000원 — 전국 1위(전국 평균 9,500원)
◆ E-1058(A) 명상 과금 구조가 116개 서비스 목록에 0건 — 서비스 신규 정의가 선행

[숙박 수요 실측]
◆ E-0317(B) 서울 숙박형 템플스테이 2곳뿐 — 봉은사·화계사
◆ E-0374(C) 봉은사 템플스테이 연 3,000~5,000명 추정 · 1박2일 휴식형 10만원
◆ E-0510(B) 외국인 템플스테이 50~120명/일 참여
◆ E-1051(A) 2025 전국 외국인 템플스테이 55,515명(+13.7%, 전체 증가율 5.1%의 2.7배)
            외국인 대응 사찰 31/158곳(19.6%)
◆ E-1000(A) 봉은사 방문 유럽인 비중 31.9% · 개별여행 97.5% · 서울 체류 9.05일(전체 5.96일)
◆ E-1011(B) 서울 8일 이상 체류자의 봉은사 전환율 14.1%
◆ E-1009(A) 봉은사 방문 외국인의 종교·순례 목적 2.0% · '역사/전통 체험' 고려 46.6%
            2025 외국인 템플스테이 참가자 중 불교신자 9.9%
◆ E-1005(A) 봉은사 방문자 총지출 1.27배(357.1만 vs 280.4만) · 쇼핑비만 0.92배
            단기 체험상품 지출자 10.9%(전체 5.6%) · 문화오락 지출자 48.8%(전체 28.9%)
◆ E-1052(B) 외국인 연 방문 10~61만 · 유료 프로그램 참여 1만 · 전환율 2~10%
◆ E-1033(A) 9~2월 언급 점유율 19.4%인데 템플스테이 언급은 28.9% — 비수기에 오히려 강함
"""

# ═══════════════════════════════════════════════════════════════
# ① 면적 — 800평 = 2,645㎡ 배분
# ═══════════════════════════════════════════════════════════════
GFA = 2_645          # 1개층 800평 (발주 지정)
A_ROOM   = 1_600     # 객실존
A_SEON   = 450       # 선방·명상홀   ← 낮/밤 이중가동
A_LOUNGE = 350       # 다경실·서고라운지 ← 낮/밤 이중가동
A_SERVE  = 245       # 공양·차 서비스존 (조리 게이트 COOK)
assert A_ROOM + A_SEON + A_LOUNGE + A_SERVE == GFA

EFF = [0.68, 0.72, 0.75]   # 객실존 전용률 — double-loaded 표준 70~75%, 느슨/표준/타이트 설계
def A_ROOM_NET(i): return A_ROOM * EFF[i]

# 객실 구성 — 3등급
#   ① 선재(禪齋) 스위트  45㎡ 좌식·개별욕실·전용 다실
#   ② 온돌 스탠다드      26㎡ 좌식·개별욕실
#   ③ 장경각 베드        7㎡  서가 결합형 · 공용욕실  ← Book and Bed 구조 이식
SUITE_SQM, STD_SQM, POD_SQM = 45, 26, 7
SUITE_N = [4, 5, 6]
STD_N   = [20, 24, 26]
POD_N   = [24, 32, 36]

def room_area(i):
    return SUITE_N[i]*SUITE_SQM + STD_N[i]*STD_SQM + POD_N[i]*POD_SQM
for _i in range(3):            # 설계 정합 — 객실 순면적이 전용면적을 넘지 않는가
    assert room_area(_i) <= A_ROOM_NET(_i), \
        f"{CASE[_i]}: 객실 {room_area(_i)}㎡ > 전용가능 {A_ROOM_NET(_i):.0f}㎡"
def keys(i):                      # 판매 단위 수
    return SUITE_N[i] + STD_N[i] + POD_N[i]
def capacity(i):                  # 최대 동시 수용 인원 (E-0873 요건 20인 이상 확인용)
    return SUITE_N[i]*2 + STD_N[i]*2 + POD_N[i]*1

# ═══════════════════════════════════════════════════════════════
# ② RL-09 숙박 — 밤(21:00~10:00)
# ═══════════════════════════════════════════════════════════════
# 단가: 현행 9~12만원을 하한, 서울 5성급 26.8만·고야산 프리미엄 28.2만을 상한으로
SUITE_RATE = [280_000, 350_000, 420_000]   # Zenbo 45.1만의 62~93%
STD_RATE   = [140_000, 180_000, 220_000]   # 4성급 ADR 16.7만 ±
POD_RATE   = [55_000,  70_000,  85_000]    # Book&Bed 싱글 4.7만 · 당일형 3~5만 위

# 가동률 — 서울 숙박형 템플스테이가 2곳뿐인 공급 희소성 vs 종교시설 주말편중
OCC_SUITE = [0.30, 0.42, 0.55]
OCC_STD   = [0.38, 0.52, 0.65]
OCC_POD   = [0.35, 0.50, 0.62]

def rev_suite(i): return SUITE_N[i]*SUITE_RATE[i]*365*OCC_SUITE[i]
def rev_std(i):   return STD_N[i]*STD_RATE[i]*365*OCC_STD[i]
def rev_pod(i):   return POD_N[i]*POD_RATE[i]*365*OCC_POD[i]
def rev_rooms(i): return rev_suite(i)+rev_std(i)+rev_pod(i)

# 체류 부가 — 투숙객 1인당 추가 지출 (공양·차·굿즈는 각 라인에 귀속, 여기선 숙박부대만)
GUEST_NIGHTS = lambda i: (SUITE_N[i]*2*365*OCC_SUITE[i]
                          + STD_N[i]*2*365*OCC_STD[i]
                          + POD_N[i]*1*365*OCC_POD[i])
ANCILLARY = [12_000, 18_000, 25_000]        # 다과·대여·프로그램 업셀 (E-1005 체험지출 1.27배)
def rev_anc(i): return GUEST_NIGHTS(i)*ANCILLARY[i]

# 독점 프라이빗 스테이 — 닌나지 쇼린안 모델 (E-0450 C · 폐장 후 경내 독점)
PRIV_NIGHTS = [6, 12, 24]                   # 연 개최 횟수
PRIV_RATE   = [3_000_000, 5_000_000, 8_000_000]
def rev_priv(i): return PRIV_NIGHTS[i]*PRIV_RATE[i]

def rev_stay(i): return rev_rooms(i)+rev_anc(i)+rev_priv(i)

# ═══════════════════════════════════════════════════════════════
# ③ RL-06 명상 — 낮(11:00~19:00) · 같은 면적 재판매
# ═══════════════════════════════════════════════════════════════
WALK_POOL = 112_349          # E-1021(A) 도보 10~15분권 종사자

# ③-1 점심 선(禪) — 30분 완결·무예약 (E-1017 절대제약)
#     선릉 3,000원 10회권(E-1016)을 앵커로, 삼성동 점심값 15,000원(E-1018)의 1/3~2/3
LUNCH_PEN  = [0.010, 0.025, 0.045]    # 도보권 침투율
LUNCH_FREQ = [10, 18, 26]             # 연 이용 횟수
LUNCH_FEE  = [5_000, 7_000, 9_000]
def lunch_users(i): return WALK_POOL*LUNCH_PEN[i]
def rev_lunch(i):   return lunch_users(i)*LUNCH_FREQ[i]*LUNCH_FEE[i]

# ③-2 선잠(禪眠) 데이유즈 — Book and Bed ¥960/1H 구조 이식
#     수면공간 수요 1위 51.3%(E-1015) · 삼성동 무료 휴식공간 0곳(E-1019)
#     낮에 비는 장경각 베드를 시간 단위로 판다 = 같은 면적을 하루 두 번 판매
NAP_BEDS   = lambda i: POD_N[i]                 # 낮에 노는 베드 전량
NAP_DAYS   = [240, 250, 260]                    # 주중 영업일
NAP_TURN   = [0.8, 1.4, 2.0]                    # 베드당 일 회전 (40~50분 슬롯)
NAP_FEE    = [9_000, 12_000, 15_000]            # 수면카페 8,900원(40분) 위
def rev_nap(i): return NAP_BEDS(i)*NAP_DAYS[i]*NAP_TURN[i]*NAP_FEE[i]

# ③-3 드롭인 명상 클래스 — 저녁 60분 (MNDFL 드롭인 $15 ≈ 2.1만원)
DROP_SESS  = [300, 500, 700]         # 연 회차
DROP_SEATS = [12, 18, 24]            # 회당 참가
DROP_FEE   = [20_000, 25_000, 30_000]
def rev_drop(i): return DROP_SESS[i]*DROP_SEATS[i]*DROP_FEE[i]

# ③-4 1일 선 리트리트 — 주말 (Zenbo 데이트립 ¥23,000 = 21.6만원의 1/3~1/2)
RET_DAYS  = [40, 60, 80]
RET_SEATS = [12, 18, 25]
RET_FEE   = [70_000, 90_000, 120_000]   # 차명상 시장가 3~7만 / 권고 5~10만(E-1042) 상단
def rev_retreat(i): return RET_DAYS[i]*RET_SEATS[i]*RET_FEE[i]

# ③-5 스님과의 대화(몽크챗) — 외국인 · Tier1 (E-0639)
#     통역 만족도 4.22점 열위(E-1008) · 영어 프로그램 사찰 20%뿐(E-0316)
MONK_SESS  = [150, 250, 350]
MONK_SEATS = [8, 12, 16]
MONK_FEE   = [25_000, 35_000, 45_000]
def rev_monk(i): return MONK_SESS[i]*MONK_SEATS[i]*MONK_FEE[i]

def rev_medi(i):
    return rev_lunch(i)+rev_nap(i)+rev_drop(i)+rev_retreat(i)+rev_monk(i)

# ═══════════════════════════════════════════════════════════════
# ④ 비용 — CAPEX / OPEX
# ═══════════════════════════════════════════════════════════════
# CAPEX ㎡당 (리모델 기준 · 건물 전체 45~70억/8,868㎡ = 51~79만원/㎡가 평균값)
#   객실은 배관·욕실·차음이 들어가 평균의 2.5~3배
C_SUITE, C_STD, C_POD = 2_800_000, 2_200_000, 1_400_000   # 원/㎡
C_SEON, C_LOUNGE, C_SERVE = 1_300_000, 1_500_000, 2_000_000
FF_E = [0.12, 0.15, 0.18]      # 집기·비품 비율

def capex(i):
    hard = (SUITE_N[i]*SUITE_SQM*C_SUITE + STD_N[i]*STD_SQM*C_STD + POD_N[i]*POD_SQM*C_POD)
    hard += (A_ROOM - room_area(i))*1_200_000        # 복도·코어
    hard += A_SEON*C_SEON + A_LOUNGE*C_LOUNGE + A_SERVE*C_SERVE
    return hard*(1+FF_E[i])

# OPEX
STAFF_N   = [11, 15, 19]          # 프론트·객실·프로그램·지도법사
STAFF_COST= 46_000_000            # 인당 연 인건비(4대보험 포함)
# E-0880(A) 템플스테이 운영인력 이탈 급소 — 사찰당 평균 2.27명이 표준. 이 모델은 그 5~8배
UTIL_SQM  = 95_000                # 원/㎡·년 (24시간 가동 · 온돌·급탕 반영)
AMENITY   = [9_000, 12_000, 15_000]     # 객실 소모품 원/박
MEDI_COGS = [0.14, 0.16, 0.18]          # 명상 라인 변동비율(강사료·다과)
MKT       = [0.06, 0.07, 0.08]          # 매출 대비 마케팅·OTA 수수료
REPAIR    = [0.03, 0.035, 0.04]

def opex(i):
    labor = STAFF_N[i]*STAFF_COST
    util  = GFA*UTIL_SQM
    amen  = GUEST_NIGHTS(i)*AMENITY[i]
    cogs  = rev_medi(i)*MEDI_COGS[i]
    rev   = rev_stay(i)+rev_medi(i)
    return labor+util+amen+cogs+rev*(MKT[i]+REPAIR[i])

DEPR_YEARS = 12
def depr(i): return capex(i)/DEPR_YEARS

def revenue(i): return rev_stay(i)+rev_medi(i)
def gop(i):     return revenue(i)-opex(i)
def ebit(i):    return gop(i)-depr(i)
def payback(i):
    g = gop(i)
    return capex(i)/g if g > 0 else None

# ═══════════════════════════════════════════════════════════════
# ⑤ 면적 경합 — 대관(RL-08)과의 트레이드오프
# ═══════════════════════════════════════════════════════════════
# 800평을 숙박에 주면 총 소요가 8,868㎡를 초과한다. 무엇을 접어야 하는가.
TOTAL_GFA = 8_868                                  # E-0501(A) 대상 면적
NEED = {"전시": 1_450, "F&B 5축": 691, "리테일": 800,
        "교육": 500, "명상(전용)": 0, "대관": 1_500}   # 명상은 숙박층에 흡수 → 전용면적 0
LOBBY_RATE = 0.29                                  # E-0532(A) 로비·동선·부대 비중
RL08_REV = 300_000_000                             # 대관 기준안 3.0억 (02-대관BM 실측 정합)
RL08_SQM_REV = 183_900                             # 원/㎡·년 (1,150원×365×41.7%×1.0499)

def area_check(i, keep_daegwan=True):
    need = sum(NEED.values()) - (0 if keep_daegwan else NEED["대관"])
    core = need + GFA
    lobby = core*LOBBY_RATE/(1-LOBBY_RATE)
    return core+lobby, core, lobby

# ═══════════════════════════════════════════════════════════════
# ⑥ 단계 개관 — CAPEX 48~56억을 한 번에 쓸 수 없다면
# ═══════════════════════════════════════════════════════════════
# Phase 1 = 낮(명상) + 장경각 베드만. 스위트·스탠다드(욕실·배관)를 뒤로 미룬다.
#   RL-03B가 "편집샵·아카데미는 다이닝보다 나중에"라고 판단한 것과 같은 논리
def capex_p1(i):
    hard = POD_N[i]*POD_SQM*C_POD
    hard += A_SEON*C_SEON + A_LOUNGE*C_LOUNGE + A_SERVE*0.5*C_SERVE
    hard += 300*1_200_000                              # 최소 복도·코어
    return hard*(1+FF_E[i])
def rev_p1(i):
    guest_n = POD_N[i]*1*365*OCC_POD[i]
    return rev_medi(i) + rev_pod(i) + guest_n*ANCILLARY[i]
def opex_p1(i):
    labor = max(5, STAFF_N[i]-6)*STAFF_COST
    util  = (A_SEON+A_LOUNGE+POD_N[i]*POD_SQM+A_SERVE*0.5)*UTIL_SQM
    amen  = POD_N[i]*365*OCC_POD[i]*AMENITY[i]
    cogs  = rev_medi(i)*MEDI_COGS[i]
    return labor+util+amen+cogs+rev_p1(i)*(MKT[i]+REPAIR[i])
def gop_p1(i): return rev_p1(i)-opex_p1(i)

if __name__ == "__main__":
    print("="*104)
    print("RL-06 명상 + RL-09 숙박 통합 모델 v1.0 — 800평 1개층 · 24시간 이중가동")
    print("="*104)
    print(f"{'':30}{'보수':>14}{'기준':>16}{'낙관':>16}")
    print("-"*104)
    print(f"{'[면적] 배정':30}{GFA:>13,}㎡{GFA:>15,}㎡{GFA:>15,}㎡")
    for i in range(3):
        pass
    print(f"{'  객실 순면적':30}" + "".join(f"{room_area(i):>13,}㎡" for i in range(3)))
    print(f"{'  판매 단위(키)':30}" + "".join(f"{keys(i):>14,}실" for i in range(3)))
    print(f"{'  최대 동시수용':30}" + "".join(f"{capacity(i):>14,}인" for i in range(3)))
    print("-"*104)
    rows = [
        ("숙박 · 선재 스위트", rev_suite), ("숙박 · 온돌 스탠다드", rev_std),
        ("숙박 · 장경각 베드", rev_pod), ("숙박 · 체류부가", rev_anc),
        ("숙박 · 독점 프라이빗", rev_priv),
        ("★ RL-09 숙박 소계", rev_stay),
        ("명상 · 점심 선(禪)", rev_lunch), ("명상 · 선잠 데이유즈", rev_nap),
        ("명상 · 드롭인 클래스", rev_drop), ("명상 · 1일 리트리트", rev_retreat),
        ("명상 · 스님과의 대화", rev_monk),
        ("★ RL-06 명상 소계", rev_medi),
        ("매출 합계", revenue),
    ]
    for name, fn in rows:
        print(f"{name:30}" + "".join(f"{eok(fn(i)):>14.1f}억" for i in range(3)))
    print("-"*104)
    for name, fn in [("OPEX", opex), ("GOP(상각전)", gop), ("감가상각", depr), ("영업이익", ebit), ("CAPEX", capex)]:
        print(f"{name:30}" + "".join(f"{eok(fn(i)):>14.1f}억" for i in range(3)))
    print("-"*104)
    print(f"{'영업이익률':30}" + "".join(f"{ebit(i)/revenue(i)*100:>14.1f}%" for i in range(3)))
    print(f"{'㎡당 영업이익':30}" + "".join(f"{ebit(i)/GFA/1e4:>13.0f}만원" for i in range(3)))
    print(f"{'회수기간(GOP 기준)':30}" + "".join(f"{payback(i):>13.1f}년" for i in range(3)))
    print(f"{'RevPAR(객실당 일)':30}" + "".join(f"{rev_rooms(i)/keys(i)/365:>12,.0f}원" for i in range(3)))
    print()
    print("="*104)
    print("면적 경합 — 800평 숙박을 넣으면 무엇이 밀려나는가")
    print("="*104)
    for keep in (True, False):
        tot, core, lobby = area_check(1, keep)
        label = "대관 유지" if keep else "대관 포기"
        over = tot - TOTAL_GFA
        print(f"{label:12} 코어 {core:>6,}㎡ + 로비·부대 {lobby:>6,}㎡ = {tot:>6,}㎡ "
              f"/ 가용 {TOTAL_GFA:,}㎡ → {'초과 +' if over>0 else '여유 '}{abs(over):,.0f}㎡")
    print()
    print(f"대관 1,500㎡가 버는 돈           {eok(RL08_REV):>6.1f}억  (㎡당 {RL08_SQM_REV:,}원)")
    print(f"같은 1,500㎡를 숙박·명상으로 쓰면 {eok(revenue(1)/GFA*1500):>6.1f}억  (㎡당 {revenue(1)/GFA:,.0f}원)")
    print(f"→ 배수 {(revenue(1)/GFA)/RL08_SQM_REV:.1f}배")
    print()
    print("="*104)
    print("이중가동 검산 — 같은 면적을 두 번 파는 것이 실제로 얼마인가")
    print("="*104)
    for i in range(3):
        share = A_SEON + A_LOUNGE + POD_N[i]*POD_SQM     # 낮/밤 공유 면적
        print(f"{CASE[i]:4} 공유면적 {share:>5,}㎡ · 낮 매출 {eok(rev_medi(i)):>5.1f}억 "
              f"· 밤 매출 {eok(rev_stay(i)):>5.1f}억 · 공유면적 ㎡당 낮매출 {rev_medi(i)/share/1e4:>5.0f}만원")
    print()
    print("="*104)
    print("단계 개관 — Phase 1(명상+장경각 베드)만 먼저 열면")
    print("="*104)
    print(f"{'':22}{'보수':>13}{'기준':>15}{'낙관':>15}")
    for name, fn in [("P1 CAPEX", capex_p1), ("P1 매출", rev_p1),
                     ("P1 OPEX", opex_p1), ("P1 GOP", gop_p1)]:
        print(f"{name:22}" + "".join(f"{eok(fn(i)):>13.1f}억" for i in range(3)))
    print(f"{'P1 회수(GOP)':22}" + "".join(
        f"{capex_p1(i)/gop_p1(i):>12.1f}년" if gop_p1(i) > 0 else f"{'불가':>13}" for i in range(3)))
    print(f"{'전체 대비 CAPEX':22}" + "".join(f"{capex_p1(i)/capex(i)*100:>13.0f}%" for i in range(3)))
    print(f"{'전체 대비 매출':22}" + "".join(f"{rev_p1(i)/revenue(i)*100:>13.0f}%" for i in range(3)))
    print()
    print("="*104)
    print("제도 요건 검증 (E-0873 · E-0874)")
    print("="*104)
    for i in range(3):
        ok20 = "✅" if capacity(i) >= 20 else "❌"
        ann = GUEST_NIGHTS(i)
        print(f"{CASE[i]:4} 동시수용 {capacity(i):>3}인 {ok20} (요건 20인+) · "
              f"연 숙박 연인원 {ann:>7,.0f}명 ✅ (요건 500명+)")
