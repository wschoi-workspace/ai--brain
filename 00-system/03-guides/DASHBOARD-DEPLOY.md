# 프로젝트 포트폴리오 대시보드 — 맥미니 배포 가이드

직원 누구나 **링크로 접속**, **PM은 본인 프로젝트 수정**, **대표는 전체 열람·수정**.
서버 1개(화면+API)를 맥미니에서 상시 가동하고 **Tailscale**로 사내·재택 접속.

---

## 구성 요소
| 파일 | 역할 |
|---|---|
| `02-scripts/dashboard-server.py` | 화면+API 서버 (표준 라이브러리만, 설치 불필요) |
| `01-templates/포트폴리오_대시보드.html` | 화면 (서버가 읽어 서빙) |
| `01-templates/_data/users.json` | 로그인 사용자·PIN·권한 |
| `01-templates/_data/projects/*.json` | **실제 프로젝트 데이터(PM 수정분 저장)** ★백업 |
| `02-scripts/portfolio-users.json` | 사용자·배정 원본(편집 후 build로 반영) |
| `02-scripts/build-dashboard.sh` | 재생성(템플릿·화면·시드) |
| `02-scripts/com.projectrent.dashboard.plist` | launchd 상시가동 |

---

## 1. 설치 + 상시 가동 (한 줄 — 이관 가능)
설치 스크립트가 **현재 사용자·경로·파이썬을 자동 감지**해 launchd 서비스를 만들고 띄웁니다. 경로 수정 불필요.
```bash
bash ~/do-better-workspace/00-system/02-scripts/install-dashboard.sh
# 미리보기만(설치 안 함): DRY_RUN=1 bash …/install-dashboard.sh
# 포트 변경:            DASHBOARD_PORT=9000 bash …/install-dashboard.sh
# 제거:                 bash …/uninstall-dashboard.sh
```
→ 빌드(시드 생성) + plist 생성·로드 + 헬스체크까지 자동. `http://127.0.0.1:8770` 가동.

> 모든 스크립트가 **스크립트 위치 기준 상대경로**로 동작 → 어느 맥/사용자에서도 그대로 실행됩니다.

## 3. Tailscale로 노출 (포트 개방 없이, 사내·재택)
맥미니에 Tailscale 설치·로그인(이미 설치됨). 그다음 localhost:8770을 tailnet에 게시:
```bash
TS=/Applications/Tailscale.app/Contents/MacOS/Tailscale
$TS serve --bg 8770
$TS serve status          # 게시 URL 확인
```
→ `https://<맥미니이름>.<tailnet>.ts.net/` 형태의 **HTTPS 링크**가 나옵니다.
- 이 링크는 **같은 Tailscale 조직(테일넷)에 로그인한 기기만** 접속 가능 → 안전.
- 직원 기기에 Tailscale 설치 + 회사 테일넷 로그인 → 위 링크 접속.
- (구버전 Tailscale은 `$TS serve https / http://127.0.0.1:8770` 형태)

## 4. 직원 안내 (로그인)
| 역할 | ID | PIN |
|---|---|---|
| 대표(전체 열람·수정) | 최원석 | 0000 |
| PM/직원 | 양은정/김준호/전제훈/양지혜/정예은/조나연/김가은/윤혜정 | 1111~8888 |

- **PM 권한**: 프로젝트의 `pm`이 본인이면 그 프로젝트를 **수정·저장** 가능.
- **직원 권한**: 배정된(`members`) 프로젝트는 **읽기 전용**.
- 본인 업무는 화면에서 `📤 업무분장 분배`로 받아갈 수 있음.

---

## 운영(관리자) 워크플로
- **PIN·사용자 변경 / PM·배정 변경**: `02-scripts/portfolio-users.json` 편집 → `bash build-dashboard.sh`. (서버 재시작 불필요 — 매 요청마다 읽음)
- **프로젝트 추가**:
  - 간단: 대표로 로그인 → `＋ 프로젝트 추가` → 마스터 엑셀 업로드(서버 저장).
  - 또는 시드로 영구 편입: `generate-portfolio.py`의 SOURCES에 추가 → build.
- **PM이 수정한 데이터**: `_data/projects/*.json`에 저장됨 → **정기 백업**(예: `cp -r _data ~/backup/_data-$(date +%F)`).
- **새 화면 반영**: HTML/생성기 수정 후 `build-dashboard.sh` → 직원은 새로고침.

## 다른 맥(맥미니)으로 이관
모두 상대경로·자동감지라 **폴더 복사 + 설치 한 줄**이면 끝.
1. 새 맥에 `do-better-workspace/` 폴더를 복사 (최소: `00-system/01-templates`(_data 포함·xlsx 포함) + `00-system/02-scripts`).
   - **`_data/` 를 반드시 함께 복사** = 실제 프로젝트 데이터 이관.
2. 새 맥에서: `bash …/02-scripts/install-dashboard.sh`
   - 새 사용자명·경로를 자동 감지해 plist 재생성·가동. 수정할 것 없음.
3. Tailscale/CF 노출 재설정(3장) → 새 링크 직원 공유.
- 백업/복원: `_data/` 폴더만 복사하면 데이터 백업·복원 완료(서버 내려두고 복사 권장).
- 클라우드/GAS로 이관도 동일 데이터(JSON)라 이식 용이.

## 권한 규칙 (서버 강제)
- 열람: 대표 OR 본인이 PM OR `members` 포함.
- 수정/저장: 대표 OR 본인이 그 프로젝트 `pm`.
- 생성·삭제: 대표만.

## 보안 한계 (인지)
- PIN은 **약한 게이팅**(Tailscale 망분리가 1차 방어선). 진짜 SSO/감사로그가 필요하면 추후 인증 강화.
- 데이터는 맥미니 `_data/`에만 존재 → 백업이 곧 안전장치.

## 문제 해결
- 화면 안 뜸: `cat /tmp/pr-dashboard.err`, `curl http://127.0.0.1:8770/api/health`
- 로그인 실패: `_data/users.json`에 해당 ID·PIN 있는지 확인.
- 외부 접속 안 됨: 직원 기기 Tailscale 로그인 상태, `$TS serve status` 확인.
