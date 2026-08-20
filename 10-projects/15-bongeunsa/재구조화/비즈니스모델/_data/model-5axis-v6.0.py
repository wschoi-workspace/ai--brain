# -*- coding: utf-8 -*-
"""v6.0 — 곡차를 '체험 서비스'로 재구성
전환: 주류 판매(페어링 부착) → 곡차 체험 프로그램(해설·시음·양조·소장)
근거: 판매 단위가 '술 한 잔'이 아니라 '체험 회차'가 되면 법·여론·가격이 모두 유리해진다.
"""
def eok(v): return v/1e8
CASE=["보수","기준","낙관"]

# ══════════ 축1 · 다이닝 — 곡차 동반 코스(통합 상품) ══════════
SEATS=[30,40,45]; TIMES=[2.0,2.0,2.5]; OCC=[0.60,0.75,0.80]; DAYS=[260,260,270]
LS=[0.45,0.45,0.42]
# 곡차 동반 코스 = 음식 + 곡차 3~4종 + 해설. 별도 페어링가 대신 통합 단가.
GOK_L=[125_000,135_000,145_000]   # 점심 곡차동반 (기존 90,000+45,000=135,000 대비 통합가)
GOK_D=[205_000,225_000,240_000]   # 저녁 곡차동반 (기존 150,000+75,000=225,000)
NOA_L=[85_000,90_000,95_000]      # 무알콜(차 동반) 코스
NOA_D=[140_000,150_000,160_000]
GOK_PICK=[0.55,0.70,0.80]         # 곡차 코스 선택률 (나머지는 무알콜)
def covers(i): return SEATS[i]*TIMES[i]*OCC[i]
def d_heads(i): return covers(i)*DAYS[i]
def blend(i):
    g=LS[i]*GOK_L[i]+(1-LS[i])*GOK_D[i]
    n=LS[i]*NOA_L[i]+(1-LS[i])*NOA_D[i]
    return GOK_PICK[i]*g+(1-GOK_PICK[i])*n
def rev_dining(i): return d_heads(i)*blend(i)

# ══════════ 축2 · 아카데미 (사찰음식) ══════════
REG_P=[650_000,700_000,750_000]; REG_CAP=[14,16,18]; REG_CLASS=[6,10,14]; REG_UTIL=[0.70,0.80,0.88]
OD_P=[60_000,75_000,90_000]; OD_CAP=[16,18,20]; OD_SESS=[100,160,220]; OD_UTIL=[0.65,0.78,0.85]
PRO_P=[1_500_000,1_800_000,2_200_000]; PRO_CAP=[12,16,20]; PRO_CLASS=[1,2,3]
def rev_reg(i): return REG_P[i]*REG_CAP[i]*REG_UTIL[i]*REG_CLASS[i]
def rev_od(i):  return OD_P[i]*OD_CAP[i]*OD_UTIL[i]*OD_SESS[i]
def rev_pro(i): return PRO_P[i]*PRO_CAP[i]*PRO_CLASS[i]
def rev_acad(i): return rev_reg(i)+rev_od(i)+rev_pro(i)
def acad_heads(i):
    return REG_CAP[i]*REG_UTIL[i]*REG_CLASS[i]+OD_CAP[i]*OD_UTIL[i]*OD_SESS[i]+PRO_CAP[i]*PRO_CLASS[i]

# ══════════ 축3 · 곡차 체험 (신설 · 독립 라인) ══════════
# ① 곡차 문화 해설 + 시음 (1~1.5시간)
TAST_P=[65_000,80_000,95_000]; TAST_CAP=[12,14,16]; TAST_SESS=[90,140,190]; TAST_UTIL=[0.60,0.75,0.85]
# ② 곡차 빚기 (양조 실습 · 발효 7~14일 후 수령 → 재방문 강제)
BREW_P=[75_000,90_000,110_000]; BREW_CAP=[14,16,18]; BREW_SESS=[80,130,180]; BREW_UTIL=[0.60,0.75,0.85]
# ③ 곡차 마스터클래스 (명인 초빙 · 고단가 소수)
MAST_P=[250_000,300_000,350_000]; MAST_CAP=[10,12,14]; MAST_SESS=[6,12,20]; MAST_UTIL=[0.70,0.80,0.88]
def rev_tast(i): return TAST_P[i]*TAST_CAP[i]*TAST_UTIL[i]*TAST_SESS[i]
def rev_brew(i): return BREW_P[i]*BREW_CAP[i]*BREW_UTIL[i]*BREW_SESS[i]
def rev_mast(i): return MAST_P[i]*MAST_CAP[i]*MAST_UTIL[i]*MAST_SESS[i]
def rev_gok(i): return rev_tast(i)+rev_brew(i)+rev_mast(i)
def gok_heads(i):
    return (TAST_CAP[i]*TAST_UTIL[i]*TAST_SESS[i]+BREW_CAP[i]*BREW_UTIL[i]*BREW_SESS[i]
            +MAST_CAP[i]*MAST_UTIL[i]*MAST_SESS[i])

# ══════════ 축4 · 마이크로 편집샵 (25평) ══════════
CV=[110_000,255_000,525_634]
SM_CONV=[0.030,0.045,0.065]; SM_AOV=[30_000,38_000,48_000]
XSELL=[0.18,0.24,0.30]
GOK_XSELL=[0.40,0.50,0.58]     # ★ 곡차 체험 참가자는 소장 구매전환이 훨씬 높다
ONLINE=[0.45,0.60,0.75]
def sm_buyers(i):
    return CV[i]*SM_CONV[i]+(d_heads(i)+acad_heads(i))*XSELL[i]+gok_heads(i)*GOK_XSELL[i]
def rev_sm_off(i): return sm_buyers(i)*SM_AOV[i]
def rev_sm_on(i): return rev_sm_off(i)*ONLINE[i]
def rev_sm(i): return rev_sm_off(i)+rev_sm_on(i)

# ══════════ 축5 · 전통다원 ══════════
T_SEATS=[30,35,40]; T_PRICE=[22_000,26_000,30_000]; T_TURN=[1.3,1.6,1.8]; T_DAYS=[300,313,330]
def rev_tea(i): return T_SEATS[i]*T_PRICE[i]*T_TURN[i]*T_DAYS[i]

def tot(i): return rev_dining(i)+rev_acad(i)+rev_gok(i)+rev_sm(i)+rev_tea(i)

# ══════════ 면적 ══════════
def a_dining(i): return SEATS[i]*5.0*(4/3)
A_ACAD=[100,130,160]      # 조리 실습실
A_GOK=[60,80,100]         # 곡차 체험실 + 발효 저장고
A_SM=[66,83,99]           # 25평 내외
def a_tea(i): return T_SEATS[i]*3.0*1.25
def area(i): return a_dining(i)+A_ACAD[i]+A_GOK[i]+A_SM[i]+a_tea(i)

# ══════════ 원가 ══════════
C_DIN=[0.34,0.33,0.32]    # 음식+곡차 통합 원가
C_ACAD=[0.22,0.20,0.18]
C_GOK=[0.26,0.24,0.22]    # 시음주·재료 (체험이라 재료비 비중 낮음)
C_SM=[0.58,0.55,0.52]
C_TEA=[0.33,0.33,0.33]
CPS=[3.2,3.5,3.8]
ACAD_STAFF=[2,3,4]; GOK_STAFF=[2,3,4]; SM_STAFF=[2,3,4]
WAGE=3.5e7
def staff(i): return covers(i)/CPS[i]+T_SEATS[i]/20+ACAD_STAFF[i]+GOK_STAFF[i]+SM_STAFF[i]
def labor(i): return staff(i)*WAGE
def cogs(i):
    return (rev_dining(i)*C_DIN[i]+rev_acad(i)*C_ACAD[i]+rev_gok(i)*C_GOK[i]
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

V51=dict(tot=45.1, op=13.6, area=641, capex=13.6, opsqm=213)

print("="*106)
print("v6.0 — 곡차를 '판매'가 아니라 '체험'으로 재구성")
print("="*106)
print(f"{'':<26}{'보수':>15}{'기준':>15}{'낙관':>15}")
print("-"*106)
for lab,v in [
 ("곡차 동반 코스 선택률",[f"{GOK_PICK[i]:.0%}" for i in range(3)]),
 ("  점심 곡차동반 / 무알콜",[f"{GOK_L[i]//1000}만 / {NOA_L[i]//1000}만" for i in range(3)]),
 ("  저녁 곡차동반 / 무알콜",[f"{GOK_D[i]//1000}만 / {NOA_D[i]//1000}만" for i in range(3)]),
 ("→ 블렌디드 객단가",[f"{blend(i):,.0f}원" for i in range(3)]),
 ("  v5.1 대비",[f"{blend(i)/(123_000+35_000*0.45):.0%}" for i in range(3)]),
 ("일 커버수",[f"{covers(i):.0f}명" for i in range(3)]),
]:
    print(f"{lab:<26}"+"".join(f"{x:>15}" for x in v))
print("-"*106)
print("매출 구성")
for lab,f in [("축1 다이닝(곡차동반 포함)",rev_dining),
              ("축2 아카데미(사찰음식)",rev_acad),
              ("축3 곡차 체험 계",rev_gok),
              ("   곡차 해설·시음",rev_tast),("   곡차 빚기(양조)",rev_brew),("   명인 마스터클래스",rev_mast),
              ("축4 편집샵 계",rev_sm),("   오프라인",rev_sm_off),("   온라인",rev_sm_on),
              ("축5 전통다원",rev_tea)]:
    print(f"{'  '+lab:<26}"+"".join(f"{eok(f(i)):>14.1f}억" for i in range(3)))
print("-"*106)
print(f"{'합계':<26}"+"".join(f"{eok(tot(i)):>14.1f}억" for i in range(3)))
print(f"{'  v5.1 대비':<26}"+"".join(f"{eok(tot(i))/V51['tot']-1:>+15.0%}" for i in range(3)))
print()
print(f"{'곡차 관련 매출':<26}"+"".join(f"{eok(rev_gok(i)):>14.1f}억" for i in range(3)))
print(f"{'  전체 대비':<26}"+"".join(f"{rev_gok(i)/tot(i):>15.0%}" for i in range(3)))
print(f"{'곡차 체험 참가자':<26}"+"".join(f"{gok_heads(i):>14,.0f}명" for i in range(3)))
print(f"{'  → 편집샵 전환':<26}"+"".join(f"{GOK_XSELL[i]:>15.0%}" for i in range(3)))
print()
print("="*106)
print("손익")
print("="*106)
print(f"{'':<26}{'보수':>15}{'기준':>15}{'낙관':>15}{'v5.1 기준':>14}")
print("-"*106)
print(f"{'매출액':<26}"+"".join(f"{eok(tot(i)):>14.1f}억" for i in range(3))+f"{V51['tot']:>13.1f}억")
print(f"{'  매출원가':<26}"+"".join(f"{-eok(cogs(i)):>14.1f}억" for i in range(3)))
print(f"{'    원가율':<26}"+"".join(f"{cogs(i)/tot(i):>15.0%}" for i in range(3)))
print(f"{'  인건비':<26}"+"".join(f"{-eok(labor(i)):>14.1f}억" for i in range(3)))
print(f"{'    인원':<26}"+"".join(f"{staff(i):>14.0f}명" for i in range(3)))
print(f"{'  기타·마케팅':<26}"+"".join(f"{-eok(tot(i)*(OTHER[i]+MKT[i])):>14.1f}억" for i in range(3)))
print(f"{'  감가상각':<26}"+"".join(f"{-eok(dep(i)):>14.1f}억" for i in range(3)))
print("-"*106)
print(f"{'영업이익':<26}"+"".join(f"{eok(op(i)):>+14.1f}억" for i in range(3))+f"{V51['op']:>+13.1f}억")
print(f"{'  영업이익률':<26}"+"".join(f"{op(i)/tot(i):>+15.1%}" for i in range(3)))
print(f"{'세후이익':<26}"+"".join(f"{eok(op(i)-tax(i)):>+14.1f}억" for i in range(3)))
print("-"*106)
print(f"{'면적 계':<26}"+"".join(f"{area(i):>14.0f}㎡" for i in range(3))+f"{V51['area']:>13.0f}㎡")
for lab,f in [("다이닝",a_dining),("아카데미",lambda i:A_ACAD[i]),("곡차 체험실",lambda i:A_GOK[i]),
              ("편집샵",lambda i:A_SM[i]),("전통다원",a_tea)]:
    print(f"{'  '+lab:<26}"+"".join(f"{f(i):>14.0f}㎡" for i in range(3)))
print(f"{'  배정 1,000㎡ 대비':<26}"+"".join(f"{area(i)-1000:>+14.0f}㎡" for i in range(3)))
print(f"{'CAPEX':<26}"+"".join(f"{eok(capex(i)):>14.1f}억" for i in range(3)))
print(f"{'회수기간':<26}"+"".join((f"{capex(i)/(op(i)-tax(i)):>14.1f}년" if op(i)>0 else f"{'불가':>15}") for i in range(3)))
print(f"{'★ ㎡당 영업이익':<26}"+"".join(f"{op(i)/area(i)/1e4:>13.0f}만원" for i in range(3))+f"{V51['opsqm']:>12.0f}만원")
