---
name: telegram
description: 텔레그램 메시지 읽기/보내기/검색. "텔레그램", "Telegram", "메시지 보내", "텔레그램 확인", "TG", "텔레그램 읽어" 등을 언급하면 자동 실행.
allowed-tools: Bash, Read
---

# Telegram Skill

개인 텔레그램 계정 연동 (tgcli 기반)

## Prerequisites

tgcli가 설치 및 인증되어 있어야 합니다:
```bash
tgcli auth status
```

---

## 주요 기능

### 1. 대화 목록 조회

```bash
# 전체 대화 목록
tgcli channels list --limit 20

# 검색
tgcli channels list --query "키워드" --limit 10

# 특정 대화방 상세 정보
tgcli channels show --chat "username_or_id"
```

### 2. 메시지 읽기

```bash
# 최근 메시지 읽기
tgcli messages list --chat "username_or_id" --limit 10

# 날짜 범위 지정
tgcli messages list --chat "username_or_id" --after "2026-03-28" --before "2026-03-30" --limit 20

# 특정 메시지 상세 보기
tgcli messages show --chat "username_or_id" --id 12345

# 메시지 전후 맥락 보기
tgcli messages context --chat "username_or_id" --id 12345 --before 5 --after 5
```

### 3. 메시지 검색

```bash
# 키워드 검색
tgcli messages search "검색어" --limit 10

# 특정 대화방에서 검색
tgcli messages search "검색어" --chat "username_or_id" --limit 10

# 정규식 검색
tgcli messages search --regex "패턴" --chat "username_or_id"

# 태그로 검색
tgcli messages search --tag "태그명" --limit 10
```

### 4. 메시지 보내기

```bash
# 텍스트 메시지 전송
tgcli send text --to "username_or_id" --message "안녕하세요"

# 파일 전송
tgcli send file --to "username_or_id" --file "/path/to/file" --caption "파일 설명"
```

### 5. 그룹 관리

```bash
# 그룹 목록
tgcli groups list --limit 10

# 그룹 정보
tgcli groups info --chat "group_username_or_id"

# 그룹 멤버 추가
tgcli groups members add --chat "group_id" --user "user_id"
```

### 6. 연락처 검색

```bash
# 연락처 검색
tgcli contacts search "이름" --limit 10

# 연락처 상세 정보
tgcli contacts show --user "user_id"
```

### 7. 미디어 다운로드

```bash
# 메시지의 미디어 파일 다운로드
tgcli media download --chat "username_or_id" --id 12345 --output "/path/to/save"
```

### 8. 포럼 토픽

```bash
# 토픽 목록
tgcli topics list --chat "username_or_id" --limit 10

# 토픽 검색
tgcli topics search --chat "username_or_id" --query "키워드"
```

---

## 글로벌 옵션

모든 명령에 사용 가능:

| 옵션 | 설명 |
|------|------|
| `--json` | JSON 형식 출력 (파싱 용이) |
| `--timeout <시간>` | 타임아웃 설정 (예: `30s`, `5m`) |

---

## CLI 명령어 요약

| 명령어 | 설명 |
|--------|------|
| `channels list` | 대화 목록 조회 |
| `channels show` | 대화방 상세 정보 |
| `messages list` | 메시지 목록 |
| `messages search` | 메시지 검색 |
| `messages show` | 메시지 상세 보기 |
| `messages context` | 메시지 전후 맥락 |
| `send text` | 텍스트 전송 |
| `send file` | 파일 전송 |
| `groups list` | 그룹 목록 |
| `groups info` | 그룹 정보 |
| `contacts search` | 연락처 검색 |
| `media download` | 미디어 다운로드 |
| `topics list` | 토픽 목록 |
| `tags set/list/search` | 채널 태그 관리 |

---

## 사용 팁

- `--json` 플래그를 붙이면 프로그래밍적으로 파싱하기 쉬운 JSON 출력
- `--chat`에는 username(@없이) 또는 숫자 ID 모두 사용 가능
- 메시지 전송 시 상대방의 username 또는 대화방 ID 필요
- `tgcli doctor --connect`로 연결 상태 진단 가능

---

## 보안

- 인증 세션은 로컬에 저장됨
- API 자격증명(api_id, api_hash)은 tgcli config에 저장
- 민감한 메시지 내용은 로그나 파일에 저장하지 않도록 주의

---

## Version History

- **v1.0.0 (2026-03-29)**: 초기 작성 - tgcli 기반 텔레그램 연동
