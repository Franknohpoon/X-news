import os
import requests
import feedparser
import json
from datetime import datetime, timedelta
import hashlib

# X API 사용 여부 확인
USE_TWITTER = all([
    os.environ.get('BEARER_TOKEN'),
    os.environ.get('API_KEY'),
    os.environ.get('API_SECRET'),
    os.environ.get('ACCESS_TOKEN'),
    os.environ.get('ACCESS_TOKEN_SECRET')
])

# X API 초기화
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
    print("⚠️  X API 설정 없음")

def load_news_sources():
    """news_sources.json 파일 로드"""
    try:
        with open('news_sources.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  news_sources.json 없음 - 기본 RSS만 사용")
        return {
            "정치": {
                "rss": ["https://rss.hankyung.com/politics.xml"],
                "twitter_accounts": []
            },
            "경제": {
                "rss": ["https://rss.hankyung.com/new/news.xml"],
                "twitter_accounts": []
            }
        }

# 제외 키워드
EXCLUDE_KEYWORDS = ['부고', '날씨', '교통', '미세먼지', '로또', '광고']

def is_relevant_news(text):
    """관련성 체크"""
    for word in EXCLUDE_KEYWORDS:
        if word in text:
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
                    'source': 'rss',
                    'hash': hashlib.md5(title.encode()).hexdigest()[:8]
                })
            
            if len(news_items) >= max_items:
                break
        
        return news_items
    except Exception as e:
        print(f"  RSS 에러: {e}")
        return []

def fetch_twitter_posts(username, max_results=3):
    """X 트윗 가져오기"""
    if not USE_TWITTER:
        return []
    
    try:
        client = get_twitter_client()
        username = username.replace('@', '')
        
        # 사용자 정보
        user = client.get_user(username=username)
        if not user.data:
            print(f"    ⚠️  @{username} 찾을 수 없음")
            return []
        
        user_id = user.data.id
        
        # 최근 24시간 트윗
        start_time = datetime.utcnow() - timedelta(hours=24)
        
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=max_results,
            tweet_fields=['created_at', 'public_metrics'],
            start_time=start_time,
            exclude=['retweets', 'replies']
        )
        
        news_items = []
        
        if tweets.data:
            for tweet in tweets.data:
                text = tweet.text
                link = f"https://twitter.com/{username}/status/{tweet.id}"
                
                if is_relevant_news(text):
                    news_items.append({
                        'title': text[:100] + '...' if len(text) > 100 else text,
                        'link': link,
                        'source': f'X:@{username}',
                        'hash': hashlib.md5(text.encode()).hexdigest()[:8],
                        'likes': tweet.public_metrics['like_count']
                    })
        
        return news_items
    
    except Exception as e:
        print(f"    ⚠️  X 에러 (@{username}): {e}")
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
    """모든 뉴스 수집"""
    print("\n📡 뉴스 수집 시작...\n")
    
    sources = load_news_sources()
    news_by_category = {}
    
    for category, source_config in sources.items():
        print(f"  [{category}] 수집 중...")
        all_news = []
        
        # RSS 수집
        for rss_url in source_config.get('rss', []):
            news = fetch_rss_news(rss_url, max_items=2)
            all_news.extend(news)
        
        # X 트윗 수집
        for twitter_account in source_config.get('twitter_accounts', [])[:5]:
            tweets = fetch_twitter_posts(twitter_account, max_results=2)
            all_news.extend(tweets)
        
        # 중복 제거 및 정렬
        all_news = deduplicate_news(all_news)
        all_news.sort(key=lambda x: x.get('likes', 0), reverse=True)
        
        news_by_category[category] = all_news[:5]
        print(f"    ✅ {len(news_by_category[category])}개 수집")
    
    return news_by_category

def create_telegram_summary(news_by_category):
    """텔레그램 메시지 생성"""
    today = datetime.now().strftime('%Y년 %m월 %d일 %A')
    message = f"📰 <b>{today} 주요 뉴스</b>\n\n"
    
    emoji_map = {
        '예측시장': '🎲',
        'AI': '🤖',
        '정치': '🏛',
        '경제': '📈',
        '연예': '🎬'
    }
    
    total = 0
    
    for category, news_list in news_by_category.items():
        if not news_list:
            continue
        
        emoji = emoji_map.get(category, '🔹')
        message += f"{emoji} <b>{category}</b>\n"
        
        for idx, item in enumerate(news_list[:3], 1):
            title = item['title']
            link = item['link']
            source_icon = '📱' if 'X:' in item['source'] else '📰'
            
            if link:
                message += f"{idx}. <a href='{link}'>{title}</a> {source_icon}\n"
            else:
                message += f"{idx}. {title} {source_icon}\n"
            
            total += 1
        
        message += "\n"
    
    if total == 0:
        message += "⚠️ 수집된 뉴스가 없습니다.\n\n"
    
    message += "━━━━━━━━━━━━━━━\n"
    message += f"총 {total}개 • #뉴스요약"
    
    return message

def send_to_telegram(message):
    """텔레그램 전송"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ 텔레그램 설정 없음")
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
            print(f"❌ 텔레그램 실패: {response.status_code}")
            print(f"   {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ 텔레그램 에러: {e}")
        return False

def main():
    """메인 실행"""
    print("="*60)
    print("🤖 뉴스 봇 시작 (RSS + X 트윗)")
    print("="*60)
    
    # 뉴스 수집
    news_by_category = collect_all_news()
    
    print("\n" + "="*60)
    
    # 텔레그램 전송
    print("\n💬 텔레그램 메시지 생성 중...")
    telegram_summary = create_telegram_summary(news_by_category)
    print("-" * 50)
    print(telegram_summary)
    print("-" * 50)
    telegram_success = send_to_telegram(telegram_summary)
    
    print("\n" + "="*60)
    if telegram_success:
        print("✅ 텔레그램 전송 완료!")
    else:
        print("❌ 전송 실패")
    print("="*60)

if __name__ == "__main__":
    main()
