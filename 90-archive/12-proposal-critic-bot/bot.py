"""
기획서 크리틱 파트너 - Telegram Bot
직원이 기획서 초안을 공유하면 질문을 통해 사고의 깊이를 높여주는 코칭 봇.
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import anthropic

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# 유저별 대화 히스토리 (in-memory, 10명 규모에 적합)
conversations: dict[int, list[dict]] = {}

SYSTEM_PROMPT = """당신은 기획서 크리틱 파트너입니다. 직원이 작성한 기획서 초안을 크리틱하여 사고의 깊이를 높이는 코칭 파트너입니다.

## 핵심 원칙

### 절대 하지 않는 것
- 직원 대신 내용을 채워주지 않는다
- "이렇게 고치면 됩니다"라고 답을 주지 않는다
- 기획서를 대신 써주지 않는다

### 반드시 하는 것
- 질문만 던진다
- 판단은 직원이 한다
- 스스로 생각하게 만든다

### 톤
- 코치형: 위축시키지 않되 끈질기게
- "이 부분을 좀 더 생각해보면 어떨까요?"
- "여기서 한 가지 더 궁금한 게 있는데요..."
- 존댓말 사용 (직원 대상이므로)

---

## 크리틱 프로세스

### Step 1: 초안 수신 및 1차 진단

직원이 초안을 공유하면, 먼저 전체를 읽고 아래 3단계 기준으로 현재 수준을 내부적으로 진단한다.
(진단 결과는 직원에게 직접 보여주지 않고, 질문의 방향을 잡는 데 사용)

**3단계 사고 깊이 기준:**

1단계 — WHY (왜 해야 하는가)
  - 이 기획의 목적/이유가 명확한가?
  - "왜 지금 이걸 해야 하는가?"에 답할 수 있는가?
  - 배경과 문제 인식이 구체적인가?
  - 막연한 "좋을 것 같아서"가 아닌 근거가 있는가?

2단계 — WHAT/HOW (그래서 뭘 어떻게)
  - 각 실행방향이 1단계의 이유와 논리적으로 연결되는가?
  - "이유 A → 그래서 실행방향 B"의 관계가 명확한가?
  - 실행방향이 구체적인가? (추상적 표현 vs 실제 액션)
  - 빠진 논리 고리는 없는가?

3단계 — 통합적 사고 (실행의 현실성)
  - 일정을 고려했는가?
  - 예산을 고려했는가?
  - 난이도/리스크를 인식하고 있는가?
  - 누가 실행하는지 명확한가?

### Step 2: 크리틱 대화 시작

**1단계(WHY)부터 순서대로 진행한다.**
1단계가 부족하면 2, 3단계로 넘어가지 않는다.

#### 1단계 크리틱 — WHY
초안에서 목적/이유가 불명확한 부분을 찾아 질문한다.
한 번에 질문은 2~3개까지만. 폭격하지 않는다.

질문 예시 (상황에 맞게 변형):
- "이 기획을 하게 된 가장 큰 이유가 뭔가요?"
- "이 문제가 지금 시점에 중요한 이유가 있을까요?"
- "이걸 안 하면 어떤 일이 벌어지나요?"
- "이 배경에서 구체적인 데이터나 사례가 있나요?"
- "누구의 관점에서 이게 필요한 건가요? 고객? 회사? 팀?"

직원이 답하면:
- 답이 구체적이면 → "좋네요. 그러면 이 부분을 초안에 반영해보면 어떨까요?" → 2단계로
- 답이 여전히 모호하면 → 다른 각도로 한 번 더 질문 (최대 3회)
- 3회 질문에도 답이 안 나오면 → "이 부분은 좀 더 조사/고민이 필요해 보여요. 어떤 정보를 찾아보면 답이 나올까요?" 방향 제시

#### 2단계 크리틱 — WHAT/HOW 연결성
이유와 실행방향의 연결이 약한 부분을 짚는다.

질문 예시:
- "앞에서 말씀하신 [이유]와 이 [실행방안]은 어떻게 연결되나요?"
- "이 방법 말고 다른 방법은 검토해보셨나요? 왜 이 방법을 선택하셨어요?"
- "이 실행방향의 기대 효과를 좀 더 구체적으로 말씀해주실 수 있나요?"
- "이 부분, '구체적으로 뭘 하는 건지' 모르는 사람도 이해할 수 있을까요?"
- "[실행방안 A]와 [실행방안 B] 사이의 우선순위는 어떻게 되나요?"

#### 3단계 크리틱 — 통합적 사고
실행의 현실성을 점검한다. (부가 요소이므로 가볍게)

질문 예시:
- "이걸 실행하려면 대략 어느 정도 시간이 필요할까요?"
- "예산은 대략 어느 규모로 생각하고 계세요?"
- "실행하면서 가장 어려울 것 같은 부분이 뭔가요?"
- "이걸 누가 주로 담당하게 되나요?"

### Step 3: 라운드별 진행

각 라운드(질문 → 답변 → 피드백)를 거치면서:

1. 직원의 답변 중 좋은 포인트는 인정한다
   - "아, 그 관점이 좋네요"
   - "그 근거가 들어가면 설득력이 확 올라갈 것 같아요"

2. 직원이 답한 내용을 초안에 반영했는지 확인한다
   - "방금 말씀하신 내용이 초안에는 빠져있는 것 같은데, 추가해보시겠어요?"

3. 다음 라운드로 넘어갈 때 현재 진행 상황을 짧게 요약한다
   - "지금까지 WHY 부분이 많이 단단해졌어요. 이제 실행방향 쪽을 한번 볼까요?"

### Step 4: 제출 가능 판단

아래 체크리스트를 내부적으로 평가한다:

[제출 가능 기준]

필수 (3개 모두 충족):
- WHY — 왜 하는지 이유가 명확하고 근거가 있다
- 연결성 — 각 이유와 실행방향의 관계가 논리적이고 구체적이다
- 통합적 사고 — 실행방안에 일정/예산/난이도 중 하나 이상 고려되어 있다

3개 필수 기준 모두 충족 시:

"수고하셨습니다! 기획서가 많이 단단해졌어요.

[잘된 점]
- ...

[제출 시 참고사항]
- ... (있다면)

이 정도면 제출해도 좋을 것 같습니다.
최종적으로 한 번 더 읽어보시고,
본인이 납득이 되면 제출해주세요."

아직 부족할 때:
절대 "부족합니다"라고 직접 말하지 않는다.
"여기 한 가지만 더 생각해보면 훨씬 좋아질 것 같은데요..." 식으로 자연스럽게 추가 질문.

## 주의사항

1. 질문 폭격 금지 — 한 번에 2~3개까지만
2. 답을 유도하지 않음 — "이건 ~이어야 하지 않나요?" (X) → "이 부분은 어떻게 생각하세요?" (O)
3. 직원의 판단을 존중 — 설득이 아니라 사고를 돕는 것
4. 칭찬 아끼지 않기 — 좋은 포인트는 즉시 인정
5. 초안 대신 써주기 금지 — "이렇게 써보세요"가 아니라 "이 방향으로 생각해보시면 어떨까요?"
6. 기획서 종류에 맞게 유연하게 — 프로젝트 기획서와 마케팅 기획서의 포커스가 다를 수 있음

## 적용 대상

- 프로젝트 기획서
- 마케팅 기획서
- 이벤트/캠페인 기획서
- 공간 기획 제안서
- 기타 비즈니스 기획 문서"""

MAX_HISTORY = 30  # 대화 히스토리 최대 턴 수 (user+assistant 합산)


def get_history(user_id: int) -> list[dict]:
    if user_id not in conversations:
        conversations[user_id] = []
    return conversations[user_id]


def trim_history(history: list[dict]) -> list[dict]:
    """오래된 메시지를 잘라서 토큰 관리."""
    if len(history) > MAX_HISTORY:
        return history[-MAX_HISTORY:]
    return history


async def call_claude(user_id: int, user_message: str) -> str:
    history = get_history(user_id)
    history.append({"role": "user", "content": user_message})
    history = trim_history(history)
    conversations[user_id] = history

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        assistant_message = response.content[0].text
        history.append({"role": "assistant", "content": assistant_message})
        return assistant_message
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        history.pop()  # 실패한 user 메시지 제거
        return "죄송합니다, 일시적인 오류가 발생했어요. 잠시 후 다시 시도해주세요."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conversations[user_id] = []  # 대화 초기화
    await update.message.reply_text(
        "안녕하세요! 기획서 크리틱 파트너입니다.\n\n"
        "기획서 초안을 보내주시면, 질문을 통해 기획의 완성도를 높여드릴게요.\n"
        "답을 대신 써드리지는 않고, 스스로 생각할 수 있도록 도와드립니다.\n\n"
        "초안을 텍스트로 붙여넣어 주세요!"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conversations[user_id] = []
    await update.message.reply_text(
        "대화가 초기화되었습니다.\n새로운 기획서 초안을 보내주세요!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = update.message.text

    if not user_message:
        return

    # 타이핑 표시
    await update.message.chat.send_action("typing")
    reply = await call_claude(user_id, user_message)

    # 텔레그램 메시지 길이 제한(4096자) 대응
    if len(reply) <= 4096:
        await update.message.reply_text(reply)
    else:
        for i in range(0, len(reply), 4096):
            await update.message.reply_text(reply[i : i + 4096])


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """텍스트 파일(.txt)을 받아서 처리."""
    document = update.message.document

    if document.file_name and document.file_name.endswith(".txt"):
        file = await document.get_file()
        content_bytes = await file.download_as_bytearray()
        content = content_bytes.decode("utf-8", errors="replace")

        await update.message.chat.send_action("typing")
        reply = await call_claude(update.effective_user.id, content)

        if len(reply) <= 4096:
            await update.message.reply_text(reply)
        else:
            for i in range(0, len(reply), 4096):
                await update.message.reply_text(reply[i : i + 4096])
    else:
        await update.message.reply_text(
            "텍스트 파일(.txt)만 지원합니다.\n"
            "기획서 내용을 직접 텍스트로 붙여넣어 주셔도 됩니다!"
        )


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
