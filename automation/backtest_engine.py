from dataclasses import dataclass
from typing import List, Dict, Optional

from automation.strategy_rules import PositionState, should_add_unit, should_exit


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
        self.position_cost: Dict[str, float] = {}

    def _unit_size_cash(self) -> float:
        return self.initial_capital * self.unit_fraction

    def buy_initial(self, date: str, ticker: str, price: float):
        cost = self._unit_size_cash()
        if self.cash < cost:
            return
        self.cash -= cost
        state = PositionState(
            ticker=ticker,
            units_held=1,
            initial_entry_price=price,
            last_unit_entry_price=price,
        )
        self.positions[ticker] = state
        self.position_cost[ticker] = cost
        self.trades.append(Trade(date, ticker, "BUY", price, 1, "ENTRY"))

    def add_unit(self, date: str, ticker: str, price: float):
        cost = self._unit_size_cash()
        if self.cash < cost:
            return
        state = self.positions[ticker]
        self.cash -= cost
        self.position_cost[ticker] = self.position_cost.get(ticker, 0.0) + cost
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
        state = self.positions[ticker]
        if state.initial_entry_price and state.units_held > 0:
            avg_ref = state.initial_entry_price
            if state.units_held == 2 and state.entry_price_unit_2:
                avg_ref = (state.initial_entry_price + state.entry_price_unit_2) / 2
            elif state.units_held == 3 and state.entry_price_unit_2 and state.entry_price_unit_3:
                avg_ref = (state.initial_entry_price + state.entry_price_unit_2 + state.entry_price_unit_3) / 3
            invested = self.position_cost.get(ticker, self._unit_size_cash() * state.units_held)
            proceeds = invested * (price / avg_ref)
            self.cash += proceeds
        self.trades.append(Trade(date, ticker, "SELL", price, 0, reason))
        del self.positions[ticker]
        self.position_cost.pop(ticker, None)

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
