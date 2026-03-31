from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
from pykrx import stock

from automation.benchmark_loader import fetch_kospi_history
from automation.universe import MANUAL_MARKET_CAP, get_manual_universe


@dataclass
class MarketSnapshot:
    prices: Dict[str, pd.DataFrame]
    market_caps: Dict[str, pd.DataFrame]
    benchmark: pd.DataFrame



def get_trading_days(start: str, end: str) -> List[str]:
    days = stock.get_market_ohlcv_by_date(start, end, "005930").index
    return [d.strftime("%Y%m%d") for d in days]



def get_universe(asof: str, min_market_cap: int = 1_000_000_000_000) -> List[str]:
    tickers = stock.get_market_ticker_list(date=asof, market="ALL")
    if not tickers:
        return get_manual_universe()

    selected = []
    for ticker in tickers:
        try:
            cap_df = stock.get_market_cap_by_date(asof, asof, ticker)
            if cap_df.empty:
                continue
            market_cap = int(cap_df.iloc[-1]["시가총액"])
            if market_cap >= min_market_cap:
                selected.append(ticker)
        except Exception:
            continue
    return selected or get_manual_universe()



def fetch_price_frame(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = stock.get_market_ohlcv_by_date(start, end, ticker)
    if df.empty:
        return df
    df = df.rename(
        columns={
            "시가": "open",
            "고가": "high",
            "저가": "low",
            "종가": "close",
            "거래량": "volume",
        }
    )
    df.index = pd.to_datetime(df.index)
    return df[["open", "high", "low", "close", "volume"]]



def fetch_market_cap_frame(ticker: str, start: str, end: str) -> pd.DataFrame:
    df = stock.get_market_cap_by_date(start, end, ticker)
    if df.empty:
        price_df = fetch_price_frame(ticker, start, end)
        if price_df.empty:
            return pd.DataFrame()
        fallback = pd.DataFrame(index=price_df.index)
        fallback["market_cap"] = MANUAL_MARKET_CAP.get(ticker, 1_500_000_000_000)
        return fallback
    df = df.rename(columns={"시가총액": "market_cap"})
    df.index = pd.to_datetime(df.index)
    return df[["market_cap"]]



def fetch_benchmark(start: str, end: str, ticker: str = "005930") -> pd.DataFrame:
    try:
        df = fetch_kospi_history()
        return df.loc[pd.to_datetime(start): pd.to_datetime(end)][["close"]]
    except Exception:
        df = stock.get_market_ohlcv_by_date(start, end, ticker)
        df = df.rename(columns={"종가": "close"})
        df.index = pd.to_datetime(df.index)
        return df[["close"]]



def load_market_snapshot(start: str, end: str, asof: str | None = None) -> MarketSnapshot:
    asof = asof or end
    universe = get_universe(asof)
    prices: Dict[str, pd.DataFrame] = {}
    market_caps: Dict[str, pd.DataFrame] = {}

    for ticker in universe:
        price_df = fetch_price_frame(ticker, start, end)
        if price_df.empty:
            continue
        cap_df = fetch_market_cap_frame(ticker, start, end)
        prices[ticker] = price_df
        market_caps[ticker] = cap_df

    benchmark = fetch_benchmark(start, end)
    return MarketSnapshot(prices=prices, market_caps=market_caps, benchmark=benchmark)
