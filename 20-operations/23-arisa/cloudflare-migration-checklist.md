# ARISA 대시보드 고정 URL — named tunnel 설정 가이드 ✅ 구축 완료 (2026-07-08)

> **결과: `https://arisa.projectrent.co.kr`** — tunnel `arisa`(UUID 312c7f9f-d19e-43d3-a041-ff8921059d22) → 맥미니 :8780, launchd com.cloudflared.arisa 상시가동. 존 Active 전환만 대기. 상세 이력은 23-progress.md 참조. 아래는 구축 당시 가이드 원문.

> 목적: 리더 대시보드를 `arisa.<새도메인>` **고정 URL**로 영구 노출(통신사 DNS·임시 URL 문제 해결).
> 방향(2026-07-08 확정): **새 전용 도메인 + named tunnel을 맥미니에서 상시가동**. 대표님이 named tunnel 방식 채택 확정.
> ✅ project-rent.com은 **건드리지 않음** → 이메일(GWS)·홈페이지 100% 무영향.

## 배경 (2026-07-08 장애 확인)
- 구 quick tunnel URL(crossword-….trycloudflare.com) **사망** — cloudflared 프로세스 없음, 응답 000
- 리더들이 받은 팀 Brief 텔레그램 링크가 전부 미작동 → "보고 공유 안 됨" 인식의 원인 중 하나
- 리더 3인(전제훈·배성원·윤혜정)은 tailnet 밖(기기: 맥미니·대표 iPhone·대표 MacBook Air뿐) → ts.net URL 불가
- 잠정 조치: 맥미니 `.env`에 `DASHBOARD_BASE_URL=https://server-mini-macmini.tail7739de.ts.net` (대표 기기만 열림)

## 1단계: 도메인 준비 — **projectrent.co.kr 사용 확정** (2026-07-08, 대표님 액션) ⏳
> ⚠️ **긴급**: projectrent.co.kr(최원석 명의, 가비아, 2021 등록)이 **2026-07-07 만료 → 사용 정지** 상태.
> 만료 30일 내(~08-06) 미갱신 시 말소. 현재 NS/A/MX 레코드 없음 → 메일 등 기존 서비스 영향 0 (터널용으로 안전).
1. **가비아(gabia.com) 로그인 → projectrent.co.kr 갱신(연장)** — 계정 메일 추정: insightprobe@gmail.com
2. [dash.cloudflare.com](https://dash.cloudflare.com) 가입 → Add a site → `projectrent.co.kr` → Free 플랜 → Cloudflare가 지정하는 네임서버 2개 확인 (.co.kr은 Registrar 직구매만 불가, 존 등록은 가능)
3. 가비아 도메인 관리에서 네임서버를 그 2개로 변경 → Cloudflare에서 zone Active 될 때까지 대기(수분~수시간)
4. 완료되면 알려주기 → 아래 2단계는 Claude가 진행 (호스트네임: `arisa.projectrent.co.kr`)

## 2단계: named tunnel 설정 (도메인 준비 후 — 맥미니에서 진행)
0. cloudflared 설치: `brew` 없음 → GitHub releases `cloudflared-darwin-arm64.tgz` → `~/.local/bin/` (⚠️ 설치 실행에 사용자 권한 승인 필요)
1. `~/.local/bin/cloudflared tunnel login` → 출력된 URL을 대표가 브라우저에서 열어 새 도메인 zone 선택·인증 (cert.pem 생성)
2. `cloudflared tunnel create arisa` → 터널 UUID + `~/.cloudflared/<UUID>.json` 생성
3. `cloudflared tunnel route dns arisa arisa.<도메인>` → Cloudflare zone에 CNAME 자동 생성
4. `~/.cloudflared/config.yml` 작성:
   ```yaml
   tunnel: <UUID>
   credentials-file: /Users/server-mini/.cloudflared/<UUID>.json
   ingress:
     - hostname: arisa.<도메인>
       service: http://localhost:8780   # 통합 대시보드 셸 (맥미니)
     - service: http_status:404
   ```
5. **launchd 상시화**: `~/Library/LaunchAgents/com.cloudflared.arisa.plist` (`cloudflared tunnel run arisa`, RunAtLoad+KeepAlive) → 재부팅 자동 복구. named tunnel은 재시작해도 URL 불변.
6. 맥미니 `~/do-better-workspace/.env`의 `DASHBOARD_BASE_URL=https://arisa.<도메인>` 교체 → daily-brief·weekly 코드 무수정 반영(상수화 완료, weekly 하드코딩도 2026-07-08 교체됨)
7. 검증: `curl https://arisa.<도메인>/` 200 + 대표 폰(셀룰러) 실측 — 통신사 DNS 확인
8. 리더 3명 + 대표에게 **최종 고정 URL 재발송** (07-08 팀 브리프 재발송 겸)

## 참고: project-rent.com을 안 쓰는 이유
project-rent.com은 hostcocoa 네임서버 + 이메일 Google Workspace(MX). Cloudflare 무료는 도메인 전체 이전만 가능 → MX/SPF/DKIM/DMARC 복제 필요(누락 시 회사메일 중단). 새 도메인이 리스크 0이라 채택.
