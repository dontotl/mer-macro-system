from dataclasses import dataclass
from typing import Optional


@dataclass
class PositionState:
    ticker: str
    units_held: int = 0
    initial_entry_price: Optional[float] = None
    entry_price_unit_2: Optional[float] = None
    entry_price_unit_3: Optional[float] = None
    last_unit_entry_price: Optional[float] = None
    add_step_1_done: bool = False
    add_step_2_done: bool = False



def is_aligned(ma5: float, ma10: float, ma20: float, ma60: float) -> bool:
    return ma5 > ma10 > ma20 > ma60



def entry_candidate(row, rs_percentile_cutoff: float) -> bool:
    return all(
        [
            row["market_cap"] >= 1_000_000_000_000,
            row["rs_percentile"] <= rs_percentile_cutoff,
            row["is_3m_high"],
            is_aligned(row["ma5"], row["ma10"], row["ma20"], row["ma60"]),
        ]
    )



def should_add_unit(close_price: float, state: PositionState) -> bool:
    if state.units_held == 1 and not state.add_step_1_done:
        return close_price >= state.initial_entry_price * 1.08
    if state.units_held == 2 and not state.add_step_2_done:
        return close_price >= state.initial_entry_price * 1.16
    return False



def should_exit(close_price: float, ma20: float, state: PositionState) -> Optional[str]:
    if state.units_held == 0:
        return None
    if close_price < ma20:
        return "MA20_BREAK"
    if state.last_unit_entry_price and close_price <= state.last_unit_entry_price * 0.92:
        return "STOP_8PCT"
    return None
