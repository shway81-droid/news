"""뉴스봇 메인 실행 파일"""
import sys
from rss_fetcher import fetch_all_feeds
from news_ranker import rank_and_summarize_news
from telegram_sender import send_news_to_telegram


def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("🤖 테크 뉴스봇 시작")
    print("=" * 50)

    # Step 1: RSS 피드에서 뉴스 수집
    print("\n📡 Step 1: RSS 피드 수집 중...")
    all_news = fetch_all_feeds()

    if not all_news:
        print("❌ 수집된 뉴스가 없습니다.")
        sys.exit(1)

    # Step 2: Claude AI로 뉴스 선별 및 요약
    print("\n🤖 Step 2: AI가 뉴스를 분석 중...")
    ranked_news = rank_and_summarize_news(all_news)

    if not ranked_news:
        print("❌ 선별된 뉴스가 없습니다.")
        sys.exit(1)

    # Step 3: 텔레그램으로 전송
    print("\n📱 Step 3: 텔레그램 전송 중...")
    success = send_news_to_telegram(ranked_news)

    # 결과 출력
    print("\n" + "=" * 50)
    if success:
        print("✅ 뉴스봇 실행 완료!")
    else:
        print("⚠️ 뉴스봇 실행 완료 (텔레그램 전송 실패)")
    print("=" * 50)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
