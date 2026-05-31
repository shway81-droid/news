"""날씨 수집 모듈 (무안군 일로읍)

데이터 소스: wttr.in JSON (API 키 불필요).
"""
from typing import Dict, Optional

import requests

# 무안군 일로읍 대략 좌표 (위도, 경도)
LAT, LON = 34.92, 126.43
LOCATION_NAME = "무안 일로읍"

HEADERS = {"User-Agent": "curl/8.0"}  # wttr.in 은 브라우저 UA 에 HTML 을 줌


def fetch_weather() -> Optional[Dict]:
    """현재 날씨 + 오늘 최저/최고/강수확률 수집"""
    url = f"https://wttr.in/{LAT},{LON}?format=j1&lang=ko"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        cur = data["current_condition"][0]
        today = data["weather"][0]

        # 한글 날씨 설명 (lang=ko) 우선, 없으면 영문
        desc = cur.get("lang_ko", [{}])[0].get("value") or cur["weatherDesc"][0]["value"]

        # 오늘 시간대별 강수확률 최대값
        rain_chance = max(
            (int(h.get("chanceofrain", 0)) for h in today.get("hourly", [])),
            default=0,
        )

        weather = {
            "location": LOCATION_NAME,
            "desc": desc,
            "temp": cur["temp_C"],
            "feels": cur["FeelsLikeC"],
            "min": today["mintempC"],
            "max": today["maxtempC"],
            "humidity": cur["humidity"],
            "rain_chance": rain_chance,
        }
        print(f"✅ 날씨: {desc} {weather['temp']}℃ (체감 {weather['feels']}℃), "
              f"{weather['min']}~{weather['max']}℃, 강수 {rain_chance}%")
        return weather
    except Exception as e:
        print(f"❌ 날씨 수집 실패: {e}")
        return None


if __name__ == "__main__":
    print(fetch_weather())
