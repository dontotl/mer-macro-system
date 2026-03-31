from __future__ import annotations

from datetime import datetime

import pandas as pd

from automation.data_loader import load_market_snapshot
from automation.run_backtest_experiments import build_candidates
from automation.holding import render_holding

START = "20160101"
END = "20260331"



def render_signal_report(asof: str | None = None) -> str:
    asof = asof or datetime.now().strftime("%Y%m%d")
    snapshot = load_market_snapshot(START, END, use_cached_only=True)
    frames, candidates_by_date = build_candidates(snapshot, 0.1, True, False)

    dt = pd.to_datetime(asof)
    lines = []
    lines.append("[오늘 신호 리포트]")
    if dt in candidates_by_date:
        todays = sorted(candidates_by_date[dt], key=lambda x: x[1], reverse=True)[:10]
        lines.append("신규 진입 후보:")
        for ticker, rs_ratio, close in todays:
            lines.append(f"- {ticker} / 종가 {close:.0f} / RS {rs_ratio:.2f}")
    else:
        lines.append("신규 진입 후보 없음")

    lines.append("")
    lines.append(render_holding())
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_signal_report())
