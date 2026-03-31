from dataclasses import dataclass
from typing import List, Dict, Optional

from strategy_rules import PositionState, should_add_unit, should_exit


@dataclass
class Trade:
    date: str
    ticker: str
    action: str
    price: float
    units_after: int
    reason: str


class BacktestEngine:
    def __init__(self, initial_capital: float, unit_fraction: float = 0.2):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.unit_fraction = unit_fraction
        self.positions: Dict[str, PositionState] = {}
        self.trades: List[Trade] = []

    def _unit_size_cash(self) -> float:
        return self.initial_capital * self.unit_fraction

    def buy_initial(self, date: str, ticker: str, price: float):
        state = PositionState(
            ticker=ticker,
            units_held=1,
            initial_entry_price=price,
            last_unit_entry_price=price,
        )
        self.positions[ticker] = state
        self.trades.append(Trade(date, ticker, "BUY", price, 1, "ENTRY"))

    def add_unit(self, date: str, ticker: str, price: float):
        state = self.positions[ticker]
        if state.units_held == 1:
            state.units_held = 2
            state.entry_price_unit_2 = price
            state.last_unit_entry_price = price
            state.add_step_1_done = True
            reason = "ADD_8PCT"
        elif state.units_held == 2:
            state.units_held = 3
            state.entry_price_unit_3 = price
            state.last_unit_entry_price = price
            state.add_step_2_done = True
            reason = "ADD_16PCT"
        else:
            return
        self.trades.append(Trade(date, ticker, "ADD", price, state.units_held, reason))

    def sell_all(self, date: str, ticker: str, price: float, reason: str):
        if ticker not in self.positions:
            return
        self.trades.append(Trade(date, ticker, "SELL", price, 0, reason))
        del self.positions[ticker]

    def on_bar(self, date: str, ticker: str, row):
        state: Optional[PositionState] = self.positions.get(ticker)
        if state is None:
            return

        exit_reason = should_exit(row["close"], row["ma20"], state)
        if exit_reason:
            self.sell_all(date, ticker, row["close"], exit_reason)
            return

        if should_add_unit(row["close"], state):
            self.add_unit(date, ticker, row["close"])


if __name__ == "__main__":
    print("Backtest engine skeleton ready.")
