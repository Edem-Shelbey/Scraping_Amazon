# view/report_io.py
import os, json
from datetime import datetime
from typing import Any, Dict

REPORTS_DIR = os.path.join("view", "reports")
def ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)

def save_text(path: str, content: str):
    ensure_reports_dir()
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def save_json(path: str, data: Dict[str, Any]):
    ensure_reports_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def archive_json(report: Dict[str, Any], out_dir: str = REPORTS_DIR, limit_name: str = "report"):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"{limit_name}_{ts}.json")
    save_json(path, report)
    # latest
    try:
        save_json(os.path.join(out_dir, "report_latest.json"), report)
    except Exception:
        pass
    return path
