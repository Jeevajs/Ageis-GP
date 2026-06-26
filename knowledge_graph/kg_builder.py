from pathlib import Path
import json
import pandas as pd
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "incidents_master.csv"
KG_DIR = ROOT / "data" / "kg"
KG_FILE = KG_DIR / "aegis_knowledge_graph.json"

def build_kg_from_incidents():
    df = pd.read_csv(DATA)
    graph = nx.MultiDiGraph()
    for _, row in df.iterrows():
        incident = str(row["incident_id"])
        service = str(row["service"])
        root_cause = str(row["root_cause"])
        alert = str(row["alert"])
        graph.add_node(incident, label="Incident", name=incident)
        graph.add_node(service, label="Service", name=service)
        graph.add_node(root_cause, label="RootCause", name=root_cause)
        graph.add_node(alert, label="Alert", name=alert)
        graph.add_edge(incident, service, relation="AFFECTS")
        graph.add_edge(incident, alert, relation="TRIGGERED_BY")
        graph.add_edge(incident, root_cause, relation="HAS_ROOT_CAUSE")
        graph.add_edge(service, root_cause, relation="HAS_OBSERVED_FAILURE")
    data = {
        "nodes": [{"id": n, **attrs} for n, attrs in graph.nodes(data=True)],
        "edges": [{"source": u, "target": v, **attrs} for u, v, attrs in graph.edges(data=True)]
    }
    KG_DIR.mkdir(parents=True, exist_ok=True)
    KG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved KG to {KG_FILE}")
    return data

def load_kg():
    if not KG_FILE.exists():
        return build_kg_from_incidents()
    return json.loads(KG_FILE.read_text(encoding="utf-8"))

if __name__ == "__main__":
    build_kg_from_incidents()
