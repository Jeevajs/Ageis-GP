from multi_agents.log_agent import LogAnalysisAgent
from multi_agents.metric_agent import MetricAnalysisAgent
from multi_agents.retrieval_agent import RetrievalAgent
from multi_agents.graph_agent import GraphReasoningAgent
from gnn.gnn_agent import GNNRCABaselineAgent
from agents.phase4_5_agent import AegisPhase45Agent

class AgenticIncidentPlanner:
    def run(self, incident, use_llm=True, model="gpt-4o-mini"):
        timeline = []
        def add_event(step, agent, status, summary):
            timeline.append({"step": step, "agent": agent, "status": status, "summary": summary})
        log_result = LogAnalysisAgent().analyze(incident)
        add_event(1, "LogAnalysisAgent", "completed", log_result["summary"])
        metric_result = MetricAnalysisAgent().analyze(incident)
        add_event(2, "MetricAnalysisAgent", "completed", metric_result["summary"])
        retrieval_result = RetrievalAgent().analyze(incident)
        add_event(3, "RetrievalAgent", "completed", retrieval_result["summary"])
        graph_result = GraphReasoningAgent().analyze(incident)
        add_event(4, "GraphReasoningAgent", "completed", graph_result["summary"])
        gnn_result = GNNRCABaselineAgent().analyze(incident)
        add_event(5, "GNNRCABaselineAgent", "completed" if gnn_result.get("available") else "skipped", gnn_result["summary"])
        final = AegisPhase45Agent().analyze(incident, use_llm=use_llm, model=model)
        add_event(6, "FinalSynthesisAgent", "completed", f"Final RCA: {final.get('probable_root_cause')}")
        confidence_values = [log_result.get("severity_score", 0), metric_result.get("metric_score", 0),
                             retrieval_result.get("retrieval_score", 0), graph_result.get("graph_score", 0),
                             final.get("confidence", 0)]
        if gnn_result.get("available") and gnn_result.get("top3_root_causes"):
            confidence_values.append(gnn_result["top3_root_causes"][0]["confidence"])
        ensemble_confidence = round(sum(confidence_values) / len(confidence_values), 2)
        final["phase6_multi_agent"] = {"log_analysis": log_result, "metric_analysis": metric_result,
                                       "retrieval_analysis": retrieval_result, "graph_analysis": graph_result,
                                       "gnn_analysis": gnn_result, "timeline": timeline,
                                       "ensemble_confidence": ensemble_confidence}
        final["confidence"] = max(float(final.get("confidence", 0)), ensemble_confidence)
        final["mode"] = "Phase 6 + 7 + 8: Multi-Agent + KG + GNN-style RCA + Enhanced UI"
        return final
