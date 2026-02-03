import tweepy
import feedparser
import os
from datetime import datetime
import json

# X API 인증
def get_twitter_client():
    """X API 클라이언트 초기화"""
    client = tweepy.Client(
        bearer_token=os.environ.get('BEARER_TOKEN'),
        consumer_key=os.environ.get('API_KEY'),
        consumer_secret=os.environ.get('API_SECRET'),
        access_token=os.environ.get('ACCESS_TOKEN'),
        access_token_secret=os.environ.get('ACCESS_TOKEN_SECRET')
    )
    return client

# 뉴스 피드 소스 (한국어)
NEWS_FEEDS = {
    '크립토': [
        'https://www.coindeskkorea.com/rss',
        'https://www.blockmedia.co.kr/feed',
    ],
    '정치': [
        'https://news.google.com/rss/search?q=정치+when:1d&hl=ko&gl=KR&ceid=KR:ko',
    ],
    '경제': [
        'https://news.google.com/rss/search?q=경제+when:1d&hl=ko&gl=KR&ceid=KR:ko',
    ],
    '연예': [
        'https://news.google.com/rss/search?q=연예+when:1d&hl=ko&gl=KR&ceid=KR:ko',
    ]
}

def fetch_news(category, feed_url, max_items=2):
    """RSS 피드에서 뉴스 가져오기"""
    try:
        feed = feedparser.parse(feed_url)
        news_items = []
        
        for entry in feed.entries[:max_items]:
            title = entry.title
            link = entry.link if hasattr(entry, 'link') else ''
            news_items.append({
                'title': title,
                'link': link
            })
        
        return news_items
    except Exception as e:
        print(f"Error fetching {category} news: {e}")
        return []

def create_daily_summary():
    """일일 뉴스 요약 생성"""
    today = datetime.now().strftime('%Y년 %m월 %d일')
    
    tweet = f"📰 {today} 주요 뉴스\n\n"
    
    # 각 카테고리별로 뉴스 수집
    for category, feeds in NEWS_FEEDS.items():
        tweet += f"🔹 {category}\n"
        
        all_news = []
        for feed_url in feeds:
            news_items = fetch_news(category, feed_url, max_items=2)
            all_news.extend(news_items)
        
        # 카테고리당 최대 2개 뉴스
        for item in all_news[:2]:
            # 트윗 길이 제한 고려
            title = item['title'][:80] + '...' if len(item['title']) > 80 else item['title']
            tweet += f"• {title}\n"
        
        tweet += "\n"
    
    tweet += "#뉴스요약 #데일리뉴스"
    
    # 트윗 길이 제한 (280자 초과시 자르기)
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    
    return tweet

def post_tweet(tweet_text):
    """트윗 포스팅"""
    try:
        client = get_twitter_client()
        response = client.create_tweet(text=tweet_text)
        print(f"✅ Tweet posted successfully! ID: {response.data['id']}")
        return True
    except Exception as e:
        print(f"❌ Error posting tweet: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🤖 뉴스 봇 시작...")
    
    # 뉴스 요약 생성
    daily_summary = create_daily_summary()
    print("\n생성된 트윗:")
    print("-" * 50)
    print(daily_summary)
    print("-" * 50)
    
    # 트윗 포스팅
    success = post_tweet(daily_summary)
    
    if success:
        print("✅ 오늘의 뉴스 봇 실행 완료!")
    else:
        print("❌ 트윗 포스팅 실패")

if __name__ == "__main__":
    main()
