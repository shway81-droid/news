"""네이버 뉴스 검색 모듈 (k-skill 프록시 경유)

네이버 검색 Open API 뉴스 검색을 프록시로 호출한다. 별도 API 키 불필요.
아침 브리핑의 '주요뉴스' 후보 풀을 최신 일반 뉴스로 보강하는 용도.
"""
from datetime import datetime, timezone
from typing import List, Dict

import requests

from config import KSKILL_PROXY_BASE_URL, NAVER_NEWS_QUERIES


def fetch_top_news(queries: List[str] = None, per_query: int = 5) -> List[Dict]:
    """검색어별 최신 뉴스를 모아 중복 제거 후 반환 (rss_fetcher 와 같은 dict 형식)"""
    queries = queries or NAVER_NEWS_QUERIES
    results: List[Dict] = []
    seen_titles = set()

    for q in queries:
        for item in _search(q, display=per_query, sort="date"):
            title = item.get("title", "")
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            results.append({
                "title": title,
                "link": item.get("original_link") or item.get("link", ""),
                "source": "네이버뉴스",
                "summary": (item.get("description", "") or "")[:200],
                "published": _parse_iso(item.get("pub_date_iso")),
            })

    print(f"✅ 네이버 뉴스 {len(results)}건 수집 ({', '.join(queries)})")
    return results


def _search(query: str, display: int = 5, sort: str = "date") -> List[Dict]:
    """프록시의 네이버 뉴스 검색 엔드포인트 호출"""
    base = (KSKILL_PROXY_BASE_URL or "").rstrip("/")
    if not base or len(query) < 2:
        return []
    url = f"{base}/v1/naver-news/search"
    try:
        resp = requests.get(
            url,
            params={"q": query, "display": display, "sort": sort},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
    except Exception as e:
        print(f"⚠️ 네이버 뉴스 검색 실패 ('{query}'): {e}")
        return []


def _parse_iso(iso: str) -> datetime:
    """pub_date_iso → datetime (실패 시 현재 시각)"""
    if iso:
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


if __name__ == "__main__":
    for n in fetch_top_news():
        print(f"- [{n['source']}] {n['title']}")
