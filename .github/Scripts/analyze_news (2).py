# .github/scripts/analyze_news.py
import os
import sys
import re
import google.generativeai as genai
from datetime import datetime
import json

def setup_gemini():
    """Gemini AI 설정"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

def parse_news_file(filename):
    """뉴스 파일 파싱"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 기본 정보 추출
        timestamp_match = re.search(r'📊 경제 기사 리포트 \((\d+_\d+) 기준\)', content)
        timestamp = timestamp_match.group(1) if timestamp_match else "unknown"
        
        # 기사 수 추출
        article_count_match = re.search(r'📈 총 수집 기사 수: (\d+)건', content)
        article_count = article_count_match.group(1) if article_count_match else "0"
        
        # 개별 기사 추출
        articles = []
        article_pattern = r'\[(\d+)\] (.*?)\n    📅 발행일: (.*?)\n    📝 요약: (.*?)\n    🔗 링크: (.*?)\n    📰 출처: (.*?)\n'
        
        for match in re.finditer(article_pattern, content, re.DOTALL):
            article = {
                'index': match.group(1),
                'title': match.group(2).strip(),
                'date': match.group(3).strip(),
                'summary': match.group(4).strip(),
                'url': match.group(5).strip(),
                'source': match.group(6).strip()
            }
            articles.append(article)
        
        return {
            'timestamp': timestamp,
            'article_count': article_count,
            'articles': articles,
            'raw_content': content
        }
        
    except Exception as e:
        print(f"❌ 파일 파싱 오류: {e}")
        return None

def create_investment_analysis_prompt(news_data):
    """투자 분석을 위한 프롬프트 생성"""
    articles_text = ""
    for i, article in enumerate(news_data['articles'], 1):
        articles_text += f"""
[기사 {i}]
제목: {article['title']}
요약: {article['summary']}
출처: {article['source']}
발행일: {article['date']}
---
"""
    
    prompt = f"""
다음은 {news_data['article_count']}건의 한국 경제 뉴스입니다. 전문 투자자 관점에서 종합적으로 분석해주세요.

{articles_text}

다음 관점에서 상세히 분석해주세요:

## 📊 시장 영향 분석
- 주식시장(코스피/코스닥)에 미치는 영향
- 환율, 금리, 채권시장 영향
- 섹터별 영향도 (반도체, 자동차, 바이오, 금융, 부동산 등)

## 🎯 투자 기회 및 위험
- 단기 투자 기회 (1-3개월)
- 중기 투자 전략 (6개월-1년)
- 장기 투자 관점 (1년 이상)
- 주요 위험 요소들

## 💡 섹터별 투자 전략
- 유망 섹터와 이유
- 회피해야 할 섹터와 이유
- 관련 개별 종목 언급 (구체적 종목명)

## 📈 투자자 액션 플랜
- 즉시 고려할 사항
- 지켜봐야 할 지표들
- 포트폴리오 조정 방향

## 🔍 추가 모니터링 포인트
- 향후 주목해야 할 경제지표
- 정책 변화 모니터링 포인트
- 글로벌 이슈 연관성

분석 시 다음 사항을 고려해주세요:
- 구체적이고 실행 가능한 투자 아이디어 제시
- 리스크 수준별 투자 방안 구분
- 개인투자자와 기관투자자 관점 모두 고려
- 현실적인 투자 금액대별 전략 차별화

한국어로 전문적이면서도 이해하기 쉽게 작성해주세요.
"""
    
    return prompt

def analyze_with_gemini(model, news_data):
    """Gemini AI를 사용한 뉴스 분석"""
    try:
        prompt = create_investment_analysis_prompt(news_data)
        
        print(f"🤖 Gemini AI 분석 시작...")
        print(f"📊 분석 대상: {news_data['article_count']}건의 경제 뉴스")
        
        response = model.generate_content(prompt)
        
        if response.text:
            print(f"✅ 분석 완료 (응답 길이: {len(response.text)} 문자)")
            return response.text
        else:
            print(f"❌ 분석 응답이 비어있습니다")
            return None
            
    except Exception as e:
        print(f"❌ Gemini 분석 오류: {e}")
        return None

def create_analysis_markdown(news_data, analysis_result, original_filename):
    """분석 결과를 마크다운으로 저장"""
    
    # 타임스탬프 기반 파일명 생성
    timestamp = news_data['timestamp']
    analysis_filename = f"analysis_{timestamp}.md"
    
    # 현재 시간
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
    
    markdown_content = f"""# 📊 경제 뉴스 투자 분석 리포트

## 📋 분석 개요
- **분석 시간**: {current_time}
- **원본 리포트**: `{original_filename}`
- **분석 대상**: {news_data['article_count']}건의 경제 뉴스
- **생성 방식**: Gemini AI 자동 분석

---

## 🗞️ 분석 대상 뉴스 요약
"""
    
    # 뉴스 요약 추가
    for i, article in enumerate(news_data['articles'], 1):
        markdown_content += f"""
### [{i}] {article['title']}
- **출처**: {article['source']}
- **발행일**: {article['date']}
- **요약**: {article['summary']}

"""
    
    markdown_content += f"""
---

## 🤖 AI 투자 분석 결과

{analysis_result}

---

## 📌 분석 정보
- **AI 모델**: Gemini Pro
- **분석 방식**: 자동화된 투자 관점 분석
- **업데이트**: GitHub Actions를 통한 자동 생성
- **주의사항**: 이 분석은 AI에 의한 자동 생성 결과이며, 투자 결정 시 반드시 추가적인 전문가 상담과 개인의 신중한 판단이 필요합니다.

---
*Generated by GitHub Actions + Gemini AI at {current_time}*
"""
    
    try:
        with open(analysis_filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ 분석 파일 생성 완료: {analysis_filename}")
        return analysis_filename
        
    except Exception as e:
        print(f"❌ 파일 생성 오류: {e}")
        return None

def main():
    """메인 실행 함수"""
    if len(sys.argv) != 2:
        print("사용법: python analyze_news.py <news_report_file>")
        sys.exit(1)
    
    news_filename = sys.argv[1]
    
    print(f"🚀 뉴스 분석 시작: {news_filename}")
    
    try:
        # Gemini AI 설정
        model = setup_gemini()
        print("✅ Gemini AI 설정 완료")
        
        # 뉴스 파일 파싱
        news_data = parse_news_file(news_filename)
        if not news_data:
            print("❌ 뉴스 파일 파싱 실패")
            sys.exit(1)
        
        print(f"✅ 뉴스 파일 파싱 완료: {news_data['article_count']}건")
        
        # Gemini로 분석
        analysis_result = analyze_with_gemini(model, news_data)
        if not analysis_result:
            print("❌ AI 분석 실패")
            sys.exit(1)
        
        # 마크다운 파일 생성
        output_file = create_analysis_markdown(news_data, analysis_result, news_filename)
        if not output_file:
            print("❌ 분석 파일 생성 실패")
            sys.exit(1)
        
        print(f"🎉 분석 완료: {output_file}")
        
    except Exception as e:
        print(f"❌ 분석 프로세스 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()