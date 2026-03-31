from __future__ import annotations

from pathlib import Path

import pandas as pd

from automation.run_backtest import build_candidates
from automation.data_loader import load_market_snapshot
from automation.backtest_engine import BacktestEngine
from automation.metrics import summarize_performance

START = "20160101"
END = "20260331"
INITIAL_CAPITAL = 100_000_000
RS_TOP_PERCENTILE = 0.2



def run_fast():
    snapshot = load_market_snapshot(START, END, use_cached_only=True)
    frames = build_candidates(snapshot)
    all_dates = sorted(snapshot.benchmark.index)
    engine = BacktestEngine(initial_capital=INITIAL_CAPITAL, unit_fraction=0.2)
    equity_records = []

    candidates_by_date = {}
    for ticker, df in frames.items():
        df = df.copy()
        df["turnover"] = df["close"] * df["volume"]
        df["turnover_3d_avg_prev"] = df["turnover"].shift(1).rolling(3).mean()
        required = ["market_cap", "rs_percentile", "is_3m_high", "ma5", "ma10", "ma20", "ma60", "close", "open", "volume", "rs_ratio", "turnover_3d_avg_prev"]
        valid = df.dropna(subset=required).copy()
        cond = (
            (valid["market_cap"] >= 1_000_000_000_000)
            & (valid["rs_percentile"] <= RS_TOP_PERCENTILE)
            & (valid["is_3m_high"] == True)
            & (valid["ma5"] > valid["ma10"])
            & (valid["ma10"] > valid["ma20"])
            & (valid["ma20"] > valid["ma60"])
            & (valid["close"] > valid["open"])
            & (valid["turnover"] >= valid["turnover_3d_avg_prev"] * 1.5)
        )
        valid = valid[cond]
        for dt, row in valid.iterrows():
            candidates_by_date.setdefault(dt, []).append((ticker, float(row["rs_ratio"]), float(row["close"])))

    for date in all_dates:
        date_str = date.strftime("%Y-%m-%d")
        for ticker in list(engine.positions.keys()):
            row = frames[ticker].loc[date] if date in frames[ticker].index else None
            if row is None or row[["close", "ma20"]].isna().any():
                continue
            engine.on_bar(date_str, ticker, row)

        available_slots = 5 - sum(state.units_held for state in engine.positions.values())
        if available_slots > 0 and date in candidates_by_date:
            todays = [x for x in candidates_by_date[date] if x[0] not in engine.positions]
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

    out_dir = Path("automation/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    equity_curve.to_csv(out_dir / "equity_curve.csv", header=["equity"])
    pd.DataFrame([t.__dict__ for t in engine.trades]).to_csv(out_dir / "trades.csv", index=False)
    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Total Return: {summary.total_return:.2%}\n")
        f.write(f"CAGR: {summary.cagr:.2%}\n")
        f.write(f"MDD: {summary.mdd:.2%}\n")
        f.write(f"Sharpe: {summary.sharpe:.2f}\n")

    print(summary)


if __name__ == "__main__":
    run_fast()
