# GUBI × 답십리 전시기획 제안서

## 프로젝트 개요
- **클라이언트**: GUBI (덴마크 디자인 헤리티지 브랜드, 1967 코펜하겐)
- **컨셉**: Heritage Meets Heritage — 덴마크 디자인 헤리티지 × 답십리 로컬 헤리티지
- **핵심 전략**: 단순 공간 대관 제안이 아니라 "지역 문화 프로젝트"로 격상. "왜 답십리가 GUBI 헤리티지와 연결되는가"를 설득
- **소유/제안 주체**: Project Rent
- **시작일**: 2026-06-12

## 핵심 논리 (Wow Moment)
- **GUBI** = Design Heritage Reimagined (잊혀진 20세기 디자인 아이콘을 발굴·재해석)
- **답십리** = Cultural Heritage Reimagined (오래된 물건이 새 주인을 만나 재발견되는 곳)
- → 두 헤리티지 철학이 **물리적으로 일치**. "GUBI는 답십리를 설명하고, 답십리는 GUBI를 증명한다"
- 신뢰 기반: 프로젝트렌트가 성수동 팝업 문화(2019 가나초콜릿하우스)를 만들고, 답십리 OUVRE를 직접 운영하는 당사자

## 사용자 확정 사항
- 언어: 국문 본문 + 영문 헤드라인
- OUVRE·성수동 서사: 사실로 반영 (수치는 사용자 추가 제공)
- 4개 전시장(두손/고복희/호박/오브): placeholder 페이지 + "🔄 UPDATE PENDING" 표시
- 근거 데이터: 별도 부록 없이 본문에 녹임
- GUBI 헤리티지 포커스 컨셉 반영

## 2026-06-12 — v1 초안 제작

### 조사
- GUBI 웹 조사: 1967 코펜하겐 설립, 2000년대 relaunch, "rediscovering 20th century design treasures" 철학, Beetle Chair·Bestlite·Multi-Lite·Gräshoppa 등 발굴 아이콘, glamorous·sensual·eclectic 미학
- 프로젝트렌트 정체성: `20-operations/R_define/` — 리테일 미디어 플랫폼, Retail as Media/Editorial Discipline/Modular Scalability, 250+ 팝업·60억·RXR 특허

### 산출물
- [x] `reports/gubi-dapsimni-proposal-v1-2026-06-12.html` — **20p HTML PT** (프로젝트렌트 표준 다크테마, #6C5CE7, Pretendard, 키보드 네비+편집모드)
  - s01 Cover: Heritage Meets Heritage
  - s02 Why Seoul, Why Now (Big Shift)
  - s03 About GUBI / s04 GUBI's Heritage Focus
  - s05 About Project Rent / s06 성수동을 만든 팀 / s07 답십리 OUVRE
  - s08 Our Difference (We Create Context)
  - s09~s10 Why Dapsimni (헤리티지 디스트릭트 + 크리에이티브 디스트릭트)
  - **s11 Why GUBI Fits Here — Heritage Meets Heritage (★Wow)**
  - s12 Exhibition Concept / s13~s16 거점 4곳 (placeholder)
  - s17 Visitor Flow / s18 Beyond Exhibition / s19 Why Project Rent / s20 Closing
- [x] config.json

### 2026-06-12 수정
- [x] 답십리 공간 표기 정정: "오브/OUVRE" → **`of`**, 인스타그램 **`@ofjec_t`** 추가 (s07·s12·s15)
- [x] 내부 검토용 PDF 생성 `gubi-dapsimni-proposal-v1-2026-06-12.pdf` (21p)
- [x] **편집 가능한 PPTX 생성** `gubi-dapsimni-proposal-v1-2026-06-12.pptx` (20슬라이드, 16:9 다크테마)
  - python-pptx로 텍스트박스·도형·표 모두 편집 가능 객체로 구현 (이미지 캡처 0) — `build_pptx.py`
  - 폰트 Pretendard 지정(미설치 PC는 fallback), 총 도형 179개·표 1개

### 2026-06-12 — HTML 인라인 편집기 내장
- [x] HTML에 PPT 수준 편집기 통합 (우상단 **✏️ Edit** 버튼 → 편집모드)
  - 텍스트 서식: 굵게(B)·기울임(I)·밑줄(U)·크기(A±)·색상 6종 (드래그 선택 후 적용, execCommand)
  - 이미지: 버튼 추가 + 슬라이드로 **드래그&드롭** (거점 placeholder에 드롭 시 배경 채움), 휠로 크기조절, ✕ 삭제
  - 오브젝트 이동: **이동 모드**에서 카드·표·이미지 끌어 위치 이동(translate/absolute)
  - **저장**: 편집본을 새 HTML로 다운로드 (이미지 base64 포함, 편집 UI 자동 제거)
  - @media print에서 편집 UI 숨김 → PDF/PPT 영향 없음

### 2026-06-13 — 축약본(Short) 제작
- [x] `reports/gubi-dapsimni-proposal-short-2026-06-13.html` — **13장 느슨한 축약본**
  - 통합: GUBI+헤리티지포커스(s02), PR소개+성수동(s03), 답십리 디스트릭트 2장→1장(s05), Concept+Journey(s07), Beyond+WhyPR(s12)
  - 거점 4곳(두손/고복희/of/호박)은 개별 유지 + placeholder
  - 동일 디자인 시스템 + 인라인 편집기(텍스트서식·이미지 드래그&드롭·이동·저장) 그대로 탑재
  - 풀버전(20장 v1)은 그대로 보존
- [x] 축약본에 **"The Perfect Stage" 슬라이드 신설** (s06, 13→14장)
  - 답십리=서울 최강 역사 콘텐츠 밀도 + 힙의 재부상(of·해외·DJ) + "구비 100년 역사 × 답십리 축적된 시간 = 하나의 사건" 시너지
  - s05(동네 소개)→[신규 s06]→s07(Heritage Meets Heritage Wow) 빌드업 배치, slide-number 01~14 재정렬

## 2026-06-15 — 신규 브랜드 「리진(LI-TSIN)」 브랜드 씽킹 시뮬레이션

답십리 **같은 동네**의 별개 신규 브랜드 컨셉(GUBI 전시와 무관). 하이엔드 컬처 라이프스타일 살롱 — 조선 무희 리진 서사 + 헤리티지 트랜스레이션(3-Pillar) + 답십리 게이트웨이.

- [x] `/brand-thinking` 9-Phase 시뮬레이션 → `litsin-brand-simulation.md`
- 핵심 결론:
  - **리진의 직무 = 번역가/게이트웨이** — 인물 서사와 사업 기능이 정확히 일치
  - **자산-정체성 역설 경보**: F&B가 가장 돈 됨 → "예쁜 카페" 수렴 위험. F&B=미끼, 공예=목적지로 구조 고정
  - 추천 하이브리드: **정체성=게이트웨이(B안) × 수익=3층 깔때기**(F&B 게이트 → 큐레이션 커머스 → 멤버십 살롱)
  - 불공정 우위 = Project Rent가 답십리 당사자(`of` 운영, 점주·장인 네트워크) → 외부 복제 불가
- ⚠️ 리진 실존 여부 학계 논쟁 → 카피는 "전설/모티프" 톤으로(사실 단정 금지)
- 사용자 확정 (2026-06-15):
  - **사업 무게중심 = 답십리 앵커 시설** (자체 P&L 아닌 동네 활성화. KPI=동네 트래픽·QR전환·멤버십)
  - **F&B 직영 + "리진" 명칭 전면** (실존 논쟁은 "전설/모티프" 톤으로 회피하며 이름은 당당히 사용)
  - 출력 = 클라이언트 제안 HTML 덱 (Mode B)
- [x] `litsin-brand-proposal-2026-06-15.html` — **11p PT 덱**(project-rent 다크테마, #6C5CE7, Pretendard, 키보드 네비+편집모드+SAVE)
  - 01 Cover(LI-TSIN) / 02 The Tension(콘텐츠 No.1 vs 문턱) / 03 The Woman(리진 서사·전설톤) / 04 The Idea(헤리티지 트랜스레이션) / 05 One Scene(한 테이블 동서고금) / 06 Three Pillars(공예=주연) / 07 Gateway 3층 깔때기 / **08 Anchor Thesis(동네 로비·앵커 KPI ★무게중심)** / 09 Why Project Rent(4 Moat) / 10 Evolution / 11 Closing
  - 공간스펙·예산·오픈시점 = `TBD` 자리표시자로 표기 (커버/클로징)
  - 검증: 1710×929 뷰포트 전 슬라이드 overflow 없음(최대 30px 여유), 콘솔 에러 favicon 404뿐, 키보드 네비 정상
- [x] **v2 (2026-06-15 오후)** — 사용자 피드백 반영 재작성:
  - 전체 폰트 약 1.5배 확대 (본문 15→22, h2 46→64, 라벨 11→15 등), 패딩·갭 축소로 흡수
  - 메인 타이틀군 **Pretendard Bold(700)** 전환, 본문 weight 400으로 상향
  - **배꽃(梨花) 모티프 신규 슬라이드 추가** → 11→12장. "04 The Pear Blossom — 이름에 담긴 향, 배꽃" (오감 아이덴티티: 후각=배꽃 시그니처 센트 / 시각=흰5장꽃잎·梨花月白 / 미각=맑은 단맛·배 숙성 크림)
  - 배꽃=경계의 꽃(낮↔밤·흑↔백) → '경계를 넘은' 리진 서사와 동형. 모티프 출처=이조년 「다정가」(정서 차용, 직접인용 아님)
  - simulation.md에 `Phase 6.5 BRAND IDENTITY CODE` 섹션 추가(오감 시그니처+한자 주의)
  - 재검증: 1440×810(16:9 노트북, 빡빡) 전 12슬라이드 body overflow 0, 콘솔 favicon 404뿐
- [x] **v3 (2026-06-15 저녁)** — 폰트 재조정 + 아이덴티티 + PR 비노출:
  - 폰트 50%→**20% 확대로 하향**(v1 대비 1.2배). 13장 v2의 큰 글씨 호소 반영
  - **Identity System 슬라이드 추가**(로고 락업 + 시그니처 센트 3단[Top 배꽃·청배 / Heart 백목련·백차·묵향 / Base 침향·한지·머스크] + Core Palette 5색)
  - 배꽃 SVG 로고는 잠시 넣었다가 **사용자 지시로 전부 삭제**(이미지 대신 워드마크 LI-TSIN·梨花·La Fleur 락업만)
  - ⚠️ **Project Rent 흔적 전면 제거**(사용자 지시): "Why Project Rent" 슬라이드 삭제, of/@ofjec_t·ws.choi·RXR·by Project Rent·crew 크레딧 모두 제거 → 리진 브랜드 자체 중립 자료화. footer/brand-mark/meta = "LI-TSIN"으로 통일. (※ 평소 'by Project Rent' 크레딧 룰의 예외 케이스)
  - 최종 **12장**: Cover/Tension/Woman/PearBlossom/**Identity**/Idea/OneScene/Pillars/Gateway/Anchor/Evolution/Closing
  - 검증: PR·SVG 흔적 grep 0건, 1440×810 전 12슬라이드 body overflow 0

### 남은 작업 (GUBI 전시 — 기존)
- [ ] **4개 전시장 상세정보 업데이트** (두손갤러리 평수·사진, 고복희/오브/호박 면적·프로그램)
- [ ] OUVRE 성과 수치 확정 (방문객·매출·미디어 노출 등)
- [ ] GUBI 이번 전시의 구체 방향(전시 작품 리스트, 헤리티지 테마) 반영
- [ ] 일정·예산 섹션 추가 검토
- [ ] 최종 QA 후 공유본(PDF) 제작
