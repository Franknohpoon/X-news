import tweepy
import os
import json
from collections import defaultdict

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

def categorize_account(username, name, description):
    """계정을 카테고리로 자동 분류"""
    text = f"{username} {name} {description or ''}".lower()
    
    # 크립토 키워드
    crypto_keywords = [
        'crypto', 'bitcoin', 'btc', 'ethereum', 'eth', 'blockchain', 'nft', 
        'defi', 'web3', 'coin', '코인', '비트', '이더', '암호화폐', '블록체인', 
        '가상자산', 'binance', 'coinbase', 'upbit'
    ]
    
    # 정치 키워드
    politics_keywords = [
        'politics', 'government', 'congress', 'parliament', 'president',
        '정치', '국회', '대통령', '의원', '청와대', '정부', '장관', '당대표'
    ]
    
    # 경제 키워드
    economy_keywords = [
        'economy', 'market', 'finance', 'stock', 'business', 'invest',
        '경제', '증시', '주식', '재테크', '투자', '금융', '기업', '코스피'
    ]
    
    # 연예 키워드
    entertainment_keywords = [
        'entertainment', 'movie', 'drama', 'kpop', 'k-pop', 'celebrity',
        '연예', '영화', '드라마', '예능', '아이돌', '배우', '가수', '엔터'
    ]
    
    # 뉴스 언론사 키워드
    news_keywords = [
        'news', 'times', 'post', 'journal', 'herald', 'daily',
        '뉴스', '신문', '일보', '타임즈', '저널'
    ]
    
    # 점수 기반 분류
    scores = defaultdict(int)
    
    for keyword in crypto_keywords:
        if keyword in text:
            scores['크립토'] += 2
    
    for keyword in politics_keywords:
        if keyword in text:
            scores['정치'] += 2
    
    for keyword in economy_keywords:
        if keyword in text:
            scores['경제'] += 2
    
    for keyword in entertainment_keywords:
        if keyword in text:
            scores['연예'] += 2
    
    # 뉴스 언론사는 모든 카테고리에 약간씩 점수
    for keyword in news_keywords:
        if keyword in text:
            for cat in ['정치', '경제', '연예']:
                scores[cat] += 1
    
    # 가장 높은 점수의 카테고리 반환
    if scores:
        best_category = max(scores.items(), key=lambda x: x[1])
        if best_category[1] >= 2:  # 최소 점수 2 이상
            return best_category[0]
    
    return '기타'

def get_my_following_list():
    """내가 팔로우하는 계정 목록 가져오기"""
    print("🔍 X API로 팔로잉 목록 가져오는 중...\n")
    
    client = get_twitter_client()
    
    try:
        # 내 정보 가져오기
        me = client.get_me()
        my_id = me.data.id
        my_username = me.data.username
        
        print(f"✅ 로그인 성공: @{my_username}\n")
        
        # 팔로잉 목록 가져오기
        following = client.get_users_following(
            id=my_id,
            max_results=1000,
            user_fields=['username', 'name', 'description', 'public_metrics']
        )
        
        accounts = []
        
        if following.data:
            print(f"📊 총 {len(following.data)}개 계정 발견\n")
            
            for user in following.data:
                accounts.append({
                    'username': user.username,
                    'name': user.name,
                    'description': user.description,
                    'followers': user.public_metrics['followers_count']
                })
        else:
            print("⚠️  팔로잉 계정이 없거나 가져올 수 없습니다.")
        
        return accounts
    
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        print("\n💡 가능한 원인:")
        print("1. API 권한 부족 (Read 권한 필요)")
        print("2. Rate limit 초과")
        print("3. Access Token 만료")
        return []

def create_news_sources_file(accounts):
    """팔로잉 계정을 카테고리별로 분류하여 JSON 파일 생성"""
    print("🔄 계정 분류 중...\n")
    
    categorized = {
        '크립토': [],
        '정치': [],
        '경제': [],
        '연예': [],
        '기타': []
    }
    
    for account in accounts:
        category = categorize_account(
            account['username'],
            account['name'],
            account['description']
        )
        
        categorized[category].append({
            'username': f"@{account['username']}",
            'name': account['name'],
            'followers': account['followers']
        })
        
        print(f"  [{category:4s}] @{account['username']:20s} - {account['name'][:30]}")
    
    # 카테고리별 통계
    print("\n" + "="*60)
    print("📊 카테고리별 분류 결과:")
    print("="*60)
    for category, accts in categorized.items():
        print(f"  {category:6s}: {len(accts):3d}개")
    print("="*60 + "\n")
    
    # JSON 파일 생성
    news_sources = {
        "크립토": {
            "rss": [
                "https://www.coindeskkorea.com/rss",
                "https://www.tokenpost.kr/rss/index.xml",
                "https://www.blockmedia.co.kr/feed"
            ],
            "twitter_accounts": [acc['username'] for acc in categorized['크립토']],
            "telegram_channels": []
        },
        "정치": {
            "rss": [
                "https://www.chosun.com/arc/outboundfeeds/rss/politics/?outputType=xml",
                "https://rss.hankyung.com/politics.xml"
            ],
            "twitter_accounts": [acc['username'] for acc in categorized['정치']],
            "telegram_channels": []
        },
        "경제": {
            "rss": [
                "https://rss.hankyung.com/new/news.xml",
                "https://www.mk.co.kr/rss/30000001/",
                "https://www.sedaily.com/RSS/S01.xml"
            ],
            "twitter_accounts": [acc['username'] for acc in categorized['경제']],
            "telegram_channels": []
        },
        "연예": {
            "rss": [
                "https://www.mk.co.kr/rss/50200011/",
                "https://entertain.naver.com/now/rss"
            ],
            "twitter_accounts": [acc['username'] for acc in categorized['연예']],
            "telegram_channels": []
        },
        "기타": {
            "rss": [],
            "twitter_accounts": [acc['username'] for acc in categorized['기타']],
            "telegram_channels": []
        }
    }
    
    # JSON 파일로 저장
    with open('news_sources.json', 'w', encoding='utf-8') as f:
        json.dump(news_sources, f, ensure_ascii=False, indent=2)
    
    print("✅ news_sources.json 파일 생성 완료!\n")
    
    # 상세 정보 파일도 생성
    detailed_info = {
        category: [
            {
                'username': acc['username'],
                'name': acc['name'],
                'followers': acc['followers']
            }
            for acc in accounts
        ]
        for category, accounts in categorized.items()
    }
    
    with open('news_sources_detailed.json', 'w', encoding='utf-8') as f:
        json.dump(detailed_info, f, ensure_ascii=False, indent=2)
    
    print("✅ news_sources_detailed.json 파일 생성 완료! (팔로워 수 포함)\n")
    
    return news_sources

def main():
    """메인 실행"""
    print("="*60)
    print("  X 팔로잉 목록 → 뉴스 소스 자동 설정 스크립트")
    print("="*60 + "\n")
    
    # 1. 팔로잉 목록 가져오기
    accounts = get_my_following_list()
    
    if not accounts:
        print("❌ 계정을 가져올 수 없습니다. 종료합니다.")
        return
    
    # 2. 카테고리별 분류 및 JSON 생성
    news_sources = create_news_sources_file(accounts)
    
    print("\n" + "="*60)
    print("✨ 완료!")
    print("="*60)
    print("\n📝 다음 단계:")
    print("1. 'news_sources.json' 파일을 확인하세요")
    print("2. 잘못 분류된 계정이 있다면 수정하세요")
    print("3. 텔레그램 채널도 추가하고 싶다면 'telegram_channels'에 추가")
    print("4. GitHub에 업로드하세요")
    print("\n💡 팁:")
    print("- '기타' 카테고리는 필요 없으면 삭제해도 됩니다")
    print("- 팔로워 수는 'news_sources_detailed.json'에서 확인 가능")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
