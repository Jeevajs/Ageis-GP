from neo4j_kg.neo4j_client import Neo4jClient

class KGQueryService:
    def __init__(self):
        self.client = Neo4jClient()
    def close(self):
        self.client.close()
    def health(self):
        return self.client.test_connection()
    def get_incident_context(self, incident_id):
        return self.client.run_query("""
        MATCH (i:Incident {id:$incident_id})
        OPTIONAL MATCH (i)-[:AFFECTS]->(s:Service)
        OPTIONAL MATCH (i)-[:HAS_ROOT_CAUSE]->(r:RootCause)
        OPTIONAL MATCH (s)-[:DEPENDS_ON]->(d:Service)
        RETURN i.id AS incident_id, i.alert AS alert, i.severity AS severity,
               s.name AS service, r.name AS root_cause, collect(DISTINCT d.name) AS dependencies
        """, {"incident_id": incident_id})
    def get_service_incident_history(self, service):
        return self.client.run_query("""
        MATCH (s:Service {name:$service})<-[:AFFECTS]-(i:Incident)-[:HAS_ROOT_CAUSE]->(r:RootCause)
        RETURN i.id AS incident_id, i.alert AS alert, i.severity AS severity,
               r.name AS root_cause, i.baseline_mttr AS baseline_mttr
        ORDER BY i.baseline_mttr DESC LIMIT 20
        """, {"service": service})
    def get_root_cause_frequency(self):
        return self.client.run_query("""
        MATCH (i:Incident)-[:HAS_ROOT_CAUSE]->(r:RootCause)
        RETURN r.name AS root_cause, count(i) AS count
        ORDER BY count DESC LIMIT 20
        """)
    def get_graph_snapshot(self, limit=100):
        return self.client.run_query("""
        MATCH (a)-[r]->(b)
        RETURN labels(a)[0] AS source_label, coalesce(a.name,a.id) AS source,
               type(r) AS relation, labels(b)[0] AS target_label, coalesce(b.name,b.id) AS target
        LIMIT $limit
        """, {"limit": limit})
