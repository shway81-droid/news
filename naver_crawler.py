"""네이버 뉴스 헤드라인 크롤러"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple


# 네이버 언론사 코드 매핑
PRESS_CODES = {
    # 경제 신문 (10개)
    '015': '한국경제',
    '009': '매일경제',
    '011': '서울경제',
    '008': '머니투데이',
    '014': '파이낸셜뉴스',
    '018': '이데일리',
    '243': '아주경제',
    '648': '비즈니스워치',
    '366': '조선비즈',
    '024': '매경이코노미',
    # 주요 일간지 (10개)
    '023': '조선일보',
    '025': '중앙일보',
    '020': '동아일보',
    '028': '한겨레',
    '032': '경향신문',
    '005': '국민일보',
    '022': '세계일보',
    '047': '오마이뉴스',
    '081': '서울신문',
    '469': '한국일보',
}

# 수집 대상 언론사 코드
TARGET_ECONOMY = ['015', '009', '011', '008', '014', '018', '243', '648', '366', '024']  # 경제지 10개
TARGET_DAILY = ['023', '025', '020', '028', '032', '005', '022', '047', '081', '469']    # 일간지 10개


def fetch_press_headline(press_code: str) -> Dict:
    """특정 언론사의 헤드라인 기사 1개 수집

    Args:
        press_code: 네이버 언론사 코드

    Returns:
        뉴스 정보 딕셔너리 또는 빈 딕셔너리
    """
    url = f'https://media.naver.com/press/{press_code}/newspaper'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"  ⚠️ {PRESS_CODES.get(press_code, press_code)} 접속 실패: {e}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')

    # 첫 번째 기사 링크 찾기
    article_links = soup.select('a[href*="/article/"]')
    if not article_links:
        print(f"  ⚠️ {PRESS_CODES.get(press_code, press_code)} 기사 없음")
        return {}

    first_article = article_links[0]
    title = first_article.get_text(strip=True)
    link = first_article.get('href', '')

    return {
        'title': title,
        'source': PRESS_CODES.get(press_code, f'언론사({press_code})'),
        'link': link,
        'press_code': press_code
    }


def fetch_naver_headlines() -> Tuple[List[Dict], List[Dict]]:
    """네이버 뉴스에서 언론사별 헤드라인 수집

    Returns:
        (경제 뉴스 리스트, 일간지 뉴스 리스트)
    """
    economy_news = fetch_economy_headlines()
    daily_news = fetch_daily_headlines()
    return economy_news, daily_news


def fetch_economy_headlines() -> List[Dict]:
    """경제 신문 헤드라인만 수집"""
    economy_news = []
    print("  💰 경제 신문 수집 중...")
    for press_code in TARGET_ECONOMY:
        news = fetch_press_headline(press_code)
        if news:
            economy_news.append(news)
            print(f"    ✅ {news['source']}: {news['title'][:40]}...")
    return economy_news


def fetch_daily_headlines() -> List[Dict]:
    """일간지 헤드라인만 수집"""
    daily_news = []
    print("  📰 주요 일간지 수집 중...")
    for press_code in TARGET_DAILY:
        news = fetch_press_headline(press_code)
        if news:
            daily_news.append(news)
            print(f"    ✅ {news['source']}: {news['title'][:40]}...")
    return daily_news


if __name__ == "__main__":
    # 테스트 실행
    print("=== 네이버 뉴스 헤드라인 크롤링 테스트 ===\n")

    economy, daily = fetch_naver_headlines()

    print(f"\n💰 경제 신문: {len(economy)}/10개 수집")
    for news in economy:
        print(f"  - {news['source']}: {news['link']}")

    print(f"\n📰 주요 일간지: {len(daily)}/10개 수집")
    for news in daily:
        print(f"  - {news['source']}: {news['link']}")
