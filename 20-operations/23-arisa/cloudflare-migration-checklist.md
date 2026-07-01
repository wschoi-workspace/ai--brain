# ARISA 대시보드 고정 URL — 새 도메인 named tunnel 설정 가이드

> 목적: 리더 대시보드를 `arisa.<새도메인>` **고정 URL**로 영구 노출(통신사 DNS·임시 URL 문제 해결).
> 방향(2026-06-30 결정): **새 전용 도메인 + named tunnel을 노트북에 먼저** → 고정 URL 확보. 맥미니 상시가동 이전은 추후(가용성 개선).
> ✅ project-rent.com은 **건드리지 않음** → 이메일(GWS)·홈페이지 100% 무영향.

## 1단계: 새 도메인 Cloudflare 등록 (대표님 — 결제·계정)
1. [dash.cloudflare.com](https://dash.cloudflare.com) 계정 생성
2. 도메인 등록 — **Cloudflare Registrar에서 바로 구매**(연 ~$10, 예: `arisa-pr.com`·`dobetter-ax.com` 등 짧은 것) → zone 자동 생성, 네임서버 설정 불필요
   - (또는 가비아 등에서 구매 후 네임서버를 Cloudflare로 — Registrar 직구매가 가장 간단)
3. 도메인명 정해지면 알려주기 → 아래 2단계는 내가 진행

## 2단계: named tunnel 설정 (도메인 준비 후 — 내가 진행, 일부 사용자 `!`)
1. `~/.local/bin/cloudflared tunnel login` → 브라우저에서 새 도메인 zone 선택·인증 (**사용자 `!` 실행**, cert.pem 생성)
2. `cloudflared tunnel create arisa` → 터널 UUID + `~/.cloudflared/<UUID>.json` 생성
3. `cloudflared tunnel route dns arisa arisa.<도메인>` → Cloudflare zone에 CNAME 자동 생성
4. `~/.cloudflared/config.yml` 작성:
   ```yaml
   tunnel: <UUID>
   credentials-file: /Users/choi_ai/.cloudflared/<UUID>.json
   ingress:
     - hostname: arisa.<도메인>
       service: http://localhost:8770
     - service: http_status:404
   ```
5. **launchd 상시화**: `~/Library/LaunchAgents/com.cloudflared.arisa.plist` (`cloudflared tunnel run arisa`, RunAtLoad+KeepAlive) → 맥 재부팅·재시작 시 자동 복구. (단 노트북 슬립은 caffeinate로 커버, clamshell 슬립은 맥미니 이전 전까지 잔존)
6. `.env`에 `DASHBOARD_BASE_URL=https://arisa.<도메인>` 한 줄 추가 → daily-brief 코드 무수정 반영(이미 상수화됨)
7. `weekly-report-aggregate.py` `_telegram_summary`의 ts.net 하드코딩도 `DASHBOARD_BASE_URL` 상수로 교체(아직 미반영)
8. 검증: WebFetch로 `https://arisa.<도메인>/api/health` → `{"ok":true}` + 대표 폰 실측
9. 리더 3명 + 대표에게 **최종 고정 URL 재발송** → 임시 trycloudflare 종료(`pkill -f "cloudflared tunnel --url"`)

## 3단계: 맥미니 상시가동 이전 (추후 — 가용성 근본해결)
- 맥미니 현재 offline 4일(Tailscale last seen). 살린 뒤: 대시보드 서버 + aggregator + 봇 + cloudflared를 맥미니로 이전 → 노트북 슬립 무관. 별도 작업(launchd·.env·mem0·gws 인증 포함 패키지 이전).

## 현재 임시 상태 (고정 URL 완성 전까지)
- quick tunnel: `nohup ~/.local/bin/cloudflared tunnel --url http://localhost:8770`(URL: crossword-international-comparative-operations.trycloudflare.com), `/tmp/cf-tunnel.log`
- daily-brief `DASHBOARD_BASE_URL` 기본값 = 이 임시 URL → 내일 알림 열림(맥 켜둔 동안)
- ⚠️ 맥 재부팅/완전 슬립 시 터널 죽고 URL 변경 → 고정 URL 완성 전까지 맥 유지

## 참고: project-rent.com을 안 쓰는 이유
project-rent.com은 hostcocoa 네임서버 + 이메일 Google Workspace(MX). Cloudflare 무료는 도메인 전체 이전만 가능 → MX/SPF/DKIM/DMARC 복제 필요(누락 시 회사메일 중단). 새 도메인이 리스크 0이라 채택.
