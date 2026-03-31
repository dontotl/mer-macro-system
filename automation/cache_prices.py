from __future__ import annotations

from pathlib import Path

from automation.data_loader import fetch_price_frame, get_universe

START = "20160101"
END = "20260331"
CACHE_DIR = Path("automation/cache/prices")



def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    universe = get_universe(END)
    print(f"universe_count={len(universe)}")
    saved = 0
    skipped = 0
    for idx, ticker in enumerate(universe, start=1):
        path = CACHE_DIR / f"{ticker}.csv"
        if path.exists():
            skipped += 1
            continue
        try:
            df = fetch_price_frame(ticker, START, END)
            if df.empty:
                print(f"[{idx}/{len(universe)}] empty {ticker}")
                continue
            df.to_csv(path)
            saved += 1
            print(f"[{idx}/{len(universe)}] saved {ticker} rows={len(df)}")
        except Exception as e:
            print(f"[{idx}/{len(universe)}] error {ticker}: {e}")
    print(f"saved={saved} skipped={skipped}")


if __name__ == "__main__":
    main()
