from pathlib import Path
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
STORE_FILE = ROOT / "data" / "remediation" / "approval_events.json"

def _load():
    if not STORE_FILE.exists():
        return []
    return json.loads(STORE_FILE.read_text(encoding="utf-8"))

def _save(events):
    STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STORE_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")

def record_event(incident_id, action_id, decision, approver="demo-user", notes=""):
    events = _load()
    event = {"timestamp": datetime.utcnow().isoformat(), "incident_id": incident_id,
             "action_id": action_id, "decision": decision, "approver": approver, "notes": notes}
    events.append(event)
    _save(events)
    return event

def get_events():
    return _load()
