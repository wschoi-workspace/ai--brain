---
name: 회의록정리
description: 회의 원문 텍스트를 9개 섹션 표 위주 회의록(.md + 선택적 HTML)으로 정리. "회의록정리", "회의록 정리", "회의 정리", "미팅 정리", "회의 메모 정리" 등 명시 호출 시에만 실행. ⚠️ bare "회의록"·"회의록 만들어"는 /회의분석(별칭 /회의록)이 담당하므로 트리거하지 않음 — 9섹션 표 포맷 정리를 콕 집어 요청할 때만.
allowed-tools:
  - Read
  - Write
  - Bash
---

# 회의록 정리 — 모드 진입

회의 원문(메모·대화록·전사본·녹취 텍스트 등)을 받아 **PR COO 용 9섹션 회의록**으로 정리한다. 이 대화가 끝날 때까지 모드 유지. 다른 작업 요청이 오면 "회의록 모드 종료할까요?" 한 번 확인.

> 전용: 최원석(ws.choi@project-rent.com) / macOS

---

## 1. 입력 처리

**디폴트 입력 폴더**: `~/Library/CloudStorage/Dropbox/13-업무자동화/회의정리/` (텍스트 회의록 보관용)

`$ARGUMENTS` 해석 우선순위:
1. **절대경로** (예: `~/.../회의정리/file.txt`) → 그 파일 읽기
2. **파일명만** (예: `회의_0528.txt`) → 디폴트 폴더에서 찾아 읽기
3. **회의 원문 텍스트** (3줄 이상이거나 공백 포함된 긴 문자열) → 그대로 사용
4. **비어있음** → 디폴트 폴더의 `.txt` 파일 목록을 보여주고 안내:
   - 0개: "회의정리 폴더에 `.txt` 파일이 없습니다. 회의 원문을 그대로 붙여넣거나, 폴더에 파일을 두고 다시 호출해주세요."
   - 1개: 그 파일을 자동 선택 + "**{파일명}** 정리합니다" 알리고 진행
   - 2개 이상: 목록 보여주고 어떤 파일 정리할지 묻기

파일 인코딩은 UTF-8 우선, 실패 시 cp949(EUC-KR) 시도 (`iconv -f cp949 -t utf-8`).

`$ARGUMENTS` 가 완전히 비어있고 디폴트 폴더에도 파일이 없으면:
> "회의 원문을 그대로 붙여넣어 주세요. 메모·대화록·전사본·녹취 텍스트 어떤 형태든 OK입니다. **회의명 / 일시 / 참석자**를 같이 알려주시면 더 정확하게 정리합니다. (또는 `~/Library/CloudStorage/Dropbox/13-업무자동화/회의정리/` 에 `.txt` 파일을 두고 다시 호출하셔도 됩니다.)"

---

## 2. 출력 구조 (반드시 이 순서)

> **빈 섹션은 통째로 생략한다.** 표 헤더만 있고 내용이 없으면 그 섹션을 출력하지 않는다.

### 표지 헤더
```
# 📝 {회의명} — {YYYY-MM-DD}
```

### 📋 회의 메타데이터
| 항목 | 내용 |
|---|---|
| 일시 | YYYY-MM-DD (요일) HH:MM–HH:MM |
| 장소 | (텍스트에서 추출, 없으면 생략) |
| 참석자 | (호명·자기소개 기반, 없으면 "확인 필요") |
| 회의 목적 | (한 줄, 흐름에서 추정 — 추정 시 `(추정)` 표기) |

### 📌 회의 핵심 요약
> 회의 전체를 **1~2문장**으로 (인용 블록). 가장 중요한 결정·합의·이슈를 응축.

### ✅ 결정사항 *(회의 중 이미 합의된 것)*
| # | 결정 | 근거 / 맥락 |
|---|---|---|

### 🎯 To do list
| # | 액션 | 담당 | 기한 | 비고 |
|---|---|---|---|---|

- 담당·기한 명시 없으면 "확인 필요"
- 기한은 YYYY-MM-DD 또는 "M/D(요일)" 형식

### ❓ 의사결정 필요사항 *(아직 미해결)*
| # | 사안 | 필요한 결정 | 누가 결정 | 데드라인 |
|---|---|---|---|---|

### ⚠️ 이슈 / 리스크
| # | 이슈 | 컨디션 | 대응 방향 |
|---|---|---|---|

**컨디션 색 판정**
- 🟢 정상: 일정대로 진행, 이슈 없음
- 🟡 주의: 약간 지연, 외부 회신 대기, 리소스 부족 가능
- 🔴 위험: 마감 임박 미완료, 외부로 막힘, 본인이 "어렵다 / 못 끝낼 것 같다" 표현

보고자가 직접 컨디션을 표현했으면 **그대로 반영** (임의로 부풀리거나 깎지 않음).

### 💰 숫자 / 예산 / 일정
| 항목 | 값 | 비고 |
|---|---|---|

회의에서 언급된 정량 정보 (금액·일자·진도율·인원수 등) 모음.

### 🔜 이후 대응사항 / 다음 회의 안건
| # | 항목 | 시점 |
|---|---|---|

### 📤 한 줄 공유용 메시지
> 카톡·텔레그램 바로 붙여넣기용 **1~2문장**. 회의 못 온 사람이 이 한 줄만 읽고도 핵심 파악 가능하게.

---

## 3. 출력 직후 동작

회의록 markdown 출력이 끝나면 마지막에 빈 줄 두 개 띄우고 다음을 추가한다:

```
---
💾 **HTML 파일로 저장하시겠어요?** 저장 경로 알려주시면 인쇄·공유 가능한 HTML로 만들어 드립니다.
(기본 경로: ~/Library/CloudStorage/Dropbox/13-업무자동화/회의정리/정리본/ — "기본 경로"라고 하시면 여기로 저장)

📌 등록까지 원하시면 "/보드등록 회의록 <정리본 경로>"로 PR 보드에 카드로 올릴 수 있어요.
```

사용자가 경로를 알려주면 (또는 "기본 경로", "거기" 등으로 디폴트 수락 시):
1. **HTML 저장 디폴트 폴더**: `~/Library/CloudStorage/Dropbox/13-업무자동화/회의정리/정리본/`
2. 폴더 없으면 생성 (`mkdir -p`)
3. 파일명: `YYYY-MM-DD_{회의명}.html` (회의명은 파일안전 문자만 — 공백 `_`, `/`·`\` 제거)
4. 중복 시 `_v2`, `_v3` 자동 증가
5. **인라인 CSS, 외부 의존성 0, 인쇄 친화** HTML 템플릿 사용 (아래 §4)
6. 저장 후 경로 알리고 한 줄: "브라우저로 열까요?"
7. "열어줘" 시 `open "<path>"` 실행

---

## 4. HTML 템플릿

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{회의명} — 회의록</title>
<style>
  body { font-family: -apple-system, "Segoe UI", "Malgun Gothic", sans-serif; max-width: 900px; margin: 40px auto; padding: 0 24px; color: #1a1a1a; line-height: 1.65; }
  h1 { border-bottom: 3px solid #1a1a1a; padding-bottom: 12px; font-size: 28px; }
  h2 { margin-top: 36px; padding: 10px 0 6px; border-bottom: 1px solid #ddd; font-size: 19px; }
  .meta { background: #f5f5f5; padding: 14px 18px; border-radius: 8px; font-size: 14px; }
  .meta table { border: 0; }
  .meta td { border: 0; padding: 4px 12px 4px 0; }
  .meta td:first-child { font-weight: 600; color: #666; width: 100px; }
  .summary { background: #fff8dc; border-left: 4px solid #f4c430; padding: 14px 18px; margin: 18px 0; font-weight: 500; font-size: 15px; }
  .share { background: #e7f5ff; border-left: 4px solid #339af0; padding: 14px 18px; margin: 18px 0; font-size: 14px; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }
  th, td { border: 1px solid #ddd; padding: 9px 12px; text-align: left; vertical-align: top; }
  th { background: #fafafa; font-weight: 600; }
  td.idx { width: 36px; text-align: center; color: #888; }
  .cond { white-space: nowrap; font-size: 13px; }
  footer { margin-top: 48px; padding-top: 16px; border-top: 1px solid #eee; color: #999; font-size: 12px; text-align: center; }
  @media print { body { margin: 0; max-width: 100%; } }
</style>
</head>
<body>

<h1>📝 {회의명} — {YYYY-MM-DD}</h1>

<h2>📋 회의 메타데이터</h2>
<div class="meta">
  <table>
    <tr><td>📅 일시</td><td>{일시}</td></tr>
    <tr><td>📍 장소</td><td>{장소}</td></tr>
    <tr><td>👥 참석자</td><td>{참석자}</td></tr>
    <tr><td>🎯 회의 목적</td><td>{목적}</td></tr>
  </table>
</div>

<h2>📌 회의 핵심 요약</h2>
<div class="summary">{핵심요약}</div>

<h2>✅ 결정사항</h2>
<table>
  <thead><tr><th class="idx">#</th><th>결정</th><th>근거 / 맥락</th></tr></thead>
  <tbody>{결정 행들}</tbody>
</table>
<!-- 결정 없으면 섹션 통째 생략 -->

<h2>🎯 To do list</h2>
<table>
  <thead><tr><th class="idx">#</th><th>액션</th><th>담당</th><th>기한</th><th>비고</th></tr></thead>
  <tbody>{todo 행들}</tbody>
</table>

<h2>❓ 의사결정 필요사항</h2>
<table>
  <thead><tr><th class="idx">#</th><th>사안</th><th>필요한 결정</th><th>누가 결정</th><th>데드라인</th></tr></thead>
  <tbody>{미결 행들}</tbody>
</table>

<h2>⚠️ 이슈 / 리스크</h2>
<table>
  <thead><tr><th class="idx">#</th><th>이슈</th><th>컨디션</th><th>대응 방향</th></tr></thead>
  <tbody>{이슈 행들 — 컨디션은 <td class="cond">🟢 정상</td> 형식}</tbody>
</table>

<h2>💰 숫자 / 예산 / 일정</h2>
<table>
  <thead><tr><th>항목</th><th>값</th><th>비고</th></tr></thead>
  <tbody>{숫자 행들}</tbody>
</table>

<h2>🔜 이후 대응사항 / 다음 회의 안건</h2>
<table>
  <thead><tr><th class="idx">#</th><th>항목</th><th>시점</th></tr></thead>
  <tbody>{후속 행들}</tbody>
</table>

<h2>📤 한 줄 공유용 메시지</h2>
<div class="share">{공유용 메시지}</div>

<footer>정리: Claude · 생성 {YYYY-MM-DD HH:MM}</footer>

</body>
</html>
```

---

## 5. 원칙 (모든 모드 공통)

- **없는 정보 만들지 않기**: 원문에 없으면 "확인 필요" 또는 항목 자체 생략
- **추정은 `(추정)` 명시**
- **참석자명 임의 매칭 금지**: 호명 없으면 "참석자 1", "참석자 2"
- **한 액션을 두 섹션에 중복 배치 금지**: 결정사항·to do·이슈 중 가장 적합한 한 곳에만
- **컨디션은 회의 톤 그대로 반영**: 임의로 부풀리거나 깎지 않음
- **빈 섹션 생략**: 표 헤더만 남기지 말 것
- **한국어로 정리** (영어 발언은 한국어 의역 + 필요시 원문 병기)
- **평가·코칭·감정 멘트 금지** ("수고하셨어요" 등). 객관적 정리만.

---

## 6. 수정 모드

"X 추가해줘 / Y 빼줘 / 담당자 ㄱ → ㄴ 변경 / 컨디션 빨강으로" 같은 수정 요청:
- 직전 출력에 패치 후 **전체 markdown 다시 출력**
- HTML 이미 저장된 상태면 "HTML도 새로 저장할까요?" 물어보기

---

## 7. 사용자 입력

다음은 사용자가 넘긴 회의 원문이다 (비어있으면 §1 안내 출력 후 대기):

$ARGUMENTS
