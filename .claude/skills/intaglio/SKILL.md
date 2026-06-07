# intaglio: 사진 → 요판화(凹版畫) 스타일 변환

사진 이미지를 요판화 기법(에칭, 인그레이빙, 메조틴트)으로 변환하는 필터 스킬.
"요판화", "intaglio", "에칭", "etching", "인그레이빙", "engraving", "메조틴트", "mezzotint", "판화 필터", "동판화" 등을 언급하면 자동 실행.

## 사용법

```
/intaglio [이미지경로] [스타일]
```

### 스타일 옵션
| 스타일 | 설명 | 특징 |
|--------|------|------|
| `etching` (기본) | 에칭 — 교차 해칭 + 에지 라인 | 산(acid)으로 부식시킨 동판 느낌. 명암에 따라 해칭 밀도 조절 |
| `engraving` | 인그레이빙 — 평행선 굵기 변조 | 지폐/우표 스타일. 수평선의 굵기로 톤 표현 |
| `mezzotint` | 메조틴트 — 점묘 + 그레인 텍스처 | 어두운 베이스에서 밝은 부분을 깎아내는 기법 재현 |

### 출력
- 형식: PNG (그레이스케일)
- 파일명: `{원본이름}-{스타일}.png`
- 동판 프레스 자국(플레이트 마크) 자동 추가

## 실행 프로세스

### 1단계: 이미지 경로 확인
- 사용자가 이미지 경로를 제공하지 않으면 요청
- PNG, JPG, JPEG 지원

### 2단계: 필터 적용

```bash
python3 00-system/02-scripts/intaglio-filter.py "{이미지경로}" {스타일}
```

### 3단계: 결과 확인
- 출력된 PNG 파일을 Read 도구로 확인하여 사용자에게 보여줌
- 필요시 파라미터 조정 후 재실행

## 스크립트 위치

`00-system/02-scripts/intaglio-filter.py`

## 의존성

- Python 3 + OpenCV (`opencv-python-headless`) + Pillow + NumPy
- 설치: `pip3 install opencv-python-headless Pillow numpy`

## 팁

- **사진(인물/풍경/건물)**에서 효과가 가장 좋음
- 텍스트/인포그래픽은 상대적으로 효과 약함
- etching이 가장 범용적, engraving은 공식문서/화폐 느낌, mezzotint는 예술적 분위기
