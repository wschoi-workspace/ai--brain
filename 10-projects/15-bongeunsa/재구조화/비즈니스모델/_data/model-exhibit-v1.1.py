# -*- coding: utf-8 -*-
"""RL-01 전시 비즈니스 모델 v1.0
구조: 상설(무료·집객) + 기획전(유료·수익) + 시즌 미디어아트(공모·정부예산)
"""
def eok(v): return v/1e8
CASE=["보수","기준","낙관"]

BENCH = """
[벤치마크 실측]
◆ 마이아트뮤지엄 — 봉은사 도보권 직접 경쟁자
  · 서울 강남구 테헤란로 518(대치동) 지하1층 · 삼성역 인근 · 2019.10 개관
  · 성인 25,000 / 청소년 18,000 / 어린이 16,000원 (단체 성인 22,000)
  · 개관 이래 블록버스터 14회 · 누적 120만명 → 회당 약 8.6만명 · 연 약 20만명
  · 10:00~19:40 (입장마감 19:00)
◆ 피크닉 piknic — 회기 구조 참고
  · 2018 개관 · 전시 회기 4~6개월 · 연 2~3회
  · 전시 입장료 + 카페·레스토랑·디자인스토어 + 대관 병행
◆ 국가유산 미디어아트 — 통도사 건의 실체
  · 국가유산청 주최 · 국가유산진흥원 주관 · 2021년부터
  · 매년 공모로 개최지 선정 · 2024년 7개 지역 118만명 (회당 약 17만명)
  · 야간 개방형 · 통도사는 10개 전각 벽화 30점을 디지털 영상 10점으로 재현
  · 19:00~21:00 · 메인 영상 1일 2회 · 약 1.5개월 기간 한정
◆ 블록버스터 전시의 구조
  · 외부 기획사가 미술관을 사실상 대관하는 형식
  · 초기비용 수십억 — 공공 미술관은 감당 못 해 기획사 계획에 종속
◆ 대조군
  · 별마당 도서관: 무료 · 개장 10개월 코엑스몰 1,700만명 (E-0494)
  · 체스터 대성당: 4파운드 도입 → 방문객 30~40% 감소 → 폐지 (E-0473)
  · teamLab 도지: 평일 1,600엔 / 주말 2,200엔 (E-0459)
  · 고다이지: 야간 800엔 · 연 3회 시즌 (E-0460)

[봉은사 보유 자산]
  · 판전 경판 3,479판 (E-0508)
  · 보물 — 2점 또는 21점으로 문서 간 불일치 (E-0509)
  · 무형문화재 2종: 수륙재(국가 제125호, 2013) · 생전예수재(서울시, 2019) (E-0512)
  · 불교중앙박물관이 전국 성보박물관 34곳 지원·감독 → 특별전 유치 경로 (E-0429)
  · 8,868㎡ · 무주 대공간 · 6~8m 통층 (E-0502)

[법적 지위 — 가장 안전]
  · 전시장·박물관은 건축법·전통사찰법·도시공원법 3법을 모두 통과하는 유일 용도 (E-0135)
  · G2 9건 중 8건이 Tier1 (해석 불요)

[결정적 약점]
  · 수요원자 54개에 '전시 관람권을 사겠다' 0건 — 가장 가까운 수요는 해설·도록 (E-1060)
"""

# ══════ ① 상설전 — 무료 집객 엔진 ══════
# 봉은사 역사관 + 성보 상설 + 판전 경판 아카이브
CV=[110_000,255_000,525_634]        # 문화센터 연간 방문객
PERM_RATE=[0.55,0.65,0.72]          # 상설전 관람률 (무료라 높음)
def perm_visitors(i): return CV[i]*PERM_RATE[i]
PERM_PRICE=[0,0,0]                  # 무료
def rev_perm(i): return perm_visitors(i)*PERM_PRICE[i]

# ══════ ② 기획전 — 유료 · 회기제 ══════
SHOWS=[2,3,3]                        # 연 개최 회수
PER_SHOW=[15_000,30_000,50_000]      # 회당 관람객 — 마이아트뮤지엄 회당 8.6만의 17/35/58%
TICKET=[12_000,15_000,18_000]        # 마이아트뮤지엄 25,000원의 48~72%
DISCOUNT=[0.82,0.85,0.87]            # 단체·청소년·할인 반영 실수령률
def show_visitors(i): return SHOWS[i]*PER_SHOW[i]
def rev_show(i): return show_visitors(i)*TICKET[i]*DISCOUNT[i]

# ══════ ③ 시즌 미디어아트 — 야간 ══════
# 자체 개최분(유료) + 국가유산 미디어아트 공모 선정 시 정부예산
MEDIA_DAYS=[30,45,60]
MEDIA_PER_DAY=[500,900,1_500]
MEDIA_PRICE=[8_000,10_000,12_000]    # 고다이지 800엔 · teamLab 1,600~2,200엔 참조
def media_visitors(i): return MEDIA_DAYS[i]*MEDIA_PER_DAY[i]
def rev_media(i): return media_visitors(i)*MEDIA_PRICE[i]
# 국가유산 미디어아트 공모 선정 확률은 모델에 넣지 않고 별도 표기
GRANT=[0,0,0]                        # 보수적으로 0 처리

# ══════ ④ 부대 — 도슨트·도록 ══════
# ※ 굿즈·도록 매출은 RL-04 리테일로 귀속 (이중계상 방지). 여기는 도슨트만.
DOCENT_RATE=[0.06,0.09,0.12]         # 유료 관람객 중 도슨트 이용률
DOCENT_P=[8_000,10_000,12_000]
def rev_docent(i): return (show_visitors(i)+media_visitors(i))*DOCENT_RATE[i]*DOCENT_P[i]

# ══════ ⑤ 전시 대관 — 외부 기획사 유치 ══════
# 블록버스터는 기획사가 대관하는 구조 → 우리가 빌려주는 쪽
RENT_SHOWS=[0,1,2]                   # 연 유치 회수
RENT_FEE=[0,150_000_000,180_000_000] # 회당 대관료
def rev_rent(i): return RENT_SHOWS[i]*RENT_FEE[i]

def tot(i): return rev_perm(i)+rev_show(i)+rev_media(i)+rev_docent(i)+rev_rent(i)

# ══════ 면적 ══════
A_PERM=[450,600,700]      # 상설전시실 + 역사관
A_SPECIAL=[600,900,1_100] # 기획전시실
A_BACK=[250,350,400]      # 수장고·준비실·하역
def area(i): return A_PERM[i]+A_SPECIAL[i]+A_BACK[i]

# ══════ 원가 ══════
# 전시는 회기제라 '제작비'가 F&B의 식재료비에 해당
SHOW_COST=[180_000_000,260_000_000,340_000_000]  # 회당 기획전 제작비(자체기획 기준)
MEDIA_COST=[250_000_000,380_000_000,500_000_000] # 시즌 미디어아트 제작비(콘텐츠+장비)
def cost_content(i): return SHOWS[i]*SHOW_COST[i]+MEDIA_COST[i]
STAFF=[6,9,12]            # 큐레이터·에듀케이터·안내·기술
WAGE=3.5e7
def labor(i): return STAFF[i]*WAGE
OTHER=[0.09,0.08,0.07]    # 수도광열·보험·운송·보안
MKT=[0.10,0.09,0.08]      # 전시는 마케팅비가 F&B보다 크다
CAPEX_U=[420,380,340]     # 만원/평 — 전시장은 마감보다 설비(조명·항온항습·보안)
def capex(i): return area(i)/3.3058*CAPEX_U[i]*1e4
def dep(i): return capex(i)/10
def op(i): return tot(i)-cost_content(i)-labor(i)-tot(i)*(OTHER[i]+MKT[i])-dep(i)

print(BENCH)
print("="*104)
print("RL-01 전시 — 3층 구조")
print("="*104)
print(f"{'':<28}{'보수':>16}{'기준':>16}{'낙관':>16}")
print("-"*104)
rows=[
 ("① 상설전(무료)",[f"{perm_visitors(i):,.0f}명" for i in range(3)]),
 ("  CV 대비 관람률",[f"{PERM_RATE[i]:.0%}" for i in range(3)]),
 ("② 기획전 회수",[f"{SHOWS[i]}회" for i in range(3)]),
 ("  회당 관람객",[f"{PER_SHOW[i]:,}명" for i in range(3)]),
 ("  연 관람객",[f"{show_visitors(i):,.0f}명" for i in range(3)]),
 ("  티켓(실수령)",[f"{TICKET[i]*DISCOUNT[i]:,.0f}원" for i in range(3)]),
 ("  마이아트 25,000 대비",[f"{TICKET[i]/25_000:.0%}" for i in range(3)]),
 ("③ 미디어아트 일수",[f"{MEDIA_DAYS[i]}일" for i in range(3)]),
 ("  일 관람객 / 단가",[f"{MEDIA_PER_DAY[i]:,}명 / {MEDIA_PRICE[i]:,}원" for i in range(3)]),
 ("  연 관람객",[f"{media_visitors(i):,.0f}명" for i in range(3)]),
 ("⑤ 전시 대관 유치",[f"{RENT_SHOWS[i]}회" for i in range(3)]),
]
for lab,v in rows: print(f"{lab:<28}"+"".join(f"{x:>16}" for x in v))
print("-"*104)
print("매출")
for lab,f in [("  상설전(무료)",rev_perm),("  기획전 입장",rev_show),
              ("  시즌 미디어아트",rev_media),("  도슨트",rev_docent),("  전시 대관",rev_rent)]:
    print(f"{lab:<28}"+"".join(f"{eok(f(i)):>15.1f}억" for i in range(3)))
print(f"{'  합계':<28}"+"".join(f"{eok(tot(i)):>15.1f}억" for i in range(3)))
print()
print(f"{'총 관람객(중복 포함)':<28}"+"".join(f"{perm_visitors(i)+show_visitors(i)+media_visitors(i):>15,.0f}명" for i in range(3)))
print(f"{'  유료 관람객':<28}"+"".join(f"{show_visitors(i)+media_visitors(i):>15,.0f}명" for i in range(3)))
print(f"{'  유료 비중':<28}"+"".join(f"{(show_visitors(i)+media_visitors(i))/(perm_visitors(i)+show_visitors(i)+media_visitors(i)):>16.0%}" for i in range(3)))
print()
print("="*104)
print("손익")
print("="*104)
print(f"{'':<28}{'보수':>16}{'기준':>16}{'낙관':>16}")
print("-"*104)
print(f"{'매출액':<28}"+"".join(f"{eok(tot(i)):>15.1f}억" for i in range(3)))
print(f"{'  전시 제작비':<28}"+"".join(f"{-eok(cost_content(i)):>15.1f}억" for i in range(3)))
print(f"{'    기획전 회당':<28}"+"".join(f"{eok(SHOW_COST[i]):>15.1f}억" for i in range(3)))
print(f"{'    미디어아트':<28}"+"".join(f"{eok(MEDIA_COST[i]):>15.1f}억" for i in range(3)))
print(f"{'  인건비':<28}"+"".join(f"{-eok(labor(i)):>15.1f}억" for i in range(3)))
print(f"{'    인원':<28}"+"".join(f"{STAFF[i]:>15}명" for i in range(3)))
print(f"{'  기타·마케팅':<28}"+"".join(f"{-eok(tot(i)*(OTHER[i]+MKT[i])):>15.1f}억" for i in range(3)))
print(f"{'  감가상각':<28}"+"".join(f"{-eok(dep(i)):>15.1f}억" for i in range(3)))
print("-"*104)
print(f"{'영업이익':<28}"+"".join(f"{eok(op(i)):>+15.1f}억" for i in range(3)))
print(f"{'  영업이익률':<28}"+"".join(f"{op(i)/tot(i):>+16.1%}" for i in range(3)))
print("-"*104)
print(f"{'면적':<28}"+"".join(f"{area(i):>15,.0f}㎡" for i in range(3)))
print(f"{'  상설/기획/백룸':<28}"+"".join(f"{A_PERM[i]}/{A_SPECIAL[i]}/{A_BACK[i]}"+' '*4 for i in range(3)))
print(f"{'  배정 2,000㎡ 대비':<28}"+"".join(f"{area(i)-2000:>+15,.0f}㎡" for i in range(3)))
print(f"{'CAPEX':<28}"+"".join(f"{eok(capex(i)):>15.1f}억" for i in range(3)))
print(f"{'회수기간':<28}"+"".join((f"{capex(i)/op(i):>15.1f}년" if op(i)>0 else f"{'회수불가':>16}") for i in range(3)))
print(f"{'★ ㎡당 영업이익':<28}"+"".join(f"{op(i)/area(i)/1e4:>14.0f}만원" for i in range(3)))
print()
print("  ※ 비교 — 다이닝 5축 ㎡당 영업이익 206만원 / 대관 32~39만원")
print()
print("="*104)
print("92억 모델(E-0526)과의 대조")
print("="*104)
print(f"  92억 모델 전시 입장료: 21.0억 = 15,000원 × 400명 × 350일 = 14만명")
print(f"  v1.0 기준안 유료 관람객: {show_visitors(1)+media_visitors(1):,.0f}명 · 매출 {eok(rev_show(1)+rev_media(1)):.1f}억")
print(f"  → 관람객은 {(show_visitors(1)+media_visitors(1))/140_000:.0%}, 매출은 {(rev_show(1)+rev_media(1))/21e8:.0%}")
print(f"  마이아트뮤지엄 연 20만명(성인 25,000원) 대비 유료 관람객 {(show_visitors(1)+media_visitors(1))/200_000:.0%}")
