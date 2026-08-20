# -*- coding: utf-8 -*-
"""총투자 예산 구조 v1.1 — 보수 / 상업화 분리 · 전시 3,300㎡ 앵커안 반영

★2026-08-18 대표 판단 두 가지
  ① A단 45~70억은 '노후설비 교체 및 가동을 위한 보수용 예산'이며 상업화 예산과 별도다
  ② 총투자 예산은 기본 200억으로 설계한다

── v1.1 변경 (2026-08-18) ─────────────────────────────────────
  전시 CAPEX 16.70 → 24.70억 (전용 3,300㎡ 앵커안 · finance/inputs.json v1.1과 동기)
  ★이 모델에서 예비비는 잔여값(TARGET − 소계)이라 전시 증액분이 그대로 예비비를 잠식한다.
    200억 틀을 유지하면 예비비가 통상 하한(5~10%) 아래로 떨어지므로 두 관점을 병기한다:
      관점 A  총투자 200억 고정  → 예비비가 얼마 남는가
      관점 B  예비비율 7.4% 유지 → 총투자가 얼마가 되는가
  ⚠️ 증분이익(5년차 세후)은 전시 CAPEX +8.0억의 감가상각 증가만큼 하락한다(AFTER_TAX_ADJ).
     추정치이며 정밀값은 단일점 모델(00F) 재실행으로 확정해야 한다.

①이 재무 판단을 근본적으로 바꾼다.
보수비는 이 건물을 쓰려면 어떤 용도로 쓰든 드는 돈이다 —
재임대를 택해도 20년 넘은 수변전·냉난방·EV·방수는 교체해야 한다.
따라서 '사업 vs 재임대' 비교에서 보수비는 양쪽에 공통으로 들어가며,
사업의 순수 증분 투자는 총투자에서 보수비를 뺀 금액이다.
"""
def eok(v): return v/1e8

# ═══════════════════════════════════════════════════════════════
# ① 예산 구조 — 보수 / 상업화 분리
# ═══════════════════════════════════════════════════════════════
# [A] 보수예산 — 건물 가동을 위한 필수. 용도와 무관
REPAIR = {
 "수변전 설비":        4.47,
 "냉난방 전면 교체":    6.20,
 "엘리베이터 3대":      6.25,    # 2.1~10.4 중간값
 "옥상방수":           2.19,
 "급배수·전기 간선":     8.00,
 "소방·안전 기준 충족":   5.00,
 "외피·단열·창호":      10.00,
 "공용부 마감":         15.39,
}
def repair_total(): return sum(REPAIR.values())     # ≈ 57.5억 (E-1089 기준안)

# [B] 상업화예산 — 사업을 하기로 해서 드는 돈
COMMERCIAL = {
 "숙박 객실 조성 (61실)":      52.30,
 "숙박 기반설비 (신설분)":      17.10,   # 급배수 입상·환기덕트·방화구획·차음·스프링클러·급탕증설
 "전시 (불교문화 전시관)":      24.70,   # v1.1 — 전용 3,300㎡ 앵커안(구 1,450㎡ 16.70)
 "F&B 5축":                14.60,
 "리테일 (50평 3존)":         4.00,
 "교육 (강의실·공방)":          3.22,
}
def commercial_total(): return sum(COMMERCIAL.values())    # ≈ 107.9억

# [C] 부대비
DESIGN_RATE = 0.095
PREOPEN = 4.0
TARGET = 200.0                      # ★대표 지정 총투자 예산

CONT_RATE_V10 = 14.9/200.0          # v1.0 예비비율 7.4% — 관점 B의 기준

def structure(mode="A"):
    """A = 총투자 200억 고정(예비비 잔여) / B = 예비비율 7.4% 유지(총투자 변동)"""
    a = repair_total(); b = commercial_total()
    d = (a+b)*DESIGN_RATE
    sub = a+b+d+PREOPEN
    if mode == "A":
        total = TARGET; cont = total - sub
    else:
        total = sub/(1-CONT_RATE_V10); cont = total - sub
    return dict(repair=a, commercial=b, design=d, pre=PREOPEN,
                sub=sub, contingency=cont, total=total)

# ═══════════════════════════════════════════════════════════════
# ② ★증분 투자 — 재임대와 비교할 때 무엇이 순수 사업 비용인가
# ═══════════════════════════════════════════════════════════════
# 재임대를 택해도 드는 보수비 범위
#   최소  핵심 설비만 교체해 임대 가능 상태로 (케희 2안 27.0억)
#   표준  전면 보수 (기준안 57.5억)
REPAIR_IF_LEASE = {"최소": 27.0, "표준": 57.5}

def incremental(lease_repair, mode="A"):
    """사업을 택했을 때 재임대 대비 추가로 드는 돈"""
    s = structure(mode)
    return s['total'] - lease_repair

# ═══════════════════════════════════════════════════════════════
# ③ 증분 수익률 — 추가 투자로 얼마를 더 버는가
# ═══════════════════════════════════════════════════════════════
AFTER_TAX = {          # 5년차 세후이익 (model-final 기준 · 전시 16.7 시점)
 "국비 0":    26.8,
 "국비 43.4": 30.0,
 "국비 72.8": 32.2,
}
# v1.1 보정 — 전시 CAPEX +8.0억의 감가상각 증가(연 0.667억)가 세후를 깎는다
EXHIB_CAPEX_DELTA = 24.70 - 16.70
AFTER_TAX_ADJ = -(EXHIB_CAPEX_DELTA/12) * (1 - 0.5*(0.19*1.1))
def after_tax(label): return AFTER_TAX[label] + AFTER_TAX_ADJ
LEASE_AFTER = 27.1     # 재임대 세후

def incremental_return(subsidy_label, lease_repair, subsidy=0.0, loan=0.0, mode="A"):
    inc_inv = incremental(lease_repair, mode) - subsidy - loan
    inc_profit = after_tax(subsidy_label) - LEASE_AFTER
    payback = inc_inv/inc_profit if inc_profit > 0 else None
    return inc_inv, inc_profit, payback

# ═══════════════════════════════════════════════════════════════
# ④ 필요 현금 — 200억 기준 재계산
# ═══════════════════════════════════════════════════════════════
# 개관 전 상업화분 = 전시16.7 + F&B14.6 + 리테일4.0 + 교육3.2 + 숙박Phase1 23.3 = 61.8
#   + 숙박 기반설비 17.1 (급배수 입상관·환기덕트·방화구획은 층 전체를 한 번에 — Phase 분할 불가)
#   ※ 숙박 Phase2/3 29.0억은 이미 61.8에서 제외돼 있으므로 다시 빼지 않는다
PRE_OPEN_COMMERCIAL = 61.8 + 17.1
WC_CONSERVATIVE = 24.6                        # 보수안 3년 현금부족 (Phase 중단 전제)

def cash_need(subsidy=0.0, loan=0.0, mode="A"):
    s = structure(mode)
    pre_open = s['repair'] + s['design'] + PREOPEN + PRE_OPEN_COMMERCIAL - subsidy - loan
    return dict(pre_open=pre_open,
                stable=pre_open + WC_CONSERVATIVE,
                recommended=pre_open + WC_CONSERVATIVE + s['contingency'])

# 국비 대상액 — 200억 기준 재산정
def subsidy_base(include_stay, mode="A"):
    s = structure(mode)
    excl = COMMERCIAL["F&B 5축"] + COMMERCIAL["리테일 (50평 3존)"]
    if not include_stay:
        excl += COMMERCIAL["숙박 객실 조성 (61실)"] + COMMERCIAL["숙박 기반설비 (신설분)"]
    core = s['repair'] + s['commercial'] - excl
    ratio = core/(s['repair']+s['commercial'])
    return core + (s['design']+s['pre']+s['contingency'])*ratio

if __name__ == "__main__":
    W=104
    print("═"*W); print("총투자 예산 구조 v1.1 — 보수 / 상업화 분리 · 전시 3,300㎡ 앵커안"); print("═"*W)
    s = structure()

    print("\n[A] 보수예산 — 건물 가동을 위한 필수 · 용도 무관")
    print("─"*W)
    for k,v in REPAIR.items(): print(f"  {k:24}{v:>7.2f}억")
    print(f"  {'소계':24}{s['repair']:>7.2f}억   ← E-1089 기준안 57.5억과 정합")

    print("\n[B] 상업화예산 — 사업을 하기로 해서 드는 돈")
    print("─"*W)
    for k,v in COMMERCIAL.items(): print(f"  {k:24}{v:>7.2f}억")
    print(f"  {'소계':24}{s['commercial']:>7.2f}억")

    print("\n[C] 총투자 200억 구성")
    print("─"*W)
    for lab,k in [("보수예산","repair"),("상업화예산","commercial"),("설계·감리","design"),
                  ("개관준비비","pre"),("예비비","contingency")]:
        print(f"  {lab:24}{s[k]:>7.1f}억{s[k]/TARGET*100:>7.1f}%")
    print(f"  {'★총투자':24}{s['total']:>7.1f}억{100.0:>7.1f}%")
    print(f"\n  예비비 {s['contingency']:.1f}억 = 총투자의 {s['contingency']/s['total']*100:.1f}%")
    b = structure("B")
    print(f"  ★관점 B — 예비비율 7.4%를 유지하려면 총투자 {b['total']:.1f}억 (예비비 {b['contingency']:.1f}억)")
    print(f"  ※ 통상 예비비는 5~10%. 법난기념관 139% 증액 선례가 있는 현장이다")

    print("\n[②] ★증분 투자 — 재임대와 비교하면")
    print("─"*W)
    print("  재임대를 택해도 노후설비는 교체해야 한다. 그 금액은 양쪽에 공통으로 든다.")
    print()
    print(f"  {'재임대 시 보수비':22}{'사업 총투자':>12}{'증분 투자':>12}   해석")
    for lab, r in REPAIR_IF_LEASE.items():
        inc = incremental(r)
        print(f"  {lab+' '+str(r)+'억':22}{TARGET:>11.1f}억{inc:>11.1f}억   "
              f"{'임대도 전면보수 필요 시' if lab=='표준' else '임대는 최소보수만 할 경우'}")

    print("\n[③] 증분 수익률 — 추가 투자로 연 얼마를 더 버는가")
    print("─"*W)
    print(f"  {'시나리오':30}{'증분투자':>10}{'증분이익':>10}{'회수':>9}")
    for slab, sub in [("국비 0", 0.0), ("국비 43.4", 43.4), ("국비 72.8", 72.8)]:
        for llab, r in REPAIR_IF_LEASE.items():
            for loan_lab, loan in [("융자 0", 0.0), ("융자 30", 30.0)]:
                if loan == 0.0 and slab != "국비 0": continue
                inv, prof, pb = incremental_return(slab, r, sub, loan)
                tag = f"{slab} · 임대보수 {llab} · {loan_lab}"
                print(f"  {tag:30}{inv:>9.1f}억{prof:>9.1f}억"
                      f"{(f'{pb:.1f}년' if pb else '불가'):>9}")

    print("\n[④] 필요 현금 — 200억 기준")
    print("─"*W)
    print(f"  {'재원 조합':26}{'개관 전':>11}{'안정선':>11}{'권장선':>11}")
    for lab, sub, loan in [("국비 0 · 융자 0", 0.0, 0.0),
                           ("국비 43.4 · 융자 0", 43.4, 0.0),
                           ("국비 43.4 · 관광기금 30", 43.4, 30.0),
                           ("국비 72.8 · 관광기금 30", 72.8, 30.0),
                           ("국비 88.4 · 관광기금 60", 88.4, 60.0)]:
        c = cash_need(sub, loan)
        print(f"  {lab:26}{c['pre_open']:>10.1f}억{c['stable']:>10.1f}억{c['recommended']:>10.1f}억")
    print(f"\n  ※ 개관 전 = 보수 {s['repair']:.1f} + 설계감리 {s['design']:.1f} + 개관준비 {PREOPEN:.1f}"
          f" + 상업화 개관전분 {PRE_OPEN_COMMERCIAL:.1f} − 국비 − 융자")
    print(f"  ※ 숙박 Phase2/3 {29.0:.1f}억은 2·3년차 말 집행 (단계 개관)")

    print("\n[⑤] 국비 대상액 — 200억 기준 재산정")
    print("─"*W)
    for lab, inc in [("보수 — 보수예산 + 전시·교육", False), ("적극 — 숙박 포함", True)]:
        b = subsidy_base(inc)
        print(f"  {lab:30} 대상 {b:>6.1f}억 → 25% {b*0.25:>5.1f}억 · 35% {b*0.35:>5.1f}억 · 50% {b*0.5:>5.1f}억")
    print(f"\n  ★보수예산 {s['repair']:.1f}억은 '국민에게 개방되는 문화시설의 기반 정비'로")
    print(f"    국비 대상에 넣는 것이 자연스럽다 — 수익시설이 아니기 때문")
