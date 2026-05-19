# Claude 개인 어시스턴트 텔레그램 봇

텔레그램에서 Claude와 직접 대화할 수 있는 개인용 챗봇.

## 셋업

### 1. 텔레그램 봇 생성
1. 텔레그램에서 `@BotFather`에게 `/newbot`
2. 봇 이름/username 설정
3. 발급된 봇 토큰 복사

### 2. 환경 설정
```bash
cp .env.example .env
# .env 파일에 토큰과 API 키 입력
```

### 3. 설치 및 실행
```bash
pip install -r requirements.txt
python bot.py
```

### 4. 사용자 제한 (선택)
1. 봇에서 `/myid` 명령어로 본인 ID 확인
2. `.env`의 `ALLOWED_USER_IDS`에 ID 추가

## 명령어

| 명령어 | 설명 |
|--------|------|
| `/start` | 대화 시작/초기화 |
| `/reset` | 대화 히스토리 초기화 |
| `/myid` | 내 텔레그램 ID 확인 |

## 백그라운드 실행

```bash
nohup python bot.py > bot.log 2>&1 &
```
