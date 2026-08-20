# -*- coding: utf-8 -*-
"""봉은문화센터 재무모델 v1.1 — 게이트 조건부 × 역산 하이브리드 · Destination 단일안 반영
계약 산출물 대응: 최종결과물③ 5개년 수지분석·경제성 / 계약 3조1항 사업계획서 / 3조2항 경제성 검토 / 과업 Ch.7

구성 (플랜 2026-08-17 승인):
  M1 수익  — model-v0.2.py 드라이버 이관 (3시나리오 × 게이트 3케이스)
  M2 비용  — 라인 이익률(tax-5yr 이관) + 공통 시설운영비 블록(신설·가정)
  M3 세무  — 부가세·법인세 누진·지방소득세·고유목적사업준비금 50%·재산세 (tax-5yr 이관)
  M4 5개년 — 2027~2031 캘린더 (Y1 부분운영·2028 개관 가정·램프업·라인별 CAPEX 시점)
  M5 판정  — 역산: 기준선 30억(세전)/약 27억(세후) 임계배수·BEP·회수기간·민감도

원칙: 방문객 절대수 추정 금지(상향식 드라이버만) · 유권해석 전 확정 불가는 게이트 케이스로만 ·
      모든 수치는 이 스크립트 재실행으로 재현(손계산 금지) · benchmarks.json 값 인입 시 자동 대체

── v1.1 변경 (2026-08-18, Destination 단일안 확정 반영) ──────────────────────
  ① RL-01 전시를 3,300㎡ 앵커안(v1.3)으로 확장 — 서브라인 3개로 분해
       a 입장   : 기존 드라이버 무변경 (v0.2 회귀 검증 대상)
       b 해설   : 신설. RL-01 검토서 v1.2 판정 "팔 것은 관람권이 아니라 해설"(해설 4.3억 > 입장 2.4억) 반영
       c 심화   : 신설. 검토서 v1.2 권고안 0.2/0.7/1.8억 이관
     ⚠️ 면적 확대는 매출 드라이버가 아니다. 3,300㎡의 효과는 '기획전 2트랙 동시 운영'이며
        그 수익 효과는 RL-08(기획사 대관 회전)에서 잡는다. 면적 비례 증액 금지.
  ② RL-08 대관 — 전용면적 1,500㎡ 폐지. 전시홀 기획전 트랙(A 1,200 + B 800 = 2,000㎡)의
     회기 사이 유휴 회전으로 전환. 면적 ↑, 가동일 ↓(60/100/140 → 40/70/100일).
     대공간 판매일 상한 152일(SETEC 실측 41.7%) 및 RL-07 B2B 34일 병행 제약은 유지.
  ③ RL-09 숙박 — Phase 2 강등. 권고경로는 G1L/G2L(숙박 제외). G1/G2는 비교용으로만 존치.
  ④ capex_lines RL-01 16.7 → 24.7억 (한계 CAPEX 43.3만원/㎡ × 1,750㎡ 초과분 · 추정)
"""
import json, os, copy

BASE = os.path.dirname(os.path.abspath(__file__))
INP = json.load(open(os.path.join(BASE, "inputs.json"), encoding="utf-8"))
BM  = json.load(open(os.path.join(BASE, "benchmarks.json"), encoding="utf-8"))

CASE = ["보수", "기준", "낙관"]
def eok(v): return v / 1e8

# ══════════════════════════════════════════════════════════════════
# M1 수익 — model-v0.2.py 드라이버 원본 이관 (검증: 코어 합계 19.7/66.7/139.3 재현)
# ══════════════════════════════════════════════════════════════════
FOREIGN = [100_000, 300_000, 609_390]   # E-1052 하한 / 중간 / E-0310 실측
DEVOTEE = [200_000, 200_000, 200_000]   # E-0513 (B)
FOR_IN  = [0.30, 0.45, 0.60]            # 문화센터 진입률 (C)
DEV_IN  = [0.40, 0.60, 0.80]            # (C)
CV = [int(FOREIGN[i]*FOR_IN[i] + DEVOTEE[i]*DEV_IN[i]) for i in range(3)]

LINES = {}
def add(code, name, gate, grade, amounts, driver, area=0, sub=None):
    LINES[code] = dict(code=code, name=name, gate=gate, grade=grade, amt=amounts, driver=driver, area=area,
                       sub=sub or {})

# ── RL-01 전시 · v1.3 앵커안 (전용 3,300㎡) ─────────────────────────────────
# 구성: 상설(무료·성보) 1,000 + 기획전A 1,200 + 기획전B 800 + 미디어아트 300 = 3,300㎡
# 상설·미디어아트는 매출 0(집객·법적 안전판). 유료 매출은 기획전 트랙에서만 발생.
c01=[0.12,0.18,0.20]; p01=[10_000,13_000,15_000]
R01a = [CV[i]*c01[i]*p01[i] for i in range(3)]                      # a 입장 — v0.2 원본 드라이버
PAID = [CV[i]*c01[i] for i in range(3)]                             # 유료 관람객 수
g01=[0.15,0.25,0.35]; pg01=[5_000,8_000,12_000]
R01b = [PAID[i]*g01[i]*pg01[i] for i in range(3)]                   # b 해설
R01c = [0.2e8, 0.7e8, 1.8e8]                                        # c 심화 프로그램 (검토서 v1.2 이관)
add("RL-01","전시 (입장·해설·심화)","T1","C",[R01a[i]+R01b[i]+R01c[i] for i in range(3)],
    "전용 3,300㎡ 앵커안 · a입장 CV×유료전환 12/18/20%(C)×티켓 1.0/1.3/1.5만(C) "
    "+ b해설 유료관람객×이용률 15/25/35%(C)×해설료 5/8/12천원(C·B-11 대기) "
    "+ c심화 0.2/0.7/1.8억(검토서 v1.2 이관·C)", 3300,
    sub={"a 입장": R01a, "b 해설": R01b, "c 심화": R01c})
s02=[60,80,80]; pr02=[15_000,20_000,25_000]; t02=[1.0,1.5,1.8]; d02=[300,330,350]
add("RL-02","F&B · 전통다원","COOK","B",[s02[i]*pr02[i]*t02[i]*d02[i] for i in range(3)],
    "좌석 60/80/80 × 객단가 1.5/2.0/2.5만(A·E-0149) × 회전 1.0/1.5/1.8 × 영업일 300/330/350", 400)
s03=[60,80,80]; pr03=[50_000,70_000,80_000]; t03=[1.0,1.4,1.8]; d03=[280,300,320]
add("RL-03","F&B · 사찰음식 다이닝","COOK","B",[s03[i]*pr03[i]*t03[i]*d03[i] for i in range(3)],
    "좌석 60/80/80 × 코스 5/7/8만(A·E-0182) × 회전 1.0/1.4/1.8 × 영업일 280/300/320", 600)
c04=[0.15,0.215,0.28]; p04=[6_400,9_000,12_000]
add("RL-04","리테일 · 상품판매","T1","B",[CV[i]*c04[i]*p04[i] for i in range(3)],
    "CV × 구매전환 15/21.5/28%(A·E-1006) × 객단가 6,400/9,000/12,000원(뮷즈 역산)", 800)
pr05=[50_000,70_000,100_000]; cap05=[16,16,20]; u05=[0.50,0.65,0.75]; n05=[300,600,800]
add("RL-05","교육 · 체험 클래스","T2","B",[pr05[i]*cap05[i]*u05[i]*n05[i] for i in range(3)],
    "회차단가 5/7/10만(B·E-1042) × 정원 16/16/20(E-1007) × 가동 50/65/75% × 연회차 300/600/800", 500)
pen06=[0.01,0.03,0.045]; f06=[10,20,25]; p06=[3_000,5_000,8_000]
add("RL-06","명상 프로그램 (B2C)","T2","B",[112_349*pen06[i]*f06[i]*p06[i] for i in range(3)],
    "도보권 112,349명(A·E-1021) × 침투 1/3/4.5% × 연이용 10/20/25회 × 회차권 3~8천원(E-1016)", 500)
pr07=[1_500_000,2_500_000,3_000_000]; n07=[30,80,120]
add("RL-07","기업 B2B 프로그램","T2","B",[pr07[i]*n07[i] for i in range(3)],
    "회당 150/250/300만(B·E-1040 채택, E-0581 격하) × 연 30/80/120건(C)", 0)
r08=[1_150,2_000,3_202]; d08=[40,70,100]
add("RL-08","대관 (전시홀 회기 회전)","T2","A",[2_000*r08[i]*d08[i] for i in range(3)],
    "전시 기획전 트랙 2,000㎡(A 1,200+B 800) × 단가 1,150/2,000/3,202원/㎡·일(A·E-1079) "
    "× 회기 사이 유휴 가동 40/70/100일(C·B-12 대기) — 전용면적 0", 0)
rm09=[10,20,25]; rt09=[100_000,120_000,150_000]; o09=[0.30,0.45,0.55]
add("RL-09","숙박 · 체류","T2","B",[rm09[i]*rt09[i]*o09[i]*365 for i in range(3)],
    "객실 10/20/25(C) × 박단가 10/12/15만(A·E-0428) × 가동 30/45/55% × 365일", 800)
cf=[5_000_000,7_500_000,10_000_000]; cn=[10,25,45]
ef=[5_000_000,6_500_000,8_000_000];  en=[20,40,55]
inf_=[300_000,400_000,500_000];      inn=[200,800,1_500]
add("RL-10","멤버십 · 구독","T2","B",[cf[i]*cn[i]+ef[i]*en[i]+inf_[i]*inn[i] for i in range(3)],
    "법인 500~1,000만×10/25/45사(E-1041) + 임원기수 500~800만×20/40/55명(E-1047) + 개인 30~50만×200/800/1,500명(C)", 0)

GATES = {g: set(v["lines"]) for g, v in INP["gates"].items()}
GATE_NAMES = {g: v["name"] for g, v in INP["gates"].items()}

def gate_lines(gate):
    return [L for c, L in LINES.items() if c in GATES[gate]]

# ══════════════════════════════════════════════════════════════════
# M2 비용 — 라인 이익률 + 공통 시설운영비
# ══════════════════════════════════════════════════════════════════
MARG = {k: v for k, v in INP["margins"].items() if not k.startswith("_")}
def bm_value(slot_id):
    for s in BM["slots"]:
        if s["id"] == slot_id and s.get("value") is not None:
            return s["value"]
    return None

_b01 = bm_value("B-01")
OPEX_M2 = _b01 if _b01 else INP["opex_common"]["per_m2_year_won"]   # 케이스별 원/㎡·년
AREA = INP["opex_common"]["area_m2"]
def common_opex(ci):  # 억원
    return OPEX_M2[CASE[ci]] * AREA / 1e8

# ══════════════════════════════════════════════════════════════════
# M3 세무 — tax-5yr 이관
# ══════════════════════════════════════════════════════════════════
T = INP["tax"]
def corporate_tax(base_eok):
    if base_eok <= 0: return 0.0
    prev, t = 0.0, 0.0
    for cap, rate in T["corporate_brackets"]:
        if base_eok <= cap:
            return t + (base_eok - prev) * rate
        t += (cap - prev) * rate; prev = cap
    return t + (base_eok - prev) * 0.24

def vat_of(rev_eok, exempt):
    r = T["vat_rate"]
    taxable = rev_eok * (1 - exempt)
    return taxable * (r / (1 + r)) if T["price_includes_vat"] else taxable * r

# ══════════════════════════════════════════════════════════════════
# M4 5개년 전개 — 2027~2031 · 개관 2028 · 램프업 · CAPEX 시점
# ══════════════════════════════════════════════════════════════════
CAL = INP["calendar"]; YEARS = CAL["years"]; OPEN = CAL["open_year"]
RAMP = INP["ramp"]; RASSIGN = RAMP["assign"]
DEPR_Y = INP["depreciation_years"]

def line_rev_year(L, ci, year, gate):
    """라인 L의 해당 연도 매출(억) — 게이트 소속·개관·램프업·Y1 부분운영 반영"""
    if L["code"] not in GATES[gate]: return 0.0
    base = eok(L["amt"][ci])
    if year < OPEN:
        return base * CAL["partial_y1"].get(L["code"], 0.0)
    idx = min(year - OPEN, 4)
    return base * RAMP[RASSIGN[L["code"]]][idx]

def capex_lines_year(gate, year):
    """라인별 CAPEX(억) — 개관 전년(OPEN-1)에 일괄, RL-09는 Phase 분할(개관 기준 상대연차)"""
    out = 0.0
    CL = INP["capex_lines_eok"]
    for code in GATES[gate]:
        if code not in CL: continue
        v = CL[code]
        if isinstance(v, dict):
            for off, amt in v["phase"].items():
                if year == (OPEN - 1) + int(off): out += amt
        else:
            if year == OPEN - 1: out += v
    return out

def building_capex(ci):
    return INP["capex_building"]["cases_eok"][CASE[ci]]

def depr_year(gate, ci, year):
    """감가상각(억) — 건물분은 개관연도부터, 라인분은 투입 익년부터 정액 12년"""
    d = 0.0
    if year >= OPEN: d += building_capex(ci) / DEPR_Y
    CL = INP["capex_lines_eok"]
    for code in GATES[gate]:
        if code not in CL: continue
        v = CL[code]
        pairs = [((OPEN - 1) + int(o), a) for o, a in v["phase"].items()] if isinstance(v, dict) else [(OPEN - 1, v)]
        for iy, amt in pairs:
            if year > iy: d += amt / DEPR_Y
    return d

def year_pnl(gate, ci, year, rev_scale=1.0, margins=None, opex_mult=1.0, fund_rate=None):
    margins = margins or MARG
    fund = T["fund_rate"] if fund_rate is None else fund_rate
    gross = vat = op = 0.0
    for L in gate_lines(gate):
        r = line_rev_year(L, ci, year, gate) * rev_scale
        m = margins[L["code"]]
        v = vat_of(r, m["vat_exempt"])
        gross += r; vat += v
        op += (r - v) * m["margin"]
    opex_f = INP.get("pre_open_opex_factor", 1.0) if year < OPEN else 1.0
    op -= common_opex(ci) * opex_mult * opex_f
    depr = depr_year(gate, ci, year)
    prop = T["building_value_eok"] * T["property_tax_rate"]
    ebit = op - depr - prop
    tax_base = max(0.0, ebit * (1 - fund))
    ct = corporate_tax(tax_base); lt = ct * T["local_tax_on_corp"]
    return dict(year=year, gross=gross, vat=vat, net=gross - vat, op=op,
                depr=depr, prop=prop, ebit=ebit, ct=ct, lt=lt, after=ebit - ct - lt)

def steady_pnl(gate, ci, **kw):
    """정상가동(램프업 완료·개관 4년차 이후) 연간 손익"""
    return year_pnl(gate, ci, OPEN + 4, **kw)

def five_year(gate, ci):
    return [year_pnl(gate, ci, y) for y in YEARS]

def total_capex(gate, ci):
    CL = INP["capex_lines_eok"]
    line_sum = 0.0
    for code in GATES[gate]:
        if code in CL:
            v = CL[code]
            line_sum += v["total"] if isinstance(v, dict) else v
    return building_capex(ci) + line_sum

def payback(gate, ci, horizon=15):
    """누적 현금흐름(세후이익+감가−CAPEX)이 0 이상이 되는 개관 후 연차"""
    cum = -building_capex(ci)
    cum -= capex_lines_year(gate, OPEN - 1)  # 개관 전 라인 투자
    years_out = []
    for k in range(0, horizon):
        y = OPEN + k
        p = year_pnl(gate, ci, y) if y <= YEARS[-1] else year_pnl(gate, ci, YEARS[-1])
        # RL-09 후속 Phase 투자
        extra = capex_lines_year(gate, y) if y > OPEN - 1 else 0.0
        cum += p["after"] + p["depr"] - extra
        years_out.append(cum)
        if cum >= 0: return k + 1, years_out
    return None, years_out

# ══════════════════════════════════════════════════════════════════
# M5 역산 판정 — 임계배수·BEP·기준선
# ══════════════════════════════════════════════════════════════════
BASELINE = INP["baseline"]["value_eok"]
BASELINE_AT = BASELINE - corporate_tax(BASELINE * (1 - T["fund_rate"])) * (1 + T["local_tax_on_corp"])  # 임대도 과세 시 세후

def solve_scale(gate, ci, target_after):
    """정상가동 세후이익이 target 이상이 되는 매출 배수 k (이분법)"""
    lo, hi = 0.05, 12.0
    if steady_pnl(gate, ci, rev_scale=hi)["after"] < target_after: return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if steady_pnl(gate, ci, rev_scale=mid)["after"] >= target_after: hi = mid
        else: lo = mid
    return round(hi, 3)

def judge(gate, ci):
    sp = steady_pnl(gate, ci)
    pb, _ = payback(gate, ci)
    ocf = sp["after"] + sp["depr"]           # 영업현금흐름(감가 환입) — 재임대 30억과의 현금 비교용
    return dict(
        gate=gate, case=CASE[ci],
        steady_rev=round(sp["gross"], 1), steady_after=round(sp["after"], 1),
        steady_ocf=round(ocf, 1),
        vs_baseline_pre=round(sp["after"] / BASELINE, 2),
        vs_baseline_at=round(sp["after"] / BASELINE_AT, 2),
        meets_baseline=bool(sp["after"] >= BASELINE_AT),
        ocf_vs_baseline=round(ocf / BASELINE, 2),
        bep_k=solve_scale(gate, ci, 0.0),
        req_k_baseline=solve_scale(gate, ci, BASELINE_AT),
        total_capex=round(total_capex(gate, ci), 1),
        payback_yrs=pb)

def sensitivity(gate="G2", ci=1):
    base = steady_pnl(gate, ci)["after"]
    out = [("기준", round(base, 1), 0.0)]
    def rec(label, **kw):
        v = steady_pnl(gate, ci, **kw)["after"]
        out.append((label, round(v, 1), round(v - base, 1)))
    m2 = copy.deepcopy(MARG)
    for k, v in m2.items():
        if v["grade"] == "E": v["margin"] = max(0.0, v["margin"] - 0.10)
    rec("E등급 이익률 −10%p", margins=m2)
    m3 = copy.deepcopy(MARG)
    for k, v in m3.items(): v["margin"] = max(0.0, v["margin"] - 0.05)
    rec("전 라인 이익률 −5%p (보수 고정비 리스크)", margins=m3)
    rec("공통 운영비 +50%", opex_mult=1.5)
    rec("매출 −20%", rev_scale=0.8)
    rec("고유목적사업준비금 미적용", fund_rate=0.0)
    return out

# ══════════════════════════════════════════════════════════════════
# 실행 — 재현 검증 + 전체 그리드 산출
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    W = 110
    print("═"*W); print("봉은문화센터 재무모델 v1.1 — 게이트 조건부 × 역산 하이브리드 · Destination 단일안"); print("═"*W)

    # [회귀 검증] v0.2 원본 드라이버 재현 — v1.1 변경분(RL-01 해설·심화, RL-08 회전)을 되돌린 값으로 대조
    core_v02 = [sum(eok(L["amt"][i]) for c, L in LINES.items() if c not in ("RL-01", "RL-08"))
                + eok(R01a[i]) + eok(1_500 * r08[i] * [60, 100, 140][i]) for i in range(3)]
    print(f"\n[회귀] v0.2 원본 드라이버 재현: 보수 {core_v02[0]:.1f} / 기준 {core_v02[1]:.1f} / 낙관 {core_v02[2]:.1f} 억  (기대 19.7/66.7/139.3)")
    assert all(abs(core_v02[i] - e) < 0.15 for i, e in enumerate([19.7, 66.7, 139.3])), "v0.2 재현 실패"
    print("        → 일치 ✓  (v1.1 변경분을 되돌리면 원본과 동일 — 나머지 8개 라인 무손상)")

    # [v1.1] Destination 단일안 반영 코어 합계
    core = [sum(eok(L["amt"][i]) for L in LINES.values()) for i in range(3)]
    print(f"[v1.1] 코어 10 합계: 보수 {core[0]:.1f} / 기준 {core[1]:.1f} / 낙관 {core[2]:.1f} 억"
          f"  (v0.2 대비 {core[0]-core_v02[0]:+.1f}/{core[1]-core_v02[1]:+.1f}/{core[2]-core_v02[2]:+.1f})")
    for lab, vals in LINES["RL-01"]["sub"].items():
        print(f"        RL-01 {lab:<6}{eok(vals[0]):>6.2f}억 /{eok(vals[1]):>6.2f}억 /{eok(vals[2]):>6.2f}억")
    print(f"        RL-08 회전  {eok(LINES['RL-08']['amt'][0]):>6.2f}억 /{eok(LINES['RL-08']['amt'][1]):>6.2f}억 "
          f"/{eok(LINES['RL-08']['amt'][2]):>6.2f}억   (전용면적 0 · v0.2 대비 "
          f"{eok(LINES['RL-08']['amt'][1] - 1_500*r08[1]*100):+.2f}억)")
    print(f"[기준선] 재임대 연 {BASELINE:.0f}억(세전) · 임대 과세 반영 시 세후 약 {BASELINE_AT:.1f}억 — 판정은 세후 기준")

    # 게이트 × 시나리오 판정 그리드
    print("\n" + "═"*W); print("게이트 × 시나리오 — 정상가동 판정 그리드"); print("═"*W)
    hdr = f"{'게이트':<24}{'케이스':<6}{'매출':>8}{'세후이익':>9}{'현금흐름':>9}{'vs기준선':>9}{'판정':>5}{'BEP배수':>8}{'필요배수':>9}{'총투자':>8}{'회수':>7}"
    print(hdr); print("-"*W)
    grid = []
    for g in ("G0", "G1", "G1L", "G2", "G2L"):
        for ci in range(3):
            j = judge(g, ci); grid.append(j)
            pb = f"{j['payback_yrs']}년" if j["payback_yrs"] else "15+년"
            rk = f"{j['req_k_baseline']:.2f}x" if j["req_k_baseline"] else "도달불가"
            bk = f"{j['bep_k']:.2f}x" if j["bep_k"] else "—"
            mark = "✓" if j["meets_baseline"] else "✗"
            print(f"{GATE_NAMES[g]:<24}{j['case']:<6}{j['steady_rev']:>7.1f}억{j['steady_after']:>8.1f}억{j['steady_ocf']:>8.1f}억{j['vs_baseline_at']:>8.2f}x{mark:>4}{bk:>8}{rk:>9}{j['total_capex']:>7.1f}억{pb:>7}")
        print("-"*W)

    # 5개년 — 권고 케이스(G1·기준 / G2·기준)
    for g in ("G1L", "G2L"):
        print(f"\n[5개년 수지 — {GATE_NAMES[g]} · 기준 케이스]  (2027=부분운영, 2028 개관 가정)")
        ys = five_year(g, 1)
        print("  " + "".join(f"{y['year']}".rjust(10) for y in ys))
        for lab, key in [("총매출","gross"),("부가세","vat"),("영업이익*","op"),("감가상각","depr"),("EBIT","ebit"),("세후이익","after")]:
            print(f"  {lab:<10}" + "".join(f"{y[key]:>9.1f}억" for y in ys))
        print("   *공통 운영비 차감 후")

    # 민감도
    print("\n[민감도 — G2·기준, 정상가동 세후이익]")
    for lab, v, d in sensitivity():
        print(f"  {lab:<34}{v:>8.1f}억  {('' if d==0 else f'{d:+.1f}억')}")

    # JSON 산출
    out = dict(
        meta=dict(version="1.1", date="2026-08-18", baseline_pre=BASELINE, baseline_after=round(BASELINE_AT,1),
                  core_check=[round(c,1) for c in core], core_v02=[round(c,1) for c in core_v02],
                  recommended_path="G2L", note="RL-01 3,300㎡ 앵커안 · RL-08 전시홀 회기 회전 · RL-09 Phase2 강등"),
        lines={c: dict(name=L["name"], gate=L["gate"], grade=L["grade"],
                       rev=[round(eok(L["amt"][i]),1) for i in range(3)], driver=L["driver"], area=L["area"],
                       sub={k:[round(eok(v[i]),2) for i in range(3)] for k,v in L["sub"].items()}) for c, L in LINES.items()},
        common_opex={CASE[i]: round(common_opex(i),1) for i in range(3)},
        grid=grid,
        five_year={g: {CASE[ci]: [ {k: round(v,2) if isinstance(v,float) else v for k,v in y.items()} for y in five_year(g,ci)] for ci in range(3)} for g in ("G0","G1","G1L","G2","G2L")},
        sensitivity=sensitivity(),
        pending_benchmarks=[s["id"] for s in BM["slots"] if s.get("value") is None])
    with open(os.path.join(BASE, "out", "finance-model.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n→ out/finance-model.json 저장 · 대기 벤치마크 슬롯 {len(out['pending_benchmarks'])}건")
