from graph.graph_rca_ranker import rank_root_cause_services
class GraphReasoningAgent:
    def analyze(self, incident):
        candidates = rank_root_cause_services(incident, top_k=5)
        top = candidates[0] if candidates else {}
        return {"agent": "GraphReasoningAgent", "candidates": candidates,
                "top_candidate": top.get("service", "unknown"), "graph_score": top.get("score", 0.0),
                "summary": f"Top graph RCA candidate: {top.get('service', 'unknown')}"}
