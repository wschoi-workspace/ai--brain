# 34 · 프로젝트렌트 US/LA 마케팅 진출 플레이북 — Progress

> 목적: 프로젝트렌트 US 진출 마케팅 플레이북(내부 범용). 개별 상품 30여 개를 LA 대안 +
> USD 가격으로 매핑하고, 시장·경쟁·규제·신규솔루션·리포지셔닝을 얹은 실행문서.
> 산출물: md 리서치 + project-rent 다크테마 HTML 덱.

## 원본 자료 (repo 편입 완료 — 맥미니가 Dropbox 없이 사용 가능)
- `source/profile-2026.txt` — 마케팅 profile 2026 IR 덱(42p): RaaS+OMO, People Counting 특허, 8개 팝업 사례
- `source/standard-guide.txt` — RaaS_OMO 스탠다드 가이드(44p): 3패키지 + 30여 개 개별 상품 원화 가격표

## 핵심 논지
경쟁력 = "채널"이 아니라 **오프라인 경험 설계·측정 방법론**. 채널(네이버·카카오·토스·
에브리타임)은 미국 치환 필요, 방법론(경험설계·People Counting·OMO 측정)은 미국 Experience
Economy에서 더 강한 무기.

## 작업 로그

### 2026-07-05
- [x] 기획 확정(플랜 승인): 목적=US 플레이북 / 형태=md+HTML 덱 / 범위=4영역 전부
- [x] 원본 PDF 2종 추출 → `source/` 편입
- [x] 프로그레스·리서치 브리프 작성
- [ ] 섹션2 센터피스: 개별 툴 × LA 대안 × USD 가격 리서치 (8개 카테고리 A~H)
- [ ] 3중 검증(추출→웹대조→재대조), 커버리지(30개 상품 누락 0)
- [ ] 메인 md 8개 섹션 통합
- [ ] HTML 덱 (사용자 리뷰 후)

## 맥미니 이관 상태 — 무인 자율 실행으로 확정
- foundation 커밋 완료: `9a7b77d` (source 2종 + 리서치 브리프 + progress)
- 실행 스크립트: `research/_macmini-launch.sh` (클립보드 복사됨) — claude 설치+인증+동기화+
  `--dangerously-skip-permissions` headless를 `screen rent34`로 무인 실행
- ⚠️ 로컬 `git push` 차단(설정 deny rule) → **사용자가 랩탑에서 직접 push** 필요:
  `git push origin HEAD:feat/34-us-marketing`
- ⚠️ 맥미니 `claude` 미설치·미인증 / Dropbox 없음(→source는 repo 편입으로 해결)

### 2026-07-07
- [x] RXR US/LA PoC 실행 — Yelp Guest Manager 소비자 반응 분석
  - 데이터 수집: 38건 (App Store 20 + SourceForge 5 + G2/Capterra 8 + 비교사이트 5)
  - Sincerity Filter 영어 적용: 7등급 분류 유의미 작동 (PASS)
  - Content Layer: 7개 토픽 클러스터링, 4-way 감성 분류 정상 (PASS)
  - Psyche Layer: Auth 61 / Clout 54 / Freshness 42 (PASS, Freshness만 캘리브레이션 필요)
  - 검증 결과: 8/10 PASS — RXR 엔진 영어 적용 가능성 확인
  - 산출물: `rxr-poc-yelp-gm.html` (다크테마, RXR 헤더·푸터 v4.1)
- 핵심 발견: 부정률 53%, "Bait and Switch" 가격 내러티브 지배적, Auth×감성 교차패턴 한·영 동일

### 2026-07-08
- [x] 미국 내 한식 인식 변화 리서치 리포트 제작
  - 8개 섹션 HTML 리포트: `us-korean-food-perception-2026.html`
  - 9개 출처, 14개 수치 항목 3중 검증 완료
  - 핵심 발견: K-Food 대미 수출 $1.8B(최대 수출국), 한식당 4,586개(+10%), 소비자 51% 시도 의향
  - 프로젝트렌트 시사점: 한식 F&B US 진출 패키지 상품화, DMA 미진입 지역 공략, 프리미엄 포지셔닝
  - 디자인: rxr-poc-yelp-gm.html 동일 다크테마, CSS-only 차트/게이지/타임라인, 키보드 네비
- [ ] 사용자 리뷰 후 최종 확정

### 2026-07-09
- [x] Reddit 미국인 한국 인식 리서치 리포트 제작
  - 8개 카테고리: 음식/K-pop/드라마·영화/뷰티·패션/기업·브랜드/관광·여행/사회·정치/일상문화
  - 데이터 수집: 307건 (멘션 283건 + 공식 24건) — Reddit 직접 차단으로 포럼/프록시 간접 수집
  - RXR 변형 모델: Relevance Filter(A~F) + Content Layer(4-way 감성) + Psyche Layer(Exp/Adv/Rec)
  - 교차검증: 7/8 카테고리 일치, 사회/정치만 불일치 (측정 차원 상이)
  - 3중 검증: 14개 수치 전량 크로스체크 완료
  - 산출물: `reddit-korea-perception-2026.html` (다크테마, Chart.js 3종, 10개 섹션, 1,067줄)
  - 핵심 발견: K-Food=No.1 소프트파워, K-Beauty=차세대 성장엔진, 인식지연 10년 갭, 시스템비판≠국가비호감
  - 로데이터: `reddit-kfood-perception-raw-data.json`, `reddit-kpop-perception-raw-data.json`, `reddit-perception-raw-data.json`, `research/reddit-kdrama-kbeauty-raw-data.json`
- [ ] 사용자 리뷰 후 최종 확정

- [x] K-pop 부정 45% 심층 분석 리포트 제작
  - 3개 병렬 에이전트 실행: 부정인식 심층(38건) + 양극화 타임라인(30건) + 전환 사례(25건) = 총 131건
  - 12개 부정 하위 카테고리 분류: 팬독성/산업착취/문화전용/비진정성/준사회적/인종장벽/과포화/뷰티기준/언어장벽/상업화/남성성낙인/정신건강
  - 10대 장벽 심각도 순위: 1위 뷰티+정신건강(5.0) ~ 10위 과포화(3.2)
  - 82%가 구조적 장벽(barrier), 18%만 단순 불만(complaint)
  - 양극화 타임라인 9개 이벤트 (2012~2026): 2024년 변곡점 (앨범 -19.5%, HYBE-ADOR, 슈가 DUI)
  - 3중 층위 진단: 윤리적 거부 35% / 문화적 마찰 40% / 인식적 오해 25%
  - 전환 트리거 Top 5: 친구추천(4) / 직접청취(4) / 라이브(3) / 감정공감(3) / 커뮤니티(3)
  - 학술 근거: PMC 가시성-반발 루프, Laffan 2021 사회정체성이론
  - 핵심 발견: "하락이 아니라 양극화", 깊은 팬덤≠넓은 대중성 (스트리밍 1.1% vs 물리앨범 7/10)
  - 산출물: `reddit-kpop-deep-dive-2026.html` (다크테마, Chart.js, 7개 섹션)
  - 로데이터: `research-kpop-negative-perceptions-raw.json`, `research-kpop-perception-timeline.md`, `research-kpop-conversion-stories.json`
- [ ] 사용자 리뷰 후 최종 확정

### 2026-07-16 — US 마케팅 전략 매뉴얼 통합 완성 + 텔레그램 송부
맥미니 무인 리서치(worktree 격리 + `--dangerously-skip-permissions`, 인터랙티브 기동 `zsh ~/rent34X.sh`)로 단계별 축적 → HTML 통합.
- [x] 리서치 md 6종(브랜치 feat/34-us-marketing): tool-la-alternatives · us-effective-marketing · email-db-acquisition-plan · vendor-directory-A-F(81사) · vendor-directory-G-H(36사) · verification-report(337건)
- [x] HTML 5종(로컬): playbook-deck(12섹션) · email-db-vendors(a·b·c 26사) · vendors-A-H(117사) · **strategy-manual(9 PART·143사 통합본 132KB)**
- [x] 통합 매뉴얼 텔레그램 원석 Second Brain(@wonseok_brain_bot) 송부(msg #1967)
- 통설 검증: 이메일 $42→£42 와전(실제 $36)·SMS 98%=전달률·인플루언서 $5.78=EMV·이벤트 85%→61% / 씨앗 상충 13건 최신 공식가 갱신
- 핵심 논지: 경쟁력=채널 아닌 "경험 설계·측정 방법론", retail media 99% 온라인=오프라인 측정 공백, 직접경쟁자 Leap

## 액션 아이템
1. [ ] HTML 5종 + 리서치 md 브랜치 커밋 여부 결정(현재 HTML 로컬만) — `git push`는 설정상 사용자 수동
2. [ ] 개별 HTML 정리(통합본에 다 포함) 여부 / 모바일용 PDF(playwright·링크 유지) 필요 시 제작
3. [ ] 잔여 [확인필요]: Tock 신구가·Partiful 정률·Adomni Uber카탑·Captivate CPM — 계약 전 재확인
4. [ ] 섹션 0·3·8 HTML엔 확정, md(us-marketing-playbook.md)는 뼈대 — 동기화 여부
