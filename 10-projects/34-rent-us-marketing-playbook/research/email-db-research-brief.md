# 추가 리서치 브리프 (C) — 미국 효과적 마케팅 + 이메일 DB 확보플랜 + 케이스

너는 프로젝트렌트 US 플레이북의 **추가 리서치**를 수행한다. 승인 없이 끝까지 실행하라.
병렬 리서치 에이전트를 미션별로 나눠 돌리고, 모든 수치·가격·업체링크는 3중 검증한다.

## 먼저 읽을 컨텍스트 (중복 금지·심화 확장)
- `10-projects/34-rent-us-marketing-playbook/research/tool-la-alternatives.md` (D Paid Digital, F 예약, G 측정)
- `10-projects/34-rent-us-marketing-playbook/us-marketing-playbook.md` 섹션 6 (QR→Email/SMS→CRM 스택) — 이미 다룬 것은 심화·확장하되 반복하지 말 것

---

## 미션 1 — 미국에서 가장 효과적인 마케팅 방식 (증거 기반)
**파일: `research/us-effective-marketing.md` (신규)**
- 채널별 ROI·효과를 데이터로 근거화해 "미국에서 무엇이 가장 효과적인가"를 정리.
  이메일 마케팅 ROI($/$1), SMS(오픈율·CTR), experiential, retail media, 인플루언서, 검색/SEO, 로컬 뉴스레터, 리퍼럴 등.
- **핵심 논점: 이메일 마케팅이 왜 미국에서 여전히 최고 ROI 채널인가**(업계 통설 $36~42/$1 등)를 복수 출처로 검증.
- 리테일/이벤트/소상공인 맥락 우선. 각 주장에 출처 URL + [추정] 태그. 표로 "채널 | 효과지표 | 강점 | 약점 | 출처".

## 미션 2 — 이메일 DB 확보플랜 (방문객→회원가입, a·b·c 3단계)
**파일: `research/email-db-acquisition-plan.md` (신규)**
방문객 여정 3단계로 구조화. **각 파트마다 업체 표**:
`업체명 | 공식링크 | 한줄 소개(2~3문장) | 핵심 기능 | 가격 | 비고(출처)`

- **a. 현장 캡처 (Venue Capture)** — 방문객이 이메일을 남기는 접점
  QR(Flowcode·Beaconstac/Bitly·QR Tiger), NFC 태그/밴드, 태블릿·키오스크 사인업(iPad 리드캡처 — Klaviyo/Mailchimp 태블릿 폼, TapMango), 이벤트 체크인(Luma·Eventbrite). 각 접점별 이메일 캡처율 벤치마크.
- **b. 회원가입·옵트인 전환 (Signup & Opt-in Conversion)** — 이메일을 받아내는 전환 장치
  인센티브(경품·할인·디지털 굿즈·스핀휠), 랜딩·팝업폼(Klaviyo Forms·Typeform·Unbounce·OptinMonster), 월렛 멤버십 패스(PassKit·Apple/Google Wallet), 더블옵트인·컴플라이언스(CAN-SPAM/TCPA). **현장 사인업 전환율 벤치마크** 포함.
- **c. CRM·이메일 포워딩·너처링 (Email Forwarding & Nurture)** — 확보 DB로 발송·자동화·리텐션
  ESP(Klaviyo·Mailchimp·Brevo·Customer.io·Omnisend), 웰컴/포스트이벤트 자동 플로우, 세그먼트, 리텐션·재방문. 가격·핵심기능·강점 비교.
각 업체는 **실제 공식 URL(WebFetch로 존재 확인)** + 2~3문장 소개 + 가격 필수.

## 미션 3 — 유사 패턴 참고 업체·마케팅 케이스
**위 `email-db-acquisition-plan.md` 하단 "참고 케이스" 섹션**
- 방문객→이메일 DB→포워딩(너처링)을 잘하는 브랜드/기업/팝업 **실제 사례**(링크 포함).
- experiential·팝업·리테일에서 QR·wallet·CRM으로 재방문·매출을 만든 케이스.
- 프로젝트렌트와 유사한 "경험+측정+CRM 결합" 비즈니스 모델 업체 벤치마크(예: AnyRoad·Leap 등 — 무엇을 어떻게 하는지).
- 각 케이스: 무엇을 했는가 / 성과(수치 있으면) / 시사점 / 출처.

---

## 검증·마무리 (필수)
- 3중 검증(추출→공식출처 대조→재대조). 가격은 공식 페이지 우선, 비공개는 RFQ, 불확실 `[추정]`/`[확인필요]`.
- **모든 업체 링크는 실재하는 공식 URL**이어야 함 — WebFetch로 200 확인, 죽은 링크 금지.
- `34-progress.md`에 "2026-07-07 추가리서치(C) 완료" 로그·액션 갱신.
- `git add -A && git commit -m "research(34): 미국 효과 마케팅 + 이메일 DB 확보플랜(a·b·c) + 참고 케이스"` 후 `git push origin HEAD:feat/34-us-marketing`(실패 시 커밋만).
- **HTML·PNG는 만들지 말 것** — 통합은 사용자 세션에서 한다.
