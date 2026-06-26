from tools.incident_tools import query_logs, search_incidents, search_runbooks
from agents.react_agent import AegisReActAgent
from graph.graph_rca_ranker import rank_root_cause_services
from llm.rca_prompt_builder import build_rca_prompt
from llm.openai_client import call_openai, extract_json_safely

class AegisPhase45Agent:
    def analyze(self, incident, use_llm=True, model="llama3"):
        query = f"{incident.get('alert','')} {incident.get('service','')} {incident.get('logs','')} {incident.get('metrics','')}"
        trace = [
            "Phase 4: Build RAG context from incident and runbooks.",
            "Phase 5: Rank candidate root-cause services using service dependency graph."
        ]

        log_findings = query_logs(incident.get("logs", ""))
        similar = search_incidents(query, top_k=5)
        runbooks = search_runbooks(query, top_k=5)
        graph_candidates = rank_root_cause_services(incident, top_k=5)

        trace.append(f"Log findings: {log_findings}")
        trace.append(f"Retrieved {len(similar)} similar incidents.")
        trace.append(f"Retrieved {len(runbooks)} runbooks.")
        trace.append(f"Graph candidates: {graph_candidates}")

        fallback = AegisReActAgent().analyze(incident)

        if use_llm:
            prompt = build_rca_prompt(incident, similar, runbooks, graph_candidates)
            llm_text = call_openai(prompt, model=model)
            parsed = extract_json_safely(llm_text)

            if parsed:
                return {
                    "mode": "Phase 4 + 5: LLM RCA + RAG + Graph Ranking",
                    "incident_summary": incident,
                    "probable_root_cause": parsed.get("root_cause", fallback["probable_root_cause"]),
                    "confidence": parsed.get("confidence", fallback["confidence"]),
                    "evidence": parsed.get("evidence", []),
                    "recommended_actions": parsed.get("recommended_actions", fallback["recommended_actions"]),
                    "risk_level": parsed.get("risk_level", "Medium"),
                    "human_approval_required": parsed.get("human_approval_required", True),
                    "graph_root_cause_candidates": graph_candidates,
                    "similar_incidents": fallback["similar_incidents"],
                    "relevant_runbooks": fallback["relevant_runbooks"],
                    "citations": parsed.get("citations", fallback["citations"]),
                    "reasoning_trace": trace + ["LLM RCA completed successfully."],
                    "llm_raw_output": llm_text
                }

            trace.append("LLM unavailable or invalid JSON. Falling back to baseline RCA.")

        fallback["mode"] = "Fallback: Phase 1-3 RCA + RAG + Graph Ranking"
        fallback["evidence"] = log_findings
        fallback["graph_root_cause_candidates"] = graph_candidates
        fallback["risk_level"] = "Medium"
        fallback["human_approval_required"] = True
        fallback["reasoning_trace"] = trace + fallback.get("reasoning_trace", [])
        return fallback
