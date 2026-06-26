"""
AEGIS Final Demo API

Run:
uvicorn api.main:app --reload

Open:
http://127.0.0.1:8000/docs
"""

import sys
from pathlib import Path

# Allow imports from project root
sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from pydantic import BaseModel

from multi_agents.planner_agent import AgenticIncidentPlanner
from remediation.remediation_engine import RemediationEngine
from remediation.approval_store import load_events


app = FastAPI(title="AEGIS Final Demo API")

planner = AgenticIncidentPlanner()
engine = RemediationEngine()


class IncidentRequest(BaseModel):
    incident_id: str
    service: str
    severity: str = "P2"
    alert: str
    logs: str
    metrics: str = ""
    use_llm: bool = True
    model: str = "gpt-4o-mini"


class ApprovalRequest(BaseModel):
    incident_id: str
    action_id: str
    approver: str = "demo-user"
    notes: str = ""


@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "AEGIS Final Demo API"
    }


@app.post("/analyze")
def analyze(req: IncidentRequest):
    data = req.model_dump()
    use_llm = data.pop("use_llm")
    model = data.pop("model")

    result = planner.run(
        incident=data,
        use_llm=use_llm,
        model=model
    )

    return result


@app.post("/analyze-and-plan")
def analyze_and_plan(req: IncidentRequest):
    data = req.model_dump()
    use_llm = data.pop("use_llm")
    model = data.pop("model")

    result = planner.run(
        incident=data,
        use_llm=use_llm,
        model=model
    )

    plan = engine.build_plan(
        incident=data,
        root_cause=result.get("probable_root_cause"),
        recommended_actions=result.get("recommended_actions", [])
    )

    return {
        "analysis": result,
        "remediation_plan": plan
    }


@app.post("/approve")
def approve(req: ApprovalRequest):
    return engine.approve_action(
        incident_id=req.incident_id,
        action_id=req.action_id,
        approver=req.approver,
        notes=req.notes
    )


@app.post("/reject")
def reject(req: ApprovalRequest):
    return engine.reject_action(
        incident_id=req.incident_id,
        action_id=req.action_id,
        approver=req.approver,
        notes=req.notes
    )


@app.get("/approval-events")
def approval_events():
    return load_events()