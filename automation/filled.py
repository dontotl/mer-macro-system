from __future__ import annotations

import argparse
from datetime import datetime

from automation.portfolio_state import ensure_state, save_state



def recalc_stop(position: dict) -> None:
    if position["unitsHeld"] == 1:
        position["stopPrice"] = round(position["initialEntry"] * 0.92, 2)
    elif position["unitsHeld"] == 2 and position.get("add1"):
        position["stopPrice"] = round(position["add1"] * 0.92, 2)
    elif position["unitsHeld"] == 3 and position.get("add2"):
        position["stopPrice"] = round(position["add2"] * 0.92, 2)



def do_buy(ticker: str, price: float, name: str | None = None):
    state = ensure_state()
    positions = state.get("positions", [])
    if any(p["ticker"] == ticker for p in positions):
        raise ValueError(f"{ticker} already exists in portfolio")
    position = {
        "ticker": ticker,
        "name": name or ticker,
        "unitsHeld": 1,
        "initialEntry": price,
        "add1": None,
        "add2": None,
        "lastUnitEntry": price,
        "stopPrice": round(price * 0.92, 2),
        "ma20": None,
    }
    positions.append(position)
    state["positions"] = positions
    state["asOf"] = datetime.now().isoformat()
    save_state(state)



def do_add(ticker: str, price: float):
    state = ensure_state()
    for p in state.get("positions", []):
        if p["ticker"] == ticker:
            if p["unitsHeld"] >= 3:
                raise ValueError(f"{ticker} already has 3 units")
            p["unitsHeld"] += 1
            if p["unitsHeld"] == 2:
                p["add1"] = price
            elif p["unitsHeld"] == 3:
                p["add2"] = price
            p["lastUnitEntry"] = price
            recalc_stop(p)
            state["asOf"] = datetime.now().isoformat()
            save_state(state)
            return
    raise ValueError(f"{ticker} not found in portfolio")



def do_sell(ticker: str):
    state = ensure_state()
    state["positions"] = [p for p in state.get("positions", []) if p["ticker"] != ticker]
    state["asOf"] = datetime.now().isoformat()
    save_state(state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["buy", "add", "sell"])
    parser.add_argument("ticker")
    parser.add_argument("price", nargs="?", type=float)
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    if args.action == "buy":
        if args.price is None:
            raise ValueError("buy requires price")
        do_buy(args.ticker, args.price, args.name)
    elif args.action == "add":
        if args.price is None:
            raise ValueError("add requires price")
        do_add(args.ticker, args.price)
    elif args.action == "sell":
        do_sell(args.ticker)
