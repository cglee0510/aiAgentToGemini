#!/usr/bin/env python3
"""
새로운 PC에서 프로젝트 환경을 자동으로 설정하는 스크립트
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def setup_console_encoding():
    """Windows 콘솔 인코딩 설정"""
    try:
        if platform.system() == "Windows":
            import locale
            # UTF-8 인코딩 시도
            os.system('chcp 65001 > nul 2>&1')
            # stdout 인코딩 확인
            current_encoding = sys.stdout.encoding
            print(f"[INFO] 현재 인코딩: {current_encoding}")
    except Exception as e:
        print(f"[WARNING] 인코딩 설정 실패: {e}")

def safe_print(text):
    """안전한 출력 (이모지 문제 해결)"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 이모지 제거하여 출력
        import re
        clean_text = re.sub(r'[^\x00-\x7F\uAC00-\uD7AF]', '?', text)
        print(clean_text)

def run_command(command, check=True):
    """명령어 실행"""
    safe_print(f"[실행] {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            safe_print(f"[출력] {result.stdout.strip()}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        safe_print(f"[오류] {e.stderr}")
        return False
    except Exception as e:
        safe_print(f"[오류] {str(e)}")
        return False

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    safe_print(f"[Python] 버전: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        safe_print("[경고] Python 3.8 이상이 권장됩니다.")
        return False
    return True

def setup_virtual_environment():
    """가상환경 생성 및 활성화"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        safe_print("[INFO] 기존 가상환경 발견됨")
        response = input("기존 가상환경을 삭제하고 새로 만드시겠습니까? (y/N): ")
        if response.lower() == 'y':
            safe_print("[INFO] 기존 가상환경 삭제 중...")
            import shutil
            shutil.rmtree(venv_path)
        else:
            safe_print("[INFO] 기존 가상환경 사용")
            return True
    
    safe_print("[INFO] 새 가상환경 생성 중...")
    if not run_command(f"{sys.executable} -m venv venv"):
        safe_print("[ERROR] 가상환경 생성 실패")
        return False
    
    safe_print("[SUCCESS] 가상환경 생성 완료")
    return True

def get_activation_command():
    """OS별 가상환경 활성화 명령어 반환"""
    if platform.system() == "Windows":
        return "venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"

def install_requirements():
    """requirements.txt 설치"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("❌ requirements.txt 파일이 없습니다.")
        create_requirements = input("requirements.txt를 생성하시겠습니까? (y/N): ")
        if create_requirements.lower() == 'y':
            create_requirements_file()
        else:
            return False
    
    print("📦 패키지 설치 중...")
    
    # 가상환경의 pip 경로 찾기
    if platform.system() == "Windows":
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    # pip 업그레이드
    if not run_command(f"{python_path} -m pip install --upgrade pip"):
        print("⚠️ pip 업그레이드 실패")
    
    # requirements.txt 설치
    if not run_command(f"{pip_path} install -r requirements.txt"):
        print("❌ 패키지 설치 실패")
        return False
    
    print("✅ 패키지 설치 완료")
    return True

def create_requirements_file():
    """requirements.txt 생성"""
    requirements_content = """# Google Gemini API 관련
google-generativeai>=0.3.0

# 웹 크롤링 및 RSS 관련
requests>=2.31.0
beautifulsoup4>=4.12.0
feedparser>=6.0.10
lxml>=4.9.3

# 데이터 처리
pandas>=2.1.0
numpy>=1.24.0

# Git 작업
GitPython>=3.1.40

# 스케줄링
schedule>=1.2.0

# 설정 파일 관리
python-dotenv>=1.0.0

# 로깅
loguru>=0.7.2

# 날짜/시간 처리
python-dateutil>=2.8.2

# 기타 유틸리티
tqdm>=4.66.0
rich>=13.7.0
"""
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)
    
    print("✅ requirements.txt 파일 생성 완료")

def create_vscode_settings():
    """VSCode 설정 파일 생성"""
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    # settings.json 생성
    if platform.system() == "Windows":
        python_path = "./venv/Scripts/python.exe"
    else:
        python_path = "./venv/bin/python"
    
    settings_content = f'''{{
    "python.defaultInterpreterPath": "{python_path}",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "files.encoding": "utf8",
    "python.analysis.autoImportCompletions": true,
    "python.analysis.typeCheckingMode": "basic"
}}'''
    
    settings_file = vscode_dir / "settings.json"
    with open(settings_file, "w", encoding="utf-8") as f:
        f.write(settings_content)
    
    print("✅ VSCode 설정 파일 생성 완료")

def create_env_template():
    """환경변수 템플릿 파일 생성"""
    env_content = """# GitHub Token (필수)
GITHUB_TOKEN=your_github_token_here

# Gemini API Key (선택사항 - GitHub Actions에서 사용)
GEMINI_API_KEY=your_gemini_api_key_here

# 사용법:
# 1. 위 값들을 실제 값으로 변경
# 2. 파일명을 .env로 변경
# 3. .env 파일은 Git에 커밋하지 마세요 (.gitignore에 추가됨)
"""
    
    with open(".env.template", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("✅ 환경변수 템플릿 파일 생성 완료")

def create_gitignore():
    """gitignore 파일 생성"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
economic_news_report_*.txt
analysis_*.md
"""
    
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore 파일 생성 완료")

def verify_installation():
    """설치 검증"""
    print("\n🔍 설치 검증 중...")
    
    # 가상환경의 python 경로 찾기
    if platform.system() == "Windows":
        python_path = "venv\\Scripts\\python"
    else:
        python_path = "venv/bin/python"
    
    # 주요 패키지 import 테스트
    test_imports = [
        "import requests",
        "import pandas",
        "import feedparser", 
        "import schedule",
        "from git import Repo",
        "import google.generativeai as genai"
    ]
    
    for import_cmd in test_imports:
        test_cmd = f'{python_path} -c "{import_cmd}; print(\\"✅ {import_cmd.split()[-1]} OK\\")"'
        if not run_command(test_cmd, check=False):
            print(f"❌ {import_cmd} 실패")
            return False
    
    print("✅ 모든 패키지 import 성공!")
    return True

def display_next_steps():
    """다음 단계 안내"""
    activation_cmd = get_activation_command()
    
    print("\n" + "="*60)
    print("🎉 환경 설정 완료!")
    print("="*60)
    print("\n📋 다음 단계:")
    print(f"1️⃣ 가상환경 활성화:")
    if platform.system() == "Windows":
        print(f"   venv\\Scripts\\activate")
    else:
        print(f"   source venv/bin/activate")
    
    print("\n2️⃣ 환경변수 설정:")
    print("   .env.template을 .env로 복사하고 실제 값으로 수정")
    
    print("\n3️⃣ VSCode 사용시:")
    print("   - Ctrl+Shift+P → 'Python: Select Interpreter'")
    print("   - './venv/Scripts/python.exe' (Windows) 또는 './venv/bin/python' (Linux/Mac) 선택")
    
    print("\n4️⃣ 프로그램 실행:")
    print("   python agent.py")
    
    print("\n💡 문제 해결:")
    print("   - import 오류 시: pip install -r requirements.txt --upgrade")
    print("   - VSCode에서 모듈 인식 안됨: 인터프리터 재선택")
    print("   - 권한 오류 시: 관리자 권한으로 실행")

def main():
    """메인 함수"""
    # 콘솔 인코딩 설정
    setup_console_encoding()
    
    safe_print("aiAgentToGemini 프로젝트 환경 설정")
    safe_print("="*50)
    
    # Python 버전 확인
    if not check_python_version():
        safe_print("[ERROR] Python 버전이 너무 낮습니다.")
        return
    
    # 현재 디렉토리 확인
    if not (Path("agent.py").exists() or Path("webCroll.py").exists()):
        safe_print("[ERROR] agent.py 또는 webCroll.py 파일이 없습니다.")
        safe_print("[HELP] 프로젝트 루트 디렉토리에서 실행하세요.")
        return
    
    safe_print("[SUCCESS] 프로젝트 파일 확인됨")
    
    # 1. 가상환경 설정
    if not setup_virtual_environment():
        return
    
    # 2. 패키지 설치
    if not install_requirements():
        return
    
    # 3. VSCode 설정 생성
    create_vscode_settings()
    
    # 4. 환경변수 템플릿 생성
    create_env_template()
    
    # 5. gitignore 생성
    create_gitignore()
    
    # 6. 설치 검증
    if verify_installation():
        # 7. 다음 단계 안내
        display_next_steps()
    else:
        safe_print("[ERROR] 설치 검증 실패. 수동으로 확인이 필요합니다.")

if __name__ == "__main__":
    main()