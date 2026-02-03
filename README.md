# 🤖 X 자동 뉴스 봇

매일 자동으로 크립토, 정치, 경제, 연예 등 주요 뉴스를 X(트위터)에 포스팅하는 봇입니다.

## 🚀 설정 방법

### 1. GitHub Repository 생성
1. 새 GitHub 저장소를 만듭니다
2. 이 파일들을 업로드합니다:
   - `news_bot.py`
   - `requirements.txt`
   - `.github/workflows/daily_news.yml`

### 2. X API 키 설정
X Developer Portal에서 발급받은 API 키를 GitHub Secrets에 추가합니다.

**GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret**

다음 5개의 시크릿을 추가하세요:
- `BEARER_TOKEN`
- `API_KEY`
- `API_SECRET`
- `ACCESS_TOKEN`
- `ACCESS_TOKEN_SECRET`

### 3. GitHub Actions 활성화
1. 저장소의 **Actions** 탭으로 이동
2. "I understand my workflows, go ahead and enable them" 클릭
3. 워크플로우가 활성화됩니다

### 4. 실행 시간 설정 (선택사항)
`.github/workflows/daily_news.yml` 파일의 cron 설정을 수정하면 실행 시간을 변경할 수 있습니다.

```yaml
schedule:
  - cron: '0 0 * * *'  # 매일 UTC 0시 (한국시간 오전 9시)
```

#### 시간 변경 예시:
- 한국시간 오후 6시: `'0 9 * * *'` (UTC 9시)
- 한국시간 정오 12시: `'0 3 * * *'` (UTC 3시)

## 🧪 테스트 방법

1. **수동 실행으로 테스트**
   - GitHub 저장소 → Actions → Daily News Bot → Run workflow
   - "Run workflow" 버튼 클릭

2. **로컬에서 테스트**
```bash
# 환경변수 설정 (임시)
export BEARER_TOKEN="your_bearer_token"
export API_KEY="your_api_key"
export API_SECRET="your_api_secret"
export ACCESS_TOKEN="your_access_token"
export ACCESS_TOKEN_SECRET="your_access_token_secret"

# 실행
python news_bot.py
```

## 📝 커스터마이징

### 뉴스 소스 변경
`news_bot.py`의 `NEWS_FEEDS` 딕셔너리에서 RSS 피드 URL을 수정하세요.

```python
NEWS_FEEDS = {
    '크립토': [
        'https://www.coindeskkorea.com/rss',
        # 다른 크립토 뉴스 RSS 추가 가능
    ],
    # 카테고리 추가/삭제 가능
}
```

### 트윗 포맷 변경
`create_daily_summary()` 함수에서 트윗 텍스트를 수정하세요.

### 카테고리별 뉴스 개수 조정
`fetch_news()` 함수의 `max_items` 파라미터를 조정하세요.

## 🔍 문제 해결

### Actions 로그 확인
- GitHub 저장소 → Actions → 실패한 워크플로우 클릭
- 에러 메시지 확인

### 일반적인 문제
1. **API 키 오류**: Secrets가 정확히 입력되었는지 확인
2. **트윗이 안 올라감**: X API 권한 확인 (Read and Write 필요)
3. **중복 트윗 오류**: X는 동일한 내용의 트윗을 연속으로 올릴 수 없습니다

## 📌 주의사항

- X API Essential tier는 월 50,000 트윗 제한이 있습니다
- RSS 피드가 항상 작동하는지 주기적으로 확인하세요
- 뉴스 저작권을 존중하여 헤드라인만 공유합니다

## 🛠️ 기술 스택

- Python 3.10
- Tweepy (X API 라이브러리)
- Feedparser (RSS 파싱)
- GitHub Actions (자동화)

## 📄 라이선스

MIT License
