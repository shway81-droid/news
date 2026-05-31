"""주가지수 수집 모듈 (나스닥·S&P500, 전일 대비)

데이터 소스: Stooq 일봉 CSV (API 키 불필요). 실패 시 Yahoo Finance 폴백.
"""
import csv
import io
from typing import List, Dict, Optional

import requests

# (표시명, Stooq 심볼, Yahoo 심볼)
INDICES = [
    ("나스닥", "^ndq", "^IXIC"),
    ("S&P500", "^spx", "^GSPC"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def fetch_indices() -> List[Dict]:
    """주요 지수의 종가와 전일 대비 등락 수집"""
    results = []
    for name, stooq_sym, yahoo_sym in INDICES:
        quote = _from_stooq(stooq_sym) or _from_yahoo(yahoo_sym)
        if quote:
            close, prev = quote
            change = close - prev
            pct = (change / prev * 100) if prev else 0.0
            results.append({
                "name": name,
                "close": close,
                "change": change,
                "change_pct": pct,
            })
            print(f"✅ {name}: {close:,.2f} ({change:+,.2f}, {pct:+.2f}%)")
        else:
            print(f"❌ {name}: 시세 수집 실패")
    return results


def _from_stooq(symbol: str) -> Optional[tuple]:
    """Stooq 일봉 CSV에서 최근 종가·전일 종가 반환"""
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        rows = list(csv.DictReader(io.StringIO(resp.text)))
        closes = [float(r["Close"]) for r in rows if r.get("Close") not in (None, "", "N/D")]
        if len(closes) >= 2:
            return closes[-1], closes[-2]
    except Exception as e:
        print(f"⚠️ Stooq {symbol} 실패: {e}")
    return None


def _from_yahoo(symbol: str) -> Optional[tuple]:
    """Yahoo Finance 차트 API 폴백"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
        if len(closes) >= 2:
            return closes[-1], closes[-2]
    except Exception as e:
        print(f"⚠️ Yahoo {symbol} 실패: {e}")
    return None


if __name__ == "__main__":
    for idx in fetch_indices():
        print(idx)
