@echo off
chcp 65001 > nul
echo aiAgentToGemini 환경 설정
echo ========================

REM Python 확인
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo 오류: Python이 설치되지 않았습니다.
    echo https://python.org에서 Python 3.8+ 설치하세요
    pause
    exit /b 1
)

echo Python 설치 확인됨
python --version

REM 프로젝트 파일 확인
if not exist "agent.py" (
    if not exist "webCroll.py" (
        echo 오류: 프로젝트 파일이 없습니다.
        echo 프로젝트 루트 디렉토리에서 실행하세요
        pause
        exit /b 1
    )
)

echo 프로젝트 파일 확인됨

REM 기존 가상환경 확인
if exist "venv" (
    echo 기존 가상환경 발견됨
    set /p "choice=기존 가상환경을 삭제하고 새로 만드시겠습니까? (y/N): "
    if /i "%choice%"=="y" (
        echo 기존 가상환경 삭제 중...
        rmdir /s /q venv
    )
)

REM 가상환경 생성
if not exist "venv" (
    echo 가상환경 생성 중...
    python -m venv venv
    if %errorLevel% neq 0 (
        echo 가상환경 생성 실패
        pause
        exit /b 1
    )
    echo 가상환경 생성 완료
)

REM 가상환경 활성화
echo 가상환경 활성화...
call venv\Scripts\activate.bat

REM pip 업그레이드
echo pip 업그레이드 중...
python -m pip install --upgrade pip

REM requirements.txt 확인 및 생성
if not exist "requirements.txt" (
    echo requirements.txt 생성 중...
    (
        echo google-generativeai^>=0.3.0
        echo requests^>=2.31.0
        echo beautifulsoup4^>=4.12.0
        echo feedparser^>=6.0.10
        echo lxml^>=4.9.3
        echo pandas^>=2.1.0
        echo numpy^>=1.24.0
        echo GitPython^>=3.1.40
        echo schedule^>=1.2.0
        echo python-dotenv^>=1.0.0
        echo loguru^>=0.7.2
        echo python-dateutil^>=2.8.2
        echo tqdm^>=4.66.0
        echo rich^>=13.7.0
    ) > requirements.txt
    echo requirements.txt 생성 완료
)

REM 패키지 설치
echo 패키지 설치 중...
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo 패키지 설치 실패
    echo 수동으로 pip install -r requirements.txt 실행하세요
    pause
    exit /b 1
)

REM VSCode 설정 생성
if not exist ".vscode" mkdir .vscode
echo VSCode 설정 파일 생성 중...
(
    echo {"python.defaultInterpreterPath": "./venv/Scripts/python.exe","python.terminal.activateEnvironment": true,"files.encoding": "utf8"}
) > .vscode\settings.json

REM 환경변수 템플릿 생성
if not exist ".env.template" (
    echo 환경변수 템플릿 생성 중...
    (
        echo GITHUB_TOKEN=your_github_token_here
        echo GEMINI_API_KEY=your_gemini_api_key_here
    ) > .env.template
)

REM 설치 검증
echo 설치 검증 중...
python -c "import requests, pandas, feedparser, schedule; from git import Repo; import google.generativeai; print('모든 패키지 import 성공!')"
if %errorLevel% neq 0 (
    echo 설치 검증 실패 - 일부 패키지에 문제가 있을 수 있습니다.
) else (
    echo 설치 검증 성공!
)

echo.
echo ========================
echo 환경 설정 완료!
echo ========================
echo.
echo 다음 단계:
echo 1. .env.template을 .env로 복사하고 실제 토큰 값 입력
echo 2. VSCode에서 Python 인터프리터 선택
echo 3. 가상환경 활성화: venv\Scripts\activate
echo 4. 프로그램 실행: python agent.py

pause