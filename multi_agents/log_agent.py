class LogAnalysisAgent:
    def analyze(self, incident):
        logs = str(incident.get("logs", "")).lower()
        findings = []
        severity_score = 0.2
        patterns = {
            "timeout": ("Timeout found in logs", 0.75),
            "connection reset": ("Connection reset found in logs", 0.75),
            "under replicated": ("HDFS under-replication found", 0.85),
            "oomkilled": ("OOMKilled memory failure found", 0.90),
            "crashloopbackoff": ("CrashLoopBackOff found", 0.90),
            "connection pool": ("Database connection pool exhaustion found", 0.88),
            "consumer lag": ("Kafka consumer lag found", 0.82),
            "http 500": ("HTTP 500 application error found", 0.70),
            "machine check": ("Hardware machine check found", 0.92),
            "not responding": ("Node not responding found", 0.85),
        }
        for keyword, (msg, score) in patterns.items():
            if keyword in logs:
                findings.append({"pattern": keyword, "finding": msg, "score": score})
                severity_score = max(severity_score, score)
        if not findings:
            findings.append({"pattern": "unknown", "finding": "No known high-confidence pattern found", "score": 0.30})
        return {"agent": "LogAnalysisAgent", "findings": findings, "severity_score": round(severity_score, 2),
                "summary": "; ".join([x["finding"] for x in findings[:3]])}
