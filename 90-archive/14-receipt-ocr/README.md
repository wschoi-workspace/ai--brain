# 영수증 OCR → Excel 변환기

영수증 이미지 폴더를 선택하면 Gemini 2.5 Flash로 OCR 처리하여 Excel 파일로 정리해주는 툴.

## 추출 필드 (7개)

| 필드 | 설명 |
|------|------|
| 날짜 | 거래일자 (YYYY-MM-DD) |
| 상호 | 매장명 |
| 사업자번호 | 123-45-67890 형식 |
| 총금액 | 최종 결제금액 |
| 결제수단 | 카드 / 현금 / 기타 |
| 주소 | 매장 주소 |
| 원본파일명 | 이미지 파일명 |

## 지원 이미지 포맷

`.jpg`, `.jpeg`, `.png`, `.webp`, `.heic` (iPhone)

## 개발 환경 실행

### 1. 의존성 설치

```bash
cd 10-projects/14-receipt-ocr
pip install -r requirements.txt
```

### 2. API 키 설정

`.env` 파일에 Gemini API 키 입력:
```env
GEMINI_API_KEY=your_key_here
```

### 3. GUI 실행

```bash
python3 src/gui.py
```

### 4. CLI 테스트 (단일 이미지)

```bash
python3 src/receipt_ocr.py sample/receipt_001.jpg
```

### 5. CLI 테스트 (폴더 전체)

```bash
python3 src/receipt_ocr.py sample/
```

## 비용 예상

- **Gemini 2.5 Flash**: 영수증 100건당 약 300~700원
- 실제 비용은 이미지 크기/해상도에 따라 변동

## Windows .exe 빌드 가이드

Mac에서는 Windows .exe를 직접 빌드할 수 없음. Windows PC에서 진행.

### Windows PC에서

```bash
# 1. Python 3.10+ 설치
# 2. 이 프로젝트 폴더 복사
# 3. 가상환경 생성
python -m venv venv
venv\Scripts\activate

# 4. 의존성 설치
pip install -r requirements.txt
pip install pyinstaller

# 5. .exe 빌드
pyinstaller --onefile --windowed --name "ReceiptOCR" src/gui.py

# 결과물: dist/ReceiptOCR.exe
```

### 배포 시 포함 파일

```
배포 폴더/
├── ReceiptOCR.exe       # 실행 파일
└── .env                 # API 키 (회사 공용 키 1개)
```

직원은 .exe를 실행하고, 영수증 이미지가 있는 폴더를 선택한 뒤 "변환 시작" 버튼을 누르면 됨.

## 파일 구조

```
14-receipt-ocr/
├── src/
│   ├── receipt_ocr.py         # Gemini OCR 호출
│   ├── excel_writer.py        # Excel 생성
│   └── gui.py                 # Tkinter GUI (진입점)
├── .env                       # API 키 (git 제외)
├── .env.example               # 템플릿
├── requirements.txt
├── README.md
└── sample/                    # 테스트 이미지
```

## 출력 Excel 파일

- 저장 위치: 입력한 영수증 폴더 안
- 파일명: `receipts_YYYYMMDD_HHMM.xlsx`
- 시트명: `영수증_정리`
- OCR 실패한 행은 빨간색 글자로 표시됨

## 문제 해결

| 문제 | 해결 |
|------|------|
| "API 키 없음" 오류 | `.env` 파일에 `GEMINI_API_KEY` 설정 확인 |
| HEIC 변환 실패 | `pip install pillow-heif` 실행 |
| 네트워크 오류 | 인터넷 연결 + 회사 프록시 확인 |
| 인식률 낮음 | 이미지 선명도 확인, 영수증 전체 찍기 |
