# -*- coding: utf-8 -*-
"""행사 유치 수익모델 v1.0 — 대관이냐 수수료 공유냐

질문(2026-08-18 대표): 불교박람회 등 행사를 대관 또는 매출 수수료 공유 모델로 수익화할 수 있는가.

출발점 — 대관은 천장이 낮다.
  E-1080  대관 단독으로 기준선 30억 불가 (1층 6,158㎡ 365일 100% 가동해도 25.8억)
  00H     대관 전용면적 0으로 재편 · 기획전 회기 사이에 2,000㎡를 돌려 연 2.8억
  ★그런데 대공간 판매일에 여유 48일이 생겼다 (상한 152 − 대관 70 − B2B 34)

그 48일을 무엇으로 채우는가가 이 검토의 대상이다.
"""
def eok(v): return v/1e8

BASIS = """
[불교박람회 — 실측]
◆ E-0826(B) 2026 서울국제불교박람회 · 조계종 총무원 주최 · 불교신문사 주관
            코엑스 B홀 4/2~5(4일) · 관람객 25만명(역대 최대, 전년 20만)
            2030세대 73% · 무종교 48% · ★2027년 전시장 2배 확대 계획
◆ E-0304(B) 2024년 참가 업체 294개 · 부스 435개 · 관람객 10만(전년 3배) · MZ 80%
◆ 입장료(2026 공식) 현장 1인 10,000원 / 할인예매 1일권 5,000원 / 사전등록 4일 무료
◆ E-0703(B)/E-0825(B) 조계종 문화상품 공모전 수상작이 2027 박람회로 연계
◆ E-0220(A) '문화 접점이면 무종교 청년이 온다'를 실증한 행사

[봉은사의 조건]
◆ 코엑스 도보권 — 봉은사 방문 외국인의 61.2%가 코엑스몰 동반 방문 (E-1043 B · Lift 3.30배)
◆ 00H 재편 후 대공간 = 기획전 트랙 2,000㎡ (A 1,200 + B 800) · 전용 대관홀 0㎡
◆ 대공간 판매일 상한 152일 (SETEC 실측 41.7% · E-1083 A)
   └ 대관 70일 + RL-07 B2B 34일 = 104일 → ★여유 48일
◆ 주차 269대 (법난기념관 지하 · E-1066 A)
◆ 연 방문객 120만 (5차 리포트 삼각검증 확정치)

[대관 단가 — 천장]
◆ E-1079(A) 코엑스 전시장 3,202~3,905원/㎡·일 · SETEC 1,150원 · 코엑스 로비 10,000원
◆ E-1082(B) 강남 전시공간 평당·일 단가 13.8배 격차 — 규모가 아니라 조건이 정한다
            고단가 조건 = 1층·정원·발렛·★음식물 반입·창고
◆ E-1080(A) 신설 시설이 코엑스 단가를 즉시 받을 근거는 없다

[리스크 — 이 라인의 진짜 제약]
◆ E-0833(B) ★종단 선점 리스크 — 총무원이 박람회를 직접 운영. 봉은사가 같은 층위를
            표방하면 역할 충돌 또는 하위 협력자로 흡수
◆ E-0233(A) 박람회가 이미 "불교 테마 잡화점"·"수행·성찰 부스가 소외된 주객전도" 비판을 받음
◆ E-0230(A) 상업성이 노골적일수록 비판 강도 급증 —
            웰니스화 환영 / 현대화 조건부 / ★직접 상업화(박람회 굿즈·관람료)는 비판
◆ E-1093(A) 운영모델 3안 중 '협업(공동사업·수익 배분)'이 이미 검토 대상에 있음
"""

# ═══════════════════════════════════════════════════════════════
# ① 같은 4일을 세 가지로 팔면
# ═══════════════════════════════════════════════════════════════
AREA = 2000          # 00H 기획전 트랙 (A 1,200 + B 800)
DAYS = 4             # 박람회 회기

# [모델 1] 단순 대관 — ㎡·일 단가
RATES = {"SETEC 1,150원": 1150, "중간 2,000원": 2000, "코엑스급 3,202원": 3202}
def rev_rental(rate): return AREA*DAYS*rate

# [모델 2] 부스 수수료 공유
BOOTH_N   = [40, 60, 85]                  # 봉은사관 부스 수 (2,000㎡ · 통로·체험공간 감안)
BOOTH_FEE = [1_500_000, 1_800_000, 2_200_000]   # 부스당 참가비 (국내 전시회 통상 150~250만)
SHARE     = [0.20, 0.25, 0.30]            # 봉은사 배분율
def rev_booth_share(i): return BOOTH_N[i]*BOOTH_FEE[i]*SHARE[i]
def booth_gross(i): return BOOTH_N[i]*BOOTH_FEE[i]

# [모델 3] 공동 주최 — 부스 + 입장 + 판매 수수료
VISITOR   = [15_000, 30_000, 50_000]      # 봉은사관 방문객 (박람회 25만의 6~20%)
PAID_RATE = [0.25, 0.30, 0.35]            # 유료 입장 비율 (사전등록 무료가 다수)
TICKET    = 7_500                          # 현장 1만 / 할인 5천의 중간
SALES_PV  = [12_000, 18_000, 25_000]      # 방문객 1인 구매액
SALES_FEE = [0.08, 0.10, 0.12]            # 판매 수수료율
def rev_ticket(i): return VISITOR[i]*PAID_RATE[i]*TICKET*0.5      # 입장 수입의 50% 배분
def rev_sales(i): return VISITOR[i]*SALES_PV[i]*SALES_FEE[i]
def rev_cohost(i): return rev_booth_share(i)+rev_ticket(i)+rev_sales(i)

# ═══════════════════════════════════════════════════════════════
# ② 봉은사 자체 매출 유발 — 행사가 데려온 사람이 쓰는 돈
# ═══════════════════════════════════════════════════════════════
# F&B·리테일은 각 라인에 귀속되므로 여기서는 '유발 매출'로만 표기 (중복 방지)
FB_RATE, FB_PV = 0.35, 22_000        # 방문객의 35%가 F&B 이용 · 객단가 22,000원
RT_RATE, RT_PV = 0.24, 38_000        # 편집샵 구매전환 24% · 객단가 38,000원 (5차 리포트)
def induced(i):
    return VISITOR[i]*FB_RATE*FB_PV + VISITOR[i]*RT_RATE*RT_PV

# ═══════════════════════════════════════════════════════════════
# ③ 여유 48일을 채우면 — 연간 행사 포트폴리오
# ═══════════════════════════════════════════════════════════════
FREE_DAYS = 48
EVENTS = {
 "불교박람회 봉은사관":   dict(days=4,  n=1, model="cohost", note="2027년 2배 확대 — 위성회장 수요"),
 "사찰음식 페어":        dict(days=3,  n=1, model="cohost", note="RL-03 다이닝·아카데미와 연계"),
 "명상·웰니스 페스티벌":  dict(days=3,  n=1, model="cohost", note="RL-06 명상 라인 연계"),
 "종단 행사·법회":       dict(days=6,  n=2, model="rental", note="총무원·교구 행사 유치"),
 "기업 컨퍼런스·MICE":   dict(days=2,  n=6, model="rental", note="코엑스 오버플로 · RL-07 연계"),
}
def portfolio_days(): return sum(v['days']*v['n'] for v in EVENTS.values())

if __name__ == "__main__":
    W=104
    print("═"*W); print("행사 유치 수익모델 v1.0 — 대관이냐 수수료 공유냐"); print("═"*W)

    print("\n[①] ★같은 4일 · 같은 2,000㎡를 세 가지로 팔면")
    print("─"*W)
    print("  모델 1 — 단순 대관 (방을 빌려준다)")
    for lab, r in RATES.items():
        print(f"    {lab:20}{eok(rev_rental(r)):>8.2f}억   {AREA:,}㎡ × {DAYS}일 × {r:,}원")
    print()
    print("  모델 2 — 부스 수수료 공유 (판을 같이 한다)")
    print(f"    {'':20}{'보수':>9}{'기준':>9}{'낙관':>9}")
    print(f"    {'봉은사관 부스':20}" + "".join(f"{BOOTH_N[i]:>8}개" for i in range(3)))
    print(f"    {'부스 총매출':20}" + "".join(f"{eok(booth_gross(i)):>8.2f}억" for i in range(3)))
    print(f"    {'배분율':20}" + "".join(f"{SHARE[i]*100:>8.0f}%" for i in range(3)))
    print(f"    {'★봉은사 수입':20}" + "".join(f"{eok(rev_booth_share(i)):>8.2f}억" for i in range(3)))
    print()
    print("  모델 3 — 공동 주최 (부스 + 입장 + 판매)")
    for lab, f in [("부스 수수료", rev_booth_share), ("입장 수입 배분", rev_ticket), ("판매 수수료", rev_sales)]:
        print(f"    {lab:20}" + "".join(f"{eok(f(i)):>8.2f}억" for i in range(3)))
    print(f"    {'★봉은사 수입':20}" + "".join(f"{eok(rev_cohost(i)):>8.2f}억" for i in range(3)))

    print("\n  " + "─"*(W-4))
    r_mid = rev_rental(3202); c_mid = rev_cohost(1)
    print(f"  ★대관 최고단가 {eok(r_mid):.2f}억  vs  공동주최 기준 {eok(c_mid):.2f}억  →  {c_mid/r_mid:.1f}배")
    print(f"    같은 방, 같은 나흘인데 '빌려주기'와 '같이 하기'가 {c_mid/r_mid:.0f}배 차이납니다")

    print("\n[②] 유발 매출 — 행사가 데려온 사람이 쓰는 돈 (타 라인 귀속)")
    print("─"*W)
    print(f"  {'':20}{'보수':>9}{'기준':>9}{'낙관':>9}")
    print(f"  {'봉은사관 방문객':20}" + "".join(f"{VISITOR[i]:>8,}명" for i in range(3)))
    print(f"  {'F&B 유발':20}" + "".join(f"{eok(VISITOR[i]*FB_RATE*FB_PV):>8.2f}억" for i in range(3)))
    print(f"  {'리테일 유발':20}" + "".join(f"{eok(VISITOR[i]*RT_RATE*RT_PV):>8.2f}억" for i in range(3)))
    print(f"  {'소계':20}" + "".join(f"{eok(induced(i)):>8.2f}억" for i in range(3)))
    print(f"  ※ RL-02·03·04에 귀속 — 이 라인 매출로 계상하지 않음 (중복 방지)")
    print(f"  ※ 기준안에서 직접수입 {eok(rev_cohost(1)):.2f}억 + 유발 {eok(induced(1)):.2f}억"
          f" = 실질 {eok(rev_cohost(1)+induced(1)):.2f}억")

    print("\n[③] 여유 48일을 채우면 — 연간 행사 포트폴리오")
    print("─"*W)
    print(f"  {'행사':22}{'일수':>6}{'횟수':>6}{'점유일':>7}  모델    비고")
    for k,v in EVENTS.items():
        print(f"  {k:22}{v['days']:>5}일{v['n']:>5}회{v['days']*v['n']:>6}일  "
              f"{'공동주최' if v['model']=='cohost' else '대관':6}  {v['note']}")
    pd = portfolio_days()
    print(f"  {'합계':22}{'':>6}{'':>6}{pd:>6}일  / 여유 {FREE_DAYS}일 → "
          f"{'초과 +' if pd>FREE_DAYS else '여유 '}{abs(FREE_DAYS-pd)}일")

    # 포트폴리오 매출
    co_events = [v for v in EVENTS.values() if v['model']=='cohost']
    rental_days = sum(v['days']*v['n'] for v in EVENTS.values() if v['model']=='rental')
    # 공동주최는 규모별로 차등 — 박람회 100%, 나머지 40%
    co_rev = rev_cohost(1) + rev_cohost(1)*0.4*2
    rental_rev = AREA*rental_days*2000
    print(f"\n  공동주최 3건 (박람회 100% + 페어 2건 각 40%)  {eok(co_rev):>6.2f}억")
    print(f"  대관 {rental_days}일 × 2,000㎡ × 2,000원          {eok(rental_rev):>6.2f}억")
    print(f"  ★행사 라인 합계                              {eok(co_rev+rental_rev):>6.2f}억")
    print(f"  ※ 00H의 대관 2.8억과 별개 — 대관은 기획전 회기 사이 상시 임대,")
    print(f"     이 라인은 여유 48일에 얹는 이벤트 트랙")
