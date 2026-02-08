# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

텔레그램 뉴스봇 - RSS 피드와 네이버 뉴스에서 뉴스를 수집하여 Groq AI로 선별/요약 후 텔레그램으로 전송하는 자동화 시스템

## 실행 명령어

```bash
# 의존성 설치
pip install -r requirements.txt

# 테크 뉴스봇 실행 (RSS 피드 + AI 선별)
python main.py

# 경제 뉴스봇 실행 (네이버 경제지 10개 크롤링)
python main_economy.py

# 일간지 뉴스봇 실행 (네이버 일간지 10개 크롤링)
python main_daily.py

# 개별 모듈 테스트
python rss_fetcher.py      # RSS 수집 테스트
python naver_crawler.py    # 네이버 크롤링 테스트
python telegram_sender.py  # 텔레그램 메시지 포맷 테스트
```

## 환경 변수

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export GROQ_API_KEY="your_groq_api_key"  # 무료 API
```

## 아키텍처

세 개의 독립적인 뉴스봇:

### 1. 테크 뉴스봇 (`main.py`)
```
RSS 피드 → rss_fetcher.py → news_ranker.py (Groq AI) → telegram_sender.py
```
- 여러 RSS 피드에서 뉴스 수집 (최근 48시간 내, `config.HOURS_LIMIT`)
- Groq AI(`llama-3.3-70b-versatile`)로 중요도 평가 및 요약
- 출처별 1개씩 선택 후 AI타임스에서 추가 채움 (총 10개, `config.NEWS_COUNT`)

### 2. 경제 뉴스봇 (`main_economy.py`)
```
네이버 뉴스 → naver_crawler.py → telegram_sender.py
```
- 네이버 경제지 페이지에서 헤드라인 크롤링
- 경제지 10개 각각 최신 기사 1개씩 수집

### 3. 일간지 뉴스봇 (`main_daily.py`)
```
네이버 뉴스 → naver_crawler.py → telegram_sender.py
```
- 네이버 일간지 페이지에서 헤드라인 크롤링
- 주요 일간지 10개 각각 최신 기사 1개씩 수집

## 주요 모듈

| 파일 | 역할 |
|------|------|
| `config.py` | RSS 피드 목록, 환경변수, 설정값 (`NEWS_COUNT`, `HOURS_LIMIT`) |
| `rss_fetcher.py` | RSS 파싱 및 시간 필터링 (`fetch_all_feeds()`) |
| `naver_crawler.py` | 네이버 언론사별 헤드라인 크롤링 (`fetch_economy_headlines()`, `fetch_daily_headlines()`) |
| `news_ranker.py` | Groq API로 뉴스 선별/요약 (`rank_and_summarize_news()`) |
| `telegram_sender.py` | 텔레그램 메시지 포맷팅 및 전송 (`send_news_to_telegram()`, `send_economy_only_to_telegram()`, `send_daily_only_to_telegram()`) |

## RSS 피드 추가 방법

`config.py`의 `RSS_FEEDS` 배열에 추가:
```python
{"name": "피드명", "url": "RSS URL"}
```

## 네이버 언론사 추가 방법

`naver_crawler.py`에서:
1. `PRESS_CODES` 딕셔너리에 언론사 코드 매핑 추가 (코드는 네이버 미디어 URL에서 확인)
2. `TARGET_ECONOMY` 또는 `TARGET_DAILY` 리스트에 코드 추가

네이버 언론사 URL 형식: `https://media.naver.com/press/{언론사코드}/newspaper`
