import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from pydantic import BaseModel
from agents.langgraph_workflow import run_langgraph_agent
app=FastAPI(title="AEGIS Phase 1-3 API")
class IncidentRequest(BaseModel):
    incident_id:str="API-INC-001"; service:str; severity:str="P2"; alert:str; logs:str; metrics:str=""
@app.get("/")
def health(): return {"status":"ok","service":"AEGIS Phase 1-3"}
@app.post("/analyze")
def analyze(req:IncidentRequest): return run_langgraph_agent(req.model_dump())
