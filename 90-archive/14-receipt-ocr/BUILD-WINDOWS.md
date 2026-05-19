# Windows .exe 빌드 가이드

Windows PC에서 `ReceiptOCR.exe` 파일을 만드는 전체 과정.

---

## 준비물

- **Windows 10 또는 11 PC** (64비트)
- **인터넷 연결**
- **이 프로젝트 폴더** (USB/클라우드로 Windows PC에 복사)

---

## Step 1: Python 설치 (5분)

### 1-1. 다운로드

1. 브라우저에서 https://www.python.org/downloads/ 접속
2. 노란색 **"Download Python 3.x.x"** 버튼 클릭 (3.11 이상 권장)

### 1-2. 설치

1. 다운받은 `.exe` 파일 실행
2. **⚠️ 반드시 체크**: 첫 화면 아래 **"Add python.exe to PATH"** 체크박스 선택
3. **"Install Now"** 클릭
4. 설치 완료 후 **"Close"** 클릭

### 1-3. 설치 확인

1. `Windows 키 + R` → `cmd` 입력 → Enter (명령 프롬프트 열림)
2. 다음 명령 입력:
   ```
   python --version
   ```
3. `Python 3.11.x` 같은 결과가 나오면 성공
   - ❌ `'python'은(는) 내부 또는 외부 명령이...` 오류 → 1-2의 PATH 체크박스 놓친 것. Python 재설치.

---

## Step 2: 프로젝트 폴더 복사 (2분)

1. Mac에서 `14-receipt-ocr` 폴더 전체를 **USB 또는 클라우드(Google Drive 등)** 로 복사
2. Windows PC에서 **`C:\Users\사용자명\Desktop\receipt-ocr`** 위치에 붙여넣기
3. 폴더 안에 다음 파일이 있는지 확인:
   - `src/` 폴더
   - `.env` 파일 ← API 키 들어있음
   - `requirements.txt`

### ⚠️ `.env` 파일 확인

Windows 탐색기는 기본적으로 점(.)으로 시작하는 파일을 숨깁니다.

1. 탐색기 상단 메뉴 **"보기"** 클릭
2. **"숨긴 항목"** 체크박스 선택
3. `.env` 파일이 보이는지 확인. 없으면 Mac에서 다시 복사.

---

## Step 3: 의존성 설치 (3분)

1. Windows 명령 프롬프트 열기 (`Windows + R` → `cmd`)
2. 프로젝트 폴더로 이동:
   ```
   cd C:\Users\사용자명\Desktop\receipt-ocr
   ```
3. 가상환경 생성 (권장):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
   - 프롬프트 앞에 `(venv)` 표시되면 성공
4. 필수 패키지 설치:
   ```
   pip install -r requirements.txt
   pip install pyinstaller
   ```
   - 1~2분 소요
   - 에러 없이 `Successfully installed ...` 메시지 나오면 성공

---

## Step 4: 동작 테스트 (선택, 3분)

빌드 전에 Python 스크립트가 Windows에서도 잘 동작하는지 확인.

```
python src\gui.py
```

- GUI 창이 뜨면 성공
- 테스트 영수증 1~2장으로 변환 시도해보기
- 문제없으면 창 닫고 다음 단계로

**❌ 오류 발생 시**:
- `GEMINI_API_KEY 없음` → `.env` 파일 위치/내용 확인
- `ModuleNotFoundError` → `pip install -r requirements.txt` 재실행

---

## Step 5: .exe 빌드 (5분)

명령 프롬프트에서 (venv 활성화 상태):

```
pyinstaller --onefile --windowed --name "ReceiptOCR" src\gui.py
```

**옵션 설명**:
- `--onefile`: 단일 .exe 파일로 만들기 (배포 간편)
- `--windowed`: 실행 시 검은 콘솔 창 안 뜨게 (GUI만)
- `--name`: 실행 파일 이름

**빌드 시간**: 2~5분

**결과물**: `dist\ReceiptOCR.exe` (약 30~50MB)

### ⚠️ 백신 오탐지

PyInstaller로 만든 .exe가 **Windows Defender**에 의심 파일로 걸릴 수 있습니다.

- "위협 탐지됨" 뜨면 **"허용"** 선택
- 사내 보안 정책 때문에 차단되면 IT팀에 예외 요청 필요

---

## Step 6: 배포 폴더 만들기 (2분)

팀원에게 나눠줄 폴더 구성:

### 6-1. 새 폴더 만들기

`바탕화면\ReceiptOCR_배포\` 폴더 생성

### 6-2. 파일 3개 넣기

```
ReceiptOCR_배포\
├── ReceiptOCR.exe        ← dist/ 에서 복사
├── .env                   ← 프로젝트 루트에서 복사
└── 사용법.txt             ← 아래 내용으로 새로 작성
```

### 6-3. `사용법.txt` 내용 (예시)

```
=== 영수증 OCR 변환기 사용법 ===

1. ReceiptOCR.exe 를 더블클릭하여 실행합니다.

2. "찾아보기" 버튼을 클릭하여 영수증 이미지들이 있는
   폴더를 선택합니다.

3. "변환 시작" 버튼을 누릅니다.

4. 변환이 완료되면 같은 폴더에
   receipts_날짜시간.xlsx 파일이 생성됩니다.

5. "결과 Excel 열기" 버튼으로 바로 확인 가능합니다.

=== 지원 이미지 포맷 ===
.jpg / .jpeg / .png / .webp / .heic (아이폰 사진)

=== 주의사항 ===
- 인터넷 연결이 필요합니다.
- .env 파일을 삭제하지 마세요. 삭제 시 작동 안 함.
- 한 번에 100장 이하를 권장합니다.

문의: [담당자 연락처]
```

---

## Step 7: 팀원에게 배포 (1분)

### 7-1. ZIP 압축

`ReceiptOCR_배포` 폴더를 마우스 우클릭 → **"압축(ZIP) 폴더로 보내기"**

### 7-2. 공유

- 사내 메신저/이메일/공유 드라이브로 **`ReceiptOCR_배포.zip`** 전송
- 팀원은 ZIP 압축 해제 후 `ReceiptOCR.exe` 더블클릭

---

## 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| .exe 실행해도 아무것도 안 뜸 | `--windowed` 옵션 때문에 콘솔 숨김. 에러 확인 어려움 | 디버깅용으로 `--windowed` 없이 재빌드 |
| `.env` 파일 못 읽음 오류 | .exe 옆에 `.env` 파일이 없음 | 배포 폴더에 `.env` 같이 넣었는지 확인 |
| 백신이 .exe 차단 | PyInstaller 오탐지 | Windows Defender에서 허용/예외 등록 |
| `ModuleNotFoundError` (빌드 후) | 숨은 의존성 누락 | `pyinstaller --onefile --windowed --hidden-import <모듈명> src\gui.py` |
| `.exe` 용량이 너무 큼 (100MB+) | onefile이라 압축됨 | 정상. 첫 실행 시 압축 해제로 2~3초 느림 |

---

## 업데이트 시 재빌드

코드 수정 후 .exe를 다시 만들려면:

1. 새 코드를 Windows PC로 복사 (또는 git pull)
2. Step 5 명령 다시 실행:
   ```
   cd C:\Users\사용자명\Desktop\receipt-ocr
   venv\Scripts\activate
   pyinstaller --onefile --windowed --name "ReceiptOCR" src\gui.py
   ```
3. 새 `ReceiptOCR.exe`로 교체 배포

---

## 빌드 시간 요약

| 단계 | 예상 시간 |
|------|----------|
| Python 설치 | 5분 |
| 프로젝트 복사 | 2분 |
| 의존성 설치 | 3분 |
| 테스트 | 3분 |
| .exe 빌드 | 5분 |
| 배포 폴더 구성 | 3분 |
| **합계** | **약 20~25분** |

두 번째부터는 **Step 5만** 실행하면 되므로 **5분**이면 재빌드 가능.
