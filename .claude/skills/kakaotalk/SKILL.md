---
name: kakaotalk
description: This skill should be used when the user asks to "카톡 보내줘", "카카오톡 메시지", "KakaoTalk message", "채팅 읽어줘", "~에게 메시지 보내줘", or needs to send/read messages via KakaoTalk on macOS.
version: 2.0.0
---

# KakaoTalk CLI

macOS에서 CLI를 통해 카카오톡 메시지를 읽고 보내는 스킬.

## 트리거

- "카카오톡 메시지", "카톡 읽어줘", "~에게 메시지 보내줘"

## 스크립트 구조

| 파일 | 용도 |
|------|------|
| `kakao_read.py` | 채팅방 검색, 열기, 메시지 읽기 |
| `kakao_send.py` | 메시지 발송 |

---

## 메시지 발송 워크플로우

### Step 1: 채팅방 열고 대화 내역 읽기

대상 이름으로 채팅방을 열고 대화 내역을 읽습니다:

```bash
uv run --with atomacos python .claude/skills/kakaotalk/scripts/kakao_read.py "대상이름" --json
```

**출력 예시:** (2026-08-16 실측으로 원본 문서 오류 수정 — 키가 `chat`/`message`이며 `is_me` 포함)
```json
{
  "chat": "구봉",
  "messages": [
    {"sender": "나", "time": "오후 3:24", "message": "오늘 저녁 뭐 먹을까?", "is_me": true},
    {"sender": "구봉", "time": "오후 3:45", "message": "파스타 어때?", "is_me": false}
  ]
}
```

⚠️ 파싱 시 주의: 최상위 키는 `chat_name`이 아니라 **`chat`**, 본문 키는 `text`가 아니라 **`message`**다.
채팅방을 못 찾으면 `{"error": ..., "chat": null, "messages": []}` 형태로 나온다.

**메시지 분석 시 주의:**
- 배열 끝부분이 최신 메시지 (최근일수록 가치 높음)
- 1주일 이상 된 내용은 상황이 바뀌었을 수 있음
- 최근 대화 주제와 자연스럽게 이어지는 메시지 작성

### Step 2: 맥락 파악 후 메시지 작성

읽은 대화 내역을 바탕으로:
1. 최근 대화 흐름 파악
2. 사용자 요청에 맞는 메시지 초안 작성
3. 자연스럽고 맥락에 맞는 내용 구성

### Step 3: 사용자 확인 (필수)

**먼저 텍스트로 메시지 내용을 보여준 후** AskUserQuestion으로 확인:

```
[텍스트 출력]
**최근 대화 요약:**
- {최근 대화 내용 요약}

**보낼 메시지:**
받는 사람: {채팅방}
---
{메시지 내용}

sent with claude code
---

[AskUserQuestion]
질문: "이 메시지를 보낼까요?"
옵션: ["보내기", "수정 필요"]
```

### Step 4: 발송

사용자 확인 후 메시지 발송:

```bash
uv run --with atomacos python .claude/skills/kakaotalk/scripts/kakao_send.py "채팅방이름" "메시지"
```

---

## 메시지 읽기 전용 워크플로우

단순히 대화 내역만 확인할 때:

```bash
uv run --with atomacos python .claude/skills/kakaotalk/scripts/kakao_read.py "대상이름" --json
```

읽은 후 사용자에게 요약 제공:
- 최근 대화 2-3개 요약
- 현재 진행 중인 대화 주제
- 답장이 필요한 내용이 있는지

---

## CLI 옵션 레퍼런스

### kakao_read.py

```bash
# 기본: 채팅방 열고 메시지 읽기
kakao_read.py "채팅방이름" [--limit N] [--json]

# 채팅 목록
kakao_read.py --list [--json]

# 검색
kakao_read.py --search "검색어" [--json]

# 읽고 창 닫기
kakao_read.py "채팅방이름" --close
```

### kakao_send.py

```bash
# 기본 (서명 포함)
kakao_send.py "채팅방" "메시지"
# → "메시지\n\nsent with claude code"

# 서명 없이
kakao_send.py "채팅방" "메시지" --no-signature

# 보내고 창 닫기
kakao_send.py "채팅방" "메시지" --close
```

---

## 예시 시나리오

### "구봉한테 보낼 메시지 제안"

```
[Step 1] 채팅방 열고 읽기
uv run --with atomacos python .../kakao_read.py "구봉" --json

[Step 2] 맥락 파악
최근 대화: 저녁 메뉴 논의 중

[Step 3] 메시지 제안
"파스타 좋아! 오늘 7시에 만날까?"

[Step 4] 사용자 확인 후 발송
```

---

## 요구사항

1. **atomacos**: 별도 설치 불필요 — 모든 명령에 `uv run --with atomacos` 를 붙여 실행한다(uv가 격리 환경에 자동 주입). 워크스페이스 python은 3.9라 직접 import되지 않으므로 이 방식이 정본이다.
2. **Accessibility 권한**: System Settings > Privacy & Security > Accessibility. Claude Code를 구동하는 앱(VS Code/터미널)에 권한이 있어야 한다. `AXIsProcessTrusted()` 로 확인.
3. **카카오톡 실행 + 메인 창 열림**: 앱이 떠 있어도 창이 닫혀 있으면 창 0개로 잡혀 조회가 빈다. 먼저 `open -a KakaoTalk` 로 메인 창을 띄운다.

## 부작용 주의 (실측 기준)

- **클립보드를 덮어쓴다**: 채팅방 검색(`--search`, 안 열린 방 열기)과 모든 발송은 `pbcopy` + Cmd+V 를 쓴다. 사용자가 복사해둔 내용이 날아간다.
- **키 입력이 전역으로 나간다**: 채팅방을 못 찾으면 Cmd+F·방향키·Enter가 엉뚱한 창에 들어갈 수 있다. 발송 전 대상 확인은 생략하지 않는다.
- **이미 열린 창을 쓰면 부작용 없음**: `--list` 와 이미 열려 있는 채팅방 읽기는 AX 트리만 순회하므로 클립보드·키 입력을 건드리지 않는다.
- **기본 서명**: 발송 시 `sent with claude code` 가 자동으로 붙는다. 뺄 때는 `--no-signature`.

## 🔴 대상 오선택 — 가장 큰 위험 (2026-08-16 실측)

닫혀 있는 방을 이름으로 열 때 스크립트는 `Cmd+F` → 검색어 입력 → `↓` → `Enter` 를 누른다.
**이 선택이 빗나가면 전혀 다른 채팅방이 열린다.** 실측에서 `"Choi won seok"` 을 요청했는데
업무 단톡방 `세스크맨슬&렌트&공존` 이 열렸다. 원본 코드에는 열린 방이 맞는지 확인하는 절차가
없어서, 그대로 발송했다면 엉뚱한 단톡방에 메시지가 나갔을 것이다.

**대응 (이 워크스페이스 사본에 적용됨)**: `kakao_send.py` 의 `send_message()` 에 대상 검증을
추가했다. 요청한 이름이 실제 열린 창 제목에 포함되지 않으면 발송을 중단하고 에러를 반환한다.
업스트림 원본에는 없는 로컬 수정이므로, 플러그인을 재설치·업데이트하면 사라진다.

**운용 원칙**:
1. **발송 대상 채팅방은 미리 열어둔 상태에서 실행한다.** 열려 있으면 `find_open_chat` 이
   창 제목으로 직접 잡으므로 검색 자체가 돌지 않아 오선택이 발생하지 않는다.
2. 발송 후에는 `kakao_read.py` 로 해당 방을 다시 읽어 **실제로 그 방에 들어갔는지 확인한다.**
   "발송 성공" 출력만으로 완료 판정하지 않는다.
3. 읽기(`kakao_read.py`)에는 이 검증이 없다. 반환된 `chat` 값이 요청한 이름과 다르면
   **다른 방을 읽은 것이므로 그 내용을 근거로 삼지 않는다.**

## 🟡 읽기의 함정 2종 (2026-08-16 실측)

**1) `--limit` 을 작게 주면 최신 메시지를 놓친다.**
`--limit 5` 로 읽었더니 최신이 "오후 9:51"(전날)로 나왔는데, 같은 방을 `--limit 100` 으로
읽으니 실제 최신은 "오후 3:42"였다. limit이 최신 N개를 주는 것이 아니다.
→ **읽을 때는 기본값(100)을 쓴다. 발송 확인처럼 최신이 중요한 작업에서 작은 limit을 쓰지 않는다.**
이 함정 때문에 실제로 "발송 실패"라고 오판했다가, AX 트리를 직접 확인하고 정정한 사례가 있다.

**2) 카카오톡이 백그라운드면 창이 0개로 보인다.**
앱이 실행 중이고 `AXIsProcessTrusted=True` 여도, 카카오톡이 전면이 아니면 `app.windows()` 가
빈 리스트를 반환한다. 이때 `--list` 는 조용히 0건을 내놓는다(에러가 아니다).
→ **작업 전 반드시 `osascript -e 'tell application "KakaoTalk" to activate'` 로 전면에 올리고
1~2초 기다린다.** 조회 결과가 0건이면 "없다"가 아니라 "창이 안 보인다"를 먼저 의심한다.

## 발송 후 확인 절차 (권장)

```bash
# 1) 전면화
osascript -e 'tell application "KakaoTalk" to activate'
# 2) 발송
uv run --with atomacos python .claude/skills/kakaotalk/scripts/kakao_send.py "방이름" "내용"
# 3) 확인 — limit을 줄이지 말 것
uv run --with atomacos python .claude/skills/kakaotalk/scripts/kakao_read.py "방이름" --json --limit 100
```
`success: true` 는 **키를 눌렀다는 뜻일 뿐 전송 보장이 아니다.** 3)에서 마지막 메시지로
들어갔는지(`is_me=true`, 시각이 현재와 일치) 확인해야 완료다.
