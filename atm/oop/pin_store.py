import json
from datetime import datetime
from pathlib import Path

from django.contrib.auth.hashers import check_password, make_password

DEFAULT_PIN = "1234"
FILE = Path(__file__).resolve().parent / "pin_store.json"


def _read():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def check(pin):
    """True if pin matches the saved PIN (or the default 1234 if never changed)."""
    data = _read()
    if data.get("hash"):
        return check_password(pin, data["hash"])
    return pin == DEFAULT_PIN


def change(new_pin):
    FILE.write_text(
        json.dumps({"hash": make_password(new_pin), "changed": datetime.now().isoformat()}),
        encoding="utf-8",
    )


def changed_at():
    value = _read().get("changed")
    return datetime.fromisoformat(value) if value else None