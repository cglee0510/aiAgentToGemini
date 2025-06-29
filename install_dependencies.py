#!/usr/bin/env python3
"""
requirements.txt 기반 자동 모듈 설치/업그레이드 스크립트
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command):
    """명령어 실행 및 결과 반환"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def install_requirements():
    """requirements.txt 기반 패키지 설치"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("❌ requirements.txt 파일을 찾을 수 없습니다.")
        return False
    
    print("📦 requirements.txt 발견!")
    print("🔄 패키지 설치/업그레이드를 시작합니다...")
    
    # pip 업그레이드
    print("\n1️⃣ pip 업그레이드 중...")
    success, output = run_command(f"{sys.executable} -m pip install --upgrade pip")
    if success:
        print("✅ pip 업그레이드 완료")
    else:
        print(f"⚠️ pip 업그레이드 실패: {output}")
    
    # requirements.txt 설치
    print("\n2️⃣ requirements.txt 패키지 설치 중...")
    success, output = run_command(f"{sys.executable} -m pip install -r requirements.txt --upgrade")
    
    if success:
        print("✅ 모든 패키지 설치/업그레이드 완료!")
        print("\n📋 설치된 패키지 목록:")
        run_command(f"{sys.executable} -m pip list")
        return True
    else:
        print(f"❌ 패키지 설치 실패:\n{output}")
        return False

def check_outdated():
    """업데이트 가능한 패키지 확인"""
    print("\n🔍 업데이트 가능한 패키지 확인 중...")
    success, output = run_command(f"{sys.executable} -m pip list --outdated")
    if success and output.strip():
        print("📋 업데이트 가능한 패키지:")
        print(output)
    else:
        print("✅ 모든 패키지가 최신 버전입니다.")

def main():
    print("🚀 Python 패키지 자동 설치/업그레이드 도구")
    print("=" * 50)
    
    # 가상환경 확인
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 가상환경이 활성화되어 있습니다.")
    else:
        print("⚠️ 가상환경이 활성화되지 않았습니다.")
        response = input("계속 진행하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("종료합니다.")
            return
    
    # 패키지 설치
    if install_requirements():
        check_outdated()
    
    print("\n🎉 작업 완료!")

if __name__ == "__main__":
    main()