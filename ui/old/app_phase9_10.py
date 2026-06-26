import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from multi_agents.planner_agent import AgenticIncidentPlanner
from remediation.remediation_engine import RemediationEngine
from remediation.approval_store import get_events
from neo4j_kg.kg_query_service import KGQueryService


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "incidents_master.csv"


st.set_page_config(
    page_title="AEGIS Phase 9-10",
    layout="wide"
)

st.title("AEGIS Phase 9 + 10")
st.caption("Neo4j Knowledge Graph Explorer + Human Approval Remediation Workflow")


if not DATA.exists():
    st.error("incidents_master.csv not found. Run previous phases first.")
    st.stop()


df = pd.read_csv(DATA)

planner = AgenticIncidentPlanner()
engine = RemediationEngine()


with st.sidebar:
    st.header("Settings")
    use_llm = st.toggle("Use OpenAI LLM", value=True)
    model = st.text_input("OpenAI Model", "gpt-4o-mini")


tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Incident RCA + Remediation",
        "Neo4j KG Explorer",
        "Approval Audit Log",
        "Dataset"
    ]
)


# -------------------------------------------------------------------
# TAB 1: Incident RCA + Remediation
# -------------------------------------------------------------------
with tab1:
    selected = st.selectbox(
        "Select incident",
        df["incident_id"].tolist()
    )

    # Store selected incident globally so Neo4j tab uses the same incident
    st.session_state["selected_incident_id"] = selected

    row = df[df["incident_id"] == selected].iloc[0].to_dict()

    c1, c2 = st.columns(2)

    with c1:
        service = st.text_input("Service", row["service"])

        # Store selected service globally so Neo4j tab uses the same service
        st.session_state["selected_service"] = service

        severity = st.text_input("Severity", row["severity"])
        alert = st.text_input("Alert", row["alert"])

    with c2:
        logs = st.text_area("Logs", row["logs"], height=120)
        metrics = st.text_area("Metrics", row["metrics"], height=80)

    incident = {
        "incident_id": selected,
        "service": service,
        "severity": severity,
        "alert": alert,
        "logs": logs,
        "metrics": metrics
    }

    if st.button("Run RCA and Build Remediation Plan", type="primary"):
        result = planner.run(
            incident,
            use_llm=use_llm,
            model=model
        )

        st.session_state["phase9_10_result"] = result
        st.session_state["phase9_10_incident"] = incident

        st.success("RCA and remediation planning completed")

    if "phase9_10_result" in st.session_state:
        result = st.session_state["phase9_10_result"]
        incident = st.session_state["phase9_10_incident"]

        st.subheader("Root Cause")
        st.write(result.get("probable_root_cause"))

        st.subheader("Evidence")
        for evidence in result.get("evidence", []):
            st.write(f"- {evidence}")

        st.subheader("Recommended Actions")
        for action_text in result.get("recommended_actions", []):
            st.write(f"- {action_text}")

        st.subheader("Human Approval Remediation Plan")

        plan = engine.build_plan(
            incident,
            result.get("probable_root_cause"),
            result.get("recommended_actions", [])
        )

        for action in plan:
            with st.expander(
                f"{action['step']}. {action['title']} | "
                f"Risk: {action['risk']} | "
                f"Status: {action['status']}"
            ):
                st.write("Action ID:", action["action_id"])
                st.write("Command Preview:", action["command_preview"])
                st.write("Rollback:", action["rollback"])
                st.write("Requires Approval:", action["requires_approval"])

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(
                        f"Approve {action['action_id']}",
                        key=f"approve_{action['action_id']}"
                    ):
                        st.success(
                            engine.approve_action(
                                incident["incident_id"],
                                action["action_id"],
                                "demo-user",
                                "Approved from UI"
                            )
                        )

                with col2:
                    if st.button(
                        f"Reject {action['action_id']}",
                        key=f"reject_{action['action_id']}"
                    ):
                        st.warning(
                            engine.reject_action(
                                incident["incident_id"],
                                action["action_id"],
                                "demo-user",
                                "Rejected from UI"
                            )
                        )

                with col3:
                    st.json(engine.simulate_execution(action))


# -------------------------------------------------------------------
# TAB 2: Neo4j Knowledge Graph Explorer
# -------------------------------------------------------------------
with tab2:
    st.subheader("Neo4j Knowledge Graph Explorer")

    try:
        kg = KGQueryService()
        health = kg.health()

        st.write("Neo4j Connection:", health)

        if health.get("connected"):
            selected_service_for_kg = st.session_state.get(
                "selected_service",
                df["service"].iloc[0]
            )

            selected_incident_for_kg = st.session_state.get(
                "selected_incident_id",
                df["incident_id"].iloc[0]
            )

            service_q = st.text_input(
                "Service for KG Query",
                selected_service_for_kg
            )

            incident_q = st.text_input(
                "Incident ID for KG Query",
                selected_incident_for_kg
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("Get Incident Context"):
                    incident_context = kg.get_incident_context(incident_q)
                    st.dataframe(
                        pd.DataFrame(incident_context),
                        use_container_width=True
                    )

            with col2:
                if st.button("Get Service Incident History"):
                    service_history = kg.get_service_incident_history(service_q)
                    st.dataframe(
                        pd.DataFrame(service_history),
                        use_container_width=True
                    )

            with col3:
                if st.button("Root Cause Frequency"):
                    root_cause_frequency = kg.get_root_cause_frequency()
                    st.dataframe(
                        pd.DataFrame(root_cause_frequency),
                        use_container_width=True
                    )

            st.subheader("KG Snapshot")

            edges = kg.get_graph_snapshot(limit=100)

            st.dataframe(
                pd.DataFrame(edges),
                use_container_width=True
            )

        kg.close()

    except Exception as error:
        st.error(f"Neo4j not available: {error}")
        st.info("Start Neo4j and run: python neo4j_kg/neo4j_loader.py")


# -------------------------------------------------------------------
# TAB 3: Approval Audit Log
# -------------------------------------------------------------------
with tab3:
    st.subheader("Approval Audit Log")

    events = get_events()

    if events:
        st.dataframe(
            pd.DataFrame(events),
            use_container_width=True
        )
    else:
        st.info("No approval events recorded yet.")


# -------------------------------------------------------------------
# TAB 4: Dataset
# -------------------------------------------------------------------
with tab4:
    st.subheader("Incident Dataset")

    st.dataframe(
        df,
        use_container_width=True
    )