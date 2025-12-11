"""경제/일간지 뉴스봇 메인 실행 파일"""
import sys
from rss_fetcher import fetch_single_feed
from telegram_sender import send_economy_news_to_telegram
from config import ECONOMY_RSS_FEEDS, DAILY_RSS_FEEDS


def fetch_headline_news(feeds: list, category: str) -> list:
    """각 신문사에서 최신 헤드라인 1개씩 수집"""
    news_list = []

    for feed_info in feeds:
        try:
            news_items = fetch_single_feed(feed_info["url"], feed_info["name"])
            if news_items:
                # 가장 최신 뉴스 1개만 선택
                latest = news_items[0]
                news_list.append(latest)
                print(f"✅ {feed_info['name']}: {latest['title'][:40]}...")
            else:
                print(f"⚠️ {feed_info['name']}: 뉴스 없음 (생략)")
        except Exception as e:
            print(f"❌ {feed_info['name']} 수집 실패: {e} (생략)")

    return news_list


def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("📰 경제/일간지 뉴스봇 시작")
    print("=" * 50)

    # Step 1: 경제 뉴스 수집
    print("\n📡 Step 1: 경제 뉴스 수집 중...")
    economy_news = fetch_headline_news(ECONOMY_RSS_FEEDS, "경제")
    print(f"   → 경제 뉴스 {len(economy_news)}개 수집")

    # Step 2: 일간지 뉴스 수집
    print("\n📡 Step 2: 일간지 뉴스 수집 중...")
    daily_news = fetch_headline_news(DAILY_RSS_FEEDS, "일간지")
    print(f"   → 일간지 뉴스 {len(daily_news)}개 수집")

    # 뉴스가 하나도 없으면 종료
    if not economy_news and not daily_news:
        print("\n❌ 수집된 뉴스가 없습니다.")
        sys.exit(1)

    # Step 3: 텔레그램으로 전송
    print("\n📱 Step 3: 텔레그램 전송 중...")
    success = send_economy_news_to_telegram(economy_news, daily_news)

    # 결과 출력
    print("\n" + "=" * 50)
    if success:
        print("✅ 경제/일간지 뉴스봇 실행 완료!")
    else:
        print("⚠️ 경제/일간지 뉴스봇 실행 완료 (텔레그램 전송 실패)")
    print("=" * 50)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
