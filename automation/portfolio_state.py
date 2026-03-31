from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

STATE_PATH = Path("automation/state/portfolio_state.json")
EXAMPLE_PATH = Path("automation/state/portfolio_state.example.json")



def ensure_state() -> Dict[str, Any]:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_PATH.exists():
        if EXAMPLE_PATH.exists():
            STATE_PATH.write_text(EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            STATE_PATH.write_text(json.dumps({"asOf": None, "totalUnits": 5, "usedUnits": 0, "cashUnits": 5, "positions": []}, ensure_ascii=False, indent=2), encoding="utf-8")
    return load_state()



def load_state() -> Dict[str, Any]:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))



def save_state(state: Dict[str, Any]) -> None:
    state["usedUnits"] = sum(p["unitsHeld"] for p in state.get("positions", []))
    state["cashUnits"] = state.get("totalUnits", 5) - state["usedUnits"]
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
