# -*- coding: utf-8 -*-
"""v5.0 — 사찰음식 4축 확산 모델
연구소(Research) → 아카데미(Academy) → 프리미엄 다이닝(Dining) → 슈퍼마켓(Market)
온지음 3공방 구조의 상업적 확장판. 전통주는 각 축을 관통하는 축으로 편입.
"""
def eok(v): return v/1e8
CASE=["보수","기준","낙관"]

BENCH = """
[벤치마크 — 사찰음식 교육 실측 (조계종 공식)]
  · 정규강좌 12주(주1회): 초급 600,000 / 중급 700,000 / 고급 600,000원 — 교재·식재료 포함
  · 한국사찰음식문화체험관: 월 4회 120,000원 · 1일 강좌 별도
  · 운영기관 3원화: 체험관(문화체험) · 향적세계(교육) · 발우공양(다이닝) — E-0435
  · 동국대 전통사찰음식연구소 별도 존재
[벤치마크 — 진관사]
  · 서울 은평구 북한산 자락 · 스님이 직접 농사·장 담그기·발효
  · 요리교실 상시 운영 · 템플스테이 기간 다양화
  · 은평한옥마을과 산책로로 연결 — 마을+사찰 동선 결합형
[벤치마크 — 전통주 교육]
  · 빚기 원데이 45,000~60,000원(단체) · 이화주 60,000원 · 정원 16~20명
  · 발효 7~14일 후 수령 → 구조적 재방문 장치
[시장]
  · HMR 국내 5조원 · 가공식품 온라인 구매 비중 2018년 2.4% → 2020년 11.4%
  · 봉은사는 이미 가정간편식·밀키트·할랄인증·수출을 구상 중 — E-0511
"""

# ══════════ 축1 · 프리미엄 다이닝 + 전통주 페어링 (v4.0 계승) ══════════
SEATS=[30,40,45]; TIMES=[2.0,2.0,2.5]; OCC=[0.60,0.75,0.80]; DAYS=[260,260,270]
LS=[0.45,0.45,0.42]; LP=[85_000,90_000,95_000]; DP=[140_000,150_000,160_000]
PAIR_L=[40_000,45_000,50_000]; PAIR_D=[65_000,75_000,85_000]; PAIR_RATE=[0.60,0.75,0.85]
def covers(i): return SEATS[i]*TIMES[i]*OCC[i]
def d_heads(i): return covers(i)*DAYS[i]
def blend_food(i): return LS[i]*LP[i]+(1-LS[i])*DP[i]
def blend_pair(i): return (LS[i]*PAIR_L[i]+(1-LS[i])*PAIR_D[i])*PAIR_RATE[i]
def rev_food(i): return d_heads(i)*blend_food(i)
def rev_pair(i): return d_heads(i)*blend_pair(i)

# ══════════ 축2 · 아카데미 ══════════
# ① 사찰음식 정규과정 (12주) — 조계종 실측 60~70만원
REG_P=[650_000,700_000,750_000]; REG_CAP=[14,16,18]; REG_CLASS=[6,10,14]  # 연 개설 기수
REG_UTIL=[0.70,0.80,0.88]
# ② 원데이 클래스 (사찰음식)
OD_P=[60_000,75_000,90_000]; OD_CAP=[16,18,20]; OD_SESS=[100,160,220]; OD_UTIL=[0.65,0.78,0.85]
# ③ 전통주 양조·시음 (v4.0 계승)
BR_P=[60_000,75_000,90_000]; BR_CAP=[14,16,18]; BR_SESS=[80,130,180]; BR_UTIL=[0.60,0.75,0.85]
# ④ 전문가·지도자 과정 (고단가 소수)
PRO_P=[1_500_000,1_800_000,2_200_000]; PRO_CAP=[12,16,20]; PRO_CLASS=[1,2,3]
def rev_reg(i):  return REG_P[i]*REG_CAP[i]*REG_UTIL[i]*REG_CLASS[i]
def rev_od(i):   return OD_P[i]*OD_CAP[i]*OD_UTIL[i]*OD_SESS[i]
def rev_br(i):   return BR_P[i]*BR_CAP[i]*BR_UTIL[i]*BR_SESS[i]
def rev_pro(i):  return PRO_P[i]*PRO_CAP[i]*PRO_CLASS[i]
def rev_acad(i): return rev_reg(i)+rev_od(i)+rev_br(i)+rev_pro(i)
def acad_heads(i):
    return (REG_CAP[i]*REG_UTIL[i]*REG_CLASS[i]+OD_CAP[i]*OD_UTIL[i]*OD_SESS[i]
            +BR_CAP[i]*BR_UTIL[i]*BR_SESS[i]+PRO_CAP[i]*PRO_CLASS[i])

# ══════════ 축3 · 슈퍼마켓 (신규) ══════════
# 문화센터 전체 방문객(CV) — 마스터 모델 v0.2 기준
CV=[110_000,255_000,525_634]
SM_CONV=[0.030,0.045,0.065]     # 마이크로 매장 — 진열 SKU 제한으로 전환 하향
SM_AOV=[30_000,38_000,48_000]   # 큐레이션 편집샵 — SKU 적은 대신 객단가 상향
XSELL=[0.18,0.24,0.30]          # 다이닝·아카데미 참가자의 추가 구매전환
ONLINE=[0.45,0.60,0.75]         # 오프라인 대비 온라인 비율 (뮷즈 온라인 43% 참조)
def sm_buyers(i): return CV[i]*SM_CONV[i] + (d_heads(i)+acad_heads(i))*XSELL[i]
def rev_sm_off(i): return sm_buyers(i)*SM_AOV[i]
def rev_sm_on(i):  return rev_sm_off(i)*ONLINE[i]
def rev_sm(i): return rev_sm_off(i)+rev_sm_on(i)

# ══════════ 축4 · 전통다원 ══════════
T_SEATS=[30,35,40]; T_PRICE=[22_000,26_000,30_000]; T_TURN=[1.3,1.6,1.8]; T_DAYS=[300,313,330]
def rev_tea(i): return T_SEATS[i]*T_PRICE[i]*T_TURN[i]*T_DAYS[i]

def tot(i): return rev_food(i)+rev_pair(i)+rev_acad(i)+rev_sm(i)+rev_tea(i)

# ══════════ 면적 ══════════
def a_dining(i): return SEATS[i]*5.0*(4/3)
A_ACAD=[120,160,200]     # 조리 실습실 + 양조 실습실·저장고
A_SM=[66,83,99]          # 마이크로 편집샵 20/25/30평 (창고는 별도 백룸 최소화)
def a_tea(i): return T_SEATS[i]*3.0*1.25
def area(i): return a_dining(i)+A_ACAD[i]+A_SM[i]+a_tea(i)

# ══════════ 원가 ══════════
C_FOOD=[0.31,0.30,0.29]; C_PAIR=[0.42,0.40,0.38]
C_ACAD=[0.22,0.20,0.18]          # 재료·교재
C_SM=[0.58,0.55,0.52]            # 상품 매입·위탁제조 (리테일 원가율)
C_TEA=[0.33,0.33,0.33]
CPS=[3.2,3.5,3.8]                # 다이닝 커버·인
ACAD_STAFF=[3,4,6]               # 강사·조교
SM_STAFF=[3,4,6]                 # 매장·물류·온라인
WAGE=3.5e7
def staff(i): return covers(i)/CPS[i]+T_SEATS[i]/20+ACAD_STAFF[i]+SM_STAFF[i]
def labor(i): return staff(i)*WAGE
def cogs(i):
    return (rev_food(i)*C_FOOD[i]+rev_pair(i)*C_PAIR[i]+rev_acad(i)*C_ACAD[i]
            +rev_sm(i)*C_SM[i]+rev_tea(i)*C_TEA[i])
OTHER=[0.08,0.07,0.07]; MKT=[0.03,0.025,0.02]
CAPEX_U=[760,700,640]
def capex(i): return area(i)/3.3058*CAPEX_U[i]*1e4
def dep(i): return capex(i)/10
def op(i): return tot(i)-cogs(i)-labor(i)-tot(i)*(OTHER[i]+MKT[i])-dep(i)
def tax(i):
    p=op(i)
    if p<=0: return 0
    b=p*0.5
    return b*0.09 if b<=2e8 else 2e8*0.09+(b-2e8)*0.19

V4=dict(tot=34.8, op=11.5, area=478, capex=10.4, opsqm=241)

print(BENCH)
print("="*108)
print("v5.0 · 4축 확산 모델 — 매출 구성")
print("="*108)
print(f"{'':<28}{'보수':>16}{'기준':>16}{'낙관':>16}")
print("-"*108)
lines=[("축1 다이닝 (음식)",rev_food),("축1 전통주 페어링",rev_pair),
       ("축2 아카데미 계",rev_acad),
       ("   정규과정 12주",rev_reg),("   원데이 클래스",rev_od),
       ("   전통주 양조·시음",rev_br),("   전문가·지도자",rev_pro),
       ("축3 슈퍼마켓 계",rev_sm),
       ("   오프라인 매장",rev_sm_off),("   온라인",rev_sm_on),
       ("축4 전통다원",rev_tea)]
for lab,f in lines:
    mark="  " if lab.startswith("   ") else ""
    print(f"{mark+lab:<28}"+"".join(f"{eok(f(i)):>15.1f}억" for i in range(3)))
print("-"*108)
print(f"{'합계':<28}"+"".join(f"{eok(tot(i)):>15.1f}억" for i in range(3)))
print(f"{'  v4.0 대비':<28}"+"".join(f"{eok(tot(i))/V4['tot']-1:>+16.0%}" for i in range(3)))
print()
print("축별 비중")
for lab,f in [("다이닝+페어링",lambda i:rev_food(i)+rev_pair(i)),("아카데미",rev_acad),
              ("슈퍼마켓",rev_sm),("전통다원",rev_tea)]:
    print(f"{'  '+lab:<28}"+"".join(f"{f(i)/tot(i):>16.0%}" for i in range(3)))
print()
print("모객 규모(연간)")
print(f"{'  다이닝 커버':<28}"+"".join(f"{d_heads(i):>15,.0f}명" for i in range(3)))
print(f"{'  아카데미 수강':<28}"+"".join(f"{acad_heads(i):>15,.0f}명" for i in range(3)))
print(f"{'  슈퍼 구매자':<28}"+"".join(f"{sm_buyers(i):>15,.0f}명" for i in range(3)))
print(f"{'  (문화센터 CV)':<28}"+"".join(f"{CV[i]:>15,.0f}명" for i in range(3)))
print()
print("="*108)
print("손익")
print("="*108)
print(f"{'':<28}{'보수':>16}{'기준':>16}{'낙관':>16}")
print("-"*108)
print(f"{'매출액':<28}"+"".join(f"{eok(tot(i)):>15.1f}억" for i in range(3)))
print(f"{'  매출원가':<28}"+"".join(f"{-eok(cogs(i)):>15.1f}억" for i in range(3)))
print(f"{'    원가율':<28}"+"".join(f"{cogs(i)/tot(i):>16.0%}" for i in range(3)))
print(f"{'  인건비':<28}"+"".join(f"{-eok(labor(i)):>15.1f}억" for i in range(3)))
print(f"{'    인원':<28}"+"".join(f"{staff(i):>15.0f}명" for i in range(3)))
print(f"{'  기타·마케팅':<28}"+"".join(f"{-eok(tot(i)*(OTHER[i]+MKT[i])):>15.1f}억" for i in range(3)))
print(f"{'  감가상각':<28}"+"".join(f"{-eok(dep(i)):>15.1f}억" for i in range(3)))
print("-"*108)
print(f"{'영업이익':<28}"+"".join(f"{eok(op(i)):>+15.1f}억" for i in range(3)))
print(f"{'  영업이익률':<28}"+"".join(f"{op(i)/tot(i):>+16.1%}" for i in range(3)))
print(f"{'  v4.0 대비':<28}"+"".join(f"{eok(op(i))-V4['op']:>+15.1f}억" for i in range(3)))
print(f"{'세후이익':<28}"+"".join(f"{eok(op(i)-tax(i)):>+15.1f}억" for i in range(3)))
print("-"*108)
print(f"{'면적 계':<28}"+"".join(f"{area(i):>15.0f}㎡" for i in range(3)))
for lab,f in [("다이닝",a_dining),("아카데미",lambda i:A_ACAD[i]),
              ("슈퍼마켓",lambda i:A_SM[i]),("전통다원",a_tea)]:
    print(f"{'  '+lab:<28}"+"".join(f"{f(i):>15.0f}㎡" for i in range(3)))
print(f"{'  배정 1,000㎡ 대비':<28}"+"".join(f"{area(i)-1000:>+15.0f}㎡" for i in range(3)))
print(f"{'CAPEX':<28}"+"".join(f"{eok(capex(i)):>15.1f}억" for i in range(3)))
print(f"{'회수기간':<28}"+"".join((f"{capex(i)/(op(i)-tax(i)):>15.1f}년" if op(i)>0 else f"{'불가':>16}") for i in range(3)))
print(f"{'★ ㎡당 영업이익':<28}"+"".join(f"{op(i)/area(i)/1e4:>14.0f}만원" for i in range(3)))
print(f"{'  v4.0 241만원 대비':<28}"+"".join(f"{(op(i)/area(i)/1e4)/V4['opsqm']-1:>+16.0%}" for i in range(3)))
print()
print("="*108)
print("축 간 상호작용 — 왜 4축이 각각보다 큰가")
print("="*108)
print(f"  · 아카데미 수강생 {acad_heads(1):,.0f}명이 슈퍼 구매전환 {XSELL[1]:.0%}로 이어짐")
print(f"  · 슈퍼 구매자 {sm_buyers(1):,.0f}명 중 {(d_heads(1)+acad_heads(1))*XSELL[1]/sm_buyers(1):.0%}가 다이닝·아카데미 경유")
print(f"  · 전통주 양조 클래스는 발효 7~14일 후 수령 → 재방문이 구조적으로 강제됨")
print(f"  · 연구소(비수익)가 콘텐츠 원천 — 정규과정 커리큘럼·메뉴·상품 레시피가 모두 여기서 나옴")
print(f"  · 온라인 {eok(rev_sm_on(1)):.1f}억은 공간을 쓰지 않는 매출 — 공사 기간에도 가동 가능")
