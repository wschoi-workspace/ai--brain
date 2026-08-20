# -*- coding: utf-8 -*-
"""RL-10 멤버십 비즈니스 모델 v1.0
핵심: 보시 트랙과 이용 트랙을 분리한다. 그리고 갱신율로 5개년을 본다.
"""
def eok(v): return v/1e8
CASE=["보수","기준","낙관"]

BENCH="""
[국내 문화기관 B2C 멤버십 — 실측]
◆ 리움미술관     프렌즈 10만(1인) / 패밀리 30만(4인) / 패밀리50 50만(8인)
◆ 국립현대미술관  친구 무료 / 가족 7만 / 가족+ 10만 · 재가입 20% 할인
  → B2C 문화 멤버십의 실제 밴드는 7만~50만원. 100만원 이상은 이 시장에 없다.
[B2B·임원 — 실측]
◆ 한국능률협회(KMA)  회장단 1,700만 / 이사단 1,000만 / 정회원 490만
  → 수영장도 사우나도 없이 이 가격. 시설이 아니라 대상이 가격을 정한다 (E-1041)
◆ 고려대 AMP  6개월 1,200만(실질 1,900만) · 정원 50~60명 · 연 2회
  → 기수제는 멤버십보다 이탈 관리가 쉽고 동문 네트워크가 자동 형성 (E-1047)
[타겟 — 하나 웰스리포트]
◆ 영리치(40대 이하): '사회적 위상·인맥' 55.7% · 회원권 보유율 16.8% (E-1045)
◆ 올드리치: '문화적 소양' 54.3% · 회원권 보유율 23.3% (E-1046)
  → 이들이 사는 것은 시설이 아니라 관계와 소양이다
[법적·정서 제약]
◆ 보증금 금지 — 디아드 청담 보증금 10억 모델로 목표 500명 중 100명(20%) 모집 후 공매.
  대법원 2013다85417은 입회금 동시 반환 청구 시 수백억 리스크를 인정 (E-1048)
◆ 과세 급소 — 강남구청 2012년 '교인 외 일반 주민도 이용 가능한가' 기준으로
  10곳 이상에 5억여원 추징 (E-1049)
◆ 봉은사는 현재 타이치명상·선명상을 0원 무료 공익으로 운영 중 (E-1049)
  → 유료 멤버십은 과세 판정과 내부 정서 양쪽에 동시에 걸린다
◆ 4원칙 ③ 투명성 — 보시와 이용료를 명확히 구분·공개 (E-0243)
"""

# ══════ 모수 ══════
CV=[110_000,255_000,525_634]        # 문화센터 연간 방문객
WALK=112_349                         # 도보권 직장인 (E-1021)
DEVOTEE=[50_000,70_000,100_000]      # 봉은사 등록 신도 (E-0339 · 5~10만 추정)

# ══════ ① 이용 트랙 — B2C 문화 멤버십 ══════
# 리움 프렌즈 10만 ~ 패밀리 30만 밴드. 봉은사는 브랜드가 리움만 못하므로 중하단.
CUL_FEE=[120_000,180_000,250_000]
CUL_CONV=[0.0012,0.0028,0.005]       # CV 대비 가입 전환 — 미술관 멤버십 통상 0.1~0.5%
def cul_new(i): return CV[i]*CUL_CONV[i]

# ══════ ② 이용 트랙 — 웰니스 월정액 ══════
# 도보권 직장인 대상. 월정액 → 연환산
WEL_M=[70_000,95_000,120_000]
WEL_PEN=[0.0020,0.0040,0.0065]       # 도보권 침투율 — 현행 무료 프로그램에서의 유료 전환 저항 반영
def wel_new(i): return WALK*WEL_PEN[i]

# ══════ ③ 이용 트랙 — 법인 멤버십 ══════
# KMA 정회원 490만 밴드. 권고 500~1,000만
CORP_FEE=[5_000_000,7_000_000,10_000_000]
CORP_N=[6,14,25]
# ══════ ④ 이용 트랙 — 임원 기수제 ══════
# AMP형. 기수제는 '갱신'이 아니라 '수료' → 이탈 개념이 없다
EXE_FEE=[5_000_000,6_500_000,8_000_000]
EXE_CAP=[16,20,24]; EXE_CLASS=[1,2,2]
# ══════ ⑤ 관계 트랙 — 신도 후원 등급제 (보시 기반) ══════
# ※ 이용 대가가 아니라 기부. 과세·정서 판정이 다르다.
DON_RATE=[0.008,0.014,0.022]         # 신도 중 등급 후원 참여율
DON_AVG=[350_000,500_000,700_000]    # 연 평균 후원액
# ══════ ⑥ 온라인 구독 ══════
SUB_M=[9_900,14_900,19_900]
SUB_N=[400,1_100,2_400]

def rev_cul(i,members): return members*CUL_FEE[i]
def rev_wel(i,members): return members*WEL_M[i]*12
def rev_corp(i): return CORP_FEE[i]*CORP_N[i]
def rev_exe(i): return EXE_FEE[i]*EXE_CAP[i]*EXE_CLASS[i]
def rev_don(i): return DEVOTEE[i]*DON_RATE[i]*DON_AVG[i]
def rev_sub(i): return SUB_M[i]*12*SUB_N[i]

# ══════ 갱신율 — 이 라인의 핵심 미지수 ══════
# 국내 종교시설 멤버십 사례 0건. 구독 서비스 일반 벤치마크로 대체.
RENEW=[0.55,0.65,0.72]

# ══════ 원가 ══════
STAFF=[2,3,5]; WAGE=3.5e7            # 회원관리·CRM·영업
SERVICE_COST=[0.30,0.26,0.22]        # 회원 혜택 제공 원가(무료입장·할인·라운지 등)
MKT=[0.12,0.10,0.08]                 # 신규 모집 비용
CRM_CAPEX=[150_000_000,220_000_000,300_000_000]   # 예약·CRM 시스템

def year1(i):
    cul=cul_new(i); wel=wel_new(i)
    tot=(rev_cul(i,cul)+rev_wel(i,wel)+rev_corp(i)+rev_exe(i)+rev_don(i)+rev_sub(i))
    return tot,cul,wel

def op_of(i,tot):
    labor=STAFF[i]*WAGE
    dep=CRM_CAPEX[i]/5
    return tot*(1-SERVICE_COST[i]-MKT[i])-labor-dep

print(BENCH)
print("="*106)
print("RL-10 멤버십 — 두 트랙 분리 설계")
print("="*106)
print(f"{'':<30}{'보수':>15}{'기준':>15}{'낙관':>15}")
print("-"*106)
for lab,v in [
 ("【이용 트랙 — 과세 영역】",["","",""]),
 ("① 문화 멤버십 연회비",[f"{CUL_FEE[i]:,}원" for i in range(3)]),
 ("   리움 10~50만 대비",[f"{CUL_FEE[i]/300_000:.0%}" for i in range(3)]),
 ("   가입자(CV 전환)",[f"{cul_new(i):,.0f}명" for i in range(3)]),
 ("② 웰니스 월정액",[f"{WEL_M[i]:,}원/월" for i in range(3)]),
 ("   가입자(도보권 침투)",[f"{wel_new(i):,.0f}명" for i in range(3)]),
 ("③ 법인 멤버십",[f"{CORP_FEE[i]//10000:,}만 × {CORP_N[i]}사" for i in range(3)]),
 ("④ 임원 기수제",[f"{EXE_FEE[i]//10000:,}만 × {EXE_CAP[i]}명 × {EXE_CLASS[i]}기" for i in range(3)]),
 ("⑥ 온라인 구독",[f"{SUB_M[i]:,}원 × {SUB_N[i]:,}명" for i in range(3)]),
 ("【관계 트랙 — 보시 영역】",["","",""]),
 ("⑤ 신도 후원 등급제",[f"{DON_AVG[i]//10000}만 × {DEVOTEE[i]*DON_RATE[i]:,.0f}명" for i in range(3)]),
]:
    print(f"{lab:<30}"+"".join(f"{x:>15}" for x in v))
print("-"*106)
print("1년차 매출")
for lab,f in [("  문화 멤버십",lambda i: rev_cul(i,cul_new(i))),
              ("  웰니스 월정액",lambda i: rev_wel(i,wel_new(i))),
              ("  법인 멤버십",rev_corp),("  임원 기수제",rev_exe),
              ("  온라인 구독",rev_sub),("  신도 후원(보시)",rev_don)]:
    print(f"{lab:<30}"+"".join(f"{eok(f(i)):>14.1f}억" for i in range(3)))
tot1=[year1(i)[0] for i in range(3)]
print(f"{'  합계':<30}"+"".join(f"{eok(tot1[i]):>14.1f}억" for i in range(3)))
print(f"{'   중 이용 트랙(과세)':<30}"+"".join(f"{eok(tot1[i]-rev_don(i)):>14.1f}억" for i in range(3)))
print(f"{'   중 관계 트랙(보시)':<30}"+"".join(f"{eok(rev_don(i)):>14.1f}억" for i in range(3)))
print()
print("="*106)
print("★ 5개년 — 갱신율이 이 라인의 전부입니다")
print("="*106)
print(f"  갱신율 가정: 보수 {RENEW[0]:.0%} · 기준 {RENEW[1]:.0%} · 낙관 {RENEW[2]:.0%}  (국내 종교시설 사례 0건 — 구독 일반 벤치마크)")
print()
for i,c in enumerate(CASE):
    print(f"[{c}]  신규 유입은 1년차와 동일하게 유지된다고 가정")
    print(f"{'':<10}{'1년차':>12}{'2년차':>12}{'3년차':>12}{'4년차':>12}{'5년차':>12}{'누적':>13}")
    cul_base=cul_new(i); wel_base=wel_new(i)
    cul_m=cul_base; wel_m=wel_base; sub_m=SUB_N[i]; corp_n=CORP_N[i]
    revs=[]
    for y in range(5):
        if y>0:
            cul_m=cul_m*RENEW[i]+cul_base
            wel_m=wel_m*RENEW[i]+wel_base
            sub_m=sub_m*RENEW[i]+SUB_N[i]
            corp_n=min(corp_n*0.85+CORP_N[i]*0.5, CORP_N[i]*2.2)
        r=(cul_m*CUL_FEE[i]+wel_m*WEL_M[i]*12+corp_n*CORP_FEE[i]
           +rev_exe(i)+sub_m*SUB_M[i]*12+rev_don(i))
        revs.append(r)
    print(f"{'  매출':<10}"+"".join(f"{eok(r):>11.1f}억" for r in revs)+f"{eok(sum(revs)):>12.1f}억")
    ops=[op_of(i,r) for r in revs]
    print(f"{'  영업이익':<10}"+"".join(f"{eok(o):>+11.1f}억" for o in ops)+f"{eok(sum(ops)):>+12.1f}억")
    print(f"{'  회원수':<10}"+"".join(f"{cul_m if False else 0:>11}" for _ in range(0))+
          f"  문화 {cul_m:,.0f}명 · 웰니스 {wel_m:,.0f}명 · 구독 {sub_m:,.0f}명 (5년차)")
    print()
print("="*106)
print("갱신율 민감도 — 5년 누적 영업이익 (기준안 기준)")
print("="*106)
i=1
print(f"{'갱신율':<12}{'5년 누적 매출':>18}{'5년 누적 영업이익':>20}{'5년차 문화회원':>18}")
print("-"*106)
for rn in [0.45,0.55,0.65,0.75,0.85]:
    cul_base=cul_new(i); wel_base=wel_new(i)
    cul_m=cul_base; wel_m=wel_base; sub_m=SUB_N[i]; corp_n=CORP_N[i]
    tr=0; to=0
    for y in range(5):
        if y>0:
            cul_m=cul_m*rn+cul_base; wel_m=wel_m*rn+wel_base; sub_m=sub_m*rn+SUB_N[i]
            corp_n=min(corp_n*0.85+CORP_N[i]*0.5, CORP_N[i]*2.2)
        r=(cul_m*CUL_FEE[i]+wel_m*WEL_M[i]*12+corp_n*CORP_FEE[i]+rev_exe(i)+sub_m*SUB_M[i]*12+rev_don(i))
        tr+=r; to+=op_of(i,r)
    mark=" ←기준 가정" if abs(rn-0.65)<0.01 else ""
    print(f"{rn:<12.0%}{eok(tr):>17.1f}억{eok(to):>19.1f}억{cul_m:>16,.0f}명{mark}")
print("-"*106)
print("  ※ 갱신율 45%와 85% 사이에서 5년 누적 영업이익이 크게 갈립니다.")
print("     이 값은 국내에 벤치마크가 없어 개관 2년차가 되어야 알 수 있습니다.")
