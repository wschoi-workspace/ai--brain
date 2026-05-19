---
name: gemini
description: Gemini AI와 대화하고 피드백 받기. "제미나이", "Gemini", "gemini한테 물어봐", "제미나이 피드백", "Gemini 리뷰", "제미나이 대화 가져와" 등을 언급하면 자동 실행.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Gemini Integration Skill

Gemini API를 통해 대화하고, 기존 Gemini 대화를 가져와서 Claude와 함께 논의합니다.

## When to Use

- "제미나이한테 물어봐", "Gemini 피드백 받아줘"
- "제미나이 대화 가져와", "Gemini이랑 한 이야기 리뷰해줘"
- "이거 Gemini한테 보내줘", "제미나이 의견도 들어보자"

## 모드

### 모드 1: Chat - Gemini에게 직접 질문

사용자가 Gemini에게 직접 질문하고 싶을 때:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/gemini_chat.py chat "질문 내용"
```

**흐름:**
1. 사용자 프롬프트를 Gemini API로 전송
2. 응답을 `50-resources/gemini-feedback/` 에 자동 저장
3. Gemini 응답을 사용자에게 보여줌
4. 사용자와 함께 Gemini 답변에 대해 논의

### 모드 2: Review - 파일을 Gemini에게 보내서 피드백 받기

기획서, 문서 등을 Gemini에게 보내서 피드백을 받고 싶을 때:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/gemini_chat.py review "파일경로" "추가 요청사항(선택)"
```

**흐름:**
1. 파일 내용을 Gemini API로 전송
2. Gemini 피드백을 `50-resources/gemini-feedback/` 에 저장
3. Gemini 피드백을 사용자에게 보여줌
4. Claude 관점의 추가 의견을 덧붙임
5. 사용자와 3자 토론 (사용자 + Claude + Gemini 피드백)

### 모드 3: Conversation - 기존 Gemini 대화 가져오기

Gemini 웹에서 한 대화를 가져와서 이어서 논의할 때:

**사전 준비:** 사용자에게 Gemini 대화 내용을 복사해서 파일로 저장하도록 안내

```
Gemini 대화 내용을 복사해서 파일로 저장해주세요.
저장 위치 예시: 50-resources/gemini-feedback/gemini-conversation-원본.md
```

저장된 파일을 읽어서 논의:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/gemini_chat.py conversation "파일경로" "논의하고 싶은 포인트(선택)"
```

**흐름:**
1. 기존 대화 파일 읽기
2. 대화 내용을 사용자에게 요약해서 보여줌
3. Claude 관점에서 Gemini 답변에 대한 분석/보완 의견 제시
4. 사용자와 함께 심화 논의

## Workflow

### Step 1: 모드 판단

사용자의 요청을 분석하여 모드를 결정:
- "제미나이한테 물어봐", "Gemini 의견" → **chat**
- "이 파일 Gemini한테 보여줘", "제미나이 피드백" + 파일 → **review**
- "제미나이 대화 가져와", "이전 Gemini 대화" → **conversation**

### Step 2: 실행

해당 모드의 스크립트를 실행합니다.

### Step 3: 결과 공유 및 논의

Gemini 응답을 사용자에게 보여준 뒤, Claude 관점의 분석을 추가합니다:

```markdown
## Gemini 응답
(Gemini 답변 내용)

## Claude 분석
(Gemini 답변에 대한 보완/다른 관점/추가 인사이트)

## 논의 포인트
- 어떤 부분이 더 궁금하신가요?
- Gemini 의견 중 특히 공감되는 부분이 있나요?
```

## 저장 위치

모든 Gemini 응답은 `50-resources/gemini-feedback/` 에 자동 저장됩니다:
- `gemini-chat-YYYYMMDD-HHMMSS.md`
- `gemini-review-YYYYMMDD-HHMMSS.md`

## Error Handling

- **API 키 없음**: `.env` 파일 확인 안내
- **파일 없음**: 올바른 파일 경로 안내
- **API 에러**: 에러 메시지 표시, 재시도 안내
