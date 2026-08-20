# -*- coding: utf-8 -*-
"""총사업비 2단 구조 + 정부재원 시나리오 v1.0

★정정 — 00D 5개년 검토는 총 CAPEX를 90.8억으로 계산했으나 이는 '라인별 조성비'만 센 값이다.
E-1089(A)가 2026-08-17에 확정한 '건물 투자비 45~70억'이 통째로 빠져 있었다.

구조
  A단 리모델링비 — 건물 기반(설비 교체 + 공간 전환). 견적 2사 실측 기반 3단
  B단 사업비     — 라인별 조성(전시·F&B·리테일·교육·숙박)
  총사업비       — A + B + 설계감리 + 개관준비비 (+ 예비비) = 150~200억
"""
def won(v): return f"{v:,.1f}억"

BASIS = """
[A단 근거 — 견적 실측]
◆ E-0528(A) 에이비씨건설 28.56억(필수 노후설비) / 케희건설 41.50억(1안 전면)·27.00억(2안 핵심)
            주요항목 엘리베이터 3대 2.1~10.4억 · 냉난방 6.2억 · 수변전 4.47억 · 옥상방수 2.19억
◆ E-0073(B) 견적 3중 불일치 — 원 견적 27.00/28.56/41.50 · RFP 종합 27~45 · master-report 28~41
◆ E-0530(B) 설비 27~45 + 인테리어·공간전환 15~25 = 총 45~70억 (VAT 별도)
            ★전시 설비·콘텐츠 제작비는 미포함
◆ E-1089(A) 3단 병기 확정 — 보수 70 / 기준 57.5 / 낙관 45억 (2026-08-17 결정)
◆ E-0045(B) 설비 20년+ 경과 전면 교체 필요
◆ E-0504(A) 전환 제약 4종 — 설비 노후 · 지하 곡선벽 · 2층 벽체 철거 · 판매시설 전환 시 주차 강화
◆ E-0118(A) 내부 용도변경·인테리어 수준이면 현상변경 허가 불요 (외관·증축·구조변경 시 필요)

[예비비 근거 — 바로 옆 사업의 실증]
◆ E-1064(A) 법난기념관 예산 1,467억 → 중간설계 산출 2,040억(139%)
            절감 49억 반영 후 1,991억 증액 요청. 사유는 물가상승 346억·지하철9호선 방진·지열·무대AV

[정부재원 — 2026년 확인]
◆ 문체부 종교문화지원 예산 1,043.56억 (2025년 903.09억 대비 +15.6%)
   └ ★종교문화시설 건립 407억 (+4.6%) · 10·27 법난기념관 88억
   └ 전통종교문화유산 보존 321.75억 · 종교문화활동 지원 228.05억
◆ 국고보조율 25~50% + 자부담 50% 전제 (인근 주민이 이용 가능한 공간 조성 시)
◆ ★지원 제외 원칙 — 순수 종교활동·포교 목적 사업
◆ 나라살림연구소 — 사업 2020년 69.4억(8건) → 2024년 334.87억(46건) → 2025년 389.14억
   └ ★실집행률 2024년 33.0% · 0% 집행 22.2%(2022)→39.1%(2024)
   └ 미집행 18건 중 13건이 이듬해 138억 추가 배정
◆ SBS 2026.8.5~6 보도 (5일 템플스테이 / 6일 종교문화시설) · 조계종·문화사업단 "일부 사실과 다르다" 반박
"""

# ═══════════════════════════════════════════════════════════════
# ① A단 — 건물 리모델링비
# ═══════════════════════════════════════════════════════════════
CASE = ["하한", "기준", "상한"]
A_EQUIP  = [27.0, 35.0, 45.0]     # 설비 교체 — 견적 2사 실측 밴드
A_INTER  = [18.0, 22.5, 25.0]     # 인테리어·공간 전환
def a_stage(i): return A_EQUIP[i] + A_INTER[i]     # 45 / 57.5 / 70

# ═══════════════════════════════════════════════════════════════
# ② B단 — 라인별 사업비 · 국비 대상 구분
# ═══════════════════════════════════════════════════════════════
# subsidy: 'yes' 문화·교육 인프라 / 'no' 수익시설 / 'arg' 포지셔닝에 따라 갈림
B_LINES = {
 "전시 (불교문화 전시관)": dict(capex=16.7, subsidy="yes", note="RL-01 v1.2 · 관람객 306,500명"),
 "교육 (강의실·공방)":     dict(capex=3.22, subsidy="yes", note="RL-05 · 200㎡"),
 "명상 (기생형)":          dict(capex=0.0,  subsidy="yes", note="RL-06 구조C · 전용면적 0"),
 "F&B 5축":               dict(capex=14.6, subsidy="no",  note="RL-03B · 수익시설"),
 "리테일":                 dict(capex=4.0,  subsidy="no",  note="RL-04 5차 · 수익시설"),
 "숙박 800평":             dict(capex=52.3, subsidy="arg", note="RL-09 · 외국인 체험 인프라 논리 시 인정 가능"),
}
def b_stage(): return sum(v['capex'] for v in B_LINES.values())    # 90.8

# ═══════════════════════════════════════════════════════════════
# ③ 총사업비
# ═══════════════════════════════════════════════════════════════
DESIGN_RATE = [0.095, 0.095, 0.10]    # 설계·감리 (공사비 대비)
PREOPEN     = [4.0, 4.0, 4.0]         # 개관준비비 — 인력채용·교육·마케팅·시스템
CONTINGENCY = [0.0, 0.0, 19.0]        # 예비비 — 상한안에만 (법난기념관 139% 선례)

def total(i):
    a, b = a_stage(i), b_stage()
    design = (a+b)*DESIGN_RATE[i]
    return dict(a=a, b=b, sub=a+b, design=design,
                pre=PREOPEN[i], cont=CONTINGENCY[i],
                total=a+b+design+PREOPEN[i]+CONTINGENCY[i])

# ═══════════════════════════════════════════════════════════════
# ④ 국비 대상액 — 포지셔닝이 규모를 정한다
# ═══════════════════════════════════════════════════════════════
def subsidy_base(i, include_stay):
    """국비 대상액 = 총사업비 − 수익시설분. 부대비는 대상 비율로 안분"""
    t = total(i)
    excluded = sum(v['capex'] for v in B_LINES.values()
                   if v['subsidy']=="no" or (v['subsidy']=="arg" and not include_stay))
    core_ratio = (t['sub']-excluded)/t['sub']
    return (t['sub']-excluded) + (t['design']+t['pre']+t['cont'])*core_ratio

SUBSIDY_RATES = [0.25, 0.35, 0.50]

# ═══════════════════════════════════════════════════════════════
# ⑤ 00D 5개년 재계산 — CAPEX 90.8 → 148.3
# ═══════════════════════════════════════════════════════════════
DEPR_YEARS = 12
AFTER_TAX_OLD = [17.8, 26.8, 30.5, 31.4, 32.1]   # 00D v1.0 (감가 90.8 기준)
DEPR_OLD      = [5.2, 5.2, 6.8, 7.6, 7.6]
EFF_TAX = 0.093

def recalc(i=1, subsidy=0.0):
    """A단을 더한 감가상각으로 세후이익 재계산. subsidy는 무상 재원(감가 대상에서 제외)"""
    t = total(i)
    # 자산 계상액 = 총사업비 − 개관준비비(비용처리) − 국고보조금(자산차감법 가정)
    asset = t['total'] - t['pre'] - subsidy
    out=[]
    for y in range(1,6):
        # A단·부대비는 개관 전 투입 → 1년차부터 상각. B단 숙박 Phase2/3만 지연
        d_old = DEPR_OLD[y-1]
        d_add = (asset - 90.8)/DEPR_YEARS if asset > 90.8 else (asset-90.8)/DEPR_YEARS
        depr = d_old + d_add
        ebit_old = AFTER_TAX_OLD[y-1]/(1-EFF_TAX)          # 세후 → 세전 역산
        ebit = ebit_old - d_add
        after = ebit*(1-EFF_TAX) if ebit>0 else ebit
        out.append(dict(depr=depr, ebit=ebit, after=after))
    return out

def cashflow(i=1, subsidy=0.0, loan=0.0):
    """개관 전 투입 = A단 + 설계감리 + 개관준비 + B단 개관전분(61.8)"""
    t = total(i)
    pre_open = t['a'] + t['design'] + t['pre'] + 61.8 - subsidy - loan
    rows = recalc(i, subsidy)
    cf = -pre_open; out=[]
    later = {2: 19.9, 3: 9.1}          # 숙박 Phase2/3
    for y in range(1,6):
        c = rows[y-1]['after'] + rows[y-1]['depr'] - later.get(y,0.0)
        cf += c; out.append((rows[y-1]['after'], rows[y-1]['depr'], later.get(y,0.0), c, cf))
    return pre_open, out

if __name__ == "__main__":
    W=104
    print("═"*W); print("총사업비 2단 구조 v1.0 — ★00D의 CAPEX 90.8억 정정"); print("═"*W)

    print("\n[A단] 건물 리모델링비 — 견적 2사 실측 기반")
    print("─"*W)
    print(f"  {'항목':26}{'하한':>10}{'기준':>10}{'상한':>10}   근거")
    print(f"  {'설비 교체':26}" + "".join(f"{A_EQUIP[i]:>9.1f}억" for i in range(3))
          + "   에이비씨 28.56 / 케희 41.50·27.00")
    print(f"  {'인테리어·공간 전환':26}" + "".join(f"{A_INTER[i]:>9.1f}억" for i in range(3)) + "   E-0530 추정")
    print(f"  {'A단 소계':26}" + "".join(f"{a_stage(i):>9.1f}억" for i in range(3)) + "   ★E-1089 확정 3단")

    print("\n[B단] 라인별 사업비 — 국비 대상 구분")
    print("─"*W)
    mark = {"yes":"⭕ 문화·교육", "no":"❌ 수익시설", "arg":"△ 포지셔닝 의존"}
    for k,v in B_LINES.items():
        print(f"  {k:26}{v['capex']:>9.1f}억   {mark[v['subsidy']]:16} {v['note']}")
    print(f"  {'B단 소계':26}{b_stage():>9.1f}억")

    print("\n[총사업비] ★150~200억")
    print("─"*W)
    print(f"  {'항목':26}{'하한안':>10}{'기준안':>10}{'상한안':>10}")
    for lab,key in [("A단 리모델링","a"),("B단 사업비","b"),("소계","sub"),
                    ("설계·감리","design"),("개관준비비","pre"),("예비비","cont")]:
        print(f"  {lab:26}" + "".join(f"{total(i)[key]:>9.1f}억" for i in range(3)))
    print(f"  {'★총사업비':26}" + "".join(f"{total(i)['total']:>9.1f}억" for i in range(3)))
    print(f"\n  ※ 예비비는 상한안에만 — 법난기념관이 예산 1,467억 → 산출 2,040억(139%)으로 튄 선례(E-1064)")
    print(f"  ※ VAT 별도 · 과세분은 재원 확정 후 산정")

    print("\n[국비] 포지셔닝이 규모를 정한다 — 기준안 166억 기준")
    print("─"*W)
    print(f"  {'인정 범위':34}{'대상액':>10}" + "".join(f"{int(r*100)}%".rjust(10) for r in SUBSIDY_RATES))
    for label, inc in [("보수 — A단 + 전시·교육만", False),
                       ("★적극 — 숙박을 외국인 체험으로", True)]:
        base = subsidy_base(1, inc)
        print(f"  {label:34}{base:>9.1f}억" + "".join(f"{base*r:>9.1f}억" for r in SUBSIDY_RATES))
    d = subsidy_base(1,True)*0.5 - subsidy_base(1,False)*0.5
    print(f"\n  ★숙박 52.3억의 국비 인정 여부가 가르는 금액 (50% 기준): {d:.1f}억")
    print(f"  상한안 200억 + 적극 인정 + 50% → 국비 {subsidy_base(2,True)*0.5:.1f}억")

    print("\n[재계산] 00D 5개년 — CAPEX 90.8 → {:.1f}억".format(total(1)['total']-total(1)['pre']))
    print("─"*W)
    for sub_label, sub in [("국비 없음", 0.0), ("국비 47.6억 (보수·50%)", 47.6), ("국비 73.7억 (적극·50%)", 73.7)]:
        rows = recalc(1, sub)
        pre_open, cfs = cashflow(1, sub)
        payback = next((y for y,(a,d,l,c,cum) in enumerate(cfs,1) if cum>=0), None)
        print(f"\n  ▸ {sub_label}")
        print(f"    {'':14}" + "".join(f"{y}년차".rjust(10) for y in range(1,6)))
        print(f"    {'세후이익':14}" + "".join(f"{r['after']:>9.1f}억" for r in rows))
        print(f"    {'감가상각':14}" + "".join(f"{r['depr']:>9.1f}억" for r in rows))
        print(f"    {'누적현금흐름':14}" + "".join(f"{c[4]:>9.1f}억" for c in cfs))
        print(f"    개관 전 투입 {pre_open:.1f}억 · 회수 {str(payback)+'년차' if payback else '5년 내 미도달'}")

    print("\n[비교] 00D v1.0 대비")
    print("─"*W)
    r0 = recalc(1, 0.0)
    print(f"  {'':22}{'00D v1.0':>12}{'정정 후':>12}{'차이':>12}")
    print(f"  {'총 CAPEX':22}{90.8:>11.1f}억{total(1)['total']-total(1)['pre']:>11.1f}억"
          f"{total(1)['total']-total(1)['pre']-90.8:>+11.1f}억")
    print(f"  {'감가상각(5년차)':22}{7.6:>11.1f}억{r0[4]['depr']:>11.1f}억{r0[4]['depr']-7.6:>+11.1f}억")
    print(f"  {'5년차 세후이익':22}{32.1:>11.1f}억{r0[4]['after']:>11.1f}억{r0[4]['after']-32.1:>+11.1f}억")
    p0,c0 = cashflow(1,0.0)
    print(f"  {'개관 전 투입':22}{61.8:>11.1f}억{p0:>11.1f}억{p0-61.8:>+11.1f}억")
    print(f"  {'5년 누적 현금흐름':22}{80.1:>11.1f}억{c0[-1][4]:>11.1f}억{c0[-1][4]-80.1:>+11.1f}억")
