import os
import requests
import feedparser
from datetime import datetime
import hashlib

# X API 사용 여부 확인
USE_TWITTER = all([
    os.environ.get('BEARER_TOKEN'),
    os.environ.get('API_KEY'),
    os.environ.get('API_SECRET'),
    os.environ.get('ACCESS_TOKEN'),
    os.environ.get('ACCESS_TOKEN_SECRET')
])

# X API 초기화 (있는 경우만)
if USE_TWITTER:
    try:
        import tweepy
        def get_twitter_client():
            client = tweepy.Client(
                bearer_token=os.environ.get('BEARER_TOKEN'),
                consumer_key=os.environ.get('API_KEY'),
                consumer_secret=os.environ.get('API_SECRET'),
                access_token=os.environ.get('ACCESS_TOKEN'),
                access_token_secret=os.environ.get('ACCESS_TOKEN_SECRET')
            )
            return client
        print("✅ X API 사용 가능")
    except Exception as e:
        USE_TWITTER = False
        print(f"⚠️  X API 초기화 실패: {e}")
else:
    print("⚠️  X API 설정 없음 - 텔레그램만 사용")

# 뉴스 소스 (RSS)
NEWS_FEEDS = {
    '크립토': [
        'https://www.coindeskkorea.com/rss',
        'https://www.tokenpost.kr/rss/index.xml',
    ],
    '정치': [
        'https://www.chosun.com/arc/outboundfeeds/rss/politics/?outputType=xml',
    ],
    '경제': [
        'https://rss.hankyung.com/new/news.xml',
        'https://www.mk.co.kr/rss/30000001/',
    ],
    '연예': [
        'https://www.mk.co.kr/rss/50200011/',
    ]
}

# 제외 키워드
EXCLUDE_KEYWORDS = ['부고', '날씨', '교통', '미세먼지', '로또', '광고']

def is_relevant_news(title):
    """뉴스 관련성 체크"""
    for word in EXCLUDE_KEYWORDS:
        if word in title:
            return False
    return True

def fetch_rss_news(feed_url, max_items=3):
    """RSS 뉴스 가져오기"""
    try:
        feed = feedparser.parse(feed_url)
        news_items = []
        
        for entry in feed.entries[:max_items * 2]:
            title = entry.title
            link = entry.link if hasattr(entry, 'link') else ''
            
            if is_relevant_news(title):
                news_items.append({
                    'title': title,
                    'link': link,
                    'hash': hashlib.md5(title.encode()).hexdigest()[:8]
                })
            
            if len(news_items) >= max_items:
                break
        
        return news_items
    except Exception as e:
        print(f"  RSS 에러: {e}")
        return []

def deduplicate_news(news_list):
    """중복 제거"""
    seen = set()
    unique = []
    for news in news_list:
        if news['hash'] not in seen:
            seen.add(news['hash'])
            unique.append(news)
    return unique

def collect_all_news():
    """모든 카테고리 뉴스 수집"""
    print("\n📡 뉴스 수집 시작...\n")
    
    news_by_category = {}
    
    for category, feeds in NEWS_FEEDS.items():
        print(f"  [{category}] 수집 중...")
        all_news = []
        
        for feed_url in feeds:
            news = fetch_rss_news(feed_url, max_items=3)
            all_news.extend(news)
        
        # 중복 제거
        all_news = deduplicate_news(all_news)
        news_by_category[category] = all_news[:3]  # 최대 3개
        
        print(f"    ✅ {len(news_by_category[category])}개 수집")
    
    return news_by_category

def create_twitter_summary(news_by_category):
    """X용 요약 (280자 제한)"""
    today = datetime.now().strftime('%Y년 %m월 %d일')
    tweet = f"📰 {today} 주요 뉴스\n\n"
    
    emoji_map = {'크립토': '💰', '정치': '🏛', '경제': '📈', '연예': '🎬'}
    
    for category, news_list in news_by_category.items():
        if not news_list:
            continue
        
        emoji = emoji_map.get(category, '🔹')
        tweet += f"{emoji} {category}\n"
        
        for item in news_list[:2]:
            title = item['title'][:60] + '...' if len(item['title']) > 60 else item['title']
            tweet += f"• {title}\n"
        
        tweet += "\n"
    
    tweet += "#뉴스요약 #데일리뉴스"
    
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    
    return tweet

def create_telegram_summary(news_by_category):
    """텔레그램용 상세 요약"""
    today = datetime.now().strftime('%Y년 %m월 %d일 %A')
    message = f"📰 <b>{today} 주요 뉴스</b>\n\n"
    
    emoji_map = {'크립토': '💰', '정치': '🏛', '경제': '📈', '연예': '🎬'}
    total = 0
    
    for category, news_list in news_by_category.items():
        if not news_list:
            continue
        
        emoji = emoji_map.get(category, '🔹')
        message += f"{emoji} <b>{category}</b>\n"
        
        for idx, item in enumerate(news_list, 1):
            title = item['title']
            link = item['link']
            
            if link:
                message += f"{idx}. <a href='{link}'>{title}</a>\n"
            else:
                message += f"{idx}. {title}\n"
            
            total += 1
        
        message += "\n"
    
    if total == 0:
        message += "⚠️ 수집된 뉴스가 없습니다.\n\n"
    
    message += "━━━━━━━━━━━━━━━\n"
    message += f"총 {total}개 뉴스 • #뉴스요약"
    
    return message

def post_to_twitter(text):
    """X에 포스팅"""
    if not USE_TWITTER:
        print("⚠️  X API 사용 불가 - 스킵")
        return False
    
    try:
        client = get_twitter_client()
        response = client.create_tweet(text=text)
        print(f"✅ X 포스팅 성공! ID: {response.data['id']}")
        return True
    except Exception as e:
        print(f"❌ X 포스팅 실패: {e}")
        return False

def send_to_telegram(message):
    """텔레그램 전송"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ 텔레그램 설정 없음 (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ 텔레그램 전송 성공!")
            return True
        else:
            print(f"❌ 텔레그램 전송 실패:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 텔레그램 에러: {e}")
        return False

def main():
    """메인 실행"""
    print("="*60)
    print("🤖 뉴스 봇 시작")
    print("="*60)
    
    # 뉴스 수집
    news_by_category = collect_all_news()
    
    print("\n" + "="*60)
    
    # X 포스팅
    if USE_TWITTER:
        print("\n📱 X 트윗 생성 중...")
        twitter_summary = create_twitter_summary(news_by_category)
        print("-" * 50)
        print(twitter_summary)
        print("-" * 50)
        twitter_success = post_to_twitter(twitter_summary)
    else:
        twitter_success = False
        print("\n⚠️  X 포스팅 스킵")
    
    # 텔레그램 전송
    print("\n💬 텔레그램 메시지 생성 중...")
    telegram_summary = create_telegram_summary(news_by_category)
    print("-" * 50)
    print(telegram_summary)
    print("-" * 50)
    telegram_success = send_to_telegram(telegram_summary)
    
    # 결과
    print("\n" + "="*60)
    if twitter_success and telegram_success:
        print("✅ X + 텔레그램 포스팅 완료!")
    elif twitter_success:
        print("✅ X 포스팅 완료 (텔레그램 실패)")
    elif telegram_success:
        print("✅ 텔레그램 전송 완료 (X 스킵/실패)")
    else:
        print("❌ 모든 포스팅 실패")
    print("="*60)

if __name__ == "__main__":
    main()
