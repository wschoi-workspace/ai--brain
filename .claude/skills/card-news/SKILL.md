# card-news: 카드뉴스 제작 → Buffer Draft 업로드

카드뉴스 HTML 제작, PNG 캡처, Buffer Draft 업로드를 자동화하는 스킬.
"카드뉴스", "card news", "인스타 카드", "카드뉴스 올려", "Buffer 업로드", "카드뉴스 수정" 등을 언급하면 자동 실행.

## 워크플로우

### 1단계: 카드뉴스 HTML 제작/수정
- 카드뉴스 HTML 파일 위치: `10-projects/card-news/`
- 디자인 스타일: 다크 네이비 배경, 블루 포인트(#3182F6), Pretendard 폰트
- 1080×1080 인스타 정사각형
- 파일명 규칙: `topic{N}-{slug}.html`

### 2단계: Playwright PNG 캡처
`/playwright` 스킬을 사용하여 각 카드를 개별 PNG로 캡처.

```
캡처할 HTML: 10-projects/card-news/topic{N}-{slug}.html
출력 위치: 10-projects/card-news/output/
파일명: topic{N}-card-{1,2,3,4}.png
크기: 1080×1080
```

### 3단계: 이미지 호스팅
로컬 PNG를 임시 호스팅 서비스에 업로드하여 URL을 확보.

```bash
# litterbox.catbox.moe (72시간 임시 호스팅)
curl -s -F "reqtype=fileupload" -F "time=72h" \
  -F "fileToUpload=@{파일경로}" \
  https://litterbox.catbox.moe/resources/internals/api.php
```

### 4단계: Buffer API로 Draft 업로드

#### 환경 변수 (`.env`에서 로드)
```
BUFFER_API_TOKEN=<Buffer API 토큰>
BUFFER_CHANNEL_ID=69e44bb9031bfa423c1c71a5
```

#### GraphQL 요청

```bash
curl -s -X POST 'https://api.buffer.com' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $BUFFER_API_TOKEN" \
  -d '{
    "query": "mutation CreatePost($input: CreatePostInput!) { createPost(input: $input) { ... on PostActionSuccess { post { id text dueAt } } ... on MutationError { message } } }",
    "variables": {
      "input": {
        "text": "<캡션 텍스트>",
        "channelId": "<BUFFER_CHANNEL_ID>",
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "saveToDraft": true,
        "metadata": {
          "instagram": {
            "type": "post",
            "shouldShareToFeed": true
          }
        },
        "assets": {
          "images": [
            {"url": "<이미지1_URL>"},
            {"url": "<이미지2_URL>"},
            {"url": "<이미지3_URL>"},
            {"url": "<이미지4_URL>"}
          ]
        }
      }
    }
  }'
```

### 주요 참고사항

- Buffer API는 GraphQL 기반 (`https://api.buffer.com`)
- 이미지는 URL로만 전달 가능 (로컬 파일 직접 업로드 불가)
- `saveToDraft: true` → Buffer Drafts에 저장되어 수정 후 게시 가능
- `saveToDraft: false` + `mode: "addToQueue"` → 바로 큐에 추가
- Instagram은 `metadata.instagram.type` 필수 (`post`, `reel`, `story`, `carousel`)
- Buffer Drafts 확인: `https://publish.buffer.com/channels/{CHANNEL_ID}/drafts`

### Buffer API 유용한 쿼리

```graphql
# 조직 ID 조회
{ account { organizations { id name } } }

# 채널 목록 조회
{ channels(input: { organizationId: "<ORG_ID>" }) { id name service } }
```

## 사용 예시

사용자: "카드뉴스 topic1 수정해서 Buffer에 올려줘"
→ HTML 수정 → Playwright 캡처 → 이미지 호스팅 → Buffer Draft 업로드

사용자: "새 카드뉴스 만들어서 바로 예약해"
→ HTML 생성 → 캡처 → 호스팅 → Buffer 큐에 추가 (saveToDraft: false)
