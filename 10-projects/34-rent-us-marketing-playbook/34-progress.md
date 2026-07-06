# 34 · 프로젝트렌트 US/LA 마케팅 진출 플레이북 — Progress

> 목적: 프로젝트렌트 US 진출 마케팅 플레이북(내부 범용). 개별 상품 30여 개를 LA 대안 +
> USD 가격으로 매핑하고, 시장·경쟁·규제·신규솔루션·리포지셔닝을 얹은 실행문서.
> 산출물: md 리서치 + project-rent 다크테마 HTML 덱.

## 원본 자료 (repo 편입 완료 — 맥미니가 Dropbox 없이 사용 가능)
- `source/profile-2026.txt` — 마케팅 profile 2026 IR 덱(42p): RaaS+OMO, People Counting 특허, 8개 팝업 사례
- `source/standard-guide.txt` — RaaS_OMO 스탠다드 가이드(44p): 3패키지 + 30여 개 개별 상품 원화 가격표

## 핵심 논지
경쟁력 = "채널"이 아니라 **오프라인 경험 설계·측정 방법론**. 채널(네이버·카카오·토스·
에브리타임)은 미국 치환 필요, 방법론(경험설계·People Counting·OMO 측정)은 미국 Experience
Economy에서 더 강한 무기.

## 작업 로그

### 2026-07-05
- [x] 기획 확정(플랜 승인): 목적=US 플레이북 / 형태=md+HTML 덱 / 범위=4영역 전부
- [x] 원본 PDF 2종 추출 → `source/` 편입
- [x] 프로그레스·리서치 브리프 작성
- [ ] 섹션2 센터피스: 개별 툴 × LA 대안 × USD 가격 리서치 (8개 카테고리 A~H)
- [ ] 3중 검증(추출→웹대조→재대조), 커버리지(30개 상품 누락 0)
- [ ] 메인 md 8개 섹션 통합
- [ ] HTML 덱 (사용자 리뷰 후)

## 맥미니 이관 상태 — 무인 자율 실행으로 확정
- foundation 커밋 완료: `9a7b77d` (source 2종 + 리서치 브리프 + progress)
- 실행 스크립트: `research/_macmini-launch.sh` (클립보드 복사됨) — claude 설치+인증+동기화+
  `--dangerously-skip-permissions` headless를 `screen rent34`로 무인 실행
- ⚠️ 로컬 `git push` 차단(설정 deny rule) → **사용자가 랩탑에서 직접 push** 필요:
  `git push origin HEAD:feat/34-us-marketing`
- ⚠️ 맥미니 `claude` 미설치·미인증 / Dropbox 없음(→source는 repo 편입으로 해결)

## 액션 아이템
1. [사용자·랩탑] `git push origin HEAD:feat/34-us-marketing` (제출 차단돼 수동)
2. [사용자·맥미니] 클립보드 스크립트 붙여넣기 → 인증(키 or `claude` 로그인) → 실행
3. [무인] 리서치·초안 커밋 → 이동 중 `ssh macmini-ts` / `screen -r rent34`로 확인
4. [복귀 후] 결과 3중검증 재대조 + HTML 덱 제작(사용자 리뷰)
