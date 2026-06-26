import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import subprocess
import pandas as pd
import streamlit as st

from multi_agents.planner_agent import AgenticIncidentPlanner
from remediation.remediation_engine import RemediationEngine
from remediation.approval_store import get_events
from neo4j_kg.kg_query_service import KGQueryService
from phase4.full_aegis_orchestrator import FullAEGISPhase4Orchestrator


ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "processed" / "incidents_master.csv"
EVAL_DATA = ROOT / "data" / "evaluation" / "phase4_demo_incidents.csv"

SUMMARY_FILE = ROOT / "phase_outputs" / "phase3_vs_phase4_summary.csv"
CATEGORY_FILE = ROOT / "phase_outputs" / "phase3_vs_phase4_category_summary.csv"
PHASE3_FILE = ROOT / "phase_outputs" / "phase3_llm_human_results.csv"
PHASE4_FILE = ROOT / "phase_outputs" / "phase4_full_aegis_results.csv"


st.set_page_config(page_title="AEGIS Final Demo", layout="wide")

st.title("AEGIS Phase 4 Final Demo")
st.caption("Neo4j Knowledge Graph Explorer + Human Approval Remediation Workflow")


if not DATA.exists():
    st.error("incidents_master.csv not found. Run: python scripts/run_demo_setup.py")
    st.stop()


df_all = pd.read_csv(DATA)
df_eval = pd.read_csv(EVAL_DATA) if EVAL_DATA.exists() else pd.DataFrame()


with st.sidebar:
    st.header("Settings")

    use_llm = st.toggle("Use OpenAI LLM", value=True)
    model = st.text_input("OpenAI Model", "gpt-4o-mini")

    st.markdown("---")

    ticket_source = st.radio(
        "Ticket Source",
        ["All Tickets", "20 Evaluation Incidents"],
        index=0
    )

    st.markdown("---")

    if ticket_source == "20 Evaluation Incidents":
        st.info("Using 20 special evaluation incidents.")
    else:
        st.info("Using full incidents_master.csv dataset.")


if ticket_source == "20 Evaluation Incidents":
    if df_eval.empty:
        st.error("20 incident evaluation file not found: data/evaluation/phase4_demo_incidents.csv")
        st.stop()
    df = df_eval.copy()
else:
    df = df_all.copy()


planner = AgenticIncidentPlanner()
engine = RemediationEngine()


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Incident RCA + Remediation",
    "Neo4j KG Explorer",
    "Approval Audit Log",
    "Dataset",
    "Phase-4 Advanced AEGIS",
    "Phase-3 vs Phase-4 Evaluation"
])


# ============================================================
# TAB 1: INCIDENT RCA + REMEDIATION
# ============================================================
with tab1:
    st.subheader("Incident RCA + Human Approval Remediation")

    selected = st.selectbox(
        "Select incident",
        df["incident_id"].astype(str).tolist(),
        key="tab1_incident_select"
    )

    row = df[df["incident_id"].astype(str) == selected].iloc[0].to_dict()

    st.markdown("### Incident Overview")

    c1, c2, c3 = st.columns(3)
    c1.metric("Incident ID", selected)
    c2.metric("Affected Service", row.get("service", "N/A"))
    c3.metric("Severity", row.get("severity", "N/A"))

    c1, c2 = st.columns(2)

    with c1:
        service = st.text_input("Service", str(row.get("service", "")), key="tab1_service")
        severity = st.text_input("Severity", str(row.get("severity", "P2")), key="tab1_severity")
        alert = st.text_input("Alert", str(row.get("alert", "")), key="tab1_alert")

    with c2:
        logs = st.text_area("Logs", str(row.get("logs", "")), height=120, key="tab1_logs")
        metrics = st.text_area("Metrics", str(row.get("metrics", "")), height=80, key="tab1_metrics")

    incident = {
        "incident_id": selected,
        "service": service,
        "severity": severity,
        "alert": alert,
        "logs": logs,
        "metrics": metrics,
        "traces": str(row.get("traces", "")),
        "screenshot_summary": str(row.get("screenshot_summary", "")),
    }

    if st.button("Run RCA and Build Remediation Plan", type="primary"):
        result = planner.run(incident, use_llm=use_llm, model=model)
        st.session_state["phase9_10_result"] = result
        st.session_state["phase9_10_incident"] = incident
        st.success("RCA and remediation planning completed")

    if "phase9_10_result" in st.session_state:
        result = st.session_state["phase9_10_result"]
        incident = st.session_state["phase9_10_incident"]

        root_cause = result.get("probable_root_cause", result.get("root_cause", "N/A"))
        confidence = result.get("confidence", result.get("rca_confidence", "N/A"))

        st.markdown("---")
        st.markdown("## RCA Result")

        c1, c2, c3 = st.columns(3)
        c1.metric("Probable Root Cause", root_cause)
        c2.metric("Confidence", confidence)
        c3.metric("Affected Service", incident.get("service", "N/A"))

        st.markdown("### Service Impact")

        impact_df = pd.DataFrame([{
            "Incident ID": incident.get("incident_id"),
            "Affected Service": incident.get("service"),
            "Severity": incident.get("severity"),
            "Alert": incident.get("alert"),
            "Probable Root Cause": root_cause
        }])

        st.dataframe(impact_df, use_container_width=True)

        st.markdown("### Evidence")

        evidence = result.get("evidence", [])
        if evidence:
            for e in evidence:
                st.write(f"- {e}")
        else:
            st.info("No evidence returned.")

        st.markdown("### Recommended Actions")

        actions = result.get("recommended_actions", [])
        if actions:
            action_df = pd.DataFrame({
                "Step": list(range(1, len(actions) + 1)),
                "Recommended Action": actions
            })
            st.dataframe(action_df, use_container_width=True)
        else:
            st.info("No recommended actions returned.")

        st.markdown("## Human Approval Remediation Plan")

        plan = engine.build_plan(
            incident,
            root_cause,
            actions
        )

        for action in plan:
            title = action.get("title", "Remediation Action")
            risk = action.get("risk", "N/A")
            status = action.get("status", "N/A")
            action_id = action.get("action_id", "N/A")

            with st.expander(f"{action.get('step', '')}. {title} | Risk: {risk} | Status: {status}"):

                c1, c2 = st.columns(2)

                with c1:
                    st.write("**Action ID:**", action_id)
                    st.write("**Requires Approval:**", action.get("requires_approval", "N/A"))
                    st.write("**Command Preview:**", action.get("command_preview", "N/A"))

                with c2:
                    st.write("**Rollback:**", action.get("rollback", "N/A"))

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button(f"Approve {action_id}", key=f"approve_{action_id}"):
                        st.success(
                            engine.approve_action(
                                incident["incident_id"],
                                action_id,
                                "demo-user",
                                "Approved from UI"
                            )
                        )

                with col2:
                    if st.button(f"Reject {action_id}", key=f"reject_{action_id}"):
                        st.warning(
                            engine.reject_action(
                                incident["incident_id"],
                                action_id,
                                "demo-user",
                                "Rejected from UI"
                            )
                        )

                with col3:
                    simulation = engine.simulate_execution(action)
                    st.write("**Execution Simulation:**")
                    st.write(simulation)


# ============================================================
# TAB 2: NEO4J KG EXPLORER
# ============================================================
with tab2:
    st.subheader("Neo4j Knowledge Graph Explorer")

    try:
        kg = KGQueryService()
        health = kg.health()

        connected = health.get("connected", False)

        if connected:
            st.success("Neo4j Connected")
        else:
            st.error("Neo4j Not Connected")

        with st.expander("Neo4j Health Details"):
            st.write(health)

        if connected:
            st.markdown("### Query Knowledge Graph")

            service_list = sorted(df["service"].dropna().astype(str).unique().tolist())
            incident_list = sorted(df["incident_id"].dropna().astype(str).unique().tolist())

            if not service_list:
                service_list = ["payment-service"]

            if not incident_list:
                incident_list = ["RAW-INC-0001"]

            c1, c2 = st.columns(2)

            with c1:
                service_q = st.selectbox(
                    "Select Service for KG Query",
                    service_list,
                    key="kg_service_select"
                )

            with c2:
                incident_q = st.selectbox(
                    "Select Incident ID for KG Query",
                    incident_list,
                    key="kg_incident_select"
                )

            c1, c2, c3 = st.columns(3)

            with c1:
                if st.button("Get Incident Context"):
                    context = kg.get_incident_context(incident_q)
                    if context:
                        st.markdown("### Incident Context")
                        st.dataframe(pd.DataFrame(context), use_container_width=True)
                    else:
                        st.warning("No incident context found in Neo4j. Reload Neo4j data.")

            with c2:
                if st.button("Get Service Incident History"):
                    history = kg.get_service_incident_history(service_q)
                    if history:
                        st.markdown("### Service Incident History")
                        st.dataframe(pd.DataFrame(history), use_container_width=True)
                    else:
                        st.warning("No service history found in Neo4j.")

            with c3:
                if st.button("Root Cause Frequency"):
                    freq = kg.get_root_cause_frequency()
                    if freq:
                        st.markdown("### Root Cause Frequency")
                        st.dataframe(pd.DataFrame(freq), use_container_width=True)
                    else:
                        st.warning("No root cause frequency data found.")

            st.markdown("### KG Snapshot")

            edges = kg.get_graph_snapshot(limit=100)

            if edges:
                st.dataframe(pd.DataFrame(edges), use_container_width=True)
            else:
                st.warning("Neo4j is connected but graph has no data.")
                st.code("python neo4j_kg\\neo4j_loader.py")

        kg.close()

    except Exception as e:
        st.error(f"Neo4j not available: {e}")
        st.info("Start Neo4j and load graph data:")
        st.code(
            "docker start aegis-neo4j\n"
            "python neo4j_kg\\neo4j_loader.py"
        )


# ============================================================
# TAB 3: APPROVAL AUDIT LOG
# ============================================================
with tab3:
    st.subheader("Approval Audit Log")

    events = get_events()

    if events:
        st.dataframe(pd.DataFrame(events), use_container_width=True)
    else:
        st.info("No approval events recorded yet.")


# ============================================================
# TAB 4: DATASET
# ============================================================
with tab4:
    st.subheader("Dataset Viewer")

    c1, c2, c3 = st.columns(3)
    c1.metric("Selected Dataset", ticket_source)
    c2.metric("Total Incidents", len(df))
    c3.metric("Unique Services", df["service"].nunique() if "service" in df.columns else 0)

    st.dataframe(df, use_container_width=True)


# ============================================================
# TAB 5: PHASE-4 ADVANCED AEGIS
# ============================================================
with tab5:
    st.subheader("Phase-4 Advanced AEGIS Analysis")

    selected = st.selectbox(
        "Select incident for Phase-4",
        df["incident_id"].astype(str).tolist(),
        key="phase4_incident_select"
    )

    row = df[df["incident_id"].astype(str) == selected].iloc[0].to_dict()

    incident = {
        "incident_id": row.get("incident_id", selected),
        "service": row.get("service", ""),
        "severity": row.get("severity", "P2"),
        "alert": row.get("alert", ""),
        "logs": row.get("logs", ""),
        "metrics": row.get("metrics", ""),
        "traces": row.get("traces", ""),
        "screenshot_summary": row.get("screenshot_summary", ""),
    }

    c1, c2, c3 = st.columns(3)
    c1.metric("Incident ID", incident["incident_id"])
    c2.metric("Affected Service", incident["service"])
    c3.metric("Severity", incident["severity"])

    st.markdown("### Incident Context")

    c1, c2 = st.columns(2)

    with c1:
        st.text_input("Alert", str(incident["alert"]), disabled=True, key="phase4_alert")
        st.text_area("Logs", str(incident["logs"]), height=120, disabled=True, key="phase4_logs")

    with c2:
        st.text_area("Metrics", str(incident["metrics"]), height=80, disabled=True, key="phase4_metrics")
        st.text_area(
            "Traces / Screenshot Summary",
            f"{incident.get('traces', '')}\n{incident.get('screenshot_summary', '')}",
            height=120,
            disabled=True,
            key="phase4_trace_summary"
        )

    approved = st.checkbox("Approve autonomous execution simulation", value=False)

    if st.button("Run Full Phase-4 AEGIS", type="primary"):
        orchestrator = FullAEGISPhase4Orchestrator()
        phase4_result = orchestrator.run(
            incident,
            use_llm=use_llm,
            model=model,
            approved=approved,
        )
        st.session_state["phase4_result"] = phase4_result
        st.success("Full Phase-4 AEGIS analysis completed")

    if "phase4_result" in st.session_state:
        result = st.session_state["phase4_result"]
        planner_result = result.get("planner_result", {})

        root_cause = planner_result.get(
            "probable_root_cause",
            planner_result.get("root_cause", "Not available")
        )

        confidence = planner_result.get(
            "confidence",
            planner_result.get("rca_confidence", "N/A")
        )

        st.markdown("---")
        st.markdown("## RCA Summary")

        c1, c2, c3 = st.columns(3)
        c1.metric("Probable Root Cause", root_cause)
        c2.metric("Confidence", confidence)
        c3.metric("Execution Status", result.get("autonomous_execution", {}).get("status", "N/A"))

        st.markdown("### Affected Service Impact")

        service_df = pd.DataFrame([{
            "Incident ID": result["incident"].get("incident_id"),
            "Affected Service": result["incident"].get("service"),
            "Severity": result["incident"].get("severity"),
            "Alert": result["incident"].get("alert"),
            "Root Cause": root_cause
        }])

        st.dataframe(service_df, use_container_width=True)

        st.markdown("### Evidence")

        evidence = planner_result.get("evidence", [])

        if evidence:
            for item in evidence:
                st.write(f"- {item}")
        else:
            st.info("No evidence returned.")

        st.markdown("### Recommended Actions")

        actions = planner_result.get("recommended_actions", [])

        if actions:
            actions_df = pd.DataFrame({
                "Step": list(range(1, len(actions) + 1)),
                "Recommended Action": actions
            })
            st.dataframe(actions_df, use_container_width=True)
        else:
            st.info("No recommended actions available.")

        st.markdown("---")
        st.markdown("## Advanced Phase-4 Components")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### Multimodal RCA")
            mm = result.get("multimodal_rca", {})

            st.metric("Signals Detected", mm.get("signal_count", 0))

            signals = mm.get("signals", [])

            if signals:
                for signal in signals:
                    st.write(f"- {signal}")
            else:
                st.info("No multimodal signal detected.")

        with c2:
            st.markdown("### RL Remediation Policy")
            rl = result.get("rl_remediation_policy", {})

            st.metric("Recommended Action", rl.get("recommended_action", "N/A"))
            st.metric("Expected Reward", rl.get("expected_reward", "N/A"))

            st.write("**Policy Type:**", rl.get("policy_type", "N/A"))

        st.markdown("### GNN RCA Ranking")

        gnn = result.get("gnn_rca_ranking", {})
        top_causes = gnn.get("top3_root_causes", [])

        if top_causes:
            st.dataframe(pd.DataFrame(top_causes), use_container_width=True)
        else:
            st.warning("No GNN RCA output available.")

        st.markdown("### Remediation Plan")

        plan = result.get("remediation_plan", [])

        if plan:
            clean_plan = []

            for item in plan:
                clean_plan.append({
                    "Action ID": item.get("action_id"),
                    "Title": item.get("title"),
                    "Risk": item.get("risk"),
                    "Status": item.get("status"),
                    "Requires Approval": item.get("requires_approval"),
                    "Rollback": item.get("rollback")
                })

            st.dataframe(pd.DataFrame(clean_plan), use_container_width=True)
        else:
            st.info("No remediation plan generated.")

        st.markdown("### Autonomous Execution")

        execution = result.get("autonomous_execution", {})

        c1, c2, c3 = st.columns(3)
        c1.metric("Approved", execution.get("approved", False))
        c2.metric("Executed", execution.get("executed", False))
        c3.metric("Status", execution.get("status", "N/A"))

        st.info(f"Command Preview: {execution.get('command', 'N/A')}")
        st.caption(f"Real Execution Enabled: {execution.get('real_execution_enabled', False)}")


# ============================================================
# TAB 6: PHASE-3 VS PHASE-4 EVALUATION
# ============================================================
with tab6:
    st.subheader("Phase-3 vs Phase-4 Evaluation")

    c1, c2 = st.columns([1, 3])

    with c1:
        run_eval = st.button("Run Evaluation Now", type="primary")

    with c2:
        st.info("This runs: python evaluation/run_phase3_phase4_comparison.py")

    if run_eval:
        with st.spinner("Running Phase-3 vs Phase-4 comparison..."):
            completed = subprocess.run(
                ["python", "evaluation/run_phase3_phase4_comparison.py"],
                cwd=str(ROOT),
                capture_output=True,
                text=True
            )

        if completed.returncode == 0:
            st.success("Evaluation completed successfully.")
            st.code(completed.stdout)
        else:
            st.error("Evaluation failed.")
            st.code(completed.stderr)

    if SUMMARY_FILE.exists():
        st.markdown("## Overall Comparison")

        summary_df = pd.read_csv(SUMMARY_FILE)
        st.dataframe(summary_df, use_container_width=True)

        st.markdown("### Key Metrics")

        if len(summary_df) >= 2:
            p3 = summary_df.iloc[0]
            p4 = summary_df.iloc[1]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Phase-3 Accuracy", f"{p3['rca_accuracy_pct']}%")
            c2.metric("Phase-4 Accuracy", f"{p4['rca_accuracy_pct']}%")
            c3.metric("Phase-3 Avg Latency", f"{p3['avg_latency_sec']} sec")
            c4.metric("Phase-4 Avg Latency", f"{p4['avg_latency_sec']} sec")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Phase-3 Cost / Incident", f"${p3['avg_cost_per_incident_usd']}")
            c2.metric("Phase-4 Cost / Incident", f"${p4['avg_cost_per_incident_usd']}")
            c3.metric("Phase-3 Security", p3["avg_security_score"])
            c4.metric("Phase-4 Security", p4["avg_security_score"])

        if CATEGORY_FILE.exists():
            st.markdown("## Category-wise Comparison")
            st.dataframe(pd.read_csv(CATEGORY_FILE), use_container_width=True)

        if PHASE3_FILE.exists():
            st.markdown("## Phase-3 Individual Incident Results")
            st.dataframe(pd.read_csv(PHASE3_FILE), use_container_width=True)

        if PHASE4_FILE.exists():
            st.markdown("## Phase-4 Individual Incident Results")
            st.dataframe(pd.read_csv(PHASE4_FILE), use_container_width=True)

    else:
        st.warning("Evaluation output not found. Click 'Run Evaluation Now' or run this command manually:")
        st.code("python evaluation/run_phase3_phase4_comparison.py")