"""
Run AEGIS Final Demo Setup.

Use this before the final presentation demo. It builds every required artifact:
- Clean logs
- Incident repository
- FAISS vector database
- Service graph
- Local knowledge graph
- GNN-style RCA model
- Evaluation output CSV

Command:
    python scripts/run_demo_setup.py
"""
import subprocess
import sys

COMMANDS = [
    "python scripts/prepare_demo_data.py",
    "python incidents/raw_log_loader.py",
    "python incidents/create_incidents_from_logs.py",
    "python incidents/generate_synthetic_incidents.py",
    "python incidents/merge_incidents.py",
    "python rag/build_faiss_index.py",
    "python graph/service_graph.py",
    "python knowledge_graph/kg_builder.py",
    "python gnn/gnn_feature_builder.py",
    "python gnn/gnn_rca_baseline.py",
    "python evaluation/run_final_evaluation.py",
]


def main() -> None:
    """Execute setup commands in order and stop on the first failure."""
    print("Starting AEGIS final demo setup...\n")

    for command in COMMANDS:
        print(f">>> Running: {command}")
        result = subprocess.run(command, shell=True)
        if result.returncode != 0:
            print(f"\nSetup failed at: {command}")
            sys.exit(result.returncode)

    print("\nAEGIS final demo setup completed successfully.")
    print("Run the demo UI with:")
    print("streamlit run ui/app_final_demo.py")


if __name__ == "__main__":
    main()
