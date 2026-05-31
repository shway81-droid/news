"""아침 브리핑 봇 메인 실행 파일

미국 증시(나스닥·S&P500) + 무안 일로읍 날씨 + 주요 뉴스 TOP 3 을
하나의 텔레그램 메시지로 묶어 매일 아침 전송한다.
"""
import sys

from stock_fetcher import fetch_indices
from weather_fetcher import fetch_weather
from rss_fetcher import fetch_all_feeds
from naver_news import fetch_top_news
from news_ranker import summarize_top_news
from telegram_sender import send_briefing_to_telegram


def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("☀️ 아침 브리핑 봇 시작")
    print("=" * 50)

    # Step 1: 미국 증시 지수
    print("\n📈 Step 1: 미국 증시 수집 중...")
    stocks = fetch_indices()

    # Step 2: 무안 일로읍 날씨
    print("\n🌤 Step 2: 날씨 수집 중...")
    weather = fetch_weather()

    # Step 3: 주요 뉴스 TOP 3 (네이버 일반뉴스 + RSS 후보 풀 → Groq 선별)
    print("\n📰 Step 3: 주요 뉴스 수집·요약 중...")
    naver_news = fetch_top_news()
    rss_news = fetch_all_feeds()
    news_pool = naver_news + rss_news
    top_news = summarize_top_news(news_pool, count=3) if news_pool else []

    # 모든 정보 수집 실패 시에만 종료
    if not stocks and not weather and not top_news:
        print("\n❌ 수집된 정보가 없습니다.")
        sys.exit(1)

    # Step 4: 텔레그램 전송
    print("\n📱 Step 4: 텔레그램 전송 중...")
    success = send_briefing_to_telegram(stocks, weather, top_news)

    print("\n" + "=" * 50)
    if success:
        print("✅ 아침 브리핑 전송 완료!")
    else:
        print("⚠️ 아침 브리핑 실행 완료 (텔레그램 전송 실패)")
    print("=" * 50)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
