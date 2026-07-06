# 봉은문화센터 설문 — 배포 & 데이터 취합 가이드

온라인 설문(Vercel) + 응답 수집(Apps Script → 구글시트). 아래 **2단계만** 하시면 수집이 시작됩니다.
(구글시트·헤더·집계 함수는 이미 세팅 완료)

## 구성
| 파일 | 역할 |
|------|------|
| `index.html` | Vercel에 올릴 설문 웹앱 (22문항 + 자유의견) |
| `apps-script.gs` | 구글시트에 붙일 응답 수집 + 집계 코드 |
| `vercel.json` | Vercel 배포 설정 |

## ✅ 이미 완료된 것 (내가 세팅)
- 응답 수집 시트 생성 + **`응답` 탭 + 헤더 24열**(timestamp·Q1~Q22·자유의견) 입력 완료
  → **https://docs.google.com/spreadsheets/d/12ESWt5ocwVVTDa_15LcZX1SOJOWSKvH2gB6nacsS50c/edit**
- `apps-script.gs`에 doPost(수집) + `setupAggregation`(동의율·분포·교차분석) 준비

---

## STEP 1 · Apps Script 배포 (≈ 3분)
1. 위 구글시트 → 상단 **확장 프로그램 → Apps Script**
2. 기본 코드 지우고 `apps-script.gs` 전체 **복사 → 붙여넣기 → 저장**
3. 우측 상단 **배포 → 새 배포 → (유형) 웹 앱**
   - 실행 계정: **나**
   - 액세스 권한: **모든 사용자** ← 익명 수집에 필수
4. **배포 → 권한 승인 → 웹 앱 URL 복사** (`https://script.google.com/macros/s/AKfyc.../exec`)
5. `index.html` 의 `const APPS_SCRIPT_URL = "";` → 따옴표 안에 그 URL 붙여넣기 → 저장

## STEP 2 · Vercel 배포 (≈ 3분, 대시보드 권장)
> 이 PC의 npm 권한 이슈로 CLI(`npx vercel`)가 막혀 있어 **대시보드 방식**을 권장합니다.

1. [vercel.com](https://vercel.com) 로그인 → **Add New → Project**
2. **이 `bongeunsa-survey` 폴더를 끌어다 놓기**(Drag & Drop Deploy) — Git 없이 바로 배포됨
3. 배포 완료 → `https://xxxx.vercel.app` 주소 발급 → **이 주소를 응답자에게 공유**

(또는 npm 권한 복구 후 CLI: `sudo chown -R 501:20 ~/.npm` → `cd bongeunsa-survey && npx vercel --prod`)

---

## 데이터 취합 & 분석
- 응답이 들어오면 시트 `응답` 탭에 한 줄씩 누적됩니다.
- Apps Script 편집기에서 **`setupAggregation` 1회 실행** → `집계` 탭 자동 생성:
  - **동의율**(Q5·Q6·Q9: 매우동의+동의 비율) + 평균
  - 핵심 단일문항 분포(연령·종교·구조·우려·미래방향 등)
  - 복수응답·교차분석 수식 예시
- **핵심 교차분석**(보고서용): *비불교인의 동의율* → "종교를 넘어선 사회적 합의" 근거
  `=COUNTIFS(응답!C2:C,"<>불교",응답!F2:F,"<=2")/COUNTIF(응답!C2:C,"<>불교")`

## 점검 체크리스트
- [ ] Apps Script 액세스 권한 = **모든 사용자**
- [ ] `index.html`의 `APPS_SCRIPT_URL` 입력 완료
- [ ] 테스트 1건 제출 → `응답` 탭에 행 들어오는지 확인
- [ ] Vercel 주소를 모바일에서 열어 응답·제출 확인

## 설문이 검증하는 6대 가설
1. 현대인은 정신문화 공간을 필요로 하는가 (Q5)
2. 불교는 수행 중심 가치를 회복해야 하는가 (Q9·Q10)
3. 봉은사는 서울의 정신문화 랜드마크가 될 수 있는가 (Q6·Q18)
4. 문화센터는 본원의 Gateway여야 하는가 (Q12)
5. 어느 수준까지 문화화·상업화가 허용되는가 (Q15·Q16·Q17)
6. "수행 기반 문화 플랫폼" 방향에 사회적 공감이 있는가 (Q21)
