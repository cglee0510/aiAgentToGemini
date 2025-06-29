# aiAgentToGemini

경제 뉴스 자동 수집 및 AI 분석 시스템

## 🚀 새로운 PC에서 빠른 설정

### 방법 1: 자동 설정 스크립트 (추천)

```bash
# 1. 프로젝트 클론
git clone https://github.com/cglee0510/aiAgentToGemini.git
cd aiAgentToGemini

# 2. 자동 설정 실행
python setup_environment.py
```

### 방법 2: Windows 배치 파일

```bash
# 1. 프로젝트 클론
git clone https://github.com/cglee0510/aiAgentToGemini.git
cd aiAgentToGemini

# 2. 관리자 권한으로 실행
setup.bat
```

### 방법 3: 수동 설정

```bash
# 1. 프로젝트 클론
git clone https://github.com/cglee0510/aiAgentToGemini.git
cd aiAgentToGemini

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. 의존성 설치
pip install -r requirements.txt

# 5. 환경변수 설정
copy .env.template .env
# .env 파일에 실제 토큰 값 입력
```

## 📋 필수 의존성

- Python 3.8+
- Git
- GitHub Token (repo 권한 필요)
- Gemini API Key (선택사항)

## 🔧 환경변수 설정

`.env` 파일을 생성하고 다음 값들을 설정하세요:

```env
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### GitHub Token 생성 방법:
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. `repo` 권한 체크
4. 생성된 토큰을 `.env` 파일에 입력

## 🎯 VSCode 설정

1. **Python 인터프리터 선택:**
   - `Ctrl+Shift+P` → "Python: Select Interpreter"
   - `./venv/Scripts/python.exe` (Windows) 또는 `./venv/bin/python` (Linux/Mac) 선택

2. **자동 설정:**
   - 설정 스크립트 실행 시 `.vscode/settings.json`이 자동 생성됩니다

## 🏃‍♂️ 실행 방법

```bash
# 가상환경 활성화 후
python agent.py
```

## 📦 주요 패키지

- `google-generativeai` - Gemini AI
- `requests`, `beautifulsoup4`, `feedparser` - 웹 크롤링
- `pandas`, `numpy` - 데이터 처리
- `GitPython` - Git 작업
- `schedule` - 스케줄링

## 🐛 문제 해결

### Import 오류가 발생하는 경우:

```bash
# 1. 가상환경이 활성화되었는지 확인
# 2. 패키지 재설치
pip install -r requirements.txt --upgrade

# 3. VSCode 인터프리터 재선택
# Ctrl+Shift+P → "Python: Select Interpreter"
```

### 권한 오류가 발생하는 경우:

```bash
# 관리자 권한으로 실행 또는
pip install --user -r requirements.txt
```

### 가상환경 문제:

```bash
# 가상환경 삭제 후 재생성
rmdir /s /q venv    # Windows
rm -rf venv         # Linux/Mac

python -m venv venv
# 활성화 후 패키지 재설치
```

## 📁 프로젝트 구조

```
aiAgentToGemini/
├── agent.py                 # 메인 에이전트
├── webCroll.py             # 웹 크롤링 모듈
├── requirements.txt        # 의존성 목록
├── setup_environment.py    # 환경 설정 스크립트
├── setup.bat              # Windows 배치 파일
├── .env.template          # 환경변수 템플릿
├── .vscode/
│   └── settings.json      # VSCode 설정
└── venv/                  # 가상환경 (로컬)
```

## 🔄 업데이트

```bash
# 최신 코드 가져오기
git pull origin main

# 의존성 업데이트
pip install -r requirements.txt --upgrade
```

## 🆘 지원

문제가 발생하면 다음을 확인하세요:

1. Python 버전 (3.8+ 필요)
2. 가상환경 활성화 상태
3. VSCode Python 인터프리터 설정
4. 환경변수 (.env) 설정
5. 네트워크 연결 (GitHub, RSS 피드)