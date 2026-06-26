"""
AEGIS Final Demo

Run:
python main_demo.py
"""

from multi_agents.planner_agent import AgenticIncidentPlanner
from remediation.remediation_engine import RemediationEngine


def main():

    incident = {
        "incident_id": "INC-DEMO-001",
        "service": "payment-service",
        "severity": "P1",
        "alert": "Database connection timeout",
        "logs": """
        ERROR connection timeout
        ERROR database unavailable
        ERROR retries exceeded
        """,
        "metrics": """
        cpu=72
        memory=68
        error_rate=23
        """
    }

    print("=" * 80)
    print("AEGIS INCIDENT ANALYSIS")
    print("=" * 80)

    planner = AgenticIncidentPlanner()

    analysis = planner.run(
        incident=incident,
        use_llm=True,
        model="gpt-4o-mini"
    )

    print("\nROOT CAUSE")
    print("-" * 40)
    print(analysis["probable_root_cause"])

    print("\nCONFIDENCE")
    print("-" * 40)
    print(analysis["confidence"])

    print("\nRECOMMENDATIONS")
    print("-" * 40)

    for action in analysis["recommended_actions"]:
        print(f"✓ {action}")

    engine = RemediationEngine()

    plan = engine.build_plan(
        incident,
        analysis["probable_root_cause"],
        analysis["recommended_actions"]
    )

    print("\nREMEDIATION PLAN")
    print("-" * 40)

    for action in plan["actions"]:
        print(action)

    print("\nDemo Complete")


if __name__ == "__main__":
    main()