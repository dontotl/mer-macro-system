from __future__ import annotations

from io import StringIO
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup


NAVER_KOSPI_URL = "https://finance.naver.com/sise/sise_index_day.naver?code=KOSPI&page={page}"



def fetch_kospi_history(max_pages: int = 300) -> pd.DataFrame:
    rows: List[dict] = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for page in range(1, max_pages + 1):
        resp = requests.get(NAVER_KOSPI_URL.format(page=page), headers=headers, timeout=20)
        resp.raise_for_status()
        resp.encoding = "euc-kr"
        tables = pd.read_html(StringIO(resp.text))
        if not tables:
            break
        table = tables[0]
        if "날짜" not in table.columns:
            continue
        for _, row in table.dropna().iterrows():
            try:
                close_col = "종가" if "종가" in table.columns else "체결가"
                rows.append(
                    {
                        "date": pd.to_datetime(row["날짜"]),
                        "close": float(str(row[close_col]).replace(",", "")),
                    }
                )
            except Exception:
                continue
    if not rows:
        raise RuntimeError("Failed to fetch KOSPI history from Naver Finance")
    df = pd.DataFrame(rows).drop_duplicates(subset=["date"]).sort_values("date")
    return df.set_index("date")
