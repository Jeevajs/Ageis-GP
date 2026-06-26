def build_rca_prompt(incident, similar_incidents, runbooks, graph_candidates=None):
    similar_text = "\n\n".join([
        f"Similar Incident {i+1}:\nID: {x.get('id')}\nTitle: {x.get('title')}\nScore: {round(x.get('score',0),4)}\nText: {x.get('text','')[:1000]}"
        for i, x in enumerate(similar_incidents[:5])
    ])

    runbook_text = "\n\n".join([
        f"Runbook {i+1}:\nID: {x.get('id')}\nTitle: {x.get('title')}\nScore: {round(x.get('score',0),4)}\nContent: {x.get('text','')[:1000]}"
        for i, x in enumerate(runbooks[:5])
    ])

    graph_text = ""
    if graph_candidates:
        graph_text = "\n".join([
            f"- {x.get('service')} | score={x.get('score')} | reason={x.get('reason')}"
            for x in graph_candidates
        ])

    return f"""
You are AEGIS, an AI incident response assistant for Site Reliability Engineering.

Analyze the incident using:
1. Current incident alert, logs, and metrics
2. Similar retrieved incidents
3. Retrieved runbooks
4. Service dependency graph root-cause candidates

Return STRICT JSON only.

Current Incident:
Incident ID: {incident.get('incident_id')}
Service: {incident.get('service')}
Severity: {incident.get('severity')}
Alert: {incident.get('alert')}
Logs: {incident.get('logs')}
Metrics: {incident.get('metrics')}

Similar Incidents:
{similar_text}

Runbooks:
{runbook_text}

Graph-Based RCA Candidates:
{graph_text}

Required JSON format:
{{
  "root_cause": "specific probable root cause",
  "confidence": 0.0,
  "evidence": [
    "evidence from current logs",
    "evidence from similar incidents",
    "evidence from runbook or graph"
  ],
  "recommended_actions": [
    "step 1",
    "step 2",
    "step 3"
  ],
  "citations": [
    {{
      "source": "incident/runbook/graph",
      "id": "source id",
      "reason": "why this source supports the answer"
    }}
  ],
  "risk_level": "Low/Medium/High",
  "human_approval_required": true
}}

Rules:
- Do not hallucinate commands.
- Use citations from retrieved incidents, runbooks, or graph candidates.
- For destructive actions like restart, rollback, scale down, delete, mark human_approval_required as true.
- Confidence must be between 0 and 1.
"""
