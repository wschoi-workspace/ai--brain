# -*- coding: utf-8 -*-
"""세금 + 5개년 전개 v1.0 — 계약서 제3조가 요구한 5개년 경제성 검토

지금까지 나온 모든 라인 검토는 ①1년차 ②세전 ③매출 중심이었다.
마스터 v0.2가 "이 문서의 숫자는 전부 매출입니다"라고 적어둔 공백이 여기서 메워진다.

세 가지를 한다.
  ① 라인별 영업이익을 통일 양식으로 모은다 (지금은 감가 전/후·CAPEX 포함/제외가 제각각)
  ② 세금을 계산한다 — 부가세 · 법인세 · 지방소득세 · 고유목적사업준비금
  ③ 5개년으로 편다 — 램프업 곡선 + CAPEX 투입 시점 + 누적 현금흐름
"""
def eok(v): return v/1e8
E = 1e8

TAX_BASIS = """
[세무 구조 — 근거]
◆ E-0174(A) 비영리내국법인은 수익사업 소득에만 법인세 납부의무.
            단 전시 입장료·상품 판매·F&B·유상 체험은 대부분 수익사업에 해당
◆ E-0172(A)/E-0531(A) ★법인세법 제29조 — 종교법인은 수익사업 소득의 50%까지
            고유목적사업준비금으로 손금산입 → 실효세율이 절반.
            단 5년 내 미사용 시 익금산입 + 이자상당액 추가 납부
◆ E-0167(A) 직영 A안 예상 법인세율 9~19% · 수익 직접 귀속 · 준비금 활용 가능
◆ E-0170(A) 별도법인 C안은 ★이중과세 + 준비금 활용 불가 + 부동산 이전 시 취득세·양도세
◆ E-0173(A) ★직영·위탁·별도법인·임대 4안 모두 재산세 과세로 전환 —
            어떤 구조를 택해도 현재의 재산세 면제는 상실된다
◆ E-0175(A) 지방세특례제한법 제50조 — 종교목적 취득세 면제분의 추징 가능성
            (단 과거 웨딩홀 임대 이력으로 이미 과세 전환됐을 수 있음)
◆ E-1049(A)/E-0438(A) 강남구청 2012년 '교인 외 일반 주민 이용 가능 여부' 기준으로
            소망교회 등 10곳 이상에 5억여 원 추징 (밀알복지재단 개별 3억 4,339만원)
◆ E-0562(A) ★공통 선결 게이트 2건 = 문체부 유권해석 + 직영 세무설계(수익사업 개시신고·구분회계)
            9.27 임기 만료 전 통과가 전체 전략의 임계경로

[법령 — 2026년 기준 · 웹 확인]
◆ 법인세율   2억 이하 9% / 2억~200억 19% / 200억~3,000억 21% / 3,000억 초과 24%
◆ 지방소득세 법인세액의 10%
◆ 법인세법 제29조 고유목적사업준비금 — 수익사업소득의 50% 한도 손금산입 · 5년 사용기한
◆ 부가가치세법 제26조①18 — 종교·자선·학술·구호 등 공익목적 단체가
   ★고유목적사업을 위해 '실비 또는 무상'으로 공급하는 재화·용역만 면세
   → F&B·리테일·숙박·유료 프로그램은 실비가 아니므로 과세
"""

# ═══════════════════════════════════════════════════════════════
# ① 라인별 통일 양식 — 매출 · 영업이익 · CAPEX
# ═══════════════════════════════════════════════════════════════
# margin 출처: S=리포트 산출값 / E=유사 라인에서 유추(추정)
LINES = {
 # 라인            매출   이익률  등급 CAPEX  램프업키  면세비율  출처
 "RL-01 전시":     (10.30, 0.181, "S", 16.7, "std",  0.00, "v1.2 영업이익 1.9억"),
 "RL-02 전통다원":  ( 4.60, 0.302, "S",  0.0, "std",  0.00, "5축 통합 이익률"),
 "RL-03 사찰음식":  (28.80, 0.302, "S", 14.6, "std",  0.00, "RL-03B 14.2억/47.1억"),
 "RL-04 리테일":   (19.00, 0.284, "S",  4.0, "std",  0.05, "5차 5.4억/19.0억 · 불교서적 면세"),
 "RL-05 교육":     ( 8.23, 0.304, "S",  3.22,"std",  0.10, "신규5.04(30.5%)+5축아카데미3.19(30.2%) · 어린이 공익분"),
 "RL-06 명상":     ( 6.64, 0.536, "S",  0.0, "fast", 0.00, "단독 구조C 4.09억/7.64억"),
 "RL-07 기업 B2B": ( 2.61, 0.400, "S",  0.0, "fast", 0.00, "겸임 기준 1.12억/2.78억"),
 "RL-08 대관":     ( 1.84, 0.600, "E",  0.0, "fast", 0.00, "원가율 40% 가정 — 02-대관BM 미확정"),
 "RL-09 숙박":     (18.50, 0.220, "E", 52.3, "slow", 0.00, "★통합 27.3%에서 명상 제외 추정"),
 "RL-10 멤버십":   (14.16, 0.550, "S",  0.0, "memb", 0.00, "v1.1 9.3억/16.9억"),
 "RL-11 장묘서비스":( 4.00, 0.600, "E",  0.0, "slow", 0.30, "의례 중심 고마진 추정 · 일부 실비"),
 "RL-13 시즌·야간": ( 4.28, 0.450, "E",  0.0, "std",  0.00, "★OPEX 미산출 — 부스료 고마진 추정"),
 "RL-16 아카데미":  ( 0.60, 0.300, "E",  0.0, "cplan",0.00, "RL-05 교육과 동일 구조"),
}
CAPEX_UNBOOKED = 0.0   # RL-10·RL-13의 개보수분 미분리 (리포트 명시)

# ═══════════════════════════════════════════════════════════════
# ② 램프업 곡선
# ═══════════════════════════════════════════════════════════════
RAMP = {
 "std":   [0.60, 0.85, 1.00, 1.00, 1.00],   # 일반 — 개관 3년차 정상화
 "fast":  [0.75, 0.95, 1.00, 1.00, 1.00],   # 공간 의존 낮음(B2B·명상·대관)
 "slow":  [0.50, 0.75, 0.90, 1.00, 1.00],   # 숙박·장묘 — 인지 축적 필요
 "memb":  [1.00, 1.34, 1.57, 1.72, 1.82],   # RL-10 v1.1 5개년 곡선(갱신 65%) 비례
 "cplan": [1.00, 1.50, 2.20, 2.80, 3.20],   # C안 — 실판매 데이터 축적 후 확산
}
YEARS = 5

# ═══════════════════════════════════════════════════════════════
# ③ CAPEX 투입 시점 — Phase
# ═══════════════════════════════════════════════════════════════
# RL-09 숙박은 자체 Phase 분할(리포트 §07) · 나머지는 개관 전 일괄
CAPEX_SCHEDULE = {
 "RL-09 숙박": {0: 23.3, 2: 19.9, 3: 9.1},   # 0=개관 전 · 2=2년차 말 · 3=3년차 말
}
def capex_year(name, total, y):
    """y: 0=개관전, 1~5=연차. 반환 억원"""
    if name in CAPEX_SCHEDULE:
        return CAPEX_SCHEDULE[name].get(y, 0.0)
    return total if y == 0 else 0.0

# ═══════════════════════════════════════════════════════════════
# ④ 세금
# ═══════════════════════════════════════════════════════════════
VAT_RATE = 0.10
PRICE_INCLUDES_VAT = True      # ★B2C 표시가는 부가세 포함이 관행 — 라인 리포트에 명시 없음
DEPR_YEARS = 12
FUND_RATE = 0.50               # 고유목적사업준비금 손금산입률 (법인세법 §29)
LOCAL_TAX = 0.10               # 지방소득세 = 법인세의 10%
PROPERTY_TAX_RATE = 0.004      # 재산세 추정 — 공시가 대비 (E-0173 과세 전환)
BLDG_VALUE = 300.0             # 봉은문화회관 해당분 공시가 추정(억) ※미확인

def corporate_tax(base_eok):
    """법인세 누진 (억원 입력)"""
    if base_eok <= 0: return 0.0
    t = 0.0
    if base_eok <= 2:      t = base_eok*0.09
    elif base_eok <= 200:  t = 2*0.09 + (base_eok-2)*0.19
    else:                  t = 2*0.09 + 198*0.19 + (base_eok-200)*0.21
    return t

def depr_year(y):
    """감가상각 — CAPEX 투입 시점 이후부터 상각한다"""
    d = 0.0
    for name,(rev, mgn, grade, capex, rk, exempt, src) in LINES.items():
        if name in CAPEX_SCHEDULE:
            for iy, amt in CAPEX_SCHEDULE[name].items():
                if y > iy:                     # iy년차 말 투입 → 다음 연차부터 상각
                    d += amt/DEPR_YEARS
        else:
            d += capex/DEPR_YEARS              # 개관 전 투입 → 1년차부터
    return d

def year_pnl(y):
    """y: 1~5"""
    gross = op = vat = 0.0
    for name,(rev, mgn, grade, capex, rk, exempt, src) in LINES.items():
        r = rev * RAMP[rk][y-1]
        gross += r
        v = r*(1-exempt) * (VAT_RATE/(1+VAT_RATE) if PRICE_INCLUDES_VAT else VAT_RATE)
        vat += v
        op += (r - v) * mgn                    # ★이익률은 공급가액(순매출) 기준으로 적용
    net_rev = gross - vat                      # 공급가액 기준 순매출
    op_net = op
    depr = depr_year(y)
    prop = BLDG_VALUE*PROPERTY_TAX_RATE
    ebit = op_net - depr - prop
    base = max(0.0, ebit*(1-FUND_RATE))        # 고유목적사업준비금 50% 손금산입
    ct = corporate_tax(base)
    lt = ct*LOCAL_TAX
    return dict(gross=gross, vat=vat, net=net_rev, op=op_net, depr=depr,
                prop=prop, ebit=ebit, base=base, ct=ct, lt=lt,
                after=ebit-ct-lt)

def totals():
    return [year_pnl(y) for y in range(1, YEARS+1)]

if __name__ == "__main__":
    W=104
    print("═"*W); print("세금 + 5개년 전개 v1.0 — 계약서 제3조 5개년 경제성 검토"); print("═"*W)

    print("\n[①] 라인별 통일 양식 — 정상 가동 기준")
    print("─"*W)
    print(f"  {'라인':16}{'매출':>8}{'이익률':>8}{'등급':>5}{'영업이익':>9}{'CAPEX':>8}  {'램프':>6}  출처")
    tr=to=tc=0
    for n,(rev,mgn,g,cap,rk,ex,src) in LINES.items():
        tr+=rev; to+=rev*mgn; tc+=cap
        print(f"  {n:16}{rev:>7.2f}억{mgn*100:>7.1f}%{g:>5}{rev*mgn:>8.2f}억{cap:>7.1f}억  {rk:>6}  {src}")
    print("  "+"─"*(W-2))
    print(f"  {'합계':16}{tr:>7.2f}억{to/tr*100:>7.1f}%{'':>5}{to:>8.2f}억{tc:>7.1f}억")
    ns = sum(1 for v in LINES.values() if v[2]=="E")
    print(f"  ※ 이익률 등급 E(추정) {ns}개 라인 — RL-08·09·11·13. 이 넷의 이익률이 결과를 흔든다")

    print("\n[②] 세금 — 1년차 기준")
    print("─"*W)
    p = year_pnl(1)
    rows = [("총매출 (VAT 포함)", p['gross']), ("  부가가치세", -p['vat']),
            ("순매출 (공급가액)", p['net']), ("영업이익 (감가·재산세 전)", p['op']),
            ("  감가상각", -p['depr']), ("  재산세", -p['prop']),
            ("세전이익 EBIT", p['ebit']),
            ("  고유목적사업준비금 50% 손금", -(p['ebit']-p['base'])),
            ("과세표준", p['base']), ("  법인세", -p['ct']), ("  지방소득세", -p['lt']),
            ("세후이익", p['after'])]
    for n,v in rows:
        print(f"  {n:30}{v:>10.2f}억")
    print(f"\n  실효세율 (EBIT 대비)          {(p['ct']+p['lt'])/p['ebit']*100:>9.1f}%")
    print(f"  준비금 없었다면               {corporate_tax(p['ebit'])*1.1/p['ebit']*100:>9.1f}%")
    print(f"  ★절세 효과                    {(corporate_tax(p['ebit'])*1.1-(p['ct']+p['lt'])):>9.2f}억")

    print("\n[③] 5개년 전개")
    print("─"*W)
    ts = totals()
    def row(label, key, fmt="{:>10.1f}억"):
        print(f"  {label:24}" + "".join(fmt.format(t[key]) for t in ts))
    print(f"  {'':24}" + "".join(f"{y}년차".rjust(11) for y in range(1,6)))
    row("총매출(VAT 포함)","gross"); row("부가가치세","vat"); row("순매출","net")
    row("영업이익","op"); row("감가상각","depr"); row("재산세","prop")
    row("세전이익 EBIT","ebit"); row("법인세","ct"); row("지방소득세","lt")
    row("★세후이익","after")
    print("  "+"─"*(W-2))
    cum=0; cums=[]
    for t in ts:
        cum+=t['after']; cums.append(cum)
    print(f"  {'세후이익 누적':24}" + "".join(f"{c:>10.1f}억" for c in cums))

    print("\n[④] 현금흐름 — CAPEX 투입 반영")
    print("─"*W)
    cap0 = sum(capex_year(n, v[3], 0) for n,v in LINES.items())
    print(f"  개관 전 CAPEX 투입            {-cap0:>10.1f}억")
    cf = -cap0; cfs=[]
    for y in range(1,6):
        t = ts[y-1]
        capy = sum(capex_year(n, v[3], y) for n,v in LINES.items())
        # 현금흐름 = 세후이익 + 감가상각(비현금) − 추가 CAPEX
        c = t['after'] + t['depr'] - capy
        cf += c; cfs.append((capy, c, cf))
    print(f"  {'':24}" + "".join(f"{y}년차".rjust(11) for y in range(1,6)))
    print(f"  {'추가 CAPEX':24}" + "".join(f"{-x[0]:>10.1f}억" for x in cfs))
    print(f"  {'연간 현금흐름':24}" + "".join(f"{x[1]:>10.1f}억" for x in cfs))
    print(f"  {'★누적 현금흐름':24}" + "".join(f"{x[2]:>10.1f}억" for x in cfs))
    tot_capex = cap0 + sum(x[0] for x in cfs)
    print(f"\n  총 CAPEX {tot_capex:.1f}억 · 5년 누적 현금흐름 {cfs[-1][2]:+.1f}억")
    if cfs[-1][2] < 0:
        print(f"  → ★5년 안에 회수되지 않는다. 부족분 {-cfs[-1][2]:.1f}억")
    yrs = None
    for i,x in enumerate(cfs,1):
        if x[2] >= 0: yrs = i; break
    print(f"  → 투자 회수 시점: {str(yrs)+'년차' if yrs else '5년 내 미도달'}")

    print("\n[⑤] 민감도 — 무엇이 결과를 흔드는가 (5년차 세후이익 기준)")
    print("─"*W)
    base5 = ts[-1]['after']
    def sens(label, mod):
        import copy
        global LINES, BLDG_VALUE, FUND_RATE, PRICE_INCLUDES_VAT
        keep = (dict(LINES), BLDG_VALUE, FUND_RATE, PRICE_INCLUDES_VAT)
        mod()
        v = year_pnl(5)['after']
        LINES, BLDG_VALUE, FUND_RATE, PRICE_INCLUDES_VAT = keep
        print(f"  {label:38}{v:>9.1f}억{v-base5:>+9.1f}억{(v-base5)/base5*100:>+8.1f}%")
    print(f"  {'기준안':38}{base5:>9.1f}억")
    def m1():
        global LINES
        LINES = {k:(v[0], v[1]-0.10 if v[2]=="E" else v[1], *v[2:]) for k,v in LINES.items()}
    sens("E등급 4개 라인 이익률 −10%p", m1)
    def m2():
        global FUND_RATE; FUND_RATE = 0.0
    sens("고유목적사업준비금 미적용", m2)
    def m3():
        global PRICE_INCLUDES_VAT; PRICE_INCLUDES_VAT = False
    sens("표시가가 VAT 별도였다면", m3)
    def m4():
        global BLDG_VALUE; BLDG_VALUE = 600.0
    sens("재산세 과표 2배 (600억)", m4)
    def m5():
        global LINES
        LINES = {k:(v[0]*0.8, *v[1:]) for k,v in LINES.items()}
    sens("전 라인 매출 −20%", m5)

    print("\n[⑥] 기준선 대비")
    print("─"*W)
    BASE = 30.0
    print(f"  웨딩홀 임대 기준선            {BASE:>10.1f}억  (임대료 수입 — 비용·세금 거의 없음)")
    for y in (1,3,5):
        t = ts[y-1]
        print(f"  {y}년차 세후이익               {t['after']:>10.1f}억  ({t['after']/BASE:.2f}x)")
    print(f"\n  ※ 기준선 30억은 '임대 수입'이라 세후 비교가 아니다.")
    print(f"     임대도 수익사업이므로 과세되며, 준비금 적용 시 세후 약 {30-corporate_tax(30*0.5)*1.1:.0f}억 수준")
