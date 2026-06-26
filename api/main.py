import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from pydantic import BaseModel

from agents.langgraph_workflow import run_langgraph_agent
from phase4.full_aegis_orchestrator import FullAEGISPhase4Orchestrator
from remediation.remediation_engine import RemediationEngine
from remediation.approval_store import get_events

app = FastAPI(title="AEGIS Unified API")

phase4_orchestrator = FullAEGISPhase4Orchestrator()
remediation_engine = RemediationEngine()


class IncidentRequest(BaseModel):
    incident_id: str = "API-INC-001"
    service: str
    severity: str = "P2"
    alert: str
    logs: str
    metrics: str = ""
    traces: str = ""
    screenshot_summary: str = ""
    use_llm: bool = True
    model: str = "gpt-4o-mini"
    approved: bool = False


class ApprovalRequest(BaseModel):
    incident_id: str
    action_id: str
    approver: str = "demo-user"
    notes: str = ""


@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "AEGIS Unified API",
        "supported_modes": [
            "Phase-3 LangGraph RCA",
            "Phase-4 Full AEGIS RCA",
            "RAG",
            "OpenAI",
            "Multi-Agent",
            "Neo4j",
            "GNN RCA",
            "RL Policy",
            "Multimodal RCA",
            "Human Approval",
            "Autonomous Execution Simulation",
        ],
    }


@app.post("/analyze")
def analyze_phase3(req: IncidentRequest):
    data = req.model_dump()
    data.pop("use_llm", None)
    data.pop("model", None)
    data.pop("approved", None)
    return run_langgraph_agent(data)


@app.post("/phase4/analyze")
def analyze_phase4(req: IncidentRequest):
    data = req.model_dump()

    use_llm = data.pop("use_llm")
    model = data.pop("model")
    approved = data.pop("approved")

    return phase4_orchestrator.run(
        incident=data,
        use_llm=use_llm,
        model=model,
        approved=approved,
    )


@app.post("/analyze-and-plan")
def analyze_and_plan(req: IncidentRequest):
    data = req.model_dump()

    use_llm = data.pop("use_llm")
    model = data.pop("model")
    approved = data.pop("approved")

    return phase4_orchestrator.run(
        incident=data,
        use_llm=use_llm,
        model=model,
        approved=approved,
    )


@app.post("/approve")
def approve(req: ApprovalRequest):
    return remediation_engine.approve_action(
        req.incident_id,
        req.action_id,
        req.approver,
        req.notes,
    )


@app.post("/reject")
def reject(req: ApprovalRequest):
    return remediation_engine.reject_action(
        req.incident_id,
        req.action_id,
        req.approver,
        req.notes,
    )


@app.get("/approval-events")
def approval_events():
    return get_events()