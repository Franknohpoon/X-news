import tweepy
import feedparser
import os
import requests
from datetime import datetime

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

# 뉴스 피드 소스 (한국 주요 언론사)
NEWS_FEEDS = {
    '크립토': [
        'https://www.coindeskkorea.com/rss',  # 코인데스크코리아
        'https://www.tokenpost.kr/rss/index.xml',  # 토큰포스트
        'https://www.blockmedia.co.kr/feed',  # 블록미디어
    ],
    '정치': [
        'https://www.chosun.com/arc/outboundfeeds/rss/politics/?outputType=xml',  # 조선일보 정치
        'https://rss.hankyung.com/politics.xml',  # 한국경제 정치
    ],
    '경제': [
        'https://rss.hankyung.com/new/news.xml',  # 한국경제 전체
        'https://www.mk.co.kr/rss/30000001/',  # 매일경제 경제
        'https://www.sedaily.com/RSS/S01.xml',  # 서울경제
    ],
    '연예': [
        'https://entertain.naver.com/movie',  # 네이버 연예 (RSS 형식 변환 필요)
        'https://www.mk.co.kr/rss/50200011/',  # 매일경제 연예
    ]
}

def fetch_news(category, feed_url, max_items=3):
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

def create_twitter_summary():
    """X용 짧은 요약 생성 (280자 제한)"""
    today = datetime.now().strftime('%Y년 %m월 %d일')
    
    tweet = f"📰 {today} 주요 뉴스\n\n"
    
    for category, feeds in NEWS_FEEDS.items():
        tweet += f"🔹 {category}\n"
        
        all_news = []
        for feed_url in feeds:
            news_items = fetch_news(category, feed_url, max_items=2)
            all_news.extend(news_items)
        
        # 카테고리당 최대 2개 뉴스
        for item in all_news[:2]:
            title = item['title'][:80] + '...' if len(item['title']) > 80 else item['title']
            tweet += f"• {title}\n"
        
        tweet += "\n"
    
    tweet += "#뉴스요약 #데일리뉴스"
    
    # 트윗 길이 제한
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    
    return tweet

def create_telegram_summary():
    """텔레그램용 상세 요약 생성 (길이 제한 없음)"""
    today = datetime.now().strftime('%Y년 %m월 %d일')
    
    message = f"📰 <b>{today} 주요 뉴스</b>\n\n"
    
    for category, feeds in NEWS_FEEDS.items():
        # 카테고리 이모지 추가
        emoji_map = {
            '크립토': '💰',
            '정치': '🏛',
            '경제': '📈',
            '연예': '🎬'
        }
        emoji = emoji_map.get(category, '🔹')
        
        message += f"{emoji} <b>{category}</b>\n"
        
        all_news = []
        for feed_url in feeds:
            news_items = fetch_news(category, feed_url, max_items=3)
            all_news.extend(news_items)
        
        # 카테고리당 최대 3개 뉴스 (텔레그램은 더 많이 가능)
        for idx, item in enumerate(all_news[:3], 1):
            title = item['title']
            link = item['link']
            
            # 텔레그램은 링크를 클릭 가능하게 표시
            if link:
                message += f"{idx}. <a href='{link}'>{title}</a>\n"
            else:
                message += f"{idx}. {title}\n"
        
        message += "\n"
    
    message += "━━━━━━━━━━━━━━━\n"
    message += "#뉴스요약 #데일리뉴스"
    
    return message

def post_tweet(tweet_text):
    """X에 트윗 포스팅"""
    try:
        client = get_twitter_client()
        response = client.create_tweet(text=tweet_text)
        print(f"✅ X 트윗 포스팅 성공! ID: {response.data['id']}")
        return True
    except Exception as e:
        print(f"❌ X 트윗 포스팅 실패: {e}")
        return False

def send_telegram_message(message):
    """텔레그램으로 메시지 전송"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("⚠️  텔레그램 설정이 없습니다. X만 포스팅합니다.")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("✅ 텔레그램 메시지 전송 성공!")
            return True
        else:
            print(f"❌ 텔레그램 메시지 전송 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 텔레그램 에러: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🤖 뉴스 봇 시작...\n")
    
    # X용 요약 생성 및 포스팅
    print("📱 X 트윗 생성 중...")
    twitter_summary = create_twitter_summary()
    print("-" * 50)
    print(twitter_summary)
    print("-" * 50)
    twitter_success = post_tweet(twitter_summary)
    
    print("\n")
    
    # 텔레그램용 요약 생성 및 전송
    print("💬 텔레그램 메시지 생성 중...")
    telegram_summary = create_telegram_summary()
    print("-" * 50)
    print(telegram_summary)
    print("-" * 50)
    telegram_success = send_telegram_message(telegram_summary)
    
    print("\n" + "=" * 50)
    if twitter_success and telegram_success:
        print("✅ 모든 플랫폼 포스팅 완료!")
    elif twitter_success:
        print("✅ X 포스팅 완료! (텔레그램 스킵)")
    elif telegram_success:
        print("✅ 텔레그램 전송 완료! (X 스킵)")
    else:
        print("❌ 포스팅 실패")
    print("=" * 50)

if __name__ == "__main__":
    main()
