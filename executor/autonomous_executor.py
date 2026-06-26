import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_FILE = ROOT / "data" / "remediation" / "execution_audit.json"
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)


class AutonomousExecutor:
    """
    Safe autonomous execution layer.
    Real execution is disabled by default.

    To enable real execution:
    set AEGIS_EXECUTE_REAL=true

    For dissertation/demo, keep false.
    """

    def __init__(self):
        self.real_execution_enabled = os.getenv("AEGIS_EXECUTE_REAL", "false").lower() == "true"

    def execute(self, incident_id, action, approved=False):
        command = self._map_action_to_command(action)

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "incident_id": incident_id,
            "action": action,
            "command": command,
            "approved": approved,
            "real_execution_enabled": self.real_execution_enabled,
            "executed": False,
            "status": "PENDING_APPROVAL",
        }

        if not approved:
            self._save_event(event)
            return event

        if not self.real_execution_enabled:
            event["status"] = "SIMULATION_ONLY"
            event["executed"] = False
            self._save_event(event)
            return event

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            event["executed"] = True
            event["status"] = "EXECUTED"
            event["stdout"] = result.stdout
            event["stderr"] = result.stderr
        except Exception as exc:
            event["status"] = "FAILED"
            event["error"] = str(exc)

        self._save_event(event)
        return event

    def _map_action_to_command(self, action):
        mapping = {
            "restart_service": "echo kubectl rollout restart deployment/service-name",
            "scale_service": "echo kubectl scale deployment service-name --replicas=3",
            "rollback_deployment": "echo kubectl rollout undo deployment/service-name",
            "increase_memory": "echo update memory limit in deployment manifest",
            "increase_db_pool": "echo update DB connection pool configuration",
            "route_traffic_alternate_path": "echo route traffic to alternate healthy path",
            "escalate_to_sre": "echo create escalation ticket",
        }
        return mapping.get(action, "echo manual review required")

    def _save_event(self, event):
        if AUDIT_FILE.exists():
            data = json.loads(AUDIT_FILE.read_text())
        else:
            data = []

        data.append(event)
        AUDIT_FILE.write_text(json.dumps(data, indent=2))