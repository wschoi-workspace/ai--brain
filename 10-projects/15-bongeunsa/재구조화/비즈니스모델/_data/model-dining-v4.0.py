# -*- coding: utf-8 -*-
"""다이닝 모델 v4.0 — 전통주 페어링 중심 + 체험 상품화
설계 지시: 전통주 페어링을 주력으로 운영하고 체험을 상품화한다.
법적 전제: 브루펍(맥주)과 전통주는 지위가 다르다 — 수왕사 선례 참조.
"""
def eok(v): return v/1e8

# ══════════ 법적 근거 재정리 ══════════
LEGAL = """
[기존 배제 판정의 한계]
  E-0612 '브루펍·주류 F&B [배제]' — 근거등급 C, 출처는 Church Brew Works(맥주 브루펍).
  → 맥주 양조장을 배제한 판정이지 '전통주'를 직접 판정한 것이 아니다.

[전통주가 다른 이유 — 수왕사 송화백일주]
  · 전북 완주 수왕사 · 대한민국에서 유일하게 '승려가 빚는 술'
  · 제조자 = 수왕사 주지 벽암 스님(조영귀)
  · 1994년 농식품부 식품명인 1호 지정
  · 2013년 전북 무형문화재 6-4호 지정
  · 곡차 전통: 해발 600m 수도승이 고산병·혈액순환 장애 예방 목적으로 주 1~2모금
  → 사찰의 술 제조·음용은 국가가 무형문화재로 인정한 전통문화다.

[적용 가능한 조문]
  · 시행령 제7조 제2호 '전통문화 관련 상품의 판매'(E-0107) — 무형문화재 전통주는 명백한 전통문화
  · 시행령 제7조 '사찰에서 생산하는 토산품'(E-0151·Tier1) — 수왕사 선례 존재
  → 판매·페어링은 Tier2(해석 대상)이나 근거가 두껍다. 제조는 별도 면허 문제.

[남는 리스크 — 법이 아니라 종단·여론]
  · 불음주계 vs 곡차 문화의 내부 해석
  · '사찰에서 술을 판다'는 프레임 — 불신·상업화 토픽 2.2%(E-0206)를 직접 자극
  · 주세법상 주류판매업 면허(판매) / 주류제조면허(제조)는 별개 절차
"""

# ══════════ 벤치마크 ══════════
BM = {
 "온지음 페어링": dict(점심=80_000, 저녁=120_000, 코스대비="약 40%"),
 "전통주 빚기 클래스": dict(단체=45_000, 이화주=60_000, 정원="16~20명",
                       특징="발효 7~14일 후 수령 → 재방문 장치"),
 "전통주 시장": dict(출고액="전년 대비 −6.9%(주춤)",
                 추세="프리미엄은 2030 중심 성장 · 고가/저가 양극화"),
}

# ══════════ v4.0 다이닝 (온지음형 기반 · 페어링 중심) ══════════
SEATS=[30,40,45]
TIMES=[2.0,2.0,2.5]
OCC=[0.60,0.75,0.80]
DAYS=[260,260,270]
LUNCH_SHARE=[0.45,0.45,0.42]
LUNCH_P=[85_000,90_000,95_000]
DINNER_P=[140_000,150_000,160_000]
# ★ 페어링 중심 — 부착률과 단가를 대폭 상향 (v3.0 B안: 35,000 × 45%)
PAIR_L=[40_000,45_000,50_000]     # 점심 페어링 (온지음 80,000의 50~63%)
PAIR_D=[65_000,75_000,85_000]     # 저녁 페어링 (온지음 120,000의 54~71%)
PAIR_RATE=[0.60,0.75,0.85]        # 페어링이 기본 구성이므로 부착률 높음

def turn(i): return TIMES[i]*OCC[i]
def covers(i): return SEATS[i]*turn(i)
def blend_food(i): return LUNCH_SHARE[i]*LUNCH_P[i]+(1-LUNCH_SHARE[i])*DINNER_P[i]
def blend_pair(i): return (LUNCH_SHARE[i]*PAIR_L[i]+(1-LUNCH_SHARE[i])*PAIR_D[i])*PAIR_RATE[i]
def rev_food(i): return covers(i)*blend_food(i)*DAYS[i]
def rev_pair(i): return covers(i)*blend_pair(i)*DAYS[i]

# ══════════ 체험 상품 (신설) ══════════
# ① 전통주 빚기 클래스 — 발효 7~14일 후 수령 = 재방문 강제
BREW_P=[60_000,75_000,90_000]; BREW_CAP=[14,16,18]
BREW_UTIL=[0.60,0.75,0.85]; BREW_SESS=[100,150,200]   # 연 회차
# ② 페어링 클래스 · 곡차 문화 강의 + 시음
TAST_P=[45_000,55_000,65_000]; TAST_CAP=[16,20,20]
TAST_UTIL=[0.55,0.70,0.80]; TAST_SESS=[80,120,160]
# ③ 병 판매 (봉은사 큐레이션 전통주 · 사찰 토산품)
BOTTLE_P=[35_000,45_000,55_000]
BOTTLE_CONV=[0.12,0.18,0.25]      # 다이닝+체험 참가자 대비 구매전환
def rev_brew(i): return BREW_P[i]*BREW_CAP[i]*BREW_UTIL[i]*BREW_SESS[i]
def rev_tast(i): return TAST_P[i]*TAST_CAP[i]*TAST_UTIL[i]*TAST_SESS[i]
def exp_heads(i): return BREW_CAP[i]*BREW_UTIL[i]*BREW_SESS[i]+TAST_CAP[i]*TAST_UTIL[i]*TAST_SESS[i]
def rev_bottle(i): return (covers(i)*DAYS[i]+exp_heads(i))*BOTTLE_CONV[i]*BOTTLE_P[i]

# ══════════ 전통다원 ══════════
T_SEATS=[30,35,40]; T_PRICE=[22_000,26_000,30_000]
T_TURN=[1.3,1.6,1.8]; T_DAYS=[300,313,330]
def rev_tea(i): return T_SEATS[i]*T_PRICE[i]*T_TURN[i]*T_DAYS[i]

def tot(i): return rev_food(i)+rev_pair(i)+rev_brew(i)+rev_tast(i)+rev_bottle(i)+rev_tea(i)

# ══════════ 면적 ══════════
SQM_SEAT=5.0
def hall(i): return SEATS[i]*SQM_SEAT
def kitchen(i): return hall(i)/3
BREW_LAB=[60,80,100]      # 양조 실습실 + 발효 저장고
def tea_area(i): return T_SEATS[i]*3.0*1.25
def area(i): return hall(i)+kitchen(i)+BREW_LAB[i]+tea_area(i)

# ══════════ 원가 ══════════
FOOD_RATE=[0.31,0.30,0.29]
PAIR_COGS=[0.42,0.40,0.38]        # 주류 매입원가 — 식재료보다 높음
BREW_COGS=[0.22,0.20,0.18]        # 재료비(쌀·누룩) 낮음
BOTTLE_COGS=[0.55,0.52,0.50]      # 위탁제조·매입
CPS=[3.2,3.5,3.8]                 # 다이닝 커버·인
EXP_STAFF=[2,3,3]                 # 체험 전담(양조 강사·소믈리에)
WAGE=3.5e7
def staff(i): return covers(i)/CPS[i]+T_SEATS[i]/20+EXP_STAFF[i]
def labor(i): return staff(i)*WAGE
def cogs(i):
    return (rev_food(i)*FOOD_RATE[i]+rev_pair(i)*PAIR_COGS[i]
            +(rev_brew(i)+rev_tast(i))*BREW_COGS[i]
            +rev_bottle(i)*BOTTLE_COGS[i]+rev_tea(i)*0.33)
OTHER=[0.08,0.07,0.07]            # 수도광열+관리
MKT=[0.03,0.02,0.015]
CAPEX_UNIT=[780,720,660]          # 양조 실습실·저장고 포함으로 상향
def capex(i): return area(i)/3.3058*CAPEX_UNIT[i]*1e4
def deprec(i): return capex(i)/10
def op(i): return tot(i)-cogs(i)-labor(i)-tot(i)*(OTHER[i]+MKT[i])-deprec(i)
def tax(i):
    p=op(i)
    if p<=0: return 0
    b=p*0.5
    return b*0.09 if b<=2e8 else 2e8*0.09+(b-2e8)*0.19

V3B=dict(tot=20.2, op=5.5, area=312, capex=7.1, opsqm=177)

print(LEGAL)
print("="*106)
print("v4.0 — 전통주 페어링 중심 · 체험 상품화")
print("="*106)
print(f"{'':<26}{'보수':>15}{'기준':>15}{'낙관':>15}")
print("-"*106)
for lab,v in [
 ("좌석 · 타임 · 점유율",[f"{SEATS[i]}석 {TIMES[i]:.1f}×{OCC[i]:.0%}" for i in range(3)]),
 ("일 커버수",[f"{covers(i):.0f}명" for i in range(3)]),
 ("점심 코스 / 페어링",[f"{LUNCH_P[i]//1000}만 / {PAIR_L[i]//1000}만" for i in range(3)]),
 ("저녁 코스 / 페어링",[f"{DINNER_P[i]//1000}만 / {PAIR_D[i]//1000}만" for i in range(3)]),
 ("페어링 부착률",[f"{PAIR_RATE[i]:.0%}" for i in range(3)]),
 ("→ 실질 객단가(식+주)",[f"{blend_food(i)+blend_pair(i):,.0f}원" for i in range(3)]),
 ("  온지음 250,000 대비",[f"{(blend_food(i)+blend_pair(i))/250_000:.0%}" for i in range(3)]),
 ("  v3.0 B안 대비",[f"{(blend_food(i)+blend_pair(i))/(123_000+35_000*0.45):.0%}" for i in range(3)]),
]:
    print(f"{lab:<26}"+"".join(f"{x:>15}" for x in v))
print("-"*106)
print("매출 구성")
for lab,f in [("다이닝 (음식)",rev_food),("전통주 페어링",rev_pair),
              ("전통주 빚기 클래스",rev_brew),("시음·페어링 클래스",rev_tast),
              ("병 판매(토산품)",rev_bottle),("전통다원",rev_tea)]:
    print(f"{'  '+lab:<26}"+"".join(f"{eok(f(i)):>14.1f}억" for i in range(3)))
print(f"{'합계':<26}"+"".join(f"{eok(tot(i)):>14.1f}억" for i in range(3)))
print(f"{'  주류 관련 비중':<26}"+"".join(f"{(rev_pair(i)+rev_brew(i)+rev_tast(i)+rev_bottle(i))/tot(i):>15.0%}" for i in range(3)))
print(f"{'  v3.0 B안 대비':<26}"+"".join(f"{eok(tot(i))/V3B['tot']-1:>+15.0%}" for i in range(3)))
print()
print("체험 참가자 수(연간)")
print(f"{'  양조 클래스':<26}"+"".join(f"{BREW_CAP[i]*BREW_UTIL[i]*BREW_SESS[i]:>14.0f}명" for i in range(3)))
print(f"{'  시음 클래스':<26}"+"".join(f"{TAST_CAP[i]*TAST_UTIL[i]*TAST_SESS[i]:>14.0f}명" for i in range(3)))
print(f"{'  체험 합계':<26}"+"".join(f"{exp_heads(i):>14.0f}명" for i in range(3)))
print(f"{'  다이닝 대비':<26}"+"".join(f"{exp_heads(i)/(covers(i)*DAYS[i]):>15.0%}" for i in range(3)))
print()
print("="*106)
print("손익")
print("="*106)
print(f"{'':<26}{'보수':>15}{'기준':>15}{'낙관':>15}")
print("-"*106)
print(f"{'매출액':<26}"+"".join(f"{eok(tot(i)):>14.1f}억" for i in range(3)))
print(f"{'  매출원가':<26}"+"".join(f"{-eok(cogs(i)):>14.1f}억" for i in range(3)))
print(f"{'    원가율':<26}"+"".join(f"{cogs(i)/tot(i):>15.0%}" for i in range(3)))
print(f"{'  인건비':<26}"+"".join(f"{-eok(labor(i)):>14.1f}억" for i in range(3)))
print(f"{'    인원':<26}"+"".join(f"{staff(i):>14.0f}명" for i in range(3)))
print(f"{'  기타·마케팅':<26}"+"".join(f"{-eok(tot(i)*(OTHER[i]+MKT[i])):>14.1f}억" for i in range(3)))
print(f"{'  감가상각':<26}"+"".join(f"{-eok(deprec(i)):>14.1f}억" for i in range(3)))
print("-"*106)
print(f"{'영업이익':<26}"+"".join(f"{eok(op(i)):>+14.1f}억" for i in range(3)))
print(f"{'  영업이익률':<26}"+"".join(f"{op(i)/tot(i):>+15.1%}" for i in range(3)))
print(f"{'  v3.0 B안 대비':<26}"+"".join(f"{eok(op(i))-V3B['op']:>+14.1f}억" for i in range(3)))
print(f"{'세후이익':<26}"+"".join(f"{eok(op(i)-tax(i)):>+14.1f}억" for i in range(3)))
print("-"*106)
print(f"{'면적':<26}"+"".join(f"{area(i):>14.0f}㎡" for i in range(3)))
print(f"{'  양조 실습실·저장고':<26}"+"".join(f"{BREW_LAB[i]:>14.0f}㎡" for i in range(3)))
print(f"{'  배정 1,000㎡ 대비':<26}"+"".join(f"{area(i)-1000:>+14.0f}㎡" for i in range(3)))
print(f"{'CAPEX':<26}"+"".join(f"{eok(capex(i)):>14.1f}억" for i in range(3)))
print(f"{'회수기간':<26}"+"".join((f"{capex(i)/(op(i)-tax(i)):>14.1f}년" if op(i)>0 else f"{'불가':>15}") for i in range(3)))
print(f"{'★ ㎡당 영업이익':<26}"+"".join(f"{op(i)/area(i)/1e4:>13.0f}만원" for i in range(3)))
print(f"{'  v3.0 B안 177만원 대비':<26}"+"".join(f"{(op(i)/area(i)/1e4)/V3B['opsqm']-1:>+15.0%}" for i in range(3)))
