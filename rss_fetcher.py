"""RSS 피드 수집 모듈"""
import feedparser
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser
from typing import List, Dict
import requests

from config import RSS_FEEDS, HOURS_LIMIT


def fetch_all_feeds() -> List[Dict]:
    """모든 RSS 피드에서 뉴스 수집"""
    all_news = []

    for feed_info in RSS_FEEDS:
        try:
            news_items = fetch_single_feed(feed_info["url"], feed_info["name"])
            all_news.extend(news_items)
            print(f"✅ {feed_info['name']}: {len(news_items)}개 수집")
        except Exception as e:
            print(f"❌ {feed_info['name']} 수집 실패: {e}")

    # 중복 제거 (제목 기준)
    seen_titles = set()
    unique_news = []
    for news in all_news:
        if news["title"] not in seen_titles:
            seen_titles.add(news["title"])
            unique_news.append(news)

    # 최신순 정렬
    unique_news.sort(key=lambda x: x["published"], reverse=True)

    print(f"\n📰 총 {len(unique_news)}개 뉴스 수집 완료")
    return unique_news


def fetch_single_feed(url: str, source_name: str) -> List[Dict]:
    """단일 RSS 피드에서 뉴스 수집"""
    news_items = []

    # User-Agent 설정
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        feed = feedparser.parse(response.content)
    except:
        feed = feedparser.parse(url)

    if not feed.entries:
        return []

    # 시간 기준 설정 (최근 N시간)
    now = datetime.now(timezone.utc)
    time_limit = now - timedelta(hours=HOURS_LIMIT)

    for entry in feed.entries:
        try:
            # 발행일 파싱
            published = parse_date(entry)

            # 시간 필터링 (최근 N시간 내)
            if published and published < time_limit:
                continue

            # 제목 정리 (CDATA 제거)
            title = clean_title(entry.get("title", ""))
            if not title:
                continue

            news_item = {
                "title": title,
                "link": entry.get("link", ""),
                "source": source_name,
                "published": published or now,
                "summary": clean_title(entry.get("summary", entry.get("description", ""))[:200])
            }
            news_items.append(news_item)

        except Exception as e:
            continue

    return news_items


def parse_date(entry) -> datetime:
    """RSS 엔트리에서 날짜 파싱"""
    date_fields = ["published", "updated", "pubDate", "date"]

    for field in date_fields:
        if hasattr(entry, field) and getattr(entry, field):
            try:
                parsed = date_parser.parse(getattr(entry, field))
                # timezone이 없으면 UTC로 설정
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed
            except:
                continue

    # published_parsed 사용
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except:
            pass

    return datetime.now(timezone.utc)


def clean_title(text: str) -> str:
    """제목 정리 (CDATA, HTML 태그 제거)"""
    if not text:
        return ""

    # CDATA 제거
    text = text.replace("<![CDATA[", "").replace("]]>", "")

    # HTML 태그 제거
    import re
    text = re.sub(r"<[^>]+>", "", text)

    # 공백 정리
    text = " ".join(text.split())

    return text.strip()


if __name__ == "__main__":
    # 테스트 실행
    news = fetch_all_feeds()
    print("\n--- 최근 뉴스 5개 ---")
    for i, item in enumerate(news[:5], 1):
        print(f"{i}. [{item['source']}] {item['title']}")
