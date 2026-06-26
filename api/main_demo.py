from phase4.full_aegis_orchestrator import FullAEGISPhase4Orchestrator


def main():
    incident = {
        "incident_id": "DEMO-INC-001",
        "service": "payment-service",
        "severity": "P1",
        "alert": "Payment Gateway Timeout",
        "logs": "Payment gateway timeout. Downstream provider slow. HTTP 504 errors observed.",
        "metrics": "latency_p95=8000 error_rate=22 cpu=65 memory=70",
        "traces": "Trace shows payment-service waiting on external payment gateway call.",
        "screenshot_summary": "Grafana dashboard shows latency spike and payment timeout increase.",
    }

    aegis = FullAEGISPhase4Orchestrator()
    result = aegis.run(incident, use_llm=True, model="gpt-4o-mini", approved=False)

    print("\n========== AEGIS PHASE-4 FULL DEMO ==========\n")
    print("Root Cause:")
    print(result["planner_result"].get("probable_root_cause"))

    print("\nMultimodal RCA:")
    print(result["multimodal_rca"])

    print("\nGNN RCA Ranking:")
    print(result["gnn_rca_ranking"])

    print("\nRL Remediation Policy:")
    print(result["rl_remediation_policy"])

    print("\nRemediation Plan:")
    print(result["remediation_plan"])

    print("\nAutonomous Execution:")
    print(result["autonomous_execution"])


if __name__ == "__main__":
    main()