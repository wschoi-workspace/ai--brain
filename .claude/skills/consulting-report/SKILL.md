---
name: consulting-report
description: >
  컨설팅 레포트 제작 — 이미 수행한 분석·데이터를 McKinsey/Bain(MBB) 스타일의
  진단·전략 컨설팅 레포트(HTML 덱)로 구조화·제작하는 오케스트레이터.
  입력(분석결과/인사이트/수치) → Governing Thought + Ghost Deck(액션타이틀 먼저) →
  MBB 아키텍처 매핑(Exec Summary·SCQA·MECE, 본문 vs Back-up 분리) →
  슬라이드 콘텐츠(So What/Now What·Exhibit·Doblin 옵션) → project-rent 다크테마 HTML 덱 → 검증·PDF.
  펌 스타일 4종(McKinsey/Bain/한국 공공형/하이브리드) 선택 지원.
  "컨설팅 레포트", "컨설팅 보고서", "맥킨지 레포트", "맥킨지 스타일", "베인 스타일",
  "MBB 레포트", "MBB 포맷", "consulting report", "컨설팅 덱", "진단 레포트",
  "전략 보고서", "경영진 보고서", "컨설팅 형식으로", "맥킨지처럼" 등을 언급하면 실행.
  ⚠️ 정부 제안서 제작은 /gov-proposal, RFP 분석은 /rfp-analysis, 브랜드 SNS 진단은
  /brand-analysis 가 담당 — 본 스킬은 "이미 가진 분석을 MBB 레포트로 제작"하는 데 특화.
user-invocable: true
model: opus
context: fork
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Edit
  - WebFetch
  - WebSearch
  - Agent
  - AskUserQuestion
  - mcp__plugin_playwright_playwright__browser_navigate
  - mcp__plugin_playwright_playwright__browser_take_screenshot
  - mcp__plugin_playwright_playwright__browser_close
---

# /consulting-report — 컨설팅 레포트 제작 (McKinsey · Bain 스타일)

## Core Philosophy

일류 컨설팅 레포트는 **"바쁜 의사결정자가 1장만 봐도 결론과 행동을 이해"**하도록 설계된다.
핵심은 화려한 디자인이 아니라 **논증의 구조**다 — 답을 먼저(Answer First), 근거는 MECE하게,
제목은 결론을 담은 액션 타이틀로, 깊은 근거는 [Back-up]으로 분리.

이 스킬은 **이미 수행한 분석·데이터를 입력으로 받아** 그 구조를 자동 적용하고,
project-rent 다크테마 HTML 덱으로 완성한다. **분석을 새로 하지 않는다** — 분석이 필요하면
먼저 `/rfp-analysis`·`/brand-analysis`를 돌리고 그 결과를 이 스킬에 넘긴다.

> **"했다"가 아니라 "잘했다"** — 제목만 읽어도 논증이 흐르는지(Ghost Deck 테스트)가 합격선.

---

## 참조 자산 (반드시 먼저 Read)

| 파일 | 역할 |
|------|------|
| `00-system/01-templates/consulting-report-template.md` | **매크로 구조** — 리포트 ①~⑩ 섹션 시퀀스 + 펌별 포맷 비교 + Doblin 모듈 |
| `00-system/01-templates/executive-report-framework.md` | **마이크로 구조** — 피라미드/SCQA/So What·Now What/액션타이틀/1p Exec Summary |
| `00-system/01-templates/consulting-report-hybrid-deck.html` | **HTML 패턴** — 8장 덱(Cover/ExecSum/Cheat Sheet/Doblin/Exhibit/A·A·I/Roadmap)의 마크업·CSS |
| `00-system/01-templates/doblin-diagnostic-slides.html` | **옵션 모듈** — Doblin Ten Types 진단 매트릭스 + 포지션 매핑 |
| `00-system/04-design/project-rent-design-guide.md` | **디자인 토큰** — 색(#6C5CE7 극소량)·Pretendard·12컬럼·8px |
| `00-system/04-design/presentation-narrative-guide.md` | (옵션) B2C 감성 서사가 필요할 때 |

---

## 펌 스타일 4종 (Phase 0에서 선택)

| 스타일 | 시그니처 | 언제 |
|--------|---------|------|
| **McKinsey** | 텍스트 밀도 높음, Exhibit 번호+하단 출처 각주, [Back-up] 분리, 러닝헤더 | 논리·정합성이 중요한 진단/전략 |
| **Bain** | 결과·실행 지향, 권고-임팩트 직접 연결, 간결 | 실행안·ROI 중심 |
| **한국 공공형** | **긴 액션타이틀(제목=한 문장 결론)**, 주체 라벨(맥킨지/삼일 등), [Back-up] ~28%, 선진도시 벤치마크, 실행 로드맵 | 시·정부·공공기관 용역 보고 |
| **하이브리드** | MBB 골격 + NYT Competitor Cheat Sheet + Wolff Olins Ambition→Action→Impact + Doblin 모듈 | 제안·발표용, 설득력 극대화 |

> 근거: McKinsey *Social Impact Bonds*·*서울시 시정 컨설팅 보고서*(긴 액션타이틀·Back-up 28%·주체라벨),
> NYT *Innovation Report*(Cheat Sheet), Wolff Olins *Credbook*(A·A·I). 상세는 consulting-report-template.md.

---

## 실행 흐름

### Phase 0 — 입력 수집 & 스코핑
참조 자산 6종을 Read한 뒤, 다음을 확인. **부족하면 AskUserQuestion으로 묻고, 임의 생성 금지.**
- **분석 내용/데이터**: 어떤 분석을 했나 (수치·인사이트·근거). 파일/텍스트로 받음
- **클라이언트 · 목적 · 청중**: 누구에게 무엇을 결정하게 할 보고인가
- **펌 스타일**: 위 4종 중 (미정 시 AskUserQuestion)
- **분량/형식**: 풀 리포트(①~⑩) vs 핵심 덱(6~8장) vs Exec Summary 1장
- **Doblin 모듈 포함 여부**: 혁신/포지셔닝 진단이 필요하면 포함

### Phase 1 — Governing Thought & Ghost Deck (스토리라인 먼저)
- 입력에서 **Governing Thought**(리포트 전체를 떠받치는 한 문장 결론) 도출
- **모든 슬라이드의 액션 타이틀만** 먼저 작성 → 위에서 아래로 읽어 논증이 완결되는지 검증
- 통과 못 하면 여기서 재배열. **콘텐츠·디자인은 아직 손대지 않는다**
- 결과를 `{프로젝트}/consulting-report-storyline.md`로 저장하고 사용자에게 확인받기

### Phase 2 — MBB 아키텍처 매핑
consulting-report-template.md의 ①~⑩에 입력을 배치하고, 각 항목을 **본문 vs [Back-up]으로 분류**:
```
① Cover  ② Executive Summary(=답)  ③ Context/Objective(SCQA)
④ Approach/Methodology  ⑤ Findings  ⑥ Analysis(So What·이슈트리)
⑦ Recommendations(Now What·우선순위)  ⑧ Roadmap(간트)  ⑨ Expected Impact  ⑩ Appendix/Back-up
```
- 본문은 핵심 메시지만, 상세 데이터·방법론·해외사례는 [Back-up]/Appendix로
- 각 챕터는 governing thought 1개를 5~8장으로 증명 (MECE)

### Phase 3 — 슬라이드 콘텐츠 작성
executive-report-framework.md 규칙 적용:
- 모든 데이터에 **So What**(인사이트), 모든 인사이트에 **Now What**(액션+담당+기한)
- **Exhibit**: 차트마다 액션타이틀 + `Exhibit N` 번호 + **하단 출처 각주(출처·n수·단위)**
- 핵심 숫자는 3개 이하 (Rule of Three), 단위 정확히(% vs %p)
- (옵션) **Doblin 진단**: doblin-diagnostic-slides.html 패턴으로 매트릭스+포지션 매핑
- (하이브리드) **Competitor Cheat Sheet**(경쟁사 동일 카드) + **Ambition→Action→Impact 케이스**

### Phase 4 — HTML 덱 제작
- consulting-report-hybrid-deck.html의 마크업·CSS를 토대로, project-rent 다크테마 적용
  (#1A1A1A 배경 / 크림 텍스트 / #6C5CE7 극소량 / Pretendard / 12컬럼·8px)
- 전 슬라이드 **러닝헤더**(`보고서명 | 섹션`), 슬라이드당 1메시지, 푸터에 by Project Rent
- **공유/캡처용이므로 화면 네비바(prev/next/edit)·progress bar 제거** (워크스페이스 컨벤션)
- 저장: `{프로젝트}/consulting-report-{주제}.html`

### Phase 5 — 검증 & 출력
- **Ghost Deck 재검증**: 슬라이드 제목만 읽어 논증이 흐르나
- **숫자 3중 체크**(CLAUDE.md): 모든 수치·인용·출처를 추출 → 신뢰출처 크로스체크 → 재대조.
  단위(% vs %p)·귀속·맥락·출처표기 대조. 불확실하면 지어내지 말고 자리표시자 + 확인 요청
- **Exhibit 출처 각주** 누락 없는지, **러닝헤더 일관**·**네비바 없음** 확인
- Playwright(또는 `/tmp` pdf.js 캡처 스크립트)로 슬라이드 PNG 캡처해 렌더 육안 확인
- 필요 시 PDF 출력 (`/playwright`), 공유용이면 보안 세팅([[feedback_share_pdf_security]])

---

## 산출물

| 파일 | 내용 |
|------|------|
| `{프로젝트}/consulting-report-storyline.md` | Phase 1 액션타이틀 스토리라인 (확인용) |
| `{프로젝트}/consulting-report-{주제}.html` | 최종 컨설팅 레포트 덱 |
| `{프로젝트}/consulting-report-{주제}-preview-p{n}.png` | 슬라이드 미리보기 |
| (옵션) `{주제}.pdf` | 제출/공유용 PDF |

---

## 안티패턴 (하지 말 것)
- ❌ 분석을 새로 지어내기 → 입력에 없는 수치 생성 금지. 부족하면 질문
- ❌ "분석한 결과…"로 시작하는 제목 → 액션 타이틀(결론)로
- ❌ 본문에 모든 근거 욱여넣기 → 핵심만 본문, 상세는 [Back-up]
- ❌ 우선순위·담당·기한 없는 To-do 나열 → Recommendation은 우선순위+책임자+기한
- ❌ 출처 없는 차트 → 모든 Exhibit에 하단 각주
- ❌ 네비바/progress bar 포함 → 공유용은 제거

## 연계 스킬
- 분석이 먼저 필요하면: `/rfp-analysis`(RFP·경쟁PT) · `/brand-analysis`(브랜드 SNS 진단)
- 감성 PT 서사가 필요하면: `/proposal-architect`(10단계 하이브리드 공식)
- 캡처·PDF: `/playwright` · 전략 검증: `/thinking-partner`
