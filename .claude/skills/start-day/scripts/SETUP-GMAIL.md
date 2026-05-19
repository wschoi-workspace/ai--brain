# Gmail API 셋업 가이드

## 1. Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 (예: `claude-gmail`)
3. Gmail API 활성화:
   - 좌측 메뉴 > APIs & Services > Library
   - "Gmail API" 검색 > **Enable**

## 2. OAuth 클라이언트 ID 생성

1. APIs & Services > Credentials > **Create Credentials** > **OAuth client ID**
2. 동의 화면 설정 (처음이라면):
   - User Type: **External** 선택
   - 앱 이름: `Claude Gmail` (아무 이름)
   - 이메일: 본인 이메일
   - 스코프: `gmail.readonly` 추가
   - 테스트 사용자: 본인 Gmail 추가
3. OAuth 클라이언트 ID 생성:
   - Application type: **Desktop app**
   - 이름: `Claude Code`
4. **JSON 다운로드** 클릭

## 3. 인증 파일 저장

```bash
# 디렉토리 생성
mkdir -p ~/.config/gmail-claude

# 다운로드한 JSON을 credentials.json으로 저장
mv ~/Downloads/client_secret_*.json ~/.config/gmail-claude/credentials.json
```

## 4. 의존성 설치

```bash
pip install google-auth-oauthlib google-api-python-client
```

## 5. 최초 인증 실행

```bash
cd /path/to/do-better-workspace
python3 .claude/skills/start-day/scripts/gmail_unreplied.py
```

- 브라우저가 열리며 Google 로그인 요청
- 권한 승인 후 `token.json`이 자동 생성됨
- 이후 실행부터는 브라우저 인증 불필요

## 6. 테스트

```bash
python3 .claude/skills/start-day/scripts/gmail_unreplied.py
```

정상 출력 예시:
```json
[
  {"from": "홍길동", "subject": "프로젝트 미팅 일정", "date": "2026-03-28", "days_ago": 1},
  {"from": "김철수", "subject": "견적서 검토 요청", "date": "2026-03-27", "days_ago": 2}
]
```

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| `credentials_missing` 에러 | `~/.config/gmail-claude/credentials.json` 확인 |
| `dependencies_missing` 에러 | `pip install google-auth-oauthlib google-api-python-client` |
| 토큰 만료 에러 | `~/.config/gmail-claude/token.json` 삭제 후 재실행 |
| 403 에러 | Google Cloud Console에서 Gmail API 활성화 확인 |
| 테스트 사용자 에러 | OAuth 동의 화면 > 테스트 사용자에 본인 이메일 추가 |

## 보안 참고

- `credentials.json`과 `token.json`은 `.gitignore`에 추가되어 있음
- 토큰은 `gmail.readonly` 스코프만 가짐 (메일 읽기만 가능, 발송/삭제 불가)
- 토큰은 자동 갱신되며, 갱신 실패 시 브라우저 재인증 필요
