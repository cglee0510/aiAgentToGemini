#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 호환 간단 환경 설정 스크립트
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def run_cmd(command):
    """명령어 실행"""
    print(f"[실행] {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            if result.stdout.strip():
                print(f"[성공] {result.stdout.strip()}")
            return True
        else:
            print(f"[실패] {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[오류] {str(e)}")
        return False

def main():
    print("aiAgentToGemini 환경 설정 시작")
    print("=" * 40)
    
    # Python 버전 확인
    version = sys.version_info
    print(f"Python 버전: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("경고: Python 3.8 이상이 권장됩니다.")
    
    # 프로젝트 파일 확인
    if not (Path("agent.py").exists() or Path("webCroll.py").exists()):
        print("오류: 프로젝트 파일이 없습니다.")
        print("프로젝트 루트 디렉토리에서 실행하세요.")
        input("계속하려면 Enter를 누르세요...")
        return
    
    print("프로젝트 파일 확인됨")
    
    # 가상환경 처리
    venv_path = Path("venv")
    if venv_path.exists():
        print("기존 가상환경 발견됨")
        choice = input("기존 가상환경을 삭제하고 새로 만드시겠습니까? (y/N): ")
        if choice.lower() == 'y':
            print("기존 가상환경 삭제 중...")
            try:
                import shutil
                shutil.rmtree(venv_path)
                print("삭제 완료")
            except Exception as e:
                print(f"삭제 실패: {e}")
                print("수동으로 venv 폴더를 삭제하고 다시 실행하세요.")
                input("계속하려면 Enter를 누르세요...")
                return
    
    # 가상환경 생성
    if not venv_path.exists():
        print("가상환경 생성 중...")
        if not run_cmd(f'"{sys.executable}" -m venv venv'):
            print("가상환경 생성 실패")
            input("계속하려면 Enter를 누르세요...")
            return
        print("가상환경 생성 완료")
    
    # pip 업그레이드 및 패키지 설치
    if platform.system() == "Windows":
        pip_path = "venv\\Scripts\\pip.exe"
        python_path = "venv\\Scripts\\python.exe"
    else:
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    print("pip 업그레이드 중...")
    run_cmd(f'"{python_path}" -m pip install --upgrade pip')
    
    # requirements.txt 확인
    if not Path("requirements.txt").exists():
        print("requirements.txt 생성 중...")
        requirements = """google-generativeai>=0.3.0
requests>=2.31.0
beautifulsoup4>=4.12.0
feedparser>=6.0.10
lxml>=4.9.3
pandas>=2.1.0
numpy>=1.24.0
GitPython>=3.1.40
schedule>=1.2.0
python-dotenv>=1.0.0
loguru>=0.7.2
python-dateutil>=2.8.2
tqdm>=4.66.0
rich>=13.7.0"""
        
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write(requirements)
        print("requirements.txt 생성 완료")
    
    print("패키지 설치 중...")
    if not run_cmd(f'"{pip_path}" install -r requirements.txt'):
        print("패키지 설치 실패")
        print("수동으로 다음 명령어를 실행하세요:")
        print(f'"{pip_path}" install -r requirements.txt')
        input("계속하려면 Enter를 누르세요...")
        return
    
    print("패키지 설치 완료")
    
    # VSCode 설정 폴더 생성
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    # VSCode settings.json 생성
    if platform.system() == "Windows":
        interpreter_path = "./venv/Scripts/python.exe"
    else:
        interpreter_path = "./venv/bin/python"
    
    settings_content = f"""{{"python.defaultInterpreterPath": "{interpreter_path}","python.terminal.activateEnvironment": true,"files.encoding": "utf8"}}"""
    
    with open(".vscode/settings.json", "w", encoding="utf-8") as f:
        f.write(settings_content)
    print("VSCode 설정 파일 생성 완료")
    
    # 환경변수 템플릿 생성
    if not Path(".env.template").exists():
        env_template = """GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here"""
        
        with open(".env.template", "w", encoding="utf-8") as f:
            f.write(env_template)
        print("환경변수 템플릿 생성 완료")
    
    # 설치 검증
    print("설치 검증 중...")
    test_cmd = f'"{python_path}" -c "import requests, pandas, feedparser, schedule; from git import Repo; import google.generativeai; print(\\"모든 패키지 import 성공!\\")"'
    
    if run_cmd(test_cmd):
        print("설치 검증 성공!")
    else:
        print("설치 검증 실패 - 일부 패키지에 문제가 있을 수 있습니다.")
    
    print("\n" + "=" * 40)
    print("환경 설정 완료!")
    print("=" * 40)
    print("\n다음 단계:")
    print("1. .env.template을 .env로 복사하고 실제 토큰 값 입력")
    print("2. VSCode에서 Python 인터프리터 선택:")
    print("   Ctrl+Shift+P -> 'Python: Select Interpreter'")
    print(f"   '{interpreter_path}' 선택")
    print("3. 가상환경 활성화:")
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("4. 프로그램 실행: python agent.py")
    
    input("\n계속하려면 Enter를 누르세요...")

if __name__ == "__main__":
    main()