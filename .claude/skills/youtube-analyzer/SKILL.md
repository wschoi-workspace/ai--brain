---
name: youtube-analyzer
description: YouTube 영상 분석 및 노션 저장. "유튜브 분석", "영상 요약", "YouTube 정리", "유튜브 요약", "영상 분석" 등을 언급하거나 youtube.com 또는 youtu.be URL을 제공하면 자동 실행.
allowed-tools:
  - Bash
  - Read
  - Write
---

# YouTube Analyzer Skill

YouTube 영상의 자막/내용을 추출하고, 상세하게 분석 요약한 뒤 Notion DB에 저장합니다.

## When to Use

- 사용자가 YouTube URL을 제공할 때 (youtube.com, youtu.be)
- "유튜브 분석", "영상 요약", "YouTube 정리" 등을 언급할 때
- "이 영상 정리해줘", "영상 노션에 저장해줘" 등

## Workflow

### Step 1: URL 확인 및 자막 추출

YouTube URL에서 자막과 메타데이터를 추출합니다:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/youtube_transcript.py "YOUTUBE_URL"
```

출력: JSON (metadata + transcript)

**자막이 없는 경우**: 영상 설명(description)과 메타데이터만으로 가능한 범위 내에서 분석합니다. 사용자에게 자막이 없음을 알려주세요.

### Step 2: 내용 분석 및 요약

추출된 자막/내용을 바탕으로 다음을 작성합니다:

#### 2-1. 핵심 요약 (summary)
- 영상의 핵심 내용을 3~5문장으로 요약
- "이 영상은 ~에 대해 다룬다" 식이 아니라, 실제 내용 중심으로

#### 2-2. 주요 인사이트 (insights)
- 영상에서 얻을 수 있는 핵심 인사이트 3~7개
- 각 인사이트는 구체적이고 실행 가능한 형태로
- 원석님의 관심사(마케팅, 비즈니스, 공간기획, 브랜딩) 관점에서 특히 유용한 것 강조

#### 2-3. 실행 아이디어 (actions)
- 이 영상의 내용을 실제 업무에 적용할 수 있는 아이디어 2~5개
- "~하면 좋겠다"가 아니라 "~를 ~에 적용한다" 식의 구체적 액션

#### 2-4. 카테고리 판단
다음 중 가장 적합한 것 선택:
- 마케팅 / 비즈니스 / 브랜딩 / 데이터분석 / 자동화/AI / 공간기획 / 트렌드 / 기타

#### 2-5. 태그 추출
영상 내용에서 핵심 키워드 3~5개를 태그로 추출

### Step 3: 사용자에게 분석 결과 보여주기

분석 결과를 먼저 사용자에게 보여줍니다:

```markdown
## [영상 제목]
**채널**: 채널명 | **길이**: MM:SS

### 핵심 요약
(요약 내용)

### 주요 인사이트
1. ...
2. ...

### 실행 아이디어
1. ...
2. ...

> 카테고리: XX | 태그: #태그1 #태그2
```

### Step 4: Notion DB에 저장

분석 결과를 JSON으로 구성하여 저장합니다:

```bash
export NOTION_TOKEN="$NOTION_TOKEN"
python3 ${CLAUDE_SKILL_DIR}/scripts/notion_save.py '{
  "title": "영상 제목",
  "url": "YouTube URL",
  "channel": "채널명",
  "duration": "MM:SS",
  "date": "YYYY-MM-DD",
  "category": "카테고리",
  "summary": "핵심 요약 (짧은 버전, 2000자 이내)",
  "insights": "주요 인사이트 요약 (2000자 이내)",
  "actions": "실행 아이디어 요약 (2000자 이내)",
  "summary_detail": "상세 요약 (페이지 본문용)",
  "insights_detail": "- 인사이트1\n- 인사이트2",
  "actions_detail": "1. 액션1\n2. 액션2",
  "tags": ["태그1", "태그2"],
  "rating": "★★★★"
}'
```

저장 완료 후 Notion 페이지 URL을 사용자에게 공유합니다.

### Step 5: 유용도 평가

영상의 유용도를 자체 판단하여 기본값으로 설정합니다:
- ★★★★★: 즉시 실행 가능한 구체적 방법론 포함
- ★★★★: 좋은 인사이트가 있으나 일부 추상적
- ★★★: 참고할 만한 내용
- ★★: 일반적인 내용, 새로운 것 적음
- ★: 관련성 낮음

## Error Handling

- **자막 없음**: 메타데이터 + description으로 가능한 범위 분석, 사용자에게 알림
- **비공개 영상**: 접근 불가 안내
- **Notion 저장 실패**: 에러 메시지 표시, 분석 결과는 터미널에서 확인 가능

## Notion DB Info

- DB ID: `32b4703a-5867-81bc-836d-f3a4f76a0c60`
- DB Name: YouTube 영상 요약 DB
