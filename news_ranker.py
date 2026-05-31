"""Groq AI로 뉴스 선별 및 요약 모듈 (무료)"""
import requests
from typing import List, Dict

from config import GROQ_API_KEY, NEWS_COUNT


def rank_and_summarize_news(news_list: List[Dict]) -> List[Dict]:
    """Groq API로 뉴스 중요도 평가 및 요약"""

    if not news_list:
        print("⚠️ 분석할 뉴스가 없습니다.")
        return []

    # 1단계: 각 출처에서 최소 1개씩 우선 선택 (균형 보장)
    guaranteed_news = select_one_per_source(news_list)
    print(f"📌 {len(guaranteed_news)}개 출처에서 각 1개씩 선택")

    # 2단계: 10개 미만이면 AI타임스에서 추가 선별
    remaining_slots = NEWS_COUNT - len(guaranteed_news)

    if remaining_slots > 0:
        # AI타임스 뉴스 중 이미 선택된 것 제외
        guaranteed_links = {n["link"] for n in guaranteed_news}
        aitimes_news = [n for n in news_list if n["source"] == "AI타임스" and n["link"] not in guaranteed_links]

        # AI타임스에서 부족한 만큼 추가
        additional = aitimes_news[:remaining_slots]
        guaranteed_news.extend(additional)
        if additional:
            print(f"📌 AI타임스에서 {len(additional)}개 추가 선택")

    # 3단계: AI로 요약 추가
    if GROQ_API_KEY:
        final_news = add_ai_summaries(guaranteed_news)
    else:
        print("⚠️ GROQ_API_KEY가 설정되지 않았습니다.")
        final_news = add_default_summaries(guaranteed_news)

    return final_news[:NEWS_COUNT]


def summarize_top_news(news_list: List[Dict], count: int = 3) -> List[Dict]:
    """브리핑용: 가장 중요한 뉴스 count개를 선별하고 한줄 요약 (Groq)"""
    if not news_list:
        return []

    # Groq 키가 없으면 최신순 count개로 폴백
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY 없음 — 최신순으로 대체")
        return [{**n, "ai_summary": n.get("summary", "")[:60]} for n in news_list[:count]]

    news_text = format_news_for_ai(news_list)
    prompt = f"""아래 뉴스 목록에서 오늘 가장 중요한 뉴스 {count}개를 선별하고 한줄 요약을 작성하세요.

## 뉴스 목록
{news_text}

## 응답 형식 (정확히 {count}개)
번호|출처|제목|한줄요약

예시:
1|AI타임스|오픈AI 새 모델 발표|GPT-5 출시로 성능 대폭 향상

중요: 반드시 위 형식(|로 구분)만 출력하고, 한줄요약은 30자 내외로 작성하세요."""

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.3,
        }
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60,
        )
        if response.status_code != 200:
            print(f"❌ Groq API 오류: {response.status_code}")
            return [{**n, "ai_summary": n.get("summary", "")[:60]} for n in news_list[:count]]

        response_text = response.json()["choices"][0]["message"]["content"]

        top = []
        seen_links = set()
        for line in response_text.strip().split("\n"):
            line = line.strip()
            if "|" not in line:
                continue
            parts = line.split("|")
            if len(parts) < 4:
                continue
            source, title, summary = parts[1].strip(), parts[2].strip(), parts[3].strip()
            matched = find_matching_news(title, source, news_list)
            if matched and matched.get("link") not in seen_links:
                seen_links.add(matched.get("link"))
                top.append({**matched, "ai_summary": summary})
            if len(top) >= count:
                break

        # 부족하면 최신순으로 채우기
        for news in news_list:
            if len(top) >= count:
                break
            if news.get("link") not in seen_links:
                seen_links.add(news.get("link"))
                top.append({**news, "ai_summary": news.get("summary", "")[:60]})

        print(f"🤖 주요뉴스 {len(top)}개 선별 완료")
        return top[:count]

    except Exception as e:
        print(f"❌ 주요뉴스 요약 실패: {e}")
        return [{**n, "ai_summary": n.get("summary", "")[:60]} for n in news_list[:count]]


def select_one_per_source(news_list: List[Dict]) -> List[Dict]:
    """각 출처에서 가장 최신 글 1개씩 선택"""
    selected = {}
    for news in news_list:
        source = news["source"]
        if source not in selected:
            selected[source] = news
    return list(selected.values())


def select_with_ai(news_list: List[Dict], count: int) -> List[Dict]:
    """AI로 추가 뉴스 선별"""
    if not news_list or count <= 0:
        return []

    news_text = format_news_for_ai(news_list)

    prompt = f"""당신은 바이브 코딩과 개발 트렌드 전문 뉴스 큐레이터입니다.
아래 뉴스 목록에서 개발자에게 가장 중요한 뉴스 {count}개를 선별해주세요.

## 선별 기준 (우선순위 순)
1. **바이브 코딩 관련** (AI 코딩, Cursor, Claude Code, Copilot, 코드 생성 등)
2. **개발 도구/기술** (프레임워크, 라이브러리, IDE, DevOps 등)
3. **AI/LLM 기술 발전** (새로운 모델, API, 성능 개선 등)
4. **테크 기업 개발 문화** (기술 블로그, 아키텍처, 개발 경험 등)

일반적인 AI 산업 뉴스보다 **실제 개발에 도움되는 기술 뉴스**를 우선하세요.

## 뉴스 목록
{news_text}

## 응답 형식
각 뉴스에 대해 아래 형식으로 정확히 {count}개를 응답해주세요:

번호|출처|제목|한줄요약

예시:
1|AI타임스|오픈AI, 새로운 모델 발표|GPT-5 출시로 AI 성능 대폭 향상
2|네이버 D2|React 19 정식 출시|새로운 훅과 서버 컴포넌트 지원

중요: 반드시 위 형식(|로 구분)을 지켜주세요. 다른 설명 없이 {count}개 뉴스만 출력하세요."""

    try:
        # Groq API 호출
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.3
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code != 200:
            print(f"❌ Groq API 오류: {response.status_code}")
            print(response.text)
            return add_default_summaries(news_list[:NEWS_COUNT])

        result = response.json()
        response_text = result["choices"][0]["message"]["content"]
        ranked_news = parse_ai_response(response_text, news_list)

        print(f"🤖 Groq AI가 {len(ranked_news)}개 뉴스를 선별했습니다.")
        return ranked_news

    except Exception as e:
        print(f"❌ Groq API 오류: {e}")
        print("⚠️ 최신순으로 반환합니다.")
        return add_default_summaries(news_list[:NEWS_COUNT])


def format_news_for_ai(news_list: List[Dict]) -> str:
    """뉴스 목록을 AI 분석용 텍스트로 변환"""
    lines = []
    for i, news in enumerate(news_list[:50], 1):  # 최대 50개만 전송
        lines.append(f"{i}. [{news['source']}] {news['title']}")
    return "\n".join(lines)


def parse_ai_response(response: str, original_news: List[Dict]) -> List[Dict]:
    """AI 응답 파싱"""
    ranked_news = []
    lines = response.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or "|" not in line:
            continue

        parts = line.split("|")
        if len(parts) < 4:
            continue

        try:
            source = parts[1].strip()
            title = parts[2].strip()
            summary = parts[3].strip()

            # 원본 뉴스에서 찾기
            matched_news = find_matching_news(title, source, original_news)

            if matched_news:
                ranked_news.append({
                    **matched_news,
                    "ai_summary": summary
                })
        except:
            continue

    # 부족하면 원본에서 채우기
    if len(ranked_news) < NEWS_COUNT:
        existing_links = {n.get("link") for n in ranked_news}
        for news in original_news:
            if len(ranked_news) >= NEWS_COUNT:
                break
            if news.get("link") not in existing_links:
                ranked_news.append({
                    **news,
                    "ai_summary": news.get("summary", "")[:50]
                })

    return ranked_news[:NEWS_COUNT]


def find_matching_news(title: str, source: str, news_list: List[Dict]) -> Dict:
    """제목과 출처로 원본 뉴스 찾기"""
    # 정확한 매칭
    for news in news_list:
        if news["title"] == title or title in news["title"] or news["title"] in title:
            return news

    # 출처 + 부분 매칭
    for news in news_list:
        if news["source"] == source and (
            title[:20] in news["title"] or news["title"][:20] in title
        ):
            return news

    return None


def add_default_summaries(news_list: List[Dict]) -> List[Dict]:
    """기본 요약 추가 (AI 실패 시)"""
    result = []
    for news in news_list:
        result.append({
            **news,
            "ai_summary": news.get("summary", "")[:50] + "..."
        })
    return result


def add_ai_summaries(news_list: List[Dict]) -> List[Dict]:
    """AI로 뉴스 요약 추가"""
    if not news_list:
        return []

    # 이미 요약이 있는 뉴스는 그대로
    needs_summary = [n for n in news_list if not n.get("ai_summary")]

    if not needs_summary or not GROQ_API_KEY:
        return add_default_summaries(news_list)

    # AI에게 요약 요청
    news_text = "\n".join([f"{i+1}. [{n['source']}] {n['title']}" for i, n in enumerate(needs_summary)])

    prompt = f"""아래 뉴스들의 한줄 요약을 작성해주세요.

## 뉴스 목록
{news_text}

## 응답 형식
번호|한줄요약

예시:
1|GPT-5 출시로 AI 성능 대폭 향상
2|새로운 훅과 서버 컴포넌트 지원

한줄 요약은 20자 내외로 핵심만 작성하세요."""

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.3
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            response_text = result["choices"][0]["message"]["content"]

            # 요약 파싱
            summaries = {}
            for line in response_text.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        try:
                            idx = int(parts[0].strip()) - 1
                            summaries[idx] = parts[1].strip()
                        except:
                            continue

            # 요약 적용
            for i, news in enumerate(needs_summary):
                news["ai_summary"] = summaries.get(i, news.get("summary", "")[:50])

        return news_list

    except Exception as e:
        print(f"⚠️ 요약 생성 실패: {e}")
        return add_default_summaries(news_list)


if __name__ == "__main__":
    # 테스트
    test_news = [
        {"title": "테스트 뉴스 1", "source": "테스트", "link": "http://test1.com", "summary": "요약1"},
        {"title": "테스트 뉴스 2", "source": "테스트", "link": "http://test2.com", "summary": "요약2"},
    ]
    print("테스트 실행...")
    result = rank_and_summarize_news(test_news)
    for r in result:
        print(r)
