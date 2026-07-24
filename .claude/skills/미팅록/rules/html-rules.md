# HTML 보고서 제작 규칙 — HTML Rules

## 템플릿

`templates/meeting-report-template.html` (FILAMENT data 스킨 — 화이트 배경·#FF6450 액센트·Pretendard)

모든 유형이 이 단일 템플릿을 사용한다.

## 제작 규칙

- `{{placeholder}}`를 실제 내용으로 치환
- 섹션 5개 고정, 내용 없는 섹션은 "해당 없음"으로 두되 삭제하지 않는다
- PDF 저장 버튼(우상단)·편집모드(좌상단 ✎)는 템플릿에 내장 — 제거하지 않는다
- [검토] 항목은 `.review` 박스 또는 인라인 `<span class="rv">[검토]</span>` 마커 사용

## 주의

이 스킬의 HTML은 R다크 테마가 아님 — 워크스페이스 기본 다크 스타일을 적용하지 말 것.
