from tools.incident_tools import search_incidents, search_runbooks
class RetrievalAgent:
    def analyze(self, incident):
        query = f"{incident.get('alert','')} {incident.get('service','')} {incident.get('logs','')} {incident.get('metrics','')}"
        similar = search_incidents(query, top_k=5)
        runbooks = search_runbooks(query, top_k=5)
        return {
            "agent": "RetrievalAgent",
            "similar_incidents": [{"id": x.get("id"), "title": x.get("title"), "score": round(x.get("score", 0), 4), "root_cause": x.get("root_cause", "")} for x in similar],
            "runbooks": [{"id": x.get("id"), "title": x.get("title"), "score": round(x.get("score", 0), 4)} for x in runbooks],
            "retrieval_score": round(similar[0].get("score", 0), 2) if similar else 0.0,
            "summary": f"Retrieved {len(similar)} similar incidents and {len(runbooks)} runbooks"
        }
