"""
Final one-command setup for AEGIS.
Run from project root:
    python scripts/run_final_setup.py
"""
import subprocess
import sys

commands = [
    "python scripts/phase1_setup_data.py",
    "python incidents/raw_log_loader.py",
    "python incidents/create_incidents_from_logs.py",
    "python incidents/generate_synthetic_incidents.py",
    "python incidents/merge_incidents.py",
    "python rag/build_faiss_index.py",
    "python scripts/setup_phase4_5.py",
    "python scripts/setup_phase6_7_8.py",
    "python evaluation/evaluate_phase9_10.py"
]

for cmd in commands:
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"FAILED: {cmd}")
        sys.exit(result.returncode)

print("\nAEGIS final setup completed.")
print("Run UI: streamlit run ui/app_final.py")
