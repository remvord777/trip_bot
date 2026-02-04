import json
from pathlib import Path

ADVANCES_FILE = Path("data/advances.json")


def load_advances() -> dict:
    if not ADVANCES_FILE.exists():
        return {}
    with ADVANCES_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_advances(data: dict):
    ADVANCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ADVANCES_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_advance(telegram_id: str, advance: dict):
    data = load_advances()
    data.setdefault(telegram_id, []).append(advance)
    save_advances(data)
