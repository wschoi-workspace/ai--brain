# -*- coding: utf-8 -*-
"""봉은문화센터 다이닝 모델 v1.0 — RL-03 사찰음식 다이닝 + RL-02 전통다원
v0.2 대비 변경: ① 코스 믹스 도입 ② 원가 구조 신설(외부 리서치) ③ CAPEX·감가상각
                ④ 조리 게이트 닫힘 시 대안모델 ⑤ 세후 이익·회수기간
"""
CASE=["보수","기준","낙관"]
def eok(v): return v/1e8
def won(v): return f"{v:,.0f}"

# ══════════ 벤치마크 (외부 리서치 실측) ══════════
BM = {
 "발우공양": dict(
   코스=[36_000,50_000,70_000,120_000],  # 선/원/마음/희 — 2026 실측
   일평균객수=120, 외국인=0.35, 좌석형태="전실 룸(홀 없음)",
   예약타임=5,  # 11:30 13:30 18:00 18:30 19:00
   영업="월~토 11:30~20:20 · 브레이크 15:00~18:00",
   비고="조계종 직영 · 미쉐린 1스타 2016~ · 종로 조계사 건너편"),
 "파인다이닝 표준(KB사례)": dict(
   객단가=200_000, 테이블=12, 일수용=50, 예약률=0.70, 월매출=210_000_000,
   인건비=0.333, 식재료=0.429, 임대료=0.048, 발렛=0.014,
   유지비=0.033, 마케팅=0.024, 세금=0.024, 순이익=0.095,
   비고="테이블당 요리사 1.5명 · 미쉐린 획득 시 매출 +30%"),
 "외식업 평균(2024 통계)": dict(
   식재료=0.407, 인건비=0.332, 영업이익률=0.087,
   비고="2020년 영업이익률 12.1% → 2024년 8.7%로 3.4%p 하락"),
 "주방 CAPEX 단가": dict(
   일반식당=(250,350), 카페베이커리=(130,200), 파인다이닝추정=(350,500),
   단위="만원/평", 비고="환기·가스·배수·방수·전기가 전체의 40%"),
}

# ══════════ 면적 ══════════
FNB_TOTAL=1000            # E-0532 F&B 배정
DINING_AREA=600           # RL-03
TEAROOM_AREA=400          # RL-02
KITCHEN_RATIO=0.25        # 주방 = 식당면적의 1/4 (설계 표준)
SQM_PER_SEAT_ROOM=3.75    # 룸형 좌석당 면적
SQM_PER_SEAT_HALL=2.50    # 홀형

dining_hall = DINING_AREA*(1-KITCHEN_RATIO)   # 450㎡
seat_room  = dining_hall/SQM_PER_SEAT_ROOM     # 120석
seat_hall  = dining_hall/SQM_PER_SEAT_HALL     # 180석

# ══════════ RL-03 다이닝 — 코스 믹스 방식 ══════════
# 발우공양 구조 이식: 점심 저단가 / 저녁 고단가
LUNCH_SHARE=[0.60,0.50,0.45]
LUNCH_PRICE=[36_000,40_000,45_000]      # 발우공양 선식 36,000 기준
DINNER_PRICE=[50_000,65_000,80_000]     # 원 50,000 ~ 마음 70,000 기준
SEATS=[80,80,100]
TURN=[1.00,1.50,1.80]                    # 발우공양 일 120명이 기준점
DAYS=[280,300,310]                       # 월~토 주6일 = 연 313일

def blended(i):
    return LUNCH_SHARE[i]*LUNCH_PRICE[i] + (1-LUNCH_SHARE[i])*DINNER_PRICE[i]
def covers(i):
    return SEATS[i]*TURN[i]
def rev_dining(i):
    return covers(i)*blended(i)*DAYS[i]

# ══════════ RL-02 전통다원 ══════════
T_SEATS=[60,80,80]; T_PRICE=[15_000,20_000,25_000]
T_TURN=[1.0,1.5,1.8]; T_DAYS=[300,330,350]
def rev_tea(i): return T_SEATS[i]*T_PRICE[i]*T_TURN[i]*T_DAYS[i]

# ══════════ 원가 구조 ══════════
# 봉은사 고유 조건: 임차료 0(자가) · 발렛 불요(주차 보유) · 마케팅 저비용(자체 트래픽)
# 사찰음식: 육류·고급식재 없음 → 식재료비가 파인다이닝(42.9%)보다 낮음
COST = {
 "식재료비":      [0.38,0.35,0.32],   # 외식평균 40.7% / 파인다이닝 42.9% 대비 하향
 "임차료":        [0.00,0.00,0.00],   # ★ 자가 — 일반 파인다이닝 4.8~15% 대비 절대 우위
 "수도광열·소모품":[0.06,0.05,0.045],
 "마케팅":        [0.03,0.02,0.015],  # 자체 트래픽 · 사찰 브랜드
 "관리·보험·기타": [0.04,0.03,0.03],
}
# 인건비는 비율이 아니라 인원×임금으로 산정 (비율 가정은 저매출 구간에서 붕괴)
COVER_PER_STAFF=[5.0,6.0,7.0]   # KB 실측 1.4커버·인(객단가 20만) ~ 한정식 13커버·인 사이
WAGE=3.5e7
TEA_PER_STAFF=20
def staff(i):  return covers(i)/COVER_PER_STAFF[i] + T_SEATS[i]/TEA_PER_STAFF
def labor(i):  return staff(i)*WAGE
def cost_rate(i): return sum(v[i] for v in COST.values())

# ══════════ CAPEX ══════════
PYEONG=3.3058
CAPEX_UNIT=[500,420,350]   # 만원/평 (보수=고급사양, 낙관=효율사양)
DEPREC_YEARS=10
def capex(i):
    py=(DINING_AREA+TEAROOM_AREA)/PYEONG
    return py*CAPEX_UNIT[i]*1e4
def deprec(i): return capex(i)/DEPREC_YEARS

# ══════════ 세금 ══════════
# 법인세 9%(2억 이하) / 19%(2~200억) · 고유목적사업준비금 50% 손금산입(E-0172)
GOYU_RATE=0.50
def corp_tax(profit):
    if profit<=0: return 0
    base=profit*(1-GOYU_RATE)          # 준비금 50% 손금산입
    return base*0.09 if base<=2e8 else 2e8*0.09+(base-2e8)*0.19

# ══════════ 조리 게이트 닫힘 시 대안 ══════════
# 완제품 반입·콜드프렙 도시락형 — 프리미엄 불가, 외주라 원가율 상승
ALT_PRICE=[18_000,25_000,30_000]
ALT_COVERS=[60,90,120]
ALT_DAYS=[260,280,300]
ALT_COST=[0.62,0.58,0.55]   # 외주 완제품이라 식재료(매입)비율이 높음
ALT_LABOR=[0.22,0.20,0.18]  # 조리 인력 불필요 → 인건비 하락
ALT_OTHER=[0.10,0.09,0.08]

if __name__=="__main__":
    print("="*108)
    print("벤치마크 원장 — 외부 리서치 실측 (2026-08)")
    print("="*108)
    b=BM["발우공양"]
    print(f"◆ 발우공양 (조계종 직영·미쉐린 1스타) — 가장 가까운 직접 벤치마크")
    print(f"   코스 4종: 선 36,000(평일점심) / 원 50,000 / 마음 70,000 / 희 120,000(사전예약)")
    print(f"   일 평균 {b['일평균객수']}명 · 외국인 {b['외국인']:.0%} · {b['좌석형태']} · 예약타임 {b['예약타임']}개")
    print(f"   {b['영업']}")
    k=BM["파인다이닝 표준(KB사례)"]
    print(f"\n◆ 파인다이닝 손익 표준 (객단가 20만·테이블 12·일수용 50·예약률 70% → 월매출 2.1억)")
    print(f"   식재료 {k['식재료']:.1%} · 인건비 {k['인건비']:.1%} · 임대료 {k['임대료']:.1%} · 발렛 {k['발렛']:.1%}")
    print(f"   유지 {k['유지비']:.1%} · 마케팅 {k['마케팅']:.1%} · 세금 {k['세금']:.1%} → 순이익 {k['순이익']:.1%}")
    e=BM["외식업 평균(2024 통계)"]
    print(f"\n◆ 외식업 평균: 식재료 {e['식재료']:.1%} · 인건비 {e['인건비']:.1%} · 영업이익률 {e['영업이익률']:.1%}")
    print(f"   {e['비고']}")

    print()
    print("="*108)
    print("면적 → 좌석 산정")
    print("="*108)
    print(f"  F&B 배정 {FNB_TOTAL}㎡ = 다이닝 {DINING_AREA}㎡ + 다원 {TEAROOM_AREA}㎡  (E-0532)")
    print(f"  다이닝 {DINING_AREA}㎡ 중 주방 {DINING_AREA*KITCHEN_RATIO:.0f}㎡(1/4) · 홀 {dining_hall:.0f}㎡")
    print(f"  → 룸형 {SQM_PER_SEAT_ROOM}㎡/석 = {seat_room:.0f}석 / 홀형 {SQM_PER_SEAT_HALL}㎡/석 = {seat_hall:.0f}석")
    print(f"  ※ 모델은 80~100석 사용 — 발우공양식 룸 구성 전제 (물리적 상한 120석)")

    print()
    print("="*108)
    print("RL-03 사찰음식 다이닝 — 코스 믹스 · 조리 게이트 열림 전제")
    print("="*108)
    print(f"{'':<20}{'보수':>16}{'기준':>16}{'낙관':>16}")
    print("-"*108)
    rows=[("점심 비중",[f"{LUNCH_SHARE[i]:.0%}" for i in range(3)]),
          ("점심 단가",[won(LUNCH_PRICE[i]) for i in range(3)]),
          ("저녁 단가",[won(DINNER_PRICE[i]) for i in range(3)]),
          ("블렌디드 객단가",[won(blended(i)) for i in range(3)]),
          ("좌석",[f"{SEATS[i]}석" for i in range(3)]),
          ("회전",[f"{TURN[i]:.2f}" for i in range(3)]),
          ("일 커버수",[f"{covers(i):.0f}명" for i in range(3)]),
          ("영업일",[f"{DAYS[i]}일" for i in range(3)]),
          ]
    for lab,vals in rows:
        print(f"{lab:<20}"+"".join(f"{v:>16}" for v in vals))
    print("-"*108)
    print(f"{'매출(억)':<20}"+"".join(f"{eok(rev_dining(i)):>16.1f}" for i in range(3)))
    print(f"{'발우공양 대비':<20}"+"".join(f"{covers(i)/120:>15.2f}x" for i in range(3)))

    print()
    print("="*108)
    print("RL-02 전통다원")
    print("="*108)
    print(f"{'매출(억)':<20}"+"".join(f"{eok(rev_tea(i)):>16.1f}" for i in range(3)))

    print()
    print("="*108)
    print("F&B 통합 손익 (RL-02 + RL-03) — 조리 게이트 열림")
    print("="*108)
    print(f"{'항목':<22}{'보수':>16}{'기준':>16}{'낙관':>16}")
    print("-"*108)
    tot=[rev_dining(i)+rev_tea(i) for i in range(3)]
    print(f"{'매출액':<22}"+"".join(f"{eok(tot[i]):>15.1f}억" for i in range(3)))
    print(f"{'  식재료비':<22}"+"".join(f"{-eok(tot[i]*COST['식재료비'][i]):>15.1f}억" for i in range(3)))
    print(f"{'  인건비(인원×임금)':<22}"+"".join(f"{-eok(labor(i)):>15.1f}억" for i in range(3)))
    print(f"{'    필요 인원':<22}"+"".join(f"{staff(i):>15.0f}명" for i in range(3)))
    print(f"{'    매출 대비':<22}"+"".join(f"{labor(i)/tot[i]:>16.0%}" for i in range(3)))
    for name in ["임차료","수도광열·소모품","마케팅","관리·보험·기타"]:
        print(f"{'  '+name:<22}"+"".join(f"{-eok(tot[i]*COST[name][i]):>15.1f}억" for i in range(3)))
    print(f"{'  감가상각(주방·인테리어)':<22}"+"".join(f"{-eok(deprec(i)):>15.1f}억" for i in range(3)))
    print("-"*108)
    op=[tot[i]*(1-cost_rate(i))-labor(i)-deprec(i) for i in range(3)]
    print(f"{'영업이익':<22}"+"".join(f"{eok(op[i]):>15.1f}억" for i in range(3)))
    print(f"{'  영업이익률':<22}"+"".join(f"{op[i]/tot[i]:>15.1%}" for i in range(3)))
    tax=[corp_tax(op[i]) for i in range(3)]
    print(f"{'  법인세(준비금 50% 반영)':<22}"+"".join(f"{-eok(tax[i]):>15.1f}억" for i in range(3)))
    net=[op[i]-tax[i] for i in range(3)]
    print(f"{'세후이익':<22}"+"".join(f"{eok(net[i]):>15.1f}억" for i in range(3)))
    print(f"{'  세후이익률':<22}"+"".join(f"{net[i]/tot[i]:>15.1%}" for i in range(3)))
    print("-"*108)
    print(f"{'CAPEX':<22}"+"".join(f"{eok(capex(i)):>15.1f}억" for i in range(3)))
    print(f"{'  단가(만원/평)':<22}"+"".join(f"{CAPEX_UNIT[i]:>16}" for i in range(3)))
    print(f"{'회수기간(세후이익 기준)':<22}"+"".join(
        (f"{capex(i)/net[i]:>15.1f}년" if net[i]>0 else f"{'회수불가':>16}") for i in range(3)))

    print()
    print("="*108)
    print("★ 손익분기 — 하루에 몇 명을 받아야 본전인가")
    print("="*108)
    print(f"{'':<24}{'보수':>16}{'기준':>16}{'낙관':>16}")
    print("-"*108)
    var=[COST['식재료비'][i]+COST['수도광열·소모품'][i]+COST['관리·보험·기타'][i] for i in range(3)]
    fixed=[labor(i)+deprec(i)+tot[i]*COST['마케팅'][i] for i in range(3)]
    cm=[1-var[i] for i in range(3)]
    be_rev=[fixed[i]/cm[i] for i in range(3)]
    be_cov=[be_rev[i]/(blended(i)*DAYS[i]) for i in range(3)]
    print(f"{'공헌이익률':<24}"+"".join(f"{cm[i]:>16.0%}" for i in range(3)))
    print(f"{'고정비(인건비+감가+마케팅)':<24}"+"".join(f"{eok(fixed[i]):>15.1f}억" for i in range(3)))
    print(f"{'BEP 매출':<24}"+"".join(f"{eok(be_rev[i]):>15.1f}억" for i in range(3)))
    print(f"{'BEP 일 커버수':<24}"+"".join(f"{be_cov[i]:>15.0f}명" for i in range(3)))
    print(f"{'계획 일 커버수':<24}"+"".join(f"{covers(i):>15.0f}명" for i in range(3)))
    print(f"{'안전마진':<24}"+"".join(f"{(covers(i)-be_cov[i])/covers(i):>+16.0%}" for i in range(3)))
    print(f"{'판정':<24}"+"".join(f"{('흑자' if covers(i)>be_cov[i] else '적자'):>16}" for i in range(3)))
    print("-"*108)
    print(f"  ※ 발우공양(미쉐린 1스타·조계종 직영·2009년 개업) 실적이 일 120명")
    print(f"     기준안 BEP {be_cov[1]:.0f}명 = 발우공양의 {be_cov[1]/120:.0%} — 신규 매장이 즉시 그 수준에 도달해야 본전")

    print()
    print("="*108)
    print("조리 게이트 닫힘 — 완제품 반입 대안모델")
    print("="*108)
    alt_rev=[ALT_COVERS[i]*ALT_PRICE[i]*ALT_DAYS[i] for i in range(3)]
    alt_op=[alt_rev[i]*(1-ALT_COST[i]-ALT_LABOR[i]-ALT_OTHER[i]) for i in range(3)]
    print(f"{'항목':<22}{'보수':>16}{'기준':>16}{'낙관':>16}")
    print("-"*108)
    print(f"{'객단가':<22}"+"".join(f"{won(ALT_PRICE[i]):>16}" for i in range(3)))
    print(f"{'일 커버수':<22}"+"".join(f"{ALT_COVERS[i]:>15}명" for i in range(3)))
    print(f"{'매출액':<22}"+"".join(f"{eok(alt_rev[i]):>15.1f}억" for i in range(3)))
    print(f"{'  매입원가(외주 완제품)':<22}"+"".join(f"{-eok(alt_rev[i]*ALT_COST[i]):>15.1f}억" for i in range(3)))
    print(f"{'  인건비(조리 불요)':<22}"+"".join(f"{-eok(alt_rev[i]*ALT_LABOR[i]):>15.1f}억" for i in range(3)))
    print(f"{'  기타':<22}"+"".join(f"{-eok(alt_rev[i]*ALT_OTHER[i]):>15.1f}억" for i in range(3)))
    print(f"{'영업이익':<22}"+"".join(f"{eok(alt_op[i]):>15.1f}억" for i in range(3)))
    print(f"{'  영업이익률':<22}"+"".join(f"{alt_op[i]/alt_rev[i]:>15.1%}" for i in range(3)))
    print("-"*108)
    print(f"{'게이트 열림 대비 매출':<22}"+"".join(f"{alt_rev[i]/tot[i]:>15.0%}" for i in range(3)))
    print(f"{'게이트 열림 대비 이익':<22}"+"".join(f"{alt_op[i]/op[i]:>15.0%}" for i in range(3)))

    print()
    print("="*108)
    print("v0.2 대비 변경 — 무엇이 왜 바뀌었나")
    print("="*108)
    OLD=[8.4,23.5,36.9]  # v0.2 RL-03
    print(f"{'':<22}{'보수':>16}{'기준':>16}{'낙관':>16}")
    print(f"{'v0.2 RL-03 매출':<22}"+"".join(f"{OLD[i]:>15.1f}억" for i in range(3)))
    print(f"{'v1.0 RL-03 매출':<22}"+"".join(f"{eok(rev_dining(i)):>15.1f}억" for i in range(3)))
    print(f"{'증감':<22}"+"".join(f"{(eok(rev_dining(i))/OLD[i]-1):>15.0%}" for i in range(3)))
