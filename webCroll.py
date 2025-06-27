import requests
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import time
import re
import random
from bs4 import BeautifulSoup

# 전역 변수로 마지막 크롤링 시간과 캐시 관리
last_crawl_time = None
cached_news = None
CACHE_DURATION = 60  # 60초 캐시 지속시간

def get_rss_feeds():
    """한국 주요 경제 뉴스 RSS 피드 목록"""
    rss_feeds = [
        {
            'name': '한국경제',
            'url': 'https://www.hankyung.com/feed/economy',
            'category': '경제'
        },
        {
            'name': '연합뉴스 경제',
            'url': 'https://www.yna.co.kr/rss/economy.xml',
            'category': '경제'
        },
        {
            'name': '매일경제',
            'url': 'https://www.mk.co.kr/rss/30000042/',
            'category': '경제'
        },
        {
            'name': '머니투데이',
            'url': 'https://rss.mt.co.kr/mt_newsflash.xml',
            'category': '속보'
        },
        {
            'name': '조선비즈',
            'url': 'https://biz.chosun.com/rss/finance.xml',
            'category': '금융'
        }
    ]
    return rss_feeds

def crawl_rss_news(max_articles=20):
    """RSS 피드로 경제 뉴스 크롤링"""
    
    print(f"📰 RSS 피드로 경제 뉴스 수집 중... (최대 {max_articles}개)")
    
    all_articles = []
    rss_feeds = get_rss_feeds()
    
    for feed_info in rss_feeds:
        try:
            print(f"   📡 {feed_info['name']} RSS 수집 중...")
            
            # RSS 피드 파싱
            feed = feedparser.parse(feed_info['url'])
            
            if feed.bozo:
                print(f"   ⚠️ {feed_info['name']} RSS 파싱 오류: {feed.bozo_exception}")
                continue
            
            if not feed.entries:
                print(f"   ⚠️ {feed_info['name']} RSS에 항목이 없습니다.")
                continue
            
            print(f"   ✅ {feed_info['name']}에서 {len(feed.entries)}개 항목 발견")
            
            # 각 기사 처리
            feed_count = 0
            for entry in feed.entries:
                try:
                    # 제목 추출
                    title = entry.title if hasattr(entry, 'title') else '제목 없음'
                    title = re.sub(r'<[^>]+>', '', title).strip()  # HTML 태그 제거
                    
                    # 링크 추출
                    link = entry.link if hasattr(entry, 'link') else ''
                    
                    # 요약 추출
                    summary = ''
                    if hasattr(entry, 'summary'):
                        summary = entry.summary
                        summary = re.sub(r'<[^>]+>', '', summary).strip()  # HTML 태그 제거
                        if len(summary) > 200:
                            summary = summary[:200] + "..."
                    
                    if not summary:
                        summary = f"{title}에 관한 {feed_info['name']} 뉴스입니다."
                    
                    # 발행일 추출
                    pub_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            pub_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M")
                        except:
                            pass
                    elif hasattr(entry, 'published'):
                        pub_date = entry.published[:16] if len(entry.published) > 16 else entry.published
                    
                    # 경제 관련 키워드 확인
                    economic_keywords = [
                        '경제', '금융', '주식', '부동산', '증시', '환율', 'GDP', '금리', '인플레이션', 
                        '기업', '산업', '무역', '투자', '시장', '코스피', '코스닥', '재정', '예산',
                        '은행', '대출', '적금', '펀드', '보험', '카드', '결제', '핀테크',
                        '수출', '수입', '관세', '통상', 'FTA', '제조업', '서비스업',
                        '반도체', '자동차', '조선', '철강', '화학', '바이오', 'IT', 'AI',
                        '부가세', '소득세', '법인세', '세금', '세율', '조세',
                        '채권', '국채', '회사채', '수익률', '배당',
                        '소비', '물가', '가격', '비용', '매출', '수익', '손실',
                        '고용', '취업', '실업', '일자리', '임금', '연봉',
                        '정부', '한국은행', '금융위', '기획재정부',
                        '달러', '원화', '유로', '엔화', '위안화'
                    ]
                    
                    # 제목에 경제 키워드가 있거나, 경제 카테고리 RSS인 경우 포함
                    has_economic_keyword = any(keyword in title for keyword in economic_keywords)
                    is_economic_category = feed_info['category'] in ['경제', '금융']
                    
                    if has_economic_keyword or is_economic_category:
                        article = {
                            '제목': title,
                            '요약': summary,
                            '발행일': pub_date,
                            'URL': link,
                            '출처': feed_info['name']
                        }
                        
                        all_articles.append(article)
                        feed_count += 1
                        
                        print(f"     📝 수집: {title[:50]}...")
                        
                        # 피드당 최대 5개까지만
                        if feed_count >= 5:
                            break
                
                except Exception as e:
                    print(f"     ❌ 기사 처리 중 오류: {e}")
                    continue
            
            print(f"   ✅ {feed_info['name']}에서 {feed_count}개 수집 완료")
            
            # 피드 간 간격
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"   ❌ {feed_info['name']} RSS 수집 실패: {e}")
            continue
    
    # 발행일 기준으로 정렬 (최신순)
    if all_articles:
        try:
            all_articles.sort(key=lambda x: x['발행일'], reverse=True)
        except:
            pass
    
    # 최대 개수 제한
    if len(all_articles) > max_articles:
        all_articles = all_articles[:max_articles]
    
    print(f"✅ 총 {len(all_articles)}건의 경제 뉴스 수집 완료")
    
    # DataFrame 생성
    if len(all_articles) == 0:
        print("❌ 수집된 뉴스가 없습니다.")
        return pd.DataFrame(columns=['제목', '요약', '발행일', 'URL', '출처'])
    
    try:
        df = pd.DataFrame(all_articles)
        return df
    except Exception as e:
        print(f"❌ DataFrame 생성 실패: {e}")
        return pd.DataFrame(columns=['제목', '요약', '발행일', 'URL', '출처'])

def filter_economic_news(df):
    """경제 뉴스 필터링 (RSS는 이미 필터링되어 있으므로 간단한 처리)"""
    try:
        if df.empty:
            print("⚠️ 수집된 뉴스가 없습니다.")
            return df
        
        print(f"🔍 RSS 뉴스 수: {len(df)}건")
        
        # 결측값 처리
        df = df.fillna('')
        
        # 문자열 변환
        for col in df.columns:
            df[col] = df[col].astype(str)
        
        # 중복 제거 (제목 기준)
        before_count = len(df)
        df = df.drop_duplicates(subset=['제목'], keep='first')
        after_count = len(df)
        
        if before_count != after_count:
            print(f"🔄 중복 제거: {before_count}건 → {after_count}건")
        
        print(f"✅ 최종 뉴스 수: {len(df)}건")
        return df
        
    except Exception as e:
        print(f"❌ 필터링 중 오류: {e}")
        return df

def create_sample_economic_news():
    """크롤링 실패시 샘플 경제 뉴스 데이터 생성"""
    sample_news = [
        {
            '제목': '한국은행, 기준금리 동결 결정...경제 불확실성 고려',
            '요약': '한국은행이 이번달 금융통화위원회에서 기준금리를 현 수준에서 동결하기로 결정했다. 대내외 경제 불확실성과 인플레이션 압력을 종합적으로 고려한 결과다.',
            '발행일': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'URL': 'https://example.com/news/1',
            '출처': '한국경제'
        },
        {
            '제목': '코스피 2600선 회복...외국인 매수세 지속',
            '요약': '코스피 지수가 장중 2600선을 회복하며 상승세를 보이고 있다. 외국인 투자자들의 지속적인 매수세가 지수 상승을 견인했다는 분석이다.',
            '발행일': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'URL': 'https://example.com/news/2',
            '출처': '연합뉴스'
        },
        {
            '제목': '부동산 정책 변화 신호...정부 규제 완화 검토',
            '요약': '정부가 부동산 시장 안정화를 위해 일부 규제 완화 방안을 검토하고 있다고 발표했다. 주택 공급 확대와 시장 활성화가 주요 목표다.',
            '발행일': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'URL': 'https://example.com/news/3',
            '출처': '매일경제'
        },
        {
            '제목': '반도체 수출 증가세...올해 2분기 실적 기대',
            '요약': '한국의 반도체 수출이 전년 동기 대비 증가세를 보이며 올해 2분기 실적에 대한 기대감이 높아지고 있다. AI 수요 증가가 주요 요인으로 분석된다.',
            '발행일': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'URL': 'https://example.com/news/4',
            '출처': '조선비즈'
        },
        {
            '제목': '환율 안정세...원/달러 1,380원대 유지',
            '요약': '원/달러 환율이 1,380원대에서 안정세를 보이고 있다. 미 연준의 통화정책 변화 기대감과 국내 수출 호조가 영향을 미쳤다는 분석이다.',
            '발행일': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'URL': 'https://example.com/news/5',
            '출처': '머니투데이'
        }
    ]
    
    return pd.DataFrame(sample_news)

def generate_per_report():
    """경제 뉴스 리포트 생성 (RSS 기반 + 캐시 시스템)"""
    global last_crawl_time, cached_news
    
    try:
        print("📊 경제 뉴스 리포트 생성 시작...")
        
        # 캐시 확인 (60초 이내면 캐시 사용)
        current_time = datetime.now()
        if (last_crawl_time and cached_news is not None and 
            (current_time - last_crawl_time).seconds < CACHE_DURATION):
            
            remaining_time = CACHE_DURATION - (current_time - last_crawl_time).seconds
            print(f"🔄 캐시된 데이터 사용 (갱신까지 {remaining_time}초 남음)")
            economic_news = cached_news
        else:
            # 새로 크롤링
            print("🕐 새로운 뉴스 데이터 수집 중...")
            
            # 크롤링 간격 체크 (최소 30초 간격 보장 - RSS는 덜 제한적)
            if last_crawl_time:
                time_diff = (current_time - last_crawl_time).seconds
                if time_diff < 30:
                    wait_time = 30 - time_diff
                    print(f"⏳ 적절한 간격을 위해 {wait_time}초 대기 중...")
                    time.sleep(wait_time)
            
            # RSS 크롤링 수행
            news_df = crawl_rss_news(max_articles=15)
            
            if news_df.empty:
                if cached_news is not None:
                    print("⚠️ 새 데이터 수집 실패 - 이전 캐시 데이터 사용")
                    economic_news = cached_news
                else:
                    print("⚠️ RSS 수집 실패 - 샘플 데이터 사용")
                    economic_news = create_sample_economic_news()
            else:
                # 경제 뉴스 필터링
                economic_news = filter_economic_news(news_df)
                
                if economic_news.empty:
                    if cached_news is not None:
                        print("⚠️ 필터링된 뉴스 없음 - 이전 캐시 데이터 사용")
                        economic_news = cached_news
                    else:
                        print("⚠️ 필터링 결과 없음 - 샘플 데이터 사용")
                        economic_news = create_sample_economic_news()
                else:
                    # 캐시 업데이트
                    cached_news = economic_news.copy()
                    last_crawl_time = current_time
                    print(f"✅ 새 데이터 캐시 업데이트 완료")
        
        # 리포트 파일 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"economic_news_report_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"📊 경제 기사 리포트 ({timestamp} 기준)\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"📈 총 수집 기사 수: {len(economic_news)}건\n")
            f.write(f"🕐 생성 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분 %S초')}\n")
            f.write(f"📡 데이터 소스: RSS 피드 (한국경제, 연합뉴스, 매일경제, 머니투데이, 조선비즈)\n")
            
            # 캐시 상태 표시
            if last_crawl_time:
                cache_age = (current_time - last_crawl_time).seconds
                f.write(f"🔄 데이터 수집 시간: {last_crawl_time.strftime('%H:%M:%S')} ({cache_age}초 전)\n\n")
            else:
                f.write(f"🔄 데이터 수집 시간: 방금 전\n\n")
            
            # 출처별 통계
            if '출처' in economic_news.columns:
                source_counts = economic_news['출처'].value_counts()
                f.write("📊 출처별 기사 수:\n")
                for source, count in source_counts.items():
                    f.write(f"   - {source}: {count}건\n")
                f.write("\n")
            
            for idx, row in economic_news.iterrows():
                f.write(f"[{idx+1}] {row['제목']}\n")
                f.write(f"    📅 발행일: {row['발행일']}\n")
                f.write(f"    📝 요약: {row['요약']}\n")
                f.write(f"    🔗 링크: {row['URL']}\n")
                if '출처' in row:
                    f.write(f"    📰 출처: {row['출처']}\n")
                f.write(f"    {'-'*50}\n\n")
        
        print(f"✅ {len(economic_news)}건의 경제 기사 리포트 생성 완료: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ 리포트 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

# 이전 함수들과의 호환성을 위한 별칭
def crawl_naver_news(query="경제", max_pages=1):
    """호환성을 위한 함수 - RSS 크롤링으로 리다이렉트"""
    print("📡 RSS 피드 방식으로 전환하여 뉴스 수집 중...")
    return crawl_rss_news(max_articles=10)