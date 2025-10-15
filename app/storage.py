# app/storage.py
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TASKS_FILE = DATA_DIR / "tasks.json"

def init_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("{}")

def load_tasks() -> dict:
    try:
        return json.loads(TASKS_FILE.read_text())
    except Exception:
        return {}

def save_tasks(tasks: dict):
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))
