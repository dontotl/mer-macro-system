from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd

from automation.backtest_engine import BacktestEngine
from automation.data_loader import load_market_snapshot
from automation.metrics import summarize_performance
from automation.strategy_rules import entry_candidate

START = "20160101"
END = "20260331"
INITIAL_CAPITAL = 100_000_000
RS_TOP_PERCENTILE = 0.2



def prepare_indicators(price_df: pd.DataFrame, cap_df: pd.DataFrame, benchmark: pd.DataFrame) -> pd.DataFrame:
    df = price_df.join(cap_df, how="left")
    df["market_cap"] = df["market_cap"].ffill()
    for window in [5, 10, 20, 60]:
        df[f"ma{window}"] = df["close"].rolling(window).mean()
    df["is_3m_high"] = df["close"] >= df["close"].rolling(60).max()
    stock_ret = df["close"].pct_change(60)
    bench_ret = benchmark["close"].reindex(df.index).pct_change(60)
    df["rs_ratio"] = stock_ret / bench_ret.replace(0, pd.NA)
    return df



def rank_rs(frames: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    combined = pd.DataFrame({ticker: df["rs_ratio"] for ticker, df in frames.items()})
    pct = combined.rank(axis=1, ascending=False, pct=True)
    for ticker, df in frames.items():
        df["rs_percentile"] = pct[ticker]
    return frames



def build_candidates(snapshot) -> Dict[str, pd.DataFrame]:
    frames = {}
    for ticker, price_df in snapshot.prices.items():
        frames[ticker] = prepare_indicators(price_df, snapshot.market_caps[ticker], snapshot.benchmark)
    return rank_rs(frames)



def run() -> tuple[pd.Series, List[dict], object]:
    snapshot = load_market_snapshot(START, END)
    frames = build_candidates(snapshot)
    all_dates = sorted(snapshot.benchmark.index)
    engine = BacktestEngine(initial_capital=INITIAL_CAPITAL, unit_fraction=0.2)
    equity_records = []

    for date in all_dates:
        date_str = date.strftime("%Y-%m-%d")
        # manage open positions first
        for ticker in list(engine.positions.keys()):
            row = frames[ticker].loc[date] if date in frames[ticker].index else None
            if row is None or row.isna().any():
                continue
            engine.on_bar(date_str, ticker, row)

        # one new entry per day max, if capital room exists
        available_slots = 5 - sum(state.units_held for state in engine.positions.values())
        if available_slots > 0:
            todays = []
            for ticker, df in frames.items():
                if ticker in engine.positions:
                    continue
                if date not in df.index:
                    continue
                row = df.loc[date]
                required = ["market_cap", "rs_percentile", "is_3m_high", "ma5", "ma10", "ma20", "ma60", "close"]
                if row[required].isna().any():
                    continue
                if entry_candidate(row, RS_TOP_PERCENTILE):
                    todays.append((ticker, row["rs_ratio"], row["close"]))
            if todays:
                todays.sort(key=lambda x: x[1], reverse=True)
                ticker, _, close = todays[0]
                engine.buy_initial(date_str, ticker, float(close))

        equity = engine.cash
        for ticker, state in engine.positions.items():
            if date in frames[ticker].index:
                close = float(frames[ticker].loc[date]["close"])
                avg_ref = state.initial_entry_price
                if state.units_held == 2 and state.entry_price_unit_2:
                    avg_ref = (state.initial_entry_price + state.entry_price_unit_2) / 2
                elif state.units_held == 3 and state.entry_price_unit_2 and state.entry_price_unit_3:
                    avg_ref = (state.initial_entry_price + state.entry_price_unit_2 + state.entry_price_unit_3) / 3
                invested = engine.position_cost.get(ticker, INITIAL_CAPITAL * 0.2 * state.units_held)
                equity += invested * (close / avg_ref)
        equity_records.append((date, equity))

    equity_curve = pd.Series({d: v for d, v in equity_records}).sort_index()
    summary = summarize_performance(equity_curve)
    trades = [trade.__dict__ for trade in engine.trades]
    return equity_curve, trades, summary



def save_outputs(equity_curve: pd.Series, trades: List[dict], summary) -> None:
    out_dir = Path("automation/results")
    out_dir.mkdir(parents=True, exist_ok=True)

    equity_curve.to_csv(out_dir / "equity_curve.csv", header=["equity"])
    pd.DataFrame(trades).to_csv(out_dir / "trades.csv", index=False)

    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Total Return: {summary.total_return:.2%}\n")
        f.write(f"CAGR: {summary.cagr:.2%}\n")
        f.write(f"MDD: {summary.mdd:.2%}\n")
        f.write(f"Sharpe: {summary.sharpe:.2f}\n")

    plt.figure(figsize=(10, 5))
    equity_curve.plot(title="KRX RS Trend Following Equity Curve")
    plt.tight_layout()
    plt.savefig(out_dir / "equity_curve.png")


if __name__ == "__main__":
    equity_curve, trades, summary = run()
    save_outputs(equity_curve, trades, summary)
    print(summary)
