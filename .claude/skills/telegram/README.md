# Telegram Skill

텔레그램 개인 계정을 Claude Code에서 사용할 수 있게 연동합니다.

## 설정 가이드

### 1. tgcli 설치

```bash
npm install -g @kfastov/tgcli
```

### 2. Telegram API 자격증명 발급

1. https://my.telegram.org 접속
2. 전화번호 입력 → 텔레그램 앱으로 온 인증코드 입력
3. **API development tools** 클릭
4. 앱 생성 (App title: 아무거나, Platform: Other)
5. `api_id` (숫자)와 `api_hash` (문자열) 복사

### 3. tgcli 인증

터미널에서 직접 실행 (인터랙티브):

```bash
tgcli auth
```

순서대로 입력:
1. api_id
2. api_hash
3. 전화번호 (+82...)
4. 텔레그램 앱에서 받은 인증코드

### 4. 동작 확인

```bash
tgcli auth status
tgcli channels list --limit 5
```

---

## 사용 예시

Claude Code에서 자연어로 요청:

- "텔레그램에서 홍길동한테 온 메시지 확인해줘"
- "텔레그램으로 '회의 10분 늦습니다' 보내줘"
- "텔레그램에서 '프로젝트' 키워드로 검색해줘"
- "텔레그램 그룹 목록 보여줘"

---

## 트러블슈팅

### tgcli 명령어를 찾을 수 없음
```bash
# npm 글로벌 bin 경로 확인
npm bin -g
# PATH에 추가 필요할 수 있음
export PATH="$PATH:$(npm bin -g)"
```

### 인증 만료
```bash
tgcli auth status  # 상태 확인
tgcli auth         # 재인증
```

### 연결 문제 진단
```bash
tgcli doctor --connect
```

---

## 기술 스택

- **CLI 도구**: [@kfastov/tgcli](https://www.npmjs.com/package/@kfastov/tgcli) v2.0.8
- **프로토콜**: Telegram TDLib (개인 계정 API)
- **인증**: 전화번호 기반 세션 인증
