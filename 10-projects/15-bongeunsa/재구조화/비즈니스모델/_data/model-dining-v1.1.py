# -*- coding: utf-8 -*-
"""다이닝 모델 v1.1 — 발우공양 타임 구조 반영
v1.0 대비: 좌석×회전을 '좌석 × 타임수 × 타임당 점유율'로 분해.
회전율은 결과이지 가정이 아니다 — 타임제가 회전을 만든다.
"""
CASE=["보수","기준","낙관"]
def eok(v): return v/1e8

# ── 발우공양 실측 (balwoo.or.kr 공식) ──
BW_TIMES=3          # 점심1부 11:30~13:20 / 점심2부 13:30~14:50 / 저녁 18:00~20:20
BW_COVERS=120       # E-0424
BW_DAYS=313         # 월~토, 일요일 휴무
BW_SEAT_EST=(50,60) # 타임당 40명 ÷ 점유율 67~80%

# ── 봉은사 설계 ──
SEATS=[50,60,70]
TIMES=[3.0,3.0,3.5]           # 낙관은 저녁 2부제 도입
OCC=[0.55,0.70,0.80]          # 타임당 점유율 (룸 예약제 상한 ~80%)
DAYS=[300,313,313]
LUNCH_SHARE=[0.60,0.55,0.50]
LUNCH_PRICE=[36_000,40_000,45_000]
DINNER_PRICE=[50_000,65_000,80_000]

def turn(i):    return TIMES[i]*OCC[i]
def covers(i):  return SEATS[i]*turn(i)
def blended(i): return LUNCH_SHARE[i]*LUNCH_PRICE[i]+(1-LUNCH_SHARE[i])*DINNER_PRICE[i]
def rev_dining(i): return covers(i)*blended(i)*DAYS[i]

# ── 면적 ──
SQM_SEAT=3.75; KITCH=1/3   # 주방 = 홀의 1/3 (전체의 1/4)
def hall(i):   return SEATS[i]*SQM_SEAT
def kitchen(i):return hall(i)*KITCH
def dining_area(i): return hall(i)+kitchen(i)
TEAROOM=400
def fnb_area(i): return dining_area(i)+TEAROOM

# ── 전통다원 (변경 없음) ──
T_SEATS=[60,80,80]; T_PRICE=[15_000,20_000,25_000]
T_TURN=[1.0,1.5,1.8]; T_DAYS=[300,330,350]
def rev_tea(i): return T_SEATS[i]*T_PRICE[i]*T_TURN[i]*T_DAYS[i]

# ── 원가 ──
COST={"식재료비":[0.38,0.35,0.32],"임차료":[0,0,0],
      "수도광열·소모품":[0.06,0.05,0.045],"마케팅":[0.03,0.02,0.015],
      "관리·보험·기타":[0.04,0.03,0.03]}
COVER_PER_STAFF=[5.0,6.0,7.0]; WAGE=3.5e7; TEA_PER_STAFF=20
def staff(i): return covers(i)/COVER_PER_STAFF[i]+T_SEATS[i]/TEA_PER_STAFF
def labor(i): return staff(i)*WAGE
def var_rate(i): return COST["식재료비"][i]+COST["수도광열·소모품"][i]+COST["관리·보험·기타"][i]

PY=3.3058; CAPEX_UNIT=[500,420,350]; DEP_Y=10
def capex(i): return fnb_area(i)/PY*CAPEX_UNIT[i]*1e4
def deprec(i): return capex(i)/DEP_Y
def corp_tax(p):
    if p<=0: return 0
    b=p*0.5
    return b*0.09 if b<=2e8 else 2e8*0.09+(b-2e8)*0.19

V10_AREA=1000; V10_CAPEX=[15.1,12.7,10.6]; V10_REV_D=[9.3,18.9,35.9]

print("="*104)
print("발우공양 타임 구조 → 좌석 역산  (balwoo.or.kr 공식 실측)")
print("="*104)
print(f"  3타임 구조 · 일 {BW_COVERS}명 → 타임당 {BW_COVERS/BW_TIMES:.0f}명")
print(f"  점유율 67~80% 역산 시 좌석 {BW_SEAT_EST[0]}~{BW_SEAT_EST[1]}석 · 실효 회전 {BW_COVERS/BW_SEAT_EST[1]:.1f}~{BW_COVERS/BW_SEAT_EST[0]:.1f}")
print(f"  ※ v1.0은 80석×회전1.5로 잡았음 — 좌석 과다·회전 과소")
print()
print("="*104)
print("v1.1 봉은사 다이닝 — 회전은 가정이 아니라 타임 구조의 결과")
print("="*104)
print(f"{'':<22}{'보수':>14}{'기준':>14}{'낙관':>14}")
print("-"*104)
for lab,vals in [
    ("좌석",[f"{SEATS[i]}석" for i in range(3)]),
    ("일 타임수",[f"{TIMES[i]:.1f}" for i in range(3)]),
    ("타임당 점유율",[f"{OCC[i]:.0%}" for i in range(3)]),
    ("→ 실효 회전",[f"{turn(i):.2f}" for i in range(3)]),
    ("→ 일 커버수",[f"{covers(i):.0f}명" for i in range(3)]),
    ("발우공양 대비",[f"{covers(i)/BW_COVERS:.2f}x" for i in range(3)]),
    ("블렌디드 객단가",[f"{blended(i):,.0f}" for i in range(3)]),
    ("영업일",[f"{DAYS[i]}일" for i in range(3)]),
]:
    print(f"{lab:<22}"+"".join(f"{v:>14}" for v in vals))
print("-"*104)
print(f"{'다이닝 매출':<22}"+"".join(f"{eok(rev_dining(i)):>13.1f}억" for i in range(3)))
print(f"{'  v1.0 대비':<22}"+"".join(f"{eok(rev_dining(i))/V10_REV_D[i]-1:>+14.0%}" for i in range(3)))
print()
print("="*104)
print("★ 면적이 줄어듭니다 — 이것이 이번 발견의 실질")
print("="*104)
print(f"{'':<22}{'보수':>14}{'기준':>14}{'낙관':>14}")
print("-"*104)
print(f"{'홀':<22}"+"".join(f"{hall(i):>12.0f}㎡" for i in range(3)))
print(f"{'주방':<22}"+"".join(f"{kitchen(i):>12.0f}㎡" for i in range(3)))
print(f"{'다이닝 소계':<22}"+"".join(f"{dining_area(i):>12.0f}㎡" for i in range(3)))
print(f"{'전통다원':<22}"+"".join(f"{TEAROOM:>12.0f}㎡" for i in range(3)))
print(f"{'F&B 합계':<22}"+"".join(f"{fnb_area(i):>12.0f}㎡" for i in range(3)))
print(f"{'배정(E-0532) 1,000㎡ 대비':<22}"+"".join(f"{fnb_area(i)-V10_AREA:>+12.0f}㎡" for i in range(3)))
print("-"*104)
print(f"  → 기준안에서 {V10_AREA-fnb_area(1):.0f}㎡가 남습니다. 전시·명상·대관 등 다른 라인으로 재배분 가능")
print()
print("="*104)
print("손익 (RL-02 + RL-03)")
print("="*104)
tot=[rev_dining(i)+rev_tea(i) for i in range(3)]
print(f"{'항목':<22}{'보수':>14}{'기준':>14}{'낙관':>14}")
print("-"*104)
print(f"{'매출액':<22}"+"".join(f"{eok(tot[i]):>13.1f}억" for i in range(3)))
print(f"{'  식재료비':<22}"+"".join(f"{-eok(tot[i]*COST['식재료비'][i]):>13.1f}억" for i in range(3)))
print(f"{'  인건비':<22}"+"".join(f"{-eok(labor(i)):>13.1f}억" for i in range(3)))
print(f"{'    인원':<22}"+"".join(f"{staff(i):>13.0f}명" for i in range(3)))
print(f"{'    매출대비':<22}"+"".join(f"{labor(i)/tot[i]:>14.0%}" for i in range(3)))
for n in ["임차료","수도광열·소모품","마케팅","관리·보험·기타"]:
    print(f"{'  '+n:<22}"+"".join(f"{-eok(tot[i]*COST[n][i]):>13.1f}억" for i in range(3)))
print(f"{'  감가상각':<22}"+"".join(f"{-eok(deprec(i)):>13.1f}억" for i in range(3)))
print("-"*104)
op=[tot[i]*(1-var_rate(i)-COST['마케팅'][i])-labor(i)-deprec(i) for i in range(3)]
print(f"{'영업이익':<22}"+"".join(f"{eok(op[i]):>+13.1f}억" for i in range(3)))
print(f"{'  영업이익률':<22}"+"".join(f"{op[i]/tot[i]:>+14.1%}" for i in range(3)))
net=[op[i]-corp_tax(op[i]) for i in range(3)]
print(f"{'세후이익':<22}"+"".join(f"{eok(net[i]):>+13.1f}억" for i in range(3)))
print(f"{'CAPEX':<22}"+"".join(f"{eok(capex(i)):>13.1f}억" for i in range(3)))
print(f"{'  v1.0 대비':<22}"+"".join(f"{eok(capex(i))-V10_CAPEX[i]:>+13.1f}억" for i in range(3)))
print(f"{'회수기간':<22}"+"".join((f"{capex(i)/net[i]:>13.1f}년" if net[i]>0 else f"{'회수불가':>14}") for i in range(3)))
print()
print("="*104)
print("★ 손익분기")
print("="*104)
fixed=[labor(i)+deprec(i)+tot[i]*COST['마케팅'][i] for i in range(3)]
cm=[1-var_rate(i) for i in range(3)]
be_rev=[fixed[i]/cm[i] for i in range(3)]
be_cov=[be_rev[i]/(blended(i)*DAYS[i]) for i in range(3)]
be_seat_occ=[be_cov[i]/(SEATS[i]*TIMES[i]) for i in range(3)]
print(f"{'':<22}{'보수':>14}{'기준':>14}{'낙관':>14}")
print("-"*104)
print(f"{'공헌이익률':<22}"+"".join(f"{cm[i]:>14.0%}" for i in range(3)))
print(f"{'고정비':<22}"+"".join(f"{eok(fixed[i]):>13.1f}억" for i in range(3)))
print(f"{'BEP 매출':<22}"+"".join(f"{eok(be_rev[i]):>13.1f}억" for i in range(3)))
print(f"{'BEP 일 커버수':<22}"+"".join(f"{be_cov[i]:>13.0f}명" for i in range(3)))
print(f"{'계획 일 커버수':<22}"+"".join(f"{covers(i):>13.0f}명" for i in range(3)))
print(f"{'BEP 타임당 점유율':<22}"+"".join(f"{be_seat_occ[i]:>14.0%}" for i in range(3)))
print(f"{'계획 타임당 점유율':<22}"+"".join(f"{OCC[i]:>14.0%}" for i in range(3)))
print(f"{'안전마진':<22}"+"".join(f"{(covers(i)-be_cov[i])/covers(i):>+14.0%}" for i in range(3)))
print(f"{'판정':<22}"+"".join(f"{('흑자' if covers(i)>be_cov[i] else '적자'):>14}" for i in range(3)))
print("-"*104)
print(f"  ※ BEP를 '타임당 점유율'로 바꿔 읽으면 실무 목표가 됩니다 —")
print(f"     기준안은 매 타임 좌석의 {be_seat_occ[1]:.0%}를 채우면 본전, {OCC[1]:.0%}를 채우면 계획 달성")
print()
print("="*104)
print("v1.0 → v1.1 요약")
print("="*104)
V10=[(-2.3,15.1,'회수불가',114),(5.1,12.7,'2.6년',114),(17.1,10.6,'0.7년',101)]
print(f"{'':<22}{'보수':>14}{'기준':>14}{'낙관':>14}")
print(f"{'v1.0 영업이익':<22}"+"".join(f"{V10[i][0]:>+13.1f}억" for i in range(3)))
print(f"{'v1.1 영업이익':<22}"+"".join(f"{eok(op[i]):>+13.1f}억" for i in range(3)))
print(f"{'v1.0 CAPEX':<22}"+"".join(f"{V10[i][1]:>13.1f}억" for i in range(3)))
print(f"{'v1.1 CAPEX':<22}"+"".join(f"{eok(capex(i)):>13.1f}억" for i in range(3)))
print(f"{'v1.0 BEP 커버':<22}"+"".join(f"{V10[i][3]:>13}명" for i in range(3)))
print(f"{'v1.1 BEP 커버':<22}"+"".join(f"{be_cov[i]:>13.0f}명" for i in range(3)))
