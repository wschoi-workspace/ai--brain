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
- [x] 섹션2 센터피스: 개별 툴 × LA 대안 × USD 가격 리서치 (8개 카테고리 A~H) — 맥미니 무인 실행
- [x] 3중 검증(추출→웹대조→재대조), 커버리지(30개 상품 누락 0) — 비공개 가격은 RFQ+[추정] 병기
- [x] 메인 md 섹션 4~7 초안 + 0~3·8 뼈대 (`us-marketing-playbook.md`)
- [ ] 섹션 0~3·8 확정 (사용자 취향판단)
- [ ] HTML 덱 (사용자 리뷰 후)

#### 2026-07-05 맥미니 무인 실행 로그
- `research/tool-la-alternatives.md` 작성 완료: 8개 카테고리 × 30여 상품 전수, 병렬 리서치 에이전트 10기 투입
- `us-marketing-playbook.md` 작성: 섹션4(시장: PQ Media US $64.4B/2025, in-store retail media 공백) ·
  섹션5(규제: TCPA·CAN-SPAM·CCPA·LAMC 28.04·FTC 2024 fake review rule) ·
  섹션6(팝업 CRM 스택 + Cultural Engagement Score 공백 확인) · 섹션7(리포지셔닝 5단 사다리) 초안
- 핵심 발견: ① 침투 바이럴·구매유도 체험단은 FTC 규제로 이식 불가(★1) ② 토스류 리워드 푸시는 미국에 대응물 부재
  ③ "단기 팝업용 턴키 실측 측정"은 미국 빈 포지션(Placer.ai=추정치, Dor 등=상설매장용) ④ 직접 경쟁자는 Leap(RaaS, 흑자)
- ⚠️ 실행 중 이슈: 리서치 도중 맥미니의 다른 자동화가 repo 브랜치를 main으로 전환 → 산출물은 untracked라 보존,
  `git worktree`로 `feat/34-us-marketing`에 커밋하여 해결. **무인 리서치와 arisa류 자동화가 같은 워킹트리를 공유하는 구조는 위험 — 이후 무인 작업은 전용 worktree에서 실행 권장.**

## 맥미니 이관 상태
- repo `~/do-better-workspace` 존재, `screen`·`node` 있음, GitHub remote 공유
- ✅ claude CLI 설치·인증 완료, 무인 리서치 브리프 실행 성공 (2026-07-05)
- 경로 확정: `/Users/server-mini/do-better-workspace`

## 액션 아이템
- [ ] (사용자) 센터피스 표 리뷰 → 섹션 0~3·8 방향 확정 → HTML 덱 지시
- [ ] RFQ 견적 요청 리스트 발송 검토: Secret Media Network(Fever)·The Infatuation·LA Times Studios·Intersection(LA Metro)·JCDecaux(LAX)·Captivate·Attentive·Placer.ai (리드타임 2~4주)
- [ ] [확인필요] 태그 항목 재검증: Business Wire 내셔널 단가($760/775), Tock·Yelp GM 신구 가격, Partiful 티켓 수수료, Storefront 인수 시점, BrandBox 종료 여부
- [ ] 환율 기준 확정(문서는 ₩1,400/USD [추정] 사용)
- [ ] 무인 실행 인프라: 브랜치 전환 충돌 방지(전용 worktree 운용) 결정
