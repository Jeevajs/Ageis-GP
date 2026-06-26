import re
class MetricAnalysisAgent:
    def analyze(self, incident):
        metrics = str(incident.get("metrics", "")).lower()
        findings = []
        score = 0.2
        def extract_num(name):
            match = re.search(name + r"\s*=\s*(\d+)", metrics)
            return int(match.group(1)) if match else None
        checks = [
            ("cpu", 85, "High CPU usage detected"),
            ("memory", 85, "High memory usage detected"),
            ("error_rate", 10, "High error rate detected"),
            ("consumer_lag", 1000, "High consumer lag detected"),
            ("db_connections", 90, "Database connection saturation detected"),
        ]
        for name, threshold, msg in checks:
            val = extract_num(name)
            if val and val >= threshold:
                findings.append(f"{msg}: {val}")
                score = max(score, 0.8)
        if not findings:
            findings.append("No critical metric threshold breach detected")
        return {"agent": "MetricAnalysisAgent", "findings": findings, "metric_score": round(score, 2),
                "summary": "; ".join(findings[:3])}
