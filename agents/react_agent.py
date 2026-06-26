from tools.incident_tools import query_logs, search_incidents, search_runbooks
class AegisReActAgent:
    def analyze(self, incident):
        q=f"{incident.get('alert','')} {incident.get('service','')} {incident.get('logs','')} {incident.get('metrics','')}"
        trace=["Reason: Understand incident context.","Act: Analyze raw log patterns."]
        findings=query_logs(incident.get("logs","")); trace.append(f"Observe: {findings}")
        trace.append("Act: Retrieve similar incidents using FAISS RAG."); similar=search_incidents(q,5); trace.append(f"Observe: Retrieved {len(similar)} similar incidents.")
        trace.append("Act: Retrieve relevant runbooks using FAISS RAG."); runbooks=search_runbooks(q,5); trace.append(f"Observe: Retrieved {len(runbooks)} runbooks.")
        rc=self.infer_root_cause(incident.get("logs",""), similar)
        conf=round(min(0.45+(similar[0]["score"] if similar else 0)+(0.1 if runbooks else 0),0.95),2)
        return {"incident_summary":incident,"probable_root_cause":rc,"confidence":conf,
        "recommended_actions":self.recommend(rc),
        "similar_incidents":[{"id":x["id"],"title":x["title"],"score":round(x["score"],4)} for x in similar],
        "relevant_runbooks":[{"id":x["id"],"title":x["title"],"score":round(x["score"],4)} for x in runbooks],
        "reasoning_trace":trace,
        "citations":[{"source":x["source"],"id":x["id"],"title":x["title"],"score":round(x["score"],4)} for x in similar[:3]+runbooks[:3]]}
    def infer_root_cause(self, logs, similar):
        t=logs.lower()
        if "under replicated" in t: return "Insufficient HDFS block replicas"
        if "timeout" in t: return "Network or downstream timeout"
        if "connection reset" in t: return "Transient network failure"
        if "machine check" in t: return "Hardware fault detected"
        if "not responding" in t: return "Compute node failure"
        if "connection pool" in t: return "Database connection pool exhaustion"
        if "oomkilled" in t: return "Pod memory exhaustion"
        if "consumer lag" in t: return "Consumer processing bottleneck"
        return similar[0].get("root_cause","Unknown root cause") if similar else "Unknown root cause"
    def recommend(self, rc):
        t=rc.lower()
        if "hdfs" in t or "replicas" in t: return ["Check DataNode health.","Trigger block re-replication.","Validate NameNode block report."]
        if "network" in t or "timeout" in t: return ["Check network latency.","Validate downstream service health.","Retry after stabilization."]
        if "hardware" in t or "node" in t: return ["Drain affected node.","Inspect hardware logs.","Restart or replace node after approval."]
        if "database" in t: return ["Check DB connections.","Increase pool temporarily.","Kill stale sessions and review slow queries."]
        if "memory" in t: return ["Check pod events.","Increase memory limit.","Capture heap dump if leak suspected."]
        if "consumer" in t: return ["Check lag and partitions.","Scale consumers.","Fix downstream bottleneck."]
        return ["Review similar incidents.","Check runbook steps.","Escalate to service owner."]
