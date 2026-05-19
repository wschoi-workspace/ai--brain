# 80-R_tech

> R-lab 기술 레지스트리 — RXR Master Framework 기술 스택 및 구현 현황
> 최종 업데이트: 2026-04-06

---

## 개요

RXR Master Framework의 기술 구현 현황, 오픈소스 스택, 구현 로드맵을 관리하는 폴더.

**원칙:** 기술은 오픈소스일 뿐. 해석 프레임 + 변환 테이블이 자산.

---

## 기술 스택 총정리

### 핵심 오픈소스 기술

| 기능 | 기술 | 용도 | 라이선스 | 정확도 |
|------|------|------|:---:|:---:|
| 사람 감지 | YOLOv8 (Ultralytics) | L0 유동인구, L2 진입 | MIT | 92~95% |
| 다중 추적 | BoT-SORT | L2 진입, L3 동선 | Apache 2.0 | 94~97% |
| 시선/체형 | MediaPipe Pose/Face | L1 시선, 체형 추정 | Apache 2.0 | 70~80% |
| 아웃핏 분류 | DeepFashion2 + ResNet/EfficientNet | 라이프스타일 세그먼트 | MIT/Apache | 80~88% |
| 컬러 추출 | OpenCV HSV | 아웃핏 컬러 팔레트 | Apache 2.0 | 95%+ |
| Re-ID (세션) | OSNet (의류+체형 임베딩) | L5 당일 재방문 | MIT | 80~90% |
| 감성 분석 | KoBERT / HuggingFace Transformers | L7 Content Layer | MIT/Apache | 78~85% |
| 형태소 분석 | KoNLPy (Mecab) | L7 Psyche Layer (FWA) | GPL/Apache | — |
| 대시보드 | FastAPI + React/Next.js | 시각화 | MIT | — |
| PDF 생성 | Playwright | 슬라이드 → PDF | Apache 2.0 | — |

### 인프라 요구사항

```
CCTV 기반 필수:
  ☐ 카메라 2대+ (최소 720p, 권장 1080p+)
  ☐ GPU 서버 (NVIDIA T4 이상)
  ☐ 영상 저장소 (30일분 ≈ 5TB)
  ☐ 실시간 처리 파이프라인

매장 시스템:
  ☐ POS 시스템 API 연동 (L4)
  ☐ 회원 CRM 시스템 (L6)
  ☐ 매장 내 서베이 시스템 - QR 기반 (서베이)
  ☐ DID 콘텐츠 스케줄링 시스템 (L0~L1)

외부 데이터:
  ☐ SNS 크롤링 API - 네이버/인스타그램 (L7)
  ☐ 온라인 판매 플랫폼 API (OMO)
```

---

## 층위별 구현 현황 (2026-04-06)

| 레벨 | 기능 | 구현도 | 기술 | 다음 단계 |
|:---:|------|:---:|------|------|
| **L0** | 유동인구 카운팅 | ✅ 100% | YOLOv8 | 안정화 |
| **L1** | 시선 추적 | △ 50% | MediaPipe | IR 카메라 추가로 정확도 개선 |
| **L2** | 매장 진입 감지 | ✅ 95% | BoT-SORT | 직원 제외 로직 개선 |
| **아웃핏** | 라이프스타일 분류 | ⬜ 설계됨 | DeepFashion2+CNN | Phase 1에서 프로토타입 |
| **L3** | 체류 시간 (절대) | △ 30% | 프레임 범위 | Zone 설정 + DQS 구현 |
| **L3** | DQS (체류 품질) | ⬜ 수식 설계됨 | — | 기대 체류 기준표 + 밀도 계수 |
| **L4** | 구매 전환 (POS) | ⬜ 0% | POS API | 자사 매장 POS 연동 |
| **L5** | 재방문 (세션 내) | ⬜ 설계됨 | OSNet Re-ID | 의류 기반 세션 내 Re-ID |
| **L5** | 재방문 (일간) | ⬜ 설계됨 | 회원 앱 | 회원 전환 유도 전략 |
| **L6** | 회원 CRM | ⬜ 10% | Odoo/커스텀 | CRM 시스템 구축 |
| **L7** | 리뷰 크롤링 | ⬜ 0% | API 크롤러 | 네이버/인스타 크롤러 |
| **L7** | Content Layer | ⬜ 0% | KoBERT | 감성분석 모델 학습 |
| **L7** | Psyche Layer (FWA) | ⬜ 0% | K-LIWC+KoNLPy | FWA 파이프라인 구축 |
| **L7** | RQL (후기 품질) | ⬜ 수식 설계됨 | — | 자동 판정 파이프라인 |
| **C.C** | AI 고객 카테고리 | ⬜ 설계됨 | K-means/DBSCAN | 데이터 축적 후 |
| **OMO** | 온·오프 통합 | ⬜ 설계됨 | API 파이프라인 | Phase 3 |

---

## RXR 핵심 독점 설계 (경쟁사 미보유)

| 설계 | 내용 | 상태 |
|------|------|:---:|
| **DQS** (Dwell Quality Score) | 체류시간의 4차원 복합 측정 — `(실제/기대) × 밀도 × 세그먼트 보정` | 수식 완료 |
| **RQL** (Review Quality Level) | 후기 질적 깊이 5단계 — `가중 L7 = RQL × Authenticity × Clout` | 수식 완료 |
| **행동↔심리 변환 테이블** | 서베이 기준점 → 행동만으로 인게이지먼트 추론 | 설계 완료, 데이터 필요 |
| **멘탈코스트 인게이지먼트 L0~L7** | 전환별 심리적 비용 기반 관계 깊이 | 정의 완료 |
| **2-Layer Algorithm** | Content(n-gram) + Psyche(FWA) 이중 분석 | 설계 완료 |
| **아웃핏 세그먼트 7군** | 패션 타입 → 라이프스타일 분류 (얼굴 인식 없이) | 설계 완료 |
| **구매 유형 4분류** | 확신/충동/목적/동반 — DQS+동선으로 자동 판별 | 설계 완료 |
| **진입 품질 4분류** | 목적/유인/동반/통과 — 외부↔내부 행동으로 판별 | 설계 완료 |
| **Sincerity Gate 3단계** | Gate 1(전체) → Gate 2(협찬제외) → Gate 3(Auth 60+) 단계적 정제 | **파일럿 실증 완료** |
| **Account Trust Level** | T1 순수개인 ~ T5 위장계정, 5단계 계정 신뢰도 분류 | 설계 완료 |
| **Sincerity Filter** | 리그램/단순공유, 보도자료복붙, 위장계정, 나열형 자동 태깅 | **v1.0 구현 완료** |

### Sincerity Filter v1.0 — Raw Data 자동 분류 체계

이클립스 월드 파일럿(2026.04)에서 개발 및 실증.

**Content Class 6단계:**

| 등급 | 분류 | 감지 방법 | 분석 처리 |
|:---:|------|------|------|
| **A** | 진성후기 | 개인 경험 신호 2건+, 구체적 디테일 3건+ | 2-Layer 핵심 분석 대상 |
| **B** | 일반포스트 | 특별 플래그 없음 | 2-Layer 분석 대상 |
| **C** | 협찬 | "제공받", "#광고", "체험단" 등 감지 | 2-Layer 분석 (진심 스펙트럼) |
| **D** | 나열형정보 | "총정리", "리스트", "모음" 제목 | 버즈량만 카운트 |
| **E** | 리그램/단순공유 | "리그램", "퍼옴", 해시태그만 있는 글 | 버즈량만 카운트 |
| **F** | 비즈니스/보도자료 | 보도자료 문구 3건+ 매칭, 비즈니스 신호 2건+ | 제외 또는 카운트만 |

**Trust Score 산출:**
- 기본 100점에서 감점 방식
- 리그램 -30, 해시태그만 -25, 보도자료복붙 -35, 비즈니스위장 -25, 나열형 -20, 협찬 -15
- 개인경험 +15, 구체적디테일 +10 (가점)
- 70+ = 신뢰 가능, 40~69 = 주의, ~39 = 필터 대상

**파일럿 결과 — Gate 3 적용 효과:**
- Gate 1(전체 90건): 긍정 46%, Auth 57.2
- Gate 3(Auth 60+ 64건): 긍정 33%, Auth 64.4
- → **진심 필터 적용 시 긍정률 13%p 하락** = 과장된 긍정 26건이 걸러짐

---

## 개인정보보호 정책

| 원칙 | 내용 |
|------|------|
| **얼굴 인식 금지** | Re-ID는 의류+체형 기반만 사용 |
| **세션 기반** | 매장 퇴장 시 임시 ID 즉시 삭제 |
| **이미지 미저장** | 분석 후 원본 프레임 삭제, 벡터만 저장 |
| **CCTV 안내** | 매장 입구 촬영 안내문 게시 |
| **데이터 보관** | 영상 30일, 분석 데이터 1년 |
| **접근 제한** | 분석 담당자만 데이터 접근 |

---

## 구현 로드맵

### Phase 1: Bracket 파일럿 (즉시~3개월)
1. L0~L2 안정화
2. **아웃핏 AI 프로토타입** (7세그먼트, 수동 레이블링 500건)
3. L3 DQS v1.0 (Zone + 기대 체류 기준)
4. 리워드 서베이 시스템

### Phase 2: 데이터 축적 (3~6개월)
5. L4 POS 연동 (자사 매장)
6. **행동↔심리 변환 테이블 v1.0**
7. 아웃핏 × 구매 교차 분석
8. L7 리뷰 크롤링 + 2-Layer 파이프라인

### Phase 3: 통합 (6~12개월)
9. L6 회원 CRM 구축
10. **AI C.C 통합 세그먼테이션**
11. OMO 온·오프 연결
12. 외부 Basic 서비스 론칭

---

## 폴더 구조

```
80-r-tech/
├── 81-framework/         방법론·개념·알고리즘 문서
├── 82-case-reports/      브랜드별 케이스 리포트 (ghana/saero/beyond/comonstyle/eclipse)
├── 83-slides/            발표 슬라이드 (pptx/pdf/html) — 구버전은 archive/
├── 84-scripts/           자동화 스크립트 (_common + 브랜드별)
├── 85-analysis-results/  원본·가공 데이터 (brand/raw·filtered·결과)
└── 86-templates/         재사용 설문·감사 템플릿
```

**논리 흐름**: `81 (프레임워크)` → `84 (스크립트 실행)` → `85 (원본·가공 데이터)` → `82 (브랜드 리포트)` → `83 (발표)` / `86 (재사용 템플릿)`

---

## 네이밍 규칙

| 항목 | 규칙 | 예시 |
|---|---|---|
| 날짜 | ISO `YYYY-MM-DD` | `rxr-analysis-saero-2026-04-05` |
| 구분자 | 문서는 `-`, Python은 `_` | `saero-popup-report.html`, `saero_crawl.py` |
| 언어 | 영문 소문자 (브랜드명 영문 표기) | `ghana-chocolate` |
| 버전 | `-v2`, `-v3` 접미사 / 구버전은 `archive/`로 이동 | `ghana-perception-shift-v2.html` |
| 리포트 변형 | `-external` (공개용) / `-locked` (내부용) / 기본 (작업본) | `beyond-popup-rxr-sns-report-external.html` |

---

## 관련 문서

| 문서 | 위치 |
|------|------|
| RXR 마스터 프레임워크 v1.1 | `81-framework/rxr-master-framework.md` |
| 마스터 프레임워크 슬라이드 | `83-slides/rxr-master-framework-slides.pdf` |
| 층위별 고도화 가이드 | `81-framework/rxr-layer-implementation-guide.md` |
| 고도화 슬라이드 | `83-slides/rxr-layer-implementation-slides.pdf` |
| 4축 종합 검토 보고서 | `81-framework/rxr-4axis-framework-review.md` |
| 4축 비즈니스 피치덱 | `83-slides/rxr-4axis-business-pitch.pptx` |
| 데이터 로직 전략 | `81-framework/rxr-data-logic-strategy.html` |
| 2-Layer 분석 알고리즘 | `81-framework/rxr-2layer-analysis-algorithm.html` |
| EMV 개념 가이드 | `81-framework/emv-concept-guide.html` |
| 경쟁사 심화 리서치 | `81-framework/retail-tech-solutions-deep-research.md` |
| FWA 학술 리서치 | `81-framework/function-word-analysis-research.md` |
| 가나초콜릿 FWA 케이스 | `81-framework/ghana-chocolate-function-word-analysis.md` |
| Bracket 특허 문서 | Dropbox: `02-프로젝트렌트RENT/03_R-lab/01.분석솔루션/` |

---

## 브랜드 케이스 인덱스

| 브랜드 | 케이스 리포트 | 원본 데이터 | 스크립트 |
|---|---|---|---|
| **Ghana** (초콜릿) | `82-case-reports/ghana/` (5개, perception-shift v1/v2 포함) | — | `84-scripts/ghana/` (5개) |
| **Saero** (팝업) | `82-case-reports/saero/` (5개) | `85-analysis-results/saero/` (8개) | `84-scripts/saero/` (3개) |
| **Beyond** (팝업) | `82-case-reports/beyond/` (4개) | `85-analysis-results/beyond/` (6개) | `84-scripts/beyond/` (2개) |
| **Comonstyle** (팝업) | `82-case-reports/comonstyle/` (3개) | `85-analysis-results/comonstyle/` (5개) | `84-scripts/comonstyle/` (4개) |
| **Eclipse** (팝업) | `82-case-reports/eclipse/` (3개) | `85-analysis-results/eclipse/` (19개, 파일럿 완료) | `84-scripts/eclipse/` (1개) |
| **HelloKitty × Jisoo** | — | `85-analysis-results/hellokitty-jisoo/` (5개) | `84-scripts/hellokitty/` (2개) |

---

> Project RENT · R-lab · 2026
