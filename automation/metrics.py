from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass
class PerformanceSummary:
    total_return: float
    cagr: float
    mdd: float
    sharpe: float



def calculate_drawdown(equity_curve: pd.Series) -> pd.Series:
    running_max = equity_curve.cummax()
    return equity_curve / running_max - 1.0



def summarize_performance(equity_curve: pd.Series) -> PerformanceSummary:
    returns = equity_curve.pct_change().dropna()
    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1.0
    years = max(len(equity_curve) / 252.0, 1e-9)
    cagr = (equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / years) - 1.0
    drawdown = calculate_drawdown(equity_curve)
    mdd = drawdown.min()
    sharpe = 0.0
    if not returns.empty and returns.std() > 0:
        sharpe = math.sqrt(252) * returns.mean() / returns.std()
    return PerformanceSummary(total_return=total_return, cagr=cagr, mdd=mdd, sharpe=sharpe)
