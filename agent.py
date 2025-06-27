import os
import time
import stat
import schedule
import requests
import google.generativeai as genai
from datetime import datetime
from git import Repo, exc
from webCroll import generate_per_report  # webCroll 모듈 임포트

# 환경 설정
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
print(f"GitHub Token: {'설정됨' if GITHUB_TOKEN else '설정되지 않음'}")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"Gemini API Key: {'설정됨' if GEMINI_API_KEY else '설정되지 않음'}")
REPO_URL = f"https://{GITHUB_TOKEN}@github.com/cglee0510/aiAgentToGemini.git"
LOCAL_DIR = r"F:\aiAgentToGemini"  # 새로운 폴더명으로 변경

# Gemini 초기화
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

def setup_repository():
    """저장소 초기화 및 설정"""
    if not os.path.exists(LOCAL_DIR) or not os.path.exists(os.path.join(LOCAL_DIR, ".git")):
        # 저장소가 없으면 새로 클론
        try:
            print("📦 리포지토리 클론 중...")
            Repo.clone_from(REPO_URL, LOCAL_DIR)
            print("✅ 클론 완료")
            return True
        except Exception as e:
            print(f"❌ 클론 실패: {e}")
            return False
    else:
        # 기존 저장소가 있으면 리모트 확인 및 설정
        try:
            repo = Repo(LOCAL_DIR)
            print("🔍 기존 저장소 확인 중...")
            
            # origin 리모트가 있는지 확인
            if 'origin' not in [remote.name for remote in repo.remotes]:
                print("🔧 origin 리모트 추가 중...")
                repo.create_remote('origin', REPO_URL)
                print("✅ origin 리모트 추가 완료")
            
            # Git 상태 확인 및 정리
            print("🧹 Git 상태 정리 중...")
            
            # 로컬 변경사항이 있으면 stash
            if repo.is_dirty():
                print("💾 로컬 변경사항 stash 중...")
                repo.git.stash()
            
            # 안전한 pull 시도
            print("🔄 기존 저장소에서 pull 시도")
            origin = repo.remote(name='origin')
            
            # fetch 먼저 시도
            origin.fetch()
            
            # 강제로 원격 상태와 동기화
            repo.git.reset('--hard', 'origin/main')
            print("✅ 강제 동기화 완료")
            return True
            
        except exc.InvalidGitRepositoryError:
            print(f"❌ 유효하지 않은 Git 저장소: {LOCAL_DIR}")
            return recreate_repository()
        except Exception as e:
            print(f"❌ Git 동기화 실패: {e}")
            print("🔄 저장소 재생성을 시도합니다...")
            return recreate_repository()

def safe_remove_directory(path):
    """안전한 디렉토리 삭제 (윈도우 대응)"""
    import stat
    import shutil
    
    def handle_remove_readonly(func, path, exc):
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)
            func(path)
    
    try:
        if os.path.exists(path):
            # 1단계: 모든 파일의 읽기 전용 속성 제거
            for root, dirs, files in os.walk(path):
                for fname in files:
                    full_path = os.path.join(root, fname)
                    try:
                        os.chmod(full_path, stat.S_IWRITE)
                    except:
                        pass
            
            # 2단계: 폴더 삭제
            shutil.rmtree(path, onerror=handle_remove_readonly)
            print(f"✅ 폴더 삭제 완료: {path}")
            return True
    except Exception as e:
        print(f"❌ 폴더 삭제 실패: {e}")
        print(f"💡 수동 삭제 방법: 관리자 권한으로 'rmdir /s /q \"{path}\"' 실행")
        return False

def recreate_repository():
    """문제가 있는 저장소를 삭제하고 다시 클론"""
    try:
        print("🗑️ 기존 저장소 삭제 중...")
        
        if not safe_remove_directory(LOCAL_DIR):
            return False
        
        # 잠시 대기 (파일 시스템 동기화)
        time.sleep(1)
        
        print("📦 리포지토리 다시 클론 중...")
        Repo.clone_from(REPO_URL, LOCAL_DIR)
        print("✅ 재클론 완료")
        return True
    except Exception as e:
        print(f"❌ 재클론 실패: {e}")
        return False

def check_github_actions_status():
    """GitHub Actions 실행 상태 확인 (선택사항)"""
    try:
        # GitHub API를 통해 최근 워크플로우 실행 상태 확인
        if GITHUB_TOKEN:
            headers = {
                'Authorization': f'token {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 리포지토리 정보에서 워크플로우 실행 확인
            repo_name = "cglee0510/quant"  # 실제 리포지토리명으로 변경
            url = f"https://api.github.com/repos/{repo_name}/actions/runs?per_page=3"
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                runs = response.json().get('workflow_runs', [])
                if runs:
                    print("🔍 최근 GitHub Actions 실행 상태:")
                    for i, run in enumerate(runs[:3], 1):
                        status = run.get('status', 'unknown')
                        conclusion = run.get('conclusion', 'unknown')
                        created_at = run.get('created_at', '')
                        workflow_name = run.get('name', 'Unknown')
                        
                        status_emoji = {
                            'in_progress': '⏳',
                            'completed': '✅' if conclusion == 'success' else '❌',
                            'queued': '🔄'
                        }.get(status, '❓')
                        
                        print(f"   {i}. {status_emoji} {workflow_name}: {status} ({conclusion}) - {created_at[:19]}")
                    
                    # 최신 실행 상태 상세 정보
                    latest_run = runs[0]
                    if latest_run.get('status') == 'in_progress':
                        print("⏳ 현재 AI 분석이 진행 중입니다...")
                    elif latest_run.get('conclusion') == 'success':
                        print("✅ 최근 AI 분석이 성공적으로 완료되었습니다.")
                    elif latest_run.get('conclusion') == 'failure':
                        print("❌ 최근 AI 분석에서 오류가 발생했습니다.")
                        print(f"🔗 로그 확인: https://github.com/{repo_name}/actions")
                else:
                    print("🔍 실행된 워크플로우가 없습니다.")
            else:
                print(f"⚠️ GitHub API 응답 오류: {response.status_code}")
                
    except Exception as e:
        print(f"ℹ️ GitHub Actions 상태 확인 실패 (정상 작동에는 영향 없음): {e}")

def check_analysis_results():
    """생성된 분석 결과 파일들 확인"""
    try:
        analysis_files = []
        if os.path.exists(LOCAL_DIR):
            for file in os.listdir(LOCAL_DIR):
                if file.startswith("analysis_") and file.endswith(".md"):
                    analysis_files.append(file)
        
        if analysis_files:
            # 최신 파일 정렬
            analysis_files.sort(reverse=True)
            print(f"📊 발견된 AI 분석 파일 수: {len(analysis_files)}개")
            print(f"🔍 최신 분석 파일: {analysis_files[0]}")
            
            # 최신 파일의 수정 시간 확인
            latest_file = os.path.join(LOCAL_DIR, analysis_files[0])
            if os.path.exists(latest_file):
                mtime = os.path.getmtime(latest_file)
                mod_time = datetime.fromtimestamp(mtime)
                time_diff = datetime.now() - mod_time
                
                if time_diff.seconds < 300:  # 5분 이내
                    print(f"🔥 최근 분석 완료: {mod_time.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff.seconds}초 전)")
                else:
                    print(f"📅 최근 분석 완료: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                # 파일 크기 확인
                file_size = os.path.getsize(latest_file)
                print(f"📄 분석 파일 크기: {file_size:,} bytes")
        else:
            print("📊 아직 생성된 AI 분석 파일이 없습니다.")
            print("💡 첫 번째 뉴스 수집 후 약 2-3분 후에 분석 파일이 생성됩니다.")
            
    except Exception as e:
        print(f"⚠️ 분석 결과 확인 중 오류: {e}")

def git_commit_push(file_path: str, commit_message: str):
    """Git 커밋 및 푸시 (GitHub Actions 트리거 최적화)"""
    try:
        repo = Repo(LOCAL_DIR)
        
        # 파일이 실제로 존재하는지 확인
        full_path = os.path.join(LOCAL_DIR, file_path)
        if not os.path.exists(full_path):
            print(f"❌ 파일이 존재하지 않습니다: {full_path}")
            return False
        
        # 변경사항 스테이징
        repo.index.add([file_path])
        
        # 변경사항이 있는지 확인
        if not repo.index.diff("HEAD"):
            print("📝 변경사항이 없습니다.")
            return True
        
        # 커밋 생성 (GitHub Actions가 감지할 수 있도록 명확한 메시지)
        enhanced_message = f"🤖 AUTO-NEWS: {commit_message}"
        repo.index.commit(enhanced_message)
        
        # 원격 저장소에 푸시
        origin = repo.remote(name='origin')
        origin.push()
        print(f"✅ {file_path} 푸시 완료 - GitHub Actions 트리거됨")
        
        # GitHub Actions 트리거 확인
        print(f"🔄 자동 AI 분석이 GitHub에서 시작됩니다...")
        print(f"📊 분석 결과는 약 2-3분 후 같은 리포지토리에 업로드됩니다.")
        print(f"🎯 예상 분석 파일명: analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        return True
        
    except Exception as e:
        print(f"❌ Git 작업 실패: {e}")
        return False

def periodic_task():
    """주기적 작업 실행 (GitHub Actions 최적화 버전)"""
    print("\n" + "="*60)
    print("📰 경제 기사 리포트 생성 및 AI 분석 트리거 시작...")
    print(f"🕐 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 이전 GitHub Actions 상태 확인 (선택사항)
        print("🔍 GitHub Actions 상태 확인 중...")
        check_github_actions_status()
        print("-" * 40)
        
        # 리포트 생성
        print("📊 경제 뉴스 수집 중...")
        report_file = generate_per_report()
        
        if not report_file:
            print("❌ 리포트 생성 실패 - 다음 실행을 기다립니다.")
            return
        
        # 생성된 파일을 로컬 디렉토리로 이동
        src_path = report_file
        dest_path = os.path.join(LOCAL_DIR, report_file)
        
        if os.path.exists(src_path):
            import shutil
            shutil.move(src_path, dest_path)
            print(f"📁 파일 이동 완료: {dest_path}")
        else:
            print(f"⚠️ 파일이 존재하지 않습니다: {src_path}")
            return
        
        # Git 작업 (GitHub Actions 트리거)
        print("🚀 GitHub에 업로드 및 AI 분석 트리거 중...")
        if git_commit_push(report_file, f"경제뉴스 자동수집: {report_file}"):
            print(f"✅ 뉴스 업로드 완료: {report_file}")
            print(f"🤖 GitHub Actions에서 Gemini AI 분석이 자동으로 시작됩니다...")
            print(f"📈 투자자 관점의 상세 분석이 곧 생성됩니다...")
        else:
            print(f"⚠️ Git 업로드 실패: {report_file}")
            
    except Exception as e:
        print(f"❌ 작업 실패: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("="*60 + "\n")

def display_system_status():
    """시스템 상태 표시"""
    print("🎯 시스템 상태 확인")
    print("-" * 40)
    
    # 환경변수 확인
    print(f"🔑 GitHub Token: {'✅ 설정됨' if GITHUB_TOKEN else '❌ 미설정'}")
    print(f"🤖 Gemini API Key: {'✅ 설정됨' if GEMINI_API_KEY else '❌ 미설정'}")
    
    # 디렉토리 확인
    print(f"📁 작업 디렉토리: {LOCAL_DIR}")
    print(f"📂 디렉토리 존재: {'✅ 있음' if os.path.exists(LOCAL_DIR) else '❌ 없음'}")
    
    # Git 상태 확인
    if os.path.exists(os.path.join(LOCAL_DIR, ".git")):
        print(f"🔧 Git 저장소: ✅ 초기화됨")
    else:
        print(f"🔧 Git 저장소: ❌ 초기화 필요")
    
    print("-" * 40)

def main():
    """메인 실행 함수 (GitHub Actions 최적화 버전)"""
    print("🚀 경제 기사 수집 및 AI 분석 에이전트 시작")
    print("🔗 GitHub Actions + Gemini AI 자동화 시스템")
    print("=" * 60)
    
    # 시스템 상태 표시
    display_system_status()
    
    # GitHub 토큰 확인
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN 환경변수가 설정되지 않았습니다.")
        print("💡 설정 방법:")
        print("   Windows: set GITHUB_TOKEN=your_token_here")
        print("   Linux/Mac: export GITHUB_TOKEN=your_token_here")
        return
    
    # Gemini API 키 확인 (선택사항 - GitHub Actions에서 사용)
    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY가 로컬에 설정되지 않았습니다.")
        print("💡 GitHub Actions에서 AI 분석이 수행되므로 로컬 설정은 선택사항입니다.")
        print("📊 GitHub Secrets에 GEMINI_API_KEY가 설정되어 있는지 확인하세요.")
    
    # 상위 디렉토리 확인 및 생성
    parent_dir = os.path.dirname(LOCAL_DIR)
    if not os.path.exists(parent_dir):
        print(f"📁 상위 디렉토리 생성: {parent_dir}")
        os.makedirs(parent_dir, exist_ok=True)
    
    # 저장소 설정
    print("\n🔧 Git 저장소 설정 중...")
    if not setup_repository():
        print("❌ 저장소 설정 실패.")
        print("🔧 수동 해결 방법:")
        print(f"   1. 관리자 권한으로 실행")
        print(f"   2. 또는 수동으로 폴더 삭제: rmdir /s /q \"{LOCAL_DIR}\"")
        print(f"   3. 또는 LOCAL_DIR을 다른 경로로 변경")
        return
    
    # 기존 분석 결과 확인
    print("\n📊 기존 AI 분석 결과 확인 중...")
    check_analysis_results()
    
    # GitHub Actions 워크플로우 확인
    print("\n🔍 GitHub Actions 워크플로우 상태 확인 중...")
    check_github_actions_status()
    
    # 즉시 한 번 실행
    print("\n🔄 초기 뉴스 수집 및 AI 분석 트리거 시작...")
    periodic_task()
    
    schedule.every(120).seconds.do(periodic_task)
    
    print("\n" + "="*60)
    print("⏰ 자동화 시스템 가동 중")
    print("🔄 30초마다 경제 뉴스 수집 및 AI 분석 트리거")
    print("🤖 완전 자동화 플로우:")
    print("   1. 📰 뉴스 크롤링 (로컬)")
    print("   2. 📤 GitHub 업로드 (로컬)")
    print("   3. 🤖 AI 분석 트리거 (GitHub Actions)")
    print("   4. 📊 분석 결과 생성 (Gemini AI)")
    print("   5. 📥 결과 자동 업로드 (GitHub)")
    print("\n📊 분석 결과는 analysis_*.md 파일로 자동 생성됩니다")
    print("🔗 GitHub 리포지토리에서 실시간 확인 가능")
    print("🛑 종료하려면 Ctrl+C를 누르세요")
    print("="*60)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")
        print("🔄 GitHub Actions는 계속해서 자동 분석을 수행합니다.")
        print("📊 새로운 뉴스 파일이 업로드되면 자동으로 AI 분석이 실행됩니다.")

# agent.py 파일 끝에 추가해서 테스트하세요

def debug_github_connection():
    """GitHub 연결 상태 디버깅"""
    print("🔍 GitHub 연결 디버깅 시작...")
    
    # 1. 환경변수 확인
    print(f"1️⃣ GITHUB_TOKEN: {'설정됨' if GITHUB_TOKEN else '❌ 미설정'}")
    
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN을 먼저 설정하세요!")
        return
    
    # 2. Token 권한 확인
    try:
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        user_response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if user_response.status_code == 200:
            user_info = user_response.json()
            print(f"2️⃣ GitHub 인증: ✅ {user_info.get('login')}")
        else:
            print(f"2️⃣ GitHub 인증: ❌ {user_response.status_code}")
            return
    except Exception as e:
        print(f"2️⃣ GitHub 인증 오류: {e}")
        return
    
    # 3. 리포지토리 이름 추출 및 확인
    try:
        import re
        repo_match = re.search(r'github\.com/([^/]+/[^/.]+)', REPO_URL)
        if repo_match:
            repo_name = repo_match.group(1)
            print(f"3️⃣ 추출된 리포지토리: {repo_name}")
        else:
            print("3️⃣ 리포지토리 이름 추출 실패")
            print(f"   REPO_URL: {REPO_URL}")
            return
    except Exception as e:
        print(f"3️⃣ 리포지토리 이름 추출 오류: {e}")
        return
    
    # 4. 리포지토리 접근 확인
    try:
        repo_url = f"https://api.github.com/repos/{repo_name}"
        repo_response = requests.get(repo_url, headers=headers, timeout=10)
        
        if repo_response.status_code == 200:
            repo_info = repo_response.json()
            print(f"4️⃣ 리포지토리 접근: ✅")
            print(f"   이름: {repo_info.get('full_name')}")
            print(f"   Private: {repo_info.get('private')}")
            print(f"   URL: {repo_info.get('html_url')}")
        elif repo_response.status_code == 404:
            print(f"4️⃣ 리포지토리 접근: ❌ 404 (찾을 수 없음)")
            print(f"   확인사항:")
            print(f"   - 리포지토리 이름이 정확한가? {repo_name}")
            print(f"   - Private 리포지토리라면 Token에 repo 권한이 있는가?")
        else:
            print(f"4️⃣ 리포지토리 접근: ❌ {repo_response.status_code}")
    except Exception as e:
        print(f"4️⃣ 리포지토리 접근 오류: {e}")
        return
    
    # 5. GitHub Actions 확인
    try:
        actions_url = f"https://api.github.com/repos/{repo_name}/actions/runs"
        actions_response = requests.get(actions_url, headers=headers, timeout=10)
        
        if actions_response.status_code == 200:
            runs = actions_response.json().get('workflow_runs', [])
            print(f"5️⃣ GitHub Actions: ✅ (실행 기록 {len(runs)}개)")
        elif actions_response.status_code == 404:
            print(f"5️⃣ GitHub Actions: ⚠️ 워크플로우 없음")
            print(f"   .github/workflows/ 폴더에 yml 파일이 있는지 확인하세요")
        else:
            print(f"5️⃣ GitHub Actions: ❌ {actions_response.status_code}")
    except Exception as e:
        print(f"5️⃣ GitHub Actions 확인 오류: {e}")

# agent.py 파일 끝에 추가 (수정된 버전)

def debug_github_connection():
    """GitHub 연결 상태 디버깅"""
    print("🔍 GitHub 연결 디버깅 시작...")
    
    # 1. 환경변수 확인
    print(f"1️⃣ GITHUB_TOKEN: {'설정됨' if GITHUB_TOKEN else '❌ 미설정'}")
    
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN을 먼저 설정하세요!")
        return
    
    # 2. Token 권한 확인
    try:
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        user_response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if user_response.status_code == 200:
            user_info = user_response.json()
            print(f"2️⃣ GitHub 인증: ✅ {user_info.get('login')}")
        else:
            print(f"2️⃣ GitHub 인증: ❌ {user_response.status_code}")
            return
    except Exception as e:
        print(f"2️⃣ GitHub 인증 오류: {e}")
        return
    
    # 3. 리포지토리 이름 추출 및 확인
    try:
        import re
        repo_match = re.search(r'github\.com/([^/]+/[^/.]+)', REPO_URL)
        if repo_match:
            repo_name = repo_match.group(1)
            print(f"3️⃣ 추출된 리포지토리: {repo_name}")
        else:
            print("3️⃣ 리포지토리 이름 추출 실패")
            print(f"   REPO_URL: {REPO_URL}")
            return
    except Exception as e:
        print(f"3️⃣ 리포지토리 이름 추출 오류: {e}")
        return
    
    # 4. 리포지토리 접근 확인
    try:
        repo_url = f"https://api.github.com/repos/{repo_name}"
        repo_response = requests.get(repo_url, headers=headers, timeout=10)
        
        if repo_response.status_code == 200:
            repo_info = repo_response.json()
            print(f"4️⃣ 리포지토리 접근: ✅")
            print(f"   이름: {repo_info.get('full_name')}")
            print(f"   Private: {repo_info.get('private')}")
            print(f"   URL: {repo_info.get('html_url')}")
        elif repo_response.status_code == 404:
            print(f"4️⃣ 리포지토리 접근: ❌ 404 (찾을 수 없음)")
            print(f"   확인사항:")
            print(f"   - 리포지토리 이름이 정확한가? {repo_name}")
            print(f"   - Private 리포지토리라면 Token에 repo 권한이 있는가?")
        else:
            print(f"4️⃣ 리포지토리 접근: ❌ {repo_response.status_code}")
    except Exception as e:
        print(f"4️⃣ 리포지토리 접근 오류: {e}")
        return
    
    # 5. GitHub Actions 확인
    try:
        actions_url = f"https://api.github.com/repos/{repo_name}/actions/runs"
        actions_response = requests.get(actions_url, headers=headers, timeout=10)
        
        if actions_response.status_code == 200:
            runs = actions_response.json().get('workflow_runs', [])
            print(f"5️⃣ GitHub Actions: ✅ (실행 기록 {len(runs)}개)")
        elif actions_response.status_code == 404:
            print(f"5️⃣ GitHub Actions: ⚠️ 워크플로우 없음")
            print(f"   .github/workflows/ 폴더에 yml 파일이 있는지 확인하세요")
        else:
            print(f"5️⃣ GitHub Actions: ❌ {actions_response.status_code}")
    except Exception as e:
        print(f"5️⃣ GitHub Actions 확인 오류: {e}")

# 디버깅 실행 (수정된 부분)
# if __name__ == "__main__":
#     debug_github_connection()

if __name__ == "__main__":
    main()

