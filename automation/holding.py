from __future__ import annotations

from automation.portfolio_state import ensure_state



def render_holding() -> str:
    state = ensure_state()
    lines = []
    lines.append("[보유현황]")
    lines.append(f"사용 유닛: {state['usedUnits']} / {state['totalUnits']}")
    lines.append(f"남은 유닛: {state['cashUnits']}")

    positions = state.get("positions", [])
    if not positions:
        lines.append("보유 종목 없음")
        return "\n".join(lines)

    for p in positions:
        lines.append(f"- {p.get('name', '-') } ({p['ticker']}) / {p['unitsHeld']}유닛")
        lines.append(f"  - 최초진입: {p.get('initialEntry', '-')}")
        lines.append(f"  - 추가1: {p.get('add1', '-')}")
        lines.append(f"  - 추가2: {p.get('add2', '-')}")
        lines.append(f"  - 마지막유닛 기준 손절: {p.get('stopPrice', '-')}")
        lines.append(f"  - 20일선: {p.get('ma20', '-')}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_holding())
