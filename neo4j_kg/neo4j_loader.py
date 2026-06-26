import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import pandas as pd
from neo4j_kg.neo4j_client import Neo4jClient

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "incidents_master.csv"

def load_incidents_to_neo4j(clear_existing=True):
    df = pd.read_csv(DATA)
    client = Neo4jClient()
    if clear_existing:
        client.run_query("MATCH (n) DETACH DELETE n")

    client.run_query("CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE")
    client.run_query("CREATE CONSTRAINT service_name IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE")
    client.run_query("CREATE CONSTRAINT root_cause_name IF NOT EXISTS FOR (r:RootCause) REQUIRE r.name IS UNIQUE")

    for _, row in df.iterrows():
        params = {
            "incident_id": str(row["incident_id"]),
            "service": str(row["service"]),
            "severity": str(row["severity"]),
            "alert": str(row["alert"]),
            "logs": str(row["logs"]),
            "metrics": str(row["metrics"]),
            "root_cause": str(row["root_cause"]),
            "mttr": float(row["mttr_minutes_baseline"])
        }
        client.run_query("""
        MERGE (i:Incident {id: $incident_id})
        SET i.severity=$severity, i.alert=$alert, i.logs=$logs, i.metrics=$metrics, i.baseline_mttr=$mttr
        MERGE (s:Service {name: $service})
        MERGE (r:RootCause {name: $root_cause})
        MERGE (a:Alert {name: $alert})
        MERGE (i)-[:AFFECTS]->(s)
        MERGE (i)-[:TRIGGERED_BY]->(a)
        MERGE (i)-[:HAS_ROOT_CAUSE]->(r)
        MERGE (s)-[:HAS_OBSERVED_FAILURE]->(r)
        """, params)

    dependencies = [
        ("frontend","auth-service"),("frontend","cart-service"),("cart-service","inventory-service"),
        ("cart-service","payment-service"),("payment-service","database"),
        ("payment-service","notification-service"),("order-service","payment-service"),
        ("order-service","inventory-service"),("inventory-service","database"),
        ("hdfs-namenode","hdfs-datanode"),("hdfs-datanode","network"),
        ("bgl-kernel","hardware-node"),("kubernetes-pod","container-runtime")
    ]
    for src, dst in dependencies:
        client.run_query("""
        MERGE (a:Service {name:$src})
        MERGE (b:Service {name:$dst})
        MERGE (a)-[:DEPENDS_ON]->(b)
        """, {"src": src, "dst": dst})
    client.close()
    print(f"Loaded {len(df)} incidents into Neo4j.")

if __name__ == "__main__":
    load_incidents_to_neo4j()
