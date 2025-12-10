"""텔레그램 메시지 전송 모듈"""
import requests
from datetime import datetime
from typing import List, Dict

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_news_to_telegram(news_list: List[Dict]) -> bool:
    """텔레그램으로 뉴스 전송"""

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 텔레그램 설정이 없습니다. (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
        print("\n--- 메시지 미리보기 ---")
        print(format_message(news_list))
        return False

    message = format_message(news_list)

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            print("✅ 텔레그램 전송 성공!")
            return True
        else:
            print(f"❌ 텔레그램 전송 실패: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ 텔레그램 전송 오류: {e}")
        return False


def format_message(news_list: List[Dict]) -> str:
    """뉴스 목록을 텔레그램 메시지 형식으로 변환"""

    # 현재 날짜
    now = datetime.now()
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    date_str = now.strftime(f"%Y-%m-%d ({weekdays[now.weekday()]}) %H:%M")

    # 헤더
    lines = [
        "🗞 <b>오늘의 테크 뉴스 TOP 10</b>",
        f"📅 {date_str}",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        ""
    ]

    # 숫자 이모지
    num_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    # 뉴스 항목
    for i, news in enumerate(news_list[:10]):
        emoji = num_emojis[i] if i < 10 else f"{i+1}."

        title = escape_html(news.get("title", ""))
        source = escape_html(news.get("source", ""))
        link = news.get("link", "")
        summary = escape_html(news.get("ai_summary", news.get("summary", ""))[:80])

        lines.append(f"{emoji} <b>[{source}]</b>")
        lines.append(f"<a href=\"{link}\">{title}</a>")

        if summary:
            lines.append(f"   → {summary}")

        lines.append("")

    # 푸터
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━",
        "🤖 Powered by Claude AI"
    ])

    return "\n".join(lines)


def escape_html(text: str) -> str:
    """HTML 특수문자 이스케이프"""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def send_test_message() -> bool:
    """테스트 메시지 전송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 텔레그램 설정이 없습니다.")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": "🔔 뉴스봇 테스트 메시지입니다!",
        }

        response = requests.post(url, json=payload, timeout=30)
        return response.status_code == 200

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


if __name__ == "__main__":
    # 테스트
    test_news = [
        {
            "title": "오픈AI, 새로운 모델 발표",
            "source": "AI타임스",
            "link": "https://example.com/1",
            "ai_summary": "GPT-5 출시로 AI 성능이 크게 향상됨"
        },
        {
            "title": "네이버, 하이퍼클로바X 업데이트",
            "source": "IT월드",
            "link": "https://example.com/2",
            "ai_summary": "한국어 성능 개선 및 새로운 기능 추가"
        },
    ]

    print("--- 메시지 미리보기 ---")
    print(format_message(test_news))
