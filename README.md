# AEGIS Final Demo-Ready Project

**AEGIS: An Autonomous Agentic Framework for Incident Response and Root Cause Analysis in Cloud Systems**

This version is cleaned for final presentation. The main runnable files have clear names and the documentation explains the final demo flow.

## Main Commands

```bash
pip install -r requirements.txt
copy .env.example .env
python scripts/run_demo_setup.py
streamlit run ui/app_final_demo.py
```

## Main Files

| Purpose | File |
|---|---|
| Final setup | `scripts/run_demo_setup.py` |
| Final UI | `ui/app_final_demo.py` |
| Final API | `api/main_demo.py` |
| Final evaluation | `evaluation/run_final_evaluation.py` |
| Demo guide | `docs/FINAL_DEMO_GUIDE.md` |
| Presentation script | `docs/PRESENTATION_SCRIPT.md` |

## Setup Details

Use Python 3.11.

```bash
conda create -n aegis_demo python=3.11 -y
conda activate aegis_demo
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

AEGIS still works without an OpenAI key by using deterministic fallback RCA.

## Run Demo Setup

```bash
python scripts/run_demo_setup.py
```

Expected outputs:

```text
data/processed/incidents_master.csv
vector_db/aegis.faiss
data/kg/aegis_knowledge_graph.json
data/gnn/gnn_rca_baseline.joblib
phase_outputs/final_evaluation_results.csv
```

## Run Final UI

```bash
streamlit run ui/app_final_demo.py
```

## Optional API

```bash
uvicorn api.main_demo:app --reload
```

## Optional Neo4j

```bash
docker run --name aegis-neo4j -p7474:7474 -p7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5
python neo4j_kg/neo4j_loader.py
```

## Final Presentation Demo Flow

1. Select incident.
2. Run end-to-end AEGIS analysis.
3. Show RCA, confidence, evidence, and citations.
4. Show multi-agent timeline.
5. Show graph RCA candidates.
6. Show GNN-style Top-3 RCA.
7. Show remediation plan.
8. Approve one action.
9. Show approval audit log.
10. Show MTTR dashboard.

## Safety Note

AEGIS does not execute real production commands. The remediation workflow is simulation-only and requires human approval for risky actions.
