I have everything needed. Producing the atom set.

## (1) Atoms — at-0260 ~ at-0289

```json
[
{
  "id": "at-0260",
  "title": "불교 일반 — 네이버 블로그 멘션 2,809건 3군 비교 수집 (불교1,084·기독교786·명상웰니스939)",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "2026-06-13 네이버 블로그 검색 API로 3개 비교군을 크롤링. 불교군 6개 키워드(템플스테이 후기·사찰 명상·힙불교·불교 MZ·사찰음식·봉은사), 키워드당 최대 200건(start 1·101), sort=date, 링크 중복 제거. 제목+요약(description) 텍스트만 수집하고 본문은 수집하지 않았다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/progress.md", "loc": "L14", "quote": "Phase2 멘션 크롤링: 네이버 블로그 **2,809건**(불교 1084·기독교 786·명상웰니스 939)" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/scripts/buddhism_crawl.py", "loc": "L32-36", "quote": "'불교': ['템플스테이 후기', '사찰 명상', '힙불교', '불교 MZ', '사찰음식', '봉은사']," }
  ],
  "basis": "crawled_data",
  "limitation": "네이버 블로그 단일 채널. 제목+요약만 수집(본문 미수집)이라 텍스트 길이가 100자 내외로 짧다. 협찬글 필터 없음 — 광고성 여부는 'promo' 키워드 카운트로만 근사. 인스타·유튜브·커뮤니티 등 실제 MZ 주 채널은 전부 미포함.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0261",
  "title": "불교 일반 — 3개 비교군의 수집 기간이 7배 차이 난다 (불교 71일 vs 명상웰니스 10일)",
  "kind": "record",
  "maturity": "raw",
  "ownership": "context",
  "summary": "naver-raw.json의 postdate를 집계하면 불교군 2026-04-04~06-13(71일), 기독교군 2026-05-16~06-13(29일), 명상웰니스군 2026-06-04~06-13(10일)이다. sort=date로 최신순 200건씩 긁은 결과 검색량이 많은 군일수록 기간이 짧아졌다. 즉 3군 비교는 동일 기간 비교가 아니다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/data/naver-raw.json", "loc": "postdate 집계 (불교 20260404~20260613 / 기독교 20260516~20260613 / 명상웰니스 20260604~20260613)", "quote": "\"date\": \"20260404\" … \"date\": \"20260613\"" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/scripts/buddhism_crawl.py", "loc": "L25", "quote": "def search(query, start=1, display=100, sort='date'):" }
  ],
  "basis": "crawled_data",
  "limitation": "리포트·PT 어디에도 이 기간 비대칭이 표기돼 있지 않다. 3군 KPI 정면 비교표(긍정률·진정성·현대성)는 서로 다른 관측창의 값을 나란히 놓은 것이므로, 계절성·이슈성 편차가 보정되지 않았다. 원 리포트는 이를 '최근'으로만 표기.",
  "conflict": "reports/02-종교영성-경쟁분석.html의 '② 멘션 KPI 정면 비교' 표는 3군을 동일 조건인 것처럼 병렬 제시한다",
  "uncertain": false
},
{
  "id": "at-0262",
  "title": "불교 일반 — '불교' 표본 1,084건 중 196건(18.1%)이 '봉은사' 검색어에서 왔다",
  "kind": "record",
  "maturity": "raw",
  "ownership": "context",
  "summary": "불교군 쿼리별 수집량: 템플스테이 후기 200 · 힙불교 197 · 봉은사 196 · 불교 MZ 184 · 사찰 명상 177 · 사찰음식 130. 즉 '불교 일반 인식'이라 부른 표본의 약 1/5이 봉은사 특정 멘션이며, 나머지도 템플스테이·힙불교·사찰음식이라는 이미 긍정 편향된 접점 키워드로 구성돼 있다. '불교' 자체를 쿼리로 넣은 건은 0건.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/data/naver-raw.json", "loc": "query 필드 카운트", "quote": "{'템플스테이 후기': 200, '사찰 명상': 177, '힙불교': 197, '불교 MZ': 184, '사찰음식': 130, '봉은사': 196}" }
  ],
  "basis": "crawled_data",
  "limitation": "봉은사 판단에 쓸 때 순환 참조 위험 — 봉은사 멘션이 18% 섞인 데이터로 '불교 일반이 이러하니 봉은사가 적임'이라 결론내면 자기 데이터로 자기를 정당화하는 구조가 된다. 또한 6개 키워드가 전부 체험·트렌드 접점이라 '불교에 무관심하거나 부정적인 대중'은 표본에 구조적으로 진입할 수 없다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0263",
  "title": "불교 일반 — 블로그 멘션 감성 분포: 긍정 36.8% / 부정 2.2% / 중립 61.0%, P/N 16.6",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "불교군 1,084건에 대한 감성 판정 결과. 중립이 61.0%로 과반이며 부정은 2.2%에 그친다. 긍정/부정 비는 16.6배.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/data/analysis.json", "loc": "L13-19", "quote": "\"pos\": 36.8, \"neg\": 2.2, \"neu\": 61.0, \"exp\": 47.1, \"promo\": 16.4, \"auth\": 61.7, \"pos_neg_ratio\": 16.6" }
  ],
  "basis": "crawled_data",
  "limitation": "감성은 LLM이 아니라 20개 긍정어·15개 부정어 사전의 단순 출현 카운트로 판정(p>ng면 긍정). 반어·부정문·문맥 무시. 부정어 사전에 '싫·별로·실망' 등 강한 어휘만 있어 완곡한 비판은 전부 중립으로 흘러간다 — 부정 2.2%는 실제 부정 여론이 아니라 사전 민감도의 하한값에 가깝다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0264",
  "title": "불교 일반 — 3군 긍정률 비교: 불교 36.8% > 기독교 18.1%, 그러나 명상웰니스 51.7%로 최고",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "긍정률은 명상웰니스 51.7%(P/N 24.2) > 불교 36.8%(16.6) > 기독교 18.1%(9.5). 리포트가 강조한 '불교는 기독교의 2배'는 맞지만, 같은 표에서 불교는 명상·웰니스군에 긍정률·P/N 모두 밀린다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/data/analysis.json", "loc": "L34-40, L56-61", "quote": "기독교 \"pos\": 18.1 … 명상웰니스 \"pos\": 51.7, \"pos_neg_ratio\": 24.2" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/reports/불교-인식변화-진단리포트.html", "loc": "② 사람들은 불교를 어떻게 말하는가", "quote": "긍정률 36.8%로 기독교(18.1%)의 2배" }
  ],
  "basis": "crawled_data",
  "limitation": "at-0261의 기간 비대칭이 직접 걸리는 지표. 명상웰니스군은 10일치 최신 글만이라 이벤트성 긍정 글이 과대 반영됐을 수 있다. 또 기독교군 쿼리('교회 청년'·'기독교 신앙')는 신앙 담론형, 불교군 쿼리는 체험형이라 애초에 긍정어 출현 확률이 다르다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0265",
  "title": "불교 일반 — 멘션 토픽 분포: 수행·명상 42.6% / 힙·현대화 37.5% / F&B·웰니스 34.3% vs 전통·역사 12.9%",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "7개 토픽 키워드군 출현률(중복 허용). 상위 3개가 수행·명상 42.6, 힙·현대화 37.5, F&B·웰니스 34.3이고 전통·역사는 12.9, 공동체·위로 13.6. 현대 계열(힙+웰니스 71.8)이 전통 계열(전통+고루 14.2)의 약 5배, 리포트 표현으로는 '전통보다 현대가 3배'.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/data/analysis.json", "loc": "L4-12", "quote": "\"수행·명상\": 42.6, \"전통·역사\": 12.9, \"F&B·웰니스\": 34.3, \"공동체·위로\": 13.6, \"힙·현대화\": 37.5" }
  ],
  "basis": "crawled_data",
  "limitation": "토픽은 고정 키워드 사전 매칭이라 수집 쿼리와 순환한다 — '힙불교'·'불교 MZ'·'사찰음식'으로 긁은 표본에서 '힙·현대화'·'F&B·웰니스' 토픽이 높게 나오는 것은 발견이 아니라 설계의 결과다. '전통·역사'를 쿼리로 넣은 적이 없으므로 12.9%는 과소평가일 가능성이 크다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0266",
  "title": "불교 일반 — 부정 계열 토픽 합계 3.5% (불신·상업화 2.2% + 고루·접근성 1.3%)",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "블로그 멘션에서 '상업·장사·논란·비판·부담' 계열 언급이 2.2%, '고루·올드·촌스·어렵·문턱' 계열이 1.3%. 리포트는 이 3.5%를 근거로 '불교의 약점은 비호감이 아니라 아직 닿지 않은 거리'라고 규정하고, 동시에 2.2%를 과잉 상업화 리스크의 방어선 지표로 설정했다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/reports/불교-인식변화-진단리포트.html", "loc": "L132 (② 토픽 분포 콜아웃)", "quote": "'고루함·불신' 같은 부정 토픽은 합쳐도 <strong>3.5%</strong>에 불과 — 약점은 '비호감'이 아니라 '아직 닿지 않은 거리'다." }
  ],
  "basis": "crawled_data",
  "limitation": "네이버 블로그는 구조적으로 우호적 채널이다(체험 후기·방문기 중심). 불교 비판 담론은 커뮤니티·유튜브 댓글·기사 댓글에 몰려 있는데 그 채널이 표본에 없다. 3.5%를 '대중의 부정 여론 총량'으로 읽으면 안 되고, '블로그 체험 후기 안에서의 부정 언급률'로만 읽어야 한다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0267",
  "title": "불교 일반 — 진정성 지수 61.7 (경험 후기 47.1%, 홍보성 16.4%) · 산식 = 경험률×0.6 + (100−홍보율)×0.4",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "불교군은 '다녀·가봤·해봤·후기·체험·직접' 계열 어휘가 47.1%에서 출현하고 '문의·예약·할인·이벤트·협찬' 계열이 16.4%. 두 값을 6:4로 가중해 61.7을 산출했다. 리포트는 이를 '체험으로 이야기되는 종교'의 근거로 사용한다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/scripts/analyze.py", "loc": "L45", "quote": "'auth':round((exp/n*100)*0.6 + (100-promo/n*100)*0.4,1),  # 진정성 근사" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/data/analysis.json", "loc": "L16-18", "quote": "\"exp\": 47.1, \"promo\": 16.4, \"auth\": 61.7" }
  ],
  "basis": "crawled_data",
  "limitation": "0.6/0.4 가중치는 임의 설정이며 검증 근거가 없다(코드 주석도 '근사'). RXR 정식 파이프라인의 Sincerity Filter(A~G 분류·Account Trust)가 아니라 키워드 2종 카운트의 선형 결합이다. 협찬 표기가 본문에만 있으면 요약에서 잡히지 않아 promo 16.4%는 하한값.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0268",
  "title": "불교 일반 — 3군 진정성·경험 후기 비교: 불교 61.7(경험 47.1%) > 명상웰니스 54.5(30.2%) > 기독교 45.3(12.5%)",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "경험 후기 비율은 불교 47.1% / 명상웰니스 30.2% / 기독교 12.5%로 3.8배 격차. 리포트는 '기독교는 경험이 아닌 포교·정보 콘텐츠로 이야기되어 진정성이 낮다'고 해석했다. 3군 중 불교가 유일하게 우위인 지표.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/data/analysis.json", "loc": "L18, L39-40, L60-61", "quote": "불교 \"auth\": 61.7 … 기독교 \"exp\": 12.5, \"auth\": 45.3 … 명상웰니스 \"exp\": 30.2, \"auth\": 54.5" }
  ],
  "basis": "crawled_data",
  "limitation": "쿼리 설계가 결과를 만들었을 가능성이 크다 — 불교군에는 '템플스테이 후기'·'명상 후기'처럼 후기라는 단어가 쿼리에 들어 있고, 기독교군 쿼리 4종('교회 청년'·'기독교 신앙'·'성당 미사'·'천주교 영성')에는 체험 어휘가 하나도 없다. 지표 간 비교라기보다 쿼리 간 비교에 가깝다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0269",
  "title": "불교 일반 — 포지셔닝 좌표(토픽 파생): 불교 현대성 83.5 / 라이프스타일성 56.1, 기독교 50.9/23.6, 명상웰니스 96.3/32.8",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "x축 현대성 = (힙+웰니스)/(힙+웰니스+전통+고루), y축 라이프스타일성 = (웰니스+힙)/(웰니스+힙+수행+공동체)로 토픽 비율에서 파생시킨 좌표. 불교는 현대성에서 명상웰니스(96.3)에 밀리지만 라이프스타일성 56.1로 3군 중 1위다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/scripts/analyze.py", "loc": "L40-41", "quote": "x_modern=round(modern/(modern+trad+0.01)*100,1)   # 0 전통 ~ 100 현대" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/data/analysis.json", "loc": "L20-21, L41-42, L62-63", "quote": "\"x_modern\": 83.5, \"y_life\": 56.1 … 50.9 / 23.6 … 96.3 / 32.8" }
  ],
  "basis": "crawled_data",
  "limitation": "두 축이 같은 7개 토픽 비율에서 파생돼 서로 독립이 아니다(힙·웰니스가 양 축에 동시 투입). 따라서 '2축 포지셔닝 맵'은 독립 차원의 좌표계가 아니라 하나의 토픽 분포를 두 방향으로 사영한 것에 가깝다. 축 이름(현대성·라이프스타일성)은 해석적 명명이지 측정된 구성개념이 아니다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0270",
  "title": "불교 일반 — '힙·현대화' 토픽 언급률이 기독교군의 11배 (37.5% vs 3.4%)",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "힙·현대화 토픽(힙·MZ·뉴진·트렌디·감성·인스타·굿즈·핫플·젊)은 불교 37.5%, 명상웰니스 7.1%, 기독교 3.4%. 종교 카테고리 안에서 '현대·트렌드 언어로 이야기되는 것'은 사실상 불교 단독이다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/data/analysis.json", "loc": "L9, L30, L51", "quote": "불교 \"힙·현대화\": 37.5 … 기독교 \"힙·현대화\": 3.4 … 명상웰니스 \"힙·현대화\": 7.1" }
  ],
  "basis": "crawled_data",
  "limitation": "불교군에만 '힙불교'·'불교 MZ' 쿼리가 있고 기독교군에는 대응 쿼리('힙기독교' 등)가 없다. 격차의 상당 부분이 쿼리 비대칭에서 온다. 다만 '힙불교'라는 검색어가 성립하고 대응어가 성립하지 않는다는 사실 자체는 별도 신호로 볼 여지가 있다.",
  "conflict": null,
  "uncertain": true
},
{
  "id": "at-0271",
  "title": "불교 일반 — 분석이 지목한 화이트스페이스: '현대적 깊이'(현대성 × 종교적 깊이) 4분면이 비어 있다",
  "kind": "concept",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "전통↔현대 / 종교↔웰니스 2축 4분면에서 기독교·천주교=전통·종교, 명상앱=현대·웰니스, 사찰음식·템플스테이=전통·웰니스를 점유하고 '현대 × 종교적 깊이' 칸이 비어 있다는 판정. 근거 수치는 명상웰니스군의 라이프스타일성 32.8 대비 불교 56.1, 기독교 현대성 50.9 대비 불교 83.5.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/reports/04-인식변화-전략제언.html", "loc": "L77 (② 비어 있는 자리)", "quote": "현대 · 종교적 깊이 &nbsp;← 비어 있음 … '현대적 수행' (Life OS)" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/progress.md", "loc": "L19", "quote": "포지셔닝 빈 자리 = **\"현대적 깊이\"** (명상앱=현대·얕음 / 기독교=깊음·올드 사이)" }
  ],
  "basis": "analysis",
  "limitation": "'빈칸'은 3개 비교군만 놓은 좌표계에서 나온 것이다. 비교군에 요가·필라테스·심리상담·자기계발 커뮤니티 등 실제 경쟁 카테고리를 넣으면 이 칸이 비어 있지 않을 수 있다. 또 '깊이'는 측정된 값이 아니라 y축(라이프스타일성)의 역방향 해석이다.",
  "conflict": null,
  "uncertain": true
},
{
  "id": "at-0272",
  "title": "불교 일반 — 종교 호감도 54.4점으로 1위, 개신교 34.7점과 약 20점 격차 (한국리서치 2025)",
  "kind": "record",
  "maturity": "published",
  "ownership": "context",
  "summary": "100점 척도 호감도에서 불교 52.5(2023)→54.4(2025) 1위, 천주교 51.3→52.7 2위, 개신교 33.3→34.7 최하위. 신자 수는 개신교가 1위인데 호감도는 불교가 1위인 '교세–호감 역전 구조'.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/market-research.md", "loc": "L18-21", "quote": "**불교-개신교 호감 격차 ≈ 20점.** 신자수(개신교 1위) ↔ 호감도(불교 1위) **역전 구조**" }
  ],
  "basis": "secondary_data",
  "limitation": "한국리서치 종교인식조사 인용. 원 보고서 표본크기·조사방법·문항 표현은 워크스페이스에 미확보 — 재인용 상태다. 호감도는 태도 지표이지 방문·소비 의향이 아니므로, '호감 1위 → 방문 전환' 사이의 연결은 이 데이터로 입증되지 않는다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0273",
  "title": "불교 일반 — 비종교인 호감 1위 응답 20%, '매우 부정' 18%로 개신교(49%)의 1/2.7",
  "kind": "record",
  "maturity": "published",
  "ownership": "context",
  "summary": "비종교인이 가장 호감 가는 종교로 불교를 꼽은 비율 20%(천주교 13%, 개신교 6%). '매우 부정' 응답은 불교 18%, 천주교 19%, 개신교 49%. 리포트는 이를 '안티가 가장 적은 자산(blank canvas)'으로 규정했다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/reports/02-종교영성-경쟁분석.html", "loc": "L61, L66", "quote": "개신교의 '매우 부정' 49%는 불교(18%)의 <strong>2.7배</strong>다" }
  ],
  "basis": "secondary_data",
  "limitation": "한국리서치 재인용. 비종교인의 20%가 '호감 1위'로 꼽았다는 것은 80%는 다른 답을 했다는 뜻이기도 하다 — 리포트는 전자만 강조한다. 무관심(어느 쪽도 아님) 비율이 이 데이터에 표기되지 않았다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0274",
  "title": "불교 일반 — 한국 종교 보유율 2004년 54% → 2022년 37% → 2025년 40%",
  "kind": "record",
  "maturity": "published",
  "ownership": "context",
  "summary": "20년 사이 종교 인구가 17%p 감소했다가 2025년 소폭 반등. 종교별 신자 비율은 개신교 16~20%, 불교 16~18%, 천주교 6~11%(기관별 편차). 20대 종교율은 2004년 45%에서 2022년 19%로 급락.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/market-research.md", "loc": "L9-12", "quote": "종교 보유율: 2004년 54% → 2022년 37%(바닥) → 2025년 40%(소폭 반등)" }
  ],
  "basis": "secondary_data",
  "limitation": "한국갤럽·한국리서치·목회데이터연구소 3개 기관 값을 혼합 인용해 신자 비율에 기관별 편차 범위(16~20% 등)가 남아 있다. 2025년 40% '반등'이 추세 전환인지 단년 변동인지 판별할 시계열이 확보돼 있지 않다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0275",
  "title": "불교 일반 — MZ 탈종교: 18~29세 무종교 72%, 30대 64% (전년 대비 증가)",
  "kind": "audience",
  "maturity": "published",
  "ownership": "context",
  "summary": "2030이 탈종교화의 진앙. 리포트는 이를 '개종을 노리지 말고 호감 높은 무종교 2030을 신자가 아닌 이용자로 흡수하라'는 전략 액션의 근거로 사용했다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/market-research.md", "loc": "L10", "quote": "**2030 무종교: 18-29세 72%, 30대 64%** (전년 대비 증가) — 탈종교 진앙" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/reports/04-인식변화-전략제언.html", "loc": "L96 (④ 4대 전략 액션)", "quote": "근거: 2030 무종교 64~72% · 박람회 MZ 80%" }
  ],
  "basis": "secondary_data",
  "limitation": "무종교 비율은 '종교 없음' 응답일 뿐 '불교에 관심 없음'이 아니며, 반대로 '불교 콘텐츠 수요가 있다'는 근거도 아니다. 이 수치와 박람회 MZ 80%를 이어 붙이는 것은 서로 다른 모집단(전국 인구 vs 박람회 방문객)의 결합이다. 05 담론리포트는 별도로 '무종교 48%'라는 다른 값을 병기하고 있어 기준이 통일돼 있지 않다.",
  "conflict": "reports/05-불교담론-지형분석.html L104는 '무종교 48%'로 표기 — market-research.md의 64~72%와 모집단·정의가 다름",
  "uncertain": true
},
{
  "id": "at-0276",
  "title": "불교 일반 — 신자 고령화·저관여: 60대+ 43~56%, 청년 침투 8%, 주간 활동 4%",
  "kind": "audience",
  "maturity": "published",
  "ownership": "context",
  "summary": "불교 신자 구성에서 60대 이상이 43~56%, 청년층 침투율 8%, 주 1회 이상 종교활동 참여 4%. 개신교 주간 활동 55%와 대비된다. 리포트는 이를 '비호감이 아니라 올드함·저관여가 약점'이라는 진단의 근거로 사용했다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/reports/02-종교영성-경쟁분석.html", "loc": "L97 (③ 경쟁자별 강·약점 — 불교 약점)", "quote": "신자 고령화(60대+ 43~56%)</li><li>청년 침투 8%·주간활동 4%" }
  ],
  "basis": "secondary_data",
  "limitation": "43~56%라는 넓은 범위는 출처 기관이 다른 값을 합쳐 놓은 것이며 원 출처가 리포트에 개별 명기돼 있지 않다. 주간 활동 4%는 봉은사 같은 도심 대형사찰의 실제 방문 빈도와 다를 수 있다(전국 평균).",
  "conflict": null,
  "uncertain": true
},
{
  "id": "at-0277",
  "title": "불교 일반 — 개신교 '가나안 성도' 10.5%(2012) → 26.6%(2023), 20대는 45%",
  "kind": "record",
  "maturity": "published",
  "ownership": "context",
  "summary": "교회에 나가지 않는 개신교인 비율이 11년 만에 2.5배로 증가, 20대는 45%. 리포트는 개신교를 '조직 결속 강요 → 이탈'의 반면교사로 배치하고, 강요 없음·낮은 진입장벽을 불교의 반대 포지션으로 규정했다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/market-research.md", "loc": "L13", "quote": "개신교 가나안성도(교회 안 나감): 2012년 10.5% → 2023년 26.6% (2.5배). 20대 45%" }
  ],
  "basis": "secondary_data",
  "limitation": "목회데이터연구소 재인용. 개신교 내부 현상이며 불교에 그대로 대칭 적용되지 않는다 — 불교는 애초에 주간 활동률이 4%(at-0276)라 '이탈'을 셀 조직 소속 자체가 약하다. 반면교사 프레임은 해석이지 데이터가 보증하는 인과가 아니다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0278",
  "title": "불교 일반 — 서울국제불교박람회: 2024년 10만명(전년 3배)·MZ 80%, 2026년 25만명·2030 73%",
  "kind": "audience",
  "maturity": "published",
  "ownership": "context",
  "summary": "박람회 방문객의 2030 비중이 두 연도 모두 70~80%대. 2024년은 전년 대비 3배 증가·서버 마비, 슬로건 '재밌는 불교'. 2025년 코엑스는 '무해력'과 100인 MZ크루 운영. 리포트가 '수요 실증'으로 삼는 핵심 지표.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/market-research.md", "loc": "L37-38", "quote": "**서울국제불교박람회 2024: 10만명(전년 3배), MZ 80%**, 서버 마비. 슬로건 \"재밌는 불교\"" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/reports/05-불교담론-지형분석.html", "loc": "L104 (① 행위자×쟁점 — 대중)", "quote": "열광 — 박람회 25만('26)·2030 73%·무종교 48%" }
  ],
  "basis": "secondary_data",
  "limitation": "박람회 방문객은 자기선택 표본이라 '불교에 관심 있는 MZ'의 비율일 뿐 'MZ 일반의 불교 관심도'가 아니다. 2026-06-14 검증에서 10만('24)과 25만('26)은 연도 차이로 확정됐으나, MZ 80%와 2030 73%의 연령 구간 정의가 서로 다를 수 있다. 1회성 이벤트 방문이 지속 참여로 이어지는지는 이 데이터에 없다(at-0285 참조).",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0279",
  "title": "불교 일반 — 템플스테이 2024년 61.7만명 연인원 역대 최대(+13%, 누적 760만·외국인 11%), 2025년 순참가 35만·외국인 5.5만",
  "kind": "record",
  "maturity": "published",
  "ownership": "context",
  "summary": "템플스테이 참가가 사상 최대치를 경신. 61.7만은 2024 연인원, 35만은 2025 순참가로 집계 기준이 다르며 2026-06-14 검증에서 상충이 아님을 확인했다. 외국인 비율 11%는 누적 기준.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/market-research.md", "loc": "L39", "quote": "템플스테이 2024 **61.7만명 역대최대**(+13%, 누적 760만, 외국인 11%)" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/progress.md", "loc": "L48-49", "quote": "템플 35만('25 순참가) **연도·집계 명시** — 10만('24)·61.7만('24 연인원)과 충돌 아님(기준 차이)" }
  ],
  "basis": "secondary_data",
  "limitation": "한국불교문화사업단 발표 수치 재인용. 연인원/순참가/누적 세 기준이 섞여 있어 인용 시 기준 명시가 필수다. 산중 사찰 중심 프로그램의 수요이므로 도심 사찰(봉은사)의 프로그램 수요로 직접 환산되지 않는다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0280",
  "title": "불교 일반 — 매크로 수요: 글로벌 웰니스 6.8조$(2024), 정신웰니스 연평균 +12.4%(19~24), 미국 성인 명상률 17.3%",
  "kind": "record",
  "maturity": "published",
  "ownership": "context",
  "summary": "글로벌 웰니스 경제 6.8조 달러(+7.9%), 2029년 9.8조 전망. 정신웰니스는 2019~24 연평균 +12.4%로 최고 성장(2024~29 전망 +10.1%). 명상앱 시장 16억(2024)→22억 달러(2025), Calm 매출 5.96억. 미국 성인 명상률 17.3%(2022, 2012년 4.1%의 4.2배). 한국 '마보' 앱 누적 95만+·가입 45만+.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/market-research.md", "loc": "L30-33", "quote": "글로벌 웰니스경제 2024년 **6.8조 달러**(+7.9%), 2029년 9.8조. **정신웰니스 +12.4%**(2019~24 연평균, 최고 성장" }
  ],
  "basis": "secondary_data",
  "limitation": "Global Wellness Institute 등 산업 협회 추정치로 정의 범위가 넓다. 명상앱 22억 달러는 '명상 관리 앱' 협의 정의값(원문 명시). 미국 명상률은 국내 수요로 환산되지 않으며, 마보 앱은 누적 다운로드/가입 기준이라 활성 사용자가 아니다. 연령대 통계는 출처 미확보 상태로 원문에 표기돼 있다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0281",
  "title": "불교 일반 — 사찰음식의 글로벌 통화화: 정관 스님 넷플릭스 '셰프의 테이블'(2017), 프랑스 마스터셰프 200명 백양사 순례(2026)",
  "kind": "record",
  "maturity": "published",
  "ownership": "context",
  "summary": "사찰음식이 비건·웰니스 트렌드와 결합해 외국인·MZ 양쪽으로 확산. 오뚜기 두수고방·CJ 비비고 등 기업 협업 사례. 2026-06-14 검증에서 '정관 스님 제임스비어드상 본인 수상'은 오류로 확인돼 '해당 다큐가 방송부문 수상'으로 정정, 미쉐린 스타는 없음(2022 아시아 50 베스트 Icon Award가 권위 수상).",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": false },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/market-research.md", "loc": "L43", "quote": "해당 **다큐가 제임스비어드상 방송부문 수상**(스님 본인 수상 아님). **본인 미쉐린 스타 없음**" }
  ],
  "basis": "secondary_data",
  "limitation": "개별 사례 나열이며 사찰음식 시장 규모·성장률 같은 정량 지표가 없다. 이 항목은 최초 작성 시 수상 귀속 오류가 있었던 자리이므로 재인용 시 정정본(다큐 수상·미쉐린 없음)을 반드시 따라야 한다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0282",
  "title": "불교 일반 — 담론 지형: 5개 행위자 × 3대 쟁점 매트릭스 (학계·언론·종단지도부·실천스님·대중 × 현대화·상업화·웰니스화)",
  "kind": "concept",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "일반인 멘션과 별도로 학술·언론·불교 내부·글로벌 4축을 웹리서치해 행위자×쟁점 15칸을 4단계(◎열광/○긍정/△양가/✕비판)로 채운 구조도. 예: 언론은 웰니스화 ◎·상업화 ✕, 실천스님은 웰니스화 ✕·현대화 ○, 종단지도부는 현대화 ◎.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/discourse-research.md", "loc": "L17-28", "quote": "기호: ◎ 열광·적극 / ○ 긍정 / △ 양가·신중 / ✕ 우려·비판" }
  ],
  "basis": "analysis",
  "limitation": "정량 멘션과 달리 정성 인용 기반이며, 각 칸의 기호는 수집된 인용문에 대한 작성자의 판정이지 측정값이 아니다. 원문 한계 표기대로 중앙·한겨레 정식 사설은 미확보(경향·한경 중심)라 언론 행위자 칸이 특정 매체에 편중돼 있다.",
  "conflict": null,
  "uncertain": true
},
{
  "id": "at-0283",
  "title": "불교 일반 — 담론 구조는 갈등이 아니라 분업: 종단 지도부=액셀(방편 논리), 교계 지식인·실천 스님=브레이크(진정성 프레임)",
  "kind": "concept",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "종단 지도부는 재정·교세·세대 위기를 현대화로 돌파하며 '방편'을 정당화 논리로 쓰고(31년 만의 조직개편·미디어홍보실 신설·뉴진스님 법명 부여), 교계 지식인·실천 스님은 형식 변화는 수용하되 신행·수행·계율 본질 침식을 경계한다. 양쪽 모두 '포교 기회'라는 대전제는 공유하며 속도만 다투는 구조.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/discourse-research.md", "loc": "L10", "quote": "종단 지도부는 **액셀**(확장 프레임…), 교계 지식인·실천 스님은 **브레이크**(진정성 프레임…). 양쪽 다 \"포교 기회\"라는 대전제는 공유." }
  ],
  "basis": "analysis",
  "limitation": "행위자 유형을 2진영으로 압축한 해석이라 진영 내부 편차(종단 내 반대파, 지식인 내 적극 찬성파)가 지워진다. 인용된 발화자는 소수(법장·이상엽·인경·정관·묘장)이며 발화 빈도·대표성이 집계돼 있지 않다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0284",
  "title": "불교 일반 — 비판 강도는 상업성 노출도에 비례: 웰니스화 환영 → 현대화 조건부 → 직접 상업화 비판",
  "kind": "concept",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "템플스테이·사찰음식 같은 웰니스화는 환영, 힙불교 같은 현대화는 조건부 환영, 박람회 굿즈·관람료 같은 직접 상업화는 비판이라는 일관된 그라데이션. 구체 비판 표현으로 '불교 테마 잡화점', '수행·성찰 부스 소외, 주객전도'(박람회 관람객), 관람료에 대한 '통행세·산적'(시사저널·MBC)이 확인된다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/discourse-research.md", "loc": "L12", "quote": "**상업성이 노골적일수록 비판 강도↑** — 웰니스화…환영 / 현대화(힙불교)는 조건부 환영 / 직접 상업화…비판. 일관된 그라데이션." }
  ],
  "basis": "analysis",
  "limitation": "인용문 기반 패턴 판정이며 비판 강도를 정량화한 지표가 아니다. 다만 멘션 데이터의 '불신·상업화' 토픽 2.2%(at-0266)와 방향이 일치해 두 층위가 서로를 약하게 지지한다. 관람료 논란은 2023년 폐지로 일단락된 상태라 시점 차이에 주의.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0285",
  "title": "불교 일반 — 화제성은 신자 수로 전환되지 않았다: 2025 통계상 2030 신자 수 변화 없음",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "박람회 25만명·2030 73%·MZ 80% 같은 화제성 지표와 달리 2025 통계에서 2030 신자 수는 변화가 없다. 담론장은 이를 근거로 '화제성 ≠ 신심/깊이'를 공통 논리축으로 삼고, '파티 끝나고 술 깨면 무엇이 남나'(강성용), '사적재화형 종교'(법보신문, 이아나코네 개념 차용) 같은 표피성 경계를 반복한다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/reports/05-불교담론-지형분석.html", "loc": "L121 (② 갈등이 아니라 분업)", "quote": "공통 논리축은 \"화제성 ≠ 신심\" … 그리고 <strong>2025 통계상 2030 신자 수 변화 없음</strong>이라는 냉정한 데이터" }
  ],
  "basis": "secondary_data",
  "limitation": "'변화 없음'의 원 통계 출처·표본이 리서치 문서에 명기돼 있지 않아 재검증 필요. 이 atom은 at-0278(박람회 MZ 80%)과 정면으로 긴장 관계에 있으며, 봉은사 기획에서 MZ 유입을 근거로 쓸 때 반드시 함께 제시해야 하는 반대 증거다.",
  "conflict": "at-0278 — 박람회 MZ 80%·2030 73%의 '수요 실증' 서사와 신자 수 무변화가 정면 충돌. 원 리포트는 KPI 요약에서 전자만 노출한다",
  "uncertain": true
},
{
  "id": "at-0286",
  "title": "불교 일반 — McMindfulness 4단계 인과 사슬 (탈맥락화→도구화→개인화→신뢰붕괴)",
  "kind": "concept",
  "maturity": "published",
  "ownership": "context",
  "summary": "Ronald Purser(2019, 한국 태고종 수계 불교 교사) 비판을 4단계로 구조화. ①윤리·공동체·해방을 '짐'으로 떼고 측정·판매 가능한 기법만 추출('Buddhist meditation without the Buddhism') ②생산성·스트레스 관리에 종속('void of a moral compass' — 군 드론 조종사·헤지펀드 트레이더에게도 윤리 검토 없이 적용) ③고통 원인을 구조에서 개인으로 전가 ④'돈 받는 거래'로 인식되며 신뢰 붕괴. 미국 마인드풀니스 산업 규모 10억 달러 이상. Žižek(2001)은 서구 불교를 '자본주의의 완벽한 이데올로기적 보충물'로 규정.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": false },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/discourse-research.md", "loc": "L53-60", "quote": "① 탈맥락화 | 윤리·공동체·해방을 \"짐\"으로 떼고 측정·판매 가능 기법만 추출 | Purser \"without the Buddhism\"" }
  ],
  "basis": "secondary_data",
  "limitation": "서구 마인드풀니스 산업 비판이며 한국 사찰 운영에 그대로 적용되는 실증이 아니다. 4단계 사슬은 원저자가 제시한 도식이 아니라 이 리서치가 재구성한 것이다. 원문 한계 표기대로 '가장 날선 비판은 마음챙김 세속화 영역에 집중'돼 있어, 공간·프로그램 상업화 비판으로는 간접 근거다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0287",
  "title": "불교 일반 — 일본 장례불교 실패 선례: 1989~2019년 약 2,300만명 사찰과 인연 단절, 보시 부담 47.3%",
  "kind": "record",
  "maturity": "published",
  "ownership": "context",
  "summary": "일본은 장례의 90.1%가 불교식이지만 47.3%가 보시를 부담으로 느끼고, '장례에만 집중하는 사원'이라는 경멸적 명칭이 통용된다. 30년간 약 2,300만명이 사찰과 인연을 끊었고 오사카 사찰 매각·철거, 교토 사찰 주차장 전환이 공분을 샀다. 리포트는 이를 '수익 압박→과잉 상업시설→돈 받는 사원→이탈' 경로의 실증으로 사용한다.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": false },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/discourse-research.md", "loc": "L66", "quote": "90.1% 불교식 장례 but 47.3%가 보시 부담 … 1989~2019 2,300만명 이탈. 오사카 사찰 매각·철거" }
  ],
  "basis": "secondary_data",
  "limitation": "Buddhistdoor·Nippon.com 재인용이며 원 통계 방법론 미확인. 일본의 이탈은 단카(檀家) 제도라는 한국에 없는 구조에 기인한 부분이 크므로, 상업화만을 단일 원인으로 읽으면 과잉 일반화다. 2,300만이라는 수치는 리포트에서 '보시 36% 비판'과 '47.3% 부담' 두 값이 문서 간 혼용되고 있어 인용 시 확인 필요.",
  "conflict": "discourse-research.md L39는 '보시 36% 비판', L66은 '47.3%가 보시 부담'으로 서로 다른 값 병기",
  "uncertain": true
},
{
  "id": "at-0288",
  "title": "불교 일반 — 담론 리스크에서 역산한 4대 방어 원칙 (맥락 동반·총량 분리·투명성·참여)",
  "kind": "concept",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "글로벌 함정 4종을 각각의 방어선으로 번역한 것. ①McMindfulness→상업 접점마다 '왜 사찰인가' 본질 동반 ②일본 사찰화→상업 시설 총량·가시성 통제 + 수행/상업 공간 물리적 분리 ③신뢰 붕괴→보시·이용료 투명화(관람료 '통행세' 프레임 재점화 차단) ④Žižek 보충물→개인 웰니스를 넘어 공동체·사회 참여와 연결(참여불교 모델). 국내 발현 지표로 멘션 부정 토픽 2.2%를 방어선 수치로 설정.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": false, "time_bound": false },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/research/discourse-research.md", "loc": "L80, L82", "quote": "**총량·분리·투명성** — 상업 시설 양·가시성 통제, 본질/상업 공간 분리, 요금 투명 … 부정 토픽 2.2%(상업화·불신)가 바로 이 담론의 국내 발현" }
  ],
  "basis": "analysis",
  "limitation": "규범적 처방이지 관측 결과가 아니다. '총량 상한선'의 구체 수치(면적·매출 비중·시설 수)는 어디에도 정의돼 있지 않아 실행 기준으로 바로 쓸 수 없다. 방어선으로 삼은 2.2%도 at-0266의 채널 한계를 그대로 물려받아, 이 수치가 오르지 않는다고 해서 여론이 안전하다는 뜻은 아니다.",
  "conflict": null,
  "uncertain": false
},
{
  "id": "at-0289",
  "title": "불교 일반 — 2026-06-14 수치 검증 결과: 멘션 지표 전부 정확, 외부 인용 6종 정정",
  "kind": "record",
  "maturity": "shaped",
  "ownership": "context",
  "summary": "멘션 파생 수치(긍정 36.8·진정성 61.7·토픽·P/N)는 analysis.json과 리포트/PT가 전부 일치함을 확인. 외부 인용 6종은 정정: ①정관 스님 수상 귀속 오류 ②'서구 마인드풀니스 95% 불교 추출' 출처 불명으로 삭제 ③미국 명상률 18.3%→17.3%(NHIS) ④정신웰니스 +12.4%를 2019~24 연평균으로 명시 ⑤박람회·템플스테이 수치의 연도·집계기준 명시 ⑥템플 외국인 11%=누적 기준 명시.",
  "attributes": { "tangible": false, "ownable": false, "reproducible": true, "time_bound": true },
  "source": [
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/progress.md", "loc": "L42-46", "quote": "멘션 수치(analysis.json): **전부 정확** 확인 … 외부 수치 6종 정정 (웹 재확인)" },
    { "file": "/Users/choi_ai/do-better-workspace/90-archive/30-buddhism-brand-analysis/progress.md", "loc": "L55", "quote": "종교 멘션 수치는 키워드 휴리스틱 기반 → 정밀화 시 rxr-mention-analysis 풀 파이프라인 적용 가능" }
  ],
  "basis": "analysis",
  "limitation": "검증은 '리포트 값이 analysis.json과 일치하는가'(내적 정합)와 '외부 인용이 원출처와 일치하는가'(2차 대조)까지였고, 크롤링 방법론 자체(기간 비대칭·쿼리 편향·키워드 휴리스틱)는 검증 대상이 아니었다. 작성자 스스로 멘션 수치를 '키워드 휴리스틱 기반'으로 규정하고 정밀화 여지를 남겼다.",
  "conflict": null,
  "uncertain": false
}
]
```

## (2) 데이터 신뢰도 메모 — 봉은사 판단에 쓸 때의 한계

1. **채널 단일·우호 편향**: 전량이 네이버 블로그이고, 그것도 제목+요약(약 100자)만 수집했다. 블로그는 체험 후기·방문기 중심의 구조적 우호 채널이라 부정 2.2%는 여론이 아니라 이 채널의 하한값이다. 불교 비판이 실제로 몰려 있는 커뮤니티·유튜브 댓글·기사 댓글은 표본에 전혀 없다.
2. **3군 관측창이 7배 차이**: 불교 71일(4/4~6/13), 기독교 29일, 명상웰니스 10일. 리포트의 3군 KPI 정면 비교표는 서로 다른 기간의 값을 나란히 놓은 것인데, 이 사실이 리포트·PT 어디에도 표기돼 있지 않다.
3. **쿼리가 결과를 만들었다**: 불교 1,084건은 '템플스테이 후기·힙불교·불교 MZ·사찰음식' 등 이미 긍정 접점인 6개 키워드에서만 나왔고, 그중 196건(18.1%)은 아예 '봉은사' 검색어다. '불교 일반이 이러하니 봉은사가 적임'이라는 논증은 봉은사 데이터 18%가 섞인 순환 구조가 된다. '힙·현대화 토픽 37.5%'도 '힙불교'로 긁었기 때문에 나온 값이다.
4. **분석 엔진이 RXR 정식 파이프라인이 아니다**: 감성은 긍정어 20개·부정어 15개 단순 카운트, 진정성 61.7은 경험률×0.6+(100−홍보율)×0.4라는 임의 가중치의 근사값(코드 주석에도 '근사'). 포지셔닝 2축도 같은 토픽 비율에서 파생돼 서로 독립이 아니다. 작성자 본인이 progress.md에서 "키워드 휴리스틱 기반"이라 명시했다.
5. **가장 중요한 반대 증거가 요약에서 빠져 있다**: 박람회 MZ 80%·2030 73%는 KPI 배지로 크게 노출되지만, 같은 리서치가 확인한 "2025 통계상 2030 신자 수 변화 없음"은 담론 리포트 본문에만 있다. 봉은사 기획에서 MZ 유입을 근거로 쓸 때는 at-0285를 반드시 함께 놓아야 한다.

## (3) 폐기한 일반론 (atom으로 만들지 않은 문장 5개)

| 폐기 문장 | 출처 위치 | 폐기 사유 |
|---|---|---|
| "불교는 강요 없음·낮은 진입장벽·포용성을 가진, 안티가 가장 적은 종교(blank canvas)다" | market-research.md L25 | 수치 없는 성격 규정. '강요 없음'을 측정한 지표가 없다 |
| "현대인이 종교에 기대하는 것이 구원·내세에서 위로·의미로 바뀌었고, 불교는 이 변화에 구조적으로 들어맞는다" | 진단리포트 ④ 인식의 이동 벡터 | 어떤 종교에나 끼워 쓸 수 있는 서사. 이동 벡터 5줄 전부 데이터가 아니라 수사 |
| "문화센터는 불교를 믿게 하는 곳이 아니라 불교적 삶의 감각을 부담 없이 경험하게 하는 Gateway다" | 04-전략제언 ③ 전략 방향 | 컨셉 선언. 수치 근거 없고 봉은사 고유 자산도 아님 |
| "가볍게 들어와 깊게 머무는 동선" / "멋있고 존중할 만한 수행으로 번역" | 04-전략제언 ③·④ | 카피이지 발견이 아니다. 반증 불가 |
| "봉은사는 도심 입지(접근성)+1,200년 수행 자산(깊이)으로 이 자리에 설 수 있는 거의 유일한 후보다" | 04-전략제언 L79 | 이 리서치가 뒷받침하지 않는 결론. '유일'을 검증한 경쟁 사찰 비교가 0건이고, 애초에 봉은사 고유 주장이라 context 데이터로 등록하면 오인 위험 |

추가로, `불교-brand-analysis-제안서.html`(23p→26p PT)은 위 4개 리포트의 내용을 재배열한 파생 산출물이라 중복 atom을 만들지 않았다. 원자 근거는 전부 원본 리포트·리서치·analysis.json에서 잡았다.