# 28-ai-education-ax Progress

## 폴더 구조
```
28-ai-education-ax/
├── 28-progress.md               ← 이 파일 (전체 프로그레스)
├── ax-education-proposal.html   ← 제안서 풀버전
├── ax-education-slides.html     ← 제안서 슬라이드
├── ax-education-slides.pdf      ← 제안서 PDF
├── 01-demos/                    ← 라이브 데모 시나리오 + 슬라이드 (3종)
├── 02-guides/                   ← 실습 가이드, 바이브코딩 매뉴얼
├── 03-samples/                  ← 교육용 샘플 데이터 (가상화)
├── 04-references/               ← AX 에세이 시리즈 (V1 4개 + V2 4개)
│   └── source/                  ← 원본 GPT 대화 docx 2개
├── 05-lectures/                 ← 사고전환 강의 슬라이드 (V1 26장 + V2 30장)
└── hold/                        ← 슬라이드 이미지 자산
```

---

## 교육 철학 (핵심 프레임)

1. **"AI가 대단하다" ❌ → "이게 이렇게 쉽다" ✅**
2. **패턴 통일**: ① 파일 넣고 ② 물어보고 ③ 받는다
3. **감정 곡선**: 속도충격(매출) → 리스크공포(HR) → 후회+행동전환(관공서)
4. **소상공인 포커스**: "중요하지 않은데 어렵고 은근히 많은 잡일" 줄여주기
5. **마무리는 행동**: "오늘 밤 딱 하나만" + QR코드
6. **케이스 부족 → 뒤집기**: "지금 시작하면 5%가 된다"

**배경 논의**: GPT 대화("일하는 미래") — 패턴 민주화, 오케스트레이터, 주니어 딜레마, 경영진 설득, Anthropic Austin Lau 사례 → `04-references/` 에 원본 보관

---

## 2026-05-20

### 라이브 데모 + 슬라이드 3종 완성

**강사용 시나리오 (스크롤형) 3종** → `01-demos/`
- 매출분석편 — 로스팅하우스(뉴믹스 기반) 9,900만, 외국인 87%, 객단가 2배
- 인사관리편 — 한빛디자인A+소울크리에이티브B(실데이터 기반) 14명, 리스크캘린더
- 관공서 서류편 — 신청서 + 지원사업 조회 + 사업계획서 + 공공양식(희망드림)

**16:9 슬라이드 3종** → `01-demos/`
- 매출분석 15장 / 인사관리 15장 / 관공서 16장
- 디자인: 청보라+블랙+화이트 3색 / N키 강사노트 / F키 풀스크린
- 전체 비식별화 완료 (회사명·직원명 가상)

**비식별화 매핑**:
- 뉴믹스커피 → 로스팅하우스 / 홍길동 → 김민수
- 프로젝트렌트R → 한빛디자인A / 필라멘트앤코F → 소울크리에이티브B
- 직원: 이수진, 박현우, 김하늘, 정유진, 한소희, 오서연, 최준호

### 제안서 제작 완료

**산출물 3종**:
| 파일 | 용도 | 비고 |
|------|------|------|
| `ax-education-proposal.html` | 풀버전 제안서 (웹/인쇄) | 8섹션, R스타일가이드 적용 |
| `ax-education-slides.html` | 슬라이드 축약본 (프레젠테이션) | 9장, 다크 배경, 키보드 네비 |
| `ax-education-slides.pdf` | PDF 출력본 | A4 가로, 텍스트 스케일업 |

**제안서 구조** (풀버전):
1. 왜 지금 AX인가 — 사례(Anthropic/Klarna/Shopify/BCG), 속도 격차, 실험 횟수 경쟁
2. 교육 목표 — 사고전환 / 실무역량 / AX 확산 조직
3. 왜 3단계인가 — Mindset → Capability → Execution (순서 바뀌면 실패하는 이유)
4. 프로그램 구조 상세 — 타임라인 형태 3단계 + 4회차 커리큘럼
5. 운영 방식 — Option A 1박2일 vs Option B 4회 분할(권장)
6. 4가지 변화 — 대기시간 제거, KPI 전환, 운영구조 전환, 지금 시작
7. 기대 효과 — 조직/실무자/장기/확장 4축
8. 예상 비용 — 단계별 단가 + 시뮬레이션

**3단계 핵심 로직** (가장 중요한 제안 포인트):
- 1단계: 자세 전환 — "왜 바뀌어야 하는가" 공감대
- 2단계: 부서별 동의 + 효용감 → 부서당 AX 리더 1명 양성
- 3단계: 높아진 이해도로 자기 부서 데이터 탐색 → 문제 도출 → 개발자와 해결 개념 설계

**비용 구조**:
- 1단계: 일반교육 150만/시간 | C-Level 개념+실습 50만/명 (4시간)
- 2단계: 2회 80만/명 | 4회(권장) 150만/명 (8~10명 기준)
- 3단계: 35만/명/회 (5~8명 미만)
- 시뮬레이션: 1단계(150만) + 2단계 2회×8명(640만) + 3단계 1회×8명(280만) = **1,070만원**

**브랜딩**: 클로징 슬라이드 RXR 표기

---

---

## 2026-05-21

### 슬라이드 그리드 시스템 적용 리팩토링

**배경**: 기존 슬라이드가 `1fr 1fr 1fr` 임의 분할이라 콘텐츠 양/컴포넌트 수 변화 시 구조 붕괴. grid-system.md 작성 후 엄격 적용.

**디자인 시스템 신설**:
- `00-system/04-design/grid-system.md` 생성 (280줄) — AI용 공간 행동 규칙
- 기존 `project-rent-design-guide.md`(브랜드 스타일링)와 역할 분리
- 핵심: 12-column grid, 8px spacing, box logic, adaptive layout rule

**슬라이드 변경** (`ax-education-slides.html`):
- CSS Grid `repeat(12, 1fr)` + column span 방식으로 전면 재구축
- 모든 스페이싱 8px 배수, 거터 20px, 마진 56px 통일
- 카드 radius 12px, padding 24px (가이드 정합)

**레이아웃 매핑**:
| 슬라이드 | Column Span | 내용 |
|---------|-------------|------|
| S1 커버 | 12col center | 타이틀 + 서브카피 |
| S2 Why AX | 4+4+4 | 문제/본질/결론 3카드 |
| S3 Why 3 Stages | 4+4+4 + 12col chain | 단계별 카드 + 화살표 플로우 |
| S4 Program | 4+4+4 | AX개론/워크샵/확산 |
| S5 Stage 1 | 6+6 | 01~03 / 04~06 상세 |
| S6 Stage 2 | 3+3+3+3 | Session 1~4 |
| S7 Stage 3 | 6+6 | 스텝 4개 / Why This Works |
| S8 Cost | 3+3+3+3 + 12col table | KPI 카드 + 가격표 |
| S9 Closing | 12col center | 클로징 메시지 |

**캡처 완료**: `ax-education-slide-1~9.png` (1920x1080)

---

### 다음 액션 (2026-05-21 시점)

**제안서**
- [ ] 클라이언트 피드백 반영
- [ ] 필요 시 제안서 풀버전 PDF 출력
- [ ] 업종별 사례·인원 규모별 시뮬레이션 커스터마이징

**데모·교육 콘텐츠**
- [ ] 마무리 슬라이드 ("오늘 밤 딱 하나만" + QR + 다음 스텝)
- [ ] 3개 데모 → 30분 통합 플로우
- [ ] 교육용 가상 사업자등록증 이미지 → `03-samples/`
- [ ] 데모 리허설 + 시간 측정
- [ ] 관공서 지원사업 목록 2026년 유효성 확인
- [ ] 바이브코딩 실습 트랙 설계 (데모 후 핸즈온) → `02-guides/`
- [x] GPT 대화 원본("일하는 미래") `04-references/source/`에 보관

---

## 2026-06-07

### AX 사고전환 에세이 시리즈 — V1 + V2 완성

**출발점**: GPT와의 AX 대담(ChatGPT_AX대담.docx)에서 "해상도의 차이", "판단의 위기", "비즈니스 전환", "별자리 설계자" 4가지 주제를 도출.

**V1 — 조직 혁신 관점 (4챕터)**

| Ch | 파일 | 제목 | 관점 |
|---|---|---|---|
| 1 | `ax-chapter01-resolution.html` | 같은 세계를 보고 있는데, 왜 다른 이야기를 하는 걸까 | 조직 커뮤니케이션 |
| 2 | `ax-chapter02-judgment.html` | 다 괜찮아 보이는 시대, 누가 판단하는가 | 조직 판단 체계 |
| 3 | `ax-chapter03-transition.html` | 만드는 조직에서 해석하는 조직으로 | 조직 전환 |
| 4 | `ax-chapter04-constellation.html` | 별자리 설계자 | 사일로 연결 역할 |

**V2 — AI 불안 개인 + 실무자/관리자 양면 관점 (4챕터, 최종)**

| Ch | 파일 | 제목 | 핵심 전환 |
|---|---|---|---|
| 1 | `ax-chapter01-resolution-V2.html` | 당신이 불안한 진짜 이유 | 불안→해상도 3축(변수·시간·맥락) |
| 2 | `ax-chapter02-judgment-V2.html` | 당신의 실력이 보이지 않는 시대 | 실무자: "왜" 보여줘라 / 관리자: "왜" 물어봐라 |
| 3 | `ax-chapter03-transition-V2.html` | 만드는 사람에서 해석하는 사람으로 | 만드는 가치↓, 해석하는 가치↑ (양면) |
| 4 | `ax-chapter04-attitude-V2.html` | 새로운 일의 자세 | 멈추기(변수)+묻기(시간)+맞추기(맥락) |

**V2 핵심 설계 원칙**:
- 대상: AI에 대해 불안하거나 아직 충격을 인지 못한 사람
- 관점: 개인의 불안에서 시작 → AI 이전의 문제 직시 → AI가 증폭 → 실무자/관리자 양면 행동
- "해상도" 3축(변수·시간·맥락)이 4챕터를 관통하며 진화
- Ch1에서 정의 → Ch2에서 차이가 안 보임 → Ch3에서 가치 전환 → Ch4에서 3습관과 연결

**전문가 인용 (에세이 전체)**:
- Kahneman (System 1/2, 게으른 사고)
- Mollick (Jagged Frontier, 758명 실험)
- Gerlich (666명, 인지 외주화 실증)
- Brynjolfsson (튜링 트랩)
- Christensen (혁신가의 딜레마)
- Levitt (드릴 vs 구멍)
- Hoffman (AI는 증폭기)
- Drucker (지식 노동자 생산성)
- Eric Ries (린 스타트업)

**소스 파일**: `04-references/source/`
- `ChatGPT_AX대담.docx` — 원본 GPT 대화
- `나 GPT_일하는 미래.docx` — GPT 대화 원본 2

### 강의 슬라이드 — V1 + V2 완성

| 버전 | 파일 | 장수 | 관점 |
|---|---|---|---|
| V1 | `05-lectures/ax-mindset-slides.html` | 26장 | 조직 관점, 커뮤니케이션→판단 |
| **V2** | `05-lectures/ax-mindset-slides-V2.html` | **30장** | AI 불안 개인 + 양면 구조 |

**V2 슬라이드 구조** (30장, ~60분):
- Part A (14장): 불안의 정체 → 해상도 3축 → 네비 비유 → 사고 증폭 vs 포기
- Part B (12장): 실력이 안 보이는 시대 → 실무자/관리자 양면 → 한쪽만 바뀌면 안 됨
- Closing (4장): 3습관×3축 → 증폭기 → 양면 CTA → 마무리

**슬라이드 기능**: 키보드(←→Space), N키 강사노트, F키 풀스크린, 터치 스와이프, 프로그레스바

**리서치 리포트**: `30-knowledge/37-claude-code/ai-thinking-resolution-research-2024.html`
- Mollick, Brynjolfsson, Kahneman, Suleyman, Gerlich, Autor, Acemoglu, Nadella, Hoffman 연구 종합

---

### 다음 액션

**에세이**
- [ ] V2 에세이 전체 통독 후 톤/흐름 최종 QA
- [ ] 필요 시 Ch3/Ch4 해상도 설명 추가 보강
- [ ] 에세이 → 카드뉴스 / SNS 콘텐츠 변환

**강의 슬라이드**
- [ ] V2 슬라이드 전체 리허설 + 시간 측정 (목표 55~60분)
- [ ] 슬라이드 캡처 (Playwright)
- [ ] 강사노트 기반 발표 대본 최종 정리

**데모·교육 콘텐츠**
- [ ] V2 사고전환 강의 + 기존 데모 3종 → 통합 교육 플로우 설계
- [ ] 마무리 슬라이드 ("오늘 밤 딱 하나만" + QR)
- [ ] 바이브코딩 실습 트랙 설계

---

## 2026-06-10 — 일일업무보고봇 첨부파일 수신 기능

직원이 텔레그램으로 업무보고 시 **결과물 파일도 함께 제출**할 수 있도록 봇 확장.

### 구현
- **봇 스크립트**: `00-system/02-scripts/daily-report-bot.py` (python-telegram-bot 21.10)
- **수신 시점**: 보고 중 아무 단계에서나 (모든 state에 `filters.PHOTO | filters.Document.ALL` 핸들러)
- **처리 흐름**: 텔레그램 다운로드 → `gws drive +upload`로 "일일업무보고" 폴더 업로드 → 링크 누적
  - 파일명 규칙: `날짜_이름_원본명`
  - 드라이브 폴더 ID: `18JLhq98zVbJps1B-AXQ0xgxWqscIBYbe`
  - 링크 형식: `https://drive.google.com/file/d/{id}/view`
- **출력 연결**:
  - 관리자봇 보고서에 `■ 첨부 산출물` 섹션 + 링크
  - 구글시트 **메타 G열("첨부")**에 `파일명: 링크` 기록 (헤더 추가 완료)

### 의미
- 기존 `output` = 텍스트 설명뿐 → 실물 파일 링크 결합으로 **검증 가능(verifiable)** 보고 실현

### 상태
- 문법 검사 통과 / 드라이브 업로드 단위 테스트 통과 / 봇 재시작 가동 중(PID 40876)
- 커밋 `241eac8` (봇 관련 8파일 일괄)
- ⏳ **남은 것**: 텔레그램 실사용 테스트(직원 `/report` 흐름) — 사용자 직접 진행 예정

### 참고: 알려진 개선 여지 (미반영)
- 봇 토큰·시트ID 하드코딩 → `.env` 이관 권장
- `improvement`(개선포인트) 필드가 수집 단계 없이 항상 빈 값 (instructions엔 STEP 존재)
- 시트 헤더 자동 생성 로직 없음 (수동 세팅 전제)

---

## 2026-06-14 — AX 에세이 V3 (최원석 문체 변환 + 숫자 팩트체크)

### 작업
이림 강의 2026 교육메뉴얼 AX 에세이 4편을 신규 `/문체` 스킬로 V3 변환.
경로: `Dropbox/02-프로젝트렌트RENT/07.AI연습/이림 _강의2026/교육메뉴얼/AX_에세이/`

- **`/문체` 스킬 신설**: 저서 『결국, 오프라인』 문체 DNA 10규칙 추출 → 휴머나이저 특화 스킬(`do-better-workspace/.claude/skills/문체/`). 명시 호출 전용
- **V3 4편 변환**: ch01 resolution / ch02 judgment / ch03 transition / ch04 attitude. 단문 단언 리듬·대조 재정의·구어체→단정조·어휘 격상. HTML/CSS/통계/인용 보존, chapter-label·footer V2→V3

### 숫자 재검증 — 오류 5건 수정 (웹 출처 크로스체크)
| 위치 | 수정 |
|------|------|
| ch03 | BCG 74% "파일럿 실패"→"기업의 74%가 AI 가치 실현·확장 어려움(26%만 실험단계 넘음)" |
| ch01 | "19% 더 틀렸다"→"정답확률 19퍼센트포인트 낮음" (단위) |
| ch01·02 | 몰릭 귀속 정정: 와튼 몰릭 단독→HBS+BCG 공동, 주저자 Dell'Acqua, 758명·43% 정확 |
| ch02 | 영국 코파일럿 "정부 1,000개"→"기업통상부(DBT) 1,000개", "동료 감지못함"→"독립평가서 품질·정확도 하락" |
| ch01·04 | Turing Trap 출처 "(Stanford HAI)"→"Daedalus (2022)" |

- 정확 확인(유지): 43%·758명·666명(Gerlich, Societies 2025), 인용문 3건(Hoffman·Brynjolfsson·Christensen)

### 신규 규칙 확립
숫자·통계 자료는 항상 **출처 크로스체크 + 3중 검증**(추출→웹대조→반영후 재대조). CLAUDE.md 작업규칙 + 메모리(`feedback_number_verification`) 영구 반영.

### 남은 것
- (선택) V2 원본 4편에도 동일 숫자 수정 적용
- (선택) V3 4편 Playwright PDF/PNG 렌더링

---

## 2026-06-20 — AX 직원교육 뉴스레터 (주1회 텔레그램 순차발송)

### 배경
`RXR_ai강의_v1.html`(20파트, 공유 워크스페이스 셋업 전제)을 **공유 인프라 의존분 제거** 후
"각자 자기 Claude Code에서 완결되는 한 개념 + 한 실습"으로 경량 재구성.
직원 대상 뉴스레터로 **주 1회 · 7회차(약 두 달) · 텔레그램** 순차 발송.

### 확정 전제 (사용자)
- 실습환경: 각자 Claude Code(공유 git/CLAUDE.md 셋업 없음) → 로컬 완결 예제만
- 채널: 텔레그램 / 주기: 주1회 7회차 / 범위: 플랜+전체콘텐츠+발송자동화 전부

### 산출물 (`newsletter/`)
- **curriculum.md** — 7회차 매핑(개념·v1근거·실습미션·비유)
- **episodes/** — 텔레그램 본문 8건(ep-00 온보딩 + ep-01~07.md), 상세 HTML 2건(ep-01·02.html, R 다크테마)
- **send-newsletter.py** — 회차 카운터 기반 발송(daily-report-bot 패턴 재사용). `--test/--dry-run/--episode/--status` 지원
- **delivery-status.json** — last_sent_episode 카운터(현재 0, 미시작) / **recipients.json** — 직원 chat_id(현재 빈 배열→매니저 폴백)
- **send-newsletter.sh** + `~/Library/LaunchAgents/com.dobetter.ax-newsletter.plist` — 매주 월 09:00 (plutil OK, **아직 load 안 함**)

### 회차 구성
EP01 왜 까만화면(에이전트 3특성) / EP02 말하듯+확인해줘 / EP03 쪼개기·Plan·/clear /
EP04 CLAUDE.md / EP05 첫 스킬 / EP06 HTML 비주얼 / EP07 깎아쓰기+1년후풍경

### 검증 완료
- EP01 본인 chat_id 실발송 성공(Markdown 파싱 통과), dry-run·status 정상
- plist 문법 OK, 스크립트 실행권한 부여

### 직원봇 재사용 확정 (전용 봇 불필요)
- 직원 발송은 **일일업무보고봇**(`DAILY_REPORT_BOT_TOKEN`) 재사용 → 직원이 이미 아는 봇으로 발송
- 수신자 = `arisa-employees.json`의 `by_telegram_id` 자동 사용 (개인채팅 user_id=chat_id)
- 현재 **명부 12명 중 텔레그램ID 학습 3명** → 나머지 9명은 봇에 1회 메시지(/report 등) 필요
- 스크립트에 `--audience {me,employees}` 추가, 래퍼·plist는 `--audience employees`로 차주 발송
- **roadmap.html** 추가(8주 여정 맵), 샘플(온보딩+EP01) 본인 발송 검증 완료

### 운영 시작 전 남은 결정 (사용자 확인 필요)
1. **미학습 직원 9명** — 일일업무보고봇에 1회 메시지 유도(전체 안내) → chat_id 자동 학습
2. **launchd load** — `launchctl load ~/Library/LaunchAgents/com.dobetter.ax-newsletter.plist` (차주 월 09:00 가동)
3. EP03~07 상세 HTML 제작 여부(현재 텔레그램 본문만)

### 2차 — 직무별 심화 예제 강화 (2026-06-20)
- 직원 구성 확인: 공간팀3·기획팀3·운영1 + 마케팅 업무 → **4직무군**(디자인/기획·PM/운영/마케팅)
- **`job-playbook.html`** 신설 — 4직무 탭 × 업무흐름 3단계(리서치/자료정리/보고서) = **12블록** 예제집(복붙 프롬프트+산출물+검증+출처스킬), R 다크테마
- **`job-examples.md`** 신설 — 예제집 콘텐츠 원천
- 회차 본문(ep-01~07) 강화 — "💼 내 직무라면" 직무별 1줄 + 예제집 안내, EP02·05·06에 공통흐름 보강. 전 회차 1,041자 이하(텔레그램 여유)
- `curriculum.md`·`roadmap.html` 반영. 소스: 워크스페이스 자산(RXR 8종·brand-analysis·card-news·소상공인 M1·디자인컨설팅·survey) + 온라인 사례(콘텐츠 캘린더·경쟁사 90일·프롬프트 4요소)
- 예제집 전달 방식 → **텔레그램 첨부**로 확정(아래 3차 보안)

### 3차 — 30일 보안 패키지 구축 (2026-06-20)
사용자 요청: 텔레그램 전달 자료를 발송 30일 후 삭제·사용불가로. 풀 패키지(삭제+만료링크+워터마크+공지).
- **`build-locked.py`** — `job-playbook.html`→`job-playbook-locked.html` 빌더. 프로젝트렌트 표준 패턴 재사용(비번 게이트+EXPIRY `new Date` 비교+CSS 워터마크+보안공지+Base64 payload+TextDecoder)
- **`job-playbook-locked.html`** — 비번 `projectrent2026`, 만료 `2026-08-31`(빌드 인자), 워터마크 "AX 교육 · Project Rent", 하단 보안공지. payload 디코드·12블록 정상
- **`send-newsletter.py` 보안 보강**:
  - `tg_send`가 message_id 반환 → `sent-log.json`에 발송 기록(token/chat/msg/episode/sent_at)
  - `tg_send_document`(multipart) — 예제집 보안본 첨부(`--attach`)
  - `--purge` — `SECURITY_TTL_DAYS=30` 경과분 `deleteMessage`로 회수 후 로그 정리
  - **검증 완료**: 텍스트+첨부 발송→msg기록→타임스탬프 31일전 조작→`--purge`→텔레그램 실삭제+로그 비움 확인
- **`com.dobetter.ax-newsletter-purge.plist`** — 매일 04:30 `--purge` (plutil OK, 미등록 대기)
- 회차 본문 8개에 "🔒 30일 후 자동 삭제·무단 공유 금지" 공지 푸터 추가
- **텔레그램 한계 명시**: 수신자 캡처/복사/전달 사본은 회수 불가 → 삭제+워터마크+공지는 유출 억제·추적이지 완전 차단 아님

### 4차 — 직원 자동등록 (2026-06-20)
- 봇 링크: **https://t.me/Dailywork_report_bot** (@Dailywork_report_bot, "업무보고 도우미")
- `daily-report-bot.py`에 `register_subscriber()` + `cmd_start` 훅 추가 → 직원이 봇 [시작]만 눌러도 `recipients.json`에 chat_id 자동 등록 + "AX 뉴스레터 신청 완료" 안내
- `send-newsletter.py` `resolve_audience`: 자동구독(recipients.json) ∪ 직원명부(by_telegram_id) 합집합·중복제거
- 봇 재시작 완료(launchctl kickstart). 함수 단위 + 합집합 dry-run 검증 통과
- 직원 공지문구: "봇 링크 → [시작] 누르면 자동 수신 신청" + 30일 자동삭제 안내

### 5~7차 — 케이스북·주차 스텝·프로젝트 일정 특별편 (2026-06-21)
- **5차 케이스북**: `casebook/case-{design,planning,ops,marketing}.html` 4종(워크스루+목업+성과근거) + 보안본. 직무매칭 발송 `--casebook`
- **6차 주차 스텝**: `build-steps.py`+`step_content.py` → `steps/wk1~7-{4직무}.html` 28개 + 보안본. 각 스텝=워크스루+성과+🎤차주 **주간 공유** 5분 발표(발표슬라이드 AI제작 프롬프트). WK2 충실화(왜/팁/이어서). 발송 `--steps`(직무 스텝 + **마케팅 전직무 공통 동봉**)
- **7차 프로젝트 일정 특별편(WK8)**: 기획/디자인/운영 3종. 턴키 팝업 8단계 기준, **①정의 ②현황 ③D-Day 역산 일정표** 순차(stages) + **🚩 핵심 마일스톤** 섹션. `--steps --wk 8`(마케팅 미존재 조용히 skip)
- 회차 본문 ep-01~07에 "📎 이번 주 직무 심화 스텝 첨부 → 차주 주간 공유 발표" 안내
- 총 스텝 HTML 31개(WK1~8) + 보안본 31개. 전체 보안본 비번 `projectrent2026`·만료 `2026-08-31`
- 검증: 직무매칭 dry-run, 본인 실발송(텍스트+첨부), purge 정상

### 정식 가동 체크리스트 (사용자 요청 시)
1. 직원 전체에게 봇 링크 공지 → 각자 [시작] → recipients.json 자동 등록
2. 예제집 보안본 재빌드(만료일/비번 확정): `python build-locked.py --expiry YYYY-MM-DD --pw ___`
3. 발송 가동: `launchctl load ~/Library/LaunchAgents/com.dobetter.ax-newsletter.plist`
4. purge 가동: `launchctl load ~/Library/LaunchAgents/com.dobetter.ax-newsletter-purge.plist`
5. 정식 발송은 `--audience employees --attach`로 (직원봇+예제집 첨부)
