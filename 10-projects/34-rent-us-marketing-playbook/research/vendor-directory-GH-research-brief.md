# 추가 리서치 브리프 (E) — G·H 카테고리 업체 디렉토리(세부가이드)

너는 프로젝트렌트 US 플레이북의 **카테고리 G·H 업체 디렉토리**를 만든다. 승인 없이 끝까지 실행하라.
A~F 디렉토리(`vendor-directory-A-F.md`)와 **완전히 동일한 포맷·밀도**로 이어 붙일 G·H 편을 작성한다.

## 먼저 읽을 것 (포맷·씨앗)
- `research/vendor-directory-A-F.md` (포맷 기준 — 표 컬럼·선택가이드·비고(출처) 구조를 그대로 따를 것)
- `research/tool-la-alternatives.md` G·H 섹션 (씨앗 — named 업체·공식링크·서비스종류로 확장)

## 미션 — `research/vendor-directory-G-H.md` (신규)
2개 섹션(G·H). **각 섹션마다 업체 표**:
`업체명 | 공식링크(WebFetch 200 확인) | 기본 서비스(무엇을 파는가) | 가격 | 가능한 마케팅 서비스 종류`
각 섹션 하단에 "선택 가이드" 2~4줄 + "비고(출처)".

- **G. 측정 / 리포트 / 설문**
  - 방문객·트래픽 실측(피플카운팅): Placer.ai · Dor · Density · RetailNext · V-Count · Vemcount · Aislelabs · Sensormatic ShopperTrak 등
  - 설문 SaaS(DIY): Typeform · SurveyMonkey · Qualtrics · Jotform · Google Forms
  - 패널·현장 리서치: Pollfish · SurveyMonkey Audience · Drive Research(인터셉트) · 기타 인터셉트 대행
  - 브랜드 인지/리프트: Suzy · Attest · YouGov BrandIndex · (플랫폼 brand lift: Meta/LinkedIn)
  - 서비스종류=실측 트래픽/전환 분석·존별 동선·설문·brand lift·post-event 리포트
- **H. 영상 / 사진**
  - 사진 마켓플레이스/프리랜서: Snappr · Thumbtack · Splento · 로컬 LA 스튜디오
  - 비디오그래퍼/프로덕션: Thumbtack · 로컬 LA 프로덕션(이벤트 recap/highlight)
  - UGC 제작: Billo · Insense · Trend.io · Fiverr · Upwork (B 카테고리와 중복 시 "영상 제작 관점"으로 재기술)
  - 숏폼 제작 에이전시/스튜디오: Vidico · DMAK Productions 등
  - 편집 전문: Fiverr/Upwork 편집, 전문 편집 스튜디오
  - 서비스종류=공간/이벤트 사진·recap 영상·UGC 숏폼·인터뷰/테스티모니얼·편집

## 검증·마무리 (필수)
- 3중 검증(추출→공식출처 대조→재대조). 가격은 공식 페이지 우선, 비공개는 RFQ, 불확실 `[추정]`/`[확인필요]`.
- **모든 업체 링크는 실재하는 공식 URL** — WebFetch 200 확인, 죽은 링크 금지(리다이렉트/변경 시 실 URL로 교체).
- 기존 tool-la-alternatives.md G·H와 상충하면 최신 공식가 우선 + 상충 사실 표기.
- `34-progress.md`에 "2026-07-08 업체 디렉토리 G·H(E) 완료" 로그 추가.
- `git add -A && git commit -m "research(34): G·H 카테고리 업체 디렉토리(세부가이드)"` 후 `git push origin HEAD:feat/34-us-marketing`(실패 시 커밋만).
- **HTML·PNG는 만들지 말 것** — 통합·시각화는 사용자 세션에서.
