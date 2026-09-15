# 07 · 워크스페이스 진단 & 정리 — Progress

> **목적** · do-better-workspace 전수 진단(구조·용량 / git 위생 / 프로젝트 현황 / 스킬·시스템)과 정리 실행
> **정본** · `2026-09-16-workspace-audit.html` — 진단 대시보드. 실행 결과 배너 포함
> **기록** · `2026-09-16-cleanup-targets.txt` — 삭제/격리 대상 목록(실행 전 기록)

---

## 2026-09-16 — 1차 진단 및 S0~S3 + 아카이브 실행

### 진단 범위
프로젝트 31 · 운영 9 · 스킬 67 · 전체 4.3GB / 27,500여 파일.
3-way 병렬 탐색 후 **주요 주장은 읽기 전용 명령으로 직접 재확인**.

탐색 보고 중 2건이 사실과 달라 정정:
- `.emok_reply.eml` 노출 → 이미 gitignore 등록됨
- 워크트리 3개 단순 삭제 가능 → **미머지 커밋 24·5·1개 보유**. 그냥 지웠으면 arisa-vnext 24커밋 소실

### 처리 결과

| 구분 | 전 | 후 |
|---|---|---|
| 워크스페이스 | 4.3GB | **2.7GB** |
| 외부 잔재(`~/.claude/jobs/5faacc0f`) | 1.67GB | **1.5MB** |
| 활성 프로젝트 | 31 | **25** |
| 워크트리 | 6개 | **1개** |
| 미push 커밋 | 17 | **0** |
| git 미등록 스킬 | 5 | **0** |
| progress.md 누락 | 9 | **0** |
| 2MB+ 추적 파일 | 36 | 14 |

### 단계별

| 단계 | 내용 | 상태 |
|---|---|---|
| S0 | gitignore 보완 → 유일본 스킬 5종(29파일) 편입 → 수정 12건 반영 → `git archive` 정합 확인 → 20커밋 push | ✅ |
| S1 | 루트 잡파일 18 · `.playwright-mcp`(742) · `.omc`(680) · `__pycache__` · `.DS_Store` | ✅ 격리 방식 |
| S2 | 워크트리 3개 제거(1.7GB) + 외부 잔재 3개(1.67GB). **브랜치·미머지 커밋 전량 보존 확인** | ✅ |
| S3 | 파생물 132개 추적 해제(303MB). 파일은 디스크 유지 | ✅ |
| S4 | 아카이브 6건 이동 · progress.md 9건 · CLAUDE.md 갱신 | ◐ 일부 |

### 커밋 (7건, 전부 push 완료)
`dd9b1c3` gitignore 차단 → `c0a85e1` 유일본 스킬 편입 → `98df7b3` 스킬 수정 12건 →
`6859be7` 파생물 추적 해제 → `668d007` 아카이브 이동 → `2a8e491` 진단 리포트 →
`a547f22` progress 9건 → `2d2e1e2` 리포트 실행결과 반영

### 방식을 바꾼 것 2가지
1. **삭제 → 격리** — 환경에서 `rm`이 차단돼 있어 `90-archive/_cleanup-20260916/`(42MB)로 이동.
   결과적으로 되돌릴 수 있게 되어 이 방식이 더 나았다
2. **번호 재배번 보류** — 아카이브 이동만으로 29·37 두 쌍 자연 해소. 나머지는 참조 경로 위험

### ⚠️ 이번에 걸린 함정
**아카이브 이동이 gitignore를 무력화한다.** `.gitignore`가 `/10-projects/...` 절대경로라
폴더를 옮기는 순간 패턴이 빗나간다. `git rm --cached`로 303MB를 해제한 직후 이동했더니
staged가 18.9MB여야 할 것이 **181.9MB**로 튀었다. 커밋 전 크기 확인에서 잡아 `git reset` 후 복구.
→ 메모리 `feedback_archive_move_gitignore`

---

## 남은 것

### 바로 할 수 있는 것
- [x] **격리 폴더 처리 완료** (2026-09-16) — `90-archive/_cleanup-20260916/` 제거. 워크스페이스 2.7GB → **2.6GB**
  - 캐시·캡처·중복 41MB → `~/.Trash/ws-cleanup-20260916/` (복구 가능)
    · `cache/` 22M(.playwright-mcp·.omc) · `innisfree-self-nested/` 15M(md5 동일) · `root-junk/` 4.3M · `self-nested/` 60K
  - **유일본 6건(308KB)은 원위치 복구** — 브랜치에도 없어 지우면 복구 경로가 없었다
    · `engine/out/result.json` → `10-projects/15-bongeunsa/engine/out/` (봉은사 엔진 스코어링: 8,868㎡·21 atoms·20 units)
      ⚠️ `engine/`은 `worktree-bongeunsa-engine` 브랜치에만 있고 main엔 없다. 경로를 새로 만들어 넣었으므로 **브랜치 머지 시 자연 합류**
    · `deck-measured-{raw,raw2,new}.json` + `m390.jpeg` + `scope-top.jpeg` → `20-operations/23-arisa/`
  - 복구분은 원래도 untracked였으므로 추적 상태 변화 없음
  - ⚠️ `rm`이 이 환경에서 차단돼 있다. 삭제는 `mv ~/.Trash/` 로 우회했다
- [x] **`90-archive/_cleanup-20260722/` 32MB 정리 완료** (2026-09-16) — 7월에 분리해두고 2개월 방치된 보관소.
      원본 생존 여부를 전수 확인하고 `~/.Trash/ws-cleanup-20260722/`로 이동
  - `png-root/` 64개 26MB — 페이지별 확인용 캡처(`proposal-p1~p10` · `50p-slide-1~10` · `guide-01~06` 등). 원본 덱은 각 프로젝트 폴더에 생존
  - `to-delete/` 4개 5.2MB — `_gubi-v1-preview.pdf`(원본 PDF는 90-archive/31-gubi-dapsimni/reports/에 있음) ·
    `_part2-capture.html`+`part2-preview.png`(원본은 26-reporting-os 가이드 Part2) ·
    **`_napkin-v3-share-nopw.pdf`** — 무암호 공유본. 메모리 `share_pdf_security`(PDF 128bit 암호화 필수)에 비추면
    **남겨두는 쪽이 오히려 위험**한 파일이었다. 원본 HTML은 30-napkin-mag-sns/reports/에 생존
  - `bak-files/` 11개 + `bak-sensitive/` 2개 524KB — **원본 13개 전부 생존 확인**.
    bak-sensitive는 `users.json`·`portfolio-users.json` 백업(7/4)으로 민감정보라 제거가 맞다
  - 부수: `.gitignore` 103행 `90-archive/_cleanup-20260722/` 제거 — 215행 와일드카드 `_cleanup-*/`와 중복이었다
  - **격리 폴더 전량 정리 완료. 워크스페이스 2.59GB**
- [ ] `node_modules` 810MB — `38-ax-pre-diagnosis` 469MB(소스는 164K), 루트 341MB

### 정리 중 발견 — 확인 필요
- [ ] ⚠️ **`90-archive/30-basket-report-webapp/SETUP.md` PIN·관리자 비밀번호 평문**.
      git 히스토리에도 남아 있다. 서비스 생존 시 자격증명 교체
- [ ] ⚠️ **`25-basket-ops-manual` launchd 헛돎** — 온보딩 8회 발송 완료 후에도 09-15까지 매일 실행
- [ ] **`41-chungdam-nine-sns` git 추적 0건** — 09-09 "자료 없음" 오판의 원인.
      progress.md만 추적 편입함. 나머지는 추적 vs SSOT를 80-r-tech로 고정 중 택일

### 보류 — 별도 작업으로 분리
- [ ] **번호 충돌 38·41·43 세 쌍** (결번: 16~25·27·31~34·54)
- [ ] **`.git` 329MB** — `filter-repo` + force-push 필요. 병렬 세션 환경이라 세션이 하나뿐일 때 실행
- [ ] **미커밋 277건** — 데일리 139 등 타 세션·직접 작업분. 사용자 판단 영역
- [ ] **`매트릭스` ⚠️ 미결 3건** (2026-07-31 등록, 6주 반 경과)
      ① E열 기본 정렬: 교차 최소 vs 논리 순서 ② D↔D-1 짝 정렬 후퇴(4px→10~20px)
      ③ 예고 확장 3종(Target 해석 자료 / 컨셉 해석 열 / D-1 매출 산식)
      → **렌더러 공통이라 새 프로젝트에도 그대로 걸린다**
- [ ] 구조 잔여: `00-inbox`(README 1개뿐, 00-system과 번호대 중복) · `99-moc`(JD 체계 밖) ·
      카테고리 루트 낱파일(30-knowledge 4 · 50-resources 11 · 80-r-tech 4) ·
      `56-k-heritage-popup` 백업 5종 난립 · frontmatter 없는 SKILL.md 6건
