"""설정 관리 모듈"""
import os

# 텔레그램 설정
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Groq API 설정 (무료)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# RSS 피드 목록
RSS_FEEDS = [
    # AI 뉴스 (국내)
    {"name": "AI타임스", "url": "https://www.aitimes.com/rss/allArticle.xml"},
    {"name": "IT월드", "url": "https://www.itworld.co.kr/rss"},
    # AI 뉴스 (해외)
    {"name": "OpenAI", "url": "https://openai.com/news/rss.xml"},
    {"name": "Google Blog", "url": "https://blog.google/feed/"},
    # 국내 테크 블로그
    {"name": "네이버 D2", "url": "https://d2.naver.com/d2.atom"},
    {"name": "토스", "url": "https://toss.tech/rss.xml"},
    {"name": "쿠팡 엔지니어링", "url": "https://medium.com/feed/coupang-engineering"},
    {"name": "데브시스터즈", "url": "https://tech.devsisters.com/rss.xml"},
    # 개발/기술 뉴스
    {"name": "GeekNews", "url": "https://news.hada.io/rss/news"},
    {"name": "요즘IT", "url": "https://yozm.wishket.com/magazine/feed/"},
    # 개인 블로그
    {"name": "JavaExpert", "url": "https://javaexpert.tistory.com/rss"},
]

# 뉴스 설정
NEWS_COUNT = 10  # 선별할 뉴스 개수
HOURS_LIMIT = 48  # 최근 N시간 내 뉴스만 수집
