"""네이버 뉴스 헤드라인 크롤러"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple


# 네이버 언론사 코드 매핑
PRESS_CODES = {
    # 경제 신문
    '015': '한국경제',
    '009': '매일경제',
    '011': '서울경제',
    '008': '머니투데이',
    '014': '파이낸셜뉴스',
    # 주요 일간지
    '023': '조선일보',
    '025': '중앙일보',
    '020': '동아일보',
    '028': '한겨레',
    '032': '경향신문',
    # 기타 참고용
    '001': '연합뉴스',
    '030': '전자신문',
    '081': '서울신문',
    '088': '매일신문',
    '005': '국민일보',
}

# 수집 대상 언론사 코드
TARGET_ECONOMY = ['015', '009', '011', '008', '014']  # 한경, 매경, 서울경제, 머니투데이, 파이낸셜
TARGET_DAILY = ['023', '025', '020', '028', '032']    # 조중동, 한겨레, 경향


def fetch_naver_headlines() -> Tuple[List[Dict], List[Dict]]:
    """네이버 뉴스 메인에서 언론사별 헤드라인 수집

    Returns:
        (경제 뉴스 리스트, 일간지 뉴스 리스트)
    """
    url = 'https://news.naver.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ 네이버 뉴스 접속 실패: {e}")
        return [], []

    soup = BeautifulSoup(response.text, 'html.parser')
    headlines = soup.select('a[class*="headline"]')

    # 언론사별 첫 기사 수집 (중복 방지)
    economy_news = {}
    daily_news = {}

    for item in headlines:
        title = item.get_text(strip=True).replace('신문보기', '').strip()
        href = item.get('href', '')

        # URL에서 언론사 코드 추출
        if 'press/' not in href:
            continue

        press_code = href.split('press/')[1].split('/')[0]
        press_name = PRESS_CODES.get(press_code, f'언론사({press_code})')

        news_item = {
            'title': title,
            'source': press_name,
            'link': href,
            'press_code': press_code
        }

        # 경제 신문 (아직 수집 안 된 언론사만)
        if press_code in TARGET_ECONOMY and press_code not in economy_news:
            economy_news[press_code] = news_item

        # 일간지 (아직 수집 안 된 언론사만)
        if press_code in TARGET_DAILY and press_code not in daily_news:
            daily_news[press_code] = news_item

    # dict를 list로 변환
    economy_list = list(economy_news.values())
    daily_list = list(daily_news.values())

    return economy_list, daily_list


if __name__ == "__main__":
    # 테스트 실행
    print("=== 네이버 뉴스 헤드라인 크롤링 테스트 ===\n")

    economy, daily = fetch_naver_headlines()

    print("💰 경제 신문 헤드라인:")
    for news in economy:
        print(f"  ✅ {news['source']}: {news['title'][:50]}...")
    print(f"  → {len(economy)}/5개 수집\n")

    print("📰 주요 일간지 헤드라인:")
    for news in daily:
        print(f"  ✅ {news['source']}: {news['title'][:50]}...")
    print(f"  → {len(daily)}/5개 수집")
