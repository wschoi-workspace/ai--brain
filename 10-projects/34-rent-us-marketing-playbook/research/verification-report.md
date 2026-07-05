# 최종 3중검증 리포트 (B) — 2026-07-06 맥미니 무인 실행

> 대상: `tool-la-alternatives.md`(센터피스 A~H) + `us-marketing-playbook.md`(섹션 4~7)
> 방법: 병렬 검증 에이전트 11기(카테고리 A~H 8기 + 섹션4/5/6 3기)가 인용된 출처 URL을 WebFetch로 직접 열어
> ⓐ수치 ⓑ단위 ⓒ귀속 ⓓ맥락 ⓔ출처표기 5축 대조. 죽은 링크·수치 부재 시 WebSearch 재삼각검증.
> 오류는 두 파일에 인라인 반영(셀 내 `〔수정: 기존 X→Y, 근거 URL〕` 마커 총 37개), 반영 후 잔존값 grep 재대조 완료.

## 요약

| 구분 | 건수 |
|---|---|
| **검증 총계** | **337건** |
| 출처 일치(OK) | 276건 (82%) |
| 수정(값·단위·귀속 오류 → 파일 반영) | 31건 |
| 플래그(출처 확인불가 → [추정]/[확인필요] 강등 또는 출처 보강 반영) | 30건 |

**신뢰도 총평**: 핵심 하중 수치(FTC 벌금, Leap 사실관계, PQ Media/eMarketer 시장규모, PR와이어 단가, 인플루언서 티어 요율, Dor 가격 앵커, LAMC 벌금 스케줄)는 전부 원출처와 일치 확인. 오류는 주로 ①자체 산술 배수(3~7배→2~7배, 5~20배→5~24배 등) ②출처-수치 귀속 불일치(수치는 실존하나 인용된 URL에 없음) ③구버전 2차 출처(Suzy·SurveyMonkey) 유형이었고 모두 정정. 사실관계가 반대였던 것은 Storefront 인수 방향 1건. **문서 기준환율 ₩1,400/USD는 2026-07 시장환율(~₩1,530)보다 원화 강세 가정이므로 집행 시 USD 예산을 ~10% 보수적으로 볼 것.**

## 하중 큰(load-bearing) 항목 판정

| 항목 | 파일위치 | 기존값 | 출처확인 | 판정 | 근거URL |
|---|---|---|---|---|---|
| FTC 가짜리뷰 벌금 | tool L35·L49·L53 / playbook §5.5 | 건당 최대 $51,744, 2025년 $53,088 조정 | Federal Register 2025-01-17 원문 확인. **2026년 연례 조정은 셧다운(CPI 미산출)으로 OMB M-26-11이 취소 → $53,088 현행 유지** | 수정(보강) — playbook [추정] 태그를 확정값으로 승격 | https://www.federalregister.gov/documents/2025/01/17/2025-01361/adjustments-to-civil-penalty-amounts |
| Leap 사실관계 | playbook §4.2 | 2025.1 $20M 조달+흑자, 누적 $198M, 12개 Tier-1 시장 100+ 매장, LA 운영 | PRNewswire(2025.1.17)·Tracxn·Leap 공식 3중 일치 | OK | https://www.prnewswire.com/news-releases/retail-platform-leap-raises-20-million-demonstrates-profitability--adds-karen-katz-to-board-302354377.html |
| PQ Media 시장규모 | playbook §4.1 | 글로벌 2024 $128.35B(+10.5%)·2025 $138.94B(B2C $97.24B/B2B $41.74B)·미국 2025 $64.43B(46.4%)·2026 +11.8% | PQ Media 보도자료·InsideAudioMarketing 기사 전 수치 일치 | OK | https://www.insideaudiomarketing.com/post/pq-media-u-s-leads-global-experiential-marketing-growth |
| eMarketer retail media | playbook §4.1 | 미국 2025 $58.79B→2026 $69.33B(+18%), Amazon·Walmart 89%+ | 일치 (참고: 2025.12 개정 전망은 2026 $72.97B) | OK | https://www.emarketer.com/content/faq-on-retail-media-networks-how-marketers-should-allocate-budgets-2026 |
| retail media 온라인 비중 | playbook §4.1 | 지출의 ~90% 온라인 | eMarketer 원문 "99% of retail media ad dollars go towards online channels" | **수정** ~90%→~99% (공백 논거 강화) | 동상 |
| 파워페이지 가격갭 | tool 인덱스·L28·L33 / playbook §7 | 한국 대비 3~7배 | 근거 시세(Shopify mid-tier $1,600~$10,000/건)는 정확하나 자체 산술이 $8,000~25,000÷$3,500=2.3~7.1배 | **수정** 3~7배→약 2~7배 | https://www.shopify.com/blog/influencer-pricing |
| 체험단 가격갭 | tool 인덱스·L54 | 5~20배 | $99÷$21≈4.7배, $500÷$21≈23.8배 | **수정** 5~20배→약 5~24배 | (산술 재검산) |
| PR Newswire 단가 | tool L64 | CA 로컬 $350+연회비 $195, 리저널 $475–575, 내셔널 $805, 초과 $140–245/100단어, 멀티미디어 $325 | Prezly·Pressonify 전 수치 일치 | OK | https://www.prezly.com/academy/pr-newswire-pricing |
| Business Wire 단가 | tool L65 | 로컬 $475, 내셔널 $760–775, 초과 $195–365, 멀티미디어 $425 | 초과분은 전 출처 $195 고정 — $365 확인 불가 | **수정** $195–365→$195 (나머지 OK) | https://www.prezly.com/academy/business-wire-pricing |
| PRWeb / EIN 단가 | tool L65 | PRWeb $120/$245/$360/$480 · EIN $149/$499/$999 | PRWeb 공식·EIN 공식 요금 페이지 정확 일치 (Prezly의 EIN 리뷰는 구가 게재 → 공식 URL로 교체) | OK(출처 보강) | https://www.prweb.com/pricing/ · https://www.einpresswire.com/pricing |
| 인플루언서 티어 요율 | tool L45~47 | IMH mid $500–5K·macro $5–10K·mega $10–50K+ / Shopify mid $1.6–10K·macro $5–25K | 원문 정확 일치. 단 "IMH·Shopify·Impact 3사 교차 일치"는 오류 — Impact는 티어 정의·요율 상이(mid $8–20K) | **수정** 귀속(3사→2사 일치) | https://influencermarketinghub.com/instagram-influencer-rates/ |
| Dor 가격 앵커 | tool L156·L159·L168 | HW $300/대 + SW $150/월/센서(연납 $135) | 공식 요금 페이지 per-sensor 단위까지 정확 | OK — 앵커로 사용 안전 | https://www.getdor.com/pricing |
| LAMC §28.04 벌금 | tool L120 / playbook §5.4 | 1회 $100→2회 $250→3회 $500, 경범죄 기준 | 조례(Ord. 180998) 원문 일치. 경범죄는 "달력연도 내 4회차부터" — tool의 "연 4회 이상"이 원문 부합, playbook "연 3회 초과"는 동치 → 표기 통일 | OK(표기 통일) | https://cityclerk.lacity.org/onlinedocs/2008/08-1512_ord_180998.pdf |
| TCPA 손해배상 | playbook §5.1 | 건당 $500/고의 $1,500, 상한 없음 | 47 U.S.C. §227(b)(3) 일치 | OK | https://www.law.cornell.edu/uscode/text/47/227 |
| FCC one-to-one 룰 폐기 | playbook §5.1 | 2025.1 무효화 → "2025.9 공식 폐기" | 실제: 2025.1.24 11항소법원 vacate → FCC 2025.7.14 삭제 명령 → **2025.8.29 관보 게재·발효**(90 FR 42137) | **수정** 날짜 정정 | https://www.fcc.gov/document/fcc-removes-one-one-consent-rule-nullified-court-decision |
| CAN-SPAM 벌금 | playbook §5.2 | 건당 최대 $53,088(2025.1.17) | FTC 공식 확인 + 2026 조정 취소로 유지 | OK(보강) | https://www.ftc.gov/news-events/news/press-releases/2025/02/ftc-publishes-inflation-adjusted-civil-penalty-amounts-2025 |
| CCPA 기준·벌금 | playbook §5.3 | 매출 $26,625,000 / 벌금 $2,663·$7,988 | cppa.ca.gov 공식 일치. 격년 조정 — 차기 2027.1 | OK | https://cppa.ca.gov/regulations/cpi_adjustment.html |
| 밀레니얼 78% (Eventbrite×Harris 2014) | playbook §4.3 | 78%, 성인 2,083명, 2014 | PDF 원문 직접 확인(밀레니얼 서브샘플 n=507) | OK | https://eventbrite-s3.s3.amazonaws.com/marketing/Millennials_Research/Gen_PR_Final.pdf |
| 팝업 리테일 $10B~$80B 병기 | playbook §4.3 | $10B(협의)~$80B(광의, 신뢰도 제한) | Capital One Shopping 확인 — 병기 구조 타당(광의 $80B는 야드세일·푸드트럭 포함) | OK | https://capitaloneshopping.com/research/pop-up-retail-statistics/ |

## 수정 반영 내역 (31건)

| # | 항목 | 파일위치 | 기존값 → 수정값 | 근거URL |
|---|---|---|---|---|
| 1 | 파워페이지 가격갭 | tool 인덱스·L28·L33, playbook §7 | 3~7배 → 약 2~7배 (산술 재검산) | 내부 산술 |
| 2 | 릴스 프리미엄 귀속 | tool L26 | 인용출처(influee)는 2~3배 제시 → 편차 병기+출처 추가 | https://influencerfee.com/blog/instagram-reels-monetization-guide/ |
| 3 | "IMH·Shopify·Impact 교차 일치" | tool L45 | Impact는 티어 정의·요율 상이 → "2사 일치, Impact 상이" | https://impact.com/influencer/how-much-do-influencers-charge-per-post/ |
| 4 | TikTok macro 요율 | tool L46 | $1,500~$5,000(어느 출처에도 없음) → Shopify $5–15K vs Insense $0.5–2K 병기 | https://www.shopify.com/blog/influencer-pricing |
| 5 | LA 레스토랑 인플루언서 사례 | tool L47 | $400~$500(mustard.love에 부재) → $500+식사(LA Times 2026.6, Hollywood Thai), 출처 교체 | https://www.spokesman.com/stories/2026/jun/29/restaurants-are-paying-influencers-for-promotional/ |
| 6 | 체험단 가격갭 | tool 인덱스·L54 | 5~20배 → 약 5~24배 | 내부 산술 |
| 7 | Business Wire 초과 단가 | tool L65 | $195–365 → $195 고정 | https://www.prezly.com/academy/business-wire-pricing |
| 8 | PR 풀서비스 리테이너 | tool L66 | $5,000–15,000 → $7,500–15,000+ (출처상 풀서비스 티어) | https://www.shapiropr.com/post/the-cost-of-hiring-a-publicist-in-los-angeles-what-you-re-paying-for-when-hiring-a-publicist |
| 9 | Infatuation "Nike·Amex급" | tool L68 | 인용 출처에 부재 → 예시 삭제(현 소유 JPMorgan Chase 고지) | https://www.theinfatuation.com/about/partnerships |
| 10 | 스폰서 기사 중간값 | tool L69 | 중간값 $2,500(HubSpot에 없음) → 블로그 <$1,500 / 퍼블리케이션 $1,500–18,000 재기술 | https://blog.hubspot.com/marketing/cost-sponsored-content |
| 11 | 검색광고 표본 귀속 | tool L87 | 16,446개 표본은 2025 WordStream 기준(버티컬 수치는 2026 LocaliQ) 명시 | https://www.wordstream.com/blog/2025-google-ads-benchmarks |
| 12 | Bing 할인율 | tool L88 | 40~48% → 약 33% 저렴(버티컬 최대 46~70%) | https://megadigital.ai/en/blog/bing-ads-cost/ |
| 13 | 오픈 익스체인지 CPM | tool L89 | ~$2.80(인용출처에 부재) → [추정] $1~4 강등 + 출처 교체 | https://owlclaw.com/benchmarks/programmatic-ads-benchmarks/ |
| 14 | Meta CPM 표기 | tool L90 | "중앙값 $11.54~13.48" → 평균~중앙값 구분 명시 | https://sovran.ai/benchmarks/meta-ads-cpm-by-industry |
| 15 | 토스 CPP 단위 | tool L91 | CPP ₩1.2M~2.6M → 캠페인 총액(공식 CPP는 건당 ₩30~100) 단위 정정 | 토스 공식 상품소개서(2차) |
| 16 | 대학신문 배너 | tool L94 | $50~135/월 → $100~135/월($50은 2주 단가) | https://campusecho.com/printonline-advertising-dates-rates-sizes/ |
| 17 | SAUCED LAB 가격 | tool L110 | ~$4,000/멀티 $10,000+(페이지에 부재) → RFQ [확인필요] 강등 | https://www.saucedlab.com/wildposting-losangeles |
| 18 | Street team LA 프리미엄 | tool L111 | +15~25% → Tier1 프리미엄(2차 시장 대비 최대 +40~60%) | https://streetteamsco.com/blog/street-team-marketing-cost-guide.html |
| 19 | 버스 풀랩 귀속 | tool L114 | $8–15K(상위 10 DMA) → 중형시장 $8–15K·대도시 $15–30K/월/대 | https://www.influize.com/blog/bus-advertising-costs |
| 20 | Vertical Impression | tool L116 | 주거 3,000+(출처에 부재) → 캐나다계, 미국 2,400+ 스크린·98 DMA | https://www.screenversemedia.com/post/screenverse-and-vertical-impression-partner-to-bring-elevator-advertising-to-us-programmatic-buyers |
| 21 | 영화관 상위 DMA 단위 | tool L117 | "스크린당 주 $1,000–5,000+" → 극장당 4주 수천 달러~$46,000+ (단위 오류) | https://dashtwo.com/outdoor-advertising/cinema-advertising/ |
| 22 | E비고 환율 결론 | tool L124·헤더 | ₩7M≈$5,000–5,200 → 기준환율 ₩1,400 명시 + 실환율(~₩1,530) 병기, "예산 내 수렴" 완화 | (환율 재검산) |
| 23 | Posh 티켓 수수료 | tool L136 | 약 2~5% [추정] → 10%+$0.99/티켓 (playbook §6.2와 정렬) | https://support.posh.vip/en/articles/11459046 |
| 24 | SurveyMonkey Advantage | tool L161 | $46/월 → $39/월(연납, 인용 출처 현행가) | https://www.usercall.co/post/surveymonkey-pricing |
| 25 | Suzy 계약 규모 | tool L164 | $34K~$187K·중간값 $88K → $35,795~$183,555·중간값 ~$99,000 (Vendr 2026-07) | https://www.vendr.com/marketplace/suzy |
| 26 | V-Count 엔트리 | tool L160 | $500~$1,200 → [추정] $300~$2,000(Sensource) | https://sensourceinc.com/blog/how-much-do-people-counting-sensors-cost/ |
| 27 | retail media 온라인 비중 | playbook §4.1 | ~90% → ~99% | https://www.emarketer.com/content/faq-on-retail-media-networks-how-marketers-should-allocate-budgets-2026 |
| 28 | Peerspace 시간당 | playbook §4.2 | 평균 $137~289 → 평균 $126($137/$289는 소형/대형 기준값) | https://www.peerspace.com/venues/los-angeles--ca/pop-up-retail-space |
| 29 | Storefront 인수 방향 | playbook §4.2 | "PopUp Immo 인수 후" → PopUp Immo가 2016년 Storefront를 인수(브랜드 유지) — 방향 반대였음 | https://www.crunchbase.com/acquisition/popup-immo-2-acquires-storefront--fdd49090 |
| 30 | FCC one-to-one 폐기일 | playbook §5.1 | 2025.9 → 2025.7.14 명령·2025.8.29 관보 발효 | https://www.fcc.gov/document/fcc-removes-one-one-consent-rule-nullified-court-decision |
| 31 | CA temporary seller's permit | playbook §5.6 | 3~5영업일 → 온라인 등록 시 당일 발급 가능 | https://cdtfa.ca.gov/industry/temporary-sellers/ |

(그 외: MKG 클라이언트 Target→Meta 교체, Fake Review $53,088 [추정]→확정 승격, Fiverr 편집 $25–75→$15–80, testimonial 배칭 절감 20–30%→40–60%, LA 영상 패키지 웨딩 기준 명시, H비고 배수 산술 2건, TCPA 더블옵트인 "법정 강제"→"캐리어 관행 표준" 정밀화 — 위 표와 함께 전부 인라인 반영됨)

## 플래그 반영 내역 (강등·출처보강, 주요 30건)

| 항목 | 파일위치 | 조치 |
|---|---|---|
| Reddit 실효 권장 $50/일 / Nextdoor CPC $2.50–3.50 | tool L29 | 값은 독립 출처 확인 → 출처 URL 추가(stackmatix·nextdooradvertisingagency) |
| Nextdoor CPM $10~$20 | tool L29 | 인용 출처는 $20 단일값 → "약 $20(Taradel), $10~$20 [추정]" 강등 |
| 파워페이지 패키지 상한 산식 | tool L28 | 혼합 구성 가정 명시(전곳 상한 시 최대 $50,000) |
| 6AM City $15,000/오픈율 45%/CTR 0.5% | tool L71 | 수치 정확하나 인용 출처에 부재 → BuySellAds URL 추가 |
| BW 내셔널 $760–775 | tool L65 | 출처 간 상이 실재 — [추정] 유지 |
| Tock 신구가 혼재 | tool L133 | [확인필요] 유지 + 최신 출처(Essential $299/Premium $399) 병기, Events Pro $699 추가 |
| OpenTable 하드웨어 미포함 | tool L134 | 직접 명시 미확인 → [확인필요] 부기 |
| Yelp GM 월납 $159 | tool L132 | 공식 확인 → [추정] 해제(역방향 승격) |
| Placer.ai 연간 구독 | tool L158·L168 | 인용 출처 현행 기재는 $5K~30K → 하한 $12K→$5K로 확대, 비고 동기화 |
| 인터셉트 서베이 | tool L162 | Drive Research 대면조사 $20K~50K+ 감안 → [추정] $5,000~$20,000+로 상향 |
| Qualtrics 출처 | tool L161 | 수치는 정확하나 /pricing엔 없음 → /buy-online으로 교체, Vendr 중간값 $28,591 병기 |
| Density 요금 단위 | tool L159 | 월납 기준 명시(연납 Rooms $8/유닛) |
| Captivate CPM $8–12 | tool L116 | 현행 공개 자료에 없음 — [확인필요—2018 자료] 유지, RFQ 필수 |
| WeHo·Sunset 뮤럴 2배 | tool L112 | 인용 출처에 계수 없음 → [추정] 부기 + Lamar 인수 URL 추가 |
| 죽은/차단 링크 | tool L155(airfreshmarketing 404)·L163(irpr 403), playbook Meta help | altterrain·wearesculpt·facebook help/417527072254206으로 교체/보강 |
| Snappr 자료 시점 | tool L179 | 구형(2020 표기) 주의 문구 부기 |
| 1인 오퍼레이터/풀크루 일당 | tool L183 | 인용 출처에 명시 없음 → [추정] 병기 |
| 편집·경량 제작 $100–500 | tool L182 | 합성 범위 → [추정] 병기 |
| NFC Tyvek $0.10–0.50 | playbook §6.4 | 인용 출처에 단가 부재 → [확인필요] 강등 + atlasrfidstore URL 추가 |
| Smile.io Plus $999 | playbook §6.5 | 연납 조건 부기("월 단위 해지"의 예외) |
| Postscript SMS 단가 | playbook §6.1 | 정가 $0.015에 현행 인하가 $0.009 병기 |
| PassKit "1센트 미만" | playbook §6.3 | 볼륨(5만+) 전제 명시 |
| Luma Plus $59 | playbook §6.2 | 연납 기준 명시 |
| BrandBox "사실상 종료" | playbook §4.2 | 종료 확정 출처 미발견 → "2019년 이후 공개 소식 부재"로 완화, [확인필요] 유지 |
| In-store retail media $0.58B | playbook §4.1 | 정확값 공개 출처 미확인 → "$0.5B+" 수정 |
| Partiful 수수료 | tool L136·playbook §6.2 | "비공개" → "규모별 변동·공표 정률 없음" 정밀화 |
| Intersection 역 수 | tool L114 | 출처 내 93/100 혼재 — 현행 유지(경미) |
| FB그룹/Discord 시딩, 조닝/임시사용, Resy 해지 조건 등 | 각처 | 기존 [확인필요] 표기가 적절 — 유지 |

## 재대조(3단계) 결과

- 수정 반영 후 두 파일 전체를 grep 재검사: 구(舊)값(3~7배, 5~20배, $195–365, ~90%, $0.58B, 40~48%, Nike·Amex, 2025.9 폐기, 3~5영업일, $137~289 등) 잔존 없음 — 히트는 전부 `〔수정〕` 마커 내부의 기존값 인용뿐.
- 문서 내 상충 해소: Posh 수수료(센터피스↔플레이북), LAMC 경범죄 기준(연 4회차 표기 통일), FTC $53,088(전 파일 확정값 통일).
- 잔여 리스크: RFQ·[추정] 항목은 집행 전 개별 견적 필수(진행 파일 액션 아이템 참조). 환율은 ₩1,400 가정 유지 — 실집행 시 시장환율(~₩1,530) 재환산 필요.
