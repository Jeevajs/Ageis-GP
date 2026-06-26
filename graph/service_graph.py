from pathlib import Path
import json
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DIR = ROOT / "data" / "graph"
GRAPH_FILE = GRAPH_DIR / "service_dependency_graph.json"

DEFAULT_EDGES = [
    ("frontend", "auth-service"),
    ("frontend", "cart-service"),
    ("cart-service", "inventory-service"),
    ("cart-service", "payment-service"),
    ("payment-service", "database"),
    ("payment-service", "notification-service"),
    ("order-service", "payment-service"),
    ("order-service", "inventory-service"),
    ("inventory-service", "database"),
    ("notification-service", "email-gateway"),
    ("hdfs-client", "hdfs-namenode"),
    ("hdfs-namenode", "hdfs-datanode"),
    ("hdfs-datanode", "network"),
    ("bgl-node", "bgl-kernel"),
    ("bgl-kernel", "hardware-node"),
    ("kubernetes-pod", "container-runtime"),
    ("container-runtime", "node"),
]

def build_default_graph():
    graph = nx.DiGraph()
    graph.add_edges_from(DEFAULT_EDGES)
    return graph

def save_default_graph():
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    graph = build_default_graph()
    data = {"nodes": list(graph.nodes()), "edges": list(graph.edges())}
    GRAPH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved default graph to {GRAPH_FILE}")

def load_graph():
    if not GRAPH_FILE.exists():
        save_default_graph()
    data = json.loads(GRAPH_FILE.read_text(encoding="utf-8"))
    graph = nx.DiGraph()
    graph.add_nodes_from(data.get("nodes", []))
    graph.add_edges_from([tuple(x) for x in data.get("edges", [])])
    return graph

def get_neighbors(service: str):
    graph = load_graph()
    if service not in graph:
        return {"upstream": [], "downstream": []}
    return {"upstream": list(graph.predecessors(service)), "downstream": list(graph.successors(service))}
