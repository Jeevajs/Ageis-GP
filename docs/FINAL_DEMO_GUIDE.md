# AEGIS Final Demo Guide

## Demo-Ready Command Sequence

Run these commands from the project root.

```bash
conda create -n aegis_demo python=3.11 -y
conda activate aegis_demo
pip install -r requirements.txt
copy .env.example .env
python scripts/run_demo_setup.py
streamlit run ui/app_final_demo.py
```

## What to Validate

After `run_demo_setup.py`, confirm these files exist:

```text
data/processed/clean_logs.csv
data/processed/incidents_master.csv
vector_db/aegis.faiss
vector_db/documents.json
data/graph/service_dependency_graph.json
data/kg/aegis_knowledge_graph.json
data/gnn/gnn_rca_baseline.joblib
phase_outputs/final_evaluation_results.csv
```

## Final UI Validation

In the UI, validate:

1. Incident dropdown loads.
2. RCA analysis runs.
3. Probable root cause appears.
4. Evidence appears.
5. Recommended actions appear.
6. Agent timeline appears.
7. Graph RCA candidates appear.
8. GNN-style RCA Top-3 appears.
9. Remediation plan appears.
10. Approve/reject buttons update audit log.
11. MTTR dashboard opens.
12. Knowledge graph tab opens.

## Presentation Talking Points

- RAG grounds the RCA using historical incidents and runbooks.
- OpenAI converts evidence into explainable RCA.
- Multi-agent design separates log, metric, retrieval, graph, and synthesis responsibilities.
- Knowledge graph captures incident-service-root-cause relationships.
- Human approval prevents unsafe autonomous actions.
