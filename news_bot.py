"""
X 뉴스 봇 - RSS + X 트윗 수집 → 텔레그램 전송
news_sources.json 파일을 읽어서 뉴스 수집
"""

import os
import requests
import feedparser
import json
from datetime import datetime, timedelta
import hashlib

# ==================== X API 설정 ====================

USE_TWITTER = all([
    os.environ.get('BEARER_TOKEN'),
    os.environ.get('API_KEY'),
    os.environ.get('API_SECRET'),
    os.environ.get('ACCESS_TOKEN'),
    os.environ.get('ACCESS_TOKEN_SECRET')
])

if USE_TWITTER:
    try:
        import tweepy
        def get_twitter_client():
            return tweepy.Client(
                bearer_token=os.environ.get('BEARER_TOKEN'),
                consumer_key=os.environ.get('API_KEY'),
                consumer_secret=os.environ.get('API_SECRET'),
                access_token=os.environ.get('ACCESS_TOKEN'),
                access_token_secret=os.environ.get('ACCESS_TOKEN_SECRET')
            )
        print("✅ X API 사용 가능")
    except Exception as e:
        USE_TWITTER = False
        print(f"⚠️  X API 사용 불가: {e}")
else:
    print("⚠️  X API 설정 없음 - RSS만 사용")

# ==================== 설정 ====================

EXCLUDE_KEYWORDS = ['부고', '날씨', '교통', '미세먼지', '로또', '광고', '이벤트']

EMOJI_MAP = {
    '예측시장': '🎲',
    'AI': '🤖',
    '정치': '🏛',
    '경제': '📈',
    '연예': '🎬',
    '크립토': '💰'
}

# ==================== 뉴스 소스 로드 ====================

def load_news_sources():
    """news_sources.json 파일 로드"""
    try:
        with open('news_sources.json', 'r', encoding='utf-8') as f:
            sources = json.load(f)
            print(f"✅ news_sources.json 로드 완료 ({len(sources)}개 카테고리)")
            return sources
    except FileNotFoundError:
        print("⚠️  news_sources.json 없음 - 기본 RSS만 사용")
        return {
            "정치": {
                "rss": ["https://rss.hankyung.com/politics.xml"],
                "twitter_accounts": []
            }
        }
    except Exception as e:
        print(f"❌ news_sources.json 로드 실패: {e}")
        return {}

# ==================== 뉴스 수집 ====================

def is_relevant_news(text):
    """뉴스 관련성 체크"""
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
                    'source': 'RSS',
                    'hash': hashlib.md5(title.encode()).hexdigest()[:8]
                })
            
            if len(news_items) >= max_items:
                break
        
        return news_items
    except Exception as e:
        print(f"      RSS 에러: {str(e)[:50]}")
        return []

def fetch_twitter_posts(username, max_results=3):
    """X 트윗 가져오기 (최근 24시간)"""
    if not USE_TWITTER:
        return []
    
    try:
        client = get_twitter_client()
        username = username.replace('@', '').strip()
        
        # 사용자 정보
        user = client.get_user(username=username)
        if not user.data:
            return []
        
        user_id = user.data.id
        start_time = datetime.utcnow() - timedelta(hours=24)
        
        # 트윗 가져오기
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
        print(f"      X 에러 (@{username}): {str(e)[:50]}")
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
    print("\n" + "="*60)
    print("📡 뉴스 수집 시작")
    print("="*60)
    
    sources = load_news_sources()
    news_by_category = {}
    
    for category, source_config in sources.items():
        print(f"\n🔹 [{category}]")
        all_news = []
        
        # RSS 수집
        rss_feeds = source_config.get('rss', [])
        if rss_feeds:
            print(f"  📰 RSS: {len(rss_feeds)}개 피드")
            for rss_url in rss_feeds:
                news = fetch_rss_news(rss_url, max_items=2)
                all_news.extend(news)
        
        # X 트윗 수집
        twitter_accounts = source_config.get('twitter_accounts', [])
        if twitter_accounts and USE_TWITTER:
            print(f"  📱 X: {len(twitter_accounts)}개 계정")
            for account in twitter_accounts[:5]:  # 최대 5개
                tweets = fetch_twitter_posts(account, max_results=2)
                all_news.extend(tweets)
        
        # 중복 제거 및 정렬
        all_news = deduplicate_news(all_news)
        all_news.sort(key=lambda x: x.get('likes', 0), reverse=True)
        
        news_by_category[category] = all_news[:5]  # 카테고리당 최대 5개
        print(f"  ✅ 총 {len(news_by_category[category])}개 수집")
    
    return news_by_category

# ==================== 텔레그램 전송 ====================

def create_telegram_message(news_by_category):
    """텔레그램 메시지 생성"""
    today = datetime.now().strftime('%Y년 %m월 %d일 %A')
    message = f"📰 <b>{today} 주요 뉴스</b>\n\n"
    
    total_count = 0
    
    for category, news_list in news_by_category.items():
        if not news_list:
            continue
        
        emoji = EMOJI_MAP.get(category, '🔹')
        message += f"{emoji} <b>{category}</b>\n"
        
        for idx, item in enumerate(news_list[:3], 1):  # 카테고리당 최대 3개 표시
            title = item['title']
            link = item['link']
            source_icon = '📱' if item['source'].startswith('X:') else '📰'
            
            if link:
                message += f"{idx}. <a href='{link}'>{title}</a> {source_icon}\n"
            else:
                message += f"{idx}. {title} {source_icon}\n"
            
            total_count += 1
        
        message += "\n"
    
    if total_count == 0:
        message += "⚠️ 오늘은 수집된 뉴스가 없습니다.\n\n"
    
    message += "━━━━━━━━━━━━━━━\n"
    message += f"총 {total_count}개 뉴스"
    
    return message

def send_to_telegram(message):
    """텔레그램으로 메시지 전송"""
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
            print(f"❌ 텔레그램 전송 실패")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    
    except Exception as e:
        print(f"❌ 텔레그램 에러: {e}")
        return False

# ==================== 메인 실행 ====================

def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("🤖 X 뉴스 봇 시작")
    print("="*60)
    
    # 뉴스 수집
    news_by_category = collect_all_news()
    
    # 텔레그램 메시지 생성
    print("\n" + "="*60)
    print("💬 텔레그램 메시지 생성")
    print("="*60)
    
    telegram_message = create_telegram_message(news_by_category)
    
    print("\n[생성된 메시지 미리보기]")
    print("-" * 60)
    print(telegram_message[:500] + "..." if len(telegram_message) > 500 else telegram_message)
    print("-" * 60)
    
    # 텔레그램 전송
    print("\n📤 텔레그램 전송 중...")
    success = send_to_telegram(telegram_message)
    
    # 결과
    print("\n" + "="*60)
    if success:
        print("✅ 완료!")
    else:
        print("❌ 실패")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
