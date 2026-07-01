# ARISA 전체 → 맥미니 이관 마스터 가이드

> **맥미니에서 새 Claude Code 세션을 열고, 이 문서를 따라 진행**한다.
> 목표: 노트북(macbookair)에서 돌던 ARISA 전체(14 서비스·2 코드베이스)를 맥미니(server-mini-macmini)로 옮겨 상시가동.
> 작성: 2026-07-01 (노트북 세션에서 인벤토리 기반 작성)

## ⚠️ 최우선 주의 3가지
1. **텔레그램 polling 충돌**: 같은 봇 토큰은 한 기기에서만 polling 가능. 맥미니에서 봇 켜기 **전에 노트북 봇을 전부 꺼야** 함(Phase 5). 안 그러면 409 충돌로 한쪽이 죽음.
2. **맥미니 사용자명**: 아래 모든 경로는 `/Users/choi_ai` 기준. 맥미니 홈이 다르면(`whoami`로 확인) plist·run.sh·.env 참조 경로를 전부 치환해야 함. **같으면 무치환**.
3. **비밀·데이터는 git에 없음**: `.env`, `~/.mem0*`, 일부 json은 AirDrop 등으로 별도 전송(Phase 2).

## 인벤토리 (이관 대상)

### 코드베이스 2개 (git clone)
| repo | 원격 | 로컬 경로 |
|---|---|---|
| do-better-workspace | github.com/wschoi-workspace/**ai--brain**.git | `~/do-better-workspace` |
| arisa-project-memory | github.com/wschoi-workspace/**arisa-project-memory**.git | `~/arisa-project-memory` |

### 서비스 14개 (plist: `~/Library/LaunchAgents/`)
**do-better-workspace 계열 (.venv311 = uv/Python3.11, 또는 `/usr/bin/python3`)**
| plist | 스크립트 | 스케줄 |
|---|---|---|
| com.projectrent.dashboard | 02-scripts/dashboard-server.py | KeepAlive (8770) · `/usr/bin/python3` (표준lib) |
| com.projectrent.daily-brief | 02-scripts/daily-brief-aggregate.py | 07:30 |
| com.projectrent.weekly-report | 02-scripts/weekly-report-aggregate.py | 월 08:30 |
| com.projectrent.daily-checkin | 02-scripts/daily-report-checkin.py | 22:00 |
| com.arisa.daily-report-bot | 02-scripts/daily-report-bot.py | KeepAlive |
| com.arisa.daily-report-bot-restart | (kickstart) | 04:00 |
| com.arisa.second-brain | 24-second-brain/run.sh → bot.py | KeepAlive |
| com.basket.ops-bot | 02-scripts/basket-ops-bot.py | KeepAlive |
| com.basket.weekly-insight | 02-scripts/basket-weekly-insight.py | 월 09:? |
| com.basket.onboarding | (basket) | 화·수 09:00 |
| com.arisa.caffeinate | /usr/bin/caffeinate | **맥미니는 불필요(데스크탑) → 제외** |

**arisa-project-memory 계열 (.venv = Python3.9)**
| plist | 스크립트 | |
|---|---|---|
| com.arisa.telegram-bot | scripts/telegram_bot.py | KeepAlive (회의록 봇) |
| com.arisa.watcher | scripts/watcher.py | KeepAlive |
| com.arisa.zero-server | (zero-server) | KeepAlive |

### 비밀·데이터 (git 미포함 → AirDrop 전송)
- `~/do-better-workspace/.env` (16 keys), `~/arisa-project-memory/.env` (7 keys)
- `~/.mem0/` , `~/.mem0-employees/` (mem0 벡터 데이터 — qdrant local)
- `~/do-better-workspace/00-system/02-scripts/.basket-chats.json`
- `~/do-better-workspace/10-projects/28-ai-education-ax/newsletter/recipients.json`
- `~/do-better-workspace/00-system/01-templates/_data/users.json` (대시보드 계정·PIN — git 여부 확인, 없으면 전송)

### 런타임 도구
- **uv** (`~/.local/bin/uv`) — venv311 관리
- **node/npm** (gws CLI: `npm i -g @google-workspace/...` → `~/.npm-global/bin/gws`, **oauth 재인증 필요**)
- **cloudflared** (`~/.local/bin/cloudflared` 2026.6.1)
- venv311 핵심 패키지: `openai==2.43.0 python-telegram-bot mem0ai==2.0.7 qdrant-client==1.18.0 httpx==0.28.1 python-dotenv`

---

## Phase 0 — 맥미니 준비
```bash
whoami                      # 홈 경로 확인 (choi_ai 아니면 이하 경로 전부 치환)
# 도구 설치 (없으면)
xcode-select --install 2>/dev/null   # git 등
curl -LsSf https://astral.sh/uv/install.sh | sh   # uv
# node: brew 또는 nodejs.org, 그 후 npm prefix ~/.npm-global 설정
# cloudflared: GitHub release arm64 (노트북과 동일 방식)
```
- Tailscale 로그인 확인 (`tailscale status`에서 online). 유선 이더넷 권장.

## Phase 1 — 코드 clone
```bash
cd ~
git clone https://github.com/wschoi-workspace/ai--brain.git do-better-workspace
git clone https://github.com/wschoi-workspace/arisa-project-memory.git arisa-project-memory
```

## Phase 2 — 비밀·데이터 전송 (노트북 → 맥미니, AirDrop)
노트북에서 아래를 AirDrop/USB로 맥미니 같은 경로에 복사:
- `~/do-better-workspace/.env`, `~/arisa-project-memory/.env`
- `~/.mem0/`, `~/.mem0-employees/` (폴더째)
- `.basket-chats.json`, `recipients.json`, `users.json` (git에 없으면)

## Phase 3 — 환경 구성
```bash
# venv311 (uv)
cd ~/do-better-workspace/20-operations/24-second-brain
uv venv .venv311 --python 3.11
uv pip install --python .venv311/bin/python openai python-telegram-bot mem0ai==2.0.7 qdrant-client==1.18.0 httpx python-dotenv
# arisa-project-memory venv (3.9 계열 — requirements-arisa.txt 사용)
cd ~/arisa-project-memory && python3 -m venv .venv && .venv/bin/pip install -r <(...)  # repo의 requirements
# gws CLI
npm config set prefix ~/.npm-global && npm i -g <gws패키지> && gws login   # oauth 브라우저 재인증
```
> venv311 정확한 패키지는 노트북 `~/do-better-workspace/00-system/02-scripts/migration/requirements-venv311.txt` 참조(비었으면 site-packages 기준 위 목록).

## Phase 4 — plist 복사 + 등록
```bash
# 노트북에서 plist 14개 AirDrop → 맥미니 ~/Library/LaunchAgents/
# 사용자명 다르면 경로 치환: sed -i '' 's#/Users/choi_ai#/Users/<맥미니>#g' *.plist
# caffeinate 제외. 각 서비스 bootstrap:
for p in ~/Library/LaunchAgents/com.projectrent.*.plist ~/Library/LaunchAgents/com.arisa.*.plist ~/Library/LaunchAgents/com.basket.*.plist; do
  launchctl bootstrap gui/$(id -u) "$p"
done
```

## Phase 5 — 봇 전환 (⚠️ polling 충돌 방지 — 핵심)
**순서 엄수**: ① 노트북에서 전 봇 끄기 → ② 맥미니에서 켜기
```bash
# [노트북에서 실행] 텔레그램 polling 봇 전부 정지
for s in com.arisa.daily-report-bot com.arisa.second-brain com.basket.ops-bot com.arisa.telegram-bot com.arisa.watcher; do
  launchctl bootout gui/$(id -u)/$s 2>/dev/null
done
pkill -9 -f 'daily-report-bot.py|bot.py|basket-ops-bot.py|telegram_bot.py'
# [맥미니에서] Phase 4의 bootstrap이 봇 기동 → getMe/deleteWebhook 로그 확인, 409 없어야
```

## Phase 6 — cloudflared 터널 + 고정 URL
- 새 도메인 확보 시 named tunnel(별도 `cloudflare-migration-checklist.md`). 임시론 quick tunnel.
- `.env`에 `DASHBOARD_BASE_URL=https://<고정도메인>` → 코드 무수정 반영.

## Phase 7 — 검증
- `launchctl list | grep -E 'projectrent|arisa|basket'` 전부 로드
- `curl 127.0.0.1:8770/api/health` → `{"ok":true}`
- 텔레그램 각 봇에 `/report` 등 테스트 (409 없음 = polling 단일)
- daily-brief 수동 1회 `--no-telegram` → 팀 파일 생성
- gws 시트 읽기 동작(oauth)

## 롤백
- 맥미니 봇에 문제 시: 맥미니 bootout → 노트북에서 다시 bootstrap(코드/데이터 노트북에 그대로 남아있음). 데이터(.mem0)는 양쪽 복사본이라 안전.

---
## 미해결/확인 필요
- 맥미니 사용자명(경로 치환 여부) · gws 재인증 · users.json git 포함 여부 · basket-onboarding/zero-server 스크립트 경로(plist에서 확인) · arisa venv 정확한 requirements(repo 내 requirements.txt 확인)
