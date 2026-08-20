# -*- coding: utf-8 -*-
"""다이닝 모델 v2.0 — 엔트리 파인 · 소규모 고단가 재설계
설계 지시: ① 복합공간이므로 규모 축소 ② 엔트리 파인 수준으로 경량화
          ③ 객단가는 발우공양 대비 130~150% ④ 좌석 40~60석
"""
CASE=["보수","기준","낙관"]
def eok(v): return v/1e8

# ══════ 발우공양 블렌디드 객단가 추정 (130~150%의 기준점) ══════
# 코스 실측: 선 36,000(평일점심 한정) / 원 50,000 / 마음 70,000 / 희 120,000(사전예약)
# 판매 믹스는 비공개 → 타임 구조로 추정
BW = dict(
  lunch_share=0.55,          # 점심 2타임 : 저녁 1타임 → 점심이 다수
  lunch_avg=38_000,          # 선 36,000 중심 + 일부 원 50,000
  dinner_avg=58_000,         # 원 50,000 ~ 마음 70,000 중심 + 희 일부
)
BW_BLEND = BW['lunch_share']*BW['lunch_avg'] + (1-BW['lunch_share'])*BW['dinner_avg']
BW_COVERS=120; BW_DAYS=313
BW_REV = BW_BLEND*BW_COVERS*BW_DAYS

# ══════ v2.0 설계 ══════
TARGET_MULT=[1.30,1.40,1.50]        # 발우공양 대비 배수 (지시)
SEATS=[40,50,60]                     # 지시: 40~60석
TIMES=[2.5,3.0,3.0]                  # 고급화 → 체류 연장. 보수는 점심 1.5부
OCC=[0.50,0.65,0.78]                 # 룸 예약제 상한 80%
DAYS=[300,313,313]
LUNCH_SHARE=[0.55,0.52,0.50]

# 목표 블렌디드에서 코스가 역산
BLEND=[BW_BLEND*m for m in TARGET_MULT]
# 저녁/점심 단가비 2.0 고정 → 점심 = blend/(ls + (1-ls)*2.0)
def lunch_price(i):
    ls=LUNCH_SHARE[i]
    return BLEND[i]/(ls+(1-ls)*2.0)
def dinner_price(i): return lunch_price(i)*2.0

def turn(i):   return TIMES[i]*OCC[i]
def covers(i): return SEATS[i]*turn(i)
def rev_dining(i): return covers(i)*BLEND[i]*DAYS[i]

# ══════ 면적 — 고급화로 좌석당 면적 상향 ══════
SQM_SEAT=4.0            # 엔트리 파인 룸형 (v1.1은 3.75)
KITCH=1/3
def hall(i): return SEATS[i]*SQM_SEAT
def kitchen(i): return hall(i)*KITCH
def dining_area(i): return hall(i)+kitchen(i)

# 전통다원도 경량화 (v1.1 400㎡ → 축소)
T_SEATS=[30,40,50]; T_PRICE=[18_000,22_000,26_000]
T_TURN=[1.2,1.6,1.9]; T_DAYS=[300,313,330]
T_SQM=3.0
def tea_area(i): return T_SEATS[i]*T_SQM*1.25   # 홀+백룸
def rev_tea(i): return T_SEATS[i]*T_PRICE[i]*T_TURN[i]*T_DAYS[i]
def fnb_area(i): return dining_area(i)+tea_area(i)

# ══════ 원가 ══════
COST={"식재료비":[0.35,0.33,0.31],"임차료":[0,0,0],
      "수도광열·소모품":[0.055,0.045,0.04],"마케팅":[0.03,0.02,0.015],
      "관리·보험·기타":[0.04,0.03,0.03]}
COVER_PER_STAFF=[4.0,5.0,6.0]   # 고급화 → 생산성 하향 (v1.1은 5/6/7)
WAGE=3.5e7; TEA_PER_STAFF=20
def staff(i): return covers(i)/COVER_PER_STAFF[i]+T_SEATS[i]/TEA_PER_STAFF
def labor(i): return staff(i)*WAGE
def var_rate(i): return COST["식재료비"][i]+COST["수도광열·소모품"][i]+COST["관리·보험·기타"][i]

PY=3.3058
CAPEX_UNIT=[620,560,500]        # 고급 사양 (v1.1은 500/420/350)
DEP_Y=10
def capex(i): return fnb_area(i)/PY*CAPEX_UNIT[i]*1e4
def deprec(i): return capex(i)/DEP_Y
def corp_tax(p):
    if p<=0: return 0
    b=p*0.5
    return b*0.09 if b<=2e8 else 2e8*0.09+(b-2e8)*0.19

V11=dict(area=[650,700,750], capex=[9.8,8.9,7.9], op=[-1.4,5.8,18.1],
         rev=[13.0,28.1,50.9], bep_occ=[0.84,0.62,0.44], seats=[50,60,70])

print("="*106)
print("기준점 — 발우공양 블렌디드 객단가 추정")
print("="*106)
print(f"  코스 실측: 선 36,000(평일점심) / 원 50,000 / 마음 70,000 / 희 120,000(사전예약)")
print(f"  판매 믹스 비공개 → 타임 구조로 추정: 점심 {BW['lunch_share']:.0%} × {BW['lunch_avg']:,}원 + 저녁 {1-BW['lunch_share']:.0%} × {BW['dinner_avg']:,}원")
print(f"  → 발우공양 블렌디드 객단가 ≈ {BW_BLEND:,.0f}원  (연매출 환산 {eok(BW_REV):.1f}억)")
print(f"  ※ 추정치 — 실제 믹스가 확인되면 아래 전 수치가 비례 이동합니다")
print()
print("="*106)
print("v2.0 설계 — 엔트리 파인 · 소규모 고단가")
print("="*106)
print(f"{'':<24}{'보수':>15}{'기준':>15}{'낙관':>15}")
print("-"*106)
rows=[
 ("발우공양 대비 배수",[f"{TARGET_MULT[i]:.0%}" for i in range(3)]),
 ("→ 블렌디드 객단가",[f"{BLEND[i]:,.0f}원" for i in range(3)]),
 ("  점심 코스",[f"{lunch_price(i):,.0f}원" for i in range(3)]),
 ("  저녁 코스",[f"{dinner_price(i):,.0f}원" for i in range(3)]),
 ("  발우 선식 36,000 대비",[f"{lunch_price(i)/36_000:.0%}" for i in range(3)]),
 ("  발우 마음식 70,000 대비",[f"{dinner_price(i)/70_000:.0%}" for i in range(3)]),
 ("좌석",[f"{SEATS[i]}석" for i in range(3)]),
 ("일 타임수",[f"{TIMES[i]:.1f}" for i in range(3)]),
 ("타임당 점유율",[f"{OCC[i]:.0%}" for i in range(3)]),
 ("→ 실효 회전",[f"{turn(i):.2f}" for i in range(3)]),
 ("→ 일 커버수",[f"{covers(i):.0f}명" for i in range(3)]),
 ("  발우공양 120명 대비",[f"{covers(i)/BW_COVERS:.0%}" for i in range(3)]),
 ("영업일",[f"{DAYS[i]}일" for i in range(3)]),
]
for lab,v in rows: print(f"{lab:<24}"+"".join(f"{x:>15}" for x in v))
print("-"*106)
print(f"{'다이닝 매출':<24}"+"".join(f"{eok(rev_dining(i)):>14.1f}억" for i in range(3)))
print(f"{'전통다원 매출':<24}"+"".join(f"{eok(rev_tea(i)):>14.1f}억" for i in range(3)))
tot=[rev_dining(i)+rev_tea(i) for i in range(3)]
print(f"{'F&B 합계':<24}"+"".join(f"{eok(tot[i]):>14.1f}억" for i in range(3)))
print(f"{'  v1.1 대비':<24}"+"".join(f"{eok(tot[i])/V11['rev'][i]-1:>+15.0%}" for i in range(3)))

print()
print("="*106)
print("면적 — 복합공간 안에서 얼마나 가벼워지는가")
print("="*106)
print(f"{'':<24}{'보수':>15}{'기준':>15}{'낙관':>15}")
print("-"*106)
print(f"{'다이닝 홀 (4.0㎡/석)':<24}"+"".join(f"{hall(i):>13.0f}㎡" for i in range(3)))
print(f"{'다이닝 주방':<24}"+"".join(f"{kitchen(i):>13.0f}㎡" for i in range(3)))
print(f"{'다이닝 소계':<24}"+"".join(f"{dining_area(i):>13.0f}㎡" for i in range(3)))
print(f"{'전통다원':<24}"+"".join(f"{tea_area(i):>13.0f}㎡" for i in range(3)))
print(f"{'F&B 합계':<24}"+"".join(f"{fnb_area(i):>13.0f}㎡" for i in range(3)))
print(f"{'  v1.1 대비':<24}"+"".join(f"{fnb_area(i)-V11['area'][i]:>+13.0f}㎡" for i in range(3)))
print(f"{'  배정 1,000㎡ 대비':<24}"+"".join(f"{fnb_area(i)-1000:>+13.0f}㎡" for i in range(3)))
print("-"*106)
print(f"  → 기준안에서 배정 대비 {1000-fnb_area(1):.0f}㎡가 남습니다 (v1.1은 300㎡)")
print(f"  → 8,868㎡ 전체 대비 F&B 비중 {fnb_area(1)/8868:.1%} (v1.1 7.9% · 통합배치안 11.3%)")

print()
print("="*106)
print("손익")
print("="*106)
print(f"{'항목':<24}{'보수':>15}{'기준':>15}{'낙관':>15}")
print("-"*106)
print(f"{'매출액':<24}"+"".join(f"{eok(tot[i]):>14.1f}억" for i in range(3)))
print(f"{'  식재료비':<24}"+"".join(f"{-eok(tot[i]*COST['식재료비'][i]):>14.1f}억" for i in range(3)))
print(f"{'  인건비':<24}"+"".join(f"{-eok(labor(i)):>14.1f}억" for i in range(3)))
print(f"{'    인원':<24}"+"".join(f"{staff(i):>14.0f}명" for i in range(3)))
print(f"{'    매출대비':<24}"+"".join(f"{labor(i)/tot[i]:>15.0%}" for i in range(3)))
for n in ["임차료","수도광열·소모품","마케팅","관리·보험·기타"]:
    print(f"{'  '+n:<24}"+"".join(f"{-eok(tot[i]*COST[n][i]):>14.1f}억" for i in range(3)))
print(f"{'  감가상각':<24}"+"".join(f"{-eok(deprec(i)):>14.1f}억" for i in range(3)))
print("-"*106)
op=[tot[i]*(1-var_rate(i)-COST['마케팅'][i])-labor(i)-deprec(i) for i in range(3)]
print(f"{'영업이익':<24}"+"".join(f"{eok(op[i]):>+14.1f}억" for i in range(3)))
print(f"{'  영업이익률':<24}"+"".join(f"{op[i]/tot[i]:>+15.1%}" for i in range(3)))
print(f"{'  v1.1 대비':<24}"+"".join(f"{eok(op[i])-V11['op'][i]:>+14.1f}억" for i in range(3)))
net=[op[i]-corp_tax(op[i]) for i in range(3)]
print(f"{'세후이익':<24}"+"".join(f"{eok(net[i]):>+14.1f}억" for i in range(3)))
print(f"{'CAPEX':<24}"+"".join(f"{eok(capex(i)):>14.1f}억" for i in range(3)))
print(f"{'  단가(만원/평)':<24}"+"".join(f"{CAPEX_UNIT[i]:>15}" for i in range(3)))
print(f"{'  v1.1 대비':<24}"+"".join(f"{eok(capex(i))-V11['capex'][i]:>+14.1f}억" for i in range(3)))
print(f"{'회수기간':<24}"+"".join((f"{capex(i)/net[i]:>14.1f}년" if net[i]>0 else f"{'회수불가':>15}") for i in range(3)))

print()
print("="*106)
print("★ 손익분기")
print("="*106)
fixed=[labor(i)+deprec(i)+tot[i]*COST['마케팅'][i] for i in range(3)]
cm=[1-var_rate(i) for i in range(3)]
be_rev=[fixed[i]/cm[i] for i in range(3)]
# ★ 정정: 다원 공헌이익이 고정비를 함께 부담한다.
#   다이닝이 감당할 고정비 = 총고정비 − 다원 공헌이익
tea_cm=[rev_tea(i)*cm[i] for i in range(3)]
be_rev_dining=[max(0,(fixed[i]-tea_cm[i]))/cm[i] for i in range(3)]
be_cov=[be_rev_dining[i]/(BLEND[i]*DAYS[i]) for i in range(3)]
be_occ=[be_cov[i]/(SEATS[i]*TIMES[i]) for i in range(3)]
print(f"{'':<24}{'보수':>15}{'기준':>15}{'낙관':>15}")
print("-"*106)
print(f"{'공헌이익률':<24}"+"".join(f"{cm[i]:>15.0%}" for i in range(3)))
print(f"{'고정비':<24}"+"".join(f"{eok(fixed[i]):>14.1f}억" for i in range(3)))
print(f"{'BEP 매출':<24}"+"".join(f"{eok(be_rev[i]):>14.1f}억" for i in range(3)))
print(f"{'BEP 일 커버수':<24}"+"".join(f"{be_cov[i]:>14.0f}명" for i in range(3)))
print(f"{'계획 일 커버수':<24}"+"".join(f"{covers(i):>14.0f}명" for i in range(3)))
print(f"{'BEP 타임당 점유율':<24}"+"".join(f"{be_occ[i]:>15.0%}" for i in range(3)))
print(f"{'계획 타임당 점유율':<24}"+"".join(f"{OCC[i]:>15.0%}" for i in range(3)))
print(f"{'  v1.1 BEP 점유율':<24}"+"".join(f"{V11['bep_occ'][i]:>15.0%}" for i in range(3)))
print(f"{'안전마진':<24}"+"".join(f"{(covers(i)-be_cov[i])/covers(i):>+15.0%}" for i in range(3)))
print(f"{'판정':<24}"+"".join(f"{('흑자' if covers(i)>be_cov[i] else '적자'):>15}" for i in range(3)))
print("-"*106)
print(f"  ※ 기준안: {SEATS[1]}석 {TIMES[1]:.0f}타임에서 매 타임 {SEATS[1]*be_occ[1]:.0f}명({be_occ[1]:.0%})이면 본전,")
print(f"     {SEATS[1]*OCC[1]:.0f}명({OCC[1]:.0%})이면 계획 달성")

print()
print("="*106)
print("면적당 생산성 — 복합공간에서 F&B가 자기 자리값을 하는가")
print("="*106)
print(f"{'':<24}{'보수':>15}{'기준':>15}{'낙관':>15}")
print("-"*106)
print(f"{'㎡당 매출(만원)':<24}"+"".join(f"{tot[i]/fnb_area(i)/1e4:>15.0f}" for i in range(3)))
print(f"{'㎡당 영업이익(만원)':<24}"+"".join(f"{op[i]/fnb_area(i)/1e4:>15.0f}" for i in range(3)))
print(f"{'  v1.1 ㎡당 매출':<24}"+"".join(f"{V11['rev'][i]*1e8/V11['area'][i]/1e4:>15.0f}" for i in range(3)))
print(f"{'  v1.1 ㎡당 영업이익':<24}"+"".join(f"{V11['op'][i]*1e8/V11['area'][i]/1e4:>15.0f}" for i in range(3)))
print("-"*106)
print(f"  ※ 대관 벤치마크: 코엑스 3,202~3,905원/㎡·일 → 연 100일 가동 시 ㎡당 32~39만원")
