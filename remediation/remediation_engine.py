from remediation.remediation_catalog import get_actions_for_root_cause
from remediation.approval_store import record_event

class RemediationEngine:
    def build_plan(self, incident, root_cause, recommended_actions=None):
        actions = get_actions_for_root_cause(root_cause)
        plan = []
        for i, action in enumerate(actions, start=1):
            plan.append({"step": i, "incident_id": incident.get("incident_id"),
                         "service": incident.get("service"), "root_cause": root_cause,
                         **action,
                         "status": "PENDING_APPROVAL" if action["requires_approval"] else "READY_SAFE_READ_ONLY"})
        return plan
    def approve_action(self, incident_id, action_id, approver="demo-user", notes=""):
        return record_event(incident_id, action_id, "APPROVED", approver, notes)
    def reject_action(self, incident_id, action_id, approver="demo-user", notes=""):
        return record_event(incident_id, action_id, "REJECTED", approver, notes)
    def simulate_execution(self, action):
        if action.get("requires_approval") and action.get("status") != "APPROVED":
            return {"executed": False, "reason": "Human approval required before execution", "action_id": action.get("action_id")}
        return {"executed": True, "mode": "SIMULATION_ONLY", "action_id": action.get("action_id"),
                "command_preview": action.get("command_preview"),
                "message": "Action simulated successfully. No real infrastructure was changed."}
