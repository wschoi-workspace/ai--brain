# -*- coding: utf-8 -*-
"""봉은문화센터 종합 재무모델 v1.0 — 단일 진실원(SSOT)

2026-08-17 하루에 나온 검토 12건의 최종 확정값을 한 파일에 모은다.
지금까지 각 리포트가 자기 숫자를 갖고 있었고, 정정이 여러 번 있었다.
이 파일이 그 최종 상태이며, 종합 리포트(00F)의 모든 표는 여기서 나온다.

검토 이력
  RL-01 전시 v1.2 / RL-03·03B 다이닝·5축 / RL-04 5차 독립 / RL-05 교육
  RL-06 명상 단독 / RL-07 B2B / RL-08 대관 실측 / RL-09 숙박 / RL-10 멤버십
  RL-11~16 별도트랙 재산정 / 00C 교차정합 / 00D 세금·5개년 / 00E 총사업비·자금조달
"""
def eok(v): return v/1e8

# ═══════════════════════════════════════════════════════════════
# ① 매출 — 16개 라인 최종 확정값
# ═══════════════════════════════════════════════════════════════
# (매출억, 영업이익률, 이익률등급 S=산출/E=추정, CAPEX억, 램프업키, 면세비율, 출처)
LINES = {
 "RL-01 전시":      (10.30, 0.181, "S", 16.70, "std",  0.00, "v1.2 권고안 · 해설 중심 재편"),
 "RL-02 전통다원":   ( 4.60, 0.302, "S",  0.00, "std",  0.00, "RL-03B 5축 축5"),
 "RL-03 사찰음식":   (28.80, 0.302, "S", 14.60, "std",  0.00, "5축 다이닝 25.9 + 곡차 2.9"),
 "RL-04 리테일":    (19.00, 0.284, "S",  4.00, "std",  0.05, "5차 독립리포트 50평·SPV 5,500"),
 "RL-05 교육":      ( 8.23, 0.304, "S",  3.22, "std",  0.10, "신규 6건 5.04 + 5축 아카데미 3.19"),
 "RL-06 명상":      ( 6.64, 0.536, "S",  0.00, "fast", 0.00, "단독 구조C 기생형 · 카니발 조정 후"),
 "RL-07 기업 B2B":  ( 2.61, 0.400, "S",  0.00, "fast", 0.00, "4계층 · 겸임 조직 기준"),
 "RL-08 대관":      ( 1.84, 0.600, "E",  0.00, "fast", 0.00, "1,000㎡ 축소안 · 원가율 40% 가정"),
 "RL-09 숙박":      (18.50, 0.220, "E", 52.30, "slow", 0.00, "800평 61실 · 이익률 추정"),
 "RL-10 멤버십":    (14.16, 0.550, "S",  0.00, "memb", 0.00, "2트랙 · 중복 조정 후"),
 "RL-11 장묘서비스":  ( 4.00, 0.600, "E",  0.00, "slow", 0.30, "영대공양·컨시어지 — 시설형 제외"),
 "RL-13 시즌·야간":  ( 4.28, 0.450, "E",  0.00, "std",  0.00, "부스료·야간프로그램·협찬"),
 "RL-16 아카데미":   ( 0.60, 0.300, "E",  0.00, "cplan",0.00, "사찰운영자 아카데미"),
}
# 계상 제외: RL-12 온라인(RL-04에 흡수) · RL-14~15(1년차 0, 3년차부터) · RL-11 시설형(계약 범위 밖)

RAMP = {
 "std":   [0.60, 0.85, 1.00, 1.00, 1.00],
 "fast":  [0.75, 0.95, 1.00, 1.00, 1.00],
 "slow":  [0.50, 0.75, 0.90, 1.00, 1.00],
 "memb":  [1.00, 1.34, 1.57, 1.72, 1.82],
 "cplan": [1.00, 1.50, 2.20, 2.80, 3.20],
}
# RL-14~16 종단 확산분 — 9차 별도트랙 리포트의 5개년 전개
# ★중복 조정: 만개 12.1억(도매6.0+IP2.1+용역4.0) 중 RL-16 아카데미(위 LINES에 계상)를 제외 → 11.5억
C_FULL = 11.5
C_RAMP = [0.00, 0.25, 0.60, 0.85, 1.00]
C_TRACK = [C_FULL*r for r in C_RAMP]      # 0 / 2.9 / 6.9 / 9.8 / 11.5
INCLUDE_C = False    # ★기본 제외 — 00E v2.0과 정합. 포함 시 별도 표기

# ═══════════════════════════════════════════════════════════════
# ② 총사업비 — 2단 구조
# ═══════════════════════════════════════════════════════════════
CASE = ["하한", "기준", "상한"]
A_EQUIP, A_INTER = [27.0, 35.0, 45.0], [18.0, 22.5, 25.0]
DESIGN_RATE, PREOPEN, CONTINGENCY = [0.095, 0.095, 0.10], [4.0]*3, [0.0, 0.0, 19.0]
def a_stage(i): return A_EQUIP[i]+A_INTER[i]
def b_stage(): return sum(v[3] for v in LINES.values())
def tpc(i):
    a, b = a_stage(i), b_stage()
    d = (a+b)*DESIGN_RATE[i]
    return dict(a=a, b=b, design=d, pre=PREOPEN[i], cont=CONTINGENCY[i],
                total=a+b+d+PREOPEN[i]+CONTINGENCY[i], capex=a+b+d+CONTINGENCY[i])

# ═══════════════════════════════════════════════════════════════
# ③ 세금
# ═══════════════════════════════════════════════════════════════
VAT_RATE, FUND_RATE, LOCAL_TAX = 0.10, 0.50, 0.10
DEPR_YEARS, BLDG_VALUE, PROP_RATE = 12, 300.0, 0.004
def corp_tax(base):
    if base <= 0: return 0.0
    if base <= 2:     return base*0.09
    if base <= 200:   return 2*0.09 + (base-2)*0.19
    return 2*0.09 + 198*0.19 + (base-200)*0.21

# ═══════════════════════════════════════════════════════════════
# ④ 5개년 손익
# ═══════════════════════════════════════════════════════════════
CAPEX_LATER = {2: 19.9, 3: 9.1}      # 숙박 Phase2/3

def pnl(y, i=1, subsidy=0.0):
    gross = op = vat = 0.0
    for name,(rev, mgn, g, cap, rk, ex, src) in LINES.items():
        r = rev*RAMP[rk][y-1]
        gross += r
        v = r*(1-ex)*(VAT_RATE/(1+VAT_RATE))
        vat += v
        op += (r-v)*mgn
    if INCLUDE_C:
        gross += C_TRACK[y-1]; op += C_TRACK[y-1]*0.35     # C안 확산분 이익률 35% 가정
    t = tpc(i)
    asset = t['capex'] - subsidy
    base_depr = (asset - sum(CAPEX_LATER.values()))/DEPR_YEARS
    depr = base_depr + sum(a/DEPR_YEARS for yy,a in CAPEX_LATER.items() if y > yy)
    prop = BLDG_VALUE*PROP_RATE
    ebit = op - depr - prop
    tax_base = max(0.0, ebit*(1-FUND_RATE))
    ct = corp_tax(tax_base); lt = ct*LOCAL_TAX
    return dict(gross=gross, vat=vat, net=gross-vat, op=op, depr=depr, prop=prop,
                ebit=ebit, ct=ct, lt=lt, after=ebit-ct-lt)

def five(i=1, subsidy=0.0): return [pnl(y, i, subsidy) for y in range(1,6)]

def cashflow(i=1, subsidy=0.0):
    t = tpc(i)
    pre_open = t['a'] + t['design'] + t['cont'] + t['pre'] + 61.8 - subsidy
    rows = five(i, subsidy); cf = -pre_open; out=[]
    for y in range(1,6):
        c = rows[y-1]['after'] + rows[y-1]['depr'] - CAPEX_LATER.get(y, 0.0)
        cf += c; out.append((c, cf))
    return pre_open, out

# ═══════════════════════════════════════════════════════════════
# ⑤ 국비
# ═══════════════════════════════════════════════════════════════
NO_SUBSIDY = ["RL-03 사찰음식", "RL-04 리테일"]          # 수익시설(F&B·리테일)
ARG_SUBSIDY = ["RL-09 숙박"]                            # 포지셔닝 의존
def subsidy_base(i, include_stay):
    t = tpc(i)
    excl = sum(LINES[k][3] for k in NO_SUBSIDY)
    if not include_stay: excl += sum(LINES[k][3] for k in ARG_SUBSIDY)
    core = t['a']+t['b']-excl
    ratio = core/(t['a']+t['b'])
    return core + (t['design']+t['pre']+t['cont'])*ratio

BASELINE_AFTER = 27.1     # 재임대 세후 (임대 30억 − 법인세·지방세)

if __name__ == "__main__":
    W=106
    print("═"*W); print("봉은문화센터 종합 재무모델 v1.0 — 검토 12건 통합"); print("═"*W)

    print("\n[①] 매출 — 16개 라인 중 계상 13개")
    print("─"*W)
    print(f"  {'라인':16}{'매출':>9}{'이익률':>8}{'등급':>5}{'영업이익':>10}{'CAPEX':>9}  출처")
    tr=to=0
    for n,(rev,mgn,g,cap,rk,ex,src) in LINES.items():
        tr+=rev; to+=rev*mgn
        print(f"  {n:16}{rev:>8.2f}억{mgn*100:>7.1f}%{g:>5}{rev*mgn:>9.2f}억{cap:>8.1f}억  {src}")
    print("  "+"─"*(W-2))
    print(f"  {'합계':16}{tr:>8.2f}억{to/tr*100:>7.1f}%{'':>5}{to:>9.2f}억{b_stage():>8.1f}억")
    print(f"  ※ 이익률 추정(E) 5개 — RL-08·09·11·13·16 · 마스터 v0.2(66.7억) 대비 {tr/66.7:.2f}배")

    print("\n[②] 총사업비 — 2단 구조")
    print("─"*W)
    print(f"  {'':22}{'하한안':>12}{'기준안':>12}{'상한안':>12}")
    for lab,k in [("A단 리모델링","a"),("B단 사업비","b"),("설계·감리","design"),
                  ("개관준비비","pre"),("예비비","cont"),("총사업비","total")]:
        pre = "  " if k!="total" else "★ "
        print(f"  {pre}{lab:20}" + "".join(f"{tpc(i)[k]:>11.1f}억" for i in range(3)))

    print("\n[③] 5개년 손익 — 국비 없음 (기준안)")
    print("─"*W)
    rows = five(1, 0.0)
    print(f"  {'':18}" + "".join(f"{y}년차".rjust(11) for y in range(1,6)))
    for lab,k in [("총매출(VAT포함)","gross"),("부가가치세","vat"),("순매출","net"),
                  ("영업이익","op"),("감가상각","depr"),("재산세","prop"),
                  ("세전이익","ebit"),("법인세","ct"),("지방소득세","lt"),("★세후이익","after")]:
        print(f"  {lab:18}" + "".join(f"{r[k]:>10.1f}억" for r in rows))

    print("\n[④] 국비 시나리오 — 기준안 166.4억")
    print("─"*W)
    for lab, inc in [("보수 — 전시·교육·A단", False), ("적극 — 숙박 포함", True)]:
        b = subsidy_base(1, inc)
        print(f"  {lab:24} 대상 {b:>6.1f}억 → 25% {b*0.25:>5.1f}억 · 35% {b*0.35:>5.1f}억 · 50% {b*0.5:>5.1f}억")
    print()
    print(f"  {'시나리오':22}{'개관전':>10}{'5년차세후':>11}{'5년누적CF':>11}{'회수':>7}{'기준선대비':>11}")
    scen = [("국비 없음", 0.0), ("국비 43.4억 (보수·50%)", subsidy_base(1,False)*0.5),
            ("국비 72.8억 (적극·50%)", subsidy_base(1,True)*0.5)]
    for lab, sub in scen:
        rows = five(1, sub); pre, cfs = cashflow(1, sub)
        pb = next((y for y,(c,cum) in enumerate(cfs,1) if cum>=0), None)
        a5 = rows[4]['after']
        print(f"  {lab:22}{pre:>9.1f}억{a5:>10.1f}억{cfs[-1][1]:>+10.1f}억"
              f"{(str(pb)+'년차' if pb else '미도달'):>7}{a5/BASELINE_AFTER:>10.2f}x")

    print("\n[⑤] 민감도 — 5년차 세후이익 (국비 43.4억 기준)")
    print("─"*W)
    sub = subsidy_base(1,False)*0.5
    base5 = five(1, sub)[4]['after']
    print(f"  {'기준':32}{base5:>9.1f}억")
    import copy
    orig = dict(LINES)
    def s(label, mod, restore=True):
        global LINES
        keep = dict(LINES); mod()
        v = five(1, sub)[4]['after']
        if restore: LINES = keep
        print(f"  {label:32}{v:>9.1f}억{v-base5:>+9.1f}억{(v-base5)/base5*100:>+8.1f}%")
    def m1():
        global LINES
        LINES = {k:(v[0]*0.8,)+v[1:] for k,v in LINES.items()}
    s("전 라인 매출 −20%", m1)
    def m2():
        global LINES
        LINES = {k:(v[0], v[1]-0.10 if v[2]=="E" else v[1])+v[2:] for k,v in LINES.items()}
    s("추정 이익률 5개 −10%p", m2)
    def m3():
        global LINES
        LINES = {k:(v[0]*0.56 if k=="RL-09 숙박" else v[0],)+v[1:] for k,v in LINES.items()}
    s("숙박 보수안 (기준의 56%)", m3)
    def m4():
        global FUND_RATE; FUND_RATE = 0.0
    keep_fr = FUND_RATE; s("고유목적사업준비금 미적용", m4); FUND_RATE = keep_fr
    def m5():
        global BLDG_VALUE; BLDG_VALUE = 600.0
    keep_bv = BLDG_VALUE; s("재산세 과표 2배", m5); BLDG_VALUE = keep_bv

    print("\n[⑥] 기준선 비교 — 재임대 세후 27.1억")
    print("─"*W)
    for lab, sub in scen:
        rows = five(1, sub)
        marks = "".join("✓" if r['after']>=BASELINE_AFTER else "✗" for r in rows)
        yr = next((y for y,r in enumerate(rows,1) if r['after']>=BASELINE_AFTER), None)
        print(f"  {lab:22} 연차별 {marks}  → {'{}년차 돌파'.format(yr) if yr else '5년 내 미달'}")

    print("\n[⑦] C안 종단 확산분 — 별도 가산 (기본 계상 제외)")
    print("─"*W)
    print(f"  {'':16}" + "".join(f"{y}년차".rjust(11) for y in range(1,6)))
    print(f"  {'C안 매출':16}" + "".join(f"{c:>10.1f}억" for c in C_TRACK))
    import builtins
    g = globals()
    for lab, sub in scen:
        g['INCLUDE_C'] = False; base = five(1, sub)[4]['after']
        g['INCLUDE_C'] = True;  withc = five(1, sub)[4]['after']
        g['INCLUDE_C'] = False
        print(f"  {lab:22} 5년차 세후 {base:>5.1f}억 → C안 포함 {withc:>5.1f}억 ({withc-base:+.1f}억)")
    print(f"  ※ 만개 11.5억 = 도매 6.0 + IP 2.1 + 용역 3.4 (RL-16 아카데미는 위에 계상)")
    print(f"  ※ 전제 — 실판매 데이터 축적 후 2년차부터. R-12 전국사찰 수요조사가 선행")
