from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "incidents_master.csv"
OUT = ROOT / "data" / "gnn" / "gnn_features.csv"

KEYWORDS = ["timeout", "connection reset", "under replicated", "oomkilled", "crashloopbackoff",
            "connection pool", "consumer lag", "http 500", "machine check", "not responding",
            "database", "kafka"]

def build_features():
    df = pd.read_csv(DATA)
    rows = []
    for _, r in df.iterrows():
        text = f"{r['alert']} {r['logs']} {r['metrics']}".lower()
        row = {"incident_id": r["incident_id"], "service": r["service"], "root_cause": r["root_cause"],
               "severity_num": {"P1": 3, "P2": 2, "P3": 1}.get(str(r["severity"]), 1),
               "text_length": len(text)}
        for kw in KEYWORDS:
            row[f"kw_{kw.replace(' ', '_')}"] = int(kw in text)
        rows.append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"Saved GNN-style features to {OUT}")

if __name__ == "__main__":
    build_features()
