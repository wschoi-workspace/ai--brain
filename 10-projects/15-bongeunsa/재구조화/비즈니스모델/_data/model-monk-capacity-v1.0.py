# -*- coding: utf-8 -*-
"""진행 인력 통합 상한 v1.0 — 세 검토가 각각 지목했으나 아무도 계산하지 않은 값

문제: RL-05·RL-06·RL-07이 각각 "진행 인력이 병목"이라 선언하고 끝냈다.
      마스터 v0.2는 RL-05 낙관을 900→800회로 깎으며 사유를 '진행자 공급 상한'이라 적었으나
      그 상한이 얼마인지는 어디에도 없다. model-reconcile-v1.0은 MONK_SESSIONS_YR_CAP = None.

방법: 봉은사 보유 인력 수가 미확인이므로 상한을 직접 셀 수 없다.
      → 필요량을 역산하고 업계 표준·종단 자원과 대조해 조달 가능성으로 판정한다.

핵심 1: 풀은 하나가 아니라 셋이다. 성격이 달라 상한의 의미가 다르다.
        S 스님 전속 — 살 수 없다 / D 지도법사 — 시간이 걸린다(양성) / X 외부 강사 — 돈이면 된다
핵심 2: FTE 총량보다 분야 분할이 먼저 터진다.
        한 사람이 사찰음식·불교학·다도·공방·어린이·외국어를 다 하지 못한다(RL-05가 지목).
        분야별로 올림하면 총량 FTE보다 훨씬 많은 사람이 필요하다.
"""
import math
def eok(v): return v/1e8
CASE = ["보수", "기준", "낙관"]

BENCH = """
[상한의 근거가 될 뻔한 것들 — 전부 봉은사 자체 수치가 아니다]
◆ E-0880(A) 템플스테이 사찰당 평균 운영인력 2.27명 · 퇴직 지도법사 1년 미만 60%·실무자 66%
             20년이 지난 2022년 국회 세미나에서도 인력 안정화가 미해결 과제
◆ E-0874(A) 템플스테이 운영 표준 — 지도법사 배치 + 전담실무자 1인 이상 4대보험 (최소 요건)
◆ E-0873(A) 지정요건에 '지도법사·실무자 배치' 명시 · 예비운영 1년
◆ E-0884(B) 조계종 선명상 — 전국 50여 곳 · 핵심 운영사찰 40곳 · 지도자 100여 명
             → 사찰당 약 2명. 봉은사가 종단에서 끌어올 수 있는 유일한 기성 풀
◆ E-0511(C) 봉은 사찰음식문화연구소 (소장 우관 스님) — 조직은 이미 있다
◆ E-0435(A) 조계종 사찰음식 3기관 분업(체험관·향적세계·발우공양)
◆ E-0431(B) 선재사찰음식문화센터 — 명장 1호가 이미 강좌를 운영 중
             → 사찰음식 강사는 종단 안에서 가져오는 경로가 있다
◆ E-0605(B) 셰프 승려 초빙 게스트 = 상시 운영 부담 없이 최고 단가
◆ E-0644(A) 지도자 양성 과정 — 졸업생이 다시 공급자가 되는 재생산 구조
◆ E-0481(A) 왓포 — 사원 내 정규 교육기관이 강사:학생 1:6으로 공급을 자가 재생산
◆ E-0659(B) 기업 연수 프리미엄 = "공간이 아니라 진행 주체를 판다" → 스님 대체 불가
◆ E-0639(B) 몽크챗 = 스님이 있어야 성립하는 상품 그 자체

🔴 봉은사 현재 상주 스님 수 · 지도 가능 인원은 요소 775건 어디에도 없다.
   E-0339(C) 신도 5~10만 추정조차 "종무 자료로 실측해야 한다"고 단서가 붙어 있다.
"""

FTE_HOURS  = 1_800      # 연간 1인 가동시간 (RL-05 model-edu-v1.0 전제 계승)
PREP_RATIO = 0.6        # 준비·정리 (진행시간 대비) — 동일 전제 계승
WEEKS      = 50

# ═══════════════════════════════════════════════════════════════
# ① 프로그램 원장 — 라인별 최신 검토값 (마스터 v0.2 아님)
# ═══════════════════════════════════════════════════════════════
# (라인, 프로그램, 회차[보수,기준,낙관], 진행시간h, 풀, 분야, 기준안매출억, 비고)
S, D, X = "S 스님", "D 지도법사", "X 외부강사"

PROGRAMS = [
    # ── RL-06 명상 (본 검토 v1.0) ─────────────────────────────
    ("RL-06", "드롭인 명상 클래스",   [300, 500, 700], 1.00, D, "명상",     2.250, ""),
    ("RL-06", "1일 선 리트리트",      [ 40,  60,  80], 6.00, D, "명상",     0.972, "종일"),
    ("RL-06", "스님과의 대화",        [150, 250, 350], 0.75, S, "몽크챗",   1.050, "스님 아니면 상품이 성립 안 됨 E-0639"),
    # 점심 선·선잠은 무인 — 진행 인력 0

    # ── RL-05 교육·체험 (model-edu-v1.0) ──────────────────────
    ("RL-05", "다도·차담·필사",       [120, 250, 340], 2.50, D, "다도",     1.820, ""),
    ("RL-05", "공방·메이커",          [ 80, 150, 220], 2.50, X, "공방",     0.864, ""),
    ("RL-05", "청소년·어린이",        [ 60, 100, 140], 2.00, X, "어린이",   0.390, ""),
    ("RL-05", "원데이 사찰음식",      [ 60, 120, 180], 3.00, X, "사찰음식", 1.248, "조리 게이트 E-0041"),
    ("RL-05", "불교 아카데미",        [ 24,  36,  48], 2.00, S, "불교학",   0.270, "교리 — 스님"),
    ("RL-05", "지도자 양성 과정",     [ 15,  30,  30], 3.00, S, "불교학",   0.480, "권위 필요 · 단 공급 재생산 E-0644"),
    ("RL-05", "사찰음식 전문가 과정", [ 10,  20,  30], 3.00, X, "사찰음식", 0.384, "조리 게이트"),

    # ── RL-07 기업 B2B (model-b2b-v1.0) ───────────────────────
    ("RL-07", "T0 출강형 특강",       [ 16,  45, 100], 4.00, D, "명상",     0.540, "진행2h+이동2h · 고객사×연회차"),
    ("RL-07", "T1 내방 매스형",       [  6,  18,  24], 3.00, D, "명상",     0.756, ""),
    ("RL-07", "T2 프리미엄 리트리트", [  4,  12,  18], 8.00, S, "몽크챗",   0.480, "종일 · E-0659 진행 주체를 판다"),
    ("RL-07", "T3 연간계약 세션",     [  4,  16,  36], 3.00, D, "명상",     1.000, "T3_N × T3_SESSION"),
]

# ── 별도 취급 항목 ────────────────────────────────────────────
# RL-09 예불: 주 14회 × 52 = 728회. 그러나 이것은 신규 부담이 아니다.
#   봉은사는 지금도 새벽·저녁 예불을 하고 있고, 투숙객은 '기존 예불에 참여'한다.
#   증분은 투숙객 안내·영어 해설분만.
YEBUL_TOTAL   = 728
YEBUL_INCR_HR = [0.25, 0.25, 0.25]    # 회당 증분(안내·해설)만
YEBUL_SESS    = [365, 500, 600]        # 투숙객이 있는 날만

# RL-09 몽크챗: model-stay-v1.0의 명상 라인은 RL-06과 같은 상품이다.
#   reconcile v1.0이 RL-06 810과 RL-09 250을 각각 더해 이중계상 중.
DOUBLE_COUNTED = 250

# RL-01 해설·도슨트: 별도 풀(해설사). RL-05 트랙 D가 "RL-01이 이미 계상"으로 0 처리.
#   인력 풀도 분리 — 도슨트는 스님·지도법사가 아니다. 본 모델 범위 밖(경고만).

# ═══════════════════════════════════════════════════════════════
# ② 소요 시간 집계
# ═══════════════════════════════════════════════════════════════
def hours(prog, i):
    _, _, n, hr, *_ = prog
    return n[i] * hr * (1 + PREP_RATIO)

def by_pool(i):
    d = {S: 0.0, D: 0.0, X: 0.0}
    for p in PROGRAMS:
        d[p[4]] += hours(p, i)
    d[S] += YEBUL_SESS[i] * YEBUL_INCR_HR[i] * (1 + PREP_RATIO)
    return d

def by_domain(i):
    d = {}
    for p in PROGRAMS:
        d.setdefault((p[4], p[5]), 0.0)
        d[(p[4], p[5])] += hours(p, i)
    d[(S, "예불·의례")] = YEBUL_SESS[i] * YEBUL_INCR_HR[i] * (1 + PREP_RATIO)
    return d

def sessions(i):
    return sum(p[2][i] for p in PROGRAMS)

# ═══════════════════════════════════════════════════════════════
# ③ 필요 인원 — 총량 FTE vs 분야 분할
# ═══════════════════════════════════════════════════════════════
def fte_flat(i):
    """총량만 본 필요 인원 — 한 사람이 무엇이든 한다고 가정한 비현실 하한"""
    return {k: v / FTE_HOURS for k, v in by_pool(i).items()}

def fte_domain(i, min_one=True):
    """분야별로 올림 — 한 분야에 최소 1명. 현실적 필요 인원"""
    out = {}
    for (pool, dom), h in by_domain(i).items():
        need = h / FTE_HOURS
        out[(pool, dom)] = max(1, math.ceil(need)) if (min_one and h > 0) else math.ceil(need)
    return out

def headcount(i):
    d = fte_domain(i)
    r = {S: 0, D: 0, X: 0}
    for (pool, _), n in d.items():
        r[pool] += n
    return r

# ═══════════════════════════════════════════════════════════════
# ④ 대조군 — 조달 가능성 판정
# ═══════════════════════════════════════════════════════════════
TEMPLE_AVG_STAFF = 2.27      # E-0880 사찰당 평균 운영인력
SEON_LEADERS_NAT = 100       # E-0884 종단 선명상 지도자 (전국)
SEON_SITES       = 50        # E-0884 전국 50여 곳
SEON_PER_SITE    = SEON_LEADERS_NAT / SEON_SITES     # 사찰당 약 2명

# ═══════════════════════════════════════════════════════════════
# ⑤ 역산 — 인력 상한을 먼저 정하면 회차는 얼마인가
# ═══════════════════════════════════════════════════════════════
def capacity_given(pool_staff, i):
    """풀별 인원이 주어졌을 때 소화 가능 시간과 청구 시간의 비"""
    need = by_pool(i)
    return {k: (pool_staff.get(k, 0) * FTE_HOURS) / need[k] if need[k] else float('inf')
            for k in (S, D, X)}

# ── 단일 장애점 — 분야당 1명은 사람이 나가면 상품이 정지한다 ──
# E-0880: 지도법사 1년 미만 퇴직 60% · 실무자 66%. 분야당 1명 편성은 그 확률에 상품을 건다.
CRITICAL = {("S 스님", "몽크챗"), ("D 지도법사", "명상")}   # 매출 기여가 큰 분야 = 백업 필수

def headcount_backup(i):
    """핵심 분야에 백업 1명씩 — 이탈 리스크를 반영한 현실 편성"""
    d = fte_domain(i)
    r = {S: 0, D: 0, X: 0}
    for key, n in d.items():
        pool, _ = key
        r[pool] += n + (1 if key in CRITICAL else 0)
    return r

def revenue_at_risk(i):
    """분야가 비면 죽는 매출 — 각 라인 모델의 상품별 실매출(기준안)을 그대로 귀속시킨다.
    회차 비례 배분은 단가 차이를 뭉갠다(몽크챗 3.5만 vs 리트리트 9만).
    보수·낙관은 기준안 매출 × 회차비 근사 — 방향만 본다."""
    out = {}
    for p in PROGRAMS:
        key = (p[4], p[5])
        scale = (p[2][i] / p[2][1]) if p[2][1] else 0
        out[key] = out.get(key, 0) + p[6] * scale
    out[(S, "예불·의례")] = 0.0
    return out

if __name__ == "__main__":
    W = 100
    print("═" * W)
    print("진행 인력 통합 상한 v1.0 — RL-05 · RL-06 · RL-07 · RL-09")
    print("═" * W)

    print("\n[0] 기존 원장의 오류 3건 — 합산 전에 정리해야 한다")
    print("─" * W)
    print(f"  ① 이중계상 — reconcile v1.0이 'RL-06 유인 810' + 'RL-09 몽크챗 250'을 각각 더함.")
    print(f"     model-stay-v1.0의 명상 라인 = RL-06과 같은 상품 → {DOUBLE_COUNTED}회 중복 제거")
    print(f"  ② 누락     — RL-07을 T2 12회만 계상. 실제로는 T0·T1·T3도 사람이 진행한다")
    t07 = sum(p[2][1] for p in PROGRAMS if p[0] == "RL-07")
    print(f"     RL-07 기준안 실제 진행 회차 {t07}회 (T0 45 + T1 18 + T2 12 + T3 16) — 계상의 {t07/12:.1f}배")
    print(f"  ③ 구값     — RL-05를 마스터 v0.2의 600회로 계상. model-edu-v1.0 기준안은 706회")
    print(f"  ④ 과대계상 — RL-09 예불 728회를 신규 부담으로 계상. 봉은사는 지금도 예불을 한다")
    print(f"     → 투숙객 안내·해설 증분(회당 {YEBUL_INCR_HR[1]}h)만 계상")

    print("\n[1] 청구 원장 — 정리 후")
    print("─" * W)
    print(f"{'라인':8}{'프로그램':22}{'풀':10}{'분야':10}{'보수':>8}{'기준':>8}{'낙관':>8}{'시간':>7}")
    for p in PROGRAMS:
        print(f"{p[0]:8}{p[1]:22}{p[4]:10}{p[5]:10}"
              f"{p[2][0]:>8,}{p[2][1]:>8,}{p[2][2]:>8,}{p[3]:>6.2f}h")
    print(f"{'RL-09':8}{'예불 안내(증분)':22}{S:10}{'예불·의례':10}"
          f"{YEBUL_SESS[0]:>8,}{YEBUL_SESS[1]:>8,}{YEBUL_SESS[2]:>8,}{YEBUL_INCR_HR[1]:>6.2f}h")
    print("─" * W)
    for i in range(3):
        pass
    print(f"{'합계 진행회차':30}" + "".join(f"{sessions(i)+YEBUL_SESS[i]:>18,}회" for i in range(3)))
    print(f"{'  = 주당':30}" + "".join(f"{(sessions(i)+YEBUL_SESS[i])/WEEKS:>17,.1f}회" for i in range(3)))

    print("\n[2] 풀별 소요 시간과 총량 FTE")
    print("─" * W)
    print(f"{'':16}" + "".join(f"{c:>27}" for c in CASE))
    for pool in (S, D, X):
        row = f"{pool:16}"
        for i in range(3):
            h = by_pool(i)[pool]
            row += f"{h:>14,.0f}h ({h/FTE_HOURS:>4.1f}FTE)"
        print(row)
    print("─" * W)
    row = f"{'총계':16}"
    for i in range(3):
        h = sum(by_pool(i).values())
        row += f"{h:>14,.0f}h ({h/FTE_HOURS:>4.1f}FTE)"
    print(row)

    print("\n[3] ★분야 분할 — 한 사람이 여섯 분야를 다 하지 못한다")
    print("─" * W)
    print(f"{'풀':10}{'분야':12}" + "".join(f"{c+' FTE':>12}{'인원':>6}" for c in CASE))
    doms = sorted(set(list(by_domain(0).keys()) + list(by_domain(2).keys())))
    for key in doms:
        pool, dom = key
        row = f"{pool:10}{dom:12}"
        for i in range(3):
            h = by_domain(i).get(key, 0)
            row += f"{h/FTE_HOURS:>12.2f}{fte_domain(i).get(key,0):>6}"
        print(row)
    print("─" * W)
    for i in range(3):
        hc = headcount(i)
        flat = fte_flat(i)
        print(f"{CASE[i]:6} 분야 올림 후 필요 인원  S {hc[S]}명 · D {hc[D]}명 · X {hc[X]}명 = "
              f"총 {sum(hc.values())}명   "
              f"(총량 FTE는 {sum(flat.values()):.1f}명 — 분할 손실 {sum(hc.values())-sum(flat.values()):.1f}명)")

    print("\n[4] 조달 가능성 — 봉은사 보유 인력이 미확인이므로 표준과 대조한다")
    print("─" * W)
    print(f"  대조군 ① 템플스테이 사찰당 평균 운영인력  {TEMPLE_AVG_STAFF}명 (상근 FTE)  (E-0880 A)")
    print(f"  대조군 ② 종단 선명상 지도자 사찰당 배분   {SEON_PER_SITE:.1f}명   (E-0884 B · 전국 100명/50곳)")
    print()
    for i in range(3):
        hc = headcount(i)
        sd = hc[S] + hc[D]
        print(f"  {CASE[i]:4} 사찰 내부가 대야 하는 인원(S+D) {sd:>2}명 = "
              f"업계 표준의 {sd/TEMPLE_AVG_STAFF:>4.1f}배 · 종단 배분분의 {sd/SEON_PER_SITE:>4.1f}배 "
              f"· 외부 조달 가능(X) {hc[X]}명")

    print("\n[5] ★인원은 회차에 거의 반응하지 않는다 — 상한의 성격이 다르다")
    print("─" * W)
    print(f"{'':10}{'진행회차':>12}{'총량 FTE':>12}{'분야 인원':>12}{'회차 배수':>12}{'인원 배수':>12}{'1인당 회차':>13}")
    base_s, base_h = sessions(0) + YEBUL_SESS[0], sum(headcount(0).values())
    for i in range(3):
        s = sessions(i) + YEBUL_SESS[i]
        hc = sum(headcount(i).values())
        f = sum(fte_flat(i).values())
        print(f"{CASE[i]:10}{s:>11,}회{f:>11.1f}명{hc:>11}명"
              f"{s/base_s:>11.2f}배{hc/base_s*base_s/base_h*base_h/hc if False else hc/base_h:>11.2f}배{s/hc:>12,.0f}회")
    print()
    print("  🔴 회차가 2.3배로 늘어도 인원은 1.13배(8→9명)다. **인력은 변동비가 아니라 진입비용이다.**")
    print("     그래서 마스터가 '진행자 공급 상한'을 이유로 회차를 900→800으로 깎은 것은")
    print("     상한을 잘못 이해한 조정이다 — 회차를 깎아도 필요 인원은 줄지 않는다.")
    print("     제약은 「몇 회를 하는가」가 아니라 「몇 분야를 여는가」에 걸린다.")

    print("\n[6] ★단일 장애점 — 분야당 1명은 그 사람이 나가면 상품이 정지한다")
    print("─" * W)
    print(f"  E-0880(A) 지도법사 1년 미만 퇴직 60% · 실무자 66%. 분야당 1명 편성은 그 확률에 상품을 건다.")
    print()
    rar = revenue_at_risk(1)
    print(f"{'풀':10}{'분야':12}{'기준 인원':>10}{'귀속 매출':>12}{'상태':>26}")
    for key in sorted(fte_domain(1).keys()):
        pool, dom = key
        n = fte_domain(1)[key]
        rv = rar.get(key, 0)
        st = "🔴 단일 장애점 — 백업 필요" if key in CRITICAL else ("⚠️  단일 담당" if n == 1 else "")
        print(f"{pool:10}{dom:12}{n:>9}명{rv:>11.2f}억{st:>26}")
    print("─" * W)
    for i in range(3):
        hb = headcount_backup(i); h0 = headcount(i)
        print(f"  {CASE[i]:4} 백업 반영 전 {sum(h0.values())}명 → 반영 후 {sum(hb.values())}명 "
              f"(S {hb[S]} · D {hb[D]} · X {hb[X]}) · 내부(S+D) {hb[S]+hb[D]}명 "
              f"= 업계 표준의 {(hb[S]+hb[D])/TEMPLE_AVG_STAFF:.1f}배")

    print("\n[7] ★판정 — 총량은 되는데 분산이 안 된다")
    print("─" * W)
    print("  ⚠️ 앞의 '표준의 3.5배'는 단위가 어긋난 비교다.")
    print("     E-0880의 사찰당 2.27명은 상근 FTE이고, 위 인원수는 겸임을 포함한 관여 인원이다.")
    print("     같은 단위(FTE)로 놓으면 결론이 뒤집힌다.")
    print()
    print(f"{'':6}{'내부 FTE(S+D)':>16}{'vs 표준 2.27':>14}{'관여 인원':>11}{'1인 평균 배정':>15}{'판정':>10}")
    for i in range(3):
        f = fte_flat(i); hb = headcount_backup(i)
        fte_in = f[S] + f[D]
        n_in = hb[S] + hb[D]
        v = "✅" if fte_in <= TEMPLE_AVG_STAFF else ("⚠️" if fte_in <= TEMPLE_AVG_STAFF*1.5 else "❌")
        print(f"{CASE[i]:6}{fte_in:>15.1f}명{fte_in/TEMPLE_AVG_STAFF:>13.2f}배{n_in:>10}명"
              f"{fte_in/n_in:>14.2f}FTE{v:>8}")
    print("─" * W)
    print("  🔴 기준안 내부 소요는 2.1 FTE로 업계 표준 2.27명과 사실상 같다.")
    print("     그런데 그 2.1 FTE를 8명이 나눠 맡아야 한다 — 1인 평균 배정이 0.26 FTE다.")
    print("     즉 이 사업은 '사람이 모자라서' 안 되는 게 아니라 '전담자를 둘 수 없어서' 위험하다.")
    print()
    print("  이것이 E-0880이 20년째 못 푼 문제의 구조다 — 사찰당 2.27명이 '적다'가 아니라")
    print("  잘게 쪼개져 있어 아무도 전업이 되지 못하고, 그래서 1년 미만 퇴직률이 60%가 된다.")
    print("  회차를 깎아도(보수안) 1인 평균 배정은 0.21 FTE로 오히려 더 나빠진다.")

    print("\n[7-b] 풀별 시간 효율 — 희소 자원이 제값을 받고 있는가")
    print("─" * W)
    print(f"{'풀':12}{'소요시간':>10}{'귀속매출':>11}{'시간당 매출':>14}{'FTE':>8}{'관여인원':>9}")
    rar = revenue_at_risk(1)
    for pool in (S, D, X):
        h = by_pool(1)[pool]
        rv = sum(v for (p, _), v in rar.items() if p == pool)
        print(f"{pool:12}{h:>9,.0f}h{rv:>10.2f}억{rv*1e8/h:>13,.0f}원{h/FTE_HOURS:>7.1f}{headcount_backup(1)[pool]:>8}명")
    h_s_nb = by_pool(1)[S] - YEBUL_SESS[1]*YEBUL_INCR_HR[1]*(1+PREP_RATIO)
    rv_s = sum(v for (p, _), v in rar.items() if p == S)
    print(f"{'  S(예불 제외)':12}{h_s_nb:>9,.0f}h{rv_s:>10.2f}억{rv_s*1e8/h_s_nb:>13,.0f}원")
    print()
    print("  스님 시간은 예불(매출 0·의무)을 빼면 시간당 매출이 가장 높다 — 희소 자원이 제값을 받고 있다.")
    print("  문제는 단가가 아니라 그 0.4 FTE가 3개 분야로 갈려 4명이 관여해야 한다는 점이다.")

    print("\n[8] ★분야 접기 — 인력을 줄이는 유일한 수단은 회차가 아니라 분야다")
    print("─" * W)
    print("  분야 하나를 여는 순간 최소 1명(핵심은 2명)이 붙는다. 회차를 깎아도 그 1명은 안 줄어든다.")
    print("  그렇다면 인당 귀속매출이 낮은 분야부터 접는 것이 인력 대비 매출을 최대화한다. 기준안 기준.")
    print()
    rar = revenue_at_risk(1); fd = fte_domain(1)
    rows = []
    for key in fd:
        pool, dom = key
        n = fd[key] + (1 if key in CRITICAL else 0)
        rows.append((rar.get(key, 0) / n, key, n, rar.get(key, 0), pool))
    rows.sort(reverse=True)
    print(f"{'순위':>4}{'풀':10}{'분야':12}{'인원':>6}{'귀속매출':>11}{'인당매출':>11}{'누적매출':>11}{'누적인원':>10}")
    cum_r = cum_n = 0
    for r, (rate, key, n, rv, pool) in enumerate(rows, 1):
        cum_r += rv; cum_n += n
        print(f"{r:>4}{pool:10}{key[1]:12}{n:>5}명{rv:>10.2f}억{rate:>10.2f}억{cum_r:>10.2f}억{cum_n:>9}명")
    print("─" * W)
    top3 = rows[:3]
    print(f"  상위 3개 분야({', '.join(k[1] for _,k,_,_,_ in top3)}) = "
          f"인원 {sum(n for _,_,n,_,_ in top3)}명으로 매출 {sum(v for _,_,_,v,_ in top3):.2f}억 "
          f"= 전체 {cum_r:.2f}억의 {sum(v for _,_,_,v,_ in top3)/cum_r*100:.0f}%")
    print(f"  하위 3개 분야는 인원 {sum(n for _,_,n,_,_ in rows[-3:])}명으로 "
          f"{sum(v for _,_,_,v,_ in rows[-3:]):.2f}억 = {sum(v for _,_,_,v,_ in rows[-3:])/cum_r*100:.0f}%")
    print("  ⚠️ 단 예불·의례(귀속매출 0)는 접을 수 없다 — 템플스테이 운영 표준 의무(E-0874)이고 사찰의 본업이다.")

    print("\n[9] 조달 경로 — 있는 것부터 쓴다")
    print("─" * W)
    for pool, path in [
        (X, "즉시 조달 가능 — 종단 기관에서 가져온다. 사찰음식 3기관 분업(E-0435)·선재센터(E-0431)·"
            "게스트 초빙(E-0605)으로 상시 고용 없이 운영. 봉은 사찰음식문화연구소(E-0511)는 이미 있다"),
        (D, "시간이 걸린다 — 종단 선명상 지도자 100여 명(E-0884)에서 배정 요청이 1순위. "
            "동시에 지도자 양성 과정(E-0644)이 스스로 공급을 재생산한다(왓포 1:6 모델 E-0481). "
            "★이 과정은 RL-05의 매출 항목이면서 D풀의 공급원이다 — 접으면 안 되는 이유"),
        (S, "살 수 없다 — 몽크챗·T2·아카데미는 스님이 있어야 상품이 성립한다(E-0639·E-0659). "
            "봉은사 상주 인력에서 배정하는 수밖에 없고, 그 수가 미확인이다"),
    ]:
        print(f"  {pool}")
        for ln in [path[i:i+88] for i in range(0, len(path), 88)]:
            print(f"      {ln}")

    print("\n[10] 마스터 v0.2 '진행자 공급 상한' 재판정")
    print("─" * W)
    print("  마스터는 RL-05 낙관을 900→800회로 깎으며 사유를 '진행자 공급 상한'이라 적었다.")
    print("  그러나 RL-05 낙관에서 사찰 내부 인력이 필요한 것은 다음뿐이다:")
    for p in PROGRAMS:
        if p[0] == "RL-05" and p[4] in (S, D):
            print(f"    {p[1]:22} {p[2][2]:>4}회 · {p[4]}")
    edu_sd = sum(p[2][2] for p in PROGRAMS if p[0] == "RL-05" and p[4] in (S, D))
    edu_x  = sum(p[2][2] for p in PROGRAMS if p[0] == "RL-05" and p[4] == X)
    print(f"    → 내부 {edu_sd}회 / 외부조달 {edu_x}회 (전체 {edu_sd+edu_x}회의 {edu_x/(edu_sd+edu_x)*100:.0f}%가 외부)")
    print("  🔴 RL-05를 깎은 것은 진단이 틀렸다 — 이 라인은 대부분 외부 강사로 돌아간다.")
    print("     상한에 실제로 걸리는 것은 RL-05가 아니라 몽크챗·T2·아카데미다.")
