# 자동 리서치 브리프 — 맥미니 무인 실행용

> 이 파일은 맥미니의 headless claude(`--dangerously-skip-permissions`)에 투입되는
> 자기완결적 지시서다. 승인 없이 끝까지 실행한다. 아래 순서대로 수행하라.

## 컨텍스트
너는 프로젝트렌트(한국 성수동 기반 오프라인 마케팅/팝업 RaaS 플랫폼)의 **미국(LA) 진출
마케팅 플레이북**을 위한 리서치를 수행한다. 회사의 현재 상품 라인업은 아래 두 원본에 있다:
- `10-projects/34-rent-us-marketing-playbook/source/profile-2026.txt` (IR 덱)
- `10-projects/34-rent-us-marketing-playbook/source/standard-guide.txt` (30여 개 상품 원화 가격표)

먼저 이 두 파일을 **반드시 읽어라.** standard-guide.txt에는 개별 상품명·가격이 다 있다.

## 미션 (센터피스)
스탠다드 가이드의 **개별 상품 30여 개 각각에 대해**, LA/미국 현지에서 적용 가능한 대안이
있는지 조사하고, 있으면 **USD 가격 기준까지** 찾아라. 결과를
`10-projects/34-rent-us-marketing-playbook/research/tool-la-alternatives.md`에 표로 작성한다.

표 컬럼: `상품 | 한국 채널·가격(₩) | LA/US 대안 | LA 가격 기준(USD) | 전이도(★1~5) | 출처URL`

8개 카테고리로 묶어 조사(누락 0):
- **A. Owned/Aggregator 소셜**: Rent IG / 인스타 파워페이지(뭐하지 등) → LA 애그리게이터 IG
  (@secretlosangeles·@eater_la·@lafoodie·The Infatuation) 스폰서 포스트 단가 / 침투 바이럴
  (카카오오픈챗·네이버카페·당근) → Reddit·Nextdoor·FB Groups·Discord
- **B. 인플루언서/체험단**: 메가·매크로·마이크로 US 티어별 요율 / 체험단 → UGC creator gifting(FTC #ad)
- **C. PR/미디어/뉴스레터**: 보도자료 → PR Newswire·Business Wire + LA Times·LAist·Eater LA·
  Time Out LA·Secret LA / 기획기사 → sponsored feature / 주말랭이 → US 로컬 뉴스레터 스폰서십
- **D. Paid Digital**: Google Ads / 네이버→Bing / GFA·카카오배너→GDN·프로그래매틱 / Meta Ads /
  토스 머니알림·행운퀴즈 → US 리워드앱(Fetch·Ibotta) 근사치 / 에브리타임 → Fizz·Sidechat
- **E. OOH/오프라인**: 포스터+휴먼빌보드 → wild posting·sign spinner·street team / 건물외벽 →
  Arts District·Melrose 빌딩랩·뮤럴 / 버스·지하철 → LA Metro + 프리웨이 빌보드·Uber/Lyft 탑퍼
  (Adomni·Firefly) / 엘리베이터 → Captivate
- **F. F&B/예약/경험 인프라**: 캐치테이블 → Resy·OpenTable·Yelp Waitlist·Tock·Eventbrite RSVP
- **G. 측정/리포트/설문**: People Counting 특허 → Placer.ai·Density·RetailNext / 설문 → Typeform·SurveyMonkey
- **H. 영상/사진**: 공간사진·스캐치·릴스·숏츠 → LA 프로덕션 day rate·UGC creator rate

## 검증 규칙 (필수 — CLAUDE.md 3중 검증)
모든 USD 가격·수치는: (1)추출 (2)신뢰출처 웹대조 (3)재대조. 단위(월/건/CPM·CPP)·귀속
(누구 단가)·맥락을 대조해 표기. **불확실하면 지어내지 말고** `[추정]`/`[확인필요]` 태그 +
근거 범위로 남겨라. 각 가격 셀에 출처 URL 병기. 가격 미공개 시장은 "요청견적(RFQ)"로 명시.

## 추가 리서치 (센터피스 완료 후, 여유 시)
메인 문서 `us-marketing-playbook.md`에 아래 섹션 초안도 작성:
4. 미국 experiential/retail media 시장규모·주요 경쟁사·Experience Economy 수치(검증)
5. 규제·실무: TCPA(SMS)·CAN-SPAM(Email)·CCPA(데이터)·OOH 퍼밋·FTC 인도스먼트 가이드
6. 신규 솔루션: QR+Email/SMS CRM·RSVP·Digital Passport·NFC·Cultural Engagement Score
7. US 리포지셔닝: Experience→Engagement→Data→CRM→Community
(0~3, 8번 섹션은 사용자가 취향판단하므로 뼈대만.)

## 산출·마무리
- `research/tool-la-alternatives.md` (센터피스) + `us-marketing-playbook.md`(섹션4~7 초안) 작성
- `34-progress.md`의 체크박스·작업로그·액션아이템 갱신(날짜 2026-07-05, "맥미니 무인 실행")
- 완료 후 `git add -A && git commit -m "research(34): LA 대안·가격 매핑 + 섹션4~7 초안 (맥미니 무인)"`
  후 `git push`(가능 시). push 충돌 시 커밋만 남기고 progress에 기록.
- HTML 덱은 만들지 말 것(사용자 리뷰 후 별도). PNG 생성 금지.
