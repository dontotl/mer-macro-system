from __future__ import annotations

import re
from io import StringIO
from typing import List

import pandas as pd
import requests


HEADERS = {"User-Agent": "Mozilla/5.0"}
MARKET_URL = "https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={page}"
CODE_RE = re.compile(r"/item/main\.naver\?code=(\d+)")



def _fetch_page(sosok: int, page: int) -> tuple[pd.DataFrame, List[str]]:
    resp = requests.get(MARKET_URL.format(sosok=sosok, page=page), headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = "euc-kr"
    tables = pd.read_html(StringIO(resp.text))
    table = tables[1].dropna(subset=["종목명"]).copy()
    codes = CODE_RE.findall(resp.text)
    return table, codes



def fetch_large_cap_universe(min_market_cap_eok: int = 10000) -> pd.DataFrame:
    results = []
    for sosok in [0, 1]:  # 0 KOSPI, 1 KOSDAQ
        page = 1
        while True:
            table, codes = _fetch_page(sosok, page)
            if table.empty:
                break
            table = table.reset_index(drop=True)
            table["code"] = codes[: len(table)]
            table["market"] = "KOSPI" if sosok == 0 else "KOSDAQ"
            table["시가총액"] = pd.to_numeric(table["시가총액"], errors="coerce")
            table = table[table["시가총액"] >= min_market_cap_eok]
            if table.empty:
                break
            results.append(table[["code", "종목명", "시가총액", "market"]])
            page += 1
            if page > 50:
                break
    if not results:
        raise RuntimeError("Failed to build large-cap universe from Naver Finance")
    return pd.concat(results, ignore_index=True).drop_duplicates(subset=["code"])
