from graph.service_graph import load_graph, get_neighbors

KEYWORD_TO_SERVICE = {
    "database": "database",
    "db": "database",
    "jdbc": "database",
    "connection pool": "database",
    "kafka": "kafka",
    "consumer lag": "kafka",
    "queue": "kafka",
    "email": "email-gateway",
    "notification": "notification-service",
    "payment": "payment-service",
    "cart": "cart-service",
    "inventory": "inventory-service",
    "auth": "auth-service",
    "hdfs": "hdfs-namenode",
    "namenode": "hdfs-namenode",
    "datanode": "hdfs-datanode",
    "replication": "hdfs-datanode",
    "under replicated": "hdfs-datanode",
    "connection reset": "network",
    "timeout": "network",
    "machine check": "hardware-node",
    "not responding": "hardware-node",
    "kernel": "bgl-kernel",
    "oomkilled": "kubernetes-pod",
    "crashloopbackoff": "kubernetes-pod",
}

def rank_root_cause_services(incident, top_k=5):
    graph = load_graph()
    service = incident.get("service", "")
    text = f"{incident.get('alert','')} {incident.get('logs','')} {incident.get('metrics','')}".lower()
    scores = {}

    def add_score(node, value, reason):
        if not node:
            return
        if node not in scores:
            scores[node] = {"service": node, "score": 0.0, "reasons": []}
        scores[node]["score"] += value
        scores[node]["reasons"].append(reason)

    add_score(service, 0.40, "Affected service from incident input")

    if service in graph:
        neighbors = get_neighbors(service)
        for n in neighbors["downstream"]:
            add_score(n, 0.25, f"Downstream dependency of affected service {service}")
        for n in neighbors["upstream"]:
            add_score(n, 0.10, f"Upstream caller of affected service {service}")

    for keyword, mapped_service in KEYWORD_TO_SERVICE.items():
        if keyword in text:
            add_score(mapped_service, 0.35, f"Keyword evidence matched: {keyword}")
            if mapped_service in graph:
                for dep in graph.successors(mapped_service):
                    add_score(dep, 0.10, f"Dependency of keyword-matched service {mapped_service}")

    ranked = []
    for item in scores.values():
        item["score"] = round(min(item["score"], 1.0), 3)
        item["reason"] = "; ".join(item["reasons"][:3])
        ranked.append(item)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_k]
