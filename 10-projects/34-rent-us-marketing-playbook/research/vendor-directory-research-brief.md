# 추가 리서치 브리프 (D) — A~F 카테고리 업체 디렉토리(세부가이드)

너는 프로젝트렌트 US 플레이북의 **카테고리 A~F 업체 디렉토리**를 만든다. 승인 없이 끝까지 실행하라.
병렬 리서치 에이전트를 카테고리별로 나눠 돌리고, 모든 가격·공식링크는 3중 검증한다.

## 목적
상품 카테고리 A~F 각각에 대해 **미국/LA 실제 업체**를 이름·공식링크·기본서비스·가격·서비스종류로
정리한 세부 가이드. 기존 `research/tool-la-alternatives.md`가 "채널 유형·가격"이라면, 이번 건
**"구체적 named 업체 + 클릭 가능한 공식링크 + 그 업체로 가능한 마케팅 서비스 종류"**로 확장·심화한다.

## 먼저 읽을 것
- `research/tool-la-alternatives.md` (A~F에 이미 나온 LA 대안·가격 — named 업체로 확장할 씨앗)
- `research/email-db-acquisition-plan.md` (업체 디렉토리 포맷 참고 — 같은 밀도로)

## 미션 — `research/vendor-directory-A-F.md` (신규)
6개 섹션(A~F). **각 섹션마다 업체 표**:
`업체명 | 공식링크(WebFetch 200 확인) | 기본 서비스(무엇을 파는가) | 가격 | 가능한 마케팅 서비스 종류`
각 섹션 하단에 "선택 가이드"(어떤 상황에 어느 업체) 2~4줄.

- **A. Owned/Aggregator 소셜**: LA 애그리게이터 IG(Secret Media Network/Fever·The Infatuation·Eater LA(Vox)·Discover LA·DailyHive·Time Out 등), 커뮤니티 광고(Reddit Ads·Nextdoor Ads·Facebook Groups·Discord), 인플루언서/UGC 애그리게이터. 서비스종류=스폰서 피드/스토리/릴스·커뮤니티 네이티브 광고.
- **B. 인플루언서/체험단**: 인플루언서 마켓플레이스·플랫폼(Collabstr·Aspire·GRIN·Upfluence·#paid·Insense·Billo·Trend.io·Social Cat gifting 등), UGC 플랫폼. 서비스종류=티어별 유료 포스트·gifting·UGC 영상·whitelisting.
- **C. PR/미디어/뉴스레터**: 와이어(PR Newswire·Business Wire·PRWeb·EIN Presswire), LA 매체(LA Times Studios·LAist·Eater LA(Vox Creative)·Time Out LA·Secret LA), 로컬 뉴스레터(6AM City·LA Taco·The LAnd·Paved 마켓플레이스·beehiiv), 부티크 PR 에이전시. 서비스종류=와이어 배포·스폰서 피처·뉴스레터 스폰서십·PR 리테이너.
- **D. Paid Digital**: Google Ads·Microsoft(Bing) Ads·Meta Ads·Google Display·프로그래매틱 DSP(StackAdapt·Basis 등)·리워드앱(Ibotta·Fetch)·캠퍼스(Fizz·Sidechat)·오퍼월(Unity/Tapjoy·Digital Turbine/Fyber). 서비스종류=검색·디스플레이·소셜·리타게팅·리워드/인게이지먼트.
- **E. OOH/오프라인**: wild posting(Wildposting.com·ALT TERRAIN·Blue Line Media·SAUCED LAB), sign spinner(AArrow)·street team(Street Teams Co), 뮤럴(Colossal Media·Overall Murals), wallscape/빌보드(AdQuick·Lamar·Outfront·Clear Channel), 트랜짓(Intersection=LA Metro), 라이드셰어(Adomni·Firefly), 엘리베이터(Captivate·Vertical Impression·Screenverse), 시네마(NCM), 공항(JCDecaux). 서비스종류=와일드포스팅·월스케이프·트랜짓·라이드셰어·엘리베이터·시네마·공항·스트리트팀.
- **F. 행사당 렌탈→SaaS 월구독(F&B·예약·경험 인프라)**: 예약(Yelp Guest Manager·Tock·OpenTable·Resy·SevenRooms), RSVP/티켓(Eventbrite·Luma·Partiful·Posh), 웨이팅(Yelp Waitlist), 예약앱 광고(Yelp Ads·OpenTable Boost/Bonus Points). 서비스종류=예약·웨이팅·RSVP/티켓팅·선결제/노쇼방지·예약앱 내 검색광고.

## 검증·마무리 (필수)
- 3중 검증(추출→공식출처 대조→재대조). 가격은 공식 페이지 우선, 비공개는 RFQ, 불확실 `[추정]`/`[확인필요]`.
- **모든 업체 링크는 실재하는 공식 URL** — WebFetch로 200 확인, 죽은 링크 금지(리다이렉트/변경 시 실 URL로 교체).
- 기존 tool-la-alternatives.md와 수치가 상충하면 최신 공식가 우선, 상충 사실을 표기.
- `34-progress.md`에 "2026-07-07 업체 디렉토리(D) 완료" 로그 추가.
- `git add -A && git commit -m "research(34): A~F 카테고리 업체 디렉토리(세부가이드)"` 후 `git push origin HEAD:feat/34-us-marketing`(실패 시 커밋만).
- **HTML·PNG는 만들지 말 것** — 통합·시각화는 사용자 세션에서.
