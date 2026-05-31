"""날씨 수집 모듈 (무안군 일로읍)

1순위: 기상청 단기예보 (k-skill 프록시 경유, 국내 최정확, API 키 불필요)
폴백:  wttr.in (프록시 장애 시)
둘 다 API 키 불필요.
"""
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta

import requests

from config import KSKILL_PROXY_BASE_URL

# 무안군 일로읍 대략 좌표 (위도, 경도)
LAT, LON = 34.92, 126.43
LOCATION_NAME = "무안 일로읍"

KST = timezone(timedelta(hours=9))

HEADERS = {"User-Agent": "curl/8.0"}  # wttr.in 은 브라우저 UA 에 HTML 을 줌

# 기상청 코드 → 한글
SKY_DESC = {"1": "맑음", "3": "구름많음", "4": "흐림"}
PTY_DESC = {"1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}

# 오전/오후 시간대 (시작시, 끝시, 대표시)
AM_WINDOW = (6, 11, 9)
PM_WINDOW = (12, 18, 15)


def fetch_weather() -> Optional[Dict]:
    """현재 날씨 + 오늘 최저/최고/강수확률 + 오전·오후 요약 (기상청 우선, wttr.in 폴백)"""
    return _from_kma() or _from_wttr()


def _from_kma() -> Optional[Dict]:
    """기상청 단기예보 (k-skill 프록시). 격자 변환은 프록시가 처리."""
    base = (KSKILL_PROXY_BASE_URL or "").rstrip("/")
    if not base:
        return None
    url = f"{base}/v1/korea-weather/forecast"
    base_date, base_time = _kma_base_kst()
    try:
        resp = requests.get(
            url,
            params={"lat": LAT, "lon": LON, "baseDate": base_date, "baseTime": base_time},
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json()["response"]["body"]["items"]["item"]
        if not items:
            return None

        items.sort(key=lambda x: (x["fcstDate"], x["fcstTime"]))
        today = items[0]["fcstDate"]

        near = {}        # 가장 이른 예보 시각의 카테고리별 값
        pop_today = 0
        tmn = tmx = None
        tmps_today = []
        hourly = {}      # hour -> {"sky","pty","pop"}
        for it in items:
            cat, val = it["category"], it["fcstValue"]
            near.setdefault(cat, val)
            if it["fcstDate"] != today:
                continue
            hour = int(it["fcstTime"]) // 100
            slot = hourly.setdefault(hour, {})
            if cat == "POP":
                slot["pop"] = _to_int(val)
                pop_today = max(pop_today, _to_int(val))
            elif cat in ("SKY", "PTY"):
                slot[cat.lower()] = val
            elif cat == "TMN":
                tmn = val
            elif cat == "TMX":
                tmx = val
            elif cat == "TMP":
                tmps_today.append(val)

        # hour -> {"desc","pop"}
        hourly_desc = {
            h: {
                "desc": PTY_DESC.get(s.get("pty", "0")) or SKY_DESC.get(s.get("sky", ""), ""),
                "pop": s.get("pop", 0),
            }
            for h, s in hourly.items()
        }

        temp = near.get("TMP", "")
        pty, sky = near.get("PTY", "0"), near.get("SKY", "")
        weather = {
            "location": LOCATION_NAME,
            "desc": PTY_DESC.get(pty) or SKY_DESC.get(sky, "정보없음"),
            "temp": temp,
            "feels": "",  # 기상청 단기예보는 체감온도 미제공
            "min": _clean_num(tmn) or _min_of(tmps_today) or temp,
            "max": _clean_num(tmx) or _max_of(tmps_today) or temp,
            "humidity": near.get("REH", ""),
            "rain_chance": pop_today,
            "am": _period_summary(hourly_desc, *AM_WINDOW),
            "pm": _period_summary(hourly_desc, *PM_WINDOW),
        }
        print(f"✅ 날씨(기상청 {base_date} {base_time}): {weather['desc']} {temp}℃, "
              f"{weather['min']}~{weather['max']}℃, 강수 {pop_today}%, "
              f"오전={weather['am']}, 오후={weather['pm']}")
        return weather
    except Exception as e:
        print(f"⚠️ 기상청 날씨 실패, wttr.in 폴백: {e}")
        return None


def _kma_base_kst() -> tuple:
    """오늘 하루 전체 예보가 포함되도록 '오늘 아침 발표분'을 고정 사용.

    기상청 단기예보는 발표시각 이후 시간대만 제공하므로, '최신 발표분'을 쓰면
    낮/저녁에 실행할 때 오늘 오전·오후가 누락된다. 실행 시각과 무관하게 오늘의
    아침 발표분(0500)을 고정해 오늘 0600~ 전체(오전·오후·최저/최고)를 받는다.
    """
    ref = datetime.now(KST)
    hm = ref.hour * 100 + ref.minute
    if hm >= 510:   # 05:10 이후 → 오늘 0500 발표분
        return ref.strftime("%Y%m%d"), "0500"
    if hm >= 210:   # 02:10~05:10 → 오늘 0200 발표분
        return ref.strftime("%Y%m%d"), "0200"
    prev = ref - timedelta(days=1)   # 02:10 이전 → 전날 2300 발표분
    return prev.strftime("%Y%m%d"), "2300"


def _from_wttr() -> Optional[Dict]:
    """wttr.in 폴백"""
    url = f"https://wttr.in/{LAT},{LON}?format=j1&lang=ko"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        cur = data["current_condition"][0]
        today = data["weather"][0]
        desc = cur.get("lang_ko", [{}])[0].get("value") or cur["weatherDesc"][0]["value"]

        hourly_desc = {}
        for h in today.get("hourly", []):
            hour = int(h.get("time", "0")) // 100
            h_desc = h.get("lang_ko", [{}])[0].get("value") or h["weatherDesc"][0]["value"]
            hourly_desc[hour] = {"desc": h_desc, "pop": _to_int(h.get("chanceofrain", 0))}

        rain_chance = max((v["pop"] for v in hourly_desc.values()), default=0)
        weather = {
            "location": LOCATION_NAME,
            "desc": desc,
            "temp": cur["temp_C"],
            "feels": cur["FeelsLikeC"],
            "min": today["mintempC"],
            "max": today["maxtempC"],
            "humidity": cur["humidity"],
            "rain_chance": rain_chance,
            "am": _period_summary(hourly_desc, *AM_WINDOW),
            "pm": _period_summary(hourly_desc, *PM_WINDOW),
        }
        print(f"✅ 날씨(wttr.in): {desc} {weather['temp']}℃ (체감 {weather['feels']}℃), "
              f"{weather['min']}~{weather['max']}℃, 강수 {rain_chance}%")
        return weather
    except Exception as e:
        print(f"❌ 날씨 수집 실패: {e}")
        return None


def _period_summary(hourly_desc: Dict, lo: int, hi: int, target: int) -> Optional[Dict]:
    """시간대(lo~hi) 대표 하늘상태 + 최대 강수확률"""
    window = {h: v for h, v in hourly_desc.items() if lo <= h <= hi and v.get("desc")}
    if not window:
        return None
    rep_hour = target if target in window else min(window, key=lambda h: abs(h - target))
    return {
        "desc": window[rep_hour]["desc"],
        "pop": max(v["pop"] for v in window.values()),
    }


def _to_int(v) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def _clean_num(v: Optional[str]) -> str:
    """'18.0' → '18', None → ''"""
    if v in (None, ""):
        return ""
    try:
        f = float(v)
        return str(int(f)) if f == int(f) else str(f)
    except ValueError:
        return str(v)


def _min_of(vals):
    nums = [float(v) for v in vals if _is_num(v)]
    return str(int(min(nums))) if nums else ""


def _max_of(vals):
    nums = [float(v) for v in vals if _is_num(v)]
    return str(int(max(nums))) if nums else ""


def _is_num(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    print(fetch_weather())
