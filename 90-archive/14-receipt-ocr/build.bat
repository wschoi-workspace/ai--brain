@echo off
chcp 65001 > nul
echo ======================================
echo  ReceiptOCR Windows 빌드 스크립트
echo ======================================
echo.

REM Python 설치 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았습니다.
    echo https://www.python.org/downloads/ 에서 Python 3.11+ 설치 후
    echo "Add python.exe to PATH" 체크 필수!
    pause
    exit /b 1
)

echo [1/4] 가상환경 생성 중...
if not exist venv (
    python -m venv venv
)

echo [2/4] 가상환경 활성화...
call venv\Scripts\activate.bat

echo [3/4] 의존성 설치 중... (1~2분 소요)
pip install --upgrade pip > nul
pip install -r requirements.txt
pip install pyinstaller

echo [4/4] .exe 빌드 중... (2~5분 소요)
pyinstaller --onefile --windowed --name "ReceiptOCR" --clean src\gui.py

if exist dist\ReceiptOCR.exe (
    echo.
    echo ======================================
    echo  빌드 성공!
    echo ======================================
    echo.
    echo 결과물: dist\ReceiptOCR.exe
    echo.
    echo 배포하려면 다음 파일들을 한 폴더에 모아 ZIP으로 압축하세요:
    echo   - dist\ReceiptOCR.exe
    echo   - .env
    echo   - 사용법.txt
    echo.
) else (
    echo.
    echo [ERROR] 빌드 실패. 로그를 확인하세요.
)

pause
