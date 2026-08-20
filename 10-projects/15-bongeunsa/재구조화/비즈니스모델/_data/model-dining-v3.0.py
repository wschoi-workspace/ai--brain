# -*- coding: utf-8 -*-
"""다이닝 모델 v3.0 — 온지음 벤치마크 편입 · 2트랙 비교
A안 = v2.0 엔트리 파인 (발우공양 140% · 50석 · 3타임 · 주6일)
B안 = 온지음형 하이엔드 (연구 기반 · 30석 · 2타임 · 주5일)
"""
def eok(v): return v/1e8

# ══════════ 벤치마크 3종 ══════════
BM = {
"발우공양": dict(
  주체="한국불교문화사업단(조계종) 직영", 개업=2009, 미쉐린="1스타 2016~",
  코스=[36_000,50_000,70_000,120_000], 블렌디드=47_000,
  좌석="50~60석 추정(전실 룸)", 타임=3, 영업일=313, 주=6,
  일커버=120, 외국인=0.35, 페어링="없음",
  연매출_환산=47_000*120*313),
"온지음": dict(
  주체="화동문화재단 부설 전통문화연구소(2013.6)", 개업=2013, 미쉐린="1스타",
  코스=[200_000,300_000], 블렌디드=250_000,
  좌석="약 30석(테이블 4 + 바 + 룸 1)", 타임=2, 영업일=208, 주=4,
  일커버=48, 외국인=None,
  페어링="전통주 점심 80,000 / 저녁 120,000 · 와인 점심 120,000 / 저녁 180,000",
  구조="옷공방·맛공방·집공방 3개 부문(의·식·주) · 고조리서 연구 → 현대 메뉴",
  예약="캐치테이블 · 매주 월 11시에 5주 후 오픈",
  휴무="토·일·월 휴무", 연매출_환산=250_000*48*208),
}

print("="*108)
print("벤치마크 대조 — 왜 온지음이 봉은사와 닮았는가")
print("="*108)
print(f"{'':<18}{'발우공양':>32}{'온지음':>34}")
print("-"*108)
rows=[
 ("운영 주체","한국불교문화사업단(조계종)","화동문화재단 부설 연구소"),
 ("개업","2009","2013"),
 ("미쉐린","1스타 (2016~)","1스타"),
 ("성격","사찰음식 대중화","고조리서 연구 → 현대 메뉴"),
 ("복합 구성","단일 레스토랑","옷·맛·집 3개 공방"),
 ("코스 가격","36/50/70/120천원","점심 200 / 저녁 300천원"),
 ("블렌디드 객단가","약 47,000원","약 250,000원"),
 ("좌석","50~60석 (전실 룸)","약 30석 (테이블4+바+룸1)"),
 ("일 타임수","3타임","2타임"),
 ("영업","월~토 · 주6일 · 313일","화~금 · 주4일 · 208일"),
 ("일 커버수","120명","약 48명"),
 ("페어링","없음","전통주 8~12만 / 와인 12~18만"),
]
for a,b,c in rows: print(f"{a:<18}{b:>32}{c:>34}")
print("-"*108)
print(f"{'연매출 환산':<18}{eok(BM['발우공양']['연매출_환산']):>31.1f}억{eok(BM['온지음']['연매출_환산']):>33.1f}억")
print()
print("  ★ 온지음은 좌석 절반 · 영업일 66%인데 매출은 발우공양의 "
      f"{BM['온지음']['연매출_환산']/BM['발우공양']['연매출_환산']:.1f}배")
print("  ★ 봉은사와의 구조적 대응: 비영리 법인 운영 · 연구소 부설 · 복합 구성 · 전통 복원 콘텐츠")
print()
print("  ⚠ 결정적 차이 — 온지음 매출의 상당분이 주류 페어링인데 봉은사는 주류가 원천 배제(E-0612)")
print("     대체 수단은 무알콜 차·발효음료 페어링뿐이고, 단가는 주류보다 낮게 형성됨")

# ══════════ 2트랙 설계 ══════════
def build(name, seats, times, occ, days, lunch_p, dinner_p, lunch_share,
          pair_rate, pair_price, cps, food_rate, sqm_seat, capex_unit,
          tea_seats, tea_price, tea_turn, tea_days):
    covers = seats*times*occ
    blend  = lunch_share*lunch_p + (1-lunch_share)*dinner_p
    rev_food = covers*blend*days
    rev_pair = covers*pair_rate*pair_price*days
    rev_d = rev_food+rev_pair
    rev_t = tea_seats*tea_price*tea_turn*tea_days
    tot = rev_d+rev_t
    hall = seats*sqm_seat; kit=hall/3; d_area=hall+kit
    t_area = tea_seats*3.0*1.25
    area = d_area+t_area
    staff = covers/cps + tea_seats/20
    labor = staff*3.5e7
    capex = area/3.3058*capex_unit*1e4
    dep = capex/10
    var = food_rate+0.05+0.03      # 식재료 + 수도광열 + 관리
    mkt = 0.02
    op = tot*(1-var-mkt)-labor-dep
    tax = 0 if op<=0 else (op*0.5*0.09 if op*0.5<=2e8 else 2e8*0.09+(op*0.5-2e8)*0.19)
    net = op-tax
    cm = 1-var
    fixed = labor+dep+tot*mkt
    tea_cm = rev_t*cm
    be_rev_d = max(0,fixed-tea_cm)/cm
    be_cov = be_rev_d/((blend+pair_rate*pair_price)*days)
    be_occ = be_cov/(seats*times)
    return dict(name=name, seats=seats, times=times, occ=occ, days=days, covers=covers,
        blend=blend, lunch_p=lunch_p, dinner_p=dinner_p, pair_price=pair_price, pair_rate=pair_rate,
        rev_food=rev_food, rev_pair=rev_pair, rev_d=rev_d, rev_t=rev_t, tot=tot,
        area=area, d_area=d_area, t_area=t_area, staff=staff, labor=labor,
        capex=capex, dep=dep, op=op, net=net, cm=cm, be_cov=be_cov, be_occ=be_occ,
        margin=(covers-be_cov)/covers, payback=(capex/net if net>0 else None),
        op_per_sqm=op/area, rev_per_sqm=tot/area, food_rate=food_rate, cps=cps)

A = build("A · 엔트리 파인 (v2.0)", seats=50, times=3.0, occ=0.65, days=313,
          lunch_p=44_500, dinner_p=88_900, lunch_share=0.52,
          pair_rate=0.20, pair_price=15_000,          # 차 페어링
          cps=5.0, food_rate=0.33, sqm_seat=4.0, capex_unit=560,
          tea_seats=40, tea_price=22_000, tea_turn=1.6, tea_days=313)

B = build("B · 온지음형 하이엔드", seats=30, times=2.0, occ=0.78, days=260,
          lunch_p=90_000, dinner_p=150_000, lunch_share=0.45,
          pair_rate=0.45, pair_price=35_000,          # 차·발효음료 페어링 (주류 불가)
          cps=3.2, food_rate=0.31, sqm_seat=5.0, capex_unit=750,
          tea_seats=30, tea_price=26_000, tea_turn=1.4, tea_days=300)

print()
print("="*108)
print("2트랙 비교 — 같은 자리에서 무엇을 할 것인가")
print("="*108)
print(f"{'':<26}{'A · 엔트리 파인':>26}{'B · 온지음형':>26}{'차이':>18}")
print("-"*108)
def r(lab, fa, fb, fmt="{}", diff=None):
    va, vb = fa, fb
    d = diff if diff is not None else ""
    print(f"{lab:<26}{fmt.format(va):>26}{fmt.format(vb):>26}{d:>18}")

r("좌석", f"{A['seats']}석", f"{B['seats']}석")
r("일 타임수", f"{A['times']:.0f}타임", f"{B['times']:.0f}타임")
r("타임당 점유율", f"{A['occ']:.0%}", f"{B['occ']:.0%}")
r("일 커버수", f"{A['covers']:.0f}명", f"{B['covers']:.0f}명")
r("영업일", f"{A['days']}일 (주6)", f"{B['days']}일 (주5)")
r("점심 코스", f"{A['lunch_p']:,}원", f"{B['lunch_p']:,}원")
r("저녁 코스", f"{A['dinner_p']:,}원", f"{B['dinner_p']:,}원")
r("블렌디드 객단가", f"{A['blend']:,.0f}원", f"{B['blend']:,.0f}원")
r("  발우공양 47,000 대비", f"{A['blend']/47_000:.0%}", f"{B['blend']/47_000:.0%}")
r("  온지음 250,000 대비", f"{A['blend']/250_000:.0%}", f"{B['blend']/250_000:.0%}")
r("페어링(차·발효음료)", f"{A['pair_price']:,}원 × 부착 {A['pair_rate']:.0%}", f"{B['pair_price']:,}원 × 부착 {B['pair_rate']:.0%}")
print("-"*108)
r("다이닝 매출", f"{eok(A['rev_d']):.1f}억", f"{eok(B['rev_d']):.1f}억")
r("  중 페어링", f"{eok(A['rev_pair']):.1f}억", f"{eok(B['rev_pair']):.1f}억")
r("전통다원 매출", f"{eok(A['rev_t']):.1f}억", f"{eok(B['rev_t']):.1f}억")
r("F&B 합계 매출", f"{eok(A['tot']):.1f}억", f"{eok(B['tot']):.1f}억", diff=f"{eok(B['tot']-A['tot']):+.1f}억")
print("-"*108)
r("필요 인원", f"{A['staff']:.0f}명 (커버·인 {A['cps']})", f"{B['staff']:.0f}명 (커버·인 {B['cps']})")
r("인건비", f"{eok(A['labor']):.1f}억 ({A['labor']/A['tot']:.0%})", f"{eok(B['labor']):.1f}억 ({B['labor']/B['tot']:.0%})")
r("식재료비율", f"{A['food_rate']:.0%}", f"{B['food_rate']:.0%}")
r("영업이익", f"{eok(A['op']):+.1f}억", f"{eok(B['op']):+.1f}억", diff=f"{eok(B['op']-A['op']):+.1f}억")
r("  영업이익률", f"{A['op']/A['tot']:.1%}", f"{B['op']/B['tot']:.1%}")
r("세후이익", f"{eok(A['net']):+.1f}억", f"{eok(B['net']):+.1f}억")
print("-"*108)
r("F&B 면적", f"{A['area']:.0f}㎡", f"{B['area']:.0f}㎡", diff=f"{B['area']-A['area']:+.0f}㎡")
r("  다이닝", f"{A['d_area']:.0f}㎡", f"{B['d_area']:.0f}㎡")
r("  다원", f"{A['t_area']:.0f}㎡", f"{B['t_area']:.0f}㎡")
r("배정 1,000㎡ 대비", f"{A['area']-1000:+.0f}㎡", f"{B['area']-1000:+.0f}㎡")
r("CAPEX", f"{eok(A['capex']):.1f}억", f"{eok(B['capex']):.1f}억")
r("회수기간", f"{A['payback']:.1f}년" if A['payback'] else "불가", f"{B['payback']:.1f}년" if B['payback'] else "불가")
print("-"*108)
r("★ ㎡당 영업이익", f"{A['op_per_sqm']/1e4:.0f}만원", f"{B['op_per_sqm']/1e4:.0f}만원",
  diff=f"{(B['op_per_sqm']/A['op_per_sqm']-1):+.0%}")
r("㎡당 매출", f"{A['rev_per_sqm']/1e4:.0f}만원", f"{B['rev_per_sqm']/1e4:.0f}만원")
r("BEP 타임당 점유율", f"{A['be_occ']:.0%}", f"{B['be_occ']:.0%}")
r("안전마진", f"{A['margin']:+.0%}", f"{B['margin']:+.0%}")
print()
print("="*108)
print("판정")
print("="*108)
print(f"  · 절대 이익은 A가 큽니다 ({eok(A['op']):.1f}억 vs {eok(B['op']):.1f}억) — 규모가 2배이므로 당연")
print(f"  · 그러나 ㎡당 영업이익은 B가 {B['op_per_sqm']/A['op_per_sqm']:.2f}배 — 복합공간에서는 이쪽이 평가 기준")
print(f"  · B는 면적을 {A['area']-B['area']:.0f}㎡ 덜 쓰고, 배정 1,000㎡ 중 {1000-B['area']:.0f}㎡를 반납합니다")
print(f"  · B의 BEP 점유율 {B['be_occ']:.0%}는 A({A['be_occ']:.0%})보다 높아 집객 리스크는 더 큽니다")
