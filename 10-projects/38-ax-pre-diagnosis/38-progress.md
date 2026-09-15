# 38. AX 교육 사전진단 — Progress

> 2026-09-16 워크스페이스 진단에서 누락이 확인되어 소급 작성. 이전 기록은 파일 구조와 산출물에서 역추적한 것이다.

> **무엇** · AX(AI 업무전환) 교육 참가자 사전진단 대화형 인터뷰 웹앱 + 응답 통합 리포트
> **교육 세션 코드** · `RXR_AX_EDU` (제목 "AX 초심자 교육" — `supabase/schema.sql` 시드값)
> **스택** · Next.js 16.2.10 · React 19.2.4 · TypeScript · Tailwind v4 · Supabase · OpenAI SDK (bun)
> **배포** · Vercel 프로젝트 연결됨 (`.vercel/project.json` — projectName `38-ax-pre-diagnosis`)
> **상위 프로젝트** · `10-projects/28-ai-education-ax/` (AX 교육 본편) — 다만 28-progress.md에 본 프로젝트 언급은 없음

---

## 2026-07-21 — 웹앱 구축 (하루 작업, 파일 기준 추정)

파일 mtime이 **02:59 → 09:21** 한 구간에 몰려 있다. 스캐폴딩부터 관리자 화면까지 하루에 끝난 것으로 보인다.

### 시간순 (mtime 기준 추정)

| 시각 | 내용 |
|---|---|
| 02:59 | `create-next-app` 스캐폴딩 (README·eslint·postcss·tsconfig·public/*.svg) |
| 03:01 | `package.json` — supabase-js · openai 의존성 추가 |
| 03:04 | `supabase/schema.sql` — 테이블 4종 + RLS |
| 03:05~03:06 | `src/lib/` (analyze·questions·supabase) · `api/session` · layout·globals |
| 06:48~07:21 | `types.ts` · `.env.local` · `gpt-system-prompt.md` · `api/answer` |
| 07:44~07:56 | `api/analyze` · Vercel 링크(`.vercel/`) |
| 08:17~08:59 | `page.tsx` · 관리자 API 3종(sessions·analyze·reset) · `admin/page.tsx` · `api/chat` |
| 09:08~09:21 | `join/[code]` · `interview/[token]` 페이지 |

### DB 스키마 (`supabase/schema.sql`)

- `education_sessions` — 교육 프로그램 단위. `code` unique, 시드 1건 `RXR_AX_EDU`
- `interview_sessions` — 참여자별. URL `token`, `status`(started/in_progress/completed), `consent_given`
- `interview_answers` — 문항별 답변(`question_id` q1~q8 + `additional`, `is_follow_up`)
- `interview_analysis` — AI 분석 결과 17필드(ai_familiarity_level · desired_ai_role · expectation_clarity_score · recommended_difficulty · needs_expectation_adjustment 등) + `raw_analysis` jsonb
- RLS 활성 + **anon 토큰 기반 정책**(select/update/insert 허용)

### 인터뷰 설계

- `gpt-system-prompt.md` — 인터뷰어 프롬프트. 제1원칙 "**AI 지식을 시험하는 것이 절대 아니다**". 반드시 파악할 **7가지**(현재 AI 수준 / 참여 이유 / 기대하는 변화 / 적용 업무 / 기대하는 AI 역할 수준 / 만족 기준 / 교육 후 첫 행동). 소요 5~7분, 음성 답변 허용 안내
- `src/lib/questions.ts` — 문항 정의. 타입 3종(`select` · `select_with_detail` · `free`), free 문항은 `referenceExamples`로 보기를 제시만 하고 강제하지 않는 구조
- 08:42 `interview-result-Ym2nRFR7.html` — 개인 결과 페이지 샘플 1건(최원석 본인 테스트분으로 보임)

---

## 2026-07-23 — 응답 8명 통합 리포트 (파일 기준 추정)

`설문통합리포트.html`(14:00) / `설문통합리포트-익명.html`(14:04) — 7섹션 구성.

- **조사 기간** 2026.07.21 ~ 07.23 · **응답자 8명** · 분석 기준 7개 핵심 항목
- 구성: 전체 요약 대시보드 → 응답자 전체 비교표 → 응답자별 상세 프로필(2장) → 요청·특이사항 그룹핑 → 교육 설계 시사점 6 + 종합 추천 난이도·구성
- 핵심 수치(리포트 본문): **100% AI 사용 경험 보유 / 75% 완성본 수준 기대 / 88% 실습 중심 선호**
  - AI 수준 분포 — 적극 활용 3 · 기본 활용 4 · 경험 있음 1
  - 기대 역할 — 완성본 4 · 초안+피드백 3 · 수치 자동입력 1
  - 참여 동기 — 업무 효율화 6 · AI 활용 확장 2
- 핵심 발견으로 적힌 것 — 전원이 AI 경험은 있으나 "간단한 질문" 수준에 머물러 있고, 니즈가 **매장 운영(재고/원가/매출) · 콘텐츠 제작 · 행정 자동화** 3개 영역에 집중
- 교육 설계 시사점 6종 — ①난이도 차별화 ②실습>이론 ③데모 3종 매칭 ④"완성본" 기대 관리 ⑤심리적 안전 장치 ⑥업종 특화 사례
- **익명본을 따로 뽑았다** — 실명본에는 응답자 8명 실명이 그대로 들어 있어 공유용을 분리한 것으로 보인다

---

## 자산 상태 (2026-09-16 확인)

- 폴더 총 **469MB**, 그중 `node_modules`가 사실상 전부. 소스·산출물은 수백 KB
- `.gitignore`에 `/node_modules` 있음 → git 추적 파일 **35개**(소스 + 리포트 2종 + 결과 샘플 1종). `.env.local`은 미추적(정상)
- **재사용 중** — `.claude/skills/chat-survey/SKILL.md`가 본 폴더를 "레퍼런스 구현"으로 지정하고 구조 복제를 지시한다

---

## 남은 것

- **운영 URL·라이브 여부 확인 필요** — Vercel 프로젝트는 링크돼 있으나 배포 도메인 기록이 폴더 어디에도 없다
- **28-ai-education-ax와의 연결 기록 없음** — 통합 리포트의 "교육 설계 시사점"이 실제 커리큘럼에 반영됐는지 확인 필요
- Supabase 프로젝트가 아직 살아 있는지(무료 플랜 일시정지 여부) 확인 필요
- 폴더 용량 469MB의 대부분이 `node_modules` — 보관만 할 거면 삭제 검토(재설치는 `bun install`)
- 후속 교육 회차에 재사용한다면 `education_sessions`에 코드 추가 필요 — 현재 시드는 `RXR_AX_EDU` 1건뿐
