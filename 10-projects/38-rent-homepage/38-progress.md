# 38 — PROJECT RENT 홈페이지 신규 제작

## 개요
- Genspark 제작 홈페이지(sandbox preview)를 워크스페이스로 이식, R스타일가이드(`00-system/04-design/project-rent-design-guide.md`)로 전면 재스타일링
- 콘텐츠·섹션 구성은 원본 유지, 디자인만 교체
- 원본: `_source/original.html` (genspark.genspark.site sandbox 651d5430)

## 파일 구조
```
38-rent-homepage/
├── index.html          # 단일 파일 (CSS/JS 인라인)
├── assets/             # hero.mp4 (57MB) + 케이스 이미지 37장 (로컬 저장)
└── _source/
    ├── original.html   # 원본 백업
    └── verify.py       # Playwright 검증 스크립트 (evaluate 전용, PNG 없음)
```

## 2026-07-20 — 최초 제작 완료

### 디자인 시스템 적용
- CSS Variables: 가이드 선언부 그대로 (`--bg #1A1A1A`, `--accent #6C5CE7`, `--fg #F5F0EB` 등 10-Color)
- Pretendard Variable CDN + 3-Weight (200/300/500), H1 72px/200 · H2 44px/500 · Body 14px/300 · Label 11px/0.25em
- 12-column grid 그대로 구현: `repeat(12,1fr)`, gap 14px, max-width 1440px, 섹션 `.sec { padding: 100px 120px 120px }`
- 포인트 컬러 극소량: 섹션당 청보라 1곳 (Hero Number 154%, $1,840억, Stats 300+, Perf 숫자, story 첫 카드 border, CTA/submit)
- Sharp 엣지 (라운드 제거), 순수 #000 미사용, 스크롤 리빌 + motion tokens + prefers-reduced-motion

### 섹션 (10개)
1. 고정 헤더 (로고/GNB/KO·EN 토글/문의 CTA/햄버거) 2. Hero (영상 배경) 3. Highlight 슬라이더 3장 4. Stats KPI 4장 (카운트업) 5. Market 6. Services 7종 (4+3 행) 7. Performance 로테이션 (4,539%/99%/88%) 8. Archive 필터+케이스 7+More 9. About 타임라인+스토리 10. Partners 마퀴 + Contact 폼 + 푸터(`by Project Rent`)

### 사용자 결정 반영
- Contact 폼 제출 → `mailto:projectrent43@gmail.com` (제목/본문 자동 조립) + Toast
- Admin 패널 제거 (원본의 비밀번호 하드코딩·Table API 삭제)
- KO/EN 토글: `data-i18n`/`data-i18n-html` + 딕셔너리 + localStorage

### 검증 결과 (verify.py, 전 항목 통과)
- 콘솔 에러 0 / 12-col grid 확인 / accent·bg 토큰 일치 / Pretendard Variable 적용
- KO↔EN 전환 (hero/case/market/partners/form 전부 반영, localStorage 저장)
- Highlight 슬라이더 (화살표/점/키보드/자동), Archive 필터 (beauty→1개), Performance 로테이션, KPI 카운트업
- 반응형: ≤1200px 패딩 60px, ≤768px 햄버거 표시·GNB 숨김
- 콘텐츠 원본 대조: 수치(154%·$1,840억·$3,120억·17.6%·25%·$7,090억·22조·259조·4.3조·300+·40.2·98%·23.7%·4,539%·99%·88%·72.1%·11,470명·특허 10-2545502)·케이스 7종·타임라인 2018→2026 모두 1:1 이식

### 원본 대비 의도적 변경
- Admin 섹션/패널 전체 제거, 폼 백엔드(Table API) → mailto
- 원본 딕셔너리에만 있고 DOM에 없던 timeline2019는 원본 DOM 기준(6개 항목)으로 유지
- 푸터 저작권 연도 2025 → 2026, `by Project Rent` 크레딧 추가
- Highlight 3번 슬라이드 로고 이미지(simple-icons CDN) → 텍스트 카드로 대체 (가이드 톤 유지)

## 2026-07-20 (2차) — 영상 압축 + 타이포 정리
- hero.mp4 압축: 57MB → 6.1MB (imageio-ffmpeg 정적 바이너리, libx264 CRF28/preset slow/오디오 제거/faststart). 원본은 `_source/hero-original.mp4` 보관
- 히어로 타이틀 가이드 정합: weight 200 · line-height 1.0 · letter-spacing -0.04em. 크기는 72px 유지 — 가이드 H1 108px는 3줄 카피(KO 15.75em)가 컨테이너 1200px를 초과해 줄바꿈 깨짐 → 가이드 반응형 스케일(72px)이 상한
- 재검증: 압축 영상 정상 재생(1920×1080), KO/EN 히어로 오버플로 없음, 콘솔 에러 0

## 2026-07-20 (3차) — 원본 레퍼런스 레이아웃 재현 (사용자 확인: Genspark 원본 레이아웃 + R토큰)
- 방향: 원본 홈페이지의 레이아웃 디테일을 동일하게 재현, 컬러·폰트는 R가이드 토큰(#1A1A1A/#6C5CE7/#F5F0EB, Pretendard 최대 500) 유지. **서비스 7종 카드 파트만 신규 디자인 유지**
- Highlight/Performance/Contact: 풀블리드 accent(#6C5CE7) 배경 밴드 복원 — 풀스크린 중앙정렬 슬라이더(원형 네비 56px, 필 도트), 120px 대형 숫자, 다크 폼 카드
- 라운드 복원: 카드 16px, 스탯카드 24px, 배지/랭스위치 20px, 버튼·입력 6~8px, 도트 원형
- 섹션 헤더: 매거진 sec-head → 원본 badge(필) + section-title(56px) 패턴
- Stats: 헤더 제거, 숫자(56px accent)→라벨 순서, 라운드 카드 / Market: 숫자 상단 accent 32px 카드
- Archive: 필터 필 버튼(active accent bg), 이미지 240px 고정, hover -8px / About: 타임라인 연도 24px accent, 스토리 카드 전부 accent 보더 40px 패딩
- 헤더: 로고 "PROJECT RENT." 20px, GNB 15px, IR Deck 아웃라인 버튼 복원, 히어로 볼드(500)+바운스 스크롤 인디케이터
- 검증: accent 밴드 3곳 적용·라운드·슬라이더/필터/EN 전환·모바일 1col 모두 통과, 콘솔 에러 0

## 2026-07-21 (4차) — 디테일 폴리싱 (사용자 확인 완료 "좋아 굿")
- 서비스 카드: 타이틀 Pretendard ExtraBold(800), 상하 간격 축소 (타이틀 마진 10/12px, 피처 패딩 10px)
- 히어로 타이틀: max-width 900→1200px + word-break keep-all → 3줄 고정 (1024~1440 검증)
- Archive 카드: 이미지 240→280px, 텍스트 블록 여백 50% 축소 (패딩 10/24/12px, 타이틀 마진 3/2px) → 카드 379px, 이미지:텍스트 ≈ 7:3

## 2026-07-21 — Cloudflare Pages 배포 완료
- 프로젝트: `rent-homepage` / 계정: ws.choi@project-rent.com (wrangler OAuth)
- **URL: https://rent-homepage.pages.dev** (200 확인, 영상 포함 11MB, 39파일)
- 배포 명령: `_deploy/`(index.html+assets만) 구성 → `npx wrangler pages deploy _deploy --project-name=rent-homepage --branch=main`
- 재배포 시 동일 명령 반복 (index.html 수정 → _deploy 복사 → deploy)

## 2026-07-21 (2차) — 문의 폼 아리사 통합
- 기존 문제: mailto 방식(projectrent43@gmail.com) — 방문자 메일 앱 의존, 서버 수집 없음
- 해결: Pages Function `functions/api/inquiry.js` — 폼 POST 수신 → 아리사 매니저 봇(DAILY_REPORT_MANAGER_BOT) 텔레그램으로 대표에게 즉시 알림
- 시크릿: TELEGRAM_TOKEN/TELEGRAM_CHAT_ID (wrangler pages secret, .env의 매니저 봇 값)
- 프론트: fetch POST /api/inquiry → 성공 토스트 "문의가 접수되었습니다" / 실패 시 mailto 폴백
- E2E 테스트: 배포 URL에서 POST → {"ok":true}, 텔레그램 수신 확인
- ⚠️ 재배포 시 functions/ 디렉토리가 프로젝트 루트에 있어야 함 (cwd=38-rent-homepage에서 deploy 실행)

## 2026-07-21 (3차) — 문의 구글시트 취합 연결 완료
- 취합 시트: "PROJECT RENT 홈페이지 문의 취합" (ID 1zdGWTmBmMCYKOvmU7IqPgttgUcZwYpf-oGm-wgjuzHM, 문의내역 탭 7열)
- Apps Script 웹훅 배포(대표 계정, `_source/inquiry-sheet-webhook.gs`, 공유 시크릿 검증) → Function이 텔레그램 + 시트 동시 기록
- 시크릿: SHEET_WEBHOOK_URL / SHEET_SECRET (wrangler pages secret)
- ⚠️ 교훈: Pages Function에서 waitUntil 백그라운드 fetch는 유실됨 → await 방식으로 전환 (응답 {ok, sheet})
- E2E: 폼 POST → 텔레그램 수신 + 시트 행 기록 확인 (테스트 행 3개는 시트에서 수동 삭제 가능)

## 2026-07-21 (4차) — 커스텀 도메인 www.project-rent.com 연결 완료
- 경위: project-rent.com NS가 기존 홈페이지 업체(hostcocoa.com)에 있어 가비아 설정 무효 → **네임서버를 가비아(ns/ns1/ns2.gabia.co.kr)로 전환** (DNS 주도권 확보)
- 가비아 존 구성(12 레코드): 구글 MX 6 + SPF TXT(`v=spf1 include:_spf.google.com ip4:52.79.92.223 ~all`, 구글 include 신규 보강) + site-verification TXT + **www CNAME → rent-homepage.pages.dev.**(가비아는 값 끝에 점 필수) + apex A 4개(3.168.178.16/22/39/44, 기존 루트 사이트 유지)
- Cloudflare Pages 커스텀 도메인 API 등록 → status active, SSL 발급 완료, https://www.project-rent.com 200 확인 (--resolve 검증)
- 로컬 ISP 캐시만 옛 IP 잔존 — TTL 만료 후 자연 해소
- Cloudflare API는 wrangler OAuth 토큰(~/Library/Preferences/.wrangler/config/default.toml) 재사용

## 2026-07-21 (5차) — SEO 기반 작업
- sitemap.xml(다운로드 파일) + robots.txt(Yeti 허용, Sitemap 명시) 배포 루트에 배치 → 200 확인
- index.html SEO 메타 보강: canonical, Open Graph 7종, twitter:card, JSON-LD Organization 스키마
- 남은 등록: Google Search Console(DNS TXT 기존 토큰 활용 가능) + 네이버 서치어드바이저(소유확인 메타 필요)

## 2026-07-21 (6차) — 검색엔진 등록 완료
- **네이버 서치어드바이저**: HTML 메타(naver-site-verification=010e37...) index.html 삽입·배포 → 소유확인 통과. 사이트맵 제출+수집 요청은 사용자 진행
- **구글 서치콘솔**: 도메인 속성 project-rent.com 등록. 이슈 2건 해결 — ①기존 google-site-verification TXT가 SPF 추가 때 덮어써져 소실 → 새 토큰(pXvXVc...) TXT 추가 ②가비아 붙여넣기 시 토큰 중간 공백 유입 → pbcopy로 클립보드 직접 주입해 해결. 소유확인 통과, URL 색인 등록 확인, 색인 재요청+사이트맵 제출 진행
- 최종 TXT 2개 공존 확인: google-site-verification + SPF(v=spf1 include:_spf.google.com ip4:52.79.92.223 ~all), 중복 없음
- ⚠️ 교훈: 가비아 TXT는 "수정"하면 기존 레코드 덮어씀 — 반드시 [+레코드 추가]. 긴 값은 pbcopy로 전달해 공백 유입 방지

## 남은 것 / 다음 단계
- [ ] 루트(project-rent.com)도 새 사이트로 넘길지 결정 — 넘기면 apex A 4개 삭제 + 가비아 포워딩(→ www)
- [ ] 시트의 [테스트] 행 정리 (선택)
- [ ] Instagram/LinkedIn/YouTube 푸터 링크 실제 URL 연결
- [ ] IR Deck 버튼: 원본에 있었으나 링크 대상 없어 이번 버전에서 제외 — 필요 시 추가
