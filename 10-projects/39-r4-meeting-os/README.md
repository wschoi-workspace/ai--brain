# 39 — R4 Meeting OS 회의록 시뮬레이터

회의 전사 데이터를 실행 가능한 프로젝트 데이터로 변환하는 AI Meeting Intelligence System의
**Phase 1 Conversation Prototype** (가설 검증용 시뮬레이터).

> 검증 가설: AI가 회의 전사를 분석하고, 필요한 후속 질문을 한 뒤,
> 실제 업무에 사용할 수 있는 실행 중심 회의 결과물을 만들 수 있는가?

## 접속

- **맥미니 상시가동**: https://server-mini-macmini.tail7739de.ts.net:8781/ (tailnet 전용)
- 로컬 실행: `python3 00-system/02-scripts/meeting-simulator-server.py 8781`
- CLI 테스트: `python3 meeting-simulator-server.py --test 전사파일.txt`

## 구성

| 파일 | 역할 |
|------|------|
| `00-system/02-scripts/meeting-simulator-server.py` | 서버+프롬프트 5종+UI 올인원 (표준 라이브러리만, pip 의존 0) |
| `00-system/02-scripts/install-r4meeting.sh` | 맥미니 launchd 설치 스크립트 (`com.projectrent.r4meeting`, 포트 8781) |
| `00-system/02-scripts/r4-data/sessions/` | 세션 JSON (gitignore, 로그: `/tmp/r4-meeting.log|.err`) |
| `test-transcripts/` | 검증용 전사 (정보공유형·기획협의형 시나리오) |

## 파이프라인 (LLM 5회 호출, claude-sonnet-4-6)

```
전사 입력 → ①classify(타입 12종+메타 추정) → 사용자 타입 확인
→ ②extract(회의록 A~L+결정+액션+산출물+지원요청, 12K tok, 백그라운드)
→ ③detect(필수정보 모델 8세트 대조 → 6상태 판정 + 질문 생성)
→ 질문 루프(최대 3라운드, 답변 5종: 답변/추후확인/해당없음/AI추정수용/담당자질문)
→ ④revise(patch 반영 + 서버측 결정론 infoStatus 갱신)
→ ⑤finalize(준비도 12영역 + Executive Summary)
→ 7탭 결과 + export.md(회의록정리 9섹션 호환)/export.json
```

## 검증 결과 (2026-07-21, v1.1)

| 시나리오 | 분류 | 추출 | 특이사항 |
|----------|------|------|----------|
| 봉은사 킥오프 (실제, 3.5K자) | PROJECT_KICKOFF 85% ✅ | 결정1·액션2, CRITICAL 누락 10개 정확 탐지 | 질문→답변→준비도 41→54% 갱신 확인 |
| 순수 정보공유 (대화체) | INFO_SHARE 95% ✅ | **액션 0개 (억지 생성 없음)** ✅ | 질문도 IMPORTANT만 3개 |
| 기획협의 (A/B안+일정충돌) | PLANNING 90% ✅ (v1.0에선 킥오프 오분류) | 액션 3 전원 담당자 정확, 지원요청 2(BLOCKING) | 일정 충돌 → 미해결 이슈로 기록 |

LLM 소요: classify 2~5s / extract 8~18s / detect 6~18s / revise 4~10s / finalize 5~7s
(짧은 회의 기준. 1~2시간 전사는 extract 1~3분 예상, 백그라운드+폴링 처리)

## 프롬프트 튜닝 기록

- **v1.0 → v1.1 (2026-07-21)**
  - classify: 킥오프 편향 보정 — "이미 진행 중 프로젝트의 방향·대안 논의 = PLANNING" 구분 기준 명시. 요약·보고서 형식 텍스트도 내용 기준 판단.
  - extract: ①연도 환각 금지(회의 일시 없으면 상대 표현 그대로 + INFERRED) ②발언 충돌 → G_open_issues 필수 기록 ③외부 수령 자료(도면·견적·승인)는 supportRequests 필수 추출.
  - revise: newQuestions 스키마(id/tier/...) 명시 — v1.0에서 `questionId`로 반환→서버 KeyError 버그. 서버측 `_normalize_questions()` + 결정론적 infoStatus 반영 + do_POST 예외 가드로 3중 방어.
  - finalize: "infoStatus CONFIRMED 항목은 확보된 정보로 평가에 반영" — 답변한 예산이 NOT_READY로 나오던 문제 해소.

- **v1.1 → v1.2 (2026-07-21 밤) — R유럽 40KB 원본 STT 실전 테스트로 발견**
  - **extract 2호출 분리**: 40KB 노이즈 STT에서 전수 추출 시 출력이 12K 토큰 초과(`stop_reason: max_tokens`)
    → gpt-4o 폴백이 축약본 생성(결정 1·액션 1)하던 문제. `extract-minutes`(8K) + `extract-items`(10K)로 분리
    + 출력 압축 규칙(무들여쓰기·evidence 1개·quote 60자) 추가.
  - 결과: 결정 1→7, 액션 1→14, 산출물 0→4, 지원요청 0→5. 사람이 작성한 정리본과 동등 이상 커버리지.
  - classify는 원본 STT에서도 정확: PLANNING 82%, STT 품질·고유명사 오인식·수치 불확실 경고까지 생성.

### 실전 테스트 #4 — R유럽 원본 STT (40KB, 화자 구분 없음)

| 항목 | 결과 |
|------|------|
| 분류 | PLANNING 82% (2차: WORKING_SESSION, FOLLOW_UP) ✅ |
| 추출 | 결정 7(하이브리드 확정 등) · 액션 14(담당·기한 포함) · 지원요청 5(BLOCKING 2) |
| 정리본 대비 | 사람 작성 회의록(결정 7·투두 10)과 동등 이상 — 누락 없음 |
| 소요 | classify 28s / extract-minutes 119s / extract-items 108s / detect 60s |
| 한계 | 상대 기한("차주 초")을 실제 날짜로 환산하지 않음(보수적 — 환각 방지 우선) |

## 남은 과제 (Phase 2+)

- 전사 10만 자 초과 청킹 (현재 입력 거부 가드만)
- extract 출력 잘림(`max_tokens`) 시 minutes/actions 2호출 분리
- R4 본개발 연동 (Phase 3): 세션 JSON이 인터페이스 계약 검증 자료
- Meeting Coach (Phase 4): 회의 전 아젠다·실시간 경고
- 회의 원문 음성 전사 (MVP 제외 항목)
