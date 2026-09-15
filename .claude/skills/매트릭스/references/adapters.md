# Adapters — 입력 4종 → IR 매핑

어댑터는 LLM이 수행한다(별도 스크립트 없음). 검증만 결정론적 규칙으로 한다.
아래 필드명은 워크스페이스 실제 산출물에서 확인한 것이다. 추측이 아니다.

---

## A. `rxr` — RXR / 브랜드 분석 JSON

### A-1. 집계형 (`analysis.json`) — 가장 잘 맞는 형태
경로 예: `90-archive/30-buddhism-brand-analysis/data/analysis.json`

실제 구조 (확인됨):
```json
{
  "불교":   { "n":1084, "topics":{"수행·명상":42.6,"전통·역사":12.9,"F&B·웰니스":34.3,
                                 "공동체·위로":13.6,"힙·현대화":37.5,"고루·접근성":1.3,"불신·상업화":2.2},
             "pos":36.8, "neg":2.2, "neu":61.0,
             "exp":47.1, "promo":16.4, "auth":61.7, "pos_neg_ratio":16.6,
             "x_modern":83.5, "y_life":56.1 },
  "기독교":  { ... }, "명상웰니스": { ... }
}
```

매핑:
| 스테이지 | role | 노드 | 링크 value |
|---|---|---|---|
| 세그먼트 | origin | 최상위 키 (`불교`, `기독교`, …) | — (노드 value = `n`) |
| 인식 토픽 | structure | `topics`의 각 키 (세그먼트별 개별 노드) | `round(n × topics[t] / 100)` |
| 감성 | synthesis | 긍정 / 중립 / 부정 | 토픽 노드 유입량을 `pos:neu:neg` 비율로 안분 |
| 결론 | conclusion | LLM이 생성 (근거 링크 필수) | 상류 합계 |

- `value_basis: "count"`, `value_note: "포스트 건수(토픽 비중 안분)"`
- **주의**: `topics` 합이 100%가 아니다(멀티라벨 — 위 예시는 합 144.4%). 각 토픽 값을 그대로 쓰면 노드 유출이 유입을 넘는다. **`n`을 토픽 비중으로 정규화 안분**하고, `value_note`에 "멀티라벨 비중을 건수로 안분함"을 명시한다. 이 각주를 빠뜨리면 숫자가 거짓이 된다.
- 토픽 노드는 세그먼트마다 별도로 만들되 `category`를 토픽명으로 통일 → 색이 이어져 세그먼트 간 비교가 된다.
- `auth`(진정성), `promo`(협찬)는 스테이지로 넣지 말고 **노드 `summary`와 근거 패널**에 표기. 계층에 섞으면 축이 흐려진다.

### A-2. 레코드형 (`*-2layer-results.json`, `*-classified.json`)
경로 예: `80-r-tech/85-analysis-results/{brand}/`

필드: `date, period, title, blogger, primary_topic, topic_scores{}, sentiment(긍정|중립|부정), rql(Q1~Q5_*), is_sponsored, post_class(A_자발적…), trust_score, content_class(A~G)`

매핑 (기본): `channel/post_class` → `primary_topic` → `sentiment` → 결론
- 링크 value = **레코드 개수 집계**. `value_basis: "count"`.
- `period`가 있으면 `axis:"time"` 모드로도 만들 수 있다 (`period` → `primary_topic` → `sentiment` → 결론).
- `is_sponsored: true`는 제외하지 말고 `category`로 분리 → 필터로 껐다 켰다 하게 둔다.

---

## B. `mpcf` — /perspective 산출물

경로: `[프로젝트]/perspective/perspective-map.json`
사양 SSOT: `00-system/01-templates/perspective-framework.md` §2

매핑 (MPCF가 이미 Sankey 4계층이다):
| 스테이지 | role | 노드 | 링크 |
|---|---|---|---|
| 콘텐츠 자산 | origin | `Atom` (`id`, `title`, `kind`) | — |
| 관점 렌즈 | structure | `Perspective` (`id`, `name`) | `Reading{atom_id → perspective_id}` |
| 군집·통찰 | synthesis | `Cluster` / `Insight` | `Cluster.readings[]`, `Insight.from_clusters[]` |
| 구성안 | conclusion | `Composition` (`title`, `type`) | `Composition.source_insights[]` |

- **`Reading`이 곧 링크 실체**다. `{atom_id, perspective_id}` 쌍이 source→target.
- value: Reading 개수(`count`) 또는 `evidence[]` 길이(`evidence`). 정성 판단만 있으면 `equal`.
- 결론 카테고리는 `Composition.type` 또는 `Composition.objective_check.verdict`(`meets`/`partial`/`deviates`) 3분류를 그대로 쓴다.
- `Reading.human_verdict`가 `drop`인 것은 링크에서 제외하되, `sharpen`은 `confidence:"medium"`으로 살린다.
- **`audience`는 스테이지로 넣지 않는다.** MPCF §2.4.1이 명시하듯 직교축이다. `category` 또는 필터로 처리한다. 렌즈 열에 섞으면 MPCF 원칙 P1(관점 간 상하 관계 없음)을 위반한다.
- `Reading.confidence`를 링크 `confidence`로 그대로 전달 → 렌더러가 `low`를 점선으로 그린다.

---

## C. `meeting` — 회의록·전사 (시간축)

### C-1. R4 세션 JSON — 기계 판독 가능한 유일한 회의 산출물
경로 예: `10-projects/39-r4-meeting-os/arisa-summary-europe-final.json`

실제 키 (확인됨):
```
title_guess, summary{purpose, key_decisions[], key_changes[{before,after}], top_action, risks[]},
basic_info{project,date,participants,decision_maker,meeting_type,purpose},
decisions[{title,decision,reason,impact}], changes[{before,after}],
discussions[], todos, support, risks, to_verify, next_steps, closing_note, quality_note
```

매핑 (`axis:"time"`):
| 스테이지 | role | 노드 출처 |
|---|---|---|
| 이전 상태 | origin | `changes[].before` (+ `discussions[]`의 쟁점) |
| 논의 | structure | `discussions[]`, `risks[]`, `to_verify[]` |
| 이후 상태 | synthesis | `changes[].after` |
| 결론 | conclusion | `decisions[]` → **확정 / 보류 / 폐기** 3분류 |

- **`changes[].before/after`가 링크로 직결된다.** 이게 이 어댑터의 급소.
- `decisions[].reason`을 링크 `evidence`로, `impact`를 결론 `so_what`으로.
- `risks[]` / `to_verify[]`는 버리지 말고 결론 스테이지의 **`미결(확인 필요)`** 노드로 흡수한다. 회의에서 안 끝난 것이 안 보이면 회의록이 아니다.
- `value_basis: "equal"` — 회의 항목에는 양이 없다. 두께 배지가 반드시 뜬다.

### C-2. 회의록 MD (`/미팅록`, `/회의록정리` 산출)
JSON이 없으므로 LLM이 본문에서 직접 추출한다. 결정사항·To-Do·이슈리스크 섹션을 위 4스테이지에 매핑. 원문 문장을 `evidence[].quote`에 **그대로** 넣고 `src`에 섹션명을 적는다.

---

## D. `free` — 자유 입력 (텍스트·CSV·JSON)

가장 자주 쓰이는 범용 경로다. 순서를 지킨다.

1. **훑기** — 반복되는 축이 무엇인지 찾는다. 축 후보: 주체 / 원인 / 시점 / 채널 / 유형 / 결과.
2. **계층안 3~5단계 제시** — 사용자에게 **반드시 확인받는다.** 여기가 결과 품질을 좌우한다.
   두 가지 안을 내는 게 좋다. 예: ① 원인 → 대응 → 결과 ② 주체 → 이슈 → 상태 → 결론
3. **value 결정**:
   - 표/CSV에 수치 열이 있으면 → `count`, 어느 열인지 `value_note`에 명시
   - 수치가 없으면 → `equal`. **임의로 중요도 가중치를 만들지 않는다.**
4. **결론 스테이지 생성** — 각 결론에 `support` 링크를 붙인다. 근거를 못 대는 결론은 만들지 않는다.
5. 원문이 있으면 `evidence[].quote`에 인용을 남긴다. 나중에 "이거 어디서 나온 말이지"를 화면에서 되짚을 수 있어야 한다.

CSV 특수 규칙: 열 이름이 곧 스테이지, 행이 곧 경로다. 같은 경로가 여러 행이면 그 반복 횟수가 자연스러운 `count`가 된다.

---

## 어댑터 공통 — 하지 말 것

- 데이터에 없는 노드를 "흐름이 예뻐 보이려고" 넣지 않는다.
- 결론 스테이지 외의 계층을 LLM이 창작하지 않는다. 원 데이터의 필드에서 온 것이어야 한다.
- 유실(유입 > 유출)을 숨기려고 링크 값을 늘리지 않는다. `미분류` 노드로 흡수한다.
- 노드가 40개를 넘으면 읽히지 않는다. **상위 N개 + `기타(n건)` 노드로 접되, 접었다는 사실을 화면과 보고에 명시**한다. 조용한 절삭은 "전부 다뤘다"는 오해를 만든다.
