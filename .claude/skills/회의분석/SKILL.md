---
name: 회의분석
description: R4 Meeting OS 시뮬레이터로 회의 전사를 빠르게 분석 — 써머리(Executive Summary)·구조화 회의록·산출물 3종만 뽑는 라이트 모드. 질문 루프·준비도 등 상세 분석은 웹 UI에서 이어서. "회의분석", "회의 분석", "회의록", "회의록 만들어", "회의자료 만들어줘", "회의 자료 만들어", "회의자료", "미팅 분석", "미팅 자료", "R4 분석", "회의 시뮬레이터", "전사 분석", "meeting os" 등을 언급하면 자동 실행. /회의록 으로도 호출 가능(별칭). (9섹션 문서 포맷의 회의록만 원하면 /회의록정리가 담당 — "회의록정리"라고 명시했을 때만)
allowed-tools:
  - Read
  - Write
  - Bash
---

# 회의분석 — R4 시뮬레이터 라이트 모드 (써머리·회의록·산출물)

회의 전사(원본 STT·메모·정리본)를 맥미니 R4 시뮬레이터에 태워 **써머리 + 구조화 회의록 + 산출물**을 빠르게 뽑는다.
질문 루프는 이 스킬에서 진행하지 않는다 (상세 분석은 웹 UI에서 이어하기). 이 대화가 끝날 때까지 모드 유지.

- **서버**: `https://server-mini-macmini.tail7739de.ts.net:8781` (tailnet 전용, launchd 상시가동)
- 서버 다운 시 폴백: `python3 00-system/02-scripts/meeting-simulator-server.py --test 파일` (CLI, 질문 루프 없음)
- 직원 공유: 분석 결과는 같은 URL의 웹 UI에서 누구나(tailnet) 열람·이어하기 가능 — 세션 ID를 알려주면 됨

## 1. 입력 처리

`$ARGUMENTS` 해석 우선순위 (/회의록정리와 동일 패턴):
1. **절대경로** → 그 파일 읽기
2. **파일명만** → `~/Library/CloudStorage/Dropbox/13-업무자동화/회의정리/` 에서 찾기
3. **긴 텍스트** (3줄 이상) → 그대로 전사로 사용
4. **비어있음** → 전사를 붙여넣거나 파일 경로를 달라고 요청

전사와 함께 파악 가능한 메타(회의명·일시·참석자·프로젝트·고객사)를 대화 맥락에서 수집. 없으면 비워둠(AI가 추정).
전사 10만 자 초과 시 나눠 달라고 안내.

## 2. 세션 생성 + 타입 분류

Bash에서 python3로 호출 (curl은 전사 이스케이프 문제로 금지):

```python
import json, urllib.request
BASE = "https://server-mini-macmini.tail7739de.ts.net:8781"
body = json.dumps({"transcript": transcript, "meta": {"title": "...", "date": "...",
    "participants": "...", "project": "...", "author": "...", "client": "..."}}).encode()
req = urllib.request.Request(BASE + "/api/meeting", data=body,
    headers={"Content-Type": "application/json"})
d = json.load(urllib.request.urlopen(req, timeout=150))  # classify 동기 ~30초
```

분류 결과를 사용자에게 보고: **타입(한글)·신뢰도·판단 이유·전사 품질 경고**.
- 신뢰도 ≥ 0.7 → 그대로 진행 ("이 타입으로 진행합니다" 한 줄 알리고 계속)
- 신뢰도 < 0.7 → 12타입 중 어느 쪽인지 사용자에게 확인 후 진행

## 3. 구조화 추출 (백그라운드 + 폴링)

```python
# confirm-type → 백그라운드 추출 시작
urllib.request.urlopen(urllib.request.Request(f"{BASE}/api/meeting/{sid}/confirm-type",
    data=json.dumps({"primaryType": ptype}).encode(), headers={"Content-Type": "application/json"}), timeout=30)
# 8초 간격 폴링, status가 ANALYZING을 벗어날 때까지 (긴 전사는 3~5분)
```

status가 ERROR면 `/retry` 1회 후 그래도 실패 시 사용자에게 서버 로그(`/tmp/r4-meeting.err`) 확인 안내.

## 4. 질문 스킵 + Finalize (라이트 모드 핵심)

이 스킬은 질문 루프를 진행하지 않는다:
```python
# POST /api/meeting/{sid}/skip-questions  →  POST /api/meeting/{sid}/finalize (timeout 240)
```

## 5. 결과 보고 — 써머리·회의록·산출물 3종만

최종 보고에 포함 (이 3가지만 — 준비도·Support Map·질문 상세는 생략):
1. **써머리 (Executive Summary)**: 한 줄 요약 / 핵심 결과 / 핵심 결정 / 최대 리스크 / 다음 마일스톤
2. **회의록 요약**: 주제별 논의(제목만) + 결정사항 테이블 + To do(담당·기한)
3. **산출물**: 만들어야 할 결과물 목록 (이름·담당·기한·승인 기준)

마지막에 한 줄: "AI 후속 질문·실행 준비도 등 상세 분석은 웹 UI에서 이어서 → `{BASE}/` (세션: {sid})"

## 6. 산출물 저장 + 연계

- `GET /{sid}/export.md` 를 받아 해당 프로젝트 폴더(맥락상 판단, 모르면 사용자에게 질문)에
  `YYYY-MM-DD-회의명-r4-export.md` 로 저장
- 추가 출력 옵션 안내 (링크만 제공):
  - **PDF**: `{BASE}/api/meeting/{sid}/report.html` — 인쇄 최적화 리포트, 열어서 "인쇄→PDF로 저장"
  - **워드 문서**: `{BASE}/api/meeting/{sid}/export.doc`
- 저장 후 제안 (실행은 요청 시에만): "**/보드등록 회의록** 으로 PR 보드에 카드 등록할까요?"

## 주의

- 서버는 상태를 세션 JSON으로 보존 — 중단돼도 세션 ID로 이어하기 가능 (`GET /api/meeting/{sid}`)
- 담당자·일정은 시뮬레이터가 추천만 함. 확정은 항상 사용자 몫이라는 전제를 보고 문구에 유지
- 숫자·예산이 나오면 "AI추정/확정" 구분을 그대로 전달 (환각 방지 설계 존중)
