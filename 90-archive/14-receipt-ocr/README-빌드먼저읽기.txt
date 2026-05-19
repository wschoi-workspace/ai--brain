=== Windows에서 빌드하기 - 빠른 시작 ===

[준비물]
1. Windows 10/11 PC
2. Python 3.11+ 설치 (https://www.python.org/downloads/)
   ⚠️ 설치 시 "Add python.exe to PATH" 체크 필수!

[빌드 방법 - 자동]
1. 이 ZIP 파일을 원하는 폴더에 압축 해제
2. build.bat 파일을 더블클릭
3. 자동으로 Python 가상환경 생성 + 의존성 설치 + .exe 빌드
4. 완료되면 dist\ReceiptOCR.exe 생성됨 (약 10분 소요)

[배포 폴더 만들기]
빌드 완료 후 새 폴더를 만들고 아래 3개 파일을 넣어 ZIP 압축:
  - dist\ReceiptOCR.exe
  - .env
  - 사용법.txt

이 ZIP을 팀원 4명에게 공유하면 됩니다.

[문제 발생 시]
BUILD-WINDOWS.md 파일의 "문제 해결" 섹션 참고.

[수동 빌드 (build.bat 실행 안 될 때)]
명령 프롬프트에서:
  cd 이폴더경로
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt pyinstaller
  pyinstaller --onefile --windowed --name "ReceiptOCR" src\gui.py
