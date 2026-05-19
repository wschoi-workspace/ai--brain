# 기획서 크리틱 파트너 - Telegram Bot

직원이 기획서 초안을 보내면 질문을 통해 사고의 깊이를 높여주는 텔레그램 봇.

## 셋업

### 1. 텔레그램 봇 생성

1. 텔레그램에서 [@BotFather](https://t.me/BotFather)에게 메시지
2. `/newbot` 입력
3. 봇 이름 설정 (예: `기획서 크리틱 파트너`)
4. 봇 username 설정 (예: `proposal_critic_bot`)
5. 발급된 **토큰** 복사

### 2. 환경 설정

```bash
cd 10-projects/12-proposal-critic-bot

# .env 파일 생성
cp .env.example .env

# .env 파일 편집 - 토큰 입력
# TELEGRAM_BOT_TOKEN=위에서_받은_토큰
# ANTHROPIC_API_KEY=Anthropic_API_키
```

### 3. 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 봇 실행
python bot.py
```

## 사용법

| 명령어 | 설명 |
|--------|------|
| `/start` | 봇 시작 및 안내 |
| `/reset` | 대화 초기화 (새 기획서 시작) |
| 텍스트 전송 | 기획서 초안 또는 답변 입력 |
| .txt 파일 전송 | 텍스트 파일로 기획서 공유 |

## 동작 방식

1. 직원이 기획서 초안을 텍스트로 붙여넣기
2. 봇이 WHY(왜 해야 하는가) 질문 2~3개 제시
3. 직원이 답변하면 다음 단계(WHAT/HOW, 통합적 사고)로 진행
4. 기획서가 충분히 다듬어지면 제출 가능 판단

## 배포 (상시 운영)

로컬에서 계속 실행하거나, 서버에 배포할 수 있습니다:

```bash
# 백그라운드 실행 (nohup)
nohup python bot.py &

# 또는 Docker
docker build -t proposal-critic-bot .
docker run -d --env-file .env proposal-critic-bot
```

## 비용 참고

- Claude API: Sonnet 모델 사용, 10명 기준 월 $5~15 수준 예상
- Telegram Bot API: 무료
