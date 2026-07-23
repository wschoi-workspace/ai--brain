---
name: 퇴사처리
description: 퇴사자의 아리사 시스템 접근을 즉시 차단한다. "/퇴사처리 이름", "OO 퇴사했어", "OO 계정 차단해줘" 트리거. 명부 제거→맥미니 동기화→봇 차단→차단 검증까지 원샷.
---

# /퇴사처리 — 아리사 접근 즉시 차단

퇴사자 1명의 아리사 생태계 접근을 한 번에 끊는다. 실행부는 `00-system/02-scripts/offboard-employee.py`.

## 차단 원리 (수정하지 말 것)

- 아리사 OS(arisa-os.com)는 **매 요청마다 users.json을 재검증**한다 — users.json에서 이름이 빠지면 이미 발급된 30일 쿠키 세션·PIN 인증·재로그인이 그 즉시 전부 죽는다. 대시보드 재시작 불필요.
- 텔레그램 봇(일일보고·Basket)은 `offboarded.json` 목록을 매 메시지 확인해 거부한다. 명부(by_telegram_id) 제거만으로는 이름 자유 입력 경로가 남기 때문에 이 목록이 최종 차단선이다.

## 절차

### 1. dry-run으로 제거 대상 확인 (필수)

```bash
python3 00-system/02-scripts/offboard-employee.py 이름 --dry-run
```

출력(users.json/by_name/by_telegram_id/리더 여부)을 사용자에게 보여주고 **반드시 실행 확인을 받는다** — 파괴적 작업이며 이름 오타로 재직자를 차단할 수 있다.

### 2. 본 실행

```bash
python3 00-system/02-scripts/offboard-employee.py 이름
```

스크립트가 자동으로: 백업 생성(`_data/offboard-backups/`) → 로컬 명부 3파일 수정 → 맥미니 scp 3파일 → daily-report-bot 재시작 → arisa-os.com 로그인 차단 검증(401 확인).

### 3. 결과 보고

차단 검증 결과(✅/❌)와 백업 경로를 보고한다. 검증 ❌면 맥미니 users.json을 직접 확인한다.

### 4. 수동 체크리스트 안내 (스크립트 범위 밖 — 항상 함께 출력)

- [ ] **HR 포털**(rent-hr-portal.fly.dev) 계정 비활성 — 별도 시스템, admin 화면에서 처리
- [ ] **구글 워크스페이스** 계정 정지/이관 (Gmail·드라이브)
- [ ] 노션·Buffer 등 SaaS 초대 회수
- [ ] 사무실 와이파이 비번 교체·출입 권한 회수 (필요 시)
- [ ] 팀 리더였다면 `arisa-employees.json`의 `team_leads` 승계 지정 (스크립트가 ⚠️ 경고 출력)
- [ ] Basket 봇을 쓰던 직원이면 로컬 basket-ops-bot 재시작 (`launchctl` 로컬)

## 복구 (오처리 시)

`_data/offboard-backups/{ts}-{이름}/`의 users.json·arisa-employees.json·offboarded.json을 원위치로 복사한 뒤, 맥미니로 동일하게 scp + daily-report-bot 재시작.

## 주의

- 스크립트의 프로덕션 검증은 브라우저 UA를 쓴다 (Cloudflare가 python-urllib UA를 403 처리).
- 퇴사자의 과거 보고·회의록·프로젝트 이력은 지우지 않는다 — 접근만 차단(이력은 회사 자산).
- **users.json SSOT는 맥미니**(`~/dev/arisa2/data/users.json` 심링크, 리스트 스키마·실PIN). 로컬 users.json은 테스트 사본이므로 **절대 scp로 밀지 말 것** — 스크립트는 맥미니 파일에서 이름만 원격 제거한다(2026-07-23 덮어쓰기 사고 재발 방지). SSOT 복원 소스: arisa2 git `12096b7`(명단·역할·팀) + `data/initial_credentials.txt`(초기 PIN).
