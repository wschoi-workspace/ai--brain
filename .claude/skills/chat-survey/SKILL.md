---
name: chat-survey
description: 능동형 대화 설문조사 시스템 자동 생성. "대화형 설문", "chat survey", "챗 설문", "설문 챗봇", "인터뷰 챗봇", "사전진단 만들어줘", "설문조사 시스템", "대화형 진단" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# Chat Survey — 능동형 대화 설문조사 시스템 생성기

사용자가 **수집 항목 + 톤 + 목적**만 정의하면, AI가 자연스러운 대화로 응답을 수집하는 완전한 웹앱을 자동 생성·배포한다.

**레퍼런스 구현**: `10-projects/38-ax-pre-diagnosis/` (AX 교육 사전진단)

---

## Phase 0: 요건 수집 (필수)

사용자에게 아래 항목을 대화로 파악한다. 빠진 항목은 질문한다.

| 항목 | 설명 | 예시 |
|------|------|------|
| **설문 목적** | 이 설문으로 무엇을 파악하려는가 | "교육 참여자의 기대와 수준 파악" |
| **수집 항목** | 반드시 파악해야 할 N가지 (4~10개 권장) | 7가지: AI 사용 수준, 참여 이유, 기대 변화... |
| **항목별 예시 질문** | 각 항목에서 AI가 던질 예시 포함 질문 가이드 | "ChatGPT, 번역기, 사진 보정 앱 같은 것도 AI인데요..." |
| **톤/호칭** | 대화 분위기, 존칭 여부 | "따뜻한 존댓말, ~하시나요?" |
| **타겟 대상** | 응답자가 누구인지 | "AI를 모를 수 있는 일반 직장인" |
| **대화 턴 수** | 목표 턴 (기본 8~12턴) | 8~12턴 |
| **브랜드명** | 헤더에 표시할 이름 | "RXR-AX-EDU" |
| **관리자 코드** | 결과 조회용 비밀번호 | 환경변수로 설정 |
| **분석 항목** | 관리자 리포트에 포함할 심층 분석 | "희망·욕구 분석, 동기 유형, 준비도" |
| **추가 질문** | 마지막에 별도 수집할 자유 의견 | "추가로 하고 싶은 말씀이 있으세요?" |

---

## Phase 1: 프로젝트 스캐폴딩

### 1-1. 폴더 생성

```
10-projects/[번호]-[프로젝트명]/
```

### 1-2. Next.js 프로젝트 초기화

레퍼런스(`38-ax-pre-diagnosis`)의 구조를 복제하되 내용만 교체:

```
src/
├── app/
│   ├── page.tsx                    # 랜딩 (유효한 링크로 접속 안내)
│   ├── layout.tsx                  # Pretendard 폰트, 메타데이터
│   ├── globals.css                 # Tailwind
│   ├── join/[code]/page.tsx        # 공용 입장 (자동 세션 생성 → 리다이렉트)
│   ├── admin/page.tsx              # 관리자 대시보드
│   ├── interview/[token]/page.tsx  # 대화형 인터뷰 본체
│   └── api/
│       ├── session/route.ts        # 세션 CRUD (GET/POST/PATCH)
│       ├── chat/route.ts           # GPT 대화 (시스템 프롬프트 핵심)
│       ├── answer/route.ts         # 턴별 답변 저장
│       ├── analyze/route.ts        # 완료 시 구조화 분석
│       └── admin/
│           ├── sessions/route.ts   # 관리자 세션 목록/상세
│           ├── analyze/route.ts    # 희망·욕구 심층 분석
│           └── reset/route.ts      # 데이터 초기화
└── lib/
    ├── types.ts                    # 타입 정의
    └── supabase.ts                 # Supabase 클라이언트
```

### 1-3. 기술 스택 (고정)

- **프레임워크**: Next.js (App Router)
- **스타일**: Tailwind CSS + Pretendard
- **AI**: OpenAI GPT-4o-mini (대화) + GPT-4o-mini (분석)
- **DB**: Supabase (PostgreSQL + RLS)
- **배포**: Vercel
- **음성입력**: Web Speech API (브라우저 내장)

---

## Phase 2: 시스템 프롬프트 생성

`/api/chat/route.ts`의 SYSTEM_PROMPT를 사용자 요건으로 조립한다.

### 프롬프트 템플릿

```
너는 [설문 목적] 인터뷰어다.

목적: [목적 설명]. 참여자는 [타겟 대상]이다. [대상 특성 설명].

반드시 파악해야 할 [N]가지 + 항목별 질문 가이드:
1. [항목명]
   → "[예시 질문 가이드]"
2. [항목명]
   → "[예시 질문 가이드]"
...

대화 원칙:
- 질문할 때 반드시 2~3개의 구체적 예시를 문장 안에 자연스럽게 포함한다. 단문 질문 금지.
- 첫 질문부터 항상 예시를 곁들인다. 참여자가 [주제]를 모를 수 있다.
- 예시는 일상 언어로, 참여자의 답변 수준에 맞춰 조절한다.
- "예를 들어", "가령", "혹시 ~같은 경험" 등 자연스러운 접속 표현을 사용한다.
- 쉬운 일상 언어를 사용한다. 전문용어를 쓰지 않는다.
- 한 번에 하나의 질문만 한다. 절대 두 개 이상의 질문을 동시에 하지 않는다.
- 답변을 에코백한 뒤 다음 질문으로 넘어간다. 에코백은 단순 반복이 아니라, 공감 + 맥락 연결.
- 모호한 답변이 오면 더 풍부하고 쉬운 예시를 추가로 제시하여 안내한다.
- 이미 충분히 답한 내용을 다시 묻지 않는다.
- 전체 대화를 [턴 수] 안에 마무리한다.
- [N]가지 항목이 충분히 파악되면 요약을 보여주고 확인을 요청한다.
- 사용자가 요약을 확인하면, 추가 의견/기대치를 별도로 수집한다.
- 추가 의견까지 받은 후 마지막 메시지에 반드시 [INTERVIEW_COMPLETE] 마커를 포함한다.

톤:
- [톤/호칭 설정]

응답 형식:
매 응답마다 아래 JSON으로 응답한다:
{
  "message": "인터뷰어의 대화 메시지",
  "progress": 0~100 사이의 수집 진행도,
  "isComplete": false
}
```

### 핵심 규칙
- **예시 기반 질문**: 모든 질문에 2~3개 구체적 예시 내장 (단문 질문 금지)
- **에코백 공감**: 단순 반복 아닌 "공감 + 맥락 연결"
- **모호 답변 대응**: 더 쉽고 풍부한 예시로 재안내
- **추가 의견 수집**: 요약 확인 후 마지막에 반드시 자유 의견 수집
- **이름 필수**: 익명 불가, 반드시 이름 입력 후 진행

---

## Phase 3: Supabase DB 설정

### 테이블 3종

```sql
-- 1. 교육/설문 세션 (관리자가 미리 등록)
CREATE TABLE education_sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. 인터뷰 세션 (참여자별 1건)
CREATE TABLE interview_sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  education_id UUID REFERENCES education_sessions(id),
  token TEXT UNIQUE NOT NULL,
  participant_name TEXT,
  status TEXT DEFAULT 'started',
  current_question INT DEFAULT 0,
  consent_given BOOLEAN DEFAULT false,
  started_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

-- 3. 턴별 답변 저장
CREATE TABLE interview_answers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id UUID REFERENCES interview_sessions(id),
  question_id TEXT NOT NULL,
  raw_answer TEXT NOT NULL,
  selected_options JSONB DEFAULT '[]',
  is_follow_up BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. 분석 결과 (선택)
CREATE TABLE interview_analysis (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id UUID UNIQUE REFERENCES interview_sessions(id),
  raw_analysis JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### RLS 정책
- SELECT/INSERT: anon key 허용
- UPDATE: anon key 허용 (세션 상태 업데이트)
- DELETE: service_role만 또는 admin API 경유

### 초기 데이터
```sql
INSERT INTO education_sessions (code, title) VALUES ('[교육코드]', '[설문 제목]');
```

---

## Phase 4: 관리자 대시보드

### 구조 (위→아래)
1. **코드 인증** — 환경변수 ADMIN_CODE와 대조
2. **세션 목록** — 완료/진행중 분리, 클릭 시 상세
3. **상세 리포트**:
   - 참여자 정보 (이름, 상태, 일시, 소요시간, 턴 수)
   - 합의된 최종 써머리 (N가지 항목 요약)
   - 추가 의견/기대치
   - 희망·욕구 심층 분석 (GPT 분석)
   - 대화 로그 전문 (AI/참여자 버블)

### 심층 분석 프롬프트 템플릿
수집 항목에 맞춰 분석 프롬프트를 자동 생성:
- confirmed_summary: 합의된 항목별 요약
- desire_analysis: 표면 아래 숨은 욕구, 불만 근원, 이상 상태, 갭 분석, 동기 유형, 준비도, 레버리지 포인트, 위험 요소, 맞춤 제안
- additional_opinions: 추가 의견

---

## Phase 5: 배포

### 환경변수 (.env.local)
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
OPENAI_API_KEY=
ADMIN_CODE=
```

### Vercel 배포
```bash
vercel --prod
```

### 공용 입장 링크 형식
```
https://[도메인]/join/[교육코드]
```

---

## Phase 6: 검증 체크리스트

- [ ] 공용 링크로 접속 → "시작하기" → 이름 입력 필수 → 대화 시작
- [ ] 첫 질문부터 예시 포함 확인
- [ ] "잘 모르겠어요" 입력 시 더 풍부한 예시로 안내
- [ ] N가지 항목 수집 → 요약 → 확인 → 추가 의견 수집 → 완료
- [ ] 관리자 페이지에서 결과 조회 (써머리 + 분석 + 로그)
- [ ] 음성 입력 동작 확인

---

## 핵심 차별점 (일반 설문 vs chat-survey)

| 일반 설문 | chat-survey |
|-----------|-------------|
| 선택지 클릭 | 자연어 대화 |
| 고정된 질문 순서 | AI가 맥락에 맞춰 순서 조절 |
| 단문 질문 | 예시·상황 묘사 포함 2~3문장 |
| 모호한 답변 → 스킵 | 모호한 답변 → 더 쉬운 예시로 재안내 |
| 결과 = 원시 데이터 | 결과 = AI 심층 분석 + 맞춤 제안 |
| 이탈률 높음 | 대화형이라 완주율 높음 |
