import json
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parents[1]
STORE_PATH = BASE_DIR / "data" / "trips.json"


def load_trips() -> Dict[str, List[dict]]:
    if not STORE_PATH.exists():
        return {}
    with STORE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_trips(trips: Dict[str, List[dict]]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STORE_PATH.open("w", encoding="utf-8") as f:
        json.dump(trips, f, ensure_ascii=False, indent=2)
