"""일간지 뉴스봇 메인 실행 파일 (네이버 뉴스 헤드라인)"""
import sys
from naver_crawler import fetch_daily_headlines
from telegram_sender import send_daily_only_to_telegram


def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("📋 일간지 뉴스봇 시작 (네이버 헤드라인)")
    print("=" * 50)

    # Step 1: 네이버 뉴스에서 일간지 헤드라인 수집
    print("\n📡 Step 1: 일간지 뉴스 헤드라인 수집 중...")
    daily_news = fetch_daily_headlines()

    print(f"   → 일간지 뉴스 {len(daily_news)}/10개 수집")

    # 뉴스가 하나도 없으면 종료
    if not daily_news:
        print("\n❌ 수집된 뉴스가 없습니다.")
        sys.exit(1)

    # Step 2: 텔레그램으로 전송
    print("\n📱 Step 2: 텔레그램 전송 중...")
    success = send_daily_only_to_telegram(daily_news)

    # 결과 출력
    print("\n" + "=" * 50)
    if success:
        print("✅ 일간지 뉴스봇 실행 완료!")
    else:
        print("⚠️ 일간지 뉴스봇 실행 완료 (텔레그램 전송 실패)")
    print("=" * 50)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
