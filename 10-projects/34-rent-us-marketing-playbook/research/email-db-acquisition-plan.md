# 이메일 DB 확보플랜 — 방문객→회원가입 3단계 (a. 현장 캡처 → b. 옵트인 전환 → c. CRM·너처링)

> 작성: 2026-07-07 (맥미니 무인 실행). 검증: 3중 검증(추출→공식출처 대조→재대조) + 전 업체 공식링크 WebFetch 실재 확인(죽은 링크 0).
> 연계: 채널 효과 근거는 `us-effective-marketing.md`, 도구 기본 가격은 `us-marketing-playbook.md` 섹션 6, 규제 상세는 섹션 5 참조.

**구조**: 방문객 여정 3단계 — **a. 현장 캡처**(이메일이 잡히는 물리 접점 4종) → **b. 회원가입·옵트인 전환**(이메일을 내놓게 만드는 전환 장치) → **c. CRM·너처링**(확보 DB로 발송·자동화·리텐션). 하단에 실사례 **참고 케이스** 9건.

---
## a. 현장 캡처 (Venue Capture) — 방문객이 이메일을 남기는 접점

**설계 원칙**: 팝업 현장에서 이메일이 잡히는 물리 접점은 4종뿐이다 — ① 방문객 폰(QR), ② 스태프 디바이스/굿즈(NFC), ③ 거치형 태블릿·키오스크, ④ 입장 전 체크인(RSVP). 4종을 겹쳐 깔수록 누수 없이 잡힌다. 미국 표준 플레이는 "사전 RSVP로 50~70% 선확보 + 현장 QR/태블릿으로 워크인 보충".

### a-1. 업체 표

| 업체명 | 공식링크 | 한줄 소개 | 핵심 기능 | 가격 | 비고(출처) |
|---|---|---|---|---|---|
| **Flowcode** | https://www.flowcode.com/pricing | 미국 브랜드 이벤트에서 가장 많이 쓰이는 QR 플랫폼. QR + Flowpage(모바일 랜딩) + 폼을 한 몸으로 묶어 스캔→이메일 입력까지 원스톱. | 동적 QR, Flowpage 리드폼(Pro Plus 1,500개/Growth 3,600개 폼), 스캔 분석, CRM/CDP 연동(Enterprise) | 무료(코드 2개)~Pro Plus $25/월~Growth $250/월~Enterprise RFQ | 1 |
| **Bitly QR Codes** | https://bitly.com/pages/pricing | 링크 단축의 Bitly가 공식 제공하는 QR 생성 서비스. QR 개수 제한이 티어별로 빡빡해 소량·저비용 운영에 적합. **Beaconstac과는 별개 회사** — Beaconstac은 Uniqode로 리브랜딩(2024.1). | 티어별 QR 월 2/5/10/200개, 로고 커스텀(Core+), 커스텀 랜딩페이지 참여 분석(Growth+) | 무료~Core $10/월~Growth $29/월~Premium $199/월 | 2 |
| **Uniqode** (구 Beaconstac) | https://www.uniqode.com/pricing | G2 1위권 QR 전문 플랫폼. 2024년 1월 Beaconstac에서 Uniqode로 사명 변경(제품·데이터 연속). 폼·랜딩 내장 동적 QR로 대량 캠페인에 강함. | 동적 QR + 폼/랜딩, 스캔 분석, 디지털 명함($6/유저/월), 커스텀 도메인(Plus $2,000/년 애드온) | 무료(정적만)~Starter $9/월~Core $49/월~Plus/Business+ (연납만) | 3 |
| **QR Tiger** | https://www.qrcode-tiger.com/payment | 가성비형 QR 생성기. 동적 QR 단가가 가장 낮은 축이라 부스·포스터 다점포 배포용. 자체 리드폼은 없어 Klaviyo 호스티드 폼 URL을 태우는 조합이 정석. | 동적 QR 12~600개, 무제한 스캔(유료), Zapier/HubSpot 연동, 스캔 알림, API(Premium) | 무료(동적 3개·500스캔)~Regular $7/월~Advanced $16/월~Premium $37/월 | 4 |
| **Popl** | https://popl.co | 디지털 명함에서 이벤트 리드캡처 플랫폼으로 확장한 GTM 툴. "어떤 배지든 스캔"하는 유니버설 배지 스캐너로 스태프가 방문객 정보를 즉시 CRM으로 흘린다. | 유니버설 배지/명함 스캔, 리드 인리치먼트, Salesforce·HubSpot·Marketo 등 30+ 연동 | 개인 Pro $7.99/월~, 이벤트/팀 플랜 RFQ(데모 필수) | 5 |
| **Blinq** | https://blinq.me | 글로벌 400만 유저 디지털 명함 앱. QR·NFC·Apple Wallet으로 프로필 공유 + AI 배지/명함 스캔 리드캡처. 스태프 개인 단위 캡처 도구로 Popl 대비 저가 대안. | NFC 카드/QR 공유, AI 연락처 캡처·인리치먼트, AI 노트, HubSpot/Salesforce 연동 | 무료~Premium(7일 체험)~Business RFQ | 6 |
| **ID&C** | https://www.idcband.com | 30년 업력의 이벤트 손목밴드 전문사(코첼라 등 대형 페스티벌 납품). NFC/RFID 밴드로 입장+스탬프+리드캡처를 손목 하나에 통합. | 패브릭/실리콘/타이벡 밴드, RFID 밴드·라미네이트, 커스텀 브랜딩 | RFQ(견적) — 벌크 NFC 밴드 시장가 실리콘 $1~3, MOQ 5천 시 $0.38~0.52 [추정, 섹션 6.4 준용] | 7 |
| **Klaviyo 태블릿 폼** | https://help.klaviyo.com/hc/en-us/articles/360026474752 | Klaviyo에 전용 "키오스크 앱"은 없지만, 호스티드 Subscribe 페이지 또는 임베드 폼을 iPad 브라우저(가이드 액세스)에 띄우는 방식이 공식 권장 패턴. 수집 즉시 웰컴 플로우로 직결되는 게 최대 강점. | 팝업/플라이아웃/임베드/풀페이지/배너 폼, 호스티드 Subscribe 페이지(QR 연결), 수집→플로우 자동화 | Klaviyo 요금에 포함(무료 250프로필~Email $20/월~) | 8 |
| **Mailchimp Subscribe** | https://mailchimp.com/mailchimp-subscribe/ | 과거 iPad/Android 태블릿 오프라인 사인업 앱(구 Chimpadeedoo). **현재 App Store에서 내려간 상태로 단종 [추정]** — 공식 URL은 일반 Mailchimp 모바일 앱 페이지로 대체됨. 신규 도입 비추천. | (과거) 오프라인 이메일 수집→온라인 복귀 시 리스트 동기화 | 무료(Mailchimp 계정 필요) — 신규 사용 불가 [확인필요] | 9 |
| **Cvent iCapture** | https://www.cvent.com/en/event-marketing-management/cvent-icapture | 트레이드쇼 리드캡처 1위권 앱(Cvent 산하). 130+ 배지 프로바이더 스캔, 오프라인 캡처, 리드 스코어링까지 — B2B 행사·컨벤션형 팝업에 적합. | 배지 스캔(130+ 프로바이더), 표준화 캡처 폼, 실시간 CRM/MAP 라우팅, ROI 분석 | RFQ(데모 필수) | 10 |
| **QuickTapSurvey** | https://www.quicktapsurvey.com | iPad/Android 태블릿 오프라인 설문·리드캡처 앱. 인터넷 없이 수집 후 자동 동기화 — Mailchimp Subscribe 단종 후 실질적 대체재. | 오프라인 키오스크 모드, 35+ 질문 유형, Mailchimp/Salesforce/Zapier 연동 | 유료(티어 비공개 — pricing 페이지 별도, RFQ성) [확인필요] | 11 |
| **TapMango** | https://www.tapmango.com | 태블릿 키오스크 기반 로열티 플랫폼. 매장 카운터에 상시 거치해 전화번호/이메일을 리워드와 교환 수집 — 상설 매장·장기 팝업용. | 브랜디드 태블릿 키오스크, 포인트/리워드, SMS/이메일 캠페인, 온라인 주문 | RFQ — 실질 월 $239~400 [추정, 섹션 6.5 준용] | 12 |
| **Luma** | https://luma.com | 팝업 RSVP의 사실상 표준. 등록 시점에 이메일이 무조건 잡히므로 "체크인 = 캡처 완료" 구조. 캘린더 구독으로 재방문 CRM 효과까지. | 이벤트 페이지+RSVP(이메일 필수), 체크인 QR, 게스트 리스트 관리, Zapier/API [확인필요 — 상세는 help.luma.com] | 무료(유료티켓 5%)~Plus $59/월(수수료 0%) [섹션 6.2 준용] | 13 |
| **Eventbrite** | https://www.eventbrite.com/organizer/pricing/ | 최대 이벤트 디스커버리 채널. 커스텀 등록 폼으로 참석자 데이터를 주최자가 확보 — 단, 마케팅 이메일 발송은 별도 옵트인 체크박스 필수(CAN-SPAM). | 티켓팅+커스텀 등록 폼, 자동 리마인더, 참석자 데이터 export | 무료 이벤트 $0 / 유료 3.7%+$1.79/티켓+결제 2.9% [섹션 6.2 준용] | 14 |

**비고(출처)**
1. https://www.flowcode.com/pricing — WebFetch 확인. 폼 개수 한도는 티어 표 기재값.
2. https://bitly.com/pages/pricing — WebFetch 확인. Bitly≠Beaconstac 관계는 비고 3의 리브랜딩 발표로 교차 확인.
3. https://www.uniqode.com/pricing + 리브랜딩 공식 발표 https://www.uniqode.com/blog/updates/beaconstac-rebrands-to-uniqode (2024-01-10, PR Newswire 교차) — WebFetch/WebSearch 확인. 연납 전용 주의.
4. https://www.qrcode-tiger.com/payment — WebFetch 확인(기존 /pricing 경로는 404, /payment가 공식 가격 페이지).
5. https://popl.co — WebFetch 확인. 이벤트 플랜 가격 비공개(RFQ). Pro $7.99/월은 섹션 6.4 기확보 수치.
6. https://blinq.me — WebFetch 확인. Business 가격 비공개.
7. https://www.idcband.com — WebFetch 확인. 완제품 가격은 견적제, 시장 단가는 플레이북 섹션 6.4의 rfidhy/atlasRFID 수치 준용.
8. https://help.klaviyo.com/hc/en-us/articles/360026474752 — WebFetch 확인. 태블릿 운영 패턴은 Klaviyo Community 공식 답변(https://community.klaviyo.com/signup-forms-38/ipad-email-list-sign-up-for-brick-mortar-1003) 근거: URL 타겟팅 폼·임베드·호스티드 페이지 3방식.
9. https://mailchimp.com/mailchimp-subscribe/ — WebFetch 확인 결과 페이지는 살아있으나 콘텐츠가 일반 Mailchimp 모바일 앱 안내로 대체, 태블릿 오프라인 수집 기능 언급 소멸. App Store 트래킹(apprecs)상 "unavailable" → 단종 [추정].
10. https://www.cvent.com/en/event-marketing-management/cvent-icapture — WebFetch 확인(icapture.com은 cvent.com으로 301 리다이렉트 = Cvent 인수 후 통합).
11. https://www.quicktapsurvey.com — WebFetch 확인. 가격은 별도 페이지·비공개성.
12. https://www.tapmango.com — WebFetch 확인. 홈페이지에 가격 미공개, 데모 문의제.
13. https://luma.com — WebFetch 확인(홈페이지). 게스트 export/API 상세는 help.luma.com 별도 [확인필요].
14. https://www.eventbrite.com/organizer/pricing/ — WebFetch 확인. 참석자 이메일의 마케팅 활용 조건은 Eventbrite 약관상 별도 동의 필요 [확인필요].

### a-2. 접점별 이메일 캡처율 벤치마크

| 접점 | 벤치마크 | 신뢰도 | 출처 |
|---|---|---|---|
| 이벤트 배지·사이니지 QR 스캔율 | 참석자의 **2~6%** (일반 사이니지 기준) | [추정] — QR툴 벤더 블로그 단일 계열 | https://zodqr.com/blog/qr-code-scan-rate-benmark |
| 목적성 QR (프로그램/스케줄 안내) | 스캔율 **40~70%**, 배지 QR 30~60% — "스캔할 이유"가 명확하면 급등 | [추정] — 벤더 블로그 | https://www.qrbuild.io/blog/qr-code-scan-rate-benchmarks |
| QR CTA 효과 | 구체적 CTA("Scan for exclusive ~")가 스캔율 최대 +37% | [추정] — 벤더 블로그 | https://www.qrbuild.io/blog/qr-code-scan-rate-benchmarks |
| 키오스크/태블릿 사인업률 | 공신력 있는 공개 벤치마크 부재. 리워드 교환 조건(트래픽의 상당수 등록)이라는 벤더 주장만 존재 | [추정] — 수치 인용 불가 | — |
| 체크인(RSVP) 기반 수집률 | 사전 등록 이벤트는 구조상 **참석자 100%** 이메일 확보(등록 필수 필드). 실제 변수는 노쇼율(무료 이벤트 통상 30~50% [추정]) | 구조적 사실 + 노쇼율은 [추정] | Luma/Eventbrite 등록 구조 |
| B2B 배지스캔 앱 효과 | Cvent iCapture 도입사 사례: 리드 볼륨 +50%, 리드 품질 +50% (Truckstop.com) | 벤더 사례 — [추정] | https://www.cvent.com/en/event-marketing-management/cvent-icapture |

**실무 시사점**: 현장 QR "그냥 걸어두기"는 2~6%짜리 게임이다. ① QR에 명분(경품 응모·디지털 굿즈·스탬프)을 붙여 40%+ 게임으로 바꾸고, ② RSVP(Luma)로 입장 전에 이메일을 확보해 현장 캡처를 보험으로 돌리는 것이 정답. 키오스크는 벤치마크가 없으므로 파일럿에서 자체 측정해 Cultural Engagement Score 데이터 자산으로 삼는다(섹션 6.7-3 연계).

---

## b. 회원가입·옵트인 전환 (Signup & Opt-in Conversion) — 이메일을 받아내는 전환 장치

**설계 원칙**: 접점(a)에 도달한 방문객이 실제로 이메일을 내놓게 만드는 건 폼 UX와 인센티브다. 데이터가 말하는 우선순위: **게이미피케이션(스핀휠) > 할인/경품 인센티브 > 맨 뉴스레터 폼**. 단, 스핀휠 리드는 볼륨 대비 질이 낮을 수 있어(경품 목적 가입) 웰컴 플로우 이탈 관리가 필수.

### b-1. 업체 표

| 업체명 | 공식링크 | 한줄 소개 | 핵심 기능 | 가격 | 비고(출처) |
|---|---|---|---|---|---|
| **Klaviyo Forms** | https://help.klaviyo.com/hc/en-us/articles/360026474752 | ESP에 폼이 내장된 유일한 조합형 기본값. 팝업·임베드·풀페이지·배너 + 자체 스핀휠(spin-to-win)까지 지원하고, 제출 즉시 세그먼트·플로우로 직결. | 5종 폼 + spin-to-win, 타겟팅/URL 조건, A/B 테스트, 피어 벤치마크 리포트 내장 | Klaviyo 요금 포함(무료 250프로필~$20/월~) | 1 |
| **Typeform** | https://www.typeform.com/pricing/ | 대화형 원-퀘스천 UX로 완주율이 높은 폼 빌더. 현장 iPad 설문+이메일 수집을 "브랜드 경험"처럼 보이게 만들 때 최적. | 대화형 폼, 로직 점프, 100~10,000응답/월, Klaviyo/CRM 연동 | Basic $28~39/월~Plus $56~79/월~Business $91~129/월~Enterprise RFQ | 2 |
| **Unbounce** | https://unbounce.com/pricing/ | 랜딩페이지 빌더의 원조. QR 도착 페이지를 A/B 테스트로 최적화하는 용도 — 팝업·스티키바는 Build 티어부터. | AI 랜딩페이지, 팝업/스티키바(Build+), A/B 테스트, 1,000+ 연동 | Starter $29/월(연납 $22)~Build $99/월~Experiment $149/월~Optimize $249/월 | 3 |
| **OptinMonster** | https://optinmonster.com/pricing/ | 팝업/옵트인 폼 전문 툴의 고전 강자. 자체 웹사이트에 얹는 방식이라 팝업 스토어 마이크로사이트에 저비용 장착 가능. 스핀휠은 최상위 Growth 전용. | 팝업/플로팅바/게이미피케이션, 이그짓 인텐트, 쿠폰휠(Growth 전용), A/B 테스트 | Basic $7/월~Plus $19/월~Pro $29/월~Growth $49/월(연납가) | 4 |
| **OptiMonk** | https://www.optimonk.com/pricing/ | 헝가리산 CRO 팝업 툴. 무료 티어가 후하고(10K 페이지뷰) 스핀휠·게이미피케이션 템플릿이 풍부해 초기 테스트용 가성비 1위. | 스핀휠/스크래치카드 템플릿, 임베드·사이드메시지, 페이지뷰 과금 | 무료(10K PV)~Essential $19/월~Growth $69/월~Premium $179/월 | 5 |
| **Wheelio** | https://apps.shopify.com/wheelio-first-interactive-exit-intent-pop-up | 스핀휠 팝업의 원조 Shopify 앱. 이메일+SMS 동시 수집, Klaviyo/Omnisend 직결 — Shopify 스토어 병행 브랜드용. | 스핀휠/스크래치/슬롯머신, 이그짓 인텐트, 할인코드 자동 발급, Klaviyo·Postscript 연동 | $14.92/월(3만 노출)~$109.92/월(25만 노출), 7일 체험 | 6 |
| **PassKit** | https://passkit.com | Apple/Google Wallet 패스 발급 API. 이메일 캡처 후 "월렛 멤버십 카드"를 지급하면 폰 잠금화면에 브랜드가 상주 — 위치 기반 락스크린 알림으로 재방문 트리거까지. 멤버십 카드는 연간 개당 0.5센트라는 극저원가. | 멤버십/로열티/쿠폰 패스 발급, 실시간 패스 업데이트(포인트·체크인), 위치 기반 알림, API/Zapier/CRM 연동 | 최소 $39.50/월 [섹션 6.3 준용], 쿠폰·티켓 볼륨 시 개당 1센트 미만, 멤버십 카드 연 $0.005/개 | 7 |

**비고(출처)**
1. https://help.klaviyo.com/hc/en-us/articles/360026474752 — WebFetch 확인. spin-to-win 지원은 Klaviyo 헬프 문서군에서 확인. 벤치마크 리포트: 팝업 중앙 제출율 2.3% (https://help.klaviyo.com/hc/en-us/articles/360050110072 계열).
2. https://www.typeform.com/pricing/ — WebFetch 확인. 월 가격은 월납~연납 범위 표기.
3. https://unbounce.com/pricing/ — WebFetch 확인. Starter에는 팝업 미포함 주의.
4. https://optinmonster.com/pricing/ — WebFetch 확인. 표기가는 연납 기준(정가 대비 상시 할인 표기 — 실질가로 볼 것). 쿠폰휠은 Growth $49/월 전용.
5. https://www.optimonk.com/pricing/ — WebFetch 확인. 페이지뷰는 팝업 노출과 무관하게 사이트 로드 기준 과금 주의.
6. https://apps.shopify.com/wheelio-first-interactive-exit-intent-pop-up — WebFetch 확인(4.5★/194리뷰).
7. https://passkit.com — WebFetch 확인("membership cards for as little as 0.5 cents per year", 45일 체험). 기본 월정액은 섹션 6.3 기확보 수치.

### b-2. 인센티브 장치별 전환율 비교

| 장치 | 전환율 데이터 | 출처 |
|---|---|---|
| 맨 뉴스레터 폼(인센티브 없음) | **1.7%** (Omnisend) / **5.10%** (OptiMonk) | 1, 2 |
| 할인 코드 인센티브 | **2.4%** — 무인센티브 대비 **+41%** (Omnisend) / 할인·리드마그넷 부착 시 5.10%→**약 7.5%** (OptiMonk) | 1, 2 |
| 스핀휠(게이미피케이션) | **13.23%** (OptiMonk 럭키휠) / **29.99% vs 일반 4.04%** = +642% (Wisepops) / 휠 3.5% vs 무휠 2.0% ≈ 2배 (Omnisend) | 1, 2, 3 |
| 경품 추첨(스윕스테이크) | 팝업 단독 공개 벤치마크 부재 — 게이미피케이션 계열 상단(10%+)으로 보는 게 합리적 [추정] | — |
| 디지털 굿즈(월렛 패스·콘텐츠) | 공개 벤치마크 부재 [추정]. 대신 리텐션 채널 가치로 평가: 월렛 패스는 삭제 전까지 락스크린 재노출 | 4 |
| 카운트다운 타이머 부착 | 9.86% → **14.41%** (OptiMonk) | 2 |

### b-3. 현장 사인업 전환율 벤치마크 (팝업 폼 업계 기준선)

| 지표 | 수치 | 표본·연도 | 출처 |
|---|---|---|---|
| 이메일 팝업 평균 전환율 | **2.1%** (1.5% 미만 저조 / 3~5% 양호 / 5%+ 우수) | 12.4억 노출, 2025 | 1 |
| 팝업 평균 전환율 | **4.82%** (2025년 4.65%→상승) | 10억+ 노출, 2026 | 3 |
| 팝업 평균 전환율 | **11.09%** (상위권 42.35%) — 자사 유저 편향 감안 | OptiMonk 유저 데이터 | 2 |
| Klaviyo 팝업 제출율 | 중앙값 **2.3%**, 권장 목표 **3%+** | Klaviyo 피어 벤치마크 | 5 |
| 상위 10% 팝업 | **57.7%** (2016년엔 ~9%였음 — 타겟팅·게이미피케이션이 격차 벌림) | Wisepops 2026 / 구 Sumo 2016(17.5억 노출) 비교 | 3, 6 |

**벤치마크 해석 주의**: 플랫폼별 수치 편차(2.1%~11.09%)는 표본 구성 차이(전체 노출 vs 자사 고객) 때문. 보수적 계획 기준은 **Omnisend 2.1% + Klaviyo 목표 3%**, 스핀휠 장착 시 **10%+**를 상단 시나리오로. 단, 이는 전부 **웹 팝업** 기준 — "현장 대면 + 리워드 즉시 지급" 상황은 이보다 훨씬 높게 나오는 게 일반적이나 공개 벤치마크가 없으므로 [추정], 파일럿 실측이 필요.

### b-4. 더블옵트인·컴플라이언스 — 폼 설계 실무 요점 (상세 규제는 플레이북 섹션 5)

1. **이메일(CAN-SPAM)은 옵트인 의무가 없다** — 대신 발신자 명시·주소 표기·원클릭 수신거부가 의무. 그래도 더블옵트인(확인 메일 클릭)을 걸어야 가짜 이메일·스팸 신고를 걸러 발송 평판이 산다.
2. **SMS(TCPA)는 정반대** — 사전 서면 명시 동의 필수 + 캐리어 관행상 더블옵트인(YES 회신)이 표준. 이메일 체크박스와 SMS 체크박스는 반드시 분리하고, SMS는 사전 체크된 박스 금지.
3. **폼에 동의 문구·개인정보 링크 상시 노출** — "마케팅 이메일 수신에 동의합니다 + Privacy Policy 링크". 캘리포니아(CCPA/CPRA)는 수집 시점 고지(notice at collection)가 요건.
4. **경품 추첨 폼은 "No Purchase Necessary" 문구 + 공식 규칙 링크** 필수(주별 스윕스테이크 규정). 응모=마케팅 수신 동의로 자동 결합하지 말고 별도 체크박스로.
5. **수집 시각·장소·동의 문구 버전을 CRM에 저장**(consent record) — TCPA 소송(건당 $500~1,500) 방어의 핵심 증거.

---

## c. CRM·이메일 포워딩·너처링 (확보한 DB로 발송·자동화·리텐션)

### c-1. ESP 5사 비교

| 업체명 | 공식링크 | 한줄 소개(2~3문장) | 핵심 기능 | 가격 | 비고(출처) |
|---|---|---|---|---|---|
| **Klaviyo** | https://www.klaviyo.com/pricing | 미국 D2C·이커머스 사실상 표준 ESP. 프로필 단위 과금으로 사인업 폼→플로우→세그먼트가 한 플랫폼에 통합돼 있고, 2025년 2월부터 '활성 프로필' 기준 과금으로 바뀌어 리스트 위생이 비용에 직결된다. | 사인업 폼·QR, 비주얼 플로우 빌더, 예측 분석(CLV·churn), AI 세그먼트, 350+ 연동, SMS/WhatsApp 크레딧 | 무료 250프로필·월 500통. Email 유료: 1,000프로필 $30/월 → **2,500프로필 $60/월 → 5,000프로필 $100/월**. Email+SMS $35/월~(SMS는 크레딧 별도) | 주1 |
| **Mailchimp** | https://mailchimp.com/pricing/marketing/ | 가장 대중적인 범용 ESP. 저가 진입과 쉬운 에디터가 강점이나, 자동화 분기·세그먼트 깊이는 Klaviyo 대비 얕고 연락처 티어가 올라가면 가격 이점이 빠르게 사라진다. | 캠페인·기본 자동화(Customer Journey), 랜딩·폼, 리포트, 콘텐츠 AI | 무료 250명·월 500통. Essentials **$13/월~**(500명 기준, 티어별 증가), Standard $20/월~, Premium $350/월. 2,500명 기준 Essentials 약 $45/월 [추정] | 주2 |
| **Brevo** (구 Sendinblue) | https://www.brevo.com/pricing/ | 연락처 수가 아니라 **발송량 기준 과금**이 유일한 구조적 차별점. 리스트는 크지만 발송 빈도가 낮은 비즈니스(팝업처럼 리드가 계속 쌓이는 구조)에서 가장 저렴하다. 트랜잭셔널 메일·SMS·WhatsApp까지 한 계정. | 이메일+SMS+WhatsApp, 자동화, 트랜잭셔널 API, CRM(딜 관리) 내장, 연락처 저장 10만 명까지 무료 | 무료: 300통/일. Starter **$9/월(5,000통)**→$29/월(20,000통)→$69/월(100,000통). Business $18/월(5,000통)~: A/B테스트·무제한 자동화·랜딩 포함 | 주3 |
| **Customer.io** | https://customer.io/pricing | 마케터보다 프로덕트/데이터 팀 지향의 메시징 자동화 플랫폼. 행동 이벤트 기반 트리거와 API 유연성이 최강이지만 시작가가 높아 소규모 리스트엔 과투자. | 비주얼 워크플로 빌더, 이벤트 기반 트리거, 이메일+푸시+인앱+SMS 크로스채널, Data Pipelines(CDP) | Essentials **$100/월~(5,000프로필·월 100만 통 포함)**, 초과 $0.009/프로필·$0.12/1,000통. 5,001~10,000프로필 $145/월. Premium $1,000/월~(연결제) | 주4 |
| **Omnisend** | https://www.omnisend.com/pricing/ | 이커머스 특화 저가형 ESP로 이메일+SMS+웹푸시를 하나의 플로우에서 운영. Klaviyo의 60~70% 가격에 핵심 자동화를 제공하나 Shopify 등 이커머스 스토어 연동을 전제로 한 기능이 많다. | 이메일·SMS·웹푸시 통합 플로우, Forms AI, 제품 추천, 세그먼트, 24/7 지원 | 무료 250명·월 500통. Standard 500명 정가 $16/월(2026-07 현재 30% 프로모션 $11.20 표시), Pro 2,500명 정가 $59/월(프로모션 $41.30)·이메일 무제한. SMS $0.007~0.009/건 | 주5 |

**비고(출처)**
- 주1: Klaviyo 공식 pricing(WebFetch 확인: 무료 250프로필·500통/월·모바일 크레딧 150). 티어별 금액($30/$60/$100)은 공식 페이지가 인터랙티브라 Retainful 2026 가격 분석(https://www.retainful.com/blog/klaviyo-pricing, WebFetch 확인)으로 교차 검증. 활성 프로필 과금 전환(2025.2)도 동일 출처.
- 주2: Mailchimp 공식 pricing(WebFetch 확인: Essentials $13/Standard $20/Premium $350, 무료 250명·500통/월). 2,500명 티어 금액은 공식 페이지에 비노출 → [추정].
- 주3: Brevo 공식 pricing 페이지 실재 확인(200). 페이지가 JS 렌더링이라 금액은 costbench 2026(https://costbench.com/software/marketing-automation/brevo/) + smtpedia 2026(https://smtpedia.com/brevo-pricing/) 이중 교차 검증(둘 다 WebFetch 확인, Starter $9@5K통·$29@20K통 일치). 해지 안 한 수신거부 연락처도 과금 대상이라는 점 주의.
- 주4: Customer.io 공식 pricing(WebFetch 확인: 5,000프로필·100만 통 포함, 초과 $0.009/프로필·$0.12/1,000통). 시작가 $100은 공식 페이지 비노출 → Encharge 2026 분석(https://encharge.io/customer-io-pricing/, WebFetch 확인)으로 교차 검증.
- 주5: Omnisend 공식 pricing(WebFetch 확인). 페이지 표시가는 30% 할인 프로모션가($11.20/$41.30)로, 정가($16/$59)는 할인율 역산 — 프로모션 종료 시점 [확인필요].

### c-2. 규모별 월액 비교 (이메일 전용, 월 2~4회 발송 가정)

| 프로필 규모 | Klaviyo | Mailchimp Essentials | Brevo | Customer.io | Omnisend |
|---|---|---|---|---|---|
| 2,500프로필 | $60 | ~$45 [추정] | **$9** (Starter, 월 5천 통 이내) | $100 (5천 포함 최저구간) | $59 정가(Pro) |
| 5,000프로필 | $100 | ~$75 [추정] | **$9~29** (발송량 따라) | $100 | ~$80~90 [추정] |

- 핵심 구조 차이: Klaviyo·Mailchimp·Omnisend·Customer.io는 **프로필 수** 과금, Brevo만 **발송량** 과금. 팝업 리드는 "리스트는 빨리 크는데 발송은 캠페인 단위로 간헐적"이라 Brevo 구조가 원가상 가장 유리하다.
- 단, Brevo는 세그먼트·예측 기능 깊이가 얕음. "저원가 대량 보관+발송"은 Brevo, "고부가 자동화·분석"은 Klaviyo로 계층화하는 이원 운용도 가능.

### c-3. 자동화 플로우 설계 + 업계 벤치마크

#### (1) 웰컴 시리즈 — 가장 확실한 ROI 구간

| 지표 | 웰컴 이메일(자동) | 일반 캠페인 | 배수 |
|---|---|---|---|
| 오픈율 | 35.53% | 30.41% | 1.2x |
| 클릭률 | 3.94% | 0.74% | 5.3x |
| 전환율 | **2.11%** | 0.08% | **~26x** |
| 이메일당 매출 | $6.16 | $0.155(캠페인 평균) | ~40x |

- 출처: Omnisend 2025 데이터셋(2026 리포트), https://www.omnisend.com/blog/email-marketing-benchmarks/ (WebFetch 확인). 자동화 전체 평균으로도 캠페인 대비 **이메일당 매출 22배**($3.41 vs $0.155).
- Klaviyo 실계정 포트폴리오(BS&Co, 이커머스 14개 브랜드·직전 365일): 웰컴 플로우 첫 메일 **오픈 52.3%·클릭 9.2%·전환 4.37%**(중앙값). 전환율 P90 스프레드가 0.95~18.04%로 19배 — 오퍼·타이밍 설계가 성과를 가른다. 출처: https://bsandco.us/blog-post/klaviyo-flow-benchmarks (WebFetch 확인).
- 설계 권고(팝업 맥락): 현장 QR 옵트인 → **즉시**(웰컴+약속한 인센티브 전달) → D+2(브랜드/팝업 비하인드) → D+5(오퍼·다음 행동 유도) 3통 기본.

#### (2) 포스트이벤트 플로우 (팝업 방문 후 24h / 7d / 30d)

팝업 전용 공개 벤치마크는 없어, 가장 가까운 프록시인 **포스트퍼체이스 플로우**(방문·구매 직후 관계 형성 목적) 벤치마크를 적용한다 [추정: 프록시 매핑].

| 단계 | 목적 | 내용 예시 | 근거 벤치마크 |
|---|---|---|---|
| **+24h** | 기억이 선명할 때 감사+회수 | 방문 감사, 현장 사진/리캡, NPS 1문항 설문 | 포스트퍼체이스 첫 메일 오픈율 **58.0%** — 전 플로우 중 최고(BS&Co). 설문 응답도 24h 내가 최적 |
| **+7d** | 경험→브랜드 전환 | 팝업에서 본 제품 스토리, UGC 리그램, 온라인 스토어/다음 이벤트 연결 | 자동화 플로우 오픈율은 "전부 38% 이상"으로 캠페인 평균(~37%)을 상회(BS&Co) |
| **+30d** | 전환·재방문 | 한정 오퍼, 다음 팝업 사전등록(waitlist), 월렛 패스 설치 유도 | 플로우 매출의 신규 구매자 기여가 캠페인 대비 3배(48% vs 16%, Klaviyo 2026 벤치마크 계열 [추정 — 2차 인용]) |

- 포스트퍼체이스 계열은 "고오픈·저전환 역설"(오픈 58%·전환 0.31%)이 정상 — 목적을 즉시 전환이 아니라 **리텐션·데이터 수집**(설문·선호 태깅)에 두고 KPI를 오픈/설문응답률로 잡아야 한다(BS&Co).

#### (3) 세그먼테이션 전략 (팝업 비즈니스 기준)

- 최소 세그먼트 4축: ① **어느 팝업**에서 유입(클라이언트 브랜드별 — B2B 리포트의 핵심), ② 옵트인 채널(QR/키오스크/예약), ③ 참여도(오픈·클릭 최근 90일), ④ 구매/비구매.
- 참여 기반 발송 억제(비참여 90일+ 제외)는 Klaviyo 활성 프로필 과금 구조에서 **비용 절감과 도달률 개선을 동시에** 만든다(주1 출처).
- 자동화가 캠페인 대비 전환 19배·매출 22배(Omnisend 2025)라는 것의 실무적 의미: 인력이 없어도 **플로우 5개(웰컴·포스트이벤트·윈백·waitlist·월렛설치)가 캠페인보다 먼저**다.

### c-4. 리텐션·재방문 — 윈백/리엔게이지먼트 벤치마크

| 플로우 | 오픈율 | 클릭률 | 전환율 | 출처 |
|---|---|---|---|---|
| 고객 재활성(윈백) 자동화 | 33.11% | 1.99% | 0.54% (이메일당 매출 $0.51) | Omnisend 2025 (WebFetch 확인) |
| 윈백 플로우 (Klaviyo 실계정 중앙값) | — | — | 0.09% (첫 메일) | BS&Co (WebFetch 확인) |

- 해석: 윈백은 전 플로우 중 성과 최하 구간. 그럼에도 유지하는 이유는 ① 리스트 위생(비참여자 걸러내 과금·도달률 방어), ② 클릭한 사람의 구매 전환은 높음. **공격적 세그먼트+실질 오퍼 없이는 윈백을 늘리지 말 것**(BS&Co의 결론과 동일).
- 팝업 맥락의 윈백 = "재방문 유도": 다음 팝업 공지 사전등록을 윈백 오퍼로 쓰면 할인 없이 재활성 가능 — Vacation Inc.의 waitlist 방식(아래 케이스 2) 참조.
- 리엔게이지먼트 시퀀스 표준 4단계: 재자극 → 피드백 요청 → 인센티브 → 마지막 통보(이후 리스트 정리). 윈백 수신 후 후속 메일을 다시 여는 비율 ~45% [추정 — 업계 통설, Flowium/Klaviyo 블로그 계열].

### c-5. 비교 결론 — 팝업/경험 비즈니스(비 Shopify·오프라인 리드 중심) 권고

1. **기본값은 Klaviyo Email($20~60/월 구간 시작)**: QR 사인업 폼→플로우→세그먼트가 한 플랫폼이고, a·b단계 도구(Flowcode·Luma·PassKit)와의 연동 생태계가 가장 넓다. 이미 플레이북 섹션 6의 기본값과 일치.
2. **클라이언트 이관·저빈도 대량 리스트에는 Brevo**: 발송량 과금이라 리드 보관 원가가 사실상 0 — 팝업 종료 후 리드를 "보관+분기별 뉴스레터"로 유지하는 세컨드 레이어로 최적($9/월~).
3. Omnisend는 Shopify 스토어 전제 기능이 많아 비커머스 팝업엔 이점이 반감되고, Customer.io($100/월~)는 자체 앱/제품 이벤트 데이터가 생기는 단계(예: Digital Passport 상용화 이후)에 재검토.
4. Mailchimp은 저가 진입용일 뿐 자동화 깊이·프로필 과금 모두에서 중간값 — 신규 도입 이유가 없다.
5. 운영 공식: **Klaviyo(활성 리드·플로우) + Brevo(장기 보관·저빈도) 이원화**, 플로우 5종을 캠페인보다 먼저 구축.

---

## 참고 케이스 — 방문객→이메일 DB→너처링 실사례

### 그룹 1. 브랜드/팝업의 이메일 캡처→너처링

#### 케이스 1 — Glossier: 팝업을 'DTC 데이터의 오프라인 검증 장치'로
- **무엇을**: 온라인 커뮤니티/웹 트래픽이 강한 도시에 먼저 팝업을 열어 수요를 검증한 뒤 상설 매장으로 전환(시애틀: 팝업 → 6,200sqft 상설점). 오프라인 경험은 온라인 CRM(이메일·앰배서더)과 하나의 생태계로 연결.
- **성과**: 시애틀 팝업 **구매전환율 70%+**(자사 오프라인 최고), 팝업 평균 60%·상설점 평균 50% 전환. 상설 전환의 근거가 팝업 성과 데이터였다는 점이 핵심.
- **시사점**: 팝업 = 리드·전환 데이터를 만드는 검증 자산이라는 프로젝트렌트의 상품 논리를 그대로 입증하는 레퍼런스. "팝업 전환 데이터 → 상설/유통 의사결정" 스토리를 클라이언트 제안에 인용 가능.
- **출처**: https://www.retaildive.com/news/glossier-opens-seattle-store-as-the-first-in-brick-and-mortar-push/604891/ (WebFetch 확인)

#### 케이스 2 — Vacation Inc.: 이메일 리스트가 곧 론칭 엔진
- **무엇을**: '80년대 리조트 세계관'의 선케어 브랜드. 가입자에게 가짜 직함("shrimp cocktail designer" 등)을 부여하는 엔터테인먼트형 뉴스레터를 성수기 주3회·비수기 주2회 발송. 신제품(Orange Gelée)은 4개월간 waitlist를 쌓아 론칭.
- **성과**: 뉴스레터 오픈율 **런칭 이래 지속 50%+**(업계 기준 37%). Orange Gelée waitlist **15,000명**, 출시 **3일 만에 완판**. 연매출 $40M(전년 대비 250% 성장) 시점의 전략.
- **시사점**: "재미가 옵트인의 인센티브"가 될 수 있다는 증거 — 할인 없이 세계관·콘텐츠로 오픈율을 유지. 팝업 종료 후 다음 팝업 waitlist를 윈백 오퍼로 쓰는 모델의 원형.
- **출처**: https://digiday.com/marketing/under-the-skin-of-sunscreen-challenger-brand-vacations-email-newsletter-strategy/ · https://www.glossy.co/pop/glossy-pop-newsletter-what-vacation-did-next-the-3-year-old-brand-continues-to-shake-up-up-the-sunscreen-category/ (모두 WebFetch 확인)

#### 케이스 3 — Museum of Ice Cream: 티켓팅이 곧 DB (정성 케이스)
- **무엇을**: 유료 타임슬롯 티켓제 경험 뮤지엄. 오픈 전 수 주간 내부 이미지 없이 티저 콘텐츠만으로 수요를 만들고, 온라인 사전 티켓 구매 과정에서 방문객 연락처·방문 데이터를 전량 확보. 스폰서(Tinder)와는 방문객 설문으로 '아이스크림 취향 프로필' 데이터를 공동 수집 [추정 — 2차 보도].
- **성과**: "경험 이미지를 한 장도 공개하지 않고 완판"(공동창업자 인터뷰). 2016 오픈 당일 블록을 두른 대기줄. 구체 이메일 지표는 비공개 → 정성 시사점만.
- **시사점**: **유료 티켓제 자체가 최강의 이메일 캡처 장치**(구매=100% 옵트인 접점). 프로젝트렌트가 무료 입장 팝업에도 '사전 예약제'를 끼워 넣어야 하는 이유.
- **출처**: https://tripleseat.com/blog/3-marketing-tips-from-the-museum-of-ice-cream-that-will-help-you-increase-sales/ · https://www.adweek.com/brand-marketing/what-experiential-marketers-can-learn-museum-of-ice-cream/ (모두 WebFetch 확인)

### 그룹 2. QR·월렛 패스·CRM으로 재방문/매출을 만든 케이스

#### 케이스 4 — Starbucks Rewards: 로열티 DB가 매출의 절반 이상
- **무엇을**: 앱+월렛 기반 선불·포인트 로열티. 결제·주문·리워드를 한 계정에 묶어 방문마다 데이터가 쌓이는 구조.
- **성과**: 리워드 회원이 **미국 매출의 57%**(2024 기준; FY2025 보도로는 60% 수준·연 $13B+ [추정 — 2차 보도]). 글로벌 회원 75M+, 회원은 비회원 대비 **방문당 지출 3배**.
- **시사점**: 식별된 고객(로열티 DB)의 매출 기여가 압도적이라는 미국 소매의 대표 증거. 팝업 리드 DB의 장기 가치를 설득하는 헤드라인 숫자로 사용.
- **출처**: https://www.stampme.com/blog/how-successful-is-starbucks-rewards (WebFetch 확인; 공식 IR 페이지는 봇 차단으로 2차 출처 사용)

#### 케이스 5 — Sweetgreen SG Rewards: 복잡한 로열티를 버리고 단순 포인트로
- **무엇을**: 2025년 4월, 유료 구독형(Sweetpass, $100/년)을 폐기하고 $1=10포인트 단순 적립으로 전면 개편. 앱/웹 계정 기반 자동 등록 + 1,000포인트 가입 인센티브로 디지털 고객 DB를 재가속.
- **성과**: 개편 배경 = 기존 프로그램이 "너무 복잡하다"는 고객 데이터. 론칭 후 주당 신규 디지털 고객 2만 명·로열티 회원 방문빈도 2배 보도 [추정 — 2차 보도, 1차 IR 미확인].
- **시사점**: 옵트인 장치는 단순할수록 강하다 — 팝업 현장 가입도 '한 줄 가치제안+즉시 보상' 구조가 정답. 복잡한 스탬프/티어는 현장에서 죽는다.
- **출처**: https://www.restaurantdive.com/news/sweetgreen-points-based-sg-rewards-ripple-fries/744283/ (WebFetch 확인)

#### 케이스 6 — 월렛 패스(Apple/Google Wallet) 리텐션 벤치마크
- **무엇을**: 앱 설치 대신 QR 한 번으로 지갑에 들어가는 로열티/멤버십 패스. 락스크린 푸시·지오펜스 알림으로 재방문 유도, CRM 프로필과 동기화.
- **성과**: 30일 내 패스 이탈률 **10% 미만**(독립 로열티 앱은 1주 내 90% 이탈), 펀치카드 대비 **재방문 빈도 +28%**, 단일 매장 기준 앱 대비 **가입률 3~4배**, 월렛 푸시 발송비 $0.
- **시사점**: a·b단계에서 확보한 이메일 위에 월렛 패스를 얹으면(가입 직후 설치 유도) 이메일 오픈율(~20%)로는 못 만드는 상시 재접점이 생긴다. 플레이북 섹션 6의 PassKit($39.50/월) 스택과 직결.
- **출처**: https://regulr.ai/blog/apple-wallet-loyalty-programs (WebFetch 확인; PassKit 2024 리포트·Square 2025 Loyalty Report 인용 집계 — 원리포트 [확인필요])

### 그룹 3. '경험+측정+CRM 결합' 비즈니스 모델 벤치마크

#### 케이스 7 — AnyRoad: 경험 데이터 플랫폼 (이번 리서치로 실체 확인)
- **무엇을 하는 회사인가**: "이벤트를 위한 AI 소비자 인게이지먼트 플랫폼". 모듈 구성 — ① Guest Experience(예약·티켓팅·게스트 커뮤니케이션), ② Experience Manager(운영 자동화, QR 체크인·디지털 웨이버), ③ Data Capture+Experience Surveys(현장 1st-party 데이터·사후 설문), ④ Atlas Insights(경험의 브랜드 임팩트·ROI 분석, 오픈텍스트 AI 분석). 고객: Diageo, Ben & Jerry's, Budweiser, Sierra Nevada, Molson Coors, Hennessy, Pernod Ricard 등. 연 15M+ 데이터포인트 수집, 고객 평균 NPS +36.
- **성과 사례(Diageo·Johnnie Walker Princes Street)**: £185M 투자 방문자 센터에 티켓팅+취향 프로필 커스터마이즈+분석 적용 → **방문 전후 NPS +16pt**, 저공략 인구집단의 위스키 음용 의향 **+40%**.
- **가격**: 무료 티어(RSVP·무료 이벤트 60일), 유료 이벤트는 티켓액의 7%+결제수수료. 엔터프라이즈 플랜 RFQ.
- **프로젝트렌트와 같은 점/다른 점**: 같은 점 — "경험을 측정 가능한 브랜드 자산으로" 만드는 명제, 방문객 데이터→CRM 연계. 다른 점 — AnyRoad는 **SaaS(도구만 제공)**이고 경험 기획·제작은 안 한다. 프로젝트렌트는 기획·제작·운영까지 하는 풀스택이므로, AnyRoad는 경쟁자라기보다 '측정 레이어의 기능 벤치마크'(플레이북 6.6 Cultural Engagement Score의 대조군).
- **출처**: https://www.anyroad.com/ · https://www.anyroad.com/customers/diageo (모두 WebFetch 확인)

#### 케이스 8 — Leap: RaaS(Retail-as-a-Service)
- **무엇을**: DTC 브랜드 대신 임대계약·시공·인력·운영·데이터까지 통째로 맡아 오프라인 매장을 열어주는 플랫폼. 100개 매장·175+ 브랜드(Bombas, Frankies Bikinis, M.M. LaFleur 등), LA·마이애미·시카고·NYC 등 12개 시장. 월 12만+ 방문 데이터·5,000만+ 옴니채널 고객 데이터로 입지·운영 최적화. 2025년 1월 $20M 조달·흑자 전환 발표.
- **시사점(같은 점/다른 점)**: 같은 점 — "브랜드는 리스크 없이 오프라인 진출, 운영·데이터는 플랫폼이"라는 가치제안이 프로젝트렌트의 팝업 대행과 동형. 다른 점 — Leap은 **상설 매장·리테일 운영**이 본체(장기 임대·판매 인력)이고 경험 기획력은 없음. 프로젝트렌트는 단기 팝업·브랜딩 경험이 본체 — "Leap의 데이터 운영 모델 × 팝업 버전"으로 포지셔닝 서사에 활용 가능.
- **출처**: https://www.leapinc.com/ (WebFetch 확인)

#### 케이스 9 — Fever: 수요 데이터로 경험을 '제조'하는 플랫폼
- **무엇을**: 문화·라이브 엔터테인먼트 디스커버리 플랫폼(연 3억 명 도달·40+개국). 자체 미디어 네트워크의 검색·수요 신호로 흥행을 사전 예측해 Candlelight 같은 오리지널 경험을 직접 제작·양산. B2B(Fever for Business)로 Meta·MGM·Pfizer 등 1,000+ 기업 행사에 진출.
- **시사점(같은 점/다른 점)**: 같은 점 — 데이터로 경험의 성패를 예측·측정하고, B2C 경험을 B2B 상품으로 재판매하는 이중 수익 구조. 다른 점 — Fever는 **자체 수요(트래픽·티켓) 플랫폼**을 가졌고 프로젝트렌트는 클라이언트 브랜드 수요 기반. 시사점은 "티켓·예약 데이터를 자산화해 다음 기획의 근거로 쓰는 루프" — 프로젝트렌트가 이메일 DB로 만들 수 있는 최소 버전의 루프다.
- **출처**: https://newsroom.feverup.com/en-US/249796-fever-strengthens-its-corporate-events-division-in-the-us-with-the-launch-of-candlelight-for-business/ (WebFetch 확인)

---

## 검증 로그 (2026-07-07)

- 3중 검증: 검색 추출 → 공식/1차 출처 WebFetch 대조 → 2차 출처 재대조(가격은 최소 2개 출처 일치 확인). 불일치 항목은 [추정]/[확인필요] 표기.
- **a·b 섹션(업체 21개)**: 전 공식링크 WebFetch 확인 24건, 최종 죽은 링크 0. 우회 처리 5건 — QR Tiger는 /pricing 404→공식 /payment로 대체, Klaviyo 폼은 헬프센터 문서로 대체, 구 Sumo 팝업 통계는 후신 bdow.com으로 대체, Wisepops는 /blog/popup-stats로 대체, icapture.com은 cvent.com 301(인수 통합) 확인. Beaconstac→Uniqode 리브랜딩(2024-01-10)은 공식 발표+PR Newswire 교차 확인. Mailchimp Subscribe 앱은 App Store에서 내려간 정황으로 단종 [추정] 처리.
- **c·케이스 섹션 — WebFetch 확인(200+내용 일치) URL 23건**: klaviyo.com/pricing, mailchimp.com/pricing/marketing, brevo.com/pricing(실재 확인·본문은 JS렌더링), customer.io/pricing, omnisend.com/pricing, retainful.com(klaviyo-pricing), costbench.com(brevo), smtpedia.com(brevo-pricing), encharge.io(customer-io-pricing), omnisend.com/blog/email-marketing-benchmarks, bsandco.us(klaviyo-flow-benchmarks), digiday.com(vacation), glossy.co(vacation orange-gelee), tripleseat.com(moic), adweek.com(moic), retaildive.com(glossier-seattle), stampme.com(starbucks-rewards), restaurantdive.com(sweetgreen), regulr.ai(wallet-loyalty), anyroad.com, anyroad.com/customers/diageo, leapinc.com, newsroom.feverup.com(candlelight-for-business).
- **WebFetch 실패(문서에 미인용) 7건**: emailtooltester.com klaviyo/mailchimp pricing(403), help.brevo.com(403), shopify.com/retail/museum-of-ice-cream(404), about.starbucks.com 2026 press(403), datanext.ai glossier(403), wonderfulmuseums.com(403). retailboss.co(200이나 페이월로 본문 미확인 → 미인용).
