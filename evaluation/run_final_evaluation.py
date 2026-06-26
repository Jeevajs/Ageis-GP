"""
Run Final AEGIS Evaluation.

This script generates a presentation/report-ready CSV with:
- RCA match indicator
- Retrieval Recall@5
- Baseline MTTR
- Simulated AEGIS MTTR
- MTTR reduction percentage
- Remediation action count
- Human approval coverage

Output:
    phase_outputs/final_evaluation_results.csv
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
from agents.react_agent import AegisReActAgent
from rag.retriever import AegisRetriever
from remediation.remediation_engine import RemediationEngine

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "processed" / "incidents_master.csv"
OUTPUT_FILE = ROOT / "phase_outputs" / "final_evaluation_results.csv"


def normalize(value: object) -> str:
    """Normalize text values for simple RCA matching."""
    return str(value).lower().strip()


def main(limit: int = 50) -> None:
    """Evaluate AEGIS on the first N incidents."""
    incidents = pd.read_csv(INPUT_FILE).head(limit)
    agent = AegisReActAgent()
    retriever = AegisRetriever()
    remediation_engine = RemediationEngine()

    rows = []

    for _, incident in incidents.iterrows():
        incident_dict = incident.to_dict()
        result = agent.analyze(incident_dict)

        actual_root_cause = normalize(incident["root_cause"])
        predicted_root_cause = normalize(result["probable_root_cause"])
        rca_match = int(actual_root_cause in predicted_root_cause or predicted_root_cause in actual_root_cause)

        query = f"{incident['alert']} {incident['logs']} {incident['metrics']}"
        retrieved = retriever.search(query, top_k=5, source="incident")
        recall_at_5 = int(any(item["id"] == incident["incident_id"] for item in retrieved))

        baseline_mttr = float(incident["mttr_minutes_baseline"])
        aegis_mttr = baseline_mttr * 0.60 if rca_match else baseline_mttr * 0.82
        mttr_reduction_pct = round((baseline_mttr - aegis_mttr) / baseline_mttr * 100, 2)

        remediation_plan = remediation_engine.build_plan(
            incident=incident_dict,
            root_cause=result["probable_root_cause"],
            recommended_actions=result.get("recommended_actions", []),
        )
        approval_required_count = sum(1 for action in remediation_plan if action.get("requires_approval"))

        rows.append({
            "incident_id": incident["incident_id"],
            "actual_root_cause": incident["root_cause"],
            "predicted_root_cause": result["probable_root_cause"],
            "rca_match": rca_match,
            "retrieval_recall_at_5": recall_at_5,
            "baseline_mttr": baseline_mttr,
            "aegis_estimated_mttr": aegis_mttr,
            "mttr_reduction_pct": mttr_reduction_pct,
            "remediation_actions": len(remediation_plan),
            "approval_required_count": approval_required_count,
            "human_approval_coverage": int(approval_required_count > 0),
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output = pd.DataFrame(rows)
    output.to_csv(OUTPUT_FILE, index=False)

    print("Final AEGIS Evaluation Completed")
    print(f"RCA Accuracy: {output['rca_match'].mean():.2f}")
    print(f"Retrieval Recall@5: {output['retrieval_recall_at_5'].mean():.2f}")
    print(f"Average MTTR Reduction: {output['mttr_reduction_pct'].mean():.2f}%")
    print(f"Human Approval Coverage: {output['human_approval_coverage'].mean():.2f}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
