# CEO Daily Dashboard — Progress

## Overview
1인용 경영 대시보드. 5개 소스(Gmail, Calendar, POS, 프로젝트, 근태)를 한 화면에 모아 30초 의사결정.

## Current Status: Phase 1 MVP Complete + Obsidian Redesign

### Completed

#### Phase 0: 기획 (Done)
- [x] PRD.md — 요구사항 정의서 (의사결정 맵 D1~D5)
- [x] DESIGN.md — 디자인 시스템 정의
- [x] CLAUDE.md — 프로젝트 컨텍스트
- [x] 엑셀 템플릿 설계 (정기업무, POS)

#### Phase 1: MVP (Done)
- [x] HTML+CSS+JS 단일 파일 대시보드
- [x] Panel A: 긴급 액션 (미회신 메일 + 정기업무 D-day)
- [x] Panel B: 오늘/금주 일정 (타임라인)
- [x] Panel C: 매장 현황 (매출 테이블 + KPI + 스파크라인)
- [x] Panel D: 프로젝트 현황 (진행률/지출률 이중 바)
- [x] Panel E: 근태 관리 (초과근무 게이지 + 연차 바)
- [x] Gmail/Calendar API 연동 (GWS CLI → refresh-data.sh)
- [x] 엑셀 업로드 + 자동 파싱 (컬럼명 기반 매핑, SheetJS)
- [x] 신호등 판단 로직 (메일 48h/24h, D-day, 매출 ±15%/30%)

#### Phase 1.5: Obsidian Redesign (Done — 2026-04-19)
- [x] Claude Design에서 Obsidian 목업 제작
- [x] OBSIDIAN_GUIDE.md 디자인 가이드 생성
- [x] 전체 UI Obsidian Dark 테마 적용
  - 1920×1080 고정 캔버스 + auto-scale
  - Top bar (브랜드 로고, 동기화 상태, Refresh/Upload 버튼)
  - Surface 스케일 5단계 (--s0~--s4)
  - Geist + Geist Mono 폰트 (Google Fonts)
  - 그림자 제거 → 1px border only
  - Traffic light dot에 glow ring
  - 패널 헤더 태그 시스템 (A·D1, B·D2 등)
- [x] Panel A: u-row 그리드 + sect 섹션 라벨
- [x] Panel B: 주간 스트립(요일 셀) + 타임라인 레일 (past/now/future)
- [x] Panel C: KPI 카드 3개 + compact 테이블 + issues 그리드
- [x] Panel D: 이중 프로그레스 바 + legend + discuss 섹션
- [x] Panel E: 4열 가로 배치 (초과근무/인건비/연차/근무시간)
- [x] Upload → 모달 오버레이로 변경
- [x] 키보드 단축키 (R=Refresh, U=Upload, Esc=닫기)
- [x] file:// 프로토콜 지원 (인라인 데이터 임베드 폴백)
- [x] 실제 Gmail 데이터 연동 확인 (Brand24, 프로젝트렌트, SKT 등)

---

### Next: Phase 2 — 데이터 고도화

- [ ] 프로젝트 현황 엑셀 템플릿 + 파싱 스크립트
- [ ] 근태 엑셀 템플릿 + 파싱 스크립트
- [ ] POS 매출 전주비/전월비 자동 계산 (다중 날짜 데이터)
- [ ] 매장별 월 목표 설정 UI
- [ ] 데이터 갱신 시각 정확도 개선

### Phase 3 — 인터랙션 + 배포

- [ ] 반응형 레이아웃 (모바일/태블릿)
- [ ] 패널 접기/펼치기
- [ ] 메일 회신 완료 수동 토글
- [ ] 승인 대기 수동 입력 섹션
- [ ] 알림 커스터마이징 (임계값 조정)
- [ ] Vercel/Netlify 퍼블리싱
- [ ] 자동 데이터 갱신 (cron or GitHub Actions)

### Phase 4 — 고급 기능

- [ ] 매출 트렌드 차트 (일별/주별/월별)
- [ ] 프로젝트 간트 차트
- [ ] 알림 시스템 (Telegram/Slack 연동)
- [ ] 다중 사용자 뷰 (매장 매니저용 축소 버전)
- [ ] PWA (오프라인 + 홈 화면 추가)

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Frontend | HTML + CSS + Vanilla JS (단일 파일) |
| Design | Obsidian Dark (1920×1080, Geist, violet accent) |
| Data parse | Python (엑셀→JSON), SheetJS (브라우저 내 파싱) |
| API | GWS CLI (Gmail, Google Calendar) |
| Hosting | Local → Vercel (planned) |

## Key Files

```
16-ceo-dashboard/
├── index.html              ← 대시보드 (HTML+CSS+JS 단일 파일)
├── PRD.md                  ← 요구사항
├── DESIGN.md               ← 디자인 시스템
├── CLAUDE.md               ← 프로젝트 컨텍스트
├── PROGRESS.md             ← 이 파일
├── vercel.json             ← 배포 설정
├── data/                   ← JSON 데이터
├── scripts/                ← 데이터 처리 스크립트
└── templates/              ← 엑셀 템플릿
```

## Design Reference

- Mockup: `/tmp/ceo-dashboard/project/CEO Dashboard Mockup - Obsidian.html`
- Guide: `/tmp/ceo-dashboard/project/OBSIDIAN_GUIDE.md`
- Claude Design 번들에서 export (2026-04-19)

## Notes

- `file://`에서도 동작하도록 JSON 데이터를 HTML에 인라인 임베드 (EMBEDDED_DATA)
- HTTP 서버 사용 시 `data/*.json` fetch가 우선, localStorage 두 번째, 임베드 세 번째
- 실제 이메일 데이터는 `refresh-data.sh` 실행 시 갱신 → 임베드 데이터는 수동 업데이트 필요
- 퍼블리싱 시 Vercel에 `data/` 디렉토리 포함하거나 API route로 대체 필요
