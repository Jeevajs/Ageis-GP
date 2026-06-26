from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END
from tools.incident_tools import query_logs, search_incidents, search_runbooks
from agents.react_agent import AegisReActAgent
class IncidentState(TypedDict, total=False):
    incident: Dict[str, Any]; log_findings: List[str]; similar_incidents: List[Dict[str,Any]]; runbooks: List[Dict[str,Any]]; report: Dict[str,Any]
def analyze_logs(state): state["log_findings"]=query_logs(state["incident"].get("logs","")); return state
def retrieve_incidents(state):
    i=state["incident"]; q=f"{i.get('alert','')} {i.get('service','')} {i.get('logs','')} {i.get('metrics','')}"
    state["similar_incidents"]=search_incidents(q,5); return state
def retrieve_runbooks(state):
    i=state["incident"]; q=f"{i.get('alert','')} {i.get('service','')} {i.get('logs','')} {i.get('metrics','')}"
    state["runbooks"]=search_runbooks(q,5); return state
def generate_report(state):
    state["report"]=AegisReActAgent().analyze(state["incident"])
    state["report"]["workflow"]="LangGraph: analyze_logs -> retrieve_incidents -> retrieve_runbooks -> generate_report"
    return state
def build_graph():
    g=StateGraph(IncidentState); g.add_node("analyze_logs",analyze_logs); g.add_node("retrieve_incidents",retrieve_incidents); g.add_node("retrieve_runbooks",retrieve_runbooks); g.add_node("generate_report",generate_report)
    g.set_entry_point("analyze_logs"); g.add_edge("analyze_logs","retrieve_incidents"); g.add_edge("retrieve_incidents","retrieve_runbooks"); g.add_edge("retrieve_runbooks","generate_report"); g.add_edge("generate_report",END)
    return g.compile()
def run_langgraph_agent(incident):
    return build_graph().invoke({"incident":incident})["report"]
