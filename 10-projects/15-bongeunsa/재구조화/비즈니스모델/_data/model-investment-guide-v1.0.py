# -*- coding: utf-8 -*-
"""투자 가이드 v1.0 — 봉은사는 현금을 얼마나 확보해야 안전한가

질문: "가용현금을 얼마 확보해서 투자하면 안정적인가"

이 질문에 답하려면 두 가지를 먼저 알아야 한다.
  ① 전 라인 보수안 조합 — 지금까지 미계산으로 남겨둔 진짜 하방
  ② 적자 구간을 버티는 데 필요한 현금 (운전자본)

'안정적'을 세 단계로 정의한다.
  최소선  개관 전 자금을 댈 수 있다
  안정선  보수 시나리오에서도 현금이 마르지 않는다
  권장선  안정선 + 예비비 + 운전자본
"""
def eok(v): return v/1e8

# ═══════════════════════════════════════════════════════════════
# ① 전 라인 보수안 조합 — 미계산 항목 해소
# ═══════════════════════════════════════════════════════════════
# 각 라인 리포트의 '보수' 시나리오 매출. 5축은 라인별로 분해.
CONSERVATIVE = {
 "RL-01 전시":      ( 3.00, "v1.2 보수 — 관람 10.1만"),
 "RL-02 전통다원":   ( 2.60, "5축 보수 축5"),
 "RL-03 사찰음식":   (14.60, "5축 보수 — 다이닝 13.6 + 곡차 1.0"),
 "RL-04 리테일":    ( 9.50, "5차 보수 — 관람 20만 · SPV 4,000원"),
 "RL-05 교육":      ( 2.80, "신규 1.60 + 5축 아카데미 1.2"),
 "RL-06 명상":      ( 2.11, "단독 구조C 보수"),
 "RL-07 기업 B2B":  ( 0.42, "4계층 보수"),
 "RL-08 대관":      ( 1.20, "실측 기반 · 가동률 하락분"),
 "RL-09 숙박":      ( 8.10, "800평 보수 — 가동 30~38%"),
 "RL-10 멤버십":    ( 4.19, "v1.1 보수 5.0 × 중복조정 0.838"),
 "RL-11 장묘서비스":  ( 1.10, "영대공양 0.8 + 컨시어지 0.3"),
 "RL-13 시즌·야간":  ( 0.52, "1시즌 20일 · 25부스"),
 "RL-16 아카데미":   ( 0.12, "연 1기 15명"),
}
BASE_REV = 123.56          # 기준안 (model-final)
BASE_OP  = 41.92           # 기준안 영업이익
def cons_rev(): return sum(v[0] for v in CONSERVATIVE.values())

# ═══════════════════════════════════════════════════════════════
# ② 고정비·변동비 분해 — 라인 리포트의 3구간 손익에서 역산
# ═══════════════════════════════════════════════════════════════
# 검산 근거 (매출, 영업이익) 쌍
CALIB = {
 "RL-06 명상 구조C":  [(2.11, 0.30), (7.64, 4.09)],
 "RL-05 교육":        [(1.60, -0.41), (5.04, 1.53)],
 "RL-09 숙박+명상":   [(10.4, -3.30), (27.7, 7.60)],
}
def calib_line(pairs):
    (r1,o1),(r2,o2) = pairs
    cm = (o2-o1)/(r2-r1)          # 공헌이익률
    fixed = r1*cm - o1
    return cm, fixed

VAT_R = 0.10/1.10                  # 표시가 → 공급가액 환산
def net(rev): return rev*(1-VAT_R*0.97)   # 면세 3% 반영

# 전체 공헌이익률·고정비 — 기준안에서 역산
CM = 0.65                          # 라인별 calib 평균 (0.63~0.69)
FIXED = net(BASE_REV)*CM - BASE_OP

def op_from(rev):
    return net(rev)*CM - FIXED

# ═══════════════════════════════════════════════════════════════
# ③ 손익 — 보수 시나리오
# ═══════════════════════════════════════════════════════════════
DEPR_YEARS, PROP = 12, 1.2
RAMP_C = [0.60, 0.85, 1.00, 1.00, 1.00]    # 보수는 단일 램프
EFF_TAX = 0.093

def pnl_cons(y, capex, subsidy=0.0):
    rev = cons_rev()*RAMP_C[y-1]
    op = op_from(rev)
    depr = (capex-subsidy)/DEPR_YEARS
    ebit = op - depr - PROP
    tax = max(0.0, ebit)*EFF_TAX
    return dict(rev=rev, op=op, depr=depr, ebit=ebit, after=ebit-tax)

# ═══════════════════════════════════════════════════════════════
# ④ 필요 현금 — 3단계 정의
# ═══════════════════════════════════════════════════════════════
TPC = {"하한":152.7, "기준":166.4, "상한":199.9}
CAPEX = {"하한":148.7, "기준":162.4, "상한":195.9}     # 개관준비비 제외
PRE_OPEN_B = 61.8                                      # B단 중 개관 전 투입분
A_STAGE = {"하한":45.0, "기준":57.5, "상한":70.0}
DESIGN = {"하한":12.9, "기준":14.1, "상한":16.1}
PREOPEN_COST = 4.0
CONT = {"하한":0.0, "기준":0.0, "상한":19.0}

def pre_open_need(case, subsidy=0.0, loan=0.0):
    """개관 전에 실제로 나가는 돈"""
    return A_STAGE[case] + DESIGN[case] + CONT[case] + PREOPEN_COST + PRE_OPEN_B - subsidy - loan

def working_capital(case, subsidy=0.0, years=3, phase_stop=True):
    """보수 시나리오에서 개관 후 누적 현금 부족분 (감가상각은 비현금이라 더함)

    phase_stop=True  — 1년차 실적을 보고 숙박 Phase2/3(29억)를 집행하지 않는다.
                       RL-09 리포트의 단계 개관 권고를 그대로 따르는 경우.
    phase_stop=False — 계획대로 강행하는 경우.
    """
    worst = 0.0; cum = 0.0
    later = {} if phase_stop else {2: 19.9, 3: 9.1}
    for y in range(1, years+1):
        p = pnl_cons(y, CAPEX[case], subsidy)
        cf = p['after'] + p['depr'] - later.get(y, 0.0)
        cum += cf
        worst = min(worst, cum)
    return -worst if worst < 0 else 0.0

def guide(case, subsidy=0.0, loan=0.0, phase_stop=True):
    po = pre_open_need(case, subsidy, loan)
    wc = working_capital(case, subsidy, phase_stop=phase_stop)
    return dict(pre_open=po, wc=wc,
                minimum=po,
                stable=po+wc,
                recommended=po+wc+max(CONT[case], TPC[case]*0.10))

if __name__ == "__main__":
    W=104
    print("═"*W); print("투자 가이드 v1.0 — 가용현금을 얼마 확보해야 안전한가"); print("═"*W)

    print("\n[①] ★전 라인 보수안 조합 — 지금까지 미계산이던 진짜 하방")
    print("─"*W)
    print(f"  {'라인':16}{'기준안':>9}{'보수안':>9}{'비율':>8}   근거")
    from importlib import util as _u
    spec=_u.spec_from_file_location('mf','model-final-v1.0.py'); mf=_u.module_from_spec(spec); spec.loader.exec_module(mf)
    for k,(cv,note) in CONSERVATIVE.items():
        base = mf.LINES[k][0]
        print(f"  {k:16}{base:>8.2f}억{cv:>8.2f}억{cv/base*100:>7.0f}%   {note}")
    print("  "+"─"*(W-2))
    cr = cons_rev()
    print(f"  {'합계':16}{BASE_REV:>8.2f}억{cr:>8.2f}억{cr/BASE_REV*100:>7.0f}%")
    print(f"\n  ★보수안은 기준안의 {cr/BASE_REV*100:.0f}% — 종합리포트가 민감도로 잡은 '매출 −20%'보다")
    print(f"    {(1-cr/BASE_REV)*100:.0f}% 감소로 3배 가까이 깊다")

    print("\n[②] 고정비·변동비 분해 — 라인 리포트 3구간에서 역산")
    print("─"*W)
    for k,pairs in CALIB.items():
        cm, f = calib_line(pairs)
        print(f"  {k:20} 공헌이익률 {cm*100:>5.1f}% · 고정비 {f:>5.2f}억")
    print(f"  {'→ 전체 적용':20} 공헌이익률 {CM*100:>5.1f}% · 고정비 {FIXED:>5.2f}억 (기준안에서 역산)")

    print("\n[③] 보수 시나리오 손익 — 기준안 CAPEX 162.4억 · 국비 없음")
    print("─"*W)
    print(f"  {'':14}" + "".join(f"{y}년차".rjust(11) for y in range(1,6)))
    rows = [pnl_cons(y, CAPEX["기준"]) for y in range(1,6)]
    for lab,k in [("매출","rev"),("영업이익","op"),("감가상각","depr"),("세전이익","ebit"),("★세후이익","after")]:
        print(f"  {lab:14}" + "".join(f"{r[k]:>10.1f}억" for r in rows))
    print(f"\n  → 보수안에서는 5년 내내 적자. 정상가동에서도 연 {rows[4]['after']:.1f}억")

    print("\n[④] ★필요 현금 3단계 — 재원 시나리오별")
    print("─"*W)
    scen = [
      ("A 국비 0 · 융자 0",            0.0,  0.0),
      ("B 국비 43.4 · 융자 0",        43.4,  0.0),
      ("C 국비 43.4 · 관광기금 30",   43.4, 30.0),
      ("D 국비 72.8 · 관광기금 30",   72.8, 30.0),
      ("E 국비 72.8 · 관광기금 60",   72.8, 60.0),
    ]
    print(f"  {'시나리오':26}{'개관전':>10}{'운전자본':>10}{'최소선':>10}{'안정선':>10}{'권장선':>10}")
    for lab, sub, loan in scen:
        g = guide("기준", sub, loan)
        print(f"  {lab:26}{g['pre_open']:>9.1f}억{g['wc']:>9.1f}억"
              f"{g['minimum']:>9.1f}억{g['stable']:>9.1f}억{g['recommended']:>9.1f}억")
    print(f"\n  최소선 = 개관 전 투입액 · 안정선 = 최소선 + 보수안 3년 현금부족")
    print(f"  권장선 = 안정선 + 예비비(총사업비의 10%)")
    print(f"  ※ 위 표는 ★단계 개관 권고를 따라 보수 시 숙박 Phase2/3(29억)를 집행하지 않는 전제")

    print("\n[④-b] ★단계 개관이 곧 리스크 관리 장치")
    print("─"*W)
    for stop, lab in [(True, "Phase 중단 — 1년차 실적 보고 판단"), (False, "Phase 강행 — 계획대로 집행")]:
        wc = working_capital("기준", 43.4, phase_stop=stop)
        g = guide("기준", 43.4, 30.0, phase_stop=stop)
        print(f"  {lab:32} 운전자본 {wc:>5.1f}억 · 권장선 {g['recommended']:>6.1f}억")
    d = guide("기준",43.4,30.0,False)['recommended'] - guide("기준",43.4,30.0,True)['recommended']
    print(f"  → 차이 {d:.1f}억. 보수 시나리오에서 Phase2/3를 멈추는 것만으로 필요 현금이 줄어든다")

    print("\n[⑤] 총사업비 규모별 — 권장선 (국비 43.4 · 융자 30 기준)")
    print("─"*W)
    for case in ["하한","기준","상한"]:
        g = guide(case, 43.4, 30.0)
        print(f"  총사업비 {TPC[case]:>5.1f}억 → 개관전 {g['pre_open']:>5.1f}억 · "
              f"안정선 {g['stable']:>5.1f}억 · ★권장선 {g['recommended']:>5.1f}억")

    print("\n[⑥] 판정 — 얼마를 확보하면 되는가")
    print("─"*W)
    g_min = guide("하한", 72.8, 60.0)
    g_mid = guide("기준", 43.4, 30.0)
    g_max = guide("상한", 0.0, 0.0)
    print(f"  최상 조건 (하한안·국비72.8·융자60)   권장선 {g_min['recommended']:>6.1f}억")
    print(f"  현실 기준 (기준안·국비43.4·융자30)   권장선 {g_mid['recommended']:>6.1f}억")
    print(f"  최악 조건 (상한안·국비0·융자0)       권장선 {g_max['recommended']:>6.1f}억")
    print(f"\n  ★확보 목표 {g_mid['recommended']:.0f}억 — 현실 기준")
    print(f"    이 금액이면 총사업비 166억 사업을 국비·융자와 함께 완주하고,")
    print(f"    보수 시나리오 3년을 버틴 뒤 예비비까지 남는다")
    # 웨딩홀 임대수입 대비
    print(f"\n  참고 — 웨딩홀 임대 연 30억(세후 27.1억) 기준")
    print(f"    권장선 {g_mid['recommended']:.0f}억 = 임대 수입 {g_mid['recommended']/27.1:.1f}년치")
