import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from rl.rl_policy_agent import RLRemediationPolicyAgent
from multimodal.multimodal_rca_agent import MultimodalRCAAgent
from executor.autonomous_executor import AutonomousExecutor


class FullAEGISPhase4Orchestrator:
    """
    Unified Phase-4 AEGIS orchestrator.

    Integrates:
    - Existing Multi-Agent planner
    - RAG/OpenAI RCA
    - Multimodal RCA
    - GNN RCA ranking
    - RL remediation policy
    - Remediation engine
    - Autonomous execution simulation
    """

    def __init__(self):
        self.rl_agent = RLRemediationPolicyAgent()
        self.multimodal_agent = MultimodalRCAAgent()
        self.executor = AutonomousExecutor()

    def run(self, incident, use_llm=True, model="gpt-4o-mini", approved=False):
        planner_result = self._run_existing_planner(incident, use_llm, model)

        root_cause = (
            planner_result.get("probable_root_cause")
            or planner_result.get("root_cause")
            or "Unknown root cause"
        )

        multimodal_result = self.multimodal_agent.analyze(incident)
        gnn_result = self._run_gnn_agent(incident)
        rl_result = self.rl_agent.recommend_action(incident, root_cause)
        remediation_plan = self._build_remediation_plan(incident, root_cause, planner_result)
        execution_result = self.executor.execute(
            incident_id=incident.get("incident_id", "UNKNOWN"),
            action=rl_result["recommended_action"],
            approved=approved,
        )

        return {
            "incident": incident,
            "planner_result": planner_result,
            "multimodal_rca": multimodal_result,
            "gnn_rca_ranking": gnn_result,
            "rl_remediation_policy": rl_result,
            "remediation_plan": remediation_plan,
            "autonomous_execution": execution_result,
        }

    def _run_existing_planner(self, incident, use_llm, model):
        try:
            from multi_agents.planner_agent import AgenticIncidentPlanner
            planner = AgenticIncidentPlanner()
            return planner.run(incident, use_llm=use_llm, model=model)
        except Exception as exc:
            result = self._fallback_rca(incident)
            result["planner_error"] = str(exc)
            return result

    def _run_gnn_agent(self, incident):
        try:
            from gnn.gnn_rca_agent import GNNRCAAgent
            gnn_agent = GNNRCAAgent()
            return gnn_agent.predict(incident)
        except Exception as exc:
            return {
                "agent": "GNNRCAAgent",
                "available": False,
                "error": str(exc),
                "top3_root_causes": self._fallback_gnn(incident),
            }

    def _build_remediation_plan(self, incident, root_cause, planner_result):
        try:
            from remediation.remediation_engine import RemediationEngine
            engine = RemediationEngine()
            return engine.build_plan(
                incident,
                root_cause,
                planner_result.get("recommended_actions", []),
            )
        except Exception as exc:
            return [
                {
                    "action_id": f"{incident.get('incident_id','INC')}-ACT-001",
                    "title": "Manual review and safe remediation",
                    "requires_approval": True,
                    "risk": "medium",
                    "error": str(exc),
                }
            ]

    def _fallback_rca(self, incident):
        text = f"{incident.get('alert','')} {incident.get('logs','')} {incident.get('metrics','')}".lower()

        if "memory" in text or "oom" in text:
            root = "Memory exhaustion"
        elif "kafka" in text:
            root = "Kafka consumer processing bottleneck"
        elif "database" in text or "connection pool" in text or "jdbc" in text:
            root = "Database connection pool exhaustion"
        elif "http 500" in text or "nullpointer" in text:
            root = "Application exception after deployment"
        elif "network" in text or "packet loss" in text:
            root = "Network latency spike"
        elif "payment gateway" in text:
            root = "Payment gateway timeout"
        else:
            root = "General service degradation"

        return {
            "probable_root_cause": root,
            "confidence": 0.75,
            "evidence": ["Fallback RCA used"],
            "recommended_actions": ["Investigate logs", "Validate metrics", "Apply safe remediation plan"],
        }

    def _fallback_gnn(self, incident):
        text = f"{incident.get('alert','')} {incident.get('logs','')} {incident.get('metrics','')}".lower()

        if "memory" in text or "oom" in text:
            return [
                {"root_cause": "Memory exhaustion", "confidence": 0.86},
                {"root_cause": "Pod resource limit issue", "confidence": 0.72},
                {"root_cause": "Node pressure", "confidence": 0.55},
            ]

        if "kafka" in text:
            return [
                {"root_cause": "Kafka consumer bottleneck", "confidence": 0.88},
                {"root_cause": "Message processing delay", "confidence": 0.70},
                {"root_cause": "Downstream slowness", "confidence": 0.52},
            ]

        if "database" in text or "connection pool" in text:
            return [
                {"root_cause": "Database connection pool exhaustion", "confidence": 0.90},
                {"root_cause": "Slow query", "confidence": 0.61},
                {"root_cause": "Database saturation", "confidence": 0.58},
            ]

        return [
            {"root_cause": "Application degradation", "confidence": 0.70},
            {"root_cause": "Dependency failure", "confidence": 0.60},
            {"root_cause": "Infrastructure issue", "confidence": 0.50},
        ]