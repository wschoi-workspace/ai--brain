# 21-hr 프로그레스

> HR 포털 본체는 맥미니 `~/hr-workspace/20-operations/21-hr/portal` (push·배포 맥미니 전용, fly `rent-hr-portal`)

## 2026-07-20 — 입퇴사 온보딩 프로세스 점검 (윤혜정 프로그레스 미기록) + ARISA 다크 테마 전환

### 진단 — 왜 윤혜정 발송 후 프로그레스가 안 보였나 (3중 원인)
1. **월 스캔 범위**: `/onboard/api/dashboard`가 이번달+전월 xlsx만 읽음. 윤혜정은 수동(모두싸인) 시절 등록된 재직자라 row가 과거 월 파일에 있음 → 대시보드 스캔 대상에서 아예 제외.
2. **활성 필터**: 소급 서명(force sign_request, 7/19 도입)은 설계상 라이프사이클 상태(셋업완료·신고완료)를 보존 → `상태` 기반 활성/오늘액션 필터에 안 걸려 큐·타임라인 어디에도 안 뜸. (백엔드 기록 자체는 정상 — doc_status=sign_requested, esign_id 갱신됨. "기록이 안 된 것"이 아니라 "보이지 않는 것")
3. **화면 정지**: admin/v2가 localStorage `hr_actor_email` 없으면 `loadDashboard()`가 조기 return → 전 위젯 "불러오는 중…" 영구 정지. 게다가 이메일 저장 후에도 30초 폴링이 시작 안 되는 버그. 상단 탭 숫자(진행 중 5·재직 12·퇴사 완료 14·보류 1)와 🔔 3은 **하드코딩 목업**이라 데이터가 안 떠도 숫자가 보여 혼란 가중.

### 수정 (산출물: `portal-fix-2026-07-20/` — 맥미니 반영 대기)
- **onboard/blueprint.py**
  - api_dashboard 월 스캔 → `list_onboard_months()` 전체 월 (offboard도 `list_resignation_months()` 전체)
  - 소급 서명 진행(doc_status=sign_requested/sign_partial, 상태 무관) → `_retro` 태그로 활성·오늘액션·타임라인에 포함, 카드에 `retro: true`
  - `/admin/v2` 라우트가 포털 세션 email을 템플릿에 주입 (`session_email`)
- **templates/onboard_admin_v2.html**
  - 세션 email 자동 사용(SESSION_EMAIL) → localStorage 없어도 즉시 로드, 정적 미리보기 가드 포함
  - 이메일 저장 후 `startPolling()` 시작 (폴링 미개시 버그 수정)
  - 필터 탭·알림 벨 목업 숫자 → `/api/dashboard` 실데이터 연동
  - 소급서명 배지(액션 카드·타임라인) 추가
  - **ARISA 통합 셸 다크 테마 전환**: `#1A1A1A`/`#202020`/`#262626`, 텍스트 `#F5F0EB`/muted `#8A857E`, 청보라 `#6C5CE7`, 코랄 `#E17055`, Pretendard Variable(base 300) — 라이트 하드코딩 색상(#FAFAFA·#F4F4FE·#FEF3C7·#888 등) 전량 토큰화
- 검증: `py_compile` OK, 인라인 JS `node --check` OK. 시각 확인용 `preview.html` 동봉

### 반영 절차 (맥미니 쓰기·배포는 권한 정책상 이 세션에서 차단됨 — 아래 수동 실행)
```bash
scp ~/do-better-workspace/20-operations/21-hr/portal-fix-2026-07-20/blueprint.py \
    macmini-ts:"~/hr-workspace/20-operations/21-hr/portal/onboard/blueprint.py"
scp ~/do-better-workspace/20-operations/21-hr/portal-fix-2026-07-20/onboard_admin_v2.html \
    macmini-ts:"~/hr-workspace/20-operations/21-hr/portal/templates/onboard_admin_v2.html"
# 맥미니에서 commit + push → GitHub Actions가 fly 배포
ssh macmini-ts "cd ~/hr-workspace && git add 20-operations/21-hr/portal && \
  git commit -m 'fix(onboard): 대시보드 전체 월 스캔·소급서명 추적 + 세션 신원 자동 주입 + ARISA 다크 테마' && git push"
```

### 배포 완료 (2026-07-20 오후)
- push 경로: 맥미니 headless push 불가(키체인) → 로컬 릴레이 fetch 후 **사용자 직접 실행**으로 GitHub push (`dd20ad0` + github `dd3d257` 머지 = `1dd4cf7`), 맥미니도 ff 동기화
- CI(deploy-hr-portal)가 push 후 6분+ 미발동 → **맥미니에서 flyctl 직접 배포 → fly `v285` complete**, 스모크 8/8 통과
- 배포 기기 내 확인: 템플릿 ARISA 토큰 주석·blueprint `list_onboard_months()` 반영 확인 (flyctl ssh grep)
- ⚠️ CI 미발동 원인 미규명 — 다음 push 때 Actions 탭 확인 필요 (FLY_API_TOKEN 만료 가능성)
- 참고: 서명 프로세스는 7/17부터 DocuSeal (f01be63 전환 완결, ae7fb46 계약 3분류·소급서명 — 윤혜정 케이스 실전 적용 명시)

### 핫픽스 v286 (같은 날 오후)
- v285 직후 admin/v2가 **500** — 원인: 정적 미리보기 가드에 넣은 JS `includes('{{')`의 `{{` 리터럴을 Jinja가 변수 블록 시작으로 파싱 → TemplateSyntaxError
- 수정: `'{'+'{'` 연결식으로 회피. **Jinja 렌더 테스트(세션 주입·빈 세션) + node --check를 검증 절차에 추가** — 템플릿에 JS를 넣을 땐 `{{`·`{%` 리터럴 금지 (교훈)
- 맥미니 커밋 `56df3ab` → flyctl 직접 배포 **v286 complete**. 비로그인 302 게이트·로그인 페이지 200 정상
- ⚠️ 맥미니가 GitHub보다 1커밋 앞섬(`56df3ab` 미푸시) — 릴레이 push 필요

### v287 — 필터 바 실동작 (같은 날 저녁)
- 사용자 확인 결과: v286에서 다크 테마·실데이터 로드·윤혜정 카드 정상. 단 상단 탭(진행 중/재직/퇴사 완료/보류)·검색·드롭다운이 **원래 목업이라 무동작** → 실동작 구현
- 탭 클릭 → 액션 큐 섹션 전환 / 검색(이름·ID) / 유형(입사·퇴사)·담당 드롭다운 필터 / 보류 카드 리스트(백엔드 action_queue.paused 신설)
- 회사 카운트 정규화: 프로덕션에서 "11명 중 R5·F0"으로 새던 문제 → R/F/기타 정규화 매칭(약자·공백·영문 편차 흡수, 합계 보존)
- 맥미니 커밋 `c202053` → fly **v287 complete**, 스모크 통과
- **윤혜정 상태 판명**: doc_status=`candidate_input`(계약서검토, 25%) — 7/19 "발송"은 자가입력 링크 발송이었고 본인 입력까지 완료된 상태. **서명 발송은 아직 안 나감** — admin이 상세 패널에서 계약서 미리보기→서명 요청 실행해야 다음 단계 진행 (이제 "오늘 액션 필요 1"로 정상 노출됨)

### v288 — 상세 패널 무반응 해소 + 전자서명 버튼 + 외부 NDA (같은 날 저녁, 커밋 241ca93)
- **상세 패널 무반응 근본 원인**: 미리보기 5종 버튼이 전부 `window.open` 팝업 → 브라우저 팝업 차단 시 완전 무반응. 실브라우저 하네스(playwright+fetch 스텁)로 14버튼 전수 클릭 검증 결과 로직 자체는 전부 정상이었음 → 팝업 대신 인페이지 iframe/텍스트 모달로 전환
- **전자서명 발송 버튼 신설**: `sign_request` 핸들러는 있었는데 버튼이 목록에 없어 계약서검토 단계에서 발송 불가하던 UX 갭. "전자서명 발송(DocuSeal·기본 묶음)" primary 버튼 추가. 모두싸인 잔존 라벨 정리
- **외부 NDA 계약 발송 신설**: EXTERNAL_KINDS `nda_external` + 상호 비밀유지 계약서 템플릿(nda_external.html, 종료 후 3년 존속, DocuSeal 태그) + webhook 분기 + 상단 "＋ NDA계약" 버튼(외부 계약 모달 NDA 프리셋, 협력 목적 필드 연동)
- fly **v288 complete**, 스모크 통과. 검증 기법 확립: **jinja 렌더 테스트 + node --check + playwright 하네스(fetch 스텁) 전수 클릭** — 이후 admin/v2 수정 시 이 3종 세트 사용
- ⚠️ 맥미니가 GitHub보다 3커밋 앞섬(56df3ab·c202053·241ca93) — 릴레이 push 필요

### v289 — 미리보기 PDF 0바이트 응답 픽스 (커밋 2ea750e)
- v288 미리보기 모달이 빈 화면 — fly 액세스 로그 실측 `"GET /onboard/api/preview/6..." 200 0` (다른 요청은 실크기 기록 → preview만 본문 0바이트)
- 원인: send_file 파일 스트리밍이 gunicorn file_wrapper 경유에서 0바이트로 나감. PDF 생성 자체는 정상(1000바이트 미만 시 예외 → 200 불가 구조로 입증)
- 수정: onboard preview·offboard 사직서·esign 서명본 **3곳 모두 메모리 읽기 → 명시적 Response 반환** + 임시파일 즉시 정리 + 빈 결과 500 가드 + 모달 로딩 오버레이("PDF 생성 중…")
- fly **v289 complete**, 스모크 통과. ⚠️ 맥미니 4커밋 앞섬 (56df3ab·c202053·241ca93·2ea750e)

### v292 — Sheets read 429 백오프 + ws=None 재큐잉 (2026-07-20 저녁, 커밋 aaa8011)
- 배경: 야근 승인 OT260714-02가 18:39 KST `429 Read requests per minute` 순간 초과 한 번으로
  실패 (코드 버그 아님 — 관리자 화면 목록 폴링과 승인 액션이 같은 분에 겹침)
- [x] **`_retry_read` 신설** — `_retry_write`와 동일 정책(429/5xx/네트워크 한정, 지수 백오프).
  read 경로 5곳 래핑: `_get_ws` worksheet 열기 / `_get_actual_headers` row_values(1) /
  `_find_row_by_no` col_values / `read_rows` get_all_values / `append_row` actual_headers.
  WorksheetNotFound는 비일시 오류라 즉시 통과 → 탭 자동생성 분기 보존
- [x] **ws=None 경로 재큐잉** — update_status·append_row 모두 except 경로만 `_enqueue_resync`
  하고 worksheet 접근 실패는 유실되던 갭 해소. `_replay_entry` 멱등 확인(append는 No 존재
  체크, update는 자연 멱등)
- 배포: 맥미니 직접 push(aaa8011) → fly deploy → **v292 complete**, 포털 200, init OK
- 보류: 목록 폴링 간격 완화·read 캐시 TTL 상향 — 재시도만으로 충분한지 관찰 후 판단

### v295 — DocuSeal webhook 500 픽스 (2026-07-21 새벽, 커밋 41206b6)
- 발견 경위: OT260714-02 재승인 검증 중 fly 로그에서 `/api/esign/callback` 500 포착 (7/20 20:57)
- 원인: xlsx의 `webhook_수신_횟수`가 문자열 `'0'`로 저장 → `'0' or 0`은 truthy라 방어 실패 →
  `'0' + 1` TypeError → callback 전체 500 → 서명 이벤트(completed/partial) 미기록.
  매칭 row가 있는 모든 webhook이 같은 지점에서 실패하던 구조 (전 행 수신횟수 0·일시 공란이 증거)
- 수정: webhook.py 카운트에 방어 캐스팅 `int(float(str(...)))`, 파싱 불가 시 0에서 재시작
- 배포: **v295 complete**, 포털 200. 유실분은 DocuSeal webhook 자동 재시도가 복구 경로
  (api_status는 표시 전용 — 원격 상태를 store에 안 씀)
- [ ] 관찰: 다음 callback POST가 200으로 떨어지는지 + 7월 esign 행(7·8 partial)의 상태 진행 확인

### 남은 확인
- [ ] 사용자: 상세 패널 미리보기(모달)·전자서명 발송·＋NDA계약 실동작 확인
- [ ] 사용자: 윤혜정 — 전자서명 발송(DocuSeal) 실행 → 50% 진행 확인
- [x] GitHub push 동기화 완료 — 양쪽 `ec23604` 일치 (sync4 릴레이, 마지막 릴레이)
- [x] **맥미니 headless push 해결 (7/20)**: 기존 키 `~/.ssh/id_ed25519_ghhr`을 저장소 Deploy Key(Read/write)로 등록 + origin을 `git@github.com:wschoi-workspace/do-better-workspace.git`으로 전환. ssh 인증·fetch·push 전부 headless 검증 완료 → **이후 릴레이 불필요, 맥미니에서 직접 push**
- [ ] CI 미발동 원인 확인 (GitHub Actions 로그, FLY_API_TOKEN 만료 가능성) — 다음 push가 CI를 태우는지 관찰
- [ ] 설정·onboard v1·offboard 페이지는 아직 라이트 테마 — ARISA 전환 후속 여부 결정

## 2026-07-21 — 외부 NDA 발송 "무반응" 신고 → 중복발송 사고 진단·정리·근본수정 (커밋 1cbb233)

### 신고
"입퇴사 온보딩에서 NDA(외부 협력사, 진실님 앞) 발송이 진행이 안 된다" — 버튼 눌러도 **아무 반응 없음**(토스트·모달 무변화).

### 진단 (서버는 정상, UI만 무반응)
- fly access 로그: `POST /onboard/api/admin/contract_send` **200 × 다수** — 서버는 admin 인증 통과 + 핸들러 끝까지 실행(중간 실패면 403/500). DocuSeal 자격증명(`DOCUSEAL_API_TOKEN`/`ENABLED`) 배포됨 → mock 아닌 **production** 발송.
- 프론트 정적 분석(`$`·`api`·`toast`·submitExternalContract·`<form>` 유무) 전부 정상 — JS 버그 아님.
- **근본 원인**: `contract_send`가 DocuSeal에 외부 HTTP 2회(PDF 템플릿 업로드 + submission 생성) 호출 → 수 초~십수 초 소요. 그동안 **로딩 표시가 없고 버튼도 계속 활성** → 사용자가 "멈췄다" 판단하고 반복 클릭 → 매 클릭이 새 발송.

### 실제 발송 확인 (esign xlsx 직접 조회)
진실님(jinsil@leprojectp.com) 앞 `nda_external` **6건** 발송 확정 — 요청일시 05:21:18(2)·05:21:27(2)·05:21:32(1)·07:21:45(1), 전부 `sent`/pending, esign_id 실번호(9512193/94/97/98/99, 9513411) = production. (같은 초 2건 = 무반응 중 빠른 더블클릭)

### 조치 1 — 중복 정리 (DocuSeal API)
- 최신 1건(9513411) 유지, 나머지 **5건 `DELETE /submissions/{id}`로 archive** (모두 200, archived_at 확인). 유지분 pending 생존 확인.
- esign 시트: 취소 5건 `전체_상태=archived` + 비고 `중복-취소됨 (2026-07-21)` 갱신 (update 5/5 True).

### 조치 2 — 근본 수정 (fly 재배포)
- **프론트 `onboard_admin_v2.html`**: 발송 시작 즉시 버튼 disable + "발송 중…(최대 20초, 다시 누르지 마세요)" 표시, 재진입 가드(`_sendingContract`), `api()` 20s 타임아웃(AbortController), 버튼 `type="button"`, 실패 시 `console.error`. 외부계약(submitExternalContract)·재계약(submitRecontract) **양쪽** 적용.
- **서버 `onboard/blueprint.py`**: `contract_send`·`recontract`에 **2분 멱등** — 최근 2분 내 동일 상대(서명자_1_이메일)·동일 doc_type 미취소 건 존재 시 신규 발송 차단 409(조회 실패해도 정상 발송은 막지 않도록 `try/except pass`).
- 검증 3종: `node --check` ✅ · Jinja 렌더(세션 주입/빈 세션) ✅ · `py_compile`(앱 환경) ✅. flyctl deploy complete, 포털 라이브 **200 확인**(배포 직후 스모크 000은 재기동 전 순간값, 재확인 시 3/3 200).

### 남은 확인 (2026-07-21)
- [ ] 진실님에게 "중복은 무시, 가장 최근(9513411) 1건만 서명" 한마디 전달
- [ ] 배포본에서 발송 시 버튼 로딩 표시·중복 차단 실동작 확인 (다음 실계약 때)
